"""A rács és a néző közötti váltás nem mozdítja el a tartalmat (#6333)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QPoint, QPointF, Qt, QTimer
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


_QML_REFS = []
_MERT_ELEMEK = (
    "mainWindowWorkspace",
    "mainToolbar",
    "mainSplit",
    "photoGrid",
    "folderPane",
    "folderListView",
    "rightDrawer",
    "trayBar",
)


def _bejark(item):
    for gyerek in item.childItems():
        _QML_REFS.append(gyerek)
        yield gyerek
        yield from _bejark(gyerek)


def _elemek(window, nev: str):
    return [
        item
        for item in _bejark(window.contentItem())
        if item.objectName() == nev
    ]


def _elem(window, nev: str):
    talalatok = _elemek(window, nev)
    assert talalatok, f"a felületi elem nem található: {nev}"
    return talalatok[0]


def _teglalap(elem, content_item):
    if elem is None:
        return None
    pont = elem.mapToItem(content_item, QPointF(0, 0))
    return (pont.x(), pont.y(), elem.width(), elem.height())


def _kepkeret(frame, image, content_item):
    """A rács tesztképe piros; a képkocka középvonalán méri a látható pixeleket."""
    if image is None or not image.isVisible():
        return None
    dpr = frame.devicePixelRatio()
    kozep = image.mapToItem(
        content_item, QPointF(image.width() / 2, image.height() / 2)
    )
    cx = round(kozep.x() * dpr)
    cy = round(kozep.y() * dpr)
    if not (0 <= cx < frame.width() and 0 <= cy < frame.height()):
        return None

    def piros(x, y):
        szin = frame.pixelColor(x, y)
        return szin.red() > 180 and szin.green() < 80 and szin.blue() < 80

    if not piros(cx, cy):
        return None
    x0 = cx
    while x0 > 0 and piros(x0 - 1, cy):
        x0 -= 1
    x1 = cx
    while x1 + 1 < frame.width() and piros(x1 + 1, cy):
        x1 += 1
    y0 = cy
    while y0 > 0 and piros(cx, y0 - 1):
        y0 -= 1
    y1 = cy
    while y1 + 1 < frame.height() and piros(cx, y1 + 1):
        y1 += 1
    return (x0, y0, x1 + 1, y1 + 1)


def _merendo_elemek(window):
    return {nev: _elem(window, nev) for nev in (*_MERT_ELEMEK, "viewerImage")}


def _mintavetelez(window, controller, elems):
    content_item = window.contentItem()
    image = elems["viewerImage"]
    grid = elems["photoGrid"]
    grab_started = time.monotonic()
    frame = window.grabWindow()
    grab_duration = time.monotonic() - grab_started
    assert not frame.isNull(), "a QQuickWindow nem adott renderelt képkockát"
    kepkeret = _kepkeret(frame, image, content_item)
    return {
        "time": time.monotonic(),
        "grabDuration": grab_duration,
        "visibility": window.visibility().name,
        "window": (window.width(), window.height()),
        "content": (content_item.width(), content_item.height()),
        "frame": (frame.width(), frame.height()),
        "rects": {nev: _teglalap(elem, content_item) for nev, elem in elems.items()},
        "viewerImageVisible": image.isVisible(),
        "viewerImageFrameBounds": kepkeret,
        "gridY": float(grid.property("contentY")),
        "savedGridY": float(grid.property("savedY")),
        "viewerOpen": bool(window.property("viewerOpen")),
        "backgroundWork": bool(controller.backgroundWorkRunning()),
    }


def _gyujt(window, controller, elems, muvelet, kesz):
    """16 ms-onként vesz képkocka- és geometria-mintát, legfeljebb 3 s-ig."""
    mintak = [_mintavetelez(window, controller, elems)]
    loop = QEventLoop()
    utemezo = QTimer()
    utemezo.setTimerType(Qt.TimerType.PreciseTimer)
    utemezo.setInterval(16)
    hatarido = QTimer()
    hatarido.setSingleShot(True)
    hatarido.setInterval(3000)
    stabil = 0
    elozo = None
    action_duration = None

    def mintat_vesz():
        nonlocal stabil, elozo
        minta = _mintavetelez(window, controller, elems)
        mintak.append(minta)
        if kesz(minta):
            alairas = (
                minta["visibility"],
                minta["window"],
                minta["content"],
                minta["frame"],
                tuple(
                    (nev, minta["rects"][nev])
                    for nev in (*_MERT_ELEMEK, "viewerImage")
                    if nev != "viewerImage" or minta["viewerImageVisible"]
                ),
                minta["gridY"],
            )
            stabil = stabil + 1 if alairas == elozo else 0
            elozo = alairas
            if stabil >= 8:
                loop.quit()

    utemezo.timeout.connect(mintat_vesz)
    hatarido.timeout.connect(loop.quit)
    utemezo.start()
    hatarido.start()
    def muvelet_az_esemenyhurokben():
        nonlocal action_duration
        started = time.monotonic()
        muvelet()
        action_duration = time.monotonic() - started

    QTimer.singleShot(0, muvelet_az_esemenyhurokben)
    loop.exec()
    utemezo.stop()
    hatarido.stop()
    mintak[0]["actionDuration"] = action_duration
    return mintak


def _mozgasok(mintak, nev):
    # A könyvtár elemei csak akkor látszanak, amikor a néző zárva van: a néző
    # mögötti, takart elrendezés változása nem látható ugrás.
    rectek = [minta["rects"][nev] for minta in mintak if not minta["viewerOpen"]]
    if nev == "viewerImage":
        rectek = [
            minta["rects"][nev]
            for minta in mintak
            if minta["viewerImageVisible"]
            and minta["viewerImageFrameBounds"] is not None
        ]
    if len(rectek) < 2:
        return []
    cimkek = ("x", "y", "szélesség", "magasság")
    return [
        (cimke, min(r[i] for r in rectek), max(r[i] for r in rectek))
        for i, cimke in enumerate(cimkek)
        if max(r[i] for r in rectek) - min(r[i] for r in rectek) > 1
    ]


def _hibaosszeg(mintak, nev):
    mozgott = _mozgas_hiba(mintak, nev)
    y = [m["gridY"] for m in mintak]
    tartam = mintak[-1]["time"] - mintak[0]["time"]
    intervallumok = [
        b["time"] - a["time"] for a, b in zip(mintak, mintak[1:], strict=False)
    ]
    atlagos_koz = sum(intervallumok) / len(intervallumok)
    legnagyobb_koz = max(intervallumok)
    atlagos_grab = sum(m["grabDuration"] for m in mintak) / len(mintak)
    return (
        f"{nev}: {len(mintak)} minta / {tartam:.3f} s; "
        f"mintaköz átlag/max={atlagos_koz * 1000:.1f}/{legnagyobb_koz * 1000:.1f} ms, "
        f"grab átlag={atlagos_grab * 1000:.1f} ms, "
        f"bemeneti művelet={mintak[0]['actionDuration'] * 1000:.1f} ms; "
        + (
            ", ".join(mozgott)
            if mozgott
            else f"rács contentY={min(y):.1f}…{max(y):.1f} px; nincs 1 px-nél nagyobb elmozdulás"
        )
    )


def _mozgas_hiba(mintak, nev):
    hibak = []
    for elem in (*_MERT_ELEMEK, "viewerImage"):
        valtozasok = _mozgasok(mintak, elem)
        if valtozasok:
            hibak.extend(
                f"{elem}.{tengely} {alap:.1f}→{vege:.1f} px"
                for tengely, alap, vege in valtozasok
            )
    y = [m["gridY"] for m in mintak]
    if max(y) - min(y) > 1:
        hibak.append(f"photoGrid.contentY {min(y):.1f}→{max(y):.1f} px")
    if len({m["content"] for m in mintak}) > 1:
        hibak.append(f"window contentItem {sorted({m['content'] for m in mintak})}")
    if len({m["window"] for m in mintak}) > 1:
        hibak.append(f"ablakméret {sorted({m['window'] for m in mintak})}")
    if len({m["frame"] for m in mintak}) > 1:
        hibak.append(f"grabWindow {sorted({m['frame'] for m in mintak})}")
    if len({m["visibility"] for m in mintak}) > 1:
        hibak.append(f"window.visibility {sorted({m['visibility'] for m in mintak})}")
    kepkeretek = [m["viewerImageFrameBounds"] for m in mintak if m["viewerImageFrameBounds"]]
    if len(kepkeretek) >= 2:
        for index, tengely in enumerate(("x", "y", "jobb", "alsó")):
            minimum = min(k[index] for k in kepkeretek)
            maximum = max(k[index] for k in kepkeretek)
            if maximum - minimum > 1:
                hibak.append(f"renderelt fotó {tengely} {minimum}→{maximum} px")
    return hibak


def _dupla_kattintas(window, item):
    assert isinstance(item, QQuickItem)
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    cel = QPoint(round(pont.x()), round(pont.y()))
    QTest.mouseDClick(window, Qt.MouseButton.LeftButton, pos=cel, delay=10)


def _kattintas(window, item):
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(pont.x()), round(pont.y())),
    )


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_nezo_nyitasa_es_visszalepese_nem_mozditja_el_a_tartalmat(
    qml_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    window.show()
    assert var_feltetelre(qt_app, lambda: window.isExposed(), 3.0)

    # A rácsnak legyen visszaállítandó, ténylegesen görgethető helyzete.
    mappa = Path(controller.watchedFolders[0])
    for i in range(36):
        make_jpeg(mappa / f"scroll-{i:02}.jpg", size=(80, 60))
    controller.rescan()
    assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() >= 38, 10.0)

    grid = _elem(window, "photoGrid")
    assert var_feltetelre(
        qt_app,
        lambda: grid.property("contentHeight") > grid.height() + 250,
        5.0,
    )
    grid.setProperty("contentY", 200.0)
    assert var_feltetelre(
        qt_app, lambda: abs(float(grid.property("contentY")) - 200.0) <= 1, 3.0
    )
    eredeti_y = float(grid.property("contentY"))

    ablak_tartalom = window.contentItem()
    racs = _teglalap(grid, ablak_tartalom)
    racs_elem = next(
        (
            elem
            for elem in _elemek(window, "thumbMouseArea")
            if elem.isVisible()
            and racs[1] <= _teglalap(elem, ablak_tartalom)[1]
            + elem.height() / 2
            <= racs[1] + racs[3]
        ),
        None,
    )
    assert racs_elem is not None, "a rácsban nincs valódi dupla kattintáshoz látható kép"
    elems = _merendo_elemek(window)
    # A termelési Qt platformjai aszinkron képtöltést használnak. Az alkalmazás
    # offscreen szinkron módja blokkolná a GUI-eseményhurkot a mérés alatt.
    image = elems["viewerImage"]
    image.setProperty("asynchronous", True)
    row = int(racs_elem.parentItem().property("index"))
    viewer = _elem(window, "photoViewer")
    # Töltsük be előre ugyanazt a képet, hogy a mért kettős kattintás csak a
    # nézetváltást mérje, ne az offscreen Image dekódolásának blokkolását.
    viewer.setProperty("currentIndex", row)
    assert var_feltetelre(qt_app, lambda: image.implicitWidth() > 0, 5.0), (
        "a néző előtöltött képe nem készült el"
    )
    assert image.property("asynchronous") is True

    nyitas = _gyujt(
        window,
        controller,
        elems,
        lambda: _dupla_kattintas(window, racs_elem),
        lambda minta: bool(window.property("viewerOpen"))
        and elems["viewerImage"].isVisible()
        and minta["viewerImageFrameBounds"] is not None,
    )

    back = _elem(window, "viewerBackButton")
    assert var_feltetelre(
        qt_app,
        lambda: bool(window.property("viewerOpen"))
        and viewer.isVisible()
        and image.isVisible(),
        3.0,
    )
    assert back.isVisible(), "a nézőben nem látszik a Vissza a könyvtárhoz gomb"

    vissza = _gyujt(
        window,
        controller,
        elems,
        lambda: _kattintas(window, back),
        lambda minta: not bool(window.property("viewerOpen"))
        and not controller.backgroundWorkRunning()
        and abs(float(grid.property("contentY")) - eredeti_y) <= 1,
    )

    assert nyitas[-1]["viewerOpen"], "a rács dupla kattintása nem nyitotta meg a nézőt"
    assert any(m["viewerImageFrameBounds"] for m in nyitas), (
        "a grabWindow képkockán nem jelent meg a piros próbakép"
    )
    assert not vissza[-1]["viewerOpen"], "a Vissza gomb nem lépett vissza a könyvtárba"
    assert abs(vissza[-1]["gridY"] - eredeti_y) <= 1, (
        f"a rács helyzete nem állt vissza: {eredeti_y:.1f} → "
        f"{vissza[-1]['gridY']:.1f} px"
    )

    hibak = _mozgas_hiba(nyitas, "nyitás") + _mozgas_hiba(vissza, "visszalépés")
    assert not hibak, (
        "a nézőváltás képkockák között elmozdította vagy átméretezte a tartalmat; "
        + "; ".join(hibak)
        + "\n"
        + _hibaosszeg(nyitas, "nyitás")
        + "\n"
        + _hibaosszeg(vissza, "visszalépés")
    )
