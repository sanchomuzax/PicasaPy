"""A „Néző" és a „Szerkesztő" táblázat vezérlői VALÓDI kattintással (#5135, 2. rész).

Lefedve (a jegy táblázatának sorrendjében):

Néző
- `textOverlayHitTarget_` - a képre írt szöveg kijelölése kattintással;
- `viewerMenuLocateFile` - a néző helyi menüjének „File on Disk" tétele;
  a `reveal_in_file_manager` helyettesítve (a valódi fájlkezelő-indítás ki van váltva);
- `slideshowRotateLeftButton` - a vetítés balra forgatója;
- `video_control_bar2/moviecontrols` - a film-előnézet lejátszás/szünet gombja.

Szerkesztő
- `cropSuggestion1`, `cropSuggestion2` - a vágási javaslat kattintása
  kijelöli a javasolt téglalapot.

A többi tételről (kamera-gombok, kollázs-vászon és -párbeszédek) a
`test_nezo_szerkeszto_valodi_5135_b.py` szól.

A hatást a felhasználó felől nézzük (kijelölés, forgatás, lejátszás-jelzés,
kijelölt téglalap). Parancsot közvetlenül nem indítunk: nincs
`triggered`/`clicked`/`activated` hívás és nincs `.emit()`. A párbeszédek
takarításához a `close` hívás szabad.
"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import pytest
from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre

_MAPPA = "fotok"
_KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def _keszits_konyvtarat(lib: Path) -> None:
    cel = lib / _MAPPA
    cel.mkdir()
    for nev in _KEPEK:
        make_jpeg(cel / nev, size=(320, 240))


@pytest.fixture
def valodi_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _latszik(window, nev: str) -> bool:
    elem = window.findChild(QObject, nev)
    return elem is not None and elem.property("visible") is True


def _vizualis_bejaras(item):
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _vizualis(window, nev: str):
    """A név szerinti, látható vizuális elem (a listák sorai ide esnek)."""
    for item in _vizualis_bejaras(window.contentItem()):
        if item.objectName() == nev and item.isVisible():
            return item
    raise AssertionError(f"{nev} vizuális elem nem látszik")


def _kattints(qt_app, ablak, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    """Valódi egérkattintás `elem` középpontjára, az `ablak`-ra küldve.

    ⚠️ Az ablakot a hívó adja át, és a teszt tartja életben (lásd a
    #5127-es próbák `_kattints`-ét: az `elem.window()` minden hívásnál új
    Python-burkolót hoz létre)."""
    assert elem is not None, "a kattintandó felületi elem hiányzik"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        gomb,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


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


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = _gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    nezo.setProperty("visible", True)
    qt_app.processEvents()
    return nezo


def _szines_kep(ut: Path, szin: str) -> str:
    kep = QImage(320, 240, QImage.Format.Format_RGB32)
    kep.fill(QColor(szin))
    assert kep.save(str(ut)), f"nem sikerült elkészíteni a tesztképet: {ut}"
    return QUrl.fromLocalFile(str(ut)).toString()


def _menu_sor(menu, nev: str) -> QQuickItem:
    """A helyi menü sora az objectName alapján (a `count`/`itemAt` bejárásával)."""
    kifejezes = QQmlExpression(
        qmlContext(menu),
        menu,
        "(function () {"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        f'    if (item && item.objectName === "{nev}") return item;'
        "  }"
        "  return null;"
        "})()",
    )
    eredmeny, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert eredmeny is not None, f"{nev} menüsor nem található"
    return shiboken6.wrapInstance(shiboken6.getCppPointer(eredmeny)[0], QQuickItem)


class TestNezoSzovegKijeloles:
    def test_szovegre_kattintva_kijeloli_a_szovegdobozt(self, valodi_app, qt_app):
        window, controller, engine = valodi_app
        _elokeszit(window, qt_app, controller)
        _nezot_nyit(window, qt_app)
        szerkeszto = engine.rootContext().contextProperty("editController")
        panel = _gyerek(window, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        # állapot-előkészítés a controlleren: a szöveg megszületik a képen
        szerkeszto.previewTextPlacement(0.3, 0.6)
        szerkeszto.setTextDraft("Nyaralás")
        szerkeszto.applyText()
        qt_app.processEvents()
        panel.setProperty("textActive", True)
        # a piszkozat eltér a dobozétól: a kijelölés ezt állítja vissza
        szerkeszto.setTextDraft("Más")
        qt_app.processEvents()
        assert szerkeszto.textDraft == "Más", "a próba feltétele: eltérő piszkozat"

        cel = _vizualis(window, "textOverlayHitTarget_0")
        _kattints(qt_app, window, cel)

        assert _varj(qt_app, lambda: szerkeszto.textDraft == "Nyaralás"), (
            "a szövegre kattintás nem jelölte ki a szövegdobozt"
        )
        assert szerkeszto.textSelectedIndex == 0


class TestNezoHelyiMenuFajlHelye:
    def test_fajl_helye_valodi_menupontra_megmutatja_a_kepet(
        self, valodi_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a fájlkezelő-indítás (`reveal_in_file_manager`) ki van váltva."""
        import picasapy.app.fileops_controller as fileops_module

        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        nezo = _nezot_nyit(window, qt_app)
        # a Keresés almenü csak akkor látszik, ha az eredeti is a lemezen van
        kep = Path(controller.photos.filePathAt(0))
        eredeti = kep.parent / ".picasaoriginals" / kep.name
        eredeti.parent.mkdir(parents=True, exist_ok=True)
        eredeti.write_bytes(b"5135 eredeti")
        megmutatott: list[Path] = []
        monkeypatch.setattr(
            fileops_module, "reveal_in_file_manager", megmutatott.append
        )

        _kattints(qt_app, window, nezo, Qt.MouseButton.RightButton)
        menu = _gyerek(window, "viewerContextMenu")
        assert _varj(qt_app, lambda: menu.property("opened") is True), (
            "a néző jobbklikkje nem nyitotta meg a helyi menüt"
        )

        _kattints(qt_app, window, _menu_sor(menu, "viewerMenuLocateMenuItem"))
        almenu = _gyerek(window, "viewerMenuLocateMenu")
        assert _varj(qt_app, lambda: almenu.property("opened") is True), (
            "a Keresés almenü nem nyílt meg"
        )

        _kattints(qt_app, window, _gyerek(window, "viewerMenuLocateFile"))

        assert _varj(qt_app, lambda: len(megmutatott) == 1), (
            "a File on Disk kattintás nem a fájlkezelő-indítást hívta"
        )
        assert megmutatott == [kep]


class TestVetitesForgatasBalra:
    def test_balra_forgato_kattintasra_elforgatja_a_kepet(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        QMetaObject.invokeMethod(
            window, "startSlideshow", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        show = _gyerek(window, "slideshowView")
        # a léptető időzítő ne lépjen a kattintás közben
        show.setProperty("playing", False)
        qt_app.processEvents()
        assert controller.photos.rotateAt(0) == 0, "a próba feltétele: 0 forgatás"
        # a vezérlősáv egérmozgásra jelenik meg; a mozgást állapotként jelezzük
        sav = _gyerek(window, "slideshowControls")
        sav.setProperty("shown", True)
        assert _varj(qt_app, lambda: sav.property("opacity") > 0.99), (
            "a vezérlősáv nem jelent meg"
        )

        gomb = _vizualis(window, "slideshowRotateLeftButton")
        _kattints(qt_app, window, gomb)

        assert _varj(qt_app, lambda: controller.photos.rotateAt(0) % 4 == 3, 15.0), (
            "a balra forgató kattintás nem forgatta el a vetítés képét"
        )
        QMetaObject.invokeMethod(show, "stop", Qt.ConnectionType.DirectConnection)


class TestFilmElonezetLejatszas:
    def test_elonezet_gomb_valodi_kattintasra_indul_es_all(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        window.resize(1280, 800)
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        _kattints(qt_app, window, _gyerek(window, "trayMovieButton"))
        assert _varj(qt_app, lambda: _latszik(window, "movieDialog")), (
            "a filmkészítő gomb nem nyitotta meg a párbeszédet"
        )
        dialog = _gyerek(window, "movieDialog")
        # két kép a film forrása: állapot-előkészítés a dialóguson, mint a #4617-nél
        dialog.setProperty("movieClipSources", [
            _szines_kep(tmp_path / "piros.png", "#ff0000"),
            _szines_kep(tmp_path / "kek.png", "#0000ff"),
        ])
        qt_app.processEvents()
        gomb = _gyerek(dialog, "video_control_bar2/moviecontrols")
        ablak = gomb.window()
        assert gomb.property("text") == "▶", "a próba feltétele: a lejátszás áll"

        _kattints(qt_app, ablak, gomb)
        assert _varj(qt_app, lambda: gomb.property("text") == "❚❚"), (
            "a film-előnézet gomb nem indította el a lejátszást"
        )

        _kattints(qt_app, ablak, gomb)
        assert _varj(qt_app, lambda: gomb.property("text") == "▶"), (
            "a második kattintás nem állította meg az előnézetet"
        )
        QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()


class TestVagasiJavaslat:
    """A vágó panel 2. és 3. javaslata: a kattintás a javasolt téglalapot jelöli ki (#448)."""

    @pytest.mark.parametrize(
        ("nev", "index"),
        [("cropSuggestion1", 1), ("cropSuggestion2", 2)],
    )
    def test_javaslat_kattintasra_a_javasolt_teglalap_lesz_a_kijeloles(
        self, qml_app, qt_app, nev, index
    ):
        window, _controller, engine = qml_app
        window.setProperty("viewerOpen", True)
        _gyerek(window, "photoViewer").setProperty("currentIndex", 0)
        _gyerek(window, "viewerEditorPanel").setProperty("cropActive", True)
        qt_app.processEvents()
        szerkeszto = engine.rootContext().contextProperty("editController")
        assert _varj(qt_app, lambda: len(szerkeszto.cropSuggestions) > index), (
            "a próba feltétele: a képhez van legalább három javaslat"
        )
        javaslat = szerkeszto.cropSuggestions[index]
        overlay = _gyerek(window, "cropOverlay")
        assert overlay.property("hasSelection") is False, "a próba feltétele: nincs kijelölés"

        _kattints(qt_app, window, _vizualis(window, nev))

        assert _varj(qt_app, lambda: overlay.property("hasSelection") is True), (
            f"a {nev} kattintás nem jelölt ki semmit"
        )
        teglalap = overlay.property("cropRect")
        assert (teglalap.x(), teglalap.y(), teglalap.width(), teglalap.height()) == (
            pytest.approx(javaslat["x"]),
            pytest.approx(javaslat["y"]),
            pytest.approx(javaslat["w"]),
            pytest.approx(javaslat["h"]),
        ), f"a kijelölt téglalap nem a(z) {nev} javaslata"
