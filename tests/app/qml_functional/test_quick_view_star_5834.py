"""#5834: a gyors nézet a `.picasa.ini` csillagállapotát mutatja és váltja."""

import os
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.ini import load_document
from support.jpeg_factory import make_minta_jpeg
from support.qt_wait import wait_for_photo_op
from support.varakozas import var_feltetelre

KIADASKEP_MAPPA = "PICASAPY_5834_KIADASKEP_MAPPA"


def _csillagikon(window: QObject) -> str:
    button = window.findChild(QObject, "viewerQuickStarButton")
    assert button is not None, "a gyorsnézet Csillag gombja hiányzik"
    icon = button.property("contentItem")
    assert icon is not None, "a gyorsnézet Csillag ikonja hiányzik"
    return str(icon.property("source"))


def _kattint_csillagra(window, controller, qt_app) -> None:
    button = window.findChild(QObject, "viewerQuickStarButton")
    assert button is not None, "a gyorsnézet Csillag gombja hiányzik"
    point = button.mapToScene(
        QPointF(button.width() / 2, button.height() / 2)
    ).toPoint()
    wait_for_photo_op(
        controller,
        lambda: QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            point,
        ),
        qt_app=qt_app,
    )


def _csillag_erteke(ini_path: Path, photo_name: str) -> str | None:
    document = load_document(ini_path)
    section = document.section(photo_name)
    return section.get("star") if section else None


def test_quick_view_star_ini_olvasas_es_valtas_valodi_kattintassal(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    starred = tmp_path / "starred.jpg"
    plain = tmp_path / "plain.jpg"
    make_minta_jpeg(starred, size=(640, 480), seed=5834)
    make_minta_jpeg(plain, size=(640, 480), seed=5835)
    ini_path = tmp_path / ".picasa.ini"
    ini_path.write_text("[starred.jpg]\nstar=yes\n", encoding="utf-8")

    assert controller.begin_quick_view([str(starred), str(plain)])
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    starred_row = next(
        index
        for index, photo in enumerate(controller.photos.photos)
        if photo.name == starred.name
    )
    plain_row = next(
        index
        for index, photo in enumerate(controller.photos.photos)
        if photo.name == plain.name
    )
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", starred_row)
    base_height = int(window.height())

    def _ablakmagassag(delta: int) -> None:
        cel = base_height + delta
        window.setHeight(cel)
        assert var_feltetelre(
            qt_app, lambda: int(window.height()) == cel, 5.0
        ), f"a főablak nem vette fel a {cel} px-es magasságot"

    assert var_feltetelre(
        qt_app,
        lambda: viewer.property("visible") is True
        and viewer.property("currentIndex") == starred_row,
        5.0,
    ), "a gyorsnézet nézője nem nyílt meg"
    _ablakmagassag(-5)
    assert controller.photos.starAt(starred_row) is True, (
        "a gyorsnézeti rekord nem olvasta be a .picasa.ini csillagát"
    )
    kezdo_ikon = _csillagikon(window)
    assert "tray-star-on.svg" in kezdo_ikon, (
        f"a Csillag gomb nem a bekapcsolt ikont mutatja: {kezdo_ikon}"
    )

    _kattint_csillagra(window, controller, qt_app)
    assert var_feltetelre(
        qt_app, lambda: _csillag_erteke(ini_path, "starred.jpg") is None, 5.0
    ), "a Csillag gomb nem törölte a csillagos kép ini-kulcsát"
    assert var_feltetelre(
        qt_app,
        lambda: controller.photos.starAt(starred_row) is False
        and "tray-star-on.svg" not in _csillagikon(window),
        5.0,
    ), "a csillag levétele nem frissítette a gyorsnézet modelljét és ikonját"

    _ablakmagassag(0)
    _kattint_csillagra(window, controller, qt_app)
    assert var_feltetelre(
        qt_app,
        lambda: _csillag_erteke(ini_path, "starred.jpg") == "yes",
        5.0,
    ), "a Csillag gomb nem állította vissza a star=yes értéket"
    assert var_feltetelre(
        qt_app,
        lambda: controller.photos.starAt(starred_row) is True
        and "tray-star-on.svg" in _csillagikon(window),
        5.0,
    ), "a csillag visszaállítása nem frissítette a modellt és az ikont"

    _ablakmagassag(5)
    viewer.setProperty("currentIndex", plain_row)
    assert var_feltetelre(
        qt_app,
        lambda: viewer.property("currentIndex") == plain_row
        and "tray-star-on.svg" not in _csillagikon(window),
        5.0,
    ), "az ini-kulcs nélküli kép csillagosként jelent meg"
    _kattint_csillagra(window, controller, qt_app)
    assert var_feltetelre(
        qt_app, lambda: _csillag_erteke(ini_path, "plain.jpg") == "yes", 5.0
    ), "az eredetileg csillagtalan kép nem kapott csillagot"
    assert var_feltetelre(
        qt_app,
        lambda: controller.photos.starAt(plain_row) is True
        and "tray-star-on.svg" in _csillagikon(window),
        5.0,
    ), "a csillagtalan kép csillagozása nem frissítette a nézőt"

    capture_dir = os.environ.get(KIADASKEP_MAPPA)
    if capture_dir:
        QTest.qWait(800)
        capture = window.grabWindow()
        assert not capture.isNull(), "a gyorsnézet kiadásképe üres"
        target = Path(capture_dir)
        target.mkdir(parents=True, exist_ok=True)
        assert capture.save(str(target / "gyorsnezet-csillag-5834.png"))
