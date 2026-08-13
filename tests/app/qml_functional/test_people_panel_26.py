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
        window, _controller, _engine = qml_app

        assert _child(window, "peoplePanelTitle").property("text") == "People"

    def test_the_close_button_closes_it(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open(window, qt_app)

        QMetaObject.invokeMethod(
            _child(window, "peoplePanelClose"),
            "clicked",
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
