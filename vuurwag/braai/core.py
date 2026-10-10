"""The core of the braai, ported from lekker: the stage, the okes and the brakkie, the half-drum braai with
its coals, flames, meat, smoke and sparks, the banter in cowsay bubbles, wall(1) broadcasts, the kernel log
in the status line, top(1) on tall screens, the boot log, the help card, and the hooks and keys the extras
plug into.

How the extras plug in: hook(NAME, fn) adds fn to a list the core runs at a fixed point:
  layout (t)        after the core has placed everything for a new size
  update (t, dt)    every frame, after the core's own updates
  sky, scenery, back, actors, front, overlay (t)   drawing layers, back to front (see draw_scene)
  status (t)        returns [priority, text] fields for the status line
  boot ()           returns [colour, text] lines for the boot log
  keyseq (t, hist)  sees every key first; true swallows it
  cleanup ()        on the way out
key(KEY, HELP, fn) binds a key; a key with HELP None stays out of the help.
"""
from __future__ import annotations

import math
import random
import re
import time
from typing import Any, Callable

from . import art
from .art import BAKKIE, BRAAI, CROSS, DOG, DOG_RUN, DOG_TROT, GUY, MOON, MOON_S, NAME, TOWER, TREE, TREE_S
from .buf import Buf, Sprite, ascii7, wrap
from .banter import CORE_TALK, HOT_TALK

VERSION = "4.0"
PI = math.pi
MARK_RE = re.compile(r"(?:^|\s+)!([a-z_0-9]+)\b")
NO_REPEAT = 600.0    # a line is not said again within ten minutes

COAL = ["*", "o", ".", ":", "*", "@", ",", "o", ";", "*", "."]
TOP_FMT = "%5s %-8s %3s %3s %s %5s %9s  %-26s "
TOP_W = len(TOP_FMT % ("PID", "USER", "PR", "NI", "S", "%CPU", "TIME+", "COMMAND"))
PUFF = [".", "o", "()", "( )", "(  )", "(   )", ".   .", "'   '"]

MEAT_NAME = {"chop": "tjop", "wors": "wors", "sosatie": "sosatie", "mielie": "mielie",
             "broodjie": "braaibroodjie", "snoek": "stuk snoek"}

# the pieces on the grid by how many there are: (x in the braai, kind, width); index 0 is the one Koos
# turns, the last the one the brakkie fancies; lekker's three are the default
MEAT_LAYOUTS = {
    1: [(10, "wors", 9)],
    2: [(5, "chop", 4), (11, "wors", 9)],
    3: [(5, "chop", 4), (10, "wors", 9), (20, "chop", 4)],
    4: [(3, "chop", 4), (8, "wors", 9), (17, "chop", 4), (21, "chop", 4)],
}


def meat_col(d: float) -> str:
    return "M" if d < 0.3 else "R" if d < 0.6 else "r" if d < 0.85 else "y"


class Braai:
    """The stage.  One instance per app; the extras take it in their constructor."""

    def __init__(self, cols: int = 80, rows: int = 24, seed: int | None = None, host: str = "braai",
                 kernel: str = "", user: str = "oke", green: bool = False) -> None:
        self.rng = random.Random(seed)
        self.buf = Buf(cols, rows)
        self.ROWS, self.COLS = rows, cols
        self.HOST = host or "braai"
        self.KERNEL = ascii7(kernel)[:30]
        self.USER = re.sub(r"[^A-Za-z0-9._-]", "", user)[:12] or "oke"
        self.GREEN = green
        self.mode = "green" if green else "ansi"
        self.quit = False
        # hooks, keys and the stage
        self.HOOK: dict[str, list[Callable]] = {}
        self.KEY: dict[str, Callable] = {}
        self.KEYHELP: list[tuple[str, str]] = []
        self.KEYHIST: list[str] = []
        # host facts
        self.T = 0.0
        self.CPU = 0.0
        self.LOAD = ""
        self.UPTIME = ""
        self.UP_OFF = 0.0
        self.have_cpu = False
        self.LOG: list[str] = []
        self.LOG_T: float | None = None
        self.log_all: list[tuple[float, str]] = []    # everything ever logged (the app's own record)
        # scene state
        self.P: dict[str, Any] = {}
        self.AVOID: list[list[int]] = []
        self.STARS: list[list[float]] = []
        self.DUST: list[tuple[int, int, str]] = []
        self.GROUND: list[tuple[int, int, str, str]] = []
        self.SMOKE: list[list[float]] = []
        self.SPARKS: list[list[float]] = []
        self.ST: dict[str, dict] = {}
        self.HEAT = 0.05
        self.FAN = 0.0
        self.WIND = 0.5
        self.CHOP = 0
        self.FLIPS = 0
        self.SIPS: dict[str, int] = {}
        self.DOPS: dict[str, int] = {}
        self.SHOOT: list[float] | None = None
        self.next_shoot = 14.0
        self.BOOT_END = 2.6
        self.SAYS: list[dict] = []
        self.talk_q: list[tuple[list[str], str]] = []
        self.talk_next = self.BOOT_END + 1.5
        self.talk_bag: list[int] = []
        self.PRIO: list[list] = []
        self.WALL: dict | None = None
        self.WALL_Q: list[str] = []
        self.HOT_SINCE = 0.0
        self.next_hot_wall = 0.0
        self.RAID: dict = {}
        self.next_raid = 80 + self.rng.random() * 40
        self.CAN: dict = {}
        self.PTIME: dict[str, float] = {}
        self.BUSY: dict[str, float] = {}
        self.AUTO_AT = 40.0
        self.FIREMOD: dict[str, list[float]] = {}
        self.WIND_ADD = 0.0
        self.SKY = {"stars": 1, "moon": 1, "dust": 1, "cross": 1, "shoot": 1}
        self.POWER = 1
        self.DAYLIGHT = 0.0
        self.DOG_AWAY = 0
        self.CAST = ["koos", "sak", "jan"]
        self.HEAD: dict[str, Callable] = {}
        self.MARK: dict[str, Callable] = {}
        self.COND: dict[str, Callable] = {}
        self.FILL: dict[str, Callable[[], str]] = {}    # extra {placeholders} the extras fill in
        self.BOOTX: list[tuple[str, str]] = []
        self.HELP = 0.0
        self.GUY = GUY
        self.NAME = dict(NAME)
        self.WHO = {"K": "koos", "S": "sak", "J": "jan", "D": "dog"}
        self.TALK: list[list] = [list(x) for x in CORE_TALK]
        self.HOT: list[list] = [list(x) for x in HOT_TALK]
        self.said_at: dict[str, float] = {}
        self.DOGAT: tuple = ()
        self.COAL_PH = [[self.rng.random() * len(COAL), 0.5 + self.rng.random() * 1.5] for _ in range(22)]
        # the meat
        self.MEAT: list[dict] = []
        self.BATCH = 0
        self.MEAT_STATE = "cooking"
        self.SERVE_AT = 0.0
        self.NEWBATCH_AT = 0.0
        self.meat_count = 3
        self.new_batch()
        self.lit = False
        self.help_title = f" vuurwag {VERSION} -- sleutels / keys "
        self.core_keys()

    # ---- hooks, keys, the stage ---------------------------------------------------------------
    def hook(self, name: str, fn: Callable) -> None:
        self.HOOK.setdefault(name, []).append(fn)

    def run_hooks(self, name: str, *args: Any) -> list:
        out: list = []
        for fn in self.HOOK.get(name, ()):
            r = fn(*args)
            if r is None:
                continue
            if isinstance(r, list):
                out.extend(r)
            else:
                out.append(r)
        return out

    def key(self, k: str, help_text: str | None, fn: Callable) -> None:
        self.KEY[k] = fn
        if help_text is not None:
            self.KEYHELP.append((k, help_text))

    def claim(self, name: str, t: float, secs: float) -> bool:
        for k, until in self.BUSY.items():
            if k != name and until > t:
                return False
        self.BUSY[name] = t + secs
        return True

    def release(self, name: str) -> None:
        self.BUSY.pop(name, None)

    def calm(self, t: float) -> bool:
        return not any(v > t for v in self.BUSY.values())

    def busy(self, name: str, t: float) -> bool:
        return self.BUSY.get(name, 0) > t

    def auto_ok(self, t: float) -> bool:
        return t >= self.AUTO_AT and self.calm(t) and not self.SAYS and not self.talk_q and not self.wall_up(t)

    def auto_done(self, t: float, gap: float | None = None) -> None:
        self.AUTO_AT = t + (gap if gap is not None else 25 + self.rng.random() * 20)

    def fire_mod(self, name: str, d: float, until: float) -> None:
        self.FIREMOD[name] = [d, until]

    def wall_up(self, t: float) -> bool:
        return bool(self.WALL) and self.WALL["until"] > t

    # ---- random helpers ----------------------------------------------------------------------
    def rand(self, n: float = 1.0) -> float:
        return self.rng.random() * n

    def irand(self, n: int) -> int:
        return int(self.rng.random() * n)

    def pick(self, *items: Any) -> Any:
        return items[int(self.rng.random() * len(items))]

    # ---- host facts ---------------------------------------------------------------------------
    def set_host(self, cpu: float | None, load: str, uptime_s: float | None) -> None:
        if cpu is not None:
            self.CPU = 0.0 if cpu < 0 else 1.0 if cpu > 1 else cpu
            self.have_cpu = True
        self.LOAD = load
        if uptime_s is not None:
            self.UP_OFF = uptime_s - self.T
            d, h, m = int(uptime_s / 86400), int(uptime_s % 86400 / 3600), int(uptime_s % 3600 / 60)
            self.UPTIME = f"{d}d {h}h" if d else f"{h}h {m}m" if h else f"{m}m"

    # The braai's kernel log: the newest line shows in the status bar.  A
    # quiet message (routine stuff) does not push the host's numbers aside.
    def logmsg(self, msg: str, quiet: bool = False) -> None:
        msg = ascii7(msg)
        self.LOG.append("[%9.2f] %s" % (self.T + self.UP_OFF, msg))
        while len(self.LOG) > 5:
            self.LOG.pop(0)
        self.log_all.append((time.time(), msg))
        if len(self.log_all) > 400:
            del self.log_all[:100]
        if not quiet:
            self.LOG_T = self.T

    # ---- the meat --------------------------------------------------------------------------------
    def new_batch(self) -> None:
        self.BATCH += 1
        lay = MEAT_LAYOUTS.get(max(1, min(4, self.meat_count)), MEAT_LAYOUTS[3])
        self.MEAT = [{"x": x, "kind": k, "w": w, "done": self.rand(0.05), "gone": 0} for x, k, w in lay]
        self.MEAT_STATE = "cooking"

    def batch_text(self) -> str:
        wors = sum(1 for m in self.MEAT if m["kind"] == "wors")
        chops = len(self.MEAT) - wors
        parts = []
        if wors:
            parts.append(f"{wors} wors")
        if chops:
            parts.append(f"{chops} tjop" + ("s" if chops != 1 else ""))
        return ", ".join(parts) or "niks"

    def meat_done(self) -> float | None:
        m = [p for p in self.MEAT if not p["gone"]]
        if not m:
            return None
        return sum(min(1.0, p["done"]) for p in m) / len(m)

    def meat_name(self, kind: str | None) -> str:
        return MEAT_NAME.get(kind or "", "tjop")

    def fire_state(self) -> str:
        return "lekker" if self.HEAT < 0.6 else "warm" if self.HEAT < 0.8 else "roaring"

    # ---- layout ----------------------------------------------------------------------------------
    def layout(self) -> None:
        P = self.P = {}
        self.buf.resize(self.COLS, self.ROWS)
        ROWS, COLS = self.ROWS, self.COLS
        self.AVOID = []
        self.SAYS = []
        self.talk_q = []
        self.RAID = {}
        self.release("raid")
        self.CAN = {}
        T = self.T
        if self.talk_next < T + 1.5:
            self.talk_next = T + 1.5
        P["small"] = COLS < 60 or ROWS < 18
        if P["small"]:
            self.run_hooks("layout", T)
            return
        gd = 2 + (ROWS - 24) // 4
        if gd < 2:
            gd = 2
        if ROWS < 20:
            gd = 1
        base = P["base"] = ROWS - 2 - gd
        top = P["top"] = base - 9
        P["gd"] = gd
        P["full"] = COLS >= 80
        dog = COLS >= 66
        g = 4 if COLS >= 140 else 2 if COLS >= 90 else 0
        gw = 55 + (9 + g if dog else 0) + g + (14 + g if P["full"] else 0)
        x = (COLS - gw) // 2
        if P["full"]:
            P["jan"] = [x, top]
            x += 14 + g
        P["koos"] = [x, top]
        P["braai"] = [x + 15, base - 7]
        if dog:
            P["dog"] = [x + 43 + g, base - 3]
        P["sak"] = [x + 43 + g + (9 + g if dog else 0), top]
        P["moonspr"] = MOON if ROWS >= 26 else MOON_S
        mw, mh = P["moonspr"].w, P["moonspr"].h
        P["moon"] = [COLS - mw - 6, 2 if ROWS >= 30 else 1 if ROWS >= 22 else 0]
        P["cross"] = [int(COLS * 0.12) + 16, 3 if ROWS >= 30 else 1]
        # On a short screen the moon hangs in the rows the speech bubbles use.
        if P["moon"][1] + mh > top - 5:
            hx = [P[w][0] + GUY[w]["head"] for w in ("jan", "koos", "sak") if w in P]
            cx, bw = P["cross"][0], 20
            for mx in range(COLS - mw, -1, -1):
                if mx <= cx + 12 and mx + mw - 1 >= cx - 15:
                    continue
                ok = True
                for h in hx:
                    if not any(0 <= s and s + bw <= COLS - 1 and (s + bw < mx or s - 1 > mx + mw - 1)
                               for s in range(h - bw, h + 2)):
                        ok = False
                        break
                if ok:
                    P["moon"][0] = mx
                    break
        self.AVOID.append([P["moon"][0], P["moon"][1], P["moon"][0] + mw - 1, P["moon"][1] + mh - 1])
        left = P["jan"][0] if "jan" in P else P["koos"][0]
        right = P["sak"][0] + art.SAK_REST.w
        room = COLS - right
        for spr, need in ((TREE, 20), (TREE_S, 14)):
            tw, th = spr.w, spr.h
            if not (left >= tw + 3 and base >= need):
                continue
            P["tree"] = [spr, left - tw - 2, base - th + 1]
            self.AVOID.append([P["tree"][1], P["tree"][2], P["tree"][1] + tw - 1, base])
            break
        ww, bw = TOWER.w, BAKKIE.w
        if room >= ww + bw + 4:
            x0 = right + 2 + (room - ww - bw - 4) // 2
            P["tower"] = [x0, base - 7]
            P["bakkie"] = [x0 + ww + 1, base - 7]
        elif room >= bw + 5:
            P["bakkie"] = [right + (room - bw) // 2, base - 7]
        elif room >= ww + 6:
            P["tower"] = [right + (room - ww) // 2, base - 7]
        if "tower" in P:
            self.AVOID.append([P["tower"][0], base - 7, P["tower"][0] + ww - 1, base])
        if "bakkie" in P:
            self.AVOID.append([P["bakkie"][0], base - 7, P["bakkie"][0] + bw - 1, base])
        # A top(1) table on tall screens, low in the ground (rows base+2 .. ROWS-2, so the grass row under the feet
        # stays clear, as in lekker): root first, then every guest (CT or VM) of the node, then the okes as space allows; from
        # 180 columns two tables side by side, so the node's guests all fit.
        if ROWS >= 40:
            okes = sum(1 for w in ("koos", "sak", "jan", "dog") if w in P)
            root = gd >= 7
            total = (1 if root else 0) + self.guest_rows_count() + okes
            tw1 = TOP_W
            ncols = 2 if COLS >= 2 * tw1 + 4 + 16 else 1
            per = -(-total // ncols)
            n = max(2, min(gd - 1, per + 1))
            tw = ncols * tw1 + 2 * (ncols - 1)
            P["table"] = [ROWS - 1 - n, n, root, ncols, (COLS - tw) // 2, tw]
        # ground texture: grass along the top, stones and tufts further down;
        # sparser on very big screens, to keep the frames small
        cells = COLS * ROWS
        thin = 0.4 if cells > 10000 else 0.6 if cells > 6000 else 1
        G: list[tuple[int, int, str, str]] = []
        rnd = self.rng.random
        for y in range(base + 1, ROWS - 1):
            d = y - base
            for gx in range(COLS):
                r = rnd()
                if d == 1:
                    if r < 0.3:
                        G.append((gx, y, ('"', ",", "'", '"', ",")[int(rnd() * 5)], "g" if rnd() < 0.7 else "y"))
                elif r < 0.004 and gx < COLS - 4:
                    G.append((gx, y, "\\|/", "g"))
                elif r < 0.06 * thin:
                    G.append((gx, y, (".", ",", ".", ".", "`", ",", "o")[int(rnd() * 7)], "g" if rnd() < 0.4 else "y"))
        self.GROUND = G
        # stars: a sprinkle over the sky, but not on the moon; plus the Milky Way
        self.STARS = []
        self.DUST = []
        cxs, cys = P["cross"]
        for sx in range(COLS):
            cy = (top - 2) * (1 - sx / COLS) - 1
            for sy in range(0, top - 1):
                d = abs(sy - cy) / (1.5 + top / 8)
                if abs(sx - cxs + 1) < 17 and cys - 1 <= sy <= cys + 7:
                    continue
                if rnd() < 0.16 * thin * math.exp(-d * d):
                    self.DUST.append((sx, sy, ":" if rnd() < 0.15 else "."))
        n = int(COLS * (top - 1) / 30)
        if n > 130:
            n = 130
        for _ in range(n):
            sx, sy = int(rnd() * COLS), int(rnd() * (top - 1))
            if P["moon"][0] - 2 <= sx <= P["moon"][0] + mw + 1 and sy <= P["moon"][1] + mh:
                continue
            if abs(sx - cxs) < 16 and cys - 1 <= sy <= cys + 7:
                continue
            self.STARS.append([sx, sy, rnd() * 6.3, 0.3 + rnd() * 1.5])
        self.SMOKE = []
        self.SPARKS = []
        self.run_hooks("layout", T)

    def guest_rows_count(self) -> int:
        """How many guest rows the node wants in the top(1) table (overridden by the node extra)."""
        return 0

    # ---- drawing: the sky, the scenery, the ground, the status line ---------------------------------
    def draw_sky(self, t: float) -> None:
        b = self.buf
        plot = b.plot
        if self.SKY["dust"]:
            for x, y, c in self.DUST:
                plot(x, y, c, "b")
        if self.SKY["stars"]:
            for x, y, ph, sp in self.STARS:
                v = math.sin(t * sp + ph)
                if v > 0.95:
                    plot(x, y, "*", "W")
                elif v > 0.3:
                    plot(x, y, ".", "W")
                elif v > -0.7:
                    plot(x, y, ".", "w")
                else:
                    plot(x, y, ".", "b")
        cx, cy = self.P["cross"]
        if self.SKY["cross"]:
            for sx, sy, ch in CROSS:
                tw = math.sin(t * 1.3 + sx) > 0.97
                plot(cx + sx, cy + sy, "+" if tw else ch, "W")
        if self.SKY["moon"]:
            b.draw(self.P["moonspr"], *self.P["moon"])
        if self.SHOOT:
            x, y = self.SHOOT[0], self.SHOOT[1]
            for k in range(12):
                plot(int(x + k), int(y - k * 0.1), "*" if k == 0 else "-" if k < 6 else ".",
                     "W" if k < 3 else "w" if k < 8 else "b")

    def draw_scenery(self) -> None:
        b, P = self.buf, self.P
        if "tree" in P:
            b.draw(P["tree"][0], P["tree"][1], P["tree"][2])
        if "bakkie" in P:
            b.draw(BAKKIE, *P["bakkie"])
        if "tower" in P:
            x, y = P["tower"]
            b.draw(TOWER, x, y)
            name = self.HOST
            if len(name) > 10:
                m = re.match(r"^(.{3,10})-", name)
                name = m.group(1) if m else name[:10]
            room = 10 if len(name) > 8 else 8
            if room == 10:
                b.put(x + 1, y + 1, " " * 10, "w")
            b.put(x + 6 - room // 2 + (room - len(name)) // 2, y + 1, name, "W")
            if self.POWER:
                b.plot(x + 4, y + 2, "o", "Y" if self.rand() < 0.12 + self.CPU else "y")
            else:
                b.plot(x + 2, y + 2, "o", "b")
                b.plot(x + 4, y + 2, "o", "b")

    def draw_ground(self) -> None:
        b, P = self.buf, self.P
        base = P["base"]
        gx = P["braai"][0] + 13
        b.put(0, base, "_" * self.COLS, "y")
        rnd = self.rng.random
        heat = self.HEAT
        put = b.put
        for x, y, txt, at in self.GROUND:
            glow = abs(x - gx) < 15 - 3 * (y - base) + 5 * heat + rnd() * 2
            put(x, y, txt, ("R" if rnd() < 0.3 else "r") if glow else at)

    def draw_status(self, t: float) -> None:
        b = self.buf
        y = self.ROWS - 1
        f: list[list] = [[0, self.HOST]]
        if self.LOAD != "":
            f.append([5, f"load {self.LOAD}"])
        if self.UPTIME != "":
            f.append([6, f"up {self.UPTIME}"])
        if self.have_cpu:
            f.append([4, "cpu %d%%" % int(self.CPU * 100 + 0.5)])
        f.append([2, "vuur " + self.fire_state()])
        md = self.meat_done()
        if self.MEAT_STATE == "cooking" and md is not None:
            f.append([3, "vleis %d%%" % int(md * 100)])
        elif self.MEAT_STATE == "served":
            f.append([3, "vleis bedien"])
        else:
            f.append([3, "vleis gaar"])
        for fld in self.run_hooks("status", t):
            f.append(list(fld))
        if self.LOG:
            f.append([1 if self.LOG_T is not None and t - self.LOG_T < 5 else 7, self.LOG[-1], 1])
        q = "q om te loop "
        room = self.COLS - 1 - len(q) - 2
        while True:
            ln = 1 + 3 * (len(f) - 1)
            ln += sum(len(x[1]) + (2 if len(x) > 2 else 0) for x in f)
            if ln <= room or len(f) <= 2:
                break
            drop = max(range(len(f)), key=lambda i: f[i][0])
            f.pop(drop)
        x = 1
        for fl in f:
            txt = fl[1]
            if len(fl) > 2:
                mx = room - x - 2
                if mx < 0:
                    mx = 0
                if len(txt) > mx:
                    txt = re.sub(r"^\[[^\]]*\] ", "", txt)
                if len(txt) > mx:
                    if mx < 12:
                        break
                    cut = txt[:mx - 3]
                    if txt[len(cut):len(cut) + 1] != " ":
                        cut = re.sub(r"\s*\S*\Z", "", cut)
                    cut = re.sub(r"[\s(\[,:;-]+\Z", "", cut)
                    if len(cut) < 6:
                        break
                    txt = cut + "..."
                m = re.match(r"^(\[[^\]]*\])?(.*)$", txt)
                stamp = m.group(1) or ""
                msg = m.group(2)
                b.put(x, y, stamp, "g")
                b.put(x + len(stamp), y, msg, "w")
                if int(t * 2) % 2 == 0:
                    b.put(x + len(txt) + 1, y, " ", "v")
                x += len(txt) + 2
            else:
                if x + len(txt) > room:
                    break
                b.put(x, y, txt, "c")
                x += len(txt)
            x += 3
        b.put(self.COLS - 1 - len(q), y, q, "c")

    # ---- the braai: coals, flames, meat, smoke, sparks ----------------------------------------------
    def draw_braai(self, t: float) -> None:
        b = self.buf
        bx, by = self.P["braai"]
        b.draw(BRAAI, bx, by)
        rnd = self.rng.random
        heat = self.HEAT
        plot = b.plot
        for i in range(22):
            r = rnd()
            ph = self.COAL_PH[i]
            c = COAL[int(ph[0] + t * ph[1]) % len(COAL)]
            plot(bx + 3 + i, by + 4, c,
                 "h" if r < 0.25 * (heat - 0.55) else "Y" if r < 0.15 + 0.3 * heat else "R" if r < 0.8 else "r")
        avg = 1.5 + 2.0 * heat
        for i in range(22):
            h = avg + 1.0 * math.sin(t * 6.1 + i * 1.1) + 0.6 * math.sin(t * 9.7 - i * 2.3) + rnd() - 0.5
            if h > 5:
                h = 5
            for k in range(int(h)):
                f = (k + 0.5) / h
                ch = ("^", "(", ")", "^", "/", "\\") if k == 0 else ("(", ")", "(", ")", "^", "'") if f < 0.8 \
                    else ("'", ".", "`", ",", ")", "(")
                at = "Y" if f < 0.35 else ("Y" if rnd() < 0.5 else "R") if f < 0.6 else "R" if f < 0.85 else "r"
                plot(bx + 3 + i, by + 2 - k, ch[int(rnd() * len(ch))], at)
        flying = self.koos_flying(t)
        for i, m in enumerate(self.MEAT):
            if m["gone"] or (i == 0 and flying):
                continue
            a = "(@@@@@@@)" if m["kind"] == "wors" else "(##)" if (i == 0 and self.CHOP) else "(==)"
            b.put(bx + m["x"], by + 2, a, meat_col(m["done"]))
            if m["kind"] == "wors" and rnd() < 0.3:
                plot(bx + m["x"] + 1 + int(rnd() * 7), by + 2, "@", "R")

    def koos_flying(self, t: float) -> bool:
        k = self.ST.get("koos")
        return bool(k) and k["act_to"] > t and not k.get("salute")

    def draw_flying_chop(self, t: float) -> None:
        k = self.ST.get("koos")
        if not (k and k["act_to"] > t and not k.get("salute") and self.MEAT and not self.MEAT[0]["gone"]):
            return
        f = 1 - (k["act_to"] - t) / GUY["koos"]["act_len"]
        bx, by = self.P["braai"]
        h = int(3.6 * math.sin(PI * f) + 0.5)
        spin = ("(==)", " || ", "(##)", " || ")
        s, c = spin[int(f * 6) % 4], meat_col(self.MEAT[0]["done"])
        x = bx + (6 if h >= 2 else 5)
        for i, ch in enumerate(s):
            if ch != " ":
                self.buf.plot(x + i, by + 2 - h, ch, c)

    def update_smoke(self, t: float, dt: float) -> None:
        bx, by = self.P["braai"]
        rnd = self.rng.random
        self.WIND = 1.1 * math.sin(t / 17) + 0.5 * math.sin(t / 5.3) + 0.5 + self.WIND_ADD
        rate = 1.2 + 3.5 * self.HEAT
        if rnd() < rate * dt:
            self.SMOKE.append([bx + 5 + rnd() * 16, by + 1, -(0.9 + rnd() * 0.8), 0, 5 + rnd() * 4])
        W = self.WIND
        for p in self.SMOKE:
            p[3] += dt
            p[0] += (W * (0.3 + p[3] / 2.5) + (rnd() - 0.5)) * dt
            p[1] += p[2] * dt
        self.SMOKE = [p for p in self.SMOKE if p[3] < p[4] and p[1] >= 0 and -4 < p[0] < self.COLS]
        if rnd() < self.HEAT * self.HEAT * 0.5:
            self.SPARKS.append([bx + 5 + rnd() * 18, by + 1, (rnd() - 0.5) * 3, -(4 + rnd() * 4), 0])
        for s in self.SPARKS:
            s[4] += dt
            s[0] += (s[2] + W) * dt
            s[1] += s[3] * dt
        self.SPARKS = [s for s in self.SPARKS if s[4] < 1.1]
        if self.SHOOT:
            self.SHOOT[0] -= 60 * dt
            self.SHOOT[1] += 6 * dt
            self.SHOOT[2] -= dt
            if self.SHOOT[2] < 0:
                self.SHOOT = None
        elif t > self.next_shoot and self.SKY["shoot"]:
            self.SHOOT = [self.COLS * (0.4 + rnd() * 0.6), rnd() * (self.P["top"] / 3), 0.5 + rnd() * 0.5]
            self.next_shoot = t + 20 + rnd() * 40

    def draw_smoke(self) -> None:
        plot = self.buf.plot
        for p in self.SMOKE:
            puff = PUFF[int(len(PUFF) * p[3] / p[4])]
            x = int(p[0] - len(puff) / 2)
            yy = int(p[1])
            for i, c in enumerate(puff):
                if c != " ":
                    plot(x + i, yy, c, "w")

    def draw_sparks(self) -> None:
        plot = self.buf.plot
        for s in self.SPARKS:
            plot(int(s[0]), int(s[1]), "*" if s[4] < 0.5 else ".", "Y" if s[4] < 0.6 else "r")

    # ---- people --------------------------------------------------------------------------------------
    def draw_guy(self, who: str, t: float) -> None:
        pos = self.P.get(who)
        s = self.ST.get(who)
        if not pos or not s or s.get("hide"):
            return
        x, y = pos[0] + s.get("dx", 0), pos[1] + s.get("dy", 0)
        g = self.GUY[who]
        posed = bool(s.get("pose")) and s.get("pose_to", 0) > t
        acting = not posed and s["act_to"] > t
        sipping = acting and g.get("sip") and not s.get("throw")
        self.buf.draw(s["pose"] if posed else g["act"] if acting else g["rest"], x, y)
        if posed and s.get("noface"):
            return
        er, ec, E = g["eyes"]
        if s["face_to"] > t:
            e = E.get(s["face"], E["open"])
        elif s["blink_to"] > t or sipping or s.get("asleep"):
            e = E["shut"]
        else:
            e = E["left"] if s["look"] < 0 else E["right"] if s["look"] > 0 else E["open"]
        self.buf.put(x + ec, y + er, e, ".")
        if s["talk_to"] > t and not sipping:
            mr, mc, shut, open_ = g["mouth"]
            self.buf.put(x + mc, y + mr, open_ if int(t * 7) % 3 else shut, g["mcol"])

    def draw_zzz(self, t: float) -> None:
        if not ("jan" in self.P and self.ST.get("jan") and self.ST["jan"].get("asleep")):
            return
        x, y = self.P["jan"]
        for k in range(3):
            ph = t * 0.8 + k
            ph -= 3 * int(ph / 3)
            self.buf.put(x + 10 + int(ph * 1.5), y + 1 - int(ph), "z" if ph < 1 else "Z", "C" if ph < 2 else "c")

    def new_state(self, t: float) -> dict:
        return {"blink_at": t + 1 + self.rand(4), "blink_to": 0, "act_at": t + 3 + self.rand(8), "act_to": 0,
                "talk_to": 0, "look": 0, "face_to": 0, "face": "open", "asleep": 0, "doze_at": t + 40 + self.rand(30)}

    def update_people(self, t: float) -> None:
        for who in [w for w in self.CAST if w in self.GUY]:
            s = self.ST.get(who)
            if s is None:
                s = self.ST[who] = self.new_state(t)
            if t > s["blink_at"]:
                s["blink_to"] = t + 0.18
                s["blink_at"] = t + 2.5 + self.rand(5)
            if t > s["act_at"]:
                if any(b["who"] == who for b in self.SAYS):
                    s["act_at"] = t + 1.5
                else:
                    if not s.get("asleep"):
                        self.start_act(who, t, quiet=True)
                    s["act_at"] = t + 7 + self.rand(9)
            s["look"] = 0
            sp = next((b for b in self.SAYS if b["who"] != who), None)
            if sp and who in self.P:
                hd = self.head_of(sp["who"])
                mx = self.P[who][0] + self.GUY[who]["head"]
                if hd:
                    sx = hd[0]
                    s["look"] = -1 if sx < mx - 3 else 1 if sx > mx + 3 else 0
        j = self.ST.get("jan")
        if "jan" not in self.P or not j:
            return
        if (not j["asleep"] and t > j["doze_at"] and not self.SAYS and not self.RAID and not self.CAN and self.calm(t)
                and not any("jan" in who for who, _ in self.talk_q)):
            j["asleep"] = 1
            j["wake_at"] = t + 12 + self.rand(10)
            self.logmsg("jannie: gaan oor na kragbesparing (power-save mode)")
        if j["asleep"] and t > j.get("wake_at", 0):
            self.wake("jan", t)

    def wake(self, who: str, t: float, why: str | None = None) -> None:
        s = self.ST.get(who)
        if not s or not s.get("asleep"):
            return
        s["asleep"] = 0
        s["doze_at"] = t + 45 + self.rand(40)
        s["act_at"] = t + 2 + self.rand(3)
        if who in self.P:
            self.logmsg(f"{self.NAME[who]}: wakker uit suspend" + (f" ({why})" if why else ""))

    def set_face(self, who: str, face: str, until: float) -> None:
        s = self.ST.get(who)
        if s:
            s["face"], s["face_to"] = face, until

    # Somebody does his thing: Koos turns a chop (or, with salute, just raises
    # the tongs), Sakkie and Jannie sip their dops (or, with throw, Jannie throws one).
    def start_act(self, who: str, t: float, quiet: bool = False, length: float | None = None,
                  throw: bool = False, salute: bool = False) -> None:
        s = self.ST.get(who)
        if not s or s["act_to"] > t or who not in self.P or s.get("asleep"):
            return
        s["act_to"] = t + (length or self.GUY[who]["act_len"])
        s["throw"] = 1 if throw else 0
        s["salute"] = 1 if (salute or (who == "koos" and (not self.MEAT or self.MEAT[0]["gone"]))) else 0
        if who == "koos":
            if s["salute"]:
                return
            self.CHOP = not self.CHOP
            self.MEAT[0]["done"] += 0.02
            self.FLIPS += 1
            self.logmsg(f"grid0: koos het die tjop omgedraai (draai #{self.FLIPS})", quiet)
        elif not throw:
            self.SIPS[who] = self.SIPS.get(who, 0) + 1
            if self.SIPS[who] % 3 == 0:
                self.DOPS[who] = self.DOPS.get(who, 0) + 1
                self.logmsg(f"dop: {self.NAME[who]} het dop #{self.DOPS[who]} klaargemaak")

    # ---- the brakkie ---------------------------------------------------------------------------------
    def raid_start(self, t: float, auto: bool = False) -> None:
        if "dog" not in self.P or self.RAID or self.DOG_AWAY:
            return
        if (self.MEAT_STATE != "cooking" or len(self.MEAT) < 2 or self.MEAT[-1]["gone"] or self.wall_up(t)
                or not self.claim("raid", t, 13)):
            if auto:
                self.next_raid = t + 20
            else:
                self.say_now(t, ("D", "Woef!"))
            return
        self.RAID = {"t0": t, "step": 0}
        self.logmsg("wagter[104]: toestand D -> R, op pad na grid0")

    def update_raid(self, t: float) -> None:
        if not self.RAID and t > self.next_raid and "dog" in self.P and not self.SAYS and self.calm(t):
            self.raid_start(t, True)
        if not self.RAID:
            return
        s = t - self.RAID["t0"]
        R = self.RAID
        if R["step"] == 0 and s >= 1.5:
            R["step"] = 1
            what = "chop"
            if len(self.MEAT) >= 2:
                self.MEAT[-1]["gone"] = 1
                what = self.MEAT[-1]["kind"]
            what = self.meat_name(what)
            self.logmsg(f"grid0: 1 {what} verloor aan wagter (pid 104)")
            self.set_face("koos", "wide", t + 3)
            self.wake("jan", t, f"{what} gesteel")
            self.say_now(t, ("K", "HAAI! Los dit, hond!"), ("S|J", "Daai hond eet beter as ons!"),
                         ("K", f"Dit was MY {what}, Wagter."))
        if R["step"] == 1 and s >= 2.4:
            R["step"] = 2
            for w in ("sak", "jan"):
                self.set_face(w, "laugh", t + 3.2)
        if R["step"] == 2 and s >= 10:
            R["step"] = 3
            self.logmsg("wagter: terug op sy plek, lyk onskuldig")
        if s >= 13:
            self.RAID = {}
            self.release("raid")
            self.next_raid = t + 180 + self.rand(120)

    def dog_now(self, t: float) -> tuple:
        """Where the dog is now: (sprite, x, y, carrying-at-x or None, in front?, leaping at the grid?)."""
        if "dog" not in self.P or self.DOG_AWAY:
            return ()
        dx, dy = self.P["dog"]
        k = self.ST.get("koos")
        fast = (k and k["act_to"] > t) or any(b["who"] == "dog" for b in self.SAYS)
        if not self.RAID:
            return (DOG[int(t * (8 if fast else 3)) % 2], dx, dy, None, 0, 0)
        s = t - self.RAID["t0"]
        if s < 1:
            return (DOG[0], dx - int(2 * s + 0.5), dy, None, 0, 0)
        if s < 2:
            f = s - 1
            x = dx - 2 - int(3 * f + 0.5)
            return (DOG[0], x, dy - int(3.4 * math.sin(PI * f) + 0.5), x - 4 if f > 0.5 else None, 0, 1)
        if s < 4.2:
            x0 = dx - 5
            x = int(x0 + (self.COLS + 2 - x0) * (s - 2) / 2.2)
            return (DOG_RUN[int(s * 8) % 2], x, dy, x + 11, 1, 0)
        if s < 7:
            return ()
        if s < 10:
            x = int(self.COLS + 1 + (dx - self.COLS - 1) * (s - 7) / 3)
            return (DOG_TROT[int(s * 6) % 2], x, dy, None, 1, 0)
        return (DOG[int(t * 8) % 2], dx, dy, None, 0, 0)

    def draw_carry(self, x: int, y: int) -> None:
        self.buf.put(x, y, "(==)", meat_col(self.MEAT[-1]["done"] if len(self.MEAT) >= 2 else 1))

    def draw_dog(self, at: tuple) -> None:
        if not at:
            return
        spr, x, y, carry = at[0], at[1], at[2], at[3]
        self.buf.draw(spr, x, y)
        if carry is not None:
            self.draw_carry(carry, y + 2)

    # ---- a dop thrown from Jannie to Sakkie, over the fire ---------------------------------------------
    def start_toss(self, t: float) -> None:
        if not ("jan" in self.P and "sak" in self.P and not self.CAN):
            return
        self.wake("jan", t)
        self.start_act("jan", t, length=0.6, throw=True)
        self.CAN = {"t0": t + 0.3, "dur": 1.3}

    def update_can(self, t: float) -> None:
        if not self.CAN or t < self.CAN["t0"] + self.CAN["dur"]:
            return
        self.CAN = {}
        self.DOPS["sak"] = self.DOPS.get("sak", 0) + 1
        self.logmsg(f"dop: jannie -> sakkie, gevang (dop #{self.DOPS['sak']})")
        if self.ST.get("sak"):
            self.ST["sak"]["act_at"] = t + 0.8

    def draw_can(self, t: float) -> None:
        if not (self.CAN and t >= self.CAN["t0"] and "jan" in self.P and "sak" in self.P):
            return
        f = (t - self.CAN["t0"]) / self.CAN["dur"]
        if f > 1:
            return
        x0, y0 = self.P["jan"][0] + 9, self.P["jan"][1] + 2
        x1, y1 = self.P["sak"][0] + 1, self.P["sak"][1] + 6
        h = (y0 + y1) / 2 - (self.P["top"] - 3)
        x = x0 + (x1 - x0) * f
        y = y0 + (y1 - y0) * f - h * math.sin(PI * f)
        self.buf.put(int(x + 0.5), int(y + 0.5), "[#]", "Y")

    # ---- meat, heat and broadcasts -----------------------------------------------------------------------
    def wall(self, msg: str) -> None:
        msg = ascii7(msg)
        if msg not in self.WALL_Q:
            self.WALL_Q.append(msg)

    def start_wall(self, t: float) -> None:
        lt = time.localtime()
        when = " (%s %s %d %02d:%02d)" % (("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")[lt.tm_wday],
                                           ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
                                            "Dec")[lt.tm_mon - 1], lt.tm_mday, lt.tm_hour, lt.tm_min)
        self.WALL = {"head": f"Broadcast message from {self.USER}@{self.HOST} (pts/0)", "when": when,
                     "msg": self.WALL_Q.pop(0), "until": t + 6}

    def draw_wall(self, t: float) -> None:
        if not self.wall_up(t):
            return
        W = self.WALL
        w = self.COLS - 2
        head = W["head"] + W["when"] + ":"
        if len(head) > w:
            head = W["head"] + ":"
        msg = wrap(W["msg"], w)
        for yy in range(3 + len(msg)):
            self.buf.put(0, yy, " " * self.COLS, ".")
        self.buf.put(1, 0, head[:w], "W")
        for i, line in enumerate(msg):
            self.buf.put(1, 2 + i, line[:w], "Y")

    def update_meat(self, t: float, dt: float) -> None:
        if self.MEAT_STATE == "cooking":
            rate = (0.5 + self.HEAT) / (55 if self.BATCH == 1 else 75)
            for m in self.MEAT:
                if not m["gone"]:
                    m["done"] += dt * rate * (0.85 + 0.3 * self.rand())
            d = self.meat_done()
            if d is None or d >= 1:
                self.MEAT_STATE = "gaar"
                self.SERVE_AT = t + 40
                self.logmsg(f"grid0: batch {self.BATCH} is gaar")
                self.wall("Die vleis is gaar! Bring julle borde, manne.")
                self.PRIO.append([("K", "Vleis is reg! !serve"), ("S+J", "Lekker!")])
        if self.SERVE_AT and t >= self.SERVE_AT:
            self.SERVE_AT = 0
            self.MEAT = []
            self.MEAT_STATE = "served"
            self.NEWBATCH_AT = t + 6
            self.logmsg("grid0: vleis bedien op 3 borde")
        if self.MEAT_STATE == "served" and t >= self.NEWBATCH_AT:
            self.new_batch()
            self.logmsg(f"grid0: batch {self.BATCH} op die rooster ({self.batch_text()})")

    def update_heat(self, t: float, dt: float) -> None:
        want = 1.0 if self.FAN > 0 else 0.45 + 0.55 * self.CPU
        for k in list(self.FIREMOD):
            d, until = self.FIREMOD[k]
            if until > t:
                want += d
            else:
                del self.FIREMOD[k]
        want = 0.05 if want < 0.05 else 1 if want > 1 else want
        if self.FAN > 0:
            self.FAN -= dt
        self.HEAT += (want - self.HEAT) * (1 - math.exp(-dt / 2.5))
        self.HOT_SINCE = (self.HOT_SINCE or t) if self.CPU > 0.85 else 0
        if self.HOT_SINCE and t - self.HOT_SINCE > 3 and t > self.next_hot_wall:
            self.wall("braaitemp kritiek: draai die wors om voor dit houtskool word!")
            self.logmsg("thermal: braai temp %d%%, koos in kennis gestel" % int(self.CPU * 100 + 0.5))
            self.start_act("koos", t)
            self.next_hot_wall = t + 120

    # ---- top(1) for the okes, on tall screens ------------------------------------------------------------
    def proc_state(self, who: str, t: float) -> str:
        if who == "root":
            return "R" if self.CPU > 0.5 else "S"
        if who == "dog":
            return "R" if self.RAID else "D"
        s = self.ST.get(who)
        if not s:
            return "S"
        if s.get("asleep"):
            return "I"
        return "R" if s["act_to"] > t else "S"

    def update_ptime(self, t: float, dt: float) -> None:
        for who in ("root", "koos", "sak", "jan", "dog"):
            self.PTIME[who] = self.PTIME.get(who, 0.0) + dt * (
                0.2 + self.CPU if who == "root" else 1 if self.proc_state(who, t) == "R" else 0.01)

    def top_rows(self, t: float) -> list[tuple[str, str]]:
        """The table rows (text, colour letter) after the okes: the node's guests (node extra)."""
        return []

    def draw_top(self, t: float) -> None:
        if "table" not in self.P:
            return
        ty, n, root, ncols, x0, tw = self.P["table"]
        fmt = TOP_FMT
        header = (fmt % ("PID", "USER", "PR", "NI", "S", "%CPU", "TIME+", "COMMAND"), "v")
        rows: list[tuple[str, str]] = []
        cmd = {
            "root": "braaid --grid=0 --coals",
            "koos": "tang --draai --moenie-prik",
            "sak": "dop --sluk --count=%d" % self.DOPS.get("sak", 0),
            "jan": "koelboks --sit" + (" --zzz" if self.ST.get("jan", {}).get("asleep") else ""),
            "dog": "steel --tjop --vinnig" if self.RAID else "bedel --vir=wors",
        }
        pid = {"root": 1, "koos": 101, "sak": 102, "jan": 103, "dog": 104}
        def oke_row(who: str) -> tuple[str, str]:
            st = self.proc_state(who, t)
            pc = self.CPU * 100 if who == "root" else 3.1 + self.CPU * 20 if st == "R" else 0
            tm = self.PTIME.get(who, 0.0)
            return (fmt % (pid[who], "root" if who == "root" else self.NAME[who], 39 if who == "jan" else 20,
                           19 if who == "jan" else 0, st, "%.1f" % pc,
                           "%d:%05.2f" % (int(tm / 60), tm - 60 * int(tm / 60)), cmd[who]),
                    "W" if st == "R" else "w")

        # root first, then the node's guests, then the okes as space allows
        if root:
            rows.append(oke_row("root"))
        rows.extend(self.top_rows(t))
        for who in ("koos", "sak", "jan", "dog"):
            if who in self.P:
                rows.append(oke_row(who))
        per = n - 1
        rows = rows[: ncols * per]
        w = min(TOP_W, self.COLS - 2)
        for c in range(ncols):
            chunk = rows[c * per:(c + 1) * per]
            if not chunk:
                break
            x = x0 + c * (TOP_W + 2)
            self.buf.put(x, ty, header[0][:w].ljust(w), header[1])
            for i, (txt, col) in enumerate(chunk):
                self.buf.put(x, ty + 1 + i, txt[:w].ljust(w), col)

    # ---- speech bubbles ---------------------------------------------------------------------------------
    def draw_bubble(self, hx: int, hy: int, taken: list, lines: list[str]) -> list[int] | None:
        """cowsay-style: a top rule, < text > (or / | \\ for several lines), a bottom rule and a tail down to
        the speaker's head at (hx, hy).  It keeps clear of the moon, the scenery and other bubbles."""
        b = self.buf
        COLS = self.COLS
        w = max(len(line) for line in lines)
        bw, bh = w + 4, len(lines) + 2
        spot = None
        for lift in (0, 1, 2):
            by = hy - 1 - lift - bh
            if by < 0:
                break
            b0 = hx - bw // 2
            ds = [0]
            for d in range(1, bw // 2 + 2):
                ds.extend((-d, d))
            for d in ds:
                bx = b0 + d
                if bx < 0 or bx + bw > COLS - 1 or hx < bx - 1 or hx > bx + bw:
                    continue
                if any(bx - 1 <= tb[2] and bx + bw >= tb[0] and by <= tb[3] and by + bh - 1 >= tb[1] for tb in taken):
                    continue
                spot = [bx, by, lift]
                break
            if spot:
                break
        if not spot:
            by = hy - 1 - bh
            if by < 0:
                return None
            bx = hx - bw // 2
            if bx + bw > COLS - 1:
                bx = COLS - 1 - bw
            if bx < 0:
                bx = 0
            spot = [bx, by, 0]
        bx, by, lift = spot
        b.put(bx, by, " " + "_" * (w + 2) + " ", "w")
        for i, line in enumerate(lines):
            if len(lines) == 1:
                l, r = "<", ">"
            elif i == 0:
                l, r = "/", "\\"
            elif i == len(lines) - 1:
                l, r = "\\", "/"
            else:
                l, r = "|", "|"
            b.put(bx, by + 1 + i, l, "w")
            b.put(bx + 1, by + 1 + i, " " + line + " " * (w - len(line)) + " ", "W")
            b.put(bx + bw - 1, by + 1 + i, r, "w")
        b.put(bx, by + 1 + len(lines), " " + "-" * (w + 2) + " ", "w")
        mid = bx + bw / 2
        tail = "\\" if mid < hx - 1 else "/" if mid > hx + 1 else "|"
        for k in range(lift + 1):
            b.plot(hx, hy - 1 - k, "|" if k else tail, "w")
        return [bx, by, bx + bw - 1, by + bh - 1 + lift]

    def head_of(self, who: str) -> tuple:
        if who == "dog":
            return (self.DOGAT[1] + 2, self.DOGAT[2] + 1) if self.DOGAT else ()
        if who in self.HEAD:
            return self.HEAD[who]()
        if who not in self.P or who not in self.GUY:
            return ()
        s = self.ST.get(who, {})
        if s.get("hide"):
            return ()
        return (self.P[who][0] + self.GUY[who]["head"] + s.get("dx", 0), self.P[who][1] + s.get("dy", 0))

    def fill(self, s: str) -> str | None:
        v = {"up": self.UPTIME, "load": self.LOAD, "cpu": str(int(self.CPU * 100 + 0.5)) if self.have_cpu else ""}
        for k, fn in self.FILL.items():
            if "{" + k + "}" in s:
                v[k] = fn()
        for k, val in v.items():
            if "{" + k + "}" not in s:
                continue
            if val == "":
                return None
            s = s.replace("{" + k + "}", val)
        return s

    def present(self, who: str) -> bool:
        if who == "dog":
            return bool("dog" in self.P and not self.DOG_AWAY and not (self.RAID and self.T - self.RAID["t0"] < 10))
        if who in self.HEAD:
            return bool(self.HEAD[who]())
        return who in self.P and not self.ST.get(who, {}).get("hide")

    def cond_ok(self, c: str) -> bool:
        if c in self.COND:
            return bool(self.COND[c]())
        d = self.meat_done()
        if c == "roaring":
            return self.fire_state() == "roaring"
        if c == "wind_r":
            return self.WIND > 0.6
        if c == "wind_l":
            return self.WIND < -0.25
        if c == "raw":
            return self.MEAT_STATE == "cooking" and d is not None and d < 0.5
        if c == "almost":
            return self.MEAT_STATE == "cooking" and d is not None and 0.55 < d < 0.95
        return True

    def build_exchange(self, ex: list) -> list[tuple[list[str], str]]:
        """An exchange as it can be played now: [(speakers, text)...], or [] if a condition fails, a speaker
        is away or a value is missing.  "S+J" is a chorus (whoever of them is here); "S|J" whichever is here."""
        ex = list(ex)
        if ex and isinstance(ex[0], str):
            if not self.cond_ok(ex[0]):
                return []
            ex = ex[1:]
        lines = []
        for k, text in ex:
            want = [self.WHO[p] for p in re.split(r"[+|]", k) if p in self.WHO]
            who = [w for w in want if self.present(w)]
            if who and "|" in k:
                who = [who[0]]
            text = self.fill(text)
            if not who or text is None:
                return []
            lines.append((who, text))
        return lines

    def say_now(self, t: float, *ex: Any) -> None:
        lines = self.build_exchange(list(ex))
        if not lines:
            return
        self.talk_q = lines
        self.SAYS = []
        self.talk_next = t

    def ex_key(self, ex: list) -> str:
        for item in ex:
            if not isinstance(item, str):
                return item[1]
        return ""

    def fresh(self, ex: list, t: float) -> bool:
        return t - self.said_at.get(self.ex_key(ex), -1e9) >= NO_REPEAT

    def next_line(self, t: float) -> None:
        for _ in range(50):
            if self.talk_q:
                break
            if self.PRIO:
                ex = self.PRIO.pop(0)
                if not self.fresh(ex, t) and not any("!serve" in it[1] for it in ex if isinstance(it, tuple)):
                    continue      # (the ten-minute rule holds for the extras' lines too; serving the meat always plays)
            else:
                if not self.talk_bag:
                    self.talk_bag = list(range(len(self.TALK)))
                    self.rng.shuffle(self.talk_bag)
                if self.CPU > 0.5 and self.rand() < 0.3:
                    ex = self.HOT[self.irand(len(self.HOT))]
                else:
                    ex = self.TALK[self.talk_bag.pop(0)]
                if not self.fresh(ex, t):
                    continue
            self.talk_q = self.build_exchange(ex)
            if self.talk_q:
                self.said_at[self.ex_key(ex)] = t
        if not self.talk_q:
            self.talk_next = t + 5
            return
        who_l, text = self.talk_q.pop(0)
        who = [w for w in who_l if self.present(w)]
        if not who:
            self.talk_q = []
            self.talk_next = t + 1
            return
        do: set[str] = set()
        while True:
            m = MARK_RE.search(text)
            if not m:
                break
            do.add(m.group(1))
            text = text[:m.start()] + text[m.end():]
        if "jan" in who:
            self.wake("jan", t)
        if re.search(r"jannie", text, re.I):
            self.wake("jan", t, "geroep")
        if who[0] == "dog":
            self.wake("jan", t, "woef")
        if "flip" in do:
            self.start_act("koos", t)
        if "toss" in do:
            self.start_toss(t)
        if "serve" in do and self.MEAT_STATE == "gaar":
            self.SERVE_AT = t + 2.5
        if "salute" in do:
            self.wake("jan", t)
            self.start_act("koos", t, salute=True, length=2)
            for w in ("sak", "jan"):
                self.start_act(w, t, length=2)
        elif re.search(r"lekker", text, re.I):
            for w in ("sak", "jan"):
                if w not in who:
                    self.start_act(w, t)
        for name in sorted(do):
            if name in self.MARK:
                self.MARK[name](t, who)
        ln = len(text)
        maxw = 30 if self.COLS >= 100 else 24
        until = t + 1.8 + 0.07 * ln
        self.SAYS = [{"who": w, "lines": wrap(text, maxw), "until": until} for w in who]
        for s in self.ST.values():
            s["talk_to"] = 0
        for w in who:
            if w in self.ST:
                self.ST[w]["talk_to"] = t + 0.6 + 0.05 * ln
        self.talk_next = until + (0.5 if self.talk_q else 3 + self.rand(4))

    def update_talk(self, t: float) -> None:
        self.SAYS = [b for b in self.SAYS if b["until"] > t]
        if self.WALL_Q and not self.SAYS and not self.talk_q and not self.wall_up(t):
            self.start_wall(t)
            if self.talk_next < self.WALL["until"] + 1:
                self.talk_next = self.WALL["until"] + 1
        if self.wall_up(t):
            return
        if self.WALL_Q and not self.talk_q:
            return
        if t >= self.talk_next:
            self.next_line(t)

    def draw_talk(self, t: float) -> None:
        taken = list(self.AVOID)
        for bb in self.SAYS:
            if bb["who"] == "dog":
                if not self.DOGAT:
                    continue
                x, y = self.DOGAT[1], self.DOGAT[2]
                self.buf.put(x + 2, y - 2, bb["lines"][0], "W")
                self.buf.plot(x + 3, y - 1, "'", "w")
                continue
            hd = self.head_of(bb["who"])
            if not hd:
                continue
            box = self.draw_bubble(hd[0], hd[1], taken, bb["lines"])
            if box:
                taken.append(box)

    def draw_small(self) -> None:
        msg = ["Die braai het meer plek nodig:", "maak die venster groter.", "(q om te loop)"]
        y0 = self.ROWS // 2 - 1
        for i, m in enumerate(msg):
            if y0 + i >= self.ROWS - 1 and i:
                continue
            m = m[: self.COLS - 1 if self.COLS > 1 else 1]
            x = (self.COLS - len(m)) // 2
            self.buf.put(max(0, x), y0 + i, m, "c" if i == 2 else "Y")

    # ---- the boot: a dmesg-style log for the first seconds (any key skips it) -------------------------------
    def boot_lines(self) -> list[tuple[float, str, str]]:
        okes = [w for w in ("koos", "sak", "jan") if w in self.P]
        lines: list[tuple[float, str, str]] = [
            (0.00, "W", f"vuurwag {VERSION} op {self.HOST}"),
            (0.10, ".", ""),
            (0.20, "w", f"[    0.000000] braai: boot op {self.HOST} ({self.KERNEL})"),
            (0.45, "w", f"[    0.041337] okes: {len(okes)} gevind (" + ", ".join(self.NAME[w] for w in okes) + ")"
                        + (", 1 hond (wagter)" if "dog" in self.P else "")),
            (0.70, "w", "[    0.098112] grid0: halfdrom, 22 kolomme, 4 pote"),
            (0.95, "w", "[    0.152000] kole: aangesteek .................. ok"),
            (1.20, "w", f"[    0.311000] vleis: {self.batch_text()} (rou)"),
        ]
        if "jan" in self.P:
            lines.append((1.45, "w", "[    0.420000] koelboks0: 24 dops, gemonteer read-only"))
        tt = 1.45
        for i, (c, txt) in enumerate(self.BOOTX):
            tt += 0.25
            lines.append((tt, c, txt if c == "ok" else "[%12.6f] %s" % (0.5 + 0.0731 * i, txt)))
        tt += 0.25
        lines.append((tt, "ok", "Reached target Braai."))
        tt += 0.25
        lines.append((tt, "ok", "Started Braai Daemon."))
        return lines

    def draw_boot(self, t: float) -> None:
        y = 1
        for at, c, txt in self.boot_lines():
            if t < at:
                break
            if c == "ok":
                self.buf.put(1, y, "[", "w")
                self.buf.put(2, y, "  OK  ", "G")
                self.buf.put(8, y, "] " + txt[: self.COLS - 11], "w")
            else:
                self.buf.put(1, y, txt[: self.COLS - 2], c)
            y += 1
        if int(t * 4) % 2 == 0:
            self.buf.put(1, y, " ", "v")

    # ---- the core's keys ------------------------------------------------------------------------------------
    def core_keys(self) -> None:
        def space(t: float) -> None:
            if not self.wall_up(t):
                self.talk_next = t

        def fan(t: float) -> None:
            self.FAN = 4
            self.logmsg(f"kole: aangeblaas deur {self.USER}")

        def dop(t: float) -> None:
            if "jan" in self.P and not self.CAN:
                self.say_now(t, ("S", "Jannie, nog 'n dop?"), ("J", "Vang! !toss"), ("S", "Dankie, ou maat!"))
            else:
                self.start_act("sak", t)

        def green(t: float) -> None:
            self.GREEN = not self.GREEN
            self.mode = "green" if self.GREEN else "ansi"

        self.key(" ", "volgende lyn gesels / next line of banter", space)
        self.key("f", "blaas die vuur aan / fan the fire", fan)
        self.key("d", "gooi 'n dop oor / pass a dop", dop)
        self.key("b", "Wagter kry idees / the brakkie gets ideas", lambda t: self.raid_start(t))
        self.key("g", "groen fosfor aan/af / green phosphor", green)
        self.key("?", "hierdie hulp / this help", lambda t: setattr(self, "HELP", t + 30))

    def press(self, k: str) -> None:
        """A key, as lekker reads it: q quits, any key skips the boot or closes the help, else the extras
        see it first (keyseq) and then the bound key runs."""
        t = self.T
        if k.lower() == "q":
            self.quit = True
            return
        if t < self.BOOT_END:
            self.BOOT_END = t
            return
        if self.HELP > t:
            self.HELP = 0
            return
        if self.P.get("small"):
            return
        self.KEYHIST.append(k)
        while len(self.KEYHIST) > 12:
            self.KEYHIST.pop(0)
        if any(self.run_hooks("keyseq", t, self.KEYHIST)):
            return
        fn = self.KEY.get(k) or (self.KEY.get(k.lower()) if len(k) == 1 else None)
        if fn:
            fn(t)

    # ---- the help ---------------------------------------------------------------------------------------------
    def draw_help(self, t: float) -> None:
        e = [("q", "loop (Ctrl-C werk ook) / leave")] + self.KEYHELP
        rows = self.ROWS - 6
        COLS = self.COLS
        cols = 1
        cw = 0
        items: list[list[str]] = []
        for attempt in (1, 2):
            cols = attempt
            full = max(7 + len(h) for _, h in e)
            cw = full if cols == 1 else (COLS - 2 - 4 - 3) // 2
            if cw > COLS - 6:
                cw = COLS - 6
            items = [[("space" if k == " " else k)] + [l[: cw - 7] for l in wrap(h, cw - 7)] for k, h in e]
            n = sum(len(it) - 1 for it in items)
            if n <= rows or COLS < 40:
                break
        place = []
        c, r = 0, 0
        cut = 0
        for it in items:
            h = len(it) - 1
            if r + h > rows:
                c += 1
                r = 0
            if c >= cols:
                cut = 1
                break
            place.append((c, r, it))
            r += h
        used = 0
        for pc, pr, it in place:
            used = max(used, pr + len(it) - 1)
        if cut:
            used += 1
        w = cols * cw + 3 * (cols - 1) + 4
        if w > COLS - 2:
            w = COLS - 2
        x0, y0 = (COLS - w) // 2, (self.ROWS - 1 - (used + 4)) // 2
        if y0 < 0:
            y0 = 0
        title = self.help_title
        b = self.buf
        b.put(x0, y0, "." + "-" * (w - 2) + ".", "Y")
        if len(title) < w - 2:
            b.put(x0 + (w - len(title)) // 2, y0, title, "W")
        for i in range(used + 2):
            b.put(x0, y0 + 1 + i, "|" + " " * (w - 2) + "|", "Y")
        b.put(x0, y0 + used + 3, "'" + "-" * (w - 2) + "'", "Y")
        for pc, pr, it in place:
            x = x0 + 2 + pc * (cw + 3)
            b.put(x, y0 + 2 + pr, it[0], "C")
            for i, l in enumerate(it[1:]):
                b.put(x + 7, y0 + 2 + pr + i, l, "w")
        if cut:
            b.put(x0 + 2, y0 + 2 + used - 1, "(meer met 'n groter venster)", "c")

    # ---- the frame ---------------------------------------------------------------------------------------------
    def draw_scene(self, t: float) -> None:
        self.draw_sky(t)
        self.run_hooks("sky", t)
        self.draw_ground()
        self.draw_scenery()
        self.run_hooks("scenery", t)
        self.draw_smoke()
        self.draw_top(t)
        self.run_hooks("back", t)
        self.DOGAT = self.dog_now(t)
        D = self.DOGAT
        leap = bool(D) and D[5]
        if leap:
            self.buf.draw(D[0], D[1], D[2])
        self.draw_braai(t)
        if leap and D[3] is not None and D[2] + 1 < self.P["braai"][1] + 3:
            self.draw_carry(D[3], D[2] + 1)
        self.draw_guy("jan", t)
        if not (leap or (D and D[4])):
            self.draw_dog(D)
        self.draw_guy("sak", t)
        self.draw_guy("koos", t)
        if D and D[4]:
            self.draw_dog(D)
        self.run_hooks("actors", t)
        self.draw_zzz(t)
        self.draw_flying_chop(t)
        self.draw_can(t)
        self.draw_sparks()
        self.run_hooks("front", t)
        self.draw_wall(t)
        self.draw_talk(t)
        self.draw_status(t)
        self.run_hooks("overlay", t)
        if self.HELP > t:
            self.draw_help(t)

    def start(self) -> None:
        """After the extras are in: their boot lines, and the stage."""
        self.BOOTX = [tuple(x) for x in self.run_hooks("boot")]
        self.BOOT_END += 0.25 * len(self.BOOTX)
        self.talk_next = self.BOOT_END + 1.5
        self.AUTO_AT = self.BOOT_END + 40
        self.layout()

    def resize(self, cols: int, rows: int) -> None:
        if (cols, rows) != (self.COLS, self.ROWS) or not self.P:
            self.COLS, self.ROWS = cols, rows
            self.layout()

    def step(self, dt: float) -> None:
        """One frame: the clock, the updates and the drawing into the buffer."""
        if dt < 0:
            dt = 0
        if dt > 0.25:
            dt = 0.25
        self.T += dt
        t = self.T
        self.buf.clear()
        if self.P.get("small"):
            self.draw_small()
        elif t < self.BOOT_END:
            self.draw_boot(t)
        else:
            if not self.lit:
                self.lit = True
                self.logmsg(f"braai: vuur aangesteek op {self.HOST}")
            self.update_heat(t, dt)
            self.update_smoke(t, dt)
            self.update_meat(t, dt)
            self.update_people(t)
            self.update_raid(t)
            self.update_can(t)
            self.update_talk(t)
            self.update_ptime(t, dt)
            self.run_hooks("update", t, dt)
            self.draw_scene(t)

    def skip_boot(self) -> None:
        self.BOOT_END = min(self.BOOT_END, self.T)
