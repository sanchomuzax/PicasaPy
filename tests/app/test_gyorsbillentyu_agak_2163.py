"""#2163 — a könyvtárnézet gyorsbillentyűi a MÉRT ágakhoz mérve.

Az eredeti könyvtárnézeti kezelője (`0x005e60d0`) ugrótáblás `switch`, és a
teljes kiosztás ki van olvasva: `docs/specs/picasa-gyorsbillentyuk.md`
**10.3** (34 ág) és **10.5** (amire NINCS ág).

Az őr két irányban fog:

1. **hiány** — a bekötöttnek szánt billentyűk tényleg ott vannak, a mért
   ághoz tartozó belépővel;
2. **többlet** — amire az eredetiben NINCS ág, arra nálunk se legyen
   `Shortcut` a könyvtárnézetben; ami mégis kell, az KIVÉTEL, névvel és
   indoklással (a `KIVETEL` tábla).

⚠️ Hatókör: a könyvtárnézet gazdafájljai (`Main.qml`, `PicasaMenuBar.qml`).
A `DocumentTabStrip.qml` a PROJEKTLAP-sáv, aminek a spec **10.15** szerint
saját billentyűi vannak (`Ctrl+W`-vel együtt) — az nem ez a kezelő, ezért
nem is ez az őr méri.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml"
_MAIN = (_QML / "Main.qml").read_text(encoding="utf-8")
_MENU = (_QML / "PicasaPy" / "PicasaMenuBar.qml").read_text(encoding="utf-8")

#: A 10.3 tábla mind a 34 ága — a `Ctrl` mindegyiknél kötelező
#: (`0x005e6178`). A `Ctrl+Enter` a táblában `Ctrl+Enter`, nálunk
#: `Ctrl+Return` a Qt neve szerint; a `VK 0x12` (Alt) nem billentyű-ág.
MERT_AGAK = frozenset(
    {
        "Ctrl+Return",
        "Ctrl+0", "Ctrl+1", "Ctrl+2", "Ctrl+3", "Ctrl+4", "Ctrl+5",
        "Ctrl+6", "Ctrl+8", "Ctrl+9",
        "Ctrl+A", "Ctrl+C", "Ctrl+D", "Ctrl+F", "Ctrl+G", "Ctrl+I",
        "Ctrl+K", "Ctrl+M", "Ctrl+N", "Ctrl+O", "Ctrl+P", "Ctrl+R",
        "Ctrl+S", "Ctrl+T", "Ctrl+X",
        "Ctrl+Shift+B", "Ctrl+Shift+E", "Ctrl+Shift+H", "Ctrl+Shift+L",
        "Ctrl+Shift+U", "Ctrl+Shift+V", "Ctrl+Shift+Y",
        "Ctrl+F6", "Ctrl+F7", "Ctrl+F8", "Ctrl+F9",
    }
)

#: 10.5 — az indextábla ezekre a KIHAGYÓ ágra (`0x005e65f7`) mutat.
NINCS_AG = frozenset(
    {"Ctrl+7", "Ctrl+J", "Ctrl+Q", "Ctrl+Z"}
    | {f"Ctrl+F{n}" for n in range(1, 6)}
)

#: Amit a mért táblán KÍVÜL kötünk be — mindegyikhez indoklás. Az őr csak
#: azt engedi át, ami itt szerepel; ez a lista a jegy „soronként indokolva"
#: követelménye gépi alakban.
KIVETEL = {
    "Ctrl+Shift+R": (
        "Forgatás balra — a MENÜ kiírt billentyűje (keymap 28.), a "
        "könyvtárnézeti kezelő a Shift-ágat a `Ctrl+R`-en belül dönti el"
    ),
    "Ctrl+Shift+P": (
        "Indexképek nyomtatása — a menü kiírt billentyűje (keymap 25.), "
        "a kezelő a Shift-ágat a `Ctrl+P`-n belül dönti el"
    ),
    "Ctrl+Shift+S": (
        "SAJÁT: Mentés másként — az eredeti táblájában nincs, a "
        "mentés-szemantikánk (#444) viszont külön parancsot ad rá"
    ),
    "Ctrl+Delete": (
        "Törlés lemezről — a Delete eltérése ismert (a lap 6. szakasza), "
        "és a puszta `Delete`-tel szemben ez KÉRDEZ; hatókör: #2164"
    ),
    "Ctrl+V": (
        "Beillesztés — keymap 15., a menü kiírt billentyűje; a "
        "könyvtárnézeti kezelőben a `Ctrl+C`/`Ctrl+X` ága áll (`0x005e63f5`)"
    ),
}

_SEQ = re.compile(r'sequence:\s*"([^"]+)"')


def _billentyuk() -> set[str]:
    return {
        m.group(1)
        for szoveg in (_MAIN, _MENU)
        for m in _SEQ.finditer(szoveg)
        if m.group(1).startswith("Ctrl")
    }


class TestATobblet:
    def test_minden_bekotott_billentyunek_van_MERT_aga(self):
        idegen = sorted(_billentyuk() - MERT_AGAK - set(KIVETEL))
        assert idegen == [], (
            "olyan billentyű van bekötve a könyvtárnézetben, amire az "
            f"eredetiben nincs ág: {idegen} — vagy vedd ki, vagy írd be a "
            "KIVETEL táblába indoklással (#2163)"
        )

    def test_amire_NINCS_ag_arra_nincs_kotesunk(self):
        utkozes = sorted(_billentyuk() & NINCS_AG)
        assert utkozes == [], (
            f"a kihagyó ágra tartozó billentyűk be vannak kötve: {utkozes}"
        )

    def test_a_kivetel_tabla_nem_lehet_ures_indoklasu(self):
        """Az »empty guard« ellen: indoklás nélküli kivétel nem kivétel."""
        for billentyu, indok in KIVETEL.items():
            assert len(indok) > 40, billentyu

    def test_a_kivetel_tabla_HASZNALT(self):
        """Ha egy kivétel kikerül a kódból, a táblából is ki kell venni —
        különben a lista némán elavul."""
        arvak = sorted(set(KIVETEL) - _billentyuk())
        assert arvak == [], f"a KIVETEL táblában nem használt tétel: {arvak}"


class TestAHianyzoAgakBekotese:
    @pytest.mark.parametrize(
        "billentyu,horgony",
        [
            # a MÉRT ág → a mi belépőnk
            ("Ctrl+3", "window.nezdEsSzerkeszd()"),
            ("Ctrl+F6", "window.masodpeldanyokMutatasa()"),
            ("Ctrl+F7", "window.keressHasonlot()"),
            ("Ctrl+F8", "window.torolAHasonlosagMintat()"),
            ("Ctrl+Shift+B", 'window.kotegEffekt("bw")'),
            ("Ctrl+Shift+E", 'window.kotegEffekt("enhance")'),
            # #2902: a tükrözés két ága — a keymap 35./36. tétele
            ("Ctrl+Shift+H", "controller.flipHorizontalMany"),
            ("Ctrl+Shift+V", "controller.flipVerticalMany"),
        ],
    )
    def test_a_billentyu_a_MERT_belepot_hivja(self, billentyu, horgony):
        assert f'sequence: "{billentyu}"' in _MAIN, (
            f"{billentyu} nincs bekötve (#2163)"
        )
        kezd = _MAIN.index(f'sequence: "{billentyu}"')
        blokk = _MAIN[kezd : kezd + 700]
        assert horgony in blokk, (
            f"{billentyu} nem a várt belépőt hívja ({horgony})"
        )

    def test_a_ket_hasonlosag_billentyu_a_MEGLEVO_magot_hivja(self):
        """A `loadsim`/`clearsim` magja a #1833-ban kész — nem másoljuk."""
        assert "controller.showSimilarTo(" in _MAIN
        assert "controller.clearSimilarity()" in _MAIN


class TestAKotegEffekt:
    def test_a_bw_koteg_effekt_ismert_nev(self):
        """A `Ctrl+Shift+B` az eredetiben a `bw` szűrőt adja a kijelölésre
        (`0x005fe370(panel, "bw")`) — a köteg-motor ismerje a nevet."""
        from picasapy.app.batch_effect_controller import _KNOWN_EFFECTS

        assert "bw" in _KNOWN_EFFECTS

    def test_a_bw_a_render_lancban_is_ismert(self):
        from picasapy.render.chain import _HANDLERS  # noqa: PLC2701

        assert "bw" in _HANDLERS
