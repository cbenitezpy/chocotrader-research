"""Smoke + correctness tests for the 6 signal generators."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.loaders import load_dxy, load_fng, load_funding, load_ohlcv_4h
from src.signals.h1_fg_filter import h1_fg_filter_signal
from src.signals.h1_fg_standalone import h1_fg_standalone_signal
from src.signals.h3_funding_filter import h3_funding_filter_signal
from src.signals.h3_funding_standalone import h3_funding_standalone_signal
from src.signals.h5_dxy_filter import h5_dxy_filter_signal
from src.signals.h5_dxy_standalone import h5_dxy_standalone_signal
from src.signals._supertrend_baseline import supertrend_signal


def _load_ohlcv_slice(start: str = "2025-01-01", n_bars: int = 1000) -> pd.DataFrame:
    try:
        df = load_ohlcv_4h(symbol="BTC_USDT", variant="full", start=start)
    except FileNotFoundError as exc:
        pytest.skip(str(exc))
    return df.head(n_bars).reset_index(drop=True)


def _check_signal_contract(s: pd.Series, ohlcv: pd.DataFrame) -> None:
    """Common contract: same index, values in {-1, 0, 1}, int dtype."""
    assert len(s) == len(ohlcv), f"length mismatch: {len(s)} vs {len(ohlcv)}"
    assert s.index.equals(ohlcv.index), "index mismatch"
    assert set(s.unique()).issubset({-1, 0, 1}), f"unexpected values: {set(s.unique())}"
    assert s.dtype.kind == "i", f"expected integer dtype, got {s.dtype}"


# ----------------------------- baseline


def test_supertrend_baseline_contract():
    ohlcv = _load_ohlcv_slice()
    s = supertrend_signal(ohlcv)
    _check_signal_contract(s, ohlcv)
    # Algunas señales deben aparecer en 1000 bars de BTC 4h.
    assert (s != 0).sum() > 0


# ----------------------------- H1


def test_h1_fg_filter_subset_of_supertrend():
    """H1-filter solo CANCELA BUYs de SuperTrend, nunca agrega ni cambia
    SELLs. Por tanto cada bar:
    - filter[t] == 1 → base[t] == 1 (no agregamos BUYs nuevos)
    - filter[t] == -1 → base[t] == -1 (SELLs intactos)
    - filter[t] == 0 → base[t] ∈ {0, 1} (cancelamos BUYs o ya era HOLD)
    """
    ohlcv = _load_ohlcv_slice()
    fng = load_fng()
    base = supertrend_signal(ohlcv)
    filt = h1_fg_filter_signal(ohlcv, fng)
    _check_signal_contract(filt, ohlcv)
    # Invariantes:
    assert ((filt == 1) & (base != 1)).sum() == 0, "filter introduces BUYs"
    assert ((filt == -1) & (base != -1)).sum() == 0, "filter introduces SELLs"
    # Algunos BUYs deben quedar (no debe matar todo)
    assert (filt == 1).sum() <= (base == 1).sum()


def test_h1_fg_standalone_emits_only_on_cross():
    ohlcv = _load_ohlcv_slice()
    fng = load_fng()
    s = h1_fg_standalone_signal(ohlcv, fng)
    _check_signal_contract(s, ohlcv)
    # Cross-based signals deben ser raros pero existir en 1000 bars
    n_nz = (s != 0).sum()
    assert 0 < n_nz < 200, f"unexpected n signals: {n_nz}"


def test_h1_standalone_bad_thresholds():
    ohlcv = _load_ohlcv_slice(n_bars=100)
    fng = load_fng()
    with pytest.raises(ValueError):
        h1_fg_standalone_signal(ohlcv, fng, buy_threshold=80, sell_threshold=20)


# ----------------------------- H3


def test_h3_filter_contract():
    ohlcv = _load_ohlcv_slice()
    funding = load_funding("btcusdt")
    s = h3_funding_filter_signal(ohlcv, funding)
    _check_signal_contract(s, ohlcv)


def test_h3_standalone_contract():
    ohlcv = _load_ohlcv_slice()
    funding = load_funding("btcusdt")
    s = h3_funding_standalone_signal(ohlcv, funding)
    _check_signal_contract(s, ohlcv)


def test_h3_standalone_bad_thresholds():
    ohlcv = _load_ohlcv_slice(n_bars=100)
    funding = load_funding("btcusdt")
    with pytest.raises(ValueError):
        h3_funding_standalone_signal(ohlcv, funding, buy_threshold=0.01, sell_threshold=-0.01)


# ----------------------------- H5


def test_h5_filter_contract():
    ohlcv = _load_ohlcv_slice()
    dxy = load_dxy()
    s = h5_dxy_filter_signal(ohlcv, dxy)
    _check_signal_contract(s, ohlcv)


def test_h5_standalone_contract():
    ohlcv = _load_ohlcv_slice()
    dxy = load_dxy()
    s = h5_dxy_standalone_signal(ohlcv, dxy)
    _check_signal_contract(s, ohlcv)
