"""#1719 — a párbeszédek NE épüljenek fel induláskor.

## A regresszió, amit ez az őr megakadályoz

A tulajdonos 2026-08-28-án azt jelentette, hogy a program „kibaszott
lassan” indul. A mérés igazolta: az ablakig **13 118 ms**, ebből a
QML betöltése **11 429 ms = 87 %**. Négy verzió alatt nőtt így:

| verzió | QML betöltése |
|---|---:|
| 0.8.133 | 996 ms |
| 0.8.137 | 3 806 ms |
| 0.8.138 | **11 429 ms** |

Az ok a #1720 mérése szerint a **példányosítás**: a `Main.qml` több mint
húsz párbeszédet deklarált közvetlenül, és mind felépült MINDEN
induláskor, akkor is, ha a felhasználó egyiket sem nyitotta meg —
együtt **4600 QObject**, az indulási fa 31 %-a.

A javítás a `DeferredDialog` (`Loader { active: false }`). A ma esti
mérés a mai main-en: **QML betöltése 1718 ms** (meleg) / 2506 ms (hideg),
tehát a regresszió megszűnt.

## Egy MÉRÉS, amit a tábla őriz

A `FileOpsDialogs` halasztását kipróbáltuk, és **elvetettük — méréssel**:

| | main | halasztva |
|---|---:|---:|
| indulási fa objektumai | 12 343 | 11 792 |
| QML betöltése | 1718 ms | 1757 ms |

551 objektummal kevesebb, **időben viszont semmi** (szóráson belül).
Cserébe 14 tesztfájl keresi közvetlenül a párbeszéd gyerekeit. Mérhető
haszon nélküli, nagy kockázatú változtatás — ezért került a felmentések
közé, a számokkal együtt, hogy egy későbbi kör ne kezdje elölről.

## Miért SZERKEZETI őr, és nem időmérés

A jegy kimondottan ezt kéri: *„őr, ami MUNKAMENNYISÉGET mér …, nem időt”*.
Volt ebben a családban egy abszolút objektumszám-plafon is — azt a #1720
körében kivettük: egyetlen új menü átvitte, és a plafon emelése után is
ugyanaz maradt a kockázat. **Egy szám a jövőt tippeli; ez az őr a
HIBAOSZTÁLYT fogja meg**: aki új párbeszédet vesz fel a `Main.qml`-be,
vagy `DeferredDialog`-ba teszi, vagy ide írja, MIÉRT nem.
"""

from __future__ import annotations

import re
from pathlib import Path

_MAIN = (
    Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/Main.qml"
)

#: Azok a párbeszédek, amelyek SZÁNDÉKOSAN azonnal felépülnek, indoklással.
#: Ami itt nincs benne és mégis közvetlenül épül fel, az hiba.
#:
#: ⚠️ A lista csak RÖVIDÜLHET. Ha valaki bővíteni akarja, előbb mérje meg,
#: hány QObjectbe kerül — a #1720 mérése szerint egy közepes párbeszéd
#: 200–400 objektum, és az indulási idő ezen múlt.
AZONNAL_EPULO = {
    "InitialScanDialog": (
        "#449: az ELSŐ indítás kérdése. Az ablak megjelenése után azonnal "
        "elő kell jönnie — halasztva egy üres ablakot látna a felhasználó, "
        "mielőtt a kérdés megérkezik."
    ),
    "CreateDialogs": (
        "#1612 MÉRTE, és a #1743 őre fogta meg, miért nem lehet: a "
        "`CreateDialogs.qml` KÉT `Connections { target: controller }` "
        "blokkot tart — a kollázs/film EREDMÉNYÉT (`onCollageFinished`, "
        "`onCollageFailed`, `onMovieProgress`) és az élő előnézetet. "
        "Halasztva ezek a kezelők nem léteznek, tehát a KollázsPANELről "
        "indított kollázs visszajelzése NÉMÁN elveszne. Előbb a hallgatókat "
        "kell a `Main.qml`-be vinni (#2096), és csak utána halasztható."
    ),
    "CollageDraftDialog": (
        "#1051: a kollázs-piszkozat visszaállításának felajánlása "
        "induláskor. Ugyanaz az ok, mint az InitialScanDialog-nál — és "
        "#1612 MÉRTE, hogy a halasztás itt semmit nem hozna: az "
        "`openIfNeeded()` a főablak `Component.onCompleted`-jében fut, "
        "feltétel nélkül, tehát az `ensure()` ugyanabban a pillanatban "
        "felépítené. Nulla nyereség, plusz egy indirekció."
    ),
    "FileOpsDialogs": (
        "603 sor, a leghosszabb párbeszéd-fájlunk — a halasztása MÉRVE "
        "551 objektumot spórolna (12 343 → 11 792), IDŐBEN viszont "
        "semmit (1718 → 1757 ms, szóráson belül). Cserébe 14 tesztfájl "
        "keresi közvetlenül a gyerekeit, tehát mind átkötendő lenne. "
        "Mérhető haszon nélküli, nagy kockázatú változtatás — külön kör "
        "dolga, ha egyszer lassabb gépen mérhető nyereséget mutat (#1719)."
    ),
    "AddFileDialog": (
        "#1633: 63 soros burkoló a NATÍV `QtQuick.Dialogs` fájlválasztó "
        "körül — a felület nagy részét a rendszer adja, nem mi építjük. "
        "A halasztás itt több `ensure()`-hívást kívánna, mint amennyi "
        "objektumot megspórol."
    ),
    "TesztuzemNaploDialog": (
        "#1654: 33 sor, szintén natív fájlválasztó-burkoló. Ugyanaz az "
        "ok, mint az AddFileDialog-nál: a mérhető nyereség nulla közeli."
    ),
    "PicasaImportDialog": (
        "#146: 164 sor, EGYETLEN (integrátori) hívóhellyel. A halasztás "
        "mérhető nyeresége kicsi, a hívólánc átkötése viszont öt tesztet "
        "érint — külön kör dolga, ha egyszer méréssel indokolható."
    ),
    "ConfirmDialog": (
        "Általános megerősítő — több, egymástól független hívóhely "
        "használja ugyanazt a példányt."
    ),
}

#: A közvetlen példányosítás mintája: `XyzDialog {` vagy `XyzDialogs {`.
_PARBESZED = re.compile(r"(\w*Dialogs?)\s*\{")


def _forras() -> str:
    """A `Main.qml` kommentek nélkül — a kommentben szereplő példa ne
    számítson példányosításnak (a projekt visszatérő csapdája)."""
    return re.sub(r"//[^\n]*", "", _MAIN.read_text(encoding="utf-8"))


def _deferred_tartomanyok(szoveg: str) -> list[tuple[int, int]]:
    """A `DeferredDialog { … }` blokkok (kezdet, vég) párjai, ZÁRÓJEL-
    PÁROSÍTÁSSAL.

    ⚠️ Az első változat egy 400 karakteres visszatekintéssel döntött, és
    MUTÁCIÓS PRÓBÁN MEGBUKOTT: egy szomszédos `DeferredDialog`
    `sourceComponent`-je a látókörbe esett, ezért a közvetlenül
    példányosított párbeszéd is halasztottnak látszott. A zöld teszt
    ilyenkor nem bizonyíték — a párosítás az egyetlen megbízható alak."""
    tartomanyok: list[tuple[int, int]] = []
    for talalat in re.finditer(r"DeferredDialog\s*\{", szoveg):
        melyseg = 0
        i = talalat.end() - 1
        while i < len(szoveg):
            if szoveg[i] == "{":
                melyseg += 1
            elif szoveg[i] == "}":
                melyseg -= 1
                if melyseg == 0:
                    tartomanyok.append((talalat.start(), i))
                    break
            i += 1
    return tartomanyok


def _kozvetlenul_epulok() -> set[str]:
    szoveg = _forras()
    tartomanyok = _deferred_tartomanyok(szoveg)
    ki: set[str] = set()
    for talalat in _PARBESZED.finditer(szoveg):
        nev = talalat.group(1)
        if nev in ("DeferredDialog", "Dialog"):
            continue
        hely = talalat.start()
        if not any(kezd < hely < veg for kezd, veg in tartomanyok):
            ki.add(nev)
    return ki


class TestAHalasztas:
    def test_minden_parbeszed_halasztott_vagy_INDOKOLT(self):
        indokolatlan = sorted(_kozvetlenul_epulok() - set(AZONNAL_EPULO))
        assert indokolatlan == [], (
            "ezek a párbeszédek MINDEN induláskor felépülnek, indoklás "
            f"nélkül: {indokolatlan}. Tedd `DeferredDialog`-ba, vagy vedd "
            "fel az `AZONNAL_EPULO` táblába azzal, hogy MIÉRT nem lehet "
            "halasztani (#1719/#1720)."
        )

    def test_a_tabla_nem_tartalmaz_elavult_tetelt(self):
        """Az őr foga MÁSIK irányban: ha egy párbeszéd időközben
        halasztottá vált, a felmentése tűnjön el a táblából — különben a
        lista csendben hízik, és a következő bővítés már nem tűnik fel."""
        elavult = sorted(set(AZONNAL_EPULO) - _kozvetlenul_epulok())
        assert elavult == [], (
            f"ezek már halasztottak, a felmentésük törlendő: {elavult}"
        )

    def test_minden_felmentesnek_van_ERDEMI_indoka(self):
        for nev, indok in AZONNAL_EPULO.items():
            assert len(indok) > 60, f"{nev}: az indok túl szűkszavú"

    def test_a_tabla_szandekosan_rovid(self):
        """A lista csak rövidülhet. Ha ez a szám nőni kezd, az azt
        jelenti, hogy a halasztás szabályból kivétellé válik."""
        assert len(AZONNAL_EPULO) <= 9


class TestAHalasztasELO:
    def test_van_egyaltalan_halasztott_parbeszed(self):
        """Üres őr elleni próba: ha a `DeferredDialog` eltűnne a fájlból,
        a fenti állítások üresen is teljesülnének."""
        halasztott = _forras().count("DeferredDialog {")
        # ⚠️ SZÁNDÉKOSAN nem rögzített szám: az a jövőt tippelné, és a
        # #1720-ban épp egy ilyen plafon bukott meg. A követelmény
        # VISZONYLAG szól: a halasztás maradjon a SZABÁLY, ne a kivétel.
        assert halasztott > len(AZONNAL_EPULO), (
            f"csak {halasztott} halasztott párbeszéd van, de "
            f"{len(AZONNAL_EPULO)} felmentés — a halasztás kivétellé "
            "vált, és az indulási idő visszaesne a #1719 előtti szintre"
        )
