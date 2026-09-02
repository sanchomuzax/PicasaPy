"""Szakaszonkénti eredet-sor: mikor frissült, és mitől frissülne — #2046.

A tulajdonos vette észre: a lap fejlécében mai dátum áll, de a tartalom nagy
része hetekig változatlan. A fejléc a GENERÁLÁS idejét írja ki, nem a
forrásadatét — a bináris térkép például a `picasa3-index.sqlite`-ból jön, ami
2026-08-12 óta nem változott.

Ezért minden szakasz alá kell egy sor, ami a FORRÁS dátumát mutatja, és egy
mondatban megmondja, mitől frissülne. Az őr azt védi, hogy új szakasz ne
kerülhessen be eredet-sor nélkül.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _modul(nev: str):
    spec = importlib.util.spec_from_file_location(nev, ROOT / "scripts" / f"{nev}.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


eredet = _modul("szakasz_eredet")


def test_forras_datum_a_git_bejegyzest_adja():
    """Követett fájlnál a git utolsó commit-dátuma a forrás kora."""
    ut = ROOT / "scripts" / "allapotlap.py"
    vart = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(ut)],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    ).stdout.strip()
    assert eredet.forras_datum(ut) == vart


def test_forras_datum_nem_kovetett_fajlnal_a_fajl_idejere_esik_vissza(tmp_path):
    """Ha a fájl nincs a gitben, a módosítás ideje a forrás kora."""
    f = tmp_path / "meres.json"
    f.write_text("{}", encoding="utf-8")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", eredet.forras_datum(f))


def test_forras_datum_hianyzo_fajlnal_nem_dob():
    """Hiányzó forrás nem boríthatja fel a lapot — jelöletlen marad."""
    assert eredet.forras_datum(ROOT / "nincs-ilyen-fajl.json") is None


def test_eredet_sor_tartalmazza_a_datumot_es_a_mondatot():
    sor = eredet.eredet_sor("2026-08-12", "a bináris index újraimportálásakor")
    assert "2026-08-12" in sor
    assert "a bináris index újraimportálásakor" in sor
    assert 'class="eredet"' in sor


def test_eredet_sor_escapel():
    sor = eredet.eredet_sor("2026-08-12", "a <script> jelre")
    assert "<script>" not in sor
    assert "&lt;script&gt;" in sor


def test_eredet_sor_datum_nelkul_is_ertelmes():
    """Ismeretlen forrásdátumnál a mondat akkor is kimegy."""
    sor = eredet.eredet_sor(None, "minden futáskor")
    assert "minden futáskor" in sor
    assert "eredet" in sor


def test_minden_szakasznak_van_eredet_sora():
    """Az őr foga: `<h2>` után eredet-sornak kell jönnie.

    Enélkül egy új szakasz némán bekerülhetne dátum és magyarázat nélkül —
    pontosan az az állapot, amit a #2046 megszüntet.
    """
    lap = _modul("allapotlap")
    html = lap.epits(
        {
            "menu": {
                "viselkedes": ["a"], "erdemi": [], "csak_nev": [], "sehol": [],
            },
            "kovetkezo": [],
            "ui": None,
            "jegyek": [],
            "ossz": {
                "osszes_nyitott": 0, "blokkolt": [], "felhasznalora_var": [],
                "binaris_kutathato": [],
            },
            "erintetlen": [],
            "spec": {"lapok": 0, "sorok": 0},
            "spec_kerdesek": [],
            "kiadasok": [],
            "frissen_lezart": [],
            "ideje": __import__("datetime").datetime.now().astimezone(),
        }
    )
    cimek = re.findall(r"<h2>(.*?)</h2>(.*?)(?=<h2>|\Z)", html, re.S)
    assert cimek, "nem találtam szakaszcímet — a teszt elavult"
    eredet_nelkul = [c for c, blokk in cimek if 'class="eredet"' not in blokk]
    assert not eredet_nelkul, f"eredet-sor nélküli szakasz: {eredet_nelkul}"
