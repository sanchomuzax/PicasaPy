"""#2170 — a négy projektlap-billentyű (`Ctrl+W` · `Ctrl+Tab` · `Ctrl+←/→`).

## A mérés

Az eredeti projektlap-sáv kezelője (`0x005b2390`) `Ctrl`-t követel, és négy
billentyűt ismer:

| billentyű | cím | művelet |
|---|---|---|
| `Ctrl+Left` | `0x005b23a6` | `0x005b22b0(panel, −1)` — előző lap |
| `Ctrl+Right` | `0x005b23b6` | `0x005b22b0(panel, +1)` — következő lap |
| `Ctrl+Tab` | `0x005b23c8` | következő lap; **`Shift`-tel** előző |
| `Ctrl+W` | `0x005b23dd` | `0x005b31a0(panel, …)` — a lap bezárása |

Nálunk egyik sem volt bekötve (`grep -roh` a `qml/` alatt: 0 találat
mindegyikre); a sávban egyetlen `Shortcut` állt, az `Esc`.

⚠️ **A csúszka-léptetés (`+`/`=`/`−`/`_`, ±0,02) NEM ebben a fájlban van** —
az a szerkesztő csúszkájáé, külön elem, külön próbákkal.

## Amit a lapváltás jelent

A sávban a **könyvtár** füle mindig ott van, utána a projektlapok. A
léptetés ezen a TELJES soron megy körbe (könyvtár is beleértve), mert a
felhasználó számára az is egy fül.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app as app_csomag

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
    / "DocumentTabStrip.qml"
).read_text(encoding="utf-8")


def _billentyu_blokk(sorozat: str) -> str:
    """A `Shortcut` blokkja, kapcsos zárójel szerint vágva.

    ⚠️ Nem rögzített karakterablak: a blokk hossza a kommentektől függ, és
    egy jogos bővítés némán kivágná a keresett sort.
    """
    jel = f'sequence: "{sorozat}"'
    assert jel in _QML, f"nincs `Shortcut` erre: {sorozat}"
    kezd = _QML.rindex("Shortcut {", 0, _QML.index(jel))
    melyseg = 0
    for i in range(_QML.index("{", kezd), len(_QML)):
        if _QML[i] == "{":
            melyseg += 1
        elif _QML[i] == "}":
            melyseg -= 1
            if melyseg == 0:
                return _QML[kezd : i + 1]
    raise AssertionError(f"nem záródik a blokk: {sorozat}")


class TestANegyBillentyuLETEZIK:
    def test_ctrl_w(self):
        assert 'sequence: "Ctrl+W"' in _QML

    def test_ctrl_tab_es_shift_tab(self):
        assert 'sequence: "Ctrl+Tab"' in _QML
        assert 'sequence: "Ctrl+Shift+Tab"' in _QML

    def test_ctrl_balra_es_jobbra(self):
        assert 'sequence: "Ctrl+Left"' in _QML
        assert 'sequence: "Ctrl+Right"' in _QML


class TestAMuveletek:
    def test_a_ctrl_w_a_MEGLEVO_bezaras_uton_megy(self):
        """A jegy kiköti: „a meglévő bezárás-úton, nem külön ágon" — az
        `requestCloseActive` a piszkos lapnál kérdez, és az `Esc` is ezen
        megy. Egy külön ág megkerülné a kérdést."""
        assert "requestCloseActive()" in _billentyu_blokk("Ctrl+W")

    def test_a_ctrl_tab_a_KOVETKEZORE_valt(self):
        assert "lepjAKovetkezoLapra(1)" in _billentyu_blokk("Ctrl+Tab")

    def test_a_ctrl_shift_tab_az_ELOZORE(self):
        assert "lepjAKovetkezoLapra(-1)" in _billentyu_blokk("Ctrl+Shift+Tab")

    def test_a_nyilak_ugyanazt_a_leptetot_hivjak(self):
        assert "lepjAKovetkezoLapra(-1)" in _billentyu_blokk("Ctrl+Left")
        assert "lepjAKovetkezoLapra(1)" in _billentyu_blokk("Ctrl+Right")


class TestALepteto:
    """A léptető függvény viselkedése — a `Shortcut`-ok csak ezt hívják."""

    def test_letezik_a_lepteto(self):
        assert "function lepjAKovetkezoLapra(" in _QML

    def test_KORBE_lep(self):
        """A négy billentyű körbejár: az utolsó után a könyvtár jön."""
        kezd = _QML.index("function lepjAKovetkezoLapra(")
        blokk = _QML[kezd : kezd + 900]
        assert "%" in blokk, (
            "a léptető nem körbe lép — a maradékos osztás hiányzik"
        )


class TestAmiNEMromolhatEl:
    def test_az_Esc_megmaradt(self):
        assert 'sequence: "Esc"' in _QML

    def test_a_billentyuk_CSAK_projektlappal_elnek(self):
        """Könyvtár-nézetben nincs mit léptetni és nincs mit bezárni."""
        for sorozat in ("Ctrl+W", "Ctrl+Tab", "Ctrl+Left", "Ctrl+Right"):
            assert "hasProjectTabs" in _billentyu_blokk(sorozat), (
                f"a(z) {sorozat} projektlap nélkül is aktív"
            )


# ----------------------------------------------------------------------
# FUNKCIONÁLIS próbák — a forrás-őr önmagában nem elég: azt is mérni kell,
# hogy a billentyű tényleg a másik lapra visz. A keretet a #944 tesztfájl
# adja (valódi, aktivált ablak: a `Shortcut`-ot csak az kapja meg).
# ----------------------------------------------------------------------

import pytest  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from app.qml_functional.test_document_tab_strip_944 import (  # noqa: E402
    _child,
    _harness_qml,
    _view,
    _wait_for,
)

#: Két nyitott projektlap — a léptetés így három fülön megy körbe
#: (könyvtár · kollázs · film).
_KET_LAP = (
    '[{ "id": "collage", "title": "Collage", "modified": false },'
    ' { "id": "movie", "title": "Movie", "modified": false }]'
)


@pytest.fixture()
def sav(qt_app):
    view, root = _view(qt_app, _harness_qml(_KET_LAP), 900, 260)
    strip = _child(root, "documentTabStrip")
    yield view, strip, qt_app


def _aktiv(strip) -> str:
    return strip.property("activeTabId")


class TestALeptetesELOBEN:
    def test_a_kovetkezo_lapra_lep(self, sav):
        _view_, strip, qt_app = sav
        assert _aktiv(strip) == "library"
        strip.lepjAKovetkezoLapra(1)
        qt_app.processEvents()
        assert _aktiv(strip) == "collage"
        strip.lepjAKovetkezoLapra(1)
        qt_app.processEvents()
        assert _aktiv(strip) == "movie"

    def test_az_utolso_utan_KORBE_er(self, sav):
        _view_, strip, qt_app = sav
        for _ in range(2):
            strip.lepjAKovetkezoLapra(1)
        qt_app.processEvents()
        assert _aktiv(strip) == "movie"
        strip.lepjAKovetkezoLapra(1)
        qt_app.processEvents()
        assert _aktiv(strip) == "library", (
            "az utolsó lap után nem a könyvtár jött — nincs körbejárás"
        )

    def test_visszafele_is_KORBE_er(self, sav):
        _view_, strip, qt_app = sav
        strip.lepjAKovetkezoLapra(-1)
        qt_app.processEvents()
        assert _aktiv(strip) == "movie", (
            "a könyvtárból visszafelé nem az utolsó lapra ugrott"
        )


class TestABillentyuLANCA:
    """Nem elég, hogy a függvény jó — a billentyűnek is el kell érnie."""

    def test_a_ctrl_right_TENYLEG_lapot_valt(self, sav):
        view, strip, qt_app = sav
        assert _wait_for(qt_app, view.isActive), "az ablak nem aktiválódott"
        QTest.keyClick(
            view, Qt.Key.Key_Right, Qt.KeyboardModifier.ControlModifier
        )
        assert _wait_for(qt_app, lambda: _aktiv(strip) == "collage"), (
            f"a Ctrl+→ nem váltott lapot (aktív: {_aktiv(strip)})"
        )

    def test_a_ctrl_left_visszafele_valt(self, sav):
        view, strip, qt_app = sav
        assert _wait_for(qt_app, view.isActive)
        QTest.keyClick(
            view, Qt.Key.Key_Left, Qt.KeyboardModifier.ControlModifier
        )
        assert _wait_for(qt_app, lambda: _aktiv(strip) == "movie"), (
            f"a Ctrl+← nem lépett az utolsó lapra (aktív: {_aktiv(strip)})"
        )


# ----------------------------------------------------------------------
# A jegy MÁSIK fele: a csúszka léptetése `+`/`=`/`−`/`_` karakterekkel.
# ----------------------------------------------------------------------

_SLIDER_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PicasaSlider.qml"
).read_text(encoding="utf-8")


class TestACsuszkaLeptetes:
    """A mérés (`0x005d2290`, `WM_CHAR`): `+` (0x2b) és `=` (0x3d) → **+0,02**,
    `−` (0x2d) és `_` (0x5f) → **−0,02** (a konstansok `0x00cf50d8` /
    `0x00cf50d4`). A cél a FÓKUSZBAN lévő csúszka.

    ⚠️ A jegy külön kéri: a ±0,02 az eredeti NORMALIZÁLT (0…1) csúszkájára
    értendő, a mi csúszkáink tartománya viszont változó (−1…1, 0…255). Ezért
    a **tartomány 2 %-át** léptetjük, nem az abszolút 0,02-ot — ez tartja meg
    a mért ARÁNYT. A választás a kódban is meg van indokolva.
    """

    def test_mind_a_NEGY_karakter_kezelve_van(self):
        for jel in ("+", "=", "-", "_"):
            assert f'"{jel}"' in _SLIDER_QML, (
                f"a(z) {jel!r} karakter nincs kezelve — az eredeti mind a "
                f"négyet vizsgálja"
            )

    def test_a_lepes_a_TARTOMANY_szazaleka(self):
        assert "0.02" in _SLIDER_QML, "nincs meg a mért 2 %-os lépés"
        assert "(control.to - control.from)" in _SLIDER_QML, (
            "a lépés nem a tartományból számol — az eredeti 0,02-a a "
            "normalizált skálán 2 %"
        )

    def test_a_valasztas_INDOKOLVA_van(self):
        kezd = _SLIDER_QML.index("0.02")
        kornyek = _SLIDER_QML[max(0, kezd - 1400):kezd]
        assert "normaliz" in kornyek.lower(), (
            "nincs leírva, miért a tartomány 2 %-a és nem az abszolút 0,02"
        )

    def test_a_csuszka_FOKUSZALHATO(self):
        """A léptetés a fókuszban lévő csúszkára hat — enélkül a billentyű
        sosem ér célba."""
        assert "focus" in _SLIDER_QML.lower()


class TestACsuszkaLeptetesELOBEN:
    """A forrás-őr nem elég: a léptetésnek valódi csúszkán is hatnia kell."""

    @pytest.fixture()
    def csuszka(self, qt_app):
        qml = """
        import QtQuick
        import PicasaPy
        Item {
            width: 300; height: 60
            PicasaSlider {
                objectName: "probaCsuszka"
                anchors.centerIn: parent
                width: 200
                from: -1.0; to: 1.0; value: 0.0
            }
        }
        """
        view, root = _view(qt_app, qml, 300, 60)
        yield _child(root, "probaCsuszka"), view, qt_app

    def test_a_plusz_NOVEL_a_tartomany_2_szazalekaval(self, csuszka):
        elem, _view_, qt_app = csuszka
        # a tartomány −1…1, tehát 2 % = 0,04
        elem.leptesd(1)
        qt_app.processEvents()
        assert abs(elem.property("value") - 0.04) < 1e-6, (
            f"a lépés {elem.property('value')}, a várt 0,04 "
            f"(a −1…1 tartomány 2 %-a)"
        )

    def test_a_minusz_CSOKKENT(self, csuszka):
        elem, _view_, qt_app = csuszka
        elem.leptesd(-1)
        qt_app.processEvents()
        assert abs(elem.property("value") + 0.04) < 1e-6

    def test_a_TARTOMANYON_kivulre_nem_lep(self, csuszka):
        elem, _view_, qt_app = csuszka
        elem.setProperty("value", 0.99)
        for _ in range(5):
            elem.leptesd(1)
        qt_app.processEvents()
        assert elem.property("value") <= 1.0 + 1e-9, (
            "a léptetés kivitte a csúszkát a tartományából"
        )

    def test_a_BILLENTYU_is_leptet(self, csuszka):
        """A teljes lánc: fókusz → billentyű → érték."""
        elem, view, qt_app = csuszka
        assert _wait_for(qt_app, view.isActive)
        elem.setProperty("focus", True)
        qt_app.processEvents()
        QTest.keyClick(view, Qt.Key.Key_Plus)
        assert _wait_for(
            qt_app, lambda: abs(elem.property("value") - 0.04) < 1e-6
        ), f"a `+` billentyű nem léptetett (érték: {elem.property('value')})"
