"""Az eredeti `constants.ui` ÉLŐ színei szerepelnek a `Theme.qml`-ben (#1488).

## Mit mér ez a fájl

A Picasa a bal hasáb (album-lista), az album-elrendezés és a bélyegkép-
kijelölés színeit egy szállított szövegfájlban tartja
(`Picasa3/runtime/constants.ui`). A #384 köre a nagyját átvette; a #1488
mérése szerint hat élő szín kimaradt. Az őr azt állítja, hogy **egyetlen
élő szín se essen ki újra észrevétlenül**.

## A táblázat MÁSOLAT — és miért

A `constants.ui` a kutatási anyagban van (`research/copy_Picasa_3_7/…`),
ami **nincs verziókövetve** (`.gitignore`), tehát a CI-n nem létezik. A
tábla ezért itt áll, szó szerint a fájlból olvasva. A másolat sodródását
külön próba fogja meg azon a gépen, ahol a fájl megvan — de a FŐ állítás
nem ezen múlik: az minden gépen fut.

## A hatókör KIMONDVA

Három színcsalád tartozik ide: `alist_*` (a lista-hasáb), `alayout_*` (az
album-elrendezés) és `thumbsel_*` (a bélyegkép-kijelölés). Ami kimarad, és
miért:

| kimaradó | ok |
|---|---|
| `alist_hicolor_mac`, `alist_hicolor2_mac`, `alist_selcolor_mac` | Mac-specifikus, a projekt Linux-first |
| `alabel_buttfont_*` | szállított betűtípus (`Praxis`), amit nem viszünk tovább |
| `alabel_burncdOffset` | CD-írás — nyugdíjazott funkció (#638) |
| `publishtoweb_color` (#0000FF) | MÁS család (webre publikálás), nálunk ma nincs meg — a #2825 jegy tárgya |

⚠️ Ez az őr a szín JELENLÉTÉT méri a `Theme.qml`-ben, nem azt, hogy a
felület melyik eleme viseli. A bekötést elemenként külön próbák mérik (a
húzás-célpontot lentebb ez a fájl is ellenőrzi, forrásszinten).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]
THEME = GYOKER / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "Theme.qml"
ALBUMS_SECTION = (
    GYOKER / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "AlbumsSection.qml"
)
#: A kutatási anyag szállított fájlja — csak a fejlesztői gépen létezik.
CONSTANTS_UI = (
    GYOKER / "research" / "copy_Picasa_3_7" / "Picasa3" / "runtime" / "constants.ui"
)

#: A három élő családba tartozó színek, a `constants.ui`-ból OLVASVA.
#:
#: Az `alist_*` értékek `0xAARRGGBB` alakúak a fájlban (az alfa mindegyiknél
#: `FF`), az `alayout_*`/`thumbsel_*` értékek `#RRGGBB` alakúak — a tábla a
#: RGB-hármast tartja, mert a `Theme.qml` is így írja.
ELO_SZINEK: dict[str, str] = {
    "alist_bgcolor": "f3f3f3",
    "alist_hicolor_win": "83a7bd",
    "alist_hicolor2_win": "e5e2da",
    "alist_selcolor_win": "25648b",
    "alist_dragcolor": "82a6bd",
    "alist_catcolor": "edeae4",
    "alist_scatcolor": "25648b",
    "alist_dotcolor": "bebebe",
    "alist_stickycolor": "eae7dc",
    "alayout_titleColor": "634b45",
    "thumbsel_color1": "009eff",
    "thumbsel_color2": "ffffff",
}

#: ALSÓ KORLÁT (#1468/#1476 tanulsága): ha valaki kiüríti vagy megkurtítja a
#: táblát, az őr néma maradna, és „hibátlant" jelentene anélkül, hogy
#: bármit megnézett volna.
MIN_SZINEK = 12


def _theme_szoveg() -> str:
    return THEME.read_text(encoding="utf-8").lower()


def test_a_tabla_nem_urulhet_ki():
    assert len(ELO_SZINEK) >= MIN_SZINEK, (
        f"csak {len(ELO_SZINEK)} színt vizsgál az őr — a `constants.ui` élő "
        f"családjaiban {MIN_SZINEK} van; a rövidítés néma őrt csinál belőle"
    )


@pytest.mark.parametrize("nev,ertek", sorted(ELO_SZINEK.items()))
def test_az_elo_szin_szerepel_a_temaban(nev: str, ertek: str):
    """Minden élő `constants.ui` szín megtalálható a `Theme.qml`-ben."""
    assert f"#{ertek}" in _theme_szoveg(), (
        f"a `constants.ui` {nev} = #{ertek.upper()} színe nincs meg a "
        "`Theme.qml`-ben — a felület egy MÉRT eredeti értéket nem visel"
    )


def test_a_huzas_szine_LATHATOAN_mas_mint_a_kijelolese():
    """`alist_dragcolor` (#82A6BD) ≠ `alist_hicolor_win` (#83A7BD).

    Az eredeti szándékosan majdnem azonos színt ad a húzás-célpontnak, de
    NEM ugyanazt. Ha a két érték nálunk egybeesne, a különbség — ami az
    eredeti finom visszajelzése — elveszne."""
    assert ELO_SZINEK["alist_dragcolor"] != ELO_SZINEK["alist_hicolor_win"]
    szoveg = _theme_szoveg()
    assert "#82a6bd" in szoveg and "#83a7bd" in szoveg, (
        "mindkét színnek benne kell lennie a témában, külön néven"
    )


def test_a_huzas_celpontja_a_huzas_szinet_hasznalja():
    """Az albumlista húzás-célpontja a `Theme` húzás-színére hivatkozik.

    ⚠️ Ez FORRÁSSZINTŰ állítás: azt méri, hogy a kötés ott van, nem azt,
    hogy egy valódi húzás közben a képernyőn ez a szín látszik (ahhoz
    tényleges fogd-és-vidd eseménysor kellene). A `containsDrag` jelenléte
    a kötés mellett viszont kizárja a holt property-t."""
    szoveg = ALBUMS_SECTION.read_text(encoding="utf-8")
    assert "listDragTarget" in szoveg, (
        "az albumlista húzás-célpontja nem a `Theme.listDragTarget`-et "
        "használja — a mért #82A6BD nem jut el a felületre"
    )
    assert "containsDrag" in szoveg


@pytest.mark.skipif(
    not CONSTANTS_UI.exists(),
    reason="a szállított constants.ui csak a fejlesztői gépen van meg",
)
def test_a_masolt_tabla_egyezik_a_szallitott_fajllal():
    """A tábla sodródását fogja meg — ott, ahol a forrásfájl megvan.

    ⚠️ Ez a próba KÖRNYEZETFÜGGŐ, tehát önmagában NEM őr (a CI-n mindig
    kimarad). A fő állítást a fenti, mindenhol futó próbák teszik; ez csak
    annyit ad, hogy a fejlesztői gépen a másolat nem csúszhat el."""
    szoveg = CONSTANTS_UI.read_text(encoding="utf-8", errors="replace")
    parok = dict(
        re.findall(r"^([A-Za-z_0-9]+)=(0x[0-9A-Fa-f]{8}|#[0-9A-Fa-f]{6})\s*$",
                   szoveg, re.MULTILINE)
    )
    for nev, ertek in ELO_SZINEK.items():
        assert nev in parok, f"{nev} nincs a szállított fájlban"
        fajlbeli = parok[nev].lower().replace("0xff", "").lstrip("#")
        assert fajlbeli == ertek, (
            f"{nev}: a tábla #{ertek}, a fájl #{fajlbeli} — a másolat elcsúszott"
        )
