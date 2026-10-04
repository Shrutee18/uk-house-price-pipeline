from pathlib import Path
import duckdb

DB_PATH = Path("data/warehouse/house_prices.duckdb")
SQL_DIR = Path("sql")
OUT_DIR = Path("outputs")


def analyse() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)

    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        df = con.execute(sql_file.read_text()).df()
        out_path = OUT_DIR / f"{sql_file.stem}.csv"
        df.to_csv(out_path, index=False)
        print(f"\n{sql_file.name} -> {out_path} ({len(df)} rows)")
        print(df.head(10).to_string(index=False))

    con.close()


if __name__ == "__main__":
    analyse()
    