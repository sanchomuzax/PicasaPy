"""QML-funkcionális tesztek: a #422 4. lépcsőjének kontextusmenüi —
album (`Album`) és Emberek-album (`PplAlbum`).

A tételsor forrása a `docs/specs/ui-audit-context-menus.md` A.2 szakasza.

FONTOS a teljességről: a dokumentum az `Album` osztályt **13 tételesnek**
mondja, de név szerint csak **11-et** sorol fel. A hiányzó kettőt nem
találjuk ki — ez a teszt a 11 DOKUMENTÁLT tételt rögzíti, és külön jegy
szól a hiányzók felderítéséről. Ezért itt nincs „13 tétel" állítás.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, type_name):
    component = QQmlComponent(engine)
    component.setData(
        f'import QtQuick\nimport PicasaPy 1.0\n{type_name} {{ objectName: "m" }}\n'
        .encode("utf-8"),
        QUrl(),
    )
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj))
    return obj


def _trigger(menu, name):
    item = menu.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


class TestAlbumContextMenu:
    DOCUMENTED = [
        "albumMenuDelete",
        "albumMenuEditDescription",
        "albumMenuAddNameTags",
        "albumMenuSelectAll",
        "albumMenuClearSelection",
        "albumMenuInvertSelection",
        "albumMenuRefreshThumbnails",
        "albumMenuOnlineActions",
        "albumMenuUploadToGooglePhotos",
        "albumMenuExportAsHtml",
    ]

    def test_every_documented_command_is_present_in_order(self, qml_engine):
        menu = _load(qml_engine, "AlbumContextMenu")
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.DOCUMENTED
        ]
        assert found == self.DOCUMENTED

    def test_unbacked_commands_are_shown_but_disabled(self, qml_engine):
        """Az album törlése/leírása és a webes műveletek mögött nincs
        réteg — szürkén LÁTSZANAK (spec 5.1.)."""
        menu = _load(qml_engine, "AlbumContextMenu")
        for name in (
            "albumMenuDelete",
            "albumMenuEditDescription",
            "albumMenuAddNameTags",
            "albumMenuOnlineActions",
            "albumMenuUploadToGooglePhotos",
        ):
            assert menu.findChild(QObject, name).property("enabled") is False

    @pytest.mark.parametrize(
        "item_name,signal_name",
        [
            ("albumMenuSelectAll", "selectAllRequested"),
            ("albumMenuClearSelection", "clearSelectionRequested"),
            ("albumMenuInvertSelection", "invertSelectionRequested"),
            ("albumMenuRefreshThumbnails", "refreshThumbnailsRequested"),
            ("albumMenuExportAsHtml", "exportAsHtmlRequested"),
        ],
    )
    def test_trigger_emits_matching_signal(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = _load(qml_engine, "AlbumContextMenu")
        events = []
        getattr(menu, signal_name).connect(lambda: events.append(True))
        _trigger(menu, item_name)
        qt_app.processEvents()
        assert events == [True]


class TestPeopleAlbumContextMenu:
    """A `PplAlbum` osztály négy tétele — ezek a dokumentumban név szerint
    mind szerepelnek, tehát a lista teljes."""

    EXPECTED = [
        "peopleAlbumMenuDelete",
        "peopleAlbumMenuEdit",
        "peopleAlbumMenuSelectAll",
        "peopleAlbumMenuClearSelection",
    ]

    def test_all_four_commands_are_present_in_order(self, qml_engine):
        menu = _load(qml_engine, "PeopleAlbumContextMenu")
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.EXPECTED
        ]
        assert found == self.EXPECTED

    def test_people_album_editing_is_disabled_until_the_faces_work(
        self, qml_engine
    ):
        """A személy-album törlése/szerkesztése a #26 hatóköre."""
        menu = _load(qml_engine, "PeopleAlbumContextMenu")
        assert menu.findChild(
            QObject, "peopleAlbumMenuDelete").property("enabled") is False
        assert menu.findChild(
            QObject, "peopleAlbumMenuEdit").property("enabled") is False

    @pytest.mark.parametrize(
        "item_name,signal_name",
        [
            ("peopleAlbumMenuSelectAll", "selectAllRequested"),
            ("peopleAlbumMenuClearSelection", "clearSelectionRequested"),
        ],
    )
    def test_trigger_emits_matching_signal(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = _load(qml_engine, "PeopleAlbumContextMenu")
        events = []
        getattr(menu, signal_name).connect(lambda: events.append(True))
        _trigger(menu, item_name)
        qt_app.processEvents()
        assert events == [True]
