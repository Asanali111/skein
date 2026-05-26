"""Fixtures for the bench pytest layer."""
from __future__ import annotations

import pytest

from bench.adapters.wevex_ephemeral import WevexEphemeralAdapter


@pytest.fixture
def ephemeral_adapter():
    """Fresh in-process Wevex on a tmp DB. Closed at teardown."""
    a = WevexEphemeralAdapter()
    try:
        a.ensure_scope("project:bench")
        yield a
    finally:
        a.close()
