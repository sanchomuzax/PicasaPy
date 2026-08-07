"""QML-funkcionális teszt: a mappa-kontextusmenü HÁROM megnyitási pontja
(#422, 1. lépcső).

A `docs/specs/ui-audit-context-menus.md` 1.b szakaszának megállapítása: a
felhasználó három külön képernyőképe (a rács üres területe, a bal panel
mappa-sora, a rács tetején a mappa-fejléc) **bájtra azonos** menüt ad.
Implementációs következmény: EGY komponens, három hívóval — nem három
külön menü. Ez a teszt pontosan ezt őrzi.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open_from_window(window, path):
    QMetaObject.invokeMethod(
        window, "openFolderContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", path),
    )


class TestFolderMenuOpenPoints:
    def test_the_menu_exists_only_once(self, qml_app, qt_app):
        """Egy komponens, három hívó — nem három példány."""
        window, _controller, _engine = qml_app
        menus = [
            child for child in window.findChildren(QObject)
            if child.objectName() == "folderContextMenu"
        ]
        assert len(menus) == 1

    def test_window_entry_point_targets_the_given_folder(
        self, qml_app, qt_app, tmp_path
    ):
        """A rács mappa-fejléce ARRA a mappára nyitja a menüt, amelyiknek a
        fejléce — ezt az ablak-szintű átjárón át kéri."""
        window, _controller, _engine = qml_app
        _open_from_window(window, "/kepek/balaton")
        qt_app.processEvents()
        assert _child(window, "folderContextMenu").property("folderPath") == (
            "/kepek/balaton"
        )

    def test_empty_path_falls_back_to_the_current_folder(self, qml_app, qt_app):
        """A rács ÜRES területéről nincs saját mappa-útvonal — ilyenkor a
        jelenleg kiválasztott mappa a célpont."""
        window, controller, _engine = qml_app
        _open_from_window(window, "")
        qt_app.processEvents()
        menu = _child(window, "folderContextMenu")
        assert menu.property("folderPath") == controller.currentFolder
        assert menu.property("folderPath") != ""

    def test_feed_has_a_right_click_handler_on_the_empty_area(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        handler = _child(window, "feedEmptyAreaContextMenu")
        # csak a JOBB gomb — a bal gombos kijelölés-logika érintetlen marad
        assert handler.property("acceptedButtons") == Qt.MouseButton.RightButton

    def test_sort_state_is_refreshed_when_the_menu_opens(self, qml_app, qt_app):
        """A „Mappa rendezésének alapja ▸" pipái a menü megnyitásakor a
        vezérlő friss állapotát veszik át."""
        window, controller, _engine = qml_app
        controller.setFolderSort("name")
        qt_app.processEvents()
        _open_from_window(window, "")
        qt_app.processEvents()
        assert _child(window, "folderContextMenu").property("sortMode") == "name"
