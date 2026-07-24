"""QML-funkcionális tesztek: rács-feed — csoportosított ListView, mappa-
kiemelés, thumb-felirat, kép-minőség, kiegyensúlyozott sorok (#155: a
korábbi `test_qml_functional.py` egyik szelete, processzenkénti
izolációhoz)."""

from PySide6.QtCore import QObject


class TestLibraryFeedQml:
    """#64: a rács csoportokra bontott feed-ListView."""

    def test_feed_shows_groups(self, qml_app, qt_app):
        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        groups = controller.feedGroups
        assert len(groups) == 1
        assert groups[0]["count"] == 2
        assert grid.property("count") == 1  # egy mappa-csoport a ListView-ban

    def test_cell_geometry_follows_thumb_size(self, qml_app, qt_app):
        # #85: a cellWidth mostantól a kiegyenlített (effektív, a sort
        # kitöltő) szélesség — legalább a névleges (thumbSize+18), de a
        # rendelkezésre álló szélesség egyenletes elosztásához igazodva
        # annál nagyobb is lehet.
        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        window.setProperty("thumbSize", 200)
        qt_app.processEvents()
        nominal = 200 + 18
        assert grid.property("cellWidth") >= nominal


class TestFolderPaneHighlight:
    def test_selected_path_follows_controller(self, qml_app, qt_app):
        window, controller, _ = qml_app
        folder_pane = window.findChild(QObject, "folderPane")
        assert folder_pane is not None, "folderPane nem található"
        assert folder_pane.property("selectedPath") == controller.currentFolder


class TestThumbCaption:
    def test_mode_round_trips_on_controller(self, qml_app, qt_app):
        # A GridView indexképei ebben az offscreen headless környezetben nem
        # jönnek létre (QQuickGridView lusta elem-létrehozása valódi
        # ablak-exponálást igényel, amit az offscreen platform nem ad —
        # ugyanez a jelenség reprodukálható a módosítás előtti főágon is).
        # Ezért a controller<->QML kötést közvetlenül, a ThumbDelegate
        # komponenst pedig önállóan (lásd lent) teszteljük.
        window, controller, _ = qml_app
        controller.setThumbCaptionMode("filename")
        qt_app.processEvents()
        assert controller.thumbCaptionMode == "filename"

    def test_thumb_delegate_shows_filename_caption(self, qml_app, qt_app):
        import picasapy.app.application as app_module
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        window, controller, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 0,
                "keywords": "",
                "resolution": "320x160",
                "captionMode": "filename",
            }
        )
        assert comp.errors() == []
        assert delegate is not None
        caption = delegate.findChild(QObject, "thumbCaption")
        assert caption is not None, "thumbCaption Text nem található"
        assert caption.property("text") == "a.jpg"
        assert caption.property("visible") is True


class TestThumbDelegateImageQuality:
    # #83: a legnagyobb rács-méretben (256px) a cache-elt thumbnail
    # nagyítás nélkül, kicsinyítéssel álljon elő — a delegate Image-nek
    # mipmap-elt kicsinyítést kell használnia, hogy a köztes csúszka-
    # fokokon se legyen recés/homályos a kép.
    def test_delegate_image_uses_mipmap_for_quality_downscale(self, qml_app):
        import picasapy.app.application as app_module
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        _, _, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 0,
                "keywords": "",
                "resolution": "320x160",
            }
        )
        assert comp.errors() == []
        image = delegate.findChild(QObject, "thumbImage")
        assert image is not None, "thumbImage Image nem található"
        assert image.property("mipmap") is True
        assert image.property("smooth") is True


class TestBalancedGridRow:
    """#85: a sor a bal és jobb szél között kitöltött legyen, ne balra
    rendezett maradjon fix cellamérettel — az effektív cellaszélesség a
    rendelkezésre álló szélességből számítva töltse ki a sort."""

    @staticmethod
    def _assert_row_fills_width(grid, tolerance_cols=1):
        width = grid.property("width")
        cell_w = grid.property("cellWidth")
        columns = int(grid.property("columns"))
        assert columns >= 1, "legalább egy oszlopnak lennie kell"
        # az oszlopok együtt (kis tűréssel) kitöltik a rendelkezésre álló
        # szélességet — nem maradhat balra tömörült, üres jobb sáv
        leftover = width - columns * cell_w
        assert 0 <= leftover < cell_w * max(1, tolerance_cols) / columns + 2, (
            f"leftover={leftover} width={width} cols={columns} cell_w={cell_w}"
        )

    def test_cell_width_fills_row_at_multiple_thumb_sizes(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"

        for size in (72, 144, 256):
            window.setProperty("thumbSize", size)
            qt_app.processEvents()
            nominal = size + 18
            cell_w = grid.property("cellWidth")
            # az effektív cella legalább akkora, mint a névleges (nem zsugorodhat)
            assert cell_w >= nominal
            self._assert_row_fills_width(grid)

    def test_cell_width_adapts_on_window_resize(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        window.setProperty("thumbSize", 144)

        for w in (900, 1500):
            window.setProperty("width", w)
            qt_app.processEvents()
            self._assert_row_fills_width(grid)

    def test_displayed_image_capped_to_nominal_size_even_in_wide_cell(
        self, qml_app
    ):
        # #85 x #83: a kiegyenlítés miatt megnőtt cellában a MEGJELENÍTETT
        # kép ne nőjön a névleges (legnagyobb csúszka-fokozatnyi) méret
        # fölé — a #83-mal beállított DPR-arányos cache-t ne nagyítsuk fel
        # (recés/homályos lenne). A többlet a térközbe menjen, a kép a
        # névleges méretre plafonozva marad.
        import picasapy.app.application as app_module
        from PySide6.QtCore import QObject, QUrl
        from PySide6.QtQml import QQmlComponent

        _, _, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        nominal = 256 + 18   # a legnagyobb csúszka-fokozat névleges cellája
        wide_cell = nominal + 60   # kiegyenlítés miatt megnövelt cella
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 0,
                "keywords": "",
                "resolution": "320x160",
                "width": wide_cell,
                "height": wide_cell,
                "maxContentWidth": nominal,
                "maxContentHeight": nominal,
            }
        )
        assert comp.errors() == []
        image = delegate.findChild(QObject, "thumbImage")
        assert image is not None, "thumbImage Image nem található"
        assert image.property("width") <= 256
        assert image.property("height") <= 256
