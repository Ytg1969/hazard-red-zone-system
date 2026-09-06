"""Cache OpenStreetMap drive networks as GraphML for offline routing.

Run this while internet access is available. Large GraphML files normally stay
outside Git and can be regenerated from the documented place names.

Public Nominatim/Overpass services can be slow or transiently unavailable, so
requests are explicitly bounded and retried. A failed download still fails the
release workflow; this module never fabricates or substitutes road geometry.
"""

from pathlib import Path
import argparse
import re
import sys
import time

import osmnx as ox

DEMO_CITY_PLACES = {
    "Puri": "Puri, Odisha, India",
    "Guwahati": "Guwahati, Assam, India",
    "Chennai": "Chennai, Tamil Nadu, India",
}

DEFAULT_ATTEMPTS = 2
DEFAULT_REQUEST_TIMEOUT = 150
DEFAULT_RETRY_DELAY = 15.0


def safe_filename(place: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", place.strip()).strip("_")
    return value or "road_network"


def _configure_osmnx(request_timeout: int) -> None:
    timeout = max(30, int(request_timeout))
    ox.settings.requests_timeout = timeout
    ox.settings.use_cache = True


def _retry(operation, *, label: str, attempts: int, retry_delay: float):
    attempts = max(1, int(attempts))
    retry_delay = max(0.0, float(retry_delay))
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt >= attempts:
                break
            print(
                f"Road cache attempt {attempt}/{attempts} failed for {label}: {exc}. "
                f"Retrying in {retry_delay:g}s.",
                file=sys.stderr,
                flush=True,
            )
            if retry_delay:
                time.sleep(retry_delay)
    assert last_error is not None
    raise RuntimeError(f"Road cache failed for {label} after {attempts} attempt(s): {last_error}") from last_error


def cache_network(
    place: str,
    output_dir: str | Path = "data/cache/roads",
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _configure_osmnx(request_timeout)

    def build_graph():
        return ox.graph_from_place(place, network_type="drive", simplify=True)

    graph = _retry(build_graph, label=place, attempts=attempts, retry_delay=retry_delay)
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
    attempts: int = DEFAULT_ATTEMPTS,
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _configure_osmnx(request_timeout)

    def build_graph():
        try:
            return ox.graph_from_bbox(
                bbox=(min_lon, min_lat, max_lon, max_lat),
                network_type="drive",
                simplify=True,
            )
        except TypeError:
            return ox.graph_from_bbox(
                north=max_lat,
                south=min_lat,
                east=max_lon,
                west=min_lon,
                network_type="drive",
                simplify=True,
            )

    graph = _retry(build_graph, label=name, attempts=attempts, retry_delay=retry_delay)
    output_path = output_dir / f"{safe_filename(name)}.graphml"
    ox.save_graphml(graph, filepath=output_path)
    return output_path


def cache_demo_cities(
    output_dir: str | Path = "data/cache/roads",
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> list[Path]:
    paths = []
    for city, place in DEMO_CITY_PLACES.items():
        print(f"Caching {city}: {place}", flush=True)
        paths.append(
            cache_network(
                place,
                output_dir,
                attempts=attempts,
                request_timeout=request_timeout,
                retry_delay=retry_delay,
            )
        )
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
    parser.add_argument(
        "--attempts",
        type=int,
        default=DEFAULT_ATTEMPTS,
        help="Maximum attempts for each public OSM road download.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT,
        help="OSMnx/Nominatim/Overpass request timeout in seconds.",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY,
        help="Seconds between failed road-download attempts.",
    )
    args = parser.parse_args()

    common = {
        "attempts": args.attempts,
        "request_timeout": args.request_timeout,
        "retry_delay": args.retry_delay,
    }

    if args.demo_cities:
        for path in cache_demo_cities(args.output_dir, **common):
            print(f"Cached road network: {path}")
        return

    if args.bbox:
        path = cache_network_from_bbox(
            *args.bbox,
            name=args.name,
            output_dir=args.output_dir,
            **common,
        )
        print(f"Cached road network: {path}")
        return

    if not args.place:
        parser.error("provide a place, --demo-cities, or --bbox")

    path = cache_network(args.place, args.output_dir, **common)
    print(f"Cached road network: {path}")


if __name__ == "__main__":
    main()
