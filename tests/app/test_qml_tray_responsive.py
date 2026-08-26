"""#406: a TrayBar (alsó sáv) legyen reszponzív — szűk ablaknál a
zoom-csúszka zsugorodjon, és SEMMI ne lógjon ki a sáv jobb széléből
(kilógás-őr). A `test_qml_tray_print_email.py` betöltési mintáját követi
(önálló TrayBar, controller nélkül).

#1345: a kimeneti gombok (Nyomtatás, E-mail, Exportálás, Kollázs, Film,
Megosztás) MÁR NEM esnek vissza ikon-only módra — fix 55 × 36 képpontos
gombok lettek, amelyekben a felirat az ikon alatt, a gombon BELÜL ül,
tehát nem szélesítik a sávot. Szűk ablakban helyettük a két
csoportelválasztó marad el.

#1420: a sáv EGYETLEN `RowLayout`-ja megszűnt — a 36,5 %-os osztópont
mentén két rész lett belőle (képtálca | jobb sáv két sorral), ezért a
kilógás-őr nem egy sor gyerekeit járja be, hanem a sáv TELJES
elemfáját. A zöld gomb pedig fix 141 × 35, tehát nincs többé ikon-only
kompakt módja: a felirata a gombon BELÜL tördel két sorba, ahogy az
eredetin. Ami maradt kompaktnak: a nagyítás-csúszka és a két
csoportelválasztó."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, Signal, Slot


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


class FakeAppWindow(QObject):
    """A TrayBar `appWindow` (required var) felülete — csak azok a
    property-k/függvények, amiket a komponens ténylegesen olvas."""

    selectedIndexesChanged = Signal()
    selectedIndexChanged = Signal()
    viewerOpenChanged = Signal()
    thumbSizeChanged = Signal()

    def __init__(self):
        super().__init__()
        self._selected_indexes = []
        self._selected_index = -1
        self._viewer_open = False
        self._thumb_size = 100

    def _get_selected_indexes(self):
        return self._selected_indexes

    def _set_selected_indexes(self, value):
        self._selected_indexes = list(value)
        self.selectedIndexesChanged.emit()

    selectedIndexes = Property(
        list, _get_selected_indexes, _set_selected_indexes,
        notify=selectedIndexesChanged,
    )

    def _get_selected_index(self):
        return self._selected_index

    def _set_selected_index(self, value):
        self._selected_index = value
        self.selectedIndexChanged.emit()

    selectedIndex = Property(
        int, _get_selected_index, _set_selected_index, notify=selectedIndexChanged
    )

    def _get_viewer_open(self):
        return self._viewer_open

    def _set_viewer_open(self, value):
        self._viewer_open = bool(value)
        self.viewerOpenChanged.emit()

    viewerOpen = Property(
        bool, _get_viewer_open, _set_viewer_open, notify=viewerOpenChanged
    )

    def _get_thumb_size(self):
        return self._thumb_size

    def _set_thumb_size(self, value):
        self._thumb_size = value
        self.thumbSizeChanged.emit()

    thumbSize = Property(
        int, _get_thumb_size, _set_thumb_size, notify=thumbSizeChanged
    )

    @Slot(result=bool)
    def rotateTargetsAllVideo(self):
        return False


def _load_tray(app_module, app_window, width=900):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", None)
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / "TrayBar.qml")
    )
    item = factory.createWithInitialProperties(
        {"appWindow": app_window, "width": width}
    )
    assert item is not None, factory.errorString()
    engine._tray_factory = factory
    return item, engine


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestTrayBarNoOverflowAtNarrowWidth:
    """#406: 900 px szélességnél a tálca egyetlen gyereke sem lóghat ki
    jobbra — sem kijelöléssel, sem néző-nézetben."""

    def _assert_no_overflow(self, tray, qt_app, expected_width=900):
        """#1420: a sáv TELJES elemfáját járjuk be, nem egy sor gyerekeit.

        A régi változat a `trayRowLayout` közvetlen gyerekeire nézett; az
        az egyetlen sor a 36,5 %-os osztóponttal megszűnt. A bejárás így
        SZIGORÚBB lett: a beágyazott elemek (a műveletsor cellái, a zöld
        gomb a helyén belül) is a mérés alá esnek."""
        for _ in range(3):
            qt_app.processEvents()
        bar = _child(tray, "trayMainBar")
        assert bar.property("width") == pytest.approx(expected_width)
        overflowing = []

        def walk(item):
            for child in item.childItems():
                if not child.property("visible"):
                    continue
                w = child.property("width")
                if w:
                    right_edge = child.mapToItem(bar, w, 0).x()
                    if right_edge > bar.property("width") + 0.5:
                        overflowing.append(
                            (
                                child.objectName() or child.metaObject().className(),
                                right_edge,
                                bar.property("width"),
                            )
                        )
                walk(child)

        walk(bar)
        assert overflowing == [], f"kilógó gyerekek: {overflowing}"

    def test_no_overflow_with_grid_selection(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0, 1, 2]
        tray, engine = _load_tray(app_module, app_window, width=900)
        self._assert_no_overflow(tray, qt_app)
        tray.deleteLater()
        engine.deleteLater()

    def test_no_overflow_in_viewer(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.viewerOpen = True
        tray, engine = _load_tray(app_module, app_window, width=900)
        tray.setProperty("viewerIndex", 0)
        self._assert_no_overflow(tray, qt_app)
        tray.deleteLater()
        engine.deleteLater()

    def test_no_overflow_with_no_selection(self, app_module, qt_app):
        app_window = FakeAppWindow()
        tray, engine = _load_tray(app_module, app_window, width=900)
        self._assert_no_overflow(tray, qt_app)
        tray.deleteLater()
        engine.deleteLater()

    def test_no_overflow_when_the_separators_appear(self, app_module, qt_app):
        """#1345: a sáv LEGBŐVEBB alakja — a két csoportelválasztóval.

        A #1116 eredeti változata a Kollázs felirat saját küszöbén mért;
        az a küszöb a #1345-tel megszűnt (a gomb fix 55 × 36, a felirata
        nem szélesíti a sávot, ezért mindig látszik). A legdrágább eset
        azóta az, amikor a két elválasztó cellája (2 × 59 px) is bekerül
        — a szélességet ezért ennek a küszöbnek a széléről vesszük, nem
        fix pixelértékből (az platform- és nyelvfüggő lenne).
        """
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0, 1, 2]
        tray, engine = _load_tray(app_module, app_window, width=900)
        for _ in range(3):
            qt_app.processEvents()
        bar = _child(tray, "trayMainBar")
        # #1420: a küszöb nem „a kompakt küszöb + két cella" többé — a két
        # cella a jobb sávban ül, ami az ablak 63,5 %-a, tehát az ablakban
        # mérve többe kerül. A komponens maga adja meg a mért küszöböt.
        szeles = bar.property("separatorThreshold")
        tray.setProperty("width", szeles)
        for _ in range(3):
            qt_app.processEvents()
        assert bar.property("separatorsVisible") is True
        assert _child(tray, "trayCollageLabel").property("visible") is True
        self._assert_no_overflow(tray, qt_app, expected_width=szeles)
        tray.deleteLater()
        engine.deleteLater()

    def test_no_overflow_at_default_window_width(self, app_module, qt_app):
        """A `Main.qml` alap ablakszélessége (1280px) — feliratos (nem
        kompakt) módban se lógjon ki semmi."""
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0, 1, 2]
        tray, engine = _load_tray(app_module, app_window, width=1280)
        self._assert_no_overflow(tray, qt_app, expected_width=1280)
        tray.deleteLater()
        engine.deleteLater()


class TestTrayBarIconOnlyModeStillWorks:
    """#406: szűk (ikon-only) módban is működnek a gombok — a jelzés-
    kibocsátás (Export/E-mail/Print) és az engedélyezés-logika nem
    változhat a kompakt módban."""

    def test_export_signal_emitted_in_compact_mode(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0]
        tray, engine = _load_tray(app_module, app_window, width=900)
        for _ in range(3):
            qt_app.processEvents()
        seen = []
        tray.exportRequested.connect(lambda: seen.append(True))
        export_button = _child(tray, "trayExportButton")
        assert export_button.property("enabled") is True
        export_button.clicked.emit()
        qt_app.processEvents()
        assert seen == [True]
        tray.deleteLater()
        engine.deleteLater()

    def test_email_and_print_signals_emitted_in_compact_mode(
        self, app_module, qt_app
    ):
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0]
        tray, engine = _load_tray(app_module, app_window, width=900)
        for _ in range(3):
            qt_app.processEvents()
        email_seen = []
        print_seen = []
        tray.emailRequested.connect(lambda: email_seen.append(True))
        tray.printRequested.connect(lambda: print_seen.append(True))
        _child(tray, "trayEmailButton").clicked.emit()
        _child(tray, "trayPrintButton").clicked.emit()
        qt_app.processEvents()
        assert email_seen == [True]
        assert print_seen == [True]
        tray.deleteLater()
        engine.deleteLater()

    def test_the_output_labels_survive_the_compact_mode(self, app_module, qt_app):
        """#1345: a kimeneti gombok felirata MINDEN szélességen látszik.

        Ez a #1116-os őr utódja. Az eredeti azt állította, hogy a Kollázs
        gomb kompakt módban ikon-only marad — annak akkor volt értelme,
        amikor a felirat a gomb MELLETT ült, és így szélesítette a sávot.
        A #1345 óta a gomb fix 55 × 36 képpont, a felirat pedig az ikon
        ALATT, a gombon belül: elrejtésével egyetlen képpontot sem
        nyernénk, csak információt veszítenénk. A #1116 célja (legyen a
        Kollázs gombnak felirata, mint a Nyomtatásnak) így erősebben
        teljesül, mint korábban.
        """
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0]
        tray, engine = _load_tray(app_module, app_window, width=900)
        for _ in range(3):
            qt_app.processEvents()
        bar = _child(tray, "trayMainBar")
        assert bar.property("compact") is True

        for nev in ("trayCollageLabel", "trayPrintLabel", "trayEmailLabel",
                    "trayExportLabel"):
            felirat = _child(tray, nev)
            assert felirat.property("visible") is True, (
                f"{nev} kompakt módban eltűnt — a fix méretű gombon ezzel "
                "semmit nem nyerünk"
            )
            assert felirat.property("text") != ""

        tray.setProperty("width", bar.property("compactThreshold") + 40)
        for _ in range(3):
            qt_app.processEvents()
        assert bar.property("compact") is False
        assert _child(tray, "trayCollageLabel").property("visible") is True
        tray.deleteLater()
        engine.deleteLater()

    def test_wide_width_keeps_labelled_buttons(self, app_module, qt_app):
        """Széles ablaknál (>= a kompakt küszöb felett) a gombok
        feliratosak maradnak — a kompakt mód csak szűk helyen kapcsol be.

        A szélességet NEM fix pixelértékkel adjuk meg: a küszöb a mért
        feliratszélességektől függ, azok pedig platform- és nyelvfüggők
        (a windows-CI 1280 px-en emiatt bukott). A komponens saját
        `compactThreshold`-jából származtatjuk."""
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0]
        tray, engine = _load_tray(app_module, app_window, width=1280)
        for _ in range(3):
            qt_app.processEvents()
        bar = _child(tray, "trayMainBar")
        tray.setProperty("width", bar.property("compactThreshold") + 40)
        for _ in range(3):
            qt_app.processEvents()
        assert bar.property("compact") is False
        export_label = _child(tray, "trayExportLabel")
        assert export_label.property("visible") is not False
        tray.deleteLater()
        engine.deleteLater()
