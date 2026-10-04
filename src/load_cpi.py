from pathlib import Path
import duckdb
import pandas as pd

CPI_PATH = Path("data/reference/ons_cpi_d7bt.csv")
DB_PATH = Path("data/warehouse/house_prices.duckdb")


def load_cpi() -> None:
    # The ONS file has 8 metadata lines, then rows of (period, value).
    df = pd.read_csv(CPI_PATH, skiprows=8, header=None, names=["period", "cpi"], dtype=str)
    df["period"] = df["period"].str.strip()

    # Keep only annual rows, which look like "2018" (monthly are "2018 JAN", quarterly "2018 Q1").
    annual = df[df["period"].str.fullmatch(r"\d{4}")].copy()
    annual["year"] = annual["period"].astype(int)
    annual["cpi"] = annual["cpi"].astype(float)
    annual = annual[["year", "cpi"]]

    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS cpi_annual")
    con.execute("CREATE TABLE cpi_annual AS SELECT * FROM annual")
    print(f"Loaded {len(annual)} annual CPI values ({annual.year.min()} to {annual.year.max()})")
    print(con.execute("SELECT * FROM cpi_annual WHERE year >= 2018 ORDER BY year").df())
    con.close()


if __name__ == "__main__":
    load_cpi()