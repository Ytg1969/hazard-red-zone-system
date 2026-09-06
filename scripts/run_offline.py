"""Launch Hazard Command in explicit offline/LAN mode.

The Streamlit server still runs locally on the laptop. External source adapters
are disabled through SIH_OFFLINE_MODE, while deterministic local/demo workflows
remain available. Binding to 0.0.0.0 lets phones on the same Wi-Fi/hotspot open
the laptop-hosted app without internet access.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _lan_ip() -> str:
    """Best-effort local-network address discovery without external requests."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))
        address = sock.getsockname()[0]
    except OSError:
        address = "127.0.0.1"
    finally:
        sock.close()
    return address


def main() -> int:
    env = os.environ.copy()
    env["SIH_OFFLINE_MODE"] = "true"
    env.setdefault("SIH_REQUIRE_OPERATIONAL_DATA", "false")

    port = env.get("SIH_OFFLINE_PORT", "8501")
    lan_ip = _lan_ip()

    print("Hazard Command — OFFLINE mode")
    print(f"Laptop: http://127.0.0.1:{port}")
    if lan_ip != "127.0.0.1":
        print(f"Phone on same Wi-Fi/hotspot: http://{lan_ip}:{port}")
    print("External LIVE APIs are disabled. Local/demo data and deterministic planning remain available.")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ROOT / "app.py"),
        "--server.address=0.0.0.0",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    return subprocess.call(command, cwd=ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
