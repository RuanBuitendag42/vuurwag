"""`vuurwag` command line: run the TUI, print one snapshot, take a screenshot, or serve it to a browser."""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
import re
import shlex
import sys
import time
from datetime import datetime

from .weather import CONDITIONS, DEFAULT_PLACE


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vuurwag", description="Vuurwag - die HugeBraai vuurwag: 'n braai in ASCII vir die Proxmox-node",
                                epilog="keys: ? in the app lists every key (q leaves)")
    p.add_argument("--demo", action="store_true", help="fake but lively data (no Proxmox needed)")
    p.add_argument("--ssh", metavar="HOST", help="probe a remote Proxmox host over ssh (e.g. root@pve.example.lan)")
    p.add_argument("--sudo", action="store_true", help="with --ssh: run the probe via `sudo -n python3 -` on the host")
    p.add_argument("--interval", type=float, default=5.0, help="seconds between probes (default 5)")
    p.add_argument("--fps", type=int, default=10, help="frames a second, 1-20 (default 10; 4 is plenty for a screen left running)")
    p.add_argument("-g", "--green", action="store_true", help="green-phosphor monochrome")
    p.add_argument("--truecolor", action="store_true", help="subtle 24-bit shades instead of the 8 ANSI colours (same art)")
    p.add_argument("--no-disks", action="store_true", help="leave the disks alone (no Dokter Disk)")
    p.add_argument("--place", help=f"town for the real weather (default: $VUURWAG_PLACE or {DEFAULT_PLACE!r})")
    p.add_argument("--weather", choices=["auto"] + CONDITIONS, default="auto",
                   help="force a weather condition (default: live from Open-Meteo; --demo cycles through all of them)")
    p.add_argument("--no-weather", action="store_true", help="never touch the network for weather (clock only)")
    p.add_argument("--time", metavar="HH:MM", help="pretend the local clock says HH:MM today (sun, sky, moon)")
    p.add_argument("--date", metavar="MM-DD[ HH:MM[:SS]]", help="pretend it is that date (the special days; lekker's LEKKER_DATE)")
    p.add_argument("--debug", action="store_true", help="show fps, frame time and process cpu above the status line")
    p.add_argument("--seed", type=int, help="random seed, for reproducible screenshots")
    p.add_argument("--host", help="the host name on the tower and in the log until the first probe arrives")
    p.add_argument("--once", action="store_true", help="probe once, print a summary, exit")
    p.add_argument("--json", action="store_true", help="with --once: print the parsed Snapshot as JSON")
    p.add_argument("--screenshot", metavar="PATH", help="run headless for a few seconds and save an SVG screenshot")
    p.add_argument("--size", default="160x45", help="with --screenshot: terminal size WxH (default 160x45)")
    p.add_argument("--wait", type=float, default=6.0, help="with --screenshot: seconds to run before the shot (default 6)")
    p.add_argument("--keys", default="", help="with --screenshot: keys to press after the boot, e.g. 'n,n,w' (comma separated)")
    # accepted for the systemd units and old habits; the braai is always full-width, 7-bit, 8 colours
    for old in ("--tv", "--mono", "--ascii", "--no-camera"):
        p.add_argument(old, action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--theme", default="auto", help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="command")
    s = sub.add_parser("serve", help="serve the TUI to a browser (textual-serve) for the TV")
    s.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
    s.add_argument("--port", type=int, default=8787, help="port (default 8787)")
    s.add_argument("--public-url", help="URL the browser should use if different from host:port")
    s.add_argument("app_args", nargs=argparse.REMAINDER, help="arguments passed to the vuurwag app (e.g. --demo)")
    return p


def _runner(args: argparse.Namespace):
    from .collector import choose_runner

    return choose_runner(demo=args.demo, ssh=args.ssh, sudo=args.sudo)


def cmd_once(args: argparse.Namespace) -> int:
    from .collector import Collector
    from .model import human_bytes

    runner = _runner(args)
    snap = asyncio.run(Collector(runner).once())
    if args.json:
        print(json.dumps(dataclasses.asdict(snap), indent=2, default=str))
        return 0
    n = snap.node
    print(f"{n.hostname}: up {n.uptime / 3600:.1f} h, cpu {n.cpu_pct:.0f}%, mem {n.mem_pct:.0f}%, load {n.loadavg}")
    print(f"guests: {len(snap.running_guests)} running, {len(snap.stopped_guests)} stopped")
    for g in snap.guests:
        print(f"  {g.vmid:>4} {g.name:<18} {g.status:<8} cpu {g.cpu_pct:5.1f}%  mem {g.mem_pct:3.0f}%  tags={','.join(g.tags)}")
    print("disks:")
    for d in snap.disks:
        print(f"  {d.name:<8} {d.kind:<4} {d.model:<24} temp={d.temp} band={d.temp_band} healthy={d.healthy} wear={d.wear_pct}%")
    print("storage:")
    for s in snap.storage:
        print(f"  {s.name:<12} {s.type:<8} {s.used_pct:5.1f}% used  {human_bytes(s.avail)} free")
    hs = snap.hottest_sensor
    print(f"hottest sensor: {hs.label} {hs.temp:.0f}C" if hs else "sensors: none")
    print(f"net: {human_bytes(snap.net_total_bps)}/s  firewall={snap.firewall_running}  "
          f"tailscale={'online' if snap.tailscale and snap.tailscale.online else 'n/a'}  updates={snap.updates}")
    print(f"tasks: {len(snap.tasks)} (backups: {sum(1 for t in snap.tasks if t.is_backup)})")
    if snap.missing:
        print(f"missing sections: {', '.join(snap.missing)}")
    if snap.errors:
        print("probe errors:")
        for e in snap.errors:
            print(f"  - {e}")
    print(f"probe took {snap.probe_seconds}s via {snap.source}")
    return 0


def clock_offset(hhmm: str | None, date: str | None = None) -> float:
    """Seconds to add to time.time() so the local clock reads the given date and/or HH:MM."""
    off = 0.0
    now = datetime.now()
    if date:
        m = re.match(r"^\s*(\d\d?)-(\d\d?)(?:[ T_](\d\d?):(\d\d)(?::(\d\d))?)?\s*$", date)
        if m:
            mo, d, h, mi, s = m.groups()
            if h is None:
                h, mi, s = now.hour, now.minute, now.second
            try:
                want = now.replace(month=int(mo), day=int(d), hour=int(h) % 24, minute=int(mi or 0) % 60,
                                   second=int(s or 0) % 60, microsecond=0)
                off = (want - now).total_seconds()
            except ValueError:
                off = 0.0
    if hhmm:
        hh, _, mm = hhmm.partition(":")
        base = datetime.fromtimestamp(time.time() + off)
        target = base.replace(hour=int(hh) % 24, minute=int(mm or 0) % 60, second=0, microsecond=0)
        off += (target - base).total_seconds()
    return off


def make_weather(args: argparse.Namespace):
    from .weather import WeatherService

    if args.no_weather and args.weather == "auto":
        mode = "off"
    elif args.demo:
        mode = "demo"
    else:
        mode = "live"
    return WeatherService(place=args.place, mode=mode, forced=args.weather)


def make_app(args: argparse.Namespace):
    from .app import VuurwagApp

    host = args.host
    if not host and args.ssh:
        host = args.ssh.split("@")[-1]
    return VuurwagApp(_runner(args), interval=args.interval, fps=max(1, min(20, args.fps)), green=args.green,
                      truecolor=args.truecolor, seed=args.seed, weather=make_weather(args),
                      clock_offset=clock_offset(args.time, args.date), debug=args.debug, no_disks=args.no_disks, host=host)


def cmd_screenshot(args: argparse.Namespace) -> int:
    from .gfx.svg import tidy_svg

    w, _, h = args.size.partition("x")
    size = (int(w), int(h))
    keys = [k for k in args.keys.split(",") if k]

    async def go() -> None:
        app = make_app(args)
        async with app.run_test(size=size) as pilot:
            await pilot.pause(0.5)
            if keys:
                app.stage.b.skip_boot()
                await pilot.pause(0.3)
                for k in keys:
                    app.stage.press(k)
                    await pilot.pause(0.2)
            await pilot.pause(args.wait)
            svg = app.export_screenshot(title="Vuurwag")
        os.makedirs(os.path.dirname(os.path.abspath(args.screenshot)), exist_ok=True)
        with open(args.screenshot, "w", encoding="utf-8") as fh:
            fh.write(tidy_svg(svg))

    asyncio.run(go())
    print(f"saved {args.screenshot}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        from textual_serve.server import Server
    except ImportError:  # pragma: no cover
        print("textual-serve is not installed (uv sync should have installed it)", file=sys.stderr)
        return 1
    app_args = [a for a in args.app_args if a != "--"]
    # -P: no cwd on sys.path, so a stray ./vuurwag/ (an old checkout) is never imported instead of this install
    cmd = " ".join([shlex.quote(sys.executable), "-P", "-m", "vuurwag"] + [shlex.quote(a) for a in app_args])
    public = args.public_url or f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}"
    server = Server(cmd, host=args.host, port=args.port, title="Vuurwag - HugeBraai", public_url=public)
    print(f"vuurwag: serving `{cmd}` on http://{args.host}:{args.port} (open this on the TV's browser)")
    server.serve()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        return cmd_serve(args)
    if args.once:
        return cmd_once(args)
    if args.screenshot:
        return cmd_screenshot(args)
    os.environ.setdefault("TEXTUAL_ANIMATIONS", "none")
    app = make_app(args)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
