"""#1656 — a megjelenítési mód a többi bélyegkép-felületen is.

## A lelet

A #1596 óta a mód a bélyegkép-URL-ben utazik (`&d=<mód>`), és a
szolgáltató oldala **felület-független**. Hat felület viszont **cimke
nélkül** építette az URL-jét, tehát ott a mód **hatástalan** volt:

duplikátumok · importálás · arckeresés · idővonal · keresési találatok ·
effekt-előnézet

## A megoldás alakja

⚠️ Hat vezérlő konstruktorát átírni nem lett volna jó: mind **modul-
szintű** URL-építő függvényből dolgozik. A mód ezért ugyanoda kerül,
ahonnan a szolgáltató is kapja — a `wire_display_mode()` **egyetlen**
átvezetőjébe (`set_current_display_mode`). Ez ugyanaz az egy-forrás elv,
amiért az a függvény nevesítve van: a féloldalas tükrözés így nem tud
becsúszni.
"""

from __future__ import annotations

import pytest

from picasapy.app.display_mode_paint import (
    current_display_mode,
    current_display_mode_suffix,
    set_current_display_mode,
)


@pytest.fixture(autouse=True)
def _alaphelyzet():
    """A mód modul-szintű — minden próba után vissza az alapra, hogy egy
    teszt ne mérgezze meg a következőt."""
    eredeti = current_display_mode()
    yield
    set_current_display_mode(eredeti)


class TestAzEgyForras:
    def test_a_beallitott_mod_visszaolvashato(self):
        set_current_display_mode("sepia")
        assert current_display_mode() == "sepia"

    def test_a_kepponthato_mod_CIMKET_kap(self):
        set_current_display_mode("sepia")
        assert current_display_mode_suffix() == "&d=sepia"

    @pytest.mark.parametrize("mod", ["", "auto", "normal", "dither16", "rdesk"])
    def test_a_no_op_modok_NEM_kapnak_cimket(self, mod: str):
        """Enélkül a Qt URL-kulcsú gyorstára fölöslegesen duplázódna, és
        minden módváltás újrarenderelné a felületet hatás nélkül."""
        set_current_display_mode(mod)
        assert current_display_mode_suffix() == ""

    def test_nem_sztring_erteket_elnyel(self):
        set_current_display_mode(None)  # type: ignore[arg-type]
        assert current_display_mode() == ""
        assert current_display_mode_suffix() == ""


class TestAHatFelulet:
    """A URL-építők tényleg átveszik-e a cimkét."""

    def test_duplikatumok(self):
        from picasapy.app.dedup_controller import _thumb_url

        set_current_display_mode("bw")
        assert _thumb_url(7) == "image://thumbs/7&d=bw"

    def test_duplikatumok_hianyzo_azonositora_URES(self):
        """A `None` továbbra is üres — a QML `Image.source` üresre nem
        próbál betölteni."""
        set_current_display_mode("bw")
        from picasapy.app.dedup_controller import _thumb_url

        assert _thumb_url(None) == ""

    def test_importalas(self):
        from picasapy.app.import_source_controller import _thumb_url

        set_current_display_mode("bw")
        assert _thumb_url(3) == "image://thumbs/3&d=bw"

    @pytest.mark.parametrize("mod", ["", "normal"])
    def test_no_op_modban_az_URL_a_REGI(self, mod: str):
        """Bájtra a mód bevezetése előtti alak."""
        from picasapy.app.dedup_controller import _thumb_url as dedup_url
        from picasapy.app.import_source_controller import (
            _thumb_url as import_url,
        )

        set_current_display_mode(mod)
        assert dedup_url(7) == "image://thumbs/7"
        assert import_url(3) == "image://thumbs/3"


class TestAzAtvezetes:
    def test_a_wire_display_mode_ALLITJA_a_kozos_modot(self):
        """Az őr foga: ha valaki kiveszi a hívást az átvezetőből, a hat
        felület némán visszaesik cimke nélküli URL-re."""
        import inspect

        from picasapy.app.display_mode_controller import wire_display_mode

        forras = inspect.getsource(wire_display_mode)
        assert "set_current_display_mode(mode)" in forras, (
            "a `wire_display_mode` nem állítja a közös módot — a hat "
            "további bélyegkép-felületen a mód hatástalan lenne (#1656)"
        )


class TestAKozosEpito:
    """#1656 (2. kör) — az idővonal, a keresési találatok és a képtálca.

    Mind a három a KÖZÖS `models._thumb_url()`-t hívja, mód nélkül. Az
    alapérték volt az üres sztring — ezért maradt ott a mód hatástalan.
    Mostantól az alapérték a JELENLEGI mód.

    ⚠️ A rács modellje továbbra is a SAJÁT másolatát adja át
    (`self._display_mode`), mert az a `set_display_mode()`-dal együtt
    lépteti a `revision`-t is — a két út szándékosan külön.
    """

    @staticmethod
    def _foto():
        from picasapy.index import PhotoRecord

        return PhotoRecord(
            id=42,
            folder_path="/kepek",
            name="a.jpg",
            kind="photo",
            size=10,
            mtime_ns=1,
            star=False,
            hidden=False,
            caption=None,
            keywords=None,
            rotate_steps=0,
            filters=None,
            taken_at=None,
            orientation=None,
            width=None,
            height=None,
            geotag=None,
            exif_lat=None,
            exif_lon=None,
            face_count=0,
            unnamed_face_count=0,
        )

    def test_mod_nelkul_hivva_a_JELENLEGI_modot_veszi(self):
        from picasapy.app.models import _thumb_url

        set_current_display_mode("sepia")
        assert _thumb_url(self._foto()).endswith("&d=sepia"), (
            "az idővonal / keresés / tálca bélyegképein a mód hatástalan "
            "maradna (#1656)"
        )

    def test_a_kifejezett_ures_mod_ERVENYES_marad(self):
        """A rács modellje üres módot is átadhat — azt nem írjuk felül."""
        from picasapy.app.models import _thumb_url

        set_current_display_mode("sepia")
        assert "&d=" not in _thumb_url(self._foto(), "")

    def test_no_op_modban_nincs_cimke(self):
        from picasapy.app.models import _thumb_url

        set_current_display_mode("normal")
        assert "&d=" not in _thumb_url(self._foto())
