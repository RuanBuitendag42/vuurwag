"""Events engine: diff consecutive Snapshots and emit braai-speak events."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum

from .model import Snapshot, human_bytes


class Severity(IntEnum):
    INFO = 0      # ✓ lekker
    NOTICE = 1    # · worth a mention
    WARN = 2      # ⚠ eish
    CRIT = 3      # ✖ gatvol


@dataclass
class Event:
    kind: str                 # machine key, drives the sayings table + widgets
    severity: Severity
    text: str                 # log line (braai speak)
    subject: str | None = None  # e.g. vmid or device name
    time: float = field(default_factory=time.time)
    sticky: bool = False      # stays "active" until cleared (feeds the Braai-O-Meter)


SUSTAIN_TICKS = 3  # cpu-high must persist this many snapshots before it counts


class EventEngine:
    """Stateful: call `update(snapshot)` (or `probe_failed(msg)`) each tick, get new events back.

    `active` holds sticky conditions currently true; the Braai-O-Meter reads it.
    """

    def __init__(self) -> None:
        self.prev: Snapshot | None = None
        self.active: dict[str, Event] = {}
        self.guest_cpu_high: dict[int, int] = {}
        self.seen_tasks: set[str] = set()
        self.first = True
        self.probe_down = False
        self.ticks = 0

    # ── helpers ──
    def _set(self, key: str, ev: Event, out: list[Event]) -> None:
        ev.sticky = True
        cur = self.active.get(key)
        if cur is None or cur.kind != ev.kind or cur.severity != ev.severity:
            self.active[key] = ev      # new condition, or it escalated / de-escalated
            out.append(ev)
        else:
            cur.text = ev.text         # same condition: refresh the text, keep the original time

    def _clear(self, key: str, out: list[Event], ok: Event | None = None) -> None:
        if key in self.active:
            del self.active[key]
            if ok is not None:
                out.append(ok)

    # ── public ──
    def probe_failed(self, message: str) -> list[Event]:
        out: list[Event] = []
        self._set("probe", Event("probe_down", Severity.CRIT, f"die vuur is dood - probe failed: {message}"), out)
        self.probe_down = True
        return out

    def update(self, snap: Snapshot) -> list[Event]:
        out: list[Event] = []
        self.ticks += 1
        if self.probe_down:
            self._clear("probe", out, Event("probe_up", Severity.INFO, "die vuur brand weer - probe is back"))
            self.probe_down = False
        prev = self.prev
        n = snap.node

        if self.first:
            out.append(Event("hello", Severity.INFO,
                             f"vuurwag aangesteek on {n.hostname} - {len(snap.running_guests)} on the grid, "
                             f"{len(snap.stopped_guests)} in the yskas, {len(snap.disks)} dop(s) in the koelerboks"))
            if not snap.privileged:
                out.append(Event("unprivileged", Severity.WARN, "probe is not root - no pvesh/smartctl data (run as root or --sudo)"))

        # ── guests ──
        prev_guests = {g.vmid: g for g in prev.guests} if prev else {}
        for g in snap.guests:
            pg = prev_guests.get(g.vmid)
            if pg is not None and pg.running != g.running:
                if g.running:
                    out.append(Event("guest_started", Severity.INFO, f"{g.label} is back on the grid", str(g.vmid)))
                    self._clear(f"down:{g.vmid}", out)
                else:
                    out.append(Event("guest_stopped", Severity.WARN, f"{g.label} came off the grid ({g.status})", str(g.vmid)))
                    self._set(f"down:{g.vmid}", Event("guest_down", Severity.WARN, f"{g.label} is not running", str(g.vmid)), out)
            if pg is not None and not g.running and not pg.running:
                pass  # intentionally stopped: lives in the fridge, no nagging
            if g.lock and (pg is None or pg.lock != g.lock):
                out.append(Event("guest_locked", Severity.NOTICE, f"{g.label} is locked ({g.lock}) - someone is busy with it", str(g.vmid)))
            # sustained high cpu
            if g.running and g.cpu_pct > 80:
                self.guest_cpu_high[g.vmid] = self.guest_cpu_high.get(g.vmid, 0) + 1
                if self.guest_cpu_high[g.vmid] == SUSTAIN_TICKS:
                    self._set(f"cpu:{g.vmid}", Event("guest_cpu_high", Severity.WARN,
                                                      f"{g.label} is flaring up (cpu {g.cpu_pct:.0f} %)", str(g.vmid)), out)
            else:
                if self.guest_cpu_high.get(g.vmid, 0) >= SUSTAIN_TICKS:
                    self._clear(f"cpu:{g.vmid}", out, Event("guest_cpu_ok", Severity.INFO, f"{g.label} has settled down (cpu {g.cpu_pct:.0f} %)", str(g.vmid)))
                self.guest_cpu_high[g.vmid] = 0
            if g.running and g.mem_pct > 92:
                self._set(f"mem:{g.vmid}", Event("guest_mem_high", Severity.WARN, f"{g.label} is stuffed (mem {g.mem_pct:.0f} %)", str(g.vmid)), out)
            else:
                self._clear(f"mem:{g.vmid}", out)
        if prev:
            for vmid, pg in prev_guests.items():
                if snap.guest(vmid) is None:
                    out.append(Event("guest_vanished", Severity.CRIT, f"{pg.label} vanished from the grid entirely", str(vmid)))
                    self._set(f"gone:{vmid}", Event("guest_gone", Severity.CRIT, f"{pg.label} is missing", str(vmid)), out)
            for g in snap.guests:
                if g.vmid not in prev_guests and not self.first:
                    out.append(Event("guest_new", Severity.INFO, f"new piece on the grid: {g.label}", str(g.vmid)))
                    self._clear(f"gone:{g.vmid}", out)

        # ── node ──
        if n.cpu_pct >= 85:
            self._set("node_cpu", Event("node_cpu_high", Severity.WARN, f"the fire is roaring - node cpu {n.cpu_pct:.0f} %"), out)
        elif n.cpu_pct < 70:
            self._clear("node_cpu", out, Event("node_cpu_ok", Severity.INFO, f"fire has calmed down - node cpu {n.cpu_pct:.0f} %"))
        if n.load_pct >= 150:
            self._set("node_load", Event("node_load_high", Severity.WARN, f"load {n.loadavg[0]:.2f} on {n.cpus} cores - the coals are overloaded"), out)
        elif n.load_pct < 100:
            self._clear("node_load", out)
        if n.mem_pct >= 90:
            self._set("node_mem", Event("node_mem_high", Severity.WARN, f"the kettle is full - mem {n.mem_pct:.0f} %"), out)
        elif n.mem_pct < 85:
            self._clear("node_mem", out, Event("node_mem_ok", Severity.INFO, f"mem back to {n.mem_pct:.0f} %"))
        if n.swap_total and n.swap_used / n.swap_total > 0.5:
            self._set("node_swap", Event("node_swap_high", Severity.NOTICE, f"swap at {100 * n.swap_used / n.swap_total:.0f} % - scraping the bottom of the pot"), out)
        else:
            self._clear("node_swap", out)
        if 0 < n.uptime < 15 * 60:
            self._set("reboot", Event("reboot", Severity.WARN, f"beurtkrag! {n.hostname} rebooted {int(n.uptime // 60)} min ago"), out)
        else:
            self._clear("reboot", out)
        if n.cpu_pct == 0 and n.cpus == 1 and not snap.node.mem_total:
            pass

        # ── sensors ──
        hs = snap.hottest_sensor
        if hs:
            crit = hs.crit or 100.0
            if hs.temp >= crit - 10:
                self._set("sensor_hot", Event("sensor_hot", Severity.CRIT, f"{hs.label} at {hs.temp:.0f} °C - the lid is about to melt"), out)
            elif hs.temp >= 75:
                self._set("sensor_hot", Event("sensor_warm", Severity.WARN, f"{hs.label} at {hs.temp:.0f} °C - getting toasty"), out)
            elif hs.temp < 68:
                self._clear("sensor_hot", out, Event("sensor_ok", Severity.INFO, f"{hs.label} back to {hs.temp:.0f} °C"))

        # ── disks ──
        for d in snap.disks:
            key = f"disk_temp:{d.name}"
            band = d.temp_band
            if band == "hot":
                self._set(key, Event("disk_hot", Severity.CRIT, f"{d.name} is HOT ({d.temp:.0f} °C) - die bier kook!", d.name), out)
            elif band == "warm":
                self._set(key, Event("disk_warm", Severity.WARN, f"{d.name} is getting warm ({d.temp:.0f} °C)", d.name), out)
            elif band in ("lekker", "ice"):
                self._clear(key, out, Event("disk_cool", Severity.INFO, f"{d.name} is cold again ({d.temp:.0f} °C)", d.name))
            hk = f"disk_health:{d.name}"
            if d.healthy is False:
                s = d.smart
                why = "SMART FAILED" if s.passed is False else f"realloc={s.reallocated or 0} pending={s.pending or 0} media={s.media_errors or 0}"
                self._set(hk, Event("disk_unhealthy", Severity.CRIT, f"{d.name} ({d.model}) is going off - {why}", d.name), out)
            else:
                self._clear(hk, out)
            wear = d.wear_pct
            if wear is not None and wear >= 90:
                self._set(f"disk_wear:{d.name}", Event("disk_worn", Severity.WARN, f"{d.name} is {wear} % drunk - almost finished", d.name), out)

        # ── storage ──
        for s in snap.storage:
            key = f"storage:{s.name}"
            if not s.active:
                self._set(key, Event("storage_inactive", Severity.CRIT, f"storage {s.name} is inactive", s.name), out)
            elif s.used_pct >= 95:
                self._set(key, Event("storage_full", Severity.CRIT, f"storage {s.name} is {s.used_pct:.0f} % full - the woodpile is bare!", s.name), out)
            elif s.used_pct >= 85:
                self._set(key, Event("storage_high", Severity.WARN, f"storage {s.name} at {s.used_pct:.0f} % - ons het meer hout nodig", s.name), out)
            else:
                self._clear(key, out)

        for p in snap.zpools:
            key = f"zpool:{p.name}"
            if p.health != "ONLINE":
                self._set(key, Event("zpool_degraded", Severity.CRIT, f"zpool {p.name} is {p.health}", p.name), out)
            else:
                self._clear(key, out)

        # ── tasks ──
        for t in snap.tasks:
            if t.running and t.upid not in self.seen_tasks:
                self.seen_tasks.add(t.upid)
                if t.is_backup:
                    out.append(Event("backup_started", Severity.NOTICE, f"backup of {t.id or 'the node'} started - packing padkos", t.id))
                elif not self.first:
                    out.append(Event("task_started", Severity.NOTICE, f"task {t.type} {t.id or ''} started", t.id))
            elif not t.running:
                fin_key = f"done:{t.upid}"
                if fin_key not in self.seen_tasks and (t.upid in self.seen_tasks or (prev is not None and t.endtime and t.endtime > prev.time - 2)):
                    self.seen_tasks.add(fin_key)
                    if t.is_backup:
                        if t.ok:
                            out.append(Event("backup_ok", Severity.INFO, f"backup of {t.id or 'the node'} finished - padkos is gepak", t.id))
                        else:
                            out.append(Event("backup_failed", Severity.CRIT, f"backup of {t.id or 'the node'} FAILED: {t.status}", t.id))
                    elif t.ok is False:
                        out.append(Event("task_failed", Severity.WARN, f"task {t.type} {t.id or ''} failed: {t.status}", t.id))
        self.seen_tasks = {u for u in self.seen_tasks if u.endswith(tuple(t.upid for t in snap.tasks)) or u in {t.upid for t in snap.tasks}} if len(self.seen_tasks) > 200 else self.seen_tasks

        # ── network-ish ──
        if snap.tailscale is not None:
            if not snap.tailscale.online:
                self._set("tailscale", Event("tailscale_down", Severity.WARN, "tailscale is offline - the gate to the plot is shut"), out)
            else:
                self._clear("tailscale", out, Event("tailscale_up", Severity.INFO, "tailscale is back online"))
        if snap.firewall_running is False:
            self._set("firewall", Event("firewall_down", Severity.CRIT, "pve-firewall is NOT running - the gate is wide open"), out)
        elif snap.firewall_running:
            self._clear("firewall", out, Event("firewall_up", Severity.INFO, "pve-firewall is running again"))
        if snap.updates:
            n = snap.updates
            text = f"{n} update{'s' if n != 1 else ''} waiting" + (f": {', '.join(snap.update_packages[:3])}" if snap.update_packages else "")
            self._set("updates", Event("updates", Severity.NOTICE, text), out)
        else:
            self._clear("updates", out)
        if snap.missing and not self.first:
            pass
        bps = snap.net_total_bps
        if bps > 50_000_000:
            self._set("net_busy", Event("net_busy", Severity.NOTICE, f"lots of smoke - network at {human_bytes(bps)}/s"), out)
        else:
            self._clear("net_busy", out)

        # ── periodic sizzle lines so the log is never dead ──
        if not self.first and self.ticks % 12 == 0 and snap.running_guests:
            g = snap.running_guests[(self.ticks // 12) % len(snap.running_guests)]
            out.append(Event("sizzle", Severity.INFO, f"{g.label} sizzling nicely (cpu {g.cpu_pct:.0f} %, mem {g.mem_pct:.0f} %)", str(g.vmid)))

        self.prev = snap
        self.first = False
        return out

    # ── meter ──
    @property
    def worst(self) -> Severity:
        return max((e.severity for e in self.active.values()), default=Severity.INFO)

    def mood(self) -> str:
        """LEKKER · OKAY-ISH · EISH · GATVOL"""
        w = self.worst
        warns = sum(1 for e in self.active.values() if e.severity == Severity.WARN)
        if w >= Severity.CRIT:
            return "GATVOL"
        if w == Severity.WARN:
            return "EISH" if warns >= 2 else "OKAY-ISH"
        if w == Severity.NOTICE:
            return "OKAY-ISH" if len(self.active) >= 3 else "LEKKER"
        return "LEKKER"
