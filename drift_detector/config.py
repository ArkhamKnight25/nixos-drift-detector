from __future__ import annotations

SYSTEM_PROFILE = "/run/current-system"

ALWAYS_PRESENT_SERVICES = {
    "dbus.service",
    "systemd-journald.service",
    "systemd-logind.service",
    "systemd-udevd.service",
    "systemd-resolved.service",
    "systemd-timesyncd.service",
    "sshd.service",
    "nix-daemon.service",
    "network.target",
    "getty@tty1.service",
}

SYSTEM_SERVICE_PREFIXES = (
    "systemd-",
    "dbus-",
    "kmod-",
    "user@",
    "session-",
    "user-runtime-dir@",
    "getty@",
    "autovt@",
    "serial-getty@",
)
