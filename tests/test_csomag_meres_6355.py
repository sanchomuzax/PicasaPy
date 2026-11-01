"""A windowsos indulásmérés 5 s-os kapuja (#6355)."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_UT = Path(__file__).resolve().parents[1] / "packaging" / "windows" / "csomag_meres.py"
_spec = importlib.util.spec_from_file_location("csomag_meres_6355", _UT)
csomag_meres = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(csomag_meres)

_INDULT = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)


def _eredmeny(foablak_s: float | None) -> dict:
    sorok = [(_INDULT + timedelta(seconds=0.5), "Indulási argumentumok beolvasva")]
    if foablak_s is not None:
        sorok.append((_INDULT + timedelta(seconds=foablak_s), csomag_meres._SIKER))
    return {"indult": _INDULT, "sorok": sorok}


def test_a_foablak_ideje_a_folyamat_inditasatol_szamit():
    assert csomag_meres.foablak_mp(_eredmeny(4.25)) == 4.25
    assert csomag_meres.foablak_mp(_eredmeny(None)) is None


def test_a_hatar_alatti_indulas_rendben_van():
    assert csomag_meres.hatar_hiba("csomagolt", _eredmeny(4.9), 5.0) is None


def test_a_hatar_feletti_indulas_piros():
    uzenet = csomag_meres.hatar_hiba("csomagolt", _eredmeny(31.2), 5.0)
    assert uzenet is not None and "31.20 s" in uzenet


def test_meg_nem_jelent_foablak_piros():
    assert "nem jelent meg" in csomag_meres.hatar_hiba("csomagolt", _eredmeny(None), 5.0)


def test_hatar_nelkul_nincs_kapu():
    assert csomag_meres.hatar_hiba("csomagolt", _eredmeny(60.0), None) is None


def test_a_kepes_konyvtar_mappankent_50_kepet_kap(tmp_path):
    csomag_meres._kepekkel_tolt(tmp_path, 120)
    mappak = sorted(p.name for p in tmp_path.iterdir() if p.is_dir())
    assert mappak == ["album-000", "album-001", "album-002"]
    assert len(list((tmp_path / "album-000").glob("*.jpg"))) == 50
    assert len(list((tmp_path / "album-002").glob("*.jpg"))) == 20
