"""#3602 — az alsó sáv (`thumbui/basecontrolset`) horgonyzása KÉPPONTRA.

A #3582 R2/R3-összevetése az osztályt (a horgonyzás MÓDJÁT) mindenhol
egyezőnek találta, a rögzített ELTOLÁSOK viszont néhány képponttal
eltértek a `thumbui.tre`-kényszerektől, a `respack.yt` tervezési
téglalapjaitól és a tulajdonos 1920 px széles Picasa-képernyőképétől
(pixelre mérve, `research/testdata/screenshot/Képernyőkép 2026-07-18
150933.png`). `S` = az osztópont, `trayMainBar.splitX` (0,365 · W).

| elem | eredeti | volt (a #3602 előtt) |
|---|---|---|
| `startoggle` (csillag) bal széle | `S − 3` | `S + 0` |
| `rotateleft` bal széle | `S + 38` | `S + 42` |
| `rotateright` bal széle | `S + 75` | `S + 79` |
| a tálca 3 gombjának jobb széle a `scratchback` jobb szélétől | 7 | 5 |
| nagyító ↔ csúszka rés (a `−`/`+` jel nélkül) | 7 | 20 (a `−` jel miatt) |
| `scale_group` ↔ `metadata_group` rés | 20 | 12 |
| `metadata_group` jobb széle | `W − 15` | `W − 10` |
| `webupload_rect` szélessége | 145 | 147 |

Ez a fájl KIRAJZOLT ablakban, jelenet-koordinátában (a `trayMainBar`
saját koordinátarendszerében, `mapToItem`-mel) méri mindezt, két
ablakszélességen — a `test_also_sav_elrendezes_1420.py` mintáját követve.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF
from PySide6.QtQuick import QQuickItem

from support.qml_blokk import blokk_horgonyra

#: Fél képpont tűrés: a QML geometriája tört szám lehet.
TURES = 0.5

#: Két ablakszélesség — a #3602 „Kész, ha" pontja kettőt kér.
ABLAKOK = (1280, 1920)


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _szelesseg(window, qt_app, szelesseg: int) -> None:
    window.setProperty("width", szelesseg)
    for _ in range(4):
        qt_app.processEvents()


def _x_a_savban(window, nev: str) -> float:
    """Az elem bal széle a `trayMainBar` koordinátarendszerében."""
    sav = _elem(window, "trayMainBar")
    elem = _elem(window, nev)
    return elem.mapToItem(sav, QPointF(0, 0)).x()


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


class TestACsillagEsAForgatas:
    """`startoggle`/`rotateleft`/`rotateright` — a #3582 táblázata szerint."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_csillag_bal_szele_S_minusz_3(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        assert _x_a_savban(window, "trayStarButton") == pytest.approx(
            osztopont - 3, abs=TURES
        )

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_balra_forgatas_bal_szele_S_plusz_38(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        assert _x_a_savban(window, "trayRotateLeft") == pytest.approx(
            osztopont + 38, abs=TURES
        )

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_jobbra_forgatas_bal_szele_S_plusz_75(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        assert _x_a_savban(window, "trayRotateRight") == pytest.approx(
            osztopont + 75, abs=TURES
        )


class TestATalcaHaromGombja:
    """A jobb szélük 7 képpontra a `scratchback` jobb szélétől (nem 5)."""

    @pytest.mark.parametrize(
        "nev", ["trayHoldButton", "trayClearButton", "trayAddToButton"]
    )
    def test_a_gomb_jobb_szele_7_kepontra(self, qml_app_module, qt_app, nev):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        talca = _elem(window, "trayScratchBack")
        talca_jobb_szel = _x_a_savban(window, "trayScratchBack") + talca.property(
            "width"
        )
        gomb = _elem(window, nev)
        gomb_jobb_szel = _x_a_savban(window, nev) + gomb.property("width")
        assert talca_jobb_szel - gomb_jobb_szel == pytest.approx(7, abs=TURES)


class TestANagyitoCsoport:
    """A nagyító ↔ csúszka rés 7 px, a `−`/`+` jel eltűnik."""

    def test_a_nagyito_es_a_csuszka_kozott_7_kepont(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        nagyito = _elem(window, "trayLoupeButton")
        nagyito_jobb = _x_a_savban(window, "trayLoupeButton") + nagyito.property(
            "width"
        )
        csuszka_bal = _x_a_savban(window, "traySizeSlider")
        assert csuszka_bal - nagyito_jobb == pytest.approx(7, abs=TURES)

    def test_nincs_minusz_es_plusz_jel_a_csuszka_mellett(
        self, qml_app_module, qt_app
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        sor = _elem(window, "trayLibraryZoomRow")
        szovegek = [
            gy.property("text")
            for gy in _walk(sor)
            if gy.metaObject().className().startswith("QQuickText")
        ]
        assert "−" not in szovegek and "+" not in szovegek, (
            f"a nagyítás-csúszka mellett még ott a fölösleges jel: {szovegek}"
        )


class TestAScaleGroupEsAMetadataGroup:
    """A rés köztük 20, a `metadata_group` jobb széle `W − 15`."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_ket_csoport_kozott_20_kepont(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        zoom = _elem(window, "trayZoomGroup")
        zoom_jobb = _x_a_savban(window, "trayZoomGroup") + zoom.property("width")
        metadata_bal = _x_a_savban(window, "trayMetadataGroup")
        assert metadata_bal - zoom_jobb == pytest.approx(20, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_metadata_group_jobb_szele_W_minusz_15(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        sav = _elem(window, "trayMainBar")
        metadata = _elem(window, "trayMetadataGroup")
        jobb_szel = _x_a_savban(window, "trayMetadataGroup") + metadata.property(
            "width"
        )
        assert jobb_szel == pytest.approx(
            sav.property("width") - 15, abs=TURES
        )


class TestAZoldGombFoglalata:
    """A `webupload_rect` 145 px széles (nem 147)."""

    def test_a_hely_145_kepont_szeles(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        hely = _elem(window, "trayUploadSlot")
        assert hely.property("width") == 145


class TestASzelessegIgenyMegMindigFedi:
    """A #1420 szélesség-igénye a mostani konstansokkal is fedi a sávot —
    ha nem, a minimumra állított ablakban valami kilógna."""

    def test_a_minimumon_semmi_nem_log_ki(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        minimum = int(window.property("minimumWidth"))
        _szelesseg(window, qt_app, minimum)
        sav = _elem(window, "trayMainBar")
        for nev in ("trayStarButton", "trayZoomGroup", "trayMetadataGroup"):
            elem = _elem(window, nev)
            bal = _x_a_savban(window, nev)
            jobb = bal + elem.property("width")
            assert bal >= -TURES, f"{nev} balra lóg ki: {bal}"
            assert jobb <= sav.property("width") + TURES, (
                f"{nev} jobbra lóg ki: {jobb} > {sav.property('width')}"
            )


class TestAForrasSzintuOr:
    """A `−`/`+` `Text` a forrásból is eltűnik, nem csak a kirajzolt fából."""

    def test_a_konyvtari_nagyitas_sor_nem_tartalmaz_szoveges_jelet(self):
        import picasapy.app as app_csomag
        from pathlib import Path

        forras = (
            Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
        ).read_text(encoding="utf-8")
        blokk = blokk_horgonyra(forras, 'id: trayLibraryZoomRow')
        assert 'text: "−"' not in blokk
        assert 'text: "+"' not in blokk
