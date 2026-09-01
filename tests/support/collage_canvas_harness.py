"""Közös kiszolgáló a #947 vászon-tesztjeihez — fixture-ök és egérjáték.

A #947 két tesztfájlra bomlik (`test_collage_canvas_947.py` és
`test_collage_drag_947.py`), mert a `scripts/run_tests.py` FÁJLONKÉNT külön
processzt indít (#155): egy 900 soros fájl egy processzben túl sok
QML-engine-életciklust tartana. Ami MINDKETTŐNEK kell — a vezérlő-fixture,
a kirajzolt panel, a vizuális fa bejárása és a módosítós egéresemény —, az
itt él, egyetlen példányban.

⚠️ A `QTest.mouseMove` NEM vesz át módosítót. A „a módosítót a húzás KÖZBEN
kell kérdezni" szabály (spec 7.4) ezért csak saját `QMouseEvent`-tel
mérhető — az `_eger_mozog()` pontosan ezért létezik.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import (
    QDeadlineTimer,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QSettings,
    Qt,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg

_KEEPALIVE: list[object] = []

#: A vászon-teszt ablakmérete. Nagyobb a tervezővászonnál, hogy a lapon a
#: 132 képpontos gyűrű és a csomópontok kényelmesen elférjenek.
ABLAK = (1280, 800)

#: A lap belső szélessége egységben (spec 6.1) — ugyanaz a szám, amit a
#: `collage_model.SHEET_UNITS` és a `.cxf` is tart.
LAPEGYSEG = 1024.0

#: A gyűrű mérete KÉPERNYŐ-egységben (spec 7.2, `respack` `#ring`).
GYURU = 132


@dataclass
class _Photo:
    """A `PhotoRecord` azon mezői, amiket a kollázs-panel használ.

    #1276: a `id`/`rotate_steps`/`filters`/`mtime_ns`/`size` a KÉPTÁLCA
    miatt került ide — a `TrayMixin.trayItems` a `models._thumb_url`-t
    hívja, az pedig ezt az öt mezőt olvassa.
    """

    folder_path: str
    name: str
    caption: str | None = None
    width: int | None = 400
    height: int | None = 300
    id: int = 0
    rotate_steps: int = 0
    filters: str | None = None
    mtime_ns: int = 0
    size: int = 0


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)

    def idAt(self, row: int):
        """A `TrayMixin` rács-sorból azonosítót képez (`_tray_ids_of_rows`)."""
        if 0 <= row < len(self.photos):
            return self.photos[row].id
        return 0


# --- A két fixture TÖRZSE ----------------------------------------------------
#
# A fixture-öket szándékosan nem `@pytest.fixture`-ként adjuk ki: a
# `from … import controller` és a `def test_x(controller)` paraméter együtt
# F811-et (újradefiniálás) jelent a ruffnak minden egyes tesztfüggvénynél.
# A két tesztfájl ezért maga deklarálja a fixture-t, és ide delegál — így a
# LOGIKA marad egy példányban, a fixture-név pedig ott születik, ahol
# használják.


def keszits_kepeket(tmp_path):
    """Három JPEG egy `kepek` almappában — a kollázs bemenete."""
    root = tmp_path / "kepek"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


def nyitott_vezerlo(tmp_path, library):
    """Az IGAZI `CollageMixin` minimális hoston (a #943-as teszt mintája).

    Generátor: a hívó fixture `yield from`-mal veszi át, hogy a záró
    ellenőrzés — a kollázs-szál leállt-e — a teszt UTÁN fusson le."""
    from PySide6.QtCore import QObject

    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin
    from picasapy.app.tray_controller import TrayMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "kimenet"))

    # #1276: a `TrayMixin` azért került ide, mert a Kollázs-panel „Klipek"
    # lapja MOSTANTÓL a képtálca fel nem használt részét listázza, nem a
    # kollázs saját csomópontjait. Tálca nélküli hoston a lap üres lenne, és
    # a lap tesztjei nem mérnének semmit.
    class _Host(TrayMixin, CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma", 400, 300, id=101),
                    _Photo(str(library), "b.jpg", "Barack", 300, 400, id=102),
                    _Photo(str(library), "c.jpg", "Cseresznye", 200, 200, id=103),
                ]
            )

        def _get_settings(self):
            return self._settings

    instance = _Host()
    instance.openCollage([0, 1, 2])
    # A három kép RÖGZÍTVE a tálcán, felhasználatlanul — ez a Klipek lap
    # bemenete. (A `holdRows` rács-sorokat vár, ld. `_Photos.idAt`.)
    instance.holdRows([0, 1, 2])
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _panel(controller, width=ABLAK[0], height=ABLAK[1]):
    """A Kollázs-panel valódi, kirajzolt ablakban, a vezérlőre kötve."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(
        b"import QtQuick\nimport PicasaPy 1.0\nCollagePanel {}\n", QUrl()
    )
    assert [e.toString() for e in component.errors()] == []
    root = component.create()
    assert root is not None
    root.setProperty("controller", controller)
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    view.show()
    assert _var_a_megjelenesre(view), "az ablak nem jelent meg"
    _KEEPALIVE.extend((view, root, component))
    root.setProperty("_view", view)
    return root


def _var_a_megjelenesre(view, ezredmasodperc: int = 5000) -> bool:
    """Megvárja az ablak megjelenését — SAJÁT eseményhurokkal.

    ⚠️ SZÁNDÉKOSAN nem `QTest.qWaitForWindowExposed`. Az valódi GPU-s
    háttéren, szálas rajzoló hurokkal **holtpontra fut**, ha a jelenetben
    réteg (`layer.enabled`) van — és a #1016 óta a kollázs minden
    csomópontja ilyen. Offscreen (CI, `tests/app/conftest.py`) nincs
    holtpont, tehát a hiba csak valódi kijelzőn jelentkezne: a fejlesztő
    gépén néma befagyásként, ok nélkül. Mérve ezen a gépen: réteg nélkül
    lefut, réteggel soha nem tér vissza; ez az eseményhurok mindkettővel jó.
    """
    hurok = QEventLoop()
    hatarido = QDeadlineTimer(ezredmasodperc)
    idozito = QTimer()
    idozito.setInterval(20)

    def figyel():
        if view.isExposed() or hatarido.hasExpired():
            hurok.quit()

    idozito.timeout.connect(figyel)
    idozito.start()
    hurok.exec()
    idozito.stop()
    return view.isExposed()


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemeit a `findChild` NEM látja."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _child(root: QQuickItem, name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    raise AssertionError(f"{name} nem található a kirajzolt fában")


def _van(root: QQuickItem, name: str) -> bool:
    return any(item.objectName() == name for item in _walk(root))


def _ablakban(item: QQuickItem) -> tuple[float, float, float, float]:
    """Az elem doboza az ABLAK koordinátarendszerében (x, y, szél., mag.)."""
    sarok = item.mapToScene(item.boundingRect().topLeft())
    return (sarok.x(), sarok.y(), item.width(), item.height())


def _kozeppont(item: QQuickItem) -> tuple[float, float]:
    """Az elem KÖZEPE az ablakban — forgatás mellett is (a doboz közepe)."""
    pont = item.mapToScene(item.boundingRect().center())
    return (pont.x(), pont.y())


def _lap(panel: QQuickItem) -> QQuickItem:
    return _child(panel, "collageSheet")


def _egyseg(panel: QQuickItem) -> float:
    """Képpont / lapegység — MINDKÉT tengelyen ugyanaz (spec 6.1)."""
    return _lap(panel).width() / LAPEGYSEG


def _lap_pont(panel: QQuickItem, u: float, v: float) -> QPoint:
    """Lapegység-koordináta → ablak-koordináta."""
    lap = _lap(panel)
    pont = lap.mapToScene(QPointF(u * _egyseg(panel), v * _egyseg(panel)))
    return QPoint(round(pont.x()), round(pont.y()))


def _tartalmazza(item: QQuickItem, pont: QPoint) -> bool:
    """Rajta van-e az ABLAK-koordinátás pont az elemen (forgatással együtt)?"""
    return item.contains(item.mapFromScene(QPointF(pont)))


# --- Egérjáték ---------------------------------------------------------------


def _eger_le(view, pont: QPoint, modositok=Qt.KeyboardModifier.NoModifier):
    QTest.mousePress(view, Qt.MouseButton.LeftButton, modositok, pont)


def _eger_fel(view, pont: QPoint, modositok=Qt.KeyboardModifier.NoModifier):
    QTest.mouseRelease(view, Qt.MouseButton.LeftButton, modositok, pont)


def _eger_mozog(view, pont: QPoint, modositok=Qt.KeyboardModifier.NoModifier):
    """Egérmozgás MÓDOSÍTÓVAL — a `QTest.mouseMove` ezt nem tudja.

    A spec 7.4 szíve: a Picasa a módosítót a húzás KÖZBEN kérdezi
    (`GetAsyncKeyState`), nem a lenyomáskor rögzíti. Ezt csak úgy lehet
    mérni, ha a mozgás-eseményhez magunk adjuk a módosítót."""
    helyi = QPointF(pont)
    esemeny = QMouseEvent(
        QEvent.Type.MouseMove,
        helyi,
        helyi,
        view.mapToGlobal(pont).toPointF()
        if hasattr(view.mapToGlobal(pont), "toPointF")
        else QPointF(view.mapToGlobal(pont)),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        modositok,
    )
    QGuiApplication.sendEvent(view, esemeny)


def _csomopontok(controller):
    return controller.collageNodes.nodes


