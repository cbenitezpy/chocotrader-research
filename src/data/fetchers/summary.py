"""Quick summary of all external datasets in research/v6/data/external/.

Usage:
    python -m src.data.fetchers.summary

Reports row counts, date ranges, key percentiles. Read-only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EXT = Path(__file__).resolve().parents[3] / "data" / "external"


def _ts_range(s: pd.Series) -> str:
    return f"{str(s.iloc[0])[:19]}  ->  {str(s.iloc[-1])[:19]}"


def main() -> None:
    if not EXT.exists():
        print(f"[summary] {EXT} does not exist. Run fetchers first.")
        return

    files = sorted(EXT.glob("*.parquet"))
    print(f"=== Summary of {len(files)} external datasets in {EXT} ===\n")
    for f in files:
        df = pd.read_parquet(f)
        print(f"--- {f.name} ({f.stat().st_size / 1024:.1f} KB, {len(df)} rows) ---")
        if "date" in df.columns:
            print(f"  span: {_ts_range(df['date'])}")
        elif "funding_time" in df.columns:
            print(f"  span: {_ts_range(df['funding_time'])}")
        # Specific summaries
        if "value" in df.columns and "classification" in df.columns:  # F&G
            print(f"  F&G: mean={df['value'].mean():.1f}  median={df['value'].median():.0f}  "
                  f"p5={df['value'].quantile(0.05):.0f}  p95={df['value'].quantile(0.95):.0f}")
            print(f"  days <= 25 (Extreme Fear bottom): {(df['value'] <= 25).sum()} "
                  f"({100 * (df['value'] <= 25).mean():.1f}%)")
        elif "dxy" in df.columns:
            print(f"  DXY: mean={df['dxy'].mean():.2f}  range=[{df['dxy'].min():.2f}, {df['dxy'].max():.2f}]")
        elif "funding_rate" in df.columns:
            symbol = df["symbol"].iloc[0] if "symbol" in df.columns else "?"
            ann_rate = df["funding_rate"].mean() * 3 * 365 * 100  # 3 fundings/day annualized
            print(f"  {symbol} funding (8h): mean={df['funding_rate'].mean()*100:.4f}%  "
                  f"p1={df['funding_rate'].quantile(0.01)*100:.4f}%  "
                  f"p99={df['funding_rate'].quantile(0.99)*100:.4f}%")
            print(f"  Annualized avg: {ann_rate:.2f}% per year (long pays short net)")
            print(f"  Events > +0.05% (8h, extreme positive): "
                  f"{(df['funding_rate'] > 0.0005).sum()} "
                  f"({100 * (df['funding_rate'] > 0.0005).mean():.1f}%)")
            print(f"  Events < -0.02% (8h, capitulation):    "
                  f"{(df['funding_rate'] < -0.0002).sum()} "
                  f"({100 * (df['funding_rate'] < -0.0002).mean():.1f}%)")
        print()


if __name__ == "__main__":
    main()
