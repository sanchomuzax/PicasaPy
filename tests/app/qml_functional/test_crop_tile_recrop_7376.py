"""A vágócsempe címkéje a hatályos vágást követi (#7376)."""

from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtTest import QSignalSpy

from picasapy.ini.rect64 import Rect64, encode_rect64
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from support.qt_wait import varj_feltetelre


def _crop_sor(rect: Rect64) -> str:
    return f"crop64=1,{encode_rect64(rect)};"


def _elem(window, object_name: str) -> QObject:
    item = window.findChild(QObject, object_name)
    assert item is not None, f"{object_name} nem található a kirajzolt ablakban"
    return item


def _uj_kepkockara_var(window, qt_app) -> None:
    """A QML-állapotot valóban megrajzoló képkocka elkészültéig vár."""
    kepkockak = QSignalSpy(window.frameSwapped)
    window.update()
    assert varj_feltetelre(
        qt_app, lambda: kepkockak.count() > 0, 3.0
    ), "a vágócsempe friss QML-képkockája nem készült el"


class TestCropTileRecrop7376(EditorTestHelpers):
    def test_felirat_es_csempe_rendereles_a_crop_allapotat_koveti(
        self, qml_app_email, qt_app, tmp_path
    ):
        eredeti = Rect64(left=0.1, top=0.1, right=0.9, bottom=0.9)
        masodik = Rect64(left=0.2, top=0.2, right=0.8, bottom=0.8)
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[b.jpg]\n"
            f"filters={_crop_sor(eredeti)}\n"
            f"crop=rect64({encode_rect64(eredeti)})\n",
            encoding="utf-8",
        )

        window, _, engine = qml_app_email
        self._open_viewer(window, qt_app, index=0)
        controller = self._edit_controller(engine)
        crop_label = _elem(window, "editToolCropLabel")
        tile = _elem(window, "editToolCrop")
        straighten = _elem(window, "editToolTiltLabel")
        redeye = _elem(window, "editToolRedeyeLabel")
        szomszedos_feliratok = (
            straighten.property("text"),
            redeye.property("text"),
        )
        tile_width = tile.property("width")

        assert controller.property("hasCrop") is False
        assert crop_label.property("text") == "Vágás"
        _uj_kepkockara_var(window, qt_app)
        elotte = window.grabWindow()
        assert not elotte.isNull(), "a vágás előtti QML-képkocka üres"
        assert elotte.save(str(tmp_path / "crop-tile-before.png"))

        has_crop_jelzesek = []
        controller.hasCropChanged.connect(
            lambda: has_crop_jelzesek.append(controller.property("hasCrop"))
        )
        controller.applyCrop(
            eredeti.left,
            eredeti.top,
            eredeti.right - eredeti.left,
            eredeti.bottom - eredeti.top,
        )
        qt_app.processEvents()
        assert controller.property("hasCrop") is True
        _uj_kepkockara_var(window, qt_app)
        assert crop_label.property("text") == "Vágás megismétlése"
        assert crop_label.property("lineCount") <= 2
        assert crop_label.property("truncated") is False
        utana = window.grabWindow()
        assert not utana.isNull(), "az első Apply utáni QML-képkocka üres"
        assert utana.save(str(tmp_path / "crop-tile-after.png"))

        controller.applyCrop(
            masodik.left,
            masodik.top,
            masodik.right - masodik.left,
            masodik.bottom - masodik.top,
        )
        qt_app.processEvents()
        controller.undo()
        qt_app.processEvents()
        assert controller.property("hasCrop") is False
        assert crop_label.property("text") == "Vágás"

        controller.redo()
        qt_app.processEvents()
        assert controller.property("hasCrop") is True
        assert crop_label.property("text") == "Vágás megismétlése"

        viewer = window.findChild(QObject, "photoViewer")
        assert viewer is not None
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        assert controller.property("hasCrop") is True
        assert crop_label.property("text") == "Vágás megismétlése"

        assert has_crop_jelzesek == [True, True, False, True, True], (
            "a hasCropChanged jel nem követte az Apply, Undo, Redo és képváltás "
            f"állapotait: {has_crop_jelzesek!r}"
        )
        assert tile.property("width") == tile_width
        assert (
            straighten.property("text"),
            redeye.property("text"),
        ) == szomszedos_feliratok
