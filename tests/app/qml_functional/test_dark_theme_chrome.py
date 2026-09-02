"""QML-funkcionális tesztek: #314 — a sötét téma (#28) három vizuális hibája.

1. A splash-logó fehér háttér-korongot kap sötét témán (a logó sötét eleme
   különben eltűnik a sötét kártyahátteren) — világos témán a korong
   átlátszó (ott a kártya már amúgy is fehér).
2. A TrayBar szürke gombjainak (forgatás, Export) ikonja/felirata sötét
   témán is olvasható marad — rögzített `Theme.iconInk` tinta, nem a
   témával változó `ink`.
3. Az ehhez bevezetett Theme-tokenek (`logoDisc`, `iconInk`) párban élnek.

A splash-komponenst önállóan (QQmlComponent) töltjük — ld.
tests/app/test_qml_splash.py mintája; a TrayBar-t a teljes Main.qml-en
keresztül, a helyi `qml_app` fixture (window, controller, engine) ad
hozzáférést.

A `setDarkTheme()` a QSettings-ben is rögzíti a választást, ezért a fájl
szándékosan a funkció-szintű `qml_app` fixture-t használja; a tesztek nem
oszthatják meg ezt az állapotot.
"""

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module

# A létrehozott QQmlComponent/QQuickItem-eket életben kell tartani a teszt
# végéig (ld. test_qml_splash.py indoklása — a C++ oldal a Python-objektum
# GC-jével együtt tűnhet el, ha nincs élő referencia).
_KEEP_ALIVE: list = []


def _make_splash(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "SplashScreen.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    base = {"version": "v0.4.99 (test)", "statusText": "Indulás…", "ready": False}
    base.update(props)
    splash = comp.createWithInitialProperties(base)
    assert comp.errors() == [], comp.errors()
    assert splash is not None
    _KEEP_ALIVE.append(splash)
    return splash


def _theme_singleton(engine):
    """A Theme singleton példánya az engine-ből (ld. test_qml_dark_theme.py)."""
    return engine.singletonInstance("PicasaPy", "Theme")


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _select_row(window, qt_app, row):
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()


class TestThemeTokensPaired:
    """Az új tokenek (#314) párban élnek, és nem törlik/nevezik át a
    meglévőket."""

    def test_logo_disc_and_icon_ink_exist(self, qml_app):
        _, _, engine = qml_app
        theme = _theme_singleton(engine)
        assert theme is not None
        assert theme.property("logoDisc") is not None
        assert theme.property("iconInk") is not None

    def test_existing_tokens_untouched(self, qml_app):
        _, controller, engine = qml_app
        theme = _theme_singleton(engine)
        # néhány régi token — nem sérülhet a #314 módosítás alatt
        assert theme.property("ink") is not None
        assert theme.property("canvasBg") is not None
        assert theme.property("picasaGreen") is not None

    def test_icon_ink_stays_dark_in_both_themes(self, qml_app):
        """A gomb-króm (PicasaButton.qml) nem témavezérelt — ezért az
        iconInk-nek MINDKÉT témában sötétnek kell maradnia (nem követheti
        az `ink`-et, ami sötét témán kivilágosodik)."""
        _, controller, engine = qml_app
        theme = _theme_singleton(engine)
        controller.setDarkTheme(False)
        light_icon_ink = theme.property("iconInk")
        controller.setDarkTheme(True)
        dark_icon_ink = theme.property("iconInk")
        assert light_icon_ink.lightnessF() < 0.35
        assert dark_icon_ink.lightnessF() < 0.35


class TestSplashLogoDisc:
    """#314/1: a splash-logó fehér háttér-korongot kap sötét témán."""

    def test_disc_present_behind_logo(self, qml_app):
        _, _, engine = qml_app
        splash = _make_splash(engine)
        disc = splash.findChild(QObject, "splashLogoDisc")
        logo = splash.findChild(QObject, "splashLogo")
        assert disc is not None, "splashLogoDisc nem található"
        assert logo is not None, "splashLogo nem található"

    def test_disc_transparent_in_light_theme(self, qml_app):
        _, controller, engine = qml_app
        controller.setDarkTheme(False)
        splash = _make_splash(engine)
        disc = splash.findChild(QObject, "splashLogoDisc")
        color = disc.property("color")
        assert color.alphaF() == 0.0

    def test_disc_opaque_white_in_dark_theme(self, qml_app, qt_app):
        _, controller, engine = qml_app
        controller.setDarkTheme(True)
        splash = _make_splash(engine)
        qt_app.processEvents()
        disc = splash.findChild(QObject, "splashLogoDisc")
        color = disc.property("color")
        assert color.alphaF() == 1.0
        assert color.lightnessF() > 0.95
        controller.setDarkTheme(False)

    def test_disc_hugs_logo_with_small_margin(self, qml_app, qt_app):
        """A korong ne lógjon túl a logón: ~2 px ráhagyás minden oldalon
        (#37 mintája), a logó TÉNYLEGES (kirajzolt) méretéhez igazodva."""
        _, controller, engine = qml_app
        controller.setDarkTheme(True)
        splash = _make_splash(engine)
        qt_app.processEvents()
        disc = splash.findChild(QObject, "splashLogoDisc")
        logo = splash.findChild(QObject, "splashLogo")
        painted_w = logo.property("paintedWidth")
        painted_h = logo.property("paintedHeight")
        assert painted_w > 0 and painted_h > 0
        margin_w = disc.property("width") - painted_w
        margin_h = disc.property("height") - painted_h
        # ~2 px ráhagyás minden oldalon => összesen kb. 4 px többlet
        assert 0 < margin_w <= 8
        assert 0 < margin_h <= 8
        controller.setDarkTheme(False)

    def test_logo_still_has_explicit_height(self, qml_app):
        """#240 regresszió-védelem: a logó explicit magassága a korong
        bevezetése után is megmarad."""
        _, _, engine = qml_app
        splash = _make_splash(engine)
        logo = splash.findChild(QObject, "splashLogo")
        assert logo.property("height") == 72


class TestTrayBarIconContrast:
    """#314/2: a TrayBar szürke gombjainak ikonja/felirata sötét témán is
    olvasható marad (rögzített iconInk, nem a témával változó ink)."""

    def test_rotate_and_export_labels_use_icon_ink_when_enabled_dark(
        self, qml_app, qt_app
    ):
        window, controller, engine = qml_app
        theme = _theme_singleton(engine)
        _select_row(window, qt_app, 0)
        controller.setDarkTheme(True)
        qt_app.processEvents()

        assert _child(window, "trayRotateLeft").property("enabled") is True
        assert _child(window, "trayRotateRight").property("enabled") is True
        assert _child(window, "trayExportButton").property("enabled") is True

        icon_ink = theme.property("iconInk")
        #: #1224: a két forgatás-vezérlő KÉP lett, nem betűjel — a `color`
        #: állítás rájuk nem érvényes. A gomb-króm mindig világos, tehát a
        #: kép LÁTHATÓSÁGÁT állítjuk helyette; a szín-token továbbra is a
        #: szöveges feliratokra vonatkozik.
        for name in ("trayRotateLeftIcon", "trayRotateRightIcon"):
            ikon = _child(window, name)
            assert ikon is not None, f"{name} nem található"
            assert ikon.property("opacity") == 1.0, (
                f"{name} halvány, pedig a gomb engedélyezett"
            )
        for name in ("trayExportLabel",):
            label = _child(window, name)
            assert label.property("color") == icon_ink, (
                f"{name} színe nem az iconInk tokent követi"
            )
            # sötét, jól olvasható tinta (a gomb-króm mindig világos)
            assert label.property("color").lightnessF() < 0.35
        controller.setDarkTheme(False)

    def test_rotate_and_export_labels_readable_in_light_theme_too(
        self, qml_app, qt_app
    ):
        window, controller, engine = qml_app
        _select_row(window, qt_app, 0)
        controller.setDarkTheme(False)
        qt_app.processEvents()

        #: #1224: a forgatás-vezérlők képek — rájuk a láthatóság a mérce
        for name in ("trayRotateLeftIcon", "trayRotateRightIcon"):
            assert _child(window, name).property("opacity") == 1.0
        for name in ("trayExportLabel",):
            label = _child(window, name)
            assert label.property("color").lightnessF() < 0.35

    def test_labels_show_expected_glyphs(self, qml_app, qt_app):
        window, controller, engine = qml_app
        _select_row(window, qt_app, 0)
        qt_app.processEvents()
        #: #1224: a betűjelek helyett MÉRT méretű ikonok
        #: (`thumbui/rotateleft_icon` / `rotateright_icon`, 11 × 15).
        #: A glifa-állítás azért szűnt meg, mert épp az volt a hiba: az
        #: alakja platformonként más lett.
        for name, fajl in (
            ("trayRotateLeftIcon", "tray-rotate-left.svg"),
            ("trayRotateRightIcon", "tray-rotate-right.svg"),
        ):
            ikon = _child(window, name)
            assert fajl in str(ikon.property("source"))
            assert (ikon.width(), ikon.height()) == (11.0, 15.0)
        assert "Export" in _child(window, "trayExportLabel").property("text")
