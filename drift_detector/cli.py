from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from . import __version__
from .config import CURRENT_SYSTEM
from .models import DriftReport, Severity
from .differ import diff_services
from .evaluator.profile import get_current_profile
from .evaluator.systemd import get_declared_services
from .collectors.systemd import get_actual_services
from .report import to_json, to_console

logger = logging.getLogger("nixos-drift-detect")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="nixos-drift-detect",
        description="Detect drift between your NixOS declared config and live runtime state.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--check",
        choices=["services"],
        nargs="+",
        default=["services"],
        metavar="SUBSYSTEM",
        help="Subsystems to check: services (default: all available)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write JSON report to FILE",
    )
    parser.add_argument(
        "--format",
        choices=["json", "console", "both"],
        default="both",
        help="Terminal output format (default: both)",
    )
    parser.add_argument(
        "--severity",
        choices=["info", "warning", "critical"],
        default="info",
        help="Minimum severity to include (default: info)",
    )
    parser.add_argument(
        "--profile",
        metavar="PATH",
        default=str(CURRENT_SYSTEM),
        help=f"Override /run/current-system path (default: {CURRENT_SYSTEM})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def _run_services_check(report: DriftReport, profile: Path) -> None:
    try:
        declared = get_declared_services(profile)
    except Exception as e:
        logger.error("Failed to read declared services from profile: %s", e)
        raise

    try:
        actual = get_actual_services()
    except Exception as e:
        logger.error("Failed to collect actual services from systemctl: %s", e)
        raise

    report.drifts.extend(diff_services(declared, actual))


def main(argv: list[str] | None = None) -> int:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(name)s: %(levelname)s: %(message)s",
    )

    min_severity = Severity(args.severity)
    profile_path = Path(args.profile)

    try:
        profile = get_current_profile(profile_path)
    except FileNotFoundError:
        logger.error("Profile not found at %s — is this a NixOS system?", profile_path)
        return 1
    except PermissionError:
        logger.error("Permission denied reading %s — try running with sudo", profile_path)
        return 1
    except RuntimeError as e:
        logger.error("%s", e)
        return 1

    report = DriftReport.create(checks_run=args.check, profile_path=profile)

    try:
        for check in args.check:
            if check == "services":
                _run_services_check(report, profile)
    except Exception:
        return 1

    if args.output:
        Path(args.output).write_text(to_json(report, min_severity))
        logger.info("Report written to %s", args.output)

    if args.format == "json":
        if not args.output:
            print(to_json(report, min_severity))
    else:
        print(to_console(report, min_severity))

    summary = report.summary
    if summary["critical"] > 0:
        return 2
    if summary["warning"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
