"""A #4145 importvezérlői a főablakból is elérhetők és működnek."""

from __future__ import annotations

import pytest
import time

from PySide6.QtCore import QPoint, QPointF, QObject, Qt
from PySide6.QtTest import QTest


def _elem(gyoker, nev: str):
    talalat = gyoker.findChild(QObject, nev)
    assert talalat is not None, f"{nev} nem található"
    return talalat


def _kattint(ablak, elem, qt_app) -> None:
    assert elem.isEnabled(), f"{elem.objectName()} le van tiltva"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()} nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    for _ in range(10):
        qt_app.processEvents()


def _kattint_elso_legordulo_sorra(ablak, qt_app) -> None:
    hatarido = time.monotonic() + 2
    lista = None
    darab = 0
    tartalom_magassag = 0.0
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        listak = ablak.findChildren(QObject, "picasaComboList")
        lista = next(
            (
                jelolt
                for jelolt in listak
                if jelolt.property("visible")
                and int(jelolt.property("count")) > 0
            ),
            None,
        )
        if lista is not None:
            darab = int(lista.property("count"))
            tartalom_magassag = float(lista.property("contentHeight"))
            if tartalom_magassag > 0:
                break
        time.sleep(0.005)
    assert lista is not None and darab > 0 and tartalom_magassag > 0
    kozep = lista.mapToScene(
        QPointF(lista.width() / 2, tartalom_magassag / darab / 2)
    )
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    for _ in range(10):
        qt_app.processEvents()


@pytest.fixture(params=(675, 680, 685))
def panel_magassag(request):
    return request.param


def _nyitott_import_ablak(qml_app, qt_app, panel_magassag: int):
    foablak, _controller, _engine = qml_app
    foablak.resize(1280, 800)
    foablak.show()
    qt_app.processEvents()
    _kattint(foablak, _elem(foablak, "toolbarImportButton"), qt_app)
    import_ablak = _elem(foablak, "importSourceDialog")
    assert import_ablak.property("visible") is True
    import_ablak.setProperty("height", panel_magassag)
    qt_app.processEvents()
    return foablak, import_ablak


@pytest.fixture
def import_ablak(qml_app, qt_app, panel_magassag):
    _foablak, ablak = _nyitott_import_ablak(
        qml_app, qt_app, panel_magassag
    )
    yield ablak
    # Az ImportSourceDialog külön, modális QWindow. A következő próba
    # tényleges kattintásait ne nyelje el nyitva maradt előző ablak.
    ablak.setProperty("visible", False)
    qt_app.processEvents()


def test_a_fooldalrol_kattintva_a_kovetkezo_es_elozo_kepre_lep(
    import_ablak, qt_app
):
    ablak = import_ablak
    ablak.setProperty(
        "previewItems",
        [
            {"path": "elso.jpg", "thumbUrl": "", "excluded": False},
            {"path": "masodik.jpg", "thumbUrl": "", "excluded": False},
        ],
    )
    ablak.setProperty("previewCount", 2)
    qt_app.processEvents()

    elore = _elem(ablak, "importSourceNextButton")
    hatra = _elem(ablak, "importSourcePreviousButton")
    assert elore.property("enabled") is True
    assert hatra.property("enabled") is False
    assert str(elore.property("helpText")) == "View the next Photo"
    assert str(hatra.property("helpText")) == "View the previous Photo"

    _kattint(ablak, elore, qt_app)
    assert ablak.property("selectedPreviewIndex") == 1
    assert hatra.property("enabled") is True
    assert elore.property("enabled") is False

    _kattint(ablak, hatra, qt_app)
    assert ablak.property("selectedPreviewIndex") == 0


def test_a_fooldalrol_kattintva_az_opciok_menu_megnyilik(
    import_ablak, qt_app
):
    ablak = import_ablak
    gomb = _elem(ablak, "importSourceOptionsButton")
    assert str(gomb.property("text")) == "Options"
    assert str(gomb.property("helpText")) == "Online options"

    _kattint(ablak, gomb, qt_app)

    menu = _elem(ablak, "importSourceOnlineOptionsMenu")
    assert menu.property("visible") is True
    csillagozott = _elem(ablak, "importSourceSyncStarredOnlyCheckBox")
    assert str(csillagozott.property("text")) == "Sync starred photos only"
    assert csillagozott.property("enabled") is False


def test_a_fooldalrol_kattintva_a_forras_es_cel_valaszto_kimenetet_ad(
    qml_app, qt_app, import_ablak, tmp_path
):
    foablak, _controller, engine = qml_app
    ablak = import_ablak

    for nev in ("importSourceFromMenu", "importSourceFolderMenu"):
        _elem(ablak, nev)

    forras = tmp_path / "forras"
    cel = tmp_path / "cel"
    forras.mkdir()
    cel.mkdir()
    vezerlo = engine.rootContext().contextProperty("importSourceController")
    vezerlo._remember_source(str(forras))
    vezerlo._remember_destination(str(cel))
    qt_app.processEvents()
    assert str(forras) in list(vezerlo.recentSources)
    assert str(cel) in list(vezerlo.recentDestinations)

    for combo_nev, kimenet_nev, kimenet in (
        ("importSourceRecentBox", "sourceFolder", forras),
        ("importSourceRecentDestBox", "destFolder", cel),
    ):
        combo = _elem(ablak, combo_nev)
        assert combo.property("visible") is True
        _kattint(ablak, combo, qt_app)
        _kattint_elso_legordulo_sorra(ablak, qt_app)
        assert str(ablak.property(kimenet_nev)) == str(kimenet)


def test_a_feltoltes_jelolo_lathato_de_a_megszunt_szolgaltatas_miatt_letiltott(
    import_ablak
):
    ablak = import_ablak
    jelolo = _elem(ablak, "importSourceUploadCheckBox")
    assert jelolo.property("visible") is True
    assert jelolo.property("enabled") is False
    assert str(jelolo.property("text")) == "Upload"
    assert str(jelolo.property("helpText")) == "Upload to Picasa Web Albums..."
