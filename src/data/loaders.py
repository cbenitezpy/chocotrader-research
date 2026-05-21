"""Canonical OHLCV + external-series loaders.

Normalises the parquet schemas to what signal generators expect:
    OHLCV: ts (tz-aware UTC), open, high, low, close, volume

Reusable across tests and the backtest runner. Datasets live under
``data/ohlcv/`` (regenerable via ``src/data/fetch_ohlcv.py``) and
``data/external/`` (regenerable via the fetchers in ``src/data/fetchers/``).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# loaders.py lives at src/data/loaders.py → parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
OHLCV_DIR = _REPO_ROOT / "data" / "ohlcv"
EXT_DIR = _REPO_ROOT / "data" / "external"


def load_ohlcv_4h(
    symbol: str = "BTC_USDT",
    variant: str = "full",
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """Load 4h OHLCV in canonical schema.

    Args:
        symbol: pair underscore-joined (e.g. ``BTC_USDT``, ``ETH_USDT``).
        variant: parquet variant (``full``, ``train``, ``validation``, ``oos``,
                 ``recent``, ``gap_2024_2025``, ``early``).
        start: optional ISO date inclusive lower bound.
        end: optional ISO date inclusive upper bound.

    Returns:
        DataFrame with columns ``ts, open, high, low, close, volume``.
        ``ts`` is tz-aware UTC datetime64[ns].
    """
    path = OHLCV_DIR / f"{symbol}_4h_{variant}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"OHLCV file not found: {path}")
    df = pd.read_parquet(path)
    if "timestamp_utc" in df.columns:
        df["ts"] = pd.to_datetime(df["timestamp_utc"], unit="ns", utc=True)
    elif "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
    else:
        raise KeyError(f"OHLCV missing both 'ts' and 'timestamp_utc' columns: {path}")
    keep_cols = ["ts", "open", "high", "low", "close", "volume"]
    df = df[keep_cols].sort_values("ts").reset_index(drop=True)
    if start is not None:
        df = df[df["ts"] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        df = df[df["ts"] <= pd.Timestamp(end, tz="UTC")]
    return df.reset_index(drop=True)


def load_fng() -> pd.DataFrame:
    """Fear & Greed daily. Columns: date (tz-aware UTC), value (int 0-100)."""
    df = pd.read_parquet(EXT_DIR / "fng_daily.parquet")
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df[["date", "value", "classification"]].sort_values("date").reset_index(drop=True)


def load_funding(symbol: str = "btcusdt") -> pd.DataFrame:
    """Funding rate 8h. Columns: funding_time (tz-aware), funding_rate, mark_price, symbol."""
    df = pd.read_parquet(EXT_DIR / f"funding_{symbol.lower()}_8h.parquet")
    df["funding_time"] = pd.to_datetime(df["funding_time"], utc=True)
    return df.sort_values("funding_time").reset_index(drop=True)


def load_dxy() -> pd.DataFrame:
    """DXY (FRED DTWEXBGS) daily, business days only. Columns: date, dxy."""
    df = pd.read_parquet(EXT_DIR / "dxy_daily.parquet")
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.sort_values("date").reset_index(drop=True)
