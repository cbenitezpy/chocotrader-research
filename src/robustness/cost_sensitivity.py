"""Tier-2 robustness: cost sensitivity (reviewer critique #3).

Question: did a pessimistic cost model (0.30% round-trip) prematurely kill
strategies that would have been viable with BNB discount or maker-only fills?

We re-run the key strategies under three cost regimes, base capital $1,000:
  - baseline      : 0.10% fee + 0.05% slippage per side  (0.30% round-trip)
  - bnb_reduced   : 0.075% fee + 0.05% slippage per side (0.25% round-trip)
  - maker_optimistic: 0% fee + 0% slippage (0.00% round-trip)  <-- upper bound

The maker_optimistic regime is deliberately unrealistic (it ignores fill
uncertainty — see paper §4.5 discussion): if a strategy is still unprofitable
at zero cost, the problem is the SIGNAL, not the cost.

Usage:
    python -m src.robustness.cost_sensitivity
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest.engine import BacktestConfig, simulate, simulate_buy_and_hold
from src.backtest.metrics import compute_metrics
from src.data.loaders import load_dxy, load_fng, load_funding, load_ohlcv_4h
from src.signals._supertrend_baseline import supertrend_signal
from src.signals.h1_fg_filter import h1_fg_filter_signal
from src.signals.h3_funding_filter import h3_funding_filter_signal
from src.signals.h3_funding_standalone import h3_funding_standalone_signal
from src.signals.h5_dxy_filter import h5_dxy_filter_signal

REPORTS = Path(__file__).resolve().parents[2] / "results" / "robustness"
BASE_CAPITAL = 1000.0
START, END = "2018-02-01", "2026-04-30"

COST_REGIMES = {
    "baseline_0.30%rt":   dict(fee_per_side=0.0010, slippage_per_side=0.0005),
    "bnb_reduced_0.25%rt": dict(fee_per_side=0.00075, slippage_per_side=0.0005),
    "maker_optimistic_0%rt": dict(fee_per_side=0.0, slippage_per_side=0.0),
}


def _strategies(symbol: str):
    fng = load_fng()
    dxy = load_dxy()
    funding = load_funding(symbol.replace("_", "").lower())
    return [
        ("supertrend_baseline", lambda o: supertrend_signal(o)),
        ("h1_fg_filter", lambda o: h1_fg_filter_signal(o, fng)),
        ("h3_funding_filter", lambda o: h3_funding_filter_signal(o, funding)),
        ("h3_funding_standalone", lambda o: h3_funding_standalone_signal(o, funding)),
        ("h5_dxy_filter", lambda o: h5_dxy_filter_signal(o, dxy)),
    ]


def main(symbol: str = "BTC_USDT") -> int:
    ohlcv = load_ohlcv_4h(symbol=symbol, variant="full", start=START, end=END)
    print(f"=== Cost sensitivity — {symbol} {START}->{END} ({len(ohlcv)} bars, base ${BASE_CAPITAL:.0f}) ===\n")
    rows = []
    for regime, costs in COST_REGIMES.items():
        cfg = BacktestConfig(initial_capital=BASE_CAPITAL, **costs)
        bh = compute_metrics(simulate_buy_and_hold(ohlcv, cfg))
        print(f"--- {regime} ---  B&H BTC Sharpe={bh.sharpe:+.3f}")
        for name, fn in _strategies(symbol):
            m = compute_metrics(simulate(ohlcv, fn(ohlcv), cfg))
            delta = m.sharpe - bh.sharpe
            rows.append({
                "regime": regime, "strategy": name, "sharpe": m.sharpe,
                "delta_vs_bh": round(delta, 3), "final_equity": m.final_equity,
                "n_trades": m.n_trades,
            })
            print(f"  {name:25s} Sharpe={m.sharpe:+.3f}  Δ={delta:+.3f}  ${m.final_equity:,.0f}  ({m.n_trades} trades)")
        print()

    df = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df.to_csv(REPORTS / "cost_sensitivity.csv", index=False)

    # Key finding: does ANY strategy flip from negative to positive delta as cost falls?
    print("=== KEY FINDING ===")
    pivot = df.pivot_table(index="strategy", columns="regime", values="delta_vs_bh")
    print(pivot.to_string())
    flipped = []
    for strat in pivot.index:
        base = pivot.loc[strat, "baseline_0.30%rt"]
        free = pivot.loc[strat, "maker_optimistic_0%rt"]
        if base < 0 and free >= 0.10:
            flipped.append(strat)
    if flipped:
        print(f"\nStrategies rescued by zero cost (Δ≥+0.10): {flipped}")
    else:
        print("\nNo strategy crosses the +0.10 gate even at ZERO cost.")
        print("=> Confirms: the binding constraint is signal quality, not transaction cost.")
    print(f"\nwrote {REPORTS / 'cost_sensitivity.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
