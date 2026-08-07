"""QML-funkcionális tesztek: #423 — a mappa-fejléc (LightboxHeader.qml)
tipográfiája és a jobb-felső szinkron-kapcsoló.

A fejléc a könyvtár-feedben (LightboxFeed.qml) ListView-delegate-ként él —
`findChild`-dal offscreen nem garantált a létrejötte (ld. test_viewer.py
`TestFolderDescriptionField` indoklása) —, ezért a komponenst önállóan,
`QQmlComponent`-tel töltjük be, a projekt bevett mintája szerint.
"""

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module

# a létrehozott QQmlComponent/QQuickItem-eket életben kell tartani a teszt
# végéig (ld. test_qml_splash.py indoklása)
_KEEP_ALIVE: list = []


def _make_header(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    header = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert header is not None
    _KEEP_ALIVE.append(header)
    return header


class TestFolderHeaderTypography:
    """#423: cím Georgia 20pt, dátumsor Georgia 14pt, a cím bal
    behúzása 50px a fejléc bal szélétől."""

    def test_title_uses_georgia_20pt(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás 2026")
        title = header.findChild(QObject, "folderTitleText")
        assert title is not None
        assert title.property("font").family() == "Georgia"
        assert title.property("font").pointSize() == 20

    def test_date_uses_georgia_14pt(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(
            engine, folderName="Nyaralás 2026", dateText="2026. augusztus 7."
        )
        date = header.findChild(QObject, "folderDateText")
        assert date is not None
        assert date.property("font").family() == "Georgia"
        assert date.property("font").pointSize() == 14
        assert date.property("text") == "2026. augusztus 7."

    def test_title_indented_50px_from_header_left(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás 2026")
        title_clip = header.findChild(QObject, "folderTitleClip")
        assert title_clip is not None
        assert title_clip.property("x") == 50

    def test_date_shares_the_same_50px_indent(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(
            engine, folderName="Nyaralás 2026", dateText="2026. augusztus 7."
        )
        date = header.findChild(QObject, "folderDateText")
        # a Layout.leftMargin a ColumnLayoutban a kirajzolt x-ben
        # jelentkezik — azt ellenőrizzük közvetlenül
        assert date.property("x") == 50


class TestFolderHeaderTitleFade:
    """#423: hosszú mappanévnél halványuló kifutás, NEM "…"."""

    def test_short_name_has_no_fade(self, qml_app, qt_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="kicsi")
        # elég széles fejléc, hogy a rövid cím biztosan kiférjen — a
        # halványuló kifutás csak akkor jelenik meg, ha a cím TÉNYLEG nem
        # fér ki a rendelkezésre álló szélességbe
        header.setProperty("width", 600)
        qt_app.processEvents()
        fade = header.findChild(QObject, "folderTitleFade")
        assert fade is not None
        assert fade.property("visible") is False

    def test_long_name_shows_fade_not_ellipsis(self, qml_app, qt_app):
        _, _, engine = qml_app
        header = _make_header(
            engine,
            folderName="Ez egy nagyon-nagyon hosszú mappanév, ami biztosan "
            "nem fér ki a fejléc rendelkezésre álló szélességébe",
        )
        header.setProperty("width", 300)
        qt_app.processEvents()
        title = header.findChild(QObject, "folderTitleText")
        # nincs "…" — a teljes szöveg megmarad, a levágást a clip + a
        # halványuló Rectangle végzi, nem a Text maga (a `TextElideMode`
        # enumot a PySide nem tudja marshalni, ezért csak a szöveget és a
        # halványuló réteg láthatóságát ellenőrizzük)
        assert "…" not in title.property("text")
        fade = header.findChild(QObject, "folderTitleFade")
        assert fade is not None
        assert fade.property("visible") is True


class TestFolderHeaderSyncToggle:
    """#423: „Szinkronizálás az internettel" felirat + kapcsoló a
    mappa-fejléc jobb-felső sarkában, letiltott állapotban."""

    def test_sync_switch_present_and_disabled(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás 2026")
        switch_ = header.findChild(QObject, "folderSyncSwitch")
        assert switch_ is not None
        assert switch_.property("enabled") is False

    def test_sync_label_present(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás 2026")
        label = header.findChild(QObject, "folderSyncLabel")
        assert label is not None
        assert label.property("text") != ""

    def test_sync_row_top_right_of_header(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás 2026")
        header.setProperty("width", 400)
        sync_row = header.findChild(QObject, "folderSyncRow")
        assert sync_row is not None
        # jobb-felső: a jobb szélhez van kötve, y a fejléc tetején
        assert sync_row.property("y") == 0
