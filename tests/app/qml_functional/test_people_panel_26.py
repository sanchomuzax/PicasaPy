"""QML-funkcionális teszt: az Emberek-panel — #26.

A panel helye nem találgatás: a binárisban a `rightdrawerpanel/peoplepanel`
elem a `propertiespanel` · `tagpanel` · `geopanel` mellett áll — abból a
négyesből nálunk eddig három volt meg.

A fejléc-választó fát (#3566, spec 9/b) valódi kijelöléssel a
`test_emberek_panel_fejlec_3566.py` fedi.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from support.jpeg_factory import make_jpeg


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open(window, qt_app):
    """A panel megnyitása a Nézet menüből. Kell: a QML-ben egy elem
    `visible`-je hamis, amíg a SZÜLŐJE rejtett — zárt panelen minden
    gyerek rejtettnek látszik.

    Előtte a nyitó mappa-betöltés háttérmunkája lefut: a vége
    `statusChanged`-et küld, ami a panel kötéseit újraértékeli. A panel
    állapotát ezért a tesztek a kötések FORRÁSÁN át állítják (valódi
    kattintás a rácson, `controller.showPerson()`), nem a panel
    `setProperty`-jével — azt egy késve érkező jelzés némán visszaírná."""
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        _child(window, "menuViewPeople"),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


def _walk_items(item):
    for child in item.childItems():
        yield child
        yield from _walk_items(child)


def _library_of(window, controller, qt_app, tmp_path, count):
    """A fixture két képe (`a.jpg`, `b.jpg`) mellé további sima képek —
    egyiken sincs megnevezett arc. Az útvonalak rácssorrendben."""
    from picasapy.app.worker_thread import wait_for_all_background_workers

    lib = tmp_path / "kepek"
    names = ["a.jpg", "b.jpg"] + [f"k{i}.jpg" for i in range(count - 2)]
    for name in names[2:]:
        make_jpeg(lib / name, size=(120, 90))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    for _ in range(5):
        qt_app.processEvents()
    return [lib / name for name in names]


def _grid_cell(window, row):
    for item in _walk_items(window.contentItem()):
        if item.objectName() != "thumbMouseArea" or not item.isVisible():
            continue
        cell = item.parentItem()
        if cell is not None and cell.property("index") == row:
            return item
    raise AssertionError(f"a(z) {row}. sor cellája nincs a rácson")


def _select_photos(window, controller, qt_app, paths):
    """VALÓDI kijelölés a rácson: kattintás az elsőre, Ctrl+kattintás a
    többire (a `test_emberek_panel_fejlec_3566.py` mintája)."""
    for i, path in enumerate(paths):
        row = controller.photos.rowOfPath(str(path))
        assert row >= 0, f"{path.name} nincs a rácson"
        item = _grid_cell(window, row)
        center = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier if i
            else Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        for _ in range(5):
            qt_app.processEvents()
    assert _child(window, "peoplePanel").property("selectionCount") == len(
        paths
    )


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

    def test_nothing_selected_promises_the_selection(self, qml_app, qt_app):
        """#3566: a „No people have been found yet" (Text3) a Név
        nélküliek album üres esete — máshol kijelölés nélkül is Text5."""
        window, _controller, _engine = qml_app
        _open(window, qt_app)
        panel = _child(window, "peoplePanel")
        assert panel.property("selectionCount") == 0
        assert panel.property("currentPerson") == ""

        empty = _child(window, "peoplePanelEmptyText")
        assert empty.property("visible") is True
        assert "currently selected photos" in empty.property("text")
        assert _child(window, "peoplePanelHeader").property("visible") is False

    def test_a_selection_replaces_the_promise_with_a_header(
        self, qml_app, qt_app, tmp_path
    ):
        """Spec 9/b, többképes ág, „van kép" sor: két kijelölt kép,
        megnevezett arc nélkül, a Név nélküliek albumon KÍVÜL — a fejléc a
        kibontott „Unnamed groups of people:", és a Text5 ígérete eltűnik.
        A 0 kijelölés esetétől (fent) épp ebben különbözik."""
        window, controller, _engine = qml_app
        paths = _library_of(window, controller, qt_app, tmp_path, 2)
        _open(window, qt_app)
        _select_photos(window, controller, qt_app, paths)

        header = _child(window, "peoplePanelHeader")
        assert header.property("visible") is True
        assert header.property("text") == "Unnamed groups of people:"
        assert _child(window, "peoplePanelEmptyText").property("visible") is False

    def test_a_person_album_promises_who_appears_with_them(self, qml_app, qt_app):
        """#3723: a `currentPerson` a `Main.qml`-ben
        `controller.currentPersonName`-hez van KÖTVE (`personViewChanged`-en
        át, ami a `statusChanged`-hez kötött — `people_controller.py::
        _init_people`). A valódi API (`controller.showPerson()`) a kötés
        FORRÁSÁT állítja, ezért egy késve érkező `statusChanged` (a nyitó
        mappa-szinkron háttérmunkájának vége — épp ez a Windows-CI hazárdja,
        ld. lentebb a `test_a_late_status_signal_does_not_undo_it`-ot) nem
        írja felül csendben — szemben egy közvetlen
        `panel.setProperty("currentPerson", …)`-vel, ami magát a kötött QML-
        tulajdonságot próbálja meg legyőzni."""
        window, controller, _engine = qml_app
        _open(window, qt_app)
        controller.showPerson("Roy Avery")
        qt_app.processEvents()

        assert "appear with" in _child(
            window, "peoplePanelEmptyText"
        ).property("text")

    def test_a_late_status_signal_does_not_undo_it(self, qml_app, qt_app):
        """#3723 (a Windows-CI ingadozásának reprodukálása, gép nélkül):
        a nyitó mappa-szinkron háttérmunkája a teszt lépései UTÁN is
        küldhet egy `statusChanged`-et (ez élesíti a `currentPersonName`
        kötést, ld. fent) — ezt a CI-n MÉRT hazárdot itt kézzel váltjuk ki.
        A valódi `controller.showPerson()`-on át beállított nézet egy ilyen
        késve érkező jelzést is túlél, mert a jelzés csak azt a forrást
        értékeli ki újra, amit mi is a valódi API-n át állítottunk —
        szemben a `panel.setProperty()`-s felülírással, amit egy ilyen
        jelzés némán visszaírna a kötés eredeti (üres) értékére."""
        window, controller, _engine = qml_app
        _open(window, qt_app)
        controller.showPerson("Roy Avery")
        qt_app.processEvents()
        controller.statusChanged.emit()
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


_FACE_LANDMARKS = FaceLandmarks(
    right_eye=(40.0, 30.0), left_eye=(70.0, 30.0), nose=(55.0, 45.0),
    mouth_right=(45.0, 60.0), mouth_left=(65.0, 60.0),
)


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


class TestUnnamedAlbumHeader:
    """#3585 / #3566 (spec 9/b, 9/d): a „Név nélküliek" albumban, több
    kijelölt arcnál a panel fejléce a csoportosítás-váltógombot követi —
    csoportosítva `PeoplePanel::UnnamedCluster`, kibontva
    `PeoplePanel::Unnamed`.

    A kijelölés VALÓDI kattintás az arc-rácson (a
    `test_emberek_panel_fejlec_3566.py` mintája): előbb egy valódi,
    `unnamed` állapotú arcot szúrunk az indexbe (`replace_faces` —
    ugyanaz az út, mint a szkennelésé, csak detektor nélkül), utána
    kattintunk a `faceTile_<id>` csempére."""

    def _seed_unnamed_faces(self, tmp_path, count):
        lib = tmp_path / "kepek"
        names = [f"p{i}.jpg" for i in range(count)]
        for name in names:
            make_jpeg(lib / name, size=(120, 90))
        face_ids = []
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, lib)
            for name in names:
                photo_id = conn.execute(
                    "SELECT id FROM photos WHERE name = ?", (name,)
                ).fetchone()["id"]
                face = FaceDetection(
                    left=20.0, top=10.0, right=90.0, bottom=80.0, score=0.9,
                    landmarks=_FACE_LANDMARKS,
                )
                replace_faces(conn, photo_id, [face])
                conn.commit()
                face_ids.append(conn.execute(
                    "SELECT id FROM face WHERE photo_id = ?", (photo_id,)
                ).fetchone()["id"])
        return face_ids

    def _click_faces(self, window, qt_app, face_ids):
        """A csempe a rács `reload()`-ja után, aszinkron jön létre, és a
        helye az elrendezés végéig mozoghat — ezért megvárjuk, hogy
        látsszon, és kattintás után azt is, hogy a kijelölés átmenjen
        (a CI lassabb gépén az azonnali kattintás mellément)."""
        view = _child(window, "unnamedFacesView")
        for i, face_id in enumerate(face_ids):
            target = f"faceTile_{face_id}"
            item = None
            for _ in range(150):
                item = next(
                    (it for it in _walk(window.contentItem())
                     if it.objectName() == target and it.isVisible()
                     and it.width() > 0),
                    None,
                )
                if item is not None:
                    break
                QTest.qWait(20)
            assert item is not None, f"{target} nem található/nem látszik a rácson"
            QTest.qWait(50)
            center = item.mapToScene(item.boundingRect().center())
            QTest.mouseClick(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.ControlModifier if i
                else Qt.KeyboardModifier.NoModifier,
                QPoint(round(center.x()), round(center.y())),
            )
            for _ in range(100):
                if view.property("selectedCount") >= i + 1:
                    break
                QTest.qWait(20)

    def _open_unnamed_album(self, window, qt_app, tmp_path, selected):
        face_ids = self._seed_unnamed_faces(tmp_path, selected)
        _open(window, qt_app)
        window.setProperty("unnamedFacesOpen", True)
        qt_app.processEvents()
        view = _child(window, "unnamedFacesView")
        self._click_faces(window, qt_app, face_ids)
        assert view.property("selectedCount") == selected
        return view, face_ids

    def test_the_header_follows_the_cluster_toggle(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        view, face_ids = self._open_unnamed_album(window, qt_app, tmp_path, selected=2)
        label = _child(window, "peoplePanelHeader")

        assert label.property("visible") is True
        assert label.property("text") == "Unnamed people in these photos:"
        assert _child(window, "peoplePanelEmptyText").property("visible") is False

        _click(window, _child(view, "clusterToggleButton"), qt_app)
        # a váltás üríti az arc-kijelölést (onGroupedChanged: clearSelection +
        # reload) — a két arcot valódi kattintással jelöljük ki újra
        self._click_faces(window, qt_app, face_ids)
        qt_app.processEvents()

        assert view.property("grouped") is False
        assert view.property("selectedCount") == 2
        assert label.property("text") == "Unnamed groups of people:"

    def test_outside_the_album_the_header_is_never_the_grouped_one(
        self, qml_app, qt_app, tmp_path
    ):
        """A csoportosítás jelzője (`+0x2af`) csak az albumban áll: máshol
        a többképes ág „van kép" sora a kibontott fejléc (#3566). A három
        kép kijelölése valódi kattintás a rácson."""
        window, controller, _engine = qml_app
        paths = _library_of(window, controller, qt_app, tmp_path, 3)
        _open(window, qt_app)
        _select_photos(window, controller, qt_app, paths)

        assert _child(window, "peoplePanelHeader").property("text") == (
            "Unnamed groups of people:"
        )

    def test_one_selected_face_asks_who(self, qml_app, qt_app, tmp_path):
        """Egy kijelölt arcnál az eredeti egyképes ága fut (9/b, #3566)."""
        window, _controller, _engine = qml_app
        self._open_unnamed_album(window, qt_app, tmp_path, selected=1)

        label = _child(window, "peoplePanelHeader")
        assert label.property("visible") is True
        assert label.property("text") == "Who is in these photos?"


_ANNA_ID = "1111111111111111"
_BELA_ID = "2222222222222222"
# Anna és Béla EGY képen
_KOZOS_INI = (
    "[Contacts2]\n"
    f"{_ANNA_ID}=Anna;;\n"
    f"{_BELA_ID}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID};"
    f"rect64(5000280075006e00),{_BELA_ID}\n"
)

_CECILIA_ID = "3333333333333333"
_SZEMELY_ALBUM_INI = (
    "[Contacts2]\n"
    f"{_ANNA_ID}=Anna;;\n"
    f"{_BELA_ID}=Béla;;\n"
    f"{_CECILIA_ID}=Cecília;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID};"
    f"rect64(5000280075006e00),{_BELA_ID};"
    f"rect64(7000280095006e00),{_CECILIA_ID}\n"
    "[b.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID}\n"
)


def _szemely_album_kepek(window, controller, qt_app, tmp_path):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    lib = tmp_path / "kepek"
    for name in ("a.jpg", "b.jpg"):
        make_jpeg(lib / name, size=(120, 90))
    (lib / ".picasa.ini").write_text(_SZEMELY_ALBUM_INI, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    for _ in range(5):
        qt_app.processEvents()
    _open(window, qt_app)
    controller.showPerson("Anna")
    for _ in range(5):
        qt_app.processEvents()
    return lib


def _lathato_szemelyek(panel):
    return sorted(
        item.objectName().removeprefix("peoplePanelRow_")
        for item in _walk_items(panel)
        if item.objectName().startswith("peoplePanelRow_") and item.isVisible()
    )


def _lathato_szemely_darabszamok(panel):
    return {
        item.objectName().removeprefix("peoplePanelCount_"):
            item.property("text")
        for item in _walk_items(panel)
        if item.objectName().startswith("peoplePanelCount_") and item.isVisible()
    }


class TestPersonAlbumExcludesViewedPerson:
    # rontás-kontroll: szűrés nélkül az Anna-sor is látszik; a csak-Annás
    # képnél pedig a hibás fejléc-ág „Unnamed groups…” feliratot mutat.
    def test_a_photo_with_three_people_shows_only_the_other_two(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = _szemely_album_kepek(window, controller, qt_app, tmp_path)

        _select_photos(window, controller, qt_app, [lib / "a.jpg"])
        panel = _child(window, "peoplePanel")
        # Az eltérő írásmód a kis- és nagybetűt nem érzékeny összevetést is méri.
        panel.setProperty("currentPerson", "aNnA")

        assert _child(window, "peoplePanelHeader").property("text") == (
            "Also in these photos:"
        )
        assert _lathato_szemelyek(panel) == ["Béla", "Cecília"]
        assert _lathato_szemely_darabszamok(panel) == {
            "Béla": "1 photos",
            "Cecília": "1 photos",
        }

    def test_a_photo_with_only_the_viewed_person_shows_text4(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = _szemely_album_kepek(window, controller, qt_app, tmp_path)

        _select_photos(window, controller, qt_app, [lib / "b.jpg"])

        panel = _child(window, "peoplePanel")
        header = _child(window, "peoplePanelHeader")
        empty = _child(window, "peoplePanelEmptyText")
        assert _lathato_szemelyek(panel) == []
        assert header.property("visible") is False
        assert empty.property("visible") is True
        assert empty.property("text") == (
            "Named people who appear with the currently selected person "
            "will be listed here."
        )

    def test_two_selected_photos_count_each_other_person_once(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = _szemely_album_kepek(window, controller, qt_app, tmp_path)

        _select_photos(
            window, controller, qt_app, [lib / "a.jpg", lib / "b.jpg"]
        )

        panel = _child(window, "peoplePanel")
        assert _lathato_szemelyek(panel) == ["Béla", "Cecília"]
        assert _lathato_szemely_darabszamok(panel) == {
            "Béla": "1 photos",
            "Cecília": "1 photos",
        }

    def test_editor_view_keeps_the_viewed_person_in_the_list(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = _szemely_album_kepek(window, controller, qt_app, tmp_path)
        _select_photos(window, controller, qt_app, [lib / "b.jpg"])

        row = controller.photos.rowOfPath(str(lib / "b.jpg"))
        window.setProperty("viewerOpen", True)
        viewer = _child(window, "photoViewer")
        viewer.setProperty("currentIndex", row)
        window.setProperty("activeDrawerTab", "people")
        for _ in range(10):
            qt_app.processEvents()

        panel = _child(window, "viewerPeoplePanel")
        assert _lathato_szemelyek(panel) == ["Anna"]
        assert _lathato_szemely_darabszamok(panel) == {"Anna": "1 photos"}


class TestFromPersonAlbumToUnnamed:
    """#3585 (átnézési lelet): „személy albuma → Névtelenek". A bal hasáb
    Névtelenek-sora nem vált nézetet a controllerben, így a
    `currentPersonName` az előző személyé marad. A Névtelenek albumban ettől
    még a Névtelenek fejléce kell, nem az előző személy „Szintén ezeken a
    fotókon" utasítása (Text4)."""

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
        # előfeltétel: Anna albumában, kijelölés nélkül a Text4 szól
        assert "appear with" in _child(
            window, "peoplePanelEmptyText").property("text")

        self._nevtelenek(window, qt_app, selected=2)

        label = _child(window, "peoplePanelHeader")
        assert label.property("visible") is True
        assert label.property("text") == "Unnamed people in these photos:"
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

    def test_back_to_the_person_album_its_text_returns(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _open(window, qt_app)
        self._anna_albuma(window, controller, qt_app, tmp_path)
        self._nevtelenek(window, qt_app, selected=2)

        window.setProperty("unnamedFacesOpen", False)
        qt_app.processEvents()

        assert _child(window, "peoplePanelHeader").property("visible") is False
        empty = _child(window, "peoplePanelEmptyText")
        assert empty.property("visible") is True
        assert "appear with" in empty.property("text")
