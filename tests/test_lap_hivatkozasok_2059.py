"""A lapon a jegyszám és a kiadás legyen kattintható — #2059.

A tulajdonos többször kérte chatben, de jegy nem készült róla, ezért elveszett.
A lap fő haszna, hogy ne kelljen a GitHubot böngészni; ha viszont a jegycímről
nem lehet a jegyre jutni, a böngészés mégis kézzel megy.
"""

from __future__ import annotations

import datetime
import importlib.util
import re
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]


def _modul(nev: str):
    spec = importlib.util.spec_from_file_location(nev, GYOKER / "scripts" / f"{nev}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lap = _modul("allapotlap")


def _html() -> str:
    return lap.epits(
        {
            "menu": {"viselkedes": ["a"], "erdemi": [], "csak_nev": [], "sehol": []},
            "kovetkezo": [],
            "ui": None,
            "jegyek": [],
            "ossz": {
                "osszes_nyitott": 1,
                "blokkolt": [{"number": 4242, "title": "blokkolt jegy"}],
                "felhasznalora_var": [{"number": 1111, "title": "rád vár"}],
                "binaris_kutathato": [],
            },
            "erintetlen": [{"number": 909, "title": "régóta érintetlen",
                            "created": "2026-01-01T00:00:00Z"}],
            "spec": {"lapok": 0, "sorok": 0},
            "spec_kerdesek": [],
            "kiadasok": [{"verzio": "v0.8.232", "mikor": "2026-09-02 19:50"}],
            "frissen_lezart": [{"number": 2058, "title": "frissen lezárt"}],
            "ideje": datetime.datetime.now().astimezone(),
        }
    )


def test_a_jegyszamok_a_jegyre_mutatnak():
    html = _html()
    for szam in (4242, 1111, 909, 2058):
        assert f'href="https://github.com/sanchomuzax/PicasaPy/issues/{szam}"' in html, (
            f"a #{szam} nem kattintható"
        )


def test_a_kiadas_a_kiadas_oldalara_mutat():
    assert 'href="https://github.com/sanchomuzax/PicasaPy/releases/tag/v0.8.232"' in _html()


def test_nem_marad_hivatkozas_nelkuli_jegyszam():
    """Az őr foga: `#NNNN` csak horgonyon belül állhat a listákban."""
    html = _html()
    listak = re.findall(r"<ul class=\"tickets\">(.*?)</ul>", html, re.S)
    assert listak, "nincs jegylista — a teszt elavult"
    for blokk in listak:
        csupasz = re.sub(r"<a\b[^>]*>.*?</a>", "", blokk, flags=re.S)
        maradek = re.findall(r"#\d{2,}", csupasz)
        assert not maradek, f"hivatkozás nélküli jegyszám: {maradek}"
