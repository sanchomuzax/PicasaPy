"""A típushibák és az üres kijelölés modális Információ-ablaka (#7121)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


_UZIENETEK = {
    "rotation_type": (
        "One or more images could not be rotated because of the file type."
    ),
    "rotation_empty": "Must have selected images to rotate.",
    "batch_type": (
        "Some images were not modified because of the file type.  Note that "
        "effects cannot be applied to movies."
    ),
    "batch_empty": "This operation requires selected images.",
}


def _kepeket_keszit(mappa) -> None:
    make_jpeg(mappa / "a.jpg", size=(320, 200))
    make_jpeg(mappa / "b.jpg", size=(320, 200))
    (mappa / "film.mp4").write_bytes(b"\x00" * 32)


@pytest.fixture
def info_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _objektum(ablak, nev: str):
    elem = ablak.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _sorok(controller, *, video: bool) -> list[int]:
    return [
        i
        for i, foto in enumerate(controller.photos.photos)
        if (foto.kind == "video") is video
    ]


def _ablak_elokeszit(ablak, controller, qt_app, magassag_eltolas: int) -> None:
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 3), (
        "a két kép és a videó nem töltődött be"
    )
    cel = int(ablak.height()) + magassag_eltolas
    ablak.setHeight(cel)
    assert _varj(qt_app, lambda: int(ablak.height()) == cel), (
        f"a főablak magassága nem állt be {cel} px-re"
    )
    ablak.show()
    ablak.requestActivate()
    assert _varj(qt_app, lambda: ablak.isActive()), "a főablak nem aktiválódott"


def _kijelol(ablak, qt_app, sorok: list[int]) -> None:
    ablak.setProperty("selectedIndexes", sorok)
    ablak.setProperty("selectedIndex", sorok[-1] if sorok else -1)
    qt_app.processEvents()


def _info_ablakot_ellenoriz(ablak, qt_app, vart_szoveg: str) -> QObject:
    dialog = _objektum(ablak, "operationInfoDialog")
    assert _varj(qt_app, lambda: dialog.property("visible") is True), (
        "nem jelent meg a modális Információ-ablak"
    )
    assert dialog.property("modal") is True
    assert dialog.property("title") == "Info"

    szoveg = _objektum(ablak, "operationInfoText")
    assert szoveg.property("text") == vart_szoveg
    ikon = _objektum(ablak, "operationInfoIcon")
    assert isinstance(ikon, QQuickItem)
    assert ikon.property("source").toString() == "icons/dialog-info.svg"

    gomb = _objektum(ablak, "operationInfoOkButton")
    assert _varj(qt_app, lambda: gomb.isVisible() and gomb.isEnabled()), (
        "az OK gomb nem vált láthatóvá és engedélyezetté"
    )
    assert gomb.property("text") == "OK"
    return dialog


def _ok_gombra_kattint(ablak, qt_app) -> None:
    gomb = _objektum(ablak, "operationInfoOkButton")
    assert isinstance(gomb, QQuickItem)
    pont = gomb.mapToScene(QPointF(gomb.width() / 2, gomb.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    assert _varj(
        qt_app,
        lambda: not _objektum(ablak, "operationInfoDialog").property(
            "visible"
        ),
    ), "az OK gomb nem zárta be az ablakot"


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
@pytest.mark.parametrize("eset", tuple(_UZIENETEK))
def test_figyelmeztetes_info_ablakban_es_ok_gombbal(
    info_app, qt_app, eset: str, magassag_eltolas: int
):
    ablak, controller, _engine = info_app
    _ablak_elokeszit(ablak, controller, qt_app, magassag_eltolas)
    kepek = _sorok(controller, video=False)
    videok = _sorok(controller, video=True)

    if eset == "rotation_type":
        controller.rotateRightMany([kepek[0], videok[0]])
        assert _varj(qt_app, lambda: controller.photos.photos[kepek[0]].rotate_steps == 1), (
            "a figyelmeztetés előtt a támogatott kép nem fordult el"
        )
    elif eset == "rotation_empty":
        controller.rotateRightMany([])
    elif eset == "batch_type":
        controller.applyEffectMany([kepek[0], videok[0]], "sepia")
    else:
        _kijelol(ablak, qt_app, [])
        QTest.keyClick(
            ablak,
            Qt.Key.Key_B,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )

    dialog = _info_ablakot_ellenoriz(ablak, qt_app, _UZIENETEK[eset])
    if eset == "batch_type":
        assert _varj(
            qt_app,
            lambda: "sepia" in controller.photos.photos[kepek[0]].filters,
        ), "a támogatott kép nem kapta meg az effektet az ablak megjelenéséig"

    _ok_gombra_kattint(ablak, qt_app)

    if eset == "rotation_type":
        controller.rotateRightMany(kepek)
        assert _varj(qt_app, lambda: controller.photos.photos[kepek[1]].rotate_steps == 1)
        assert dialog.property("visible") is False, (
            "tiszta képes forgatásnál is megjelent az ablak"
        )
    elif eset == "batch_type":
        controller.applyEffectMany(kepek, "bw")
        assert _varj(qt_app, lambda: not controller.batchEditActive), (
            "a tiszta képes effekt nem fejeződött be"
        )
        assert dialog.property("visible") is False, (
            "tiszta képes effekt után is megjelent az ablak"
        )
