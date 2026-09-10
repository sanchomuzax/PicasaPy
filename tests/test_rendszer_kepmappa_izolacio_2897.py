"""#2897 — a tesztek nem írhatnak a rendszer VALÓDI képmappájába.

A kollázs- és a film-kimenet célmappája a beállítás HIÁNYÁBAN a rendszer
képmappájának `Picasa` alkönyvtárára esik vissza. Aminek a fixture-je nem
téríti el a `collage/outputDir`-t, az a felhasználó valódi mappájába ír: a
main CI windowsos lába emiatt lett vörös
(`…/Pictures/Picasa/Collages/autosave.cxf`), és a #1054-es őr csak
teardownban, UTÓLAG fogta meg.

A gyökér-conftest ezért MINDEN teszt idejére ideiglenes mappára téríti a
`pictures_dir()`-t. Ez az őr azt méri, hogy a háló tényleg ott van — enélkül a
szabály csak remény.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QStandardPaths

from picasapy.app import collage_output, movie_output


def _rendszer_kepmappa() -> Path:
    hely = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.PicturesLocation
    )
    return Path(hely) if hely else Path.home() / "Pictures"


class TestAHalo:
    def test_a_kollazs_celmappa_NEM_a_valodi_kepmappaban_van(self):
        cel = collage_output.output_dir(None)
        assert not cel.is_relative_to(_rendszer_kepmappa()), (
            "a kollázs-kimenet a rendszer valódi képmappájába mutat — a "
            "gyökér-conftest eltérítése nem működik (#2897)"
        )

    def test_a_film_celmappa_sem(self):
        """A `movie_output` a SAJÁT névterébe importálja a `pictures_dir`-t,
        ezért külön eltérítést kíván — ez az eset erre az egy csapdára van."""
        cel = movie_output.output_dir(None)
        assert not cel.is_relative_to(_rendszer_kepmappa())

    def test_a_beallitott_mappa_tovabbra_is_eroesebb(self):
        """A háló nem írhatja felül a felhasználó választását."""
        assert collage_output.output_dir("/valahol/mashol") == Path(
            "/valahol/mashol"
        )


class TestAKijelolesKikeri:
    @pytest.mark.valodi_kepmappa
    def test_a_jelolessel_a_VALODI_feloldas_lathato(self):
        """A jelölés nélkül nem lehetne mérni a valódi viselkedést sem — a
        `test_kepek_mappa_1088.py` erre épül."""
        assert collage_output.output_dir(None).is_relative_to(
            _rendszer_kepmappa()
        )
