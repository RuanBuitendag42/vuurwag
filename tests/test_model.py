"""Parsing the probe document (a fixture captured from a real node as root; host name generalised to "pve")."""
from __future__ import annotations

import json
from pathlib import Path

from vuurwag.model import human_bytes, human_duration, parse_snapshot

FIXTURE = Path(__file__).parent / "fixtures" / "pve-node.json"


def load():
    return json.loads(FIXTURE.read_text())


def test_fixture_parses_everything():
    snap = parse_snapshot(load(), source="fixture")
    assert snap.privileged is True
    assert snap.missing == []
    assert snap.node.hostname == "pve"
    assert snap.node.cpus == 6
    assert snap.node.mem_total > 15 * 1024 ** 3
    assert 0 <= snap.node.cpu_pct <= 100
    assert 0 < snap.node.mem_pct < 100


def test_guests_sorted_and_states():
    snap = parse_snapshot(load())
    vmids = [g.vmid for g in snap.guests]
    assert vmids == sorted(vmids)
    assert {g.vmid for g in snap.stopped_guests} == {110, 111}
    assert len(snap.running_guests) == 5
    dns = snap.guest(100)
    assert dns is not None and dns.name == "core-dns" and dns.tags == ["core", "dns"]
    assert dns.label == "100 core-dns"
    assert 0 < dns.mem_pct < 100


def test_disks_smart():
    snap = parse_snapshot(load())
    assert len(snap.disks) == 1
    d = snap.disks[0]
    assert d.name == "sda" and d.kind == "SSD" and d.model == "TS256GMTS830S"
    assert d.smart.available and d.smart.passed is True
    assert d.temp and 20 < d.temp < 60
    assert d.temp_band in ("lekker", "ice")
    assert d.healthy is True
    assert d.smart.power_on_hours == 4234
    assert d.wear_pct == 20  # Remaining_Lifetime_Perc 80


def test_storage_sensors_network_misc():
    snap = parse_snapshot(load())
    names = {s.name for s in snap.storage}
    assert names == {"local", "local-lvm"}
    for s in snap.storage:
        assert 0 < s.used_pct < 100 and s.free_pct == 100 - s.used_pct
    hs = snap.hottest_sensor
    assert hs is not None and hs.label == "Package id 0" and hs.crit == 100.0
    assert any(n.iface == "enp1s0" for n in snap.network)
    assert snap.net_total_bps >= 0
    assert snap.firewall_running is True
    assert snap.tailscale and snap.tailscale.online and snap.tailscale.peers == 3
    assert snap.updates is None or snap.updates >= 0
    assert len(snap.tasks) == 15 and all(not t.is_backup for t in snap.tasks)


def test_all_sections_null_is_fine():
    doc = {k: None for k in ("node", "guests", "storage", "disks", "zfs", "sensors", "network", "tasks", "firewall", "tailscale", "updates")}
    doc["errors"] = ["pvesh: not installed"]
    snap = parse_snapshot(doc)
    assert snap.guests == [] and snap.disks == [] and snap.storage == []
    assert snap.firewall_running is None and snap.tailscale is None and snap.updates is None
    assert "guests" in snap.missing and "disks" in snap.missing
    assert snap.node.hostname == "?"
    assert snap.hottest_sensor is None


def test_unprivileged_fixture_shape():
    doc = load()
    doc["privileged"] = False
    doc["guests"] = None
    doc["disks"] = [{"name": "sda", "size": "238.5G", "model": "TS", "rota": False, "tran": "sata", "nvme": False, "smart": None}]
    snap = parse_snapshot(doc)
    assert not snap.privileged
    assert snap.disks[0].smart.available is False
    assert snap.disks[0].healthy is None and snap.disks[0].temp_band == "unknown"


def test_nvme_wear_and_health():
    doc = load()
    doc["disks"] = [{
        "name": "nvme0n1", "size": "931.5G", "model": "X", "rota": False, "tran": "nvme", "nvme": True,
        "smart": {"available": True, "passed": None, "temp": 70, "power_on_hours": 10, "percentage_used": 93,
                  "available_spare": 100, "media_errors": 2, "reallocated": None, "pending": None,
                  "uncorrectable": None, "crc_errors": None, "remaining_life": None},
    }]
    d = parse_snapshot(doc).disks[0]
    assert d.kind == "NVMe" and d.temp_band == "hot" and d.wear_pct == 93 and d.healthy is False


def test_human_helpers():
    assert human_bytes(0) == "0B"
    assert human_bytes(1536) == "1.5KB"
    assert human_bytes(3 * 1024 ** 3) == "3.0GB"
    assert human_duration(90) == "1m"
    assert human_duration(3600 * 5 + 60 * 7) == "5h 7m"
    assert human_duration(86400 * 2 + 3600 * 3) == "2d 3h"
