from __future__ import annotations

from pathlib import Path


def get_current_profile(override: Path | None = None) -> Path:
    profile = override if override is not None else Path("/run/current-system")

    if not profile.exists():
        raise RuntimeError(
            f"Profile path '{profile}' does not exist. "
            "Make sure you are running on a NixOS system."
        )

    return profile.resolve()
