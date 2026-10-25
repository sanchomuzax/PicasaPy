"""#5900: a felirat utáni ini-frissítés átmeneti hibánál újrapróbál."""

from __future__ import annotations

import pytest

from picasapy.app import ini_ujraprobalas
from picasapy.app.ini_ujraprobalas import update_document_ujraprobalva
from picasapy.ini import IniConflictError, load_document, with_backuphash


def _ini(tmp_path):
    ini = tmp_path / ".picasa.ini"
    ini.write_text("[a.jpg]\ncaption=x\n", encoding="utf-8")
    return ini


def test_elso_permissionerror_utan_a_masodik_proba_beirja(tmp_path, monkeypatch):
    ini = _ini(tmp_path)
    eredeti = ini_ujraprobalas.update_document
    hivasok = []

    def egyszer_bukik(path, mutate, *, backup):
        hivasok.append(1)
        if len(hivasok) == 1:
            raise PermissionError("zárolt")
        return eredeti(path, mutate, backup=backup)

    monkeypatch.setattr(ini_ujraprobalas, "update_document", egyszer_bukik)
    alvasok = []
    update_document_ujraprobalva(
        ini, lambda d: with_backuphash(d, "a.jpg"), backup=False, alvas=alvasok.append
    )
    assert len(hivasok) == 2
    assert alvasok == [pytest.approx(0.1)]
    assert load_document(ini).section("a.jpg").get("backuphash")


def test_tartos_hiba_az_utolso_probalkozas_utan_tovabbmegy(tmp_path, monkeypatch):
    ini = _ini(tmp_path)

    def mindig_utkozik(path, mutate, *, backup):
        raise IniConflictError("változott")

    monkeypatch.setattr(ini_ujraprobalas, "update_document", mindig_utkozik)
    alvasok = []
    with pytest.raises(IniConflictError):
        update_document_ujraprobalva(
            ini, lambda d: d, backup=False, probak=3, alvas=alvasok.append
        )
    assert alvasok == [pytest.approx(0.1), pytest.approx(0.2)]


def test_mas_hiba_nem_probal_ujra(tmp_path, monkeypatch):
    ini = _ini(tmp_path)
    hivasok = []

    def masik_hiba(path, mutate, *, backup):
        hivasok.append(1)
        raise ValueError("nem átmeneti")

    monkeypatch.setattr(ini_ujraprobalas, "update_document", masik_hiba)
    with pytest.raises(ValueError):
        update_document_ujraprobalva(ini, lambda d: d, alvas=lambda _: None)
    assert len(hivasok) == 1


def test_nulla_proba_hiba(tmp_path):
    with pytest.raises(ValueError):
        update_document_ujraprobalva(_ini(tmp_path), lambda d: d, probak=0)
