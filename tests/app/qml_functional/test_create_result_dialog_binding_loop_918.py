"""A `createResultDialog` kötési huroktól mentes legyen — #918.

## A lelet

A `python picasapy` indításakor a napló kétszer írta:

```
CreateDialogs.qml:275:5: QML Dialog: Binding loop detected for property
"implicitWidth"
```

A 275. sor a `createResultDialog` — a „Létrehozás" befejezését visszajelző
ablak. Az ok: a dialógus egyetlen gyereke egy csupasz `Text`, ami egyszerre
kapott `wrapMode: Text.WordWrap`-ot és fix `width: 360`-at. Egyetlen gyerek
esetén a `Dialog` ezt teszi meg `contentItem`-nek, és az `implicitWidth`-jét
a tartalom `implicitWidth`-jéből számolja — a tördelő `Text`
`implicitWidth`-je viszont a saját szélességétől függ, amit a `Dialog`
állítana be. Innen a kör.

## Mit őriz ez a fájl

1. A `qInstallMessageHandler`-t elkapva ténylegesen NEM jelenik-e meg
   „Binding loop detected" üzenet — sem a dialógusok LÉTREHOZÁSAKOR (ahogy
   az eredeti hiba is startupkor jelentkezett), sem egy HOSSZÚ eredmény-
   üzenet megjelenítésekor.
2. Kirajzolt ellenőrzés (a PROTOKOLL 1. pontja szerint — a property-olvasás
   itt nem elég): hosszú üzenettel a szöveg tényleg TÖRDELVE, korlátos
   szélességben jelenik meg, nem nyújtja szét a dialógust.

A `CreateDialogs` a `PicasaPy 1.0` modul regisztrált típusa (ld.
`src/picasapy/app/qml/PicasaPy/qmldir`), ezért közvetlenül példányosítható —
nem kell hozzá a teljes `Main.qml`-t vagy a valódi controllereket betölteni.
Az `appWindow` kötelező property-hez egy minimális, kézzel írt stub elég,
mert a `createResultDialog` a `controller`-jelzésekre (`onCollageFinished`
stb.) reagál, amiket itt közvetlenül állítunk elő a `message` property és az
`open()` hívásán keresztül.
"""

from __future__ import annotations

import time

from PySide6.QtCore import (
    Property,
    QObject,
    QUrl,
    Signal,
    Slot,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView

_KEEPALIVE: list[object] = []


class _ControllerStub(QObject):
    """Annyi az `AppController`-ből, amennyi a `CreateDialogs.qml`
    közvetlen (nem `typeof`-őrzött) `controller`-hivatkozásaihoz kell.

    A `Connections { target: controller }` a fájl `_MOZOG` bekötve
    marad — ha `controller` context property nincs beállítva, a bare
    azonosító `ReferenceError`-t dob, amit a projekt saját `qml_warnings`
    őre (#305/#718) VALÓDI QML-szkripthibaként buktatna el, holott itt
    csak a teszt-környezet hiányos stubja lenne az ok."""

    collageFinished = Signal(str, int, int, int)
    collageFailed = Signal(str)
    movieProgress = Signal(int, int)
    movieFinished = Signal(str, int, int, int)
    movieFailed = Signal(str)

    @Property(int, constant=True)
    def heldCount(self):
        return 0

    # A `collageDialog`/`movieDialog` `ComboBox`-ai `onCurrentIndexChanged`
    # kötéssel hívják ezeket — MÁR a `CreateDialogs` LÉTREHOZÁSAKOR is,
    # hiszen a `currentIndex` a kezdeti -1-ről 0-ra vált. Enélkül a stub
    # nélkül `TypeError: … is not a function` jönne, amit a projekt saját
    # `qml_warnings` őre (#305/#718) valódi QML-hibaként buktatna.
    @Slot("QVariant", str, str)
    def requestCollagePreview(self, indexes, kind, border):
        pass

    @Slot("QVariant", str, str, str)
    def makeCollage(self, indexes, kind, target, border):
        pass

    @Slot()
    def shuffleCollage(self):
        pass

    @Slot("QVariant", str, int, float)
    def exportMovie(self, indexes, target, height, seconds):
        pass


def _wait_for(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő).

    A `Dialog` megnyitása után az elrendezés NEM azonnal fut le: egyetlen
    `processEvents()` után a tördelő `Text` még az egysoros állapotában van.
    Valódi kijelzőn ez véletlenül gyorsabb, fejnélküli (offscreen) CI-ben
    viszont nem — a #918 első köre pontosan ezen bukott el mindkét CI-lábon
    (a magasság 12–14 px maradt, azaz egyetlen sor).
    """
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.01)
    return feltetel()


def _view(qt_app, qml: str, width: int = 800, height: int = 600):
    """A `CreateDialogs` valódi ablakban, a `PicasaPy` modul feloldva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    stub = _ControllerStub()
    view.engine().rootContext().setContextProperty("controller", stub)

    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    _KEEPALIVE.extend((view, root, component, stub))
    view.show()
    qt_app.processEvents()
    return view, root


#: minimális `appWindow`-stub — a `CreateDialogs.qml` csak a
#: `selectedIndexes` hosszát olvassa belőle, a `createResultDialog`-hoz
#: pedig egyáltalán nem kell
_QML = """
import QtQuick
import PicasaPy 1.0
Item {
    id: root
    width: 800
    height: 600
    QtObject {
        id: fakeAppWindow
        property var selectedIndexes: []
        property int selectedIndex: -1
    }
    CreateDialogs {
        id: dialogs
        objectName: "dialogs"
        anchors.fill: parent
        appWindow: fakeAppWindow
    }
}
"""


class _MessageCapture:
    """`qInstallMessageHandler`-figyelő — az ÖSSZES Qt-üzenetet gyűjti,
    hogy a `Binding loop detected` mintára rá lehessen kérdezni."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self._previous = None

    def __enter__(self) -> "_MessageCapture":
        def handler(msg_type, context, message):  # noqa: ARG001 - Qt-aláírás
            self.messages.append(message)

        self._previous = qInstallMessageHandler(handler)
        return self

    def __exit__(self, *exc_info: object) -> None:
        qInstallMessageHandler(self._previous)

    @property
    def binding_loops(self) -> list[str]:
        return [m for m in self.messages if "Binding loop detected" in m]


#: hosszú, több mondatos eredmény-üzenet — a #459/3 „nem található" mondata
#: ismételve, hogy biztosan több sort igényeljen bármilyen tördelt
#: szélesség mellett
_LONG_MESSAGE = (
    "Collage saved: /home/felhasznalo/nagyon/hosszu/utvonal/amit/a/"
    "kollazs/celjaul/valasztott/kep.jpg\n"
    "12 pictures used.\n"
    "3 picture(s) could not be found and will not be shown. "
    "(The missing files must have been moved, renamed or deleted)"
)


class TestCreateResultDialogHasNoBindingLoop:
    """#918: a kötési hurok NE jelenjen meg — sem létrehozáskor, sem
    hosszú üzenet megjelenítésekor."""

    def test_no_binding_loop_when_the_dialogs_are_created(self, qt_app):
        with _MessageCapture() as capture:
            _view(qt_app, _QML)

        assert not capture.binding_loops, (
            "kötési hurkot jelzett a Qt a CreateDialogs.qml betöltésekor "
            "(#918) — a napló minden induláskor teleírná magát:\n"
            + "\n".join(capture.binding_loops)
        )

    def test_no_binding_loop_when_a_long_result_message_is_shown(self, qt_app):
        view, root = _view(qt_app, _QML)
        dialog = root.findChild(QObject, "createResultDialog")
        assert dialog is not None, "createResultDialog nem található"

        with _MessageCapture() as capture:
            dialog.setProperty("message", _LONG_MESSAGE)
            dialog.metaObject().invokeMethod(dialog, "open")
            view.contentItem().update()
            qt_app.processEvents()

        assert not capture.binding_loops, (
            "kötési hurkot jelzett a Qt egy HOSSZÚ eredmény-üzenet "
            "megnyitásakor (#918):\n" + "\n".join(capture.binding_loops)
        )


class TestCreateResultDialogRendersALongMessageSensibly:
    """A jegy #459/3 mondatát nevezi meg: hosszú szöveggel is tördelve,
    korlátos szélességben kell megjelennie — kirajzolt ellenőrzés, nem
    property-olvasás (PROTOKOLL 1. pont)."""

    def test_the_text_wraps_within_a_bounded_width(self, qt_app):
        view, root = _view(qt_app, _QML)
        dialog = root.findChild(QObject, "createResultDialog")
        text_item = root.findChild(QQuickItem, "createResultText")
        assert dialog is not None and text_item is not None

        dialog.setProperty("message", _LONG_MESSAGE)
        dialog.metaObject().invokeMethod(dialog, "open")
        # az elrendezést KI KELL VÁRNI — ld. `_wait_for` docstringje
        _wait_for(qt_app, lambda: (text_item.property("lineCount") or 0) > 1)

        width = text_item.width()
        assert 0 < width <= 400, (
            f"a szöveg kirajzolt szélessége {width:.0f} px — nem korlátos, "
            "tördelt sávban jelenik meg (#918)"
        )
        # A tördelés bizonyítéka a SOROK SZÁMA, nem a képpont-magasság: a
        # betűméret platformfüggő (a #918 első köre 14 px-t mért Linuxon és
        # 12-t Windowson), ezért a beégetett px-küszöb önmagában is hibás
        # mérce volt. A `lineCount` közvetlenül azt mondja ki, amit a teszt
        # állítani akar: több sorba került-e a szöveg.
        sorok = text_item.property("lineCount")
        assert sorok is not None and sorok > 1, (
            f"a szöveg {sorok} sorba került — nem tördelt, hanem egyetlen "
            f"(túl széles) sorba (szélesség: {width:.0f} px) (#918)"
        )
