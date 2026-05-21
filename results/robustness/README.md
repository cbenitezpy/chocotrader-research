# Robustness checks (Tier 2 + Tier 3)

Adversarial response to five red-team critiques of the main result. All runs
use a **$1,000 base** and the realistic `next_open` fill model. Reproduce with:

```bash
python -m src.robustness.cost_sensitivity
python -m src.robustness.start_date_sensitivity
python -m src.robustness.daily_timeframe
python -m src.robustness.altcoin_universe
python -m src.robustness.long_short_experiment BTC_USDT
python -m src.robustness.long_short_experiment ETH_USDT
```

| # | Critique | Test | Verdict |
|---|---|---|---|
| 1 | Long-only invalidates the conclusion | `long_short_experiment` — 1x perp, real funding | **Refuted.** Shorting *lowers* Sharpe (BTC 0.908→0.524). |
| 2 | 4h is "no man's land" | `daily_timeframe` | **Refuted.** Daily (0.911) ≤ 4h (0.972); neither clears gate. |
| 3 | Cost model is pessimistic | `cost_sensitivity` | **Refuted.** No negative-Sharpe strategy flips even at 0% cost. |
| 4 | Wrong (large-cap) universe | `altcoin_universe` | **Refuted.** 0/7 surviving mid-caps clear the gate (upper bound). |
| 5 | Benchmark depends on start date | `start_date_sensitivity` | **Partly true, cuts against critic.** Active beats B&H only on drawdown, never on the gate; underperforms on Sharpe from 2021/2022 starts. |

CSV outputs: `cost_sensitivity.csv`, `start_date_sensitivity.csv`,
`daily_timeframe.csv`, `altcoin_universe.csv`, `long_short_{BTC,ETH}_USDT.csv`.

**Methodological note:** the long/short experiment first produced a Sharpe of
2.7 — inconsistent with its −66% drawdown and sub-baseline final equity. Per
our own red-flag rule, we treated the too-good number as a bug, found a
double-counting error in the perpetual mark-to-market, fixed it, and re-ran.
The corrected figures are above. See paper §6.5.
