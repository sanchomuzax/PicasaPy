"""A Package csak a saját csomagja láttán hagyja ki az építést (#6414).

Az 1.0.14 kiadásnál a kiadási automata a kiadásképet (`toolbar.png`)
előbb töltötte fel, mint ahogy a Package elindult; a `build-and-upload`
job a „van már melléklet" feltétel miatt kihagyta a wheel, az sdist és a
.deb építését. A kihagyás feltétele ezért a wheel jelenléte, nem a
mellékletek száma.

Szövegből olvas, nem `yaml`-lal: a CI-környezetben nincs PyYAML.
"""

from __future__ import annotations

import re
from pathlib import Path

_PACKAGE = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "package.yml"


def _build_job() -> str:
    szoveg = _PACKAGE.read_text(encoding="utf-8")
    eleje = re.search(r"^  build-and-upload:\n", szoveg, re.M)
    assert eleje, "nincs build-and-upload job a package.yml-ben"
    vege = re.search(r"^  [A-Za-z0-9_-]+:\n", szoveg[eleje.end() :], re.M)
    return szoveg[eleje.end() : eleje.end() + vege.start()] if vege else szoveg[eleje.end() :]


def _kihagyo_lekerdezes() -> str:
    job = _build_job()
    sor = next(
        (s for s in job.splitlines() if "gh release view" in s and "--json assets" in s),
        None,
    )
    assert sor, "a build-and-upload nem kérdezi le a kiadás mellékleteit"
    return sor


def test_a_kihagyas_a_wheel_jelenleten_mulik():
    sor = _kihagyo_lekerdezes()
    assert ".whl" in sor, (
        "a kihagyás nem a wheelt keresi: egy kiadáskép vagy más melléklet "
        "is kiváltaná, és a csomagok nem épülnének meg"
    )


def test_a_puszta_mellekletszam_nem_dont():
    sor = _kihagyo_lekerdezes()
    assert "'.assets | length'" not in sor, (
        "a mellékletek puszta száma dönt: a kiadás után azonnal feltöltött "
        "kiadáskép elég ahhoz, hogy a Package semmit ne építsen"
    )
