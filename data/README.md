# Data

Datasets are **not committed** to this repository — they are regenerated from
public sources by the fetchers. This avoids redistributing exchange data and
keeps the repo small.

## Regenerate everything

```bash
make fetch
```

or individually:

```bash
python -m src.data.fetchers.fetch_fng          # -> data/external/fng_daily.parquet
python -m src.data.fetchers.fetch_dxy          # -> data/external/dxy_daily.parquet
python -m src.data.fetchers.fetch_funding BTCUSDT ETHUSDT
python -m src.data.fetch_ohlcv BTC_USDT ETH_USDT   # -> data/ohlcv/<sym>_4h_full.parquet
```

## Sources and terms

| Dataset | Source | Coverage | Terms |
|---|---|---|---|
| OHLCV 4h | Binance public klines API | 2017-08 → now | Binance API terms; we fetch, not redistribute |
| Fear & Greed | alternative.me API | 2018-02 → now | Free API |
| Funding rate 8h | Binance USD-M perpetuals API | 2019-09 → now | Binance API terms |
| DXY (DTWEXBGS) | FRED (St. Louis Fed) | 2006 → now | Public domain (US Federal Reserve) |

Each user fetches the data under the original provider's terms. This repository
provides the code to fetch and process it, not the data itself.

## Out-of-sample note

The out-of-sample dataset reserved for the final research phase was **never
accessed** (the walk-forward gate was not cleared) and is intentionally **not**
part of this repository, preserving its seal for any future study.
