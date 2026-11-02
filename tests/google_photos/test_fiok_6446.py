"""A belépett Google-fiók e-mail-címe a belépési válaszból (#6446)."""

from __future__ import annotations

import pytest

from picasapy.google_photos_fiok import account_email_from_tokens
from support.google_fiok import PROBA_EMAIL, PROBA_REFRESH, id_token


def test_az_id_token_torzsebol_az_email_olvashato():
    tokens = {"refresh_token": PROBA_REFRESH, "id_token": id_token({"email": PROBA_EMAIL})}

    assert account_email_from_tokens(tokens) == PROBA_EMAIL


def test_id_token_nelkul_nincs_fiok():
    assert account_email_from_tokens({"refresh_token": PROBA_REFRESH}) == ""


@pytest.mark.parametrize(
    "token",
    [
        "nem-jwt",
        "a.b",
        "a.!!!.c",
        id_token(["nem", "szotar"]),
        id_token({"sub": "1234"}),
        id_token({"email": 42}),
    ],
)
def test_serult_vagy_hianyos_id_token_nem_ad_fiokot(token):
    assert account_email_from_tokens({"id_token": token}) == ""


def test_nem_szoveges_tokenvalasz_nem_ad_fiokot():
    assert account_email_from_tokens(None) == ""  # type: ignore[arg-type]
