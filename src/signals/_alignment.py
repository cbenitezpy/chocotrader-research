"""Alignment helpers: merge daily/8h external series into 4h OHLCV index.

Contract: NO look-ahead. For each OHLCV bar with timestamp T (which covers
[T, T+4h)) and closes at T_close = T + 4h, we return the last external value
strictly available BEFORE T_close minus a configurable lag.

See research/v6/data/alignment_spec.md for the full contract.
"""

from __future__ import annotations

import pandas as pd


def _to_ns_utc(s: pd.Series) -> pd.Series:
    """Coerce any tz-aware datetime Series to ns resolution, UTC.

    Pandas/pyarrow can return us/ms resolutions; merge_asof requires identical
    resolutions on both sides. Standardise on ns to avoid surprises.
    """
    out = pd.to_datetime(s, utc=True)
    if hasattr(out, "dt") and getattr(out.dt, "unit", None) != "ns":
        out = out.astype("datetime64[ns, UTC]")
    return out


def _bar_close_dt(ohlcv: pd.DataFrame, tf_hours: int = 4) -> pd.Series:
    """Return the close timestamp of each OHLCV bar (= ts + tf_hours)."""
    ts = _to_ns_utc(ohlcv["ts"])
    return ts + pd.Timedelta(hours=tf_hours)


def align_daily_to_4h(
    daily_df: pd.DataFrame,
    ohlcv_4h: pd.DataFrame,
    value_col: str,
    date_col: str = "date",
    lag_hours: int = 4,
    tf_hours: int = 4,
) -> pd.Series:
    """For each 4h bar close, return last daily ``value_col`` available
    (close_dt - lag_hours) - ε before. Forward-fill across gaps.

    Use case: F&G index daily → 4h OHLCV bars.

    Args:
        daily_df: DataFrame with date_col (tz-aware date) and value_col.
        ohlcv_4h: DataFrame with ``ts`` column (vela start, tz-aware).
        value_col: name of the value column in daily_df.
        date_col: name of the timestamp column in daily_df.
        lag_hours: minimum publish-lag to enforce (default 4h, F&G safe).
        tf_hours: timeframe of OHLCV (default 4).

    Returns:
        pd.Series indexed by ohlcv_4h.index, values = last published value.

    Raises:
        KeyError if columns missing.
        ValueError if daily_df not sorted ascending.
    """
    if date_col not in daily_df.columns:
        raise KeyError(f"daily_df missing '{date_col}'")
    if value_col not in daily_df.columns:
        raise KeyError(f"daily_df missing '{value_col}'")
    if not daily_df[date_col].is_monotonic_increasing:
        raise ValueError(f"daily_df['{date_col}'] must be monotonic ascending")

    bar_close = _bar_close_dt(ohlcv_4h, tf_hours=tf_hours)
    cutoff = bar_close - pd.Timedelta(hours=lag_hours)

    # merge_asof: for each cutoff timestamp, find the last daily row with
    # date_col STRICTLY before cutoff. allow_exact_matches=False enforces it.
    left = pd.DataFrame({"cutoff": cutoff}).reset_index(drop=False).rename(columns={"index": "_idx"})
    left = left.sort_values("cutoff").reset_index(drop=True)
    right = daily_df[[date_col, value_col]].copy()
    right[date_col] = _to_ns_utc(right[date_col])
    right = right.sort_values(date_col).reset_index(drop=True)
    merged = pd.merge_asof(
        left,
        right,
        left_on="cutoff",
        right_on=date_col,
        direction="backward",
        allow_exact_matches=False,
    )
    merged = merged.sort_values("_idx").reset_index(drop=True)
    result = pd.Series(merged[value_col].values, index=ohlcv_4h.index, name=value_col)
    return result


def align_funding_to_4h(
    funding_df: pd.DataFrame,
    ohlcv_4h: pd.DataFrame,
    agg: str = "last",
    window_hours: int = 24,
    time_col: str = "funding_time",
    value_col: str = "funding_rate",
    tf_hours: int = 4,
) -> pd.Series:
    """For each 4h bar close, return last (or avg over window_hours) funding
    rate available strictly before close.

    Args:
        funding_df: DataFrame with time_col (8h timestamps) and value_col.
        ohlcv_4h: DataFrame with ``ts`` column.
        agg: 'last' (single most recent) or 'avg' (mean over last ``window_hours``).
        window_hours: window for 'avg' aggregation.
        time_col: timestamp column in funding_df.
        value_col: funding rate column.
        tf_hours: OHLCV timeframe.

    Returns:
        pd.Series indexed by ohlcv_4h.index.

    Raises:
        ValueError on bad agg.
    """
    if agg not in {"last", "avg"}:
        raise ValueError(f"agg must be 'last' or 'avg', got {agg!r}")
    if not funding_df[time_col].is_monotonic_increasing:
        raise ValueError(f"funding_df['{time_col}'] must be monotonic ascending")

    bar_close = _bar_close_dt(ohlcv_4h, tf_hours=tf_hours)

    if agg == "last":
        left = pd.DataFrame({"cutoff": bar_close}).reset_index(drop=False).rename(columns={"index": "_idx"})
        left = left.sort_values("cutoff").reset_index(drop=True)
        right = funding_df[[time_col, value_col]].copy()
        right[time_col] = _to_ns_utc(right[time_col])
        right = right.sort_values(time_col).reset_index(drop=True)
        merged = pd.merge_asof(
            left,
            right,
            left_on="cutoff",
            right_on=time_col,
            direction="backward",
            allow_exact_matches=False,
        )
        merged = merged.sort_values("_idx").reset_index(drop=True)
        return pd.Series(merged[value_col].values, index=ohlcv_4h.index, name=value_col)

    # agg == "avg": mean of funding rates in [close - window, close)
    f = funding_df[[time_col, value_col]].copy()
    f[time_col] = _to_ns_utc(f[time_col])
    f = f.sort_values(time_col).reset_index(drop=True)
    # Convert timestamps to int64 ns for fast comparison.
    times_ns = f[time_col].astype("int64").to_numpy()
    vals = f[value_col].to_numpy()
    out = []
    window_ns = int(pd.Timedelta(hours=window_hours).total_seconds() * 1_000_000_000)
    for close_ts in bar_close:
        close_ns_val = int(pd.Timestamp(close_ts).value)
        window_start_ns = close_ns_val - window_ns
        mask = (times_ns >= window_start_ns) & (times_ns < close_ns_val)
        if mask.any():
            out.append(float(vals[mask].mean()))
        else:
            out.append(float("nan"))
    return pd.Series(out, index=ohlcv_4h.index, name=f"{value_col}_avg_{window_hours}h")


def align_dxy_to_4h(
    dxy_df: pd.DataFrame,
    ohlcv_4h: pd.DataFrame,
    lag_days: int = 2,
    date_col: str = "date",
    value_col: str = "dxy",
    tf_hours: int = 4,
) -> pd.Series:
    """For each 4h bar close, return last DXY value available
    (close - lag_days) - ε before. Forward-fills weekends/holidays.

    Args:
        dxy_df: DataFrame with date_col (business days, tz-aware) and value_col.
        ohlcv_4h: DataFrame with ``ts`` column.
        lag_days: conservative publish lag in days (default 2 = FRED + weekend safety).
        date_col, value_col, tf_hours: passthrough.

    Returns:
        pd.Series indexed by ohlcv_4h.index.
    """
    if not dxy_df[date_col].is_monotonic_increasing:
        raise ValueError(f"dxy_df['{date_col}'] must be monotonic ascending")

    bar_close = _bar_close_dt(ohlcv_4h, tf_hours=tf_hours)
    cutoff = bar_close - pd.Timedelta(days=lag_days)

    left = pd.DataFrame({"cutoff": cutoff}).reset_index(drop=False).rename(columns={"index": "_idx"})
    left = left.sort_values("cutoff").reset_index(drop=True)
    right = dxy_df[[date_col, value_col]].dropna(subset=[value_col]).copy()
    right[date_col] = _to_ns_utc(right[date_col])
    right = right.sort_values(date_col).reset_index(drop=True)
    merged = pd.merge_asof(
        left,
        right,
        left_on="cutoff",
        right_on=date_col,
        direction="backward",
        allow_exact_matches=False,
    )
    merged = merged.sort_values("_idx").reset_index(drop=True)
    return pd.Series(merged[value_col].values, index=ohlcv_4h.index, name=value_col)
