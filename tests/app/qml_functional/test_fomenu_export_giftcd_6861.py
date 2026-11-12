"""#6861: a mappamenü HTML-exportja és a Create Gift CD panelje kattintásból nyílik."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject
from PySide6.QtQml import QQmlExpression, qmlContext

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _kattints
from tests.app.qml_functional._teszt_menu_6861 import megnyit_fomenu
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def qml_app(qt_app, tmp_path, request, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))

    def kepeket_keszit(mappa: Path) -> None:
        make_minta_jpeg(mappa / "a.jpg", size=(640, 400), seed=85)
        make_minta_jpeg(mappa / "b.jpg", size=(500, 500), seed=86)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket_keszit,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        web_export_vezerlo=True,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel) -> bool:
    return var_feltetelre(qt_app, feltetel, 5.0)


def _elem(gyoker, nev: str):
    elem = _objektum(gyoker, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _ablakmagassag(window, qt_app, offset: int) -> None:
    vart = window.height() + offset
    window.setHeight(vart)
    assert _varj(qt_app, lambda: window.height() == vart), (
        f"a főablak magassága nem állt be {vart} px-re"
    )


def _kijelol_ket_kept(window, qt_app, controller) -> None:
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2), (
        "a két tesztkép nem töltődött be"
    )
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _menu_tetel(window, qt_app, cim: str, nev: str):
    megnyit_fomenu(window, qt_app, cim)
    tetel = _elem(window, nev)
    assert tetel.property("visible") is True, f"{nev} nem látszik a menüben"
    assert tetel.property("enabled") is True, f"{nev} le van tiltva"
    _kattints(qt_app, tetel)
    return tetel


def _kiadasi_kep(window, mappa: str | None, nev: str) -> None:
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    kep = window.grabWindow()
    assert not kep.isNull(), "a kiadáskép üres"
    assert kep.save(str(cel / nev), "PNG"), f"a kiadáskép nem menthető: {nev}"


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_folder_menu_export_html_cel_sablonlista_elonezet_es_export_gomb(
    qml_app, qt_app, height_offset
):
    window, controller, engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)

    # A jegy Create menüt nevez meg, a parancsleltár és a mért QML szerint ez
    # a Folder menü parancsa; az eredeti útvonalat tartjuk meg.
    _menu_tetel(window, qt_app, "F&older", "menuFolderWebExport")
    dialog = _elem(window, "webExportDialog")
    assert _varj(qt_app, lambda: dialog.property("visible") is True), (
        "a Folder ▸ Export as HTML Page... nem nyitotta meg az exportablakot"
    )
    assert dialog.property("title") == "Export as HTML Page..."
    folder_name = Path(str(controller.currentFolder)).name
    assert dialog.property("albumTitle") == folder_name
    assert _elem(dialog, "webExportTitleField").property("text") == folder_name
    assert _elem(dialog, "webExportSizeBox").property("currentIndex") == 3

    target = Path(str(dialog.property("targetFolder")))
    assert target.name == folder_name, (
        f"az alapértelmezett célmappa nem a megnyitott mappát kapta: {target}"
    )
    web_export_controller = engine.rootContext().contextProperty("webExportController")
    expected_target = Path(
        str(web_export_controller.defaultWebExportTargetForFolder(
            str(controller.currentFolder)
        ))
    )
    assert target == expected_target

    names = dialog.property("templateDisplayNames")
    if hasattr(names, "toVariant"):
        names = names.toVariant()
    assert len(names) == 7
    assert _elem(dialog, "webExportTemplateList").property("count") == 7
    preview = _elem(dialog, "webExportTemplatePreview")
    assert str(preview.property("source")), "a kiválasztott sablonnak nincs előnézete"

    preview_ready = QQmlExpression(
        qmlContext(preview), preview, "status === Image.Ready"
    )

    def _elonezet_kesz():
        ertek, hiba = preview_ready.evaluate()
        assert not hiba, preview_ready.error()
        return bool(ertek)

    assert _varj(qt_app, _elonezet_kesz), (
        "a kiválasztott sablon előnézete nem töltődött be"
    )
    export = _elem(dialog, "webExportGenerateButton")
    assert export.property("enabled") is True, "érvényes cél mellett az Export tiltott"

    if height_offset == 0:
        output_dir = os.environ.get("PICASAPY_6861_SCREENSHOT_DIR")
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            kep = dialog.grabWindow()
            assert not kep.isNull(), "a HTML-export kiadásképe üres"
            assert kep.save(
                str(Path(output_dir) / "picasapy-export-html.png"), "PNG"
            )
    QMetaObject.invokeMethod(dialog, "close")
    assert _varj(qt_app, lambda: dialog.property("visible") is False)


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_create_gift_cd_a_mappa_nevevel_es_mukodo_include_slideshow_valasztoval(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _kijelol_ket_kept(window, qt_app, controller)

    _menu_tetel(window, qt_app, "&Create", "menuCreateGiftCd")
    host = _elem(window, "giftCdHost")
    assert _varj(qt_app, lambda: host.property("visible") is True), (
        "a Create ▸ Create a Gift CD... nem nyitotta meg a panelt"
    )
    assert _elem(window, "publishCdName").property("text") == Path(
        str(controller.currentFolder)
    ).name
    slideshow = _elem(window, "publishIncludeSlideshowCheck")
    assert slideshow.property("visible") is True
    assert slideshow.property("checked") is True
    if height_offset == 0:
        _kiadasi_kep(window, os.environ.get("PICASAPY_6861_SCREENSHOT_DIR"),
                     "picasapy-gift-cd.png")

    _kattints(qt_app, slideshow)
    assert slideshow.property("checked") is False, (
        "az Include Slideshow választó nem reagált a kattintásra"
    )
    _kattints(qt_app, _elem(window, "publishPresentCdCancel"))
    assert _varj(qt_app, lambda: host.property("visible") is False)
