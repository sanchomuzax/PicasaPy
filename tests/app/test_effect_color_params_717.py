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

import numpy as np
import pytest

from picasapy.app.effect_params import effect_params, has_params
from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
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
        """#2146: a `tint` ismét alkalmazható — SHIFTTEL.

        A #2141 idején nem volt felületi belépési pontja: az 1. fül 6.
        csempéje az eredeti elsődlegesére (`picniktint`) kötött, a `tint`
        pedig a Shiftes másodlagos. A #2141 kommentje ezt előre jelezte:
        „a Shift-ág megépítése a #2146".

        A Shift-ág megépült (nyolc csempén), tehát a `tint` visszakerült a
        vezérlő `_EFFECT_NAMES` listájába — enélkül a Shifttel megnyomott
        csempe `ValueError`-t adna. A próba eredeti SZÁNDÉKA is teljesül
        megint: a lánc a teljes paraméter-készletet viszi, a színt is."""
        editing.applyEffectWithParams("tint", [0.5, "#336699"])
        assert _chain(editing) == "tint=1,0.500000,ff336699;", (
            "a `tint` nem alkalmazható a felületről — pedig a #2146 óta a "
            "Shiftes csempe ezt hívja"
        )

    def test_ansel_writes_the_color(self, editing):
        editing.applyEffectWithParams("ansel", ["#336699"])
        assert _chain(editing) == "ansel=1,ff336699;"

    def test_dir_tint_writes_the_color(self, editing):
        editing.applyEffectWithParams("dir_tint", [0.5, 0.5, 0.25, 0.25, "#336699"])
        assert _chain(editing) == (
            "dir_tint=1,0.500000,0.500000,0.250000,0.250000,ff336699;"
        )

    def test_radtint_writes_the_color(self, editing):
        editing.applyEffectWithParams("radtint", [0.5, 0.5, 0.25, "#336699"])
        assert _chain(editing) == "radtint=1,0.500000,0.500000,0.250000,ff336699;"

    def test_white_dir_tint_writes_the_darkening_alpha(self, editing):
        """#3908: a fehér `dir_tint` a Picasában NEM néma — a natív
        `0x0090f525` a TELJES dword-öt hasonlítja `0x00ffffff`-fel, és a
        Picasa a színt mindig `ff` alfával írja, tehát a betöltött dword
        (`0xffffffff`) sosem egyezik a `0x00ffffff` kihagyó konstanssal: a
        szorzás lefut, és a fehér felület eggyel sötétedik
        (`v·255 >> 8 = v−1`, `docs/specs/filters-decoded.md`, #3900).

        A saját rendererünk a #3902 óta ugyanígy a teljes dwordot
        hasonlítja (`render/dir_tint.py`). Ez a próba a LÁNCBA ÍRT alakot
        ellenőrzi: `00ffffff` mellett a szorzás kimaradna, `ffffffff`
        mellett lefut — a mi láncunknak ezért az utóbbit kell írnia. A
        kirajzolt eredményt a `TestWhiteDirTintEndToEnd` méri.
        """
        editing.applyEffectWithParams("dir_tint", [0.5, 0.5, 0.25, 0.25, "#ffffff"])
        assert _chain(editing) == (
            "dir_tint=1,0.500000,0.500000,0.250000,0.250000,ffffffff;"
        )

    def test_focalzoom_writes_all_six_parameters(self, editing):
        # #3596: a sugár SZÁZALÉKKÉNT megy a láncba — a 8 × 6-os képen a
        # tartomány `10 … min(W, H)/2 = 3`, a 6,5 képpont ennek a fele
        editing.applyEffectWithParams("focalzoom", [0.5, 0.5, 60.0, 6.5, 70.0, 10.0])
        assert _chain(editing) == (
            "FocalZoom=1,0.500000,0.500000,60.000000,50.000000,70.000000,10.000000;"
        )

    def test_default_apply_uses_white_as_the_pick_color(self, editing):
        # #357: a mért NAS-mintákban a Picasa fehér alapszínnel ELHAGYJA a
        # szín-paramétert — a mi íróoldalunk ezt nem tükrözi (mindig
        # kiírjuk), de a fehér ugyanaz az alapérték, mint a renderelő
        # `_DEFAULT_TINT_COLOR`-ja (`render/chain.py`), tehát a hiányzó
        # paraméter esetén is ugyanazt a képet adja.
        # #3908: az alfa `ff` — a négy régi, színkerekes effekt (`tint`/
        # `ansel`/`dir_tint`/`radtint`) a Picnik-generációs effektektől
        # eltérően `ff`-fel ír, a valós korpusz szerint (`filters-decoded.md`).
        editing.applyEffectWithParams("ansel", [])
        assert _chain(editing) == "ansel=1,ffffffff;"

    def test_radtint_default_apply_writes_the_full_set(self, editing):
        editing.applyEffectWithParams("radtint", [])
        assert _chain(editing) == "radtint=1,0.500000,0.500000,0.250000,ffffffff;"


class TestWhiteDirTintEndToEnd:
    """#3908 + #3902, végponttól végpontig: a felületen alkalmazott fehér
    Színátmenet (`applyEffectWithParams` → `format_param_values` → a mentett
    lánc → `parse_filters` → `apply_filters`) a színezett félen ugyanúgy egy
    árnyalatnyit sötétít, mint a Picasa (`v · 255 >> 8`: 200 → 199, 0 → 0),
    a régi, `00ffffff`-es sor pedig továbbra is változatlanul hagyja a képet.

    A beállítás teljes súlyt ad a felső sorokra: a `Gradient = 0` a natív
    Feather-padlóra esik (a rámpa telít), a `Shade = 0` pedig azonossá
    teszi a tónusgörbét — így a sötétedés KIZÁRÓLAG a színszorzásból jöhet.
    Az alsó sor a súly nélküli fél.
    """

    _WHITE_FULL_WEIGHT = [0.5, 0.5, 0.0, 0.0, "#ffffff"]

    @staticmethod
    def _render(chain: str, value: int) -> np.ndarray:
        image = np.full((16, 4, 3), value, dtype=np.uint8)
        result, skipped = apply_filters(image, parse_filters(chain))
        assert skipped == ()
        return result

    @pytest.mark.parametrize(("value", "darkened"), [(200, 199), (0, 0)])
    def test_the_applied_white_darkens_like_picasa(self, editing, value, darkened):
        editing.applyEffectWithParams("dir_tint", self._WHITE_FULL_WEIGHT)
        result = self._render(_chain(editing), value)
        assert result[0].tolist() == [[darkened] * 3] * 4, (
            "a PicasaPy-ban alkalmazott fehér Színátmenet a színezett félen "
            f"{value} → {darkened} helyett {result[0, 0].tolist()}-t ad"
        )
        assert result[-1].tolist() == [[value] * 3] * 4

    @pytest.mark.parametrize("value", [200, 0])
    def test_a_legacy_00ffffff_row_stays_unchanged(self, value):
        result = self._render(
            "dir_tint=1,0.500000,0.500000,0.000000,0.000000,00ffffff;", value
        )
        np.testing.assert_array_equal(
            result, np.full((16, 4, 3), value, dtype=np.uint8)
        )
