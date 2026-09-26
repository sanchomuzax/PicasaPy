"""QML-funkcionális teszt: az Emberek-panel — #26.

A panel helye nem találgatás: a binárisban a `rightdrawerpanel/peoplepanel`
elem a `propertiespanel` · `tagpanel` · `geopanel` mellett áll — abból a
négyesből nálunk eddig három volt meg. A szakasz-feliratok is az eredeti
szövegforrásából jönnek:

    PeoplePanel::InThis  „In this photo:"
    PeoplePanel::Known2  „People in these photos:"
    PeoplePanel::Known1  „Also in these photos:"
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open(window, qt_app):
    """A panel megnyitása a Nézet menüből. Kell: a QML-ben egy elem
    `visible`-je hamis, amíg a SZÜLŐJE rejtett — zárt panelen minden
    gyerek rejtettnek látszik."""
    QMetaObject.invokeMethod(
        _child(window, "menuViewPeople"),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


class TestPanelWiring:
    def test_it_is_closed_until_the_menu_opens_it(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        assert _child(window, "peoplePanel").property("visible") is False

        QMetaObject.invokeMethod(
            _child(window, "menuViewPeople"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert _child(window, "peoplePanel").property("visible") is True

    def test_the_title_is_the_original_one(self, qml_app, qt_app):
        """#754: a cím a FIÓK közös fejlécében él, nem a panelben.

        Az eredetiben egy fejléc van, és annak szövege a lap neve — ugyanaz,
        mint a Nézet menü tételéé (`PeoplePanel::title`)."""
        window, _controller, _engine = qml_app
        _open(window, qt_app)

        assert _child(window, "rightDrawerTitle").property("text") == "People"

    def test_the_close_button_closes_it(self, qml_app, qt_app):
        """#754: a bezáró gomb is a fiók fejlécében van (`close`, 14 × 14)."""
        window, _controller, _engine = qml_app
        _open(window, qt_app)

        QMetaObject.invokeMethod(
            _child(window, "rightDrawerClose"),
            "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert _child(window, "peoplePanel").property("visible") is False


class TestSections:
    def test_the_here_label_follows_the_selection_size(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        panel = _child(window, "peoplePanel")

        panel.setProperty("selectionCount", 1)
        assert panel.property("hereLabel") == "In this photo:"

        panel.setProperty("selectionCount", 3)
        assert panel.property("hereLabel") == "People in these photos:"

    def test_the_together_section_appears_only_with_data(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open(window, qt_app)
        panel = _child(window, "peoplePanel")

        assert _child(window, "peoplePanelAlsoLabel").property("visible") is False

        panel.setProperty("peopleWith", [{"name": "Anna Kis", "count": 2}])
        qt_app.processEvents()

        also = _child(window, "peoplePanelAlsoLabel")
        assert also.property("visible") is True
        assert also.property("text") == "Also in these photos:"

    def test_an_empty_panel_says_something_instead_of_nothing(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        _open(window, qt_app)

        assert _child(window, "peoplePanelEmptyText").property("visible") is True
        assert _child(window, "peoplePanelEmptyText").property("text")


class TestEmptyStates:
    """#26: az eredeti panelnek ÖT külön magyarázó szövege volt aszerint,
    mit néz éppen a felhasználó (`peoplepanel_text.tre`) — üres listát
    sosem hagyott."""

    def test_nothing_selected_says_no_people_yet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open(window, qt_app)
        panel = _child(window, "peoplePanel")
        panel.setProperty("selectionCount", 0)
        panel.setProperty("currentPerson", "")
        qt_app.processEvents()

        assert "No people have been found yet" in _child(
            window, "peoplePanelEmptyText"
        ).property("text")

    def test_a_selection_promises_the_people_on_it(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open(window, qt_app)
        panel = _child(window, "peoplePanel")
        panel.setProperty("selectionCount", 2)
        qt_app.processEvents()

        assert "currently selected photos" in _child(
            window, "peoplePanelEmptyText"
        ).property("text")

    def test_a_person_album_promises_who_appears_with_them(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open(window, qt_app)
        panel = _child(window, "peoplePanel")
        panel.setProperty("currentPerson", "Roy Avery")
        qt_app.processEvents()

        assert "appear with" in _child(
            window, "peoplePanelEmptyText"
        ).property("text")


def _click(window, item, qt_app):
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest

    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


class TestUnnamedAlbumHeader:
    """#3585 / #3566 (spec 9/b, 9/d): a „Név nélküliek" albumban, több
    kijelölt arcnál a panel fejléce a csoportosítás-váltógombot követi —
    csoportosítva `PeoplePanel::UnnamedCluster`, kibontva
    `PeoplePanel::Unnamed`."""

    def _open_unnamed_album(self, window, qt_app, selected):
        _open(window, qt_app)
        window.setProperty("unnamedFacesOpen", True)
        qt_app.processEvents()
        view = _child(window, "unnamedFacesView")
        view.setProperty("selectedCount", selected)
        qt_app.processEvents()
        return view

    def test_the_header_follows_the_cluster_toggle(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        view = self._open_unnamed_album(window, qt_app, selected=2)
        label = _child(window, "peoplePanelUnnamedLabel")

        assert label.property("visible") is True
        assert label.property("text") == "Unnamed people in these photos:"
        assert _child(window, "peoplePanelEmptyText").property("visible") is False

        _click(window, _child(view, "clusterToggleButton"), qt_app)

        assert view.property("grouped") is False
        assert label.property("text") == "Unnamed groups of people:"

    def test_no_unnamed_header_outside_the_album(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open(window, qt_app)
        panel = _child(window, "peoplePanel")
        panel.setProperty("selectionCount", 3)
        qt_app.processEvents()

        assert _child(window, "peoplePanelUnnamedLabel").property("visible") is False

    def test_no_unnamed_header_without_a_multiple_selection(self, qml_app, qt_app):
        """Egy kijelölt arcnál az eredeti egyképes ága fut (9/b) — az a
        #3566-é, itt csak az, hogy a „Név nélküli…" fejléc NEM jelenik meg."""
        window, _controller, _engine = qml_app
        self._open_unnamed_album(window, qt_app, selected=1)

        assert _child(window, "peoplePanelUnnamedLabel").property("visible") is False
