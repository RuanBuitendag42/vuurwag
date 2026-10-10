"""Koos's one-liners for the node's events, in the plaas voice, with a ten-minute no-repeat rule.

The node extra plays one of these (as a line from Koos, in a cowsay bubble) when the probe reports something:
a guest starting, a backup finishing, a disk getting warm, the firewall down, Eskom having been here.
`{subject}` is the guest, disk, storage or sensor the event is about.
"""
from __future__ import annotations

import random
import time

COOLDOWN = 600.0

LINES: dict[str, list[str]] = {
    "hello": ["Hallo, manne. Die vuur is aan en {subject} staan.", "Die host is {subject}. Kom sit, die kole is reg.",
              "Welkom by die braai. {subject} braai saam.", "Die probe is terug van {subject}. Alles op sy plek."],
    "guest_started": ["{subject} is op. Nog 'n bord op die tafel.", "Daar kom {subject} deur die hek. Jy's laat!",
                      "{subject} het gestart. Gooi nog 'n tjop op.", "Kyk wie's hier: {subject}. Trek 'n stoel nader."],
    "guest_stopped": ["{subject} is af. Huis toe, seker.", "Daar loop {subject} uit by die hek. Totsiens!",
                      "{subject} het gestop. Een tjop minder.", "{subject} is weg. Die hond kry sy bord."],
    "guest_cpu_high": ["{subject} sweet soos 'n boer in Januarie.", "{subject} werk hard. Gee hom 'n koue een.",
                       "{subject} se CPU brand. Haal hom van die kole af.", "Rustig, {subject}. Dis 'n braai, nie 'n oes nie."],
    "guest_cpu_ok": ["{subject} het afgekoel. Goed so.", "{subject} asem weer. Nog 'n dop?",
                     "{subject} is weer rustig. Soos die dam na die reen.", "{subject} is terug by normaal. Lekker."],
    "guest_mem_high": ["{subject} se geheue is vol. Soos Jannie se bord.", "{subject} het te veel pap geeet. Geheue op 9 uit 10.",
                       "{subject} is propvol. Maak bietjie plek, man.", "{subject} se RAM sit vas soos 'n bakkie in die modder."],
    "guest_vanished": ["{subject} is weg. Net so. Soos my hoed in die wind.", "Waar is {subject}? Hy was nou net hier.",
                       "{subject} het verdwyn. Jakkals?", "{subject} is nie meer in die lys nie. Wagter, gaan soek."],
    "guest_new": ["Nuwe gas: {subject}. Welkom op die plaas.", "{subject} is nuut hier. Gee hom 'n bord.",
                  "Daar's 'n nuwe gas: {subject}. Bring nog 'n stoel.", "{subject} het ingetrek. Die kraal word vol."],
    "guest_locked": ["{subject} is gesluit. Iemand werk aan hom.", "{subject} het 'n slot op. Backup of snapshot, seker.",
                     "Los {subject} uit, hy's besig.", "{subject} is toegesluit soos die koöperasie op 'n Sondag."],
    "guest_gone": ["{subject} is weg."], "guest_down": ["{subject} is af."],
    "node_cpu_high": ["Die host werk hard. Die vuur brul.", "CPU hoog. Gooi hout op, Jannie!",
                      "Die host sweet. Soos die skape in Februarie.", "Sjoe, die server is warm. Perfekte braaiweer."],
    "node_cpu_ok": ["Die host het afgekoel. Rustige vuur.", "CPU weer normaal. Die kole gloei net.",
                    "Die server asem weer. Nog 'n dop, manne.", "Alles rustig op die host. Soos 'n Sondagmiddag."],
    "node_load_high": ["Die load is hoog. Elke kern werk.", "Load {subject}. Die host ploeg.",
                       "Die host dra swaar. Soos die bakkie met 'n vrag mielies.", "Load hoog. Gee die host 'n koue een."],
    "node_mem_high": ["Die host se geheue is vol. Soos Tannie se spens voor die basaar.", "RAM op {subject}. Iemand eet te veel.",
                      "Die geheue sit vas. Maak plek, manne.", "Host se RAM is vol. Soos die dam na 'n goeie reen."],
    "node_mem_ok": ["Die geheue is weer oop. Lekker.", "RAM terug na normaal. Die host asem.",
                    "Geheue reg. Soos 'n leeg bord na die vleis.", "Die host het plek gemaak. Goed so."],
    "node_swap_high": ["Die host swap. Soos Jannie van stoel tot stoel.", "Swap is hoog. Die host krap in die ou kas.",
                       "Swap! Die host soek plek soos 'n skaap in die kraal.", "Die swap is vol. Nie goed nie, manne."],
    "reboot": ["Eskom was hier. Die host het herbegin.", "Die host is pas weer op. Beurtkrag, seker.",
               "Herbegin. Die vuur moes weer aangesteek word.", "Die host het geslaap en is wakker. Soos Jannie."],
    "sensor_hot": ["{subject} is warm! Haal die server van die kole af.", "{subject} brand. Dis nie 'n tjop nie, man!",
                   "{subject} is te warm. Maak die deur oop.", "Sjoe, {subject}. Soos 'n Desembermiddag in die Karoo."],
    "sensor_warm": ["{subject} word warm. Hou hom dop.", "{subject} is lou. Soos Sakkie se dop.",
                    "{subject} word warmerig. Soos die kole voor die vleis.", "{subject} is warm. Nog nie koorsig nie."],
    "sensor_ok": ["{subject} het afgekoel. Goed so.", "{subject} is weer koel. Soos die dam in Junie.",
                  "{subject} terug by normaal. Lekker.", "{subject} is reg. Dankie, wind."],
    "disk_warm": ["{subject} word warm. Die dokter moet kyk.", "{subject} is warmerig. Nie goed vir 'n disk nie.",
                  "{subject} sweet. Skuif hom uit die son.", "{subject} is lou. Soos 'n Castle wat te lank gestaan het."],
    "disk_hot": ["{subject} brand! Bel die dokter!", "{subject} is te warm, manne. Backup nou.",
                 "{subject} is koorsig. Dokter Disk, kom gou.", "{subject} kook. Dis nie pap nie, dis 'n disk!"],
    "disk_cool": ["{subject} het afgekoel. Die dokter is tevrede.", "{subject} is weer koel. Lekker.",
                  "{subject} terug by normaal. Soos 'n plaasaand.", "{subject} is reg. Nog 'n dop, dokter?"],
    "disk_unhealthy": ["{subject} is siek! SMART se so. Backup, nou!", "{subject} het slegte sektore. Soos 'n ou bakkie se bande.",
                       "{subject} is nie gesond nie. Maak 'n backup voor die dominee kom.", "{subject}: SMART het gefaal. Bel die dokter!"],
    "disk_worn": ["{subject} is verslete. Soos Oom Faan se hoed.", "{subject} het min lewe oor. Begin spaar vir 'n nuwe een.",
                  "{subject} is bykans op. Soos die diesel voor maandeinde.", "{subject} is oud. Respek, maar backup."],
    "storage_high": ["{subject} raak vol. Soos die dam na die reen, net nie so lekker nie.",
                     "{subject} is byna vol. Gooi ou goed weg, Jannie.", "{subject} het min plek. Soos die kraal in lamtyd.",
                     "{subject}: plek raak min. Hout is ook min."],
    "storage_full": ["{subject} is vol! Niks pas meer in nie.", "{subject} is propvol. Soos Jannie na die melktert.",
                     "{subject}: 0% oor. Dit is 'n probleem, manne.", "{subject} is vol. Maak skoon, soos die kraal in die lente."],
    "storage_inactive": ["{subject} is af. Die stoor is toe.", "{subject} antwoord nie. Soos die koöperasie na vyf.",
                         "{subject} is nie aktief nie. Kyk daarna, Sakkie.", "{subject} slaap. Of hy's dood. Kyk."],
    "zpool_degraded": ["{subject} is gedegradeer! 'n Disk het geval.", "{subject}: ZFS kla. Een been is lam.",
                       "{subject} loop mank. Vervang die disk.", "{subject} is nie gesond nie. ZFS se so, en ZFS lieg nie."],
    "backup_started": ["Die backup van {subject} het begin. Tannie pak die kombuis.", "vzdump {subject} loop. Hou die vuur laag.",
                       "Backup {subject}. Goed. Backups is soos reen: altyd welkom.", "Die backup van {subject} is aan die gang."],
    "backup_ok": ["Die backup van {subject} is klaar. Tannie bring die slaai!", "vzdump {subject}: OK. Dankie Vader.",
                  "Backup {subject} geslaag. Nou kan ons rustig eet.", "{subject} is gebackup. Soos koring in die silo."],
    "backup_warn": ["Die backup van {subject} is klaar, met 'n paar waarskuwings. Kyk later in die log.",
                    "vzdump {subject}: klaar, maar hy het gekla. Die padkos is gepak, net 'n bietjie gekreukel.",
                    "Backup {subject} is daar. Hy het net gebrom soos Oom Faan se bakkie.",
                    "{subject} is gebackup, met waarskuwings. Soos 'n oes met 'n bietjie hael: die meeste is in."],
    "backup_failed": ["Die backup van {subject} het gefaal! Tannie het die slaai laat val.", "vzdump {subject}: FOUT. Nie goed nie, manne.",
                      "Backup {subject} het misluk. Kyk na die log.", "{subject} se backup is deur. Soos 'n hek wat oopgelos is."],
    "task_failed": ["Taak {subject} het gefaal. Kyk in die log.", "{subject}: fout. Iemand moet kyk.",
                    "Die taak {subject} het misluk. Soos my eerste braai.", "{subject} het nie gewerk nie. Weer probeer."],
    "tailscale_down": ["Tailscale is af. Geen sein op die plaas nie.", "Die VPN is weg. Ons is afgesny soos in '92.",
                       "Tailscale offline. Niemand kan ons bereik nie. Lekker, eintlik.", "Geen tailscale nie. Die toring se battery is pap."],
    "tailscale_up": ["Tailscale is terug. Die wereld kan weer inbel.", "VPN aan. Sein op die plaas!",
                     "Tailscale online. Die dominee kan weer WhatsApp.", "Tailscale is op. Dankie, toring."],
    "firewall_down": ["Die hek staan oop! pve-firewall is af!", "Die firewall is af. Enige jakkals kan inkom.",
                      "Hek oop, manne. Maak toe voor die beeste uitloop.", "pve-firewall loop nie. Wagter, hou wag!"],
    "firewall_up": ["Die hek is toe. Firewall loop.", "pve-firewall is aan. Die beeste bly in.",
                    "Firewall op. Jakkalse, bly weg.", "Die hek is reg. Dankie, Sakkie."],
    "updates": ["{subject} updates wag. Soos die koöperasie se rekening.", "Daar's {subject} pakkette om op te dateer. Later.",
                "{subject} updates. Na die braai, manne.", "apt se {subject} goed wag. Die wors wag nie."],
    "net_busy": ["Die netwerk is besig. {subject}. Iemand laai 'n fliek af.", "Die lyn is vol: {subject}. Jannie, is dit jy?",
                 "Netwerk besig op {subject}. Soos die N1 voor Desember.", "{subject} oor die lyn. Die rook trek vinnig."],
    "probe_down": ["Die probe antwoord nie. Die vuur is dood?", "Geen woord van die host nie. Die lyn is af.",
                   "Die probe is weg. Soos die krag. Ons wag.", "Host stil. Ssh het nie deurgekom nie."],
    "probe_up": ["Die probe is terug! Die vuur brand weer.", "Daar's die host. Welkom terug.",
                 "Probe aan. Die lyn is reg. Gooi hout op.", "Die host praat weer. Soos Oom Faan na sy tweede dop."],
    "unprivileged": ["Die probe is nie root nie. Ek sien net die helfte.", "Geen root nie. Die disks en die gaste is vir my toe.",
                     "Ek loop as gewone mens. Gee my root, dan sien ek alles.", "Half blind, manne: die probe het nie root nie."],
    "sizzle": ["Tsss. Die vleis sis.", "Hoor hoe sis die wors.", "Die kole praat.", "Tsss. Lekker."],
}

IDLE: list[str] = [
    "Ons soek reen.", "Die wind is uit die weste.", "Die windpomp draai darem.", "Hoor jy die jakkals?",
    "Die kole is perfek.", "Nog vyf minute.", "Moenie die wors prik nie.", "Die Suiderkruis staan hoog vanaand.",
    "Rooibos na die vleis.", "Tannie bak melktert vir die basaar.", "Die dam is halfvol. Of halfleeg.",
    "Die skape le al.", "Die beeste staan by die hek.", "Kameeldoring. Die beste hout.", "Pap en sous is reg.",
    "Die dominee kom Sondag.", "Die koöperasie het weer die prys opgesit.", "Oupa het altyd gese: geduld.",
    "Die hoenders krap in die tuin.", "Die mielies staan mooi.", "Castle vir die jongmense, Klipdrift vir die ooms.",
    "Daar's niks soos 'n plaasaand nie.", "Die Melkweg is helder vanaand.", "Die hek moet toe bly.",
]

EASTER: dict[str, list[str]] = {
    "springbok": ["BOKKE! Daar's die drie!", "Op die Bokke!", "Die Bokke wen altyd as ons braai."],
    "lekker": ["LEKKER!", "Lekker, manne!", "Ja-nee. Lekker."],
    "boerewors": ["Wors uit die hemel!", "Dit reen wors!", "Die slaghuis het geskiet!"],
    "fireworks": ["Vuurwerk! Wagter, kom hier!", "Kyk daai lug!", "Mooi, man!"],
    "loadshedding": ["Eskom! Weer!", "Beurtkrag. Ons braai deur.", "Stage 4. Lekker donker."],
    "rain": ["Reen! Die lande gaan dit drink.", "Dankie Vader, daar's die reen.", "Hou die vleis droog!"],
    "dog": ["HAAI! Los dit, hond!", "Wagter! Sit!", "Daai hond eet beter as ons."],
}


class Bank:
    """Picks lines without repeating any line within `cooldown` seconds (falls back to the least recent)."""

    def __init__(self, rng: random.Random | None = None, cooldown: float = COOLDOWN) -> None:
        self.rng = rng or random.Random()
        self.cooldown = cooldown
        self.last: dict[str, float] = {}

    def pick(self, lines: list[str], now: float | None = None) -> str:
        now = time.time() if now is None else now
        ok = lines or ["..."]
        fresh = [ln for ln in ok if now - self.last.get(ln, -1e9) >= self.cooldown]
        pool = fresh or [min(ok, key=lambda ln: self.last.get(ln, -1e9))]
        ln = self.rng.choice(pool)
        self.last[ln] = now
        return ln


SAYINGS = LINES
_BANK = Bank()


def say(kind: str, subject: str | None = None, rng: random.Random | None = None, now: float | None = None, **data: object) -> str:
    """Koos's line for an event; uses the shared cooldown bank."""
    bank = _BANK if rng is None else Bank(rng)
    line = bank.pick(LINES.get(kind) or LINES["sizzle"], now)
    return line.replace("{subject}", str(subject if subject is not None else "")).format(**data) if data else \
        line.replace("{subject}", str(subject if subject is not None else ""))


def idle(rng: random.Random | None = None, now: float | None = None) -> str:
    return (_BANK if rng is None else Bank(rng)).pick(IDLE, now)


def easter(kind: str, rng: random.Random | None = None) -> str:
    return (rng or random).choice(EASTER.get(kind) or EASTER["lekker"])
