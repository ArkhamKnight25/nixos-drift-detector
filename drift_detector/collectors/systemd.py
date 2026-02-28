from __future__ import annotations

import json
import subprocess


def get_actual_services() -> dict[str, dict]:
    cmd = [
        "systemctl", "list-units",
        "--type=service", "--all",
        "--output=json", "--no-pager",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise RuntimeError(
            "systemctl not found. This tool must run on a systemd-based NixOS system."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("systemctl timed out after 30 seconds.")

    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"systemctl exited with code {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )

    stdout = result.stdout.strip()
    if not stdout:
        return {}

    try:
        raw_units = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse systemctl JSON output: {e}\n"
            f"Output was: {stdout[:500]}"
        )

    services: dict[str, dict] = {}

    for unit in raw_units:
        name = unit.get("unit", "")
        if not name.endswith(".service"):
            continue

        services[name] = {
            "active_state": unit.get("active", "unknown"),
            "sub_state": unit.get("sub", "unknown"),
            "load_state": unit.get("load", "unknown"),
            "description": unit.get("description", ""),
        }

    return services
