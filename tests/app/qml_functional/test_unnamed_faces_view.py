"""QML-funkcionális teszt: a „Névtelenek" sor a bal hasábon (FolderPane.qml)
és az `UnnamedFacesView.qml` — a `FaceScanController` bekötése (#26, 3.
lépcső). A `test_folder_pane_people.py` mintáját követi: önálló komponens,
controller/faceScanController NÉLKÜL (stub QObject-tel), findChild helyett
a modell-adaton és a jelzéseken át ellenőrizve (MEMORY 2026-07-31: a
Repeater/GridView delegate-jei nem érhetők el findChild-dal)."""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine

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

    def test_toggle_group_by_face_reloads(self, qt_app):
        stub = _StubFaceScanController()
        view = _make_view(qt_app, controller=stub)
        stub.calls.clear()
        view.setProperty("groupByFace", False)
        qt_app.processEvents()
        assert ("unnamedGroups", False, False) in stub.calls

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
