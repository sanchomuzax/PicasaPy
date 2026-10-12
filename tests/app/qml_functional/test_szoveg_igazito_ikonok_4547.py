"""A szöveg-igazító gombok SAJÁT jelet mutatnak (#4547).

## A lelet

Az eredeti szövegszerkesztő panelen a három igazító gomb
(`edittextpanel/leftalign` · `centeralign` · `rightalign`) mindegyike
saját ikont visel: a balra, középre és jobbra igazított sorok képe
(`*_icon` elemek a `edittextpanel.tre`-ben, `ui-leltar.csv`).

Nálunk mindhárom gomb ugyanazt a `≡` jelet írta ki; a különbséget csak a
buborék-súgó adta. Ez a fájl azt méri, hogy a három gomb három
KÜLÖNBÖZŐ, az igazítást ábrázoló jelet mutat-e — VALÓDI rajzolt képen,
nem a forráskódban.

## Mit mér ez a fájl

- mindhárom gombon ott van az ikon, és az ikon a helyes igazítást kapta;
- a rajzolt képen a tinta súlypontja balra / középen / jobbra áll;
- a három gomb rajzolt képe páronként különbözik;
- VALÓDI egérkattintásra a megfelelő igazítás megy a vezérlőnek;
- mindez −5 / 0 / +5 px ablakmagasságnál.

⚠️ Amit NEM mér: a képpontra pontos egyezést a referencia-képernyőképpel.
A referenciában a szövegpanel igazító gombjainak képe nincs a leltárban
(`kepek-leltar.md`), az eredeti ikon-bitkép pedig a respack-ban él.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, QRectF, Qt
from PySide6.QtTest import QTest
from PySide6.QtQuick import QQuickItem

import picasapy.app
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg

_PANEL = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "EditorTextPanel.qml"
).read_text(encoding="utf-8")

#: gombnév → az igazítás, amelyet a gomb kattintásra küld
GOMBOK = {
    "textAlign_left": "left",
    "textAlign_center": "center",
    "textAlign_right": "right",
}

#: a tinta súlypontja (0..1, a gomb szélességéhez képest) várt sorrendje
_SULYPONT_KUSZOB = 0.03


def _mappa_kepei(lib) -> None:
    make_jpeg(lib / "elso.jpg", size=(640, 400))


def _keres(elem: QQuickItem, object_name: str):
    if elem.objectName() == object_name:
        return elem
    for child in elem.childItems():
        found = _keres(child, object_name)
        if found is not None:
            return found
    return None


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _szovegpanel_nyitva(ablak, qt_app):
    """A néző megnyitása + a szöveg-eszköz bekapcsolása (mint a test_editor-ban)."""
    ablak.setProperty("viewerOpen", True)
    viewer = ablak.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = ablak.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("textActive", True)
    qt_app.processEvents()
    assert _varj(qt_app, lambda: panel.property("textActive") is True)
    return panel


def _gomb(ablak, nev: str) -> QQuickItem:
    gomb = _keres(ablak.contentItem(), nev)
    assert gomb is not None, f"hiányzik a(z) {nev} gomb"
    return gomb


def _kattints(ablak, qt_app, elem: QQuickItem) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(ablak, kozep, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep,
    )
    qt_app.processEvents()


def _tinta_sulypont(ablak, gomb: QQuickItem) -> float:
    """A gomb rajzolt képén a TINTA súlypontja, a gomb szélességének arányában.

    A gomb saját hátterét a közép-felső pixeléből vesszük (az ikon a
    függőleges közepén van, a felső sáv a háttér), és a különbözőt tintának
    tekintjük. A súlypont 0,0 = bal szél, 1,0 = jobb szél.
    """
    kep = ablak.grabWindow()
    teglalap = gomb.mapRectToScene(QRectF(0, 0, gomb.width(), gomb.height()))
    x0 = int(teglalap.left())
    y0 = int(teglalap.top())
    szel = int(teglalap.width())
    mag = int(teglalap.height())
    assert szel > 4 and mag > 4, "a gomb nincs kirajzolva"

    hatter = kep.pixelColor(x0 + szel // 2, y0 + 2)
    osszeg = 0
    sulyozott = 0.0
    for dx in range(3, szel - 3):
        oszlop = 0
        for dy in range(3, mag - 3):
            szin = kep.pixelColor(x0 + dx, y0 + dy)
            elteres = (
                abs(szin.red() - hatter.red())
                + abs(szin.green() - hatter.green())
                + abs(szin.blue() - hatter.blue())
            )
            if elteres > 120:
                oszlop += 1
        osszeg += oszlop
        sulyozott += oszlop * (dx + 0.5)
    assert osszeg > 0, "a gomb rajzolt képén nincs tinta — nincs ikon"
    return sulyozott / osszeg / szel


def _tinta_kep(ablak, gomb: QQuickItem) -> tuple:
    """A gomb rajzolt tintaképe, oszloponként (a páronkénti összevetéshez)."""
    kep = ablak.grabWindow()
    teglalap = gomb.mapRectToScene(QRectF(0, 0, gomb.width(), gomb.height()))
    x0 = int(teglalap.left())
    y0 = int(teglalap.top())
    szel = int(teglalap.width())
    mag = int(teglalap.height())
    hatter = kep.pixelColor(x0 + szel // 2, y0 + 2)
    sorok = []
    for dy in range(3, mag - 3):
        sor = []
        for dx in range(3, szel - 3):
            szin = kep.pixelColor(x0 + dx, y0 + dy)
            elteres = (
                abs(szin.red() - hatter.red())
                + abs(szin.green() - hatter.green())
                + abs(szin.blue() - hatter.blue())
            )
            sor.append(elteres > 120)
        sorok.append(tuple(sor))
    return tuple(sorok)


class TestAzIkonOttVan:
    @pytest.mark.parametrize("gomb_nev", sorted(GOMBOK))
    def test_minden_gombon_van_ikon_a_helyes_igazitassal(
        self, gomb_nev, qml_app, qt_app
    ):
        window, _c, _e = qml_app
        _szovegpanel_nyitva(window, qt_app)
        ikon = window.findChild(QObject, gomb_nev + "Icon")
        assert ikon is not None, f"nincs ikon a(z) {gomb_nev} gombon"
        assert ikon.property("align") == GOMBOK[gomb_nev]

    def test_a_gombok_felirata_NEM_a_kozos_hármas_vonal(self, qml_app, qt_app):
        """A `≡` jel volt a régi, mindhárom gombon azonos felirat."""
        assert 'label: "\\u2261"' not in _PANEL


class TestAzIkonRajzoltKepen:
    @pytest.mark.parametrize("offset", [-5, 0, 5])
    def test_a_tinta_sulypontja_balra_kozep_jobbra(self, offset, qt_app, tmp_path):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, _vezerlo, _motor = next(gen)
        try:
            ablak.setHeight(ablak.height() + offset)
            qt_app.processEvents()
            _szovegpanel_nyitva(ablak, qt_app)
            bal = _tinta_sulypont(ablak, _gomb(ablak, "textAlign_left"))
            kozep = _tinta_sulypont(ablak, _gomb(ablak, "textAlign_center"))
            jobb = _tinta_sulypont(ablak, _gomb(ablak, "textAlign_right"))
            assert bal + _SULYPONT_KUSZOB < kozep, (bal, kozep)
            assert kozep + _SULYPONT_KUSZOB < jobb, (kozep, jobb)
        finally:
            gen.close()

    @pytest.mark.parametrize("offset", [-5, 0, 5])
    def test_a_harom_gomb_rajzolt_kepe_paronkent_kulonbozik(
        self, offset, qt_app, tmp_path
    ):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, _vezerlo, _motor = next(gen)
        try:
            ablak.setHeight(ablak.height() + offset)
            qt_app.processEvents()
            _szovegpanel_nyitva(ablak, qt_app)
            kepek = {
                nev: _tinta_kep(ablak, _gomb(ablak, nev)) for nev in GOMBOK
            }
            nevek = sorted(kepek)
            for i, a in enumerate(nevek):
                for b in nevek[i + 1:]:
                    assert kepek[a] != kepek[b], f"{a} és {b} ugyanazt mutatja"
        finally:
            gen.close()


class TestAKattintasAzIgazitastKuldi:
    @pytest.mark.parametrize("offset", [-5, 0, 5])
    def test_valodi_kattintas_a_helyes_igazitast_kuldi(
        self, offset, qt_app, tmp_path
    ):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, _vezerlo, _motor = next(gen)
        try:
            ablak.setHeight(ablak.height() + offset)
            qt_app.processEvents()
            panel = _szovegpanel_nyitva(ablak, qt_app)
            kapott = []
            panel.textAlignEdited.connect(kapott.append)
            for nev, igazitas in GOMBOK.items():
                _kattints(ablak, qt_app, _gomb(ablak, nev))
                assert kapott[-1:] == [igazitas], nev
        finally:
            gen.close()
