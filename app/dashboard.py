from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

OUT = Path(__file__).resolve().parent.parent / "outputs"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.set_page_config(page_title="Greater Manchester House Prices", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


nominal = load("06_price_index.csv")
real = load("12_real_price_index.csv")
borough_real = load("13_borough_real_growth.csv")
rolling = load("08_rolling_12m.csv")
rolling["month_start"] = pd.to_datetime(rolling["month_start"])
volume = load("09_volume_index.csv")
flats = load("10_flats_vs_houses.csv")
rank = load("11_gm_rank_by_year.csv")
season = load("03_seasonality.csv")

history = load("14_monthly_series.csv")
history["month_start"] = pd.to_datetime(history["month_start"])
forecast = load("15_forecast.csv")
forecast["month_start"] = pd.to_datetime(forecast["month_start"])
check = load("16_forecast_check.csv")
check["month_start"] = pd.to_datetime(check["month_start"])
backtest = load("backtest_summary.csv")

# ---------- Sidebar controls ----------
st.sidebar.header("Filters")
min_year, max_year = int(nominal.sale_year.min()), int(nominal.sale_year.max())
y0, y1 = st.sidebar.slider("Year range", min_year, max_year, (min_year, max_year))
all_boroughs = sorted(borough_real["district"].unique())
chosen = st.sidebar.multiselect(
    "Boroughs", all_boroughs, default=all_boroughs, format_func=str.title
)
basis = st.sidebar.radio("Price basis", ["Nominal", "Real (2025 prices)"])
st.sidebar.caption(
    "Real prices are adjusted with the ONS CPI all-items index (series D7BT), "
    "so they show growth after general inflation."
)

# ---------- KPI calculations ----------
gm_nom = nominal[nominal.area == "Greater Manchester"].sort_values("sale_year")
gm_real = real[real.area == "Greater Manchester"].sort_values("sale_year")
gm_vol = volume[volume.area == "Greater Manchester"].sort_values("sale_year")
gm_rank = rank.sort_values("sale_year")

latest = int(gm_nom.sale_year.max())
nom_growth = gm_nom.price_index_2018.iloc[-1] - 100
real_growth = gm_real.real_price_index_2018.iloc[-1] - 100
rank_now = gm_rank.iloc[-1]
rank_then = gm_rank.iloc[0]
vol_now = gm_vol.volume_index_2018.iloc[-1]

# ---------- Header ----------
st.title("Greater Manchester House Prices, 2018 to 2025")
st.caption(
    "HM Land Registry Price Paid Data, standard market sales only. "
    "Real prices use ONS CPI. 2025 is the latest full year and may be revised."
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"Median price {latest}", f"£{gm_nom.median_price.iloc[-1]:,.0f}")
c2.metric("Growth since 2018 (nominal)", f"{nom_growth:+.1f}%")
c3.metric("Growth since 2018 (real)", f"{real_growth:+.1f}%")
c4.metric(
    "County price rank",
    f"{int(rank_now.price_rank)} of {int(rank_now.counties_ranked)}",
    f"{int(rank_then.price_rank - rank_now.price_rank):+d} places since {int(rank_then.sale_year)}",
)
c5.metric("Sales volume vs 2018", f"{vol_now:.0f}%", f"{vol_now - 100:+.0f} pts")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Prices over time", "Boroughs", "Market activity", "Seasonality", "Forecast"]
)

# ---------- Tab 1: prices over time ----------
with tab1:
    if basis == "Nominal":
        df, ycol, label = nominal, "price_index_2018", "Price index (2018 = 100), nominal"
    else:
        df, ycol, label = real, "real_price_index_2018", "Price index (2018 = 100), real"
    df = df[(df.sale_year >= y0) & (df.sale_year <= y1)]
    st.subheader(label)
    fig = px.line(df, x="sale_year", y=ycol, color="area", markers=True,
                  labels={"sale_year": "", ycol: "Index", "area": ""})
    fig.add_hline(y=100, line_dash="dot")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The 'Rest of England and Wales' line here excludes London.")

    st.subheader("Rolling 12-month median price, Greater Manchester (nominal)")
    r = rolling[(rolling.month_start.dt.year >= y0) & (rolling.month_start.dt.year <= y1)]
    fig = px.line(r, x="month_start", y="rolling_12m_median",
                  labels={"month_start": "", "rolling_12m_median": "Median price (£)"})
    st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 2: boroughs ----------
with tab2:
    b = borough_real[borough_real.district.isin(chosen)].copy()
    b["district"] = b["district"].str.title()
    st.subheader("Growth 2018 to 2025 by borough: nominal vs real")
    long = b.melt(id_vars="district", value_vars=["nominal_growth_pct", "real_growth_pct"],
                  var_name="measure", value_name="growth_pct")
    long["measure"] = long["measure"].map(
        {"nominal_growth_pct": "Nominal", "real_growth_pct": "Real"})
    order = b.sort_values("real_growth_pct")["district"].tolist()
    fig = px.bar(long, x="growth_pct", y="district", color="measure", barmode="group",
                 orientation="h", category_orders={"district": order},
                 labels={"growth_pct": "Total growth (%)", "district": "", "measure": ""})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Do flats explain slower growth?")
    f = flats[flats.district.isin(chosen)]
    wide = f.pivot(index="district", columns="kind", values="cagr_pct")
    share = f[f.kind == "Flat"].set_index("district")["share_of_sales_pct"]
    wide["flat_share_pct"] = share
    wide["gap"] = wide["House"] - wide["Flat"]
    wide = wide.reset_index()
    wide["district"] = wide["district"].str.title()
    fig = px.scatter(wide, x="flat_share_pct", y="gap", text="district",
                     labels={"flat_share_pct": "Flats as % of sales",
                             "gap": "House growth minus flat growth (pts per year)"})
    fig.update_traces(textposition="top center", marker_size=10)
    fig.add_hline(y=0, line_dash="dot")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Growth is compound annual (nominal). Small boroughs have few flat sales, "
        "so their flat figures are noisy."
    )

# ---------- Tab 3: market activity ----------
with tab3:
    st.subheader("Sales volume index (2018 = 100)")
    v = volume[(volume.sale_year >= y0) & (volume.sale_year <= y1)]
    fig = px.line(v, x="sale_year", y="volume_index_2018", color="area", markers=True,
                  labels={"sale_year": "", "volume_index_2018": "Index", "area": ""})
    fig.add_hline(y=100, line_dash="dot")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Here 'Rest of England and Wales' includes London.")

    st.subheader("Greater Manchester rank among counties by median price")
    rk = rank[(rank.sale_year >= y0) & (rank.sale_year <= y1)]
    fig = px.line(rk, x="sale_year", y="price_rank", markers=True,
                  labels={"sale_year": "", "price_rank": "Rank (1 = most expensive)"})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 4: seasonality ----------
with tab4:
    st.subheader("Seasonality of sales volume (100 = average month for that year)")
    s = season.copy()
    s["sale_year"] = s["sale_year"].astype(str)
    avg = season.groupby("sale_month", as_index=False)["sales_index"].mean()
    fig = px.line(s, x="sale_month", y="sales_index", color="sale_year",
                  labels={"sale_month": "", "sales_index": "Sales index", "sale_year": "Year"})
    fig.update_traces(opacity=0.35)
    fig.add_scatter(x=avg["sale_month"], y=avg["sales_index"], mode="lines+markers",
                    name="Average", line=dict(width=4, color="black"))
    fig.add_hline(y=100, line_dash="dot")
    fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTHS)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 5: forecast ----------
with tab5:
    st.subheader("Scenario: Greater Manchester median price, next 12 months (nominal)")
    st.caption(
        "A scenario, not a prediction. In backtests, a simple 'no change' assumption was "
        "about as accurate as any model tested."
    )
    h = history[history.month_start >= "2023-01-01"]
    fig = go.Figure()
    fig.add_scatter(x=h.month_start, y=h.median_price, name="Actual monthly median",
                    mode="lines")
    fig.add_scatter(x=forecast.month_start, y=forecast.hi80, mode="lines",
                    line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=forecast.month_start, y=forecast.lo80, mode="lines",
                    line=dict(width=0), fill="tonexty", name="Approx. 80% range")
    fig.add_scatter(x=forecast.month_start, y=forecast.forecast_holt, mode="lines",
                    name="Damped trend scenario", line=dict(dash="dash"))
    fig.add_scatter(x=forecast.month_start, y=forecast.naive, mode="lines",
                    name="No change from Dec 2025", line=dict(dash="dot"))

    done = check[check.complete]
    partial = check[~check.complete]
    fig.add_scatter(x=done.month_start, y=done.actual_median, mode="markers",
                    name="2026 actual (complete month)",
                    marker=dict(size=11, symbol="diamond"))
    fig.add_scatter(x=partial.month_start, y=partial.actual_median, mode="markers",
                    name="2026 actual (incomplete, may be revised)",
                    marker=dict(size=9, symbol="circle-open"))
    fig.update_layout(yaxis_title="Median price (£)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Actual 2026 sales arrived after the forecast was fixed. Months with few "
        "registered sales are shown as open circles."
    )

    st.subheader("How the models performed in backtesting")
    bt = backtest.rename(columns={
        "model": "Model", "mape": "Average error (%)", "bias_pct": "Bias (%)",
        "mape_12m_ahead": "Error 12 months ahead (%)",
        "mape_3m_ahead": "Error 3 months ahead (%)"})
    st.dataframe(bt, hide_index=True, use_container_width=True)
    st.markdown(
        "- Models were tested on 7 rolling start points, each forecasting 12 months ahead.\n"
        "- The shaded range is built from the damped trend model's past errors, "
        "so it is approximate; a shock such as a rate change could fall outside it.\n"
        "- The December 2025 starting point was a weak month, so the trend scenario "
        "starts above it.\n"
        "- Only two 2026 months (February and March) had enough registered sales to judge "
        "fairly. In those, the no-change line was closer than the trend scenario."
    )

with st.expander("Notes and limitations"):
    st.markdown(
        "- Medians are not adjusted for property mix. Areas with more flats look cheaper.\n"
        "- Real prices use annual average CPI, which measures consumer prices generally, "
        "not housing costs or wages, so they do not measure affordability.\n"
        "- Growth figures compare 2018 with 2025 only, and 2025 may be revised.\n"
        "- Monthly figures rest on a few thousand sales each, so small swings are likely noise.\n"
        "- The comparison group differs between charts: it excludes London in the price index "
        "and includes London in the volume index.\n"
        "- The forecast is a scenario. Its range comes from a small number of backtests "
        "and does not account for interest rate or policy changes."
    )

st.divider()
st.caption(
    "Contains HM Land Registry data © Crown copyright and database right 2021. "
    "This data is licensed under the Open Government Licence v3.0. "
    "Inflation data: Office for National Statistics, CPI INDEX 00: ALL ITEMS 2015=100 (D7BT), "
    "Open Government Licence."
)