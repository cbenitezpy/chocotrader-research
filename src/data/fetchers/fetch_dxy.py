"""Fetch DXY (DTWEXBGS - Broad Dollar Index) histórico desde FRED.

Usage:
    python -m src.data.fetchers.fetch_dxy

Output:
    research/v6/data/external/dxy_daily.parquet
        columns:
            date    (date, business day)
            dxy     (float)
        index: date ascending

Notes:
    - FRED DTWEXBGS = "Nominal Broad U.S. Dollar Index". Daily, business days only.
    - Pre-registration §2 H5 references "DXY" — uso DTWEXBGS (broad) que es el de
      uso institucional. Si quisiéramos el DXY clásico de ICE, sería DX-Y.NYB en
      Yahoo, pero FRED es más confiable como fuente histórica.
    - Backup secundario: DTWEXAFEGS (Advanced Foreign Economies).
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

SERIES_ID = "DTWEXBGS"
FRED_URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}"
OUTPUT = Path(__file__).resolve().parents[3] / "data" / "external" / "dxy_daily.parquet"
REQUEST_TIMEOUT_S = 30


def fetch_dxy() -> pd.DataFrame:
    """Bajar serie completa de FRED."""
    resp = requests.get(FRED_URL, timeout=REQUEST_TIMEOUT_S)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    df.columns = ["date", "dxy"]
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.normalize()
    # FRED uses "." for missing values
    df["dxy"] = pd.to_numeric(df["dxy"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def main() -> int:
    print(f"[dxy] fetching {SERIES_ID} from FRED ...", flush=True)
    df = fetch_dxy()

    nulls = df["dxy"].isna().sum()
    df_clean = df.dropna(subset=["dxy"]).reset_index(drop=True)
    print(f"[dxy] rows raw={len(df)}, with values={len(df_clean)}, nulls/holidays={nulls}")
    print(f"[dxy] earliest={df_clean['date'].iloc[0].isoformat()}")
    print(f"[dxy] latest  ={df_clean['date'].iloc[-1].isoformat()}")
    print(f"[dxy] range   ={df_clean['dxy'].min():.2f} – {df_clean['dxy'].max():.2f}")

    # Sanity: must cover pre-registered range 2018-01-01 to today
    earliest = df_clean["date"].iloc[0]
    if earliest > pd.Timestamp("2018-01-01", tz="UTC"):
        print(f"[dxy] WARNING: earliest {earliest} > 2018-01-01. Coverage shorter than expected.")
    latest = df_clean["date"].iloc[-1]
    days_stale = (pd.Timestamp.now(tz="UTC").normalize() - latest).days
    if days_stale > 7:
        print(f"[dxy] WARNING: latest is {days_stale}d old. FRED may be delayed.")
    else:
        print(f"[dxy] freshness ok (latest {days_stale}d old)")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_parquet(OUTPUT, index=False, compression="snappy")
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"[dxy] wrote {OUTPUT} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
