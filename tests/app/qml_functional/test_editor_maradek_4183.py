"""#4183 — a szerkesztőpanel két kapcsolója, valódi főablakban.

A felvételek a teljes, kirajzolt alkalmazásablakból jönnek. A gombokat
QTest kattintja meg a kirajzolt helyükön; a tesztek nem a QML forrásszövegét
vagy egy közvetlenül meghívott kattintáskezelőt ellenőriznek.
"""

# rontás-kontroll: a régi showtextcheckbox x=129/y=107 elhelyezéssel az
# editToolAutolightLabel dobozát metszi → 3 failed (900/895/905 px).

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest


def _var(qt_app, feltetel, uzenet: str, masodperc: float = 3.0) -> None:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return
        except (AttributeError, RuntimeError, TypeError):
            pass
        time.sleep(0.01)
    raise AssertionError(uzenet)


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a kirajzolt főablakban nincs {nev}"
    return elem


def _nyisd_nezot(window, qt_app, magassag: int):
    window.resize(1280, magassag)
    window.setProperty("viewerOpen", True)
    viewer = _elem(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    _var(qt_app, lambda: viewer.isVisible(), "a PhotoViewer nem nyílt meg")
    _var(
        qt_app,
        lambda: _elem(window, "viewerImage")
        .property("source")
        .toString()
        .startswith("image://editpreview/"),
        "a valódi főablak nem kérte le a szerkesztett előnézetet",
    )
    assert window.height() == magassag, (
        f"a főablak nem vette fel a kért {magassag} px magasságot: "
        f"{window.height()} px"
    )
    return viewer


def _valodi_kattintas(window, elem) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def _jelenet_pont(elem):
    return elem.mapToScene(QPointF(0, 0))


def _ellenorizd_show_text_helyet(window) -> None:
    """A szövegkapcsoló a Text-csempe alsó, üres sávjában álljon."""
    racs = _elem(window, "fixesToolGrid")
    szoveg_csempe = _elem(window, "editToolText")
    szoveg_felirat = _elem(window, "editToolTextLabel")
    kapcsolo = _elem(window, "showtextcheckbox")
    felirat = _elem(window, "showtextlabel")

    kapcsolo_doboza = kapcsolo.mapRectToItem(
        racs, QRectF(0, 0, kapcsolo.width(), kapcsolo.height())
    )
    felirat_doboza = felirat.mapRectToItem(
        racs, QRectF(0, 0, felirat.width(), felirat.height())
    )
    vezerlo_doboza = kapcsolo_doboza.united(felirat_doboza)
    szoveg_doboza = szoveg_csempe.mapRectToItem(
        racs, QRectF(0, 0, szoveg_csempe.width(), szoveg_csempe.height())
    )
    szoveg_felirat_doboza = szoveg_felirat.mapRectToItem(
        racs, QRectF(0, 0, szoveg_felirat.width(), szoveg_felirat.height())
    )

    for nev in (
        "editToolCrop",
        "editToolTilt",
        "editToolRedeye",
        "editToolEnhance",
        "editToolAutolight",
        "editToolAutocolor",
        "editToolRetouch",
        "editToolText",
    ):
        for utotag in ("Icon", "Label"):
            resz = _elem(window, nev + utotag)
            resz_doboza = resz.mapRectToItem(
                racs, QRectF(0, 0, resz.width(), resz.height())
            )
            assert not vezerlo_doboza.intersects(resz_doboza), (
                f"a Show Text kapcsoló átfedi a {nev + utotag} elemet: "
                f"kapcsoló={vezerlo_doboza}, elem={resz_doboza}"
            )

    assert vezerlo_doboza.top() >= szoveg_felirat_doboza.bottom() - 3, (
        "a Show Text kapcsoló nem a Text felirata alatti szabad helyen van: "
        f"kapcsoló={vezerlo_doboza}, felirat={szoveg_felirat_doboza}"
    )
    assert vezerlo_doboza.bottom() <= szoveg_doboza.bottom() + 3, (
        "a Show Text kapcsoló kilóg a Text-csempe üres alsó részéből: "
        f"kapcsoló={vezerlo_doboza}, Text={szoveg_doboza}"
    )
    assert vezerlo_doboza.center().x() == pytest.approx(
        szoveg_doboza.center().x(), abs=3
    ), "a Show Text kapcsoló nincs a Text csempe alá igazítva"


def _stabil_felvetel(window, qt_app):
    """Két egymást követő, azonos ablakfelvételig vár, határidővel."""
    hatarido = time.monotonic() + 3.0
    elozo = None
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        kep = window.grabWindow()
        if not kep.isNull() and elozo is not None and kep == elozo:
            return kep
        elozo = kep
        time.sleep(0.01)
    raise AssertionError("a kirajzolt ablak képe nem stabilizálódott 3 s alatt")


def _stabil_foto_felvetel(window, foto, qt_app):
    """A valódi ablakból csak a fotó kirajzolt területét hasonlítja."""
    ablak_kep = _stabil_felvetel(window, qt_app)
    teglalap = foto.mapRectToScene(
        QRectF(0, 0, foto.width(), foto.height())
    ).toAlignedRect()
    return ablak_kep.copy(teglalap)


@pytest.mark.parametrize("magassag", [900, 895, 905])
def test_bal_panel_valto_rajzolt_kattintassal_osszecsuk_es_visszanyit(
    qml_app, qt_app, magassag
):
    window, _controller, _engine = qml_app
    _nyisd_nezot(window, qt_app, magassag)
    drawer = _elem(window, "viewerLeftDrawer")
    photo_area = _elem(window, "viewerPhotoArea")
    kapcsolo = _elem(window, "toggle_left_drawer")

    nyitott_szelesseg = drawer.width()
    nyitott_foto_x = _jelenet_pont(photo_area).x()
    assert nyitott_szelesseg > 0
    assert kapcsolo.width() == pytest.approx(15, abs=3)
    assert kapcsolo.height() == pytest.approx(16, abs=3)
    nyitott = _stabil_felvetel(window, qt_app)

    _valodi_kattintas(window, kapcsolo)
    _var(
        qt_app,
        lambda: drawer.width() == pytest.approx(1, abs=1),
        "a kattintás nem csukta össze a bal szerkesztőpanelt",
    )
    csukott = _stabil_felvetel(window, qt_app)
    csukott_foto_x = _jelenet_pont(photo_area).x()
    assert nyitott_foto_x - csukott_foto_x == pytest.approx(279, abs=3), (
        "a képterület nem húzódott vissza a 279 px-re csúsztatott panel helyére"
    )
    assert nyitott != csukott, "a főablak kirajzolt képe nem változott"

    _valodi_kattintas(window, kapcsolo)
    _var(
        qt_app,
        lambda: drawer.width() == pytest.approx(nyitott_szelesseg, abs=1),
        "a kattintás nem nyitotta vissza a szerkesztőpanelt",
    )
    assert _jelenet_pont(photo_area).x() == pytest.approx(nyitott_foto_x, abs=3)


@pytest.mark.parametrize("magassag", [900, 895, 905])
def test_szoveg_kapcsolo_elrejti_majd_visszaallitja_a_kepre_rajzolt_szoveget(
    qml_app, qt_app, magassag
):
    window, _controller, engine = qml_app
    _nyisd_nezot(window, qt_app, magassag)
    edit = engine.rootContext().contextProperty("editController")

    # A valós szerkesztővezérlővel létrehozunk egy mentett feliratot; a
    # kapcsolót és a megjelenített eredményt ezután valódi kattintással
    # vizsgáljuk.
    edit.enterTextTool()
    edit.setTextDraft("PicasaPy 4183")
    edit.previewTextPlacement(0.5, 0.5)
    edit.applyText()
    _var(
        qt_app,
        lambda: edit.property("hasTextOverlay") is True,
        "a próba szövegrétege nem került a valódi szerkesztési állapotba",
    )
    kepes_gyoker = _elem(window, "viewerImage")
    _var(
        qt_app,
        lambda: kepes_gyoker.property("source")
        .toString()
        .startswith("image://editpreview/"),
        "a szövegréteges előnézet forrása hiányzik",
    )
    szoveggel = _stabil_foto_felvetel(window, kepes_gyoker, qt_app)
    kapcsolo = _elem(window, "showtextcheckbox")
    indikator = _elem(window, "showtextcheckboxIndicator")
    assert kapcsolo.isVisible(), "a szövegréteg kapcsolója nem látható"
    assert kapcsolo.property("checked") is True
    _ellenorizd_show_text_helyet(window)

    _valodi_kattintas(window, indikator)
    _var(
        qt_app,
        lambda: edit.property("textOverlayVisible") is False,
        "a kattintás nem rejtette el a fotó szövegrétegét",
    )
    _var(
        qt_app,
        lambda: kapcsolo.property("checked") is False,
        "a jelölőnégyzet nem követte a kikapcsolt állapotot",
    )
    nelkule = _stabil_foto_felvetel(window, kepes_gyoker, qt_app)
    assert szoveggel != nelkule, (
        "a főablak kirajzolt képe nem változott a szöveg elrejtésekor"
    )
    assert edit.property("hasTextOverlay") is True, (
        "a nézetkapcsoló megváltoztatta a mentett szövegréteget"
    )

    _valodi_kattintas(window, indikator)
    _var(
        qt_app,
        lambda: edit.property("textOverlayVisible") is True,
        "a kattintás nem állította vissza a fotó szövegrétegét",
    )
    _var(
        qt_app,
        lambda: kapcsolo.property("checked") is True,
        "a jelölőnégyzet nem követte a visszakapcsolt állapotot",
    )
    visszaallitva = _stabil_foto_felvetel(window, kepes_gyoker, qt_app)
    assert szoveggel == visszaallitva, (
        "a szöveg újbóli megjelenítése nem állította vissza az eredeti képet"
    )
