"""EXTRA: THE NODE -- the Proxmox facts in lekker's idiom (vuurwag's own fragment, nd_).

The probe's snapshot drives the stage exactly where lekker read /proc: the CPU drives the fire, the load and
the uptime go on the status line and stamp the kernel log.  On top of that, lekker-style:
  - the boot log gets the node's facts (pve, kernel, CPUs, memory, guests, disks, storages, firewall, tailscale)
  - the top(1) table on tall screens lists the guests, containers and VMs (vmid, name, state, cpu, uptime,
    mem, lxc|qemu) under the okes
  - the meat on the grid follows the running guests: the next batch has 1..4 pieces
  - the node's events become wall(1) broadcasts and dmesg lines, and Koos says something about them
    (guest start/stop, backup finished/failed, disk warm, storage low, firewall enabled but stopped, tailscale gone,
    updates waiting, a reboot = Eskom was here, and the probe failing = the fire dying down)
  - Dokter Disk reads the SMART facts the probe already read (never a self-test)
"""
from __future__ import annotations

from typing import Any

from .. import sayings
from ..events import Event, Severity
from ..model import Snapshot, human_bytes
from .core import TOP_FMT, Braai

WALL_KINDS = {"backup_failed", "disk_unhealthy", "disk_hot", "storage_full", "firewall_down", "zpool_degraded", "reboot",
              "probe_down", "backup_ok", "storage_high"}
SPOKEN = {"hello", "guest_started", "guest_stopped", "guest_new", "guest_vanished", "backup_ok", "backup_failed",
          "disk_warm", "disk_hot", "disk_cool", "disk_unhealthy", "storage_high", "storage_full", "firewall_down",
          "firewall_up", "tailscale_down", "tailscale_up", "updates", "reboot", "probe_down", "probe_up", "node_cpu_high",
          "node_cpu_ok", "sensor_hot", "unprivileged", "zpool_degraded", "guest_cpu_high"}
LOG_TEXT = {
    "hello": "node: {subject} probe deur, die braai ken die plaas",
    "guest_mem_high": "gaste: {subject} se geheue is vol",
    "guest_locked": "gaste: {subject} is gesluit (backup of snapshot)",
    "node_cpu_ok": "thermal: host cpu weer rustig",
    "node_load_high": "load: host dra swaar",
    "node_mem_ok": "mem: host geheue weer oop",
    "node_swap_high": "mem: host swap hoog",
    "sensor_warm": "sensors: {subject} word warm",
    "sensor_ok": "sensors: {subject} weer koel",
    "disk_worn": "smart: {subject} is verslete",
    "storage_inactive": "pvesm: {subject} is nie aktief nie",
    "task_started": "taak: {subject} begin",
    "task_failed": "taak: {subject} het gefaal",
    "net_busy": "net: lyn besig, {subject}",
    "sizzle": "grid0: tsss",
    "guest_started": "gaste: {subject} gestart, 1 bord bygesit",
    "guest_stopped": "gaste: {subject} gestop, bord weggevat",
    "guest_new": "gaste: nuwe gas {subject} op die lys",
    "guest_vanished": "gaste: {subject} is van die lys af",
    "guest_cpu_high": "gaste: {subject} sweet (cpu hoog)",
    "guest_cpu_ok": "gaste: {subject} het afgekoel",
    "backup_started": "vzdump: backup van {subject} begin",
    "backup_ok": "vzdump: backup van {subject} klaar, OK",
    "backup_warn": "vzdump: backup van {subject} klaar, met waarskuwings",
    "backup_failed": "vzdump: backup van {subject} het GEFAAL",
    "disk_warm": "smart: {subject} word warm",
    "disk_hot": "smart: {subject} is TE WARM",
    "disk_cool": "smart: {subject} het afgekoel",
    "disk_unhealthy": "smart: {subject} is SIEK, backup aanbeveel",
    "storage_high": "pvesm: {subject} raak vol, hout raak min",
    "storage_full": "pvesm: {subject} is VOL",
    "firewall_down": "hek0: pve-firewall is aan maar loop NIE, die hek staan OOP",
    "firewall_up": "hek0: pve-firewall loop, hek toe",
    "tailscale_down": "toring: tailscale weg, 0 strepies",
    "tailscale_up": "toring: tailscale online",
    "updates": "apt: {subject} pakkette wag vir opdatering",
    "reboot": "eskom: die host het herbegin (Eskom was hier)",
    "probe_down": "probe: geen antwoord van die host nie, vuur brand laag",
    "probe_up": "probe: die host praat weer",
    "node_cpu_high": "thermal: host cpu hoog, vuur brul",
    "node_mem_high": "mem: host geheue vol",
    "zpool_degraded": "zfs: {subject} gedegradeer",
    "sensor_hot": "sensors: {subject} te warm",
    "unprivileged": "probe: nie root nie, half blind",
}


FIREWALL_WORD = {"on": "loop", "off": "af", "fault": "is aan maar loop NIE"}


class Node:
    def __init__(self, b: Braai, kuier=None) -> None:
        self.b = b
        self.kuier = kuier
        self.snap: Snapshot | None = None
        self.down = False
        self.events_seen = 0
        self.guest_cpu: dict[int, float] = {}
        self.guests_laid_out = 0
        self.install()

    # ---- what the probe says ------------------------------------------------------------------------------------------
    def update(self, snap: Snapshot) -> None:
        b = self.b
        self.snap = snap
        self.down = False
        n = snap.node
        if n.hostname and n.hostname != "?":
            host = n.hostname.split(".")[0][:16]
            if host != b.HOST:
                b.HOST = host
        if n.kernel and not b.KERNEL:
            b.KERNEL = ("Linux " + n.kernel)[:30]
        b.set_host(n.cpu_pct / 100.0, "%.2f" % n.loadavg[0], n.uptime)
        # the top(1) table is sized at layout time: a new guest count on a tall screen lays the stage out again
        if "table" in b.P and len(snap.guests) != self.guests_laid_out:
            self.guests_laid_out = len(snap.guests)
            b.layout()
        self.guests_laid_out = len(snap.guests)
        running = len(snap.running_guests)
        want = 1 if running <= 1 else 2 if running <= 3 else 3 if running <= 6 else 4
        if want != b.meat_count:
            b.meat_count = want
            b.logmsg(f"grid0: {running} gaste op, volgende batch kry {want} stuk{'ke' if want != 1 else ''}", True)
        b.FIREMOD.pop("nd_down", None)

    def probe_down(self) -> None:
        self.down = True
        self.b.fire_mod("nd_down", -0.45, self.b.T + 3600)

    def disks(self) -> list[dict] | None:
        s = self.snap
        if s is None:
            return None
        if not s.privileged or "disks" in s.missing:
            return [{"name": "disks", "st": "blind", "temp": None, "why": "geen root", "hot": False}]
        out = []
        for d in s.disks:
            if not d.smart.available:
                st, why = "skip", "geen SMART"
            elif d.healthy is False:
                st = "sick"
                bits = []
                if d.smart.passed is False:
                    bits.append("SMART se FAIL")
                for k, v in (("reallocated", d.smart.reallocated), ("pending", d.smart.pending),
                             ("uncorrectable", d.smart.uncorrectable), ("media errors", d.smart.media_errors)):
                    if v:
                        bits.append(f"{v} {k}")
                why = ", ".join(bits) or "sleg"
            else:
                st, why = "ok", ""
            out.append({"name": d.name, "st": st, "temp": d.temp, "why": why, "hot": d.temp_band in ("warm", "hot")})
        return out

    # ---- the events --------------------------------------------------------------------------------------------------------
    def event(self, ev: Event) -> None:
        b = self.b
        self.events_seen += 1
        subj = ev.subject or ""
        txt = LOG_TEXT.get(ev.kind)
        if txt:
            b.logmsg(txt.replace("{subject}", str(subj)), ev.severity < Severity.NOTICE)
        else:
            b.logmsg(f"node: {ev.kind} {subj}".strip(), True)
        if ev.kind in WALL_KINDS and ev.severity >= Severity.NOTICE:
            b.wall(sayings_wall(ev))
        if ev.kind == "reboot" and self.kuier is not None and self.kuier.ls["state"] == "off" and b.T > b.BOOT_END:
            self.kuier.ls_start(b.T)
        if ev.kind == "probe_down":
            self.probe_down()
        if ev.kind in ("backup_failed", "disk_unhealthy", "firewall_down", "storage_full", "zpool_degraded"):
            for w in ("koos", "sak", "jan"):
                b.set_face(w, "wide", b.T + 3)
        if ev.kind in SPOKEN and len(b.PRIO) < 3:
            line = sayings.say(ev.kind, subj, b.rng, now=b.T)
            b.PRIO.append([("K", line)])
            if ev.kind in ("backup_ok", "guest_started", "probe_up", "firewall_up"):
                b.PRIO[-1].append(("S+J", "Lekker!"))

    # ---- the boot log, the status line, top(1) ---------------------------------------------------------------------------------
    def hook_boot(self) -> list:
        s = self.snap
        if s is None:
            return [["w", "node: wag vir die eerste probe..."]]
        n = s.node
        ct, vm = s.guest_kinds
        out = [["w", f"pve: {n.pveversion or '?'} op {n.hostname} ({n.cpus} kerne, {human_bytes(n.mem_total)} RAM)"],
               ["w", f"gaste: {len(s.running_guests)} van {len(s.guests)} loop ({ct} CT, {vm} VM)"
                     + (": " + ", ".join(g.name for g in s.running_guests[:6]) + ("..." if len(s.running_guests) > 6 else "")
                        if s.running_guests else "")],
               ["w", "disks: " + (", ".join(f"{d.name} {d.kind}" + (f" {int(d.temp)}C" if d.temp is not None else "") for d in s.disks) or "geen")],
               ["w", "pvesm: " + (", ".join(f"{st.name} {st.free_pct:.0f}% vry" for st in s.storage) or "geen stoor")],
               ["w", "hek0: pve-firewall " + FIREWALL_WORD.get(s.firewall_state, "onbekend")
                     + "; toring: tailscale " + ("n/a" if s.tailscale is None else "online" if s.tailscale.online else "offline")
                     + f"; apt: {s.updates if s.updates is not None else '?'} updates"]]
        return out

    def hook_status(self, t: float) -> list:
        s = self.snap
        f = []
        if s is not None:
            f.append([4.5, f"gaste {len(s.running_guests)}/{len(s.guests)}"])
            hs = s.hottest_sensor
            if hs:
                f.append([6.8, f"{hs.label.split()[0].lower()} {int(hs.temp)}C"])
        if self.down:
            f.append([1.5, "probe: af"])
        return f

    def guest_rows_count(self) -> int:
        return len(self.snap.guests) if self.snap is not None else 0

    def top_rows(self, t: float) -> list[tuple[str, str]]:
        """Every guest, containers and VMs: the running ones by cpu, then the stopped ones."""
        s = self.snap
        if s is None:
            return []
        fmt = TOP_FMT
        rows = []
        guests = sorted(s.guests, key=lambda g: (not g.running, -g.cpu_pct, g.vmid))
        for g in guests:
            st = "T" if not g.running else "R" if g.cpu_pct > 20 else "S"
            tm = g.uptime if g.running else 0
            rows.append((fmt % (g.vmid, g.name[:8], 20, 0, st, "%.1f" % g.cpu_pct, "%d:%02d" % (int(tm / 3600), int(tm % 3600 / 60)),
                                (("%s --mem=%d%%" % (g.kind, int(g.mem_pct))) if g.running else "%s --gestop" % g.kind)
                                + (" " + ",".join(g.tags[:2]) if g.tags else "")),
                         "W" if st == "R" else "w" if g.running else "b"))
        return rows

    def install(self) -> None:
        b = self.b
        b.guest_rows_count = self.guest_rows_count
        b.top_rows = self.top_rows
        b.hook("boot", self.hook_boot)
        b.hook("status", self.hook_status)


def sayings_wall(ev: Event) -> str:
    subj = ev.subject or ""
    k = ev.kind
    if k == "backup_failed":
        return f"vzdump: die backup van {subj} het GEFAAL. Kyk na die log voor die dominee kom."
    if k == "backup_ok":
        return f"vzdump: backup van {subj} klaar en OK. Tannie bring die slaai."
    if k == "disk_unhealthy":
        return f"Dokter Disk: {subj} is siek. Maak VANDAG 'n backup."
    if k == "disk_hot":
        return f"Dokter Disk: {subj} is te warm. Hou hom koel."
    if k == "storage_full":
        return f"pvesm: {subj} is vol. Niks pas meer in nie, manne."
    if k == "storage_high":
        return f"pvesm: {subj} raak vol. Soos die kraal in lamtyd."
    if k == "firewall_down":
        return "hek0: pve-firewall is aan maar loop NIE. Die plaashek staan oop -- maak toe!"
    if k == "zpool_degraded":
        return f"zfs: {subj} is gedegradeer. Een disk is lam."
    if k == "reboot":
        return "Eskom was hier: die host het herbegin. Die vuur word weer aangesteek."
    if k == "probe_down":
        return "probe: die host antwoord nie. Die vuur brand laag tot hy terug is."
    return ev.text
