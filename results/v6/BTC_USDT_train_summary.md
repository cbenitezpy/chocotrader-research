# Resumen `train` — BTC_USDT

**Fecha de corrida:** 2026-05-21 11:03 UTC

**Ventana:** 2018-02-01 → 2024-12-31  (`15135` bars 4h)

**Fill model:** signal-at-close, fill-at-next-open. Fees 0.10%/side, slippage 0.05%/side.

## Tabla comparativa (sorted by Δ Sharpe vs B&H BTC)

| Experimento | Sharpe | Δ Sharpe vs B&H | MaxDD | PF | Trades | WinRate | Final $ | Return % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| supertrend_baseline       | +1.154 | +0.337 | -25.59% | 1.67 | 177 | 35.0% | $398.37 | +298.37% || h3_funding_filter         | +0.917 | +0.101 | -23.78% | 1.65 | 131 | 35.1% | $226.72 | +126.72% || h3_funding_standalone     | +0.786 | -0.030 | -30.80% | ∞ | 6 | 100.0% | $195.56 | +95.56% || h5_dxy_filter             | +0.591 | -0.226 | -31.72% | 1.37 | 99 | 29.3% | $162.13 | +62.13% || h5_dxy_standalone         | +0.448 | -0.369 | -41.42% | 1.35 | 118 | 43.2% | $154.26 | +54.26% || h1_fg_standalone          | +0.106 | -0.711 | -37.71% | 1.10 | 6 | 50.0% | $101.98 | +1.98% || h1_fg_filter              | -0.100 | -0.917 | -21.21% | 0.83 | 51 | 33.3% | $90.14 | -9.86% |

## Baseline B&H BTC

- Sharpe: +0.817
- MaxDD: -77.04%
- Final: \$898.10
- Return: +798.10%

## Gates (ADR-023 §2.4) — referencia

| Gate | Umbral | Aplica en |
|---|---|---|
| Δ Sharpe vs B&H | ≥ +0.20 | train+val |
| Δ Sharpe vs B&H | ≥ +0.15 | walk-forward W3 |
| Δ Sharpe vs B&H | ≥ +0.10 | OOS forward-test |
| MaxDD | ≤ 25% | siempre |
| PF | ≥ 1.3 | train+val |
| n_trades | ≥ 50 | train+val |
