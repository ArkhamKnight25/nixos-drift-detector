from pathlib import Path

CURRENT_SYSTEM = Path("/run/current-system")
SYSTEMD_UNIT_DIR = CURRENT_SYSTEM / "etc" / "systemd" / "system"
DECLARATIVE_USERS_FILE = Path("/var/lib/nixos/declarative-users")
DECLARATIVE_GROUPS_FILE = Path("/var/lib/nixos/declarative-groups")
REPORT_VERSION = "1.0.0"

SYSTEM_SERVICE_PREFIXES = (
    "systemd-",
    "dbus",
    "getty",
    "user@",
    "session-",
    "-.service",
    "init.scope",
)

ALWAYS_PRESENT_SERVICES = {
    "dbus.service",
    "systemd-journald.service",
    "systemd-logind.service",
    "systemd-udevd.service",
    "systemd-networkd.service",
    "systemd-resolved.service",
    "systemd-timesyncd.service",
    "nix-daemon.service",
}
