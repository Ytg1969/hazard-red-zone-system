"""Generate deterministic synthetic SIH26191 demo datasets.

The generated records are for DEMO/integration testing only. They must never be
presented as official observations or used to claim scientific model accuracy.
"""

from pathlib import Path
import argparse

import numpy as np
import pandas as pd


DEFAULT_CENTER = (20.2961, 85.8245)  # Bhubaneswar-area demo anchor only


def generate_demo_data(
    habitation_count: int = 200,
    shelter_count: int = 20,
    seed: int = 26191,
    output_dir: str | Path = "data/demo/generated",
) -> tuple[Path, Path]:
    rng = np.random.default_rng(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    center_lat, center_lon = DEFAULT_CENTER
    districts = ["DEMO_A", "DEMO_B", "DEMO_C"]

    populations = rng.integers(250, 4200, size=habitation_count)
    children_share = rng.uniform(0.12, 0.28, size=habitation_count)
    elderly_share = rng.uniform(0.05, 0.16, size=habitation_count)
    children = (populations * children_share).astype(int)
    elderly = (populations * elderly_share).astype(int)

    habitations = pd.DataFrame(
        {
            "habitation_id": [f"H{i:04d}" for i in range(1, habitation_count + 1)],
            "state_code": "OD",
            "district_code": rng.choice(districts, size=habitation_count),
            "village_code": [f"V{i:05d}" for i in range(1, habitation_count + 1)],
            "name": [f"Demo Habitation {i:03d}" for i in range(1, habitation_count + 1)],
            "latitude": center_lat + rng.normal(0, 0.18, size=habitation_count),
            "longitude": center_lon + rng.normal(0, 0.18, size=habitation_count),
            "population": populations,
            "children_population": children,
            "elderly_population": elderly,
            "hazard_score": rng.uniform(10, 98, size=habitation_count).round(2),
            "exposure_score": rng.uniform(10, 95, size=habitation_count).round(2),
            "vulnerability_score": np.nan,
            "accessibility_score": rng.uniform(10, 90, size=habitation_count).round(2),
            "risk_score": np.nan,
            "risk_level": "",
            "relocation_priority": "",
            "data_timestamp": "2026-08-30T00:00:00Z",
            "data_mode": "DEMO",
        }
    )

    total_capacity = rng.integers(250, 1600, size=shelter_count)
    current_occupancy = np.array(
        [rng.integers(0, max(1, int(cap * 0.55))) for cap in total_capacity]
    )
    water_capacity = (total_capacity * rng.uniform(0.70, 1.00, size=shelter_count)).astype(int)
    sanitation_capacity = (total_capacity * rng.uniform(0.65, 1.00, size=shelter_count)).astype(int)
    access_capacity = (total_capacity * rng.uniform(0.60, 1.00, size=shelter_count)).astype(int)

    shelters = pd.DataFrame(
        {
            "shelter_id": [f"S{i:03d}" for i in range(1, shelter_count + 1)],
            "name": [f"Demo Safe Shelter {i:02d}" for i in range(1, shelter_count + 1)],
            "latitude": center_lat + rng.normal(0, 0.20, size=shelter_count),
            "longitude": center_lon + rng.normal(0, 0.20, size=shelter_count),
            "total_capacity": total_capacity,
            "current_occupancy": current_occupancy,
            "water_capacity": water_capacity,
            "sanitation_capacity": sanitation_capacity,
            "access_capacity": access_capacity,
            "effective_capacity": np.nan,
            "available_capacity": np.nan,
            "safety_score": rng.uniform(55, 98, size=shelter_count).round(2),
            "accessibility_score": rng.uniform(45, 95, size=shelter_count).round(2),
            "last_updated": "2026-08-30T00:00:00Z",
            "data_mode": "DEMO",
        }
    )

    habitation_path = output_dir / "habitations_200.csv"
    shelter_path = output_dir / "shelters_20.csv"
    habitations.to_csv(habitation_path, index=False)
    shelters.to_csv(shelter_path, index=False)
    return habitation_path, shelter_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic DEMO datasets")
    parser.add_argument("--habitations", type=int, default=200)
    parser.add_argument("--shelters", type=int, default=20)
    parser.add_argument("--seed", type=int, default=26191)
    parser.add_argument("--output-dir", default="data/demo/generated")
    args = parser.parse_args()

    habitation_path, shelter_path = generate_demo_data(
        habitation_count=args.habitations,
        shelter_count=args.shelters,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    print(f"Generated {habitation_path}")
    print(f"Generated {shelter_path}")


if __name__ == "__main__":
    main()
