from pathlib import Path
import duckdb
import pytest

DB_PATH = Path("data/warehouse/house_prices.duckdb")

EXPECTED_GM_DISTRICTS = {
    "MANCHESTER", "SALFORD", "TRAFFORD", "STOCKPORT", "TAMESIDE",
    "OLDHAM", "ROCHDALE", "BURY", "BOLTON", "WIGAN",
}


@pytest.fixture(scope="module")
def con():
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_clean_table_is_not_empty(con):
    assert scalar(con, "SELECT COUNT(*) FROM clean_ppd") > 1_000_000


def test_transaction_ids_are_unique(con):
    total = scalar(con, "SELECT COUNT(*) FROM clean_ppd")
    distinct = scalar(con, "SELECT COUNT(DISTINCT transaction_id) FROM clean_ppd")
    assert total == distinct


def test_prices_are_positive(con):
    assert scalar(con, "SELECT COUNT(*) FROM clean_ppd WHERE price <= 0") == 0


def test_no_missing_dates(con):
    assert scalar(con, "SELECT COUNT(*) FROM clean_ppd WHERE date_of_transfer IS NULL") == 0


def test_sale_years_are_expected(con):
    years = {r[0] for r in con.execute("SELECT DISTINCT sale_year FROM clean_ppd").fetchall()}
    assert years == set(range(2018, 2026))

def test_property_types_are_valid(con):
    types = {r[0] for r in con.execute("SELECT DISTINCT property_type FROM clean_ppd").fetchall()}
    assert types.issubset({"D", "S", "T", "F", "O"})


def test_cleaning_does_not_remove_too_much(con):
    raw = scalar(con, "SELECT COUNT(*) FROM raw_ppd")
    clean = scalar(con, "SELECT COUNT(*) FROM clean_ppd")
    assert clean / raw > 0.95


def test_most_postcode_districts_extracted(con):
    missing = scalar(con, "SELECT COUNT(*) FROM clean_ppd WHERE postcode_district IS NULL")
    total = scalar(con, "SELECT COUNT(*) FROM clean_ppd")
    assert missing / total < 0.05


def test_all_greater_manchester_districts_present(con):
    found = {
        r[0] for r in con.execute(
            "SELECT DISTINCT district FROM clean_ppd WHERE is_greater_manchester"
        ).fetchall()
    }
    assert EXPECTED_GM_DISTRICTS.issubset(found), f"Missing: {EXPECTED_GM_DISTRICTS - found}"


def test_median_price_is_plausible(con):
    median = scalar(con, "SELECT MEDIAN(price) FROM clean_ppd WHERE ppd_category_type = 'A'")
    assert 150_000 < median < 500_000

def test_cpi_covers_all_years(con):
    years = {r[0] for r in con.execute("SELECT year FROM cpi_annual").fetchall()}
    assert set(range(2018, 2026)).issubset(years)