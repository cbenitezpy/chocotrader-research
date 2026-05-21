# V5: Multi-Pair Validation Report

**Date:** 2026-04-09
**Strategy:** SuperTrend(10,3) 4h
**Sizing:** Fractional compound, risk_pct=0.75%, cap=50%
**Initial equity:** $500 per pair
**Stop:** Hybrid (floor $400 + trailing -25% HWM)

## Per-Pair Results (Full Period)

| Pair | Sharpe | MaxDD | PF | Trades | WR% | Return% | Calmar | Stop | Gate |
|------|--------|-------|----|--------|-----|---------|--------|------|------|
| BTC/USDT | 1.416 | -11.5% | 2.00 | 225 | 38.2 | 166.9% | 1.68 | no | PASS |
| ETH/USDT | 1.213 | -8.7% | 1.86 | 222 | 37.4 | 128.4% | 1.72 | no | PASS |
| SOL/USDT | 0.991 | -8.7% | 1.85 | 149 | 34.9 | 65.4% | 1.34 | no | FAIL |
| BNB/USDT | 0.907 | -20.3% | 1.88 | 216 | 39.8 | 109.4% | 0.64 | no | FAIL |
| XRP/USDT | 0.694 | -16.0% | 1.73 | 194 | 33.5 | 79.2% | 0.63 | no | FAIL |

## Walk-Forward Validation (70/30 split)

| Pair | IS Sharpe | OOS Sharpe | Delta | IS PF | OOS PF | OOS Pass |
|------|-----------|------------|-------|-------|--------|----------|
| BTC/USDT | 1.543 | 1.071 | -0.473 | 2.30 | 1.61 | PASS |
| ETH/USDT | 1.317 | 0.946 | -0.372 | 2.08 | 1.56 | PASS |
| SOL/USDT | 1.207 | 0.303 | -0.904 | 2.26 | 1.18 | FAIL |
| BNB/USDT | 0.911 | 0.883 | -0.028 | 1.92 | 1.74 | PASS |
| XRP/USDT | 0.637 | 0.809 | +0.172 | 1.70 | 1.76 | PASS |

## Window Analysis (2-year periods)

### BTC/USDT

| Period | Sharpe | PF | Trades | MaxDD |
|--------|--------|----|--------|-------|
| 2017-2019 | 0.427 | 1.25 | 36 | -7.1% |
| 2019-2021 | 2.647 | 5.09 | 47 | -7.0% |
| 2021-2023 | -0.276 | 0.85 | 55 | -11.2% |
| 2023-2025 | 1.984 | 2.39 | 53 | -6.2% |
| 2025-2027 | -0.223 | 0.87 | 36 | -7.6% |

**WARNING:** 2 window(s) with negative Sharpe.

### ETH/USDT

| Period | Sharpe | PF | Trades | MaxDD |
|--------|--------|----|--------|-------|
| 2017-2019 | 0.297 | 1.17 | 33 | -7.3% |
| 2019-2021 | 2.287 | 4.96 | 44 | -5.8% |
| 2021-2023 | 0.531 | 1.29 | 57 | -8.7% |
| 2023-2025 | 1.247 | 1.86 | 52 | -6.5% |
| 2025-2027 | 0.090 | 1.03 | 37 | -7.3% |

### SOL/USDT

| Period | Sharpe | PF | Trades | MaxDD |
|--------|--------|----|--------|-------|
| 2020-2022 | 1.454 | 2.45 | 38 | -5.0% |
| 2022-2024 | 1.236 | 2.48 | 51 | -8.7% |
| 2024-2026 | 0.433 | 1.29 | 51 | -6.5% |

### BNB/USDT

| Period | Sharpe | PF | Trades | MaxDD |
|--------|--------|----|--------|-------|
| 2017-2019 | 0.324 | 1.25 | 29 | -10.7% |
| 2019-2021 | 1.213 | 2.12 | 52 | -7.3% |
| 2021-2023 | 1.267 | 2.53 | 53 | -20.3% |
| 2023-2025 | 0.826 | 1.83 | 49 | -8.4% |
| 2025-2027 | 0.191 | 1.10 | 36 | -10.4% |

### XRP/USDT

| Period | Sharpe | PF | Trades | MaxDD |
|--------|--------|----|--------|-------|
| 2018-2020 | -0.096 | 0.89 | 37 | -10.3% |
| 2020-2022 | 1.338 | 2.77 | 46 | -10.2% |
| 2022-2024 | 0.367 | 1.40 | 49 | -10.0% |
| 2024-2026 | 0.966 | 1.98 | 54 | -14.6% |

**WARNING:** 1 window(s) with negative Sharpe.

## Correlation Matrix

### Return Correlations

| Pair 1 | Pair 2 | Correlation |
|--------|--------|-------------|
| BTC/USDT | ETH_USDT/USDT | 0.554 |
| BTC/USDT | BNB_USDT/USDT | 0.068 |
| ETH/USDT | BNB_USDT/USDT | 0.054 |
| BTC/USDT | XRP_USDT/USDT | -0.024 |
| ETH/USDT | SOL_USDT/USDT | 0.020 |
| SOL/USDT | XRP_USDT/USDT | -0.016 |
| ETH/USDT | XRP_USDT/USDT | -0.015 |
| SOL/USDT | BNB_USDT/USDT | -0.012 |
| BNB/USDT | XRP_USDT/USDT | 0.007 |
| BTC/USDT | SOL_USDT/USDT | 0.003 |

## Portfolio Simulations

| Portfolio | Sharpe | MaxDD | PF | Trades | Return% | Calmar |
|-----------|--------|-------|----|--------|---------|--------|
| 2 pair BTC USDT ETH USDT | 1.457 | -9.4% | 1.93 | 442 | 146.8% | 1.80 |
| 3 pair BTC USDT ETH USDT SOL USDT | 1.868 | -6.0% | 1.88 | 556 | 87.4% | 2.55 |
| 4 pair BTC USDT ETH USDT SOL USDT BNB USDT | 2.060 | -5.7% | 1.92 | 703 | 83.9% | 2.59 |
| all 5 | 2.101 | -5.1% | 1.93 | 794 | 72.3% | 2.49 |

## Summary

- **Pairs passing gates:** BTC_USDT, ETH_USDT
- **Best single pair:** BTC_USDT
- **Best portfolio:** all_5
- **Recommendation:** Multi-pair (all_5) improves Sharpe with acceptable correlation. Consider portfolio of passing pairs: BTC_USDT, ETH_USDT.
