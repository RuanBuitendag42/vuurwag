"""The braai engine: a faithful port of `lekker` (the original Perl script by a friend of the user).

`buf` is the frame buffer (one character and one colour letter per cell, 8 ANSI colours, bright = bold),
`core` the stage (the okes, the brakkie, the braai, the meat, the fire, the banter, wall(1), top(1), the boot
log and the status line), and the extras plug into the core's hooks and keys the way lekker's fragments do:
`weer` (weather and the time of day), `party` (vuurwerk, sokkie, singing, rugby, the calendar), `kuier`
(Tannie Sarie, Oom Faan, Eskom, hout, more meat, the town), `dokter` (Dokter Disk, grappe, tricks),
`plaas` (the farm: windpomp, dam, kraal, hek, more critters and skits) and `node` (the Proxmox facts).
"""
