"""A webalbum-feltöltési méret tárolása (#5482).

A Webalbumok fül legördülője öt tételt kínál a sablon sorrendjében. A kulcs
hiányában (vagy hibás értéknél) az 1600-as tétel a kiválasztott.
"""

from __future__ import annotations

import pytest

from picasapy import web_upload_size


def test_a_kulcs_a_bineris_nevet_viseli_a_preferences_csoportban():
    assert web_upload_size.KULCS == "Preferences/PWADefaultSize"


def test_az_ot_tetel_a_sablon_sorrendjeben_van():
    assert web_upload_size.MERETEK == (0, 2048, 1600, 1024, 800)


@pytest.mark.parametrize("ertek", [None, "", "abc", True, 999, "1601", 1.5])
def test_hianyzo_vagy_hibas_ertek_az_1600_tetel(ertek):
    assert web_upload_size.read_index(ertek) == 2


@pytest.mark.parametrize(
    ("ertek", "index"),
    [("0", 0), (2048, 1), ("1600", 2), (1024, 3), ("800", 4)],
)
def test_a_tarolt_meret_a_legordulo_indexe(ertek, index):
    assert web_upload_size.read_index(ertek) == index


@pytest.mark.parametrize("index", range(5))
def test_az_index_es_a_meret_kolcsonosen_visszaalakul(index):
    assert web_upload_size.read_index(web_upload_size.size_at(index)) == index


@pytest.mark.parametrize("index", [-1, 5, 99])
def test_tartomanyon_kivuli_index_az_1600_meret(index):
    assert web_upload_size.size_at(index) == 1600
