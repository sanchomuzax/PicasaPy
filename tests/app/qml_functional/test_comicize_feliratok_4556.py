"""#4556 — a Képregény (Comicize) panel csúszkái az EREDETI feliratokon.

Az eredeti Picasa `ImageFilters::BlurXY`, `DotContrast` és `DotFade`
csúszkáit a PicasaPy kitalált szavakkal (Edge Strength / Posterize /
Smoothness) jelölte. A mérce a `docs/specs/picasa-effekt-feliratok.md`
táblázata és a magyar respack (`referencia/i18n-hu/stringres.xml`):

- BlurXY      → Színes ecset
- DotContrast → Pontsűrűség
- DotFade     → Ponthalványítás

A tesztet a csempére KATTINTVA, a valódi úton nyitjuk meg a panelt, és a
KIRAJZOLT felirat-elemek szövegét nézzük, magyar fordítással, három
ablakmagasságon (−5 / 0 / +5 px), hogy az elrendezés se csússzon el.

⚠️ Ez a teszt a SZÖVEGET ellenőrzi, nem a renderelt képet: a referencia-
képernyőkép a tulajdonosi NAS-on van, amit ebből a munkafából nem olvasunk.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, Qt, QTranslator

from test_param_panel_layout_700 import _PANEL_QML, _child, _view

#: A Képregény csempéje a 5. effekt-fülön (`activeTab: 4`).
_COMICIZE_TAB = 4

#: A három csúszka felirata, sorrendben (BlurXY, DotContrast, DotFade).
_ELVART_FELIRATOK = ("Színes ecset", "Pontsűrűség", "Ponthalványítás")


@pytest.fixture
def magyar_forditas(qt_app):
    import picasapy.app.application as app_module

    translator = QTranslator(qt_app)
    assert translator.load(
        str(app_module._APP_DIR / "i18n" / "picasapy_hu.qm")
    ), "a picasapy_hu.qm nem tölthető be"
    qt_app.installTranslator(translator)
    try:
        yield translator
    finally:
        qt_app.removeTranslator(translator)


class TestAKepregenyCsuszkaiEredetiFeliratokkal:
    @pytest.mark.parametrize("magassag", [755, 760, 765])
    def test_a_felirat_az_eredeti_magyar_szoveg(
        self, qt_app, magyar_forditas, magassag
    ):
        root = _view(qt_app, _PANEL_QML.format(tab=_COMICIZE_TAB), 280, magassag)
        csempe = _child(root, "effectComicize")
        QMetaObject.invokeMethod(
            csempe, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert root.property("paramPanelActive") is True

        feliratok = tuple(
            _child(root, f"effectParamLabel{i}").property("text") for i in range(3)
        )

        assert feliratok == _ELVART_FELIRATOK, (
            f"a Képregény csúszkái {feliratok} — az eredetiek szerint "
            f"{_ELVART_FELIRATOK} (#4556), {magassag} px magas ablakban"
        )
