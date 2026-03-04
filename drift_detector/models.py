from __future__ import annotations

import socket
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from drift_detector import __version__


_SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    def __lt__(self, other: Severity) -> bool:
        return _SEVERITY_ORDER[self.value] < _SEVERITY_ORDER[other.value]


@dataclass
class DriftEntry:
    type: str
    name: str
    drift_kind: str
    severity: Severity
    message: str
    declared: Any
    actual: Any
    remediation: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class DriftReport:
    version: str
    timestamp: str
    system_profile: str
    hostname: str
    checks_run: list[str]
    drifts: list[DriftEntry] = field(default_factory=list)

    @classmethod
    def create(cls, checks_run: list[str], profile_path: Path) -> DriftReport:
        return cls(
            version=__version__,
            timestamp=datetime.now(timezone.utc).isoformat(),
            system_profile=str(profile_path.resolve()) if profile_path.exists() else str(profile_path),
            hostname=socket.gethostname(),
            checks_run=checks_run,
        )

    @property
    def summary(self) -> dict:
        critical = sum(1 for d in self.drifts if d.severity == Severity.CRITICAL)
        warning = sum(1 for d in self.drifts if d.severity == Severity.WARNING)
        info = sum(1 for d in self.drifts if d.severity == Severity.INFO)
        return {
            "total_drifts": len(self.drifts),
            "critical": critical,
            "warning": warning,
            "info": info,
        }

    def filter_by_severity(self, min_severity: Severity) -> list[DriftEntry]:
        min_val = _SEVERITY_ORDER[min_severity.value]
        return [d for d in self.drifts if _SEVERITY_ORDER[d.severity.value] >= min_val]
