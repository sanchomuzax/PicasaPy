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
        ["git", "log", "-1", "--format=%ad",
         f"--date=format:{eredet.IDO_ALAK}", "--", str(ut)],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    ).stdout.strip()
    assert eredet.forras_ideje(ut) == vart


def test_forras_datum_nem_kovetett_fajlnal_a_fajl_idejere_esik_vissza(tmp_path):
    """Ha a fájl nincs a gitben, a módosítás ideje a forrás kora."""
    f = tmp_path / "meres.json"
    f.write_text("{}", encoding="utf-8")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", eredet.forras_ideje(f))


def test_forras_datum_hianyzo_fajlnal_nem_dob():
    """Hiányzó forrás nem boríthatja fel a lapot — jelöletlen marad."""
    assert eredet.forras_ideje(ROOT / "nincs-ilyen-fajl.json") is None


def test_eredet_sor_tartalmazza_az_idopontot_es_az_esemenyt():
    sor = eredet.eredet_sor("2026-08-12 14:07", "egy bináris kutatási kör importál")
    assert "2026-08-12 14:07" in sor
    assert "egy bináris kutatási kör importál" in sor
    assert 'class="eredet"' in sor


def test_eredet_sor_escapel():
    sor = eredet.eredet_sor("2026-08-12 14:07", "a <script> jelre")
    assert "<script>" not in sor
    assert "&lt;script&gt;" in sor


def test_eredet_sor_idopont_nelkul_is_ertelmes():
    """Ismeretlen forrásidőnél az esemény akkor is kimegy."""
    sor = eredet.eredet_sor(None, "egy kutatási kör újramér")
    assert "egy kutatási kör újramér" in sor
    assert "eredet" in sor


def _lap_html() -> str:
    """Az állapotlap HTML-je üres, de szerkezetileg teljes adathalmazzal."""
    lap = _modul("allapotlap")
    return lap.epits(
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


def test_minden_eredet_sorban_PERCES_idopont_van():
    """#2057: a puszta dátumból nem ellenőrizhető, mikor frissült."""
    html = _lap_html()
    idok = re.findall(r'<time datetime="([^"]+)"', html)
    assert idok, "nincs egyetlen időbélyeg sem"
    rossz = [i for i in idok if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", i)]
    assert not rossz, f"nem perces időpont: {rossz}"


def test_az_eredet_sor_nem_a_lekerdezes_mechanikajat_irja_le():
    """#2057: »élő GitHub-lekérdezés« azt mondta meg, HOGYAN jön az adat.

    A kérdés az, MITŐL lesz más a tartalom — kiadás, fejlesztői kör, kutatás.
    """
    html = _lap_html()
    sorok = re.findall(r'<p class="eredet">(.*?)</p>', html, re.S)
    assert sorok
    tiltott = ("lekérdezés", "futáskor", "GitHub-lekérdezés")
    vetkes = [s for s in sorok if any(sz in s for sz in tiltott)]
    assert not vetkes, f"a mechanikát írja le az ok helyett: {vetkes}"
