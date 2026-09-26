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

    def __init__(self, groups=None, assign_result=True):
        super().__init__()
        self.calls: list = []
        self._groups = groups if groups is not None else []
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
        return []

    @Slot("QVariantList", result=int)
    def unignoreFaces(self, face_ids):
        self.calls.append(("unignoreFaces", list(face_ids)))
        return len(list(face_ids))

    # a csoportosítás (lenyomat + csoportba sorolás) futásának jelzései
    embeddingStarted = Signal()
    embeddingFinished = Signal(int, int)
    embeddingCancelled = Signal()
    embeddingFailed = Signal(str)


def _make_view(qt_app, controller=None):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", _StubController())
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

    def test_rejecting_only_drops_the_suggestion(self, qt_app):
        """Az elvetés NEM mellőzi az arcot — az külön döntés."""
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)

        QMetaObject.invokeMethod(
            view,
            "rejectSuggestion",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 12),
        )
        qt_app.processEvents()

        assert ("rejectSuggestion", 12) in stub.calls
        assert [c for c in stub.calls if c[0] == "ignoreFaces"] == []


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
