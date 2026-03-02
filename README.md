# nixos-drift-detector

Compares `/run/current-system` (declared state) against live runtime state and reports what's drifted.

```
nixos-drift-detect --check services
```

```
[CRITICAL] nginx.service
  Drift kind: state_mismatch
  Service 'nginx.service' is declared but not running (active=inactive, sub=dead)
  Fix: systemctl start nginx.service
```

## Install

```bash
# From source (on NixOS use a venv — --break-system-packages won't work)
git clone https://github.com/ArkhamKnight25/nixos-drift-detector
cd nixos-drift-detector
nix-shell -p python3 jq
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Nix flake packaging is planned but not done yet.

## Usage

```
--check services     check systemd service state
--format json        output JSON instead of console
--output FILE        write JSON report to file
--severity LEVEL     info | warning | critical
--profile PATH       override /run/current-system
--verbose            debug logging
```

Exit codes: `0` clean, `1` warnings, `2` critical drift.

## How it works

Reads unit files straight from `/run/current-system/etc/systemd/system/`
(the activated profile — no Nix eval at runtime), diffs against
`systemctl list-units --output=json`, and flags missing, stopped,
or undeclared services.

Filters out oneshots, template units, socket-activated services,
and hardware-conditional units (lvm, hv-, dbus aliases, etc.)
to avoid false positives.

## Status

Service drift detection works. Tested on NixOS 24.11 — baseline stays
clean, stopping a declared service shows up as critical, a transient
rogue service shows as warning, cleanup returns to baseline.

## What's next

- users/groups — `/var/lib/nixos/declarative-*` vs `/etc/passwd`
- firewall — `networking.firewall` vs live nftables rules
- /etc drift — activation script outputs vs actual files on disk
- derivation drift — service running an older `/nix/store` path than
  what the current profile declares
- reconciliation mode — suggest or apply fixes
- NixOS VM tests via `nixosTest`
- flake + NixOS module for proper packaging
