#!/usr/bin/env python3
"""vuurwag probe - runs ON the Proxmox host and prints one JSON document.

Standard library only, so it can be streamed over ssh as `python3 - < probe.py`.
Every section is optional: a missing tool or a failing command yields `null`
for that section (plus a note in `errors`), never a crash. Must run as root
for pvesh/pct/smartctl to return anything useful; as a normal user the node
section (from /proc) still works and `privileged` is reported as false.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

PROBE_VERSION = 1
PATH_EXTRA = ("/usr/sbin", "/sbin", "/usr/local/sbin", "/usr/local/bin")
ERRORS: list[str] = []


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = ":".join(list(PATH_EXTRA) + [env.get("PATH", "/usr/bin:/bin")])
    env["LC_ALL"] = "C"
    return env


def run(cmd: list[str], timeout: float = 8.0) -> str | None:
    """Run a command; return stdout or None (recording the reason)."""
    if shutil.which(cmd[0], path=_env()["PATH"]) is None:
        ERRORS.append(f"{cmd[0]}: not installed")
        return None
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_env())
    except subprocess.TimeoutExpired:
        ERRORS.append(f"{' '.join(cmd)}: timeout after {timeout}s")
        return None
    except OSError as exc:  # pragma: no cover - defensive
        ERRORS.append(f"{' '.join(cmd)}: {exc}")
        return None
    if p.returncode != 0 and not p.stdout.strip():
        err = p.stderr.strip().splitlines()
        ERRORS.append(f"{' '.join(cmd[:3])}: rc={p.returncode} {err[-1][:100] if err else ''}")
        return None
    return p.stdout


def run_json(cmd: list[str], timeout: float = 8.0) -> Any:
    out = run(cmd, timeout)
    if out is None:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        ERRORS.append(f"{' '.join(cmd[:3])}: non-JSON output")
        return None


def read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as exc:
        ERRORS.append(f"{path}: {exc.strerror}")
        return None


# ───────────────────────────── node ─────────────────────────────


def _cpu_sample() -> tuple[int, int] | None:
    stat = read("/proc/stat")
    if not stat:
        return None
    first = stat.splitlines()[0].split()
    nums = [int(x) for x in first[1:]]
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
    return sum(nums), idle


def node_section(cpu_a: tuple[int, int] | None, cpu_b: tuple[int, int] | None) -> dict[str, Any]:
    out: dict[str, Any] = {"hostname": socket.gethostname()}
    up = read("/proc/uptime")
    out["uptime"] = float(up.split()[0]) if up else None
    la = read("/proc/loadavg")
    if la:
        parts = la.split()
        out["loadavg"] = [float(parts[0]), float(parts[1]), float(parts[2])]
        running, total = parts[3].split("/")
        out["procs_running"] = int(running)
        out["procs_total"] = int(total)
    out["cpus"] = os.cpu_count()
    if cpu_a and cpu_b:
        dt = cpu_b[0] - cpu_a[0]
        di = cpu_b[1] - cpu_a[1]
        out["cpu_pct"] = round(100.0 * (dt - di) / dt, 1) if dt > 0 else 0.0
    else:
        out["cpu_pct"] = None
    mem = read("/proc/meminfo")
    if mem:
        kv: dict[str, int] = {}
        for line in mem.splitlines():
            k, _, v = line.partition(":")
            try:
                kv[k.strip()] = int(v.split()[0]) * 1024
            except (ValueError, IndexError):
                pass
        out["mem_total"] = kv.get("MemTotal")
        out["mem_available"] = kv.get("MemAvailable")
        out["mem_used"] = (kv.get("MemTotal", 0) - kv.get("MemAvailable", 0)) or None
        out["swap_total"] = kv.get("SwapTotal")
        out["swap_used"] = (kv.get("SwapTotal", 0) - kv.get("SwapFree", 0)) if "SwapTotal" in kv else None
    pvev = run(["pveversion"], 4)
    out["pveversion"] = pvev.strip() if pvev else None
    try:
        out["kernel"] = os.uname().release
    except Exception:  # pragma: no cover
        out["kernel"] = None
    model = None
    cpuinfo = read("/proc/cpuinfo")
    if cpuinfo:
        m = re.search(r"model name\s*:\s*(.+)", cpuinfo)
        model = m.group(1).strip() if m else None
    out["cpu_model"] = model
    return out


# ───────────────────────────── guests ─────────────────────────────


def guests_section(host: str) -> list[dict[str, Any]] | None:
    data = run_json(["pvesh", "get", f"/nodes/{host}/lxc", "--output-format", "json"], 8)
    if data is None:
        # fall back to pct list (no cpu/mem but at least names and states)
        txt = run(["pct", "list"], 6)
        if txt is None:
            return None
        rows = []
        for line in txt.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                rows.append({"vmid": int(parts[0]), "status": parts[1], "name": parts[-1]})
        return rows
    guests = []
    for g in data:
        guests.append({
            "vmid": int(g.get("vmid", 0)),
            "name": g.get("name"),
            "status": g.get("status"),
            "cpu": float(g.get("cpu") or 0.0),       # fraction of one core * cpus (0..1)
            "cpus": int(g.get("cpus") or 0),
            "mem": int(g.get("mem") or 0),
            "maxmem": int(g.get("maxmem") or 0),
            "swap": int(g.get("swap") or 0),
            "disk": int(g.get("disk") or 0),
            "maxdisk": int(g.get("maxdisk") or 0),
            "netin": int(g.get("netin") or 0),
            "netout": int(g.get("netout") or 0),
            "uptime": int(g.get("uptime") or 0),
            "tags": [t for t in str(g.get("tags") or "").split(";") if t],
            "lock": g.get("lock"),
            "pressure_cpu": float(g.get("pressurecpusome") or 0.0),
        })
    guests.sort(key=lambda r: r["vmid"])
    return guests


# ───────────────────────────── storage ─────────────────────────────


def storage_section(host: str) -> list[dict[str, Any]] | None:
    data = run_json(["pvesh", "get", f"/nodes/{host}/storage", "--output-format", "json"], 8)
    if data is not None:
        rows = []
        for s in data:
            rows.append({
                "name": s.get("storage"),
                "type": s.get("type"),
                "active": bool(s.get("active")),
                "total": int(s.get("total") or 0),
                "used": int(s.get("used") or 0),
                "avail": int(s.get("avail") or 0),
                "content": s.get("content"),
            })
        return sorted(rows, key=lambda r: r["name"] or "")
    txt = run(["pvesm", "status"], 8)
    if txt is None:
        return None
    rows = []
    for line in txt.splitlines()[1:]:
        p = line.split()
        if len(p) >= 6:
            try:
                rows.append({
                    "name": p[0], "type": p[1], "active": p[2] == "active",
                    "total": int(p[3]) * 1024, "used": int(p[4]) * 1024, "avail": int(p[5]) * 1024,
                    "content": None,
                })
            except ValueError:
                continue
    return rows


# ───────────────────────────── disks ─────────────────────────────


def _attr(table: list[dict[str, Any]], *ids: int) -> int | None:
    for row in table:
        if row.get("id") in ids:
            raw = row.get("raw", {}).get("value")
            return int(raw) if raw is not None else None
    return None


def disks_section() -> list[dict[str, Any]] | None:
    lsblk = run_json(["lsblk", "-J", "-d", "-o", "NAME,SIZE,TYPE,MODEL,ROTA,TRAN,SERIAL"], 6)
    if lsblk is None:
        return None
    disks = []
    for dev in lsblk.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue
        name = dev["name"]
        if name.startswith(("loop", "zram", "ram", "sr")):
            continue
        d: dict[str, Any] = {
            "name": name,
            "size": dev.get("size"),
            "model": (dev.get("model") or "").strip() or None,
            "rota": bool(dev.get("rota")),
            "tran": dev.get("tran"),
            "serial": dev.get("serial"),
            "nvme": name.startswith("nvme"),
            "smart": None,
        }
        cmd = ["smartctl", "-j", "-a", f"/dev/{name}"]
        if d["nvme"]:
            cmd = ["smartctl", "-j", "-a", "-d", "nvme", f"/dev/{name}"]
        sm = run_json(cmd, 10)
        if sm is not None:
            msgs = [m.get("string", "") for m in sm.get("smartctl", {}).get("messages", [])]
            denied = any("Permission denied" in m for m in msgs)
            smart: dict[str, Any] = {
                "available": not denied and ("smart_status" in sm or "nvme_smart_health_information_log" in sm),
                "passed": sm.get("smart_status", {}).get("passed"),
                "temp": sm.get("temperature", {}).get("current"),
                "power_on_hours": sm.get("power_on_time", {}).get("hours"),
                "model": sm.get("model_name") or d["model"],
                "reallocated": None, "pending": None, "uncorrectable": None, "crc_errors": None,
                "percentage_used": None, "available_spare": None, "media_errors": None,
                "remaining_life": None,
            }
            table = sm.get("ata_smart_attributes", {}).get("table")
            if table:
                smart["reallocated"] = _attr(table, 5)
                smart["pending"] = _attr(table, 197)
                smart["uncorrectable"] = _attr(table, 198, 160)
                smart["crc_errors"] = _attr(table, 199)
                smart["remaining_life"] = _attr(table, 169, 231, 202)
                wl = _attr(table, 177, 173)
                if smart["remaining_life"] is None and wl is not None and wl <= 100:
                    smart["remaining_life"] = wl
            nv = sm.get("nvme_smart_health_information_log")
            if nv:
                smart["percentage_used"] = nv.get("percentage_used")
                smart["available_spare"] = nv.get("available_spare")
                smart["media_errors"] = nv.get("media_errors")
                if smart["temp"] is None:
                    smart["temp"] = nv.get("temperature")
                if smart["passed"] is None:
                    cw = nv.get("critical_warning")
                    smart["passed"] = (cw == 0) if cw is not None else None
            if denied:
                ERRORS.append(f"smartctl /dev/{name}: permission denied (run as root)")
            d["smart"] = smart
        disks.append(d)
    return disks


# ───────────────────────────── zfs ─────────────────────────────


def zfs_section() -> dict[str, Any] | None:
    lst = run(["zpool", "list", "-Hp", "-o", "name,size,alloc,free,health"], 6)
    if lst is None:
        return None
    pools = []
    for line in lst.splitlines():
        p = line.split("\t")
        if len(p) >= 5:
            try:
                pools.append({"name": p[0], "size": int(p[1]), "alloc": int(p[2]), "free": int(p[3]), "health": p[4]})
            except ValueError:
                continue
    status = run(["zpool", "status", "-x"], 6)
    return {"pools": pools, "status": (status or "").strip() or None}


# ───────────────────────────── sensors ─────────────────────────────


def sensors_section() -> list[dict[str, Any]] | None:
    data = run_json(["sensors", "-j"], 6)
    if data is None:
        return None
    readings = []
    for chip, feats in data.items():
        if not isinstance(feats, dict):
            continue
        for feat, vals in feats.items():
            if not isinstance(vals, dict):
                continue
            for k, v in vals.items():
                if k.endswith("_input") and k.startswith("temp") and isinstance(v, (int, float)):
                    crit = vals.get(k.replace("_input", "_crit")) or vals.get(k.replace("_input", "_max"))
                    readings.append({"chip": chip, "label": feat, "temp": float(v), "crit": float(crit) if crit else None})
    return readings


# ───────────────────────────── network ─────────────────────────────


def _net_sample() -> dict[str, tuple[int, int]]:
    txt = read("/proc/net/dev") or ""
    out: dict[str, tuple[int, int]] = {}
    for line in txt.splitlines()[2:]:
        iface, _, rest = line.partition(":")
        iface = iface.strip()
        p = rest.split()
        if len(p) >= 9:
            out[iface] = (int(p[0]), int(p[8]))
    return out


def network_section(a: dict[str, tuple[int, int]], b: dict[str, tuple[int, int]], dt: float) -> list[dict[str, Any]]:
    rows = []
    for iface, (rx1, tx1) in b.items():
        if iface == "lo" or iface.startswith(("veth", "fwbr", "fwln", "fwpr", "tap")):
            continue
        rx0, tx0 = a.get(iface, (rx1, tx1))
        rows.append({
            "iface": iface,
            "rx_bytes": rx1, "tx_bytes": tx1,
            "rx_bps": max(0.0, (rx1 - rx0) / dt) if dt > 0 else 0.0,
            "tx_bps": max(0.0, (tx1 - tx0) / dt) if dt > 0 else 0.0,
        })
    return rows


# ───────────────────────────── tasks / firewall / tailscale / updates ─────────────────────────────


def tasks_section(host: str) -> list[dict[str, Any]] | None:
    data = run_json(["pvesh", "get", f"/nodes/{host}/tasks", "--limit", "15", "--output-format", "json"], 8)
    if data is None:
        return None
    rows = []
    for t in data:
        rows.append({
            "upid": t.get("upid"), "type": t.get("type"), "id": t.get("id") or None,
            "status": t.get("status"), "starttime": t.get("starttime"), "endtime": t.get("endtime"),
            "user": t.get("user"),
        })
    return rows


def firewall_section() -> dict[str, Any] | None:
    txt = run(["pve-firewall", "status"], 5)
    if txt is None:
        return None
    txt = txt.strip()
    return {"raw": txt, "running": "running" in txt and "enabled" in txt}


def tailscale_section() -> dict[str, Any] | None:
    data = run_json(["tailscale", "status", "--json"], 6)
    if data is None:
        return None
    peers = data.get("Peer") or {}
    self_ = data.get("Self") or {}
    return {
        "backend": data.get("BackendState"),
        "online": bool(self_.get("Online")) and data.get("BackendState") == "Running",
        "ips": data.get("TailscaleIPs") or [],
        "dns_name": self_.get("DNSName"),
        "peers": len(peers),
        "peers_online": sum(1 for p in peers.values() if p.get("Online")),
    }


def updates_section(host: str) -> dict[str, Any] | None:
    data = run_json(["pvesh", "get", f"/nodes/{host}/apt/update", "--output-format", "json"], 6)
    if data is None:
        return None
    return {"count": len(data), "packages": [p.get("Package") for p in data[:12]]}


# ───────────────────────────── main ─────────────────────────────


def collect() -> dict[str, Any]:
    t0 = time.monotonic()
    host = socket.gethostname()
    privileged = os.geteuid() == 0
    doc: dict[str, Any] = {"probe_version": PROBE_VERSION, "time": time.time(), "privileged": privileged}
    # Sample cpu and network in a quiet half second BEFORE the pvesh storm below,
    # otherwise the probe measures its own perl processes.
    cpu_a = _cpu_sample()
    net_a = _net_sample()
    time.sleep(0.5)
    cpu_b = _cpu_sample()
    net_b = _net_sample()
    doc["node"] = node_section(cpu_a, cpu_b)
    doc["network"] = network_section(net_a, net_b, 0.5)
    jobs = {
        "guests": lambda: guests_section(host),
        "storage": lambda: storage_section(host),
        "disks": disks_section,
        "zfs": zfs_section,
        "sensors": sensors_section,
        "tasks": lambda: tasks_section(host),
        "firewall": firewall_section,
        "tailscale": tailscale_section,
        "updates": lambda: updates_section(host),
    }
    # pvesh is a perl process that takes ~1 s to start; run the sections concurrently.
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {name: pool.submit(fn) for name, fn in jobs.items()}
        for name, fut in futures.items():
            try:
                doc[name] = fut.result(timeout=15)
            except Exception as exc:  # pragma: no cover - defensive
                ERRORS.append(f"{name}: {exc}")
                doc[name] = None
    doc["probe_seconds"] = round(time.monotonic() - t0, 2)
    doc["errors"] = ERRORS
    return doc


def main() -> int:
    doc = collect()
    sys.stdout.write(json.dumps(doc, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
