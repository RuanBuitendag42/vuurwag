"""EXTRA: WEER EN TYD -- the weather and the time of day (lekker's fragment 10-weer, wx_), with the real
weather from Open-Meteo driving the states lekker plays by itself.

keys:  w   the weather, one step a press: helder -> winderig -> bewolk -> reen -> donderstorm -> helder
           again (a reenboog when the sun is up); after the step the real weather takes over again
       n   the time of day: werklike tyd (the host's own clock) -> aand -> nag -> dagbreek -> dag -> werklike tyd

The sky follows the host's local clock.  Aand: the sun sinks at the left behind the horizon (behind the thorn
tree when there is one), the sky glows, the first stars come out.  Nag: the core's stars, Milky Way and
Southern Cross.  Dagbreek: the stars fade, the sun comes up on the right and the hadedas fly over shouting.
Dag: sun, slow clouds and birds; the fire still burns.  The moon shows its real phase for today's date, the
way it looks from South Africa (a waxing moon is lit on the left).  Weather: gusts that bend the smoke and
blow leaves, a tolbos and Koos's hat across the veld; clouds over the stars and the moon; rain with splashes
and puddles, a sizzling fire and Koos's umbrella over the meat; a Highveld donderstorm with lightning, KABOOM,
wide eyes and a brakkie under the bakkie; a reenboog when it clears; mis (fog) over the laagte.  Critters:
vuurvliegies, an uil in the thorn tree, vlermuise and muggies at night; birds and hadedas by day.  New
speakers: H the hadeda, U the uil.  It sets the shared DAYLIGHT (0 night .. 1 day) that the other extras read.
"""
from __future__ import annotations

import math
import time
from typing import Any

from . import banter
from .art import DOG, DOG_RUN, DOG_TROT, MOON
from .buf import Sprite, mirror_text, sprite
from .core import Braai

PI = math.pi


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def hhmm(h: float) -> str:
    m = int(h * 60 + 0.5)
    return "%02d:%02d" % (int(m / 60) % 24, m % 60)


# ---- art ---------------------------------------------------------------------------------------------------
SUN_BIG = [sprite(r"""
    \  |  /
  '. .---. .'
 -- (:::::) --
  .' '---' '.
    /  |  \
"""[1:], None, "Y"), sprite(r"""
    .  :  .
  \  .---.  /
 =- (:::::) -=
  /  '---'  \
    '  :  '
"""[1:], """
    y  y  y
  y  YYYYY  y
 yy YYYYYYY yy
  y  YYYYY  y
    y  y  y
"""[1:], "Y")]
SUN_SM = [sprite(" \\ .-. /\n- (:::) -\n / '-' \\", None, "Y"),
          sprite(" . .-. .\n= (:::) =\n ' '-' '", " y YYY y\ny YYYYY y\n y YYY y", "Y")]
LOW_ART = r"""
   _.---._
 .'=======`.
:===========:
 `.=======.'
   `-----'
"""[1:]
LOW_BIG = sprite(LOW_ART, "Y\nY\ny\nR\nr", "Y")
GOLD_BIG = sprite(LOW_ART, "Y\nY\nY\nY\ny", "Y")
LOW_SM = sprite(" .---.\n(=====)\n `---'", "Y\ny\nR", "Y")
GOLD_SM = sprite(" .---.\n(=====)\n `---'", "Y\nY\ny", "Y")

# The moon's outline, in the same boxes as the core's moons (11x6 and 7x3); the phase fills it in.
MOON_T = [(11, 6, ["   _..._", " .'     '.", ":         :", ":         :", "`.       .'", "  `-...-'"]),
          (7, 3, [" .---.", "(     )", " `---'"])]

CLOUD_ART: dict[str, list[tuple[str, str]]] = {
    "fair": [(r"""
    .--.
 .-(    ).
(___.__)__)
"""[1:], ""), (r"""
    .-.
 .-(   )-.
(         )
 `-.___.-'
"""[1:], ""), (r"""
     .--.   .-.
 .--(    )-(   )
(               )
 `--.______.---'
"""[1:], ""), (r"""
         .-~~-.
  .-~~-.(      )-.
 (                 )
(                   )
 `-.____.-~~-.____.-'
"""[1:], "")],
    "rain": [(r"""
    .-~~~-.  .-~~-.
 .-(       )(      )-.
(                     )
 `~-~-~-~-~-~-~-~-~-~'
"""[1:], "\n\n\nbbbbbbbbbbbbbbbbbbbbbbb"), (r"""
    .-~~-.
 .-(      )-.
(            )
 `~-~-~-~-~-'
"""[1:], "\n\n\nbbbbbbbbbbbbbbb")],
    "storm": [(r"""
      .-~~~-.      .-~~~-.
  .-~(       )~-.-(       )-.
 (    .  :  .   .  :   .    )
(  :   .   :  .   .  :   .   )
 `-~-~-~-~-~-~-~-~-~-~-~-~-~-'
"""[1:], """


      b  b  b   b  b   b
   b   b   b  b   b  b   b
 bbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""[1:]), (r"""
     .-~~~-.
 .-~(       )~-.-.
(   .  :   .  :   )
 `-~-~-~-~-~-~-~-'
"""[1:], """


    b  b   b  b
 bbbbbbbbbbbbbbbb
"""[1:]), (r"""
     .-~~-.     .-~~~-.
 .-~(      )~-.(       )-.
(  :  .  :   .   :  .  :  )
 `-~-~-~-~-~-~-~-~-~-~-~-'
"""[1:], """


   b  b  b   b   b  b  b
 bbbbbbbbbbbbbbbbbbbbbbbb
"""[1:])],
}
CLOUD: dict[str, list[tuple[Sprite, Sprite]]] = {
    k: [(sprite(a, m, "w"), sprite(a, m, "W" if k == "fair" else "w")) for a, m in v] for k, v in CLOUD_ART.items()
}

KOOS_MASK = """
      yyyy
    yyyyyyyy

      yyyy
   GGGGGGGGGG  ccccc
  G GGGGGGGGGGG
  G GGGGGGGG
   GGGGGGGGG
    yyyyyyyy
    yyyyyyyy
"""[1:]
KOOS_UMB = sprite(r"""
      ____
    _|____|_
     (o  o)
      \ww/
   .-'`--'`-.
  / |      |\_/
  \ |  ..  |
   \|______|
    |__||__|
    (__)(__)
"""[1:], KOOS_MASK, ".")
KOOS_BARE = sprite(r"""

     .----.
     (o  o)
      \ww/
   .-'`--'`-.  __==<
  / |      |\_/
  \ |  ..  |
   \|______|
    |__||__|
    (__)(__)
"""[1:], KOOS_MASK, ".")
CANOPY = sprite(r"""
       _.-'''''''''-._
  _.-''  \    |    /  ''-._
.'-.__.-'-.__.|.__.-'-.__.-'.
"""[1:], """
       GGGYYYYYYYYYGGG
  GGGGGGGGYYYYwYYYYGGGGGGGG
GGGGGGGGGGYYYYwYYYYGGGGGGGGGG
"""[1:], "G")
CANOPY_HALF = sprite("    _.-'-._\n .'-._|_.-'.", "    GGYYYGG\n GGGYYwYYGGG", "G")
CANOPY_SHUT = sprite("  .\n /|\\", "  G\n GwG", "G")
CANOPY_TOP: dict[int, int] = {}
for _y, _x, _txt, _c in CANOPY.segs:
    for _i in range(len(_txt)):
        _cx = _x + _i
        if _cx not in CANOPY_TOP or _y < CANOPY_TOP[_cx]:
            CANOPY_TOP[_cx] = _y

HAT = [sprite(a, None, "y") for a in ("  ____\n_|____|_", "   _/|\n _/_/\n/__/", "_\\____/_\n  ----", " |\\_\n  \\_\\_\n    \\__\\")]
OWL = [sprite(a, "\nyYyYy", "y") for a in (" ,_,\n(O,O)\n(   )\n-\"-\"-", " ,_,\n(-,-)\n(   )\n-\"-\"-",
                                            " ,_,\n(O,-)\n(   )\n-\"-\"-")]
HADEDA_ART = (r"""
      __
     \  \
,__.-=\  \___.
'     `-.__.-'
"""[1:], r"""


,__.-==---.__.
'     /  /-'
      /__/
"""[1:])
HADEDA = {-1: [sprite(a, None, "w") for a in HADEDA_ART],
          1: [sprite(mirror_text(a, None, True, {"/": "\\", "\\": "/", "(": ")", ")": "(", "<": ">", ">": "<",
                                                  "`": "'", "'": "`", "[": "]", "]": "[", "{": "}", "}": "{"}),
                     None, "w") for a in HADEDA_ART]}
BAT = ["/^v^\\", "\\_v_/"]
BIRD = ["\\v/", "-v-"]
TOLBOS = [sprite(a, None, "y") for a in (" .%#.\n(#%#%)\n `%#'", " .#%.\n(%#%#)\n `#%'")]

MODES = ["real", "aand", "nag", "dagbreek", "dag"]
WNAME = {"helder": "helder", "winderig": "winderig", "bewolk": "bewolk", "reen": "reen", "storm": "donderstorm",
         "mis": "mis"}
WNEXT = {"helder": "winderig", "winderig": "bewolk", "bewolk": "reen", "reen": "storm", "storm": "mis", "mis": "helder"}


class Weer:
    def __init__(self, b: Braai, weather_fn=None, latlon=(-26.2, 28.0), clock_offset: float = 0.0) -> None:
        self.b = b
        self.weather_fn = weather_fn          # () -> Weather | None (the live reading)
        self.latlon = latlon
        self.clock_offset = clock_offset
        self.g: dict[str, Any] = {}
        self.tod: dict[str, Any] = {"mode": "real", "phase": "", "p": 1.0, "s": 1.5, "since": 0.0, "next": 0.0,
                                    "lit": 0, "rph": "nag", "rp": 1.0, "rs": 2.0}
        self.vis: dict[str, Any] = {"sf": 1, "df": 1, "cross": 1, "moon": 1, "glow": 0, "flash": 0, "sunpos": None,
                                    "sun": None}
        self.hid: dict[str, int] = {}
        self.moon: dict[str, Any] = {"key": "", "at": -1.0, "age": 0.0, "spr": None}
        self.w: dict[str, Any] = {"state": "helder", "plan": [], "until": 0.0, "since": 0.0, "dir": 1, "cdir": 1,
                                  "gust_at": 0.0, "gust_len": 0.0, "wet": 0.0, "hat_at": 0.0, "hats": 0,
                                  "strike_at": 0.0, "tol_at": 0.0, "next": 0.0, "live_hold": 0.0}
        self.next: dict[str, float] = {}
        self.wind_cur = 0.0
        self.wind_mine = 0.0
        self.live_wind = 0.0        # the real wind, -1..1 and more, + blows right
        self.live_temp: float | None = None
        self.live_label = ""
        self.clouds: list[dict] = []
        self.cl_next: dict[str, float] = {}
        self.cbot: list[int] = []
        self.drops: list[list] = []
        self.splash: list[list] = []
        self.hiss: list[list] = []
        self.leaves: list[list] = []
        self.tol: dict = {}
        self.bolt: dict = {}
        self.boom: list[dict] = []
        self.bow: dict = {}
        self.dog: dict = {}
        self.hat: dict = {}
        self.umb = {"on": 0, "open": 0.0}
        self.flies: list[list] = []
        self.owl: dict[str, Any] = {"blink": 0, "hoot": 0.0, "hoot_to": 0.0, "x": 0, "y": 0, "side": 1}
        self.owl_box = [-9, -9, -9, -9]
        self.bats: list[list] = []
        self.birds: dict = {}
        self.hadedas: list[list] = []
        self.hd: dict[str, Any] = {}
        self.mug: dict = {}
        self.puddles: list[list] = []
        self.streaks: list[tuple] = []
        self.mist: list[list] = []
        self.bag: dict[str, list[int]] = {}
        self.said: list | None = None
        self.day_tree: dict[int, Sprite] = {}
        self.install()

    # ---- the clock -------------------------------------------------------------------------------------------
    def localtime(self) -> time.struct_time:
        return time.localtime(time.time() + self.clock_offset)

    # ---- the time of day ---------------------------------------------------------------------------------------
    def sun_hours(self) -> tuple[float, float]:
        """Sunrise and sunset for today at the place (lat, lon, on SAST), from the sun's declination and the
        equation of time; good to a few minutes."""
        lt = self.localtime()
        d = lt.tm_yday - 1
        rad = PI / 180
        decl = -23.44 * math.cos(2 * PI * (d + 10) / 365) * rad
        lat = self.latlon[0] * rad
        cosh = (math.sin(-0.83 * rad) - math.sin(lat) * math.sin(decl)) / (math.cos(lat) * math.cos(decl))
        cosh = clamp(cosh, -1, 1)
        half = math.atan2(math.sqrt(1 - cosh * cosh), cosh) / rad / 15
        bb = 2 * PI * (d - 80) / 364
        eot = 9.87 * math.sin(2 * bb) - 7.53 * math.cos(bb) - 1.5 * math.sin(bb)
        tz = -time.timezone / 3600 if not lt.tm_isdst else -time.altzone / 3600
        noon = 12 + (tz * 15 - self.latlon[1]) * 4 / 60 - eot / 60
        return noon - half, noon + half

    def real_phase(self) -> tuple[str, float, float]:
        lt = self.localtime()
        h = lt.tm_hour + lt.tm_min / 60 + lt.tm_sec / 3600
        rise, sset = self.sun_hours()
        s = (h - rise) / (sset - rise)
        if rise - 0.6 <= h < rise + 0.4:
            return "dagbreek", (h - rise + 0.6) / 1.0, s
        if rise + 0.4 <= h < sset - 0.5:
            return "dag", 1, s
        if sset - 0.5 <= h < sset + 0.8:
            return "aand", (h - sset + 0.5) / 1.3, s
        return "nag", 1, -1 if s < 0 else 2

    def manual_phase(self, t: float) -> tuple[str, float, float]:
        m, e = self.tod["mode"], t - self.tod["since"]
        if m == "aand":
            p = clamp(e / 75, 0, 1)
            return "aand", p, 0.82 + 0.24 * p
        if m == "dagbreek":
            p = clamp(e / 60, 0, 1)
            return "dagbreek", p, -0.07 + 0.25 * p
        if m == "dag":
            return "dag", 1, clamp(0.3 + e / 2400, 0.3, 0.7)
        return "nag", 1, 2

    def clock(self, t: float) -> None:
        tod = self.tod
        if tod["mode"] == "real":
            if t >= tod["next"]:
                tod["rph"], tod["rp"], tod["rs"] = self.real_phase()
                tod["next"] = t + 1
            ph, p, s = tod["rph"], tod["rp"], tod["rs"]
        else:
            ph, p, s = self.manual_phase(t)
        old = tod["phase"]
        tod["phase"], tod["p"], tod["s"] = ph, clamp(p, 0, 1), s
        if old != ph:
            self.phase_change(t, old, ph)

    def phase_change(self, t: float, old: str, ph: str) -> None:
        if ph == "dagbreek":
            self.hd["dawn"] = 0
        if old == "" or self.tod["mode"] != "real":
            return
        rise, sset = self.sun_hours()
        self.b.logmsg("son: dagbreek, sterre gaan offline" if ph == "dagbreek"
                      else "son: son.service active (running)" if ph == "dag"
                      else "son: sonsondergang om " + hhmm(sset) + ", sterre laai..." if ph == "aand"
                      else "son: nag, " + self.moon_name(self.moon["age"]) + " bo die braai")

    def daylight_target(self) -> float:
        ph, p = self.tod["phase"], self.tod["p"]
        if ph == "dag":
            return 1
        if ph == "nag":
            return 0
        if ph == "aand":
            return 0.5 + 0.5 * math.cos(PI * clamp(p / 0.9, 0, 1))
        return 0.5 - 0.5 * math.cos(PI * clamp((p - 0.1) / 0.8, 0, 1))

    def daylight_update(self, dt: float) -> None:
        b = self.b
        want = self.daylight_target()
        b.DAYLIGHT = b.DAYLIGHT + (want - b.DAYLIGHT) * (1 - math.exp(-dt / 0.8)) if self.tod["lit"] else want
        if abs(want - b.DAYLIGHT) < 0.002:
            b.DAYLIGHT = want
        self.tod["lit"] = 1

    def daylight(self) -> bool:
        return self.b.DAYLIGHT >= 0.5

    def nightish(self) -> bool:
        ph, p = self.tod["phase"], self.tod["p"]
        return ph == "nag" or (ph == "aand" and p >= 0.55) or (ph == "dagbreek" and p < 0.3)

    def wet(self) -> bool:
        return self.w["state"] in ("reen", "storm")

    def sun_at(self, s: float) -> tuple[float, float, float]:
        g = self.g
        x = g["sun_xr"] + (g["sun_xl"] - g["sun_xr"]) * s
        e = 0 if s <= 0 or s >= 1 else math.sin(PI * s) ** 0.45
        y = self.b.P["base"] - g["sun_H"] * e
        if s < 0 or s > 1:
            y += (-s if s < 0 else s - 1) * g["sun_K"]
        return x, y, e

    # ---- the moon -------------------------------------------------------------------------------------------------
    def moon_age(self) -> float:
        d = (time.time() + self.clock_offset - 947182440) / 86400
        m = 29.530588853
        return d - m * math.floor(d / m)

    @staticmethod
    def moon_lit(a: float) -> float:
        return (1 - math.cos(2 * PI * a / 29.530588853)) / 2

    @staticmethod
    def moon_name(a: float) -> str:
        return ("nuwemaan" if a < 1.0 else "wassende sekel" if a < 6.4 else "eerste kwartier" if a < 8.4
                else "wassende maan" if a < 13.8 else "volmaan" if a < 15.8 else "afnemende maan" if a < 21.1
                else "laaste kwartier" if a < 23.1 else "afnemende sekel" if a < 28.5 else "nuwemaan")

    def moon_sprite(self, big: bool, age: float) -> Sprite:
        W, H, tpl = MOON_T[0 if big else 1]
        f = age / 29.530588853
        c = math.cos(2 * PI * f)
        if c < -0.97:
            c = -1.1
        segs = []
        for y, row in enumerate(tpl):
            stripped = row.lstrip(" ")
            if not stripped:
                continue
            x0 = len(row) - len(stripped)
            body = stripped.rstrip()
            txt, col = "", ""
            for i, ch in enumerate(body):
                x = x0 + i
                v = (y + 0.5 - H / 2) / (H / 2)
                w = 1 - v * v
                w = math.sqrt(w if w > 0.09 else 0.09)
                lit = 0
                for sub in (0.3, 0.7):
                    un = clamp((x + sub - W / 2) / (W / 2) / w, -1, 1)
                    if (-un > c) if f < 0.5 else (un > c):
                        lit += 1
                if ch != " ":
                    txt += ch
                    col += "Y" if lit else "b"
                else:
                    txt += ":" if lit == 2 else "." if lit else " "
                    col += "Y"
            segs.append((y, x0, txt, col))
        return Sprite(segs)

    def moon_update(self, t: float) -> None:
        m = self.moon
        if t >= m["at"]:
            m["age"] = self.moon_age()
            m["at"] = t + 300
        key = f"{self.g.get('big', 0)}:{int(m['age'] * 4)}"
        if key != m["key"]:
            m["spr"], m["key"] = self.moon_sprite(bool(self.g.get("big")), m["age"]), key

    # ---- the sky --------------------------------------------------------------------------------------------------
    def sky_flag(self, k: str, show: bool) -> None:
        SKY = self.b.SKY
        if not show:
            if SKY[k]:
                self.hid[k] = 1
            SKY[k] = 0
        elif self.hid.get(k):
            SKY[k] = 1
            del self.hid[k]

    def sky_update(self, t: float) -> None:
        ph, p, s = self.tod["phase"], self.tod["p"], self.tod["s"]
        st = self.w["state"]
        sf, df, cross, moon, glow = 1.0, 1.0, 1, 1, 0.0
        if ph == "aand":
            sf, df = clamp((p - 0.3) / 0.55, 0, 1), clamp((p - 0.75) / 0.25, 0, 1)
            cross, moon = p > 0.6, p > 0.7
            glow = p / 0.3 if p < 0.3 else 1 if p < 0.55 else 1 - 0.97 * (p - 0.55) / 0.45
        elif ph == "dagbreek":
            sf, df = clamp(1 - p / 0.45, 0, 1), clamp(1 - p / 0.2, 0, 1)
            cross, moon = p < 0.3, p < 0.3
            glow = p / 0.4 if p < 0.4 else 1 - (p - 0.4) / 0.6
        elif ph == "dag":
            sf, df, cross, moon = 0, 0, 0, 0
        if self.wet():
            sf, df, cross, moon = 0, 0, 0, 0
            glow *= 0.4
        elif st == "bewolk":
            df = 0
            glow *= 0.7
        elif st == "mis":
            sf, df, cross = sf * 0.3, 0, 0
            glow *= 0.5
        self.vis.update(sf=sf, df=df, cross=cross, moon=moon, glow=glow)
        shoot = (ph == "nag" or (ph == "aand" and p > 0.9)) and st not in ("bewolk", "mis") and not self.wet()
        self.sky_flag("stars", sf >= 1)
        self.sky_flag("dust", df >= 1)
        self.sky_flag("cross", bool(cross))
        self.sky_flag("shoot", bool(shoot))
        self.b.SKY["moon"] = 0
        sun = None if ph == "nag" else self.sun_at(s)
        if sun and sun[1] > self.b.P["base"] + 4:
            sun = None
        self.vis["sunpos"] = sun
        self.vis["sun"] = None if (self.wet() or st == "mis") else sun

    # ---- the weather ---------------------------------------------------------------------------------------------
    def weather_key(self, t: float) -> None:
        st = WNEXT[self.w["state"]]
        plan = {
            "helder": [["helder", 0]],
            "winderig": [["winderig", 150], ["helder", 0]],
            "bewolk": [["bewolk", 180], ["helder", 0]],
            "reen": [["reen", 180], ["bewolk", 25], ["helder", 0]],
            "storm": [["storm", 120], ["reen", 35], ["bewolk", 20], ["helder", 0]],
            "mis": [["mis", 120], ["helder", 0]],
        }
        self.w["plan"] = [list(x) for x in plan[st]]
        self.w["until"] = t
        if self.w["next"] < t + 900:
            self.w["next"] = t + 900
        self.w["live_hold"] = t + sum(x[1] for x in plan[st]) + 30
        self.weather_plan(t)

    def episode(self) -> list[list]:
        r = self.b.rand()
        if r < 0.33:
            return [["winderig", 70 + self.b.rand(40)], ["helder", 0]]
        if r < 0.6:
            return [["bewolk", 70 + self.b.rand(50)], ["helder", 0]]
        if r < 0.85:
            return [["bewolk", 20], ["reen", 50 + self.b.rand(30)], ["bewolk", 20], ["helder", 0]]
        return [["bewolk", 15], ["reen", 15], ["storm", 50 + self.b.rand(25)], ["reen", 20], ["bewolk", 15], ["helder", 0]]

    def weather_plan(self, t: float) -> None:
        if not self.w["plan"] or t < self.w["until"]:
            return
        st, secs = self.w["plan"].pop(0)
        self.w["until"] = t + secs
        self.weather_set(t, st)

    def weather_set(self, t: float, st: str) -> None:
        b = self.b
        w = self.w
        old = w["state"]
        if old == st:
            return
        w["state"], w["since"] = st, t
        if st == "winderig" or (st == "storm" and old != "storm"):
            w["dir"] = 1 if (not w["hats"] or b.rand() < 0.6) else -1
            if self.live_wind and abs(self.live_wind) > 0.3:
                w["dir"] = 1 if self.live_wind > 0 else -1
            w["cdir"] = w["dir"]
        if st == "winderig":
            w["hat_at"] = t + 7 + b.rand(5)
            w["tol_at"] = t + 12 + b.rand(8)
        if st == "storm":
            w["strike_at"] = t + 2
        day = self.daylight()
        if st == "helder":
            b.logmsg("weer: lug helder, " + ("son skyn weer" if day else "sterre weer online"))
        elif st == "winderig":
            b.logmsg("weer: wind %d km/h %s, rukwinde" % (35 + b.irand(25) if not self.live_label else self.live_kmh,
                                                           "W" if w["dir"] > 0 else "O"))
        elif st == "bewolk":
            b.logmsg("weer: wolke trek oor" + ("" if day else ", maan agter die wolke"))
        elif st == "reen":
            b.logmsg("weer: storm trek weg, net reen" if old == "storm" else "weer: reen begin, kole sis")
        elif st == "mis":
            b.logmsg("weer: mis oor die laagte, sig 50 m")
        else:
            b.logmsg("weer: donderstorm! weerlig in die omgewing")
        if old in ("reen", "storm") and not self.wet() and self.vis["sunpos"] and self.vis["sunpos"][2] > 0.15:
            self.bow_start(t)
        self.talk_change(t, st, old)

    @property
    def live_kmh(self) -> int:
        w = self.weather_fn() if self.weather_fn else None
        return int(w.wind_kmh + 0.5) if w else 0

    def live_state(self, w) -> str:
        """lekker's weather state for a real reading."""
        c = w.condition
        if c == "storm":
            return "storm"
        if c in ("rain", "heavy", "drizzle", "snow"):
            return "reen"
        if c == "fog":
            return "mis"
        if max(w.wind_kmh, w.gusts_kmh * 0.7) >= 28:
            return "winderig"
        if c in ("cloudy", "overcast"):
            return "bewolk"
        return "helder"

    def weather_update(self, t: float, dt: float) -> None:
        b = self.b
        w = self.w
        live = self.weather_fn() if self.weather_fn else None
        if live is not None:
            self.live_temp = live.temp
            self.live_label = live.label
            self.live_wind = clamp(live.wind_x / 25.0, -2.5, 2.5)
            if t >= w["live_hold"] and not w["plan"]:
                want = self.live_state(live)
                if want != w["state"]:
                    self.weather_set(t, want)
                w["next"] = t + 1e9       # the real weather is known: no made-up episodes
        else:
            self.live_wind = 0.0
            if not w["next"] or w["next"] > t + 1e8:
                w["next"] = t + 600 + b.rand(900)
        self.weather_plan(t)
        w["wet"] = clamp(w["wet"] + (dt / 30 if self.wet() else -dt / 80), 0, 1)

    def gust(self, t: float) -> float:
        w = self.w
        if t > w["gust_at"] + w["gust_len"]:
            w["gust_at"] = t + 1.5 + self.b.rand(4.5)
            w["gust_len"] = 1.5 + self.b.rand(2)
        s = (t - w["gust_at"]) / w["gust_len"]
        return math.sin(PI * s) if 0 < s < 1 else 0

    def wind_update(self, t: float, dt: float) -> None:
        b = self.b
        st = self.w["state"]
        d = self.w["dir"]
        if st == "winderig":
            want = d * (1.0 + 2.2 * self.gust(t))
        elif st == "storm":
            want = d * (0.5 + 1.0 * self.gust(t))
        elif st == "reen":
            want = d * 0.3
        else:
            want = 0.0
        if self.live_wind and st not in ("winderig", "storm"):
            want += self.live_wind * (0.6 + 0.4 * self.gust(t))
        want += self.hat_gust(t)
        self.wind_cur += (want - self.wind_cur) * (1 - math.exp(-dt / 0.7))
        b.WIND_ADD += self.wind_cur - self.wind_mine
        self.wind_mine = self.wind_cur
        if st == "winderig":
            b.fire_mod("wx_wind", 0.12, t + 0.5)
        if self.wet():
            cover = self.umb["on"] and self.umb["open"] >= 1
            b.fire_mod("wx_reen", (-0.1 if cover else -0.3) - (0.1 if st == "storm" else 0), t + 0.5)
        if st == "mis":
            b.fire_mod("wx_mis", -0.05, t + 0.5)

    # ---- clouds ------------------------------------------------------------------------------------------------------
    def cloud_target(self) -> dict[str, int]:
        st = self.w["state"]
        day = self.daylight()
        COLS = self.b.COLS
        n = {"fair": 0, "rain": 0, "storm": 0}
        if st == "helder":
            n["fair"] = 2 if day else 0
        elif st == "winderig":
            n["fair"] = 3 if day else 1
        elif st == "bewolk":
            n["fair"] = COLS // 30 + 1
        elif st == "reen":
            n["rain"] = COLS // 17 + 2
        elif st == "mis":
            n["fair"] = 1
        else:
            n["storm"] = COLS // 22 + 2
            n["rain"] = COLS // 45 + 1
        return n

    def cloud_new(self, t: float, k: str, edge: bool) -> None:
        b = self.b
        COLS, ROWS = b.COLS, b.ROWS
        all_ = CLOUD[k]
        fit = [p for p in all_ if p[0].h <= (4 if ROWS < 30 else 5) and p[0].w < COLS / 2] or all_
        pair = fit[b.irand(len(fit))]
        w, h = pair[0].w, pair[0].h
        ymax = int(self.g["cloud_ymax"] * (1 if k == "fair" else 0.6 if k == "rain" else 0.35))
        if edge:
            x, y = (-w + 1 if self.w["cdir"] > 0 else COLS - 1), b.irand(ymax + 1)
        else:
            best = -1
            x = y = 0
            for _ in range(5):
                cx, cy = int(b.rand(COLS + w * 0.4) - w * 0.2), b.irand(ymax + 1)
                d = 999
                for o in self.clouds:
                    if o["gone"]:
                        continue
                    dd = abs(o["x"] + o["w"] / 2 - cx - w / 2) / 2 + abs(o["y"] - cy)
                    if dd < d:
                        d = dd
                if d > best:
                    best, x, y = d, cx, cy
        self.clouds.append({"x": float(x), "y": y, "kind": k, "spr": pair, "w": w, "h": h, "f": 0.7 + b.rand(0.6),
                            "born": t - 9 if edge else t, "gone": 0})

    def clouds_update(self, t: float, dt: float) -> None:
        b = self.b
        want = self.cloud_target()
        v = self.w["cdir"] * (0.35 + 0.5 * abs(self.wind_cur))
        for c in self.clouds:
            c["x"] += v * c["f"] * dt
        self.clouds = [c for c in self.clouds if c["x"] < b.COLS + 1 and c["x"] + c["w"] > -1
                       and not (c["gone"] and t - c["gone"] > 3)]
        for k in ("storm", "rain", "fair"):
            if t < self.cl_next.get(k, 0):
                continue
            mine = [c for c in self.clouds if c["kind"] == k and not c["gone"]]
            if len(mine) > want[k]:
                mine[b.irand(len(mine))]["gone"] = t
                self.cl_next[k] = t + 0.7
            elif len(mine) < want[k]:
                edge = bool(mine) and want[k] - len(mine) == 1
                self.cloud_new(t, k, edge)
                self.cl_next[k] = t + (4 if edge else 0.6)

    def cloud_bottoms(self) -> None:
        COLS = self.b.COLS
        self.cbot = [-1] * COLS
        for c in self.clouds:
            if c["gone"] or c["kind"] == "fair":
                continue
            bt = c["y"] + c["h"] - 1
            for x in range(int(c["x"]) + 2, int(c["x"]) + c["w"] - 2):
                if 0 <= x < COLS and self.cbot[x] < bt:
                    self.cbot[x] = bt

    # ---- rain ----------------------------------------------------------------------------------------------------------
    def canopy_box(self) -> tuple:
        b = self.b
        if not (self.umb["on"] and "koos" in b.P and b.ST.get("koos")):
            return ()
        k = b.ST["koos"]
        kx, ky = b.P["koos"][0] + k.get("dx", 0), b.P["koos"][1] + k.get("dy", 0)
        return kx + 12, kx + 26, ky - 2

    def rain_update(self, t: float, dt: float) -> None:
        b = self.b
        st = self.w["state"]
        inten = 0.6 if st == "storm" else 0.42 if st == "reen" else 0
        if st == "reen":
            inten *= clamp((t - self.w["since"]) / 5, 0.3, 1)
        if not (inten or self.drops or self.splash or self.hiss):
            return
        COLS, ROWS = b.COLS, b.ROWS
        mx = int(clamp(COLS * ROWS / 9, 60, 260))
        if inten:
            self.cloud_bottoms()
            n = inten * COLS * 0.55 * dt
            n = int(n) + (1 if b.rand() < n - int(n) else 0)
            vx = b.WIND * 3.5
            ch = "\\" if vx > 5 else "/" if vx < -5 else "|"
            for _ in range(n):
                if len(self.drops) >= mx:
                    break
                x = b.irand(COLS)
                y = self.cbot[x] + 1 if self.cbot[x] >= 0 else b.irand(2)
                self.drops.append([x, y + b.rand(), 20, ch, b.P["base"], y])
        vx = b.WIND * 3.5
        canopy = self.canopy_box() if self.umb["open"] >= 1 else ()
        bx, by = b.P["braai"]
        keep = []
        for d in self.drops:
            d[1] += d[2] * dt
            d[0] += vx * dt
            x, y = int(d[0]), int(d[1])
            if canopy and canopy[0] <= x <= canopy[0] + 28:
                top = canopy[2] - 2 + CANOPY_TOP.get(x - canopy[0], 2)
                if y >= top - 1:
                    if b.rand() < 0.5:
                        self.splash.append([x, top - 1, 0, 1])
                    continue
            if not canopy and y >= by + 1 and bx + 3 <= x <= bx + 24:
                if b.rand() < 0.25:
                    if len(b.SMOKE) < 120:
                        b.SMOKE.append([x, by + 1, -(1.0 + b.rand(0.8)), 0, 2 + b.rand(2)])
                    if len(self.hiss) < 8:
                        self.hiss.append([x, by + 1, t])
                continue
            if y >= d[4]:
                if len(self.splash) < 90:
                    self.splash.append([x, d[4] - 1, 0, 0])
                continue
            if -1 <= x <= COLS:
                keep.append(d)
        self.drops = keep
        for s in self.splash:
            s[2] += dt
        self.splash = [s for s in self.splash if s[2] < 0.3]
        self.hiss = [h for h in self.hiss if t - h[2] < 0.8]

    def draw_rain(self, t: float, front: int) -> None:
        if not (self.drops or self.splash):
            return
        plot = self.b.buf.plot
        ln = 5 if self.w["state"] == "storm" else 4
        if not front:
            for d in self.drops:
                x, y, ch = int(d[0]), int(d[1]), d[3]
                for k in range(ln):
                    if y - k > d[5]:
                        plot(x, y - k, ch, "c")
        for s in self.splash:
            if s[3] != front:
                continue
            x, y, a = s[0], s[1], s[2]
            if a < 0.12:
                plot(x, y, ".", "c")
            else:
                plot(x - 1, y, "'", "c")
                plot(x + 1, y, "'", "c")

    # ---- wind: leaves, dust and a tolbos -------------------------------------------------------------------------------
    def leaves_update(self, t: float, dt: float) -> None:
        b = self.b
        w = self.wind_cur
        if abs(w) > 0.9 and len(self.leaves) < 30 and b.rand() < (abs(w) - 0.5) * 3 * dt:
            self.leaves.append([-1 if w > 0 else b.COLS, b.P["top"] - 4 + b.rand(b.P["base"] - b.P["top"] + 6), b.rand(6.3),
                                b.pick(",", "`", "'", "~", "*", ".", ","), b.pick("y", "y", "g", "G", "Y", "y")])
        for lf in self.leaves:
            lf[0] += b.WIND * (4.5 + 2 * math.sin(t * 3 + lf[2])) * dt
            lf[1] += (1.6 * math.sin(t * 2.3 + lf[2]) + 0.25) * dt
        self.leaves = [lf for lf in self.leaves if -2 < lf[0] < b.COLS + 1 and 0 <= lf[1] < self.g["fg_hi"] + 1]
        if self.tol:
            self.tol["x"] += self.tol["dir"] * (9 + 5 * abs(w) / 3) * dt
            if self.tol["x"] < -8 or self.tol["x"] > b.COLS + 2:
                self.tol = {}
        elif self.w["state"] == "winderig" and self.w["tol_at"] and t > self.w["tol_at"]:
            d = 1 if w >= 0 else -1
            self.tol = {"x": -7 if d > 0 else b.COLS + 1, "dir": d, "t0": t}
            self.w["tol_at"] = t + 30 + b.rand(30)
            b.logmsg("veld: 1 tolbos op deurtog, geen pakkies verloor", True)
            if not b.PRIO:
                self.queue(b.pick(*banter.WX_TOLBOS))

    def draw_leaves(self, t: float) -> None:
        b = self.b
        for lf in self.leaves:
            b.buf.plot(int(lf[0]), int(lf[1]), lf[3], lf[4])
        if not self.tol:
            return
        s = t - self.tol["t0"]
        hop = 1 if abs(math.sin(s * 4.5)) > 0.75 else 0
        b.buf.draw(TOLBOS[int(s * 6) % 2], int(self.tol["x"]), b.P["base"] - 2 - hop)

    # ---- the thunderstorm ------------------------------------------------------------------------------------------------
    def strike(self, t: float) -> None:
        b = self.b
        COLS = b.COLS
        c = [cl for cl in self.clouds if not cl["gone"] and cl["kind"] != "fair" and cl["x"] >= 1 and cl["x"] + cl["w"] < COLS - 1]
        src = None
        if c:
            src = c[b.irand(len(c))]
            x, y = int(src["x"] + src["w"] * (0.25 + b.rand(0.5))), src["y"] + src["h"]
        else:
            x, y = int(COLS * (0.15 + b.rand(0.7))), 2
        ground = b.rand() < 0.6
        yend = b.P["base"] - 1 if ground else y + 3 + b.irand(int((b.P["top"] - y) * 0.5) or 1)
        path = []
        branch = []
        dx = b.pick(-1, 1)
        for yy in range(y, yend + 1):
            if b.rand() < 0.45:
                dx = b.pick(-1, 0, 1, -dx)
            path.append([x, yy, "/" if dx < 0 else "\\" if dx > 0 else "|"])
            x += dx
            if x < 1:
                x = 1
            if x > COLS - 2:
                x = COLS - 2
        if len(path) > 5:
            at = path[2 + b.irand(len(path) // 2)]
            bx, bd = at[0], (1 if at[2] == "/" else -1)
            for k in range(1, 4 + b.irand(4)):
                if b.rand() < 0.8:
                    bx += bd
                branch.append([bx, at[1] + k, "/" if bd < 0 else "\\"])
        big = b.rand() < 0.65
        wait = 0.3 + b.rand(0.8) if big else 1.5 + b.rand(1.5)
        self.bolt = {"t0": t, "path": path, "branch": branch, "src": src}
        self.boom.append({"at": t + wait, "big": big, "x": path[0][0], "y": path[0][1] - 1 if path[0][1] > 1 else 0, "done": 0})
        b.logmsg("weer: weerlig op %.1f km" % (wait * 0.343), not big)

    def storm_update(self, t: float, dt: float) -> None:
        b = self.b
        if self.w["state"] == "storm" and t >= self.w["strike_at"]:
            self.strike(t)
            self.w["strike_at"] = t + 3.5 + b.rand(6)
        if self.bolt and t - self.bolt["t0"] > 0.45:
            self.bolt = {}
        self.vis["flash"] = 0
        if self.bolt:
            s = t - self.bolt["t0"]
            self.vis["flash"] = 1 if (s < 0.1 or 0.2 < s < 0.27) else 0
        for bm in self.boom:
            if bm["done"] or t < bm["at"]:
                continue
            bm["done"] = 1
            if not bm["big"]:
                continue
            for who in b.CAST:
                if who in b.P and b.ST.get(who) and "wide" in b.GUY[who]["eyes"][2]:
                    b.set_face(who, "wide", t + 1.6)
            slept = b.ST.get("jan", {}).get("asleep")
            b.wake("jan", t, "donderweer")
            if not self.dog:
                self.dog_hide(t, 14 + b.rand(6))
            if slept and b.calm(t):
                b.say_now(t, *banter.WX_KABOOM_SLEPT)
            elif b.rand() < 0.3 and not b.SAYS and b.calm(t):
                b.say_now(t, *b.pick(*banter.WX_KABOOM))
        self.boom = [bm for bm in self.boom if t - bm["at"] < 1.4]

    def draw_bolt(self, t: float) -> None:
        if not self.bolt:
            return
        s = t - self.bolt["t0"]
        if 0.1 < s < 0.18:
            return
        plot = self.b.buf.plot
        c = "W" if s < 0.06 else "Y" if s < 0.3 else "y"
        for x, y, ch in self.bolt["path"]:
            plot(x, y, ch, c)
            plot(x + 1, y, ch, "W" if s < 0.3 else "y")
        for x, y, ch in self.bolt["branch"]:
            plot(x, y, ch, "w" if s < 0.3 else "b")

    def draw_thunder(self, t: float) -> None:
        b = self.b
        for bm in self.boom:
            if not bm["done"]:
                continue
            s = t - bm["at"]
            txt = "KABOOM!" if bm["big"] else "rrrommel..."
            x = int(clamp(bm["x"] - len(txt) // 2, 1, b.COLS - len(txt) - 2))
            y = int(clamp(bm["y"], 1, b.P["top"] - 4))
            if s < 0.6:
                x += b.irand(3) - 1
                if bm["big"]:
                    y += b.irand(2)
            for i, ch in enumerate(txt):
                b.buf.plot(x + i, y, ch, ("Y" if int(s * 8 + i) % 2 else "W") if bm["big"] else "w")
            if bm["big"] and s < 0.8:
                b.buf.put(x - 2, y, "-", "Y")
                b.buf.put(x + len(txt) + 1, y, "-", "Y")
                b.buf.put(x + 1, y - 1, "\\", "y")
                b.buf.put(x + len(txt) - 2, y - 1, "/", "y")
                b.buf.put(x + 1, y + 1, "/", "y")
                b.buf.put(x + len(txt) - 2, y + 1, "\\", "y")

    # the brakkie under the bakkie (or under the braai), peeking out
    def foreign(self, t: float, raid_ok: bool = False) -> bool:
        for k, until in self.b.BUSY.items():
            if until <= t or k.startswith("wx_") or (raid_ok and k == "raid"):
                continue
            return True
        return False

    def dog_hide(self, t: float, secs: float) -> None:
        b = self.b
        if not ("dog" in b.P and not b.DOG_AWAY and not b.RAID and not self.foreign(t)):
            return
        b.DOG_AWAY = 1
        self.dog = {"until": t + secs, "t0": t, "where": "bakkie" if "bakkie" in b.P else "braai"}
        b.logmsg(f"wagter[104]: SIGTERM van die donder, skuil onder die {self.dog['where']}")

    def dog_update(self, t: float) -> None:
        b = self.b
        if not self.dog:
            return
        if not b.DOG_AWAY:
            self.dog = {}
            return
        if t > self.dog["until"] and (self.w["state"] != "storm" or t > self.dog["until"] + 20):
            if not self.foreign(t):
                b.DOG_AWAY = 0
            self.dog = {}
            b.logmsg("wagter: terug op sy plek, bietjie klam", True)

    def draw_dog_peek(self, t: float, where: str) -> None:
        b = self.b
        if not (self.dog and self.dog["where"] == where):
            return
        x, y = (b.P["bakkie"][0] + 13, b.P["base"]) if where == "bakkie" else (b.P["braai"][0] + 11, b.P["base"])
        shiver = int(t * 9) % 2
        eyes = "--" if math.sin(t * 2.1) > 0.93 else "''"
        b.buf.blit(x + shiver, y, f"o{eyes})", "WWWY")

    # ---- the rainbow ----------------------------------------------------------------------------------------------------------
    @staticmethod
    def arc(cx: float, cy: float, rx: float, ry: float) -> list[tuple[int, int, str]]:
        col: dict[int, int] = {}
        row: dict[str, int] = {}
        cells = []
        a = 0.02
        step = 0.25 / rx
        while a < PI - 0.02:
            x, y = cx + rx * math.cos(a), cy - ry * math.sin(a)
            slope = ry / rx * abs(math.cos(a) / math.sin(a))
            if slope <= 0.8:
                c = int(x + 0.5)
                if c not in col:
                    col[c] = 1
                    r = int(y + 0.5)
                    d = y - r
                    cells.append((c, r, "'" if d < -0.22 else "." if d > 0.22 else "-"))
            else:
                r = int(y + 0.5)
                key = str(r) + ("r" if a < PI / 2 else "l")
                if key not in row:
                    row[key] = 1
                    cells.append((int(x + 0.5), r, "|" if slope > 3 else "\\" if a < PI / 2 else "/"))
            a += step
        return cells

    def bow_start(self, t: float) -> None:
        b = self.b
        COLS = b.COLS
        sx = self.vis["sunpos"][0] if self.vis["sunpos"] else COLS * 0.7
        cx = COLS * 0.36 if sx > COLS / 2 else COLS * 0.64
        foot = b.P["top"] - 3
        ry = foot - clamp(int(b.P["top"] * 0.12), 1, 6)
        rx = clamp(ry * 2, COLS * 0.28, COLS * 0.3)
        bands = []
        for k in range(6):
            runs: list[list] = []
            cells = [c for c in self.arc(cx, foot + 1, rx - 2 * k, ry - k) if c[1] <= foot and 0 <= c[0] < COLS]
            cells.sort(key=lambda c: (c[1], c[0]))
            for c in cells:
                if runs and runs[-1][1] == c[1] and runs[-1][0] + len(runs[-1][2]) == c[0]:
                    runs[-1][2] += c[2]
                else:
                    runs.append([c[0], c[1], c[2]])
            bands.append(runs)
        self.bow = {"t0": t, "until": t + 50, "bands": bands}
        b.logmsg("weer: reenboog! 7 kleure gevra, 6 gelewer (ANSI)")
        self.queue(b.pick(*banter.WX_BOW))

    def draw_bow(self, t: float) -> None:
        if not self.bow:
            return
        if t > self.bow["until"] or not self.daylight():
            self.bow = {}
            return
        inn = (t - self.bow["t0"]) / 0.5
        out = (self.bow["until"] - t) / 0.6
        col = "rYGCBM"
        put = self.b.buf.put
        for k in range(6):
            if k > inn or k > out:
                continue
            for x, y, txt in self.bow["bands"][k]:
                put(x, y, txt, col[k])

    # ---- Koos's umbrella ---------------------------------------------------------------------------------------------------------
    def pose_free(self, who: str, t: float, mine: Sprite | None) -> bool:
        s = self.b.ST.get(who)
        if not s or s.get("hide"):
            return False
        if not (s.get("pose") and s.get("pose_to", 0) > t):
            return True
        return bool(mine is not None and s["pose"] is mine)

    def umb_update(self, t: float, dt: float) -> None:
        b = self.b
        want = (self.wet() and "koos" in b.P and "braai" in b.P and not self.hat and self.pose_free("koos", t, KOOS_UMB)
                and not self.foreign(t, True))
        if want:
            self.umb["open"] = clamp(self.umb["open"] + dt / 0.9, 0, 1)
            k = b.ST["koos"]
            k["pose"], k["pose_to"], k["noface"] = KOOS_UMB, t + 0.3, 0
            if k["act_at"] < t + 2:
                k["act_at"] = t + 2
            if not self.umb["on"]:
                self.umb["on"] = 1
                b.logmsg("koos: sambreel oop oor grid0, vleis bly droog")
        elif self.umb["on"]:
            self.umb["on"], self.umb["open"] = 0, 0.0
            k = b.ST.get("koos")
            if k and k.get("pose") is KOOS_UMB:
                k["pose_to"] = 0
            b.logmsg("koos: sambreel toe", True)

    def draw_umbrella(self, t: float) -> None:
        b = self.b
        k = b.ST.get("koos")
        if not (self.umb["on"] and k and k.get("pose") is KOOS_UMB and k.get("pose_to", 0) > t and not k.get("hide")):
            return
        x0, cx, cy = self.canopy_box()
        hx, hy = b.P["koos"][0] + k.get("dx", 0) + 15, b.P["koos"][1] + k.get("dy", 0) + 4
        rows = hy - cy
        px = hx
        for i in range(rows):
            x = int(hx + i * (cx - 1 - hx) / (rows - 1) + 0.5) if rows > 1 else hx
            if i and x > px + 1:
                b.buf.put(px + 1, hy - i, "_" * (x - px - 1), "w")
            b.buf.plot(x, hy - i, "/", "w")
            px = x
        if self.umb["open"] >= 1:
            b.buf.draw(CANOPY, x0, cy - 2)
        elif self.umb["open"] >= 0.5:
            b.buf.draw(CANOPY_HALF, cx - 6, cy - 1)
        else:
            b.buf.draw(CANOPY_SHUT, cx - 2, cy - 1)

    # ---- Koos's hat in the wind -----------------------------------------------------------------------------------------------------
    def hat_gust(self, t: float) -> float:
        if not self.hat:
            return 0
        s = t - self.hat["t0"]
        if s < 1.6:
            return 3.2 * math.sin(PI * s / 1.6)
        if not self.hat["dog"] and 5.3 < s < 7.3:
            return -2.6 * math.sin(PI * (s - 5.3) / 2)
        return 0

    def hat_start(self, t: float) -> bool:
        b = self.b
        if not ("koos" in b.P and self.w["dir"] > 0 and self.pose_free("koos", t, None) and not b.ST["koos"].get("asleep")):
            return False
        if not b.claim("wx_hoed", t, 13):
            return False
        dog = 1 if ("dog" in b.P and not b.DOG_AWAY and not b.RAID) else 0
        self.hat = {"t0": t, "dog": dog, "step": 0, "x0": b.P["koos"][0] + 4, "y0": b.P["koos"][1], "dog_away": 0}
        self.w["hats"] += 1
        b.logmsg("weer: rukwind 70 km/h, koos se hoed is weg")
        b.say_now(t, *(banter.WX_HAT_GONE_DOG if dog else banter.WX_HAT_GONE))
        return True

    def hat_end(self, t: float) -> None:
        b = self.b
        k = b.ST.get("koos")
        if k and k.get("pose") is KOOS_BARE:
            k["pose_to"] = 0
        if self.hat.get("dog_away") and b.DOG_AWAY:
            b.DOG_AWAY = 0
        b.release("wx_hoed")
        self.hat = {}

    def hat_where(self, t: float) -> tuple:
        b = self.b
        s = t - self.hat["t0"]
        x0, y0 = self.hat["x0"], self.hat["y0"]
        spin = int(s * 9) % 4
        if s < 3.5:
            x = x0 + 24 * s + 6 * s * s
            if x > b.COLS:
                return ()
            return (int(x), int(y0 - 4.5 * math.sin(clamp(s * 1.6, 0, PI / 2)) + 1.2 * math.sin(s * 6)), spin)
        if self.hat["dog"]:
            if not (9.9 <= s < 10.7):
                return ()
            f = (s - 9.9) / 0.8
            dx, dy = b.P["dog"][0] - 1, b.P["dog"][1] - 1
            return (int(dx + (x0 - dx) * f + 0.5), int(dy + (y0 - dy) * f - 3 * math.sin(PI * f) + 0.5), 0 if f > 0.75 else spin)
        if not (5.5 <= s < 8.5):
            return ()
        f = (s - 5.5) / 3
        return (int(b.COLS + 1 + (x0 - b.COLS - 1) * f + 0.5), int(y0 - 4 * math.sin(PI * f) + 0.5), 0 if f > 0.8 else spin)

    def hat_update(self, t: float) -> None:
        b = self.b
        if not self.hat:
            if self.w["state"] == "winderig" and self.w["hat_at"] and t > self.w["hat_at"]:
                self.w["hat_at"] = 0 if self.hat_start(t) else t + 4
            return
        s = t - self.hat["t0"]
        end = 10.7 if self.hat["dog"] else 8.5
        if s >= end or "koos" not in b.P:
            self.hat_end(t)
            return
        k = b.ST["koos"]
        k["pose"], k["pose_to"], k["noface"] = KOOS_BARE, t + 0.3, 0
        if k["act_at"] < t + 2:
            k["act_at"] = t + 2
        h = self.hat_where(t)
        if s < 3.5 or h or (self.hat["dog"] and s > 6):
            b.set_face("koos", "wide" if s < 0.5 else "right", t + 0.2)
        if self.hat["step"] == 0 and s > 1.0:
            self.hat["step"] = 1
            for w in ("sak", "jan"):
                b.set_face(w, "laugh", t + 2.5)
            if self.hat["dog"] and "dog" in b.P and not b.DOG_AWAY and not b.RAID:
                b.DOG_AWAY = 1
                self.hat["dog_away"] = 1
            else:
                self.hat["dog"] = 0
        if self.hat["step"] == 1 and self.hat["dog"] and s > 9.5:
            self.hat["step"] = 2
            b.DOG_AWAY = 0
            self.hat["dog_away"] = 0
            b.logmsg("wagter[104]: hoed teruggebring, 0 bytes verloor")
            b.say_now(t, *banter.WX_HAT_BACK_DOG)
        if self.hat["step"] == 1 and not self.hat["dog"] and s > 8.3:
            self.hat["step"] = 2
            b.logmsg("weer: wind draai, hoed terug op koos")
            b.say_now(t, *banter.WX_HAT_BACK_WIND)

    def draw_hat_dog(self, t: float) -> None:
        b = self.b
        if not (self.hat and self.hat["dog"] and "dog" in b.P):
            return
        s = t - self.hat["t0"]
        dx, dy = b.P["dog"]
        if self.hat["dog_away"] and 1.0 < s < 6:
            x = int(dx + 34 * (s - 1.0))
            if x < b.COLS:
                b.buf.draw(DOG_RUN[int(s * 8) % 2], x, dy)
        elif self.hat["dog_away"] and s >= 6:
            x = int(b.COLS + 1 + (dx - b.COLS - 1) * clamp((s - 6) / 3.5, 0, 1))
            b.buf.draw(DOG_TROT[int(s * 6) % 2], x, dy)
            b.buf.draw(HAT[0], x - 1, dy - 1)
        elif 9.5 <= s < 9.9:
            b.buf.draw(HAT[0], dx - 1, dy - 1)

    # ---- critters ---------------------------------------------------------------------------------------------------------------------
    def owl_here(self) -> bool:
        return "tree" in self.b.P and bool(self.owl["x"]) and self.nightish() and self.w["state"] != "storm"

    def flying_ok(self) -> bool:
        return not self.wet()

    def critters_update(self, t: float, dt: float) -> None:
        b = self.b
        COLS = b.COLS
        if self.nightish():
            for f in self.flies:
                f[0] += (f[4] + 0.6 * math.sin(t * 0.7 + f[2])) * dt
                f[1] += 0.5 * math.sin(t * 0.9 + f[2] * 2) * dt
                if f[0] < 0:
                    f[0] += COLS
                if f[0] >= COLS:
                    f[0] -= COLS
                f[1] = clamp(f[1], b.P["base"] - 4, b.P["base"] + 1)
        if self.owl_here():
            self.owl_box[:] = [self.owl["x"], self.owl["y"], self.owl["x"] + 4, self.owl["y"] + 3]
            if t > self.owl["hoot"]:
                self.owl["hoot"] = t + 40 + b.rand(50)
                if not any(s["who"] == "uil" for s in b.SAYS):
                    self.owl["hoot_to"] = t + 2.5
                self.owl["side"] = -1 if b.rand() < 0.5 else 1
        else:
            self.owl_box[:] = [-9, -9, -9, -9]
        quiet = self.w["state"] in ("helder", "bewolk")
        if self.nightish() and quiet and len(self.bats) < 2 and t > self.next.get("bat", 0):
            d = -1 if b.rand() < 0.5 else 1
            self.bats.append([-5 if d > 0 else COLS, 1 + b.rand(b.P["top"] * 0.5), d, b.rand(6.3)])
            self.next["bat"] = t + 20 + b.rand(50)
        for bt in self.bats:
            bt[0] += bt[2] * (6 + 3 * math.sin(t * 1.3 + bt[3])) * dt
        self.bats = [bt for bt in self.bats if -6 < bt[0] < COLS + 1]
        if not self.birds and self.daylight() and self.flying_ok() and t > self.next.get("birds", 0):
            d = -1 if b.rand() < 0.5 else 1
            n = 3 + b.irand(3)
            self.birds = {"x": -4 if d > 0 else COLS + 4 * n, "y": 1 + b.irand(int(b.P["top"] * 0.45) or 1), "dir": d,
                          "off": [(-d * 3 * i, (1 if i % 2 else -1) * ((i + 1) // 2)) for i in range(n)]}
            self.next["birds"] = t + 30 + b.rand(60)
        if self.birds:
            self.birds["x"] += self.birds["dir"] * (7 if self.flying_ok() else 16) * dt
            if self.birds["x"] < -20 or self.birds["x"] > COLS + 20:
                self.birds = {}
        if self.hadedas:
            for h in self.hadedas:
                h[0] += h[2] * 9 * dt
            l = self.hadedas[0]
            f = 1 - l[0] / COLS if l[2] < 0 else l[0] / COLS
            if not self.hd.get("called") and f > 0.3:
                self.hd["called"] = 1
                ex = [("H", "HAA-HAA-HADEDAA!"),
                      banter.WX_HADEDA_DAWN if self.tod["phase"] == "dagbreek" else b.pick(*banter.WX_HADEDA)]
                if b.calm(t):
                    b.say_now(t, *ex)
                elif len(b.PRIO) < 2:
                    b.PRIO.append(ex)
                b.logmsg("hadeda: HAA-HAA teen 110 dB, bure in kennis gestel", True)
            if not any(-16 < h[0] < COLS + 2 for h in self.hadedas):
                self.hadedas = []
        elif (self.tod["phase"] == "dagbreek" and not self.hd.get("dawn") and self.tod["p"] > 0.45 and self.flying_ok()
              and (self.tod["mode"] != "real" or b.auto_ok(t))):
            self.hd["dawn"] = 1
            self.hadeda_start(t, True)
            if self.tod["mode"] == "real":
                b.auto_done(t)
        self.mug_update(t)

    def hadeda_start(self, t: float, dawn: bool) -> None:
        b = self.b
        d = -1 if dawn else b.pick(-1, 1)
        n = 2 + b.irand(2)
        y = int(clamp(int(b.P["top"] * 0.4), 5, b.P["top"] - 4))
        self.hadedas = [[(b.COLS + 1 if d < 0 else -15) - d * i * (14 + b.irand(5)), y + (-1 if i % 2 else 1) * b.irand(2), d, b.rand(6.3)]
                        for i in range(n)]
        self.hd["called"] = 0
        b.logmsg(f"hadeda: {n} voels inkomend, volume 11")

    def head_hadeda(self) -> tuple:
        if not self.hadedas:
            return ()
        x, y, d = self.hadedas[0][0], self.hadedas[0][1], self.hadedas[0][2]
        hx = int(x) + 2 if d < 0 else int(x) + 11
        return (hx, y) if 1 <= hx < self.b.COLS - 1 else ()

    def head_owl(self) -> tuple:
        return (self.owl["x"] + 2, self.owl["y"]) if self.owl_here() else ()

    # muggies: buzzing around one oke's head until he slaps
    def mug_start(self, t: float) -> bool:
        b = self.b
        who_l = [w for w in ("koos", "sak", "jan") if w in b.P and self.pose_free(w, t, None)]
        if not who_l or not b.claim("wx_muggies", t, 8):
            return False
        who = who_l[b.irand(len(who_l))]
        self.mug = {"who": who, "t0": t, "n": 3, "pts": [[b.rand(6.3), 1.5 + b.rand(2)] for _ in range(3)], "klap": 0}
        b.logmsg(f"muggies: 3 vasgehaak aan {b.NAME[who]}", True)
        return True

    def mug_update(self, t: float) -> None:
        b = self.b
        if not self.mug:
            return
        s = t - self.mug["t0"]
        who = self.mug["who"]
        if who not in b.P or s > 7:
            b.release("wx_muggies")
            self.mug = {}
            return
        if not self.mug["klap"] and s > 4.5:
            self.mug["klap"] = t
            self.mug["n"] = 1
            if b.ST[who].get("asleep"):
                b.wake(who, t, "muggies")
            b.set_face(who, "shut", t + 0.35)
            b.logmsg("muggies: 2 doodgeslaan, 1 ontsnap")
            b.say_now(t, *b.pick(*banter.WX_MUG[who]))
        if self.mug["klap"] and 0.35 < t - self.mug["klap"] < 0.5:
            b.set_face(who, "wide", t + 0.8)
        if not self.mug["klap"] and s > 1:
            hd = b.head_of(who)
            if hd:
                b.set_face(who, "left" if math.sin(t * 5.1 + self.mug["pts"][0][0]) < 0 else "right", t + 0.15)

    def draw_muggies(self, t: float) -> None:
        b = self.b
        if not self.mug:
            return
        hd = b.head_of(self.mug["who"])
        if not hd:
            return
        hx, hy = hd
        for i, m in enumerate(self.mug["pts"]):
            if i >= self.mug["n"]:
                break
            away = (t - self.mug["klap"]) * 25 if self.mug["klap"] else 0
            x = int(hx + m[1] * 2 * math.sin(t * 5.1 + m[0]) + away)
            y = int(hy + 1.5 + 1.6 * math.sin(t * 3.7 + m[0] * 1.7) - away / 6)
            b.buf.plot(x, y, "." if int(t * 8 + i) % 2 else "`", "W")
            if i == 0 and not self.mug["klap"] and int(t * 3) % 3:
                b.buf.put(x + 1, y - 1, "bzzz" if int(t * 2) % 2 else "zzzz", "w")
        if self.mug["klap"] and t - self.mug["klap"] < 0.7:
            b.buf.put(hx - 7, hy + 1, "KLAP!", "Y")
            b.buf.plot(hx - 2, hy + 1, "*", "W")

    # ---- the auto surprises --------------------------------------------------------------------------------------------------------
    def auto(self, t: float, dt: float) -> None:
        b = self.b
        if not (b.auto_ok(t) and b.rand() < dt / 12):
            return
        ph = self.tod["phase"]
        can = []
        if self.w["state"] == "helder" and not self.w["plan"] and t >= self.w["next"]:
            can.append("weer")
        if ph in ("dag", "dagbreek") and self.flying_ok() and not self.hadedas and t >= self.next.setdefault("hadeda", t + 300):
            can.append("hadeda")
        if self.nightish() and self.w["state"] in ("helder", "bewolk") and t >= self.next.setdefault("muggies", t + 300):
            can.append("muggies")
        if not can:
            return
        what = can[b.irand(len(can))]
        if what == "weer":
            self.w["plan"] = self.episode()
            self.w["until"] = t
            self.w["next"] = t + 900 + b.rand(1500)
            self.weather_plan(t)
            b.auto_done(t, 60)
        elif what == "hadeda":
            self.hadeda_start(t, False)
            self.next["hadeda"] = t + 600 + b.rand(900)
            b.auto_done(t)
        elif self.mug_start(t):
            self.next["muggies"] = t + 600 + b.rand(900)
            b.auto_done(t)

    # ---- banter ---------------------------------------------------------------------------------------------------------------------------
    def queue(self, ex: list | None) -> None:
        b = self.b
        b.PRIO = [e for e in b.PRIO if self.said is None or e is not self.said]
        if not ex or len(b.PRIO) >= 2:
            return
        b.PRIO.append(ex)
        self.said = ex

    def from_pool(self, k: str) -> list | None:
        pool = banter.WX_POOL.get(k)
        if not pool:
            return None
        if not self.bag.get(k):
            self.bag[k] = list(range(len(pool)))
            self.b.rng.shuffle(self.bag[k])
        return pool[self.bag[k].pop(0)]

    def talk_change(self, t: float, st: str, old: str) -> None:
        if st == "helder" and old not in ("reen", "storm"):
            return
        self.queue(self.from_pool(st))
        self.next["pump"] = t + 40 + self.b.rand(20)

    def pump(self, t: float) -> None:
        if t < self.next.get("pump", 0) or self.b.PRIO or self.w["state"] == "helder":
            return
        self.next["pump"] = t + 40 + self.b.rand(25)
        self.queue(self.from_pool(self.w["state"]))

    # ---- hooks: layout, update -------------------------------------------------------------------------------------------------------------
    def cancel(self, t: float) -> None:
        b = self.b
        if self.hat:
            self.hat_end(t)
        if self.mug:
            b.release("wx_muggies")
            self.mug = {}
        if self.dog:
            if b.DOG_AWAY:
                b.DOG_AWAY = 0
            self.dog = {}
        k = b.ST.get("koos")
        if k and k.get("pose") in (KOOS_UMB, KOOS_BARE):
            k["pose_to"] = 0
        self.umb = {"on": 0, "open": 0.0}
        self.drops = []
        self.splash = []
        self.hiss = []
        self.leaves = []
        self.bats = []
        self.hadedas = []
        self.clouds = []
        self.tol = {}
        self.bolt = {}
        self.birds = {}
        self.bow = {}
        self.boom = []
        self.cl_next = {}

    def on_layout(self, t: float) -> None:
        b = self.b
        self.cancel(t)
        self.g = {}
        if b.P.get("small"):
            return
        b.SKY["moon"] = 0
        base, top = b.P["base"], b.P["top"]
        big = self.g["big"] = 1 if b.P["moonspr"] is MOON else 0
        self.moon["key"] = ""
        COLS = b.COLS
        low = LOW_BIG if big else LOW_SM
        lw = low.w // 2 + 1
        xl = b.P["tree"][1] + int(b.P["tree"][0].w * 0.55) if "tree" in b.P else int(COLS * 0.1)
        self.g["sun_xl"] = clamp(xl, lw, COLS - lw)
        self.g["sun_xr"] = clamp(int(COLS * 0.88), lw, COLS - lw - 1)
        sh = (SUN_BIG[0] if big else SUN_SM[0]).h
        self.g["sun_H"] = base - 2 - sh // 2 - (2 if big else 1)
        self.g["sun_K"] = (low.h + 1) / 0.05
        self.g["cloud_ymax"] = int((top - 4) * 0.5)
        self.g["grp0"] = (b.P["jan"] if "jan" in b.P else b.P["koos"])[0]
        self.g["grp1"] = b.P["sak"][0] + 13
        self.g["fg_lo"] = base + 1
        self.g["fg_hi"] = b.P["table"][0] - 1 if "table" in b.P else b.ROWS - 2
        self.streaks = []
        K = int(clamp(int((top - 2) / 3), 3, 7))
        ytop = int(top * 0.4)
        for k in range(K):
            y = int(top - 2 - k * (top - 2 - ytop) / (K - 1) + 0.5)
            for _ in range(2 if k < 2 else 1):
                ln = int(COLS * (0.1 + b.rand(0.2)) * (1 - 0.4 * k / K)) + 4
                off = b.irand(int(COLS * 0.28) or 1)
                txt = "".join(b.pick("-", "-", "-", "-", "~", "~", "_", " ") for _ in range(ln))
                pos = 0
                for part in txt.split(" "):
                    if part:
                        self.streaks.append((off + pos, y, part, k / (K - 1)))
                    pos += len(part) + 1
        self.flies = [[b.rand(COLS), base - 3 + b.rand(4), b.rand(6.3), 0.8 + b.rand(1.4), (b.rand() - 0.5) * 1.2]
                      for _ in range(int(clamp(COLS // 9, 6, 18)))]
        self.puddles = []
        if self.g["fg_hi"] >= self.g["fg_lo"]:
            for _ in range(int(clamp(COLS // 14, 3, 12))):
                self.puddles.append([b.irand(COLS - 8), self.g["fg_lo"] + b.irand(self.g["fg_hi"] - self.g["fg_lo"] + 1), 3 + b.irand(5)])
        self.mist = [[b.rand(COLS), base - 6 + b.irand(7), 6 + b.irand(18), b.rand(6.3)] for _ in range(int(clamp(COLS // 8, 6, 24)))]
        self.owl["x"] = 0
        if "tree" in b.P:
            spr, tx, ty = b.P["tree"]
            self.owl["x"], self.owl["y"] = tx + (18 if spr.w > 30 else 7), ty - 4
            b.AVOID.append(self.owl_box)

    def on_update(self, t: float, dt: float) -> None:
        if not self.g:
            return
        self.clock(t)
        self.daylight_update(dt)
        self.moon_update(t)
        self.weather_update(t, dt)
        self.sky_update(t)
        self.wind_update(t, dt)
        self.clouds_update(t, dt)
        self.rain_update(t, dt)
        self.leaves_update(t, dt)
        self.storm_update(t, dt)
        self.umb_update(t, dt)
        self.hat_update(t)
        self.dog_update(t)
        self.critters_update(t, dt)
        self.auto(t, dt)
        self.pump(t)

    # ---- hooks: drawing ----------------------------------------------------------------------------------------------------------------------
    def draw_partial_sky(self, t: float) -> None:
        b = self.b
        plot = b.buf.plot
        sf, df = self.vis["sf"], self.vis["df"]
        if self.hid.get("dust") and df > 0:
            for i, (x, y, c) in enumerate(b.DUST):
                if (i * 37 % 101) / 101 < df:
                    plot(x, y, c, "b")
        if self.hid.get("stars") and sf > 0:
            for i, (x, y, ph, sp) in enumerate(b.STARS):
                if (i * 53 % 97) / 97 >= sf:
                    continue
                v = math.sin(t * sp + ph)
                if v > 0.95:
                    plot(x, y, "*", "W")
                elif v > 0.3:
                    plot(x, y, ".", "W")
                elif v > -0.7:
                    plot(x, y, ".", "w")
                else:
                    plot(x, y, ".", "b")

    def draw_glow(self, t: float) -> None:
        g = self.vis["glow"]
        if g <= 0.05:
            return
        dawn = self.tod["phase"] == "dagbreek"
        pal = "YyRrMmb"
        put = self.b.buf.put
        COLS = self.b.COLS
        for off, y, txt, h in self.streaks:
            i = int(h * 3.2 + (1 - g) * 4.5)
            if i > 6:
                continue
            put(COLS - 1 - off - len(txt) if dawn else off, y, txt, pal[i])

    def draw_sun(self, t: float) -> None:
        sun = self.vis["sun"]
        if not sun:
            return
        b = self.b
        x, y, e = sun
        big = self.g["big"]
        ph = self.tod["phase"]
        if e < 0.35 or (ph == "aand" and e < 0.5):
            spr = LOW_BIG if big else LOW_SM
        elif e < 0.6 or ph == "aand":
            spr = GOLD_BIG if big else GOLD_SM
        else:
            spr = (SUN_BIG if big else SUN_SM)[int(t * 1.5) % 2]
        w, h = spr.w, spr.h
        sx, sy = int(x - w / 2 + 0.5), int(y - h / 2 + 0.5)
        low = b.P["top"] if (sx + w > self.g["grp0"] and sx < self.g["grp1"]) else b.P["base"]
        for yy, xx, txt, col in spr.segs:
            if sy + yy >= low:
                continue
            b.buf.blit(sx + xx, sy + yy, txt, col)

    def draw_clouds(self, t: float) -> None:
        b = self.b
        day = 1 if self.daylight() else 0
        flash = self.vis["flash"]
        put = b.buf.put
        for c in self.clouds:
            a = clamp((t - c["born"]) / 3, 0, 1)
            if c["gone"]:
                a = clamp(1 - (t - c["gone"]) / 3, 0, a)
            x, y, spr = int(c["x"]), c["y"], c["spr"][day]
            g = self.vis["glow"] if c["kind"] == "fair" else 0
            if flash and c["kind"] != "fair":
                hot = self.bolt.get("src") is c and t - self.bolt["t0"] < 0.06
                b.buf.draw_col(spr, x, y, "v" if hot else "W")
            elif a >= 0.7 and g > 0.3:
                b.buf.draw_col(spr, x, y, "M" if g > 0.6 else "m")
            elif a >= 0.7:
                b.buf.draw(spr, x, y)
            else:
                b.buf.draw_col(spr, x, y, "b" if (a < 0.35 or not day) else "w")

    def draw_flyers(self, t: float) -> None:
        b = self.b
        put = b.buf.put
        for bt in self.bats:
            y = int(bt[1] + 1.5 * math.sin(t * 2.1 + bt[3]) + 0.7 * math.sin(t * 5.3 + bt[3]))
            put(int(bt[0]), int(clamp(y, 0, b.P["top"] - 3)), BAT[int(t * 7 + bt[3]) % 2], "w")
        if self.birds:
            for i, (ox, oy) in enumerate(self.birds["off"]):
                put(int(self.birds["x"] + ox), self.birds["y"] + oy, BIRD[int(t * 4 + i * 0.7) % 2], "w")
        for x, y, d, ph in self.hadedas:
            b.buf.draw(HADEDA[d][int(t * 2.5 + ph) % 2], int(x), y - 2)

    def draw_mist(self, t: float) -> None:
        if self.w["state"] != "mis":
            return
        b = self.b
        put = b.buf.put
        f = clamp((t - self.w["since"]) / 8, 0, 1)
        for i, m in enumerate(self.mist):
            if (i * 31 % 17) / 17 > f:
                continue
            x = int(m[0] + 3 * math.sin(t * 0.2 + m[3]) + self.wind_cur * 2)
            n = m[2]
            txt = "".join(("~", "-", "~", " ", "~", "-")[int(t * 0.7 + m[3] + k) % 6] for k in range(n))
            put(x, int(m[1]), txt, "w" if (i % 3) else "b")

    def hook_sky(self, t: float) -> None:
        if not self.g:
            return
        self.draw_partial_sky(t)
        self.draw_glow(t)
        if self.vis["moon"] and self.moon["spr"]:
            self.b.buf.draw(self.moon["spr"], *self.b.P["moon"])
        self.draw_bow(t)
        self.draw_sun(t)
        self.draw_clouds(t)
        self.draw_bolt(t)
        self.draw_flyers(t)

    def hook_scenery(self, t: float) -> None:
        b = self.b
        if not self.g:
            return
        if "tree" in b.P:
            spr, tx, ty = b.P["tree"]
            if self.vis["flash"]:
                b.buf.draw_col(spr, tx, ty, "W")
            elif self.daylight():
                key = id(spr)
                if key not in self.day_tree:
                    self.day_tree[key] = Sprite([(y, x, txt, col.replace("g", "G")) for y, x, txt, col in spr.segs])
                b.buf.draw(self.day_tree[key], tx, ty)
        if self.vis["flash"]:
            b.buf.put(0, b.P["base"], "_" * b.COLS, "W")
            for x, y, txt, _at in b.GROUND:
                b.buf.put(x, y, txt, "W")
        elif self.daylight():
            atr = b.buf.atr
            for x, y, txt, at in b.GROUND:
                if at == "g" and atr[y][x] == "g":
                    b.buf.put(x, y, txt, "G")
        if self.w["wet"] > 0.15:
            for p in self.puddles:
                n = int(p[2] * clamp((self.w["wet"] - 0.15) * 1.5, 0, 1) + 0.5)
                if not n:
                    continue
                txt = ("~-~~-~-~" * 3)[int(t * 2 + p[0]) % 2:][:n]
                b.buf.put(p[0] + (p[2] - n) // 2, p[1], txt, "c" if self.wet() else "b")
        if self.owl_here():
            blink = 1 if int(t * 10) % 47 < 2 else 2 if int(t * 10) % 211 < 4 else 0
            b.buf.draw(OWL[blink], self.owl["x"], self.owl["y"])
            if self.owl["hoot_to"] > t:
                txt = "hoe-hoe"
                shown = txt[: int((t - self.owl["hoot_to"] + 2.5) * 6) + 1]
                b.buf.put(self.owl["x"] - len(txt) - 1 if self.owl["side"] < 0 else self.owl["x"] + 6, self.owl["y"] + 1, shown, "w")
        if self.nightish() and self.w["state"] in ("helder", "bewolk"):
            for f in self.flies:
                v = math.sin(t * f[3] + f[2])
                if v < 0.5:
                    continue
                b.buf.plot(int(f[0]), int(f[1]), "*" if v > 0.85 else ".", "Y" if v > 0.85 else "G")
        if "bakkie" in b.P:
            self.draw_dog_peek(t, "bakkie")

    def hook_back(self, t: float) -> None:
        if not self.g:
            return
        self.draw_rain(t, 0)
        self.draw_mist(t)
        self.draw_dog_peek(t, "braai")

    def hook_actors(self, t: float) -> None:
        if self.g:
            self.draw_hat_dog(t)

    def hook_front(self, t: float) -> None:
        if not self.g:
            return
        b = self.b
        self.draw_umbrella(t)
        self.draw_rain(t, 1)
        for h in self.hiss:
            a = t - h[2]
            b.buf.put(h[0] - 1, h[1] - int(a * 2.5), "sss" if a < 0.3 else "ss", "w")
        self.draw_leaves(t)
        if self.hat:
            hw = self.hat_where(t)
            if hw:
                b.buf.draw(HAT[hw[2]], hw[0], hw[1])
        self.draw_muggies(t)
        self.draw_thunder(t)

    def hook_status(self, t: float) -> list:
        f = []
        if self.bow:
            f.append([5, "weer: reenboog"])
        elif self.w["state"] != "helder":
            f.append([5, "weer: " + WNAME[self.w["state"]]])
        if self.live_temp is not None:
            f.append([6.2, "%dC" % int(self.live_temp + 0.5)])
        if self.tod["mode"] != "real":
            f.append([6, "tyd: " + self.tod["mode"]])
        return f

    def hook_boot(self) -> list:
        lt = self.localtime()
        d = lt.tm_yday + 7 * lt.tm_hour
        age = self.moon_age()
        rise, sset = self.sun_hours()
        live = self.weather_fn() if self.weather_fn else None
        if live is not None:
            wl = "weer: %s, %s, wind %d km/h (open-meteo)" % (live.place, live.label.lower(), int(live.wind_kmh + 0.5))
            if live.temp is not None:
                wl = "weer: %s, %dC, %s, wind %d km/h (open-meteo)" % (live.place, int(live.temp + 0.5), live.label.lower(),
                                                                       int(live.wind_kmh + 0.5))
        else:
            wl = "weer: barometer %d hPa ok, wind %d km/h %s (geen internet: net die horlosie)" % (
                1008 + d % 14, 6 + d % 17, ("N", "NO", "O", "SO", "S", "SW", "W", "NW")[d % 8])
        return [["w", wl],
                ["w", "maan: %s (%d%%), son op %s, son onder %s" % (self.moon_name(age), int(self.moon_lit(age) * 100 + 0.5),
                                                                     hhmm(rise), hhmm(sset))]]

    def key_n(self, t: float) -> None:
        b = self.b
        i = MODES.index(self.tod["mode"])
        m = MODES[(i + 1) % len(MODES)]
        self.tod["mode"], self.tod["since"], self.tod["next"] = m, t, 0
        self.clock(t)
        log = {"aand": "tyd: handmatig -> aand, son sak", "nag": "tyd: handmatig -> nag, sterre online",
               "dagbreek": "tyd: handmatig -> dagbreek, hadedas laai", "dag": "tyd: handmatig -> dag, son.service active"}
        lt = self.localtime()
        b.logmsg(log.get(m) or "tyd: terug na werklike tyd, %02d:%02d (%s)" % (lt.tm_hour, lt.tm_min, self.tod["phase"]))
        self.queue(None if self.wet() else banter.WX_TOD_TALK.get(m))

    def install(self) -> None:
        b = self.b
        b.HEAD["hadeda"] = self.head_hadeda
        b.HEAD["uil"] = self.head_owl
        b.WHO["H"] = "hadeda"
        b.WHO["U"] = "uil"
        b.NAME["hadeda"] = "hadeda"
        b.NAME["uil"] = "uil"
        C = b.COND
        C["wx_reen"] = self.wet
        C["wx_storm"] = lambda: self.w["state"] == "storm"
        C["wx_wind"] = lambda: self.w["state"] == "winderig"
        C["wx_bewolk"] = lambda: self.w["state"] == "bewolk"
        C["wx_mis"] = lambda: self.w["state"] == "mis"
        C["wx_dag"] = lambda: self.tod["phase"] == "dag" and not self.wet()
        C["wx_dagbreek"] = lambda: self.tod["phase"] == "dagbreek"
        C["wx_aand"] = lambda: self.tod["phase"] == "aand" and self.vis["glow"] > 0.3
        C["wx_helder"] = lambda: self.tod["phase"] == "nag" and self.w["state"] == "helder"
        C["wx_volmaan"] = lambda: self.nightish() and self.vis["moon"] and abs(self.moon["age"] - 14.77) < 1.6
        C["wx_nuwemaan"] = lambda: self.tod["phase"] == "nag" and not self.wet() and (self.moon["age"] < 1.5 or self.moon["age"] > 28)
        C["wx_sekel"] = lambda: self.vis["moon"] and self.nightish() and 0.04 < self.moon_lit(self.moon["age"]) < 0.3
        C["wx_vuur"] = lambda: self.nightish() and self.w["state"] in ("helder", "bewolk")
        C["wx_boom"] = lambda: self.w["state"] == "storm" and "tree" in b.P
        C["wx_hond"] = lambda: bool(self.dog)
        C["wx_umb"] = lambda: bool(self.umb["on"])
        C["wx_koud"] = lambda: self.live_temp is not None and self.live_temp < 8
        C["wx_warm"] = lambda: self.live_temp is not None and self.live_temp > 30
        b.FILL["temp"] = lambda: "" if self.live_temp is None else str(int(self.live_temp + 0.5))
        b.TALK.extend(list(x) for x in banter.WX_TALK)
        b.hook("layout", self.on_layout)
        b.hook("update", self.on_update)
        b.hook("sky", self.hook_sky)
        b.hook("scenery", self.hook_scenery)
        b.hook("back", self.hook_back)
        b.hook("actors", self.hook_actors)
        b.hook("front", self.hook_front)
        b.hook("status", self.hook_status)
        b.hook("boot", self.hook_boot)
        b.key("w", "die weer: wind, wolke, reen, storm, mis / the weather", self.weather_key)
        b.key("n", "tyd van die dag: aand, nag, dagbreek, dag, regtig / time of day", self.key_n)
