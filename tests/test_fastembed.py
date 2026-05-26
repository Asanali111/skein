"""Tests for the iter-23 FastembedProvider + dimension-mismatch detection.

The provider itself loads ``BAAI/bge-small-en-v1.5`` lazily on first
instantiation. The model weights cache to ``~/.cache/fastembed/`` after
the first download, so these tests pay the ~130 MB download once per
machine, then run in seconds.
"""
from __future__ import annotations

import sys

import pytest

# Skip the whole module if fastembed isn't installed in this env (it's a
# base dep in iter 23 but devs running an older venv shouldn't see hard
# failures).
fastembed = pytest.importorskip("fastembed")

from wevex.embeddings import (
    EmbeddingProvider,
    FastembedProvider,
    get_provider,
)
from wevex.storage import Storage


# ---------------------------------------------------------------------------
# FastembedProvider shape
# ---------------------------------------------------------------------------

def test_fastembed_dimension_is_384() -> None:
    """BAAI/bge-small-en-v1.5 produces 384-dim vectors."""
    assert FastembedProvider.dimension == 384


def test_fastembed_is_real() -> None:
    """Doctor + best_available rely on this marker to treat fastembed as
    a real semantic provider (not BM25/hash placeholder)."""
    assert FastembedProvider.is_real is True


def test_fastembed_is_subclass_of_base() -> None:
    assert issubclass(FastembedProvider, EmbeddingProvider)


def test_fastembed_default_model_name() -> None:
    """Default model is BAAI/bge-small-en-v1.5 — small (~130 MB), fast."""
    assert FastembedProvider.model == "BAAI/bge-small-en-v1.5"


# ---------------------------------------------------------------------------
# Embed behavior
# ---------------------------------------------------------------------------

def test_fastembed_embed_one_returns_384_floats() -> None:
    p = FastembedProvider()
    vec = p.embed_one("wevex context bus")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec[:5])


def test_fastembed_embed_batch_shape() -> None:
    p = FastembedProvider()
    vecs = p.embed(["alpha", "beta", "gamma"])
    assert len(vecs) == 3
    assert all(len(v) == 384 for v in vecs)


def test_fastembed_embed_deterministic() -> None:
    """Same text twice -> identical vector. Important: lets the iter-18.3
    scanner-dedup mechanism work for chunks indexed by docs-watcher."""
    p = FastembedProvider()
    a = p.embed_one("the quick brown fox")
    b = p.embed_one("the quick brown fox")
    assert a == b


def test_fastembed_embed_empty_input() -> None:
    p = FastembedProvider()
    assert p.embed([]) == []


# ---------------------------------------------------------------------------
# Factory + missing-import
# ---------------------------------------------------------------------------

def test_get_provider_returns_fastembed_instance() -> None:
    p = get_provider("fastembed")
    assert isinstance(p, FastembedProvider)


def test_fastembed_missing_import_raises_with_install_hint(monkeypatch) -> None:
    """If fastembed isn't installed, instantiation must raise ImportError
    with a clear install hint — not a cryptic ModuleNotFoundError. Hides
    the fastembed module from sys.modules + sys.meta_path."""
    # Force the import inside __init__ to fail by injecting None into
    # sys.modules — Python's import machinery treats None as "marked failed".
    monkeypatch.setitem(sys.modules, "fastembed", None)
    with pytest.raises(ImportError) as exc_info:
        FastembedProvider()
    # Hint must mention how to install
    assert "pip install" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# storage.peek_embedding_dimension
# ---------------------------------------------------------------------------

def test_peek_embedding_dimension_empty_db(tmp_path) -> None:
    """Fresh DB with no embeddings yet -> None."""
    st = Storage(str(tmp_path / "wevex.db"))
    try:
        assert st.peek_embedding_dimension() is None
    finally:
        # Storage doesn't expose a close() universally; rely on GC.
        del st


def test_peek_embedding_dimension_returns_stored_dim(tmp_path) -> None:
    """Fragment with a known-dim embedding -> peek returns that dim."""
    import struct

    from wevex.models import FragmentCreate, IdentityCreate, ScopeCreate

    st = Storage(str(tmp_path / "wevex.db"))
    ident = st.get_or_create_identity(
        IdentityCreate(handle="user:peek-test", type="user", name="peek-test"),
    )
    scope = st.create_scope(
        ScopeCreate(handle="project:peek", type="project", name="peek", owner_id=ident.id),
    )

    # Create a fragment, then write a 384-byte (= 96 float32) embedding by hand.
    # Using struct directly avoids requiring numpy in the test.
    frag = st.create_fragment(FragmentCreate(
        type="fact", content="peek probe",
        scope_id=scope.id, owner_id=ident.id,
    ))
    fake_dim = 96
    fake_bytes = struct.pack(f"{fake_dim}f", *(0.0 for _ in range(fake_dim)))
    st._conn.execute(
        "UPDATE fragments SET content_embedding = ? WHERE id = ?",
        (fake_bytes, frag.id),
    )
    assert st.peek_embedding_dimension() == fake_dim
