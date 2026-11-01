"""A Google OAuth-kliens forrásainak elsőbbségi sorrendje (#6361)."""

from __future__ import annotations

import json

from picasapy.google_oauth_beepitett import get_google_oauth_credentials


def _csomagolt_kliens(utvonal, client_id="csomagolt-id", secret="csomagolt-titok"):
    utvonal.write_text(
        json.dumps({"client_id": client_id, "client_secret": secret}),
        encoding="utf-8",
    )
    return utvonal


def test_a_felhasznaloi_kliens_megelozi_a_kornyezetet_es_a_csomagot(tmp_path):
    csomagfajl = _csomagolt_kliens(tmp_path / "_google_oauth.json")

    eredmeny = get_google_oauth_credentials(
        "sajat-id",
        "sajat-titok",
        environ={
            "PICASAPY_GOOGLE_CLIENT_ID": "kornyezeti-id",
            "PICASAPY_GOOGLE_CLIENT_SECRET": "kornyezeti-titok",
        },
        credentials_file=csomagfajl,
    )

    assert eredmeny == ("sajat-id", "sajat-titok")


def test_a_kornyezeti_kliens_megelozi_a_csomagolt_klienset(tmp_path):
    csomagfajl = _csomagolt_kliens(tmp_path / "_google_oauth.json")

    eredmeny = get_google_oauth_credentials(
        environ={
            "PICASAPY_GOOGLE_CLIENT_ID": "kornyezeti-id",
            "PICASAPY_GOOGLE_CLIENT_SECRET": "kornyezeti-titok",
        },
        credentials_file=csomagfajl,
    )

    assert eredmeny == ("kornyezeti-id", "kornyezeti-titok")


def test_a_csomagolt_kliens_hasznalhato_kornyezeti_beallitas_nelkul(tmp_path):
    csomagfajl = _csomagolt_kliens(tmp_path / "_google_oauth.json")

    eredmeny = get_google_oauth_credentials(
        environ={},
        credentials_file=csomagfajl,
    )

    assert eredmeny == ("csomagolt-id", "csomagolt-titok")


def test_hianyos_vagy_hibas_forrasbol_nincs_kliens(tmp_path):
    csomagfajl = tmp_path / "_google_oauth.json"
    csomagfajl.write_text('{"client_id":"csak-azonosito"}', encoding="utf-8")

    assert get_google_oauth_credentials(
        environ={"PICASAPY_GOOGLE_CLIENT_ID": "csak-azonosito"},
        credentials_file=csomagfajl,
    ) is None

