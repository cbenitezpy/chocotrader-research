"""Fetch funding rate histórico de Binance USD-M perpetuals.

Usage:
    python -m src.data.fetchers.fetch_funding [SYMBOL ...]

    Defaults to BTCUSDT and ETHUSDT.

Output:
    research/v6/data/external/funding_<symbol_lower>_8h.parquet
        columns:
            funding_time   (datetime64[ns, UTC])
            funding_rate   (float, fraction NOT %)
            mark_price     (float)
            symbol         (str)
        index: funding_time ascending

Notes:
    - Binance fapi `/fapi/v1/fundingRate` returns max 1000 rows per call.
    - Funding events every 8h (~ 1095/year).
    - BTC perp launched 2019-09. ETH ~ same.
    - Rate limit: 500/5min weight per IP. Paginar con sleep mínimo es seguro.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
PAGE_SIZE = 1000  # API max
EARLIEST_MS = int(pd.Timestamp("2019-09-01", tz="UTC").timestamp() * 1000)
SLEEP_BETWEEN_PAGES_S = 0.25
REQUEST_TIMEOUT_S = 30
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "data" / "external"


def fetch_funding_pages(symbol: str) -> pd.DataFrame:
    """Bajar todo el histórico paginando hacia adelante."""
    rows: list[dict] = []
    start_ms = EARLIEST_MS
    page = 0
    while True:
        page += 1
        params = {
            "symbol": symbol,
            "startTime": start_ms,
            "limit": PAGE_SIZE,
        }
        resp = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            print(f"[funding][{symbol}] page {page}: empty, stopping")
            break
        rows.extend(batch)
        last_ms = batch[-1]["fundingTime"]
        print(f"[funding][{symbol}] page {page}: +{len(batch):>4d} rows, last={pd.Timestamp(last_ms, unit='ms', tz='UTC')}")
        if len(batch) < PAGE_SIZE:
            break
        # Next page starts 1ms after last entry to avoid dup
        start_ms = last_ms + 1
        time.sleep(SLEEP_BETWEEN_PAGES_S)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["funding_time"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True)
    # Some early rows have empty-string markPrice → coerce to NaN instead of failing.
    df["funding_rate"] = pd.to_numeric(df["fundingRate"], errors="coerce")
    df["mark_price"] = pd.to_numeric(df["markPrice"], errors="coerce")
    df = df[["funding_time", "funding_rate", "mark_price", "symbol"]]
    df = df.sort_values("funding_time").drop_duplicates(subset=["funding_time"]).reset_index(drop=True)
    return df


def main(argv: list[str]) -> int:
    symbols = argv[1:] if len(argv) > 1 else ["BTCUSDT", "ETHUSDT"]
    for symbol in symbols:
        print(f"\n=== {symbol} ===")
        df = fetch_funding_pages(symbol)
        if df.empty:
            print(f"[funding][{symbol}] NO DATA RETURNED. Skipping.")
            continue
        print(f"[funding][{symbol}] total rows={len(df)}")
        print(f"[funding][{symbol}] earliest={df['funding_time'].iloc[0]}")
        print(f"[funding][{symbol}] latest  ={df['funding_time'].iloc[-1]}")
        print(f"[funding][{symbol}] rate range: {df['funding_rate'].min():.6f} -- {df['funding_rate'].max():.6f}")
        print(f"[funding][{symbol}] rate p1/p50/p99: "
              f"{df['funding_rate'].quantile(0.01):.6f} / "
              f"{df['funding_rate'].quantile(0.5):.6f} / "
              f"{df['funding_rate'].quantile(0.99):.6f}")

        # Gap check: expected diff = 8h ± 1m
        diffs = df["funding_time"].diff().dt.total_seconds().dropna()
        expected_s = 8 * 3600
        gaps = ((diffs - expected_s).abs() > 300).sum()  # >5min off
        if gaps > 0:
            print(f"[funding][{symbol}] WARNING: {gaps} cadence anomalies (gap or burst). Forward-fill needed.")
        else:
            print(f"[funding][{symbol}] cadence OK (all diffs ≈ 8h)")

        out = OUTPUT_DIR / f"funding_{symbol.lower()}_8h.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False, compression="snappy")
        size_kb = out.stat().st_size / 1024
        print(f"[funding][{symbol}] wrote {out} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
