"""PARTYTJIE -- fireworks, a sokkie, a sing-song, rugby on the radio and the special days of the year
(lekker's fragment 20, pt_).

keys:  v   vuurwerk: a salvo of rockets -- peonies, rings, willows, crackle, palms and the odd heart -- and
           the brakkie runs off to hide
       k   sokkie: the radio plays, the okes dance langarm (Jannie gets up off his koelboks, Koos dances with
           the tongs), the brakkie spins
       s   sing: the okes sing a traditional song (Sarie Marais, Daar kom die Alibama, Jan Pierewiet),
           Jannie off-key, the brakkie howls along
       r   rugby: a made-up Springbok test on the radio, the score in the status line, a ball passed over
           the fire, a try, a final whistle
   P, or up up down down left right left right b a (the Konami code), is not in the help: an easter egg
   for the old site.  The boot log leaves one hint.

Special days come by themselves, by the local date: 24 September Erfenisdag (Nasionale Braaidag), 5 November
Guy Fawkes, 24-26 December Kersfees (red hats; the 26th is Tweede Kersdag), 31 December (a countdown at
midnight) and 1 January Nuwejaar; and the farm's own: 16 December Geloftedag, 27 April, 1 May, 16 June,
9 August, 21 March and the Paasnaweek.  To preview one, --date MM-DD[ HH:MM[:SS]] (lekker's LEKKER_DATE).
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable

from . import banter
from .art import DOG_RUN, DOG_TROT, GUY, SAK_REST
from .buf import Sprite, sprite, wrap
from .core import Braai

PI = math.pi
TWO = 6.28318


def easter(year: int) -> tuple[int, int]:
    """Gregorian Easter Sunday (month, day), Meeus/Jones/Butcher."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return month, day


def special_day(lt: time.struct_time) -> str:
    m, d = lt.tm_mon, lt.tm_mday
    if m == 9 and d == 24:
        return "braaidag"
    if m == 11 and d == 5:
        return "guy"
    if m == 12 and d in (24, 25):
        return "kers"
    if m == 12 and d == 26:
        return "tweede"
    if m == 12 and d == 31:
        return "oujaar"
    if m == 1 and d == 1:
        return "nuwejaar"
    if m == 12 and d == 16:
        return "gelofte"
    if m == 4 and d == 27:
        return "vryheid"
    if m == 5 and d == 1:
        return "werkers"
    if m == 6 and d == 16:
        return "jeug"
    if m == 8 and d == 9:
        return "vroue"
    if m == 3 and d == 21:
        return "mense"
    em, ed = easter(lt.tm_year + 1900 if lt.tm_year < 1900 else lt.tm_year)
    es = time.mktime((lt.tm_year, em, ed, 12, 0, 0, 0, 0, -1))
    now = time.mktime((lt.tm_year, m, d, 12, 0, 0, 0, 0, -1))
    if -2 * 86400 - 3600 <= now - es <= 86400 + 3600:      # Goeie Vrydag .. Paasmaandag
        return "paas"
    return ""


# ---- fireworks -------------------------------------------------------------------------------------------------------
PAL = {"gold": "WYRr", "red": "WRRr", "green": "WGGg", "blue": "WCBb", "cyan": "WCCc", "pink": "WMMm",
       "white": "WWww", "bok": "WYGg"}
COLOURS = ["gold", "gold", "red", "green", "blue", "cyan", "pink", "white"]
SHAPES = ["peony", "peony", "ring", "willow", "crackle", "palm", "double", "heart"]
BANG = ["BOEM!", "KRAK!", "KABOEM!", "POEF!", "PAF!", "BOEM!"]

# ---- letters of fire ----------------------------------------------------------------------------------------------------
_BIG = {
    "b": "#...|###.|#..#|#..#|###.|....", "r": "....|#.##|##..|#...|#...|....",
    "a": "....|.###|#..#|#..#|.###|....", "p": "....|###.|#..#|#..#|###.|#...",
    "e": "....|.##.|####|#...|.###|....", "k": "#...|#.#.|##..|#.#.|#..#|....",
    "c": "....|.###|#...|#...|.###|....", "o": "....|.##.|#..#|#..#|.##.|....",
    "z": "....|####|..#.|.#..|####|....",
    "0": ".##.|#..#|#..#|#..#|.##.|....", "1": ".#.|##.|.#.|.#.|###|...",
    "2": "###.|...#|.##.|#...|####|....", "3": "###.|...#|.##.|...#|###.|....",
    "4": "#..#|#..#|####|...#|...#|....", "5": "####|#...|###.|...#|###.|....",
    "6": ".##.|#...|###.|#..#|.##.|....", "7": "####|...#|..#.|.#..|.#..|....",
    "8": ".##.|#..#|.##.|#..#|.##.|....", "9": ".##.|#..#|.###|...#|.##.|....",
}
_SLIM = {
    "b": "#..|##.|#.#|#.#|##.|...", "r": "...|#.#|##.|#..|#..|...",
    "a": "...|.##|#.#|#.#|.##|...", "p": "...|##.|#.#|#.#|##.|#..",
    "e": "...|.#.|###|#..|.##|...", "k": "#..|#.#|##.|#.#|#.#|...",
    "c": "...|.##|#..|#..|.##|...", "o": "...|.#.|#.#|#.#|.#.|...",
    "z": "...|###|..#|.#.|###|...",
}
_BOTH = {"i": "#|.|#|#|#|.", "l": "#.|#.|#.|#.|.#|..", "-": "..|..|##|..|..|..", ".": ".|.|.|.|#|.", "!": "#|#|#|.|#|."}
FONT: dict[str, dict[str, list[str]]] = {"big": {}, "slim": {}}
for _c, _v in _BOTH.items():
    _BIG[_c] = _v
    _SLIM[_c] = _v
for _c in _BIG:
    _SLIM.setdefault(_c, _BIG[_c])
for _c, _v in _BIG.items():
    FONT["big"][_c] = _v.split("|")
for _c, _v in _SLIM.items():
    FONT["slim"][_c] = _v.split("|")

TAG = "braai-plek.co.za -- die plek vir 'n lekker braai"
EGG_CANDS = [(0, 4, 2, 2, "big"), (1, 4, 2, 2, "big"), (0, 3, 2, 2, "big"), (1, 3, 2, 2, "big"), (0, 2, 1, 2, "big"),
             (1, 2, 1, 2, "big"), (1, 2, 1, 2, "slim"), (1, 2, 1, 1, "big"), (0, 1, 1, 1, "big"), (1, 1, 1, 1, "slim")]
CD_CANDS = [(0, 6, 3, 3, "big"), (0, 5, 3, 2, "big"), (0, 4, 2, 2, "big"), (0, 3, 2, 2, "big"), (0, 2, 1, 1, "big")]
KONAMI = ["up", "up", "down", "down", "left", "right", "left", "right", "b", "a"]

# ---- sokkie poses ----------------------------------------------------------------------------------------------------------
POSE: dict[str, list[Sprite]] = {}
POSE["koos"] = [sprite(r"""
      ____
o???_|____|_????,=<
 \???(o  o)????//
  \???\ww/????//
   \.-'`--'`-.//
    |      |
    |  ..  |
    |______|
    /__/\__\
   (__)??(__)
"""[1:], """
      yyyy
.   yyyyyyyy    ccc
 G             cc
  G           cc
   GGGGGGGGGGGcc
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    yyyyyyyy
   yyyyyyyyyy
"""[1:], "."), sprite(r"""
      ____
    _|____|_
     (o  o)
      \ww/
   .-'`--'`-.
  / |      |\
 o??|  ..  | \__==<
    |______|
    |__|\__\
    (__)?(__)
"""[1:], """
      yyyy
    yyyyyyyy

      yyyy
   GGGGGGGGGG
  G GGGGGGGGG
 .  GGGGGGGG Gccccc
    GGGGGGGG
    yyyyyyyy
    yyyyyyyyy
"""[1:], ".")]
POSE["sak"] = [sprite(r"""
      ___
 [#]=[___]
  \??(o o)
   \??\_/
    \'   '-.
    |     | \
    |     |??)
    |_____|
    /  |  \
   (_/???\_)
"""[1:], """
      BBB
 YYYBBBBBB
  B
   B
    BBBBBBBB
    BBBBBBB B
    BBBBBBB  .
    wwwwwww
    yyyyyyy
   yyyyyyyyy
"""[1:], "."), sprite(r"""
      ___
    =[___]????o
     (o o)???/
      \_/???/
[#]--'   '-'
    |     |
    |     |
    |_____|
    |  |\  \
    (__|?(__)
"""[1:], """
      BBB
    BBBBBB    .
             B
            B
YYYBBBBBBBBB
    BBBBBBB
    BBBBBBB
    wwwwwww
    yyyyyyyy
    yyyyyyyyy
"""[1:], ".")]
POSE["jan"] = [sprite(r"""
     ___
   _(___)_?[#]
    (o o)??//
     \_/??//
  .-'   '-/
 / |     |
 \ |     |
   |_____|
   |  |  |
   (__|__)
"""[1:], """
     ccc
   ccccccc YYY
           RR
          RR
  RRRRRRRRR
 R RRRRRRR
 R RRRRRRR
   yyyyyyy
   yyyyyyy
   yyyyyyy
"""[1:], "."), sprite(r"""
     ___
o??_(___)_
 \??(o o)
  \??\_/
   \'   '-.
   |     | \
   |     |?[#]
   |_____|
   |  |\  \
   (__|?(__)
"""[1:], """
     ccc
.  ccccccc
 R
  R
   RRRRRRRR
   RRRRRRR R
   RRRRRRR YYY
   yyyyyyy
   yyyyyyyy
   yyyyyyyyy
"""[1:], ".")]
COOLER = sprite("_____________\n|    ICE    |\n|___________|", "yyyyyyyyyyyyy\nC    WWW    C\nCCCCCCCCCCCCC", ".")
DOG_SPIN = [sprite(a, m, "Y") for a, m in (
    ("  __??????_\no'')}____//\n `_/      )\n (_(_/-(_/", "\nWWW"),
    ("  __   __\n (  )_(  )\n   ('o')\n  (_| |_)", "\n\n    WWW"),
    ("_??????__\n\\\\____{(''o\n(      \\_'\n \\_)-\\_)_)", "\n        WWW"),
    ("  __   __\n (__)_(__)\n   (   )\n  (_|_|_)~", ""),
)]
SWING = {"koos": [-1, 0, 1, 0], "sak": [1, 0, -1, 0], "jan": [0, -1, 0, 1]}
DOG_FLAT = sprite("o'')}____,/", "WWW", "Y")
DOG_CURL = sprite(" ___ __\n(=''}__/)~", "\nWWWWYYYY", "Y")
SAK_NODOP = sprite(r"""
      ___
    =[___]
     (o o)
      \_/
   .-'   '-.
  / |     | \
  o |     | |
    |_____|
    |  |  |
    (__|__)
"""[1:], """
      BBB
    BBBBBB


   BBBBBBBBB
  B BBBBBBB B
    BBBBBBB B
    BBBBBBB
    wwwwwww
    yyyyyyy
"""[1:], ".")
OPP = [("All Blacks", "die All Blacks"), ("Wallabies", "die Wallabies"), ("Engeland", "Engeland"),
       ("Frankryk", "Frankryk"), ("Ierland", "Ierland"), ("Skotland", "Skotland"), ("Wallis", "Wallis"), ("Pumas", "die Pumas")]
HATS = {
    "kers": {
        "koos": [(-1, 7, ".--._", "RRRRR"), (0, 5, "/:::::::`o", "RRRRRRRRRW"), (1, 4, "(========)", "WWWWWWWWWW")],
        "sak": [(-1, 6, ".-._", "RRRR"), (0, 5, "/:::::`o", "RRRRRRRW"), (1, 4, "(======)", "WWWWWWWW")],
        "jan": [(-1, 5, ".-._", "RRRR"), (0, 4, "/:::::`o", "RRRRRRRW"), (1, 3, "(=======)", "WWWWWWWWW")],
    },
    "party": {
        "koos": [(-2, 7, "*", "Y"), (-1, 6, "/M\\", "MCM")],
        "sak": [(-2, 7, "*", "Y"), (-1, 6, "/M\\", "CMC")],
        "jan": [(-2, 6, "*", "Y"), (-1, 5, "/M\\", "YMY")],
    },
}
TELL = ["nul", "een", "twee", "drie", "vier", "vyf", "ses", "sewe", "agt", "nege", "tien"]
NOTE = [[" |\\", "o| "], ["|~|", "d d"], ["d"], ["J"]]
BOX_W = 11


class Party:
    def __init__(self, b: Braai, clock_offset: float = 0.0) -> None:
        self.b = b
        self.off = clock_offset
        self.Q: list[tuple[float, Callable]] = []
        self.avoid: dict[str, list] = {}
        self.par: list[list] = []
        self.rkt: list[list] = []
        self.bang: list[list] = []
        self.maxp = 300
        self.R = 3.0
        self.egg: dict = {}
        self.wallhold: list[str] = []
        self.egg_want = 0.0
        self.radio: dict = {}
        self.notes: list[list] = []
        self.sok: dict = {}
        self.song = 0
        self.sing: dict = {}
        self.rug: dict = {}
        self.cal: dict = {}
        self.now_lt: time.struct_time | None = None
        self.now_at = -1e9
        self.now_every = 60.0
        self.today = ""
        rng = b.rng
        self.FCH = "".join("#########@@%#####&##"[rng.randrange(20)] for _ in range(2000))
        fco = ""
        while len(fco) < 2100:
            fco += "hhhhhYYYRW"[rng.randrange(10)] * (2 + rng.randrange(4))
        self.FCO = fco
        fcool = ""
        while len(fcool) < 2100:
            fcool += "RRrr"[rng.randrange(4)] * (2 + rng.randrange(3))
        self.FCOOL = fcool
        self.FCHC = "".join("*:.'+:"[rng.randrange(6)] for _ in range(2000))
        self.install()

    # ---- the clock, the calendar ------------------------------------------------------------------------------------------
    def clock(self, t: float | None = None) -> time.struct_time:
        if t is None:
            t = self.b.T
        if self.now_lt is not None and t >= self.now_at and t - self.now_at < self.now_every:
            return self.now_lt
        self.now_lt = time.localtime(time.time() + self.off)
        self.now_at = t
        lt = self.now_lt
        left = 86400 - (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec)
        self.now_every = 0.25 if left < 75 else 1 if left < 125 else 60
        self.today = special_day(lt)
        return lt

    def day(self, t: float | None = None) -> str:
        self.clock(t)
        return self.today

    # ---- little helpers ----------------------------------------------------------------------------------------------------
    def at(self, when: float, fn: Callable) -> None:
        if len(self.Q) < 200:
            self.Q.append((when, fn))

    def run_q(self, t: float) -> None:
        if not self.Q:
            return
        due = [q for q in self.Q if q[0] <= t]
        if not due:
            return
        self.Q = [q for q in self.Q if q[0] > t]
        for _, fn in sorted(due, key=lambda q: q[0]):
            fn(t)

    def okes(self) -> list[str]:
        b = self.b
        return [w for w in ("koos", "sak", "jan") if w in b.P and b.ST.get(w) and not b.ST[w].get("hide")]

    def set_avoid(self, name: str, box: list | None = None) -> None:
        b = self.b
        old = self.avoid.pop(name, None)
        if old is not None:
            b.AVOID = [a for a in b.AVOID if a is not old]
        if not box:
            return
        self.avoid[name] = box
        b.AVOID.append(box)

    def refuse(self, t: float, what: str) -> None:
        b = self.b
        b.logmsg(f"{what}: verhoog is besig, probeer later weer", True)
        if not b.talk_q and not any(s["who"] != "dog" for s in b.SAYS):
            b.say_now(t, b.pick(*banter.PT_NO))

    def say(self, t: float, *ex: Any) -> None:
        """say_now, leaving out the lines of whoever is not here (a song must go on)."""
        b = self.b
        keep = []
        for k, text in ex:
            want = [b.WHO.get(p, "") for p in k.replace("|", "+").split("+")]
            if any(w and b.present(w) for w in want):
                keep.append((k, text))
        if keep:
            b.say_now(t, *keep)

    def faces(self, mood: str, until: float) -> None:
        for w in self.okes():
            self.b.set_face(w, mood, until)

    # ---- vuurwerk ----------------------------------------------------------------------------------------------------------------
    def add(self, *p: Any) -> None:
        if len(self.par) < self.maxp:
            self.par.append(list(p))

    def launch(self, t: float, x: float | None = None, y: float | None = None, shape: str | None = None,
               pal: str | None = None, scale: float = 1.0) -> None:
        b = self.b
        if "top" not in b.P:
            return
        R = self.R * scale
        if x is None:
            x = 4 + b.rand(b.COLS - 8)
        lo = R + 1
        hi = b.P["top"] - 2 - R * 0.8
        if hi < lo:
            hi = lo
        by = y if y is not None else lo + b.rand(hi - lo)
        y0 = b.P["base"] - 2
        up = 0.9 + b.rand(0.5)
        g = 6
        vy = -((y0 - by) + 0.5 * g * up * up) / up
        if len(self.rkt) < 30:
            self.rkt.append([x, float(y0), vy, by, shape or b.pick(*SHAPES), pal or b.pick(*COLOURS), 0.0, scale, g])

    def shell(self, x: float, y: float, shape: str, pal: str, sc: float) -> None:
        b = self.b
        R = self.R * (sc or 1)
        pp = PAL.get(pal, PAL["gold"])
        n = int(12 + 5 * R)
        D = 2.4
        if shape in ("ring", "double"):
            tilt, ph = 0.45 + b.rand(0.55), b.rand(TWO)
            for i in range(n):
                a = ph + TWO * i / n
                self.add(x, y, 2 * math.cos(a) * R * D, math.sin(a) * R * D * tilt, 0, 1.3 + b.rand(0.3), pp, 0, D, 0.8)
            if shape == "double":
                p2 = PAL[b.pick(*[c for c in COLOURS if c != pal])]
                for _ in range(n // 2):
                    a = b.rand(TWO)
                    self.add(x, y, 2 * math.cos(a) * R * D * 0.45, math.sin(a) * R * D * 0.45, 0, 1.2 + b.rand(0.4), p2, 0, D, 0.8)
        elif shape == "heart":
            for i in range(n):
                a = TWO * i / n
                hx = 16 * math.sin(a) ** 3 / 16
                hy = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 16
                self.add(x, y, 2 * hx * R * D, hy * R * D, 0, 1.9 + b.rand(0.2), pp, 0, D, 0.3)
        elif shape == "palm":
            f = 6 + b.irand(3)
            for i in range(f):
                a = -PI * (i + 0.5) / f + (b.rand() - 0.5) * 0.3
                for s in (0.55, 0.7, 0.85, 1.0):
                    self.add(x, y, 2 * math.cos(a) * R * D * s * 1.1, math.sin(a) * R * D * s * 1.1, 0, 1.6 + b.rand(0.3), pp, 1, D, 3.2)
        else:
            kind, life, g, d = (1, 2.3, 3.4, 2.0) if shape == "willow" else (2, 1.7, 1.2, D) if shape == "crackle" else (0, 1.4, 1.2, D)
            if shape == "willow":
                n = int(n * 0.8)
            for _ in range(n):
                a = b.rand(TWO)
                s = R * (math.sqrt(b.rand()) if b.rand() < 0.25 else 0.8 + b.rand(0.25))
                self.add(x, y, 2 * math.cos(a) * s * d, math.sin(a) * s * d, 0, life + b.rand(0.5), pp, kind, d, g)
        if (b.rand() < 0.45 or (sc or 1) > 1.1) and not self.egg_burning():
            self.bang.append([x, y, b.pick(*BANG), b.T + 0.7])

    def update_fw(self, t: float, dt: float) -> None:
        b = self.b
        for r in self.rkt:
            r[6] += dt
            r[2] += r[8] * dt
            r[1] += r[2] * dt
            r[0] += math.sin(r[6] * 13) * 2 * dt
            self.add(r[0] + b.rand(0.6) - 0.3, r[1] + 0.6, b.rand() - 0.5, 1 + b.rand(1.5), 0, 0.35 + b.rand(0.3), PAL["gold"], 3, 1, 3)
            if r[1] <= r[3] or r[2] > -1:
                self.shell(r[0], r[1], r[4], r[5], r[7])
                r[6] = -1
        self.rkt = [r for r in self.rkt if r[6] >= 0]
        W = b.WIND
        for p in self.par:
            p[4] += dt
            k = math.exp(-p[8] * dt)
            p[2] *= k
            p[3] = p[3] * k + p[9] * dt
            p[0] += (p[2] + (0.8 * W if p[7] == 4 else 0)) * dt
            p[1] += p[3] * dt
        self.par = [p for p in self.par if p[4] < p[5] and p[1] < b.ROWS - 1 and -3 < p[0] < b.COLS + 3]
        self.bang = [x for x in self.bang if x[3] > t]
        if len(self.bang) > 12:
            del self.bang[: len(self.bang) - 12]

    def draw_fw(self, t: float) -> None:
        b = self.b
        plot = b.buf.plot
        for p in self.par:
            x, y, f, pal, k = int(p[0] + 0.5), int(p[1] + 0.5), p[4] / p[5], p[6], p[7]
            if k == 3:
                ch, c = ("*", "Y") if f < 0.3 else (":", "R") if f < 0.6 else (".", "r")
            elif k == 4:
                ch, c = ("*", "Y") if f < 0.25 else ("+", "R") if f < 0.55 else (".", "r") if f < 0.8 else ("'", "w")
            else:
                i = 0 if f < 0.1 else 1 if f < 0.5 else 2 if f < 0.78 else 3
                ch, c = ("*" if f < 0.6 else "+" if f < 0.8 else "."), pal[i]
                if k == 2 and f > 0.4:
                    if b.rand() < 0.5:
                        continue
                    ch, c = ("*", "W") if b.rand() < 0.5 else ("+", "Y")
                elif k == 1 and f > 0.15:
                    tx, ty = int(p[0] - p[2] * 0.25 + 0.5), int(p[1] - p[3] * 0.25 + 0.5)
                    if tx != x or ty != y:
                        plot(tx, ty, ":" if p[3] > 1 else ".", pal[3])
                    ch = "*" if f < 0.6 else ","
            plot(x, y, ch, c)
        for r in self.rkt:
            x, y = int(r[0] + 0.5), int(r[1] + 0.5)
            plot(x, y, "^", "W")
            plot(x, y + 1, "|", "Y")
        for x, y, txt, until in self.bang:
            b.buf.put(int(x - len(txt) / 2), int(y), txt, "W" if until - b.T > 0.45 else "Y")

    def salvo(self, t: float, n: int, span: float | None = None, nofaces: bool = False, nodog: bool = False,
              rocket: dict | None = None) -> float:
        b = self.b
        span = span or (1 + 0.45 * n)
        rk = rocket or {}
        for i in range(n):
            when = t + 0.15 + span * i / n + b.rand(0.2)
            self.at(when, lambda t2, rk=rk: self.launch(t2, **rk))
        end = t + span + 2.5
        if not nofaces:
            self.faces("pt_up", end)
        if not nodog:
            self.dog_hide(t, end + 2)
        return end

    def key_v(self, t: float) -> None:
        b = self.b
        if len(self.rkt) > 10:
            b.logmsg("vuurwerk: wag, die lug is vol", True)
            return
        n = 4 + b.irand(3)
        self.salvo(t, n)
        b.logmsg(f"vuurwerk: {n} vuurpyle gelanseer")
        ex = b.pick(*banter.PT_OOH)
        self.at(t + 1.6, lambda t2: self.say(t2, *ex) if b.calm(t2) and not b.talk_q else None)

    # ---- the brakkie hates fireworks ------------------------------------------------------------------------------------------------
    def dog_spot(self) -> tuple:
        b = self.b
        if "bakkie" in b.P:
            return b.P["bakkie"][0] + 13, b.P["base"], DOG_FLAT
        return b.P["braai"][0] + 9, b.P["base"], DOG_CURL

    def dog_hide(self, t: float, until: float) -> None:
        b = self.b
        if self.pdog:
            if self.pdog["mode"] != "back" and until > self.pdog["until"]:
                self.pdog["until"] = until
            return
        if not ("dog" in b.P and not b.DOG_AWAY and not b.RAID):
            return
        b.DOG_AWAY = 1
        self.pdog = {"mode": "go", "t0": t, "until": until}
        b.logmsg("wagter[104]: SIGBANG, skuil " + ("onder bakkie0" if "bakkie" in b.P else "onder grid0"))

    pdog: dict = {}

    def dog_update(self, t: float) -> None:
        b = self.b
        if not self.pdog:
            return
        if not b.DOG_AWAY:
            self.pdog = {}
            return
        s = t - self.pdog["t0"]
        if self.pdog["mode"] == "go" and s > 0.7:
            self.pdog["mode"] = "hid"
        if self.pdog["mode"] == "hid" and t > self.pdog["until"]:
            self.pdog["mode"], self.pdog["t0"] = "back", t
        if self.pdog["mode"] == "back" and s > 1.2:
            self.pdog = {}
            b.DOG_AWAY = 0
            b.logmsg("wagter: terug op sy plek, maak of hy nooit bang was nie", True)

    def dog_draw(self, t: float) -> None:
        b = self.b
        if not (self.pdog and "dog" in b.P):
            return
        hx, hy, spr = self.dog_spot()
        dx, dy = b.P["dog"]
        s = t - self.pdog["t0"]
        if self.pdog["mode"] == "hid":
            b.buf.draw(spr, hx + (int(t * 12) % 2), hy - spr.h + 1)
            return
        f = s / 0.7 if self.pdog["mode"] == "go" else s / 1.2
        f = 1 if f > 1 else 0 if f < 0 else f
        x0, x1 = (dx, hx) if self.pdog["mode"] == "go" else (hx, dx)
        x = int(x0 + (x1 - x0) * f + 0.5)
        go_right = x1 > x0
        spr2 = DOG_RUN[int(t * 10) % 2] if go_right else DOG_TROT[int(t * 10) % 2]
        b.buf.draw(spr2, x, dy)

    # ---- letters of fire ----------------------------------------------------------------------------------------------------------------
    def fire_new(self, **o: Any) -> dict:
        obj = dict(o)
        obj["font"] = ""
        obj["ok"] = 0
        self.fire_layout(obj, o.get("t0"))
        return obj

    def fire_pixels(self, obj: dict, font: str, now: float) -> None:
        b = self.b
        F = FONT[font]
        ch = [c for c in "".join(obj["arr"][0]) if c in F]
        pix = []
        tm = []
        for k, c in enumerate(ch):
            g = F[c]
            w = len(g[0])
            for gy in range(len(g)):
                for gx in range(w):
                    if g[gy][gx] != "#":
                        continue
                    top = 1 if (gy == 0 or g[gy - 1][gx] != "#") else 0
                    pix.append((k, gx, gy, top))
                    tmv = list(obj["timing"]((k + gx / w) / len(ch), gy / 5))
                    tmv.extend([b.rand(6.28), 1 if tmv[3] <= now else 0])
                    tm.append(tmv)
        obj["font"], obj["pix"], obj["tm"] = font, pix, tm

    def fire_layout(self, obj: dict, now: float | None = None) -> bool:
        b = self.b
        obj["ok"] = 0
        if "top" not in b.P:
            return False
        ytop, ybot = obj["band"]()
        avail = ybot - ytop + 1
        for ai, sx, sy, gap, font in obj["cands"]:
            if ai >= len(obj["arr"]):
                continue
            lines = obj["arr"][ai]
            F = FONT[font]
            lw, lh, lmin = [], [], []
            for l in lines:
                w, mn, mx = 0, 9, -1
                for c in l:
                    if c not in F:
                        continue
                    g = F[c]
                    w += len(g[0]) * sx + gap
                    for gy in range(len(g)):
                        if "#" in g[gy]:
                            mn = min(mn, gy)
                            mx = max(mx, gy)
                lw.append(w - gap)
                lh.append((mx - mn + 1) * sy)
                lmin.append(mn)
            H = sy * (len(lines) - 1) + sum(lh)
            W = max(lw)
            if W > b.COLS - 4 or H > avail:
                continue
            if obj["font"] != font:
                self.fire_pixels(obj, font, now if now is not None else b.T)
            y0 = ytop + (avail - H) // 3
            if avail - H < 4 + (y0 - ytop):
                y0 = ytop
            x1 = (b.COLS - W) // 2
            cx, cy, cmin = [], [], []
            y = y0
            for li, l in enumerate(lines):
                x = x1 if li == 0 else x1 + lw[0] - lw[li]
                for c in l:
                    if c not in F:
                        continue
                    cx.append(x)
                    cy.append(y)
                    cmin.append(lmin[li])
                    x += len(F[c][0]) * sx + gap
                y += lh[li] + sy
            obj["pos"] = [(cx[k] + gx * sx, cy[k] + (gy - cmin[k]) * sy) for k, gx, gy, _top in obj["pix"]]
            obj.update(sx=sx, sy=sy, x0=x1, y0=y0, w=W, h=H, ok=1)
            return True
        return False

    @staticmethod
    def fire_box(o: dict) -> list[int]:
        return [o["x0"] - 1, o["y0"] - 1, o["x0"] + o["w"], o["y0"] + o["h"]]

    def spark_at(self, obj: dict, i: int, f: float) -> tuple[float, float]:
        b = self.b
        x, y = obj["pos"][i]
        sx0, sy0 = (b.P["braai"][0] + 14, b.P["braai"][1] + 1) if "braai" in b.P else (b.COLS / 2, b.P["base"])
        e = f * f * (3 - 2 * f)
        a = obj["tm"][i][4] + 9 * f
        rr = (1 - f) * (2 + obj["sy"] * 2)
        return sx0 + (x - sx0) * e + 2 * rr * math.cos(a), sy0 + (y - sy0) * e + rr * math.sin(a)

    def fire_draw(self, obj: dict | None, t: float) -> None:
        if not obj or not obj["ok"]:
            return
        b = self.b
        plot, blit = b.buf.plot, b.buf.blit
        sx, sy = obj["sx"], obj["sy"]
        pos, tm, pix = obj["pos"], obj["tm"], obj["pix"]
        tk = t * 2.5
        catch, cool = obj.get("catch", 0.2), obj.get("cool", 0.8)
        for i in range(len(pos)):
            if not pix[i][3]:
                continue
            s0, sd, lit, die = tm[i][:4]
            if t < lit + catch or t > die - cool:
                continue
            x, y = pos[i]
            ph = int(tk + i * 0.618)
            for c in range(sx):
                r = (i * 7 + c * 13 + ph * 29) % 100
                if r >= 22:
                    continue
                plot(x + c, y - 1, "()^'(),"[r % 7], "R" if r < 11 else "r")
        for i in range(len(pos)):
            x, y = pos[i]
            s0, sd, lit, die = tm[i][:4]
            if t >= die:
                continue
            if t < lit:
                if t < s0:
                    continue
                f = (t - s0) / sd
                px, py = self.spark_at(obj, i, f)
                qx, qy = self.spark_at(obj, i, f - 0.06 if f > 0.06 else 0)
                plot(int(qx + 0.5), int(qy + 0.5), ".", "R")
                plot(int(px + 0.5), int(py + 0.5), "*", "W" if f > 0.8 else "Y")
                continue
            ph = int(tk + i * 0.618)
            for j in range(sy):
                r = (i * 37 + j * 211 + ph * 101) % 1990
                if t < lit + catch:
                    blit(x, y + j, "*" * sx, "W" * sx)
                elif t > die - cool:
                    blit(x, y + j, self.FCHC[r:r + sx], self.FCOOL[r:r + sx])
                else:
                    blit(x, y + j, self.FCH[r:r + sx], self.FCO[r + 7:r + 7 + sx])

    def fire_update(self, obj: dict | None, t: float) -> None:
        if not obj or not obj["ok"]:
            return
        b = self.b
        puffs = 0
        for i, tm in enumerate(obj["tm"]):
            if tm[5] or t < tm[3]:
                continue
            tm[5] = 1
            x, y = obj["pos"][i]
            x += b.rand(obj["sx"])
            y += b.rand(obj["sy"])
            self.add(x, y, (b.rand() - 0.5) * 4, -1 - b.rand(2), 0, 1.4 + b.rand(1), None, 4, 0.8, 4)
            if b.rand() < 0.25 and len(b.SMOKE) < 60 and puffs < 3:
                puffs += 1
                b.SMOKE.append([x, y, -(0.4 + b.rand(0.6)), 0, 3 + b.rand(2)])

    # ---- the egg ------------------------------------------------------------------------------------------------------------------------
    def egg_band(self) -> tuple[int, int]:
        return 0, self.b.P["top"] - 1

    def egg_try(self, t: float) -> bool:
        b = self.b
        if self.egg or b.wall_up(t) or not b.claim("egg", t, 21):
            return False
        self.egg_want = 0

        def timing(rel: float, row: float) -> list:
            s0 = t + 3.0 + 2.6 * rel + b.rand(0.4)
            sd = 1.0 + b.rand(0.5)
            return [s0, sd, s0 + sd, t + 15 + 1.4 * b.rand() + 0.9 * row]

        fire = self.fire_new(arr=[["braai-plek.co.za"], ["braai-plek", ".co.za"]], cands=EGG_CANDS, band=self.egg_band,
                             t0=t, timing=timing)
        self.egg = {"t0": t, "fire": fire, "cheer": 0.0, "toot": 0.0}
        self.wallhold = b.WALL_Q[:]
        b.WALL_Q.clear()
        b.SAYS = []
        b.wake("jan", t, "egg0")
        b.logmsg("egg0: niks om te sien hier nie... o.")
        b.fire_mod("pt_egg", 0.6, t + 8)
        b.FAN = 3
        self.faces("pt_up", t + 8)
        self.at(t + 0.4, lambda t2: self.salvo(t2, 7, span=2.4, nofaces=True, rocket={"scale": 1.15}))
        self.at(t + 0.6, lambda t2: self.dog_hide(t2, t + 9.2))

        def lit(t2: float) -> None:
            self.faces("pt_star", t + 15)
            b.logmsg("egg0: braai-plek.co.za is ONLINE")
            if fire["ok"]:
                self.set_avoid("egg", self.fire_box(fire))

        self.at(t + 7.6, lit)
        spots = self.egg_spots(fire)

        def shower(t2: float) -> None:
            for k in range(6):
                o = {"shape": b.pick("willow", "palm", "crackle", "ring", "peony"), "pal": b.pick("gold", "gold", "white", "red")}
                if spots:
                    sp = spots[k % len(spots)]
                    o.update(x=sp[0], y=sp[1], scale=sp[2])
                self.at(t2 + 0.4 * k, lambda t3, o=o: self.launch(t3, **o))

        self.at(t + 8.2 if spots else t + 15.3, shower)

        def toot(t2: float) -> None:
            if "bakkie" in b.P:
                self.egg["toot"] = t2 + 2.5
                b.logmsg("bakkie0: toet toet")

        self.at(t + 8.6, toot)

        def room() -> int:
            return b.P["top"] - (fire["y0"] + fire["h"]) if fire["ok"] else 0

        def cheer(t2: float, howl: bool) -> None:
            lines = list(banter.PT_EGG_CHEER)
            if howl:
                lines.insert(1, ("D", "Ahoooooo!"))
            self.say(t2, *lines)
            b.start_act("koos", t2, salute=True, length=2)
            for w in ("sak", "jan"):
                b.start_act(w, t2, length=2)
            self.faces("laugh", t2 + 2.5)

        self.egg["cheer"] = t + (11.2 if room() >= 4 else 15.4)
        self.at(t + 10.6, lambda t2: self.say(t2, ("D", "Ahoooooo!")) if room() < 4 else None)

        def maybe_cheer(t2: float) -> None:
            if room() >= 4:
                cheer(t2, True)
                return
            self.egg["cheer"] = t + 15.4
            self.at(t + 15.4, lambda t3: cheer(t3, False))

        self.at(t + 11.2, maybe_cheer)
        self.at(t + 15, lambda t2: self.set_avoid("egg"))

        def done(t2: float) -> None:
            b.wall(TAG)
            for m in self.wallhold:
                if m not in b.WALL_Q:
                    b.WALL_Q.append(m)
            self.wallhold = []
            b.release("egg")
            b.logmsg("egg0: terug na die slaap. niks om te sien hier nie.", True)

        self.at(t + 18, done)
        self.at(t + 19.5, lambda t2: setattr(self, "egg", {}))
        return True

    def egg_spots(self, fire: dict) -> list:
        b = self.b
        if not fire["ok"]:
            return []
        x0, y0, x1, y1 = self.fire_box(fire)
        s: list = []
        for sc in (1, 0.75, 0.55):
            rx, ry = 2 * self.R * sc + 2, self.R * sc + 1
            if x0 > 2 * rx:
                s += [(x0 / 2, ry + 1, sc), (x0 / 2, b.P["top"] - 3 - ry, sc)]
            if b.COLS - x1 > 2 * rx:
                s += [((x1 + b.COLS) / 2, ry + 1, sc), ((x1 + b.COLS) / 2, b.P["top"] - 3 - ry, sc)]
            if b.P["top"] - 3 - y1 > 2 * ry:
                s += [(b.COLS * 0.3, y1 + ry + 1, sc), (b.COLS * 0.7, y1 + ry + 1, sc)]
            if s:
                break
        return s

    def egg_update(self, t: float) -> None:
        b = self.b
        if self.egg_want and not self.egg:
            if not self.egg_try(t) and t > self.egg_want:
                self.egg_want = 0
        if not self.egg:
            return
        self.fire_update(self.egg["fire"], t)
        e = t - self.egg["t0"]
        if e > 18:
            return
        self.wallhold.extend(b.WALL_Q)
        b.WALL_Q.clear()
        if len(self.wallhold) > 6:
            del self.wallhold[: len(self.wallhold) - 6]
        if e < self.egg["cheer"] - self.egg["t0"] - 0.2 and not b.talk_q and b.talk_next < t + 0.5:
            b.talk_next = t + 0.5

    def egg_sky(self, t: float) -> None:
        b = self.b
        if not self.egg:
            return
        e = t - self.egg["t0"]
        f = e / 1.4 if e < 1.4 else 1 - (e - 18) / 1.4 if e > 18 else 1
        if f <= 0:
            return
        ybot = b.P["top"] - 2
        cx, cy = b.COLS / 2, ybot / 2
        rx, ry = f * b.COLS * 0.75, f * (ybot + 2)
        for y in range(ybot + 1):
            d = (y - cy) / (ry or 1)
            if d * d >= 1:
                continue
            hw = int(rx * math.sqrt(1 - d * d))
            x0 = max(0, int(cx - hw))
            w = 2 * hw
            if x0 + w > b.COLS:
                w = b.COLS - x0
            if w > 0:
                b.buf.put(x0, y, " " * w, ".")

    def egg_front(self, t: float) -> None:
        b = self.b
        if not self.egg:
            return
        self.fire_draw(self.egg["fire"], t)
        if self.egg["toot"] and self.egg["toot"] > t and "bakkie" in b.P:
            bx, by = b.P["bakkie"]
            on = int(t * 4) % 2
            b.buf.put(bx + 21, by - 1, "TOET! TOET!", "W" if on else "Y")
            b.buf.plot(bx + 36, by + 3, "o", "W" if on else "Y")
            if on:
                b.buf.put(bx + 38, by + 3, "=-", "Y")

    def egg_burning(self) -> bool:
        return bool(self.egg) and 3 < self.b.T - self.egg["t0"] < 15.5

    def egg_status(self) -> list:
        return [[1, TAG]] if self.egg and 7.6 < self.b.T - self.egg["t0"] < 18 else []

    def keyseq(self, t: float, hist: list[str]) -> bool:
        n = len(hist)
        for ln in (9, 10):
            if n < ln:
                continue
            tail = [k.lower() for k in hist[n - ln:]]
            if tail != KONAMI[:ln]:
                continue
            if ln == 10:
                if not self.egg:
                    self.egg_want = t + 60
                hist.clear()
            return True
        return False

    # ---- the radio ------------------------------------------------------------------------------------------------------------------------
    def radio_where(self) -> tuple[str, int, int]:
        b = self.b
        if "bakkie" in b.P:
            return "bakkie", b.P["bakkie"][0] + 25, b.P["bakkie"][1] + 1
        if "tower" in b.P:
            return "tower", b.P["tower"][0] + 6, b.P["tower"][1]
        x = (b.P["jan"] if "jan" in b.P else b.P["koos"])[0] + 1
        y = b.P["base"] + 1
        if y + 1 > b.ROWS - 2:
            y = b.P["base"] - 1
        if "table" in b.P and b.P["table"][0] <= y + 1:
            tx = b.P["table"][4]
            if x + BOX_W >= tx and tx - BOX_W - 1 >= 0:
                x = tx - BOX_W - 1
        return "box", x, y

    def radio_on(self, t: float, why: str) -> None:
        self.radio["on"] = 1
        self.b.logmsg(f"radio: aan ({why})")

    def radio_off(self) -> None:
        self.radio = {}
        self.set_avoid("radio")

    def radio_say(self, t: float, text: str, secs: float | None = None) -> None:
        self.radio["say"] = [text, t + (secs or 2.2 + 0.06 * len(text))]

    def radio_update(self, t: float, dt: float) -> None:
        b = self.b
        if self.radio.get("on") and self.radio.get("notes") and b.rand() < self.radio["notes"] * dt and len(self.notes) < 24:
            _k, x, y = self.radio_where()
            big = b.rand() < 0.6
            self.notes.append([x + b.rand(3) - 1, y - 1, (b.rand() - 0.5) * 7, -(1.3 + b.rand(1.2)), 0, 3 + b.rand(2),
                               NOTE[b.irand(2)] if big else NOTE[2 + b.irand(2)], b.pick("C", "M", "Y", "G", "W", "C")])
        for n in self.notes:
            n[4] += dt
            n[0] += (n[2] + 1.5 * math.sin(n[4] * 3 + n[5])) * dt
            n[1] += n[3] * dt
        self.notes = [n for n in self.notes if n[4] < n[5] and n[1] > 0]
        if self.radio.get("say") and self.radio["say"][1] <= t:
            self.set_avoid("radio")
            del self.radio["say"]

    def notes_draw(self) -> None:
        put = self.b.buf.put
        for n in self.notes:
            g = ["d"] if (n[4] > n[5] * 0.7 and len(n[6]) > 1) else n[6]
            c = n[7].lower() if n[4] > n[5] * 0.8 else n[7]
            for i, row in enumerate(g):
                put(int(n[0]), int(n[1]) + i - (len(g) - 1), row, c)

    def radio_draw(self, t: float) -> None:
        b = self.b
        if not self.radio.get("on"):
            return
        kind, x, y = self.radio_where()
        beat = int(t * 2) % 2
        if kind == "box":
            b.buf.put(x + 1, y, "_______/", "w")
            b.buf.blit(x, y + 1, "[(" + ("O" if beat else "o") + "):=:(" + ("O" if beat else "o") + ")]", "wCCCYYYCCCw")
        elif kind == "bakkie":
            b.buf.put(x - 3, y + 1, "|=|", "Y")
        else:
            b.buf.plot(x - 2, y + 2, "*", "G" if beat else "g")
        if not self.radio.get("say"):
            return
        text = self.radio["say"][0]
        if kind == "box":
            l = wrap(text, b.COLS - 1 - (x + 15))
            y0 = y if len(l) > 1 else y + 1
            b.buf.put(x + 12, y0, ")) ", "C")
            for i, line in enumerate(l[:2]):
                b.buf.put(x + 15, y0 + i, line, "Y")
            return
        self.set_avoid("radio")
        box = b.draw_bubble(x, y, list(b.AVOID), wrap(text, 30 if b.COLS >= 100 else 24))
        if box:
            self.set_avoid("radio", box)

    # ---- sokkie -----------------------------------------------------------------------------------------------------------------------------
    def save_okes(self) -> dict:
        s = {}
        for who in ("koos", "sak", "jan"):
            st = self.b.ST.get(who)
            if st:
                s[who] = {k: st.get(k) for k in ("dx", "dy", "pose", "pose_to", "noface")}
        return s

    def restore_okes(self, saved: dict) -> None:
        for who, vals in saved.items():
            st = self.b.ST.get(who)
            if not st:
                continue
            for k, v in vals.items():
                if v is not None:
                    st[k] = v
                else:
                    st.pop(k, None)

    def sokkie_start(self, t: float) -> None:
        b = self.b
        if self.sok or not b.claim("sokkie", t, 22):
            self.refuse(t, "sokkie")
            return
        b.wake("jan", t, "sokkie")
        self.sok = {"t0": t, "end": t + 19, "saved": self.save_okes(), "dog": 0}
        self.radio_on(t, "sokkie")
        self.radio["notes"] = 3
        b.logmsg("radio: sokkie-stroom begin, 120 bpm")
        self.say(t, *b.pick(*banter.PT_SOK_GO))
        self.at(t + 10, lambda t2: self.say(t2, *b.pick(*banter.PT_SOK_MID)) if self.sok and not b.talk_q else None)
        if "dog" in b.P and not b.DOG_AWAY and not b.RAID and not self.pdog:
            b.DOG_AWAY = 1
            self.sok["dog"] = 1

    def sokkie_update(self, t: float) -> None:
        b = self.b
        if not self.sok:
            return
        if t >= self.sok["end"]:
            self.restore_okes(self.sok["saved"])
            if self.sok["dog"]:
                b.DOG_AWAY = 0
            self.radio_off()
            b.release("sokkie")
            self.sok = {}
            b.logmsg("radio: sokkie verby, 3 okes uitasem")
            self.say(t, b.pick(*banter.PT_SOK_END))
            return
        if self.sok["dog"] and not b.DOG_AWAY:
            self.sok["dog"] = 0
        s = t - self.sok["t0"]
        if s < 1:
            return
        bt = int((s - 1) * 2)
        ph = (s - 1) * 2 - bt
        for who in ("koos", "sak", "jan"):
            st = b.ST.get(who)
            if not st or who not in b.P or st.get("hide"):
                continue
            st["pose"] = POSE[who][(bt + (1 if who == "sak" else 0)) % 2]
            st["pose_to"] = t + 0.3
            st["dx"] = SWING[who][bt % 4]
            st["dy"] = -1 if (bt % 2 and ph < 0.4) else 0
        if int(s) % 6 == 3 and ph < 0.1:
            self.faces("laugh", t + 1.5)

    def sokkie_back(self) -> None:
        b = self.b
        if self.sok and "jan" in b.P and b.ST.get("jan") and not b.ST["jan"].get("hide"):
            b.buf.draw(COOLER, b.P["jan"][0], b.P["jan"][1] + 7)

    def sokkie_actors(self, t: float) -> None:
        b = self.b
        if not (self.sok and self.sok["dog"] and "dog" in b.P):
            return
        x, y = b.P["dog"]
        f = int(t * 7) % 4
        b.buf.draw(DOG_SPIN[f], x + (1 if f in (1, 3) else 0), y)
        if f == 2:
            b.buf.plot(x - 1, y + 1 + (f % 2), "~", "w")

    # ---- sing -------------------------------------------------------------------------------------------------------------------------------
    def mark_vals(self, t: float, who: list[str]) -> None:
        for w in self.okes():
            if w != "jan":
                self.b.set_face(w, "pt_wince", t + 4)
        self.b.logmsg("sing: jannie is 3 halftone af (soos verwag)", True)

    def sing_start(self, t: float) -> None:
        b = self.b
        if self.sing or not b.claim("sing", t, 60):
            self.refuse(t, "sing")
            return
        b.wake("jan", t, "sing")
        song = banter.PT_SONGS[self.song % len(banter.PT_SONGS)]
        self.song += 1
        log, lines = song[0], song[1:]
        lines = [("K+S", text) if (b.COLS < 100 and k == "J+K+S" and len(text) > 16) else (k, text) for k, text in lines]
        self.sing = {"t0": t, "saved": self.save_okes()}
        b.logmsg(log)
        self.say(t, b.pick(*banter.PT_SING_GO), *lines)

    def sing_update(self, t: float) -> None:
        b = self.b
        if not self.sing:
            return
        s = t - self.sing["t0"]
        if s > 1 and not b.talk_q and not any(x["who"] != "dog" for x in b.SAYS):
            self.restore_okes(self.sing["saved"])
            b.release("sing")
            self.sing = {}
            return
        sway = 1 if int(s / 1.2) % 2 else 0
        for w in self.okes():
            b.ST[w]["dx"] = -sway if w == "sak" else sway

    def sing_notes(self, t: float, dt: float) -> None:
        b = self.b
        if not self.sing:
            return
        for bb in b.SAYS:
            if bb["who"] == "dog" or b.rand() > 1.6 * dt:
                continue
            hd = b.head_of(bb["who"])
            if not hd:
                continue
            if len(self.notes) < 24:
                self.notes.append([hd[0] + 3 + b.rand(3), hd[1] - 1, 2 + b.rand(2), -(1 + b.rand(0.8)), 0, 1.6 + b.rand(0.8),
                                   NOTE[2 + b.irand(2)], b.pick("C", "M", "Y", "W")])

    # ---- rugby -------------------------------------------------------------------------------------------------------------------------------
    def rugby_start(self, t: float) -> None:
        b = self.b
        if self.rug or not b.claim("rugby", t, 39):
            self.refuse(t, "rugby")
            return
        b.wake("jan", t, "rugby")
        a = b.pick(14, 17, 20)
        self.rug = {"t0": t, "a": a, "b": a - b.pick(2, 3, 5), "opp": b.pick(*OPP), "min": 0, "saved": self.save_okes(),
                    "ball": None, "spill": 0.0, "spilt": 0, "jump": 0.0}
        self.radio_on(t, "rugby")
        self.say(t, b.pick(*banter.PT_RUGBY_GO))
        opp, die = self.rug["opp"]
        R = self.rug

        def step(at: float, code: Callable) -> None:
            self.at(t + at, lambda t2: code(t2) if self.rug and self.rug["t0"] == t else None)

        def s1(t2: float) -> None:
            R["min"] = 52
            self.radio_say(t2, f"Goeienaand, luisteraars! Tweede helfte: Bokke {R['a']}, {opp} {R['b']}.", 3.6)
            b.logmsg(f"radio: Bokke {R['a']} - {R['b']} {opp}, 52 min")

        def s2(t2: float) -> None:
            R["min"] = 58
            self.radio_say(t2, "En die Bokke is op die aanval...", 2.6)
            self.pass_ball(t2)

        def s3(t2: float) -> None:
            R["min"] = 63
            R["b"] += 3
            self.radio_say(t2, f"Strafskop vir {die}... en hy's oor.", 2.8)
            self.faces("shut", t2 + 2)
            b.logmsg(f"radio: strafskop, Bokke {R['a']} - {R['b']} {opp}")

        def s4(t2: float) -> None:
            self.say(t2, b.pick(*banter.PT_RUGBY_PEN[0]), b.pick(*banter.PT_RUGBY_PEN[1]))

        def s5(t2: float) -> None:
            R["min"] = 71
            self.radio_say(t2, "Lynstaan... losskrum... Hy breek deur! Hy is by die 22!", 3)
            self.faces("wide", t2 + 3)

        def s6(t2: float) -> None:
            R["min"] = 74
            R["a"] += 5
            self.radio_say(t2, "DRIE! Die Bokke druk!", 2.2)
            b.logmsg(f"radio: DRIE! Bokke {R['a']} - {R['b']} {opp}")
            R["jump"] = t2 + 2.4
            self.faces("laugh", t2 + 3)
            if "sak" in b.P and b.ST.get("sak") and not b.ST["sak"].get("hide"):
                R["spill"] = t2 + 0.3
            self.at(t2 + 0.6, lambda t3: self.salvo(t3, 2, span=0.5, nofaces=True,
                                                     rocket={"pal": "bok", "shape": b.pick("ring", "double", "peony")}))

        def s7(t2: float) -> None:
            self.say(t2, *banter.PT_RUGBY_TRY)

        def s8(t2: float) -> None:
            R["a"] += 2
            R["min"] = 80
            self.radio_say(t2, f"Die doelskop is oor... en daar's die eindfluitjie! Die Bokke wen, {R['a']} - {R['b']}!", 4)
            self.bang.append([b.COLS / 2, b.P.get("top", 6) / 2, "FWIEEEET!", t2 + 1.2])
            b.logmsg(f"radio: eindfluitjie, Bokke {R['a']} - {R['b']} {opp}")

        def s9(t2: float) -> None:
            self.say(t2, *banter.PT_RUGBY_END)

        def s10(t2: float) -> None:
            self.restore_okes(R["saved"])
            self.radio_off()
            b.release("rugby")
            self.rug = {}

        for at, code in ((4.6, s1), (8.6, s2), (11.6, s3), (14.6, s4), (20.4, s5), (23.6, s6), (25.9, s7), (32.5, s8),
                         (36.7, s9), (37.5, s10)):
            step(at, code)

    def hand(self, who: str) -> tuple:
        b = self.b
        hd = b.head_of(who)
        if not hd:
            return ()
        return hd[0] + (-4 if who == "sak" else 4), b.P["top"] + 5 + b.ST[who].get("dy", 0)

    def pass_ball(self, t: float) -> None:
        o = self.okes()
        if len(o) < 2 or not self.rug:
            return
        frm = self.rug["ball"][1] if self.rug["ball"] else o[0]
        to = [w for w in o if w != frm]
        self.rug["ball"] = [frm, to[self.b.irand(len(to))], t, 1.3]

    def rugby_update(self, t: float) -> None:
        b = self.b
        R = self.rug
        if not R:
            return
        s = t - R["t0"]
        if not b.talk_q and b.talk_next < t + 0.5:
            b.talk_next = t + 0.5
        bl = R["ball"]
        if bl and t > bl[2] + bl[3] + 0.5:
            if s < 23:
                self.pass_ball(t)
            else:
                R["ball"] = None
        jump = R["jump"] and R["jump"] > t
        for who in self.okes():
            b.ST[who]["dy"] = -1 if (jump and (int(t * 4) + (1 if who == "sak" else 0)) % 2) else 0
        if R["spill"] and b.ST.get("sak") and R["spill"] < t < R["spill"] + 6:
            b.ST["sak"]["pose"] = SAK_NODOP
            b.ST["sak"]["pose_to"] = t + 0.2
        if R["spill"] and not R["spilt"] and t > R["spill"] + 0.8:
            R["spilt"] = 1
            b.logmsg("dop: sakkie het dop #%d gemors (rugby)" % (b.DOPS.get("sak", 0) + 1))

    def rugby_front(self, t: float) -> None:
        b = self.b
        R = self.rug
        if not R:
            return
        bl = R["ball"]
        if bl:
            f = (t - bl[2]) / bl[3]
            a = self.hand(bl[0])
            z = self.hand(bl[1])
            if a and z:
                if f >= 1:
                    b.buf.put(z[0] - 1, z[1], "<=>", "y")
                elif f >= 0:
                    h = z[1] - 1 - (b.P["top"] - 6 if b.P["top"] - 6 > 1 else 1)
                    x = a[0] + (z[0] - a[0]) * f
                    y = a[1] + (z[1] - a[1]) * f - (h + 4) * math.sin(PI * f)
                    b.buf.put(int(x) - 1, int(y + 0.5), ("<=>", "(|)", "<=>", "(-)")[int(f * 10) % 4], "y")
        if R["spill"] and "sak" in b.P and t > R["spill"]:
            f = (t - R["spill"]) / 0.8
            x0, y0 = b.P["sak"][0] + 1, b.P["top"] + 6
            x1, y1 = x0 - 5, b.P["base"]
            if f < 1:
                b.buf.put(int(x0 + (x1 - x0) * f), int(y0 + (y1 - y0) * f - 3 * math.sin(PI * f)), "[#]", "Y")
            elif f < 4:
                b.buf.put(x1 - 1, y1, ".'[#]'." if f < 2 else "._[#]_.", "C" if f < 2 else "c")
                if f < 1.8:
                    b.buf.put(x1, y1 - 1, "' , '", "C")

    def rugby_status(self) -> list:
        R = self.rug
        if not (R and R["min"]):
            return []
        return [[1, f"Bokke {R['a']} - {R['b']} {R['opp'][0]} ({R['min']}')"]]

    # ---- the calendar ----------------------------------------------------------------------------------------------------------------------
    def hats(self, t: float) -> None:
        b = self.b
        lt = self.clock(t)
        day = self.today
        st = "kers" if day in ("kers", "tweede") else "party" if (day == "nuwejaar" or (day == "oujaar" and lt.tm_hour >= 18)) else ""
        if not st:
            return
        for who in ("koos", "sak", "jan"):
            s = b.ST.get(who)
            if who not in b.P or not s or s.get("hide"):
                continue
            x, y = b.P[who][0] + s.get("dx", 0), b.P[who][1] + s.get("dy", 0)
            for dy, dx, txt, col in HATS[st][who]:
                b.buf.blit(x + dx, y + dy, txt, col)

    def fw_gap(self, day: str, h: int) -> float | None:
        b = self.b
        if (day == "oujaar" and h == 23) or (day == "nuwejaar" and h == 0):
            return 150 + b.rand(150)
        if day in ("guy", "braaidag", "nuwejaar", "oujaar", "gelofte", "vryheid"):
            return 600 + b.rand(600)
        return None

    def cal_update(self, t: float, dt: float) -> None:
        b = self.b
        lt = self.clock(t)
        day = self.today
        if (day == "oujaar" and self.now_every < 60) or self.cal.get("cd"):
            self.countdown(t, lt)
        if t < self.cal.get("tick", 0):
            return
        self.cal["tick"] = t + 1
        date = "%02d-%02d" % (lt.tm_mon, lt.tm_mday)
        if day and self.cal.get("greeted", "") != date and t > b.BOOT_END + 2 and not self.cal.get("cd"):
            self.cal["greeted"] = date
            log, wall, ex = banter.PT_GREET[day]
            b.logmsg(log)
            b.wall(wall)
            if len(b.PRIO) < 4:
                b.PRIO.append(list(ex))
            if self.fw_gap(day, lt.tm_hour) is not None:
                self.cal["next_fw"] = t + 60 + b.rand(120)
        gap = self.fw_gap(day, lt.tm_hour)
        if gap is None:
            self.cal.pop("next_fw", None)
        elif not self.cal.get("next_fw"):
            self.cal["next_fw"] = t + gap
        elif t >= self.cal["next_fw"] and b.auto_ok(t):
            n = 4 + b.irand(4)
            self.salvo(t, n)
            b.logmsg(f"vuurwerk: {n} vuurpyle gelanseer ({banter.PT_DAYNAME[day]})")
            ex = b.pick(*banter.PT_OOH)
            self.at(t + 1.6, lambda t2: self.say(t2, *ex) if not b.talk_q else None)
            self.cal["next_fw"] = t + gap
            b.auto_done(t)
        if not self.cal.get("next_song"):
            self.cal["next_song"] = t + 1800 + b.rand(1800)
        if t >= self.cal["next_song"] and b.auto_ok(t):
            self.cal["next_song"] = t + 2700 + b.rand(2700)
            if not self.sing:
                self.sing_start(t)
            b.auto_done(t, 60)

    def countdown(self, t: float, lt: time.struct_time) -> None:
        b = self.b
        mo, d, h, mi, s = lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec
        if mo == 12 and d == 31 and h == 23 and mi == 59 and s >= 50:
            n = 60 - s
            if not b.talk_q and b.talk_next < t + 0.5:
                b.talk_next = t + 0.5
            if self.cal.get("cd") and self.cal["cd"]["n"] == n:
                return
            if not self.cal.get("cd"):
                b.claim("nuwejaar", t, 30)
            cd = self.cal["cd"] = {"n": n, "at": t}
            cd["fire"] = self.fire_new(arr=[[str(n)]], cands=CD_CANDS, band=self.egg_band, t0=t, catch=0.12, cool=0.2,
                                       timing=lambda rel, row: [t - 1, 1, t, t + 0.92 + b.rand(0.1)])
            b.SAYS = []
            if n <= 3:
                b.logmsg(f"aftelling: {n}")
            return
        if not self.cal.get("cd"):
            return
        if not (mo == 1 and d == 1):
            if t - self.cal["cd"]["at"] > 3:
                del self.cal["cd"]
            return
        del self.cal["cd"]
        year = lt.tm_year

        def timing(rel: float, row: float) -> list:
            s0 = t + 0.5 + 1.5 * rel + b.rand(0.3)
            return [s0, 0.9, s0 + 0.9, t + 11 + b.rand(1.2) + 0.6 * row]

        self.cal["year"] = self.fire_new(arr=[[str(year)]], cands=CD_CANDS, band=self.egg_band, t0=t, timing=timing)
        self.salvo(t, 12, span=6, rocket={"scale": 1.1})
        self.faces("pt_star", t + 8)
        self.say(t, *banter.PT_NEWYEAR)
        b.logmsg(f"kalender: {year} gemonteer read-write, gelukkige nuwejaar")
        self.cal["greeted"] = "01-01"
        self.cal["next_fw"] = t + (self.fw_gap("nuwejaar", 0) or 600)
        self.at(t + 13, lambda t2: b.wall(f"Gelukkige Nuwejaar! Welkom, {year}: mag jou vuur altyd brand en jou vleis altyd gaar wees."))
        self.at(t + 14, lambda t2: (self.cal.pop("year", None), b.release("nuwejaar")))

    def cal_front(self, t: float) -> None:
        b = self.b
        self.hats(t)
        cd = self.cal.get("cd")
        if cd:
            self.fire_draw(cd["fire"], t)
            o = self.okes()
            if o and t - cd["at"] < 0.9:
                who = "koos" if "koos" in o else o[0]
                hd = b.head_of(who)
                if hd:
                    b.draw_bubble(hd[0], hd[1], list(b.AVOID) + ([self.fire_box(cd["fire"])] if cd["fire"]["ok"] else []),
                                  [TELL[cd["n"]].upper() + "!"])
        yr = self.cal.get("year")
        if yr:
            self.fire_update(yr, t)
            self.fire_draw(yr, t)

    def cal_status(self) -> list:
        day = self.day(self.b.T)
        return [[5, banter.PT_DAYNAME[day]]] if day else []

    # ---- hooks --------------------------------------------------------------------------------------------------------------------------------
    def on_layout(self, t: float) -> None:
        b = self.b
        self.par = []
        self.rkt = []
        self.bang = []
        self.notes = []
        for k in list(self.avoid):
            self.set_avoid(k)
        self.avoid = {}
        if "top" not in b.P:
            return
        self.R = b.P["top"] / 3.2
        if self.R < 3.2:
            self.R = 3.2
        if self.R > 8:
            self.R = 8
        self.maxp = 420 if b.COLS * b.ROWS > 6000 else 300
        if self.egg:
            self.fire_layout(self.egg["fire"])
            e = t - self.egg["t0"]
            if self.egg["fire"]["ok"] and 7.6 < e < 15:
                self.set_avoid("egg", self.fire_box(self.egg["fire"]))
        if self.cal.get("cd"):
            self.fire_layout(self.cal["cd"]["fire"])
        if self.cal.get("year"):
            self.fire_layout(self.cal["year"])

    def on_update(self, t: float, dt: float) -> None:
        self.run_q(t)
        self.update_fw(t, dt)
        self.dog_update(t)
        self.egg_update(t)
        self.sokkie_update(t)
        self.sing_update(t)
        self.sing_notes(t, dt)
        self.rugby_update(t)
        self.radio_update(t, dt)
        self.cal_update(t, dt)

    def hook_boot(self) -> list:
        d = self.day()
        out = [["w", "vuurwerk0: 12 vuurpyle, 2 fonteine, 0 veiligheidsbrille"],
               ["w", "radio0: AM/FM, RSG, battery 63%, lugdraad gebuig"],
               ["w", "egg0: niks om te sien hier nie"]]
        if d:
            out.append(["w", f"kalender: vandag is {banter.PT_DAYNAME[d]}"])
        return out

    def install(self) -> None:
        b = self.b
        G = b.GUY
        G["koos"]["eyes"][2]["pt_up"] = "('  ')"
        G["koos"]["eyes"][2]["pt_star"] = "(*  *)"
        G["koos"]["eyes"][2]["pt_wince"] = "(>  <)"
        for who in ("sak", "jan"):
            G[who]["eyes"][2]["pt_up"] = "(' ')"
            G[who]["eyes"][2]["pt_star"] = "(* *)"
            G[who]["eyes"][2]["pt_wince"] = "(> <)"
        b.MARK["pt_cheer"] = lambda t, who: self.faces("laugh", t + 2)
        b.MARK["pt_vals"] = self.mark_vals
        for d in banter.PT_DAYNAME:
            b.COND["pt_" + d] = (lambda d=d: self.day(b.T) == d)
        b.TALK.extend(list(x) for x in banter.PT_TALK)
        b.hook("boot", self.hook_boot)
        b.hook("layout", self.on_layout)
        b.hook("update", self.on_update)
        b.hook("sky", lambda t: (self.egg_sky(t), self.draw_fw(t)))
        b.hook("back", lambda t: (self.notes_draw(), self.sokkie_back()))
        b.hook("actors", lambda t: (self.dog_draw(t), self.sokkie_actors(t)))
        b.hook("front", lambda t: (self.egg_front(t), self.cal_front(t), self.rugby_front(t), self.radio_draw(t)))
        b.hook("status", lambda t: self.egg_status() + self.rugby_status() + self.cal_status())
        b.hook("keyseq", self.keyseq)
        b.key("v", "vuurwerk! / fireworks", self.key_v)
        b.key("k", "sokkie! (langarm) / dance", self.sokkie_start)
        b.key("s", "sing 'n liedjie / sing a song", self.sing_start)
        b.key("r", "rugby oor die radio / rugby on the radio", self.rugby_start)
        b.key("P", None, lambda t: setattr(self, "egg_want", t + 60) if not self.egg else None)
