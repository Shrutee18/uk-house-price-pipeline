from pathlib import Path
import duckdb

DB_PATH = Path("data/warehouse/house_prices.duckdb")

GREATER_MANCHESTER_DISTRICTS = (
    "MANCHESTER", "SALFORD", "TRAFFORD", "STOCKPORT", "TAMESIDE",
    "OLDHAM", "ROCHDALE", "BURY", "BOLTON", "WIGAN",
)


def clean() -> None:
    con = duckdb.connect(str(DB_PATH))

    raw = con.execute("SELECT COUNT(*) FROM raw_ppd").fetchone()[0]
    print(f"Raw rows: {raw:,}")

    gm_list = ", ".join(f"'{d}'" for d in GREATER_MANCHESTER_DISTRICTS)

    con.execute("DROP TABLE IF EXISTS clean_ppd")
    con.execute(
        f"""
        CREATE TABLE clean_ppd AS
        WITH filtered AS (
            SELECT *
            FROM raw_ppd
            WHERE record_status != 'D'          -- D = record deleted by Land Registry
              AND price > 0
              AND date_of_transfer IS NOT NULL
        ),
        deduped AS (
            SELECT *
            FROM filtered
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY transaction_id
                ORDER BY source_file DESC
            ) = 1
        )
        SELECT
            transaction_id,
            price,
            date_of_transfer,
            EXTRACT(year FROM date_of_transfer)::INTEGER  AS sale_year,
            EXTRACT(month FROM date_of_transfer)::INTEGER AS sale_month,
            DATE_TRUNC('month', date_of_transfer)::DATE   AS sale_month_start,
            UPPER(TRIM(postcode))                         AS postcode,
            REGEXP_EXTRACT(UPPER(TRIM(postcode)), '^([A-Z]{{1,2}}[0-9][A-Z0-9]?)', 1)
                                                          AS postcode_district,
            property_type,
            CASE property_type
                WHEN 'D' THEN 'Detached'
                WHEN 'S' THEN 'Semi-detached'
                WHEN 'T' THEN 'Terraced'
                WHEN 'F' THEN 'Flat/Maisonette'
                ELSE 'Other'
            END                                           AS property_type_label,
            CASE old_new WHEN 'Y' THEN 'New build' ELSE 'Established' END
                                                          AS build_status,
            CASE duration WHEN 'F' THEN 'Freehold' ELSE 'Leasehold' END
                                                          AS tenure,
            UPPER(TRIM(town_city))                        AS town_city,
            UPPER(TRIM(district))                         AS district,
            UPPER(TRIM(county))                           AS county,
            ppd_category_type,
            (UPPER(TRIM(county)) = 'GREATER MANCHESTER'
             OR UPPER(TRIM(district)) IN ({gm_list})
             AND UPPER(TRIM(county)) = 'GREATER MANCHESTER') AS is_greater_manchester,
            (price > 5000000)                             AS is_high_value
        FROM deduped
        """
    )

    cleaned = con.execute("SELECT COUNT(*) FROM clean_ppd").fetchone()[0]
    print(f"Clean rows: {cleaned:,}")
    print(f"Rows removed: {raw - cleaned:,} ({(raw - cleaned) / raw:.2%})")

    print("\nRows by year:")
    print(con.execute(
        "SELECT sale_year, COUNT(*) AS sales FROM clean_ppd GROUP BY 1 ORDER BY 1"
    ).df())

    print("\nGreater Manchester sales by district:")
    print(con.execute(
        """
        SELECT district, COUNT(*) AS sales, ROUND(MEDIAN(price)) AS median_price
        FROM clean_ppd
        WHERE is_greater_manchester
        GROUP BY 1 ORDER BY 2 DESC
        """
    ).df())

    con.close()


if __name__ == "__main__":
    clean()