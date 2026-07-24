"""QML-funkcionális tesztek: hisztogram-doboz (#25, #228, #232, #235) —
a bal alsó placeholder-doboz élesítése, HistogramBox.qml (#155: a korábbi
`test_qml_functional.py` egyik szelete, processzenkénti izolációhoz)."""

from PySide6.QtCore import QObject


class TestHistogramBoxWiring:
    """#25: a bal alsó placeholder-doboz élesítése — HistogramBox.qml."""

    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def test_box_appears_in_viewer(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        assert box is not None, "viewerHistogramBox nem található"

    def test_histogram_data_bound_from_edit_controller(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        edit = engine.rootContext().contextProperty("editController")
        histogram = box.property("histogramData")
        assert set(histogram.keys()) == {"r", "g", "b"}
        assert list(histogram["r"]) == list(edit.property("histogram")["r"])

    def test_camera_summary_bound_from_edit_controller(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        edit = engine.rootContext().contextProperty("editController")
        assert box.property("cameraSummary") == edit.property("cameraSummary")

    def test_camera_summary_label_falls_back_when_no_exif(self, qml_app, qt_app):
        # a support.jpeg_factory nem ír fényképezőgép-EXIF-et — a sor
        # a "nincs adat" feliratra esik vissza, nem marad üres/eltűnő
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        label = window.findChild(QObject, "cameraSummaryText")
        assert label is not None, "cameraSummaryText nem található"
        assert label.property("text") != ""

    def test_switching_photos_updates_the_box_binding(self, qml_app, qt_app):
        """Lapozáskor a doboz a MÁSIK fotó előnézetéből frissül — a kötés
        (histogramData: editController.histogram) él, nem befagyott érték."""
        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app, index=0)
        edit = engine.rootContext().contextProperty("editController")
        box = window.findChild(QObject, "viewerHistogramBox")

        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()

        assert list(box.property("histogramData")["r"]) == list(
            edit.property("histogram")["r"]
        )

    def test_histogram_curve_is_populated_immediately_on_open(self, qml_app, qt_app):
        """#228: megnyitáskor AZONNAL nem-üres a görbe (nincs csúszka-mozdulat)."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        histogram = box.property("histogramData")
        assert any(v > 0.0 for v in histogram["r"]), "hisztogram üres megnyitáskor"

    def test_histogram_bars_render_with_nonzero_height(self, qml_app, qt_app):
        """#232: a hisztogram deklaratív téglalap-oszlopokként rajzolódik
        (nem QML Canvas). Megnyitáskor, csúszka-mozdulat nélkül is van
        látható (nem-nulla magasságú) oszlop a rajzterületen. Ez erősebb
        garancia a korábbi Canvas-`paintCount`-nál: a tényleges vizuális
        kimenet meglétét ellenőrzi (nem csak azt, hogy a rajzolás elindult),
        és nincs benne a Canvas time-of-check/paint versenyhelyzete, ami a
        #228 után is üresen hagyta a görbét az éles (Windows) ablakban."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        qt_app.processEvents()
        plot = window.findChild(QObject, "histogramPlot")
        assert plot is not None, "histogramPlot nem található"
        assert plot.property("height") > 0, "a rajzterület magassága nulla"
        # a Repeater-delegate oszlopok VIZUÁLIS gyerekek (nem QObject-
        # gyerekek), ezért childItems()-en át járjuk be őket rekurzívan
        heights: list[float] = []

        def _walk(item):
            for child in item.childItems():
                heights.append(child.property("height"))
                _walk(child)

        _walk(plot)
        assert any((h or 0) > 0 for h in heights), "nincs látható hisztogram-oszlop"

    def test_histogram_box_has_title(self, qml_app, qt_app):
        """#232: a doboz a referencia szerinti címet viseli (a placeholder
        helyett élő tartalom)."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        title = window.findChild(QObject, "histogramTitle")
        assert title is not None, "histogramTitle nem található"
        assert title.property("text") != ""

    def test_camera_summary_two_column_rows_render(self, qml_app, qt_app):
        """#235: a `bal\tjobb` cellapáros összefoglaló két oszlopban
        renderelődik (soronként bal+jobb cella), a placeholder eltűnik."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        box.setProperty(
            "cameraSummary",
            "Xiaomi Mi Note 10\t1/125 s\nFocal length: 6.72 mm\tf/1.69",
        )
        qt_app.processEvents()
        area = window.findChild(QObject, "cameraSummaryArea")
        assert area is not None, "cameraSummaryArea nem található"
        rows = area.property("summaryRows")
        rows = rows.toVariant() if hasattr(rows, "toVariant") else rows
        assert list(rows) == [
            "Xiaomi Mi Note 10\t1/125 s",
            "Focal length: 6.72 mm\tf/1.69",
        ]
        fallback = window.findChild(QObject, "cameraSummaryText")
        assert fallback.property("visible") is False
        # a delegate-sorok VIZUÁLIS gyerekek — bal/jobb cellaszövegek
        texts: list[str] = []

        def _walk(item):
            for child in item.childItems():
                value = child.property("text")
                if value:
                    texts.append(value)
                _walk(child)

        _walk(area)
        assert "Xiaomi Mi Note 10" in texts
        assert "1/125 s" in texts
        assert "Focal length: 6.72 mm" in texts
        assert "f/1.69" in texts

    def test_title_wraps_instead_of_eliding(self, qml_app, qt_app):
        """#235: a cím keskeny doboznál sortöréssel marad teljes (max 2 sor),
        nem `…`-ra vágva."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        title = window.findChild(QObject, "histogramTitle")
        # a wrapMode enum PySide-oldalon nem konvertálható — a viselkedést a
        # maximumLineCount (2 sor engedett) és a QML-forrás rögzíti
        assert title.property("maximumLineCount") == 2
