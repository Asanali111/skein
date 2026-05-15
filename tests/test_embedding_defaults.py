"""Tests for the iter-15 embedding-provider defaults and the bm25 provider."""
from __future__ import annotations

import pytest

from skein.embeddings import (
    BM25OnlyProvider,
    EmbeddingProvider,
    GeminiEmbeddingProvider,
    HashEmbeddingProvider,
    best_available_provider_name,
    get_provider,
)


def test_bm25_provider_returns_zero_vectors() -> None:
    p = BM25OnlyProvider()
    assert p.dimension == 768
    assert p.is_real is False
    vec = p.embed_one("anything")
    assert vec == [0.0] * 768


def test_bm25_provider_handles_batches() -> None:
    p = BM25OnlyProvider()
    vecs = p.embed(["one", "two", "three"])
    assert len(vecs) == 3
    assert all(v == [0.0] * 768 for v in vecs)


def test_hash_is_not_real() -> None:
    """The legacy hash provider must report is_real=False so doctor warns."""
    assert HashEmbeddingProvider().is_real is False


def test_gemini_is_real() -> None:
    """Class attribute set even before constructor — avoids needing GEMINI_API_KEY in tests."""
    assert GeminiEmbeddingProvider.is_real is True


def test_get_provider_supports_bm25_aliases() -> None:
    for name in ("bm25", "BM25", "none", "off"):
        p = get_provider(name)
        assert isinstance(p, BM25OnlyProvider)


def test_get_provider_unknown_raises() -> None:
    with pytest.raises(ValueError):
        get_provider("magic")


def test_best_available_prefers_gemini(monkeypatch) -> None:
    """GEMINI_API_KEY + importable google-genai wins over everything else."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-just-for-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Ensure the google-genai import succeeds in this test env (it's an
    # opt-in extra; if missing, the env-key alone doesn't qualify).
    pytest.importorskip("google.genai")
    assert best_available_provider_name() == "gemini"


def test_best_available_falls_back_to_openai(monkeypatch) -> None:
    """OPENAI_API_KEY + importable openai wins when no Gemini key set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    pytest.importorskip("openai")
    assert best_available_provider_name() == "openai"


def test_best_available_defaults_to_fastembed(monkeypatch) -> None:
    """With no cloud API keys, fastembed (local) is the zero-config default."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pytest.importorskip("fastembed")
    assert best_available_provider_name() == "fastembed"


def test_best_available_falls_back_to_bm25_without_fastembed(monkeypatch) -> None:
    """If fastembed isn't installed AND no cloud keys, fall back to bm25 floor."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Hide fastembed from the import system
    import sys
    monkeypatch.setitem(sys.modules, "fastembed", None)
    assert best_available_provider_name() == "bm25"


def test_provider_base_is_not_real() -> None:
    """The abstract base must declare is_real=False so subclasses default safe."""
    assert EmbeddingProvider.is_real is False
