"""The demo generator, the probe script's own helpers, and the Textual app: every key, four sizes, green mode,
the ANSI constraint on what reaches the terminal, probe failure, and the screenshot CLI."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from vuurwag.app import VuurwagApp
from vuurwag.collector import DEMO_GUESTS, Collector, DemoRunner, ProbeError, choose_runner
from vuurwag.model import parse_snapshot
from vuurwag.weather import WeatherService
from vuurwag.widgets.scene import Scene

PROBE = Path(__file__).parent.parent / "vuurwag" / "probe" / "probe.py"


def test_demo_documents_parse_and_drift():
    runner = DemoRunner(seed=42, fast=True)
    snaps = [parse_snapshot(runner.document(), "demo") for _ in range(60)]
    assert all(s.node.hostname == "pve" for s in snaps)
    assert {g.vmid for g in snaps[0].guests} == {g[0] for g in DEMO_GUESTS}
    assert {g.vmid for g in snaps[0].stopped_guests} >= {110, 111}
    assert len(snaps[0].disks) == 2 and snaps[0].disks[0].kind == "NVMe"
    cpus = {round(s.node.cpu_pct) for s in snaps}
    assert len(cpus) > 3, "demo cpu should drift"
    assert all(0 < s.node.mem_pct < 100 for s in snaps)
    assert all(s.hottest_sensor is not None for s in snaps)
    assert runner.tasks and any(t["type"] == "vzdump" for t in runner.tasks)


def test_demo_is_async_probe():
    runner = DemoRunner(seed=1)
    doc = asyncio.run(runner.probe())
    assert doc["node"]["cpus"] == 6 and doc["privileged"] is True
    snap = asyncio.run(Collector(runner).once())
    assert snap.source == "demo"


def test_choose_runner_defaults_to_demo_off_host(capsys):
    r = choose_runner(demo=False, ssh=None)
    assert r.name in ("demo", "local")
    r2 = choose_runner(ssh="root@example")
    assert r2.name == "ssh:root@example"


def test_probe_script_is_stdlib_only_and_runs_here():
    spec = importlib.util.spec_from_file_location("vuurwag_probe", PROBE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    doc = mod.collect()
    assert doc["probe_version"] == 2
    assert doc["node"]["hostname"]
    assert doc["node"]["cpu_pct"] is not None
    assert isinstance(doc["network"], list)
    json.dumps(doc)
    snap = parse_snapshot(doc, "local-test")
    assert snap.node.cpus >= 1
    src = PROBE.read_text()
    for bad in ("import requests", "import yaml", "import textual", "import rich"):
        assert bad not in src
    assert "-t short" not in src and "--test" not in src, "the probe only reads SMART, it never starts a self-test"


async def _collector_failure():
    class Boom:
        name = "boom"

        async def probe(self):
            raise ProbeError("ssh: connect to host failed")

    seen = []
    c = Collector(Boom(), interval=0.01)

    async def cb(snap, err):
        seen.append((snap, err))
        if len(seen) >= 2:
            c.stop()

    task = c.start(cb)
    try:
        await asyncio.wait_for(task, 2)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    return seen, c


def test_collector_reports_failures():
    seen, c = asyncio.run(_collector_failure())
    assert seen and seen[0][0] is None and "ssh" in seen[0][1]
    assert c.failures >= 1 and c.last_error


async def wait_for(pilot, cond, timeout=8.0):
    import time as _t
    t0 = _t.monotonic()
    while _t.monotonic() - t0 < timeout:
        if cond():
            return True
        await pilot.pause(0.1)
    return cond()


KEYS = ["space", "f", "d", "b", "w", "n", "v", "k", "s", "r", "t", "o", "l", "h", "m", "x", "j", "1", "2", "3", "4", "a", "i", "u",
        "p", "z", "e", "5", "6", "P", "up", "down", "question_mark", "escape", "g", "g"]


def demo_weather(tmp_path, name="w.json"):
    return WeatherService(mode="demo", cache_file=tmp_path / name)


@pytest.mark.parametrize("size", [(80, 24), (120, 40), (160, 45), (200, 55)])
async def test_app_runs_and_survives_every_key(size, tmp_path):
    app = VuurwagApp(DemoRunner(seed=7, fast=True), interval=0.2, fps=10, seed=7, weather=demo_weather(tmp_path))
    async with app.run_test(size=size) as pilot:
        scene = app.query_one(Scene)
        stage = app.stage
        assert await wait_for(pilot, lambda: stage.node.snap is not None), "the collector should have delivered a snapshot"
        stage.b.skip_boot()
        assert await wait_for(pilot, lambda: any("vuur aangesteek" in line for _t, line in stage.log_lines))
        for key in KEYS:
            await pilot.press(key)
            await pilot.pause(0.12)
        assert await wait_for(pilot, lambda: scene.frame > 10)
        assert scene.cache.strips and scene.cache.strips[0].cell_length == scene.size.width
        for strip in scene.cache.strips:
            for seg in strip:
                assert seg.text.isascii() and all(32 <= ord(c) < 127 for c in seg.text)
                if seg.style and seg.style.color:
                    assert seg.style.color.number is not None and seg.style.color.number < 8, "8 ANSI colours only"
                if seg.style and seg.style.bgcolor:
                    assert seg.style.bgcolor.number in (0, 1)
        assert (len(stage.node.snap.running_guests) > 0)
    # green phosphor: everything green, bright = bold
    app2 = VuurwagApp(DemoRunner(seed=3), interval=0.2, fps=6, green=True, seed=3,
                      weather=WeatherService(mode="off", cache_file=tmp_path / "w2.json"))
    async with app2.run_test(size=size) as pilot:
        await pilot.pause(0.6)
        app2.stage.b.skip_boot()
        await pilot.pause(0.5)
        sc = app2.query_one(Scene)
        assert sc.frame > 0
        styles = [seg.style for strip in sc.cache.strips for seg in strip if seg.style and seg.style.color]
        assert styles and all(s.color.number == 2 for s in styles)
    # truecolor opt-in: only shading changes
    app3 = VuurwagApp(DemoRunner(seed=3), interval=0.2, fps=6, truecolor=True, seed=3,
                      weather=WeatherService(mode="off", cache_file=tmp_path / "w3.json"))
    async with app3.run_test(size=size) as pilot:
        await pilot.pause(0.6)
        sc = app3.query_one(Scene)
        assert sc.frame > 0 and sc.stage.mode == "truecolor"


async def test_q_quits_and_the_node_events_reach_the_stage(tmp_path):
    app = VuurwagApp(DemoRunner(seed=2, fast=True), interval=0.15, fps=8, seed=2, weather=demo_weather(tmp_path))
    async with app.run_test(size=(160, 45)) as pilot:
        stage = app.stage
        assert await wait_for(pilot, lambda: stage.node.events_seen > 0)
        assert await wait_for(pilot, lambda: any("probe deur" in l or "pct:" in l for _t, l in stage.log_lines), 12)
        assert stage.b.meat_count in (1, 2, 3, 4)
        await pilot.press("q")
        await pilot.pause(0.3)
    assert app.return_value is None


async def test_weather_offline_boot_line(tmp_path):
    def fetch(url):
        raise OSError("no network in tests")
    ws = WeatherService(place="Pierre van Ryneveld, Centurion, South Africa", fetch=fetch, cache_file=tmp_path / "w.json")
    app = VuurwagApp(DemoRunner(seed=2), interval=0.2, fps=8, seed=2, weather=ws)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause(1.0)
        boot = " ".join(txt for _c, txt in app.stage.b.BOOTX)
        assert "geen internet" in boot
        assert ws.status == "offline"


async def test_probe_failure_shows_in_app(tmp_path):
    class Dead:
        name = "ssh:dead"

        async def probe(self):
            raise ProbeError("ssh: Connection timed out")

    app = VuurwagApp(Dead(), interval=0.2, fps=6, weather=WeatherService(mode="off", cache_file=tmp_path / "w.json"))
    async with app.run_test(size=(120, 40)) as pilot:
        assert await wait_for(pilot, lambda: app.stage.node.down)
        assert await wait_for(pilot, lambda: any("probe:" in line for _t, line in app.stage.log_lines))
        assert "nd_down" in app.stage.b.FIREMOD


def test_screenshot_cli_writes_exact_svg(tmp_path):
    from vuurwag.cli import main
    out = tmp_path / "shot.svg"
    assert main(["--demo", "--seed", "1", "--weather", "rain", "--time", "21:30", "--screenshot", str(out), "--size", "100x30",
                 "--wait", "1.0", "--keys", "n"]) == 0
    svg = out.read_text()
    assert svg.startswith("<svg") and "font-variant-ligatures: none" in svg
    assert not any(ch in svg for ch in "▀▄█░")
    assert '">&#160;' not in svg


def test_old_flags_are_still_accepted():
    from vuurwag.cli import build_parser, clock_offset
    args = build_parser().parse_args(["--demo", "--tv", "--mono", "--fps", "4", "--date", "12-25 18:00"])
    assert args.demo and args.fps == 4
    off = clock_offset(None, "12-25 18:00")
    import time
    lt = time.localtime(time.time() + off)
    assert (lt.tm_mon, lt.tm_mday, lt.tm_hour) == (12, 25, 18)
