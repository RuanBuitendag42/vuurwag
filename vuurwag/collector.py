"""Runners (local / ssh / demo) and the async Collector that feeds the app."""
from __future__ import annotations

import asyncio
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol

from .model import Snapshot, parse_snapshot

PROBE_PATH = Path(__file__).parent / "probe" / "probe.py"


class ProbeError(RuntimeError):
    pass


class Runner(Protocol):
    name: str

    async def probe(self) -> dict[str, Any]: ...


def _probe_source() -> str:
    return PROBE_PATH.read_text(encoding="utf-8")


async def _run_probe(argv: list[str], stdin: bytes | None, timeout: float) -> dict[str, Any]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ProbeError(f"{argv[0]} not found") from exc
    try:
        out, err = await asyncio.wait_for(proc.communicate(stdin), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise ProbeError(f"probe timed out after {timeout:.0f}s") from exc
    if proc.returncode != 0 or not out.strip():
        msg = err.decode(errors="replace").strip().splitlines()
        raise ProbeError(msg[-1][:160] if msg else f"probe exited {proc.returncode}")
    try:
        return json.loads(out.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise ProbeError("probe returned invalid JSON") from exc


@dataclass
class LocalRunner:
    """Run the probe directly on this machine (the Proxmox host)."""

    python: str = sys.executable
    name: str = "local"

    async def probe(self) -> dict[str, Any]:
        return await _run_probe([self.python, str(PROBE_PATH)], None, timeout=25)


@dataclass
class SshRunner:
    """One ssh exec per tick: the probe source is streamed on stdin."""

    host: str
    sudo: bool = False
    name: str = "ssh"

    def __post_init__(self) -> None:
        self.name = f"ssh:{self.host}"

    async def probe(self) -> dict[str, Any]:
        remote = "sudo -n python3 -" if self.sudo else "python3 -"
        argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", "-o", "ServerAliveInterval=5", self.host, remote]
        return await _run_probe(argv, _probe_source().encode(), timeout=30)


# ───────────────────────────── demo ─────────────────────────────

DEMO_GUESTS = [
    # vmid, name, cpus, maxmem GiB, maxdisk GiB, tags, running
    (100, "core-dns", 1, 1, 8, ["core", "dns"], True),
    (101, "core-portainer", 2, 1, 10, ["core", "portainer"], True),
    (102, "core-runner", 2, 2, 20, ["core", "runner"], True),
    (103, "core-infisical", 2, 1.5, 15, ["core", "secrets"], True),
    (110, "pokebraai", 2, 2, 25, ["apps", "pokebraai"], False),
    (111, "palworld", 4, 8, 30, ["apps", "games"], False),
    (113, "bw-ops", 2, 2, 16, ["apps", "braaiworld", "ops"], True),
    (114, "bw-dev", 2, 2, 16, ["apps", "braaiworld", "dev"], True),
    (116, "bw-plane", 2, 4, 24, ["apps", "braaiworld", "plane"], True),
    (121, "media-addons", 2, 3, 16, ["media", "addons", "public"], True),
]

GiB = 1024 ** 3


class DemoRunner:
    """Lively fake data for the real estate, with the occasional bit of drama."""

    name = "demo"

    def __init__(self, seed: int | None = None, fast: bool = False) -> None:
        self.rng = random.Random(seed)
        self.t0 = time.time()
        self.tick = 0
        self.fast = fast
        self.boot = self.t0 - self.rng.uniform(3 * 86400, 20 * 86400)
        self.cpu = 12.0
        self.mem = 38.0
        self.disk_temp = {"nvme0n1": 41.0, "sda": 36.0}
        self.guest_cpu = {g[0]: self.rng.uniform(1, 8) for g in DEMO_GUESTS}
        self.running = {g[0]: g[6] for g in DEMO_GUESTS}
        self.storage_used = {"local": 46.0, "local-lvm": 38.3}
        self.drama: str | None = None
        self.drama_until = 0.0
        self.tasks: list[dict[str, Any]] = []
        self.restart_vmid: int | None = None
        self.restart_at = 0.0
        self.updates = 3
        self._seed_tasks()

    # ── helpers ──
    def _seed_tasks(self) -> None:
        now = time.time()
        for i, (vmid, _, *_rest) in enumerate(DEMO_GUESTS[:5]):
            st = int(now - 2 * 86400 - i * 3)
            self.tasks.append({"upid": f"UPID:demo:{i}:vzstart:{vmid}", "type": "vzstart", "id": str(vmid),
                               "status": "OK", "starttime": st, "endtime": st + 4, "user": "root@pam"})
        st = int(now - 86400 * 0.6)
        self.tasks.insert(0, {"upid": "UPID:demo:vzdump:1", "type": "vzdump", "id": "121", "status": "OK",
                              "starttime": st, "endtime": st + 180, "user": "root@pam"})

    def _maybe_drama(self, now: float) -> None:
        if self.drama and now > self.drama_until:
            if self.drama == "backup":
                for t in self.tasks:
                    if t["upid"].startswith("UPID:demo:live-backup"):
                        t["endtime"] = int(now)
                        t["status"] = "OK" if self.rng.random() < 0.85 else "job errors"
            if self.drama == "restart" and self.restart_vmid is not None:
                self.running[self.restart_vmid] = True
            self.drama = None
        if self.drama is None and self.rng.random() < (0.08 if self.fast else 0.025):
            self.drama = self.rng.choice(["cpu_spike", "disk_warm", "backup", "restart", "mem_pressure"])
            length = self.rng.uniform(20, 50)
            self.drama_until = now + length
            if self.drama == "backup":
                vmid = self.rng.choice([100, 101, 102, 103, 121])
                self.tasks.insert(0, {"upid": f"UPID:demo:live-backup:{int(now)}", "type": "vzdump", "id": str(vmid),
                                      "status": None, "starttime": int(now), "endtime": None, "user": "root@pam"})
                self.tasks = self.tasks[:15]
            if self.drama == "restart":
                cands = [v for v, r in self.running.items() if r and v not in (100, 103)]
                self.restart_vmid = self.rng.choice(cands)
                self.running[self.restart_vmid] = False
                self.drama_until = now + self.rng.uniform(12, 25)

    def _step(self, now: float) -> None:
        self._maybe_drama(now)
        rng = self.rng
        target_cpu = 10.0 + 6 * math.sin(now / 37.0)
        if self.drama == "cpu_spike":
            target_cpu = 78 + 15 * math.sin(now / 3.0)
        self.cpu += (target_cpu - self.cpu) * 0.25 + rng.uniform(-2.5, 2.5)
        self.cpu = max(1.0, min(99.0, self.cpu))
        target_mem = 40.0 if self.drama != "mem_pressure" else 93.0
        self.mem += (target_mem - self.mem) * 0.12 + rng.uniform(-0.6, 0.6)
        self.mem = max(5.0, min(99.0, self.mem))
        for name in self.disk_temp:
            base = 41.0 if name.startswith("nvme") else 36.0
            target = base + (self.cpu - 10) * 0.12
            if self.drama == "disk_warm" and name.startswith("nvme"):
                target = 62.0
            self.disk_temp[name] += (target - self.disk_temp[name]) * 0.15 + rng.uniform(-0.4, 0.4)
        for vmid in self.guest_cpu:
            base = {102: 9.0, 121: 14.0, 116: 11.0}.get(vmid, 3.0)
            target = base + rng.uniform(-2, 2)
            if self.drama == "cpu_spike" and vmid == 102:
                target = 88.0
            self.guest_cpu[vmid] += (target - self.guest_cpu[vmid]) * 0.3
            self.guest_cpu[vmid] = max(0.2, min(99.0, self.guest_cpu[vmid]))
        if rng.random() < 0.01:
            self.updates = rng.choice([0, 1, 3, 7, 10])

    def _doc(self, now: float) -> dict[str, Any]:
        rng = self.rng
        uptime = now - self.boot
        guests = []
        for vmid, name, cpus, maxmem, maxdisk, tags, _ in DEMO_GUESTS:
            running = self.running[vmid]
            cpu_frac = (self.guest_cpu[vmid] / 100.0) if running else 0.0
            guests.append({
                "vmid": vmid, "name": name, "status": "running" if running else "stopped",
                "cpu": cpu_frac, "cpus": cpus,
                "mem": int(maxmem * GiB * (0.25 + 0.4 * (vmid % 5) / 5)) if running else 0,
                "maxmem": int(maxmem * GiB), "disk": int(maxdisk * GiB * 0.3), "maxdisk": int(maxdisk * GiB),
                "netin": int(now * 1000 * (vmid % 7 + 1)), "netout": int(now * 400 * (vmid % 3 + 1)),
                "uptime": int(uptime) if running else 0, "tags": tags, "lock": None, "pressure_cpu": 0.0,
            })
        total = 16 * GiB
        storage = [
            {"name": "local", "type": "dir", "active": True, "total": 72722055168,
             "used": int(72722055168 * self.storage_used["local"] / 100), "avail": int(72722055168 * (1 - self.storage_used["local"] / 100))},
            {"name": "local-lvm", "type": "lvmthin", "active": True, "total": 168824930304,
             "used": int(168824930304 * self.storage_used["local-lvm"] / 100), "avail": int(168824930304 * (1 - self.storage_used["local-lvm"] / 100))},
        ]
        disks = [
            {"name": "nvme0n1", "size": "931.5G", "model": "Samsung SSD 980 PRO 1TB", "rota": False, "tran": "nvme", "nvme": True,
             "smart": {"available": True, "passed": True, "temp": round(self.disk_temp["nvme0n1"], 1), "power_on_hours": 11234,
                       "model": "Samsung SSD 980 PRO 1TB", "percentage_used": 7, "available_spare": 100, "media_errors": 0,
                       "reallocated": None, "pending": None, "uncorrectable": None, "crc_errors": None, "remaining_life": None}},
            {"name": "sda", "size": "238.5G", "model": "TS256GMTS830S", "rota": False, "tran": "sata", "nvme": False,
             "smart": {"available": True, "passed": True, "temp": round(self.disk_temp["sda"], 1), "power_on_hours": 4234,
                       "model": "TS256GMTS830S", "percentage_used": None, "available_spare": None, "media_errors": None,
                       "reallocated": 0, "pending": 0, "uncorrectable": 0, "crc_errors": 0, "remaining_life": 80}},
        ]
        pkg = 42.0 + self.cpu * 0.35 + rng.uniform(-1, 1)
        sensors = [
            {"chip": "coretemp-isa-0000", "label": "Package id 0", "temp": round(pkg, 1), "crit": 100.0},
            {"chip": "coretemp-isa-0000", "label": "Core 0", "temp": round(pkg - 3, 1), "crit": 100.0},
            {"chip": "nvme-pci-0100", "label": "Composite", "temp": round(self.disk_temp["nvme0n1"], 1), "crit": 84.85},
        ]
        bps = 20_000 + 400_000 * (self.cpu / 100.0) + rng.uniform(0, 60_000)
        network = [
            {"iface": "enp1s0", "rx_bps": bps * 0.6, "tx_bps": bps * 0.4},
            {"iface": "vmbr0", "rx_bps": bps * 0.5, "tx_bps": bps * 0.3},
            {"iface": "tailscale0", "rx_bps": rng.uniform(0, 3000), "tx_bps": rng.uniform(0, 2000)},
        ]
        return {
            "probe_version": 1, "time": now, "privileged": True,
            "node": {
                "hostname": "pve", "uptime": uptime, "loadavg": [round(self.cpu / 100 * 6, 2), round(self.cpu / 100 * 5.2, 2), round(self.cpu / 100 * 4.6, 2)],
                "cpus": 6, "cpu_pct": round(self.cpu, 1), "mem_total": total, "mem_used": int(total * self.mem / 100),
                "mem_available": int(total * (1 - self.mem / 100)), "swap_total": 8 * GiB, "swap_used": int(0.014 * 8 * GiB),
                "pveversion": "pve-manager/9.2.21/4f6e0ac86f9e8c7f (running kernel: 7.0.14-20-pve)", "kernel": "7.0.14-20-pve",
                "cpu_model": "Intel(R) Core(TM) i5-8500T CPU @ 2.10GHz",
            },
            "guests": guests, "storage": storage, "disks": disks, "zfs": None, "sensors": sensors, "network": network,
            "tasks": list(self.tasks), "firewall": {"raw": "Status: enabled/running", "running": True},
            "tailscale": {"online": True, "backend": "Running", "peers": 3, "peers_online": 2, "dns_name": "pve.tailnet.ts.net."},
            "updates": {"count": self.updates, "packages": ["tailscale", "pve-firmware"][: self.updates]},
            "probe_seconds": 1.2, "errors": [],
        }

    async def probe(self) -> dict[str, Any]:
        now = time.time()
        self.tick += 1
        self._step(now)
        return self._doc(now)

    def document(self) -> dict[str, Any]:
        """Synchronous variant for tests."""
        now = time.time()
        self._step(now)
        return self._doc(now)


# ───────────────────────────── collector ─────────────────────────────


SnapshotCallback = Callable[[Snapshot | None, str | None], Awaitable[None] | None]


class Collector:
    """Runs the probe every `interval` seconds and hands Snapshots to a callback."""

    def __init__(self, runner: Runner, interval: float = 5.0) -> None:
        self.runner = runner
        self.interval = interval
        self.latest: Snapshot | None = None
        self.last_error: str | None = None
        self.failures = 0
        self._task: asyncio.Task[None] | None = None

    async def once(self) -> Snapshot:
        doc = await self.runner.probe()
        snap = parse_snapshot(doc, source=self.runner.name)
        self.latest = snap
        self.last_error = None
        self.failures = 0
        return snap

    async def run(self, callback: SnapshotCallback) -> None:
        while True:
            started = time.monotonic()
            try:
                snap = await self.once()
                res = callback(snap, None)
                if asyncio.iscoroutine(res):
                    await res
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - everything becomes a probe-failure event
                self.failures += 1
                self.last_error = str(exc)
                res = callback(None, str(exc))
                if asyncio.iscoroutine(res):
                    await res
            elapsed = time.monotonic() - started
            await asyncio.sleep(max(0.5, self.interval - elapsed))

    def start(self, callback: SnapshotCallback) -> asyncio.Task[None]:
        self._task = asyncio.create_task(self.run(callback))
        return self._task

    def stop(self) -> None:
        if self._task:
            self._task.cancel()


def choose_runner(demo: bool = False, ssh: str | None = None, sudo: bool = False) -> Runner:
    if demo:
        return DemoRunner()
    if ssh:
        return SshRunner(ssh, sudo=sudo)
    if os.path.exists("/usr/bin/pvesh") or os.path.exists("/usr/sbin/pct"):
        return LocalRunner()
    print("vuurwag: no pvesh here and no --ssh host given, running in --demo mode", file=sys.stderr)
    return DemoRunner()
