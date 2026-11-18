"""#7192: a mappalistán gépelt karakter a keresőmezőbe kerül, mint a rácson.

Az eredetiben a mappalista (`0x005c40e0`) és a rács (`0x005c42d0`) is a
`0x005c3fe0`-ba vezeti a módosító nélküli karaktert: a `0x21`-`0x7f`
tartomány a keresőmezőre fókuszál, beírja a karaktert és elnyeli az eseményt;
a `0x80`-`0xff` tartományt (az ékezetes betűket) elveti.

Minden próba VALÓDI `QKeyEvent`-et küld az ablaknak, miközben a mappalista
(vagy a rács) kap fókuszt, tehát a billentyű a termék saját útján jut el a
kezelőig. A kezelő függvényét közvetlenül egy próba sem hívja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent

from tests.support.jpeg_factory import make_jpeg
from tests.support.qml_focus import fokuszt_ad
from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _billentyu(
    window,
    qt_app,
    kulcs: Qt.Key,
    szoveg: str,
    modositok: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    """Egy teljes leütés (lenyomás és felengedés) az ablak eseményútján."""
    for tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
        qt_app.sendEvent(window, QKeyEvent(tipus, kulcs, modositok, szoveg))
    qt_app.processEvents()


def _karakter(window, qt_app, karakter: str) -> None:
    """Módosító nélküli, nyomtatható karakter; a kulcs a latin-1 kódja."""
    _billentyu(window, qt_app, Qt.Key(ord(karakter.upper())), karakter)


def _mappalista(window, qt_app):
    lista = _elem(window, "folderListView")
    fokuszt_ad(lista, qt_app)
    return lista


def _racs(window, qt_app):
    racs = _elem(window, "photoGrid")
    fokuszt_ad(racs, qt_app)
    return racs


def _nincs_bevitel(window, controller, qt_app, kulcs_leiras: str):
    """A tiltott billentyű után a mező érintetlen, és nincs keresés."""
    mezo = _elem(window, "searchField")
    qt_app.processEvents()
    assert mezo.property("text") == "", (
        f"{kulcs_leiras}: a keresőmezőbe nem kerülhetett karakter"
    )
    assert mezo.property("activeFocus") is False, (
        f"{kulcs_leiras}: a keresőmező nem kaphatott fókuszt"
    )
    assert controller.searchActive is False, f"{kulcs_leiras}: keresés indult"


def _ellenproba_betu_bemegy(window, controller, qt_app, kulcs_leiras: str):
    """Ellenpróba a negatív ághoz, fix várakozás nélkül.

    A tiltott billentyű után ugyanonnan egy érvényes karaktert gépelünk. Ha a
    tiltott billentyű bármit beírt vagy keresést indított volna, a mező
    szövege és a keresés lekérdezése eltérne a pontos `x`-től. Ugyanez a
    lépés azt is bizonyítja, hogy az eseményút él, tehát a korábbi üres
    állapot nem a halott billentyűút következménye.
    """
    _karakter(window, qt_app, "x")
    assert _varj(qt_app, lambda: controller.searchQuery == "x"), (
        f"{kulcs_leiras}: az utána gépelt 'x' nem indította el a keresést"
    )
    assert _elem(window, "searchField").property("text") == "x", (
        f"{kulcs_leiras}: a mező tartalma nem pontosan az utána gépelt 'x'"
    )


def _ket_mappa(qml_app, qt_app) -> None:
    """A `qml_app` könyvtára alá két almappa, hogy a lista léptethető legyen."""
    _window, controller, _engine = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa in ("alma", "korte"):
        (lib / mappa).mkdir(exist_ok=True)
        make_jpeg(lib / mappa / f"{mappa}.jpg", size=(80, 60))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


# --------------------------------------------------------------------------
# A kért viselkedés: a mappalistán gépelt ASCII karakter a keresőbe kerül
# --------------------------------------------------------------------------


@pytest.mark.parametrize("karakter", ["a", "z", "!", "7", "~"])
def test_mappalistan_gepelt_ascii_karakter_a_keresobe_kerul(
    qml_app, qt_app, karakter
):
    window, controller, _engine = qml_app
    _mappalista(window, qt_app)

    _karakter(window, qt_app, karakter)

    mezo = _elem(window, "searchField")
    assert mezo.property("text") == karakter, (
        f"a mappalistán gépelt {karakter!r} nem került a keresőmezőbe"
    )
    assert mezo.property("activeFocus") is True, (
        "a mappalistán gépelés nem adta át a fókuszt a keresőmezőnek"
    )
    # #7081: a keresés a gépelési szünet (150 ms) után indul
    assert _varj(qt_app, lambda: controller.searchQuery == karakter), (
        f"a mappalistán gépelt {karakter!r} nem indított keresést"
    )


def test_a_hatarkarakterek_a_21_es_7e_a_tartomany_belsejeben_vannak(
    qml_app, qt_app
):
    """A `0x21` (`!`) az alsó, a `0x7e` (`~`) a felső nyomtatható határ."""
    window, _controller, _engine = qml_app
    _mappalista(window, qt_app)

    _karakter(window, qt_app, "!")
    _karakter(window, qt_app, "~")

    assert _elem(window, "searchField").property("text") == "!~"


def test_a_karakter_egyszer_kerul_a_mezobe(qml_app, qt_app):
    window, controller, _engine = qml_app
    _mappalista(window, qt_app)

    _karakter(window, qt_app, "a")
    mezo = _elem(window, "searchField")
    assert mezo.property("text") == "a", "a karakter duplán került a mezőbe"

    # a mező fókuszt kapott, a következő betű már a mezőn át érkezik
    _karakter(window, qt_app, "b")
    assert mezo.property("text") == "ab"

    assert _varj(qt_app, lambda: controller.searchQuery == "ab")
    assert mezo.property("text") == "ab", (
        "a keresés lefutása után a mező tartalma megváltozott"
    )


# --------------------------------------------------------------------------
# Az ékezetes betű (0x80 fölött) sem a mappalistán, sem a rácson nem ugrik
# --------------------------------------------------------------------------


@pytest.mark.parametrize("betu", ["á", "é", "ő", "ű", "Ő"])
@pytest.mark.parametrize("hely", ["mappalista", "racs"])
def test_ekezetes_betu_nem_ugrik_a_mezobe(qml_app, qt_app, hely, betu):
    window, controller, _engine = qml_app
    if hely == "mappalista":
        _mappalista(window, qt_app)
    else:
        _racs(window, qt_app)

    _billentyu(window, qt_app, Qt.Key.Key_unknown, betu)

    leiras = f"{hely}: {betu!r}"
    _nincs_bevitel(window, controller, qt_app, leiras)
    _ellenproba_betu_bemegy(window, controller, qt_app, leiras)


# --------------------------------------------------------------------------
# A 0x21 alatti kódok és a módosítós billentyűk nem indítanak keresést
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("leiras", "kulcs", "szoveg"),
    [
        ("szóköz (0x20)", Qt.Key.Key_Space, " "),
        ("Enter (0x0d)", Qt.Key.Key_Return, "\r"),
        ("Backspace (0x08)", Qt.Key.Key_Backspace, "\x08"),
        ("Esc (0x1b)", Qt.Key.Key_Escape, "\x1b"),
        ("vezérlőkód (0x01)", Qt.Key.Key_unknown, "\x01"),
        ("vezérlőkód (0x1f)", Qt.Key.Key_unknown, "\x1f"),
        ("bal nyíl (üres szöveg)", Qt.Key.Key_Left, ""),
    ],
)
def test_a_21_alatti_kodok_nem_inditanak_keresest_a_mappalistan(
    qml_app, qt_app, leiras, kulcs, szoveg
):
    window, controller, _engine = qml_app
    _mappalista(window, qt_app)

    _billentyu(window, qt_app, kulcs, szoveg)

    _nincs_bevitel(window, controller, qt_app, leiras)
    _ellenproba_betu_bemegy(window, controller, qt_app, leiras)


@pytest.mark.parametrize(
    ("modosito", "nev"),
    [
        (Qt.KeyboardModifier.ControlModifier, "Ctrl"),
        (Qt.KeyboardModifier.AltModifier, "Alt"),
    ],
)
@pytest.mark.parametrize("hely", ["mappalista", "racs"])
def test_ctrl_es_alt_billentyu_nem_indit_keresest(
    qml_app, qt_app, hely, modosito, nev
):
    """Az `event.text` itt szándékosan nyomtatható (`y`): a módosító maga
    tiltja a bevitelt, nem a vezérlőkód-szöveg."""
    window, controller, _engine = qml_app
    if hely == "mappalista":
        _mappalista(window, qt_app)
    else:
        _racs(window, qt_app)

    _billentyu(window, qt_app, Qt.Key.Key_Y, "y", modosito)

    leiras = f"{hely}: {nev}+Y"
    _nincs_bevitel(window, controller, qt_app, leiras)
    _ellenproba_betu_bemegy(window, controller, qt_app, leiras)


# --------------------------------------------------------------------------
# A mappalista meglévő billentyűi nem változnak
# --------------------------------------------------------------------------


def test_a_fel_es_le_nyil_tovabbra_is_lepteti_a_mappalistat(qml_app, qt_app):
    """A kiinduló mappa a lista alján áll, ezért előbb a fel nyíl léptet."""
    window, controller, _engine = qml_app
    _ket_mappa(qml_app, qt_app)
    lista = _mappalista(window, qt_app)
    assert lista.property("count") >= 3
    alul = controller.property("currentFolder")

    _billentyu(window, qt_app, Qt.Key.Key_Up, "")
    assert _varj(
        qt_app, lambda: controller.property("currentFolder") != alul
    ), "a fel nyíl nem léptette a mappalistát"
    fent = controller.property("currentFolder")
    _nincs_bevitel(window, controller, qt_app, "fel nyíl")

    _billentyu(window, qt_app, Qt.Key.Key_Down, "")
    assert _varj(
        qt_app, lambda: controller.property("currentFolder") == alul
    ), f"a le nyíl nem lépett vissza a(z) {fent!r} mappáról"
    _nincs_bevitel(window, controller, qt_app, "le nyíl")
    _ellenproba_betu_bemegy(window, controller, qt_app, "nyilak után")
