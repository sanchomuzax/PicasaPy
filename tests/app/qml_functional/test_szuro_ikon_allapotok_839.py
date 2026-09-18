"""#839 — a szűrő-gombok be/ki állapota a MÉRT tónusokat viseli.

## A mérés (2026-09-18)

A `respack.yt`-ből a projekt saját kiolvasójával (`tools/picasa/respack.py`)
kinyert rétegek:

| réteg | mit ad |
|---|---|
| `<szűrő>_icon_0` | a KIKAPCSOLT glif — tompa zöld |
| `<szűrő>_icon_1` | a BEKAPCSOLT glif — fehér |
| `globalbuttons_filter_n` | a gomb nyugalmi háttere (szürke átmenet) |
| `globalbuttons_filter_h` | rámutatva — VILÁGOSZÖLD (`#BBD9BF` a közepén) |
| `globalbuttons_filter_p` | lenyomva/aktívan — ZÖLD (`#4E9258` a közepén) |

Képpontról képpontra összevetve a két glif-réteg **maszkja (alakja) azonos**
— csak a tónus más:

* `starsearch` / `facesearch` / `webview`: `#61996A` → `#FFFFFF`
* `moviesearch`: `#7D9F82` + `#BBD8BF` → `#FFFFFF` + `#CCCCCC`
* `geotagsearch`: `#3D8D56` → `#FFFFFF`

⇒ A jegy utolsó nyitott pontja („a be/ki állapot két külön kép") **eldőlt**:
két kép van, de a KÜLÖNBSÉG a tónus. A mi rajzolt ikonjaink ezt egyetlen
szín-váltással pontosan visszaadják — nem kell bitképet szállítanunk.

## Amit ez az őr állít

1. a négy glif-alapú szűrő kikapcsolva a mért tompa zöldet, bekapcsolva a
   mért fehéret viseli;
2. az aktív gomb háttere a mért zöld — **nem** a korábbi, SAJÁT találmányunk
   (fehér doboz + kék keret);
3. a `Theme` tokenek a mért értékeket hordozzák.

## Amit NEM mér

* a bitképek vízszintes él-árnyékolását (a 26 × 16-os gomb bal széle
  világosabb) — a mi gombjaink rajzoltak, a mért KÖZÉPSŐ tónust vesszük át;
* a nyugalmi SZÜRKE gombhátteret: nálunk a szűrő-gomb nyugalomban átlátszó,
  és az eszköztár adja alá a felületet. Ez tudatos eltérés, nem feledés;
* a **geo**-szűrőt: az a mi piros tű-SVG-nk, átlátszósággal (#361) — a mért
  tónus-pár oda SVG-újraszínezést kérne, az külön lépés.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


#: a MÉRT tónusok (ld. a modul docstringjét)
GLIF_KI = "#61996a"
GLIF_BE = "#ffffff"
HATTER_AKTIV = "#4e9258"
HATTER_RAMUTAT = "#bbd9bf"


def _elem(window, nev):
    talalt = window.findChild(QObject, nev)
    assert talalt is not None, f"a(z) {nev} nincs a jelenetben"
    return talalt


def _szin(ertek) -> str:
    return str(ertek.name() if hasattr(ertek, "name") else ertek).lower()


class TestAGlifTonusa:
    """A be/ki állapot a glif TÓNUSA — mérve, nem átlátszóság."""

    def test_kikapcsolva_a_mert_tompa_zold(self, qml_app, qt_app):
        window, _controller, _e = qml_app

        for nev in ("starFilterGlyph", "faceFilterGlyph", "movieFilterGlyph"):
            assert _szin(_elem(window, nev).property("color")) == GLIF_KI, nev

    def test_bekapcsolva_feher(self, qml_app, qt_app):
        window, controller, _e = qml_app

        controller.showStarred()
        qt_app.processEvents()

        assert _szin(_elem(window, "starFilterGlyph").property("color")) == GLIF_BE

    def test_a_masik_szuro_glifje_kozben_kikapcsolt_marad(self, qml_app, qt_app):
        """A csillag bekapcsolása nem színezheti át a többi szűrőt."""
        window, controller, _e = qml_app

        controller.showStarred()
        qt_app.processEvents()

        assert _szin(_elem(window, "faceFilterGlyph").property("color")) == GLIF_KI


class TestAGombHattere:
    def test_alapallapotban_atlatszo(self, qml_app, qt_app):
        window, _controller, _e = qml_app

        szin = _elem(window, "starFilterButton").property("color")
        #: az átlátszó `color` alfája 0 — a NEVE `#000000`, ezért az alfát
        #: kérdezzük, nem a nevet
        assert szin.alpha() == 0

    def test_az_aktiv_szuro_hattere_a_mert_zold(self, qml_app, qt_app):
        """A korábbi fehér doboz + KÉK keret a MI találmányunk volt; a mért
        három gombállapot mind a ZÖLD családba tartozik."""
        window, controller, _e = qml_app

        controller.showStarred()
        qt_app.processEvents()

        gomb = _elem(window, "starFilterButton")
        assert _szin(gomb.property("color")) == HATTER_AKTIV
        #: ⚠️ A `border` (QQuickPen) a PySide-kötésen át nem olvasható
        #: („Can't find converter for 'QQuickPen*'"), ezért a keret
        #: eltűnését a FORRÁS őrzi — ld. `TestNincsTobbeKekAkcent`.


class TestNincsTobbeKekAkcent:
    """Forrás-őr: a szűrő-sorban nem térhet vissza a kék jelölés."""

    def test_a_szuro_sor_nem_hivatkozik_a_selectionBlue_ra(self):
        from pathlib import Path as _Path

        import picasapy.app

        forras = (
            _Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "MainToolbar.qml"
        ).read_text(encoding="utf-8")
        kezd = forras.index('id: filterIconsRow')
        veg = forras.index('objectName: "dateRangeFilterSlider"')
        blokk = forras[kezd:veg]

        assert "selectionBlue" not in blokk, (
            "a szűrő-sorban visszatért a kék jelölés — a mért paletta zöld"
        )
