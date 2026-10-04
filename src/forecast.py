import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")
OUT = Path("outputs")
H = 12

df = pd.read_csv(OUT / "14_monthly_series.csv", parse_dates=["month_start"])


def build(series_df):
    y = np.log(series_df["median_price"].to_numpy())
    fit = ExponentialSmoothing(
        y, trend="add", damped_trend=True, initialization_method="estimated"
    ).fit()
    return np.exp(np.asarray(fit.forecast(H)))


# Empirical error bands from the backtest (pct_error = (forecast - actual) / actual * 100)
bt = pd.read_csv(OUT / "backtest_detail.csv")
bt = bt[bt.model == "Damped Holt"].copy()
bt["bucket"] = np.where(bt.horizon <= 6, "short", "long")
q = bt.groupby("bucket")["pct_error"].quantile([0.1, 0.9]).unstack()


def forecast_table(series_df, label):
    point = build(series_df)
    last = series_df["median_price"].iloc[-1]
    months = pd.date_range(
        series_df.month_start.iloc[-1] + pd.offsets.MonthBegin(1), periods=H, freq="MS"
    )
    rows = []
    for i, (m, f) in enumerate(zip(months, point), start=1):
        b = "short" if i <= 6 else "long"
        lo = f / (1 + q.loc[b, 0.9] / 100)
        hi = f / (1 + q.loc[b, 0.1] / 100)
        rows.append({"month_start": m, "forecast_holt": f, "naive": last,
                     "lo80": lo, "hi80": hi})
    out = pd.DataFrame(rows)
    print(f"\n{label}: last observed month {series_df.month_start.iloc[-1]:%Y-%m}, "
          f"implied change over 12 months = {100 * (point[-1] / last - 1):+.1f}%")
    return out


full = forecast_table(df, "Full series")
full.round(0).to_csv(OUT / "15_forecast.csv", index=False)
print(full.round(0).to_string(index=False))

trimmed = forecast_table(df.iloc[:-2], "Sensitivity: last 2 months dropped")
print(f"Month-12 forecast: full = {full.forecast_holt.iloc[-1]:,.0f}, "
      f"trimmed = {trimmed.forecast_holt.iloc[-1]:,.0f}")
print("\nError bands used (percent):")
print(q.round(2))