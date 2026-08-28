"""Az állapotlap „Mi áll, és kin múlik" szakasza — #1664.

Két hiba volt benne, mindkettőt a tulajdonos vette észre a kész lapon:

1. **duplázás** — a `binaris_kutathato` a `blokkolt` RÉSZHALMAZA, mégis
   egymás mellé került a két csoport, így a #1276 és a #1153 kétszer
   szerepelt ugyanabban a szakaszban;
2. **a cím ellentmondott a tartalomnak** — „Ez vár rád", alatta „Egy sincs.",
   majd négy jegy, ami nem a tulajdonosra vár.
"""

from __future__ import annotations

import collections
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "allapotlap.py"

_spec = importlib.util.spec_from_file_location("allapotlap", SCRIPT)
lap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lap)


def _jegy(n: int, cim: str = "x") -> dict:
    return {"number": n, "title": cim, "created": "2026-01-01T00:00:00Z"}


def _adat(blokkolt: list, binaris: list) -> dict:
    """A `gyujts()` alakja, csak a szakaszhoz szükséges mezőkkel kitöltve."""
    import datetime as dt
    return {
        "ideje": dt.datetime(2026, 8, 27, 22, 0),
        "menu": {"viselkedes": [], "erdemi": [], "csak_nev": [], "sehol": []},
        "kovetkezo": [],
        "jegyek": [],
        "erintetlen": [],
        "spec": {"lapok": 69, "sorok": 44226, "kerdeses": 0},
        "spec_kerdesek": [],
        "ossz": {"blokkolt": blokkolt, "binaris_kutathato": binaris,
                 "felhasznalora_var": []},
    }


def _szakasz(html: str) -> str:
    m = re.search(r"<h2>Mi áll, és kin múlik</h2>.*?</section>", html, re.S)
    assert m, "nincs meg a szakasz"
    return m.group(0)


def test_egy_jegy_csak_egy_csoportban_szerepel() -> None:
    """A #1664 magva: a részhalmaz NEM kerülhet a fölérendelt mellé."""
    kozos = [_jegy(1276), _jegy(1153)]
    html = lap.epits(_adat(blokkolt=kozos + [_jegy(684)], binaris=kozos))
    szamok = re.findall(r'class="num">#(\d+)<', _szakasz(html))
    dup = [k for k, v in collections.Counter(szamok).items() if v > 1]
    assert not dup, f"duplán szereplő jegy: {dup}"
    assert set(szamok) == {"1276", "1153", "684"}, szamok


def test_a_bianris_jegy_a_sajat_csoportjaban_van() -> None:
    html = _szakasz(lap.epits(_adat(blokkolt=[_jegy(1276), _jegy(684)],
                                    binaris=[_jegy(1276)])))
    kulso = html.index("Külső akadályon áll")
    binaris = html.index("Bináris kutatás oldja fel")
    assert html.index("#684") > kulso, "a #684 a külső akadály csoportba való"
    assert html.index("#1276") > binaris, "a #1276 a bináris csoportba való"


def test_a_szakasz_cime_nem_igeri_hogy_minden_a_tulajdonosra_var() -> None:
    html = _szakasz(lap.epits(_adat(blokkolt=[_jegy(684)], binaris=[])))
    assert "Ez vár rád" not in html
    assert "nélküled" in html and "nem rád vár" in html
