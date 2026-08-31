"""Cache OpenStreetMap drive networks as GraphML for offline routing.

Run this while internet access is available. Large GraphML files normally stay
outside Git and can be regenerated from the documented place names.
"""

from pathlib import Path
import argparse
import re

import osmnx as ox

DEMO_CITY_PLACES = {
    "Puri": "Puri, Odisha, India",
    "Guwahati": "Guwahati, Assam, India",
    "Chennai": "Chennai, Tamil Nadu, India",
}


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


def cache_network_from_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    *,
    name: str = "custom_bbox",
    output_dir: str | Path = "data/cache/roads",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        graph = ox.graph_from_bbox(
            bbox=(min_lon, min_lat, max_lon, max_lat),
            network_type="drive",
            simplify=True,
        )
    except TypeError:
        graph = ox.graph_from_bbox(
            north=max_lat,
            south=min_lat,
            east=max_lon,
            west=min_lon,
            network_type="drive",
            simplify=True,
        )
    output_path = output_dir / f"{safe_filename(name)}.graphml"
    ox.save_graphml(graph, filepath=output_path)
    return output_path


def cache_demo_cities(output_dir: str | Path = "data/cache/roads") -> list[Path]:
    paths = []
    for city, place in DEMO_CITY_PLACES.items():
        print(f"Caching {city}: {place}")
        paths.append(cache_network(place, output_dir))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache OSM driving networks for offline routing")
    parser.add_argument("place", nargs="?", help="Geocodable place, e.g. 'Puri, Odisha, India'")
    parser.add_argument("--output-dir", default="data/cache/roads")
    parser.add_argument(
        "--demo-cities",
        action="store_true",
        help="Cache Puri, Guwahati and Chennai demo road networks",
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Cache a custom bounding box",
    )
    parser.add_argument("--name", default="custom_bbox", help="Filename label for --bbox mode")
    args = parser.parse_args()

    if args.demo_cities:
        for path in cache_demo_cities(args.output_dir):
            print(f"Cached road network: {path}")
        return

    if args.bbox:
        path = cache_network_from_bbox(*args.bbox, name=args.name, output_dir=args.output_dir)
        print(f"Cached road network: {path}")
        return

    if not args.place:
        parser.error("provide a place, --demo-cities, or --bbox")

    path = cache_network(args.place, args.output_dir)
    print(f"Cached road network: {path}")


if __name__ == "__main__":
    main()
