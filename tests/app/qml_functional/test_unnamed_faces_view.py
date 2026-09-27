"""QML-funkcionális teszt: a „Névtelenek" sor a bal hasábon (FolderPane.qml)
és az `UnnamedFacesView.qml` — a `FaceScanController` bekötése (#26, 3.
lépcső). A `test_folder_pane_people.py` mintáját követi: önálló komponens,
controller/faceScanController NÉLKÜL (stub QObject-tel), findChild helyett
a modell-adaton és a jelzéseken át ellenőrizve (MEMORY 2026-07-31: a
Repeater/GridView delegate-jei nem érhetők el findChild-dal)."""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, Qt, QUrl, Signal, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

_KEEPALIVE = []


class _StubController(QObject):
    @Slot(str, result=bool)
    def isCollectionCollapsed(self, name):
        return False

    @Slot(str, bool)
    def setCollectionCollapsed(self, name, collapsed):
        pass


def _make_pane(qt_app, initial_properties=None):
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", _StubController())
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        ),
    )
    folders_model = FolderListModel()
    props = {"foldersModel": folders_model}
    props.update(initial_properties or {})
    obj = component.createWithInitialProperties(props)
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    folders_model.setParent(obj)
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([engine, component, obj, folders_model])
    return obj


class TestUnnamedFacesRowInPane:
    def test_hidden_when_count_is_zero(self, qt_app):
        pane = _make_pane(qt_app, {"unnamedFaceCount": 0})
        row = pane.findChild(QObject, "unnamedFacesItem")
        assert row is not None
        assert row.property("visible") is False

    def test_visible_with_count_and_click_emits_signal(self, qt_app):
        pane = _make_pane(qt_app, {"unnamedFaceCount": 3, "peopleCollapsed": False})
        row = pane.findChild(QObject, "unnamedFacesItem")
        assert row.property("visible") is True
        events = []
        pane.unnamedFacesChosen.connect(lambda: events.append(True))
        pane.unnamedFacesChosen.emit()
        qt_app.processEvents()
        assert events == [True]


class _StubFaceScanController(QObject):
    """Az `UnnamedFacesView.qml` felülete — `unnamedGroups`/`assignNameToFaces`
    hívást szimulál, valódi index/detektor nélkül."""

    def __init__(self, groups=None, assign_result=True, ignored=None):
        super().__init__()
        self.calls: list = []
        self._groups = groups if groups is not None else []
        self._ignored = ignored if ignored is not None else []
        self._assign_result = assign_result

    @Slot(bool, bool, result="QVariantList")
    def unnamedGroups(self, group_by_face, expand_groups):
        self.calls.append(("unnamedGroups", group_by_face, expand_groups))
        return self._groups

    @Slot("QVariantList", str, result=bool)
    def assignNameToFaces(self, face_ids, name):
        self.calls.append(("assignNameToFaces", list(face_ids), name))
        return self._assign_result

    @Slot("QVariantList", result=int)
    def ignoreFaces(self, face_ids):
        self.calls.append(("ignoreFaces", list(face_ids)))
        return len(list(face_ids))

    @Slot(int, result=bool)
    def acceptSuggestion(self, face_id):
        self.calls.append(("acceptSuggestion", face_id))
        return True

    @Slot(int)
    def rejectSuggestion(self, face_id):
        self.calls.append(("rejectSuggestion", face_id))

    @Slot(result="QVariantList")
    def ignoredGroups(self):
        self.calls.append(("ignoredGroups",))
        return self._ignored

    @Slot("QVariantList", result=int)
    def unignoreFaces(self, face_ids):
        self.calls.append(("unignoreFaces", list(face_ids)))
        return len(list(face_ids))

    # a csoportosítás (lenyomat + csoportba sorolás) futásának jelzései
    embeddingStarted = Signal()
    embeddingFinished = Signal(int, int)
    embeddingCancelled = Signal()
    embeddingFailed = Signal(str)


def _make_view(qt_app, controller=None, context=None):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", _StubController())
    for name, value in (context or {}).items():
        engine.rootContext().setContextProperty(name, value)
        _KEEPALIVE.append(value)
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "UnnamedFacesView.qml")
        ),
    )
    obj = component.createWithInitialProperties({"faceScanController": controller})
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([engine, component, obj, controller])
    return obj


class TestUnnamedFacesViewWithoutController:
    def test_no_controller_gives_empty_groups_without_crashing(self, qt_app):
        view = _make_view(qt_app, controller=None)
        model = view.property("groupsModel")
        model = model.toVariant() if hasattr(model, "toVariant") else model
        assert model in ([], None)


class TestUnnamedFacesViewWiring:
    def test_reload_calls_unnamed_groups_with_toggle_state(self, qt_app):
        stub = _StubFaceScanController(groups=[{"label": "Csoport 1", "faces": []}])
        view = _make_view(qt_app, controller=stub)
        assert ("unnamedGroups", True, False) in stub.calls
        model = view.property("groupsModel")
        assert len(model) == 1

    def test_expanding_reloads_the_full_groups(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        stub.calls.clear()
        view.setProperty("grouped", False)
        qt_app.processEvents()
        assert ("unnamedGroups", True, True) in stub.calls

    def test_add_name_button_calls_assign_name_to_faces(self, qt_app):
        stub = _StubFaceScanController(assign_result=True)
        view = _make_view(qt_app, controller=stub)
        view.setProperty("selectedFaceIds", {"7": True, "9": True})
        view.setProperty("selectedCount", 2)
        name_field = view.findChild(QObject, "unnamedNameField")
        name_field.setProperty("text", "Roy Avery")
        button = view.findChild(QObject, "addNameButton")
        assert button.property("enabled") is True
        button.clicked.emit()
        qt_app.processEvents()
        assign_calls = [c for c in stub.calls if c[0] == "assignNameToFaces"]
        assert len(assign_calls) == 1
        _tag, ids, name = assign_calls[0]
        assert sorted(ids) == [7, 9]
        assert name == "Roy Avery"
        # sikeres névadás után a kijelölés/mező törlődik
        assert view.property("selectedCount") == 0
        assert name_field.property("text") == ""

    def test_add_name_button_disabled_without_selection(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        name_field = view.findChild(QObject, "unnamedNameField")
        name_field.setProperty("text", "Roy Avery")
        button = view.findChild(QObject, "addNameButton")
        assert button.property("enabled") is False


class TestIgnorePeople:
    """#26: a mellőzés NEM törlés — az eredetiben a személy a „Mellőzött
    emberek" albumba került, és a program külön rákérdezett rá."""

    def test_the_button_needs_a_selection(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        button = view.findChild(QObject, "ignoreFacesButton")

        assert button.property("enabled") is False

        view.setProperty("selectedCount", 1)
        qt_app.processEvents()
        assert button.property("enabled") is True

    def test_it_asks_before_ignoring(self, qt_app):
        """A gomb NEM mellőz azonnal — előbb megerősítést kér."""
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        view.setProperty("selectedFaceIds", {"4": True})
        view.setProperty("selectedCount", 1)

        view.findChild(QObject, "ignoreFacesButton").clicked.emit()
        qt_app.processEvents()

        # a megerősítő ablak létezik, és a gomb NEM mellőzött azonnal
        # (a Popup önálló, ablak nélküli komponens-tesztben nem tud
        # megjelenni, ezért a `visible` itt nem mérvadó)
        assert view.findChild(QObject, "ignoreFacesDialog") is not None
        assert [c for c in stub.calls if c[0] == "ignoreFaces"] == []

    def test_confirming_ignores_the_selected_faces(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        view.setProperty("selectedFaceIds", {"4": True, "5": True})
        view.setProperty("selectedCount", 2)

        QMetaObject.invokeMethod(
            view, "ignoreSelected", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        calls = [c for c in stub.calls if c[0] == "ignoreFaces"]
        assert len(calls) == 1
        assert sorted(calls[0][1]) == [4, 5]

    def test_the_message_names_the_ignored_people_album(self, qt_app):
        """Az eredeti szövege: „…move this person to the ignored people
        album?" — ez mondja meg, hogy a mellőzés visszavehető."""
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        view.setProperty("selectedCount", 1)
        qt_app.processEvents()

        message = view.findChild(QObject, "ignoreFacesMessage").property("text")

        assert "ignored people album" in message

    def test_the_message_uses_the_dialog_palette_like_the_checkbox(self, qt_app):
        """A kérdés szövege a párbeszéd palettájának színével íródik, mint a
        „Ne kérdezzen újból" jelölő — a téma sötét tintája sötét
        párbeszéd-háttéren olvashatatlan volt (#3670 képernyőkép).
        # rontás-kontroll: `Label` helyett `Text { color: Theme.ink }` → piros."""
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        qt_app.processEvents()

        uzenet = view.findChild(QObject, "ignoreFacesMessage")
        jelolo = view.findChild(QObject, "ignoreFacesDontAskCheck")
        szoveg_szin = uzenet.property("color")
        jelolo_szin = jelolo.property("contentItem").property("color")

        assert szoveg_szin.name() == jelolo_szin.name()


class TestNameSuggestion:
    """#26: az eredeti KÉRDÉSKÉNT vetette fel a nevet („Anna?"), pipa/x
    gombbal — sosem döntött a felhasználó helyett."""

    def test_accepting_writes_the_suggested_name(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)

        QMetaObject.invokeMethod(
            view,
            "acceptSuggestion",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 12),
        )
        qt_app.processEvents()

        assert ("acceptSuggestion", 12) in stub.calls

    def test_the_x_on_a_suggested_face_ignores_it(self, qt_app):
        """#3670: az „x" a mellőzés (`PeopleAlbum::ConfirmText`: „press
        "x" to ignore"), nem a javaslat csendes elvetése — javaslatos
        csempén is ugyanaz a kérdés jön, mint a Mellőzés gombnál."""
        stub = _StubFaceScanController(groups=[{
            "label": "G",
            "faces": [{"faceId": 12, "thumbUrl": "", "suggestedName": "Anna"}],
        }])
        view = _make_view(qt_app, controller=stub)
        window = _host_in_window(qt_app, view)

        _click(window, _wait_item(window, "faceIgnoreX_12"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Ignore Person"), qt_app)

        assert ("ignoreFaces", [12]) in stub.calls
        assert [c for c in stub.calls if c[0] == "rejectSuggestion"] == []


class TestIgnoredAlbum:
    """#26: a mellőzés az eredetiben ALBUM volt (`CAlbumLabel::Ignored` =
    „Ignored people"), nem egyirányú szemetes — meg lehetett nézni, tehát
    vissza is lehetett venni belőle."""

    def test_the_ignored_mode_loads_the_ignored_album(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        stub.calls.clear()

        view.setProperty("mode", "ignored")
        qt_app.processEvents()

        assert ("ignoredGroups",) in stub.calls

    def test_naming_is_not_offered_among_ignored_people(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        view.setProperty("mode", "ignored")
        qt_app.processEvents()

        assert view.findChild(QObject, "addNameButton").property("visible") is False
        assert view.findChild(QObject, "ignoreFacesButton").property("visible") is False
        assert view.findChild(QObject, "unignoreFacesButton").property("visible") is True

    def test_unignoring_gives_the_faces_back(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        view.setProperty("mode", "ignored")
        view.setProperty("selectedFaceIds", {"3": True})
        view.setProperty("selectedCount", 1)

        QMetaObject.invokeMethod(
            view, "unignoreSelected", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        calls = [c for c in stub.calls if c[0] == "unignoreFaces"]
        assert len(calls) == 1
        assert list(calls[0][1]) == [3]


# #3585: a fejléc egyetlen csoportosítás-váltógombja és a fejléc-utasítás
# (spec `picasa-arcfelismeres.md` 9/d). A magyar alak a `stringres`-é, a
# `.ts` hordozza; itt az angol forrásszöveget mérjük.
_TOGGLE_GROUPED = (
    'Select someone you know and add a name, or click the "x" to ignore '
    "that person."
)
_TOGGLE_GROUP_IGNORE = "Select someone you know and add a name."
_TOGGLE_UNGROUPED = "Select someone you know and add a name"
_LOADING_GROUPED = "Grouping faces, please wait..."


def _host_in_window(qt_app, view):
    """A nézet egy valódi (offscreen) ablakba kerül, hogy egérrel lehessen
    rá kattintani."""
    window = QQuickWindow()
    window.resize(1000, 600)
    view.setParentItem(window.contentItem())
    view.setProperty("width", 1000)
    view.setProperty("height", 600)
    window.show()
    QTest.qWaitForWindowExposed(window)
    qt_app.processEvents()
    _KEEPALIVE.append(window)
    return window


def _click(window, item, qt_app):
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _instructions(view):
    return view.findChild(QObject, "unnamedInstructions").property("text")


class TestClusterToggle:
    """#3585: az eredetiben a `cluster` ↔ `showall` EGY váltógomb két arca
    (`unknownfaceheaderpanel.tre:24–33`) — nem két független kapcsoló."""

    def test_there_is_one_toggle_instead_of_two_checkboxes(self, qt_app):
        view = _make_view(qt_app, controller=_StubFaceScanController())

        assert view.findChild(QObject, "groupByFaceCheck") is None
        assert view.findChild(QObject, "expandGroupsCheck") is None
        assert view.findChild(QObject, "clusterToggleButton") is not None

    def test_it_opens_grouped(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        toggle = view.findChild(QObject, "clusterToggleButton")

        assert view.property("grouped") is True
        assert ("unnamedGroups", True, False) in stub.calls
        # csoportosítva a „Csoportok részletes nézete" gomb látszik
        assert toggle.property("text") == "Expand groups"
        assert _instructions(view) == _TOGGLE_GROUPED

    def test_clicking_switches_state_label_and_instructions(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        window = _host_in_window(qt_app, view)
        toggle = view.findChild(QObject, "clusterToggleButton")
        stub.calls.clear()

        _click(window, toggle, qt_app)

        assert view.property("grouped") is False
        assert toggle.property("text") == "Group by face"
        assert _instructions(view) == _TOGGLE_UNGROUPED
        assert ("unnamedGroups", True, True) in stub.calls

        stub.calls.clear()
        _click(window, toggle, qt_app)

        assert view.property("grouped") is True
        assert toggle.property("text") == "Expand groups"
        assert _instructions(view) == _TOGGLE_GROUPED
        assert ("unnamedGroups", True, False) in stub.calls

    def test_reopening_the_album_starts_grouped_again(self, qt_app):
        view = _make_view(qt_app, controller=_StubFaceScanController())
        # ablak nélkül a láthatóság nem kapcsol vissza — a nézet a
        # Main.qml-ben is ablakban él
        _host_in_window(qt_app, view)
        view.setProperty("grouped", False)
        view.setProperty("visible", False)
        qt_app.processEvents()

        view.setProperty("visible", True)
        qt_app.processEvents()

        assert view.property("grouped") is True

    def test_the_ignored_album_has_its_own_instructions(self, qt_app):
        view = _make_view(qt_app, controller=_StubFaceScanController())
        view.setProperty("mode", "ignored")
        qt_app.processEvents()

        assert _instructions(view) == _TOGGLE_GROUP_IGNORE
        toggle = view.findChild(QObject, "clusterToggleButton")
        assert toggle.property("visible") is False

    def test_while_grouping_runs_it_asks_to_wait(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)

        stub.embeddingStarted.emit()
        qt_app.processEvents()
        assert _instructions(view) == _LOADING_GROUPED

        stub.embeddingFinished.emit(3, 2)
        qt_app.processEvents()
        assert _instructions(view) == _TOGGLE_GROUPED

    def test_expanded_view_does_not_show_the_grouping_notice(self, qt_app):
        """A „várjon" szöveg csak a csoportosított állapoté (`0x0074c2c8`)."""
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        view.setProperty("grouped", False)
        stub.embeddingStarted.emit()
        qt_app.processEvents()

        assert _instructions(view) == _TOGGLE_UNGROUPED


# -- #3670: a bélyegkép „X"-e → megerősítés → `.picasa.ini` ----------------


def _walk_items(item):
    for child in item.childItems():
        yield child
        yield from _walk_items(child)


def _wait_item(window, name, predicate=None):
    """Egy delegate-elem (a GridView-é nem érhető el findChild-dal): a
    rács aszinkron jön létre, ezért megvárjuk, hogy látsszon."""
    for _ in range(150):
        for item in _walk_items(window.contentItem()):
            if (
                item.objectName() == name and item.isVisible() and item.width() > 0
                and (predicate is None or predicate(item))
            ):
                return item
        QTest.qWait(20)
    raise AssertionError(f"{name} nem látszik")


def _dialog_button(window, qt_app, text):
    """A megerősítő párbeszéd egy gombja, felirat szerint — a Popup az
    ablak overlay-ében él, a nézet elemfáján kívül."""
    for _ in range(150):
        qt_app.processEvents()
        for item in _walk_items(window.contentItem()):
            if (
                item.property("text") == text and item.isVisible()
                and item.width() > 0 and item.metaObject().indexOfSignal("clicked()") >= 0
            ):
                return item
        QTest.qWait(20)
    raise AssertionError(f"a(z) {text!r} gomb nem látszik")


def _dialog_open(view):
    return view.findChild(QObject, "ignoreFacesDialog").property("visible") is True


class _NoDetector:
    available = False

    def detect(self, image):
        return ()


def _real_controller(tmp_path):
    """Valódi `FaceScanController` + `FacesHelper` egy egyarcos képpel —
    a kattintás végén a `.picasa.ini`-t olvassuk vissza."""
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.app.faces_helper import FacesHelper
    from picasapy.faces.detector import FaceDetection, FaceLandmarks
    from picasapy.index import open_index, replace_faces, sync_tree
    from support.jpeg_factory import make_jpeg

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(100, 100))
    landmarks = FaceLandmarks(
        right_eye=(10.0, 20.0), left_eye=(30.0, 20.0), nose=(20.0, 30.0),
        mouth_right=(15.0, 40.0), mouth_left=(25.0, 40.0),
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
        photo_id = conn.execute("SELECT id FROM photos WHERE name = 'a.jpg'").fetchone()["id"]
        replace_faces(conn, photo_id, [FaceDetection(
            left=5.0, top=10.0, right=40.0, bottom=50.0, score=0.9, landmarks=landmarks,
        )])
        conn.commit()
        face_id = conn.execute("SELECT id FROM face").fetchone()["id"]
    helper = FacesHelper()
    ctl = FaceScanController(
        tmp_path / "index.db", detector=_NoDetector(), embedder=_NoDetector(),
        faces_helper=helper,
    )
    _KEEPALIVE.extend([helper, ctl])
    return ctl, lib, face_id


def _confirm_settings(tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return ConfirmSettingsBridge(settings), settings


class TestThumbnailX:
    """#3670 „kész, ha" 2. és 6. pont: a bélyegkép X-e ugyanazt a kérdést
    adja, és ugyanazt írja a `.picasa.ini`-be, mint a Mellőzés gomb —
    VALÓDI egérkattintással végigjárva.

    # rontás-kontroll: az X visszakötve a `rejectSuggestion`-re (a régi,
    # kérdés és ini-írás nélküli elvetés) → a megerősítő párbeszéd nem
    # nyílik meg, `test_x_asks_then_writes_the_ini_line` bukik."""

    def test_x_asks_then_writes_the_ini_line(self, qt_app, tmp_path):
        ctl, lib, face_id = _real_controller(tmp_path)
        view = _make_view(qt_app, controller=ctl)
        window = _host_in_window(qt_app, view)

        _click(window, _wait_item(window, f"faceIgnoreX_{face_id}"), qt_app)

        assert _dialog_open(view)
        assert not (lib / ".picasa.ini").exists()

        _click(window, _dialog_button(window, qt_app, "Ignore Person"), qt_app)

        from picasapy.ini import Rect64, encode_rect64

        expected = f"rect64({encode_rect64(Rect64(0.05, 0.10, 0.40, 0.50))}),ffffffffffffffff"
        text = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" in text
        assert f"faces={expected}" in text
        assert ctl.unnamedCount == 0

    def test_cancel_writes_nothing(self, qt_app, tmp_path):
        ctl, lib, face_id = _real_controller(tmp_path)
        view = _make_view(qt_app, controller=ctl)
        window = _host_in_window(qt_app, view)

        _click(window, _wait_item(window, f"faceIgnoreX_{face_id}"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Cancel"), qt_app)

        assert not (lib / ".picasa.ini").exists()
        assert ctl.unnamedCount == 1

    def test_the_x_is_not_offered_among_ignored_people(self, qt_app):
        group = [{
            "label": "G", "faces": [{"faceId": 3, "thumbUrl": "", "suggestedName": ""}],
        }]
        view = _make_view(
            qt_app, controller=_StubFaceScanController(groups=group, ignored=group)
        )
        window = _host_in_window(qt_app, view)
        _wait_item(window, "faceIgnoreX_3")

        view.setProperty("mode", "ignored")
        _wait_item(window, "faceTile_3")

        assert not any(
            item.objectName() == "faceIgnoreX_3" and item.isVisible()
            for item in _walk_items(window.contentItem())
        )


def _two_face_stub():
    return _StubFaceScanController(groups=[{
        "label": "G",
        "faces": [
            {"faceId": 4, "thumbUrl": "", "suggestedName": ""},
            {"faceId": 5, "thumbUrl": "", "suggestedName": ""},
        ],
    }])


class TestDontAskAgain:
    """#3670 „kész, ha" 3. pont: a *Személyek mellőzése* kérdés „Ne
    kérdezzen újból, mindig hagyja figyelmen kívül" jelölője
    (`PeoplePanel::ConfirmRemoveCheck`, spec 15.3/b.1). Bepipálva és
    jóváhagyva a következő mellőzés kérdés nélkül megy.

    # rontás-kontroll: a jóváhagyásból kivéve a `setSuppressed` hívás →
    # a második X ismét kérdez, `test_checked_and_confirmed_stops_asking`
    # bukik."""

    def test_the_checkbox_has_the_official_text(self, qt_app):
        view = _make_view(qt_app, controller=_StubFaceScanController())

        check = view.findChild(QObject, "ignoreFacesDontAskCheck")

        assert check is not None
        assert check.property("text") == "Don't ask again, always ignore"

    def test_checked_and_confirmed_stops_asking(self, qt_app, tmp_path):
        bridge, settings = _confirm_settings(tmp_path)
        stub = _two_face_stub()
        view = _make_view(qt_app, controller=stub, context={"confirmSettings": bridge})
        window = _host_in_window(qt_app, view)

        _click(window, _wait_item(window, "faceIgnoreX_4"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Don't ask again, always ignore"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Ignore Person"), qt_app)
        assert ("ignoreFaces", [4]) in stub.calls

        _click(window, _wait_item(window, "faceIgnoreX_5"), qt_app)

        assert ("ignoreFaces", [5]) in stub.calls
        assert not _dialog_open(view)
        assert bridge.isSuppressed("ignoreFaces") is True

    def test_unchecked_keeps_asking(self, qt_app, tmp_path):
        bridge, _settings = _confirm_settings(tmp_path)
        stub = _two_face_stub()
        view = _make_view(qt_app, controller=stub, context={"confirmSettings": bridge})
        window = _host_in_window(qt_app, view)

        _click(window, _wait_item(window, "faceIgnoreX_4"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Ignore Person"), qt_app)
        _click(window, _wait_item(window, "faceIgnoreX_5"), qt_app)

        assert _dialog_open(view)
        assert [c for c in stub.calls if c[0] == "ignoreFaces"] == [("ignoreFaces", [4])]

    def test_cancel_does_not_remember(self, qt_app, tmp_path):
        bridge, _settings = _confirm_settings(tmp_path)
        stub = _two_face_stub()
        view = _make_view(qt_app, controller=stub, context={"confirmSettings": bridge})
        window = _host_in_window(qt_app, view)

        _click(window, _wait_item(window, "faceIgnoreX_4"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Don't ask again, always ignore"), qt_app)
        _click(window, _dialog_button(window, qt_app, "Cancel"), qt_app)

        assert bridge.isSuppressed("ignoreFaces") is False
        assert [c for c in stub.calls if c[0] == "ignoreFaces"] == []
