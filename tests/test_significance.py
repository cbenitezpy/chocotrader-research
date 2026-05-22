"""Sanity tests for the bootstrap significance helpers."""

from __future__ import annotations

import numpy as np

from src.robustness.significance import _moving_block_indices, _sharpe


def test_sharpe_zero_for_constant_returns():
    assert _sharpe(np.zeros(100)) == 0.0


def test_sharpe_positive_for_positive_drift():
    rng = np.random.default_rng(0)
    r = rng.normal(0.001, 0.005, size=5000)  # positive mean
    assert _sharpe(r) > 0


def test_block_indices_length_and_range():
    rng = np.random.default_rng(1)
    n = 1000
    idx = _moving_block_indices(n, block=30, rng=rng)
    assert len(idx) == n
    assert idx.min() >= 0
    assert idx.max() < n


def test_block_indices_deterministic_with_seed():
    a = _moving_block_indices(500, 30, np.random.default_rng(42))
    b = _moving_block_indices(500, 30, np.random.default_rng(42))
    assert np.array_equal(a, b)


def test_block_preserves_contiguity_within_blocks():
    """Within a block, indices are consecutive (the whole point of block bootstrap)."""
    rng = np.random.default_rng(3)
    idx = _moving_block_indices(300, block=30, rng=rng)
    # the first 30 should be consecutive
    first_block = idx[:30]
    assert np.array_equal(first_block, np.arange(first_block[0], first_block[0] + 30))
