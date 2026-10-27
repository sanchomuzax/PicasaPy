"""#936 — a menüpontról indítva NYÍLJON meg a kollázs (és a film).

## ⚠️ #985: a KOLLÁZS célpontja megváltozott — a lap, nem a párbeszéd

Ez a fájl eredetileg azt állította, hogy a Létrehozás ▸ Képkollázs… a
`collageDialog` **modális ablakot** nyitja meg. A `kollazs-panel-ui-spec.md`
**3.2**-es táblája ezt kifejezetten teendőként sorolja fel:
„modálist nyit → **a lapot nyitja meg**". A #920-as sorozat (#942–#949)
megépítette a lapot, a #985 pedig bekötötte — a menüpont mostantól a
**Kollázs lapot** nyitja.

A két kollázs-teszt ezért a célponton változott: a menü jelzésétől indul
továbbra is, de a KIMENET a megnyílt lap (`controller.collageOpen`) és a
látható panel. A film ága érintetlen: az továbbra is párbeszéd.

A `movieDialog` melletti `collageDialog` komponens egyelőre a helyén marad
(`CreateDialogs.qml`), csak nem ez a belépési útja — a leszerelése külön
jegy.

## Miért nem fogta meg ezt a #922 hat tesztje

Azok a párbeszéd `openForSelection()` függvényét **közvetlenül hívták**:

    dialog.metaObject().invokeMethod(dialog, "openForSelection")

Ezzel átugrották a teljes valódi utat — menüpont → `collageRequested`
jelzés → kezelő → párbeszéd —, és pont az a láncszem hiányzott, amit így
sosem érintettek: a `Main.qml` menüsor-blokkjában **nem volt**
`onCollageRequested` kezelő. A menüpont elsütötte a jelzést, és az a
semmibe ment.

A PROTOKOLL erre való szabálya: **a KIMENETET ellenőrizd, ne a szándékot.**
Az izoláltan hívott komponens működhet úgy is, hogy a felhasználó útja
törött.

Ezek az őrök ezért a JELZÉSTŐL indulnak, nem a párbeszédtől.
"""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, QObject, QTimer


def _settle(qt_app, rounds=4):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


def _menusor(window):
    bar = window.property("menuBar")
    assert bar is not None, "nincs menüsor"
    return bar


class TestMenuJelzesVegigmegy:
    def test_a_menusor_jelzese_MEGNYITJA_a_kollazs_LAPOT(self, qml_app, qt_app):
        """A valódi út: a menüsor jelzését sütjük el, nem a panelt hívjuk.

        #985: a kimenet a megnyílt LAP (spec 3.2), nem a régi modális
        párbeszéd."""
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        assert controller.property("collageOpen") is False

        _menusor(window).metaObject().invokeMethod(_menusor(window), "collageRequested")
        _settle(qt_app, 3)

        assert controller.property("collageOpen") is True, (
            "a menüsor jelzésének nincs kezelője — a kattintás a semmibe megy"
        )
        panel = window.findChild(QObject, "collagePanel")
        assert panel is not None and panel.property("visible") is True, (
            "a Kollázs lap nem látszik a menüpont után"
        )

    def test_a_menusor_jelzese_MEGNYITJA_a_film_parbeszedet(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        _menusor(window).metaObject().invokeMethod(_menusor(window), "movieRequested")
        _settle(qt_app, 3)
        # #2096: a párbeszéd HALASZTVA épül, ezért csak a jelzés UTÁN van meg.
        # Az eset ettől ERŐSEBB lett: azt méri, hogy a menü LÉTREHOZZA és
        # megnyitja, nem csak azt, hogy egy meglévőt láthatóra állít.
        dialog = window.findChild(QObject, "movieDialog")
        assert dialog is not None, "a menü nem építette fel a film-párbeszédet"
        assert dialog.property("visible") is True

    def test_kijeloles_NELKUL_is_megnyilik_a_lap(self, qml_app, qt_app):
        """#922 + #936 + #985: a menüből, forrás nélkül is történik valami.

        Spec 3.2 utolsó bekezdése: forrás nélkül a lap **akkor is megnyílik**,
        üres vászonnal — a felhasználó ne egy néma menüpontot kapjon."""
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        _menusor(window).metaObject().invokeMethod(_menusor(window), "collageRequested")
        _settle(qt_app, 3)
        assert controller.property("collageOpen") is True
        assert controller.property("collageClipCount") == 0
