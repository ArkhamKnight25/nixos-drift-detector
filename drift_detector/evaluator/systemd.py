from __future__ import annotations

import configparser
from pathlib import Path


def _parse_unit_file(unit_path: Path) -> dict:
    text = unit_path.read_text(errors="replace")
    parser = configparser.RawConfigParser(strict=False)
    parser.read_string(text)

    info: dict = {"unit_file": str(unit_path)}

    if parser.has_section("Install"):
        info["wanted_by"] = parser.get("Install", "WantedBy", fallback="")
        info["required_by"] = parser.get("Install", "RequiredBy", fallback="")

    if parser.has_section("Service"):
        info["exec_start"] = parser.get("Service", "ExecStart", fallback="")
        info["type"] = parser.get("Service", "Type", fallback="simple")
        info["restart"] = parser.get("Service", "Restart", fallback="no")

    if parser.has_section("Unit"):
        info["description"] = parser.get("Unit", "Description", fallback="")

    return info


def get_declared_services(profile: Path) -> dict[str, dict]:
    unit_dir = profile / "etc" / "systemd" / "system"

    if not unit_dir.exists():
        raise FileNotFoundError(
            f"Systemd unit directory not found: {unit_dir}\n"
            "Expected at <profile>/etc/systemd/system/"
        )

    declared: dict[str, dict] = {}

    for unit_file in sorted(unit_dir.glob("*.service")):
        name = unit_file.name
        try:
            info = _parse_unit_file(unit_file)
        except Exception as e:
            info = {"unit_file": str(unit_file), "parse_error": str(e)}

        if info.get("wanted_by", ""):
            declared[name] = info

    return declared
