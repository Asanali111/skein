"""Tests for numpy helpers in embeddings.py."""
from __future__ import annotations

import numpy as np

from wevex.embeddings import cosine_similarity


def test_cosine_similarity_identical() -> None:
    """Identical vectors should have a similarity of 1.0."""
    a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    b = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert np.isclose(cosine_similarity(a, b), 1.0)


def test_cosine_similarity_orthogonal() -> None:
    """Orthogonal vectors should have a similarity of 0.0."""
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0], dtype=np.float32)
    assert np.isclose(cosine_similarity(a, b), 0.0)


def test_cosine_similarity_opposite() -> None:
    """Opposite vectors should have a similarity of -1.0."""
    a = np.array([1.0, 2.0], dtype=np.float32)
    b = np.array([-1.0, -2.0], dtype=np.float32)
    assert np.isclose(cosine_similarity(a, b), -1.0)


def test_cosine_similarity_zero_first() -> None:
    """If the first vector is all zeros, similarity should be 0.0."""
    a = np.array([0.0, 0.0], dtype=np.float32)
    b = np.array([1.0, 2.0], dtype=np.float32)
    assert cosine_similarity(a, b) == 0.0


def test_cosine_similarity_zero_second() -> None:
    """If the second vector is all zeros, similarity should be 0.0."""
    a = np.array([1.0, 2.0], dtype=np.float32)
    b = np.array([0.0, 0.0], dtype=np.float32)
    assert cosine_similarity(a, b) == 0.0


def test_cosine_similarity_both_zero() -> None:
    """If both vectors are all zeros, similarity should be 0.0."""
    a = np.array([0.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 0.0], dtype=np.float32)
    assert cosine_similarity(a, b) == 0.0
