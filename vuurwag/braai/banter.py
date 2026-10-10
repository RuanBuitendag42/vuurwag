"""BANTER, in the plaas voice: Afrikaans first, South African English second, Oom and Tannie register.

K = Koos (the braaier, the boer), S = Sakkie (the buurman, cap and blue jersey), J = Jannie (the youngster on
the koelboks), D = Wagter the brakkie; S+J both at once, S|J whichever is here.  T = Tannie Sarie, O = Oom
Faan, X = Dokter Disk, H = the hadeda, U = the uil, P = die dominee, R = the radio.
{up}, {load} and {cpu} are filled in from the host; an exchange that needs a missing value is skipped.  An
exchange may start with a condition (it only plays when that is true right now).  Markers: !flip Koos turns a
chop, !toss Jannie throws Sakkie a dop, !salute everyone raises a glass (or the tongs), !serve the meat comes
off the grid, and the extras add their own.  Nothing here is repeated within ten minutes.

Every list here is plain data; the stage builds what can be said right now from it.
"""
from __future__ import annotations

# ---- the core's small talk -------------------------------------------------------------------------------
CORE_TALK: list[list] = [
    [("S", "Is die kole al reg, Koos?"), ("K", "Nog vyf minute..."), ("J", "Oom het dit 'n uur gelede ook gese.")],
    [("K", "Moenie die wors prik nie!"), ("S", "Ek het hom nie aangeraak nie!")],
    [("S", "Jannie, nog 'n dop?"), ("J", "Vang! !toss"), ("S", "Dankie, ou maat!")],
    [("J", "Wie het die tang?"), ("K", "Die tang bly by my. Soos die plaas.")],
    [("K", "Die host is warm, en so is die wors.")],
    [("S", "uptime: {up}. Lekker!"), ("K", "Langer as die droogte, hoop ek.")],
    [("J", "Wie het die dam se sluis oopgelos?"), ("S", "Nie ek nie, ek was by die koelboks.")],
    [("D", "Woef!"), ("K", "Nee, Wagter! Sit!")],
    [("S", "Load average {load}."), ("K", "Gooi dan nog 'n stomp op!")],
    [("J", "Het Oom 'n backup gemaak?"), ("K", "Ja. Van die tjops.")],
    [("K", "Kyk hierdie draai! !flip"), ("S", "Lekker!")],
    [("J", "Ek is honger!"), ("K", "Geduld, my kind. Geduld is 'n boer se beste vriend.")],
    [("K", "'n Braai is nie 'n resies nie, Sakkie.")],
    [("S", "Wie is vannag op roep?"), ("J", "Die hond."), ("D", "Woef!")],
    [("J", "Kom daar reen?"), ("K", "Nee, dis net rook. Ons soek reen.")],
    ["raw", ("S", "Gee aan die tjops, asseblief."), ("K", "Wag. Nog nie.")],
    [("K", "Die host staan op {cpu}% CPU."), ("J", "En die braai op 100%.")],
    [("J", "Het iemand die host herbegin?"), ("S", "Uptime {up}. So nee.")],
    [("K", "Wie het die ys gebring?"), ("J", "Ek sit daarop, Oom.")],
    [("S", "Barbecue?"), ("K", "BRAAI, Sakkie. Braai. Ons is nie in Amerika nie.")],
    [("D", "Woef!"), ("J", "Hy wil 'n tjop he."), ("K", "Almal wil 'n tjop he.")],
    ["almost", ("K", "Wors is amper reg! !flip"), ("J", "Lekker!!")],
    ["wind_r", ("S", "Daai rook volg my soos 'n skaap!"), ("K", "Dis die wind, Sakkie. Uit die weste.")],
    ["wind_l", ("K", "Die rook is nou in my oe!"), ("S", "Braaier se voorreg, Koos.")],
    [("J", "Mooi aand, ne?"), ("S", "Ja-nee. Lekker. Plaaslug.")],
    [("K", "Stadig en laag, soos in die ou dae."), ("S", "Soos die koöperasie se betalings.")],
    [("K", "Op die braai! Gesondheid! !salute"), ("S+J", "Lekker!")],
    [("S", "sudo draai wors"), ("K", "Gedraai. 0 foute. !flip")],
    [("J", "Het Oom al probeer om die vuur af en weer aan te sit?")],
    [("S", "Die wind is uit die weste."), ("K", "Dan kom daar nie reen nie. Weer nie.")],
    [("J", "Hoeveel skape het Oom nog?"), ("K", "Genoeg. Tel jy maar die tjops.")],
    [("S", "Die mielies staan mooi, Koos."), ("K", "As die reen net wil hou."), ("J", "En die Eskom.")],
    [("K", "Die windpomp draai darem."), ("S", "Dan is daar nog water in die dam.")],
    [("J", "Hoor jy die jakkals?"), ("K", "Hy ruik die wors. Soos Wagter."), ("D", "Woef!")],
    [("S", "Klipdrift en Coke, iemand?"), ("J", "Castle vir my, dankie."), ("K", "Rooibos vir die braaier. Later.")],
    [("K", "Tannie Sarie se melktert staan in die kombuis."), ("J", "Hoekom staan ons dan hier?")],
    [("S", "Die koöperasie het weer die kunsmis se prys opgesit."), ("K", "Alles gaan op, behalwe die reen.")],
    [("J", "Wanneer is die NG kerk se basaar?"), ("K", "Saterdag. Tannie bak al van Dinsdag af.")],
    [("S", "Pap en sous is reg."), ("K", "Dan is dit net die wors wat nog wag.")],
    [("J", "Oupa het altyd gese: 'n vuur maak jy met geduld."), ("K", "En met kameeldoring.")],
    [("K", "Die Suiderkruis staan reg bo die kraal."), ("S", "Dan is dit laat. Of vroeg.")],
    [("J", "Die beeste le al by die dam."), ("K", "Slim diere. Hulle wag vir die tjops.")],
    [("S", "Ons moet die hek regmaak, Koos."), ("K", "Na die braai, Sakkie. Alles na die braai.")],
    [("J", "Koeksisters na die vleis?"), ("S", "Eers die vleis, dan die soet goed."), ("K", "Tannie se reel.")],
    [("K", "Boerewors van die slaghuis op die dorp."), ("S", "Niks klop dit nie."), ("J", "Behalwe Oom se tjops.")],
    [("S", "Hoeveel het dit gereen by julle?"), ("K", "Drie millimeter. Die stof is net natgespat.")],
]

HOT_TALK: list[list] = [
    ["roaring", ("S", "Sjoe, die vuur brul!"), ("K", "Die host werk hard. Soos 'n boer in planttyd.")],
    [("J", "CPU op {cpu}%!"), ("K", "Perfekte braaiweer.")],
    [("J", "CPU op {cpu}%! Gooi nog hout op!"), ("K", "Die host doen dit vir ons.")],
]

# ---- weer en tyd ----------------------------------------------------------------------------------------
WX_TALK: list[list] = [
    ["wx_dag", ("S", "Wie het die son aangeskakel?"), ("K", "sudo systemctl start son.")],
    ["wx_dag", ("J", "Braai in die middag? Is dit Saterdag?"), ("K", "Op die plaas is elke dag braaidag.")],
    ["wx_dag", ("K", "Smeer sonroom, manne!"), ("S", "Ek is klaar bruin gebraai van die lande.")],
    ["wx_dag", ("S", "Die dop word warm in die son."), ("J", "Daarom sit ek op die koelboks.")],
    ["wx_dag", ("K", "Die son brand die mielies."), ("S", "Ons soek reen, Koos."), ("K", "Elke dag, Sakkie.")],
    ["wx_dagbreek", ("S", "Ons het weer deur die nag gebraai."), ("J", "Ontbyt-braai, iemand?"),
     ("K", "Eiers en spek op die rooster!")],
    ["wx_dagbreek", ("J", "Is dit al oggend?"), ("K", "Ja, Jannie. Die hoenders is al wakker.")],
    ["wx_dagbreek", ("S", "Die beeste wil gemelk word."), ("K", "Die wors ook.")],
    ["wx_aand", ("J", "Mooi sonsondergang, ne?"), ("S", "Afrika. Niks klop dit nie.")],
    ["wx_aand", ("K", "Die son sak, die kole gloei. Perfek.")],
    ["wx_aand", ("S", "Kyk daai lug! Rooi en pienk."), ("K", "So lyk 'n plaas-aand.")],
    ["wx_aand", ("J", "Die skape loop kraal toe."), ("K", "Hulle weet wat tyd dit is.")],
    ["wx_volmaan", ("J", "Kyk hoe helder is die volmaan."), ("K", "Ons kan sonder 'n lig braai.")],
    ["wx_volmaan", ("D", "Ahoooo!"), ("S", "Wagter sing vir die maan.")],
    ["wx_volmaan", ("S", "Die dam blink soos 'n spieel."), ("J", "Dis die maan wat daarin le.")],
    ["wx_nuwemaan", ("S", "Donker vanaand. Geen maan nie."), ("K", "Nuwemaan. Kyk hoe blink die Melkweg.")],
    ["wx_sekel", ("J", "Die maan is net 'n skyfie vanaand."), ("S", "Soos my wins by die koöperasie.")],
    ["wx_helder", ("J", "Daar is die Suiderkruis."), ("K", "En hier is die wors. Prioriteite, Jannie.")],
    ["wx_helder", ("S", "Oupa het altyd die Suiderkruis gewys."), ("K", "En dan die pad huis toe.")],
    [("U", "Hoe-hoe!"), ("K", "Hoe? Met die tang, natuurlik.")],
    [("U", "Hoe-hoe?"), ("S", "Goed dankie, en met jou?")],
    [("J", "Daar sit 'n uil in die boom."), ("K", "Hy hou die muise dop. Ek hou die wors dop."), ("U", "Hoe-hoe.")],
    ["wx_vuur", ("J", "Kyk, vuurvliegies!"), ("S", "Of is dit die server se liggies?")],
    ["wx_wind", ("S", "Die wind waai vanaand."), ("J", "Hou jou hoed vas, Oom!")],
    ["wx_wind", ("K", "Die wind blaas die kole lekker aan."), ("S", "Gratis waaier.")],
    ["wx_wind", ("J", "My dop waai amper om!"), ("S", "Drink hom dan gou!")],
    ["wx_wind", ("K", "Die windpomp gaan vannag hard werk."), ("S", "Dan is die dam more vol.")],
    ["wx_bewolk", ("S", "Dit gaan reen, ek voel dit in my knie."), ("K", "Jou knie is al tien jaar verkeerd.")],
    ["wx_bewolk", ("J", "Waar is die sterre heen?"), ("K", "Agter die wolke. Hulle kom terug.")],
    ["wx_bewolk", ("K", "Daai wolke lyk belowend."), ("S", "Ons soek reen."), ("J", "Al vir drie maande.")],
    ["wx_reen", ("J", "Ons is nie van suiker gemaak nie!"), ("S", "Praat vir jouself. Ek is soet.")],
    ["wx_reen", ("J", "Die boere gaan bly wees."), ("K", "Ek IS 'n boer. Maar my vuur is nie bly nie.")],
    ["wx_reen", ("K", "In die Kaap braai hulle in die reen ook."), ("S", "Ons is nie in die Kaap nie, Koos.")],
    ["wx_reen", ("J", "My dop loop oor van die reen."), ("S", "Gratis hervul!")],
    ["wx_reen", ("K", "Dankie Vader, daar is die reen."), ("S", "Die mielies gaan dit drink."), ("J", "En die dam.")],
    ["wx_umb", ("K", "Die vleis bly droog. Dis al wat tel."), ("S+J", "En ons?")],
    ["wx_storm", ("J", "Trek die server se prop uit!"), ("K", "Rustig. Ons het 'n UPS."), ("S", "Ons het 'n wat?")],
    ["wx_storm", ("K", "Hoeveldse storm. Tien minute, dan is dit verby."), ("S", "Soos elke middag in Desember.")],
    ["wx_storm", ("S", "Die beeste staan met hul sterte in die wind."), ("K", "Slim diere.")],
    ["wx_boom", ("K", "Bly weg van die boom, manne!"), ("J", "Ek sit op die koelboks. Rubbervoete.")],
    ["wx_hond", ("S", "Waar is Wagter?"), ("K", "Weggekruip. Slim hond.")],
    ["wx_mis", ("J", "Ek sien nie eens die windpomp nie."), ("K", "Die mis le dik oor die laagte.")],
    ["wx_mis", ("S", "Die mis kom van die dam af."), ("K", "Goed vir die lande. Sleg vir die vuur.")],
    ["wx_koud", ("J", "Dis koud vanaand!"), ("K", "Kom staan nader aan die vuur."), ("S", "Ryp more.")],
    ["wx_koud", ("S", "Dis {temp} grade."), ("K", "Die kole gee nie om nie.")],
    ["wx_warm", ("J", "Dis {temp} grade en ons staan by 'n vuur."), ("K", "Boere is nie bang vir hitte nie.")],
    ["wx_warm", ("S", "Sjoe, dis warm. Selfs die skape le in die skaduwee."), ("K", "Drink water, Sakkie. Of Castle.")],
]

WX_POOL: dict[str, list[list]] = {
    "winderig": [[("K", "Hou vas aan julle hoede, manne!"), ("S", "Ek het 'n pet, Koos.")],
                 [("S", "Die rook kan nie besluit nie."), ("K", "Die wind ook nie.")],
                 [("J", "Die wind blaas die wors koud."), ("K", "Dan braai ons hom warm.")],
                 [("S", "Die wind is uit die weste."), ("K", "Dan bly dit droog. Soos altyd.")]],
    "bewolk": [[("S", "Dit gaan reen, ek voel dit in my knie."), ("K", "Jou knie is al tien jaar verkeerd.")],
               [("J", "Die wolke trek saam."), ("S", "Gooi gou die vleis op, Koos!")],
               [("K", "Hou jou oog op daai wolk, Jannie."), ("J", "Ek hou my oog op die wors.")],
               [("S", "Ons soek reen."), ("K", "Elke boer in die distrik soek reen.")]],
    "reen": [[("S", "Koos! Ons word nat!"), ("K", "Julle is nie van suiker gemaak nie!")],
             [("S", "Hoor hoe sis die kole!"), ("K", "Moenie bekommer nie. Die vuur hou.")],
             [("J", "Is dit nou 'n gestoomde tjop?"), ("K", "Dis 'n nuwe resep.")],
             [("S", "Wie het die sprinkler aangesit?"), ("J", "Die Here, Sakkie.")],
             [("K", "Reen! Die lande gaan dit drink."), ("S", "En die dam gaan vol word.")]],
    "storm": [[("J", "Trek die server se prop uit!"), ("K", "Rustig. Ons het 'n UPS."), ("S", "Ons het 'n wat?")],
              [("S", "Tel die sekondes tussen die weerlig en die donder!"), ("J", "Een... twee...")],
              [("K", "Hoeveldse storm. Tien minute, dan is dit verby."), ("S", "Soos elke middag in Desember.")],
              [("J", "Die hoenders is almal in die hok."), ("K", "Slimmer as ons, Jannie.")]],
    "helder": [[("J", "Die reen is verby."), ("K", "Sien? Die vuur het gehou.")],
               [("K", "Die storm is verby en die vuur brand nog."), ("S", "Taai vuur, daai.")],
               [("S", "Hoeveel millimeter was dit?"), ("K", "Genoeg vir die lande. Nie genoeg vir die dam nie.")]],
    "mis": [[("J", "Die mis le dik."), ("K", "Bly by die vuur. Die vuur ken die pad.")],
            [("S", "Ek sien nie my eie bakkie nie."), ("K", "Dis dalk beter so, Sakkie.")]],
}

WX_TOLBOS = [[("S", "Wat rol daar?"), ("K", "'n Tolbos. Welkom in die Karoo, Sakkie.")],
             [("J", "Daar gaan 'n tolbos!"), ("K", "Hy's op pad na die koöperasie.")]]
WX_BOW = [[("J", "Kyk, 'n reenboog!"), ("S", "Waar is die pot goud?"), ("K", "Onder die braai. Dis die kole.")],
          [("S", "Reenboog! Die storm is verby."), ("K", "Lekker. Terug na die vleis.")],
          [("J", "'n Reenboog oor die dam!"), ("K", "Die Here se belofte, Jannie. En my wors is nog droog.")]]
WX_KABOOM_SLEPT = [("J", "Ek was nie aan die slaap nie!"), ("K", "Natuurlik nie, Jannie.")]
WX_KABOOM = [[("S", "Was dit die donder of Jannie se maag?"), ("J", "Dis nie ek nie!")],
             [("K", "Hou die vleis dop, manne!")],
             [("S|J", "Daai een was naby!"), ("K", "Tel die sekondes, Jannie.")],
             [("J", "Die beeste gaan deur die draad hardloop!"), ("K", "Die hek is toe. Hoop ek.")]]
WX_HADEDA_DAWN = ("K", "Die hadedas is wakker, dis slaaptyd.")
WX_HADEDA = [("S", "Daai hadeda het nie 'n volumeknop nie."), ("J", "Wie het die hadeda se wekker gestel?"),
             ("K", "Dis die Suid-Afrikaanse wekker, Jannie."), ("K", "Hy soek erdwurms. Ek soek rus.")]
WX_HAT_GONE_DOG = [("K", "My hoed! Wagter, gaan haal!"), ("S|J", "Hy is mos nie 'n retriever nie.")]
WX_HAT_GONE = [("K", "My hoed! Kom terug!"), ("S|J", "Daar gaan hy! Tot siens, hoed!")]
WX_HAT_BACK_DOG = [("K", "Goeie hond! Maar dis MY hoed."), ("D", "Woef!")]
WX_HAT_BACK_WIND = [("S", "Die wind het hom teruggebring!"), ("K", "Lekker. Hy pas nog.")]
WX_MUG = {"koos": [[("K", "Muggies! Weg van my vleis!")]],
          "sak": [[("S", "Eina! Muggies!"), ("K", "Hulle hou van jou, Sakkie.")]],
          "jan": [[("J", "Muggies! Wie het hulle genooi?"), ("S", "Hulle het die braai geruik.")]]}
WX_TOD_TALK = {"aand": [("J", "Mooi sonsondergang, ne?"), ("S", "Afrika. Niks klop dit nie.")],
               "nag": [("K", "Nou is dit eers lekker donker."), ("S", "En die vuur lekker helder.")],
               "dag": [("S", "Wie het die son aangeskakel?"), ("K", "sudo systemctl start son.")]}

# ---- partytjie ----------------------------------------------------------------------------------------------
PT_OOH = [[("S", "Ooooh!"), ("J", "Aaaah!"), ("K", "Mooi, man!")],
          [("J", "Kyk daar! !pt_cheer"), ("S", "Lekker!")],
          [("K", "Dis nou vuurwerk, daai!"), ("S", "Nog een! Nog een!")],
          [("J+S", "Ooooh!"), ("K", "En Wagter is weg.")],
          [("J", "Wie het die vuurpyle gekoop?"), ("K", "Moenie vra nie, kyk net.")],
          [("S", "Die beeste gaan nie slaap vannag nie."), ("K", "Hulle sien dit elke Oujaar.")]]
PT_NO = [("K", "Wag, man! Een ding op 'n slag."), ("S", "Hou jou perde, ons is besig!"),
         ("J", "Nou nie, Oom. Netnou."), ("K", "Stadig oor die klippe!"),
         ("S", "Eers die een klaarmaak, dan die volgende.")]
PT_SOK_GO = [[("K", "Sokkie-tyd! Sit die radio harder!"), ("J", "Ek kan nie dans nie."),
              ("S", "Niemand kan nie, Jannie. Dans net!")],
             [("S", "Hierdie een is my liedjie! Kom, manne!"), ("K", "Langarm, Sakkie!")],
             [("J", "Wie het die radio aangesit?"), ("K", "Ek. Op, op, op! Sokkie!")],
             [("K", "Soos by die skousaal in '89!"), ("S", "Oom was nie eens daar nie."), ("K", "Dans net, Sakkie.")]]
PT_SOK_MID = [[("S", "Kyk hoe swaai Koos die tang!"), ("K", "Twee-stap, Sakkie. Twee-stap.")],
              [("K", "Jannie, jy trap op my voet!"), ("J", "Dis deel van die dans.")],
              [("J", "Wagter dans beter as ons."), ("D", "Woef!")],
              [("S", "Ek's die beste langarmdanser in die hele distrik!"), ("K", "Ja-nee. Jy en Wagter.")]]
PT_SOK_END = [("J", "My bene is moeg."), ("K", "Lekker gesokkie, manne!"), ("S", "Weer! Weer!")]
PT_SING_GO = [("K", "Kom ons sing, manne!"), ("S", "Een, twee, drie..."), ("J", "Ek ken net die koor."),
              ("S", "Stilte! Koos gaan sing.")]
# only old, traditional songs (public domain)
PT_SONGS: list[list] = [
    ["sing: Sarie Marais, 3 stemme (1 vals)",
     ("K", "My Sarie Marais is so ver van my hart,"),
     ("K+S", "maar ek hoop om haar weer te sien."),
     ("J", "O bring my t'rug na die ou Tra-a-ansvaa-aal... !pt_vals"),
     ("J+K+S", "daar waar my Sarie woon!"),
     ("D", "Aaa-ooooo!"),
     ("K+S", "Daar onder in die mielies by die groen doringboom,"),
     ("J+K+S", "daar woon my Sarie Marais! !salute"),
     ("S", "Jannie, jy sing vals!"),
     ("J", "Dis nie vals nie, dis jazz.")],
    ["sing: Daar kom die Alibama, 3 stemme en 'n hond",
     ("J+K+S", "Daar kom die Alibama, die Alibama, die kom oor die see!"),
     ("S", "Nooi, nooi die rietkooi nooi, die rietkooi is gemaak,"),
     ("J", "die rietkooi is vir my gema-a-aak om daarop te sla-a-aap! !pt_vals"),
     ("D", "Ahooooo!"),
     ("J+K+S", "Daar kom die Alibama! !salute"),
     ("K", "Jannie, jy's 'n hele toon te hoog."),
     ("J", "Ek sing vir die mense agter in die saal.")],
    ["sing: Jan Pierewiet, 3 stemme (1 vals)",
     ("K+S", "Jan Pierewiet, Jan Pierewiet, Jan Pierewiet staan stil!"),
     ("J", "Goeie more my vrou, hier's 'n soentjie vir jou! !pt_vals"),
     ("K+S", "Goeie more my man, daar is koffie in die kan!"),
     ("J+K+S", "Jan Pierewiet, Jan Pierewiet, Jan Pierewiet staan stil! !salute"),
     ("D", "Ahooo!"),
     ("S", "Jannie, die hond sing beter."),
     ("J", "Hy oefen meer.")],
]
PT_RUGBY_GO = [("K", "Sit die radio aan, die Bokke speel!"), ("S", "Stilte, manne! Die toets begin!"),
               ("J", "Draai die radio harder, die Bokke speel!")]
PT_RUGBY_PEN = ([("S", "Ag nee, man!"), ("J", "Nee, Skeidsregter!")],
                [("K", "Skeidsregter, kry vir jou 'n bril!"), ("K", "Dit was nooit 'n oortreding nie!")])
PT_RUGBY_TRY = [("J+K+S", "BOKKE!!!"), ("S", "Wie het my dop omgestamp?!")]
PT_RUGBY_END = [("K", "Op die Bokke! !salute"), ("J+S", "Bokke!")]
PT_TALK: list[list] = [
    [("S", "Wie het vuurwerk gebring?"), ("J", "Ek, maar Wagter het dit begrawe."), ("D", "Woef!")],
    [("K", "Vuurwerk en vleis: albei moet jy reg aansteek."), ("S", "En albei brand jou vingers.")],
    [("J", "Speel die Bokke vanaand?"), ("K", "Saterdag. Dan braai ons weer."), ("S", "Ons braai elke dag, Koos.")],
    [("S", "Rugby sonder braai is net hardloop."), ("K", "En braai sonder rugby is net kos.")],
    [("K", "Hierdie tjop is vir die Bokke se voorry."), ("J", "Dan moet Oom nog twintig braai.")],
    [("J", "Sing vir ons iets, Oom Koos."), ("K", "Net as Jannie nie saamsing nie."), ("J", "Hoekom nie?")],
    [("S", "Onthou jy die sokkie by die skousaal?"), ("K", "Ek onthou jou voete op myne.")],
    [("K", "'n Partytjie het drie dinge nodig."), ("S", "Vleis, vuur en vriende?"), ("K", "Vleis, vuur en 'n verlengkoord.")],
    [("S", "Hoeveel dops is genoeg vir 'n sokkie?"), ("J", "Een meer as wat jy nou het.")],
    [("K", "Langarm is soos braai: stadig en met gevoel."), ("J", "En jy trap op niemand se tone nie.")],
    [("J", "Ek het eendag op 'n trekker se kap gesokkie."), ("S", "En die boer?"), ("J", "Hy het die musiek harder gesit.")],
    [("S", "Wanneer skiet ons weer vuurpyle?"), ("K", "As Wagter slaap."), ("D", "Woef!")],
    [("J", "Kan die host vuurwerk hanteer?"), ("K", "CPU op {cpu}%. Hy sal oorleef.")],
    [("K", "Die Bokke wen altyd as ons braai."), ("S", "Dan moet ons elke dag braai."), ("J", "Ons braai elke dag!")],
    [("S", "Is this a party or a braai?"), ("K", "On a farm, Sakkie, that is the same thing.")],
    [("J", "Play us some Sarie Marais, Oom."), ("K", "I am a braaier, not a jukebox.")],
    [("K", "Who taught you to dance, Sakkie?"), ("S", "Wagter."), ("D", "Woef!")],
    [("J", "Die bure het weer 'n partytjie."), ("K", "Die bure is tien kilometer ver, Jannie."), ("J", "Ek hoor hulle nog.")],
    [("S", "Die radio vang net een stasie."), ("K", "RSG. Dis genoeg."), ("J", "Boeremusiek en die weerberig.")],
    ["pt_braaidag", ("K", "Vandag is Braaidag. Elke dag behoort Braaidag te wees."), ("S", "Elke dag IS Braaidag hier, Koos.")],
    ["pt_braaidag", ("J", "Erfenisdag. Wat is ons erfenis?"), ("K", "Die tang, Jannie. Die tang.")],
    ["pt_guy", ("S", "Guy Fawkes, en Wagter bewe al."), ("K", "Ek ook, as ek die bure se vuurpyle sien.")],
    ["pt_guy", ("J", "Wie was Guy Fawkes eintlik?"), ("K", "'n Ou wat ook baie van vuur gehou het.")],
    ["pt_kers", ("K", "Kersfees, en ek braai weer."), ("S", "Wat anders, Koos?")],
    ["pt_kers", ("J", "Wat het Oom vir Kersfees gekry?"), ("S", "'n Nuwe tang."), ("K", "Ek hou by my ou tang, dankie.")],
    ["pt_kers", ("S", "Tannie se Kersfees-trifle!"), ("J", "Na die vleis."), ("K", "Altyd na die vleis.")],
    ["pt_tweede", ("J", "Tweede Kersdag en ons braai die oorskiet."), ("K", "Oorskiet is die beste vleis.")],
    ["pt_oujaar", ("S", "Wat is jou voorneme vir volgende jaar?"), ("K", "Meer braai."), ("J", "Minder werk.")],
    ["pt_nuwejaar", ("J", "Nuwe jaar, nuwe ek."), ("K", "Dieselfde ou dop in jou hand, Jannie.")],
    ["pt_gelofte", ("K", "Geloftedag. Oupa het altyd die kerk toe gegaan."), ("S", "En dan gebraai."), ("K", "Natuurlik.")],
    ["pt_vryheid", ("J", "Vryheidsdag!"), ("K", "Vry om te braai, Jannie.")],
    ["pt_werkers", ("S", "Werkersdag. Niemand werk nie."), ("K", "Behalwe die braaier.")],
    ["pt_jeug", ("J", "Jeugdag! Dis my dag."), ("K", "Dan gaan haal jy die hout.")],
    ["pt_vroue", ("K", "Vrouedag. Tannie Sarie braai vandag."), ("S", "En ons?"), ("K", "Ons was die skottelgoed.")],
    ["pt_paas", ("J", "Paasfees. Waar is die eiers?"), ("K", "Op die rooster, saam met die spek.")],
    ["pt_paas", ("S", "Goeie Vrydag. Pickled fish by Tannie."), ("K", "En wors by my. Albei.")],
    ["pt_mense", ("S", "Menseregtedag."), ("K", "Elke mens het die reg op 'n tjop.")],
]
PT_GREET: dict[str, tuple[str, str, list]] = {
    "braaidag": ("kalender: 24 September, Erfenisdag (Nasionale Braaidag)",
                 "Gelukkige Braaidag! 24 September, Erfenisdag: steek die vuur aan, Suid-Afrika!",
                 [("K", "Gelukkige Braaidag, manne! !salute"), ("J+S", "Gelukkige Braaidag!")]),
    "guy": ("kalender: 5 November, Guy Fawkes (wagter op hoe gereedheid)",
            "5 November: Guy Fawkes. Hou die hond binne en die vuurpyle buite!",
            [("S", "Dis Guy Fawkes vanaand."), ("K", "Arme Wagter."), ("D", "Woef?")]),
    "kers": ("kalender: Kersfees, hoede gemonteer op 3 okes",
             "Geseende Kersfees! Vrede op aarde en vleis op die rooster.",
             [("J", "Geseende Kersfees, manne!"), ("K", "Mooi hoed, Jannie."), ("J", "Dankie. Die rooi pas by my trui.")]),
    "tweede": ("kalender: 26 Desember, Tweede Kersdag (oorskiet op die rooster)",
               "Tweede Kersdag: die oorskiet gaan op die rooster en die trifle kom uit die yskas.",
               [("K", "Tweede Kersdag, manne. Oorskiet-braai!"), ("S", "Die beste braai van die jaar.")]),
    "oujaar": ("kalender: 31 Desember, aftelling gereed vir 00:00:00",
               "Oujaarsaand! Om middernag begin 'n nuwe jaar. Bly wakker, Jannie.",
               [("K", "Laaste braai van die jaar, manne!"), ("S", "Dan moet dit die beste een wees.")]),
    "nuwejaar": ("kalender: 1 Januarie, nuwe jaar gemonteer read-write",
                 "Gelukkige Nuwejaar! Mag jou vuur altyd brand en jou vleis altyd gaar wees.",
                 [("S", "Gelukkige Nuwejaar, manne!"), ("K", "Nuwe jaar, dieselfde tang.")]),
    "gelofte": ("kalender: 16 Desember, Geloftedag / Versoeningsdag",
                "16 Desember: Geloftedag. Eers kerk, dan braai, soos Oupa gemaak het.",
                [("K", "Geloftedag, manne. !salute"), ("S+J", "Op die Gelofte!")]),
    "vryheid": ("kalender: 27 April, Vryheidsdag",
                "27 April: Vryheidsdag. Vry om te braai, vry om te kuier.",
                [("J", "Vryheidsdag!"), ("K", "Steek die vuur aan, Jannie.")]),
    "werkers": ("kalender: 1 Mei, Werkersdag",
                "1 Mei: Werkersdag. Die enigste een wat werk is die braaier.",
                [("S", "Werkersdag, Koos."), ("K", "Ek werk. Kyk, ek draai die wors.")]),
    "jeug": ("kalender: 16 Junie, Jeugdag",
             "16 Junie: Jeugdag. Jannie, dis jou dag: gaan haal die hout.",
             [("J", "Jeugdag! Vandag doen ek niks."), ("K", "Hout, Jannie. Hout.")]),
    "vroue": ("kalender: 9 Augustus, Vrouedag",
              "9 Augustus: Vrouedag. Tannie Sarie kry vandag die tang.",
              [("K", "Vrouedag, manne. Tannie braai."), ("S", "En ons was die borde.")]),
    "mense": ("kalender: 21 Maart, Menseregtedag",
              "21 Maart: Menseregtedag. Elke mens het die reg op 'n tjop.",
              [("S", "Menseregtedag, manne."), ("K", "Reg op 'n tjop. !salute")]),
    "paas": ("kalender: Paasnaweek, eiers op die rooster",
             "Paasnaweek! Hot cross buns in die kombuis en wors op die rooster.",
             [("J", "Geseende Paasfees, manne!"), ("K", "Die Here is opgestaan. En die kole ook.")]),
}
PT_DAYNAME = {"braaidag": "Braaidag!", "guy": "Guy Fawkes", "kers": "Kersfees", "tweede": "Tweede Kersdag",
              "oujaar": "Oujaarsaand", "nuwejaar": "Nuwejaar", "gelofte": "Geloftedag", "vryheid": "Vryheidsdag",
              "werkers": "Werkersdag", "jeug": "Jeugdag", "vroue": "Vrouedag", "mense": "Menseregtedag",
              "paas": "Paasfees"}
PT_NEWYEAR = [("J+K+S", "GELUKKIGE NUWEJAAR!"), ("K", "Op die nuwe jaar! !salute"), ("S|J", "Gelukkige Nuwejaar, manne!")]
PT_EGG_CHEER = [("J+K+S", "BRAAI-PLEK!"), ("K", "Ons ou webwerf, manne!"), ("S|J", "Die plek vir 'n lekker braai!")]

# ---- kuier: Tannie Sarie, Oom Faan, Eskom, hout, vleis ----------------------------------------------------
KV_NO = [("K", "Wag, man! Een ding op 'n slag."), ("S", "Hou jou perde, Jannie."),
         ("K", "Stadig oor die klippe!"), ("J", "Nie nou nie, ons is besig.")]
KV_LS_DARK = [[("K", "Eskom kan nie ons vuur afskakel nie! !salute"), ("S+J", "Gelukkig braai ons op hout!")],
              [("S", "Daar gaan die krag."), ("K", "Gelukkig braai ons op hout!"), ("S+J", "Eskom kan nie ons vuur afskakel nie!")],
              [("J", "Stage {stage}? Weer?"), ("K", "Los dit. Ons vuur loop op kameeldoring. !salute"), ("S+J", "Lekker!")],
              [("S", "Die hele dorp is donker."), ("K", "Die plaas was nog altyd donker. Kyk die sterre.")]]
KV_LS_BACK = [[("J", "Die krag is terug!"), ("S", "Vroeg? Eskom?"), ("K", "Sjuut, netnou hoor hulle ons.")],
              [("J", "Die krag is terug!"), ("K", "Ag nee, nou is die sterre weer weg.")],
              [("S", "Die krag is terug!"), ("K", "Hoe lank, dink jy?"), ("J", "Tot die volgende stage.")],
              [("S", "Die krag is terug!"), ("K", "Die melkmasjien kan more weer werk.")]]
KV_TAN_HI = {
    "pap": [("T", "Kos is reg! Wie wil pap he?"), ("S+J", "Dankie, Tannie!")],
    "slaai": [("T", "Ek het slaai gemaak. Julle eet te veel vleis."), ("J", "Slaai, Tannie? By 'n braai?"),
              ("T", "Ja, Jannie. Groen goed."), ("S+J", "Dankie, Tannie!")],
    "melktert": [("T", "Hier is melktert vir later!"), ("S+J", "Dankie, Tannie!"),
                 ("J", "Tannie se melktert is die beste in die distrik.")],
    "koeksisters": [("T", "Koeksisters, maar eers na die vleis!"), ("S+J", "Dankie, Tannie!"),
                    ("S", "Tannie wen elke jaar by die basaar.")],
}
KV_TAN_MEAT_OVER = [("T", "Koos, die vleis is amper te gaar!"), ("K", "Ja, Tannie. Ek weet, Tannie.")]
KV_TAN_MEAT_RAW = [("T", "Koos, is daai vleis nog rou?"), ("K", "Dis medium-rare, Tannie."), ("T", "Hmf. !kv_hmf")]
KV_TAN_DOPS = ("T", "Sakkie, hoeveel dops was dit nou al?")
KV_TAN_DOPS_ANS = ("S", "Net twee, Tannie.")
KV_TAN_OPINIONS = [
    [("T", "Maak tog die rook weg van my wasgoed af!"), ("K", "Ek sal met die wind praat, Tannie.")],
    [("T", "En onthou, julle eet groente ook!"), ("J", "Ja, Tannie. Aartappelskyfies."), ("T", "Jannie! !kv_hmf")],
    [("T", "Die dominee kom Sondag eet."), ("K", "Dan braai ons Sondag ook."), ("T", "Hmf. !kv_hmf")],
    [("T", "Het julle die hoenders kos gegee?"), ("J", "Wagter het, Tannie."), ("D", "Woef?")],
    [("T", "Die basaar is Saterdag en ek het nog twintig melkterte om te bak."), ("S", "Ons help eet, Tannie.")],
]
KV_TAN_TONGS = [("T", "Gee hier daai tang, Koos! !kv_tongs"), ("K", "Maar Tannie..."),
                ("T", "Mens moet die tang klik, so."), ("K", "Ja, Tannie."), ("T", "Hier, vat terug. !kv_tongsback")]
KV_TAN_TURN = [("T", "Koos, jy draai die vleis te veel om."), ("K", "Tannie, dis my styl."), ("T", "Hmf. !kv_hmf")]
KV_TAN_DOG = [("T", "Wie het die hond weer wors gegee?"), ("S+J", "Koos!"), ("K", "Hy het dit gesteel, Tannie!")]
KV_TAN_DARK = [("T", "Die krag is af, maar my gasstoof werk!"), ("K", "Tannie is slim.")]
KV_TAN_JAN = [("T", "Jannie, staan op van daai koelboks af!"), ("J", "Ja, Tannie! !kv_jump")]
KV_TAN_BYE = [("T", "Lekker eet, julle! !kv_wave"), ("T", "En moenie te laat bly nie! !kv_wave"),
              ("T", "Die skottelgoed wag, Koos. !kv_wave")]
KV_TAN_BYE_ANS = ("S+J", "Totsiens, Tannie!")
KV_JAN_SIT = [("J", "Is sy weg?"), ("K", "Ja, sy is weg."), ("J", "Lekker. !kv_sit")]
KV_OOM_HI = [("O", "Naand, manne! Ek het ys gebring."), ("S+J", "Oom Faan!")]
KV_OOM_HI_ANS = [("S|J", "Lekker, Oom! Ons ys was amper op."), ("K", "Oom is altyd betyds.")]
KV_OOM_BYE = [("O", "Nou ja, manne. Die tannie wag vir my."), ("O", "Ek moet ry, manne. Lekker braai!"),
              ("O", "Die skape moet nog getel word. Totsiens!")]
KV_OOM_BYE_ANS = ("S+J", "Mooi ry, Oom!")
KV_STORY: list[list] = [
    [("O", "Het ek julle al van die koedoe vertel?"), ("K", "Ja, Oom. Twee keer."), ("O", "Hy was so groot soos my bakkie!"),
     ("O", "Ek mik, ek skiet... en hy kyk net vir my."), ("S", "En toe, Oom?"), ("O", "Toe eet ons maar skaaptjops.")],
    [("O", "In '87 vang ek 'n kabeljou by Struisbaai."), ("O", "So lank soos daai braai!"),
     ("J", "Verlede jaar was hy so lank soos die bakkie, Oom."), ("O", "Hy groei elke jaar, Jannie.")],
    [("O", "Eendag in die Kruger staan 'n leeu langs my bakkie."), ("O", "Ek kyk vir hom. Hy kyk vir my."),
     ("O", "Toe loop hy. Hy was bang vir die snor."), ("K", "Almal is bang vir daai snor, Oom.")],
    [("O", "In my dag het ons sonder vuurhoutjies gebraai."), ("S", "Hoe, Oom?"), ("O", "Twee klippe en baie geduld."),
     ("J", "En die wors?"), ("O", "Die wors was ook geduldig.")],
    [("O", "Hierdie bakkie het al 800 000 km op die klok."), ("S", "Nog die oorspronklike enjin, Oom?"),
     ("O", "Ja! Die derde oorspronklike enjin.")],
    [("O", "Ek was in '95 by Ellispark."), ("O", "Toe Stransky daai skepskop skop..."),
     ("O", "...gooi ek my hoed in die lug. Nooit weer gesien nie."), ("K", "Is dit nie daai hoed nie, Oom?"),
     ("O", "Nee. Dis sy broer.")],
    [("O", "Die droogte van '92, manne. Die dam was 'n stofpad."), ("S", "Hoe het Oom oorleef?"),
     ("O", "Ek het die skape geleer om stof te vreet."), ("J", "En Oom?"), ("O", "Ek het Klipdrift gedrink. Dit het nie opgedroog nie.")],
    [("O", "My oupa het hierdie plaas met 'n os en 'n ploeg begin."), ("K", "En Oom?"),
     ("O", "Met 'n bakkie en 'n bank. Die os was goedkoper.")],
    [("O", "Ek het eendag 'n jakkals met my hande gevang."), ("J", "Regtig, Oom?"),
     ("O", "Ja. Hy het geslaap. Ek ook, amper."), ("K", "Klink soos Jannie.")],
]
KV_MENU: list[dict] = [
    {"log": "2 sosaties en 1 mielie", "kinds": ["sosatie", "mielie", "sosatie"],
     "talk": [("K", "Sosaties op die rooster!"), ("S", "Met appelkose? Lekker!")]},
    {"log": "3 mielies", "kinds": ["mielie", "mielie", "mielie"],
     "talk": [("J", "Mielies? Is ons op dieet?"), ("K", "Tannie se orders. Van ons eie land af.")]},
    {"log": "3 braaibroodjies", "kinds": ["broodjie", "broodjie", "broodjie"],
     "talk": [("S", "Braaibroodjies! Met tamatie en uie?"), ("K", "En baie kaas.")]},
    {"log": "1 snoek en 2 braaibroodjies", "kinds": ["broodjie", "snoek", "broodjie"],
     "talk": [("K", "Snoek met appelkooskonfyt."), ("J", "Nou praat Oom!")]},
    {"log": "2 tjops en 1 wors", "kinds": ["chop", "wors", "chop"],
     "talk": [("K", "Terug na die basics: tjops en wors."), ("S+J", "Lekker!")]},
    {"log": "3 skaaptjops", "kinds": ["chop", "chop", "chop"],
     "talk": [("K", "Skaaptjops van ons eie skape."), ("S", "Dis hoekom ons kuier, Koos.")]},
]
KV_MEAT_WAIT = [("K", "Eers eet ons hierdie, dan kom daar nog."), ("K", "Eet eers, manne! Dan kom daar meer.")]
KV_WOOD_NAME = {"kameeldoring": "Kameeldoring", "rooikrans": "Rooikrans", "sekelbos": "Sekelbos",
                "mopanie": "Mopanie", "wingerdstok": "'n Wingerdstok", "bloekom": "Bloekom", "swarthaak": "Swarthaak"}
KV_WOOD_ASK = ("K", "Jannie, die vuur wil hout he.")
KV_WOOD_CATCH = [[("K", "Kyk hoe vang hy!"), ("S", "Lekker!")], [("S", "Mooi gooi, ou!")],
                 [("K", "{wood} brand mooi."), ("J", "Beste hout in die distrik.")]]
KV_FLARE = ([("K", "Oeps! Te veel hout!"), ("K", "Sjoe! Water! Waar is my dop?"), ("K", "Haai! Die vuur is mal!")],
            [("S", "Moenie jou dop mors nie!"), ("S|J", "Moenie jou dop mors nie, Koos!")],
            [("K", "Dit was net water, manne."), ("K", "Dit was die laaste een in die koelboks..."),
             ("K", "Dis 'n braai, nie 'n brandweerstasie nie.")])
KV_TALK: list[list] = [
    ["kv_dark", ("J", "Kyk hoe helder is die sterre nou."), ("K", "Dankie, Eskom.")],
    ["kv_dark", ("S", "Is die host nog op?"), ("K", "Uptime {up}. Hy loop op die UPS.")],
    ["kv_gen", ("S", "Hoor jy daai kragopwekker?"), ("J", "Brrrrrrrr."), ("K", "Klink soos jou bakkie, Sakkie.")],
    ["kv_nosignal", ("J", "Ek het nie meer sein nie."), ("S", "Die toring se battery is pap."),
     ("K", "Lekker. Nou praat ons met mekaar.")],
    ["kv_dark", ("K", "Beurtkrag, manne. Ons braai deur."), ("S+J", "Altyd!")],
    ["kv_dark", ("J", "Wie het 'n kers?"), ("S", "Ons het 'n hele vuur, Jannie.")],
    ["kv_dark", ("S", "Die pompe staan. Die beeste moet wag vir water."), ("K", "Die windpomp werk nog. Dankie wind.")],
    ["kv_lit", ("S", "Volgens die app is daar beurtkrag om agtuur."), ("K", "Dan braai ons in die donker, soos ons oupas.")],
    ["kv_lit", ("S", "Eskom se skedule is soos my backups."), ("J", "Hoe so?"), ("S", "Niemand weet wanneer dit gebeur nie.")],
    ["kv_lit", ("J", "Wanneer is die volgende beurtkrag?"), ("K", "Kyk op die app."), ("J", "Die app is af.")],
    ["kv_lit", ("K", "Eskom het ons nog nie vanaand gevang nie."), ("S", "Klop op hout!"), ("K", "Ek klop op die braaihout.")],
    [("J", "Ek hoop Tannie bring weer melktert."), ("K", "En ek hoop Oom Faan bring weer ys.")],
    [("S", "Wat is die verskil tussen 'n braai en 'n barbecue?"), ("K", "By 'n braai vertel 'n oom stories.")],
    [("K", "Hout of houtskool?"), ("S+J", "Hout!"), ("K", "Korrek.")],
    [("S", "Wanneer kom Oom Faan weer kuier?"), ("K", "As die ys op is.")],
    [("J", "Bring Tannie vanaand pap?"), ("S", "As jy mooi vra.")],
    [("K", "'n Ware braaier gebruik nie gas nie."), ("J", "En 'n ware homelab het nie 'n cloud nie."), ("S", "Gesondheid! !salute")],
    [("J", "Sosaties of tjops?"), ("K", "Albei. Dis 'n braai.")],
    [("S", "Hoeveel stompe het ons nog?"), ("K", "Genoeg tot die son opkom.")],
    [("K", "Die kole is perfek vanaand."), ("S", "Is dit kameeldoring?"), ("K", "Uit die Kalahari, ja.")],
    [("J", "Oom Faan se bakkie het 'n nuwe duik."), ("S", "Dis nie 'n duik nie, dis karakter.")],
    ["kv_dish", ("J", "Ek vat nog 'n bietjie van Tannie se kos."), ("K", "Los vir my ook!")],
    ["kv_sosatie", ("S", "Wie het die sosaties gemarineer?"), ("K", "Tannie Sarie. Twee dae lank.")],
    ["kv_mielie", ("J", "Mielies met botter en sout!"), ("S", "Nou is dit fees.")],
    ["kv_snoek", ("K", "Snoek moet stadig gaar word."), ("J", "Soos ons internet op die plaas.")],
    ["kv_broodjie", ("S", "Braaibroodjies is die beste deel."), ("K", "Elke keer, ja.")],
    [("S", "Oom Faan se bakkie hoor jy van die hek af."), ("K", "Van die dorp af, Sakkie.")],
    [("J", "Tannie se pap is beter as die koöperasie s'n."), ("K", "Alles van Tannie is beter.")],
]
KV_WOODTALK = ["kv_wood", ("S", "Ruik jy daai {wood}?"), ("K", "Die beste rook in die land.")]

# ---- dokter disk, grappe, tricks ------------------------------------------------------------------------------
DK_VET = [("K|S", "Haha! Wagter dink jy is die veearts! !dk_laugh"),
          ("S|K", "Kyk hoe hardloop Wagter! Wit jas, groot paniek. !dk_laugh"),
          ("K|S", "Wagter! Dis nie die veearts nie! !dk_laugh")]
DK_QUIPS = [("K", "Is dit ernstig, dokter?"), ("S|K", "Sjuut! Die dokter luister."), ("J|S", "Moet ek ook hoes?")]
DK_NO = [("K", "Wag, man! Een ding op 'n slag."), ("S|J", "Nou nie. Kyk eers daar!"),
         ("J|K", "Later, later!"), ("K", "Geduld, my kind."), ("S|K", "Hou jou perde.")]
DK_JOKES: list[list] = [
    [("S", "Wat noem jy 'n vegan by 'n braai?"), ("J", "Verdwaal! !dk_laugh")],
    [("J", "Hoeveel sysadmins vat dit om 'n gloeilamp te vervang?"), ("S", "Geen. Dis 'n hardeware-probleem! !dk_laugh")],
    [("S", "Dokter, dokter, ek voel soos 'n tjop!"), ("K", "Sit stil, ek draai jou nou-nou om. !dk_laugh")],
    [("J", "Dokter, dokter, ek dink ek is 'n hardeskyf!"), ("K", "Ag nee, jy's net bietjie gefragmenteer. !dk_laugh")],
    [("J", "Ek het 'n UDP-grap..."), ("S", "Vertel!"), ("J", "Ek weet nie of jy hom gaan kry nie. !dk_laugh")],
    [("S", "Koos, het jy 'n backup gemaak?"), ("K", "Ja, op dieselfde disk. Veiliger so. !dk_laugh")],
    [("J", "Hoeveel ouens vat dit om te braai?"), ("S", "Een om te braai, drie om raad te gee. !dk_laugh")],
    [("S", "Koos, jou vuur is so klein..."), ("J", "Hoe klein?"), ("S", "Wagter wil hom doodblaas en 'n wens maak! !dk_laugh")],
    [("K", "Ek het 'n vleisgrap, maar hy's nog rou."), ("S", "Gee hom nog vyf minute. !dk_laugh")],
    [("J", "Wat is Wagter se gunsteling vleis?"), ("S", "Ander mense s'n! !dk_laugh")],
    [("K", "Ek lees 'n boek oor anti-swaartekrag."), ("J", "En?"), ("K", "Ek kan hom nie neersit nie! !dk_laugh")],
    [("S", "Wat noem jy 'n wors wat van die rooster af val?"), ("J", "'n Wors-case scenario! !dk_laugh")],
    [("S", "Jannie, hoekom het jy altyd twee dops?"), ("J", "Een vir nou, en een vir nou-nou! !dk_laugh")],
    [("S", "Wat noem jy 'n braaier wat nooit die vleis verbrand nie?"),
     ("J", "Weet nie, ek het nog nooit een ontmoet nie. !dk_laugh"), ("K", "Haai!")],
    [("J", "Ek eet net as die Bokke wen."), ("S", "En?"), ("J", "Kyk net hoe vet is ek! !dk_laugh")],
    [("K", "Hoekom het die geraamte nie braai toe gekom nie?"), ("S", "Hoekom?"), ("K", "Hy't nie die guts gehad nie! !dk_laugh")],
    [("S", "Hoekom het die boer 'n leer plaas toe gevat?"), ("J", "Hoekom?"), ("S", "Om by die hoogte van die mielies te kom! !dk_laugh")],
    [("K", "Wat se die een koei vir die ander by die dam?"), ("J", "Wat?"), ("K", "Moooi weer vandag. !dk_laugh")],
    [("J", "Wat noem jy 'n skaap met 'n masjiengeweer?"), ("S", "Wat?"), ("J", "Lammie-nator! !dk_laugh")],
    [("S", "Hoekom gaan die hoender oor die pad?"), ("K", "Om by die koöperasie uit te kom. Die mielies is goedkoper daar! !dk_laugh")],
    [("K", "Wat se die windpomp vir die wind?"), ("S", "Wat?"), ("K", "Jy draai my kop! !dk_laugh")],
    [("J", "Wat se die een stomp vir die ander?"), ("K", "Wat?"), ("J", "Ons gaan vanaand lekker brand! !dk_laugh")],
    [("S", "Hoekom het die dominee nie gebraai nie?"), ("J", "Hoekom?"), ("S", "Hy het die vuur gevrees! !dk_laugh")],
    [("K", "Wat is 'n boer se gunsteling program?"), ("S", "Wat?"), ("K", "Die weerberig. Al sewe keer per dag. !dk_laugh")],
    [("J", "Wat noem jy 'n donkie wat nie wil loop nie?"), ("S", "Wat?"), ("J", "'n Esel. Soos Sakkie. !dk_laugh"), ("S", "Haai!")],
]
DK_TALK: list[list] = [
    [("K", "Wanneer laas het jy jou disks laat toets?"), ("S", "Die dokter kom elke dag, Koos.")],
    [("J", "RAID is nie 'n backup nie."), ("K", "Ek weet, ek weet...")],
    [("S", "ZFS scrub vanaand?"), ("K", "Ja. En die rooster ook.")],
    [("K", "Wat is erger: 'n dooie disk of rou wors?"), ("S+J", "Rou wors!")],
    [("S", "Ek het my backups getoets."), ("K", "Regtig?"), ("S", "Nee. Maar ek het daaraan gedink.")],
    [("J", "Hoe oud is die host se disks?"), ("K", "Ouer as Wagter."), ("D", "Woef!")],
    [("K", "SMART status: PASSED."), ("J", "Smart? Dan is dit nie ons nie.")],
    [("S", "Drie backups, twee plekke, een buite die huis."), ("J", "En die tjops?"), ("K", "Een plek: my bord.")],
    ["dk_duty", ("J", "Wanneer kom die dokter weer?"), ("K", "Elke 24 uur, soos die melkery.")],
    ["dk_ok", ("S", "Disks gesond, vleis amper gaar."), ("K", "Die lewe is lekker.")],
    ["dk_sick", ("J", "Het Oom al daai siek disk vervang?"), ("K", "Die nuwe een is op pad van die dorp af."), ("S", "Maak solank 'n backup!")],
    ["dk_hot", ("S", "Die disk is warm, se die dokter."), ("K", "Alles is warm hier. Dis Afrika.")],
]
DK_STORY = [("K", "In 1995 het ek 'n tjop so hoog gegooi..."), ("S|J", "Hoe hoog?"),
            ("K", "Hy land vanaand! !dk_chop"), ("J|S", "...en hy is nog steeds rou. !dk_laugh")]
DK_FLIP_GO = ("K", "Kyk mooi: die legendariese dubbel-draai!")
DK_FLIP_END = [("J|S", "Tien uit tien!"), ("K", "Net soos in '95, manne.")]
DK_BONK = [("S", "Manne, kyk hierdie!")]
DK_BONK_END = [("S", "Eina!"), ("J|K", "Tien uit tien vir styl. Nul vir verstand. !dk_laugh")]
DK_FALL = [("J", "Ek leun net bietjie terug...")]
DK_FALL_END = [("J", "Ek's orraait! !dk_laugh")]
DK_DEAD = [("K", "Wagter! Speel dood!")]
DK_DEAD_MID = [("S|J", "Gee hom 'n Oscar!"), ("K", "Ag shame. Dan eet ek maar sy wors. !dk_alive")]
DK_HELLO_AUTO = "Dokter Disk, op roep! Tyd vir {what} se check-up."
DK_HELLO_CALL = "Iemand het die dokter geroep?"
DK_HELLO_NODISKS = [("X", "Ek kry geen disks nie. Is alles in die cloud?"), ("K|S", "Ons is ou skool, dokter.")]
DK_HELLO_NOPE = [("X", "Die disks is vanaand af-limiete. Net 'n huisbesoek."), ("J|S", "Ek voel bietjie honger, dokter."),
                 ("X", "Eet nog 'n tjop. Doktersvoorskrif!")]
DK_HELLO_BLIND = [("X", "Die probe sien nie die disks nie. Ek het root nodig."), ("S|K", "Probeer: --ssh root@..., dokter.")]
DK_SICK_ASK = ("K|S", "Is dit ernstig, dokter?")
DK_SICK_ANS = ("X", "Maak vandag nog 'n backup!")
DK_HEALTHY = "Gesond soos 'n perd!"
DK_THANKS = ("K|S", "Dankie, dokter!")
DK_SALUTE = ("K", "Op die disks! Gesondheid! !salute")
DK_HERE = ("X", "Rustig, ek is mos hier!")
DK_CALLING = ("K|S", "Ek bel die dokter. Hy kom nou-nou.")
DK_JAN_HOME = ("K|S", "Jannie is huis toe.")
DK_DOG_WHERE = ("K|S", "Waar is Wagter?")

# ---- plaas: the farm's own skits and critters ----------------------------------------------------------------
PL_TALK: list[list] = [
    ["pl_nag", ("J", "Hoor jy die jakkals roep?"), ("K", "Hy's by die kraal. Wagter, gaan kyk!"), ("D", "Woef!")],
    ["pl_nag", ("S", "Die uil sit weer in die bloekom."), ("K", "Hy wag vir die muise. Soos ons vir die wors.")],
    ["pl_nag", ("K", "Kyk die Melkweg vanaand."), ("J", "Oupa het gese dis die pad na die Kaap."), ("S", "Hy het gejok.")],
    ["pl_nag", ("J", "'n Vallende ster! Wens iets."), ("K", "Reen."), ("S", "Reen."), ("J", "Nog 'n tjop.")],
    ["pl_dag", ("S", "Die hoenders krap weer in Tannie se tuin."), ("K", "Dan is daar more eiers. Of moeilikheid.")],
    ["pl_dag", ("J", "Die donkie staan net daar en kyk."), ("K", "Hy's slimmer as ons, Jannie. Hy wag vir die kos.")],
    ["pl_dag", ("S", "Die skape is op die koppie."), ("K", "Tel hulle, Sakkie."), ("S", "Ek het by sewe aan die slaap geraak.")],
    ["pl_wind", ("K", "Hoor hoe kreun die windpomp."), ("S", "Hy't olie nodig."), ("K", "Soos ons almal.")],
    ["pl_dam", ("J", "Die dam is vol!"), ("K", "Dankie Vader. Nou kan die beeste drink."), ("S", "En ons kan swem."), ("K", "Jy nie.")],
    ["pl_droog", ("S", "Die dam is byna leeg."), ("K", "Ons soek reen. Bid, Sakkie."), ("J", "Ek bid al van Januarie af.")],
    [("K", "Die plaashek moet toe bly."), ("J", "Hoekom, Oom?"), ("K", "Sodat die beeste nie die braai kom bykom nie.")],
    [("S", "Oom Faan se bakkie staan by die hek."), ("K", "Dan kom hy ys bring. Of stories.")],
    [("J", "Die dominee ry verby."), ("K", "Steek die dops weg! Nee, los. Hy drink saam.")],
    [("S", "Wat se die Suiderkruis vanaand, Oom?"), ("K", "Suid is daar. Die vleis is hier.")],
    [("K", "Oupa het gese: as die beeste le, kom daar reen."), ("S", "Hulle le al drie dae."), ("J", "Hulle is net lui.")],
    [("S", "Rooibos of koffie more-oggend?"), ("K", "Rooibos. Met 'n beskuit."), ("J", "Twee beskuite.")],
    [("J", "Hoe gaan dit by die koöperasie?"), ("K", "Die diesel is op en die prys is af."), ("S", "Soos altyd.")],
    [("K", "Die kraal se draad is weer gebreek."), ("S", "Die bul?"), ("K", "Die bul.")],
    [("S", "Hou Oom nog skape of net beeste?"), ("K", "Albei. En een donkie wat niks doen nie.")],
    [("J", "Ek het die hoenders vanoggend kos gegee."), ("K", "Wagter ook?"), ("D", "Woef!"), ("J", "Hy het die eiers gegee.")],
    [("K", "Die mielies is al kniehoog."), ("S", "Dan is dit amper Kersfees."), ("J", "Op die plaas tel ons in mielies.")],
    [("S", "Hoeveel het die wors by die slaghuis gekos?"), ("K", "Moenie vra nie. Eet net.")],
    [("J", "Castle of Klipdrift, Oom?"), ("K", "Klipdrift en Coke. Castle is vir die jongmense."), ("S", "Ek is 'n jongmens.")],
    [("K", "Die ou windpomp het my pa nog opgerig."), ("S", "En hy draai nog."), ("K", "Beter as my knie.")],
    [("S", "Tannie se koeksisters het weer eerste gekom by die basaar."), ("K", "Elke jaar. Die dominee is die beoordelaar.")],
    [("J", "Wat doen 'n mens as die jakkals die lammers vat?"), ("K", "Jy kry 'n Wagter."), ("D", "Woef!")],
    [("K", "Daar's niks soos pap en sous by 'n plaasbraai nie."), ("S", "Behalwe die wors."), ("K", "Behalwe die wors.")],
]
PL_DOPRUN = [[("K", "Jannie, bring vir Oom 'n koue een uit die koelboks."), ("J", "Hier's hy, Oom! !pl_bring"), ("K", "Dankie, my kind.")],
             [("S", "Jannie, my dop is leeg."), ("J", "Ek's nie die kelner nie."), ("S", "Asseblief?"), ("J", "Hier. !pl_bring")]]
PL_POKE = [[("S", "Laat ek net die vuur bietjie regskuif... !pl_poke"), ("K", "Los my vuur, Sakkie. Dis MY vuur."),
            ("S", "Ek het hom net beter gemaak."), ("K", "Niemand maak my vuur beter nie.")],
           [("J", "Die kole le skeef. !pl_poke"), ("K", "Jannie! Weg van die tang af!"), ("J", "Ek het my hand gebruik."),
            ("K", "Dis erger.")]]
PL_GAS = [[("S", "Ek het 'n gasbraai gekoop."), ("K", "Jy het WAT gekoop?"), ("S", "Dis vinniger, Koos."),
           ("K", "Gas is nie 'n braai nie. Gas is 'n stoof wat buite staan."), ("J", "Oom het 'n punt."),
           ("S", "Julle is agter die tyd."), ("K", "Ons is op 'n plaas, Sakkie. Hout groei hier.")],
          [("J", "Wat is verkeerd met gas, Oom?"), ("K", "Geen rook, geen reuk, geen siel."), ("S", "Maar vinnig."),
           ("K", "Vinnig is vir die stad. Hier het ons tyd.")]]
PL_SLEEP = [[("S", "Jannie slaap weer."), ("K", "Los hom. Wagter, los sy dop!"), ("D", "Woef?"),
             ("J", "Ek het nie geslaap nie! Waar is my dop?"), ("S", "Vra Wagter.")]]
PL_HOUT = [[("K", "Die houtstapel is laag. Jannie, gaan haal. !pl_fetch"), ("J", "Hoekom altyd ek?"), ("K", "Jy's die jongste.")],
           [("S", "Ons het nog twee stompe oor."), ("K", "Jannie. Houtstapel. Nou. !pl_fetch"), ("J", "Ja, Oom.")]]
PL_HOUT_BACK = [("J", "Hier's die hout. Kameeldoring, soos Oom gevra het."), ("K", "Goeie kind. Gooi op.")]
PL_SELFIE = [[("J", "Kom, manne, 'n foto vir die groep! !pl_selfie"), ("S", "Se 'wors'!"), ("J+K+S", "WORS!"),
              ("K", "Het Wagter ingekom?"), ("D", "Woef!")],
             [("S", "Selfie vir Tannie, sodat sy weet ons werk. !pl_selfie"), ("K", "Ons werk mos. Kyk, ek draai die vleis."),
              ("J+K+S", "Kaas!")]]
PL_DOMINEE = [[("P", "Naand, manne. Ek was net in die omgewing..."), ("K", "Dominee! Ons het, uh, net rooibos hier."),
               ("S", "En Castle, Dominee."), ("P", "Dankie, Sakkie. Een vir die pad."), ("J", "Die dominee drink Castle?"),
               ("P", "Die Here het ook wyn gemaak, Jannie.")],
              [("P", "Goeienaand! Ek sien die rook van die kerk af."), ("K", "Dominee, kom sit. Daar's genoeg vleis."),
               ("P", "Ek sal net 'n tjoppie vat. Vir die basaar se krag."), ("S", "Die dominee eet soos 'n boer."),
               ("P", "Ek IS 'n boer se kind, Sakkie.")]]
PL_DOMINEE_BYE = [("P", "Nou ja, manne. Sondag sien ek julle in die kerk?"), ("K", "Ja, Dominee."), ("S+J", "Ja, Dominee."),
                  ("P", "En bring die wors.")]
PL_JAKKALS = [[("D", "Woef! Woef!"), ("K", "Die jakkals is by die kraal. Wagter, gaan!"), ("S", "Hy's weg. Goeie hond.")]]
PL_HADEDA_YARD = [("K", "Daai hadeda krap my gras op."), ("S", "Gooi hom met 'n pantoffel."), ("J", "Hy's groter as die pantoffel.")]
PL_HOENDER = [("S", "Die hoenders is uit!"), ("K", "Jannie, maak die hok toe."), ("J", "Hulle luister nie na my nie.")]
PL_DONKIE = [("J", "Die donkie kyk vir ons."), ("K", "Hy wil 'n tjop he."), ("S", "Hy's 'n vegetarier, Koos."), ("K", "Dan nie.")]
PL_STER = [("J", "Vallende ster!"), ("K", "Wens vir reen."), ("S", "Ek het vir 'n tjop gewens."), ("K", "Dit kom ook.")]
PL_WINDPOMP = [("S", "Die windpomp staan stil."), ("K", "Geen wind nie. Die dam moet wag.")]
PL_SKAPE = [("J", "Die skape loop oor die koppie."), ("K", "Hulle soek die laaste gras."), ("S", "Ons soek reen.")]
PL_BEESTE = [("S", "Die beeste staan by die hek."), ("K", "Hulle wil in. Hulle ruik die wors."), ("J", "Beeste eet nie wors nie."), ("K", "Hierdie s'n sal.")]

# the kernel log, when it is the farm talking
PL_LOG_JAKKALS = "jakkals: roep by die kraal, wagter op hoe gereedheid"
PL_LOG_HOENDERS = "hoenders: {n} uit die hok, krap in die werf"
PL_LOG_DONKIE = "donkie0: staan. kyk. doen niks. (normaal)"
PL_LOG_WINDPOMP = "windpomp: {rpm} rpm, dam op {pct}%"
PL_LOG_SKAPE = "skape: {n} op die koppie, 0 gemis"
PL_LOG_DOMINEE = "hek0: dominee se Corolla op die plaaspad"
PL_LOG_SELFIE = "foto: 1 selfie, {n} okes, 1 hond, 0 skerp"
