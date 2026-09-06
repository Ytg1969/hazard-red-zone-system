"""Competition-laptop preflight for Hazard Command.

This command is intentionally offline-safe. It runs the deterministic demo and
production gates, checks runtime dependencies and launch prerequisites, and
reports whether a cached road graph is present for road-aware offline routing.
Missing road cache is a warning by default because the application has an
explicit haversine fallback; use --strict-road-cache to make it a hard failure.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.demo_gate import run_demo_gate  # noqa: E402
from scripts.production_gate import run_gate  # noqa: E402

REQUIRED_RUNTIME_MODULES = [
    "streamlit",
    "pandas",
    "geopandas",
    "folium",
    "streamlit_folium",
    "networkx",
    "osmnx",
    "reportlab",
]

REQUIRED_FIELD_FILES = [
    "app.py",
    "scripts/run_offline.py",
    "scripts/demo_gate.py",
    "scripts/production_gate.py",
    "docs/mobile_offline.md",
    "docs/pre_demo_checklist.md",
]

ROAD_CACHE_FILES = {
    "Puri": "data/cache/roads/Puri_Odisha_India.graphml",
    "Guwahati": "data/cache/roads/Guwahati_Assam_India.graphml",
    "Chennai": "data/cache/roads/Chennai_Tamil_Nadu_India.graphml",
}


def _lan_ip() -> str:
    """Best-effort LAN address discovery without any internet request."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))
        address = sock.getsockname()[0]
    except OSError:
        address = "127.0.0.1"
    finally:
        sock.close()
    return address


def _dependency_state() -> dict:
    missing = [name for name in REQUIRED_RUNTIME_MODULES if importlib.util.find_spec(name) is None]
    return {
        "pass": not missing,
        "missing": missing,
        "required": list(REQUIRED_RUNTIME_MODULES),
    }


def _required_files_state(root: Path = ROOT) -> dict:
    missing = [relative for relative in REQUIRED_FIELD_FILES if not (root / relative).exists()]
    return {
        "pass": not missing,
        "missing": missing,
        "required": list(REQUIRED_FIELD_FILES),
    }


def _road_cache_state(root: Path = ROOT) -> dict:
    cities = {}
    for city, relative in ROAD_CACHE_FILES.items():
        path = root / relative
        exists = path.exists() and path.is_file() and path.stat().st_size > 0
        cities[city] = {
            "ready": exists,
            "path": relative,
            "size_mb": round(path.stat().st_size / 1024 / 1024, 2) if exists else 0.0,
        }
    puri_ready = bool(cities["Puri"]["ready"])
    return {
        "puri_ready": puri_ready,
        "all_demo_cities_ready": all(item["ready"] for item in cities.values()),
        "cities": cities,
    }


def _port_state(port: int) -> dict:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", int(port)))
        available = True
        error = None
    except OSError as exc:
        available = False
        error = str(exc)
    finally:
        sock.close()
    return {"pass": available, "port": int(port), "error": error}


def _git_state(root: Path = ROOT) -> dict:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return {
            "available": True,
            "commit": commit,
            "clean": not bool(dirty_output),
            "changed_entries": len(dirty_output.splitlines()) if dirty_output else 0,
        }
    except (OSError, subprocess.CalledProcessError):
        return {"available": False, "commit": None, "clean": None, "changed_entries": None}


def _run_offline_gates() -> tuple[dict, dict]:
    previous_offline = os.environ.get("SIH_OFFLINE_MODE")
    previous_required = os.environ.get("SIH_REQUIRE_OPERATIONAL_DATA")
    os.environ["SIH_OFFLINE_MODE"] = "true"
    os.environ["SIH_REQUIRE_OPERATIONAL_DATA"] = "false"
    try:
        demo = run_demo_gate()
        production = run_gate()
    finally:
        if previous_offline is None:
            os.environ.pop("SIH_OFFLINE_MODE", None)
        else:
            os.environ["SIH_OFFLINE_MODE"] = previous_offline
        if previous_required is None:
            os.environ.pop("SIH_REQUIRE_OPERATIONAL_DATA", None)
        else:
            os.environ["SIH_REQUIRE_OPERATIONAL_DATA"] = previous_required
    return demo, production


def run_preflight(
    *,
    root: Path = ROOT,
    port: int = 8501,
    strict_road_cache: bool = False,
    run_gates: bool = True,
) -> dict:
    dependency_state = _dependency_state()
    files_state = _required_files_state(root)
    road_state = _road_cache_state(root)
    port_state = _port_state(port)
    git_state = _git_state(root)

    if run_gates:
        try:
            demo_gate, production_gate = _run_offline_gates()
            demo_pass = bool(demo_gate.get("demo_ready"))
            production_pass = bool(production_gate.get("production_ready_offline"))
            gate_error = None
        except Exception as exc:
            demo_gate = {}
            production_gate = {}
            demo_pass = False
            production_pass = False
            gate_error = str(exc)
    else:
        demo_gate = {"skipped": True}
        production_gate = {"skipped": True}
        demo_pass = True
        production_pass = True
        gate_error = None

    core_ready = all(
        [
            dependency_state["pass"],
            files_state["pass"],
            port_state["pass"],
            demo_pass,
            production_pass,
        ]
    )
    field_ready = core_ready and (road_state["puri_ready"] or not strict_road_cache)

    warnings = []
    if not road_state["puri_ready"]:
        warnings.append(
            "Puri road GraphML cache is missing; offline routing will visibly fall back to straight-line distance."
        )
    if git_state.get("available") and git_state.get("clean") is False:
        warnings.append("Working tree has uncommitted changes; present only from a known tested commit.")
    if git_state.get("available") is False:
        warnings.append("Git metadata is unavailable; record the release commit separately for the presentation laptop.")

    lan_ip = _lan_ip()
    launch = {
        "command": f"{sys.executable} scripts/run_offline.py",
        "laptop_url": f"http://127.0.0.1:{port}",
        "phone_url": f"http://{lan_ip}:{port}" if lan_ip != "127.0.0.1" else None,
    }

    next_actions = []
    if not dependency_state["pass"]:
        next_actions.append("Install runtime dependencies: python -m pip install -r requirements.txt")
    if not road_state["puri_ready"]:
        next_actions.append(
            'While internet is available, cache Puri roads: python scripts/cache_road_network.py "Puri, Odisha, India"'
        )
    if not port_state["pass"]:
        next_actions.append(f"Free TCP port {port}, or set SIH_OFFLINE_PORT to another available port.")
    if field_ready:
        next_actions.append("Launch the field app: python scripts/run_offline.py")

    return {
        "field_ready": field_ready,
        "core_offline_ready": core_ready,
        "road_routing_ready": road_state["puri_ready"],
        "strict_road_cache": bool(strict_road_cache),
        "checks": {
            "runtime_dependencies": dependency_state,
            "required_field_files": files_state,
            "port_available": port_state,
            "demo_gate": {"pass": demo_pass, "error": gate_error, "result": demo_gate},
            "production_gate": {"pass": production_pass, "error": gate_error, "result": production_gate},
            "road_cache": road_state,
            "git": git_state,
        },
        "warnings": warnings,
        "launch": launch,
        "next_actions": next_actions,
    }


def _print_human(result: dict) -> None:
    print("Hazard Command — FIELD PREFLIGHT")
    print("=" * 38)
    print(f"Core offline workflow: {'PASS' if result['core_offline_ready'] else 'FAIL'}")
    print(f"Road-aware Puri routing: {'READY' if result['road_routing_ready'] else 'NOT CACHED'}")
    print(f"Overall field gate: {'PASS' if result['field_ready'] else 'FAIL'}")

    git_state = result["checks"]["git"]
    if git_state.get("available"):
        print(f"Commit: {git_state.get('commit')} · working tree {'clean' if git_state.get('clean') else 'DIRTY'}")

    print(f"Laptop URL after launch: {result['launch']['laptop_url']}")
    if result["launch"].get("phone_url"):
        print(f"Phone on same Wi-Fi/hotspot: {result['launch']['phone_url']}")

    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")

    if result["next_actions"]:
        print("\nNext actions:")
        for action in result["next_actions"]:
            print(f"- {action}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline-safe competition laptop preflight")
    parser.add_argument("--port", type=int, default=int(os.getenv("SIH_OFFLINE_PORT", "8501")))
    parser.add_argument(
        "--strict-road-cache",
        action="store_true",
        help="Fail the overall gate when the Puri GraphML road cache is absent.",
    )
    parser.add_argument("--json", action="store_true", help="Print the complete preflight result as JSON.")
    parser.add_argument(
        "--skip-gates",
        action="store_true",
        help="Skip the deterministic demo/production gates for a fast environment-only check.",
    )
    args = parser.parse_args()

    result = run_preflight(
        port=args.port,
        strict_road_cache=args.strict_road_cache,
        run_gates=not args.skip_gates,
    )
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_human(result)
    return 0 if result["field_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
