"""QML-funkcionális tesztek: hisztogram-doboz (#25, #228, #232, #235, #429) —
a bal alsó placeholder-doboz élesítése, HistogramBox.qml (#155: a korábbi
`test_qml_functional.py` egyik szelete, processzenkénti izolációhoz)."""

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor


def _ertek(value):
    """QML `var` property → Python-érték (#664).

    A QML `var` tulajdonságot a PySide6 verziójától függően vagy kész
    Python-szótárként adja vissza, vagy becsomagolva, `QJSValue`-ként. A
    második esetben a `["r"]` indexelés `TypeError`-t dob, ami valódi
    kötés-hibának látszik, holott csak konverzió hiányzik. Ugyanez a
    `hasattr(..., "toVariant")` minta él már a `test_qml_hidden.py`-ban és
    a `test_qml_viewer_properties.py`-ban is."""
    return value.toVariant() if hasattr(value, "toVariant") else value


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
        histogram = _ertek(box.property("histogramData"))
        assert set(histogram.keys()) == {"r", "g", "b"}
        assert list(histogram["r"]) == list(
            _ertek(edit.property("histogram"))["r"]
        )

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

        assert list(_ertek(box.property("histogramData"))["r"]) == list(
            _ertek(edit.property("histogram"))["r"]
        )

    def test_histogram_curve_is_populated_immediately_on_open(self, qml_app, qt_app):
        """#228: megnyitáskor AZONNAL nem-üres a görbe (nincs csúszka-mozdulat)."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        histogram = _ertek(box.property("histogramData"))
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

    def test_title_stays_on_a_single_line(self, qml_app, qt_app):
        """#1344: a cím EGY sor — a #235 kétsoros tördelése MEGDŐLT.

        A #235 abból indult ki, hogy „a cím mindig teljes", és ehhez két
        sort engedett (`WordWrap` + `maximumLineCount: 2`). A `respack.yt`
        mérése ezt megcáfolta: a `nerdview/nvhead` réteg doboza
        13,4 → 113,15, azaz **11 képpont magas — egyetlen sor**. Ez az
        ellenkező irányú őr: ha a tördelés visszakúszna, itt bukik.
        """
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        title = window.findChild(QObject, "histogramTitle")
        assert title.property("lineCount") == 1
        # a szöveg el is fér a sávban — tehát nem `…`-ra vágva „egysoros"
        assert title.property("contentWidth") <= title.property("width")

    def test_panel_background_is_not_brown(self, qml_app, qt_app):
        """#512: a #429-ben bevezetett `#a88974` meleg barna REGRESSZIÓ volt
        — a bejelentő eredeti Picasa-képernyőképe világosszürke panelt
        mutat. A panel mostantól a `Theme.chromeBg` tokent követi (a
        szerkesztőpanel saját krómháttere), nem rögzített barna literál."""
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        theme = engine.singletonInstance("PicasaPy", "Theme")
        assert box.property("color") != QColor("#a88974")
        assert theme is not None
        assert box.property("color") == theme.property("chromeBg")

    def test_plot_area_background_is_distinct_from_panel(self, qml_app, qt_app):
        """#512: a rajzterület (`histoback`/`histo` réteg) az eredeti
        képernyőkép szerint elkülönül, világosabb a panel hátterétől —
        a `Theme.contentPanel` tokent használja, ami eltér a panel
        `Theme.chromeBg` hátterétől."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        background = window.findChild(QObject, "histogramPlotBackground")
        assert background is not None, "histogramPlotBackground nem található"
        assert background.property("color") != box.property("color")

    def test_plot_area_never_overlaps_long_multiline_exif_text(self, qml_app, qt_app):
        """#512 regresszió: hosszú, TÖBB SOROS (pl. magyar fordítású) EXIF-
        blokk mellett sem csúszik egymásra a rajzterület és a szöveg.
        Korábban a kézzel számolt magasság-levonás (`box.anchors.margins`,
        `cameraLabel.implicitHeight`) hibás margót használt, és bőséges
        szöveg mellett a rajzterület és a szöveg doboza AZONOS y-pozícióból
        indult (mérve: 8 soros EXIF esetén mindkettő 19px-en).

        #1344: a védelem szerkezete megváltozott. Nem a `ColumnLayout`
        osztja el a helyet, hanem MÉRT, fix koordináták tartják a helyükön
        az elemeket — ezért a hiba osztálya (a tartalom tolja a rétegeket)
        közvetlenül állítható: a geometria a szöveg mennyiségétől
        FÜGGETLEN. A megengedett átfedés a `respack.yt`-ben is meglévő
        2 képpont (`histoback` alja 84, `detail1` teteje 82).
        """
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        box = window.findChild(QObject, "viewerHistogramBox")
        plot = window.findChild(QObject, "histogramPlot")
        camera = window.findChild(QObject, "cameraSummaryArea")
        assert plot is not None and camera is not None

        def _geometria():
            return (
                plot.property("y"),
                plot.property("height"),
                camera.property("y"),
                camera.property("height"),
            )

        rovid_geometria = _geometria()

        rows = [
            f"Nagyon hosszú fényképezőgép-adat sor {i}, ami biztosan több sorba törik\tÉrték {i}"
            for i in range(8)
        ]
        box.setProperty("cameraSummary", "\n".join(rows))
        for _ in range(6):
            qt_app.processEvents()

        assert _geometria() == rovid_geometria, (
            "a bőséges EXIF-szöveg elmozdította a rétegeket: "
            f"{rovid_geometria} → {_geometria()}"
        )
        plot_bottom = plot.property("y") + plot.property("height")
        assert plot_bottom <= camera.property("y") + 2.01, (
            f"a rajzterület ({plot_bottom}) a mért 2 képpontnál mélyebben "
            f"lóg rá az EXIF-szövegre ({camera.property('y')})"
        )
