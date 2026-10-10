"""Typed snapshot of the node, parsed from the probe's JSON document."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    hostname: str = "?"
    uptime: float = 0.0
    loadavg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    cpus: int = 1
    cpu_pct: float = 0.0
    mem_total: int = 0
    mem_used: int = 0
    swap_total: int = 0
    swap_used: int = 0
    pveversion: str | None = None
    kernel: str | None = None
    cpu_model: str | None = None

    @property
    def mem_pct(self) -> float:
        return 100.0 * self.mem_used / self.mem_total if self.mem_total else 0.0

    @property
    def load_pct(self) -> float:
        """1-minute load as a percentage of core count."""
        return 100.0 * self.loadavg[0] / max(1, self.cpus)


@dataclass
class Guest:
    vmid: int
    name: str
    status: str = "unknown"
    cpu: float = 0.0  # fraction 0..1 of the guest's allotted cores
    cpus: int = 1
    mem: int = 0
    maxmem: int = 0
    disk: int = 0
    maxdisk: int = 0
    netin: int = 0
    netout: int = 0
    uptime: int = 0
    tags: list[str] = field(default_factory=list)
    lock: str | None = None
    pressure_cpu: float = 0.0

    @property
    def running(self) -> bool:
        return self.status == "running"

    @property
    def cpu_pct(self) -> float:
        return 100.0 * self.cpu

    @property
    def mem_pct(self) -> float:
        return 100.0 * self.mem / self.maxmem if self.maxmem else 0.0

    @property
    def label(self) -> str:
        return f"{self.vmid} {self.name}"


@dataclass
class Storage:
    name: str
    type: str = "?"
    active: bool = True
    total: int = 0
    used: int = 0
    avail: int = 0

    @property
    def used_pct(self) -> float:
        return 100.0 * self.used / self.total if self.total else 0.0

    @property
    def free_pct(self) -> float:
        return max(0.0, 100.0 - self.used_pct)


@dataclass
class Smart:
    available: bool = False
    passed: bool | None = None
    temp: float | None = None
    power_on_hours: int | None = None
    reallocated: int | None = None
    pending: int | None = None
    uncorrectable: int | None = None
    crc_errors: int | None = None
    percentage_used: int | None = None
    available_spare: int | None = None
    media_errors: int | None = None
    remaining_life: int | None = None


@dataclass
class Disk:
    name: str
    size: str = "?"
    model: str = "?"
    rota: bool = False
    tran: str | None = None
    nvme: bool = False
    smart: Smart = field(default_factory=Smart)

    @property
    def kind(self) -> str:
        if self.nvme:
            return "NVMe"
        return "HDD" if self.rota else "SSD"

    @property
    def temp(self) -> float | None:
        return self.smart.temp

    @property
    def warm_threshold(self) -> float:
        return 45.0 if self.rota else 55.0

    @property
    def hot_threshold(self) -> float:
        return 55.0 if self.rota else 65.0

    @property
    def temp_band(self) -> str:
        """ice | lekker | warm | hot | unknown"""
        t = self.temp
        if t is None:
            return "unknown"
        if t >= self.hot_threshold:
            return "hot"
        if t >= self.warm_threshold:
            return "warm"
        if t <= (28.0 if self.rota else 32.0):
            return "ice"
        return "lekker"

    @property
    def healthy(self) -> bool | None:
        s = self.smart
        if not s.available:
            return None
        if s.passed is False:
            return False
        for v in (s.reallocated, s.pending, s.uncorrectable, s.media_errors):
            if v:
                return False
        return True

    @property
    def wear_pct(self) -> int | None:
        """How much of the drive's life is 'drunk' (0..100)."""
        s = self.smart
        if s.percentage_used is not None:
            return int(s.percentage_used)
        if s.remaining_life is not None:
            return max(0, 100 - int(s.remaining_life))
        return None


@dataclass
class Sensor:
    chip: str
    label: str
    temp: float
    crit: float | None = None


@dataclass
class Net:
    iface: str
    rx_bps: float = 0.0
    tx_bps: float = 0.0


@dataclass
class Task:
    upid: str
    type: str
    id: str | None
    status: str | None
    starttime: int
    endtime: int | None
    user: str | None

    @property
    def running(self) -> bool:
        return self.endtime is None

    @property
    def ok(self) -> bool | None:
        if self.status is None:
            return None
        return self.status == "OK"

    @property
    def is_backup(self) -> bool:
        return self.type in ("vzdump", "backup")


@dataclass
class Tailscale:
    online: bool = False
    backend: str | None = None
    peers: int = 0
    peers_online: int = 0
    dns_name: str | None = None


@dataclass
class ZfsPool:
    name: str
    size: int
    alloc: int
    free: int
    health: str


@dataclass
class Snapshot:
    time: float = field(default_factory=time.time)
    privileged: bool = True
    node: Node = field(default_factory=Node)
    guests: list[Guest] = field(default_factory=list)
    storage: list[Storage] = field(default_factory=list)
    disks: list[Disk] = field(default_factory=list)
    zpools: list[ZfsPool] = field(default_factory=list)
    zfs_status: str | None = None
    sensors: list[Sensor] = field(default_factory=list)
    network: list[Net] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    firewall_running: bool | None = None
    tailscale: Tailscale | None = None
    updates: int | None = None
    update_packages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    probe_seconds: float = 0.0
    source: str = "?"
    missing: list[str] = field(default_factory=list)  # sections the probe could not produce

    # ── convenience ──
    @property
    def running_guests(self) -> list[Guest]:
        return [g for g in self.guests if g.running]

    @property
    def stopped_guests(self) -> list[Guest]:
        return [g for g in self.guests if not g.running]

    @property
    def hottest_sensor(self) -> Sensor | None:
        cands = [s for s in self.sensors if "Package" in s.label or "Tctl" in s.label or "Composite" in s.label]
        pool = cands or self.sensors
        return max(pool, key=lambda s: s.temp) if pool else None

    @property
    def net_total_bps(self) -> float:
        # vmbr0 carries the guests; enp1s0 is the uplink. Count only physical/uplink-ish ifaces.
        phys = [n for n in self.network if not n.iface.startswith(("vmbr", "tailscale", "wg"))]
        pool = phys or self.network
        return sum(n.rx_bps + n.tx_bps for n in pool)

    def guest(self, vmid: int) -> Guest | None:
        for g in self.guests:
            if g.vmid == vmid:
                return g
        return None


# ───────────────────────────── parsing ─────────────────────────────


def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _i(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def parse_snapshot(doc: dict[str, Any], source: str = "probe") -> Snapshot:
    """Build a Snapshot from the probe's JSON. Tolerates every section being null."""
    snap = Snapshot(source=source)
    snap.time = _f(doc.get("time"), time.time())
    snap.privileged = bool(doc.get("privileged", True))
    snap.errors = [str(e) for e in (doc.get("errors") or [])]
    snap.probe_seconds = _f(doc.get("probe_seconds"))
    missing: list[str] = []

    n = doc.get("node") or {}
    if not n:
        missing.append("node")
    la = n.get("loadavg") or [0, 0, 0]
    snap.node = Node(
        hostname=str(n.get("hostname") or "?"),
        uptime=_f(n.get("uptime")),
        loadavg=(_f(la[0]), _f(la[1]), _f(la[2])),
        cpus=_i(n.get("cpus"), 1) or 1,
        cpu_pct=_f(n.get("cpu_pct")),
        mem_total=_i(n.get("mem_total")),
        mem_used=_i(n.get("mem_used")),
        swap_total=_i(n.get("swap_total")),
        swap_used=_i(n.get("swap_used")),
        pveversion=n.get("pveversion"),
        kernel=n.get("kernel"),
        cpu_model=n.get("cpu_model"),
    )

    guests = doc.get("guests")
    if guests is None:
        missing.append("guests")
    for g in guests or []:
        snap.guests.append(Guest(
            vmid=_i(g.get("vmid")), name=str(g.get("name") or f"ct{g.get('vmid')}"),
            status=str(g.get("status") or "unknown"), cpu=_f(g.get("cpu")), cpus=_i(g.get("cpus"), 1) or 1,
            mem=_i(g.get("mem")), maxmem=_i(g.get("maxmem")), disk=_i(g.get("disk")), maxdisk=_i(g.get("maxdisk")),
            netin=_i(g.get("netin")), netout=_i(g.get("netout")), uptime=_i(g.get("uptime")),
            tags=list(g.get("tags") or []), lock=g.get("lock"), pressure_cpu=_f(g.get("pressure_cpu")),
        ))
    snap.guests.sort(key=lambda x: x.vmid)

    storage = doc.get("storage")
    if storage is None:
        missing.append("storage")
    for s in storage or []:
        snap.storage.append(Storage(
            name=str(s.get("name") or "?"), type=str(s.get("type") or "?"), active=bool(s.get("active", True)),
            total=_i(s.get("total")), used=_i(s.get("used")), avail=_i(s.get("avail")),
        ))

    disks = doc.get("disks")
    if disks is None:
        missing.append("disks")
    for d in disks or []:
        sm = d.get("smart") or {}
        smart = Smart(
            available=bool(sm.get("available")), passed=sm.get("passed"),
            temp=_f(sm["temp"]) if sm.get("temp") is not None else None,
            power_on_hours=sm.get("power_on_hours"), reallocated=sm.get("reallocated"), pending=sm.get("pending"),
            uncorrectable=sm.get("uncorrectable"), crc_errors=sm.get("crc_errors"),
            percentage_used=sm.get("percentage_used"), available_spare=sm.get("available_spare"),
            media_errors=sm.get("media_errors"), remaining_life=sm.get("remaining_life"),
        )
        snap.disks.append(Disk(
            name=str(d.get("name") or "?"), size=str(d.get("size") or "?"),
            model=str(sm.get("model") or d.get("model") or "?"), rota=bool(d.get("rota")),
            tran=d.get("tran"), nvme=bool(d.get("nvme")), smart=smart,
        ))

    zfs = doc.get("zfs")
    if zfs:
        for p in zfs.get("pools") or []:
            snap.zpools.append(ZfsPool(str(p.get("name")), _i(p.get("size")), _i(p.get("alloc")), _i(p.get("free")), str(p.get("health") or "?")))
        snap.zfs_status = zfs.get("status")

    sensors = doc.get("sensors")
    if sensors is None:
        missing.append("sensors")
    for s in sensors or []:
        snap.sensors.append(Sensor(str(s.get("chip")), str(s.get("label")), _f(s.get("temp")), s.get("crit")))

    for nrow in doc.get("network") or []:
        snap.network.append(Net(str(nrow.get("iface")), _f(nrow.get("rx_bps")), _f(nrow.get("tx_bps"))))

    tasks = doc.get("tasks")
    if tasks is None:
        missing.append("tasks")
    for t in tasks or []:
        snap.tasks.append(Task(
            upid=str(t.get("upid") or ""), type=str(t.get("type") or "?"), id=t.get("id"), status=t.get("status"),
            starttime=_i(t.get("starttime")), endtime=t.get("endtime"), user=t.get("user"),
        ))

    fw = doc.get("firewall")
    if fw is None:
        missing.append("firewall")
        snap.firewall_running = None
    else:
        snap.firewall_running = bool(fw.get("running"))

    ts = doc.get("tailscale")
    if ts is None:
        missing.append("tailscale")
    else:
        snap.tailscale = Tailscale(
            online=bool(ts.get("online")), backend=ts.get("backend"), peers=_i(ts.get("peers")),
            peers_online=_i(ts.get("peers_online")), dns_name=ts.get("dns_name"),
        )

    upd = doc.get("updates")
    if upd is None:
        missing.append("updates")
    else:
        snap.updates = _i(upd.get("count"))
        snap.update_packages = [str(p) for p in (upd.get("packages") or [])]

    snap.missing = missing
    return snap


# ───────────────────────────── formatting helpers ─────────────────────────────


def human_bytes(n: float, suffix: str = "B") -> str:
    n = float(n)
    for unit in ("", "K", "M", "G", "T", "P"):
        if abs(n) < 1024.0:
            return f"{n:.0f}{unit}{suffix}" if unit == "" else f"{n:.1f}{unit}{suffix}"
        n /= 1024.0
    return f"{n:.1f}E{suffix}"


def human_duration(seconds: float) -> str:
    seconds = int(seconds)
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"
