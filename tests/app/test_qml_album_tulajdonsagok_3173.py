"""#3173 — az album tulajdonság-párbeszéde a felületen.

EGY párbeszéd, KÉT használat: a rajz az `album.fen`-é (a #422 óta a mappához),
mostantól album módban is — ott a NÉV és a HELYSZÍN is szerkeszthető, mert az
album definíciója (`[.album:<token>]`) mind a négy mezőt tudja tartani.

⚠️ A **zene** mező szándékosan inaktív marad: diavetítés-/mozgófilm-zene a
programban nincs, tehát nem is menthető sehova.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

_QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/PicasaPy"

_TESZT_QML = """
import QtQuick
import PicasaPy 1.0

Item {
    width: 600
    height: 500
    FolderPropertiesDialog {
        objectName: "azParbeszed"
    }
}
"""


@pytest.fixture
def parbeszed(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(engine)
    component.setData(_TESZT_QML.encode("utf-8"), QUrl())
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([component, obj])
    dlg = obj.findChild(QObject, "azParbeszed")
    assert dlg is not None
    yield dlg
    engine.deleteLater()


def _mezo(dlg, nev):
    obj = dlg.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestAlbumMod:
    def test_album_modban_a_nev_es_a_helyszin_SZERKESZTHETO(self, parbeszed, qt_app):
        parbeszed.setProperty("mode", "album")
        qt_app.processEvents()
        assert _mezo(parbeszed, "folderPropertiesNameField").property("enabled") is True
        assert _mezo(parbeszed, "folderPropertiesLocation").property("enabled") is True

    def test_mappa_modban_maradnak_INAKTIVAK(self, parbeszed, qt_app):
        """⛔ A mappa átnevezése fájlrendszer-művelet, a mappa-helyszín pedig
        nincs bekötve — ott NEM lehet szerkeszteni (a #422 állapota)."""
        parbeszed.setProperty("mode", "folder")
        qt_app.processEvents()
        assert _mezo(parbeszed, "folderPropertiesNameField").property("enabled") is False
        assert _mezo(parbeszed, "folderPropertiesLocation").property("enabled") is False

    def test_a_zene_MINDKET_modban_inaktiv(self, parbeszed, qt_app):
        for mod in ("folder", "album"):
            parbeszed.setProperty("mode", mod)
            qt_app.processEvents()
            assert (
                _mezo(parbeszed, "folderPropertiesUseMusic").property("enabled")
                is False
            ), f"{mod}: a zene nincs mögötte réteg, nem lehet aktív"

    def test_a_cim_album_modban_MAS(self, parbeszed, qt_app):
        """`CEditAlbum::albumTitle` = „Album tulajdonságai" (mérve)."""
        parbeszed.setProperty("mode", "folder")
        qt_app.processEvents()
        mappa_cim = parbeszed.property("title")
        parbeszed.setProperty("mode", "album")
        qt_app.processEvents()
        assert parbeszed.property("title") != mappa_cim

    def test_az_elfogadas_album_jelet_ad(self, parbeszed, qt_app):
        parbeszed.setProperty("mode", "album")
        parbeszed.setProperty("albumToken", "a" * 32)
        parbeszed.setProperty("albumName", "Régi")
        qt_app.processEvents()
        latott = []
        parbeszed.albumPropertiesAccepted.connect(
            lambda *a: latott.append(tuple(a))
        )
        _mezo(parbeszed, "folderPropertiesNameField").setProperty("text", "Új név")
        _mezo(parbeszed, "folderPropertiesDateField").setProperty("text", "2026-07-14")
        _mezo(parbeszed, "folderPropertiesLocation").setProperty("text", "Balaton")
        parbeszed.accept()
        qt_app.processEvents()
        assert latott, "nem jött album-jel"
        token, nev, datum, hely, _leiras = latott[0]
        assert token == "a" * 32
        assert nev == "Új név"
        assert datum == "2026-07-14"
        assert hely == "Balaton"

    def test_mappa_modban_a_MAPPA_jele_jon(self, parbeszed, qt_app):
        parbeszed.setProperty("mode", "folder")
        parbeszed.setProperty("folderPath", "/kepek/nyar")
        qt_app.processEvents()
        mappa, album = [], []
        parbeszed.folderPropertiesAccepted.connect(lambda *a: mappa.append(a))
        parbeszed.albumPropertiesAccepted.connect(lambda *a: album.append(a))
        parbeszed.accept()
        qt_app.processEvents()
        assert mappa and not album


class TestAMenu:
    def test_a_menutetel_a_parbeszedet_nyitja(self):
        """A bekötés a `FolderPane.qml`-ben van (a mappa-ág mintájára)."""
        forras = (_QML_DIR / "FolderPane.qml").read_text(encoding="utf-8")
        assert "onEditDescriptionRequested" in forras
        assert 'folderPropertiesDialog.mode = "album"' in forras
        assert "controller.editAlbumProperties(" in forras
        # ⛔ a mappa-ág visszaállítja a módot — különben a mappa-menü az
        # album-párbeszédet kapná
        assert 'folderPropertiesDialog.mode = "folder"' in forras
