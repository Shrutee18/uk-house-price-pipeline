import subprocess
import sys
import time

from ingest import ingest
from clean import clean
from analyse import analyse
from load_cpi import load_cpi


def run_step(name, func):
    print(f"\n=== {name} ===")
    start = time.time()
    func()
    print(f"{name} finished in {time.time() - start:.1f}s")


def run_tests():
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"])
    if result.returncode != 0:
        sys.exit("Data quality tests failed. Stopping the pipeline.")


def main():
    run_step("Ingest", ingest)
    run_step("Clean", clean)
    run_step("Load CPI", load_cpi)
    run_step("Data quality tests", run_tests)
    run_step("Analyse", analyse)
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()