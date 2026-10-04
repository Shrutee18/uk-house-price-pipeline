from pathlib import Path

import duckdb
import pandas as pd

from ingest import COLUMNS

HOLDOUT = Path("data/holdout/pp-2026.csv")
OUT = Path("outputs")

con = duckdb.connect()
actual = con.execute(
    f"""
    SELECT
        DATE_TRUNC('month', CAST(date_of_transfer AS DATE))::DATE AS month_start,
        COUNT(*) AS sales,
        MEDIAN(price) AS actual_median
    FROM read_csv('{HOLDOUT}', header=false, columns={COLUMNS})
    WHERE UPPER(TRIM(county)) = 'GREATER MANCHESTER'
      AND ppd_category_type = 'A'
      AND record_status != 'D'
    GROUP BY 1
    ORDER BY 1
    """
).df()
actual["month_start"] = pd.to_datetime(actual["month_start"])

forecast = pd.read_csv(OUT / "15_forecast.csv", parse_dates=["month_start"])
history = pd.read_csv(OUT / "14_monthly_series.csv", parse_dates=["month_start"])

typical = history[history.month_start.dt.year == 2025]["sales"].mean()
df = actual.merge(forecast, on="month_start", how="inner")
df["complete"] = df["sales"] >= 0.75 * typical

df["trend_err_pct"] = 100 * (df.forecast_holt - df.actual_median) / df.actual_median
df["naive_err_pct"] = 100 * (df.naive - df.actual_median) / df.actual_median
df["inside_80_range"] = (df.actual_median >= df.lo80) & (df.actual_median <= df.hi80)

print(f"Typical 2025 month: {typical:,.0f} sales. Months below 75% of that are flagged incomplete.\n")
cols = ["month_start", "sales", "complete", "actual_median", "forecast_holt",
        "naive", "trend_err_pct", "naive_err_pct", "inside_80_range"]
print(df[cols].round(1).to_string(index=False))

ok = df[df.complete]
if len(ok):
    print(f"\nComplete months only ({len(ok)}):")
    print(f"  Trend scenario average absolute error: {ok.trend_err_pct.abs().mean():.2f}%")
    print(f"  Naive (no change) average absolute error: {ok.naive_err_pct.abs().mean():.2f}%")
    print(f"  Actual inside the 80% range: {int(ok.inside_80_range.sum())} of {len(ok)}")

df.round(2).to_csv(OUT / "16_forecast_check.csv", index=False)