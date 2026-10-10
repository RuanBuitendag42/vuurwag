"""The Scene widget: drives the Stage at lekker's frame rate and hands Textual only the rows that changed.

The frame buffer is lekker's (one character and one colour letter per cell); a row becomes a Strip of segments
by runs of colour, and a row whose cells did not change is not rebuilt, so what goes to the terminal is small.
"""
from __future__ import annotations

import time

from textual.geometry import Region
from textual.strip import Strip
from textual.widget import Widget

from ..braai.buf import StripCache
from ..braai.stage import Stage


class Scene(Widget):
    DEFAULT_CSS = """
    Scene { width: 1fr; height: 1fr; background: #000000; }
    """

    def __init__(self, stage: Stage, fps: int = 10, debug: bool = False, **kw) -> None:
        super().__init__(**kw)
        self.stage = stage
        self.fps = max(1, min(20, fps))
        self.debug = debug
        self.cache = StripCache()
        self.frame = 0
        self._last = time.monotonic()
        self._stats_t0 = time.monotonic()
        self._stats_cpu0 = time.process_time()
        self._stats_frames = 0
        self._stats_ms = 0.0
        self.fps_measured = 0.0
        self.cpu_measured = 0.0
        self.frame_ms = 0.0

    def on_mount(self) -> None:
        self.stage.resize(self.size.width or 80, self.size.height or 24)
        self.set_interval(1.0 / self.fps, self.tick)

    def on_resize(self) -> None:
        self.stage.resize(self.size.width, self.size.height)
        self.cache = StripCache()
        self.refresh()

    def tick(self) -> None:
        now = time.monotonic()
        dt = now - self._last
        self._last = now
        w, h = self.size.width, self.size.height
        if w <= 0 or h <= 0:
            return
        t0 = time.perf_counter()
        st = self.stage
        if (w, h) != (st.cols, st.rows):
            st.resize(w, h)
        st.step(dt)
        changed = self.cache.update(st.buf, st.mode)
        self.frame += 1
        ms = (time.perf_counter() - t0) * 1000
        self._stats_ms += ms
        self._stats_frames += 1
        if now - self._stats_t0 >= 2.0:
            span = now - self._stats_t0
            self.fps_measured = self._stats_frames / span
            self.frame_ms = self._stats_ms / max(1, self._stats_frames)
            self.cpu_measured = 100.0 * (time.process_time() - self._stats_cpu0) / span
            self._stats_t0 = now
            self._stats_cpu0 = time.process_time()
            self._stats_frames = 0
            self._stats_ms = 0.0
            if self.debug:
                st.debug_text = f"{self.fps_measured:4.1f} fps  {self.frame_ms:4.1f} ms/raam  proses cpu {self.cpu_measured:3.0f}%"
        if st.quit:
            self.app.exit()
            return
        if not changed:
            return
        if len(changed) > h * 0.6:
            self.refresh()
        else:
            self.refresh(*[Region(0, y, w, 1) for y in changed])

    def render_line(self, y: int) -> Strip:
        strips = self.cache.strips
        if 0 <= y < len(strips):
            s = strips[y]
            if s.cell_length != self.size.width:
                return s.adjust_cell_length(self.size.width)
            return s
        return Strip.blank(self.size.width)
