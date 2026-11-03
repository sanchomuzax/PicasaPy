"""A főablak 5 s-os kapuja a három indítás középértékére vonatkozik (#6461).

A windowsos futtatógépen az első, hideg indulás a kód változása nélkül is
3 és 7 s között szórt (mérve 2026-11-02, hét futáson), és a kapu emiatt a
kiadás nyilvánossá tételét is megállította. A határ ezért a középértékre
vonatkozik, mint az indulóablaknál (#6367), egy-egy indítás pedig csak egy
felső plafon fölött bukik el, így a valóban lassú hideg indulás továbbra is
piros.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_UT = Path(__file__).resolve().parents[1] / "packaging" / "windows" / "csomag_meres.py"
_spec = importlib.util.spec_from_file_location("csomag_meres_6461", _UT)
csomag_meres = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(csomag_meres)

_INDULT = datetime(2026, 11, 2, 22, 0, 0, tzinfo=timezone.utc)


def _eredmeny(foablak_s: float | None) -> dict:
    sorok = [(_INDULT + timedelta(seconds=0.5), "Indulási argumentumok beolvasva")]
    if foablak_s is not None:
        sorok.append((_INDULT + timedelta(seconds=foablak_s), csomag_meres._SIKER))
    return {"indult": _INDULT, "sorok": sorok}


def test_a_hideg_elso_inditas_kiugrasa_nem_dont_ha_a_kozepertek_jo():
    # a 2026-11-02-i bukás számai: 5,55 s, 3,49 s, 3,44 s
    meresek = [_eredmeny(5.55), _eredmeny(3.49), _eredmeny(3.44)]
    assert csomag_meres.foablak_kozepertek_hiba("indulo", meresek, 5.0) is None


def test_a_lassu_kozepertek_piros():
    meresek = [_eredmeny(6.2), _eredmeny(5.4), _eredmeny(3.0)]
    uzenet = csomag_meres.foablak_kozepertek_hiba("indulo", meresek, 5.0)
    assert uzenet is not None and "középértéke 5.40 s" in uzenet


def test_ha_egy_inditasnal_nem_jelent_meg_a_foablak_piros():
    meresek = [_eredmeny(3.0), _eredmeny(None), _eredmeny(3.0)]
    assert "nem jelent meg" in csomag_meres.foablak_kozepertek_hiba("indulo", meresek, 5.0)


def test_hatar_nelkul_nincs_kozepertek_kapu():
    assert csomag_meres.foablak_kozepertek_hiba("indulo", [_eredmeny(60.0)], None) is None


def test_egy_inditas_a_plafon_folott_akkor_is_piros_ha_a_kozepertek_jo():
    plafon = csomag_meres.egyedi_plafon_mp(5.0)
    assert plafon == 8.0
    assert csomag_meres.hatar_hiba("indulo #1", _eredmeny(8.5), plafon) is not None
    assert csomag_meres.hatar_hiba("indulo #1", _eredmeny(7.05), plafon) is None


def test_plafon_hatar_nelkul_sincs():
    assert csomag_meres.egyedi_plafon_mp(None) is None


def test_a_hideg_elso_futas_plafon_feletti_ideje_figyelmeztetes_csak():
    hiba, figyelmeztetes = csomag_meres.egyedi_hatar_dontes(
        "indulo #1", _eredmeny(18.26), 8.0, 1
    )

    assert hiba is None
    assert figyelmeztetes is not None
    assert "18.26 s" in figyelmeztetes
    assert "hideg első" in figyelmeztetes


def test_a_meleg_futas_plafon_feletti_ideje_tovabbra_is_piros():
    hiba, figyelmeztetes = csomag_meres.egyedi_hatar_dontes(
        "indulo #2", _eredmeny(8.01), 8.0, 2
    )

    assert hiba is not None and "8.01 s" in hiba
    assert figyelmeztetes is None


def test_az_elso_futas_hianyzo_foablaka_tovabbra_is_piros():
    hiba, figyelmeztetes = csomag_meres.egyedi_hatar_dontes(
        "indulo #1", _eredmeny(None), 8.0, 1
    )

    assert hiba is not None and "nem jelent meg" in hiba
    assert figyelmeztetes is None


def test_a_hideg_elso_futas_a_harmas_plafon_folott_piros():
    hiba, figyelmeztetes = csomag_meres.egyedi_hatar_dontes(
        "indulo #1", _eredmeny(41.0), 8.0, 1
    )

    assert hiba is not None and "41.00 s" in hiba and "24.0 s" in hiba
    assert figyelmeztetes is None
