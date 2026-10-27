"""A nyomtatásvezérlő közös, témamixinek között használt állandói."""

from __future__ import annotations

import logging

_log = logging.getLogger("picasapy.app.print_controller")

# a margón belüli terület köré hagyott margó — az egyszerű elrendezés
# rögzített értéke (a részletes sablonrendszer, benne az állítható margóval,
# NEM ebben a körben készül el, ld. a modul docstringje)
_MARGIN_MM = 5.0

#: #3016: legfeljebb ennyente engedjük vissza az eseményhurkot a festés
#: közben (ms). MÉRT szám, nem ízlés: a laponkénti `processEvents` a 12
#: lapos, 12 megapixeles feladatot 2388 → 2815 ms-ra nyújtotta (+18 %). A
#: 200 ms a szokásos UI-válaszidő-küszöb alatt marad (a felhasználó még
#: „élőnek" látja a felületet), de tizenkét lapnál már csak néhányszor
#: fizetjük meg az árat, nem tizenkétszer.
#:
#: A ritkítás UTÁN a 12 lapos esetet háromszor mértem: −100 / +7 / +144 ms
#: (medián +7) — a különbség tehát a futások közti SZÓRÁSBA esik, szemben a
#: ritkítás nélküli, KÖVETKEZETES +427 ms-mal. Ezzel teljesül a jegy
#: negyedik feltétele: „az észlelt megállás ideje nem nő".
_FRISSITES_MS = 200.0

# #1819: az előnézeti lap felbontása. Nem nyomdai érték — csak annyi, hogy
# a képernyőn éles legyen a legnagyobb nyomatméreten is (8×10 hüvelyk ×
# 96 = 768×960 képpont), és a PNG még gyorsan elkészüljön.
_ELONEZET_DPI = 96.0
_PRINT_SIZE_PRESET_KEYS = tuple(f"printing/sizePreset{index}" for index in range(1, 6))
_PRINT_OPTION_SIZES = (
    "M3X4",
    "M3_5X5",
    "M4X5",
    "M4X6",
    "M5X7",
    "M8X10",
    "M5X8CM",
    "M9X13CM",
    "M10X15CM",
    "M13X18CM",
    "M15X20CM",
    "M20X25CM",
    "TARCA",
    "CDSIZE",
    "PASSPORT",
    "CONTACT",
)

#: A `ytPrintSizes` katalógus az eredeti stringres-táblázat sorrendjében.
#: `CDSIZE` megjelenik, de nincs fizikai mérete és a QML-ben letiltott;
#: `CONTACT` indexkép-elrendezés, nem `NyomatMeret`.
_PICASA_PRINT_SIZE_IDS = (
    "M3X4",
    "M3_5X5",
    "M4X5",
    "M4X6",
    "M5X7",
    "M8X10",
    "M5X8CM",
    "M9X13CM",
    "M10X15CM",
    "M13X18CM",
    "M15X20CM",
    "M20X25CM",
    "TARCA",
    "CDSIZE",
    "PASSPORT",
    "CONTACT",
    "TELJES_OLDAL",
)
