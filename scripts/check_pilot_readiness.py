"""Print a JSON readiness report for staged Puri pilot CSV files.

Usage:
    python scripts/check_pilot_readiness.py \
        --habitations data/pilot/processed/habitations.csv \
        --shelters data/pilot/processed/shelters.csv

This script never fills or estimates missing values. It is a gate/check only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.pilot_readiness import pilot_readiness


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check authoritative Puri pilot data readiness")
    parser.add_argument("--habitations", required=True, help="Path to staged/enriched habitation CSV")
    parser.add_argument("--shelters", required=True, help="Path to staged/enriched shelter CSV")
    parser.add_argument(
        "--fail-if-not-ready",
        action="store_true",
        help="Exit with status 1 when either dataset is not operational-ready",
    )
    return parser.parse_args()


def _load_csv(path_value: str, label: str) -> pd.DataFrame:
    path = Path(path_value)
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    return pd.read_csv(path)


def main() -> int:
    args = parse_args()
    habitations = _load_csv(args.habitations, "habitations")
    shelters = _load_csv(args.shelters, "shelters")
    report = pilot_readiness(habitations, shelters)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.fail_if_not_ready and not report["operational_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
