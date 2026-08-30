"""Cache an OpenStreetMap drive network as GraphML for offline routing.

Run this before the demo while internet access is available. The resulting
GraphML file is a cache artifact and should normally remain outside Git when it
is large; document the exact place name used so any teammate can regenerate it.
"""

from pathlib import Path
import argparse
import re

import osmnx as ox


def safe_filename(place: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", place.strip()).strip("_")
    return value or "road_network"


def cache_network(place: str, output_dir: str | Path = "data/cache/roads") -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    graph = ox.graph_from_place(place, network_type="drive", simplify=True)
    output_path = output_dir / f"{safe_filename(place)}.graphml"
    ox.save_graphml(graph, filepath=output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache an OSM driving network")
    parser.add_argument("place", help="Geocodable place, e.g. 'Cuttack, Odisha, India'")
    parser.add_argument("--output-dir", default="data/cache/roads")
    args = parser.parse_args()

    path = cache_network(args.place, args.output_dir)
    print(f"Cached road network: {path}")


if __name__ == "__main__":
    main()
