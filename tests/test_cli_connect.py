"""Tests for ``wevex connect`` (the visible command after ADR-002).

The old ``wevex clients`` and ``wevex disconnect`` commands were deleted
in iter 33 — the clients table folded into ``wevex status`` and disconnect
behavior moved under ``wevex connect --remove``. The regression coverage
for the config-mutation path (wevex entry removed cleanly, sibling
entries preserved) is kept here, just re-targeted at the new flag.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from wevex import connections as conns
from wevex.cli import main


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Redirect home, registry, and PATH so the CLI doesn't see real installs."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(conns, "CONNECTIONS_PATH", tmp_path / "connections.json")
    # WindsurfClient detects via /Applications/Windsurf.app on macOS — stub it out
    # so the "no detected clients" test isn't broken by a real Windsurf install.
    from wevex import clients as clients_mod
    monkeypatch.setattr(clients_mod, "_is_macos", lambda: False)
    return tmp_path


# ---------------------------------------------------------------------------
# `wevex connect <id>`
# ---------------------------------------------------------------------------

class TestConnectByID:
    def test_unknown_id_errors(self, isolated):
        runner = CliRunner()
        result = runner.invoke(main, ["connect", "does-not-exist"])
        assert result.exit_code != 0
        assert "Unknown client id" in result.output

    def test_not_installed_errors(self, isolated):
        # Cursor not installed (no ~/.cursor and no binary)
        runner = CliRunner()
        result = runner.invoke(main, ["connect", "cursor"])
        assert result.exit_code != 0
        assert "does not appear to be installed" in result.output


class TestConnectAll:
    def test_no_detected_clients_errors(self, isolated):
        runner = CliRunner()
        result = runner.invoke(main, ["connect", "--all"])
        assert result.exit_code != 0
        assert "No supported clients detected" in result.output


# ---------------------------------------------------------------------------
# `wevex connect --remove` (replaces `wevex disconnect` per ADR-002)
# ---------------------------------------------------------------------------

class TestConnectRemove:
    def test_removes_wevex_from_config(self, isolated):
        # Pretend cursor is connected with a real config file that has both
        # a wevex entry and an unrelated sibling. The remove path must wipe
        # wevex and leave the sibling intact.
        cfg = isolated / ".cursor" / "mcp.json"
        cfg.parent.mkdir()
        cfg.write_text(json.dumps({
            "mcpServers": {
                "wevex": {"url": "http://x/mcp"},
                "other": {"url": "http://other"},
            }
        }))
        conns.mark_connected("cursor", [str(cfg)])

        runner = CliRunner()
        result = runner.invoke(main, ["connect", "cursor", "--remove"])
        assert result.exit_code == 0

        data = json.loads(cfg.read_text())
        assert "wevex" not in data["mcpServers"]
        assert "other" in data["mcpServers"]
        assert not conns.is_connected("cursor")
