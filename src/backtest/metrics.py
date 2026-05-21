"""Performance metrics for backtests.

Standardised on:
- Sharpe (annualised, simple).
- MaxDD (peak-to-trough fraction, ≤ 0).
- Profit factor (gross wins / gross losses, ratio).
- Win rate (fraction of trades with pnl > 0).
- Total return (final/initial - 1).
- Calmar (annual return / |MaxDD|).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestResult, Trade


@dataclass(frozen=True)
class Metrics:
    """Standard metric set per backtest run."""

    sharpe: float
    sortino: float
    max_drawdown: float  # ≤ 0
    profit_factor: float
    win_rate: float
    total_return: float
    annualised_return: float
    calmar: float
    n_trades: int
    avg_trade_pct: float
    initial_equity: float
    final_equity: float


def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    if den == 0 or np.isnan(den):
        return default
    return num / den


def compute_metrics(result: BacktestResult) -> Metrics:
    """Compute the canonical metric set from a BacktestResult."""
    eq = result.equity_curve.to_numpy(dtype=float)
    rets = np.diff(eq) / eq[:-1]
    rets = rets[~np.isnan(rets)]

    cfg = result.config
    n_bars = len(eq)
    period_years = n_bars / cfg.annualization_factor

    if rets.size == 0 or rets.std(ddof=1) == 0:
        sharpe = 0.0
        sortino = 0.0
    else:
        excess = rets - cfg.risk_free_rate / cfg.annualization_factor
        sharpe = float(excess.mean() / rets.std(ddof=1) * np.sqrt(cfg.annualization_factor))
        downside = rets[rets < 0]
        sortino = (
            float(excess.mean() / downside.std(ddof=1) * np.sqrt(cfg.annualization_factor))
            if downside.size > 1 and downside.std(ddof=1) > 0
            else 0.0
        )

    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    max_dd = float(np.min(dd)) if dd.size > 0 else 0.0

    trades = result.trades
    n_trades = len(trades)
    wins = [t for t in trades if t.pnl_usd > 0]
    losses = [t for t in trades if t.pnl_usd < 0]
    gross_w = sum(t.pnl_usd for t in wins)
    gross_l = -sum(t.pnl_usd for t in losses)
    pf = _safe_div(gross_w, gross_l, default=float("inf") if gross_w > 0 else 0.0)
    win_rate = _safe_div(len(wins), n_trades)
    avg_trade_pct = (
        float(np.mean([t.return_pct for t in trades if t.is_closed])) if n_trades > 0 else 0.0
    )

    total_ret = result.total_return_pct
    ann_ret = (1.0 + total_ret) ** (1.0 / period_years) - 1.0 if period_years > 0 else 0.0
    calmar = _safe_div(ann_ret, abs(max_dd), default=0.0)

    return Metrics(
        sharpe=round(sharpe, 4),
        sortino=round(sortino, 4),
        max_drawdown=round(max_dd, 4),
        profit_factor=round(pf, 4) if np.isfinite(pf) else float("inf"),
        win_rate=round(win_rate, 4),
        total_return=round(total_ret, 4),
        annualised_return=round(ann_ret, 4),
        calmar=round(calmar, 4),
        n_trades=n_trades,
        avg_trade_pct=round(avg_trade_pct, 4),
        initial_equity=cfg.initial_capital,
        final_equity=round(result.final_equity, 4),
    )


def metrics_to_dict(m: Metrics) -> dict[str, float | int]:
    return {
        "sharpe": m.sharpe,
        "sortino": m.sortino,
        "max_drawdown": m.max_drawdown,
        "profit_factor": m.profit_factor if np.isfinite(m.profit_factor) else 999.0,
        "win_rate": m.win_rate,
        "total_return": m.total_return,
        "annualised_return": m.annualised_return,
        "calmar": m.calmar,
        "n_trades": m.n_trades,
        "avg_trade_pct": m.avg_trade_pct,
        "initial_equity": m.initial_equity,
        "final_equity": m.final_equity,
    }
