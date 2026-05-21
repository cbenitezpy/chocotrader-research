# Resumen `val` — BTC_USDT

**Fecha de corrida:** 2026-05-21 11:03 UTC

**Ventana:** 2025-01-01 → 2026-04-30  (`2764` bars 4h)

**Fill model:** signal-at-close, fill-at-next-open. Fees 0.10%/side, slippage 0.05%/side.

## Tabla comparativa (sorted by Δ Sharpe vs B&H BTC)

| Experimento | Sharpe | Δ Sharpe vs B&H | MaxDD | PF | Trades | WinRate | Final $ | Return % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| h3_funding_standalone     | +0.000 | +0.306 | 0.00% | 0.00 | 0 | 0.0% | $100.00 | +0.00% || h1_fg_standalone          | -0.371 | -0.065 | -18.68% | 0.57 | 2 | 50.0% | $92.81 | -7.19% || h5_dxy_filter             | -0.615 | -0.309 | -11.72% | 0.63 | 25 | 40.0% | $91.94 | -8.06% || supertrend_baseline       | -0.658 | -0.352 | -16.18% | 0.68 | 36 | 41.7% | $89.65 | -10.35% || h3_funding_filter         | -0.658 | -0.352 | -16.18% | 0.68 | 36 | 41.7% | $89.65 | -10.35% || h1_fg_filter              | -1.079 | -0.773 | -17.44% | 0.41 | 14 | 28.6% | $90.13 | -9.87% || h5_dxy_standalone         | -1.528 | -1.222 | -23.84% | 0.38 | 24 | 25.0% | $78.03 | -21.97% |

## Baseline B&H BTC

- Sharpe: -0.306
- MaxDD: -49.84%
- Final: \$74.01
- Return: -25.99%

## Gates (ADR-023 §2.4) — referencia

| Gate | Umbral | Aplica en |
|---|---|---|
| Δ Sharpe vs B&H | ≥ +0.20 | train+val |
| Δ Sharpe vs B&H | ≥ +0.15 | walk-forward W3 |
| Δ Sharpe vs B&H | ≥ +0.10 | OOS forward-test |
| MaxDD | ≤ 25% | siempre |
| PF | ≥ 1.3 | train+val |
| n_trades | ≥ 50 | train+val |
