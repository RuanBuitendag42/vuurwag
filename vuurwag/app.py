"""The Textual application: wires the collector, the events engine, the weather and the braai stage.

Every key goes to the stage the way lekker reads keys (q leaves; any key skips the boot or closes the help;
the extras see the rest), so `?` in the app lists everything.
"""
from __future__ import annotations

from rich.terminal_theme import TerminalTheme
from textual import events
from textual.app import App, ComposeResult

# xterm's colours, as the screenshots show them: 8 normal, 8 bright (bold = bright on the console)
XTERM_THEME = TerminalTheme(
    (0, 0, 0), (229, 229, 229),
    [(0, 0, 0), (205, 0, 0), (0, 205, 0), (205, 205, 0), (0, 0, 238), (205, 0, 205), (0, 205, 205), (229, 229, 229)],
    [(127, 127, 127), (255, 0, 0), (0, 255, 0), (255, 255, 0), (92, 92, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)],
)

from .braai.stage import Stage
from .collector import Collector, Runner
from .events import EventEngine
from .model import Snapshot
from .weather import WeatherService
from .widgets.scene import Scene


class VuurwagApp(App[None]):
    CSS = """
    Screen { background: #000000; color: #c0c0c0; }
    """
    TITLE = "Vuurwag"

    def __init__(self, runner: Runner, interval: float = 5.0, fps: int = 10, green: bool = False, truecolor: bool = False,
                 seed: int | None = None, weather: WeatherService | None = None, clock_offset: float = 0.0,
                 debug: bool = False, no_disks: bool = False, host: str | None = None, **_ignored) -> None:
        super().__init__(ansi_color=not truecolor)
        self.runner = runner
        self.collector = Collector(runner, interval)
        self.engine = EventEngine()
        self.fps = fps
        self.weather = weather
        self.debug_mode = debug
        self.stage = Stage(seed=seed, host=host, green=green, truecolor=truecolor, weather=weather,
                           clock_offset=clock_offset, no_disks=no_disks)
        self.snapshot: Snapshot | None = None

    # compatibility: the old name
    @property
    def world(self) -> Stage:
        return self.stage

    def compose(self) -> ComposeResult:
        yield Scene(self.stage, fps=self.fps, debug=self.debug_mode, id="scene")

    def on_mount(self) -> None:
        self.collector.start(self.on_snapshot)
        if self.weather:
            self.weather.start()

    def on_unmount(self) -> None:
        self.collector.stop()
        if self.weather:
            self.weather.stop()

    def export_screenshot(self, *, title: str | None = None, simplify: bool = False) -> str:
        """Textual's export, with xterm's 8 colours and a black background (what a real terminal shows)."""
        import io

        from rich.console import Console

        assert self._driver is not None, "App must be running"
        width, height = self.size
        console = Console(width=width, height=height, file=io.StringIO(), force_terminal=True, color_system="truecolor",
                          record=True, legacy_windows=False, safe_box=False)
        screen_render = self.screen._compositor.render_update(full=True, screen_stack=self.app._background_screens,
                                                              simplify=simplify)
        console.print(screen_render)
        return console.export_svg(title=title or self.title, theme=XTERM_THEME)

    async def on_key(self, event: events.Key) -> None:
        key = event.character if (event.character and event.character.isprintable() and event.key not in ("space",)) else event.key
        self.stage.press(key)
        event.stop()
        if self.stage.quit:
            self.exit()

    # ---- data ----
    async def on_snapshot(self, snap: Snapshot | None, error: str | None) -> None:
        if not self.is_running or self._exit:
            return
        if snap is None:
            for ev in self.engine.probe_failed(error or "unknown"):
                self.stage.on_event(ev)
            self.stage.on_probe_failed(error or "unknown")
            return
        self.snapshot = snap
        evs = self.engine.update(snap)
        self.stage.on_snapshot(snap)
        for ev in evs:
            self.stage.on_event(ev)
