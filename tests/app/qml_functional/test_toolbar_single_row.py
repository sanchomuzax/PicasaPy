"""QML-funkcionális tesztek: #423 — a felső eszközsáv EGYETLEN ~34px-es
csík marad minden ablakszélességen, az "Importálás" gomb soha nem törik
új sorba. Szűk ablaknál a középső szűrő-zóna zsugorodik/rejtőzik, nem a
sáv.

A `MainToolbar.qml` a `Main.qml` `header:` property-je — a scene-graphban
rendes gyerekként elérhető `findChild`-dal (nem Repeater/ListView
delegátum), ezért a szokásos `window.findChild(QObject, name)` minta
működik. A "sáv gyerekei egyetlen sorban vannak" állítást úgy mérjük,
hogy a RowLayout KÖZVETLEN gyerekeinek `y` property-jét (ugyanabban a
koordinátarendszerben, mert közös szülőjük van) hasonlítjuk össze — ha a
sáv "törne", a törött elem y-ja jóval lejjebb (kb. egy elemmagasságnyival)
kerülne, nem pár pixeles középre-igazítási eltéréssel.
"""

from PySide6.QtCore import QObject


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _set_width(window, qt_app, width):
    window.setProperty("width", width)
    qt_app.processEvents()


class TestToolbarStaysSingleStrip:
    """#423: a sáv magassága rögzített 34px, és az "Importálás" gomb +
    a keresőmező + a verzió-címke egyetlen sorban maradnak — szűk (1280)
    és széles (1920) ablaknál is."""

    def _assert_single_row(self, window, qt_app, width):
        _set_width(window, qt_app, width)
        toolbar = _child(window, "mainToolbar")
        assert toolbar.property("height") == 34, (
            f"a sáv magassága nem 34px {width}px ablakszélességnél"
        )

        import_button = _child(window, "toolbarImportButton")
        search_box = _child(window, "toolbarSearchBox")
        version_label = _child(window, "versionLabel")

        # közös szülő (a toolbar belső RowLayout-ja) — a `y` property
        # közvetlenül összehasonlítható, mert ugyanabban a koordináta-
        # rendszerben él
        ys = [
            import_button.property("y"),
            search_box.property("y"),
            version_label.property("y"),
        ]
        assert max(ys) - min(ys) < 15, (
            f"a sáv gyerekei nem egyetlen sorban vannak {width}px "
            f"ablakszélességnél (y-ok: {ys})"
        )

        # az Importálás gomb a sáv bal szélén marad, soha nem csúszik
        # lejjebb egy második "sorba"
        assert import_button.property("x") < 30
        assert import_button.property("width") == 100

    def test_single_row_at_narrow_width(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._assert_single_row(window, qt_app, 1280)

    def test_single_row_at_wide_width(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._assert_single_row(window, qt_app, 1920)

    def test_single_row_at_very_narrow_width(self, qml_app, qt_app):
        # extrém szűk ablak: a szűrő-zóna elrejtőzik, de a sáv marad
        # egy csík, és az Importálás gomb helyben marad
        window, _, qt_app_engine = qml_app
        self._assert_single_row(window, qt_app, 760)


class TestFilterZoneShrinksBeforeBarBreaks:
    """#423: szűk ablaknál a középső szűrő-zóna zsugorodik/rejtőzik el,
    nem a sáv törik."""

    def test_filter_zone_visible_at_wide_width(self, qml_app, qt_app):
        window, _, _ = qml_app
        _set_width(window, qt_app, 1920)
        zone = _child(window, "toolbarFilterZone")
        assert zone.property("visible") is True

    def test_filter_zone_hidden_at_narrow_width(self, qml_app, qt_app):
        window, _, _ = qml_app
        _set_width(window, qt_app, 760)
        zone = _child(window, "toolbarFilterZone")
        assert zone.property("visible") is False
        # a sáv ettől még nem törik — 34px marad
        toolbar = _child(window, "mainToolbar")
        assert toolbar.property("height") == 34

    def test_search_box_shrinks_but_not_below_minimum(self, qml_app, qt_app):
        window, _, _ = qml_app
        _set_width(window, qt_app, 760)
        search_box = _child(window, "toolbarSearchBox")
        assert 120 <= search_box.property("width") <= 300


class TestFiltersLabelInsideStrip:
    """#423: a "Szűrők" felirat az ikonok fölé, a csíkon BELÜL (−4px
    eltolás) — nem külön sorba kerül."""

    def test_filters_label_offset_inside_strip(self, qml_app, qt_app):
        window, _, _ = qml_app
        _set_width(window, qt_app, 1920)
        label = _child(window, "toolbarFiltersLabel")
        assert label.property("y") == -4
        # a felirat szövege megvan és nem üres
        assert label.property("text") != ""
