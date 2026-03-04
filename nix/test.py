import json

machine.start()
machine.wait_for_unit("nginx.service")

rc, out = machine.execute("nixos-drift-detect --check services --format json 2>/dev/null")
base = json.loads(out)
base_crit = base["summary"]["critical"]

machine.succeed("systemctl stop nginx")
machine.sleep(1)

rc2, out2 = machine.execute("nixos-drift-detect --check services --format json 2>/dev/null")
assert rc2 == 2, f"expected exit 2 (critical drift), got {rc2}"
report2 = json.loads(out2)
assert report2["summary"]["critical"] > base_crit, (
    f"expected critical to increase after stopping nginx, "
    f"got {report2['summary']['critical']} (was {base_crit})"
)

machine.succeed("systemctl start nginx")
machine.sleep(1)

rc3, out3 = machine.execute("nixos-drift-detect --check services --format json 2>/dev/null")
report3 = json.loads(out3)
assert report3["summary"]["critical"] == base_crit, (
    f"expected critical to return to {base_crit} after restart, "
    f"got {report3['summary']['critical']}"
)
