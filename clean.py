"""
Clean, merge and deduplicate monthly order exports into one trusted dataset.

Usage:
    python clean.py --input data/raw --output data/clean --report reports
"""

import argparse
import logging
import sys
from pathlib import Path

from cleaning import pipeline, report


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean and merge monthly order exports.")
    ap.add_argument("--input", type=Path, default=Path("data/raw"), help="folder with .csv/.xlsx exports")
    ap.add_argument("--output", type=Path, default=Path("data/clean"), help="folder for clean outputs")
    ap.add_argument("--report", type=Path, default=Path("reports"), help="folder for the quality report")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")
    try:
        stats = pipeline.run(args.input, args.output)
    except (FileNotFoundError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    path = report.write(stats, args.report)
    d = stats["duplicates"]
    print(f"{stats['rows_in']:,} raw rows -> {stats['orders_out']:,} clean orders, "
          f"{stats['customers_out']:,} customers")
    print(f"removed {d['within_file'] + d['across_files']:,} duplicates, "
          f"{stats['empty_rows']:,} empty rows, rejected {stats['rejected_rows']:,} rows")
    print(f"outputs in {args.output}/, report at {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
