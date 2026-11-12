"""A mappa-fejléc feltöltése és az Online options menü (#6870).

A referencia: a privát agent-repó
`referencia/kepernyo/2026-11-12-fejlec-upload-online-options-job646.png`
képe. A próba a ténylegesen kirajzolt menüt nyitja meg, majd a képen látható
feliratok, sorrend, elválasztók és aktív/letiltott állapotok szerint ellenőrzi.
Képpontos golden nem készül.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from support.varakozas import hibaturo_feltetel, var_feltetelre

_QML_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
_FEJLEC_GOMBOK = (_QML_DIR / "LightboxHeaderButtons.qml").read_text(
    encoding="utf-8"
)
_FEED_CSOPORT = (_QML_DIR / "LightboxFeedGroup.qml").read_text(
    encoding="utf-8"
)

_MENUTARTALOM = (
    ("headerOnlineMenuEnableSync", "Enable Sync", True),
    ("headerOnlineMenuSepAfterEnableSync", None, None),
    ("headerOnlineMenuPublic", "Public on the web", False),
    ("headerOnlineMenuUnlisted", "Limited, anyone with the link", False),
    ("headerOnlineMenuLimited", "Limited", False),
    ("headerOnlineMenuOnlyYou", "Only you", False),
    ("headerOnlineMenuSepAfterPrivacy", None, None),
    ("headerOnlineMenuWidth800", "800 Max. Width", False),
    ("headerOnlineMenuWidth1024", "1024 Max. Width", False),
    ("headerOnlineMenuWidth1600", "1600 Max. Width", False),
    ("headerOnlineMenuWidth2048", "2048 Max. Width", False),
    ("headerOnlineMenuOriginalSize", "Original Size Images", False),
    ("headerOnlineMenuSepAfterSize", None, None),
    ("headerOnlineMenuStarredOnly", "Starred Images Only", False),
    ("headerOnlineMenuSepAfterStarred", None, None),
    ("headerOnlineMenuViewOnline", "View Online", False),
    ("headerOnlineMenuRefreshStatus", "Refresh Online Status", False),
    ("headerOnlineMenuCopyUrl", "Copy URL", False),
    ("headerOnlineMenuSepBeforeDelete", None, None),
    ("headerOnlineMenuDeleteAlbum", "Delete Online Album", False),
)


def _keres(elem: QQuickItem, object_name: str):
    if elem.objectName() == object_name:
        return elem
    for child in elem.childItems():
        found = _keres(child, object_name)
        if found is not None:
            return found
    return None


def _kattints(ablak, qt_app, elem: QQuickItem) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(ablak, pont, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    qt_app.processEvents()


class TestOnlineOptionsMenu:
    def test_a_renderelt_menu_egyezik_a_job646_referencia_felirataival(self, qml_app, qt_app):
        ablak, vezerlo, _motor = qml_app
        assert var_feltetelre(
            qt_app,
            hibaturo_feltetel(lambda: vezerlo.photos.rowCount() > 0),
            3.0,
        )

        feltoltes = _keres(ablak.contentItem(), "headerUploadButton")
        nyil = _keres(ablak.contentItem(), "headerOnlineOptionsButton")
        assert feltoltes is not None, "hiányzik a Feltöltés feliratgomb"
        assert nyil is not None, "hiányzik a külön Online options nyíl"
        assert feltoltes.property("text") == "Upload"
        assert feltoltes.property("enabled") is True
        assert nyil.isEnabled(), "az Online options nyíl le van tiltva"
        assert nyil.x() == feltoltes.x() + feltoltes.width()
        assert nyil.y() == feltoltes.y()
        assert 'ToolTip.text: qsTr("Online options")' in _FEJLEC_GOMBOK

        header = feltoltes.parentItem().parentItem()
        upload_kerelem = QSignalSpy(header.uploadRequested)

        eredeti_magassag = ablak.height()
        for eltolas in (-5, 0, 5):
            ablak.setHeight(eredeti_magassag + eltolas)
            assert var_feltetelre(
                qt_app,
                hibaturo_feltetel(
                    lambda eltolas=eltolas: ablak.height()
                    == eredeti_magassag + eltolas
                ),
                3.0,
            ), f"a főablak magassága nem állt be ({eltolas:+} px)"
            nyil = _keres(ablak.contentItem(), "headerOnlineOptionsButton")
            assert nyil is not None and nyil.isVisible() and nyil.isEnabled()
            nyil_kattintas = QSignalSpy(nyil.clicked)
            _kattints(ablak, qt_app, nyil)
            assert nyil_kattintas.count() == 1, (
                f"az Online options nyíl nem kapott kattintást ({eltolas:+} px)"
            )
            menu_tetelek = []
            for object_name, text, enabled in _MENUTARTALOM:
                item = _keres(ablak.contentItem(), object_name)
                assert item is not None, (
                    f"a renderelt menüből hiányzik {object_name} "
                    f"({eltolas:+} px)"
                )
                assert item.isVisible(), (
                    f"a menü nem látszik a kattintás után ({eltolas:+} px)"
                )
                menu_tetelek.append((item, object_name, text, enabled))

            # Az Enable Sync a valódi bejelentkezési ablakot nyitja (#6865),
            # ezért az utolsó magasságon kattintjuk.
            if eltolas == 5:
                tenyleges = [
                    (name, item.property("text"))
                    for item, name, _text, _enabled in menu_tetelek
                ]
                vart = [(name, text) for name, text, _enabled in _MENUTARTALOM]
                assert tenyleges == vart, (
                    "a megnyitott menü felirata/sorrendje/tiltott állapota "
                    f"eltér a job646 képtől:\n{tenyleges!r}"
                )
                y_koordinatak = [
                    item.mapToScene(QPointF(0, 0)).y()
                    for item, _name, _text, _enabled in menu_tetelek
                ]
                assert y_koordinatak == sorted(y_koordinatak), (
                    f"a kirajzolt menüsorok nem a referencia sorrendjében állnak: "
                    f"{y_koordinatak!r}"
                )
                for item, name, _text, enabled in menu_tetelek:
                    if enabled is not None:
                        assert item.property("enabled") is enabled, (
                            f"{name} aktív állapota eltér: "
                            f"{item.property('enabled')}"
                        )

                enable_sync = menu_tetelek[0][0]
                _kattints(ablak, qt_app, enable_sync)
                assert upload_kerelem.count() == 1, (
                    "az Enable Sync nem ugyanazt a feltöltési műveletet kérte"
                )
            else:
                QTest.keyClick(ablak, Qt.Key.Key_Escape)
                qt_app.processEvents()


    def test_a_felirat_es_az_enable_sync_ugyanazt_a_feltoltesi_utvonalat_keri(self):
        assert "onUploadRequested" in _FEED_CSOPORT
        blokk = _FEED_CSOPORT.split("onUploadRequested", 1)[1].split("\n        }", 1)[0]
        assert "uploadGooglePhotosFromHeaderRows(" in blokk
        assert _FEJLEC_GOMBOK.count("header.uploadRequested()") >= 2
