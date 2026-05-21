"""Fetch 4h OHLCV klines from Binance public API.

We do NOT redistribute exchange data; this script regenerates the exact
datasets used in the study from Binance's public klines endpoint.

Usage:
    python -m src.data.fetch_ohlcv [SYMBOL ...]

    SYMBOL is underscore-joined, e.g. BTC_USDT ETH_USDT.
    Defaults to BTC_USDT and ETH_USDT.

Output:
    data/ohlcv/<SYMBOL>_4h_full.parquet
        columns: timestamp_utc (int64 ns), open, high, low, close, volume,
                 quote_volume, trades_count
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.binance.com/api/v3/klines"
INTERVAL = "4h"
PAGE_SIZE = 1000  # Binance max
# 2017-08-01 — earliest broadly-available spot history for the majors.
START_MS = int(pd.Timestamp("2017-08-01", tz="UTC").timestamp() * 1000)
SLEEP_BETWEEN_PAGES_S = 0.25
REQUEST_TIMEOUT_S = 30
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "ohlcv"


def _to_binance_symbol(symbol: str) -> str:
    """BTC_USDT -> BTCUSDT."""
    return symbol.replace("_", "").replace("/", "").upper()


def fetch_klines(symbol: str) -> pd.DataFrame:
    """Page forward through Binance klines for the full available history."""
    binance_symbol = _to_binance_symbol(symbol)
    rows: list[list] = []
    start_ms = START_MS
    page = 0
    while True:
        page += 1
        params = {
            "symbol": binance_symbol,
            "interval": INTERVAL,
            "startTime": start_ms,
            "limit": PAGE_SIZE,
        }
        resp = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        last_open_ms = batch[-1][0]
        print(
            f"[ohlcv][{symbol}] page {page}: +{len(batch):>4d} rows, "
            f"last={pd.Timestamp(last_open_ms, unit='ms', tz='UTC')}"
        )
        if len(batch) < PAGE_SIZE:
            break
        start_ms = last_open_ms + 1
        time.sleep(SLEEP_BETWEEN_PAGES_S)

    if not rows:
        return pd.DataFrame()

    # Binance kline columns:
    # [openTime, open, high, low, close, volume, closeTime, quoteVolume,
    #  trades, takerBuyBase, takerBuyQuote, ignore]
    df = pd.DataFrame(
        rows,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades_count",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ],
    )
    # openTime is ms → store as int64 ns to match the study's schema.
    df["timestamp_utc"] = (df["open_time"].astype("int64") * 1_000_000).astype("int64")
    for col in ("open", "high", "low", "close", "volume", "quote_volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["trades_count"] = pd.to_numeric(df["trades_count"], errors="coerce").fillna(0).astype("int64")
    out = df[
        ["timestamp_utc", "open", "high", "low", "close", "volume", "quote_volume", "trades_count"]
    ].copy()
    out = out.drop_duplicates(subset=["timestamp_utc"]).sort_values("timestamp_utc").reset_index(drop=True)
    return out


def main(argv: list[str]) -> int:
    symbols = argv[1:] if len(argv) > 1 else ["BTC_USDT", "ETH_USDT"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for symbol in symbols:
        print(f"\n=== {symbol} ===")
        df = fetch_klines(symbol)
        if df.empty:
            print(f"[ohlcv][{symbol}] NO DATA. Skipping.")
            continue
        first = pd.Timestamp(df["timestamp_utc"].iloc[0], unit="ns", tz="UTC")
        last = pd.Timestamp(df["timestamp_utc"].iloc[-1], unit="ns", tz="UTC")
        print(f"[ohlcv][{symbol}] rows={len(df)}  {first}  ->  {last}")
        out = OUTPUT_DIR / f"{symbol}_4h_full.parquet"
        df.to_parquet(out, index=False, compression="snappy")
        print(f"[ohlcv][{symbol}] wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
