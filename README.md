# Chocotrader Research — Does retail algorithmic trading have an edge on crypto spot?

> **TL;DR:** A pre-registered, six-phase study over 9.25 years of data asking whether any simple, retail-accessible strategy beats Buy-and-Hold BTC on Binance Spot, net of realistic costs. **It doesn't.** This repo contains the simulators, data fetchers, datasets, and the full paper documenting the negative result — and the methodology that kept us from fooling ourselves.

[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Tests](https://img.shields.io/badge/tests-26%20passing-brightgreen.svg)](tests/)

---

## What's here

- **`paper/`** — the full working paper (English + Spanish).
- **`src/signals/`** — the SuperTrend baseline plus six signal generators (Fear & Greed, funding-rate, and DXY sentiment, each as a SuperTrend filter and as a standalone signal) and the look-ahead-safe alignment layer.
- **`src/backtest/`** — the backtest engine (`next_open` fill model, explicit cost model), standardized metrics, the experiment runner, and the walk-forward runner with automated gate enforcement.
- **`src/data/`** — canonical loaders and fetchers for all external series.
- **`tests/`** — 26 unit tests covering alignment (no look-ahead), signal contracts, and the engine.
- **`results/`** — per-experiment reports and result logs for all phases (v1–v6) plus the 144-combination full-period audit.
- **`docs/`** — the pre-registration, the alignment contract, lessons learned, postmortems, and the relevant ADRs (012, 023, 024).

## Headline results

| | Final equity ($1k base, 2017–2026) | Sharpe | MaxDD |
|---|---:|---:|---:|
| **Buy & Hold BTC** | **$15,958** | **0.809** | −83.9% |
| Best active (SuperTrend BTC) | $2,190 | 0.977 | −13.7% |
| Best in-sample ensemble → **OOS** | $99.81 | **+0.041** | — |

- No strategy passed the pre-registered out-of-sample gate (Sharpe ≥ 0.8).
- A mean-reversion "edge" of Sharpe **+0.72** vanished to **−0.56** under a realistic fill model.
- In the 2023–2026 regime, **every** strategy underperformed Buy-and-Hold BTC.
- Total capital lost: **$0**.

The conclusion was then stress-tested against five adversarial critiques (cost model, 4h timeframe, start date, large-cap universe, long-only constraint) — see `src/robustness/` and `results/robustness/`. It survives all five; notably, adding short-selling via 1x perpetuals with **real funding costs** *lowers* the trend-following Sharpe rather than raising it. Full write-up in the paper's Section 6.

## Quickstart

```bash
git clone <repo-url> && cd chocotrader-research
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make fetch       # download external series (F&G, funding, DXY) + OHLCV from Binance
make test        # run the 26 tests
make reproduce   # regenerate the v6 result tables (train/val + walk-forward)
```

Without `make`, the equivalents are:

```bash
python -m src.data.fetchers.fetch_fng
python -m src.data.fetchers.fetch_dxy
python -m src.data.fetchers.fetch_funding BTCUSDT ETHUSDT
python -m src.data.fetch_ohlcv BTC_USDT ETH_USDT
pytest -o addopts="" tests/
python -m src.backtest.runner
python -m src.backtest.walkforward
```

## Reproducibility

Every table in the paper is regenerable from committed code plus regenerable datasets. The fetchers reproduce the exact external series used (Fear & Greed from alternative.me, funding rate from Binance, DXY from FRED). OHLCV is downloaded from Binance public klines via `src/data/fetch_ohlcv.py` — we do not redistribute exchange data. The out-of-sample dataset reserved for the final phase was never accessed and is not part of this repository.

## How to read the paper

Start with [`paper/chocotrader-paper-en.md`](paper/chocotrader-paper-en.md) (or [`-es.md`](paper/chocotrader-paper-es.md) for Spanish). Section 2 is the methodology; Section 4 is the results; Section 5 is what we learned. If you read only one thing, read **Section 4.2** — the fill-model artifact, where an apparent +0.72 Sharpe edge turned into −0.56 once execution was modeled realistically.

## Why publish a negative result?

The base rate of *published* trading failures is near zero, which is itself evidence of massive survivorship and publication bias. We wrote our hypotheses down before looking at the data, sealed the out-of-sample set, used a realistic execution model, and reported everything — including the two weeks wasted optimizing a signal a correct fill model would have killed on day one. **The method is the contribution.**

## Repository layout

```
chocotrader-research/
├── paper/            # the working paper (EN + ES)
├── src/
│   ├── signals/      # supertrend + 6 generators + alignment (no look-ahead)
│   ├── backtest/     # engine, metrics, runner, walk-forward
│   └── data/         # loaders + fetchers
├── tests/            # 26 unit tests
├── data/             # (gitignored parquets; regenerate via fetchers)
├── results/          # reports + result logs for v1–v6 + full-period audit
└── docs/             # pre-registration, alignment spec, lessons, postmortems, ADRs
```

## Disclaimer

This repository is research, **not financial advice**. It documents a negative result: the strategies tested had **no exploitable edge**. Past performance — including the Buy-and-Hold figures — does not predict future returns. Nothing here is an investment recommendation. The authors are not liable for losses arising from use of this code or its conclusions.

## Citation

If you use this work, please cite it — see [`CITATION.cff`](CITATION.cff).

## License

Code under [MIT](LICENSE); paper and docs under CC BY 4.0. Third-party data (alternative.me, Binance, FRED) remains under its original terms — this repo provides fetchers, not redistributed data.
