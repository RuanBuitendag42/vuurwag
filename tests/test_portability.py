"""Other people's Proxmox nodes: VMs as well as containers, the firewall off by default, an FQDN hostname,
no tailscale, a pvesh timeout, vzdump warnings, backup-only storage, and the weather place moving the sun."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from vuurwag.braai.stage import Stage
from vuurwag.events import GONE_TTL, EventEngine, Severity
from vuurwag.model import parse_snapshot
from vuurwag.weather import PRETORIA, WeatherService, country_hint, geocode_candidates, parse_geocode

HERE = Path(__file__).parent
FIXTURE = HERE / "fixtures" / "pve-node.json"
PROBE = HERE.parent / "vuurwag" / "probe" / "probe.py"


def doc():
    return json.loads(FIXTURE.read_text())


def kinds(events):
    return [e.kind for e in events]


@pytest.fixture()
def probe():
    spec = importlib.util.spec_from_file_location("vuurwag_probe_port", PROBE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def guest(vmid, kind="lxc", status="running", cpu=0.05, name=None):
    return {"vmid": vmid, "kind": kind, "name": name or f"{kind}{vmid}", "status": status, "cpu": cpu, "cpus": 2,
            "mem": 1 << 29, "maxmem": 1 << 31, "uptime": 3600 if status == "running" else 0, "tags": []}


def stage_with(d):
    st = Stage(160, 45, seed=1, host="pve", weather=WeatherService(mode="off"))
    st.resize(160, 45)
    st.on_snapshot(parse_snapshot(d))
    return st


# ── B1 firewall ──────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,enabled,running,state,fault", [
    ("Status: enabled/running", True, True, "on", False),
    ("Status: enabled/stopped", True, False, "fault", True),
    ("Status: disabled/running", False, True, "off", False),
    ("Status: disabled/stopped", False, False, "off", False),
])
def test_firewall_states(probe, raw, enabled, running, state, fault):
    fw = probe.parse_firewall(raw + "\n")
    assert (fw["enabled"], fw["running"]) == (enabled, running)
    d = doc()
    d["firewall"] = fw
    snap = parse_snapshot(d)
    assert snap.firewall_state == state
    eng = EventEngine()
    evs = eng.update(snap)
    assert ("firewall_down" in kinds(evs)) is fault
    assert (eng.mood() == "GATVOL") is fault
    boot = " ".join(line for _c, line in stage_with(d).node.hook_boot())
    word = {"on": "pve-firewall loop;", "off": "pve-firewall af;", "fault": "pve-firewall is aan maar loop NIE"}[state]
    assert word in boot


def test_firewall_command_missing(probe, monkeypatch):
    monkeypatch.setattr(probe, "run", lambda cmd, timeout=8.0: None)
    assert probe.firewall_section() is None
    d = doc()
    d["firewall"] = None
    snap = parse_snapshot(d)
    assert snap.firewall_state is None and "firewall" in snap.missing
    assert "firewall_down" not in kinds(EventEngine().update(snap))
    assert "pve-firewall onbekend" in " ".join(line for _c, line in stage_with(d).node.hook_boot())


def test_probe_v1_firewall_document_still_parses():
    d = doc()
    d["firewall"] = {"raw": "Status: disabled/stopped", "running": False}
    assert parse_snapshot(d).firewall_state == "off"


# ── B2 VMs ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_probe_lists_both_kinds_and_their_fallbacks(probe):
    ct = probe.parse_pct_list("VMID       Status     Lock         Name\n100        running                 dns\n")
    vm = probe.parse_qm_list("      VMID NAME                 STATUS     MEM(MB)    BOOTDISK(GB) PID\n"
                             "       200 win11                running    8192              64.00 1234\n")
    assert ct == [{"vmid": 100, "kind": "lxc", "status": "running", "name": "dns"}]
    assert vm == [{"vmid": 200, "kind": "qemu", "name": "win11", "status": "running"}]
    both, missing = probe.merge_guests(vm, ct)
    assert [g["vmid"] for g in both] == [100, 200] and missing == []
    assert probe.merge_guests(None, vm) == (vm, ["lxc"])
    assert probe.merge_guests(None, None) == (None, ["lxc", "qemu"])


def test_vm_only_node():
    d = doc()
    d["guests"] = [guest(200, "qemu"), guest(201, "qemu", status="stopped")]
    snap = parse_snapshot(d)
    assert snap.guest_kinds == (0, 2) and snap.guests[0].short_kind == "VM"
    st = stage_with(d)
    boot = " ".join(line for _c, line in st.node.hook_boot())
    assert "gaste: 1 van 2 loop (0 CT, 2 VM)" in boot and "LXC" not in boot
    assert ["4.5", "gaste 1/2"] == [str(x) for x in st.node.hook_status(0)[0]]
    rows = st.node.top_rows(0)
    assert any("qemu --mem=" in r for r, _c in rows) and any("qemu --gestop" in r for r, _c in rows)
    assert st.b.meat_count == 1


def test_mixed_node_and_many_running():
    d = doc()
    d["guests"] = [guest(100 + i) for i in range(5)] + [guest(200 + i, "qemu") for i in range(3)]
    st = stage_with(d)
    boot = " ".join(line for _c, line in st.node.hook_boot())
    assert "gaste: 8 van 8 loop (5 CT, 3 VM)" in boot
    rows = [r for r, _c in st.node.top_rows(0)]
    assert sum("lxc --mem" in r for r in rows) == 5 and sum("qemu --mem" in r for r in rows) == 3
    assert st.b.meat_count == 4       # more than four running: the grid holds four pieces


def test_zero_guests():
    d = doc()
    d["guests"] = []
    st = stage_with(d)
    boot = " ".join(line for _c, line in st.node.hook_boot())
    assert "gaste: 0 van 0 loop (0 CT, 0 VM)" in boot
    assert st.node.top_rows(0) == [] and st.b.meat_count == 1
    assert ["gaste 0/0"] == [x for x in st.node.hook_status(0)[0] if isinstance(x, str)]


def test_no_lxc_wording_left_in_the_status_line_or_table():
    st = stage_with(doc())
    text = " ".join(str(x) for f in st.node.hook_status(0) for x in f) + " ".join(r for r, _c in st.node.top_rows(0))
    assert "LXC" not in text and "lxc 5/" not in text


# ── B3 hostname ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_node_name_from_pve_then_short_hostname(probe, tmp_path, monkeypatch):
    nodename = tmp_path / "nodename"
    nodename.write_text("braai1\n")
    assert probe.node_name(str(nodename), str(tmp_path / "nolink")) == "braai1"
    link = tmp_path / "local"
    link.symlink_to("nodes/braai2")
    assert probe.node_name(str(tmp_path / "absent"), str(link)) == "braai2"
    monkeypatch.setattr(probe.socket, "gethostname", lambda: "pve3.example.lan")
    assert probe.node_name(str(tmp_path / "absent"), str(tmp_path / "nolink")) == "pve3"


# ── C4 guests unreadable, gone, stopped ─────────────────────────────────────────────────────────────────────────

def test_a_pvesh_timeout_is_not_every_guest_vanishing():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    d2["guests"] = None
    evs = eng.update(parse_snapshot(d2))
    assert "guest_vanished" not in kinds(evs) and eng.mood() != "GATVOL"
    evs = eng.update(parse_snapshot(d))           # back: nothing is "new" either
    assert "guest_new" not in kinds(evs) and "guest_vanished" not in kinds(evs)


def test_one_kind_unreadable_keeps_those_guests():
    eng = EventEngine()
    d = doc()
    d["guests"] = [guest(100), guest(200, "qemu")]
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    d2["guests"] = [guest(100)]
    d2["guests_missing"] = ["qemu"]
    assert "guest_vanished" not in kinds(eng.update(parse_snapshot(d2)))


def test_gone_guest_expires():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    d2["guests"] = [g for g in d2["guests"] if g["vmid"] != 100]
    evs = eng.update(parse_snapshot(d2))
    assert "guest_vanished" in kinds(evs) and eng.mood() == "GATVOL"
    d2["time"] = d["time"] + GONE_TTL + 1
    eng.update(parse_snapshot(d2))
    assert "gone:100" not in eng.active and eng.mood() != "GATVOL"


def test_stopping_a_guest_is_not_sticky():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    next(g for g in d2["guests"] if g["vmid"] == 102)["status"] = "stopped"
    evs = eng.update(parse_snapshot(d2))
    assert "guest_stopped" in kinds(evs)
    assert not any(k.startswith("down:") for k in eng.active)


# ── C5 vzdump warnings ───────────────────────────────────────────────────────────────────────────────────────────

def test_backup_with_warnings_is_a_notice():
    eng = EventEngine()
    d = doc()
    eng.update(parse_snapshot(d))
    d2 = copy.deepcopy(d)
    d2["time"] = d["time"] + 10
    d2["tasks"].insert(0, {"upid": "UPID:x:vzdump:w", "type": "vzdump", "id": "121", "status": "WARNINGS: 2",
                           "starttime": int(d["time"] + 1), "endtime": int(d["time"] + 9), "user": "root@pam"})
    evs = eng.update(parse_snapshot(d2))
    ev = next(e for e in evs if e.kind == "backup_warn")
    assert ev.severity == Severity.NOTICE
    assert "backup_failed" not in kinds(evs) and eng.mood() != "GATVOL"


# ── C6 storage ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_backup_only_storage_may_fill_up():
    eng = EventEngine()
    d = doc()
    local = d["storage"][0]
    assert local["content"] == "backup,vztmpl,snippets,iso"
    local["used"] = int(local["total"] * 0.99)
    evs = eng.update(parse_snapshot(d))
    assert "storage_full" not in kinds(evs) and "storage_high" not in kinds(evs)


def test_storage_inactive_only_after_it_was_active():
    eng = EventEngine()
    d = doc()
    d["storage"].append({"name": "usb", "type": "dir", "active": False, "total": 0, "used": 0, "avail": 0,
                         "content": "images"})
    assert "storage_inactive" not in kinds(eng.update(parse_snapshot(d)))
    d["storage"][1]["active"] = False                       # local-lvm was active a tick ago
    assert "storage_inactive" in kinds(eng.update(parse_snapshot(d)))


def test_storage_thresholds_from_env(monkeypatch):
    monkeypatch.setenv("VUURWAG_STORAGE_WARN", "50")
    monkeypatch.setenv("VUURWAG_STORAGE_CRIT", "70")
    eng = EventEngine()
    d = doc()
    lvm = d["storage"][1]
    lvm["used"] = int(lvm["total"] * 0.6)
    assert "storage_high" in kinds(eng.update(parse_snapshot(d)))
    lvm["used"] = int(lvm["total"] * 0.75)
    assert "storage_full" in kinds(eng.update(parse_snapshot(d)))


# ── C7 tailscale ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_tailscale_absent_is_not_a_fault(probe, monkeypatch):
    monkeypatch.setattr(probe.shutil, "which", lambda name, path=None: None)
    assert probe.tailscale_section() is None
    d = doc()
    d["tailscale"] = None
    eng = EventEngine()
    assert "tailscale_down" not in kinds(eng.update(parse_snapshot(d)))
    assert "tailscale n/a" in " ".join(line for _c, line in stage_with(d).node.hook_boot())


def test_tailscale_never_online_does_not_nag_but_going_offline_does():
    eng = EventEngine()
    d = doc()
    d["tailscale"] = {"installed": True, "backend": "Stopped", "online": False}
    assert "tailscale_down" not in kinds(eng.update(parse_snapshot(d)))
    assert "tailscale" not in eng.active
    d["tailscale"] = {"installed": True, "backend": "Running", "online": True}
    eng.update(parse_snapshot(d))
    d["tailscale"] = {"installed": True, "backend": "Stopped", "online": False}
    assert "tailscale_down" in kinds(eng.update(parse_snapshot(d)))


def test_old_tailscale_without_self_online(probe):
    assert probe.parse_tailscale({"BackendState": "Running", "Self": {"DNSName": "x."}})["online"] is True
    assert probe.parse_tailscale({"BackendState": "Stopped", "Self": {}})["online"] is False
    assert probe.parse_tailscale({"BackendState": "Running", "Self": {"Online": False}})["online"] is False


# ── C8 the place moves the sun ───────────────────────────────────────────────────────────────────────────────────

def test_geocoding_moves_the_sun(tmp_path):
    forecast = json.loads((HERE / "fixtures" / "open-meteo-forecast-pretoria.json").read_text())

    def fetch(url: str) -> dict:
        if "geocoding" in url:
            return {"results": [{"name": "Oslo", "latitude": 59.91, "longitude": 10.75, "country_code": "NO",
                                 "country": "Norway"}]}
        return forecast

    svc = WeatherService(place="Oslo, Norway", fetch=fetch, cache_file=tmp_path / "none.json")
    assert svc.latlon == PRETORIA                     # first run, no cache
    st = Stage(160, 45, seed=1, host="pve", weather=svc)
    rise0, set0 = st.weer.sun_hours()
    svc.fetch_now()                                    # the geocoder answers during the session
    rise1, set1 = st.weer.sun_hours()
    assert st.weer.latlon == (59.91, 10.75)
    # 17.5 degrees further west: solar noon about 70 minutes later, whatever the date
    assert ((rise1 + set1) / 2 - (rise0 + set0) / 2) == pytest.approx((28.24 - 10.75) * 4 / 60, abs=0.05)


# ── D3 any country ───────────────────────────────────────────────────────────────────────────────────────────────

def test_unknown_country_searches_unfiltered_and_ranks_by_country():
    assert country_hint("Lyon, France") == "France" and country_hint("Lyon, FR") is None
    assert geocode_candidates("Lyon, France") == [("Lyon", None, False), ("France", None, True)]
    doc_ = {"results": [{"name": "Lyon", "latitude": 41.0, "longitude": -74.0, "country_code": "US", "country": "United States"},
                        {"name": "Lyon", "latitude": 45.76, "longitude": 4.83, "country_code": "FR", "country": "France"}]}
    assert parse_geocode(doc_, "Lyon, France").country_code == "FR"
    assert parse_geocode(doc_, "Lyon").country_code == "US"


def test_two_part_place_without_country_falls_back_to_the_town(tmp_path):
    assert geocode_candidates("Hatfield, Pretoria")[-1] == ("Pretoria", None, True)
    assert geocode_candidates("Pierre van Ryneveld, Centurion")[-1] == ("Centurion", None, True)
    forecast = json.loads((HERE / "fixtures" / "open-meteo-forecast-pretoria.json").read_text())
    asked = []

    def fetch(url: str) -> dict:
        if "geocoding" in url:
            asked.append(url)
            if "name=Pretoria" in url:
                return {"results": [{"name": "Pretoria", "latitude": -25.74, "longitude": 28.19, "country_code": "ZA",
                                     "country": "South Africa"}]}
            return {"results": []}
        return forecast

    svc = WeatherService(place="Hatfield, Pretoria", fetch=fetch, cache_file=tmp_path / "none.json")
    svc.fetch_now()
    assert svc.place.name == "Pretoria" and "name=Hatfield" in asked[0]
    assert any("using Pretoria instead" in n for n in svc.notes)


# ── E disks ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_virtual_block_devices_are_not_disks(probe, monkeypatch):
    names = ["sda", "nvme0n1", "zd0", "zd16", "rbd0", "nbd0", "drbd1", "dm-0", "md0", "loop0"]

    def run_json(cmd, timeout=8.0):
        if cmd[0] == "lsblk":
            return {"blockdevices": [{"name": n, "type": "disk", "size": "1G"} for n in names]}
        return None

    monkeypatch.setattr(probe, "run_json", run_json)
    assert [d["name"] for d in probe.disks_section()] == ["sda", "nvme0n1"]
