import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

OUT = Path("outputs")
H = 12            # forecast horizon in months
MIN_TRAIN = 48    # smallest training window in months


def naive(y, h):
    return np.repeat(y[-1], h)


def drift(y, h):
    slope = (y[-1] - y[0]) / (len(y) - 1)
    return y[-1] + slope * np.arange(1, h + 1)


def holt_damped(y, h):
    fit = ExponentialSmoothing(
        y, trend="add", damped_trend=True, initialization_method="estimated"
    ).fit()
    return np.asarray(fit.forecast(h))


def arima111(y, h):
    return np.asarray(ARIMA(y, order=(1, 1, 1)).fit().forecast(h))


MODELS = {
    "Naive": naive,
    "Drift": drift,
    "Damped Holt": holt_damped,
    "ARIMA(1,1,1)": arima111,
}


def main():
    df = pd.read_csv(OUT / "14_monthly_series.csv", parse_dates=["month_start"])
    print(f"{len(df)} months, {df.month_start.min():%Y-%m} to {df.month_start.max():%Y-%m}")
    print("\nSales in the last 6 months (low counts suggest late registrations):")
    print(df.tail(6)[["month_start", "sales"]].to_string(index=False))

    y = np.log(df["median_price"].to_numpy())   # model log prices
    n = len(y)

    rows = []
    for train_end in range(MIN_TRAIN, n - H + 1, 6):
        train = y[:train_end]
        actual = np.exp(y[train_end:train_end + H])
        for name, model in MODELS.items():
            pred = np.exp(model(train, H))
            for step in range(H):
                rows.append({
                    "origin": df.month_start.iloc[train_end - 1].strftime("%Y-%m"),
                    "model": name,
                    "horizon": step + 1,
                    "actual": actual[step],
                    "forecast": pred[step],
                })

    res = pd.DataFrame(rows)
    res["abs_pct_error"] = 100 * (res.forecast - res.actual).abs() / res.actual
    res["pct_error"] = 100 * (res.forecast - res.actual) / res.actual
    res.to_csv(OUT / "backtest_detail.csv", index=False)

    summary = res.groupby("model").agg(
        mape=("abs_pct_error", "mean"),
        bias_pct=("pct_error", "mean"),
    )
    summary["mape_12m_ahead"] = res[res.horizon == 12].groupby("model")["abs_pct_error"].mean()
    summary["mape_3m_ahead"] = res[res.horizon <= 3].groupby("model")["abs_pct_error"].mean()
    summary = summary.sort_values("mape").round(2)
    summary.to_csv(OUT / "backtest_summary.csv")

    print(f"\nBacktest: {res.origin.nunique()} origins, {H}-month horizon (errors in %)")
    print(summary)


if __name__ == "__main__":
    main()