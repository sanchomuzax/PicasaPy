"""#6871: a rácsmodell megmondja, hány csillagozott kép van egy sortartományban.

A mappa-fejléc csillag gombja ebből tud csillagozott kép nélkül tiltott lenni.
A tartomány a csoport `start`/`count` párja; a számlálás a modell sorrendjét
követi, tehát a vizsgált elvárást a modell tényleges sorrendjéből számoljuk.
"""

from __future__ import annotations

import pytest


def _rekord(photo_id: int, nev: str, csillag: bool):
    from picasapy.index import PhotoRecord

    return PhotoRecord(
        id=photo_id, folder_path="/x", name=nev, kind="photo", size=1,
        mtime_ns=1, star=csillag, caption=None, keywords=None, rotate_steps=0,
        filters=None, taken_at=None, orientation=1, width=None, height=None,
    )


@pytest.fixture
def modell(qt_app):
    from picasapy.app.models import PhotoGridModel

    m = PhotoGridModel()
    m.set_photos(
        (
            _rekord(1, "a.jpg", False),
            _rekord(2, "b.jpg", True),
            _rekord(3, "c.jpg", False),
            _rekord(4, "d.jpg", True),
            _rekord(5, "e.jpg", True),
        )
    )
    return m


def _vart(modell, start: int, count: int) -> int:
    """A kért tartomány csillagozott sorai a modell VALÓDI sorrendjében."""
    sorok = [foto.star for foto in modell.photos]
    return sum(1 for csillag in sorok[max(0, start): max(0, start) + count] if csillag)


class TestCsillagozottDarabszam:
    def test_a_teljes_tartomanyban_osszesen_harom(self, modell):
        assert modell.starredCountIn(0, 5) == 3

    @pytest.mark.parametrize(
        ("start", "count"), [(0, 1), (1, 1), (0, 3), (2, 3), (3, 2), (4, 1)]
    )
    def test_a_reszlet_a_modell_sorrendjet_koveti(self, modell, start, count):
        assert modell.starredCountIn(start, count) == _vart(modell, start, count)

    def test_csillagozott_kep_nelkuli_tartomany_nulla(self, modell):
        csillagtalan = [
            i for i, foto in enumerate(modell.photos) if not foto.star
        ]
        assert csillagtalan, "a próbához kell csillagtalan sor"
        assert modell.starredCountIn(csillagtalan[0], 1) == 0

    def test_a_tartomany_a_modell_veget_tulnyulva_levagodik(self, modell):
        assert modell.starredCountIn(3, 100) == _vart(modell, 3, 100)

    @pytest.mark.parametrize(("start", "count"), [(0, 0), (2, 0), (0, -3), (9, 4)])
    def test_ures_vagy_ervenytelen_tartomany_nulla(self, modell, start, count):
        assert modell.starredCountIn(start, count) == 0

    def test_negativ_kezdet_nem_csuszik_vissza_a_vegere(self, modell):
        """A `-1` kezdet nem az utolsó sort jelenti (a Python-szelet
        negatív indexe lenne): 0-ra szorítjuk."""
        assert modell.starredCountIn(-1, 2) == _vart(modell, 0, 2)

    def test_az_ures_modellben_nulla(self, qt_app):
        from picasapy.app.models import PhotoGridModel

        assert PhotoGridModel().starredCountIn(0, 10) == 0

    def test_a_csillag_valtozasa_a_szamlalon_is_latszik(self, modell):
        elotte = modell.starredCountIn(0, 5)
        csillagtalan = next(f for f in modell.photos if not f.star)
        from dataclasses import replace

        modell.update_photo(csillagtalan.id, replace(csillagtalan, star=True))

        assert modell.starredCountIn(0, 5) == elotte + 1
