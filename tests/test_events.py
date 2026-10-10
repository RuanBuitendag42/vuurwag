"""The events engine: thresholds, stickiness and the Braai-O-Meter mood."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from vuurwag.events import SUSTAIN_TICKS, EventEngine, Severity
from vuurwag.model import parse_snapshot
from vuurwag.sayings import IDLE, SAYINGS, easter, idle, say

FIXTURE = Path(__file__).parent / "fixtures" / "pve-node.json"


def doc():
    return json.loads(FIXTURE.read_text())


def kinds(events):
    return [e.kind for e in events]


def test_hello_and_updates_on_first_tick():
    eng = EventEngine()
    evs = eng.update(parse_snapshot(doc()))
    assert kinds(evs)[0] == "hello"
    assert "updates" in kinds(evs)
    assert eng.mood() in ("LEKKER", "OKAY-ISH")


def test_guest_stop_and_start():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    for g in d2["guests"]:
        if g["vmid"] == 102:
            g["status"] = "stopped"
    evs = eng.update(parse_snapshot(d2))
    assert "guest_stopped" in kinds(evs) and "guest_down" in kinds(evs)
    assert eng.mood() == "OKAY-ISH"
    evs = eng.update(parse_snapshot(d))
    assert "guest_started" in kinds(evs)
    assert "down:102" not in eng.active
    assert eng.mood() in ("LEKKER", "OKAY-ISH")


def test_guest_cpu_must_be_sustained():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    for g in d2["guests"]:
        if g["vmid"] == 121:
            g["cpu"] = 0.95
    seen = []
    for _ in range(SUSTAIN_TICKS):
        seen += kinds(eng.update(parse_snapshot(d2)))
    assert seen.count("guest_cpu_high") == 1
    assert "cpu:121" in eng.active
    evs = eng.update(parse_snapshot(d))
    assert "guest_cpu_ok" in kinds(evs)


def test_guest_vanished_is_critical():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    d2["guests"] = [g for g in d2["guests"] if g["vmid"] != 100]
    evs = eng.update(parse_snapshot(d2))
    assert "guest_vanished" in kinds(evs)
    assert eng.mood() == "GATVOL"


def test_node_thresholds_and_reboot():
    eng = EventEngine()
    d = doc()
    d["node"]["cpu_pct"] = 95
    d["node"]["mem_used"] = int(d["node"]["mem_total"] * 0.95)
    d["node"]["uptime"] = 120
    evs = eng.update(parse_snapshot(d))
    k = kinds(evs)
    assert "node_cpu_high" in k and "node_mem_high" in k and "reboot" in k
    assert eng.mood() == "EISH"
    d["node"]["cpu_pct"] = 10
    d["node"]["mem_used"] = int(d["node"]["mem_total"] * 0.3)
    d["node"]["uptime"] = 10_000
    evs = eng.update(parse_snapshot(d))
    k = kinds(evs)
    assert "node_cpu_ok" in k and "node_mem_ok" in k
    assert eng.mood() in ("LEKKER", "OKAY-ISH")


def test_disk_temperature_bands_and_health():
    eng = EventEngine()
    d = doc()
    d["disks"][0]["smart"]["temp"] = 58
    evs = eng.update(parse_snapshot(d))
    assert "disk_warm" in kinds(evs)
    d["disks"][0]["smart"]["temp"] = 70
    evs = eng.update(parse_snapshot(d))
    assert "disk_hot" in kinds(evs) and eng.mood() == "GATVOL"
    d["disks"][0]["smart"]["temp"] = 35
    evs = eng.update(parse_snapshot(d))
    assert "disk_cool" in kinds(evs)
    d["disks"][0]["smart"]["reallocated"] = 3
    evs = eng.update(parse_snapshot(d))
    assert "disk_unhealthy" in kinds(evs)


def test_hdd_thresholds_are_lower():
    eng = EventEngine()
    d = doc()
    d["disks"][0]["rota"] = True
    d["disks"][0]["smart"]["temp"] = 47
    evs = eng.update(parse_snapshot(d))
    assert "disk_warm" in kinds(evs)


def test_storage_levels():
    eng = EventEngine()
    d = doc()
    s = d["storage"][0]
    s["used"] = int(s["total"] * 0.9)
    evs = eng.update(parse_snapshot(d))
    assert "storage_high" in kinds(evs)
    s["used"] = int(s["total"] * 0.97)
    evs = eng.update(parse_snapshot(d))
    assert "storage_full" in kinds(evs)


def test_backup_lifecycle():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    now = d["time"]
    d2 = copy.deepcopy(d)
    d2["time"] = now + 5
    d2["tasks"].insert(0, {"upid": "UPID:x:vzdump:1", "type": "vzdump", "id": "121", "status": None,
                           "starttime": int(now + 1), "endtime": None, "user": "root@pam"})
    evs = eng.update(parse_snapshot(d2))
    assert "backup_started" in kinds(evs)
    d3 = copy.deepcopy(d2)
    d3["time"] = now + 10
    d3["tasks"][0]["endtime"] = int(now + 9)
    d3["tasks"][0]["status"] = "OK"
    evs = eng.update(parse_snapshot(d3))
    assert "backup_ok" in kinds(evs)
    d4 = copy.deepcopy(d3)
    d4["time"] = now + 15
    d4["tasks"].insert(0, {"upid": "UPID:x:vzdump:2", "type": "vzdump", "id": "100", "status": "job errors",
                           "starttime": int(now + 12), "endtime": int(now + 14), "user": "root@pam"})
    evs = eng.update(parse_snapshot(d4))
    assert "backup_failed" in kinds(evs) and eng.mood() == "GATVOL" or "backup_failed" in kinds(evs)


def test_tailscale_firewall_probe_down():
    eng = EventEngine()
    d = doc()
    d["tailscale"]["online"] = False
    d["firewall"]["running"] = False
    evs = eng.update(parse_snapshot(d))
    assert "tailscale_down" in kinds(evs) and "firewall_down" in kinds(evs)
    assert eng.mood() == "GATVOL"
    evs = eng.probe_failed("ssh: connection refused")
    assert kinds(evs) == ["probe_down"] and evs[0].severity == Severity.CRIT
    d["tailscale"]["online"] = True
    d["firewall"]["running"] = True
    evs = eng.update(parse_snapshot(d))
    assert kinds(evs)[0] == "probe_up"
    assert "tailscale_up" in kinds(evs) and "firewall_up" in kinds(evs)


def test_sayings_cover_every_event_kind():
    eng_kinds = {
        "hello", "guest_started", "guest_stopped", "guest_cpu_high", "guest_cpu_ok", "guest_mem_high", "guest_vanished",
        "guest_new", "node_cpu_high", "node_cpu_ok", "node_load_high", "node_mem_high", "node_mem_ok", "node_swap_high",
        "reboot", "sensor_hot", "sensor_warm", "sensor_ok", "disk_warm", "disk_hot", "disk_cool", "disk_unhealthy",
        "disk_worn", "storage_high", "storage_full", "storage_inactive", "zpool_degraded", "backup_started", "backup_ok",
        "backup_failed", "task_failed", "tailscale_down", "tailscale_up", "firewall_down", "firewall_up", "updates",
        "net_busy", "probe_down", "probe_up", "unprivileged", "sizzle", "guest_locked",
    }
    missing = eng_kinds - set(SAYINGS)
    assert not missing, missing
    for k, lines in SAYINGS.items():
        if k not in ("guest_gone", "guest_down"):
            assert len(lines) >= 4, k
    assert len(IDLE) >= 20
    assert "{subject}" not in say("guest_started", "core-dns")
    assert idle() in IDLE
    assert isinstance(easter("springbok"), str)
