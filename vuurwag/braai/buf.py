"""The frame buffer and the sprites, as in lekker.

A cell holds one 7-bit character and one colour letter.  The letters are lekker's mask letters:
r g y b m c w (the 8 ANSI colours, lower case = normal, upper case = bright, which is bold), `.` the
terminal's own foreground, `v` reverse video (the log cursor, the top(1) header) and `h` a white-hot
coal (bright yellow on red).  A blank keeps whatever letter was put with it, so a blank in reverse
video still shows its background.

A sprite is ASCII art plus an optional colour mask of the same shape.  In the art, the spaces before the
first and after the last character of a line are transparent, spaces in between are opaque, and `?` is
always transparent.  In the mask a space means the sprite's default colour (itself a mask letter), and a
line holding a single letter colours that whole row.  Each line is stored as opaque segments
[row, column, characters, colours].
"""
from __future__ import annotations

import re

from rich.color import Color
from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip

# ---- colours: mask letter -> (ansi index, bold); bright = bold + 30..37 ---------------------------
BASE: dict[str, tuple[int, bool]] = {
    "r": (1, False), "R": (1, True), "g": (2, False), "G": (2, True), "y": (3, False), "Y": (3, True),
    "b": (4, False), "B": (4, True), "m": (5, False), "M": (5, True), "c": (6, False), "C": (6, True),
    "w": (7, False), "W": (7, True), ".": (7, False),
}
BG_LETTERS = frozenset("vh")    # colours whose blanks show
LETTERS = "rRgGyYbBmMcCwW.vh"

# --truecolor: the same art with a little more shade in it (never a different picture)
TRUE_RGB: dict[str, tuple[int, bool]] = {
    "r": (0xB03020, False), "R": (0xFF6040, True), "g": (0x3A9A48, False), "G": (0x6AE880, True),
    "y": (0xB89040, False), "Y": (0xFFD860, True), "b": (0x4868C8, False), "B": (0x80A0FF, True),
    "m": (0xA858B0, False), "M": (0xFF88FF, True), "c": (0x30A8B0, False), "C": (0x70F0F8, True),
    "w": (0xB8B8B8, False), "W": (0xFFFFFF, True), ".": (0xC8C8C8, False),
}

_SEG_RE = re.compile(r"[^ ?][^?]*[^ ?]|[^ ?]")


class Sprite:
    __slots__ = ("segs", "w", "h")

    def __init__(self, segs: list[tuple[int, int, str, str]]) -> None:
        self.segs = segs
        w = 0
        h = 0
        for y, x, txt, _c in segs:
            if x + len(txt) > w:
                w = x + len(txt)
            if y + 1 > h:
                h = y + 1
        self.w = w
        self.h = h


def sprite(art: str, mask: str | None = None, default: str = ".") -> Sprite:
    """lekker's sprite(): ASCII art plus a colour mask into opaque segments."""
    a = art.split("\n")
    if a and a[-1] == "":
        a.pop()
    m = (mask or "").split("\n")
    if m and m[-1] == "":
        m.pop()
    segs: list[tuple[int, int, str, str]] = []
    for y, line in enumerate(a):
        line = line.rstrip()
        mrow = m[y] if y < len(m) else ""
        if len(mrow) == 1:
            mrow = mrow * 200
        for mt in _SEG_RE.finditer(line):
            x, txt = mt.start(), mt.group(0)
            col = "".join((mrow[i] if i < len(mrow) and mrow[i] != " " else default) for i in range(x, x + len(txt)))
            segs.append((y, x, txt, col))
    return Sprite(segs)


def sprite_rows(art_rows: list[str], mask_rows: list[str | None], default: str = ".") -> Sprite:
    return sprite("\n".join(art_rows), "\n".join(r if r is not None else "" for r in mask_rows), default)


MIRROR_ART = str.maketrans({"/": "\\", "\\": "/", "(": ")", ")": "(", "<": ">", ">": "<", "`": "'", "'": "`",
                            "[": "]", "]": "[", "{": "}", "}": "{"})
MIRROR_PLAIN = str.maketrans({"/": "\\", "\\": "/", "(": ")", ")": "(", "[": "]", "]": "[", "<": ">", ">": "<"})


def mirror_text(text: str, w: int | None = None, swap: bool = True, table: dict | None = None) -> str:
    """Art (or a mask, with no swapping) flipped left to right in a frame w wide (the widest line if None)."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if w is None:
        w = max((len(line) for line in lines), default=0)
    out = []
    for line in lines:
        s = line.ljust(w)[::-1]
        if swap:
            s = s.translate(table or MIRROR_PLAIN)
        out.append(s)
    return "\n".join(out)


def wrap(text: str, w: int) -> list[str]:
    out = [""]
    for word in text.split():
        if out[-1] == "":
            out[-1] = word
        elif len(out[-1]) + 1 + len(word) <= w:
            out[-1] += " " + word
        else:
            out.append(word)
    return out


def ascii7(s: str) -> str:
    """Only printable 7-bit characters ever reach the buffer (a kernel name, a weather label ...)."""
    return "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in s)


class Buf:
    """lekker's $SCR / $ATR: one row of characters and one row of colour letters per screen row."""

    __slots__ = ("rows", "cols", "scr", "atr")

    def __init__(self, cols: int = 80, rows: int = 24) -> None:
        self.rows = rows
        self.cols = cols
        self.scr: list[list[str]] = []
        self.atr: list[list[str]] = []
        self.clear()

    def clear(self) -> None:
        n = self.cols
        self.scr = [[" "] * n for _ in range(self.rows)]
        self.atr = [["."] * n for _ in range(self.rows)]

    def resize(self, cols: int, rows: int) -> None:
        self.cols, self.rows = cols, rows
        self.clear()

    def blit(self, x: int, y: int, s: str, c: str) -> None:
        """Characters plus a colour string of the same length, clipped."""
        if y < 0 or y >= self.rows or x >= self.cols:
            return
        if x < 0:
            if -x >= len(s):
                return
            s, c, x = s[-x:], c[-x:], 0
        n = len(s)
        if x + n > self.cols:
            n = self.cols - x
            s, c = s[:n], c[:n]
        if n <= 0:
            return
        self.scr[y][x:x + n] = s
        self.atr[y][x:x + n] = c

    def put(self, x: int, y: int, s: str, c: str) -> None:
        """A string in one colour."""
        self.blit(x, y, s, c * len(s))

    def plot(self, x: int, y: int, ch: str, c: str) -> None:
        if y < 0 or y >= self.rows or x < 0 or x >= self.cols:
            return
        self.scr[y][x] = ch
        self.atr[y][x] = c

    def draw(self, spr: Sprite, x: int, y: int) -> None:
        """A sprite with its top-left corner at (x, y)."""
        blit = self.blit
        for sy, sx, txt, col in spr.segs:
            blit(x + sx, y + sy, txt, col)

    def draw_col(self, spr: Sprite, x: int, y: int, c: str) -> None:
        """A sprite in one colour (lightning on the tree, a cloud lit by the flash)."""
        blit = self.blit
        for sy, sx, txt, _col in spr.segs:
            blit(x + sx, y + sy, txt, c * len(txt))

    def ch(self, x: int, y: int) -> str:
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.scr[y][x]
        return "\0"

    def at(self, x: int, y: int) -> str:
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.atr[y][x]
        return "\0"

    def text(self) -> list[str]:
        return ["".join(r) for r in self.scr]

    def text_at(self, x: int, y: int, n: int) -> str:
        if 0 <= y < self.rows:
            return "".join(self.scr[y][max(0, x):max(0, x + n)])
        return ""


# ---- the palette: a letter -> a Rich style, in colour, green phosphor or truecolor ----------------------
_STYLES: dict[tuple[str, str], Style] = {}


def style_for(letter: str, mode: str = "ansi") -> Style:
    """mode: ansi (8 colours, bright = bold), green (two greens and reverse), truecolor (subtle shades)."""
    key = (letter, mode)
    st = _STYLES.get(key)
    if st is not None:
        return st
    bg_black = Color.from_ansi(0)
    if mode == "green":
        bright = letter.isupper() or letter == "h"
        if letter == "v":
            st = Style(color=Color.from_ansi(2), bgcolor=bg_black, reverse=True)
        else:
            st = Style(color=Color.from_ansi(2), bgcolor=bg_black, bold=bright or None)
    elif mode == "truecolor":
        bg = Color.from_rgb(4, 4, 8)
        if letter == "v":
            st = Style(color=Color.from_rgb(0xC8, 0xC8, 0xC8), bgcolor=bg, reverse=True)
        elif letter == "h":
            st = Style(color=Color.from_rgb(0xFF, 0xE8, 0x70), bgcolor=Color.from_rgb(0xB0, 0x30, 0x20), bold=True)
        else:
            rgb, bold = TRUE_RGB.get(letter, TRUE_RGB["."])
            st = Style(color=Color.from_rgb((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255), bgcolor=bg, bold=bold or None)
    else:
        if letter == "v":
            st = Style(color=Color.from_ansi(7), bgcolor=bg_black, reverse=True)
        elif letter == "h":
            st = Style(color=Color.from_ansi(3), bgcolor=Color.from_ansi(1), bold=True)
        else:
            idx, bold = BASE.get(letter, BASE["."])
            st = Style(color=Color.from_ansi(idx), bgcolor=bg_black, bold=bold or None)
    _STYLES[key] = st
    return st


def render_row(chars: list[str], letters: list[str], mode: str = "ansi") -> Strip:
    """A row as a Strip: one segment per run of colour; a run of blanks joins its neighbour unless a
    background is involved (as lekker sends only the colour changes that show)."""
    n = len(chars)
    segs: list[Segment] = []
    if n == 0:
        return Strip([], 0)
    start = 0
    cur = letters[0]
    for x in range(1, n):
        let = letters[x]
        if let == cur:
            continue
        # a run of blanks in a colour without a background looks the same in any such colour
        if chars[x] == " " and let not in BG_LETTERS and cur not in BG_LETTERS:
            letters[x] = cur        # (absorb it into the current run)
            continue
        if cur not in BG_LETTERS and let not in BG_LETTERS and all(c == " " for c in chars[start:x]):
            cur = let               # the blanks before take the colour of what follows
            continue
        segs.append(Segment("".join(chars[start:x]), style_for(cur, mode)))
        start, cur = x, let
    segs.append(Segment("".join(chars[start:n]), style_for(cur, mode)))
    return Strip(segs, n)


class StripCache:
    """Keeps last frame's rows and rebuilds only rows whose cells changed."""

    def __init__(self) -> None:
        self.strips: list[Strip] = []
        self.prev: list[tuple] = []
        self.w = 0
        self.h = 0

    def update(self, buf: Buf, mode: str = "ansi") -> list[int]:
        w, h = buf.cols, buf.rows
        if (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.strips = [Strip.blank(w)] * h
            self.prev = [()] * h
        changed = []
        for y in range(h):
            chars = buf.scr[y]
            letters = buf.atr[y]
            key = ("".join(chars), "".join(letters), mode)
            if key == self.prev[y]:
                continue
            self.prev[y] = key
            self.strips[y] = render_row(chars[:], letters[:], mode)
            changed.append(y)
        return changed
