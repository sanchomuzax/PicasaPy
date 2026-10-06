"""A nyomat effektív felbontása és a minőségi sávok (#1782, #4280).

## A lelet

A felhasználó eddig úgy nyomtathatott ki egy 640×480-as képet 8×10
hüvelykre, hogy a program egy szót sem szólt. Az eredeti Picasa
nyomtatási panelje ezzel szemben **minőség-ellenőrzést** végez: a
választott nyomatmérethez kiszámolja minden kép effektív felbontását, a két
beállítható DPI-határ tesztjét összeadja Best/Good/Bad kóddá, majd a küszöb
alatti képekre ellenőrzést kér (`0x007451a0`, `0x00745980`).

Az eredeti szövegei (`ThumbUIPrint::Smallest`, `::ReviewPrompt`) a
`docs/specs/`-ben; a megjelenítés a `PrintDialog.qml` dolga, ez a modul
a felbontást és a minőségi sávot számolja. Ezek a számítások Qt-függetlenek
és determinisztikusak, mint a `layout.py`; a méretkatalógus területi
kiválasztása külön a `QLocale` rendszerbeállítását olvassa.

Az eredeti küszöbök és az egyenlőségi viselkedés a
[`docs/specs/picasa-nyomtatas.md`](../../../docs/specs/picasa-nyomtatas.md)
Review-sáv fejezetében van levezetve. Az állapotsori „kis kép” figyelmeztetés
és a soronkénti minőségi kód ugyanazt a 150 DPI-s `DPIWarning` beállítást
használja; a Good/Bad elválasztását a külön `DPISevere` beállítás adja.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QLocale

#: A „kicsi kép" küszöbének ALAPÉRTÉKE képpont/hüvelykben.
#:
#: ✅ **MÉRT érték** (#2359). A modul korábban azt írta ide, hogy „SAJÁT
#: DÖNTÉS, nem mért érték" — a mérés azóta megvan, és a döntést
#: igazolta: a minőség-számoló (`0x0085c060`) a `Preferences\DPIWarning`
#: kulcsot olvassa, és az alapértéket a `0x0085c08b` tölti be
#: (`mov dword ptr [esp+0x1c], 0x96` = **150**).
#:
#: Az eredetiben ez **rejtett beállítás**, nem fix szám — nálunk a
#: `printing/dpiWarning` kulcs írja felül (ld. `PrintController`).
KICSI_KUSZOB_DPI = 150

#: A Good/Bad határ binárisból mért alapértéke (`DPISevere`, `0x64`).
JO_MINOSEGI_KUSZOB_DPI = 100


def nyomtatasi_minoseg_kod(
    dpi: float,
    *,
    best_kuszob: int = KICSI_KUSZOB_DPI,
    good_kuszob: int = JO_MINOSEGI_KUSZOB_DPI,
) -> int:
    """A bináris minősítő bájtja: a két DPI-küszöbteszt összege.

    `2` = Best, `1` = Good, `0` = Bad. Az egyenlőség mindkét tesztnél
    igaz (`DPI >= küszöb`), és a beállítások a két alapértéket külön-külön
    felülírhatják.
    """
    return int(dpi >= best_kuszob) + int(dpi >= good_kuszob)


#: Egy hüvelyk centiméterben — a metrikus méretek innen származnak, hogy
#: a forrásban a HIVATALOS centiméteres érték álljon, ne egy kézzel
#: kiszámolt hüvelyk-tizedes (#1961).
CM_PER_HUVELYK = 2.54


def _cm(szelesseg_cm: float, magassag_cm: float) -> tuple[float, float]:
    """Centiméteres nyomatméret hüvelykben."""
    return (szelesseg_cm / CM_PER_HUVELYK, magassag_cm / CM_PER_HUVELYK)


class NyomatMeret(Enum):
    """A nyomatméretek hüvelykben — KÉT készletben (#1782, #1961).

    A `TARCA` az eredeti „wallet" mérete — a legkisebb a hüvelykes
    készletben. A metrikus tagok a `ytPrintSizes::` szövegcsalád
    centiméteres tételei (`stringres` 3478–3494)."""

    #: A 3×4 és 4×5 hüvelykes érték a spec ugrótáblájának 6. és 7. ága
    #: (`docs/specs/picasa-nyomtatas.md`, 604–605. sor); a többi a #1782.
    M3X4 = (3.0, 4.0)
    M3_5X5 = (3.5, 5.0)
    M4X5 = (4.0, 5.0)
    M4X6 = (4.0, 6.0)
    M5X7 = (5.0, 7.0)
    M8X10 = (8.0, 10.0)
    TARCA = (2.5, 3.5)

    #: Metrikus nyomatméretek (`ytPrintSizes::`, stringres 3478–3494).
    #: A CD-borító is ide ágazik, de a spec nem közöl hozzá konkrét méretet,
    #: ezért nincs becsült enumtagja.
    M5X8CM = _cm(5, 8)
    M9X13CM = _cm(9, 13)
    M10X15CM = _cm(10, 15)
    M13X18CM = _cm(13, 18)
    M15X20CM = _cm(15, 20)
    M20X25CM = _cm(20, 25)
    #: ⚠️ DÖNTÉS: a „Teljes oldal" nálunk **A4** (210 × 297 mm). Az
    #: eredetiben a NYOMTATÓ papírmérete adja; nekünk a minőség-számoláshoz
    #: kell egy konkrét lap, és a metrikus készlethez az A4 tartozik. Egy
    #: helyen áll, hogy mérés esetén egyetlen sort kelljen átírni.
    TELJES_OLDAL = _cm(21.0, 29.7)

    #: `ytPrintSizes::ePassport` — MÉRT, négyzet méret (#1401, az
    #: ugrótábla `0x00776e20`/`0x00776ecb`: mindkét oldal ugyanaz a **2,0**
    #: konstans). ⚠️ SZÁNDÉKOSAN nincs sem a `HUVELYK_KESZLET`-ben, sem a
    #: `METRIKUS_KESZLET`-ben: az eredetiben az Útlevélkép parancs — nem a
    #: kézi méretválasztó — állítja be, ugyanúgy, ahogy az `eContact`
    #: (Indexképek) is a saját parancsán (`printContactSheet`) át érhető
    #: el, nem a méretlistából (ld. a Colab-mérés hat gombja: Wallet ·
    #: 3.5x5 · 4x6 · 5x7 · 8x10 · Full Page — Passport nincs köztük).
    PASSPORT = (2.0, 2.0)

    @property
    def szeles_huvelyk(self) -> float:
        return self.value[0]

    @property
    def magas_huvelyk(self) -> float:
        return self.value[1]


#: A hüvelykes méretválasztó sorrendje. A Tárca elöl és a Teljes oldal
#: hátul marad a mért gombsorrend szerint; a #4257 a 3×4-et és 4×5-öt
#: az eredeti 17-es lista szerinti helyre illeszti.
#:
#: ✅ JAVÍTVA (#3712-review): korábban ez a tuple csak ÖTÖS volt — a Tárca
#: a VÉGÉN állt, és a `TELJES_OLDAL` egyáltalán hiányzott belőle. A
#: `research/testdata/screenshot/Colab EN 29…`/`…30…` felvételek
#: egyértelműen mutatják a hat gombot ABBAN a sorrendben, ami itt áll:
#: Wallet elöl, Full Page a végén. A korábbi ötös a #1782 mérése volt, de
#: az csak a MÉRETEKET igazolta, a listabeli POZÍCIÓJUKAT és a Full Page
#: jelenlétét nem.
HUVELYK_KESZLET: tuple[NyomatMeret, ...] = (
    NyomatMeret.TARCA,
    NyomatMeret.M3X4,
    NyomatMeret.M3_5X5,
    NyomatMeret.M4X5,
    NyomatMeret.M4X6,
    NyomatMeret.M5X7,
    NyomatMeret.M8X10,
    NyomatMeret.TELJES_OLDAL,
)

#: A metrikus méretválasztó, a `ytPrintSizes` eredeti sorrendjében (#1961).
#:
#: ⚠️ SZÁNDÉKOSAN NINCS Tárca-tagja. A `printpanel.tre` mind a 17
#: `ytPrintSizes` mérethez UGYANAZT a hat gombhelyet
#: (`walletbutton`/`3x5button`/`4x6button`/`5x7button`/`8x10button`/
#: `fullbutton`) használja — a területi mértékegység dönti el, MELYIK
#: méret kerül az egyes gombhelyekre. A tulajdonos felvétele (#1953,
#: `#1953-nyomtatas-kep-kicsi.jpg`) szerint metrikus környezetben a
#: `walletbutton` helyére metrikus méret kerül — a Tárca (nem metrikus
#: fogalom) ilyenkor kiesik, a Full Page pedig MINDIG az utolsó. A #4257
#: a 15×20 cm-es nyomatot a 13×18 és 20×25 cm közé illeszti.
METRIKUS_KESZLET: tuple[NyomatMeret, ...] = (
    NyomatMeret.M5X8CM,
    NyomatMeret.M9X13CM,
    NyomatMeret.M10X15CM,
    NyomatMeret.M13X18CM,
    NyomatMeret.M15X20CM,
    NyomatMeret.M20X25CM,
    NyomatMeret.TELJES_OLDAL,
)

#: Az eredeti Picasa öt gyorsválasztójának metrikus indulóértékei (#4435).
#: A PicasaPy katalógusában szereplő 15×20 cm és Teljes oldal ettől külön
#: marad; ezek nem részei az eredeti ötösnek.
METRIKUS_ALAPMERETEK: tuple[NyomatMeret, ...] = (
    NyomatMeret.M5X8CM,
    NyomatMeret.M9X13CM,
    NyomatMeret.M10X15CM,
    NyomatMeret.M13X18CM,
    NyomatMeret.M20X25CM,
)

#: Az eredeti Picasa öt gyorsválasztójának angolszász indulóértékei (#4435).
HUVELYK_ALAPMERETEK: tuple[NyomatMeret, ...] = (
    NyomatMeret.TARCA,
    NyomatMeret.M3_5X5,
    NyomatMeret.M4X6,
    NyomatMeret.M5X7,
    NyomatMeret.M8X10,
)


def _metrikus_teruleti_meres() -> bool:
    """A rendszer területi mértékegysége metrikus-e."""
    return QLocale().measurementSystem() == QLocale.MeasurementSystem.MetricSystem


def keszlet_teruleti_mereshez() -> tuple[NyomatMeret, ...]:
    """A rendszer területi mértékegységéhez tartozó nyomatméret-katalógus.

    Az eredeti LOCALE_IMEASURE döntésének Qt-megfelelője. A katalógus a
    meglévő PicasaPy-méreteket és a saját sorrendjüket őrzi.
    """
    if _metrikus_teruleti_meres():
        return METRIKUS_KESZLET
    return HUVELYK_KESZLET


def alapmeretek_teruleti_mereshez() -> tuple[NyomatMeret, ...]:
    """Az öt gyorsválasztó induló értéke a területi mértékegység szerint.

    Ezeket a mentett PrintSize0–4 beállítások felülírják; a bővebb
    ytPrintSizes-katalógussal nem azonos a lista.
    """
    if _metrikus_teruleti_meres():
        return METRIKUS_ALAPMERETEK
    return HUVELYK_ALAPMERETEK


def effektiv_dpi(
    kep_szelesseg: int, kep_magassag: int, meret: NyomatMeret
) -> int:
    """Hány képpont jut egy hüvelykre, ha a képet erre a méretre nyomtatjuk.

    A kép a nyomat területére **illeszkedik**, és a nyomat elfordítható,
    ezért a kép hosszabbik oldala a nyomat hosszabbik oldalára kerül. A
    két irány közül a **rosszabbik** dönt: ott nyúlik legjobban a képpont.

    Értelmetlen (nulla vagy negatív) képméretre `0` — hiányzó adatból ne
    szülessen hamis megnyugtatás."""
    if kep_szelesseg <= 0 or kep_magassag <= 0:
        return 0
    kep_hosszu, kep_rovid = sorted((kep_szelesseg, kep_magassag), reverse=True)
    nyomat_hosszu, nyomat_rovid = sorted(
        (meret.szeles_huvelyk, meret.magas_huvelyk), reverse=True
    )
    return int(min(kep_hosszu / nyomat_hosszu, kep_rovid / nyomat_rovid))


@dataclass(frozen=True)
class MinosegOsszegzes:
    """Amit a nyomtatási panel állapotsora kiír."""

    #: a kijelölés LEGROSSZABB képének effektív felbontása
    #: (`ThumbUIPrint::Smallest` — nem átlag)
    legkisebb_dpi: int
    #: hány kép esik a küszöb alá (`ThumbUIPrint::ReviewPrompt`)
    kicsik: int
    #: a kijelölés mérete
    osszes: int

    @property
    def keszen_all(self) -> bool:
        """„You are ready to print." — csak ha van mit nyomtatni, ÉS
        egyetlen kép sem esik a küszöb alá."""
        return self.osszes > 0 and self.kicsik == 0


def minoseg_osszegzes(
    kepmeretek, meret: NyomatMeret, *, kuszob: int = KICSI_KUSZOB_DPI
) -> MinosegOsszegzes:
    """A kijelölés minőség-összegzése a választott nyomatmérethez.

    A `kepmeretek` `(szélesség, magasság)` párok sorozata. Az **ismeretlen
    méretű** kép (0 vagy hiányzó oldal) KICSINEK számít: ha nem tudjuk,
    mekkora, ne nyugtassuk meg a felhasználót."""
    parok = list(kepmeretek)
    if not parok:
        return MinosegOsszegzes(legkisebb_dpi=0, kicsik=0, osszes=0)
    dpik = [effektiv_dpi(sz, m, meret) for sz, m in parok]
    return MinosegOsszegzes(
        legkisebb_dpi=min(dpik),
        kicsik=sum(1 for d in dpik if d < kuszob),
        osszes=len(parok),
    )
