"""EXTRA: DIE PLAAS -- the farm around the braai (vuurwag's own fragment, pl_), in lekker's hook style.

Always there, where there is room: a windpomp on the koppie at the left that turns with the wind (the real wind
when Open-Meteo is on); the plaasdam below it that reflects the moon; the kraal at the right with the skape in
it at night; the plaashek on the far right (Oom Faan's bakkie stops beyond it); sheep and cattle on the koppie
by day; the Southern Cross and the Milky Way are the core's.  Critters: hoenders scratching in the werf, a
donkie that stands and looks, a hadeda walking the lawn, a jakkals calling at night (Wagter answers), the
fireflies, bats and the uil are the weather extra's.  Embers rise off the coals and drift with the wind; `f`
fans the fire and throws a burst of sparks.

Skits (on a key, and now and then by themselves):
   a   die dominee arrives at the wrong moment (speaker P)
   i   a selfie: everyone leans in, a flash, KLIK!
   u   Jannie fetches hout from the houtstapel
   p   somebody pokes Koos's fire ("Los my vuur!")
   z   the gas-vs-hout argument
   e   a critter now (hoenders, the donkie, a hadeda in the yard, a jakkals at night)
   5   Wagter steals a sleeping Jannie's dop
   plus a dop run (Jannie brings Koos a cold one), and Koos chasing Wagter when the brakkie steals a chop.
"""
from __future__ import annotations

import math
from typing import Any, Callable

from . import banter
from .art import DOG_RUN, DOG_TROT
from .buf import Sprite, sprite
from .core import Braai

PI = math.pi

# ---- art -------------------------------------------------------------------------------------------------------
WHEEL = [sprite(a, None, "w") for a in (" _|_ \n/-+-\\\n\\-+-/\n `|' ", " \\|/ \n -+- \n /|\\ \n  |  ",
                                        " `|' \n\\-+-/\n/-+-\\\n _|_ ", " /|\\ \n -+- \n \\|/ \n  |  ")]
TOWER_LEGS = sprite("  /|\\\n / | \\\n/  |  \\", None, "y")
KOPPIE = sprite(r"""
     _.--._
  _-'      '-._
-'             '-
"""[1:], None, "y")
DOMINEE = sprite(r"""
      ___
    _(___)_
     (o o)
      \_/
   .-'[ ]'-.
  / |  |  | \
 (_)|  |  |(_)
    |__|__|
    |  |  |
    (__|__)
"""[1:], """
      www
    wwwwwww


   wwwWWWwww
  w wwwwwww w
 www wwwwwww www
    wwwwwww
    wwwwwww
    yyyyyyy
"""[1:], ".")
DONKIE = [sprite(a, None, "y") for a in (" |\\_~~~\\\n(o)_____)\n ||    ||", " |\\_~~~\\\n(o)_____)\n ||    ||")]
HOENDER = {1: [",o>", ".o>"], -1: ["<o,", "<o."]}
HADEDA_WALK = [",_'>", ",_'v"]


class Plaas:
    def __init__(self, b: Braai, weer=None) -> None:
        self.b = b
        self.weer = weer
        self.g: dict[str, Any] = {}
        self.wheel = 0.0
        self.embers: list[list] = []
        self.hoenders: list[list] = []
        self.hoender_until = 0.0
        self.donkie: dict = {}
        self.hadeda: dict = {}
        self.jakkals: dict = {}
        self.sk: dict = {}
        self.next: dict[str, float] = {}
        self.can: dict = {}
        self.chase = 0.0
        self.flash = 0.0
        self.raid_seen = 0.0
        self.install()

    # ---- helpers -------------------------------------------------------------------------------------------------------
    def night(self) -> bool:
        return self.b.DAYLIGHT < 0.5

    def wet(self) -> bool:
        return bool(self.weer and self.weer.wet())

    def quiet(self, t: float) -> bool:
        b = self.b
        return b.calm(t) and not b.SAYS and not b.talk_q and not b.wall_up(t)

    def refuse(self, t: float) -> None:
        b = self.b
        if not b.talk_q and not b.wall_up(t):
            b.say_now(t, b.pick(*banter.PT_NO))

    # ---- layout: where the farm fits ---------------------------------------------------------------------------------------
    def on_layout(self, t: float) -> None:
        b = self.b
        P = b.P
        self.g = {}
        self.embers = []
        self.hoenders = []
        self.donkie = {}
        self.hadeda = {}
        self.jakkals = {}
        self.can = {}
        self.chase = 0.0
        if self.sk:
            self.sk_end(t)
        if P.get("small"):
            return
        base, top = P["base"], P["top"]
        tree_x = P["tree"][1] if "tree" in P else (P["jan"] if "jan" in P else P["koos"])[0]
        left_room = tree_x
        g = self.g
        # the koppie with the windpomp on it, in the sky rows at the far left (clear of the thorn tree's trunk)
        corner_free = True
        if "tree" in P:
            spr, tx, ty = P["tree"]
            for sy, sx, txt, _c in spr.segs:
                yy = ty + sy
                if (base - 11 <= yy <= base - 4 and tx + sx <= 11) or (base - 3 <= yy <= base - 1 and tx + sx <= 16):
                    corner_free = False
                    break
        else:
            corner_free = left_room >= 17
        if corner_free and base - 12 >= 1:
            g["koppie"] = (0, base - 3)
            g["windpomp"] = (5, base - 10)
        # the plaasdam on the ground at the left, clear of the top(1) table
        table_x = P["table"][4] if "table" in P else b.COLS
        if base + 3 <= b.ROWS - 2 and table_x > 16:
            g["dam"] = (1, base + 2, min(14, table_x - 3))
        # the kraal and the plaashek on the right
        right = P["sak"][0] + 13
        right_room = b.COLS - right
        tbl_r = P["table"][4] + P["table"][5] if "table" in P else 0
        if right_room >= 14 and base + 2 <= b.ROWS - 2 and b.COLS - 14 > tbl_r + 2:
            g["kraal"] = (b.COLS - 14, base + 2)
        if right_room >= 10:
            g["hek"] = (b.COLS - 9, base)
        g["yard_l"] = (1, max(1, left_room - 2))
        g["yard_r"] = (right + 2, b.COLS - 2)

    # ---- the farm, drawn ------------------------------------------------------------------------------------------------------
    def wind(self) -> float:
        return self.b.WIND

    def draw_scenery(self, t: float) -> None:
        b = self.b
        g = self.g
        if not g:
            return
        buf = b.buf
        day = not self.night()
        flash = bool(self.weer and self.weer.vis.get("flash"))
        if "koppie" in g:
            x, y = g["koppie"]
            buf.draw_col(KOPPIE, x, y, "W" if flash else "y")
            if day and not self.wet():
                for i, (dx, dy, ch, c) in enumerate(((8, 1, "o", "W"), (11, 2, "o", "W"), (4, 2, "o", "W"), (13, 1, "m", "y"), (2, 2, "m", "y"))):
                    if int(t / 7 + i) % 5 != 4:
                        buf.plot(x + dx + (int(t / 11 + i) % 2), y + dy, ch, c)
        if "windpomp" in g:
            x, y = g["windpomp"]
            buf.draw(TOWER_LEGS, x - 1, y + 4)
            buf.draw(WHEEL[int(self.wheel) % 4], x - 1, y)
        if "dam" in g:
            x, y, w = g["dam"]
            moon = bool(self.weer is None or (self.weer.vis.get("moon") and not self.wet()))
            c = "c" if self.wet() else "b"
            for r in range(2):
                txt = "".join(("~", "-", "~", "~")[int(t * 1.5 + k + r * 2) % 4] for k in range(w - r * 2))
                buf.put(x + r, y + r, txt, c)
            if not day and moon:
                buf.plot(x + w // 2 + int(math.sin(t * 0.8)), y, ")", "Y")
        if "kraal" in g:
            x, y = g["kraal"]
            buf.put(x, y - 1, "|", "y")
            buf.put(x, y, "|-|-|-|-|-|-|", "y")
            buf.put(x + 12, y - 1, "|", "y")
            if not day:
                for i in range(3):
                    buf.put(x + 2 + i * 4, y - 1, "oo" if int(t * 0.3 + i) % 7 else "o.", "W")
        if "hek" in g:
            x, y = g["hek"]
            buf.put(x, y - 1, "|       |", "y")
            buf.put(x, y, "|=|=|=|=|", "y")

    # ---- embers and the fanned fire -----------------------------------------------------------------------------------------------
    def embers_update(self, t: float, dt: float) -> None:
        b = self.b
        if "braai" not in b.P:
            return
        bx, by = b.P["braai"]
        rate = (b.HEAT - 0.35) * 2.5
        if rate > 0 and b.rand() < rate * dt and len(self.embers) < 40:
            self.embers.append([bx + 4 + b.rand(18), by + 1.5, (b.rand() - 0.5) * 1.5, -(1.5 + b.rand(1.5)), 0.0, 1.5 + b.rand(1.5)])
        W = b.WIND
        for e in self.embers:
            e[4] += dt
            e[0] += (e[2] + W * (0.5 + e[4])) * dt
            e[1] += e[3] * dt
            e[3] *= 1 - 0.6 * dt
        self.embers = [e for e in self.embers if e[4] < e[5] and e[1] > 0]

    def draw_embers(self, t: float) -> None:
        plot = self.b.buf.plot
        for e in self.embers:
            f = e[4] / e[5]
            plot(int(e[0]), int(e[1]), "*" if f < 0.3 else "+" if f < 0.55 else "." if f < 0.8 else "'",
                 "Y" if f < 0.3 else "R" if f < 0.6 else "r")

    def fan_burst(self, t: float) -> None:
        b = self.b
        if "braai" not in b.P:
            return
        bx, by = b.P["braai"]
        for _ in range(14):
            b.SPARKS.append([bx + 5 + b.rand(18), by + 1, (b.rand() - 0.5) * 6, -(4 + b.rand(6)), 0])
        b.fire_mod("pl_fan", 0.25, t + 2.5)

    # ---- critters --------------------------------------------------------------------------------------------------------------------
    def hoenders_start(self, t: float) -> bool:
        b = self.b
        g = self.g
        if self.hoenders or self.night() or self.wet() or "yard_l" not in g:
            return False
        x0, x1 = g["yard_l"] if b.rand() < 0.5 else g["yard_r"]
        if x1 - x0 < 8:
            x0, x1 = g["yard_r"]
            if x1 - x0 < 8:
                return False
        n = 2 + b.irand(2)
        y0 = b.P["base"] + 1
        y1 = min(b.ROWS - 2, b.P["base"] + 2)
        if "table" in b.P:
            y1 = min(y1, b.P["table"][0] - 1)
        for i in range(n):
            self.hoenders.append([x0 + b.rand(x1 - x0 - 3), y0 + b.irand(max(1, y1 - y0 + 1)), 1 if b.rand() < 0.5 else -1,
                                  b.rand(6.3), x0, x1 - 3, y0, y1])
        self.hoender_until = t + 60 + b.rand(90)
        b.logmsg(banter.PL_LOG_HOENDERS.format(n=n), True)
        return True

    def hoenders_update(self, t: float, dt: float) -> None:
        b = self.b
        if not self.hoenders:
            return
        if t > self.hoender_until or self.night() or self.wet():
            self.hoenders = []
            return
        for h in self.hoenders:
            if b.rand() < 0.02:
                h[2] = -h[2]
            if math.sin(t * 1.3 + h[3]) > 0.2:
                h[0] += h[2] * 2.5 * dt
            if h[0] < h[4]:
                h[0], h[2] = h[4], 1
            if h[0] > h[5]:
                h[0], h[2] = h[5], -1

    def draw_hoenders(self, t: float) -> None:
        buf = self.b.buf
        for h in self.hoenders:
            scratch = math.sin(t * 1.3 + h[3]) <= 0.2
            txt = HOENDER[h[2]][int(t * 5 + h[3]) % 2 if scratch else 0]
            buf.put(int(h[0]), int(h[1]), txt, "Y" if int(h[3] * 10) % 3 else "W")
            if scratch and int(t * 6 + h[3]) % 3 == 0:
                buf.plot(int(h[0]) + (3 if h[2] > 0 else -1), int(h[1]), "'", "y")

    def donkie_start(self, t: float) -> bool:
        b = self.b
        g = self.g
        if self.donkie or self.night() or "yard_r" not in g:
            return False
        x0, x1 = g["yard_r"]
        if x1 - x0 < 12 or "bakkie" in b.P:
            x0, x1 = g["yard_l"]
            if x1 - x0 < 12:
                return False
        self.donkie = {"x": x0 + b.irand(max(1, x1 - x0 - 10)), "y": b.P["base"] - 2, "until": t + 120 + b.rand(120)}
        b.logmsg(banter.PL_LOG_DONKIE, True)
        if len(b.PRIO) < 2:
            b.PRIO.append(list(banter.PL_DONKIE))
        return True

    def draw_donkie(self, t: float) -> None:
        if not self.donkie:
            return
        if self.b.T > self.donkie["until"] or self.night():
            self.donkie = {}
            return
        self.b.buf.draw(DONKIE[int(t * 0.5) % 2], self.donkie["x"], self.donkie["y"] + (1 if int(t * 0.5) % 2 else 0) - 1)

    def hadeda_start(self, t: float) -> bool:
        b = self.b
        g = self.g
        if self.hadeda or self.night() or self.wet() or "yard_l" not in g:
            return False
        x0, x1 = g["yard_l"]
        if x1 - x0 < 10:
            x0, x1 = g["yard_r"]
            if x1 - x0 < 10:
                return False
        y1 = min(b.ROWS - 2, b.P["base"] + 2)
        if "table" in b.P:
            y1 = min(y1, b.P["table"][0] - 1)
        self.hadeda = {"x": float(x0 + 1), "x1": x1 - 4, "y": y1, "t0": t, "until": t + 25 + b.rand(15), "said": 0}
        b.logmsg("hadeda: 1 op die grasperk, soek erdwurms", True)
        return True

    def hadeda_update(self, t: float, dt: float) -> None:
        b = self.b
        h = self.hadeda
        if not h:
            return
        if t > h["until"]:
            self.hadeda = {}
            return
        if math.sin(t * 0.9) > 0:
            h["x"] += 2 * dt
        if h["x"] > h["x1"]:
            h["x"] = h["x1"]
        if not h["said"] and t - h["t0"] > 6 and self.quiet(t):
            h["said"] = 1
            b.say_now(t, ("H", "HAA-HAA-HADEDAA!"), *banter.PL_HADEDA_YARD)

    def draw_hadeda(self, t: float) -> None:
        h = self.hadeda
        if not h:
            return
        probing = math.sin(t * 0.9) <= 0
        self.b.buf.put(int(h["x"]), h["y"], HADEDA_WALK[1 if (probing and int(t * 4) % 2) else 0], "w")

    def jakkals_start(self, t: float) -> bool:
        b = self.b
        if self.jakkals or not self.night() or self.wet():
            return False
        self.jakkals = {"t0": t, "x": 1 if b.rand() < 0.5 else b.COLS - 20, "y": max(1, b.P["top"] - 5)}
        b.logmsg(banter.PL_LOG_JAKKALS)
        if "dog" in b.P and not b.DOG_AWAY and self.quiet(t):
            b.say_now(t, *b.pick(*banter.PL_JAKKALS))
        return True

    def draw_jakkals(self, t: float) -> None:
        j = self.jakkals
        if not j:
            return
        s = t - j["t0"]
        if s > 4.5:
            self.jakkals = {}
            return
        txt = ("~ hoe-hoeeee ~", "~ hoe-hoeeee ~", "~ hoeeee...  ~", "  ...        ")[min(3, int(s / 1.2))]
        self.b.buf.put(j["x"], j["y"], txt, "w" if int(s * 3) % 2 else "b")

    def critter_now(self, t: float) -> None:
        b = self.b
        if self.night():
            cands = [self.jakkals_start]
        else:
            cands = [self.hoenders_start, self.donkie_start, self.hadeda_start]
        b.rng.shuffle(cands)
        for fn in cands:
            if fn(t):
                return
        b.logmsg("plaas: die diere slaap, probeer later", True)

    # ---- the skits -----------------------------------------------------------------------------------------------------------------------
    def sk_start(self, t: float, name: str, secs: float, lines: list, key_only: bool = False) -> bool:
        b = self.b
        if self.sk or not b.claim("pl_" + name, t, secs):
            if not key_only:
                self.refuse(t)
            return False
        self.sk = {"name": name, "t0": t, "end": t + secs, "lines": lines}
        b.say_now(t, *lines)
        return True

    def sk_end(self, t: float) -> None:
        b = self.b
        if not self.sk:
            return
        name = self.sk["name"]
        if name == "dominee":
            self.dominee_leave()
        if name == "hout":
            j = b.ST.get("jan")
            if j:
                j["hide"] = 0
        b.release("pl_" + name)
        self.sk = {}

    def sk_update(self, t: float) -> None:
        b = self.b
        if not self.sk:
            return
        s = self.sk
        name = s["name"]
        if name == "dominee":
            self.dominee_update(t)
        if name == "hout":
            j = b.ST.get("jan")
            if j and 2 < t - s["t0"] < 8:
                j["hide"] = 1
            elif j and t - s["t0"] >= 8 and j.get("hide"):
                j["hide"] = 0
                self.hout_back(t)
        if name == "sleep" and 1.5 < t - s["t0"] < 4 and "dog" in b.P:
            s["dog_run"] = 1
        if t >= s["end"] and not b.talk_q and not b.SAYS:
            self.sk_end(t)
        elif t >= s["end"] + 20:
            self.sk_end(t)

    # the dop run: a cold one flies from Jannie to Koos
    def doprun(self, t: float) -> None:
        b = self.b
        if "jan" not in b.P or "koos" not in b.P:
            self.refuse(t)
            return
        b.wake("jan", t, "dop")
        self.sk_start(t, "doprun", 9, b.pick(*banter.PL_DOPRUN))

    def mark_bring(self, t: float, who: list) -> None:
        b = self.b
        if "jan" not in b.P or "koos" not in b.P:
            return
        b.start_act("jan", t, length=0.6, throw=True)
        self.can = {"t0": t + 0.2, "dur": 1.1, "x0": b.P["jan"][0] + 9, "y0": b.P["jan"][1] + 2,
                    "x1": b.P["koos"][0] + 2, "y1": b.P["koos"][1] + 5}
        b.logmsg("dop: jannie -> koos, 'n koue een", True)

    def draw_can(self, t: float) -> None:
        c = self.can
        if not c or t < c["t0"]:
            return
        f = (t - c["t0"]) / c["dur"]
        if f > 1:
            self.can = {}
            return
        h = (c["y0"] + c["y1"]) / 2 - (self.b.P["top"] - 2)
        x = c["x0"] + (c["x1"] - c["x0"]) * f
        y = c["y0"] + (c["y1"] - c["y0"]) * f - h * math.sin(PI * f)
        self.b.buf.put(int(x + 0.5), int(y + 0.5), "[#]", "Y")

    def poke(self, t: float) -> None:
        b = self.b
        self.sk_start(t, "poke", 9, b.pick(*banter.PL_POKE))

    def mark_poke(self, t: float, who: list) -> None:
        b = self.b
        b.fire_mod("pl_poke", 0.35, t + 4)
        b.set_face("koos", "wide", t + 3)
        bx, by = b.P["braai"]
        for _ in range(10):
            b.SPARKS.append([bx + 6 + b.rand(14), by + 1, (b.rand() - 0.5) * 5, -(3 + b.rand(5)), 0])
        b.logmsg("grid0: kole gepook deur iemand anders as koos (ongemagtig)")
        self.sk["poke_at"] = t

    def draw_poke(self, t: float) -> None:
        s = self.sk
        if not (s and s["name"] == "poke" and s.get("poke_at") and t - s["poke_at"] < 2.2):
            return
        b = self.b
        bx, by = b.P["braai"]
        f = t - s["poke_at"]
        x = bx + 27 - int(min(f, 1) * 6)
        b.buf.put(x, by + 2, "--==<" if int(t * 6) % 2 else "---=<", "c")

    def gas(self, t: float) -> None:
        b = self.b
        if self.sk_start(t, "gas", 24, b.pick(*banter.PL_GAS)):
            b.set_face("koos", "wide", t + 6)
            b.set_face("sak", "laugh", t + 10)

    def sleep_steal(self, t: float) -> None:
        b = self.b
        j = b.ST.get("jan")
        if "jan" not in b.P or "dog" not in b.P or b.DOG_AWAY or not j:
            self.refuse(t)
            return
        j["asleep"] = 1
        j["wake_at"] = t + 5
        if self.sk_start(t, "sleep", 12, b.pick(*banter.PL_SLEEP)):
            b.logmsg("wagter[104]: jannie se dop opgespoor, eienaar in suspend", True)

    def draw_sleep(self, t: float) -> None:
        s = self.sk
        b = self.b
        if not (s and s["name"] == "sleep" and s.get("dog_run") and "dog" in b.P and "jan" in b.P):
            return
        f = (t - s["t0"] - 1.5) / 2.5
        if f < 0 or f > 1:
            return
        dx, dy = b.P["dog"]
        jx = b.P["jan"][0] + 12
        x = int(dx + (jx - dx) * (f * 2 if f < 0.5 else 1 - (f - 0.5) * 2))
        spr = (DOG_TROT if f < 0.5 else DOG_RUN)[int(t * 8) % 2]
        b.buf.draw(spr, x, dy)
        if f > 0.5:
            b.buf.put(x + (10 if f > 0.5 else -3), dy + 1, "[#]", "Y")

    def hout(self, t: float) -> None:
        b = self.b
        if "jan" not in b.P:
            self.refuse(t)
            return
        b.wake("jan", t, "hout")
        if self.sk_start(t, "hout", 14, b.pick(*banter.PL_HOUT)):
            b.logmsg("jannie: na die houtstapel, terug oor 6 s")

    def mark_fetch(self, t: float, who: list) -> None:
        pass

    def hout_back(self, t: float) -> None:
        b = self.b
        bx, by = b.P["braai"]
        for _ in range(16):
            b.SPARKS.append([bx + 6 + b.rand(14), by + 2, (b.rand() - 0.5) * 7, -(3 + b.rand(6)), b.rand(0.3)])
        b.fire_mod("pl_hout", 0.4, t + 30)
        b.say_now(t, *banter.PL_HOUT_BACK)
        b.logmsg("hout: 3 stompe kameeldoring van die houtstapel, vuur +40%")

    def selfie(self, t: float) -> None:
        b = self.b
        if self.sk_start(t, "selfie", 10, b.pick(*banter.PL_SELFIE)):
            b.wake("jan", t, "foto")

    def mark_selfie(self, t: float, who: list) -> None:
        b = self.b
        self.flash = t + 1.6
        for w in ("koos", "sak", "jan"):
            b.set_face(w, "laugh", t + 3)
        b.logmsg(banter.PL_LOG_SELFIE.format(n=sum(1 for w in ("koos", "sak", "jan") if w in b.P)))

    def draw_flash(self, t: float) -> None:
        if not self.flash or t > self.flash:
            return
        b = self.b
        s = self.flash - t
        if s > 1.2:
            atr = b.buf.atr
            for y in range(b.P["top"] - 2, b.P["base"] + 2):
                row = atr[y]
                for x in range(len(row)):
                    row[x] = "W"
        else:
            hd = b.head_of("jan") or b.head_of("koos")
            if hd:
                b.buf.put(hd[0] - 2, hd[1] - 1, "KLIK!", "Y" if int(t * 6) % 2 else "W")

    # the dominee
    def dominee(self, t: float) -> None:
        b = self.b
        if "dominee" in b.P:
            self.refuse(t)
            return
        if not b.claim("pl_dominee", t, 40):
            self.refuse(t)
            return
        x = b.COLS + 1
        y = b.P["base"] - 9
        b.ST["dominee"] = {"blink_at": t + 1, "blink_to": 0, "act_at": t + 1e6, "act_to": 0, "talk_to": 0, "look": 0,
                           "face_to": 0, "face": "open", "asleep": 0, "doze_at": 1e9}
        b.P["dominee"] = [x, y]
        if "dominee" not in b.CAST:
            b.CAST.append("dominee")
        tx = b.P["sak"][0] + 14
        if tx + 13 > b.COLS - 1:
            tx = b.COLS - 14
        self.sk = {"name": "dominee", "t0": t, "end": t + 40, "x": float(x), "tx": tx, "step": "in", "lines": None}
        b.logmsg(banter.PL_LOG_DOMINEE)
        for w in ("koos", "sak", "jan"):
            b.set_face(w, "wide", t + 3)
        b.wake("jan", t, "dominee")

    def dominee_update(self, t: float) -> None:
        b = self.b
        s = self.sk
        if "dominee" not in b.P:
            return
        if s["step"] == "in":
            s["x"] -= 12 * (1 / 10.0)
            if s["x"] <= s["tx"]:
                s["x"] = float(s["tx"])
                s["step"] = "talk"
                b.say_now(t, *b.pick(*banter.PL_DOMINEE))
                s["ts"] = t
        elif s["step"] == "talk" and self.quiet(t) and t - s.get("ts", t) > 1:
            b.say_now(t, *banter.PL_DOMINEE_BYE)
            s["step"] = "bye"
            s["ts"] = t
        elif s["step"] == "bye" and self.quiet(t) and t - s["ts"] > 1:
            s["step"] = "out"
        elif s["step"] == "out":
            s["x"] += 12 * (1 / 10.0)
            if s["x"] > b.COLS + 1:
                s["end"] = t
                self.sk_end(t)
                return
        b.P["dominee"][0] = int(s["x"])
        st = b.ST.get("dominee")
        if st:
            st["pose"], st["pose_to"] = DOMINEE, t + 0.5

    def dominee_leave(self) -> None:
        b = self.b
        b.CAST = [w for w in b.CAST if w != "dominee"]
        b.P.pop("dominee", None)
        b.ST.pop("dominee", None)
        b.SAYS = [s for s in b.SAYS if s["who"] != "dominee"]
        b.logmsg("hek0: die dominee is weg, 1 tjop minder", True)

    # Koos chases the brakkie when he steals a chop (the core's raid)
    def chase_update(self, t: float) -> None:
        b = self.b
        if b.RAID and b.RAID.get("step", 0) >= 1 and self.raid_seen != b.RAID["t0"]:
            self.raid_seen = b.RAID["t0"]
            self.chase = t + 2.6
            b.logmsg("koos: agter wagter aan, tang in die hand", True)
        k = b.ST.get("koos")
        if not k:
            return
        if self.chase and t < self.chase:
            f = (self.chase - t) / 2.6
            k["dx"] = int(5 * math.sin(PI * (1 - f)))
            k["dy"] = -1 if int(t * 6) % 2 else 0
        elif self.chase:
            self.chase = 0.0
            k["dx"], k["dy"] = 0, 0

    # ---- the auto surprises ----------------------------------------------------------------------------------------------------------------
    def auto(self, t: float, dt: float) -> None:
        b = self.b
        for what, gap in (("hoenders", 240), ("donkie", 600), ("hadeda", 420), ("jakkals", 300)):
            self.next.setdefault(what, t + 60 + b.rand(gap))
        if b.rand() < dt / 6:
            for what in ("hoenders", "donkie", "hadeda", "jakkals"):
                if t < self.next[what]:
                    continue
                fn = {"hoenders": self.hoenders_start, "donkie": self.donkie_start, "hadeda": self.hadeda_start,
                      "jakkals": self.jakkals_start}[what]
                if fn(t):
                    self.next[what] = t + 300 + b.rand(600)
                else:
                    self.next[what] = t + 60
                break
        self.next.setdefault("skit", t + 240 + b.rand(300))
        if t >= self.next["skit"] and b.auto_ok(t):
            self.next["skit"] = t + 420 + b.rand(600)
            fn = b.pick(self.doprun, self.poke, self.gas, self.selfie, self.hout, self.dominee)
            fn(t)
            b.auto_done(t)

    # ---- hooks ------------------------------------------------------------------------------------------------------------------------------------
    def on_update(self, t: float, dt: float) -> None:
        if not self.g:
            return
        w = self.wind()
        self.wheel += (0.4 + 2.2 * abs(w)) * dt * 3
        self.embers_update(t, dt)
        self.hoenders_update(t, dt)
        self.hadeda_update(t, dt)
        self.sk_update(t)
        self.chase_update(t)
        self.auto(t, dt)

    def hook_scenery(self, t: float) -> None:
        if not self.g:
            return
        self.draw_scenery(t)
        self.draw_donkie(t)
        self.draw_hoenders(t)
        self.draw_hadeda(t)
        self.draw_jakkals(t)

    def hook_actors(self, t: float) -> None:
        b = self.b
        if not self.g:
            return
        if "dominee" in b.P:
            b.draw_guy("dominee", t)
        self.draw_sleep(t)

    def hook_front(self, t: float) -> None:
        if not self.g:
            return
        self.draw_embers(t)
        self.draw_can(t)
        self.draw_poke(t)
        self.draw_flash(t)

    def hook_status(self, t: float) -> list:
        if "windpomp" in self.g and self.weer is not None and self.weer.live_label:
            return [[7.5, "windpomp %d rpm" % int(4 + 20 * abs(self.wind()))]]
        return []

    def hook_boot(self) -> list:
        return [["w", "plaas: windpomp, dam, kraal en hek gemonteer; skape getel: almal daar"],
                ["w", "diere: hoenders, 1 donkie, hadedas, jakkals (nag) en wagter (pid 104)"]]

    def install(self) -> None:
        b = self.b
        b.GUY["dominee"] = {"rest": DOMINEE, "act": DOMINEE, "act_len": 1,
                            "eyes": [2, 5, {"open": "(o o)", "shut": "(- -)", "left": "(oo )", "right": "( oo)",
                                            "wide": "(O O)", "laugh": "(^ ^)"}],
                            "mouth": [3, 6, "\\_/", "\\o/"], "mcol": ".", "head": 7}
        b.NAME["dominee"] = "die dominee"
        b.WHO["P"] = "dominee"
        b.MARK["pl_bring"] = self.mark_bring
        b.MARK["pl_poke"] = self.mark_poke
        b.MARK["pl_fetch"] = self.mark_fetch
        b.MARK["pl_selfie"] = self.mark_selfie
        C = b.COND
        C["pl_nag"] = lambda: self.night() and not self.wet()
        C["pl_dag"] = lambda: not self.night() and not self.wet()
        C["pl_wind"] = lambda: abs(self.wind()) > 1.0
        C["pl_dam"] = lambda: bool(self.weer and self.weer.w.get("wet", 0) > 0.5)
        C["pl_droog"] = lambda: bool(self.weer and self.weer.w.get("wet", 0) < 0.05 and self.weer.live_label)
        b.TALK.extend(list(x) for x in banter.PL_TALK)
        old_f = b.KEY.get("f")

        def fan(t: float) -> None:
            if old_f:
                old_f(t)
            self.fan_burst(t)

        b.KEY["f"] = fan
        b.hook("layout", self.on_layout)
        b.hook("update", self.on_update)
        b.hook("scenery", self.hook_scenery)
        b.hook("actors", self.hook_actors)
        b.hook("front", self.hook_front)
        b.hook("status", self.hook_status)
        b.hook("boot", self.hook_boot)
        b.key("a", "die dominee kom op die verkeerde oomblik / the dominee arrives", self.dominee)
        b.key("i", "'n selfie, almal leun in / a selfie", self.selfie)
        b.key("u", "Jannie gaan haal hout / fetches wood", self.hout)
        b.key("p", "iemand pook Koos se vuur / pokes the fire", self.poke)
        b.key("z", "gas teen hout, die argument / gas vs wood", self.gas)
        b.key("e", "'n dier nou: hoenders, donkie, hadeda, jakkals / a critter now", self.critter_now)
        b.key("5", "Wagter steel Jannie se dop / steals the dop", self.sleep_steal)
        b.key("6", "Jannie bring Oom 'n koue een / the dop run", self.doprun)
