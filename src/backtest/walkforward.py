"""Walk-forward W1/W2/W3 over the train+val window.

Splits 2018-2026 into 3 non-overlapping windows of ~2.7 years each.
Per pre_registration.md §3, gate = Δ Sharpe vs B&H BTC ≥ +0.15 in W3
(the most recent window — predictive of OOS).
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import json
import pandas as pd

from src.backtest.engine import simulate, simulate_buy_and_hold
from src.backtest.metrics import compute_metrics, metrics_to_dict
from src.backtest.runner import _experiment_definitions
from src.data.loaders import load_ohlcv_4h

# walkforward.py lives at src/backtest/ → parents[2] is the repo root.
RESULTS = Path(__file__).resolve().parents[2] / "results" / "v6"
REPORTS = Path(__file__).resolve().parents[2] / "results" / "v6"

# 3 non-overlapping ~2.7-year windows covering the 2018-2026 train+val span.
WINDOWS: dict[str, tuple[str, str]] = {
    "W1": ("2018-02-01", "2020-09-30"),
    "W2": ("2020-10-01", "2023-06-30"),
    "W3": ("2023-07-01", "2026-04-30"),
}

W3_GATE_DELTA = 0.15  # ADR-023 §2.4


def _run_window(window: str, start: str, end: str, symbol: str) -> list[dict]:
    print(f"\n=== {window}: {start} → {end} ===", flush=True)
    ohlcv = load_ohlcv_4h(symbol=symbol, variant="full", start=start, end=end)
    if ohlcv.empty:
        return []
    print(f"  bars={len(ohlcv)}")
    bh = simulate_buy_and_hold(ohlcv)
    bh_m = compute_metrics(bh)
    print(f"  B&H {symbol}: Sharpe={bh_m.sharpe:+.3f} MaxDD={bh_m.max_drawdown*100:.1f}% Final=${bh_m.final_equity:.2f}")
    rows: list[dict] = [{"window": window, "name": "buy_and_hold_btc", **metrics_to_dict(bh_m)}]
    experiments = _experiment_definitions(symbol)
    for name, fn in experiments:
        try:
            sig = fn(ohlcv)
            res = simulate(ohlcv, sig)
            m = compute_metrics(res)
            delta = m.sharpe - bh_m.sharpe
            print(f"  {name:25s} Sharpe={m.sharpe:+.3f} Δ={delta:+.3f} MaxDD={m.max_drawdown*100:.1f}% Trades={m.n_trades}")
            rows.append({"window": window, "name": name, **metrics_to_dict(m)})
        except Exception as e:
            print(f"  {name}: FAILED {e!r}")
            rows.append({"window": window, "name": name, "error": str(e)})
    return rows


def _build_wf_table(all_rows: list[dict]) -> str:
    """Pivot rows into a per-window comparison table."""
    df = pd.DataFrame(all_rows)
    if df.empty:
        return "(no data)\n"
    # For each strategy, compute delta vs B&H in each window
    pivot = df.pivot_table(index="name", columns="window", values="sharpe")
    bh = pivot.loc["buy_and_hold_btc"]
    deltas = pivot.sub(bh, axis=1)
    deltas = deltas.drop(index="buy_and_hold_btc")

    # Sort by W3 delta desc
    deltas_sorted = deltas.sort_values("W3", ascending=False)

    lines = ["| Estrategia | Δ W1 | Δ W2 | Δ W3 | Pasa gate W3 (≥+0.15) |\n",
             "|---|---:|---:|---:|:---:|\n"]
    for name, row in deltas_sorted.iterrows():
        w1 = row.get("W1", float("nan"))
        w2 = row.get("W2", float("nan"))
        w3 = row.get("W3", float("nan"))
        passes = "✅" if (pd.notna(w3) and w3 >= W3_GATE_DELTA) else "❌"
        lines.append(f"| {name:25s} | {w1:+.3f} | {w2:+.3f} | {w3:+.3f} | {passes} |\n")
    bh_line = (
        f"\n**B&H BTC absoluto:** "
        f"W1={pivot.loc['buy_and_hold_btc','W1']:+.3f}, "
        f"W2={pivot.loc['buy_and_hold_btc','W2']:+.3f}, "
        f"W3={pivot.loc['buy_and_hold_btc','W3']:+.3f}\n"
    )
    return "".join(lines) + bh_line


def main(symbol: str = "BTC_USDT") -> int:
    all_rows: list[dict] = []
    for window, (start, end) in WINDOWS.items():
        all_rows.extend(_run_window(window, start, end, symbol))

    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(RESULTS / f"walkforward_{symbol}.csv", index=False)

    md = (
        f"# Walk-Forward W1/W2/W3 — {symbol}\n\n"
        f"**Fecha de corrida:** {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"**Ventanas:**\n"
        f"- W1: {WINDOWS['W1'][0]} → {WINDOWS['W1'][1]}  (bull 2018-2020)\n"
        f"- W2: {WINDOWS['W2'][0]} → {WINDOWS['W2'][1]}  (mega bull 2020-2023)\n"
        f"- W3: {WINDOWS['W3'][0]} → {WINDOWS['W3'][1]}  (consolidación + bear 2023-2026)\n\n"
        f"## Gate ADR-023 §2.4\n\nW3 es predictivo de OOS. Gate: Δ Sharpe vs B&H ≥ +0.15.\n\n"
        f"## Tabla comparativa (sorted by Δ W3 desc)\n\n"
        + _build_wf_table(all_rows)
    )
    md_path = REPORTS / f"walkforward_{symbol}.md"
    md_path.write_text(md)
    print(f"\nwrote {md_path}")

    # Determine if any strategy passes W3 gate
    df = pd.DataFrame(all_rows)
    if not df.empty and "window" in df.columns:
        w3 = df[df["window"] == "W3"]
        bh_w3 = w3[w3["name"] == "buy_and_hold_btc"]["sharpe"].iloc[0]
        candidates = w3[w3["name"] != "buy_and_hold_btc"].copy()
        candidates["delta"] = candidates["sharpe"] - bh_w3
        passers = candidates[candidates["delta"] >= W3_GATE_DELTA]
        print(f"\n=== W3 gate evaluation (Δ ≥ +{W3_GATE_DELTA}) ===")
        if passers.empty:
            print("RESULT: NO strategy passes W3 gate.")
            print("→ Per ADR-023 §2.5 trigger #1, v6 must close formally (no OOS access).")
        else:
            print(f"RESULT: {len(passers)} strategy(ies) pass W3 gate:")
            for _, r in passers.iterrows():
                print(f"  - {r['name']:25s} Sharpe={r['sharpe']:+.3f} Δ={r['delta']:+.3f}")
            print("→ Proceed to Fase 4 OOS forward-test (NOT this script).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
