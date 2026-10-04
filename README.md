# Greater Manchester House Price Analysis, 2018 to 2025

An end-to-end Python data pipeline and interactive dashboard built on HM Land Registry
Price Paid Data: 8.07 million property sales in England and Wales, adjusted for inflation
using ONS CPI.

**Live dashboard:** [ADD STREAMLIT LINK HERE]

## Questions answered
1. How have Greater Manchester house prices changed since 2018, in cash terms and after inflation?
2. Which boroughs grew fastest, and does the housing mix (flats vs houses) explain slower growth?
3. How did sales volumes respond to the pandemic, the stamp duty holiday and rising interest rates?
4. How does Greater Manchester compare with London and the rest of England and Wales?

## Key findings
- Greater Manchester's median price rose 48.5% between 2018 and 2025 (from £164,995 to £245,000).
  After adjusting for CPI inflation, the real rise was 13.6%.
- In real terms, London fell 13.3% and the rest of England and Wales (excluding London) fell 3.5%.
  Greater Manchester was the only one of the three to gain.
- All ten boroughs rose in real terms. Oldham (+26.5%), Rochdale (+21.3%) and Tameside (+20.2%)
  grew fastest. Stockport (+5.7%) and Trafford (+8.0%), the most expensive boroughs in 2018, grew slowest.
- Real prices peaked in 2021 and are about 5% below that peak.
- Greater Manchester rose from 77th to 62nd of 112 counties by median price.
- Flats grew more slowly than houses in every borough. In Manchester, where 39% of sales are flats,
  houses grew 7.2% a year against 3.3% for flats, which explains much of its slower overall growth.
  The pattern does not hold for every borough (Salford shows little difference).
- Sales volumes fell to 84% of the 2018 level in 2020, jumped to 115% in 2021, hit a low of 76% in 2023,
  and had recovered to 87% by 2025.
- [CHECK AGAINST THE SEASONALITY TAB: Sales are consistently lowest in winter and spring and highest from July to October.]

## Architecture
Raw CSVs -> `ingest.py` (DuckDB raw table) -> `clean.py` (clean table) -> `load_cpi.py` (ONS inflation index)
-> `pytest` data quality tests -> `analyse.py` (13 SQL files to CSV outputs) -> Streamlit dashboard

`run_pipeline.py` runs every step in order and stops before producing outputs if any test fails.

## Stack
Python, pandas, DuckDB, SQL (CTEs, window functions, compound growth rates), pytest, Streamlit, Plotly

## Data quality
Eleven automated tests check uniqueness, valid prices and dates, valid property types, complete year
coverage, geography coverage, plausible medians and inflation data coverage. The Land Registry yearly
files contained no duplicates or deleted records, so cleaning removed zero rows. The filters remain as
protection for future monthly update files.

## How to run
1. Download the yearly files `pp-2018.csv` to `pp-2025.csv` from the
   [HM Land Registry yearly files page](https://www.gov.uk/government/statistical-data-sets/price-paid-data-yearly-file)
   into `data/raw/`
2. Download the CPI series D7BT as CSV from the
   [ONS page](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt)
   and save it as `data/reference/ons_cpi_d7bt.csv`
3. `python3 -m venv .venv && source .venv/bin/activate`
4. `pip install -r requirements-pipeline.txt`
5. `python src/run_pipeline.py`
6. `streamlit run app/dashboard.py`

## Limitations
- Medians are not adjusted for property mix. Areas with more flats look cheaper.
- Real prices use annual average CPI, which measures consumer prices generally. They show purchasing power,
  not housing affordability.
- Growth figures compare single-year medians for 2018 and 2025. 2025 is the latest available data and may be
  revised as late registrations arrive.
- Monthly figures rest on a few thousand sales each, so small swings are likely noise.
- The comparison group differs between charts: it excludes London in the price index and includes London
  in the volume index.

## Data sources and licences
Contains HM Land Registry data © Crown copyright and database right 2021. This data is licensed under the
Open Government Licence v3.0. Inflation data: Office for National Statistics, CPI INDEX 00: ALL ITEMS
2015=100 (D7BT), Open Government Licence. This repository contains aggregated outputs only, with no
individual addresses.