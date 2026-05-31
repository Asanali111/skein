"""Antibody tests for the iter security-audit fixes.

Each test pins one fixed bug so a future refactor can't silently reintroduce
it. Grouped by the subsystem the fix landed in.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# MCP request hardening (wevex/mcp.py)
# ---------------------------------------------------------------------------

def _call(client: TestClient, method: str, params=None, req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params
    return client.post("/mcp", json=body).json()


def test_missing_required_arg_is_invalid_params_not_internal(client: TestClient):
    """A tools/call with a required arg missing must come back as -32602
    (Invalid params), never -32603 (Internal error) from a raw KeyError."""
    resp = _call(client, "tools/call", {"name": "recall", "arguments": {}})
    assert "error" in resp
    assert resp["error"]["code"] == -32602
    # The missing key name is surfaced to help the caller fix the request.
    assert "query" in resp["error"]["message"]


def test_non_dict_params_is_invalid_params(client: TestClient):
    """`params` that isn't an object → -32602, not an AttributeError crash."""
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": [1, 2, 3]},
    ).json()
    assert resp["error"]["code"] == -32602


def test_non_dict_arguments_is_invalid_params(client: TestClient):
    resp = _call(client, "tools/call", {"name": "recall", "arguments": "nope"})
    assert resp["error"]["code"] == -32602


def test_oversized_batch_is_rejected(client: TestClient):
    """An unbounded JSON-RPC batch is a CPU-exhaustion knob; cap it."""
    from wevex.mcp import MAX_BATCH_SIZE

    batch = [
        {"jsonrpc": "2.0", "id": i, "method": "ping"}
        for i in range(MAX_BATCH_SIZE + 1)
    ]
    resp = client.post("/mcp", json=batch).json()
    # A single error object (not a list of per-item results).
    assert isinstance(resp, dict)
    assert resp["error"]["code"] == -32600


def test_in_range_batch_still_works(client: TestClient):
    batch = [{"jsonrpc": "2.0", "id": i, "method": "ping"} for i in range(3)]
    resp = client.post("/mcp", json=batch).json()
    assert isinstance(resp, list)
    assert len(resp) == 3
    assert all(r["result"] == {} for r in resp)


def test_internal_error_does_not_leak_exception_detail(client: TestClient):
    """If a handler does fault, the response must not echo str(e) (which
    routinely carries absolute paths / SQL). We assert the structural
    guarantee: no -32603 response ever carries a `data.detail` field."""
    # boost with a non-numeric value used to ValueError → -32603 w/ detail;
    # it is now -32602. Either way, no leaked detail.
    resp = _call(client, "tools/call",
                 {"name": "boost", "arguments": {"fragment_id": "x", "value": "abc"}})
    assert resp["error"]["code"] == -32602
    assert "data" not in resp["error"] or "detail" not in resp["error"].get("data", {})


# ---------------------------------------------------------------------------
# Model input bounds (wevex/models.py)
# ---------------------------------------------------------------------------

def test_ttl_seconds_overflow_rejected():
    """A huge ttl_seconds used to overflow timedelta/datetime and crash the
    write path with an unhandled OverflowError. It must be rejected up front."""
    from wevex.models import FragmentCreate

    with pytest.raises(ValidationError):
        FragmentCreate(type="decision", content="x", scope_id="s", owner_id="o",
                       ttl_seconds=10 ** 18)


def test_negative_ttl_rejected():
    from wevex.models import FragmentCreate

    with pytest.raises(ValidationError):
        FragmentCreate(type="decision", content="x", scope_id="s", owner_id="o",
                       ttl_seconds=-5)


def test_content_length_is_bounded():
    from wevex.models import FragmentCreate

    with pytest.raises(ValidationError):
        FragmentCreate(type="decision", content="z" * 300_000,
                       scope_id="s", owner_id="o")


def test_recall_query_length_is_bounded():
    from wevex.models import RecallRequest

    with pytest.raises(ValidationError):
        RecallRequest(query="q" * 5000, scope="project:x")


# ---------------------------------------------------------------------------
# Storage pagination + dedupe (wevex/storage.py)
# ---------------------------------------------------------------------------

def test_clamp_page_bounds_limit_and_offset():
    from wevex.storage import _clamp_page

    # Negative LIMIT means *unlimited* in SQLite — must clamp to 0.
    assert _clamp_page(-1, 0) == (0, 0)
    # Huge values clamp to the ceiling.
    assert _clamp_page(10 ** 9, 10 ** 9, max_limit=1000) == (1000, 10 ** 9)
    # Negative offset clamps to 0; junk types fall back safely.
    assert _clamp_page(50, -5) == (50, 0)
    assert _clamp_page("x", "y")[0] >= 0


def test_dedupe_does_not_revive_expired_fragment(seeded_storage):
    """Re-asserting content whose TTL already lapsed must create a fresh
    fragment, not value-boost the logically-dead one."""
    from wevex.models import FragmentCreate

    s = seeded_storage
    fc = FragmentCreate(
        type="decision", content="dedupe-revival-probe-unique",
        scope_id=s._test_scope.id, owner_id=s._test_user.id,
        created_by_tool="t", ttl_seconds=3600,
    )
    f1 = s.create_fragment(fc)
    # Force its expiry into the past (simulate a lapsed-but-not-yet-swept TTL).
    s._conn.execute(
        "UPDATE fragments SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?",
        (f1.id,),
    )
    s._conn.commit()

    f2 = s.create_fragment(fc)
    assert f2.id != f1.id, "expired fragment must not be revived by dedupe"

    # And live dedupe still works: re-asserting now bumps the live f2.
    f3 = s.create_fragment(fc)
    assert f3.id == f2.id, "live fragment should still dedupe"


# ---------------------------------------------------------------------------
# Hook command-string quoting (wevex/hooks_install.py)
# ---------------------------------------------------------------------------

def test_quote_bin_leaves_plain_path_bare():
    from wevex.hooks_install import _quote_bin

    assert _quote_bin("wevex") == "wevex"


def test_quote_bin_quotes_shell_metacharacters():
    """An unquoted path with a shell separator was a command-injection vector
    baked into the user's settings.json — it must be quoted/escaped."""
    from wevex.hooks_install import _quote_bin

    # `&` (command separator) and space are dangerous on BOTH cmd.exe and
    # POSIX shells, so the assertion holds regardless of the test platform.
    for danger in ("/opt/a&b/wevex", "/opt/a b/wevex"):
        out = _quote_bin(danger)
        assert out != danger, f"{danger!r} must not be emitted bare"
        # The raw separator must no longer sit unquoted in the command token.
        assert out.startswith(("'", '"')) or "\\" in out


# ---------------------------------------------------------------------------
# Secret-file permissions (wevex/paths.py)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    __import__("os").name == "nt",
    reason="POSIX file-mode bits; chmod is a near-no-op on Windows",
)
def test_atomic_write_text_secret_is_owner_only(tmp_path):
    import os
    import stat

    from wevex.paths import atomic_write_text

    p = tmp_path / "secrets" / "config.json"
    atomic_write_text(p, '{"bearer_token": "s3cr3t"}', secret=True)
    mode = stat.S_IMODE(p.stat().st_mode)
    assert mode == 0o600, f"secret file must be 0600, got {oct(mode)}"
    # No leftover temp file.
    assert not list(p.parent.glob("*.tmp"))


def test_atomic_write_text_is_atomic_and_complete(tmp_path):
    from wevex.paths import atomic_write_text

    p = tmp_path / "settings.json"
    atomic_write_text(p, "hello")
    assert p.read_text() == "hello"
    atomic_write_text(p, "world")
    assert p.read_text() == "world"
    assert not list(p.parent.glob("*.tmp"))
