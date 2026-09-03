"""#717: a záró színparaméter több effektnél lemaradt a kiírt láncból.

A #695 méréséből tudjuk: a HIÁNYZÓ paraméter nem néma elejtés — a Picasa
alapértékre esik vissza (`render/chain.py` `_DEFAULT_TINT_COLOR`). De az
alapérték nem feltétlenül az, amit a felhasználó beállított: ugyanaz a
lánc a két programban MÁS SZÍNNEL fut le, holott az ini azonos.

A hiba NEM az író kapujában volt — az a #695 óta elfogadja a regiszterbeli
teljes paraméterszámot (ld. `tests/ini/test_filter_registry_695.py`
`VALODI_MINTAK`, ami pontosan ezekkel az öt effekttel, teljes
paraméterszámmal mintázza a valódi Picasa-exportot). A hiba a felület
paraméter-katalógusában volt (`app/effect_params.py`):

- a `tint`/`dir_tint` egy csúszkás/négy csúszkás alpanelt nyitott
  színválasztó NÉLKÜL,
- az `ansel`/`radtint` egyáltalán nem szerepelt a katalógusban — a gomb
  ezért egykattintásos alapértékkel (`edit_controller._EFFECT_PARAMS`,
  ill. a hardcode-olt `("1",)`) ment a láncra, alpanel/színválasztó nélkül,
- a `FocalZoom` csak 4 paramétert (a puck + 2 csúszka) írt a regiszterbeli
  6-ból — hiányzott a Hardness és a Fade.

Ez a teszt a KIÍRT láncot ellenőrzi (nem a belső property-t): a `_chain()`
segéd a `test_effect_slider_controller.py` mintáját követi.
"""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import effect_params, has_params
from support.jpeg_factory import make_jpeg


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


@pytest.fixture
def editing(controller, photo):
    controller.beginEdit("1", str(photo))
    return controller


def _chain(controller) -> str:
    """A mentett (nem előnézeti) szűrőlánc szöveges alakja."""
    return controller._session.to_value()


class TestCatalogueHasTheFullParameterSet:
    """A katalógus vezérlőszáma egyezzen a regiszterbeli felső korláttal
    (`filter_registry.MAX_PARAM_COUNTS`, a flag utáni darabszám)."""

    @pytest.mark.parametrize(
        ("effect", "expected_control_count"),
        [
            ("tint", 2),  # Color Preservation + szín
            ("ansel", 1),  # szín
            ("dir_tint", 5),  # x, y, Feather, Shade, szín
            ("radtint", 4),  # x, y, Feather, szín
            ("focalzoom", 6),  # x, y, Impact, Radius, Hardness, Fade
        ],
    )
    def test_control_count_matches_the_registry(self, effect, expected_control_count):
        assert len(effect_params(effect)) == expected_control_count

    def test_ansel_and_radtint_now_open_a_param_panel(self):
        # korábban egyik effektnek sem volt katalógus-bejegyzése — a gomb
        # egyenesen az egykattintásos alapértékkel alkalmazott, alpanel
        # (és így színválasztó) nélkül
        assert has_params("ansel") is True
        assert has_params("radtint") is True


class TestChainCarriesTheFullParameterSet:
    """A kiírt `filters=` lánc — a TÉNYLEGES szöveg, nem a szándék."""

    def test_tint_writes_the_color(self, editing):
        """#2141: a `tint` a felületről MÁR NEM alkalmazható.

        Az 1. fül 6. csempéje az eredeti elsődlegesére (`picniktint`)
        kötött; a `tint` a Shiftes másodlagos, tehát nincs felületi
        belépési pontja (a Shift-ág a #2146). A szűrő maga él: régi
        láncból változatlanul visszajátszható.

        A próba SZÁNDÉKA — a lánc a teljes paraméter-készletet viszi,
        a szín is — a `radtint`-en él tovább (lentebb), aminek van
        felületi csempéje."""
        editing.applyEffectWithParams("tint", [0.5, "#336699"])
        assert _chain(editing) == "", (
            "a `tint` felületről alkalmazhatóvá vált — ha ez szándékos, "
            "a #2141 csempe-kötését kell újranézni"
        )

    def test_ansel_writes_the_color(self, editing):
        editing.applyEffectWithParams("ansel", ["#336699"])
        assert _chain(editing) == "ansel=1,00336699;"

    def test_dir_tint_writes_the_color(self, editing):
        editing.applyEffectWithParams("dir_tint", [0.5, 0.5, 0.25, 0.25, "#336699"])
        assert _chain(editing) == (
            "dir_tint=1,0.500000,0.500000,0.250000,0.250000,00336699;"
        )

    def test_radtint_writes_the_color(self, editing):
        editing.applyEffectWithParams("radtint", [0.5, 0.5, 0.25, "#336699"])
        assert _chain(editing) == "radtint=1,0.500000,0.500000,0.250000,00336699;"

    def test_focalzoom_writes_all_six_parameters(self, editing):
        editing.applyEffectWithParams("focalzoom", [0.5, 0.5, 60.0, 20.0, 70.0, 10.0])
        assert _chain(editing) == (
            "FocalZoom=1,0.500000,0.500000,60.000000,20.000000,70.000000,10.000000;"
        )

    def test_default_apply_uses_white_as_the_pick_color(self, editing):
        # #357: a mért NAS-mintákban a Picasa fehér alapszínnel ELHAGYJA a
        # szín-paramétert — a mi íróoldalunk ezt nem tükrözi (mindig
        # kiírjuk), de a fehér ugyanaz az alapérték, mint a renderelő
        # `_DEFAULT_TINT_COLOR`-ja (`render/chain.py`), tehát a hiányzó
        # paraméter esetén is ugyanazt a képet adja
        editing.applyEffectWithParams("ansel", [])
        assert _chain(editing) == "ansel=1,00ffffff;"

    def test_radtint_default_apply_writes_the_full_set(self, editing):
        editing.applyEffectWithParams("radtint", [])
        assert _chain(editing) == "radtint=1,0.500000,0.500000,0.250000,00ffffff;"
