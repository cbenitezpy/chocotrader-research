"""Tests for research/v6/signals/_alignment.py — no look-ahead guarantees."""

from __future__ import annotations

import pandas as pd
import pytest

from src.signals._alignment import (
    align_daily_to_4h,
    align_dxy_to_4h,
    align_funding_to_4h,
)


def _make_4h_ohlcv(start: str, n: int) -> pd.DataFrame:
    """Tiny synthetic OHLCV at 4h cadence."""
    ts = pd.date_range(start=start, periods=n, freq="4h", tz="UTC")
    return pd.DataFrame(
        {
            "ts": ts,
            "open": range(n),
            "high": range(n),
            "low": range(n),
            "close": range(n),
            "volume": [1.0] * n,
        }
    )


# ---------------------------------------------------------------- F&G daily


def test_daily_alignment_no_lookahead_within_same_day():
    """F&G value of day D (timestamp D 00:00) must NOT appear in a 4h bar
    whose cutoff (close - 4h) is exactly D 00:00.

    Day D F&G is timestamped 00:00:00 UTC of D. With lag_hours=4, the bar
    whose CUTOFF lands exactly at D 00:00 must still read D-1's value
    (strict-backward excludes exact match).
    """
    fng = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03"], utc=True
            ),
            "value": [10, 20, 30],
        }
    )
    # 4 bars opening at 20:00 day1, 00:00 day2, 04:00 day2, 08:00 day2.
    # Bar closes:                  00:00 day2, 04:00 day2, 08:00 day2, 12:00 day2.
    # Cutoffs (close - 4h):        20:00 day1, 00:00 day2, 04:00 day2, 08:00 day2.
    # Expected published <cutoff: day1 only, day1 only (strict), day1+day2, day1+day2.
    # So: [10, 10, 20, 20].
    ohlcv = _make_4h_ohlcv("2025-01-01 20:00", 4)
    result = align_daily_to_4h(fng, ohlcv, value_col="value")
    assert list(result) == [10, 10, 20, 20]


def test_daily_alignment_strict_inequality():
    """Cutoff exactly equal to publication timestamp must be EXCLUDED."""
    fng = pd.DataFrame(
        {"date": pd.to_datetime(["2025-01-02 00:00:00"], utc=True), "value": [99]}
    )
    # Bar closes 2025-01-02 04:00, cutoff = 00:00 → equality must be rejected.
    ohlcv = _make_4h_ohlcv("2025-01-02 00:00", 1)
    result = align_daily_to_4h(fng, ohlcv, value_col="value")
    # cutoff = 00:00, daily date = 00:00 → strict backward excludes → NaN
    assert pd.isna(result.iloc[0])


def test_daily_alignment_determinism():
    """Two identical calls produce identical output."""
    fng = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-06-01", "2025-01-01"], utc=True), "value": [1, 2, 3]}
    )
    ohlcv = _make_4h_ohlcv("2024-12-31 04:00", 5)
    r1 = align_daily_to_4h(fng, ohlcv, value_col="value")
    r2 = align_daily_to_4h(fng, ohlcv, value_col="value")
    pd.testing.assert_series_equal(r1, r2)


def test_daily_alignment_requires_sorted_input():
    fng = pd.DataFrame(
        {"date": pd.to_datetime(["2025-01-02", "2025-01-01"], utc=True), "value": [2, 1]}
    )
    ohlcv = _make_4h_ohlcv("2025-01-03 00:00", 1)
    with pytest.raises(ValueError, match="monotonic"):
        align_daily_to_4h(fng, ohlcv, value_col="value")


# ---------------------------------------------------------------- Funding 8h


def test_funding_last_no_lookahead():
    """Funding settled at T cannot be used for bar that closes AT T."""
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(
                ["2025-01-01 00:00", "2025-01-01 08:00", "2025-01-01 16:00"], utc=True
            ),
            "funding_rate": [0.0001, 0.0002, 0.0003],
        }
    )
    # Bar closes at 08:00 → strict-backward → must pick 00:00 (0.0001), NOT 08:00.
    ohlcv = _make_4h_ohlcv("2025-01-01 04:00", 1)
    r = align_funding_to_4h(funding, ohlcv, agg="last")
    assert r.iloc[0] == 0.0001


def test_funding_avg_window():
    """avg over last 24h excludes events at or after close."""
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(
                [
                    "2025-01-01 00:00",  # in window? yes (close-24h = 12-31 16:00)
                    "2025-01-01 08:00",  # yes
                    "2025-01-01 16:00",  # boundary - this IS the close, excluded
                ],
                utc=True,
            ),
            "funding_rate": [0.001, 0.002, 0.999],
        }
    )
    # Bar opens 12:00, closes 16:00. window = (16:00 - 24h, 16:00) = (-1 day 16:00, 16:00)
    ohlcv = _make_4h_ohlcv("2025-01-01 12:00", 1)
    r = align_funding_to_4h(funding, ohlcv, agg="avg", window_hours=24)
    # Should average 0.001 and 0.002 → 0.0015
    assert abs(r.iloc[0] - 0.0015) < 1e-9


def test_funding_invalid_agg():
    funding = pd.DataFrame(
        {"funding_time": pd.to_datetime(["2025-01-01"], utc=True), "funding_rate": [0.0]}
    )
    ohlcv = _make_4h_ohlcv("2025-01-02", 1)
    with pytest.raises(ValueError, match="agg"):
        align_funding_to_4h(funding, ohlcv, agg="foo")


# ---------------------------------------------------------------- DXY


def test_dxy_uses_lag_days():
    """DXY with default lag_days=2 must skip values too recent."""
    dxy = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"], utc=True
            ),
            "dxy": [100.0, 101.0, 102.0, 103.0],
        }
    )
    # Bar closes 2025-01-04 04:00 → cutoff = 2025-01-02 04:00 → strict backward
    # → must see 2025-01-02 (101.0).
    ohlcv = _make_4h_ohlcv("2025-01-04 00:00", 1)
    r = align_dxy_to_4h(dxy, ohlcv)
    assert r.iloc[0] == 101.0


def test_dxy_skips_nan_holidays():
    """Holiday rows with NaN dxy are dropped — alignment uses last NON-NULL date."""
    dxy = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"], utc=True),
            "dxy": [100.0, None, 102.0],
        }
    )
    # Bar opens 2025-01-03 20:00 → closes 2025-01-04 00:00 → cutoff = 2025-01-02 00:00.
    # Strict-back from cutoff 2025-01-02 00:00:
    #   dropna leaves [2025-01-01 (100), 2025-01-03 (102)].
    #   Both must be STRICTLY before cutoff:
    #     2025-01-01 < 2025-01-02 00:00 ✓
    #     2025-01-03 < 2025-01-02 00:00 ✗
    #   → picks 2025-01-01 → 100.0.
    ohlcv = _make_4h_ohlcv("2025-01-03 20:00", 1)
    r = align_dxy_to_4h(dxy, ohlcv)
    assert r.iloc[0] == 100.0


# ---------------------------------------------------------------- Real data smoke


def test_real_data_smoke_fng(tmp_path_factory):
    """Smoke test against the real parquet to confirm no look-ahead on volume."""
    import pathlib

    pkg_root = pathlib.Path(__file__).resolve().parents[1]
    fng_path = pkg_root / "data" / "external" / "fng_daily.parquet"
    if not fng_path.exists():
        pytest.skip(f"{fng_path} not fetched yet")
    fng = pd.read_parquet(fng_path)
    fng["date"] = pd.to_datetime(fng["date"], utc=True)

    ts = pd.date_range("2025-06-01", periods=1000, freq="4h", tz="UTC")
    ohlcv = pd.DataFrame({"ts": ts})
    r = align_daily_to_4h(fng, ohlcv, value_col="value")
    # Sanity: F&G values in [0, 100] (or NaN at start)
    assert r.dropna().between(0, 100).all()
    # No leak: first non-NaN bar must use a F&G publication strictly before bar close - lag.
    # Pick the first non-null row and verify by hand.
    first_idx = r.first_valid_index()
    bar_close = pd.to_datetime(ohlcv["ts"].iloc[first_idx], utc=True) + pd.Timedelta(hours=4)
    cutoff = bar_close - pd.Timedelta(hours=4)
    # The chosen value comes from a date STRICTLY before cutoff.
    candidates = fng[fng["date"] < cutoff]
    assert not candidates.empty
    assert r.iloc[first_idx] == candidates.iloc[-1]["value"]
