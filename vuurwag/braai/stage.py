"""The stage, assembled: the core with every extra plugged in, driven by the app (snapshots, events, keys)."""
from __future__ import annotations

import os
import platform
import random
import time

from ..events import Event
from ..model import Snapshot
from ..weather import WeatherService
from .core import Braai
from .dokter import Dokter
from .kuier import Kuier
from .node import Node
from .party import Party
from .plaas import Plaas
from .weer import Weer

KEYMAP = {"space": " ", "question_mark": "?", "up": "up", "down": "down", "left": "left", "right": "right"}


class Stage:
    def __init__(self, cols: int = 80, rows: int = 24, seed: int | None = None, host: str | None = None, green: bool = False,
                 truecolor: bool = False, weather: WeatherService | None = None, clock_offset: float = 0.0,
                 no_disks: bool = False, user: str | None = None) -> None:
        self.seed = seed
        self.weather = weather
        host = (host or platform.node().split(".")[0] or "braai")[:16]
        kernel = " ".join(x for x in (platform.system(), platform.release()) if x)
        user = user or os.environ.get("USER") or os.environ.get("LOGNAME") or "oke"
        self.b = Braai(cols, rows, seed=seed, host=host, kernel=kernel, user=user, green=green)
        self.truecolor = truecolor
        latlon = weather.latlon if weather else (-25.84, 28.24)
        self.weer = Weer(self.b, weather_fn=(weather.weather if weather else None), latlon=latlon, clock_offset=clock_offset,
                         latlon_fn=(lambda: weather.latlon) if weather else None)
        self.party = Party(self.b, clock_offset=clock_offset)
        self.kuier = Kuier(self.b)
        self.node = Node(self.b, kuier=self.kuier)
        self.dokter = Dokter(self.b, disks_fn=self.node.disks, no_disks=no_disks)
        self.plaas = Plaas(self.b, weer=self.weer)
        self.started = False
        self._last = time.monotonic()
        self.debug_text = ""

    # ---- what the widget calls -------------------------------------------------------------------------------------
    @property
    def mode(self) -> str:
        if self.b.GREEN:
            return "green"
        return "truecolor" if self.truecolor else "ansi"

    @property
    def cols(self) -> int:
        return self.b.COLS

    @property
    def rows(self) -> int:
        return self.b.ROWS

    @property
    def buf(self):
        return self.b.buf

    def resize(self, cols: int, rows: int) -> None:
        if not self.started:
            self.b.COLS, self.b.ROWS = cols, rows
            self.b.start()
            self.started = True
            return
        self.b.resize(cols, rows)

    def step(self, dt: float) -> None:
        if not self.started:
            self.b.start()
            self.started = True
        self.b.step(dt)
        if self.debug_text and not self.b.P.get("small") and self.b.T >= self.b.BOOT_END:
            self.b.buf.put(1, self.b.ROWS - 2, self.debug_text[: self.b.COLS - 2], "c")

    def press(self, key: str) -> None:
        k = KEYMAP.get(key, key)
        if len(k) != 1 and k not in ("up", "down", "left", "right"):
            return
        self.b.press(k)

    # ---- what the app feeds in --------------------------------------------------------------------------------------
    def on_snapshot(self, snap: Snapshot) -> None:
        self.node.update(snap)

    def on_event(self, ev: Event) -> None:
        self.node.event(ev)

    def on_probe_failed(self, error: str) -> None:
        self.node.probe_down()

    # ---- for the tests and the side channel ----------------------------------------------------------------------------
    @property
    def log_lines(self) -> list[tuple[float, str]]:
        return self.b.log_all

    @property
    def quit(self) -> bool:
        return self.b.quit

    def text(self) -> list[str]:
        return self.b.buf.text()
