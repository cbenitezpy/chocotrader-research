"""Tier-2 robustness: daily timeframe (reviewer critique #2).

Question: is 4h a "no man's land" — too slow for microstructure, too fast for
macro-trend? We resample 4h -> 1d (deterministically) and re-run SuperTrend to
see whether a slower timeframe better captures the macro-trend.

Resample rule (standard OHLCV):
    open = first, high = max, low = min, close = last, volume = sum

Usage:
    python -m src.robustness.daily_timeframe
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
START, END = "2018-02-01", "2026-04-30"


def resample_4h_to_1d(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Deterministic 4h -> 1d resample. Keeps the canonical schema."""
    df = ohlcv.copy()
    df = df.set_index(pd.DatetimeIndex(df["ts"]))
    agg = df.resample("1D").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna(subset=["open", "close"])
    agg = agg.reset_index().rename(columns={"index": "ts"})
    agg["ts"] = pd.to_datetime(agg["ts"], utc=True)
    return agg


def main(symbol: str = "BTC_USDT") -> int:
    cfg = BacktestConfig(initial_capital=BASE_CAPITAL)
    ohlcv_4h = load_ohlcv_4h(symbol=symbol, variant="full", start=START, end=END)
    ohlcv_1d = resample_4h_to_1d(ohlcv_4h)
    print(f"=== Daily vs 4h — {symbol} {START}->{END} (base ${BASE_CAPITAL:.0f}) ===")
    print(f"4h bars: {len(ohlcv_4h)}   |   1d bars: {len(ohlcv_1d)}\n")

    rows = []
    bh = compute_metrics(simulate_buy_and_hold(ohlcv_4h, cfg))
    rows.append({"variant": "buy_and_hold_btc", **_m(bh)})
    print(f"B&H BTC                Sharpe={bh.sharpe:+.3f}  MaxDD={bh.max_drawdown*100:.1f}%  ${bh.final_equity:,.0f}")

    st4 = compute_metrics(simulate(ohlcv_4h, supertrend_signal(ohlcv_4h), cfg))
    rows.append({"variant": "supertrend_4h", **_m(st4)})
    print(f"SuperTrend 4h          Sharpe={st4.sharpe:+.3f}  MaxDD={st4.max_drawdown*100:.1f}%  ${st4.final_equity:,.0f}  ({st4.n_trades} trades)")

    # On daily, annualization factor changes (365 bars/yr instead of 365*6).
    cfg_daily = BacktestConfig(initial_capital=BASE_CAPITAL, annualization_factor=365.25)
    st1 = compute_metrics(simulate(ohlcv_1d, supertrend_signal(ohlcv_1d), cfg_daily))
    rows.append({"variant": "supertrend_1d", **_m(st1)})
    print(f"SuperTrend 1d          Sharpe={st1.sharpe:+.3f}  MaxDD={st1.max_drawdown*100:.1f}%  ${st1.final_equity:,.0f}  ({st1.n_trades} trades)")

    df = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df.to_csv(REPORTS / "daily_timeframe.csv", index=False)

    print("\n=== KEY FINDING ===")
    print(f"Δ Sharpe vs B&H — 4h: {st4.sharpe - bh.sharpe:+.3f}   1d: {st1.sharpe - bh.sharpe:+.3f}")
    if st1.sharpe > st4.sharpe:
        print("Daily improves risk-adjusted return vs 4h, but check the gate:")
    else:
        print("Daily does NOT beat 4h on Sharpe.")
    print(f"Constitutional gate (Sharpe>=1.2): 1d {'PASS' if st1.sharpe>=1.2 else 'FAIL'} "
          f"({st1.sharpe:+.3f}), 4h {'PASS' if st4.sharpe>=1.2 else 'FAIL'} ({st4.sharpe:+.3f})")
    print(f"\nwrote {REPORTS / 'daily_timeframe.csv'}")
    return 0


def _m(m) -> dict:
    return {"sharpe": m.sharpe, "max_drawdown": m.max_drawdown,
            "final_equity": m.final_equity, "n_trades": m.n_trades}


if __name__ == "__main__":
    raise SystemExit(main())
