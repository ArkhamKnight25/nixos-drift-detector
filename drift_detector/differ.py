from __future__ import annotations

from .config import ALWAYS_PRESENT_SERVICES, SYSTEM_SERVICE_PREFIXES
from .models import DriftEntry, Severity


def _is_system_service(name: str) -> bool:
    if name in ALWAYS_PRESENT_SERVICES:
        return True
    return any(name.startswith(prefix) for prefix in SYSTEM_SERVICE_PREFIXES)


def diff_services(
    declared: dict[str, dict],
    actual: dict[str, dict],
) -> list[DriftEntry]:
    entries: list[DriftEntry] = []

    for svc_name, decl_info in declared.items():
        if svc_name.endswith("@.service"):
            continue

        wanted_by = decl_info.get("wanted_by", "")
        if _is_transient_target(wanted_by):
            continue

        svc_type = decl_info.get("type", "simple")

        if svc_name not in actual:
            entries.append(DriftEntry(
                type="service",
                name=svc_name,
                drift_kind="missing_declared",
                severity=Severity.CRITICAL,
                message=f"Service '{svc_name}' is declared in /run/current-system but not found in systemctl output",
                declared=decl_info,
                actual=None,
                remediation=f"systemctl start {svc_name}",
            ))
            continue

        actual_info = actual[svc_name]
        active_state = actual_info.get("active_state", "unknown")
        sub_state = actual_info.get("sub_state", "unknown")

        if svc_type == "oneshot" and active_state == "inactive" and sub_state == "dead":
            continue

        if active_state not in ("active", "activating", "reloading"):
            entries.append(DriftEntry(
                type="service",
                name=svc_name,
                drift_kind="state_mismatch",
                severity=Severity.CRITICAL,
                message=(
                    f"Service '{svc_name}' is declared but not running "
                    f"(active={active_state}, sub={sub_state})"
                ),
                declared=decl_info,
                actual=actual_info,
                remediation=f"systemctl start {svc_name}",
            ))

    for svc_name, actual_info in actual.items():
        if svc_name in declared:
            continue
        if _is_system_service(svc_name):
            continue
        if actual_info.get("active_state") != "active":
            continue
        if actual_info.get("sub_state") in ("exited", "dead"):
            continue

        entries.append(DriftEntry(
            type="service",
            name=svc_name,
            drift_kind="undeclared_running",
            severity=Severity.WARNING,
            message=f"Service '{svc_name}' is running but not declared in /run/current-system",
            declared=None,
            actual=actual_info,
            remediation=f"Add to configuration.nix or stop with: systemctl stop {svc_name}",
        ))

    return entries


_TRANSIENT_TARGETS = {
    "shutdown.target", "reboot.target", "halt.target", "poweroff.target",
    "sleep.target", "suspend.target", "hibernate.target", "hybrid-sleep.target",
    "kexec.target", "rescue.target", "emergency.target", "final.target",
}


def _is_transient_target(wanted_by: str) -> bool:
    if not wanted_by:
        return False
    targets = {t.strip() for t in wanted_by.split() if t.strip()}
    return bool(targets) and targets.issubset(_TRANSIENT_TARGETS)
