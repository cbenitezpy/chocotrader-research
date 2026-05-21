# Resumen `train_val` — BTC_USDT

**Fecha de corrida:** 2026-05-21 11:03 UTC

**Ventana:** 2018-02-01 → 2026-04-30  (`17904` bars 4h)

**Fill model:** signal-at-close, fill-at-next-open. Fees 0.10%/side, slippage 0.05%/side.

## Tabla comparativa (sorted by Δ Sharpe vs B&H BTC)

| Experimento | Sharpe | Δ Sharpe vs B&H | MaxDD | PF | Trades | WinRate | Final $ | Return % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| supertrend_baseline       | +0.972 | +0.282 | -25.59% | 1.47 | 213 | 36.6% | $366.34 | +266.34% || h3_funding_filter         | +0.724 | +0.034 | -23.78% | 1.41 | 167 | 37.1% | $208.49 | +108.49% || h3_funding_standalone     | +0.723 | +0.033 | -30.80% | ∞ | 6 | 100.0% | $195.56 | +95.56% || h5_dxy_filter             | +0.441 | -0.250 | -31.72% | 1.24 | 122 | 31.1% | $148.18 | +48.18% || h5_dxy_standalone         | +0.207 | -0.483 | -41.42% | 1.09 | 144 | 39.6% | $118.45 | +18.45% || h1_fg_standalone          | +0.048 | -0.642 | -37.71% | 0.85 | 8 | 50.0% | $94.64 | -5.36% || h1_fg_filter              | -0.215 | -0.905 | -30.25% | 0.75 | 65 | 32.3% | $81.25 | -18.75% |

## Baseline B&H BTC

- Sharpe: +0.690
- MaxDD: -77.04%
- Final: \$673.36
- Return: +573.36%

## Gates (ADR-023 §2.4) — referencia

| Gate | Umbral | Aplica en |
|---|---|---|
| Δ Sharpe vs B&H | ≥ +0.20 | train+val |
| Δ Sharpe vs B&H | ≥ +0.15 | walk-forward W3 |
| Δ Sharpe vs B&H | ≥ +0.10 | OOS forward-test |
| MaxDD | ≤ 25% | siempre |
| PF | ≥ 1.3 | train+val |
| n_trades | ≥ 50 | train+val |
