"""The stage: the fire rules, the meat, the boot log, every key at four sizes, every skit to completion, the
8-colour and 7-bit constraints, and the no-repeat rule.  All headless, on the Stage itself."""
from __future__ import annotations

import math

import pytest

from vuurwag.braai import banter
from vuurwag.braai.buf import LETTERS
from vuurwag.braai.core import Braai, MEAT_LAYOUTS, meat_col
from vuurwag.braai.party import easter, special_day
from vuurwag.braai.stage import Stage
from vuurwag.cli import clock_offset
from vuurwag.collector import DemoRunner
from vuurwag.events import EventEngine
from vuurwag.model import parse_snapshot
from vuurwag.weather import WeatherService

SIZES = [(80, 24), (120, 40), (160, 45), (200, 55)]
ALL_KEYS = [" ", "f", "d", "b", "g", "?", "w", "n", "v", "k", "s", "r", "t", "o", "l", "h", "m", "x", "j", "1", "2", "3", "4",
            "a", "i", "u", "p", "z", "e", "5", "6", "P", "up", "down", "left", "right"]


def make_stage(cols=160, rows=45, seed=3, time_hhmm="21:00", date=None, weather="clear", tmp_path=None):
    ws = WeatherService(mode="demo", forced=weather, cache_file=(tmp_path / "w.json") if tmp_path else None)
    st = Stage(cols, rows, seed=seed, host="pve", weather=ws, clock_offset=clock_offset(time_hhmm, date))
    st.resize(cols, rows)
    return st


def feed(st: Stage, runner: DemoRunner, eng: EventEngine) -> None:
    snap = parse_snapshot(runner.document(), "demo")
    st.on_snapshot(snap)
    for ev in eng.update(snap):
        st.on_event(ev)


def run(st: Stage, secs: float, dt: float = 0.1) -> None:
    for _ in range(int(secs / dt)):
        st.step(dt)


def check_frame(st: Stage) -> None:
    for row in st.b.buf.scr:
        for ch in row:
            assert 32 <= ord(ch) < 127, repr(ch)
    for row in st.b.buf.atr:
        for a in row:
            assert a in LETTERS, repr(a)


# ---- the fire -----------------------------------------------------------------------------------------------------
def test_fire_follows_the_cpu_like_lekker():
    b = Braai(160, 45, seed=1)
    b.start()
    b.skip_boot()
    b.set_host(0.0, "0.1", 100)
    for _ in range(300):
        b.step(0.1)
    assert abs(b.HEAT - 0.45) < 0.03, "an idle host settles at 0.45"
    b.set_host(1.0, "9", 100)
    for _ in range(300):
        b.step(0.1)
    assert b.HEAT > 0.95, "a busy host roars"
    assert b.fire_state() == "roaring"
    b.set_host(0.1, "1", 100)
    b.FAN = 4
    b.step(0.1)
    assert b.FAN < 4
    b.fire_mod("rain", -0.3, b.T + 100)
    for _ in range(300):
        b.step(0.1)
    assert abs(b.HEAT - (0.45 + 0.055 - 0.3)) < 0.03, "rain takes 0.3 off"
    b.fire_mod("rain", -5, b.T + 100)
    for _ in range(300):
        b.step(0.1)
    assert b.HEAT >= 0.05 - 1e-6, "never below the embers"


def test_flames_coals_and_meat_are_drawn_in_the_drum():
    b = Braai(160, 45, seed=2)
    b.start()
    b.skip_boot()
    b.set_host(0.9, "5", 100)
    for _ in range(80):
        b.step(0.1)
    bx, by = b.P["braai"]
    coals = b.buf.text_at(bx + 3, by + 4, 22)
    assert all(c in "*o.:@,;" for c in coals)
    assert set(b.buf.atr[by + 4][bx + 3:bx + 25]) <= {"h", "Y", "R", "r"}
    flames = "".join(b.buf.text_at(bx + 3, by + 2 - k, 22) for k in range(0, 4))
    assert any(c in "^()/\\'`,." for c in flames)
    meat_row = b.buf.text_at(bx, by + 2, 26)
    assert "(@@@@@@@)" in meat_row or "@" in meat_row
    assert "(==)" in meat_row or "(##)" in meat_row


# ---- the meat ------------------------------------------------------------------------------------------------------
def test_meat_cooks_pink_to_brown_and_is_served():
    assert [meat_col(d) for d in (0.1, 0.4, 0.7, 0.95)] == ["M", "R", "r", "y"]
    b = Braai(160, 45, seed=4)
    b.start()
    b.skip_boot()
    b.set_host(0.2, "1", 100)
    seen = set()
    served = False
    for _ in range(2200):
        b.step(0.1)
        d = b.meat_done()
        if d is not None:
            seen.add(meat_col(min(d, 0.99)))
        if b.MEAT_STATE == "served":
            served = True
        if served and b.MEAT_STATE == "cooking" and b.BATCH == 2:
            break
    assert {"M", "R", "r", "y"} <= seen
    assert served and b.BATCH == 2
    assert any("gaar" in line for _t, line in b.log_all)
    assert any("Die vleis is gaar" in m for m in [w for w in b.WALL_Q]) or any("borde" in line for _t, line in b.log_all)


def test_meat_count_follows_the_running_guests():
    for n, lay in MEAT_LAYOUTS.items():
        assert len(lay) == n
        for x, kind, w in lay:
            assert 3 <= x and x + w <= 25
    b = Braai(160, 45, seed=1)
    b.start()
    assert len(b.MEAT) == 3
    b.meat_count = 4
    b.new_batch()
    assert len(b.MEAT) == 4 and b.MEAT[1]["kind"] == "wors"
    b.meat_count = 1
    b.new_batch()
    assert len(b.MEAT) == 1 and b.batch_text() == "1 wors"


# ---- the boot log, the status line, the help -------------------------------------------------------------------------
def test_boot_log_then_the_braai():
    st = make_stage()
    run(st, 0.3)
    txt = "\n".join(st.text())
    assert "vuurwag 4.0 op pve" in txt
    assert "braai: boot op pve" in txt
    run(st, 1.5)
    txt = "\n".join(st.text())
    assert "okes: 3 gevind (koos, sakkie, jannie), 1 hond (wagter)" in txt
    assert "grid0: halfdrom, 22 kolomme, 4 pote" in txt
    run(st, 8)
    txt = "\n".join(st.text())
    assert "Started Braai Daemon." in txt or "o=[######################]=o" in txt
    run(st, 3)
    lines = st.text()
    assert "o=[######################]=o" in "\n".join(lines)
    assert lines[-1].strip().startswith("pve") and lines[-1].rstrip().endswith("q om te loop")
    assert any("vuur aangesteek op pve" in l for _t, l in st.log_lines)
    # the help lists every key
    st.press("?")
    st.step(0.1)
    txt = "\n".join(st.text())
    assert "sleutels / keys" in txt
    for k in ("space", "f", "w", "n", "v", "k", "s", "r", "t", "o", "l", "h", "m", "x", "j", "1", "2", "3", "4", "a", "i", "u", "p", "z", "e", "5", "6"):
        assert ("| " + k.ljust(7)) in txt, k
    st.press("x")           # any key closes the help
    st.step(0.1)
    assert "sleutels / keys" not in "\n".join(st.text())


def test_status_line_drops_fields_on_a_narrow_screen():
    st = make_stage(80, 24)
    run(st, 14)
    last = st.text()[-1]
    assert last.rstrip().endswith("q om te loop")
    assert len(last) == 80


# ---- every key at four sizes, every skit to completion -------------------------------------------------------------------
@pytest.mark.parametrize("size", SIZES)
def test_every_key_at_every_size(size, tmp_path):
    cols, rows = size
    st = make_stage(cols, rows, tmp_path=tmp_path)
    runner = DemoRunner(seed=5, fast=True)
    eng = EventEngine()
    feed(st, runner, eng)
    run(st, 0.5)
    st.b.skip_boot()
    run(st, 2)
    for i, k in enumerate(ALL_KEYS):
        st.press(k)
        run(st, 1.2)
        check_frame(st)
        if i % 5 == 0:
            feed(st, runner, eng)
    run(st, 30)
    check_frame(st)
    assert st.b.T > 60
    # no stage claim is stuck for ever: everything releases within the scene's own timing
    run(st, 120)
    assert not [k for k, until in st.b.BUSY.items() if until > st.b.T + 200]


SKITS = {
    "tannie": ("t", lambda st: st.kuier.tan, 120),
    "oom": ("o", lambda st: st.kuier.oom, 150),
    "eskom": ("l", lambda st: st.kuier.ls["state"] != "off", 260),
    "hout": ("h", lambda st: st.kuier.throw or st.kuier.flare, 40),
    "sokkie": ("k", lambda st: st.party.sok, 40),
    "sing": ("s", lambda st: st.party.sing, 90),
    "rugby": ("r", lambda st: st.party.rug, 60),
    "dokter": ("x", lambda st: st.dokter.v, 80),
    "trick-koos": ("1", lambda st: st.dokter.tr, 40),
    "trick-sak": ("2", lambda st: st.dokter.tr, 40),
    "trick-jan": ("3", lambda st: st.dokter.tr, 40),
    "trick-dog": ("4", lambda st: st.dokter.tr, 40),
    "dominee": ("a", lambda st: st.plaas.sk, 90),
    "selfie": ("i", lambda st: st.plaas.sk, 40),
    "hout-haal": ("u", lambda st: st.plaas.sk, 50),
    "pook": ("p", lambda st: st.plaas.sk, 40),
    "gas": ("z", lambda st: st.plaas.sk, 60),
    "dop-steel": ("5", lambda st: st.plaas.sk, 40),
    "dop-run": ("6", lambda st: st.plaas.sk, 40),
    "raid": ("b", lambda st: st.b.RAID, 30),
    "hat": (None, lambda st: st.weer.hat, 30),
    "egg": ("P", lambda st: st.party.egg or st.party.egg_want, 90),
}


@pytest.mark.parametrize("name", sorted(SKITS))
def test_every_skit_runs_to_completion(name, tmp_path):
    key, active, limit = SKITS[name]
    st = make_stage(160, 45, seed=7, tmp_path=tmp_path)
    runner = DemoRunner(seed=5, fast=True)
    feed(st, runner, EventEngine())
    run(st, 0.5)
    st.b.skip_boot()
    run(st, 3)
    if name == "hat":
        st.weer.w["dir"] = 1
        assert st.weer.hat_start(st.b.T)
    else:
        st.press(key)
    run(st, 0.5)
    assert active(st), f"{name} did not start"
    for _ in range(int(limit / 0.1)):
        st.step(0.1)
        if not active(st):
            break
    assert not active(st), f"{name} never finished"
    check_frame(st)
    # whoever came (Dokter Disk makes his own first round about 20 s in) leaves again, and the stage is calm
    for _ in range(900):
        if not any(w in st.b.P for w in ("tannie", "oom", "dokter", "dominee")) and not st.b.DOG_AWAY and st.b.calm(st.b.T):
            break
        st.step(0.1)
    for who in ("tannie", "oom", "dokter", "dominee"):
        assert who not in st.b.P, f"{who} is still on stage after {name}"
    assert not st.b.DOG_AWAY, f"the brakkie is still away after {name}"
    assert st.b.calm(st.b.T)
    check_frame(st)


# ---- the constraints -------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("size", [(80, 24), (160, 45)])
def test_eight_colours_and_seven_bit_everywhere(size, tmp_path):
    st = make_stage(*size, tmp_path=tmp_path, weather="storm")
    feed(st, DemoRunner(seed=2, fast=True), EventEngine())
    for i in range(400):
        st.step(0.1)
        if i == 20:
            st.b.skip_boot()
        if i % 50 == 25:
            st.press("v")
        check_frame(st)


def test_small_screen_message():
    st = make_stage(50, 12)
    run(st, 2)
    assert "maak die venster groter" in "\n".join(st.text())


# ---- banter ---------------------------------------------------------------------------------------------------------------------
def count_lines() -> int:
    n = 0
    for name in dir(banter):
        v = getattr(banter, name)
        if isinstance(v, list):
            for ex in v:
                if isinstance(ex, list):
                    n += sum(1 for item in ex if isinstance(item, tuple))
                elif isinstance(ex, tuple):
                    n += 1
        elif isinstance(v, dict):
            for ex in v.values():
                if isinstance(ex, list):
                    for e in ex:
                        if isinstance(e, list):
                            n += sum(1 for item in e if isinstance(item, tuple))
                        elif isinstance(e, tuple):
                            n += 1
                elif isinstance(ex, tuple) and len(ex) == 3 and isinstance(ex[2], list):
                    n += len(ex[2])
    return n


def test_phrase_bank_is_big_plaas_and_clean():
    from vuurwag import sayings
    n = count_lines() + sum(len(v) for v in sayings.LINES.values()) + len(sayings.IDLE)
    assert n >= 400, n
    text = " ".join(t for name in dir(banter) for t in _texts(getattr(banter, name)))
    for bad in (" boet", "bru ", "Eish", "eish", "sharp", "Howzit", "howzit"):
        assert bad not in text, bad
    for word in ("reen", "wind", "dam", "windpomp", "skape", "beeste", "koöperasie", "dominee", "melktert", "Klipdrift", "Castle",
                 "rooibos", "Suiderkruis", "jakkals", "Wagter", "Tannie", "Oom"):
        assert word in text, word
    assert all(c.isascii() or c == "ö" for c in text)


def _texts(v):
    if isinstance(v, tuple) and len(v) == 2 and isinstance(v[1], str):
        yield v[1]
    elif isinstance(v, (list, tuple)):
        for x in v:
            yield from _texts(x)
    elif isinstance(v, dict):
        for x in v.values():
            yield from _texts(x)


def test_no_line_repeats_within_ten_minutes():
    b = Braai(160, 45, seed=9)
    b.start()
    b.skip_boot()
    b.set_host(0.1, "1", 100)
    said: list[tuple[float, str]] = []
    last = None
    for _ in range(12000):   # twenty minutes of scene time
        b.step(0.1)
        if b.SAYS:
            key = b.SAYS[0]["lines"][0] + str(b.SAYS[0]["until"])
            if key != last:
                last = key
                said.append((b.T, " ".join(b.SAYS[0]["lines"])))
    assert len(said) > 40
    # the first line of every small-talk exchange (markers stripped; lines with host values vary and are skipped)
    from vuurwag.braai.core import MARK_RE
    firsts = set()
    for ex in b.TALK:
        items = [it for it in ex if isinstance(it, tuple)]
        if items and "{" not in items[0][1] and items[0][0] != "D":     # (a bark is a sound, not a line)
            firsts.add(MARK_RE.sub("", items[0][1]).strip())
    seen: dict[str, float] = {}
    repeats = 0
    for t, text in said:
        if text in firsts:
            if text in seen:
                assert t - seen[text] >= 600 - 1e-6, (text, t - seen[text])
                repeats += 1
            seen[text] = t
    assert len(seen) > 30


# ---- the calendar ------------------------------------------------------------------------------------------------------------------
def test_special_days_and_easter():
    import time as _time
    assert easter(2026) == (4, 5) and easter(2024) == (3, 31) and easter(2025) == (4, 20)
    def lt(m, d, y=2026):
        return _time.localtime(_time.mktime((y, m, d, 12, 0, 0, 0, 0, -1)))
    assert special_day(lt(9, 24)) == "braaidag"
    assert special_day(lt(12, 25)) == "kers" and special_day(lt(12, 26)) == "tweede"
    assert special_day(lt(12, 31)) == "oujaar" and special_day(lt(1, 1)) == "nuwejaar"
    assert special_day(lt(12, 16)) == "gelofte" and special_day(lt(4, 3)) == "paas" and special_day(lt(4, 6)) == "paas"
    assert special_day(lt(7, 14)) == ""


def test_new_year_countdown_burns_the_year_in(tmp_path):
    st = make_stage(160, 45, seed=1, time_hhmm=None, date="12-31 23:59:52", tmp_path=tmp_path)
    run(st, 0.5)
    st.b.skip_boot()
    run(st, 2)
    assert st.party.day() == "oujaar"
    run(st, 3)
    assert st.party.cal.get("cd"), "the last ten seconds of the year count down in letters of fire"
    st.party.off += 10          # (the calendar runs on the wall clock: jump it past midnight)
    st.party.now_at = -1e9
    run(st, 16)
    assert any("gelukkige nuwejaar" in l.lower() for _t, l in st.log_lines)
    check_frame(st)
