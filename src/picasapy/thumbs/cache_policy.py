"""A thumbnail-cache belső dekódolási és érvénytelenítési szabályai."""

from __future__ import annotations

import sys
import threading

# #673: a videó-megnyitás háttere KÉNYSZERÍTETTEN FFMPEG.
#
# Háttér-megjelölés nélkül az OpenCV a saját prioritási sorát követi
# (FFMPEG=1900, majd GSTREAMER=1800): ha a fájlt az FFMPEG nem tudja
# megnyitni — sérült vagy csonka videó —, VISSZAESIK a GStreamerre, az
# pedig több szálból egyszerre hívva SIGSEGV-vel viszi el az EGÉSZ
# processzt. Elég egy sérült videó a megnyitott mappában.
#
# Mérve (64 bájtos szemét-.mp4, 4 szál × 5 kör, 15 futás):
#   * mai állapot (automatikus háttérválasztás): 12 összeomlás / 15
#   * globális zárral sorosítva:                  5 összeomlás / 15
#   * cv2.CAP_FFMPEG-re kényszerítve:             0 összeomlás / 15
#
# A zár önmagában nem javítás: a GStreamer a saját (Python elől láthatatlan)
# csővezeték-szálain omlik össze, azok pedig túlélik a `release()`-t, így
# a Python-szintű sorosítás nem éri el őket. A #4273 ezért a dekódolót külön,
# időkorlátos folyamatban futtatja; a FFMPEG kényszerítése a GStreamerre
# visszaesést is kizárja.
#
# Amit a kényszerítéssel VESZTÜNK: ha egy videót az FFMPEG nem nyit meg, a
# GStreamer már nem kap esélyt — az ilyen fájl bélyegkép nélkül marad. Ez a
# helyes viselkedés (a sérült fájl bélyegkép nélküli, de a program él), és a
# gyakorlatban nem jár tényleges veszteséggel: a `VIDEO_EXTENSIONS` minden
# konténerét (mp4/mov/avi/mkv/wmv/3gp/mts…) az avformat kezeli.
#
# Ha a telepített OpenCV FFMPEG NÉLKÜL épült, nincs mire kényszeríteni —
# ilyenkor marad az automatikus választás, de a zárral. A külön folyamat
# ilyenkor is megvédi a főfolyamatot az összeomlástól és a beragadástól.
#
# #1611: FÜGGVÉNY, nem modulszintű konstans — és nem csak importálja a
# cv2-t, hanem MEG IS HÍVJA. Modulszinten ez a sor egymaga behozná az
# OpenCV-t az indulási láncban (`thumbs/__init__` → `thumbs/cache`), és
# ezzel elvenné a lusta import teljes nyereségét. Az eredmény egyszer
# számolódik ki, az első videó-bélyegképnél.
_ffmpeg_allapot: bool | None = None

# #4273: egy hibás vagy beragadó natív videódekóder ne tarthassa fel a
# bélyegkép-rács egyik munkaszálát korlátlan ideig. A határidő lejártakor a
# subprocess leállítja a dekódoló alfolyamatot; a szolgáltató a már meglévő
# hibás-kép útján placeholdert és jelzést ad a felületnek.
_VIDEO_DECODE_TIMEOUT_S = 5.0


#: A futtató folyamat adatai (frozen, executable) — modulszintű fogantyú,
#: hogy a teszt ezt cserélje, ne a globális `sys`-t.
_futtato = sys

# Csak az FFMPEG-telen tartaléknál használt sorosító zár (ld. fent).
_VIDEO_FALLBACK_LOCK = threading.Lock()

# #163: a szerkesztett (filters=) bélyegkép bázisa a célméret többszöröse —
# a lánc (jellemzően crop64) a nagy bázison fut, és csak a VÉGEREDMÉNYT
# kicsinyítjük a célméretre. Így az erős vágás után is éles marad a kép
# (nem a kész kis thumbnailt vágjuk tovább, amit a rács homályosan
# felnagyítana). A faktor 4: 25%-os vágás után a kimenet még pont a teljes
# célméret; ennél erősebb vágásnál is jóval élesebb a naiv útnál.
_EDIT_BASE_FACTOR = 4

# #525: a Glimmer-effektek (Holga, Lomo, Vignette, ...) sugár-/elmosás-
# képletei RÉSZBEN abszolút képpontszámban vannak megadva (a Flash
# `blurX`/`blurY` 255-ös korlátjának öröksége, ld. `belso_ragyogas.
# blur_atvalto`) — ha a láncot a MÁR kicsinyített (pl. 96–256px-es)
# thumbnailra futtatjuk, ez a sugár relatíve sokszorosan szélesebb
# vignettát rajzol, mint amit Picasa nagy (2560px-es) exportján látni
# (mérve: #525 jegy, `referencia/holga` és `referencia/lomo`). A puszta
# `_EDIT_BASE_FACTOR` (kis thumbnail-méretnél 96×4=384, 256×4=1024) ezt
# NEM oldja meg — a mérés szerint a torzulás csak kb. 1500–2000px-es
# bázisnál kezd belapulni. Ezért a bázis egy ALSÓ KORLÁTOT is kap
# (`_EDIT_BASE_MIN`) a puszta szorzat mellé, felül pedig egy teljesítmény-
# korlátot (`_EDIT_BASE_CAP`) — 2560px-es (natív méretű) bázison a Holga
# ~1 mp/kép, ami a bélyegkép-gyorsítótár (egyszeri, háttérszálas) útjára
# nézve nagyságrendi lassulás lenne. A mért kompromisszum (2560×1702-es
# referenciafotón, Holga): bázis 1536px → átlagfény-eltérés a Picasa
# kimenetétől 33,2 (a "kicsinyít-majd-effektez" út 47,9-éhez képest),
# 0,57 mp/kép; bázis 2048px → 21,2, 1,08 mp/kép; teljes (2560px) → 14,1,
# 2,65 mp/kép. Az 1536–2048-as sáv adja a legjobb arányt — jelentős
# javulás, a lassulás pedig még mindig kevesebb, mint egy nagyságrend a
# korábbi (384–1024px-es) bázishoz képest.
_EDIT_BASE_MIN = 1536
_EDIT_BASE_CAP = 2048

# #525: a bázisméret-képlet fenti változása miatt a RÉGI (a bug miatt
# sötét) szerkesztett bélyegképeket el kell avultatni — a cache-kulcs a
# forrás/mtime/méret/lánc mellé ezt a verziószámot is beleszámítja, így a
# meglévő lemez-cache-ben ragadt sötét bejegyzések nem találatot adnak,
# hanem újragenerálódnak az új bázismérettel. Csak a #163 SZERKESZTETT
# (`filters=` láncos) bélyegképeket érinti — a sima `get_or_create` út
# (a könyvtár nagy része) változatlan, nem kell újragenerálódnia.
_EDIT_CACHE_VERSION = 12
# 3 (#3472): a keret két vastagsága a bázis és a teljes kép arányában
# skálázódik — a korábbi, túl vastag keretes bélyegképek újragenerálódnak.
# 4 (#3827): a belső ragyogás (Vignetta, Matt, Múzeumi matt, Lomo, Holga,
# Éjjellátó, Képregény) a natív lánccal számol — a régi, erf-modelles
# szerkesztett bélyegképek újragenerálódnak.
# 5 (#3902): a Színátmenet `ffffffff`-es fehérje egy szinttel sötétít; a
# szint a vele egy kiadásba szánt Lágyítás 0-s keverését is fedi (#3895).
# 6 (#3913, #3917): a Ragyogás (`glow`, `glow2`) az eredeti egész
# aritmetikájával, a Lágy fókusz (`radblur`) elmosási sugara a bináris
# 0,01-es képszélesség-hányadával számol — az érintett szerkesztett
# bélyegképek újragenerálódnak.
# 7 (#3931): a Holga fekete-fehér lépése (`bw_tint`) Haeberli-súlyokkal és
# a natív fixpontos színmátrix-alkalmazóval számol — a régi, Rec.601-es
# lebegőpontos modellel készült szerkesztett bélyegképek újragenerálódnak.
# 8 (#3928): a régi Szemcse (`grain`/`grain2`) csomós, középtónusban erős
# zajt ad az eddigi egyenletes Gauss-zaj helyett — az érintett szerkesztett
# bélyegképek újragenerálódnak.
# 9 (#3939): a Gamma Correct (`gamma`) a 8 bites gamma-táblán fut, dither
# nélkül — a régi, 16 bites ditheres szinthúzón renderelt szerkesztett
# bélyegképek újragenerálódnak.
# 10 (#3942): az `AdjustCurves`-lánc a mestergörbe értékét kerekítés és
# vágás nélkül adja tovább a csatornagörbének, ami a töréspontokon túl
# extrapolál — az érintett (Sixties, Cinemascope, CrossProcess stb.)
# szerkesztett bélyegképek újragenerálódnak.
# 11 (#3951): a `SimpleColorMatrix` és a `Tint` szürkítése az eredeti
# fixpontos színmátrix-alkalmazóval számol (Neon, Lomo, Boost, Holga,
# Áttűnés, Kinemaszkóp, PicnikTint) — az érintett szerkesztett
# bélyegképek újragenerálódnak.
# 12 (#3958): a Lomo és a Holga körmaszkja 16 bites pozícióval, egész
# koordinátával és megálló-táblával számol — az érintett szerkesztett
# bélyegképek újragenerálódnak.
