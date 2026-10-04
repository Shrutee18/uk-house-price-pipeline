from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

OUT = Path(__file__).resolve().parent.parent / "outputs"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.set_page_config(page_title="Greater Manchester House Prices", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


growth = load("01_gm_price_growth.csv")
ptype = load("02_property_type.csv")
season = load("03_seasonality.csv")
compare = load("04_gm_vs_rest.csv")
county = load("05_county_ranking.csv")

# ---------- KPI calculations ----------
gm = compare[compare["area"] == "Greater Manchester"].set_index("sale_year")
rest = compare[compare["area"] == "Rest of England and Wales"].set_index("sale_year")
latest = int(gm.index.max())
prev = latest - 1

gm_median = gm.loc[latest, "median_price"]
gm_growth = 100 * (gm_median / gm.loc[prev, "median_price"] - 1)
rest_growth = 100 * (rest.loc[latest, "median_price"] / rest.loc[prev, "median_price"] - 1)
gap_pct = 100 * gm_median / rest.loc[latest, "median_price"]
gm_sales = int(gm.loc[latest, "sales"])

gm_row = county[county["county"] == "GREATER MANCHESTER"]
rank_text = (
    f"{int(gm_row['price_rank'].iloc[0])} of {len(county)}" if not gm_row.empty else "n/a"
)

# ---------- Layout ----------
st.title("Greater Manchester House Prices")
st.caption(f"HM Land Registry Price Paid Data, {prev} to {latest}. Standard market sales only.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"Median price {latest}", f"£{gm_median:,.0f}")
c2.metric("Change on previous year", f"{gm_growth:+.1f}%", f"{gm_growth - rest_growth:+.1f} pts vs rest")
c3.metric("Sales", f"{gm_sales:,}")
c4.metric("Price vs rest of E&W", f"{gap_pct:.0f}%")
c5.metric("County price rank", rank_text)

left, right = st.columns(2)

with left:
    st.subheader(f"Price growth by borough, {prev} to {latest}")
    g = growth[growth["sale_year"] == latest].copy()
    g["district"] = g["district"].str.title()
    g = g.sort_values("yoy_growth_pct")
    fig = px.bar(g, x="yoy_growth_pct", y="district", orientation="h",
                 text="yoy_growth_pct", labels={"yoy_growth_pct": "Change in median price (%)", "district": ""})
    fig.update_traces(texttemplate="%{text:.1f}%")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Median price by property type")
    fig = px.bar(ptype, x="property_type_label", y="median_price", color="area",
                 barmode="group",
                 labels={"property_type_label": "", "median_price": "Median price (£)", "area": ""})
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Seasonality of sales volume (100 = average month for that year)")
s = season.copy()
s["sale_year"] = s["sale_year"].astype(str)
fig = px.line(s, x="sale_month", y="sales_index", color="sale_year", markers=True,
              labels={"sale_month": "", "sales_index": "Sales index", "sale_year": "Year"})
fig.add_hline(y=100, line_dash="dot")
fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTHS)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Notes and limitations"):
    st.markdown(
        "- Growth figures compare two calendar years only, so they are a single year-on-year change, not a trend.\n"
        "- Medians are not adjusted for property mix. Areas with more flats look cheaper.\n"
        "- The comparison group (rest of England and Wales) includes London, which raises its medians.\n"
        "- Monthly medians are based on 2,000 to 3,300 sales each, so small swings are likely noise."
    )

st.divider()
st.caption(
    "Contains HM Land Registry data © Crown copyright and database right 2021. "
    "This data is licensed under the Open Government Licence v3.0."
)