"""40-dokter -- Dokter Disk, grappe and tricks (lekker's fragment 40, dk_).

Dokter Disk (x): about 20 s after the start, then every 24 hours of running, and whenever x is pressed, a doctor
in a white coat -- head mirror, a cyan stethoscope, a bag with a red cross -- walks in and listens to the host's
disks: at the host's tower on wide screens, or at a little stack of drive boxes he brings along where there is no
tower.  A bedside monitor shows an ECG trace per disk; the verdict comes in a bubble and in the kernel log, and a
sick disk brings a red alarm, a wall(1) broadcast and wide eyes.

Here he READS ONLY: the SMART health comes from vuurwag's probe (smartctl -a, already read for the snapshot) and he
never starts a self-test.  --no-disks keeps him away.
Grappe (j): a deck of braai jokes, told by the okes, laughter after.
Tricks: 1 Koos's double flip (or his 1995 story), 2 Sakkie crushes a can on his forehead, 3 Jannie falls off the
koelboks, 4 the brakkie plays dead.  All of them only on a key.  Also: banter about disks, backups and the
dokter.  Speaker letter X.
"""
from __future__ import annotations

import math
from typing import Any, Callable

from . import banter
from .art import BAKKIE, BRAAI, DOG, DOG_RUN, DOG_TROT, GUY, KOOS_FLIP, SAK_SIP, TOWER
from .buf import Sprite, mirror_text, sprite
from .core import Braai, meat_col

PI = math.pi

# ---- the art ------------------------------------------------------------------------------------------------------
ART_STAND = r"""
       _
    .-(O)-.
     (o o)
      \_/
   .-'\ /'-.
  / | \Y/ | \
  | |  o  | |
 _n_|     | |
|_+_|_____|_|
    (__|__)
"""[1:]
MASK_STAND = """
       W
    wwWWWww


   WWWcWcWWW
  W W cCc W W
  W W  C  W W
 yyyW     W W
 yRyyWWWWWW W
    yyyyyyy
"""[1:]
ART_WALK = (r"""
       _
    .-(O)-.
     (o o)
      \_/
   .-'\ /'-.
  / | \Y/ | \
  | |  o  | |
 _n_|     | |
|_+_|_   _|_|
   (__/ \__)
"""[1:], r"""
       _
    .-(O)-.
     (o o)
      \_/
   .-'\ /'-.
  / | \Y/ | \
  | |  o  | |
  _n_     | |
 |_+_|____|_|
     (_|_)
"""[1:])
MASK_WALK = ("""
       W
    wwWWWww


   WWWcWcWWW
  W W cCc W W
  W W  C  W W
 yyyW     W W
 yRyyWW   WWW
   yyyy yyyy
"""[1:], """
       W
    wwWWWww


   WWWcWcWWW
  W W cCc W W
  W W  C  W W
  yyy     W W
 yyRyyWWWWW W
     yyyyy
"""[1:])
ART_CARRY = (r"""
       _
    .-(O)-.
     (o o)
      \_/
   .-'\ /'-.
  /._______.\
  |         |
 _n_
|_+_|
   (__/ \__)
"""[1:], r"""
       _
    .-(O)-.
     (o o)
      \_/
   .-'\ /'-.
  /._______.\
  |         |
 _n_
|_+_|
     (_|_)
"""[1:])
MASK_CARRY = """
       W
    wwWWWww


   WWWcWcWWW
  WWwwwwwwwWW
  W         W
 yyy
 yRy
   yyyyyyyyy
"""[1:]
ART_OVER = r"""
       _
    .-(O)-.
     (o o)
      \_/
   .-'\ /'-.
   / | Y | \
   \_|_o_|_/

 _n_
|_+_|
"""[1:]
MASK_OVER = """
       W
    wwWWWww


   WWWcWcWWW
   W W c W W
   WWWWCWWWW

 yyy
 yRy
"""[1:]
ART_LISTEN = r"""
       _
    .-(O)-.
     (o o)
      \_/
    .-\ /-.
 o==='\Y/ |\
      |   | |
      |   |_n_
      |___|+_|
      (_|_)
"""[1:]
MASK_LISTEN = """
       W
    wwWWWww


    WWcWcWW
 CcccWcCcW WW
      W   W W
      W   Wyyy
      WWWWyRy
      yyyyy
"""[1:]
_MIR = {"/": "\\", "\\": "/", "(": ")", ")": "(", "[": "]", "]": "[", "<": ">", ">": "<", "{": "}", "}": "{"}


def mirror15(txt: str, mask: bool = False) -> str:
    out = []
    for line in txt.split("\n"):
        if line == "":
            out.append("")
            continue
        if len(line) == 1:
            out.append(line)
            continue
        r = line.ljust(15)[::-1]
        if not mask:
            r = "".join(_MIR.get(c, c) for c in r)
        out.append(r)
    return "\n".join(out)


def pair(art: str, mask: str) -> dict[str, Sprite]:
    return {"l": sprite(art, mask, "W"), "r": sprite(mirror15(art), mirror15(mask, True), "W")}


STAND = pair(ART_STAND, MASK_STAND)
WALK = [pair(ART_WALK[i], MASK_WALK[i]) for i in (0, 1)]
CARRY = [pair(ART_CARRY[i], MASK_CARRY) for i in (0, 1)]
OVER = pair(ART_OVER, MASK_OVER)
LISTEN = pair(ART_LISTEN, MASK_LISTEN)
TIPCOL = 1

SAK_LIFT = sprite(r"""
[#]   ___
 \\ =[___]
  \\ (o o)
   \\ \_/
   .\'   '-.
    |     | \
    |     | |
    |_____|
    |  |  |
    (__|__)
"""[1:], """
YYY   BBB
 BB BBBBBB
  BB
   BB
   BBBBBBBBB
    BBBBBBB B
    BBBBBBB B
    BBBBBBB
    wwwwwww
    yyyyyyy
"""[1:], ".")
SAK_BONK = sprite(r"""
      ___
 >=<=[___]
  \\ (o o)
   \\ \_/
   .\'   '-.
    |     | \
    |     | |
    |_____|
    |  |  |
    (__|__)
"""[1:], """
      BBB
 YYYBBBBBB
  BB
   BB
   BBBBBBBBB
    BBBBBBB B
    BBBBBBB B
    BBBBBBB
    wwwwwww
    yyyyyyy
"""[1:], ".")
JAN_TIP = sprite(r"""
   ___
 _(___)_
  (O O)
   \o/
.-'   '-.
/ |     | \
| |     | |[#]
_|_|_____|_|_
|    ICE    |
|___________|
"""[1:], """
   ccc
 ccccccc


RRRRRRRRR
R RRRRRRR R
R RRRRRRR RYYY
yyyyyyyyyyyyy
C    WWW    C
CCCCCCCCCCCCC
"""[1:], ".")
JAN_DOWN_MASK = """




yyyyyyyyyyy
yyyyyyyyyyy
yyyyyyyyyyyy
ccccccccccccc
C    WWW    C
CCCCCCCCCCCCC
"""[1:]
JAN_DOWN = [sprite(a, JAN_DOWN_MASK, ".") for a in (r"""




  __     __
 (__\   /__)
     \ /
_____/_\_____
|    ICE    |
|___________|
"""[1:], r"""




   __   __
  (__\ /__)
      V
_____/_\_____
|    ICE    |
|___________|
"""[1:])]
JAN_UPPOSE = sprite(r"""
     ___
   _(___)_
 \  (o o)  /
  \  \o/  /
   \'   '/
    |   |
    |   |
_____________
|    ICE    |
|___________|
"""[1:], """
     ccc
   ccccccc
 R         R
  R       R
   RRRRRRR
    RRRRR
    RRRRR
ccccccccccccc
C    WWW    C
CCCCCCCCCCCCC
"""[1:], ".")
HAT = sprite("  ___\n_(___)_", None, "c")
DOG_SIDE = sprite(r"""


 ________
(x'')____\\/_/_>~
"""[1:], "\n\nWWW", "Y")
DOG_DEAD = [sprite(a, "\n\n\nWWW", "Y") for a in (r"""
   , ,  , ,
   | |  | |
 __|_|__|_|_
(x'')_______)~
"""[1:], r"""
   , ,   ,,
   | |  //
 __|_|_//___
(x'')_______)~
"""[1:])]

ECG = {"ok": "__/\\_/\\_______", "sick": "_/\\/\\_/\\/\\/\\_/\\__/\\/\\/\\/\\_", "sleep": "_____________z_",
       "skip": "- - - - - - ", "wait": ". . . . . . ", "warm": "__/\\_/\\__/\\___"}
ECG_COL = {"ok": "G", "sick": "R", "sleep": "c", "skip": "w", "wait": "w", "warm": "Y"}


def short_name(name: str) -> str:
    name = name.replace("/", "")
    if len(name) > 6:
        name = name[:3] + name[-3:]
    return name


class Dokter:
    """disks_fn() -> list of dicts {name, st (ok|sick|skip|sleep), temp, why, hot} from the probe, or None when the
    probe has not reported yet."""

    def __init__(self, b: Braai, disks_fn: Callable[[], list[dict] | None] | None = None, no_disks: bool = False) -> None:
        self.b = b
        self.disks_fn = disks_fn
        self.off = "nodisks" if no_disks else ""
        self.v: dict[str, Any] = {}
        self.g: dict[str, Any] = {}
        self.disk: dict[str, dict] = {}
        self.order: list[str] = []
        self.next: float | None = None
        self.want = 0.0
        self.later: list[tuple[float, Callable]] = []
        self.logq: list[tuple[str, bool]] = []
        self.tr: dict = {}
        self.flips = 0
        self.joke_bag: list[int] = []
        self.install()

    # ---- the disks, from the probe ------------------------------------------------------------------------------------------
    def read_disks(self) -> str:
        """Take the probe's SMART facts: 'ok' when there is a list, 'blind' when the probe is unprivileged, 'none' when
        nothing has arrived."""
        got = self.disks_fn() if self.disks_fn else None
        if got is None:
            return "none"
        self.order = []
        self.disk = {}
        for d in got[:16]:
            nm = short_name(d["name"])
            if nm in self.disk:
                nm = f"disk{len(self.order)}"
            self.order.append(nm)
            self.disk[nm] = {"st": d["st"], "temp": d.get("temp"), "why": (d.get("why") or "")[:40], "hot": d.get("hot", False)}
        return "blind" if any(d["st"] == "blind" for d in got) else "ok"

    # ---- the status line ----------------------------------------------------------------------------------------------------------
    def hook_status(self, t: float) -> list:
        if self.v and self.v["kind"] == "check" and self.v["phase"] in ("in", "hi", "listen"):
            return []
        sick = sum(1 for n in self.order if self.disk[n]["st"] == "sick")
        ok = sum(1 for n in self.order if self.disk[n]["st"] == "ok")
        if sick:
            return [[2, f"disks: {sick} siek!"]]
        if ok:
            return [[6, f"disks: {ok} ok"]]
        return []

    # ---- where the dokter works on this screen -------------------------------------------------------------------------------------
    def place(self) -> None:
        b = self.b
        self.g = {}
        if "base" not in b.P:
            return
        top = b.P["top"]
        occ: dict[tuple[int, int], int] = {}
        dog: dict[tuple[int, int], int] = {}

        def mark(h: dict, spr: Sprite, x0: int, y0: int, wt: int) -> None:
            for sy, sx, txt, _c in spr.segs:
                for i in range(len(txt)):
                    k = (x0 + sx + i, y0 + sy)
                    h[k] = h.get(k, 0) + wt

        for who in ("koos", "sak", "jan"):
            if who in b.P:
                for d in (-1, 1):
                    mark(occ, GUY[who]["rest"], b.P[who][0] + d, b.P[who][1], 4)
                mark(occ, GUY[who]["rest"], b.P[who][0], b.P[who][1], 21)
        mark(occ, BRAAI, b.P["braai"][0], b.P["braai"][1], 10)
        if "tower" in b.P:
            mark(occ, TOWER, b.P["tower"][0], b.P["tower"][1], 3)
        if "bakkie" in b.P:
            mark(occ, BAKKIE, b.P["bakkie"][0], b.P["bakkie"][1], 1)
        if "tree" in b.P:
            mark(occ, b.P["tree"][0], b.P["tree"][1], b.P["tree"][2], 1)
        if "dog" in b.P:
            mark(occ, DOG[0], b.P["dog"][0], b.P["dog"][1], 2)
            mark(dog, DOG[0], b.P["dog"][0], b.P["dog"][1], 2)

        def cost(h: dict, spr: Sprite, x0: int, y0: int) -> float:
            c = 0.0
            for sy, sx, txt, _col in spr.segs:
                y = y0 + sy
                for i in range(len(txt)):
                    x = x0 + sx + i
                    c += 1000 if (x < 0 or x >= b.COLS) else h.get((x, y), 0)
            return c

        best = None
        for side in ("l", "r"):
            for x in range(-2, b.COLS - 12):
                c = cost(occ, STAND[side], x, top) + abs(x + 7 - b.COLS / 2) / b.COLS
                if best is None or c < best[0]:
                    best = (c, x, side)
        _c, x, side = best
        self.g = {"mode": "stack", "kx": x, "kside": side, "kdog": cost(dog, STAND[side], x, top) > 0}
        self.g.update(x=x, side=side, dog=self.g["kdog"])
        if "tower" not in b.P:
            return
        tx = b.P["tower"][0]
        best = None
        for side in ("l", "r"):
            tc = TIPCOL if side == "l" else 14 - TIPCOL
            for tip in range(tx + 2, tx + 10):
                c = cost(occ, LISTEN[side], tip - tc, top) + abs(tip - tx - 6) / 10 + (20 if side == "r" else 0)
                if best is None or c < best[0]:
                    best = (c, tip - tc, side)
        _c, x, side = best
        self.g.update(mode="tower", x=x, side=side, dog=cost(dog, LISTEN[side], x, top) > 0)

    # ---- the visit ----------------------------------------------------------------------------------------------------------------------
    def quiet(self, t: float) -> bool:
        return self.b.calm(t) and not self.talking()

    def talking(self) -> bool:
        b = self.b
        return bool(b.SAYS or b.talk_q or b.WALL_Q or b.wall_up(b.T))

    @staticmethod
    def lst(*n: str) -> str:
        n = list(n)
        return n[0] if len(n) < 2 else ", ".join(n[:-1]) + " en " + n[-1]

    def log(self, msg: str, quiet: bool = False) -> None:
        if self.v and self.v["kind"] == "check" and self.v["phase"] in ("in", "hi", "listen"):
            if len(self.logq) < 40:
                self.logq.append((msg, quiet))
        else:
            self.b.logmsg(msg, quiet)

    def visit(self, t: float, kind: str, auto: bool) -> bool:
        b = self.b
        if self.v or "base" not in b.P or not self.g or not b.claim("dokter", t, 40):
            return False
        mode = "stand" if kind == "nope" else self.g["mode"]
        x, side, dog = (self.g["x"], self.g["side"], self.g["dog"]) if mode == "tower" else (self.g["kx"], self.g["kside"], self.g["kdog"])
        out = -16 if x + 7 < b.COLS / 2 else b.COLS + 1
        self.v = {"kind": kind, "mode": mode, "phase": "in", "pt": t, "x": float(out), "to": x, "exit": out, "auto": auto,
                  "side": side, "carry": mode == "stack", "stack": 0, "dog": 0.0, "mon": None, "mon_n": 0, "rv": 0.0, "said": 0}
        b.P["dokter"] = [out, b.P["top"]]
        if "dokter" not in b.CAST:
            b.CAST.append("dokter")
        b.ST["dokter"] = {"blink_at": t + 1, "blink_to": 0, "act_at": t + 99, "act_to": 0, "talk_to": 0, "look": 0,
                          "face_to": 0, "face": "open", "asleep": 0, "doze_at": 1e12}
        if dog and "dog" in b.P and not b.DOG_AWAY and not b.RAID:
            b.DOG_AWAY = 1
            self.v["dog"] = t
            b.say_now(t, b.pick(*banter.DK_VET))
        self.logq = []
        if kind == "check":
            self.v["read"] = self.read_disks()
            if auto or (self.next or 0) < t + 600:
                self.next = t + 86400
            b.logmsg("smart: dokter disk op sy " + ("daaglikse rondte" if auto else "huisbesoek"), True)
        return True

    def phase(self, t: float, p: str) -> None:
        self.v["phase"], self.v["pt"], self.v["said"] = p, t, 0

    def visit_end(self, t: float) -> None:
        b = self.b
        b.CAST = [w for w in b.CAST if w != "dokter"]
        b.P.pop("dokter", None)
        b.ST.pop("dokter", None)
        self.mon(False)
        if self.v.get("dog"):
            b.DOG_AWAY = 0
        self.v = {}
        for msg, q in self.logq:
            b.logmsg(msg, q)
        self.logq = []
        b.release("dokter")
        b.auto_done(t)

    def hello(self, t: float) -> None:
        b = self.b
        k = self.v["kind"]
        if k == "check" and self.v["auto"]:
            b.say_now(t, ("X", banter.DK_HELLO_AUTO.format(what="die host" if self.v["mode"] == "tower" else "die disks")))
            return
        if k == "check":
            b.say_now(t, ("X", banter.DK_HELLO_CALL))
            return
        if self.off == "blind":
            b.say_now(t, *banter.DK_HELLO_BLIND)
            return
        b.say_now(t, *banter.DK_HELLO_NOPE)

    def verdict(self, t: float) -> list:
        b = self.b
        n = self.order
        if self.v.get("read") == "blind" or (not n and self.v.get("read") == "none"):
            return list(banter.DK_HELLO_BLIND)
        if not n:
            return list(banter.DK_HELLO_NODISKS)
        by: dict[str, list[str]] = {}
        for nm in n:
            by.setdefault(self.disk[nm]["st"], []).append(nm)
        sick, ok, zzz, skip = by.get("sick", []), by.get("ok", []), by.get("sleep", []), by.get("skip", [])
        hot = [nm for nm in ok if self.disk[nm]["hot"]]
        out: list = []
        if sick:
            d = sick[0]
            why = self.disk[d]["why"] or "sleg"
            out.append(("X", (f"Oei! {d} is siek: {why}." if len(sick) == 1 else "Oei! " + self.lst(*sick) + " is siek.") + " !dk_alarm"))
            out.append(banter.DK_SICK_ASK)
            out.append(banter.DK_SICK_ANS)
            b.wall(f"Dokter Disk: {d} is siek -- {why}. Maak 'n backup!")
        elif len(ok) == len(n):
            out.append(("X", banter.DK_HEALTHY))
            out.append(("X", f"{n[0]} is kerngesond." if len(n) == 1 else f"Al {len(n)} disks is gesond."))
        elif ok:
            out.append(("X", self.lst(*ok) + " is gesond soos 'n perd."))
        if hot and not sick:
            out.append(("X", f"{hot[0]} is bietjie koorsig ({int(self.disk[hot[0]]['temp'])}C). Hou hom koel."))
        if zzz:
            out.append(("X", self.lst(*zzz) + " slaap. Rus is goeie medisyne."))
        if skip:
            out.append(("X", self.lst(*skip) + " praat nie met my nie."))
        out.append(("X", "Geen selftoets vanaand nie: ek lees net, ek prik nie."))
        if len(ok) == len(n) and len(out) < 5:
            out.append(banter.DK_SALUTE)
        return out

    def summary(self) -> str:
        n = self.order
        sick = [nm for nm in n if self.disk[nm]["st"] == "sick"]
        ok = sum(1 for nm in n if self.disk[nm]["st"] == "ok")
        if not n:
            return "smart: dokter disk het geen disks gekry nie"
        if sick:
            return f"smart: {len(sick)} van {len(n)} disks siek ({', '.join(sick)}), backup aanbeveel"
        return f"smart: {ok} van {len(n)} disks gesond" + (" (soos 'n perd)" if ok == len(n) else "")

    def visit_update(self, t: float, dt: float) -> None:
        b = self.b
        v = self.v
        st = b.ST.get("dokter")
        if not st:
            return
        s = t - v["pt"]
        ph = v["phase"]
        sd = v["side"]
        b.claim("dokter", t, 30)
        st["act_at"] = t + 99
        if ph in ("in", "out"):
            to = v["to"] if ph == "in" else v["exit"]
            d = (to > v["x"]) - (to < v["x"])
            v["x"] += d * 14 * dt
            if (to - v["x"]) * d <= 0:
                v["x"] = float(to)
            b.P["dokter"][0] = int(v["x"] + 0.5)
            walk = CARRY if v["carry"] else WALK
            st["pose"], st["pose_to"] = walk[int(t * 6) % 2][sd], t + 0.3
            if d:
                b.set_face("dokter", "left" if d < 0 else "right", t + 0.3)
            if v["x"] != to:
                return
            if ph == "out":
                if v["dog"]:
                    self.phase(t, "dog")
                else:
                    self.visit_end(t)
                return
            v["stack"] = v["carry"]
            v["carry"] = 0
            b.set_face("dokter", "open", 0)
            self.phase(t, "hi")
            self.hello(t)
        stand = LISTEN[sd] if v["mode"] == "tower" else STAND[sd]
        if ph == "hi":
            st["pose"], st["pose_to"] = stand, t + 0.3
            if not ((s > 1.2 and not self.talking()) or s > 14):
                return
            if v["kind"] == "check":
                self.phase(t, "listen")
                v["rv"] = t
                self.mon(True, t)
                b.say_now(t, ("X", "Haal diep asem..."))
            else:
                self.phase(t, "out")
                self.mon(False)
                v["carry"] = v["stack"]
                v["stack"] = 0
            return
        if ph == "listen":
            st["pose"], st["pose_to"] = (stand if v["mode"] == "tower" else OVER[sd]), t + 0.3
            if s > 3.6 and not v["said"] and not self.talking():
                v["said"] = 1
                b.say_now(t, b.pick(*banter.DK_QUIPS))
            if not ((s >= 6 and t >= self.reveal_at(len(self.order) - 1) + 1 and not self.talking()) or s > 25):
                return
            v["rv"] = 0
            self.phase(t, "say")
            for msg, _q in self.logq:
                b.logmsg(msg, True)
            self.logq = []
            b.say_now(t, *self.verdict(t))
            b.logmsg(self.summary())
            return
        if ph == "say":
            st["pose"], st["pose_to"] = stand, t + 0.3
            if not ((s > 2 and not self.talking()) or s > 30):
                return
            self.phase(t, "out")
            self.mon(False)
            v["carry"] = v["stack"]
            v["stack"] = 0
            return
        if ph == "dog" and s >= 2.6:
            self.visit_end(t)

    def reveal_at(self, i: int) -> float:
        return (self.v.get("rv") or 0) + 1.6 + 1.1 * i

    def shown(self, i: int, t: float) -> bool:
        return not self.v.get("rv") or t >= self.reveal_at(i)

    def maybe_visit(self, t: float) -> None:
        b = self.b
        if self.want:
            if t > self.want:
                self.want = 0
            elif self.quiet(t):
                if self.visit(t, "nope" if self.off else "check", False):
                    self.want = 0
            return
        if self.off:
            return
        if self.next is not None and t >= self.next and (b.auto_ok(t) if self.next > b.BOOT_END + 21 else self.quiet(t)):
            self.visit(t, "check", True)

    # ---- the bedside monitor --------------------------------------------------------------------------------------------------------------
    @staticmethod
    def trace(kind: str, t: float, w: int, ph: int) -> str:
        p = ECG[kind]
        o = int(t * 10 + ph) % len(p)
        return (p * (w // len(p) + 2))[o:o + w]

    def state(self, i: int, t: float) -> str:
        if i >= len(self.order):
            return "wait"
        d = self.disk.get(self.order[i])
        if not d or not self.shown(i, t):
            return "wait"
        if d["st"] == "ok" and d["hot"]:
            return "warm"
        return d["st"]

    def mon_size(self) -> tuple[int, int, int, int, int]:
        n = len(self.order) or 1
        mx = 6 if self.b.ROWS >= 30 else 4
        if n > mx:
            n = mx
        tc = 5 if self.b.COLS >= 100 else 0
        tw = 14 if self.b.COLS >= 100 else 12
        return tw + tc + 17, n + 2, tw, n, tc

    def mon(self, on: bool, t: float = 0.0) -> None:
        b = self.b
        old = self.v.get("mon") if self.v else None
        if old is not None:
            b.AVOID = [a for a in b.AVOID if a is not old]
        if self.v:
            self.v["mon"] = None
        if not on or "base" not in b.P:
            return
        w, h, _tw, _n, _tc = self.mon_size()
        cx = b.P["tower"][0] + 6 if self.v["mode"] == "tower" else self.v["to"] + 7
        ymax = max(0, b.P["top"] - 6 - h)
        box = None
        for y in range(ymax, -1, -1):
            for d in range(b.COLS + 1):
                for x in (cx - w // 2 - d, cx - w // 2 + d):
                    if x < 0 or x + w > b.COLS:
                        continue
                    if any(x - 1 <= a[2] and x + w >= a[0] and y - 1 <= a[3] and y + h >= a[1] for a in b.AVOID):
                        continue
                    box = [x, y, x + w - 1, y + h - 1]
                    break
                if box:
                    break
            if box:
                break
        if not box:
            x = cx - w // 2
            if x + w > b.COLS:
                x = b.COLS - w
            if x < 0:
                x = 0
            box = [x, 0, x + w - 1, h - 1]
        self.v["mon"] = box
        self.v["mon_n"] = len(self.order)
        b.AVOID.append(box)

    def draw_mon(self, t: float) -> None:
        b = self.b
        bx_ = self.v.get("mon")
        if not bx_:
            return
        if self.v["mon_n"] != len(self.order):
            self.mon(True, t)
        bx_ = self.v["mon"]
        x, y = bx_[0], bx_[1]
        w, h, tw, n, tc = self.mon_size()
        st = [self.state(i, t) for i in range(max(1, len(self.order)))]
        alarm = any(s == "sick" for s in st)
        bc = "R" if (alarm and int(t * 3) % 2) else "w"
        put = b.buf.put
        put(x, y, "." + "-" * (w - 2) + ".", bc)
        put(x + 2, y, "[", "w")
        b.buf.plot(x + 3, y, "+", "R")
        put(x + 4, y, "] DOKTER DISK", "W")
        for i in range(n):
            yy = y + 1 + i
            put(x, yy, "|" + " " * (w - 2) + "|", bc)
            if not self.order:
                put(x + 2, yy, "scan", "w")
                put(x + 9, yy, self.trace("wait", t, tw, 0), "w")
                continue
            if i == n - 1 and len(self.order) > n:
                put(x + 2, yy, f"+{len(self.order) - n + 1} meer...", "w")
                continue
            nm, k = self.order[i], st[i]
            d = self.disk[nm]
            put(x + 2, yy, nm, "W")
            put(x + 9, yy, self.trace(k, t, tw, i * 3), ECG_COL[k])
            txt, c = (("ok", "G") if k == "ok" else ("warm", "Y") if k == "warm" else ("SIEK!", "h" if int(t * 4) % 2 else "R") if k == "sick"
                      else ("zzz", "c") if k == "sleep" else ("??", "w") if k == "skip" else ("." * (1 + int(t * 3) % 3), "w"))
            put(x + 10 + tw + tc, yy, txt, c)
            if tc and d["temp"] is not None and k != "wait":
                put(x + 10 + tw, yy, "%3dC" % int(d["temp"]), "r" if k == "sick" else "g")
        put(x, y + h - 1, "'" + "-" * (w - 2) + "'", bc)

    def draw_stack(self, x: int, yb: int, t: float, lid: bool) -> None:
        b = self.b
        nm = self.order or ["sda", "sdb", "nvme0"]
        if lid:
            b.buf.put(x + 1, yb - 3, "_______", "w")
        for i in range(3):
            yy = yb - 2 + i
            b.buf.put(x, yy, "[", "w")
            b.buf.put(x + 8, yy, "]", "w")
            if i >= len(nm):
                b.buf.put(x + 1, yy, "  --   ", "w")
                continue
            k = "wait" if self.v["phase"] == "in" else self.state(i, t)
            led = ("G" if k == "ok" else ("R" if int(t * 4) % 2 else "r") if k == "sick" else "Y" if k == "warm" else "c" if k == "sleep"
                   else "w" if k == "skip" else ("Y" if b.rand() < 0.5 else "y"))
            b.buf.put(x + 1, yy, "%-6s" % nm[i], "W")
            b.buf.plot(x + 7, yy, "o", led)

    def draw_dog(self, t: float) -> None:
        b = self.b
        if not (self.v.get("dog") and "dog" in b.P):
            return
        dx, dy = b.P["dog"]
        if self.v["phase"] == "dog":
            f = min(1.0, (t - self.v["pt"]) / 2.5)
            b.buf.draw(DOG_TROT[int(t * 6) % 2], int(b.COLS + 1 + (dx - b.COLS - 1) * f), dy)
            return
        s = t - self.v["dog"]
        if s > 3:
            return
        x = dx if s < 0.5 else int(dx + (s - 0.5) * 30)
        b.buf.draw(DOG[0] if s < 0.5 else DOG_RUN[int(s * 8) % 2], x, dy)
        if s < 1.2:
            b.buf.put(dx + 2, dy - 2, "Woef?!", "W")

    # ---- tricks ----------------------------------------------------------------------------------------------------------------------------------
    def refuse(self, t: float, *ex: Any) -> bool:
        b = self.b
        if not b.talk_q and not b.wall_up(t):
            b.say_now(t, *(ex if ex else (b.pick(*banter.DK_NO),)))
        return False

    def trick(self, t: float, name: str, ln: float, *steps: tuple) -> bool:
        b = self.b
        if self.tr or self.v or not b.claim("dk_trick", t, ln + 12):
            return self.refuse(t)
        self.tr = {"name": name, "t0": t, "len": ln, "steps": sorted(steps, key=lambda s: s[0]), "i": 0, "who": {},
                   "chop": None, "dog": 0, "draw": None, "back": None, "tick": None}
        return True

    def pose(self, who: str, spr: Sprite, t: float, secs: float, noface: bool = False) -> None:
        st = self.b.ST.get(who)
        if not st:
            return
        st["pose"], st["pose_to"], st["noface"] = spr, t + secs, 1 if noface else 0
        if st["act_at"] < t + 4:
            st["act_at"] = t + 4
        self.tr["who"][who] = 1

    def trick_update(self, t: float) -> None:
        if not self.tr:
            return
        s = t - self.tr["t0"]
        while self.tr and self.tr["i"] < len(self.tr["steps"]) and self.tr["steps"][self.tr["i"]][0] <= s:
            self.tr["i"] += 1
            self.tr["steps"][self.tr["i"] - 1][1](t)
        if not self.tr:
            return
        if self.tr["tick"]:
            self.tr["tick"](t, s)
        if (s >= self.tr["len"] and not self.talking()) or s >= self.tr["len"] + 10:
            self.trick_end()

    def trick_end(self) -> None:
        b = self.b
        if not self.tr:
            return
        for who in self.tr["who"]:
            st = b.ST.get(who)
            if st:
                for k in ("pose", "pose_to", "noface", "dx", "dy"):
                    st.pop(k, None)
                st["pose_to"] = 0
        if self.tr["chop"] is not None and b.MEAT and b.MEAT[0] is self.tr["chop"]:
            self.tr["chop"]["gone"] = 0
        if self.tr["dog"]:
            b.DOG_AWAY = 0
        self.tr = {}
        b.release("dk_trick")

    def faces(self, mood: str, until: float, *who: str) -> None:
        for w in who:
            if w in self.b.P:
                self.b.set_face(w, mood, until)

    def trick_koos(self, t: float) -> None:
        b = self.b
        m = b.MEAT[0] if b.MEAT else None
        self.flips += 1
        if (self.flips - 1) % 2 or not m or m["gone"] or b.MEAT_STATE != "cooking":
            self.trick_story(t)
            return

        def s1(t2: float) -> None:
            b.say_now(t2, banter.DK_FLIP_GO)

        def s2(t2: float) -> None:
            if not (b.MEAT and b.MEAT[0] is m and not m["gone"]):
                self.trick_end()
                return
            self.tr["chop"], self.tr["fly"] = m, t2
            m["gone"] = 1
            self.pose("koos", KOOS_FLIP, t2, 0.7)
            self.faces("dk_up", t2 + 2.4, "koos", "sak", "jan")
            b.logmsg("grid0: tjop gelanseer, dubbel-draai")

        def s3(t2: float) -> None:
            m["gone"] = 0
            self.tr.pop("fly", None)
            for _ in range(8):
                b.SPARKS.append([b.P["braai"][0] + 6 + b.rand(4), b.P["braai"][1] + 1, (b.rand() - 0.5) * 6, -(2 + b.rand(4)), 0])
            self.pose("koos", KOOS_FLIP, t2, 1.2)
            b.CHOP = not b.CHOP
            self.faces("laugh", t2 + 3, "sak", "jan")
            b.say_now(t2, *banter.DK_FLIP_END)

        if not self.trick(t, "flip", 6.5, (0, s1), (1.4, s2), (3.8, s3)):
            return
        self.tr["draw"] = self.draw_flip

    def apogee(self) -> int:
        h = self.b.P["braai"][1] + 2 - 1
        return 9 if h > 9 else h

    def draw_flip(self, t: float) -> None:
        b = self.b
        if not (self.tr.get("fly") and self.tr["chop"]):
            return
        f = (t - self.tr["fly"]) / 2.4
        if f < 0 or f > 1:
            return
        bx, by = b.P["braai"]
        h = int(self.apogee() * math.sin(PI * f) + 0.5)
        s = ("(==)", " || ", "(##)", " || ")[int(f * 8) % 4]
        x = bx + (6 if h >= 2 else 5)
        c = meat_col(self.tr["chop"]["done"])
        for i, ch in enumerate(s):
            if ch != " ":
                b.buf.plot(x + i, by + 2 - h, ch, c)
        if 0.4 < f < 0.6:
            b.buf.plot(x + 1 + b.irand(2), by + 1 - h, "*", "Y")

    def trick_story(self, t: float) -> None:
        b = self.b

        def s1(t2: float) -> None:
            self.pose("koos", KOOS_FLIP, t2, 3)
            b.say_now(t2, *banter.DK_STORY)

        self.trick(t, "story", 10, (0, s1))

    def mark_chop(self, t: float, who: list) -> None:
        if not (self.tr and self.tr["name"] == "story"):
            return
        self.tr["fall"] = t
        self.tr["draw"] = self.draw_1995
        self.faces("dk_up", t + 1.6, "koos", "sak", "jan")

    def draw_1995(self, t: float) -> None:
        b = self.b
        if not (self.tr.get("fall") and "braai" in b.P):
            return
        f = (t - self.tr["fall"]) / 1.5
        bx, by = b.P["braai"]
        if f > 1:
            if not self.tr.get("landed"):
                self.tr["landed"] = 1
                for _ in range(12):
                    b.SPARKS.append([bx + 11 + b.rand(5), by + 1, (b.rand() - 0.5) * 8, -(3 + b.rand(5)), 0])
                b.SMOKE.append([bx + 13, by + 1, -1.2, 0, 4])
                b.logmsg("grid0: tjop van 1995 het geland (hy is nog rou)")
            return
        y = int((by + 2) * f * f)
        b.buf.put(bx + 12, y, "(==)", "M")
        if y > 0:
            for i in (0, 1):
                b.buf.plot(bx + 13 + i, y - 1, "'", "w")

    def trick_sak(self, t: float) -> None:
        b = self.b
        if "sak" not in b.P:
            return

        def s1(t2: float) -> None:
            b.say_now(t2, *banter.DK_BONK)

        def s2(t2: float) -> None:
            self.pose("sak", SAK_SIP, t2, 1.2)

        def s3(t2: float) -> None:
            self.pose("sak", SAK_LIFT, t2, 0.5)

        def s4(t2: float) -> None:
            self.pose("sak", SAK_BONK, t2, 0.5)
            b.set_face("sak", "shut", t2 + 0.5)
            self.tr["bonk"] = t2
            b.logmsg("dop: sakkie het blikkie #%d platgedruk (voorkopmetode)" % (1 + b.DOPS.get("sak", 0)))

        def s5(t2: float) -> None:
            self.tr["dizzy"] = t2
            b.set_face("sak", "dk_dizzy", t2 + 3.5)
            b.say_now(t2, *banter.DK_BONK_END)

        if not self.trick(t, "bonk", 6.5, (0, s1), (0.8, s2), (2.0, s3), (2.5, s4), (3.0, s5)):
            return
        self.tr["draw"] = self.draw_bonk

        def tick(t2: float, s: float) -> None:
            dz = self.tr.get("dizzy")
            b.ST["sak"]["dx"] = int(1.4 * math.sin((t2 - dz) * 4)) if (dz and t2 < dz + 3.5) else 0
            self.tr["who"]["sak"] = 1

        self.tr["tick"] = tick

    def draw_bonk(self, t: float) -> None:
        b = self.b
        x, y = b.P["sak"][0] + b.ST["sak"].get("dx", 0), b.P["sak"][1]
        if self.tr.get("bonk") and t < self.tr["bonk"] + 0.6:
            b.buf.put(x - 4, y, "KRAK!", "Y")
            b.buf.plot(x + 1, y, "*", "W")
        dz = self.tr.get("dizzy")
        if not dz:
            return
        if not b.ST["sak"].get("pose_to", 0) > t:
            b.buf.put(x + 1, y + 6, ">=<", "Y")
        if t > dz + 3.5:
            return
        for k in range(3):
            a = (t - dz) * 5 + k * 2.09
            b.buf.plot(x + 7 + int(4.5 * math.cos(a)), y - 1 + int(1.2 * math.sin(a) + 0.5), "*+."[k], "YWY"[k])

    def trick_jan(self, t: float) -> None:
        b = self.b
        if "jan" not in b.P:
            self.refuse(t, banter.DK_JAN_HOME)
            return
        b.wake("jan", t)

        def s1(t2: float) -> None:
            b.say_now(t2, *banter.DK_FALL)

        def s2(t2: float) -> None:
            self.pose("jan", JAN_TIP, t2, 0.5, True)

        def s3(t2: float) -> None:
            self.tr["down"] = t2
            self.faces("wide", t2 + 1.5, "koos", "sak")
            b.logmsg("koelboks0: jannie het afgeval (die dops is reg)")

        def s4(t2: float) -> None:
            self.tr.pop("down", None)
            self.pose("jan", JAN_UPPOSE, t2, 1.8)
            b.set_face("jan", "laugh", t2 + 1.8)
            b.ST["jan"]["dy"] = -1
            b.say_now(t2, *banter.DK_FALL_END)

        def s5(t2: float) -> None:
            b.ST["jan"]["dy"] = 0

        if not self.trick(t, "fall", 6.5, (0, s1), (1.6, s2), (2.1, s3), (4.1, s4), (4.4, s5)):
            return

        def tick(t2: float, s: float) -> None:
            if self.tr.get("down"):
                self.pose("jan", JAN_DOWN[int(t2 * 5) % 2], t2, 0.2, True)

        def draw(t2: float) -> None:
            s = t2 - self.tr["t0"] - 2.1
            if s < 0 or s > 2:
                return
            b.buf.draw(HAT, b.P["jan"][0] + 2, b.P["jan"][1] - int(4 * math.sin(PI * s / 2) + 0.5))

        self.tr["tick"] = tick
        self.tr["draw"] = draw

    def trick_dog(self, t: float) -> None:
        b = self.b
        if not ("dog" in b.P and not b.DOG_AWAY and not b.RAID):
            self.refuse(t, banter.DK_DOG_WHERE)
            return

        def s1(t2: float) -> None:
            b.say_now(t2, *banter.DK_DEAD)

        def s2(t2: float) -> None:
            b.DOG_AWAY = 1
            self.tr["dog"], self.tr["dead"] = 1, t2

        def s3(t2: float) -> None:
            b.say_now(t2, *banter.DK_DEAD_MID)
            b.logmsg("wagter[104]: toestand D -> Z (speel dood)", True)

        if not self.trick(t, "dead", 8.5, (0, s1), (1.4, s2), (2.6, s3)):
            return
        self.tr["back"] = self.draw_dead

    def mark_alive(self, t: float, who: list) -> None:
        b = self.b
        if not (self.tr and self.tr["name"] == "dead"):
            return
        b.DOG_AWAY = 0
        self.tr["dog"] = 0
        self.tr["woof"] = t
        self.tr["draw"] = self.draw_woof
        self.later.append((t + 0.8, lambda t2: self.faces("laugh", t2 + 3, "koos", "sak", "jan")))
        b.logmsg("wagter[104]: hervat (wors bespeur)")

    def draw_dead(self, t: float) -> None:
        b = self.b
        if not (self.tr.get("dead") and b.DOG_AWAY and "dog" in b.P):
            return
        s = t - self.tr["dead"]
        x, y = b.P["dog"]
        b.buf.draw(DOG_SIDE if s < 0.4 else DOG_DEAD[1 if 2.2 < s < 2.5 else 0], x, y)

    def draw_woof(self, t: float) -> None:
        b = self.b
        if self.tr.get("woof") and t < self.tr["woof"] + 1.6 and "dog" in b.P:
            b.buf.put(b.P["dog"][0] + 1, b.P["dog"][1] - 2, "Woef! Woef!", "W")

    # ---- grappe ---------------------------------------------------------------------------------------------------------------------------------
    def mark_laugh(self, t: float, who: list) -> None:
        tell = set(who)
        self.faces("laugh", t + 3, *[w for w in ("koos", "sak", "jan", "dokter") if w not in tell])
        self.later.append((t + 1.2, lambda t2: self.faces("laugh", t2 + 2, *[w for w in ("koos", "sak", "jan") if w in tell])))

    def mark_alarm(self, t: float, who: list) -> None:
        self.faces("wide", t + 4, "koos", "sak", "jan")
        self.b.wake("jan", t, "siek disk")

    def joke(self, t: float) -> None:
        b = self.b
        if not b.calm(t):
            self.refuse(t)
            return
        for _ in range(len(banter.DK_JOKES)):
            if not self.joke_bag:
                self.joke_bag = list(range(len(banter.DK_JOKES)))
                b.rng.shuffle(self.joke_bag)
            ex = banter.DK_JOKES[self.joke_bag.pop(0)]
            if not b.fresh(ex, t) or not b.build_exchange(ex):
                continue
            b.said_at[b.ex_key(ex)] = t
            b.say_now(t, *ex)
            return

    # ---- hooks and keys ------------------------------------------------------------------------------------------------------------------------
    def on_layout(self, t: float) -> None:
        b = self.b
        self.trick_end()
        self.place()
        if not self.v:
            return
        if self.v["phase"] in ("out", "dog") or not self.g:
            self.visit_end(t)
            return
        tower = self.v["mode"] != "stand" and self.g["mode"] == "tower"
        self.v["mode"] = "tower" if tower else "stand" if self.v["mode"] == "stand" else "stack"
        self.v["to"], self.v["side"] = (self.g["x"], self.g["side"]) if tower else (self.g["kx"], self.g["kside"])
        self.v["x"] = float(self.v["to"])
        self.v["exit"] = -16 if self.v["to"] + 7 < b.COLS / 2 else b.COLS + 1
        self.v["stack"] = 1 if (self.v["mode"] == "stack" and (self.v["stack"] or self.v["carry"])) else 0
        self.v["carry"] = 0
        b.P["dokter"] = [self.v["x"], b.P["top"]]
        if self.v.get("mon"):
            self.mon(True, t)

    def on_update(self, t: float, dt: float) -> None:
        if self.next is None:
            self.next = t + 20
        if self.v:
            self.visit_update(t, dt)
        else:
            self.maybe_visit(t)
        self.trick_update(t)
        due = [l for l in self.later if l[0] <= t]
        self.later = [l for l in self.later if l[0] > t]
        for _at, fn in due:
            fn(t)

    def hook_scenery(self, t: float) -> None:
        b = self.b
        if not (self.v and self.v["mode"] == "tower" and "tower" in b.P and self.v["phase"] in ("listen", "say")):
            return
        x, y = b.P["tower"]
        sick = any(self.disk[n]["st"] == "sick" for n in self.order)
        show_sick = sick and not self.v["rv"]
        b.buf.put(x + 2, y + 1, self.trace("sick" if show_sick else "ok", t, 8, 0), "R" if show_sick else "G")
        if b.POWER:
            b.buf.plot(x + 4, y + 2, "o", "Y" if b.rand() < 0.5 else "y")

    def hook_actors(self, t: float) -> None:
        b = self.b
        if not (self.v and "dokter" in b.P):
            return
        b.draw_guy("dokter", t)
        x = b.P["dokter"][0] + 3
        if self.v["carry"]:
            self.draw_stack(x, b.P["top"] + 8, t, False)
        elif self.v["stack"]:
            self.draw_stack(x, b.P["base"], t, self.v["phase"] != "listen")
        self.draw_dog(t)

    def hook_front(self, t: float) -> None:
        b = self.b
        if self.v and self.v.get("mon") and not b.wall_up(t):
            self.draw_mon(t)
        if self.tr and self.tr.get("draw"):
            self.tr["draw"](t)

    def hook_boot(self) -> list:
        if self.off == "nodisks":
            return [["w", "smart: --no-disks, dokter van diens af"]]
        got = self.disks_fn() if self.disks_fn else None
        if got is None:
            return [["w", "smart: wag vir die probe (dokter op roep, net lees)"]]
        if any(d["st"] == "blind" for d in got):
            return [["w", "smart: probe sien nie die disks nie (root nodig), dokter op roep"]]
        n = len(got)
        return [["w", f"smart: {n} disk{'s' if n != 1 else ''} gevind (dokter op roep, net lees, geen selftoets)"]]

    def key_x(self, t: float) -> None:
        b = self.b
        if self.v and self.v["phase"] not in ("out", "dog"):
            if not self.talking():
                b.say_now(t, banter.DK_HERE)
            return
        if self.visit(t, "nope" if self.off else "check", False):
            return
        self.want = t + 90
        if not self.v and not b.talk_q:
            b.say_now(t, banter.DK_CALLING)

    def install(self) -> None:
        b = self.b
        b.GUY["dokter"] = {"rest": STAND["l"], "act": STAND["l"], "act_len": 1,
                           "eyes": [2, 5, {"open": "(o o)", "shut": "(- -)", "left": "(oo )", "right": "( oo)",
                                           "wide": "(O O)", "laugh": "(^ ^)"}],
                           "mouth": [3, 6, "\\_/", "\\o/"], "mcol": ".", "head": 7}
        b.NAME["dokter"] = "dokter disk"
        b.WHO["X"] = "dokter"
        G = b.GUY
        G["koos"]["eyes"][2]["dk_up"] = "('  ')"
        G["koos"]["eyes"][2]["dk_dizzy"] = "(@  @)"
        for w in ("sak", "jan"):
            G[w]["eyes"][2]["dk_up"] = "(' ')"
            G[w]["eyes"][2]["dk_dizzy"] = "(@ @)"
        b.MARK["dk_chop"] = self.mark_chop
        b.MARK["dk_alive"] = self.mark_alive
        b.MARK["dk_laugh"] = self.mark_laugh
        b.MARK["dk_alarm"] = self.mark_alarm
        C = b.COND
        C["dk_ok"] = lambda: bool(self.order) and not any(self.disk[n]["st"] == "sick" for n in self.order)
        C["dk_sick"] = lambda: any(self.disk[n]["st"] == "sick" for n in self.order)
        C["dk_hot"] = lambda: any(self.disk[n]["hot"] for n in self.order)
        C["dk_duty"] = lambda: not self.off
        b.TALK.extend(list(x) for x in banter.DK_TALK)
        b.hook("layout", self.on_layout)
        b.hook("update", self.on_update)
        b.hook("scenery", self.hook_scenery)
        b.hook("back", lambda t: self.tr["back"](t) if (self.tr and self.tr.get("back")) else None)
        b.hook("actors", self.hook_actors)
        b.hook("front", self.hook_front)
        b.hook("status", self.hook_status)
        b.hook("boot", self.hook_boot)
        b.key("x", "Dokter Disk: kyk nou na die disks (lees net) / check the disks", self.key_x)
        b.key("j", "'n grap / a joke", self.joke)
        b.key("1", "Koos wys af / shows off", self.trick_koos)
        b.key("2", "Sakkie se blikkie-truuk / can trick", self.trick_sak)
        b.key("3", "Jannie leun agteroor / leans back", self.trick_jan)
        b.key("4", "Wagter, speel dood! / play dead", self.trick_dog)
