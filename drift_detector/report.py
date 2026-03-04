from __future__ import annotations

import json
from .models import DriftEntry, DriftReport, Severity

_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_DIM = "\033[2m"


def _severity_color(severity: Severity) -> str:
    return {
        Severity.CRITICAL: _RED,
        Severity.WARNING: _YELLOW,
        Severity.INFO: _CYAN,
    }.get(severity, _RESET)


def to_json(report: DriftReport, min_severity: Severity = Severity.INFO) -> str:
    drifts = report.filter_by_severity(min_severity)
    summary = {
        "total_drifts": len(drifts),
        "critical": sum(1 for d in drifts if d.severity == Severity.CRITICAL),
        "warning": sum(1 for d in drifts if d.severity == Severity.WARNING),
        "info": sum(1 for d in drifts if d.severity == Severity.INFO),
    }
    data = {
        "version": report.version,
        "timestamp": report.timestamp,
        "system_profile": report.system_profile,
        "hostname": report.hostname,
        "checks_run": report.checks_run,
        "summary": summary,
        "drifts": [d.to_dict() for d in drifts],
    }
    return json.dumps(data, indent=2)


def to_console(report: DriftReport, min_severity: Severity = Severity.INFO) -> str:
    lines: list[str] = []
    summary = report.summary

    lines.append(f"\n{_BOLD}NixOS Drift Detector{_RESET}  v{report.version}")
    lines.append(f"{_DIM}Host:    {report.hostname}{_RESET}")
    lines.append(f"{_DIM}Profile: {report.system_profile}{_RESET}")
    lines.append(f"{_DIM}Time:    {report.timestamp}{_RESET}")
    lines.append(f"{_DIM}Checks:  {', '.join(report.checks_run)}{_RESET}")
    lines.append("")

    drifts = report.filter_by_severity(min_severity)

    if not drifts:
        lines.append(f"{_GREEN}✓ No drift detected — system matches declared configuration{_RESET}")
        return "\n".join(lines)

    crit = summary["critical"]
    warn = summary["warning"]
    info = summary["info"]

    status_parts = []
    if crit:
        status_parts.append(f"{_RED}{_BOLD}{crit} CRITICAL{_RESET}")
    if warn:
        status_parts.append(f"{_YELLOW}{warn} WARNING{_RESET}")
    if info:
        status_parts.append(f"{_CYAN}{info} INFO{_RESET}")

    lines.append(f"Found {summary['total_drifts']} drift(s): {', '.join(status_parts)}")
    lines.append("")

    for entry in drifts:
        color = _severity_color(entry.severity)
        lines.append(f"{color}{_BOLD}[{entry.severity.value.upper()}]{_RESET} {_BOLD}{entry.name}{_RESET}")
        lines.append(f"  Drift kind: {entry.drift_kind}")
        lines.append(f"  {entry.message}")
        if entry.declared is not None:
            lines.append(f"  Declared:   {entry.declared}")
        if entry.actual is not None:
            lines.append(f"  Actual:     {entry.actual}")
        if entry.remediation:
            lines.append(f"  {_DIM}Fix: {entry.remediation}{_RESET}")
        lines.append("")

    return "\n".join(lines)
