"""Fetch Fear & Greed Index histórico desde alternative.me.

Usage:
    python -m src.data.fetchers.fetch_fng

Output:
    research/v6/data/external/fng_daily.parquet
        columns:
            date          (date, UTC, day boundary)
            value         (int 0-100)
            classification (str: Extreme Fear / Fear / Neutral / Greed / Extreme Greed)
            timestamp     (int64 unix seconds, original API value)
        index: date ascending
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.alternative.me/fng/"
OUTPUT = Path(__file__).resolve().parents[3] / "data" / "external" / "fng_daily.parquet"
REQUEST_TIMEOUT_S = 30


def fetch_fng_all() -> pd.DataFrame:
    """Bajar histórico completo (limit=0 = all)."""
    resp = requests.get(
        API_URL,
        params={"limit": 0, "format": "json"},
        timeout=REQUEST_TIMEOUT_S,
    )
    resp.raise_for_status()
    raw = resp.json()
    rows = raw["data"]
    df = pd.DataFrame(rows)
    df["timestamp"] = df["timestamp"].astype("int64")
    df["value"] = df["value"].astype("int64")
    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.normalize()
    df = df.rename(columns={"value_classification": "classification"})
    df = df[["date", "value", "classification", "timestamp"]]
    df = df.sort_values("date").reset_index(drop=True)
    df = df.drop_duplicates(subset=["date"], keep="last")
    return df


def main() -> int:
    print(f"[fng] fetching from {API_URL} ...", flush=True)
    df = fetch_fng_all()
    print(f"[fng] rows={len(df)}")
    print(f"[fng] earliest={df['date'].iloc[0].isoformat()}")
    print(f"[fng] latest  ={df['date'].iloc[-1].isoformat()}")

    # Sanity checks
    assert df["value"].between(0, 100).all(), "F&G value out of [0,100] range"
    assert df["date"].is_monotonic_increasing, "dates not monotonic increasing"
    gaps = (df["date"].diff().dt.days > 1).sum()
    if gaps > 0:
        print(f"[fng] WARNING: {gaps} gap days detected (forward-fill needed downstream)")
    else:
        print("[fng] no gaps detected (continuous daily coverage)")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT, index=False, compression="snappy")
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"[fng] wrote {OUTPUT} ({size_kb:.1f} KB)")

    # Bucketing summary
    counts = df["classification"].value_counts()
    print("[fng] classification distribution:")
    for k, v in counts.items():
        print(f"      {k:>15s}: {v:>5d}  ({100 * v / len(df):.1f}%)")

    extreme_fear = (df["value"] <= 25).sum()
    print(f"[fng] days with F&G ≤ 25 (Extreme Fear / Fear bottom): {extreme_fear} ({100*extreme_fear/len(df):.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
