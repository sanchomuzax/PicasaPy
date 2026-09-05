"""#883: a gombnak NÉGY állapota van az eredetiben, nálunk kettő volt.

A hiányzó kettő nem díszítés:

* **rámutatás** — az eredetiben a felső 2 képpontsor és a bal 2 oszlop
  sötétedik (belső árnyék bal-felülről). NEM a teljes kitöltés változik.
* **bekapcsolt** — arany keret (`#C39B62`), változatlan kitöltéssel.

És a meglévő kettő egyike rossz irányba tért el: a **lenyomott** az
eredetiben MELEGEBB (`#A4A19D` … `#CBC6C2`, R>G>B), nálunk `Qt.darker`
hideg szürkét adott.

⚠️ A jegy „a négy állapot háttere páronként különbözik" elfogadási pontját
NEM így teljesítjük, mert az **ellentmond a saját mérésének**: a rámutatás
és a bekapcsolt állapot kitöltése az eredetiben MEGEGYEZIK a normáléval.
Négy különböző hátteret állítani azt jelentené, hogy eltérünk attól, amit
kimértünk. Helyette azt állítjuk, ami igaz: a lenyomott kitöltés más és
melegebb, a rámutatásnak külön árnyékrétege van, a bekapcsoltnak külön
keretszíne.

⚠️ A színek NEM éghetnek be. A #336 pontosan ezen bukott meg: fix világos
háttér + témafüggő felirat = üres gombok sötét témán. A mért értékek ezért
a `Theme` VILÁGOS ágán élnek, a sötét ág származtatott — és erre külön őr
van itt lent.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor

from test_qml_button_contrast import _load_button, _theme_singleton  # noqa: F401


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


def _szin(item, nev) -> QColor:
    return QColor(item.property(nev))


class TestALenyomottMelegebb:
    def test_a_lenyomott_kitoltese_MAS(self, app_module, qt_app):
        alap, _f1, _e1 = _load_button(app_module, qt_app)
        lenyomott, _f2, _e2 = _load_button(app_module, qt_app, {"down": True})

        assert _szin(alap, "surfaceTop") != _szin(lenyomott, "surfaceTop")
        assert _szin(alap, "surfaceBottom") != _szin(lenyomott, "surfaceBottom")

    def test_a_lenyomott_MELEGEBB_nem_hidegebb(self, app_module, qt_app):
        """Ez a lényeg: nem az számít, hogy sötétebb, hanem hogy MERRE tér el.

        Az eredeti létrája `#A4A19D` … `#CBC6C2`: a vörös csatorna a
        legnagyobb, a kék a legkisebb. Egy `Qt.darker`-rel sötétített
        semleges szürke ezzel szemben R = G = B marad.
        """
        lenyomott, _f, _e = _load_button(app_module, qt_app, {"down": True})

        for nev in ("surfaceTop", "surfaceBottom"):
            szin = _szin(lenyomott, nev)
            assert szin.red() > szin.green() > szin.blue(), (
                f"{nev} = {szin.name()} — nem melegebb szürke (R>G>B), "
                "tehát az eredetivel ellentétes irányba tér el"
            )


class TestABekapcsoltAranyKeret:
    def test_a_bekapcsolt_keret_arany(self, app_module, qt_app):
        bekapcsolt, _f, _e = _load_button(
            app_module, qt_app, {"checkable": True, "checked": True}
        )
        assert _szin(bekapcsolt, "borderColor") == QColor("#c39b62")

    def test_a_bekapcsolt_kitoltese_VALTOZATLAN(self, app_module, qt_app):
        """Az eredetiben csak a keret jelzi — a kitöltés nem változik."""
        alap, _f1, _e1 = _load_button(app_module, qt_app)
        bekapcsolt, _f2, _e2 = _load_button(
            app_module, qt_app, {"checkable": True, "checked": True}
        )
        assert _szin(alap, "surfaceTop") == _szin(bekapcsolt, "surfaceTop")
        assert _szin(alap, "surfaceBottom") == _szin(bekapcsolt, "surfaceBottom")

    def test_a_ki_nem_kapcsolt_keret_NEM_arany(self, app_module, qt_app):
        alap, _f, _e = _load_button(app_module, qt_app)
        assert _szin(alap, "borderColor") != QColor("#c39b62")


class TestAFeliratAlfaja:
    def test_a_felirat_80_szazalekos(self, app_module, qt_app):
        """Az eredetiben `CC000000` — a tinta 80%-os átlátszatlansággal.

        NEM szürke szín: a színt a téma adja, az alfát az eredeti. Így sötét
        témán is helyes marad.
        """
        alap, _f, _e = _load_button(app_module, qt_app)
        assert _szin(alap, "inkColor").alphaF() == pytest.approx(0.8, abs=0.01)

    def test_a_zold_gomb_felirata_TELI_feher(self, app_module, qt_app):
        zold, _f, _e = _load_button(app_module, qt_app, {"accent": "#3a8a3a"})
        szin = _szin(zold, "inkColor")
        assert szin.alphaF() == pytest.approx(1.0, abs=0.01)
        assert szin == QColor("white")


class TestAZoldGombNemReagal:
    """Az eredetiben mind a három állapotban ugyanaz a kép
    (`b1_decrect_green_n`) — csak a szövege fehér."""

    def test_lenyomva_sem_valtozik(self, app_module, qt_app):
        alap, _f1, _e1 = _load_button(app_module, qt_app, {"accent": "#3a8a3a"})
        lenyomott, _f2, _e2 = _load_button(
            app_module, qt_app, {"accent": "#3a8a3a", "down": True}
        )
        assert _szin(alap, "surfaceTop") == _szin(lenyomott, "surfaceTop")
        assert _szin(alap, "surfaceBottom") == _szin(lenyomott, "surfaceBottom")

    def test_ramutataskor_nincs_arnyek(self, app_module, qt_app):
        zold, _f, _e = _load_button(app_module, qt_app, {"accent": "#3a8a3a"})
        assert zold.property("showingHoverShade") is False


class TestASzinekNemEgnekBe:
    """#336-őr: a mért értékek a VILÁGOS ágon élnek, a sötét származtatott."""

    def test_sotet_temaban_MAS_szinek(self, app_module, qt_app):
        alap, _f, _e = _load_button(app_module, qt_app)
        tema = _theme_singleton(alap)
        vilagos_also = _szin(alap, "surfaceBottom")

        tema.setProperty("dark", True)
        try:
            sotet_also = _szin(alap, "surfaceBottom")
            assert sotet_also != vilagos_also, (
                "a gomb háttere sötét témában is a világos mért értéket "
                "adja — ez a #336 hibája, üres gombokkal"
            )
        finally:
            tema.setProperty("dark", False)

    def test_vilagos_temaban_a_MERT_ertekek(self, app_module, qt_app):
        alap, _f, _e = _load_button(app_module, qt_app)
        assert _szin(alap, "surfaceTop") == QColor("#f9f9f9")
        assert _szin(alap, "surfaceBottom") == QColor("#d0d0d0")
        assert _szin(alap, "borderColor") == QColor("#bbbbbb")
