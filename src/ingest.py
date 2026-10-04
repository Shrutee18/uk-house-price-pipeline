from pathlib import Path
import duckdb

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/warehouse/house_prices.duckdb")

# The Land Registry files have no header row, so we supply the column names.
COLUMNS = {
    "transaction_id": "VARCHAR",
    "price": "BIGINT",
    "date_of_transfer": "TIMESTAMP",
    "postcode": "VARCHAR",
    "property_type": "VARCHAR",   # D=detached, S=semi, T=terraced, F=flat, O=other
    "old_new": "VARCHAR",         # Y=newly built, N=established
    "duration": "VARCHAR",        # F=freehold, L=leasehold
    "paon": "VARCHAR",
    "saon": "VARCHAR",
    "street": "VARCHAR",
    "locality": "VARCHAR",
    "town_city": "VARCHAR",
    "district": "VARCHAR",
    "county": "VARCHAR",
    "ppd_category_type": "VARCHAR",
    "record_status": "VARCHAR",
}


def ingest() -> None:
    files = sorted(RAW_DIR.glob("pp-*.csv"))
    if not files:
        raise FileNotFoundError(f"No pp-*.csv files found in {RAW_DIR}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    file_list = [str(f) for f in files]
    con.execute("DROP TABLE IF EXISTS raw_ppd")
    con.execute(
        f"""
        CREATE TABLE raw_ppd AS
        SELECT
            transaction_id,
            price,
            CAST(date_of_transfer AS DATE) AS date_of_transfer,
            postcode, property_type, old_new, duration,
            paon, saon, street, locality,
            town_city, district, county,
            ppd_category_type, record_status,
            filename AS source_file
        FROM read_csv({file_list}, header=false, columns={COLUMNS}, filename=true)
        """
    )

    rows = con.execute("SELECT COUNT(*) FROM raw_ppd").fetchone()[0]
    print(f"Loaded {rows:,} rows from {len(files)} file(s)")
    print(con.execute("SELECT * FROM raw_ppd LIMIT 5").df())
    con.close()


if __name__ == "__main__":
    ingest()