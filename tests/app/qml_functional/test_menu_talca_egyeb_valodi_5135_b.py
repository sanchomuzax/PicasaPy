"""Az „Egyéb" táblázat tételei VALÓDI egérkattintással (#5135, 3. rész, B).

Első kör: a NYOMTATÁS párbeszéd vezérlői (a szegély-/felirat-panel a `_c`
fájlban van). Minden tétel a valódi kattintásra indul; a hatást a párbeszéd
állapotán mérjük (`copies`, `fitMode`, `printSize`, `orientation`), nem a
kezelő meghívásán.

Lefedve:
- `printFitRadio`, `printFillRadio` - az illesztés (egész kép / kitöltés);
- `printCopiesPlusButton`, `printCopiesMinusButton` - a példányszám;
- `printPresetFullPage`, `printPresetSize0` - a nyomatméret-előbeállítások;
- `printOrientationBox` - a tájolás-legördülő: valódi kattintás a
  legördülőn, majd a tételen;
- `printPdfBrowseButton` - a tallózás a célfájl-választót nyitja (a
  natív ablak helyett a QML-párbeszéd `visible` állapotát mérjük).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_MAPPA = "fotok"
_KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def _keszits_konyvtarat(lib: Path) -> None:
    cel = lib / _MAPPA
    cel.mkdir()
    for nev in _KEPEK:
        make_jpeg(cel / nev, size=(320, 240))


@pytest.fixture
def egyeb_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elokeszit(window, qt_app, controller) -> None:
    """Megjeleníti az ablakot, betölti a mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = str(Path(str(controller.watchedFolders[0])) / _MAPPA)
    controller.selectFolder(cel)
    assert _varj(
        qt_app, lambda: len(controller.photos.photos) == len(_KEPEK)
    ), "a teszt mappája nem töltődött be"
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _gyerek(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _latszik(window, nev: str) -> bool:
    elem = _objektum(window, nev)
    return elem is not None and elem.property("visible") is True


def _zar(qt_app, objektum) -> None:
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _vizualis_bejaras(item):
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _klikk_ablakban(qt_app, ablak, elem) -> None:
    """Valódi bal kattintás az `elem` közepén, a MEGTARTOTT `ablak`-ra küldve.

    Az `elem.window()` új wrapper-t ad vissza, és a Python ezt a felugró
    alkalmazásnál felszabadíthatja, ami a nyomtatás ablakot is megsemmisíti.
    Ezért a már kezünkben lévő ablak-hivatkozást küldjük a kattintásnak.
    """
    assert elem is not None, "a kattintandó elem hiányzik"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName() or 'az elem'}: nincs kattintható mérete"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _legordulo_tetele(ablak, szoveg: str):
    """A megnyitott legördülő `szoveg` tétele, a VIZUÁLIS fában, láthatóan.

    A legördülő felugró eleme ugyanannak az ablaknak az overlay-jében él,
    mint a legördülő maga, ezért az ablak fáját járjuk be (a nyilvános
    ablaklistát nem, mert a szerkesztett ablak-wrapper így elveszhet).

    A tétel szövege egy `Text` a legördülő delegáltjában; a zárt ComboBox
    saját, azonos szövege nem delegáltban van, ezért azt kiszűrjük. A
    visszaadott elem a DELEGÁLT (a kattintható sor), nem a szöveg.
    """
    for item in _vizualis_bejaras(ablak.contentItem()):
        if item.property("text") != szoveg or not item.isVisible():
            continue
        delegalt = _delegalt_szulo(item)
        if delegalt is not None and delegalt.width() > 0:
            return delegalt
    return None


def _delegalt_szulo(item):
    szulo = item.parentItem()
    while szulo is not None:
        if "Delegate" in szulo.metaObject().className():
            return szulo
        szulo = szulo.parentItem()
    return None


def _valassz_legordulobol(qt_app, ablak, legordulo, szoveg: str) -> None:
    """Valódi kattintás a legördülőn, majd valódi kattintás a tételen.

    A legördülő nyitó átmenete valós időt vesz igénybe, és az eseményhurok
    pörgetése ezt nem gyorsítja: a tétel pozíciója csak akkor biztos, ha
    fél másodpercig nem változott.
    """
    _klikk_ablakban(qt_app, ablak, legordulo)
    utolso = {"y": None, "mikor": 0.0}

    def megallt() -> bool:
        tetel = _legordulo_tetele(ablak, szoveg)
        if tetel is None:
            utolso["y"] = None
            return False
        y = tetel.mapToScene(QPointF(0, 0)).y()
        if y != utolso["y"]:
            utolso["y"] = y
            utolso["mikor"] = time.monotonic()
        return time.monotonic() - utolso["mikor"] >= 0.5

    assert _varj(qt_app, megallt), (
        f"a legördülő nem nyílt meg, vagy nincs rajta: {szoveg!r}"
    )
    _klikk_ablakban(qt_app, ablak, _legordulo_tetele(ablak, szoveg))


def _nyomtatas_megnyit(window, qt_app, menu_bar):
    """Fájl ▸ Print… valódi kattintással; visszaadja a nyomtatás párbeszédet.

    A nyomtatás önálló ablak, alapméretben (480x420) a tartalma nagyrészt az
    ablakon kívül esik, és a kattintás ott nem érne a gombhoz. Ezért a
    tesztelt tételek elérhetőségéhez az ablakot megnagyobbítjuk (ez
    előkészítés, nem a tesztelt művelet).
    """
    _megnyit(menu_bar, qt_app, "&File")
    _kattints(qt_app, _gyerek(window, "menuFilePrint"))
    assert _varj(qt_app, lambda: _latszik(window, "printDialog")), (
        "a Fájl ▸ Print… nem nyitotta meg a nyomtatást"
    )
    nyomtatas = _gyerek(window, "printDialog")
    nyomtatas.setProperty("width", 900)
    nyomtatas.setProperty("height", 1000)
    qt_app.processEvents()
    return nyomtatas


def _beallitas(objektum, mezo: str, kulcs: str):
    """Egy JS-objektum (QJSValue) mezője, Python-értékként."""
    return objektum.property(mezo).toVariant()[kulcs]


def _fajlvalasztó_nyitva(nyomtatas) -> bool:
    """A PDF-cél fájlválasztó (névtelen QML-elem) nyitva van-e.

    A tallózó választónak nincs objectName-je, ezért a típusa alapján
    keressük a nyomtatás párbeszéd gyermekei között.
    """
    return any(
        _valasztoablak(elem) and elem.property("visible") is True
        for elem in nyomtatas.findChildren(QObject)
    )


def _valasztoablak(elem) -> bool:
    """Fájl- vagy mappaválasztó (QML `FileDialog` / `FolderDialog`)."""
    nev = elem.metaObject().className()
    return "FileDialog" in nev or "FolderDialog" in nev


def _nyomtatas_panel_megnyit(window, qt_app):
    """A „Border and Text Options" gombbal nyitja a szegély-panelt."""
    gomb = _gyerek(window, "printOptionsButton")
    _kattints(qt_app, gomb)
    assert _varj(qt_app, lambda: _latszik(window, "printOptionsPanel")), (
        "a szegély-beállítások gomb nem nyitotta meg a panelt"
    )
    return _gyerek(window, "printOptionsPanel")


def _vizualis_keres(window, nev: str):
    """Az elem a VIZUÁLIS fában: a Repeater-delegátumoknak nincs QObject-szülőjük."""
    verem = [window.contentItem()]
    while verem:
        elem = verem.pop()
        if elem.objectName() == nev:
            return elem
        verem.extend(elem.childItems())
    raise AssertionError(f"{nev} nem található a vizuális fában")


class TestNyomtatasVezerlok:
    def test_fit_radio_valodi_kattintassal_visszaallitja_az_illeszteset(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        nyomtatas = _nyomtatas_megnyit(window, qt_app, menu_bar)

        _kattints(qt_app, _gyerek(window, "printFillRadio"))
        assert _varj(qt_app, lambda: nyomtatas.property("fitMode") == "fill"), (
            "a Fill the page kattintás nem váltott kitöltésre"
        )
        _kattints(qt_app, _gyerek(window, "printFitRadio"))
        assert _varj(qt_app, lambda: nyomtatas.property("fitMode") == "fit"), (
            "a Whole picture kattintás nem állította vissza az illesztést"
        )
        _zar(qt_app, nyomtatas)

    def test_peldanyszam_valodi_kattintasokkal_nott_es_csokkent(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        assert nyomtatas.property("copies") == 1, "a kezdő példányszám nem 1"

        _kattints(qt_app, _gyerek(window, "printCopiesPlusButton"))
        assert _varj(qt_app, lambda: nyomtatas.property("copies") == 2), (
            "a + gomb nem növelte a példányszámot"
        )
        _kattints(qt_app, _gyerek(window, "printCopiesMinusButton"))
        assert _varj(qt_app, lambda: nyomtatas.property("copies") == 1), (
            "a - gomb nem csökkentette a példányszámot"
        )
        _zar(qt_app, nyomtatas)

    def test_teljes_oldalas_elobeallitas_valodi_kattintassal_valtja_a_meretet(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        nyomtatas.setProperty("printSize", "TELJES_OLDAL_MAS")
        assert nyomtatas.property("printSize") == "TELJES_OLDAL_MAS"

        _kattints(qt_app, _gyerek(window, "printPresetFullPage"))
        assert _varj(
            qt_app, lambda: nyomtatas.property("printSize") == "TELJES_OLDAL"
        ), "a Teljes oldal előbeállítás kattintás nem váltotta a nyomatméretet"
        _zar(qt_app, nyomtatas)

    def test_tajolas_legordulobol_valodi_kattintassal_valaszthato(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        assert nyomtatas.property("orientation") == "auto"

        _valassz_legordulobol(
            qt_app, nyomtatas, _gyerek(window, "printOrientationBox"), "Landscape"
        )
        assert _varj(
            qt_app, lambda: nyomtatas.property("orientation") == "landscape"
        ), "a legördülő Landscape tétele nem állította a tájolást"
        _zar(qt_app, nyomtatas)

    def test_pdf_tallozas_valodi_kattintassal_megnyitja_a_cel_valasztot(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        assert not _fajlvalasztó_nyitva(nyomtatas), "már nyitva volt a választó"

        _kattints(qt_app, _gyerek(window, "printPdfBrowseButton"))
        assert _varj(qt_app, lambda: _fajlvalasztó_nyitva(nyomtatas)), (
            "a Browse… gomb nem nyitotta meg a PDF-cél választót"
        )
        for elem in nyomtatas.findChildren(QObject):
            if _valasztoablak(elem):
                _zar(qt_app, elem)
        _zar(qt_app, nyomtatas)

    def test_nyomatmeret_elobeallitas_0_valodi_kattintassal_valtja_a_meretet(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        nyomtatas = _nyomtatas_megnyit(window, qt_app, menu_bar)
        azonositok = nyomtatas.property("printSizePresetIds")
        gomb = _vizualis_keres(nyomtatas, "printPresetSize0")
        assert gomb.property("enabled") is True, "az első nyomatméret tiltott"
        cel = azonositok[0]

        _kattints(qt_app, gomb)

        assert _varj(qt_app, lambda: nyomtatas.property("printSize") == cel), (
            f"az első nyomatméret-előbeállítás nem váltotta a méretet ({cel})"
        )
        _zar(qt_app, nyomtatas)
