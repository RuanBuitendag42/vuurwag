"""The frame buffer and the sprites: lekker's rules for transparency, masks, clipping and the 8-colour palette."""
from __future__ import annotations

from rich.color import ColorType

from vuurwag.braai import art
from vuurwag.braai.buf import LETTERS, Buf, StripCache, mirror_text, render_row, sprite, style_for, wrap


def test_sprite_segments_follow_lekker_rules():
    s = sprite("ab ?cd\n  x  \n", "RR  gg\n  Y", "w")
    # row 0: 'ab' (a segment), then '?' splits, then 'cd'; inner spaces stay opaque only between characters
    assert s.segs[0] == (0, 0, "ab", "RR")
    assert s.segs[1] == (0, 4, "cd", "gg")
    assert s.segs[2] == (1, 2, "x", "Y")
    assert s.w == 6 and s.h == 2
    # one mask letter colours the whole row
    s2 = sprite("hello", "G")
    assert s2.segs[0][3] == "GGGGG"
    # leading and trailing spaces are transparent, inner spaces are opaque
    s3 = sprite("  a b  ", None, "c")
    assert s3.segs == [(0, 2, "a b", "ccc")]


def test_core_art_is_exact_and_ascii():
    assert art.KOOS_REST.h == 10 and art.SAK_REST.h == 10 and art.JAN_REST.h == 10
    # (the mask is two letters short on purpose, as in lekker: the "=o" at the right keeps the default colour)
    assert art.BRAAI.segs[0] == (3, 0, "o=[######################]=o", "WWwwwwwwwwwwwwwwwwwwwwwwWW..")
    assert art.KOOS_REST.segs[4][2] == ".-'`--'`-.  __==<"
    assert (1, 0, "o'')}____//", "WWWYYYYYYYY") in art.DOG[0].segs
    for spr in (art.KOOS_REST, art.KOOS_FLIP, art.SAK_REST, art.SAK_SIP, art.JAN_REST, art.JAN_SIP, art.BRAAI, art.MOON,
                art.MOON_S, art.BAKKIE, art.TOWER, art.TREE, art.TREE_S, *art.DOG, *art.DOG_TROT, *art.DOG_RUN):
        for _y, _x, txt, col in spr.segs:
            assert txt.isascii() and all(32 <= ord(c) < 127 for c in txt)
            assert all(c in LETTERS for c in col)
            assert len(txt) == len(col)


def test_buf_blit_put_plot_clip():
    b = Buf(10, 3)
    b.put(-2, 1, "hello", "R")
    assert "".join(b.scr[1][:3]) == "llo" and b.atr[1][0] == "R"
    b.put(8, 0, "abcd", "G")
    assert "".join(b.scr[0]) == "        ab"
    b.plot(50, 50, "x", "W")      # off screen: ignored
    b.plot(9, 2, "x", "W")
    assert b.ch(9, 2) == "x" and b.at(9, 2) == "W"
    b.draw(sprite("ab\n?c", None, "y"), 3, 1)
    assert b.text_at(3, 1, 2) == "ab" and b.ch(4, 2) == "c" and b.ch(3, 2) == " "
    b.resize(4, 2)
    assert b.text() == ["    ", "    "]


def test_mirror_and_wrap():
    assert mirror_text("/ab(", 4, True) == ")ba\\"
    assert mirror_text("/ab(", 6, False) == "  (ba/"
    assert wrap("een twee drie vier", 9) == ["een twee", "drie vier"]
    assert wrap("", 5) == [""]


def test_palette_is_eight_ansi_colours_bold_for_bright():
    for let in LETTERS:
        st = style_for(let, "ansi")
        if let == "v":
            assert st.reverse
            continue
        assert st.color is not None and st.color.type == ColorType.STANDARD and st.color.number < 8
        assert st.bgcolor is not None and st.bgcolor.type == ColorType.STANDARD and st.bgcolor.number in (0, 1)
        assert bool(st.bold) == (let.isupper() or let == "h")
    g = style_for("R", "green")
    assert g.color.number == 2 and g.bold
    assert style_for("r", "green").color.number == 2 and not style_for("r", "green").bold
    t = style_for("R", "truecolor")
    assert t.color.type == ColorType.TRUECOLOR and t.bold


def test_render_row_merges_blanks_and_keeps_backgrounds():
    chars = list("ab   cd  ")
    letters = list("RRwwwGGww")
    strip = render_row(chars[:], letters[:], "ansi")
    texts = [seg.text for seg in strip]
    assert "".join(texts) == "ab   cd  "
    assert len(strip._segments) <= 3
    # a reverse-video blank keeps its own segment
    chars = list("a b")
    letters = list("wvw")
    strip = render_row(chars[:], letters[:], "ansi")
    assert any(seg.style.reverse for seg in strip)


def test_strip_cache_rebuilds_only_changed_rows():
    b = Buf(8, 3)
    cache = StripCache()
    assert cache.update(b) == [0, 1, 2]
    assert cache.update(b) == []
    b.put(0, 1, "x", "Y")
    assert cache.update(b) == [1]
    b.resize(6, 2)
    assert cache.update(b) == [0, 1]
