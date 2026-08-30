from math import radians, sin, cos, sqrt, atan2
from pathlib import Path


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlambda / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def load_hazard_layer(path: str | Path):
    """Load a vector hazard layer and normalize it to WGS84.

    The function imports GeoPandas lazily so core non-GIS unit tests can still
    import the package in constrained environments.
    """
    import geopandas as gpd

    gdf = gpd.read_file(Path(path))
    if gdf.empty:
        raise ValueError("hazard layer is empty")
    if "hazard_score" not in gdf.columns:
        raise ValueError("hazard layer must contain a hazard_score field")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif str(gdf.crs).upper() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def calculate_hazard_exposure(habitation: dict, hazard_data=None) -> dict:
    """Calculate hazard intensity from a vector hazard layer when provided.

    If no geospatial layer is supplied, an existing `hazard_score` is passed
    through and explicitly labelled as provided/demo data.

    For vector layers:
    - inside one or more polygons -> maximum intersecting hazard score;
    - outside all polygons -> proximity-decayed score within 10 km of the
      nearest polygon, otherwise zero.
    """
    if hazard_data is None:
        score = _bounded(habitation.get("hazard_score", 0))
        return {
            "hazard_score": score,
            "hazard_source": "provided_or_demo",
            "inside_hazard_zone": None,
            "distance_to_hazard_km": None,
            "hazard_type": None,
        }

    import geopandas as gpd
    from shapely.geometry import Point

    hazards = load_hazard_layer(hazard_data) if isinstance(hazard_data, (str, Path)) else hazard_data.copy()
    if hazards.crs is None:
        hazards = hazards.set_crs("EPSG:4326")
    elif str(hazards.crs).upper() != "EPSG:4326":
        hazards = hazards.to_crs("EPSG:4326")

    point = Point(float(habitation["longitude"]), float(habitation["latitude"]))
    intersecting = hazards[hazards.geometry.intersects(point)]

    if not intersecting.empty:
        chosen = intersecting.loc[intersecting["hazard_score"].astype(float).idxmax()]
        return {
            "hazard_score": _bounded(chosen["hazard_score"]),
            "hazard_source": chosen.get("source", "vector_intersection"),
            "inside_hazard_zone": True,
            "distance_to_hazard_km": 0.0,
            "hazard_type": chosen.get("hazard_type"),
        }

    # Use a projected CRS for metric distance calculations.
    point_gdf = gpd.GeoDataFrame(
        [{"geometry": point}], geometry="geometry", crs="EPSG:4326"
    ).to_crs("EPSG:3857")
    hazards_m = hazards.to_crs("EPSG:3857")
    distances_m = hazards_m.geometry.distance(point_gdf.geometry.iloc[0])
    nearest_index = distances_m.idxmin()
    distance_km = float(distances_m.loc[nearest_index]) / 1000.0
    nearest = hazards.loc[nearest_index]
    nearest_score = _bounded(nearest["hazard_score"])
    proximity_factor = max(0.0, 1.0 - distance_km / 10.0)
    score = nearest_score * proximity_factor

    return {
        "hazard_score": round(score, 2),
        "hazard_source": nearest.get("source", "vector_proximity"),
        "inside_hazard_zone": False,
        "distance_to_hazard_km": round(distance_km, 2),
        "hazard_type": nearest.get("hazard_type"),
    }
