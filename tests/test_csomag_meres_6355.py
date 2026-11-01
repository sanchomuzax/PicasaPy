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


def _indulo_eredmeny(ms: float | None, *, kep_kotelezo: bool = False, kep_info=None) -> dict:
    sorok = []
    if ms is not None:
        sorok.append(
            (_INDULT + timedelta(milliseconds=ms), csomag_meres._INDULOABLAK)
        )
    return {
        "indult": _INDULT,
        "sorok": sorok,
        "indulo_hatar_ms": 1000,
        "indulo_kep_kotelezo": kep_kotelezo,
        "indulo_kep_info": kep_info,
        "indulo_kep_hiba": None,
    }


def test_az_induloablak_ideje_a_folyamat_inditasatol_szamit():
    assert csomag_meres.induloablak_ms(_indulo_eredmeny(742)) == 742
    assert csomag_meres.induloablak_ms(_indulo_eredmeny(None)) is None


def test_az_indulo_hatar_alatt_zold_felett_piros():
    assert csomag_meres.indulo_hatar_hiba(
        "csomagolt", _indulo_eredmeny(999), 1000
    ) is None
    assert "1001 ms" in csomag_meres.indulo_hatar_hiba(
        "csomagolt", _indulo_eredmeny(1001), 1000
    )
    assert "nem jelent meg" in csomag_meres.indulo_hatar_hiba(
        "csomagolt", _indulo_eredmeny(None), 1000
    )


def test_a_windowsos_kapu_a_renderelt_also_sort_is_ellenorzi():
    nincs_kep = _indulo_eredmeny(500, kep_kotelezo=True)
    assert "képe nem volt ellenőrizhető" in csomag_meres.indulo_hatar_hiba(
        "csomagolt", nincs_kep, 1000
    )
    van_kep = _indulo_eredmeny(500, kep_kotelezo=True, kep_info=(420, 248, 2))
    assert csomag_meres.indulo_hatar_hiba("csomagolt", van_kep, 1000) is None


def test_a_renderelt_indulokepen_a_szovegmentes_also_savot_meri():
    from io import BytesIO

    from PIL import Image

    image = Image.new("RGB", (8, 8), "#568fb7")
    image.putpixel((0, 6), (205, 205, 205))
    buffer = BytesIO()
    image.save(buffer, "PNG")
    assert csomag_meres._renderelt_indulokep_ellenorzese(buffer.getvalue()) == (
        (8, 8, 2),
        None,
    )

    image = Image.new("RGB", (8, 8), "#ffffff")
    buffer = BytesIO()
    image.save(buffer, "PNG")
    info, error = csomag_meres._renderelt_indulokep_ellenorzese(buffer.getvalue())
    assert info is None and "alsó sávja" in error


def test_a_meresi_jelentes_kiirja_az_induloablak_ms_idejet():
    eredmeny = _indulo_eredmeny(426, kep_info=(420, 248, 2))
    eredmeny.update(
        {
            "kod": 0,
            "fal_mp": 2.0,
            "kimenet": "",
            "indulo_kep_kotelezo": True,
        }
    )
    report = csomag_meres._jelentes("csomagolt", 1, eredmeny)
    assert "426 ms" in report
    assert "renderelt indulókép ellenőrizve" in report


def test_a_kepes_konyvtar_mappankent_50_kepet_kap(tmp_path):
    csomag_meres._kepekkel_tolt(tmp_path, 120)
    mappak = sorted(p.name for p in tmp_path.iterdir() if p.is_dir())
    assert mappak == ["album-000", "album-001", "album-002"]
    assert len(list((tmp_path / "album-000").glob("*.jpg"))) == 50
    assert len(list((tmp_path / "album-002").glob("*.jpg"))) == 20


def _indulo(ms: float | None) -> dict:
    sorok = []
    if ms is not None:
        sorok.append((_INDULT + timedelta(milliseconds=ms), csomag_meres._INDULOABLAK))
    return {"indult": _INDULT, "sorok": sorok, "indulo_kep_kotelezo": False}


def test_az_induloablak_kapuja_a_kozeperteket_nezi():
    """#6367: egy kiugró (CI-zaj) mérés nem dönt, a középérték igen."""
    kiugro = [_indulo(784), _indulo(8398), _indulo(386)]
    assert csomag_meres.indulo_kozepertek_hiba("indulo", kiugro, 1000) is None
    lassu = [_indulo(1500), _indulo(1600), _indulo(400)]
    assert "középértéke 1500 ms" in csomag_meres.indulo_kozepertek_hiba("indulo", lassu, 1000)
    hianyzo = [_indulo(400), _indulo(None), _indulo(400)]
    assert "nem jelent meg" in csomag_meres.indulo_kozepertek_hiba("indulo", hianyzo, 1000)
