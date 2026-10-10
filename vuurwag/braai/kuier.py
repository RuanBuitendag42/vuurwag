"""30-kuier: visitors, Eskom and the neighbourhood (lekker's fragment 30, kv_).

  t  Tannie Sarie walks over from the house with pap en sous, a slaai, a melktert or koeksisters, has opinions
     about the meat and the koelboks, and walks back
  o  Oom Faan pulls up in his red bakkie (TOET-TOET!), climbs out with ice, tells one tall story and drives off
     in a cloud of dust
  l  loadshedding: Eskom switches the town off block by block, the stars come out and a generator drones;
     press again and the power returns.  It also strikes by itself every 10-20 minutes (and when the node
     rebooted: Eskom was here).
  h  hout: Jannie (or Koos) throws a log on the fire -- sparks; too much wood and it flares up, and Koos
     douses it with his dop
  m  meer vleis: sosaties, mielies, braaibroodjies, snoek, tjops en wors

Always there: a little town on the horizon (rows base-3 .. base-1, behind everything, in the margins beside the
group -- none at 80 columns) with lit windows, street lights, a church, a water tower, a cell mast and the kafee;
its lights follow DAYLIGHT.  Now and then a bakkie or a minibus taxi on the far road, hidden while it passes
behind the group.  Tannie, Oom, a log and a new menu also come by themselves once in a while.  New speakers: T, O.
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable

from . import banter
from .art import BAKKIE, BRAAI, DOG, JAN_REST, KOOS_FLIP, KOOS_REST, SAK_REST, TOWER
from .buf import Sprite, mirror_text, sprite
from .core import Braai, meat_col

PI = math.pi


def rows(s: str) -> list[str]:
    return s[1:].split("\n")[:-1] if s.startswith("\n") else s.split("\n")


def spr_rows(art: list[str], mask: list[str | None], default: str = ".") -> Sprite:
    return sprite("\n".join(art), "\n".join(m if m is not None else "" for m in mask), default)


# ---- Tannie Sarie: a bun, glasses, a magenta dress, a white apron --------------------------------------------------
TAN_ART = rows(r"""
      (@)
    .-"""+'"""'+r"""-.
   ( [o-o] )
    '. - .'
   .-'"-"'-.
  / /  ~  \ \
 ( (\@@@@@/) )
  `-\_____/-'
   /_:_:_:_\
    (_) (_)
""")
TAN_MASK = rows("""
      www
    wwwwwww
   w       w
    ww R ww
   MMMMMMMMM
  M M  w  M M
 M McWWWWWcM M
  MMcccccccMM
   MWMWMWMWM
    yyy yyy
""")
TAN_ARMS: dict[str, tuple[list[int], list[str], list[str]]] = {
    "free": ([5, 6, 7], ["  / |     | \\", " ( (|  _  |) )", "  `-|_____|-'"],
             ["  M W     W M", " M MW  W  WM M", "  MMWWWWWWWMM"]),
    "wave": ([2, 3, 4, 5, 6, 7], ["   ( [o-o] )o", "    '. - .' |", "   .-'\"-\"'-.|", "  / |     |/", " ( (|  _  |", "  `-|_____|"],
             ["   w       w.", "    ww R ww M", "   MMMMMMMMMM", "  M W     WM", " M MW  W  W", "  MMWWWWWWW"]),
    "tongs": ([5, 6, 7], ["  / |     |`--==<", " ( (|  _  |", "  `-|_____|"],
              ["  M W     WMMMccc", " M MW  W  W", "  MMWWWWWWW"]),
    "click": ([5, 6, 7], ["  / |     |`--==-", " ( (|  _  |", "  `-|_____|"],
              ["  M W     WMMMccc", " M MW  W  W", "  MMWWWWWWW"]),
}
DISH = {
    "pap": ("@@@@@", "WWWWW", "~", "pap en sous", "\\@@@/", "cWWWc"),
    "slaai": ("%*%*%", "GRGRG", " ", "'n slaai", "\\%*%/", "cGRGc"),
    "melktert": (":.:.:", "YyYyY", " ", "'n melktert", "(:.:)", "yYyYy"),
    "koeksisters": ("8o8o8", "YyYyY", " ", "koeksisters", "(8o8)", "yYyYy"),
}
_TAN_SPR: dict[str, Sprite] = {}


def tan_spr(dish: str, arms: str, step: int) -> Sprite:
    key = f"{dish}/{arms}/{step}"
    s = _TAN_SPR.get(key)
    if s is not None:
        return s
    a = list(TAN_ART)
    m = list(TAN_MASK)
    if arms == "dish":
        top, tcol, steam = DISH[dish][:3]
        a[6] = a[6][:5] + top + a[6][10:]
        m[6] = m[6][:5] + tcol + m[6][10:]
        a[5] = a[5][:7] + steam + a[5][8:]
    else:
        rws, art, mask = TAN_ARMS[arms]
        for i, r in enumerate(rws):
            a[r] = art[i]
            m[r] = mask[i]
    if step:
        a[9], m[9] = "   (_)   (_)", "   yyy   yyy"
    s = _TAN_SPR[key] = spr_rows(a, m, ".")
    return s


# ---- Oom Faan: a wide hat, a grey moustache, khaki and a belly ---------------------------------------------------
OOM_ART = rows(r"""
       ____
    __/____\__
      (o  o)
     (~~~~~~)
  .-'`-.__.-`'-.
 / / .      . \ \
| |  (   .  )  | |
 \_\  '----'  /_/[#]
    |___/\___|
    (___)(___)
""")
OOM_MASK = rows("""
       yyyy
    yyyyyyyyyy

     WWWWWWWW
  wwwwwwwwwwwwww
 w wwYwwwwwwYw w
w w  wwwwwwww  w w
 www  yyyyyy  wwwYYY
    yyyyyyyyyy
    yyyyyyyyyy
""")
OOM_SIP = spr_rows(rows(r"""
       ____
    __/____\__
      (o  o)[#]
     (~~~~~~)//
  .-'`-.__.-'//
 / / .      .|
| |  (   .  )|
 \_\  '----' |
    |___/\___|
    (___)(___)
"""), rows("""
       yyyy
    yyyyyyyyyy
            YYY
     WWWWWWWWww
  wwwwwwwwwwwww
 w wwYwwwwwwYw
w w  wwwwwwwww
 www  yyyyyyw
    yyyyyyyyyy
    yyyyyyyyyy
"""), ".")
_OOM_SPR: dict[str, Sprite] = {}


def oom_spr(cooler: int, step: int) -> Sprite:
    key = f"{cooler}/{step}"
    s = _OOM_SPR.get(key)
    if s is not None:
        return s
    a = list(OOM_ART)
    m = list(OOM_MASK)
    if cooler:
        a[7], m[7] = " \\_\\  '----'  /_/_", " www  yyyyyy  wwwR"
        a[8], m[8] = "    |___/\\___| [__]", "    yyyyyyyyyy RRRR"
        a[9], m[9] = "    (___)(___) |__|", "    yyyyyyyyyy WWWW"
    if step:
        a[9] = a[9][:3] + "(___)  (___)" + a[9][14:]
        m[9] = m[9][:3] + "yyyyy  yyyyy" + m[9][14:]
    s = _OOM_SPR[key] = spr_rows(a, m, ".")
    return s


COOLER = sprite("[__]\n|__|", "RRRR\nWWWW", "W")

# Oom's red bakkie, drawn facing left; the mirror image faces right.
BAK_ART = r"""
          _____
    _____/ |   |____________
 __/   _   |   |   _        |
[=____/o\__|___|__/o\_______|]
      \_/         \_/
"""[1:]
BAK_MASK = """
          ccccc
    RRRRRc c   cRRRRRRRRRRRR
 RRR       c   c            r
wYRRRRWWWRRRRRRRRRWWWRRRRRRRRw
      WWW         WWW
"""[1:]
BAK_W, OOM_W = 30, 18
BAK = {-1: sprite(BAK_ART, BAK_MASK, "R"),
       1: sprite(mirror_text(BAK_ART, BAK_W, True), mirror_text(BAK_MASK, BAK_W, False), "R")}

KOOS_HIPS = sprite(r"""
      ____
    _|____|_
     (o  o)
      \ww/
   .-'`--'`-.
  /  |    |  \
  \__|_..._|__/
    |______|
    |__||__|
    (__)(__)
"""[1:], """
      yyyy
    yyyyyyyy

      yyyy
   GGGGGGGGGG
  GGGGGGGGGGGG
  GGGGGGGGGGGGG
    GGGGGGGG
    yyyyyyyy
    yyyyyyyy
"""[1:], ".")
KOOS_SPLASH = sprite(r"""
      ____     \#/
    _|____|_   //
     (o  o)   //
      \ww/   //
   .-'`--'`-.'
  / |      |
  \ |  ..  |
   \|______|
    |__||__|
    (__)(__)
"""[1:], """
      yyyy     YYY
    yyyyyyyy   GG
              GG
      yyyy   GG
   GGGGGGGGGGG
  G GGGGGGGG
  G GGGGGGGG
   GGGGGGGGG
    yyyyyyyy
    yyyyyyyy
"""[1:], ".")
KOOS_LOG = sprite(r"""
      ____     o==
    _|____|_   //
     (o  o)   //
      \ww/   //
   .-'`--'`-.'
  / |      |
  \ |  ..  |
   \|______|
    |__||__|
    (__)(__)
"""[1:], """
      yyyy     Yyy
    yyyyyyyy   GG
              GG
      yyyy   GG
   GGGGGGGGGGG
  G GGGGGGGG
  G GGGGGGGG
   GGGGGGGGG
    yyyyyyyy
    yyyyyyyy
"""[1:], ".")
JAN_UP = sprite(r"""
     ___
   _(___)_
    (o o)
     \_/
  .-'   '-.
 / |     | \
 | |     | |[#]
 |_|_____|_|
    |  |  |
____|  |  |____
|   |  |  |   |
|___(__|__)___|
"""[1:], """
     ccc
   ccccccc


  RRRRRRRRR
 R RRRRRRR R
 R RRRRRRR RYYY
 RRRyyyyyRRR
    wwwwww
yyyywwwwwwyyyy
C   wwwwww   C
CCCCyyyyyyCCCC
"""[1:], ".")
JAN_JUMP = sprite(r"""
     ___
   _(___)_
    (o o)
     \_/
\ .-'   '-. /
 \|       |/
  |       |
  |_______|
   /     \
  /_/   \_\

_____________
|    ICE    |
|___________|
"""[1:], """
     ccc
   ccccccc


R RRRRRRRRR R
 RRRRRRRRRRR
  RRRRRRRRR
  RRyyyyyRR
   wwwwwww
  yyy   yyy

yyyyyyyyyyyyy
C    WWW    C
CCCCCCCCCCCCC
"""[1:], ".")
JAN_LOG = sprite(r"""
     ___
   _(___)_
    (o o)o==
     \_/ //
  .-'   '//
 / |     |
 | |     |
_|_|_____|_
|    ICE    |
|___________|
"""[1:], """
     ccc
   ccccccc
         Yyy
         RR
  RRRRRRRRR
 R RRRRRRR
 R RRRRRRR
yyyyyyyyyyy
C    WWW    C
CCCCCCCCCCCCC
"""[1:], ".")

# ---- the town on the horizon -------------------------------------------------------------------------------------
TPL: dict[str, tuple[list[str], list[str]]] = {
    "house3": (["", "/^\\", "|o|"], ["", "bbb", "bWb"]),
    "house4": (["", "/\\/\\", "|oo|"], ["", "bbbb", "bWWb"]),
    "house5": (["", ".---.", "|o o|"], ["", "bbbbb", "bWbWb"]),
    "farm5": (["", "/^^^\\", "|o '|"], ["", "bbbbb", "bWbWb"]),
    "flats": ([" __ ", "|oo|", "|o:|"], [" bb ", "bWWb", "bWWb"]),
    "lamp": (["", "*", "|"], ["", "L", "b"]),
    "church": (["  +   ", " /^\\__", " |o|o|"], ["  C   ", " bbbbb", " bWbWb"]),
    "tower": (["(__)", " || ", " /\\ "], ["bbbb", " bb ", " bb "]),
    "mast": ([" * ", " A ", "/A\\"], [" R ", " b ", "bbb"]),
    "kafee": (["", " _____ ", "|KAFEE|"], ["", " bbbbb ", "bKKKKKb"]),
    "koop": (["", " ______ ", "|KO-OP |"], ["", " bbbbbb ", "bKKKKKKb"]),
}
CAR = {
    "taxi": {-1: ([" ____ ", "(o__o]"], [" WWWW ", "WwWWwr"]), 1: ([" ____ ", "[o__o)"], [" WWWW ", "rwWWwW"])},
    "bakkie": {-1: ([" _    ", "/_|__ ", "'o--o'"], ["", "", ""]), 1: (["    _ ", " __|_\\", "'o--o'"], ["", "", ""])},
}
PIECE: dict[str, tuple[str, str, str, list[str]]] = {
    "sosatie": ("-#o#", "-#*#", "-#o#*#o#-", ["-#o#", " #o ", "#*#-", " o# "]),
    "mielie": ("<::)", "<:;)", "<(::::::)", ["<::)", " :: ", "(::>", " :; "]),
    "broodjie": ("[==]", "[##]", "[=======]", ["[==]", " || ", "[##]", " || "]),
    "snoek": ("><'>", "<'><", "><((((('>", ["><'>", " >< ", "<'><", " >< "]),
}
STEP = [0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 1.05]
WOOD = ["kameeldoring", "rooikrans", "sekelbos", "mopanie", "wingerdstok", "bloekom", "swarthaak"]


def part_col(kind: str, ch: str, d: float) -> str:
    if kind == "sosatie":
        if ch == "#":
            return meat_col(d)
        if ch == "o":
            return "W" if d < 0.5 else "w" if d < 0.9 else "y"
        if ch == "*":
            return "Y" if d < 0.7 else "y"
        return "w"
    if kind == "mielie":
        if ch in "<>":
            return "G" if d < 0.5 else "g" if d < 0.9 else "y"
        return "Y" if d < 0.4 else ("y" if ch == ";" else "Y") if d < 0.8 else "y"
    if kind == "broodjie":
        if ch == "#":
            return "y" if d < 0.5 else "r"
        return "W" if d < 0.3 else "Y" if d < 0.7 else "y" if d < 1.05 else "r"
    return "C" if d < 0.3 else "c" if d < 0.6 else "Y" if d < 0.9 else "y"


class Kuier:
    def __init__(self, b: Braai) -> None:
        self.b = b
        self.want: dict[str, tuple[float, Callable]] = {}
        self.town: list[dict] = []
        self.gen: dict | None = None
        self.mast: dict | None = None
        self.town_runs: list[tuple] = []
        self.town_key = ""
        self.life = 0
        self.gx0, self.gx1 = 0, -1
        self.sx0, self.sx1 = 0, -1
        self.ls: dict[str, Any] = {"state": "off"}
        self.stars: list[list] = []
        self.bright: list[tuple] = []
        self.car: dict = {}
        self.car_next = 120 + b.rand(120)
        self.menu = -1
        self.drop: dict = {}
        self.batch_seen = 0
        self.pcol: dict[str, str] = {}
        self.throw: dict = {}
        self.logs: list[list] = []
        self.flare: dict = {}
        self.drops: list[list] = []
        self.woodtalk = list(banter.KV_WOODTALK)
        self.wood_last = "kameeldoring"
        self.tan: dict = {}
        self.dish: dict = {}
        self.jan_up = 0.0
        self.tongs = 0
        self.oom: dict = {}
        self.cooler: dict = {}
        self.toet: dict = {}
        self.dust: list[list] = []
        self.next = {"tannie": 900 + b.rand(900), "oom": 1500 + b.rand(1200), "wood": 480 + b.rand(420), "ls": 2400 + b.rand(3000)}
        self.flick = 0.0
        self.install()

    # ---- shared helpers ----------------------------------------------------------------------------------------------------------
    def idle(self, t: float) -> bool:
        b = self.b
        return not b.SAYS and not b.talk_q and not b.WALL_Q and not b.wall_up(t)

    def night(self) -> bool:
        return self.b.DAYLIGHT < 0.5

    def pose(self, who: str, spr: Sprite | None, t: float, dy: int = 0) -> None:
        s = self.b.ST.get(who)
        if not s:
            return
        if spr is not None:
            s["pose"], s["pose_to"], s["dy"], s["kv_posed"] = spr, t + 0.5, dy, 1
            if s["act_at"] < t + 2:
                s["act_at"] = t + 2
        elif s.get("kv_posed"):
            s.pop("pose", None)
            s.pop("kv_posed", None)
            s["pose_to"], s["dy"] = 0, 0

    def join(self, who: str, t: float, x: int, y: int) -> None:
        b = self.b
        b.ST[who] = {"blink_at": t + 1, "blink_to": 0, "act_at": t + 1e6, "act_to": 0, "talk_to": 0, "look": 0,
                     "face_to": 0, "face": "open", "asleep": 0, "doze_at": 1e9}
        b.P[who] = [x, y]
        if who not in b.CAST:
            b.CAST.append(who)

    def leave(self, who: str) -> None:
        b = self.b
        b.CAST = [w for w in b.CAST if w != who]
        b.P.pop(who, None)
        b.ST.pop(who, None)
        b.SAYS = [s for s in b.SAYS if s["who"] != who]

    def ask(self, what: str, t: float, start: Callable) -> None:
        b = self.b
        if start(t):
            return
        self.want[what] = (t + 150, start)
        if not b.SAYS and not b.talk_q and not b.wall_up(t):
            b.say_now(t, b.pick(*banter.KV_NO))
        b.logmsg(f"kuier: {what} in die tou, verhoog besig")

    # ---- the town ----------------------------------------------------------------------------------------------------------------------
    def band_ok(self, x: int) -> bool:
        return x < self.sx0 or x > self.sx1

    def bandput(self, x: int, y: int, txt: str, c: str) -> None:
        n = len(txt)
        put = self.b.buf.put
        if x < self.sx0:
            k = self.sx0 - x
            put(x, y, txt[: n if k > n else k], c)
        k = self.sx1 + 1 - x
        if k < 0:
            k = 0
        if k < n and x + n - 1 > self.sx1:
            put(x + k, y, txt[k:], c)

    def band_free(self, row: int | None = None) -> list[int]:
        b = self.b
        P = b.P
        base = P["base"]
        cov = [0] * b.COLS
        put = []
        for spr, pos in ((JAN_REST, P.get("jan")), (KOOS_REST, P.get("koos")), (SAK_REST, P.get("sak")), (BRAAI, P.get("braai")),
                         (DOG[0], P.get("dog")), (TOWER, P.get("tower")), (BAKKIE, P.get("bakkie"))):
            if pos:
                put.append((spr, pos[0], pos[1]))
        if "tree" in P:
            put.append((P["tree"][0], P["tree"][1], P["tree"][2]))
        for spr, x, y in put:
            for sy, sx, txt, _c in spr.segs:
                yy = y + sy
                if not ((yy == row) if row is not None else (yy == base - 2 or yy == base - 1)):
                    continue
                for cx in range(x + sx, x + sx + len(txt)):
                    if 0 <= cx < b.COLS:
                        cov[cx] = 1
        return cov

    def town_add(self, name: str, x: int, occ: list[int]) -> dict:
        b = self.b
        art, mask = TPL[name]
        y0 = b.P["base"] - 3
        bld: dict = {"x": x, "name": name, "segs": [], "wins": []}
        w = 0
        for r in range(3):
            a, m = art[r], mask[r] + " " * 12
            if len(a) > w:
                w = len(a)
            stripped = a.strip(" ")
            if not stripped:
                continue
            s = len(a) - len(a.lstrip(" "))
            txt = a.rstrip(" ")[s:]
            if True:
                for k, ch in enumerate(txt):
                    key = m[s + k]
                    if ch == " ":
                        continue
                    if key not in "WLRKC":
                        key = "b"
                    if key == "b":
                        bld["segs"].append((x + s + k, y0 + r, ch))
                    else:
                        bld["wins"].append({"x": x + s + k, "y": y0 + r, "ch": ch, "kind": key,
                                            "lit": (1 if b.rand() < 0.75 else 0) if key == "W" else 1,
                                            "col": ("Y" if b.rand() < 0.55 else "y") if key == "W" else "y" if key == "L"
                                            else "W" if key == "C" else "R"})
        row: dict[int, list] = {}
        for sx, sy, ch in bld["segs"]:
            row.setdefault(sy, []).append((sx, ch))
        runs = []
        for yy in sorted(row):
            run = None
            for cx, ch in sorted(row[yy]):
                if run and cx == run[0] + len(run[2]):
                    run[2] += ch
                else:
                    run = [cx, yy, ch]
                    runs.append(run)
        bld["segs"] = runs
        for cx in range(x - 1, x + w + 1):
            if 0 <= cx < b.COLS:
                occ[cx] = 1
        self.town.append(bld)
        return bld

    def town_build(self) -> None:
        b = self.b
        P = b.P
        self.town = []
        self.gen = None
        self.mast = None
        self.town_key = ""
        if not ("base" in P and P["base"] >= 12 and "koos" in P and "sak" in P):
            return
        COLS = b.COLS
        self.gx0, self.gx1 = (P["jan"] if "jan" in P else P["koos"])[0], P["sak"][0] + SAK_REST.w - 1
        self.sx0, self.sx1 = self.gx0, self.gx1
        cov = self.band_free()
        top = self.band_free(P["base"] - 3)
        for i in range(COLS):
            cov[i] = cov[i] or top[i]
        occ = [1 if self.gx0 - 1 <= x <= self.gx1 + 1 else 0 for x in range(COLS)]
        if self.gx0 - 1 < 3:
            for x in range(0, max(0, self.gx0 - 1)):
                occ[x] = 1
        if COLS - self.gx1 - 2 < 3:
            for x in range(self.gx1 + 1, COLS):
                occ[x] = 1
        runs = []
        s = None
        for x in range(COLS + 1):
            open_ = x < COLS and not cov[x] and not occ[x]
            if open_ and s is None:
                s = x
            elif not open_ and s is not None:
                runs.append([s, x - s])
                s = None
        runs.sort(key=lambda r: -r[1])
        for lm in ("kafee", "house5", "church", "tower", "mast", "koop"):
            w = max(len(TPL[lm][0][2]), len(TPL[lm][0][1]))
            r = next((r for r in runs if r[1] >= w + 2), None)
            x = None
            if r:
                x = r[0] + (r[1] - w) // 2
                runs = [q for q in runs if q is not r] + [[r[0], x - 1 - r[0]], [x + w + 1, r[0] + r[1] - x - w - 1]]
                runs.sort(key=lambda q: -q[1])
            else:
                for _ in range(40):
                    tr = b.irand(COLS - w + 1)
                    if any(occ[i] for i in range(tr, tr + w)):
                        continue
                    x = tr
                    break
            if x is None:
                continue
            bld = self.town_add(lm, x, occ)
            if lm == "house5":
                self.gen = bld
                if bld["wins"]:
                    bld["wins"][0]["lit"] = 1
            if lm == "mast":
                self.mast = next((w for w in bld["wins"] if w["kind"] == "R"), None)
        fill = ["house3", "house3", "house4", "house5", "farm5", "flats", "lamp", "lamp"]
        x = b.irand(3)
        while x < COLS - 2:
            name = fill[b.irand(len(fill))]
            w = len(TPL[name][0][2])
            if x + w <= COLS and not any(occ[i] for i in range(x, x + w)):
                self.town_add(name, x, occ)
                x += w + 2 + b.irand(4) + (5 + b.irand(10) if b.rand() < 0.2 else 0)
            else:
                x += 1
        self.town.sort(key=lambda bl: bl["x"])

    # ---- loadshedding -----------------------------------------------------------------------------------------------------------------
    def ls_start(self, t: float, auto: bool = False) -> bool:
        b = self.b
        if self.ls["state"] != "off":
            return False
        stage = b.pick(2, 2, 3, 4, 4, 4, 5, 6)
        lt = time.localtime(time.time() + 7200 + b.irand(3600))
        till = "%02d:%02d" % (lt.tm_hour, 0 if lt.tm_min < 30 else 30)
        msg = f"Eskom: Stage {stage} beurtkrag vanaf nou tot {till}. Ons vra om verskoning."
        self.ls = {"state": "pending", "t0": t, "stage": stage, "till": till, "msg": msg}
        b.wall(msg)
        b.logmsg(f"eskom: stage {stage} beurtkrag geskeduleer, NOU")
        return True

    def ls_dark(self, t: float) -> None:
        b = self.b
        L = self.ls
        L.update(state="dark", t1=t, end=t + 110 + b.rand(80), gen_at=t + 6 + b.rand(4), mast_at=t + 30 + b.rand(25), gen=0, mast_dead=0)
        b.POWER = 0
        o = b.rand(b.COLS)
        for bl in self.town:
            bl["off"] = t + 0.6 + 0.5 * int(abs(bl["x"] - o) / 9) + b.rand(0.1)
        L["fade"] = t + 1 + 0.5 * int(b.COLS / 9)
        for s in self.stars:
            s[4] = t + 1.5 + b.rand(6)
        b.logmsg(f"eskom: stage {L['stage']} beurtkrag, town0 offline tot {L['till']}")
        b.PRIO.append(list(b.pick(*banter.KV_LS_DARK)))

    def ls_restore(self, t: float) -> None:
        b = self.b
        self.ls.update(state="restore", t2=t, gen=0)
        b.POWER = 1
        for bl in self.town:
            for w in bl["wins"]:
                w["on"] = t + 0.3 + b.rand(4)
        b.logmsg("eskom: krag terug, stage 0 (vir nou)")
        b.say_now(t, *b.pick(*banter.KV_LS_BACK))

    def ls_key(self, t: float) -> None:
        st = self.ls["state"]
        if st == "off":
            self.ls_start(t)
        elif st == "dark":
            self.ls_restore(t)
        else:
            self.b.logmsg(f"eskom: besig ({st}), probeer netnou weer")

    def ls_update(self, t: float) -> None:
        b = self.b
        L = self.ls
        st = L["state"]
        if st == "pending":
            shown = b.WALL and b.WALL["msg"] == L["msg"] and b.WALL["until"] > t
            if shown or t - L["t0"] > 25:
                self.ls_dark(t)
        elif st == "dark":
            if not L["gen"] and t > L["gen_at"] and self.gen:
                L["gen"] = 1
                b.logmsg("town0: 1 kragopwekker gestart (brrrrr)", True)
            if not L["mast_dead"] and t > L["mast_at"]:
                L["mast_dead"] = 1
                b.logmsg("mast0: battery pap, 0 strepies")
            if t > L["end"]:
                self.ls_restore(t)
        elif st == "restore" and t - L["t2"] > 6:
            self.ls = {"state": "off"}

    def win_lit(self, w: dict, bl: dict | None, t: float) -> int:
        st = self.ls["state"]
        if w["kind"] == "R":
            if st == "dark" and self.ls.get("mast_dead"):
                return 0
            return 1 if (t * 0.8 - int(t * 0.8)) < 0.35 else 0
        if not self.night():
            return 0
        if st == "dark":
            if self.ls.get("gen") and self.gen and bl is self.gen and bl["wins"] and w is bl["wins"][0]:
                return 1
            return w["lit"] if t < bl.get("off", 0) else 0
        if st == "restore":
            d = t - w.get("on", 0)
            if d < 0:
                return 0
            return (w["lit"] if int(d * 14) % 3 else 0) if d < 0.45 else w["lit"]
        return w["lit"]

    def town_state(self, t: float) -> str:
        st = self.ls["state"]
        k = f"{st}/{self.life}/{self.sx0}/{self.sx1}/{int(self.night())}"
        if st == "dark":
            k += f"/{self.ls['gen']}"
            if t < self.ls["fade"]:
                k += "/" + str(int(t * 10))
        elif st == "restore":
            k += "/" + str(int(t * 10))
        return k

    def town_paint(self, t: float) -> None:
        b = self.b
        ch: dict[int, dict[int, str]] = {}
        co: dict[int, dict[int, str]] = {}
        for bl in self.town:
            for x, y, txt in bl["segs"]:
                for i, c in enumerate(txt):
                    if self.band_ok(x + i):
                        ch.setdefault(y, {})[x + i] = c
                        co.setdefault(y, {})[x + i] = "b"
            for w in bl["wins"]:
                if w["kind"] == "R" or not self.band_ok(w["x"]):
                    continue
                on = self.win_lit(w, bl, t)
                c = "b" if not on else "y" if (w["kind"] == "W" and self.ls["state"] == "dark") else w["col"]
                ch.setdefault(w["y"], {})[w["x"]] = w["ch"]
                co.setdefault(w["y"], {})[w["x"]] = c
        self.town_runs = []
        for y in sorted(ch):
            run = None
            for x in sorted(ch[y]):
                if x < 0 or x >= b.COLS:
                    continue
                if run and x - (run[0] + len(run[2])) < 2:
                    gap = x - (run[0] + len(run[2]))
                    run[2] += " " * gap + ch[y][x]
                    run[3] += "b" * gap + co[y][x]
                else:
                    run = [x, y, ch[y][x], co[y][x]]
                    self.town_runs.append(run)

    def draw_town(self, t: float) -> None:
        b = self.b
        key = self.town_state(t)
        if key != self.town_key:
            self.town_paint(t)
            self.town_key = key
        for x, y, txt, col in self.town_runs:
            b.buf.blit(x, y, txt, col)
        if self.mast and self.band_ok(self.mast["x"]):
            on = self.win_lit(self.mast, None, t)
            b.buf.plot(self.mast["x"], self.mast["y"], "*" if on else ".", "R" if on else "b")
        if self.ls["state"] == "dark" and self.ls.get("gen") and self.gen:
            x = self.gen["x"] + (int(t * 7) % 2)
            self.bandput(x, b.P["base"] - 3, ("brrrr", "rrrrr", "brrr")[int(t * 5) % 3], "w")

    def draw_dark_sky(self, t: float) -> None:
        b = self.b
        if not (self.ls["state"] == "dark" and t - self.ls["t1"] > 1):
            return
        buf = b.buf
        if b.SKY["dust"]:
            for x, y, c in self.bright:
                if buf.atr[y][x] == "b" and buf.scr[y][x] == c:
                    buf.plot(x, y, c, "w")
        if not b.SKY["stars"]:
            return
        for x, y, ph, sp, at in self.stars:
            if t < at or buf.scr[y][x] != " ":
                continue
            v = math.sin(t * sp + ph)
            buf.plot(x, y, "*" if v > 0.9 else ".", "W" if v > 0.2 else "w")

    # ---- traffic on the far road --------------------------------------------------------------------------------------------------
    def car_update(self, t: float, dt: float) -> None:
        b = self.b
        if not self.car:
            if not (t > self.car_next and "base" in b.P):
                return
            d = -1 if b.rand() < 0.5 else 1
            kind = "taxi" if b.rand() < 0.6 else "bakkie"
            self.car = {"kind": kind, "dir": d, "x": -8.0 if d > 0 else b.COLS + 1.0, "v": 3 + b.rand(2.5),
                        "hoot": [t + 4 + b.rand((b.COLS + 8) / 4.5) for _ in range(2)] if kind == "taxi" else [], "toet": 0.0}
            b.logmsg("road0: minibus-taxi op die verre pad (toet toet)" if kind == "taxi"
                     else "road0: bakkie op die verre pad, 1 kopligte werk", True)
            return
        c = self.car
        c["x"] += c["dir"] * c["v"] * dt
        for i, h in enumerate(c["hoot"]):
            if h and t > h:
                if 0 < c["x"] < b.COLS - 6:
                    c["toet"] = t + 1.4
                c["hoot"][i] = 0
        if c["x"] < -10 or c["x"] > b.COLS + 2:
            self.car = {}
            self.car_next = t + 180 + b.rand(180)

    def draw_car(self, t: float) -> None:
        b = self.b
        if not self.car:
            return
        kind, d = self.car["kind"], self.car["dir"]
        art, mask = CAR[kind][d]
        x = int(self.car["x"])
        y = b.P["base"] - len(art)
        default = "W" if kind == "taxi" else "c"
        for r, a in enumerate(art):
            for i, ch in enumerate(a):
                if ch == " " or not self.band_ok(x + i):
                    continue
                k = (mask[r] + " " * 12)[i]
                b.buf.plot(x + i, y + r, ch, k if k != " " else default)
        if self.night():
            hx = x - 1 if d < 0 else x + len(art[-1])
            self.bandput(hx - 2 if d < 0 else hx, b.P["base"] - 1, "--=" if d < 0 else "=--", "y")
        if self.car["toet"] > t and kind == "taxi":
            self.bandput(x - 1, b.P["base"] - len(art) - 1, "toet toet", "w")

    # ---- what goes on the grid ------------------------------------------------------------------------------------------------------
    def piece_draw(self, kind: str, txt: str, d: float, x: int, y: int) -> None:
        q = 0
        while q < len(STEP) - 1 and d >= STEP[q + 1]:
            q += 1
        key = f"{kind}|{txt}|{q}"
        c = self.pcol.get(key)
        if c is None:
            c = self.pcol[key] = "".join(part_col(kind, ch, STEP[q]) for ch in txt)
        if " " not in txt:
            self.b.buf.blit(x, y, txt, c)
            return
        for i, ch in enumerate(txt):
            if ch != " ":
                self.b.buf.plot(x + i, y, ch, c[i])

    def menu_put(self, t: float, i: int) -> None:
        b = self.b
        mn = banter.KV_MENU[i]
        b.BATCH += 1
        lay = [(5, 4), (10, 9), (20, 4)] if len(b.MEAT) != 4 else [(3, 4), (8, 9), (17, 4), (21, 4)]
        kinds = list(mn["kinds"])
        while len(kinds) < len(lay):
            kinds.append("chop")
        b.MEAT = [{"x": x, "w": w, "kind": kinds[j], "done": b.rand(0.05), "gone": 0} for j, (x, w) in enumerate(lay)]
        b.MEAT_STATE, b.SERVE_AT = "cooking", 0
        for m in b.MEAT[1:]:
            m["gone"] = 1
        self.drop = {"t0": t, "pieces": list(b.MEAT)}
        self.batch_seen = b.BATCH
        b.logmsg(f"grid0: {mn['log']} op die rooster")

    def meat_key(self, t: float) -> bool:
        b = self.b
        if not b.calm(t) or self.drop:
            return False
        if b.MEAT_STATE == "gaar":
            b.say_now(t, b.pick(*banter.KV_MEAT_WAIT))
            return True
        self.menu = (self.menu + 1) % len(banter.KV_MENU)
        self.menu_put(t, self.menu)
        b.start_act("koos", t, salute=True, length=1.2)
        b.say_now(t, *banter.KV_MENU[self.menu]["talk"])
        return True

    def meat_update(self, t: float) -> None:
        b = self.b
        if self.drop:
            done = True
            for i, m in enumerate(self.drop["pieces"]):
                if i == 0 or not m["gone"]:
                    continue
                if t >= self.drop["t0"] + 0.25 * i + 0.3:
                    if i < len(b.MEAT) and b.MEAT[i] is m:
                        m["gone"] = 0
                    bx, by = b.P["braai"]
                    b.SMOKE.append([bx + m["x"] + 2, by + 1, -(0.8 + b.rand(0.6)), 0, 2 + b.rand(2)])
                else:
                    done = False
            if done:
                self.drop = {}
        if b.BATCH != self.batch_seen:
            self.batch_seen = b.BATCH
            if b.BATCH > 1 and len(b.MEAT) >= 3 and b.MEAT[0]["kind"] == "chop" and b.rand() < 0.25 and b.calm(t):
                i = b.irand(len(banter.KV_MENU) - 1)
                self.menu_put(t, i)
                b.PRIO.append(list(banter.KV_MENU[i]["talk"]))

    def draw_meat(self, t: float) -> None:
        b = self.b
        if "braai" not in b.P:
            return
        bx, by = b.P["braai"]
        flying = b.koos_flying(t)
        for i, m in enumerate(b.MEAT):
            big = m.get("w", 4) == 9
            if m["gone"]:
                if not (self.drop and any(p is m for p in self.drop["pieces"])):
                    continue
                f = (t - self.drop["t0"] - 0.25 * i) / 0.3
                if f < 0 or f >= 1:
                    continue
                y = by - 2 + int(4 * f)
                p = PIECE.get(m["kind"])
                if p:
                    self.piece_draw(m["kind"], p[2] if big else p[0], m["done"], bx + m["x"], y)
                else:
                    b.buf.put(bx + m["x"], y, "(@@@@@@@)" if m["kind"] == "wors" else "(==)", meat_col(m["done"]))
                continue
            p = PIECE.get(m["kind"])
            if not p:
                continue
            txt = p[2] if big else p[1] if (i == 0 and b.CHOP) else p[0]
            if i == 0 and flying:
                continue
            under = b.buf.text_at(bx + m["x"], by + 2, 4)
            if under not in ("(==)", "(##)"):
                continue
            self.piece_draw(m["kind"], txt, m["done"], bx + m["x"], by + 2)

    def draw_flying(self, t: float) -> None:
        b = self.b
        k = b.ST.get("koos")
        if not ("braai" in b.P and k and k["act_to"] > t and not k.get("salute") and b.MEAT and not b.MEAT[0]["gone"]):
            return
        p = PIECE.get(b.MEAT[0]["kind"])
        if not p:
            return
        f = 1 - (k["act_to"] - t) / b.GUY["koos"]["act_len"]
        bx, by = b.P["braai"]
        h = int(3.6 * math.sin(PI * f) + 0.5)
        self.piece_draw(b.MEAT[0]["kind"], p[3][int(f * 6) % 4], b.MEAT[0]["done"], bx + (6 if h >= 2 else 5), by + 2 - h)

    def draw_carry(self) -> None:
        b = self.b
        D = b.DOGAT
        if not (D and D[3] is not None and len(b.MEAT) >= 2):
            return
        p = PIECE.get(b.MEAT[-1]["kind"])
        if not p:
            return
        y = D[2] + 1 if D[5] else D[2] + 2
        if D[5] and y >= b.P["braai"][1] + 3:
            return
        self.piece_draw(b.MEAT[-1]["kind"], p[0], b.MEAT[-1]["done"], D[3], y)

    # ---- hout: a log on the fire --------------------------------------------------------------------------------------------------
    def wood_start(self, t: float, auto: bool = False) -> bool:
        b = self.b
        if self.throw or self.flare or "braai" not in b.P or not b.claim("hout", t, 8):
            return False
        wood = b.pick(*WOOD)
        who = "jan" if ("jan" in b.P and b.ST.get("jan") and not b.ST["jan"].get("hide")) else "koos"
        self.throw = {"who": who, "wood": wood, "want": t, "t0": 0.0}
        if who == "jan":
            b.wake("jan", t, "hout")
        nm = banter.KV_WOOD_NAME.get(wood, wood)
        if who == "jan":
            if auto:
                b.say_now(t, banter.KV_WOOD_ASK, ("J", f"{nm}! Vang! !kv_throw"))
            else:
                b.say_now(t, ("J", f"{nm}! Vang! !kv_throw"))
        else:
            b.say_now(t, ("K", f"Nog 'n stomp {wood}. !kv_throw"))
        return True

    def throw_go(self, t: float, who: list | None = None) -> None:
        b = self.b
        if not (self.throw and not self.throw["t0"] and "braai" in b.P):
            return
        bx, by = b.P["braai"]
        j = self.throw["who"] == "jan" and "jan" in b.P
        x0, y0 = (b.P["jan"][0] + 9, b.P["jan"][1] + 2) if j else (b.P["koos"][0] + 15, b.P["koos"][1])
        self.throw.update(t0=t, dur=1.1 if j else 0.8, x0=x0, y0=y0, x1=bx + 7 + b.irand(10), y1=by + 2, pose_to=t + 0.5)
        if not j:
            self.throw["who"] = "koos"

    def log_land(self, t: float) -> None:
        b = self.b
        bx, by = b.P["braai"]
        x, wood = self.throw["x1"], self.throw["wood"]
        self.throw = {}
        for _ in range(18):
            b.SPARKS.append([x + b.rand(4) - 1, by + 2, (b.rand() - 0.5) * 7, -(3 + b.rand(7)), b.rand(0.3)])
        while len(self.logs) >= 3:
            self.logs.pop(0)
        self.logs.append([x - 2, t, t + 25 + b.rand(10), wood])
        for n, lg in enumerate(self.logs):
            b.fire_mod(f"kv_wood{n}", 0.35, lg[2] - 5)
        b.logmsg(f"hout: 1 {wood}-stomp op die vuur")
        self.wood_last = wood
        if len(self.logs) >= 2 or (b.HEAT > 0.8 and b.rand() < 0.3):
            self.flare_start(t)
        else:
            b.release("hout")
            if b.rand() < 0.6:
                ex = [(k, text.replace("{wood}", wood)) for k, text in b.pick(*banter.KV_WOOD_CATCH)]
                b.PRIO.append(ex)

    def flare_start(self, t: float) -> None:
        b = self.b
        b.claim("hout", t, 14)
        self.flare = {"t0": t, "douse": 0.0, "out": 0.0}
        b.fire_mod("kv_flare", 0.6, t + 3)
        b.set_face("koos", "wide", t + 2.5)
        b.logmsg("grid0: OPVLAM, vlamme oor die vleis")
        b.say_now(t, b.pick(*banter.KV_FLARE[0]), b.pick(*banter.KV_FLARE[1]), b.pick(*banter.KV_FLARE[2]))

    def douse_go(self, t: float) -> None:
        b = self.b
        if not (self.flare and not self.flare["douse"] and "koos" in b.P):
            return
        self.flare["douse"] = t
        x0, y0 = b.P["koos"][0] + 16, b.P["koos"][1] + 1
        self.drops = [[x0 + b.rand(2), float(y0), 3 + b.rand(9), -1 - b.rand(3), t + b.rand(0.4)] for _ in range(14)]

    def wood_update(self, t: float, dt: float) -> None:
        b = self.b
        if self.throw:
            if self.throw["t0"]:
                if t >= self.throw["t0"] + self.throw["dur"]:
                    self.log_land(t)
            elif t - self.throw["want"] > 12:
                self.throw = {}
                b.release("hout")
        self.logs = [lg for lg in self.logs if lg[2] > t]
        if self.drops:
            gy = b.P["braai"][1] + 2
            for d in self.drops:
                if t < d[4]:
                    continue
                d[3] += 18 * dt
                d[0] += d[2] * dt
                d[1] += d[3] * dt
            hit = any(d[1] >= gy for d in self.drops)
            self.drops = [d for d in self.drops if d[1] < gy]
            if hit and self.flare and not self.flare["out"]:
                self.flare["out"] = t
                bx, by = b.P["braai"]
                for _ in range(9):
                    b.SMOKE.append([bx + 4 + b.rand(16), by + 1, -(1.2 + b.rand(1.2)), 0, 2.5 + b.rand(2)])
                b.fire_mod("kv_flare", -0.5, t + 6)
                for n in range(3):
                    b.fire_mod(f"kv_wood{n}", 0, 0)
                if self.logs:
                    self.logs.pop()
                b.logmsg("grid0: opvlam geblus deur koos (1 dop, water, meestal)")
        if self.flare:
            if not self.flare["douse"] and t - self.flare["t0"] > 2:
                self.douse_go(t)
            if self.flare["out"] and t - self.flare["out"] > 2 and not self.drops:
                self.flare = {}
                b.release("hout")
            elif t - self.flare["t0"] > 14:
                self.flare = {}
                self.drops = []
                b.release("hout")

    def draw_logs(self, t: float) -> None:
        b = self.b
        bx, by = b.P["braai"]
        for x, t0, t1, _w in self.logs:
            n = 1 + int(4 * (t1 - t) / (t1 - t0) + 0.5)
            x0 = x + (5 - n) // 2
            for i in range(n):
                if x0 + i < bx + 3 or x0 + i > bx + 24:
                    continue
                r = b.rand()
                b.buf.plot(x0 + i, by + 4, "*" if r < 0.2 else "=", "Y" if r < 0.2 else "R" if r < 0.5 else "y")

    def draw_flare(self, t: float) -> None:
        b = self.b
        if not self.flare:
            return
        bx, by = b.P["braai"]
        age = t - self.flare["t0"]
        top = 4 * (1 - (t - self.flare["out"]) / 1.2) if self.flare["out"] else 7 * age if age < 0.6 else 4.2
        if top <= 0:
            return
        for i in range(20):
            h = top + 1.2 * math.sin(t * 9 + i * 1.7) + b.rand(1.2) - 0.6
            for k in range(int(h)):
                f = (k + 0.5) / (h or 1)
                b.buf.plot(bx + 4 + i, by + 1 - k, "()^'()`,"[b.irand(8)], "Y" if f < 0.3 else ("Y" if b.rand() < 0.4 else "R") if f < 0.7 else "r")

    def draw_throw(self, t: float) -> None:
        b = self.b
        if self.throw and self.throw["t0"]:
            f = (t - self.throw["t0"]) / self.throw["dur"]
            if 0 <= f < 1:
                x0, y0, x1, y1 = self.throw["x0"], self.throw["y0"], self.throw["x1"], self.throw["y1"]
                h = min(y0, y1) - (b.P["top"] - 4)
                x = x0 + (x1 - x0) * f
                y = y0 + (y1 - y0) * f - h * math.sin(PI * f)
                s = ("o==", " / ", "==o", " \\ ")[int(f * 8) % 4]
                for i, ch in enumerate(s):
                    if ch != " ":
                        b.buf.plot(int(x + i), int(y + 0.5), ch, "Y" if ch == "o" else "y")
        for d in self.drops:
            if t < d[4]:
                continue
            b.buf.plot(int(d[0]), int(d[1]), "'" if d[3] < 0 else "," if b.rand() < 0.5 else ".", "C" if b.rand() < 0.5 else "c")

    # ---- Tannie Sarie's visit ------------------------------------------------------------------------------------------------------------
    def tan_spot(self) -> tuple[int, int]:
        b = self.b
        x = (b.P["jan"][0] + 6 + b.P["koos"][0] + 7) // 2 - 7 if "jan" in b.P else b.P["koos"][0] - 6
        return (0 if x < 0 else x), b.P["base"] - 8

    def tan_start(self, t: float, auto: bool = False) -> bool:
        b = self.b
        if self.tan or "koos" not in b.P or not b.claim("tannie", t, 90):
            return False
        dish = b.pick(*DISH.keys())
        tx, ty = self.tan_spot()
        self.tan = {"step": "in", "t0": t, "dish": dish, "x": -15.0, "tx": tx, "arms": "dish", "ts": t, "v": 9 + (tx + 15) / 10,
                    "todo": [], "wave_to": 0.0}
        self.join("tannie", t, -15, ty)
        b.logmsg(f"kombuis: tannie sarie op pad braai toe met {DISH[dish][3]}")
        return True

    def tan_opinions(self) -> list[list]:
        b = self.b
        pool: list[list] = []
        d = b.meat_done()
        if b.MEAT_STATE == "cooking" and d is not None and d > 0.55:
            pool.append(list(banter.KV_TAN_MEAT_OVER))
        elif b.MEAT_STATE == "cooking" and d is not None and d < 0.3:
            pool.append(list(banter.KV_TAN_MEAT_RAW))
        n = b.DOPS.get("sak", 0)
        pool.append([banter.KV_TAN_DOPS, banter.KV_TAN_DOPS_ANS,
                     ("T", (f"Ek het {n} getel." if n > 2 else "Ek hou jou dop, Sakkie.") + " !kv_hmf")])
        pool.extend(list(x) for x in banter.KV_TAN_OPINIONS)
        if b.MEAT_STATE == "cooking" and b.MEAT and not b.MEAT[0]["gone"]:
            pool.append(list(banter.KV_TAN_TONGS))
            pool.append(list(banter.KV_TAN_TURN))
        if "dog" in b.P and not b.DOG_AWAY:
            pool.append(list(banter.KV_TAN_DOG))
        if self.ls["state"] == "dark":
            pool.append(list(banter.KV_TAN_DARK))
        o = [b.pick(*pool)]
        if "jan" in b.P and b.ST.get("jan") and not self.jan_up and b.rand() < 0.8:
            o.append(list(banter.KV_TAN_JAN))
        b.rng.shuffle(o)
        return o

    def tan_update(self, t: float, dt: float) -> None:
        b = self.b
        if not self.tan:
            return
        k = self.tan
        st = k["step"]
        quiet = self.idle(t)
        late = t - k["ts"] > 30
        b.claim("tannie", t, 30)
        if st == "in":
            k["x"] += k["v"] * dt
            if k["x"] >= k["tx"]:
                k["x"] = k["tx"]
                self.tan_step("greet", t)
                b.say_now(t, *banter.KV_TAN_HI[k["dish"]])
                for w in ("koos", "sak", "jan"):
                    b.set_face(w, "wide", t + 1.5)
        elif st == "greet" and (quiet or late):
            self.dish = {"dish": k["dish"], "x": k["tx"] + 12, "y": b.P["base"] + 1, "until": t + 120}
            k["arms"] = "free"
            b.logmsg(f"kos: {DISH[k['dish']][3]} afgelewer (1 bak, warm)")
            k["todo"] = self.tan_opinions()
            self.tan_step("talk", t)
        elif st == "talk" and (quiet or late):
            if k["todo"]:
                b.say_now(t, *k["todo"].pop(0))
                k["ts"] = t
            else:
                self.tongs_back(t)
                b.say_now(t, b.pick(*banter.KV_TAN_BYE), banter.KV_TAN_BYE_ANS)
                self.tan_step("bye", t)
        elif st == "bye" and (quiet or late) and t > k["wave_to"]:
            self.tan_step("out", t)
        elif st == "out":
            k["x"] -= k["v"] * dt
            if k["x"] < -15:
                self.leave("tannie")
                if self.jan_up and "jan" in b.P:
                    b.say_now(t, *banter.KV_JAN_SIT)
                    self.tan_step("after", t)
                else:
                    self.tan_end(t)
        elif st == "after" and (quiet or t - k["ts"] > 15):
            self.tan_end(t)
        if "tannie" not in b.P:
            return
        b.P["tannie"][0] = int(k["x"])
        walking = st in ("in", "out")
        arms = k["arms"]
        if k["wave_to"] > t and int(t * 3) % 2 == 0:
            arms = "wave"
        if self.tongs and not walking:
            arms = "tongs" if int(t * 4) % 2 else "click"
        spr = tan_spr(k["dish"], arms, int(t * 4) % 2 if walking else 0)
        if b.ST.get("tannie"):
            b.ST["tannie"]["pose"], b.ST["tannie"]["pose_to"] = spr, t + 0.5

    def tan_step(self, s: str, t: float) -> None:
        self.tan["step"], self.tan["ts"] = s, t

    def tan_end(self, t: float) -> None:
        b = self.b
        if "tannie" in b.P:
            self.leave("tannie")
        self.tongs_back(t)
        self.jan_sit(t)
        self.tan = {}
        b.release("tannie")

    def tongs_back(self, t: float) -> None:
        if not self.tongs:
            return
        self.tongs = 0
        self.b.logmsg("grid0: tang terug by koos (pid 101)", True)

    def jan_sit(self, t: float) -> None:
        if not self.jan_up:
            return
        self.jan_up = 0.0
        self.b.logmsg("jannie: koelboks0 weer gemonteer", True)

    # ---- Oom Faan's visit ------------------------------------------------------------------------------------------------------------------
    def oom_place(self) -> dict:
        b = self.b
        sx = b.P["sak"][0]
        sr = sx + 13
        o: dict[str, Any] = {"dog": 0}
        if b.COLS - (sr + 3 + OOM_W) >= BAK_W:
            o["ox"], o["bx"] = sr + 1, sr + OOM_W + 3
        elif b.COLS - sr > OOM_W:
            o["ox"], o["bx"] = sr + 1, b.COLS + 2
        else:
            o["bx"] = b.COLS + 2
            o["ox"] = b.P["dog"][0] - 4 if "dog" in b.P else sx - OOM_W + 4
            o["dog"] = 1 if "dog" in b.P else 0
        o["seen"] = 1 if o["bx"] < b.COLS else 0
        o["door"] = o["bx"] + 7 if o["seen"] else b.COLS + 1
        wy = b.P["table"][0] - 1 if "table" in b.P else b.ROWS - 2
        if wy > b.P["base"] + 5:
            wy = b.P["base"] + 5
        if wy < b.P["base"] + 1:
            wy = b.P["base"] + 1
        o["by"] = wy - 4
        o["oy"] = b.P["base"] - 8
        return o

    def oom_start(self, t: float, auto: bool = False) -> bool:
        b = self.b
        if self.oom or "sak" not in b.P or not b.claim("oom", t, 120):
            return False
        self.oom = dict(self.oom_place(), step="drive", ts=t, x=float(-BAK_W - 1), dir=1, spin=0.0, lights=1, inside=1,
                        hooted=0, hooted2=0, wx=0.0, v=5.0, dog_away=0)
        o = self.oom
        o["x0"] = o["x"]
        o["dist"] = o["bx"] - o["x"]
        o["dur"] = 1 + o["dist"] / 16 if o["seen"] else o["dist"] / 22
        b.logmsg("bakkie1: oom faan op die oprit (TOET)")
        return True

    def oom_step(self, s: str, t: float) -> None:
        self.oom["step"], self.oom["ts"] = s, t

    def do_toet(self, t: float) -> None:
        o = self.oom
        x = int(o["x"]) + BAK_W + 1 if o["dir"] > 0 else int(o["x"]) - 14
        self.toet = {"x": x, "y": o["by"] - 1, "dir": o["dir"], "until": t + 1.6}

    def oom_update(self, t: float, dt: float) -> None:
        b = self.b
        if not self.oom:
            return
        o = self.oom
        st = o["step"]
        age = t - o["ts"]
        quiet = self.idle(t)
        late = age > 35
        b.claim("oom", t, 30)
        x_was = o["x"]
        if st == "drive":
            f = min(1.0, age / o["dur"])
            o["x"] = o["bx"] - o["dist"] * (1 - f) ** 2 if o["seen"] else o["x0"] + o["dist"] * f
            if not o["hooted"] and o["x"] > -BAK_W + 8:
                o["hooted"] = 1
                self.do_toet(t)
            if f >= 1:
                self.oom_step("park", t)
                if o["seen"]:
                    for _ in range(6):
                        self.add_dust(o["x"] + b.rand(28), o["by"] + 4, b.rand(4) - 2)
        elif st == "park":
            if age > 0.7:
                o["lights"] = 0
            if age > 1.3:
                o["inside"], o["wx"] = 0, float(o["door"])
                o["v"] = 5 + abs(o["door"] - o["ox"]) / 8
                self.join("oom", t, int(o["wx"]), o["oy"])
                if o["dog"] and not b.DOG_AWAY:
                    b.DOG_AWAY = o["dog_away"] = 1
                    b.logmsg("wagter: gaan snuffel aan die bakkie se bande", True)
                self.oom_step("walk", t)
        elif st == "walk":
            o["wx"] -= o["v"] * dt
            if o["wx"] <= o["ox"]:
                o["wx"] = o["ox"]
                b.say_now(t, *banter.KV_OOM_HI, b.pick(*banter.KV_OOM_HI_ANS))
                self.oom_step("greet", t)
        elif st == "greet" and (quiet or late):
            self.cooler = {"x": o["ox"] - 4, "y": b.P["base"]}
            if b.ST.get("oom"):
                b.ST["oom"]["act_at"] = t + 2
            b.logmsg("koelboks1: +5 kg ys van oom faan")
            b.logmsg("oom: storie-modus aan (akkuraatheid 12%)", True)
            b.say_now(t, *b.pick(*banter.KV_STORY))
            self.oom_step("story", t)
        elif st == "story" and (quiet or late):
            b.say_now(t, b.pick(*banter.KV_OOM_BYE), banter.KV_OOM_BYE_ANS)
            self.oom_step("bye", t)
        elif st == "bye" and (quiet or late):
            self.cooler = {}
            if b.ST.get("oom"):
                b.ST["oom"]["act_at"] = t + 1e6
            self.oom_step("back", t)
        elif st == "back":
            o["wx"] += o["v"] * dt
            if o["wx"] >= o["door"]:
                self.leave("oom")
                if not o["seen"]:
                    o["dir"], o["x"] = -1, float(b.COLS + 1)
                o["inside"], o["lights"] = 1, 1
                self.oom_step("start", t)
        elif st == "start":
            if age > 0.4 and not o["hooted2"]:
                o["hooted2"] = 1
                self.do_toet(t)
            if age > 1.4:
                o["x0"] = o["x"]
                self.oom_step("leave", t)
        elif st == "leave":
            o["x"] = o["x0"] + o["dir"] * (7 * age + 6 * age * age)
            if o["x"] < -BAK_W - 2 or o["x"] > b.COLS + 2:
                if o["dog_away"]:
                    b.DOG_AWAY = 0
                    b.logmsg("wagter: terug op sy plek", True)
                b.logmsg("bakkie1: oom faan het die braai verlaat (stof 100%)")
                self.oom = {}
                b.release("oom")
                return
        moved = o["x"] - x_was
        o["spin"] += abs(moved)
        if abs(moved) > 0.05 and -BAK_W < o["x"] < b.COLS:
            back = o["x"] + 1 if o["dir"] > 0 else o["x"] + BAK_W - 2
            if b.rand() < 0.4 + abs(moved):
                self.add_dust(back + b.rand(2), o["by"] + 3 + b.rand(2), -o["dir"] * (2 + b.rand(3)))
        if "oom" in b.P and b.ST.get("oom"):
            b.P["oom"][0] = int(o["wx"])
            walking = st in ("walk", "back")
            cool = st in ("walk", "greet", "back")
            if walking or cool:
                b.ST["oom"]["pose"], b.ST["oom"]["pose_to"] = oom_spr(1 if cool else 0, int(t * 4) % 2 if walking else 0), t + 0.5
            else:
                b.ST["oom"]["pose_to"] = 0

    def add_dust(self, x: float, y: float, vx: float) -> None:
        if len(self.dust) > 60:
            return
        self.dust.append([x, y, vx, -(0.4 + self.b.rand(1.2)), 0.0, 1.2 + self.b.rand(1.6)])

    def dust_update(self, t: float, dt: float) -> None:
        for d in self.dust:
            d[4] += dt
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            d[2] *= 1 - 1.2 * dt
        self.dust = [d for d in self.dust if d[4] < d[5]]

    def draw_bakkie(self, t: float) -> None:
        b = self.b
        if not self.oom:
            return
        o = self.oom
        x, y, d = int(o["x"]), o["by"], o["dir"]
        if x >= b.COLS or x <= -BAK_W:
            return
        b.buf.draw(BAK[d], x, y)
        moving = o["step"] in ("drive", "leave")
        spin = ("|", "\\", "-", "/") if d < 0 else ("|", "/", "-", "\\")
        hub = spin[int(o["spin"] / 1.5) % 4] if moving else "o"
        for hx in ((7, 19) if d < 0 else (10, 22)):
            b.buf.plot(x + hx, y + 3, hub, "W")
        if o["inside"]:
            b.buf.put(x + (12 if d < 0 else 15), y + 1, "_^_", "y")
            b.buf.put(x + (12 if d < 0 else 16), y + 2, "(o" if d < 0 else "o)", "w")
        if o["lights"] and self.night():
            hx = x if d < 0 else x + BAK_W - 1
            for k in range(1, 15):
                bx = hx + d * k
                b.buf.plot(bx, y + 3, "=" if k <= 4 else "-", "Y" if k <= 8 else "y")
                if k > 6 and k % 2:
                    b.buf.plot(bx, y + 2, "_", "y")
                if k > 3 and k % 3 == 0:
                    b.buf.plot(bx, y + 4, ".", "y")

    def draw_dust(self) -> None:
        plot = self.b.buf.plot
        for d in self.dust:
            f = d[4] / d[5]
            plot(int(d[0]), int(d[1]), "." if f < 0.15 else "o" if f < 0.4 else "O" if f < 0.65 else "o" if f < 0.85 else ".",
                 "y" if f < 0.5 else "w")

    # ---- hooks ----------------------------------------------------------------------------------------------------------------------------------
    def hook_boot(self) -> list:
        return [["w", "eskom: rooster gelaai, stage 0 (vir nou)"],
                ["w", "kuier: tannie sarie (kombuis), oom faan (bakkie1) op bystand"],
                ["w", "hout: /dev/houtstapel: kameeldoring, rooikrans, sekelbos, bloekom"]]

    def on_layout(self, t: float) -> None:
        b = self.b
        if b.P.get("small"):
            return
        self.town_build()
        if self.ls["state"] == "dark":
            for bl in self.town:
                bl["off"] = t - 1
        elif self.ls["state"] == "restore":
            for bl in self.town:
                for w in bl["wins"]:
                    w["on"] = t + b.rand(1.5)
        self.stars = []
        mx, my = b.P["moon"]
        n = min(45, int(b.COLS * (b.P["top"] - 2) / 70))
        for _ in range(n):
            x, y = b.irand(b.COLS), b.irand(b.P["top"] - 2)
            if mx - 2 <= x <= mx + b.P["moonspr"].w + 1 and y <= my + b.P["moonspr"].h:
                continue
            self.stars.append([x, y, b.rand(6.3), 0.4 + b.rand(1.4), b.T + b.rand(3)])
        self.bright = [d for d in b.DUST if d[2] == ":" or (d[0] * 7 + d[1] * 3) % 4 == 0]
        if self.tan:
            tx, ty = self.tan_spot()
            self.tan["tx"] = tx
            if self.tan["step"] == "in":
                self.tan["x"] = tx
            if self.tan["step"] == "out" or "koos" not in b.P:
                self.tan_end(t)
            elif "tannie" in b.P:
                b.P["tannie"] = [int(self.tan["x"]), ty]
            else:
                self.join("tannie", t, int(self.tan["x"]), ty)
        if self.dish:
            self.dish["x"] = self.tan_spot()[0] + 12
            self.dish["y"] = b.P["base"] + 1
        if self.oom:
            pl = self.oom_place()
            st = self.oom["step"]
            if "sak" not in b.P or st in ("back", "start", "leave"):
                self.leave("oom")
                if self.oom["dog_away"]:
                    b.DOG_AWAY = 0
                self.oom = {}
                b.release("oom")
            else:
                self.oom.update(pl)
                if st in ("drive", "park"):
                    self.oom["x"], self.oom["step"] = float(self.oom["bx"]), "park"
                if st == "walk" or "oom" in b.P:
                    self.oom["wx"] = float(self.oom["ox"])
                if self.oom["dog_away"] and not self.oom["dog"]:
                    b.DOG_AWAY = 0
                    self.oom["dog_away"] = 0
                if self.oom["dog"] and not self.oom["inside"] and not b.DOG_AWAY:
                    b.DOG_AWAY = self.oom["dog_away"] = 1
                if "oom" in b.P:
                    b.P["oom"] = [int(self.oom["wx"]), self.oom["oy"]]
                elif not self.oom["inside"]:
                    self.join("oom", t, int(self.oom["wx"]), self.oom["oy"])
        if not self.oom:
            self.cooler = {}
        if self.cooler:
            self.cooler = {"x": self.oom["ox"] - 4, "y": b.P["base"]}
        self.throw = {}
        self.drops = []
        self.dust = []
        if self.drop:
            for m in self.drop["pieces"]:
                if m["gone"]:
                    m["gone"] = 0
            self.drop = {}
        self.car = {}

    def on_update(self, t: float, dt: float) -> None:
        b = self.b
        if b.P.get("small"):
            return
        self.ls_update(t)
        self.tan_update(t, dt)
        self.oom_update(t, dt)
        self.wood_update(t, dt)
        self.meat_update(t)
        self.car_update(t, dt)
        self.dust_update(t, dt)
        self.sx0, self.sx1 = self.gx0, self.gx1
        if "oom" in b.P and self.oom and self.oom["ox"] > self.gx1:
            self.sx1 = self.oom["ox"] + OOM_W + 1
        koos = (KOOS_SPLASH if (self.flare and self.flare["douse"] and t - self.flare["douse"] < 1.6)
                else KOOS_HIPS if self.tongs
                else KOOS_LOG if (self.throw and self.throw["who"] == "koos" and self.throw["t0"] and t < self.throw["pose_to"])
                else None)
        self.pose("koos", koos, t)
        if self.jan_up:
            jan, dy = (JAN_JUMP, -3) if t - self.jan_up < 0.35 else (JAN_UP, -2)
        elif self.throw and self.throw["who"] == "jan" and self.throw["t0"] and t < self.throw["pose_to"]:
            jan, dy = JAN_LOG, 0
        else:
            jan, dy = None, 0
        self.pose("jan", jan, t, dy)
        if self.dish and (t > self.dish["until"] or b.MEAT_STATE == "served"):
            self.dish = {}
        if t > self.flick and self.town:
            self.flick = t + 4 + b.rand(6)
            ws = [w for bl in self.town for w in bl["wins"] if w["kind"] == "W"]
            w = ws[b.irand(len(ws))] if ws else None
            if w and not (self.gen and self.gen["wins"] and w is self.gen["wins"][0]):
                w["lit"] = 0 if w["lit"] else 1
                self.life += 1
        for what in sorted(self.want):
            until, start = self.want[what]
            if t > until:
                del self.want[what]
                continue
            if not (b.calm(t) and self.idle(t)):
                continue
            if start(t):
                del self.want[what]
            break
        if b.auto_ok(t):
            go = {"tannie": self.tan_start, "oom": self.oom_start, "wood": self.wood_start, "ls": self.ls_start}
            for what in sorted(self.next, key=lambda k: self.next[k]):
                if t < self.next[what]:
                    continue
                ok = go[what](t, True)
                self.next[what] = t + (1200 + b.rand(2400) if what in ("tannie", "oom") else 600 + b.rand(900) if what == "wood"
                                       else 3600 + b.rand(7200))
                if not ok:
                    self.next[what] = t + 60
                else:
                    b.auto_done(t)
                break

    def hook_sky(self, t: float) -> None:
        if self.b.P.get("small"):
            return
        self.draw_dark_sky(t)
        self.draw_town(t)
        self.draw_car(t)

    def hook_actors(self, t: float) -> None:
        b = self.b
        if b.P.get("small"):
            return
        self.draw_meat(t)
        if self.logs:
            self.draw_logs(t)
        self.draw_flare(t)
        if self.dish:
            d = DISH[self.dish["dish"]]
            s = d[4]
            if self.dish["dish"] == "pap" and int(t * 2) % 3 == 0:
                s = s[:2] + "~" + s[3:]
            b.buf.blit(self.dish["x"], self.dish["y"], s, d[5])
        if self.cooler:
            b.buf.draw(COOLER, self.cooler["x"], self.cooler["y"])
        b.draw_guy("tannie", t)
        b.draw_guy("oom", t)
        self.draw_bakkie(t)

    def hook_front(self, t: float) -> None:
        b = self.b
        if b.P.get("small"):
            return
        self.draw_flying(t)
        self.draw_carry()
        self.draw_throw(t)
        if self.dust:
            self.draw_dust()
        if self.toet and self.toet["until"] > t:
            on = int((self.toet["until"] - t) * 5) % 2
            s = ("<< TOET-TOET!" if on else "<  TOET-TOET!") if self.toet["dir"] < 0 else ("TOET-TOET! >>" if on else "TOET-TOET!  >")
            x = self.toet["x"]
            if x + len(s) > b.COLS - 1:
                x = b.COLS - len(s) - 1
            b.buf.put(max(0, x), self.toet["y"], s, "Y")

    def hook_status(self, t: float) -> list:
        f = []
        if self.ls["state"] in ("dark", "pending"):
            f.append([2.5, f"eskom: stage {self.ls['stage']}"])
        if "tannie" in self.b.P:
            f.append([6.5, "kuier: tannie sarie"])
        if self.oom:
            f.append([6.5, "kuier: oom faan"])
        return f

    def install(self) -> None:
        b = self.b
        b.GUY["tannie"] = {"rest": tan_spr("pap", "free", 0), "act": tan_spr("pap", "wave", 0), "act_len": 1.5,
                           "eyes": [2, 5, {"open": "[o-o]", "shut": "[_-_]", "left": "[o-o]", "right": "[o-o]",
                                           "wide": "[O-O]", "laugh": "[^-^]", "sceptic": "[o-O]"}],
                           "mouth": [3, 7, "-", "o"], "mcol": "R", "head": 7}
        b.GUY["oom"] = {"rest": oom_spr(0, 0), "act": OOM_SIP, "act_len": 1.6, "sip": 1,
                        "eyes": [2, 6, {"open": "(o  o)", "shut": "(-  -)", "left": "(o o )", "right": "( o o)",
                                        "wide": "(O  O)", "laugh": "(^  ^)"}],
                        "mouth": [3, 6, "~~~~~~", "~-~~-~"], "mcol": "w", "head": 8}
        b.WHO["T"] = "tannie"
        b.WHO["O"] = "oom"
        b.NAME["tannie"] = "tannie sarie"
        b.NAME["oom"] = "oom faan"
        M = b.MARK

        def jump(t: float, who: list) -> None:
            if "jan" in b.P and b.ST.get("jan"):
                b.wake("jan", t, "tannie")
                self.jan_up = t
                b.logmsg("jannie: koelboks0 vrygestel (tannie se orders)")

        def tongs(t: float, who: list) -> None:
            if "tannie" in b.P:
                self.tongs = 1
                b.set_face("koos", "wide", t + 2)
                b.logmsg("grid0: tang geleen deur tannie sarie")

        M["kv_jump"] = jump
        M["kv_sit"] = lambda t, who: self.jan_sit(t)
        M["kv_tongs"] = tongs
        M["kv_hmf"] = lambda t, who: b.set_face("tannie", "sceptic", t + 2.5)
        M["kv_tongsback"] = lambda t, who: self.tongs_back(t)
        M["kv_wave"] = lambda t, who: self.tan.__setitem__("wave_to", t + 2.4) if self.tan else None
        M["kv_throw"] = self.throw_go
        C = b.COND
        C["kv_dark"] = lambda: self.ls["state"] == "dark"
        C["kv_lit"] = lambda: self.ls["state"] == "off"
        C["kv_gen"] = lambda: self.ls["state"] == "dark" and bool(self.ls.get("gen"))
        C["kv_nosignal"] = lambda: self.ls["state"] == "dark" and bool(self.ls.get("mast_dead"))
        C["kv_wood"] = lambda: bool(self.logs)
        C["kv_dish"] = lambda: bool(self.dish)
        for kind in PIECE:
            C["kv_" + kind] = (lambda kind=kind: any(m["kind"] == kind and not m["gone"] for m in b.MEAT))
        b.FILL["wood"] = lambda: self.wood_last
        b.FILL["stage"] = lambda: str(self.ls.get("stage", 4))
        b.TALK.extend(list(x) for x in banter.KV_TALK)
        b.TALK.append(self.woodtalk)
        b.hook("boot", self.hook_boot)
        b.hook("layout", self.on_layout)
        b.hook("update", self.on_update)
        b.hook("sky", self.hook_sky)
        b.hook("actors", self.hook_actors)
        b.hook("front", self.hook_front)
        b.hook("status", self.hook_status)
        b.key("t", "Tannie Sarie bring kos / brings food", lambda t: self.ask("tannie", t, self.tan_start))
        b.key("o", "Oom Faan kom kuier / comes to visit", lambda t: self.ask("oom", t, self.oom_start))
        b.key("l", "beurtkrag (Eskom), aan/af / loadshedding", self.ls_key)
        b.key("h", "hout: 'n stomp op die vuur / a log on the fire", lambda t: self.ask("hout", t, self.wood_start))
        b.key("m", "meer vleis: verander die rooster / change the grid", lambda t: self.ask("vleis", t, self.meat_key))
