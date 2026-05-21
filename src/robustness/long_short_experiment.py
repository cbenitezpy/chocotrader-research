"""Tier-3 experiment: long-only spot vs long/short perp (critique #1).

Does the ability to SHORT (capture bear markets as profit) add edge to the
SuperTrend trend-following signal? We compare, over the funding-available
window (2019-09 onward), base $1,000:

  - B&H BTC                         (passive benchmark)
  - SuperTrend long-only (spot)     (the paper's strategy)
  - SuperTrend long/short (perp 1x) (SELL signal opens a short; real funding)

Usage:
    python -m src.robustness.long_short_experiment [BTC_USDT|ETH_USDT]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from src.backtest.engine import BacktestConfig, simulate, simulate_buy_and_hold
from src.backtest.metrics import compute_metrics
from src.data.loaders import load_funding, load_ohlcv_4h
from src.robustness.long_short_engine import simulate_long_short
from src.signals._supertrend_baseline import supertrend_signal

REPORTS = Path(__file__).resolve().parents[2] / "results" / "robustness"
BASE_CAPITAL = 1000.0
START, END = "2019-09-10", "2026-04-30"  # funding history starts 2019-09
GATE = 1.2


def main(symbol: str = "BTC_USDT") -> int:
    cfg = BacktestConfig(initial_capital=BASE_CAPITAL)
    ohlcv = load_ohlcv_4h(symbol=symbol, variant="full", start=START, end=END)
    funding = load_funding(symbol.replace("_", "").lower())
    print(f"=== Long-only vs Long/Short — {symbol} {START}->{END} (base ${BASE_CAPITAL:.0f}) ===")
    print(f"bars={len(ohlcv)}  funding obs={len(funding)}\n")

    sig = supertrend_signal(ohlcv)

    bh = compute_metrics(simulate_buy_and_hold(ohlcv, cfg))
    lo = compute_metrics(simulate(ohlcv, sig, cfg))
    ls_res = simulate_long_short(ohlcv, sig, funding, cfg)
    ls = compute_metrics(ls_res)

    rows = [
        {"strategy": "buy_and_hold_btc", "sharpe": bh.sharpe, "maxdd": bh.max_drawdown,
         "final": bh.final_equity, "trades": bh.n_trades},
        {"strategy": "supertrend_long_only_spot", "sharpe": lo.sharpe, "maxdd": lo.max_drawdown,
         "final": lo.final_equity, "trades": lo.n_trades},
        {"strategy": "supertrend_long_short_perp", "sharpe": ls.sharpe, "maxdd": ls.max_drawdown,
         "final": ls.final_equity, "trades": ls.n_trades},
    ]
    for r in rows:
        d = r["sharpe"] - bh.sharpe
        print(f"  {r['strategy']:28s} Sharpe={r['sharpe']:+.3f}  Δ={d:+.3f}  "
              f"MaxDD={r['maxdd']*100:6.1f}%  ${r['final']:,.0f}  ({r['trades']} trades)")

    df = pd.DataFrame(rows)
    df["symbol"] = symbol
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"long_short_{symbol}.csv"
    df.to_csv(out, index=False)

    print("\n=== KEY FINDING ===")
    delta_ls_lo = ls.sharpe - lo.sharpe
    print(f"Shorting changes SuperTrend Sharpe by {delta_ls_lo:+.3f} "
          f"({lo.sharpe:+.3f} long-only → {ls.sharpe:+.3f} long/short).")
    print(f"Long/short vs B&H: Δ Sharpe {ls.sharpe - bh.sharpe:+.3f}")
    print(f"Constitutional gate (Sharpe>=1.2): long/short {'PASS' if ls.sharpe>=GATE else 'FAIL'} "
          f"({ls.sharpe:+.3f})")
    if ls.sharpe > lo.sharpe and ls.sharpe >= GATE:
        print("=> Shorting adds enough edge to clear the gate. The long-only "
              "constraint WAS the binding limitation.")
    elif ls.sharpe > lo.sharpe:
        print("=> Shorting helps but is NOT enough to clear the gate.")
    else:
        print("=> Shorting does NOT help (funding cost + short-side losses in the "
              "secular bull outweigh bear-capture gains).")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "BTC_USDT"))
