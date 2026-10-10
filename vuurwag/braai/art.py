"""THE ART of the core, lifted 1:1 from lekker.  People are 10 rows tall; row 9 is the ground row ("base").
Colours: G green, B blue, R red, y brown/khaki, Y yellow, c cyan, W white."""
from __future__ import annotations

from .buf import sprite

# Koos, the braaier (facing right): bush hat, beard, the tongs.
# Rest pose: tongs on the grid.  Flip pose: tongs up, turning a chop.
KOOS_REST = sprite(r"""
      ____
    _|____|_
     (o  o)
      \ww/
   .-'`--'`-.  __==<
  / |      |\_/
  \ |  ..  |
   \|______|
    |__||__|
    (__)(__)
"""[1:], """
      yyyy
    yyyyyyyy

      yyyy
   GGGGGGGGGG  ccccc
  G GGGGGGGGGGG
  G GGGGGGGG
   GGGGGGGGG
    yyyyyyyy
    yyyyyyyy
"""[1:], ".")

KOOS_FLIP = sprite(r"""
      ____
    _|____|_      ,=<
     (o  o)     _//
      \ww/    _//
   .-'`--'`-./'
  / |      |
  \ |  ..  |
   \|______|
    |__||__|
    (__)(__)
"""[1:], """
      yyyy
    yyyyyyyy      ccc
                ccc
      yyyy    GGG
   GGGGGGGGGGGG
  G GGGGGGGG
  G GGGGGGGG
   GGGGGGGGG
    yyyyyyyy
    yyyyyyyy
"""[1:], ".")

# Sakkie (facing left): cap, blue jersey, a dop in his hand.
SAK_REST = sprite(r"""
      ___
    =[___]
     (o o)
      \_/
   .-'   '-.
  / |     | \
 [#]|     | |
    |_____|
    |  |  |
    (__|__)
"""[1:], """
      BBB
    BBBBBB


   BBBBBBBBB
  B BBBBBBB B
 YYYBBBBBBB B
    BBBBBBB
    wwwwwww
    yyyyyyy
"""[1:], ".")

SAK_SIP = sprite(r"""
      ___
    =[___]
  [#](o o)
   \\ \_/
   .\'   '-.
    |     | \
    |     | |
    |_____|
    |  |  |
    (__|__)
"""[1:], """
      BBB
    BBBBBB
  YYY
   BB
   BBBBBBBBB
    BBBBBBB B
    BBBBBBB B
    BBBBBBB
    wwwwwww
    yyyyyyy
"""[1:], ".")

# Jannie (facing us): floppy hat, sits on the cooler box, dop on his knee.
JAN_REST = sprite(r"""
     ___
   _(___)_
    (o o)
     \_/
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

JAN_SIP = sprite(r"""
     ___
   _(___)_
    (o o)[#]
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
         YYY
         RR
  RRRRRRRRR
 R RRRRRRR
 R RRRRRRR
yyyyyyyyyyy
C    WWW    C
CCCCCCCCCCCCC
"""[1:], ".")

# The brakkie (a small dog).  He sits facing the braai, two tail positions;
# trots back facing left; and runs off to the right with a stolen chop.
DOG = [sprite(a, "\nWWW", "Y") for a in (r"""
  __??????_
o'')}____//
 `_/      )
 (_(_/-(_/
"""[1:], r"""
  __
o'')}____
 `_/     \\)
 (_(_/-(_/
"""[1:])]

DOG_TROT = [sprite(a, "\nWWW", "Y") for a in (r"""
  __??????_
o'')}____//
 `_/      )
 (_(_/-(_/
"""[1:], r"""
  __?????_
o'')}____/
 `_/      )
  /_/ \_\
"""[1:])]

DOG_RUN = [sprite(a, "\n        WWW", "Y") for a in (r"""
__??????__
 \\____{(''o
 (      \_'
  \_)-\_)_)
"""[1:], r"""
_???????__
 \_____{(''o
 (      \_'
 //     \\
"""[1:])]

# The half-drum braai: grid on top, coals in the drum, legs below.  The
# three empty rows above the grid are for the meat and flames (drawn live).
BRAAI = sprite(r"""



o=[######################]=o
  \                      /
   `-.________________.-'
     /|              |\
    /_|??????????????|_\
"""[1:], """



WWwwwwwwwwwwwwwwwwwwwwwwWW
  w                      w
   wwwwwwwwwwwwwwwwwwwwww
"""[1:], ".")

# the moon (a small one for short screens), and the Southern Cross with its two Pointers
MOON = sprite(r"""
   _..._
 .'   .::.
:    ::::::
:    ::::::
`.   '::::'
  `-...-'
"""[1:], None, "Y")

MOON_S = sprite(r"""
 .--.
(  .::)
 `-::'
"""[1:], None, "Y")

# (x, y) offsets: Gacrux, Mimosa, Delta, Epsilon, Acrux; then Hadar and
# Alpha Centauri, the Pointers.  Terminal cells are twice as tall as wide.
CROSS = [(6, 0, "*"), (1, 3, "*"), (11, 2, "*"), (9, 4, "."), (7, 6, "*"), (-6, 5, "*"), (-14, 6, "*")]

# a bakkie (pickup) parked on the right, for very wide screens
BAKKIE = sprite(r"""
                    ________
                   /   |    \
  ________________/    |     \_____
 |                |    |     |    `-.
 |  ____          |    |     |  ____ |
 |_/    \_________|____|_____|_/    \|
 '-\ () /--------------------\ () /-'
     `--'??????????????????????`--'
"""[1:], """
                    cccccccc
                   c   c    c
                  c    c     c
 R                                  Y
 R
                                     Y

"""[1:], "w")

# the host itself, a tower with its name on it, brought along to the braai;
# its disk light follows the CPU
TOWER = sprite(r"""
.----------.
|[        ]|
| o o  .:: |
|----------|
| [======] |
| [======] |
|  ::::::  |
'----------'
"""[1:], """


  G    bbb


w
   bbbbbb
"""[1:], "w")

# flat-topped thorn trees: a big one for very wide screens (the trunk is
# at columns 26-31) and a small one for medium ones
TREE = sprite(r"""
             __..--~~~~--..__    _..-~~-._
      __..--~~  ~~~  ~~  ~~  ~~--~~ ~~  ~~ ~-._
   _-~  ~~~  ~~  ~~~  ~~  ~~~  ~~  ~~~  ~~  ~~-_
  (__ ~~  ~~~  ~~  ~~~  ~~  ~~~  ~~  ~~~  ~~ __)
     ~~--..__..--~~-.__ ~~-._ _.-~~ _.--~~~~
                 `\  \ \  \ \/ /  / /  /'
                   `\ \ `\ \  / /' / /'
                     `\ \ `\  /' / /'
                       `\ \ \/ / /'
                         `\    /'
                          |    |
                          |    |
                          |    |
                          |    |
                          |    |
                         /      \
                     ___/  /  \  \___
"""[1:], """




y
y
y
y
y
y
y
y
y
y
y
y
y
"""[1:], "g")

TREE_S = sprite(r"""
   _.-~~-._.-~~~-._
 .~ ~~ ~~~ ~~ ~~~ ~~.
(_ ~~ ~~~  ~~ ~~~ ~_)
 `~-._\ \ \/ / /_.-~'
      `\ \  / /'
        `\  /'
         |  |
         |  |
         |  |
         |  |
        /    \
"""[1:], """



     yyyyyyyyyyy
y
y
y
y
y
y
y
"""[1:], "g")

# Each person: sprites, where the eyes and mouth sit (row, col), the eyes
# for each mood, and the mouth (shut, talking).
GUY: dict[str, dict] = {
    "koos": {"rest": KOOS_REST, "act": KOOS_FLIP, "act_len": 1.4,
             "eyes": [2, 5, {"open": "(o  o)", "shut": "(-  -)", "left": "(o o )", "right": "( o o)",
                             "wide": "(O  O)", "laugh": "(^  ^)"}],
             "mouth": [3, 6, r"\ww/", r"\wo/"], "mcol": "y", "head": 7},
    "sak": {"rest": SAK_REST, "act": SAK_SIP, "act_len": 1.6, "sip": 1,
            "eyes": [2, 5, {"open": "(o o)", "shut": "(- -)", "left": "(oo )", "right": "( oo)",
                            "wide": "(O O)", "laugh": "(^ ^)"}],
            "mouth": [3, 6, r"\_/", r"\o/"], "mcol": ".", "head": 7},
    "jan": {"rest": JAN_REST, "act": JAN_SIP, "act_len": 1.6, "sip": 1,
            "eyes": [2, 4, {"open": "(o o)", "shut": "(- -)", "left": "(oo )", "right": "( oo)",
                            "wide": "(O O)", "laugh": "(^ ^)"}],
            "mouth": [3, 5, r"\_/", r"\o/"], "mcol": ".", "head": 6},
}
NAME: dict[str, str] = {"koos": "koos", "sak": "sakkie", "jan": "jannie", "dog": "wagter"}
