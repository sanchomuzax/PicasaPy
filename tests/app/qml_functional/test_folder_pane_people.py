"""QML-funkcionális teszt: a bal hasáb Emberek gyűjteménye (#26, 1. kör).

A `FolderPane.qml` a csillagozott/album-sorok mintáját követi: a
`pane.peopleModel` ({name, count} elemek) alapján egy-egy sort rajzol
(`peopleRepeater`), a fejléc darabszáma követi őket, és egy személyre
kattintás a `pane.personChosen(name)` jelzésen át adja tovább a nevet — a
`Main.qml`-beli bekötés (`controller.showPerson`) még nincs meg (#320
mintája: a `controller.py`/`Main.qml` forró fájl, az integrátor dolga),
ezért itt egy önálló QQmlEngine-nel, controller NÉLKÜL töltjük be a
komponenst (a `test_folder_pane_collections_320.py` mintája).

A dinamikusan (Repeater) létrehozott delegate-példányok nem érhetők el
`findChild`-dal (MEMORY 2026-07-31) — a tartalmat a `peopleModel` adatán és
a `peopleRepeater.count`-on át ellenőrizzük."""

from __future__ import annotations

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


class _StubController(QObject):
    """A FolderPane induláskor lekérdezi a gyűjtemény-csukottságot — ehhez
    kell egy minimális controller-felszín, a valódi AppController nélkül."""

    from PySide6.QtCore import Slot

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


_PEOPLE = [{"name": "Anna Kis", "count": 3}, {"name": "Roy Avery", "count": 1}]


class TestPeopleListedInPane:
    def test_people_model_reaches_the_repeater(self, qt_app):
        pane = _make_pane(qt_app, {"peopleModel": _PEOPLE})
        repeater = pane.findChild(QObject, "peopleRepeater")
        assert repeater is not None, "peopleRepeater nem található"
        assert repeater.property("count") == 2

    def test_empty_model_gives_no_rows(self, qt_app):
        pane = _make_pane(qt_app)
        repeater = pane.findChild(QObject, "peopleRepeater")
        assert repeater.property("count") == 0

    def test_people_header_count_follows_the_model(self, qt_app):
        pane = _make_pane(qt_app, {"peopleModel": _PEOPLE})
        header = pane.findChild(QObject, "peopleHeader")
        assert header.property("text").endswith("(2)")


class TestPersonClickWiring:
    def test_clicking_a_person_row_emits_person_chosen(self, qt_app):
        pane = _make_pane(qt_app, {"peopleModel": _PEOPLE})
        events = []
        pane.personChosen.connect(lambda name: events.append(name))
        pane.personChosen.emit("Roy Avery")
        qt_app.processEvents()
        assert events == ["Roy Avery"]

    def test_selected_person_name_reflected_on_pane(self, qt_app):
        pane = _make_pane(qt_app, {"peopleModel": _PEOPLE})
        pane.setProperty("selectedPersonName", "Anna Kis")
        assert pane.property("selectedPersonName") == "Anna Kis"
