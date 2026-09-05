"""#2043 — a mappa-cím színe az eredeti `#634B45`, nem a fekete tinta.

A Picasa telepítőjének `runtime/constants.ui` fájlja az „Album Layout"
blokkban három értéket ad a rács fejlécének címéhez:

| kulcs | érték | nálunk |
|---|---|---|
| `alayout_titleFont` | Georgia | ✅ átvéve |
| `alayout_titleSize` | 20 | ✅ átvéve |
| `alayout_titleColor` | **`#634B45`** | ❌ `ink` (majdnem fekete) volt |

⚠️ A próbák a **kirajzolt vezérlőt** olvassák (`folderTitleText.color`), nem
a `Theme` tokent: a token helyes értéke önmagában semmit nem bizonyít, ha a
fejléc mást köt (ld. a projekt korábbi eseteit, ahol a token élt, de nem
hatott).
"""

from __future__ import annotations

import picasapy.app.application as app_module
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

#: `alayout_titleColor` a `runtime/constants.ui`-ból.
EREDETI_CIMSZIN = "#634b45"

# A C++ oldal a Python-objektum GC-jével együtt eltűnhet — ld. a
# `test_album_fejlec_gombok_1823.py` indoklását.
_KEEP_ALIVE: list = []


def _theme(engine):
    return engine.singletonInstance("PicasaPy", "Theme")


def _fejlec(engine):
    """A fejléc ÖNÁLLÓAN töltve: a `LightboxHeader` a képfolyam
    csoport-küldöttje, tehát csak feltöltött rácson születne meg."""
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    fejlec = comp.createWithInitialProperties({"folderName": "Nyaralás"})
    assert comp.errors() == [], comp.errors()
    assert fejlec is not None
    _KEEP_ALIVE.append(fejlec)
    return fejlec


def _elem(engine, nev):
    obj = _fejlec(engine).findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestAVilagosTema:
    def test_a_KIRAJZOLT_cim_szine_az_eredeti(self, qml_app):
        __window, controller, engine = qml_app
        controller.setDarkTheme(False)
        szin = _elem(engine, "folderTitleText").property("color")
        assert szin.name().lower() == EREDETI_CIMSZIN, (
            f"a mappa-cím színe {szin.name()}, az eredetié "
            f"{EREDETI_CIMSZIN} (`alayout_titleColor`)"
        )

    def test_NEM_a_tinta(self, qml_app):
        """A hiba lényege: a cím a fekete `ink`-et kapta. Ha valaki
        visszaköti, ez a próba mondja meg, miért nem szabad."""
        _window, controller, engine = qml_app
        controller.setDarkTheme(False)
        cim = _elem(engine, "folderTitleText").property("color")
        assert cim.name().lower() != _theme(engine).property("ink").name().lower()


class TestASotetTema:
    def test_a_cim_OLVASHATO_marad(self, qml_app):
        """A téma-politika szerint minden szín-tokennek van párja. A
        `#634B45` sötét háttéren olvashatatlan, ezért sötét témán a
        világosított párja jár."""
        __window, controller, engine = qml_app
        controller.setDarkTheme(True)
        szin = _elem(engine, "folderTitleText").property("color")
        assert szin.name().lower() != EREDETI_CIMSZIN, (
            "sötét témán is a világos témás cím-szín áll — a token nem "
            "párosodott"
        )
        assert szin.lightnessF() > 0.55, (
            f"sötét témán a cím világossága {szin.lightnessF():.2f} — a "
            f"sötét háttéren olvashatatlan"
        )

    def test_a_SZINEZET_megmarad(self, qml_app):
        """A pár ugyanaz a meleg barna, csak világosítva — nem szürke és
        nem más színezet."""
        __window, controller, engine = qml_app
        controller.setDarkTheme(True)
        szin = _elem(engine, "folderTitleText").property("color")
        assert 0 <= szin.hueF() * 360 <= 30, (
            f"a sötét pár színezete {szin.hueF() * 360:.0f}°, az eredetié 12°"
        )
        assert szin.saturationF() > 0.05, "a sötét pár elszürkült"
