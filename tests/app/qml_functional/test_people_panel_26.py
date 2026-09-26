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
    gyerek rejtettnek látszik.

    Előtte a nyitó mappa-betöltés háttérmunkája lefut: a vége
    `statusChanged`-et küld, ami a panel kötéseit újraértékeli — enélkül
    a teszt `setProperty`-s felülírását egy késve érkező jelzés némán
    visszaírta (teljes fájlos futásban, sorrendfüggően)."""
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)
    qt_app.processEvents()
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


_ANNA_ID = "1111111111111111"
_BELA_ID = "2222222222222222"
# Anna és Béla EGY képen: Anna albumában Béla az „Also in these photos:" sor
_KOZOS_INI = (
    "[Contacts2]\n"
    f"{_ANNA_ID}=Anna;;\n"
    f"{_BELA_ID}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID};"
    f"rect64(5000280075006e00),{_BELA_ID}\n"
)


class TestFromPersonAlbumToUnnamed:
    """#3585 (átnézési lelet): „személy albuma → Névtelenek". A bal hasáb
    Névtelenek-sora nem vált nézetet a controllerben, így a
    `currentPersonName` az előző személyé marad. A Névtelenek albumban ettől
    még a Névtelenek fejléce kell, nem az előző személy „Szintén ezeken a
    fotókon" listája."""

    def _anna_albuma(self, window, controller, qt_app, tmp_path):
        from picasapy.index import open_index, sync_tree

        lib = tmp_path / "kepek"
        (lib / ".picasa.ini").write_text(_KOZOS_INI, encoding="utf-8")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, lib)
        controller._reload_after_sync()
        controller.showPerson("Anna")
        for _ in range(5):
            qt_app.processEvents()

    def _nevtelenek(self, window, qt_app, selected):
        # a bal hasáb Névtelenek-sorának jelzése — a Main.qml kezelője fut
        _child(window, "folderPane").unnamedFacesChosen.emit()
        qt_app.processEvents()
        view = _child(window, "unnamedFacesView")
        view.setProperty("selectedCount", selected)
        qt_app.processEvents()
        return view

    def test_the_unnamed_header_replaces_the_previous_person(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _open(window, qt_app)
        self._anna_albuma(window, controller, qt_app, tmp_path)
        # előfeltétel: Anna albumában Béla valóban a „Szintén" listán van
        assert _child(window, "peoplePanelAlsoLabel").property("visible") is True

        self._nevtelenek(window, qt_app, selected=2)

        label = _child(window, "peoplePanelUnnamedLabel")
        assert label.property("visible") is True
        assert label.property("text") == "Unnamed people in these photos:"
        assert _child(window, "peoplePanelAlsoLabel").property("visible") is False
        assert _child(window, "peoplePanelEmptyText").property("visible") is False

    def test_no_person_hint_in_the_unnamed_album(
        self, qml_app, qt_app, tmp_path
    ):
        """Kijelölés nélkül az üres-szöveg sem az előző személyről szól."""
        window, controller, _engine = qml_app
        _open(window, qt_app)
        self._anna_albuma(window, controller, qt_app, tmp_path)

        self._nevtelenek(window, qt_app, selected=0)

        empty = _child(window, "peoplePanelEmptyText")
        assert empty.property("visible") is True
        assert "appear with" not in empty.property("text")

    def test_back_to_the_person_album_the_also_list_returns(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _open(window, qt_app)
        self._anna_albuma(window, controller, qt_app, tmp_path)
        self._nevtelenek(window, qt_app, selected=2)

        window.setProperty("unnamedFacesOpen", False)
        qt_app.processEvents()

        assert _child(window, "peoplePanelAlsoLabel").property("visible") is True
        assert _child(window, "peoplePanelUnnamedLabel").property("visible") is False
