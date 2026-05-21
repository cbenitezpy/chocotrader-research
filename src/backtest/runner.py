"""Orchestrator: run all v6 experiments on a given split, emit metrics table.

Usage:
    python -m src.backtest.runner

Splits per pre_registration.md §4.3:
    train:    [2018-02-01, 2024-12-31]
    val:      [2025-01-01, 2026-04-30]
    train+val: [2018-02-01, 2026-04-30]
    OOS forward-only: [2026-05-20, end-of-v6]  — NOT run by this script (Fase 4).

Emits:
    research/v6/results/run_log.jsonl  (one line per run, audit trail)
    research/v6/results/summary_<split>.csv (sortable metric table)
    research/v6/reports/<split>_summary.md  (human-readable comparison)
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from src.backtest.engine import simulate, simulate_buy_and_hold
from src.backtest.metrics import compute_metrics, metrics_to_dict
from src.data.loaders import load_dxy, load_fng, load_funding, load_ohlcv_4h
from src.signals._supertrend_baseline import supertrend_signal
from src.signals.h1_fg_filter import h1_fg_filter_signal
from src.signals.h1_fg_standalone import h1_fg_standalone_signal
from src.signals.h3_funding_filter import h3_funding_filter_signal
from src.signals.h3_funding_standalone import h3_funding_standalone_signal
from src.signals.h5_dxy_filter import h5_dxy_filter_signal
from src.signals.h5_dxy_standalone import h5_dxy_standalone_signal

# backtest/runner.py lives at src/backtest/ → parents[2] is the repo root.
# Generated artifacts go under results/v6/ alongside the committed reports.
RESULTS = Path(__file__).resolve().parents[2] / "results" / "v6"
REPORTS = Path(__file__).resolve().parents[2] / "results" / "v6"

SPLITS: dict[str, tuple[str, str]] = {
    "train":     ("2018-02-01", "2024-12-31"),
    "val":       ("2025-01-01", "2026-04-30"),
    "train_val": ("2018-02-01", "2026-04-30"),
}


def _experiment_definitions(symbol: str) -> list[tuple[str, Callable]]:
    """Return list of (name, signal_fn). Order is preserved in report."""
    funding_symbol = symbol.replace("/", "").replace("_", "").lower()
    fng = load_fng()
    dxy = load_dxy()
    funding = load_funding(funding_symbol)
    return [
        ("supertrend_baseline", lambda ohlcv: supertrend_signal(ohlcv)),
        ("h1_fg_filter",       lambda ohlcv: h1_fg_filter_signal(ohlcv, fng)),
        ("h1_fg_standalone",   lambda ohlcv: h1_fg_standalone_signal(ohlcv, fng)),
        ("h3_funding_filter",  lambda ohlcv: h3_funding_filter_signal(ohlcv, funding)),
        ("h3_funding_standalone", lambda ohlcv: h3_funding_standalone_signal(ohlcv, funding)),
        ("h5_dxy_filter",      lambda ohlcv: h5_dxy_filter_signal(ohlcv, dxy)),
        ("h5_dxy_standalone",  lambda ohlcv: h5_dxy_standalone_signal(ohlcv, dxy)),
    ]


def _log_run(record: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "run_log.jsonl").open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _format_pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def _build_md_table(rows: list[dict], bh_sharpe: float, bh_total: float) -> str:
    """Markdown table sorted by Sharpe delta vs B&H descending."""
    for r in rows:
        r["delta_sharpe"] = r["sharpe"] - bh_sharpe
        r["delta_return"] = r["total_return"] - bh_total
    rows_sorted = sorted(rows, key=lambda r: r["delta_sharpe"], reverse=True)
    header = (
        "| Experimento | Sharpe | Δ Sharpe vs B&H | MaxDD | PF | Trades | WinRate | Final $ | Return % |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    lines = [header]
    for r in rows_sorted:
        pf_str = f"{r['profit_factor']:.2f}" if r["profit_factor"] < 100 else "∞"
        lines.append(
            f"| {r['name']:25s} "
            f"| {r['sharpe']:+.3f} "
            f"| {r['delta_sharpe']:+.3f} "
            f"| {r['max_drawdown']*100:.2f}% "
            f"| {pf_str} "
            f"| {r['n_trades']} "
            f"| {r['win_rate']*100:.1f}% "
            f"| ${r['final_equity']:.2f} "
            f"| {_format_pct(r['total_return'])} |"
        )
    return "".join(lines)


def run_split(split_name: str, symbol: str = "BTC_USDT") -> dict:
    start, end = SPLITS[split_name]
    print(f"\n=== [{symbol}] split={split_name} {start} → {end} ===", flush=True)
    ohlcv = load_ohlcv_4h(symbol=symbol, variant="full", start=start, end=end)
    if ohlcv.empty:
        raise RuntimeError(f"empty OHLCV for {symbol} {split_name}")
    print(f"  OHLCV bars: {len(ohlcv)}")
    print(f"  range:  {ohlcv['ts'].iloc[0]}  →  {ohlcv['ts'].iloc[-1]}")

    # --- B&H baseline first (used for delta comparison)
    bh = simulate_buy_and_hold(ohlcv)
    bh_m = compute_metrics(bh)
    print(f"  B&H BTC: Sharpe={bh_m.sharpe:+.3f}  MaxDD={bh_m.max_drawdown*100:.1f}%  Final=${bh_m.final_equity:.2f}")
    bh_row = {"name": "buy_and_hold_btc", **metrics_to_dict(bh_m)}
    _log_run({
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "split": split_name,
        "symbol": symbol,
        "experiment": "buy_and_hold_btc",
        **metrics_to_dict(bh_m),
        "n_bars": len(ohlcv),
    })

    # --- Experiments
    rows: list[dict] = [bh_row]
    experiments = _experiment_definitions(symbol)
    for name, fn in experiments:
        try:
            sig = fn(ohlcv)
            res = simulate(ohlcv, sig)
            m = compute_metrics(res)
            row = {"name": name, **metrics_to_dict(m)}
            rows.append(row)
            print(
                f"  {name:28s} Sharpe={m.sharpe:+.3f}  ΔvsBH={m.sharpe - bh_m.sharpe:+.3f}  "
                f"MaxDD={m.max_drawdown*100:.1f}%  Trades={m.n_trades}  Final=${m.final_equity:.2f}"
            )
            _log_run({
                "ts": datetime.now(tz=timezone.utc).isoformat(),
                "split": split_name,
                "symbol": symbol,
                "experiment": name,
                **metrics_to_dict(m),
                "n_bars": len(ohlcv),
            })
        except Exception as e:
            print(f"  {name}: FAILED {e!r}")
            rows.append({"name": name, "error": str(e), **{k: float("nan") for k in metrics_to_dict(bh_m)}})

    # --- Persist
    df = pd.DataFrame(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS / f"summary_{symbol}_{split_name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"  wrote {csv_path}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS / f"{symbol}_{split_name}_summary.md"
    md = (
        f"# Resumen `{split_name}` — {symbol}\n\n"
        f"**Fecha de corrida:** {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"**Ventana:** {start} → {end}  (`{len(ohlcv)}` bars 4h)\n\n"
        f"**Fill model:** signal-at-close, fill-at-next-open. Fees 0.10%/side, slippage 0.05%/side.\n\n"
        f"## Tabla comparativa (sorted by Δ Sharpe vs B&H BTC)\n\n"
        + _build_md_table(rows[1:], bh_m.sharpe, bh_m.total_return)
        + f"\n\n## Baseline B&H BTC\n\n"
        f"- Sharpe: {bh_m.sharpe:+.3f}\n"
        f"- MaxDD: {bh_m.max_drawdown*100:.2f}%\n"
        f"- Final: \${bh_m.final_equity:.2f}\n"
        f"- Return: {_format_pct(bh_m.total_return)}\n"
        f"\n## Gates (ADR-023 §2.4) — referencia\n\n"
        f"| Gate | Umbral | Aplica en |\n|---|---|---|\n"
        f"| Δ Sharpe vs B&H | ≥ +0.20 | train+val |\n"
        f"| Δ Sharpe vs B&H | ≥ +0.15 | walk-forward W3 |\n"
        f"| Δ Sharpe vs B&H | ≥ +0.10 | OOS forward-test |\n"
        f"| MaxDD | ≤ 25% | siempre |\n"
        f"| PF | ≥ 1.3 | train+val |\n"
        f"| n_trades | ≥ 50 | train+val |\n"
    )
    md_path.write_text(md)
    print(f"  wrote {md_path}")

    return {"rows": rows, "bh": bh_m}


def main() -> int:
    for split_name in ("train", "val", "train_val"):
        run_split(split_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
