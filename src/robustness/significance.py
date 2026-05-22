"""Statistical significance of the active-vs-passive Sharpe gap.

The main paper shows SuperTrend BTC (Sharpe 0.977) edges out Buy-and-Hold
(0.809), but never tests whether that gap is distinguishable from noise. This
module answers that with a **moving-block bootstrap** (Politis & Romano style),
which preserves the autocorrelation and volatility clustering of financial
returns — an i.i.d. bootstrap would understate the Sharpe's sampling error.

We report, base $1,000, full period:
  - 95% CI for each strategy's annualized Sharpe.
  - 95% CI for the PAIRED difference (SuperTrend - B&H), resampling the same
    time blocks for both series so cross-strategy correlation is preserved.
  - A bootstrap p-value for H0: Sharpe_active <= Sharpe_passive.

If the difference CI includes 0, the active "edge" is not statistically
significant — which would strengthen, not weaken, the paper's conclusion.

Usage:
    python -m src.robustness.significance
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestConfig, simulate, simulate_buy_and_hold
from src.data.loaders import load_ohlcv_4h
from src.signals._supertrend_baseline import supertrend_signal

REPORTS = Path(__file__).resolve().parents[2] / "results" / "robustness"
BASE_CAPITAL = 1000.0
START, END = "2018-02-01", "2026-04-30"
ANNUALIZATION = 365.25 * 6   # 4h bars per year
BLOCK_SIZE = 30              # ~5 trading days at 4h; preserves short-run autocorr
N_BOOT = 5000
SEED = 7


def _returns(equity: pd.Series) -> np.ndarray:
    eq = equity.to_numpy(dtype=float)
    r = np.diff(eq) / eq[:-1]
    return r[np.isfinite(r)]


def _sharpe(returns: np.ndarray) -> float:
    if returns.size < 2 or returns.std(ddof=1) == 0:
        return 0.0
    return float(returns.mean() / returns.std(ddof=1) * np.sqrt(ANNUALIZATION))


def _moving_block_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Indices for one moving-block bootstrap resample of length ~n."""
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])
    return idx[:n]


def main(symbol: str = "BTC_USDT") -> int:
    rng = np.random.default_rng(SEED)
    cfg = BacktestConfig(initial_capital=BASE_CAPITAL)
    ohlcv = load_ohlcv_4h(symbol=symbol, variant="full", start=START, end=END)

    bh_eq = simulate_buy_and_hold(ohlcv, cfg).equity_curve
    st_eq = simulate(ohlcv, supertrend_signal(ohlcv), cfg).equity_curve
    r_bh, r_st = _returns(bh_eq), _returns(st_eq)
    # align lengths (both derive from the same bars)
    m = min(len(r_bh), len(r_st))
    r_bh, r_st = r_bh[:m], r_st[:m]

    obs_bh, obs_st = _sharpe(r_bh), _sharpe(r_st)
    obs_diff = obs_st - obs_bh
    print(f"=== Bootstrap significance — {symbol} {START}->{END} ===")
    print(f"bars={m}  block={BLOCK_SIZE}  resamples={N_BOOT}  (base ${BASE_CAPITAL:.0f})\n")
    print(f"Observed Sharpe: B&H={obs_bh:+.3f}  SuperTrend={obs_st:+.3f}  diff={obs_diff:+.3f}\n")

    boot_bh = np.empty(N_BOOT)
    boot_st = np.empty(N_BOOT)
    boot_diff = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = _moving_block_indices(m, BLOCK_SIZE, rng)  # paired indices
        boot_bh[b] = _sharpe(r_bh[idx])
        boot_st[b] = _sharpe(r_st[idx])
        boot_diff[b] = boot_st[b] - boot_bh[b]

    def ci(a: np.ndarray) -> tuple[float, float]:
        return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))

    bh_lo, bh_hi = ci(boot_bh)
    st_lo, st_hi = ci(boot_st)
    d_lo, d_hi = ci(boot_diff)
    # one-sided bootstrap p-value for H0: active <= passive  (diff <= 0)
    p_value = float(np.mean(boot_diff <= 0.0))

    print("95% bootstrap confidence intervals (annualized Sharpe):")
    print(f"  B&H BTC      : {obs_bh:+.3f}  CI [{bh_lo:+.3f}, {bh_hi:+.3f}]")
    print(f"  SuperTrend   : {obs_st:+.3f}  CI [{st_lo:+.3f}, {st_hi:+.3f}]")
    print(f"  Difference   : {obs_diff:+.3f}  CI [{d_lo:+.3f}, {d_hi:+.3f}]")
    print(f"\nOne-sided p-value  P(diff <= 0) = {p_value:.3f}")
    sig = "SIGNIFICANT" if d_lo > 0 else "NOT significant"
    print(f"Difference is {sig} at 95% (CI {'excludes' if d_lo > 0 else 'includes'} 0).")

    if d_lo <= 0:
        print("\n=> The active edge over B&H is NOT statistically distinguishable from")
        print("   noise. Even the best active strategy cannot be said to beat passive")
        print("   holding once sampling error is accounted for. This STRENGTHENS the")
        print("   paper's conclusion.")

    REPORTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"metric": "bh_sharpe", "observed": obs_bh, "ci_lo": bh_lo, "ci_hi": bh_hi},
        {"metric": "st_sharpe", "observed": obs_st, "ci_lo": st_lo, "ci_hi": st_hi},
        {"metric": "diff_st_minus_bh", "observed": obs_diff, "ci_lo": d_lo, "ci_hi": d_hi},
        {"metric": "p_value_diff_le_0", "observed": p_value, "ci_lo": None, "ci_hi": None},
    ]).to_csv(REPORTS / "significance.csv", index=False)
    print(f"\nwrote {REPORTS / 'significance.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
