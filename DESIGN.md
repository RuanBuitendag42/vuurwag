# Vuurwag v4 — design notes

v4 is an exact copy of `lekker` (the Perl braai by a friend of the user, 8,432 lines, core Perl 5 only), with more
flare and a plaas voice. v1 was widgets, v2 half-block pixel art, v3 a free-form ASCII scene with a director; v4
keeps v3's data layer (probe, model, collector, events, weather) and replaces the whole scene with a port of
lekker, extra by extra. The user runs the two side by side, so where in doubt lekker's choice stands.

## 1. lekker inventory

### Mechanics (core)
- **Frame buffer**: two strings, one byte per cell: characters and colour letters. `blit` (text + colour string,
  clipped), `put` (one colour), `plot` (a cell), `draw` (a sprite). Every frame is cleared and fully redrawn; the
  flush sends only changed stretches of changed rows (short gaps sent along), the whole screen every 30 s and after
  a resize; colour changes only when they change; blanks keep the current colour unless it has a background; the
  cursor parks at row 2 so echoed keys land under the next frame. v4: `braai/buf.py` keeps the buffer, Textual's
  compositor and a per-row cache (`StripCache`) take the diff role.
- **Sprites**: art + mask, segments `[row, col, text, colours]`; `?` transparent; a one-letter mask row colours the
  row; spaces inside a row are opaque; default colour per sprite. Mirroring swaps `/\()<>[]{}` and backtick/quote.
- **Palette**: `r R g G y Y b B m M c C w W .` (bright = bold + 30..37), `v` reverse, `h` bold yellow on red.
  `--green`/`g`: every letter becomes green, bright = bold, `v` = green reverse. v4 adds `--truecolor` (shades only).
- **Host facts**: `/proc/stat` (busy minus idle and iowait, sampled once a second), `/proc/loadavg`, `/proc/uptime`
  (the log stamp `[%9.2f]` is uptime), uname, `$USER`. v4: the probe's snapshot (`braai/node.py`).
- **Layout** (per size): `small` under 60x18; ground depth `gd = 2 + (rows-24)//4` (1 under 20 rows); `base = rows-2-gd`,
  `top = base-9`; Jannie only at >= 80 cols, the dog at >= 66; elbow room 4/2/0 at >= 140/90 cols; group width
  `55 + dog(9+g) + g + jan(14+g)` centred; braai at Koos+15, dog at Koos+43+g, Sakkie after the dog; moon big at
  >= 26 rows, at `(cols-mw-6, 2|1|0)`, slid right on short screens to leave a 20-wide bubble per head; Southern Cross at
  `(cols*0.12+16, 3|1)`; thorn tree big (46 wide, needs base >= 20) or small (21, base >= 14) left of the group; tower
  (12) and bakkie (36) centred in the room right of Sakkie, bakkie alone, or tower alone; top(1) table at >= 40 rows
  (`1 + okes` rows, root too at gd >= 7); ground texture (grass row `" , '`, tufts `\|/`, stones; thinner on big
  screens); the Milky Way band from bottom-left to top-right (`.`/`:` in dark blue), stars (<= 130) avoiding the moon
  and the cross.
- **Sky**: dust, stars breathing on their own phase (`* W / . W / . w / . b`), the cross twinkling `+`, moon, a
  shooting star (`*------....`, 60 cols/s down-left, every 20-60 s).
- **Scenery**: tree, bakkie, tower with the host name (8 or 10 characters, cut at `-`), power light, disk light
  busier with CPU; the ground line `_` and the firelight flickering `R/r` within `15 - 3*depth + 5*heat` of the braai.
- **Status line**: `host · load · up · cpu · fire lekker|hot|roaring · meat N%|gaar|served · extras · [stamp] log`,
  blinking reverse cursor, `q to leave` right; a fresh log line (5 s) outranks the numbers; priorities drop fields
  on narrow screens; the stamp goes first, then the message is cut at a word with `...`.
- **Braai**: 22 coal cells each on its own phase through `* o . : * @ , o ; * .`, colours `h` (white-hot, when heat >
  0.55), `Y`, `R`, `r`; flames per column `h = 1.5 + 2*heat + sin(6.1t + 1.1i) + 0.6 sin(9.7t - 2.3i) + noise`, max 5
  rows, glyphs `^()/\` at the root, `()^'` mid, `'.`,)(` at the tip, colours `Y / Y|R / R / r`; the meat row at
  `by+2`: `(==)`/`(##)` (the chop Koos turns), `(@@@@@@@)` wors sizzling `@` in red, pink `M` -> `R` -> `r` -> `y`.
- **Heat**: `want = fan ? 1 : 0.45 + 0.55*cpu` plus fire mods, clamped 0.05..1, eased `1 - e^(-dt/2.5)`; a busy host
  (cpu > 0.85 for 3 s) gets a wall every 2 min and Koos flips.
- **Smoke**: puffs `. o () ( ) (  ) (   ) .   . '   '` by age, rate `1.2 + 3.5*heat`, drift `wind*(0.3 + age/2.5)`,
  `wind = 1.1 sin(t/17) + 0.5 sin(t/5.3) + 0.5 + extras`; sparks when `rand < heat^2 * 0.5`.
- **Meat**: 3 pieces (chop 5, wors 10, chop 20), rate `(0.5+heat)/55` first batch then `/75`; gaar -> log + wall
  "Die vleis is gaar!" + "Vleis is reg! !serve" -> served at +40 s (or 2.5 s after the line) -> new batch after 6 s.
- **People**: per oke `rest`/`act` sprites, eye row/col with `open shut left right wide laugh` (plus `pt_up pt_star
  pt_wince dk_up dk_dizzy`), mouth open/shut when talking (`int(7t) % 3`), blinks every 2.5-7.5 s for 0.18 s, acts
  every 7-16 s (Koos flips: chop side toggles, done += 0.02, "flip #n"; Sakkie/Jannie sip, every third sip is a dop),
  listeners look toward the speaker, Jannie dozes after 40-70 s of calm (`zZZ`, "power-save mode") and wakes on
  noise. Poses from extras override the sprite until `pose_to`; `dx dy` move him; `hide` removes him.
- **The brakkie**: sits wagging (3 fps, 8 when excited); raid every 180-300 s (or `b`): creep 1 s, jump 1 s behind the
  braai, chop in mouth, run off right 2.2 s, gone 3 s, trot back 3 s, wag hard; Koos "HEY! Los dit, hond!", the others
  laugh; log "state D -> R".
- **The dop**: `!toss` Jannie throws `[#]` to Sakkie in an arc over the flames (1.3 s), Sakkie sips at once.
- **Banter**: exchanges `[cond?, [who, text]...]`, `K S J D` (+ `T O X H U` from extras; v4 adds `P`), `S+J` chorus,
  `S|J` whichever is here; `{up} {load} {cpu}` filled or the exchange skipped; markers `!flip !toss !salute !serve`
  (+ extras'); "lekker" makes the non-speakers sip; shuffled deck, 30 % hot lines when cpu > 0.5; a bubble lasts
  `1.8 + 0.07*len`, wrap 30 (24 under 100 cols); `@PRIO` plays first; `say_now` interrupts.
- **Bubbles**: cowsay `_` rule, `< >` or `/ | \`, `-` rule, tail `\ | /` to the head, lifted 0..2 rows and slid sideways
  to keep clear of `@AVOID` (moon, tree, tower, bakkie, owl, radio, egg, monitor) and other bubbles.
- **wall(1)**: queued, shown when nobody talks, 6 s, `Broadcast message from user@host (pts/0) (Day Mon D HH:MM):`
  over the top rows in `W`, the message in `Y`.
- **top(1)**: `PID USER PR NI S %CPU TIME+ COMMAND`, root `braaid --grid=0 --coals`, koos `tongs --flip
  --moenie-prik`, sakkie `dop --sip --count=N`, jannie `cooler --sit [--zzz]` (PR 39 NI 19), brakkie `beg --for=wors`
  / `steal --chop --fast`; state `R S I D`; header reverse, running rows bright.
- **Boot**: `lekker 3.0 on host`, `braai: booting on host (kernel)`, `okes: 3 detected (...), 1 dog`, `grid0:
  half-drum, 22 cols, 4 legs`, `coals: lighting .... ok`, `meat: 1 wors, 2 chops (raw)`, `cooler0: 24 dops, mounted
  read-only`, every extra's lines stamped `[%12.6f]`, `[  OK  ] Reached target Braai.`, `Started Braai Daemon.`;
  2.6 s + 0.25 s per extra line; any key skips it.
- **Keys** (core): `space f d b g ?`; any key closes the help; `keyseq` hooks see keys first (the Konami code);
  arrows are tokens `up down left right`.
- **Help**: `lekker 3.0 -- sleutels / keys`, one or two columns, wrapped, `(more with a bigger window)`.
- **Stage**: `claim(name, t, secs)` fails while another claim is live; `calm`; `auto_ok` (after 40 s, calm, nobody
  talking, no wall) and `auto_done` (gap 25-45 s) pace the surprises.

### Extras, hooks and keys
Hooks: `layout update sky scenery back actors front overlay status boot keyseq cleanup`; keys: `key(k, help, fn)`.
- **10-weer (`wx_`)**: `w` (helder -> winderig 150 s -> bewolk 180 -> reen 180 -> storm 120 -> helder, a reenboog
  when the sun is up), `n` (real -> aand 75 s -> nag -> dagbreek 60 s -> dag). Sunrise/sunset from declination and
  the equation of time (Johannesburg; v4: the place), phases dagbreek/dag/aand/nag with progress and the sun's arc
  (right to left, highest a little under the sky top, red low, gold higher, rays by day, hidden below the okes'
  hats); DAYLIGHT 0..1 eased; the moon's age from a known new moon, lit from the left when waxing, drawn into the
  outline; stars/dust fade through dusk and dawn; glow streaks (`- ~ _`) in `Y y R r M m b`; clouds fair/rain/storm
  (counts per state and width, drifting with the upper wind, fading in/out, pink at sunset, lit white by lightning,
  the struck cloud in reverse); rain from cloud bottoms (`| / \` by wind, streaks of 4/5, blue-cyan), splashes,
  puddles (`~-~~-~-~`, growing with wetness), hiss `sss` and steam on the coals, the umbrella (shaft from Koos's hand,
  canopy shut/half/open, Bokke green and gold, drops stopped at its top); gusts every 1.5-6 s, leaves, tolbos (every
  30-60 s in wind, hopping), the hat (gust to the right, spinning frames, the brakkie runs after it and trots back
  wearing it, or the wind turns and brings it back); lightning (path with a branch, 2 wide, flicker, 0.45 s), thunder
  `KABOOM!`/`rrrommel...` shaking with a burst, wide eyes, Jannie woken, the brakkie under the bakkie/braai shivering
  with `o'')`; rainbow: 6 arcs in `r Y G C B M` opposite the sun for 50 s; critters: fireflies low over the grass at
  night, the uil in the tree (blinks, winks, `hoe-hoe` typed out, box in AVOID), bats (`/^v^\ \_v_/`), birds by day
  (`\v/ -v-` in a V), hadedas (2-3, wings up/down, mirrored, `HAA-HAA-HADEDAA!` at 30 % across, at dawn and every
  10-25 min), muggies (3 around a head, `bzzz`, KLAP, 2 killed 1 escaped); auto surprises (own weather every
  15-40 min, hadeda, muggies). Status `weer: ...`, `tyd: mode`; boot `weer: barometer...`, `maan: ... son op/onder`.
- **20-party (`pt_`)**: `v` salvo of 4-6 rockets (peony, ring, willow, crackle, palm, double, heart; palettes gold
  red green blue cyan pink white bok; drag, gravity, trails, bangs `BOEM! KRAK! KABOEM! POEF! PAF!`), the okes look up,
  the brakkie bolts under the bakkie/braai (flat/curled, shivering) and trots back; letters of fire (two block fonts,
  pixels lit by sparks swirling up from the fire, flickering `#@%&` in `h Y R W`, crumbling to embers and smoke);
  the egg (`P`/Konami: the sky clears in an ellipse, `braai-plek.co.za` burns, a barrage, TOET! TOET! from the bakkie,
  BRAAI-PLEK! cheer, the tag line as a wall); the radio (bakkie window `|=|`, tower LED, or a boombox
  `[(o):=:(o)]` with notes rising); `k` sokkie 19 s (two-step poses, hips `dx`, hops, Koos with the tongs, Jannie off
  the cooler which stays drawn, the brakkie chasing his tail, laughs every 6 s); `s` songs line by line with
  `!pt_vals` (Jannie off-key, the others wince, the brakkie howls), swaying, notes from the singers; `r` rugby 37 s
  (the radio commentary, score in the status line `Bokke 17 - 14 All Blacks (52')`, a `<=>` ball passed over the fire,
  a penalty, DRIE! with a jump, Sakkie's dop spilled `[#]` and a splash, FWIEEEET!, the salute); the calendar (24 Sep,
  5 Nov, 24-26 Dec red hats, 31 Dec countdown `TIEN!`..`EEN!` in fire, midnight: the year burns, 12 rockets, wall,
  1 Jan party hats; salvos every 10-20 min on those days; a song by itself every 45-90 min).
- **30-kuier (`kv_`)**: `t` Tannie Sarie (bun, glasses, magenta dress, apron) walks in from the left with pap en
  sous / slaai / melktert (steam `~`), greets, puts the dish down (`\@@@/` on the grass, warm for 2 min), opinions
  (meat too done / raw, Sakkie's dops counted, the wasgoed, groente, the tongs borrowed and clicked `--==<`/`--==-`
  while Koos stands hands on hips, "jy draai te veel om", the dog's wors, the gasstoof), Jannie ordered up off the
  cooler (jumps, stands behind it), waves, walks out, Jannie sits again; `o` Oom Faan's red bakkie drives in from the
  left `sl`-style (TOET-TOET! ahead of it, hubs spinning, headlights at night, dust), parks beside Sakkie (or round the
  corner), Oom (wide hat, grey moustache, khaki, belly) climbs out with the cooler, "Naand manne! Ek het ys gebring",
  the cooler on the ground `[__]/|__|`, one tall story (koedoe, kabeljou, leeu, vuurhoutjies, 800 000 km, Ellispark
  '95), sips, "die tannie wag", drives off faster and faster; `l` Eskom: the wall "Stage N beurtkrag vanaf nou tot
  HH:MM", the town goes dark block by block from a random substation, POWER off (the tower's lights blue), the extra
  stars and more Milky Way come out, a generator at the house5 `brrrrr`, the mast's red light on battery until it
  dies, "krag terug" with windows flickering on, every 1-3 hours by itself; `h` hout: Jannie (or Koos) throws a log
  `o== / ==o` in an arc, sparks, the log burns down in the coals (`=`/`*`), fire +0.35 each, three logs or a hot fire
  -> flare-up (tall flames over the meat), Koos's wide eyes, "Oeps! Te veel hout!", he lifts his dop and douses it
  (drops, steam, "1 dop, water, mostly"); `m` meer vleis: sosaties `-#o#` / `-#o#*#o#-`, mielies `<::)`, broodjies
  `[==]`, snoek `><'>`, with their own colours by doneness, dropping onto the grid with a tsss, spinning when
  flipped, carried off by the brakkie; the town (kafee, house5 with the generator, church, water tower, mast,
  houses, flats, lamps) in rows base-3..base-1 in the margins, lit windows `Y/y` by night, a window flicking every
  4-10 s; a taxi (`(o__o]`, hooting `toet toet`) or bakkie on the far road every 3-6 min, hidden behind the group.
- **40-dokter (`dk_`)**: smartctl in a forked child (list form, timeouts, its own process group, niced), SMART
  health per disk (`ok sick sleep skip`, temperature, why: FAILING, reallocated/pending/uncorrectable sectors, NVMe
  critical warning, media errors, worn out, grown defects), a short self-test when the disk's own log shows none in
  23 power-on hours (v4: **never**); the dokter (white coat, head mirror `(O)`, stethoscope, bag `|_+_|`) walks in from
  the nearer side at 14 cols/s, carries a drive stack `[sda   o]` or listens at the tower (the tower shows a
  heartbeat), the monitor `.-[+] DOKTER DISK---.` with an ECG per disk (`__/\_/\___` green, sick red and jagged,
  sleep `z`, skip `- -`, wait `. .`), temperatures at >= 100 cols, `SIEK!` flashing in `h`; the verdict ("Gesond soos 'n
  perd!", "Oei! sda is siek: ...", a wall for a sick disk, "koorsig" over 60 C), the summary in the log; the brakkie
  runs from the "vet" (`Woof?!`) and trots back after; 20 s after boot, then every 24 h, and on `x`; `j` jokes (16)
  with `!dk_laugh` (the others laugh at once, the teller after 1.2 s); tricks `1` double flip (the chop twice as
  high, spinning, a star at the top; every other time the 1995 story and the chop falling out of the sky, still
  raw), `2` Sakkie lifts and flattens the can `>=<` on his forehead, KRAK!, stars circling, `3` Jannie tips back,
  boots in the air, hat up, "Ek's orraait!", `4` the brakkie plays dead (`(x'')`, a paw twitching) until there is talk
  of his wors.

### Banter categories
Small talk (with conditions raw / almost / wind_l / wind_r / roaring), hot lines, the weather pools per state
(played when the weather turns and pumped every 40-65 s), tolbos, rainbow, hat, thunder, muggies, hadeda, uil,
time of day; party talk, songs (public domain only), rugby commentary, refusals ("Wag, boet! Een ding op 'n slag");
Tannie's greetings per dish, opinions, goodbyes; Oom's stories, greetings; Eskom dark/restore; wood, flare, menus;
dokter hellos, quips, verdicts, vet lines, jokes, tricks, disk banter. v4 rewrites all of it in the plaas voice
(`braai/banter.py`, `sayings.py`) and adds the farm's own (`PL_*`).

## 2. v4 architecture

```
Stage (braai/stage.py)                       the app's one object
  Braai (braai/core.py)                      the core: buf, P, ST, MEAT, SAYS, hooks, keys, step(), draw_scene()
    Weer (braai/weer.py)    hooks + keys w n   + weather_fn (Open-Meteo), latlon, clock offset
    Party (braai/party.py)  hooks + keys v k s r P + the extended calendar
    Kuier (braai/kuier.py)  hooks + keys t o l h m
    Node  (braai/node.py)   hooks boot/status, top rows, meat count, events -> wall/log/PRIO
    Dokter (braai/dokter.py) hooks + keys x j 1-4 + disks_fn (the probe's SMART)
    Plaas (braai/plaas.py)  hooks + keys a i u p z e 5 6
Scene widget (widgets/scene.py): tick at fps, stage.step(dt), StripCache -> only changed rows refreshed
VuurwagApp (app.py): collector -> stage.on_snapshot / on_event; keys -> stage.press; ansi_color=True
```

Shared state between extras is the same as lekker's: `P`, `ST`, `SAYS`, `talk_q`, `PRIO`, `WALL_Q`, `BUSY`, `SKY`,
`POWER`, `DAYLIGHT`, `DOG_AWAY`, `CAST`, `HEAD`, `MARK`, `COND`, `FILL` (new: `{temp} {wood} {stage}`), `MEAT`,
`FIREMOD`, `WIND_ADD`. Extras keep lekker's prefixes as class names and method names.

### What changed on purpose
- Meat pieces: 1..4 per batch from the running guests (`MEAT_LAYOUTS`); `MEAT[-1]` is the brakkie's piece.
- **The top(1) table height rule** (lekker's table, with the node's guests taking precedence): shown at >= 40 rows,
  in the ground rows `base+2 .. ROWS-2` (`gd - 1` rows, header included; the grass row under the feet stays clear,
  as in lekker). The data rows are, in this order, `1 root braaid` (only when `gd >= 7`, as lekker), **every guest** (containers and VMs, `lxc` or `qemu` in the COMMAND column)
  (running ones sorted by cpu, then the stopped ones), then the okes (koos, sakkie, jannie, wagter) as space
  allows. From 158 columns (`2 * 69 + 20`, i.e. at 160x45 and up) the table is two tables side by side (each with
  its header, 2 columns apart), so a node with up to `2 * (gd - 2)` rows shows everything: at 160x45 that is 10 data
  rows (the live node: root, 7 guests, 2 okes), at 200x55 14 (root, 10 guests, 3 okes). Under 158 columns one table:
  at 120x40 four rows, i.e. the busiest guests and no okes. The table is laid out again when the guest count changes;
  the plaasdam and kraal make way for it.
- `fill()`: extras register placeholders; the ten-minute no-repeat rule applies to `PRIO` exchanges too (the serving
  line always plays).
- `mis` is a sixth weather state (`w` cycles through it); Open-Meteo sets the state, direction and strength when it
  is on, and lekker's own random episodes are switched off while it is.
- Dokter Disk never runs smartctl himself; the ECG has a `warm` trace (yellow) for a disk in the warm band.
- Screenshots: `App.export_screenshot` uses an xterm terminal theme (black, the 16 xterm colours) so the SVGs show
  what a real console shows; `gfx/svg.py` still fixes padding and ligatures.
- Keys dropped from v3: `c`, `t` (TV), camera keys, digits as guest picks (digits are lekker's tricks now).

### Measured
10 fps default. Headless scene work per frame: 80x24 0.4 ms, 120x40 0.75 ms, 160x45 1.0 ms, 200x55 1.3 ms
(the Perl original is 10 fps as well). Tests: 103, about 48 s.

## 3. Feature inventory (moved here from the README)

### What was copied from lekker (1:1)

- **The art**: Koos (bush hat, beard, tongs; rest and flip poses), Sakkie (cap, blue jersey, dop), Jannie (floppy hat,
  on the ICE koelboks), the brakkie (sit, trot, run), the half-drum braai, the moon (two sizes), the Southern Cross
  with its Pointers, the thorn trees (two sizes), the host's tower with its name and disk light, the parked bakkie,
  Tannie Sarie, Oom Faan and his red bakkie, Dokter Disk (every pose, mirrored), the sokkie poses, the Christmas and
  party hats, the sun (day, gold, low), the moon phase outline, the clouds (fair, rain, storm), Koos's umbrella and hat,
  the uil, the hadeda, bats, birds, the tolbos, the town templates, the tiny taxi and bakkie on the far road.
- **The mechanics and timing**: the layout rules per size (Jannie needs 80 columns, the brakkie 66, the tree, tower
  and bakkie only when there is room, the moon dodging the speech bubbles on short screens), the coal and flame rules
  (two travelling waves and noise per column, yellow root / red / dark red tip, white-hot coals when it roars), the
  heat following the CPU (`0.45 + 0.55 * cpu`, 2.5 s easing, the fan key, the fire mods), `sl`-style smoke bending with
  the wind, sparks, the meat cooking pink -> brown (about a minute for the first batch, "gaar" -> wall broadcast ->
  served -> new batch), blinks, sips, flips, the dop thrown over the fire, Jannie dozing off (`zZZ`), the brakkie's chop
  raid (creep, jump, run, back looking innocent), the stage (claims, calm, the auto surprises with a gap between them),
  cowsay bubbles that slide clear of the moon, the scenery and each other, the dmesg-style kernel log in the status
  line (stamped with the host's uptime, field priorities dropped on narrow screens), `wall(1)` broadcasts, the
  `top(1)` table on tall screens, the boot log with `[  OK  ]` lines and a blinking cursor, the help card, the
  "make the window bigger" message, the 10 fps default, and only changed rows going to the terminal.
- **The extras**, hooks and all: the weather and time of day (real sunrise/sunset, moon age and phase as seen from
  the south, dusk glow streaks, gusts, leaves, tolbos, hat chase with the brakkie fetching it, rain with splashes,
  puddles, a hissing fire and the umbrella over the meat, lightning with KABOOM and the brakkie under the bakkie,
  the rainbow in six ANSI colours, fireflies, uil, bats, birds, hadedas at dawn, muggies and a KLAP); the party
  (vuurwerk with peonies, rings, willows, crackle, palms and hearts, the letters of fire, the Konami/`P` egg, the radio
  in the bakkie/tower/boombox, the sokkie, the songs, the Springbok test on the radio with the score in the status
  line, the special days with hats and the Oujaar countdown in letters of fire); the kuier (Tannie Sarie and her
  dishes and opinions, Oom Faan's bakkie, stories and ice, Eskom with the town going dark block by block, the
  generator, the dead cell mast and the extra stars, hout on the fire and the flare-up Koos douses with his dop, the
  other meats, the town on the horizon with lit windows, the far road); Dokter Disk (the walk-in, the drive stack or
  the tower, the ECG bedside monitor, the verdict, the vet scare for the brakkie), grappe with laughter and the four
  tricks.
- **The palette and the console constraint**: pure 7-bit ASCII, the 8 ANSI colours with bright = bold, reverse
  video for the log cursor and the top header, a white-hot coal as bold yellow on red; `--green` phosphor; only the
  rows that changed are sent (Textual's compositor takes lekker's diff role).

### What was added on top

- **The node, in lekker's idiom** (`braai/node.py`): the CPU drives the fire exactly as lekker's `/proc/stat` did;
  load and uptime stamp the log and the status line (`lxc 8/10`, the hottest sensor); the boot log carries the node's
  facts (pve version, kernel, cores, RAM, the running guests (CT and VM counts), disks with temperatures, storages with free space,
  firewall, tailscale, updates); the `top(1)` table lists the guests under the okes (vmid, name, state, cpu, uptime,
  mem, tags); the pieces on the grid follow the running guests (1 to 4 at the next batch); node events become
  `wall(1)` broadcasts and dmesg lines with Koos's comment (guest start/stop, backup finished/failed, disk warm or
  sick, storage low, firewall down, tailscale offline, updates waiting, a reboot = Eskom was here and the town goes
  dark, a dead probe = the fire burns low until it answers). **Dokter Disk reads only**: his verdict comes from the
  SMART facts the probe already read with `smartctl -a`; he never starts a self-test (lekker's `--no-disk-test`
  behaviour, always).
- **Open-Meteo drives the weather states**: clear/partly -> helder, wind over 28 km/h -> winderig, cloudy/overcast ->
  bewolk, drizzle/rain -> reen, thunderstorm -> donderstorm, fog -> mis (a new state: streaks over the laagte, no
  sun, the fire sulking). The real wind direction and strength set the smoke, leaves and the windpomp; the
  temperature is on the status line and in the banter (`wx_koud` under 8 C, `wx_warm` over 30 C). `w` still steps
  through the states by hand and the real weather takes over again afterwards. Sunrise and sunset use the place's
  latitude and longitude.
- **Die plaas** (`braai/plaas.py`): a windpomp on the koppie that turns with the wind, the plaasdam reflecting the
  moon, the kraal with the skape in it at night, the plaashek, sheep and cattle on the koppie by day, hoenders
  scratching in the werf, a donkie that stands and looks, a hadeda walking the lawn, a jakkals calling at night
  (Wagter answers), embers drifting off the coals with the wind and a burst of sparks on `f`; and the skits: the dop
  run, Koos chasing Wagter when he steals a chop, fire poking, the gas-vs-hout argument, Wagter stealing a sleeping
  Jannie's dop, Jannie fetching hout from the houtstapel, the selfie with a flash, and the dominee arriving at the
  wrong moment (speaker `P`).
- **More special days**: Boxing Day (Tweede Kersdag), Geloftedag, Vryheidsdag, Werkersdag, Jeugdag, Vrouedag,
  Menseregtedag and the Paasnaweek (computed), next to lekker's Braaidag, Guy Fawkes, Kersfees, Oujaar and Nuwejaar.
  Preview with `--date 12-31 23:59:50`.
- **The voice**: every line (banter, bubbles, dmesg, wall, boot log, help, status) rewritten for the plaas: Afrikaans
  first, SA English second, "Ons soek reen", "Die wind is uit die weste", the koöperasie, the NG kerk basaar, melktert
  and koeksisters, pap en sous, Klipdrift and Coke, Castle, rooibos, Oupa se stories, the Suiderkruis, the jakkals.
  No "boet", "bru", "eish", "sharp" or "howzit". The brakkie is **Wagter** (pid 104). About 640 lines, event-keyed, and
  no line is repeated within ten minutes (the extras' lines included).

## 4. Layout of the code

```
vuurwag/
  probe/probe.py      the host-side collector (stdlib only, streamed over ssh; reads SMART, never tests)
  model.py            typed Snapshot + parser
  collector.py        Local / Ssh / Demo runners and the async Collector loop
  events.py           snapshot diffing -> events
  sayings.py          Koos's event lines, plaas voice, ten-minute cooldown
  weather.py          Open-Meteo client, cache, place fallback, demo cycle, sun and moon
  braai/buf.py        lekker's frame buffer: a character and a colour letter per cell; sprites; strips
  braai/art.py        the core art, 1:1
  braai/core.py       the stage: layout, people, brakkie, braai, meat, smoke, talk, wall, top, boot, help, keys, hooks
  braai/banter.py     every exchange, in the plaas voice
  braai/weer.py       weather and time of day (lekker's 10-weer) + Open-Meteo
  braai/party.py      vuurwerk, letters of fire, radio, sokkie, sing, rugby, calendar (lekker's 20-party)
  braai/kuier.py      Tannie, Oom, Eskom, hout, meat, the town, the road (lekker's 30-kuier)
  braai/dokter.py     Dokter Disk (reading only), grappe, tricks (lekker's 40-dokter)
  braai/plaas.py      the farm: windpomp, dam, kraal, hek, critters, embers, the new skits
  braai/node.py       the Proxmox facts in lekker's idiom
  braai/stage.py      the core with every extra plugged in
  widgets/scene.py    the Textual widget: fixed frame rate, only changed rows refreshed
  app.py              Textual app wiring, keys straight to the stage, xterm-palette screenshots
  cli.py              argparse entry point: run / --once / --screenshot / serve
tests/                pytest: probe, model, events, weather, the frame buffer, the fire rules, the meat, the boot log,
                      every key at four sizes, every skit to completion, the 8-colour and 7-bit constraints, the
                      no-repeat rule, the calendar, the app
deploy/               systemd units, foot.ini, vuurwag.env.example, getty drop-in (install.sh at the root)
screenshots/          SVGs (--screenshot, demo data)
requirements.txt      pinned, hashed runtime deps (uv export from uv.lock) for install.sh
DESIGN.md             the lekker inventory and what v4 changed
```
