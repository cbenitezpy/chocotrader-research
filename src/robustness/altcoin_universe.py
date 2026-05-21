"""Tier-3 research: mid-cap altcoin universe (reviewer critique #4).

Question: does the edge live in less-efficient mid-cap altcoins rather than
the hyper-arbitraged majors?

We run SuperTrend on a broader universe of liquid mid-caps and compare each to
its own Buy-and-Hold, base capital $1,000, over each pair's full history.

CRITICAL HONESTY (this is the whole point of the critique):
    This test suffers SURVIVORSHIP BIAS. Every pair here is a survivor that is
    still listed on Binance in 2026. The hundreds of mid-caps that were
    delisted, died, or rug-pulled are ABSENT. Binance's public klines API does
    not serve delisted symbols, so a bias-free point-in-time universe is not
    obtainable from this data source. Therefore: any positive result here is an
    UPPER BOUND that almost certainly overstates the real, tradable edge. A
    negative result, by contrast, is robust (survivors are the best case).

Usage:
    python -m src.robustness.altcoin_universe
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest.engine import BacktestConfig, simulate, simulate_buy_and_hold
from src.backtest.metrics import compute_metrics
from src.data.loaders import load_ohlcv_4h
from src.signals._supertrend_baseline import supertrend_signal

REPORTS = Path(__file__).resolve().parents[2] / "results" / "robustness"
BASE_CAPITAL = 1000.0
UNIVERSE = ["ADA_USDT", "AVAX_USDT", "LINK_USDT", "DOT_USDT", "ATOM_USDT", "LTC_USDT", "DOGE_USDT"]
GATE = 1.2  # constitutional Sharpe gate


def main() -> int:
    cfg = BacktestConfig(initial_capital=BASE_CAPITAL,
                         slippage_per_side=0.0010)  # alts: wider spreads → 0.10%/side
    rows = []
    print(f"=== Mid-cap altcoin universe — SuperTrend vs B&H (base ${BASE_CAPITAL:.0f}) ===")
    print("NOTE: survivors only. Delisted/dead pairs absent → positive results are an UPPER BOUND.\n")
    print(f"{'pair':>10} | {'bars':>6} {'first':>11} | {'BH Sharpe':>9} {'BH $':>9} | "
          f"{'ST Sharpe':>9} {'ST MaxDD':>8} {'ST $':>9} {'trades':>6} | {'ΔvsBH':>7} {'gate':>5}")
    print("-" * 110)
    for pair in UNIVERSE:
        try:
            ohlcv = load_ohlcv_4h(symbol=pair, variant="full")
        except FileNotFoundError:
            print(f"{pair:>10} | NOT FETCHED (run: python -m src.data.fetch_ohlcv {pair})")
            continue
        if ohlcv.empty or len(ohlcv) < 500:
            print(f"{pair:>10} | insufficient data")
            continue
        bh = compute_metrics(simulate_buy_and_hold(ohlcv, cfg))
        st = compute_metrics(simulate(ohlcv, supertrend_signal(ohlcv), cfg))
        delta = st.sharpe - bh.sharpe
        first = str(ohlcv["ts"].iloc[0])[:10]
        passes = "PASS" if st.sharpe >= GATE else "fail"
        rows.append({
            "pair": pair, "bars": len(ohlcv), "first": first,
            "bh_sharpe": bh.sharpe, "bh_final": bh.final_equity,
            "st_sharpe": st.sharpe, "st_maxdd": st.max_drawdown,
            "st_final": st.final_equity, "st_trades": st.n_trades,
            "delta_sharpe": round(delta, 3), "gate_pass": st.sharpe >= GATE,
        })
        print(f"{pair:>10} | {len(ohlcv):>6} {first:>11} | {bh.sharpe:>+9.3f} ${bh.final_equity:>7,.0f} | "
              f"{st.sharpe:>+9.3f} {st.max_drawdown*100:>7.1f}% ${st.final_equity:>7,.0f} {st.n_trades:>6} | "
              f"{delta:>+7.3f} {passes:>5}")

    df = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df.to_csv(REPORTS / "altcoin_universe.csv", index=False)

    print("\n=== KEY FINDING ===")
    n_pass = int(df["gate_pass"].sum()) if not df.empty else 0
    n_beat = int((df["delta_sharpe"] > 0).sum()) if not df.empty else 0
    print(f"SuperTrend passes the Sharpe>=1.2 gate in {n_pass}/{len(df)} survivor pairs.")
    print(f"SuperTrend beats own B&H on Sharpe in {n_beat}/{len(df)} survivor pairs.")
    print(f"Mean ST Sharpe across survivors: {df['st_sharpe'].mean():+.3f}")
    print("REMINDER: survivors only. The real (survivorship-free) figure is LOWER.")
    print("If even the survivor upper-bound fails the gate, the conclusion is robust.")
    print(f"\nwrote {REPORTS / 'altcoin_universe.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
