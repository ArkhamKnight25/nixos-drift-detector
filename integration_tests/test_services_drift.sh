#!/usr/bin/env bash
# Integration tests for nixos-drift-detector
# Run as root on a NixOS system with nginx declared and running.
# Requires: jq

set -euo pipefail

PASS=0
FAIL=0

detect() {
    nixos-drift-detect --check services --format json 2>/dev/null || true
}

echo "drift detector integration tests"
echo

# test 1: baseline
echo "test 1: capture baseline"
snap=$(detect)
base_crit=$(echo "$snap" | jq -r '.summary.critical')
base_warn=$(echo "$snap" | jq -r '.summary.warning')
echo "  baseline: crit=$base_crit warn=$base_warn"
echo "  ok"
PASS=$((PASS + 1))
echo

# test 2: stop declared service -> new critical
echo "test 2: stop nginx"
systemctl stop nginx
sleep 1
crit=$(detect | jq -r '.summary.critical')
if [[ "$crit" -gt "$base_crit" ]]; then
    echo "  ok (crit $base_crit -> $crit)"
    PASS=$((PASS + 1))
else
    echo "  fail (crit unchanged at $crit)"
    FAIL=$((FAIL + 1))
fi
systemctl start nginx
sleep 1
echo

# test 3: undeclared persistent service -> new warning
echo "test 3: rogue service"
systemd-run --unit=drift-test-rogue.service --description="drift detector rogue test" "$(which sleep)" 3600
sleep 1
warn=$(detect | jq -r '.summary.warning')
if [[ "$warn" -gt "$base_warn" ]]; then
    echo "  ok (warn $base_warn -> $warn)"
    PASS=$((PASS + 1))
else
    echo "  fail (warn unchanged at $warn)"
    FAIL=$((FAIL + 1))
fi
systemctl stop drift-test-rogue.service
sleep 1
echo

# test 4: after cleanup counts return to baseline
echo "test 4: cleanup"
snap=$(detect)
crit=$(echo "$snap" | jq -r '.summary.critical')
warn=$(echo "$snap" | jq -r '.summary.warning')
if [[ "$crit" -eq "$base_crit" && "$warn" -eq "$base_warn" ]]; then
    echo "  ok (crit=$crit warn=$warn)"
    PASS=$((PASS + 1))
else
    echo "  fail (got crit=$crit warn=$warn, expected crit=$base_crit warn=$base_warn)"
    FAIL=$((FAIL + 1))
fi
echo

echo "results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
