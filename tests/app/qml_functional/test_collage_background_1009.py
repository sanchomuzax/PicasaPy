"""A háttérkép-előnézet KIRAJZOLVA, valódi vezérlővel — #1009.

A jegy két tünete közül a felhasználó a MÁSODIKAT látja: a „Kép
használata"-ra kattintva a 37 × 37-es négyzet üres marad. Ezt a kérdést
property-ből nem lehet eldönteni — a `collageBackgroundImage` lehet helyes
úgy is, hogy a képet a `Image` elem soha nem tölti be (rossz URL-alak,
hiányzó kötés, `visible: false`). Ezért ez a fájl:

- VALÓDI `QQuickView`-ban rajzolja ki a `CollageBackgroundBox`-ot,
- a **valódi** `CollageMixin` vezérlővel (nem teszt-kettőssel), tehát a
  kattintástól a kirajzolt képpontig a teljes lánc benne van,
- VALÓDI egérkattintással váltja a módot,
- és a KÉPPONTOKAT nézi meg: az előnézet belseje egyszínű-e (üres), vagy
  van benne rajz.

⚠️ A tesztképek egyszínű pirosak (`support.jpeg_factory`), ezért nem
képpont-küszöböt állítunk, hanem azt, hogy a doboz belseje **több színt**
tartalmaz-e, mint üresen (#942: beégetett képpont-küszöbhöz és
képpont-kivonathoz nem kötünk).

A mappa neve szándékosan ékezetes és szóközös: a `file:` URL összeállítása
pontosan ezen szokott elhasalni (#190).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg

_KEEPALIVE: list[object] = []

#: A doboz tervezői mérete (a „Beállítások" lapé — a komponens azt tölti ki).
LAP_SZELESSEG = 266
LAP_MAGASSAG = 351

#: Az előnézet saját 1 képpontos kerete + 1 képpont ráhagyás.
KERET_MARGO = 2


class _Photo:
    def __init__(self, folder_path, name):
        self.folder_path = folder_path
        self.name = name
        self.caption = None
        self.width = 400
        self.height = 300


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def vezerlo(qt_app, tmp_path, library):
    """A VALÓDI kollázs-vezérlő, minimális hoston (a #943 mintája)."""
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "kimenet"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [_Photo(str(library), "a.jpg"), _Photo(str(library), "b.jpg")]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    instance = _Host()
    instance.openCollage([0, 1])
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def ures_vezerlo(qt_app, tmp_path, library):
    """Ugyanaz a vezérlő, MEGNYITOTT kollázs nélkül — az ellenpróbához."""
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "ures.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "kimenet"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos([])

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    instance = _Host()
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _doboz(qt_app, controller) -> QQuickItem:
    """A `CollageBackgroundBox` valódi ablakban, kirajzolva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(
        b"""
import QtQuick
import PicasaPy 1.0
CollageBackgroundBox { objectName: "collageBackgroundBox" }
""",
        QUrl(),
    )
    assert [e.toString() for e in component.errors()] == []
    root = component.create()
    assert root is not None
    root.setProperty("controller", controller)
    root.setWidth(LAP_SZELESSEG)
    root.setHeight(LAP_MAGASSAG)
    root.setParentItem(view.contentItem())
    view.resize(LAP_SZELESSEG, LAP_MAGASSAG)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    root.setProperty("_view", view)
    _KEEPALIVE.extend((view, root, component))
    _varj(qt_app, lambda: root.width() == LAP_SZELESSEG)
    return root


def _varj(qt_app, felteve, ezredmasodperc: int = 5000) -> bool:
    """Vár, amíg a feltétel teljesül — fejnélküli rajzolás LASSÚ (#985).

    A kép betöltése aszinkron (`asynchronous: true`), az elrendezés pedig nem
    a hívás pillanatában fut le: aki azonnal mér, a fejnélküli környezetben
    véletlenszerűen bukó tesztet ír."""
    for _ in range(max(1, ezredmasodperc // 20)):
        qt_app.processEvents()
        if felteve():
            return True
        QTest.qWait(20)
    qt_app.processEvents()
    return bool(felteve())


def _bejar(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _bejar(child)


def _keres(root: QQuickItem, name: str) -> QQuickItem:
    for item in _bejar(root):
        if item.objectName() == name:
            return item
    talalat = root.findChild(QObject, name)
    assert talalat is not None, f"{name} nem található a kirajzolt fában"
    return talalat


def _belso_szinek(root: QQuickItem, item: QQuickItem) -> set:
    """Az elem belsejében ELŐFORDULÓ színek — a saját keretét kihagyva."""
    kep = root.property("_view").grabWindow()
    sarok = item.mapToScene(QPointF(0, 0)).toPoint()
    return {
        QColor(
            kep.pixelColor(sarok.x() + dx, sarok.y() + dy)
        ).name()
        for dy in range(KERET_MARGO, int(item.height()) - KERET_MARGO)
        for dx in range(KERET_MARGO, int(item.width()) - KERET_MARGO)
    }


def _elonezet(root: QQuickItem) -> QQuickItem:
    return _keres(root, "collageCurrentBackgroundImage")


def _betoltott(kep: QQuickItem) -> bool:
    """`status === Image.Ready` — QML-kifejezésként kiértékelve.

    A `status` enumot a `property()` nem tudja Pythonba fordítani
    („Can't find converter for 'QQuickImageBase::Status'"), a QML-kontextus
    viszont igen — és az állítás így az EREDETI alakjában marad olvasható."""
    from PySide6.QtQml import qmlContext

    kifejezes = QQmlExpression(qmlContext(kep), kep, "status === Image.Ready")
    return bool(kifejezes.evaluate())


def _valt_kep_modra(qt_app, root: QQuickItem) -> None:
    """VALÓDI egérkattintás a „Kép használata" rádiógombra."""
    radio = _keres(root, "collageBitmapBgRadio")
    pont = radio.mapToScene(
        QPointF(radio.width() / 2, radio.height() / 2)
    ).toPoint()
    QTest.mouseClick(radio.window(), Qt.LeftButton, Qt.NoModifier, pont)
    qt_app.processEvents()


class TestElonezet:
    def test_a_kattintas_utan_van_hatterkep(self, qt_app, vezerlo):
        root = _doboz(qt_app, vezerlo)
        _valt_kep_modra(qt_app, root)
        assert vezerlo.collageBackgroundMode == "image"
        assert vezerlo.collageBackgroundImage != ""

    def test_az_elonezet_TENYLEG_betolti_a_kepet(self, qt_app, vezerlo):
        """`Image.Ready` — a forrás nem csak be van kötve, be is töltődött."""
        root = _doboz(qt_app, vezerlo)
        _valt_kep_modra(qt_app, root)
        kep = _elonezet(root)
        assert _varj(qt_app, lambda: _betoltott(kep)), (
            f"az előnézet nem töltött be: source={kep.property('source')}, "
            f"progress={kep.property('progress')}"
        )
        # a `paintedWidth` a KÖVETKEZŐ rajzoláskor frissül, nem a betöltéskor
        # — terhelt gépen az azonnali olvasás még 0-t lát (#985)
        assert _varj(qt_app, lambda: kep.property("paintedWidth") > 0), (
            "betöltött, de nem rajzolódott ki"
        )

    def test_az_elonezet_negyzetebe_TENYLEG_kerul_rajz(self, qt_app, vezerlo):
        """A képpontok döntik el, hogy a felhasználó lát-e valamit.

        A mérce az elem SAJÁT alapszíne: ha a négyzet belsejében egyetlen
        képpont sem tér el tőle, akkor a felhasználó üres dobozt lát —
        akkor is, ha a `collageBackgroundImage` történetesen helyes."""
        root = _doboz(qt_app, vezerlo)
        _valt_kep_modra(qt_app, root)
        kep = _elonezet(root)
        _varj(qt_app, lambda: _betoltott(kep))
        keret = _keres(root, "collageCurrentBackground")
        alapszin = QColor(keret.property("color")).name()
        assert _varj(
            qt_app, lambda: _belso_szinek(root, keret) - {alapszin}
        ), "a 37 × 37-es előnézet üres maradt"

    def test_kep_nelkuli_kollazsban_ures_a_negyzet(self, qt_app, ures_vezerlo):
        """A mérés ELLENPRÓBÁJA: kép nélkül a négyzet tényleg egyszínű.

        Enélkül az előző teszt attól is zöld lenne, hogy a doboz kerete vagy
        a háttere belelóg a mérésbe."""
        root = _doboz(qt_app, ures_vezerlo)
        _valt_kep_modra(qt_app, root)
        keret = _keres(root, "collageCurrentBackground")
        _varj(qt_app, keret.isVisible)
        alapszin = QColor(keret.property("color")).name()
        assert _belso_szinek(root, keret) == {alapszin}

    def test_a_negyzet_csak_kep_modban_latszik(self, qt_app, vezerlo):
        root = _doboz(qt_app, vezerlo)
        keret = _keres(root, "collageCurrentBackground")
        assert keret.isVisible() is False
        _valt_kep_modra(qt_app, root)
        assert _varj(qt_app, keret.isVisible)

    def test_a_kijeloles_atirja_az_elonezetet(self, qt_app, vezerlo):
        """„A kijelölt elemek használata" — a rajz is KÖVETI a választást."""
        root = _doboz(qt_app, vezerlo)
        _valt_kep_modra(qt_app, root)
        kep = _elonezet(root)
        _varj(qt_app, lambda: _betoltott(kep))
        elso = kep.property("source").toString()

        vezerlo.setCollageSelection([1])
        vezerlo.setBackgroundFromSelection()
        assert _varj(
            qt_app, lambda: kep.property("source").toString() != elso
        ), "az előnézet forrása nem követte a kijelölést"
        assert _varj(qt_app, lambda: _betoltott(kep))
