"""A két szabálykönyv (CLAUDE.md, AGENTS.md) ne csússzon szét.

A projekten KÉT eszköz dolgozik: a Claude Code a `CLAUDE.md`-t olvassa
indításkor, a Codex az `AGENTS.md`-t. Ami csak az egyikbe kerül be, azt a
másik eszköz munkamenetei SOHA nem látják — némán, hibaüzenet nélkül.

Bizonyíték (2026-08-19/20): a mért importgráfból készült sávtérkép — ami épp
azt mondja meg, mely területek művelhetők párhuzamosan és mely szerződések
vágnak át többet — csak a `CLAUDE.md`-be került be. A Codex-munkamenetek egy
napig úgy dolgoztak, hogy nem látták az ütközés-megelőzés térképét. Kézzel
senki nem vette észre; ez a teszt azért van, hogy ne is kelljen észrevenni.

Nem a teljes azonosságot követeljük meg: a két fájl eszközfüggő részei
(hook-útvonalak, klónozási lépések) szándékosan eltérnek.
"""

from __future__ import annotations

import pathlib

import pytest

_GYOKER = pathlib.Path(__file__).resolve().parents[1]
_CLAUDE = _GYOKER / "CLAUDE.md"
_AGENTS = _GYOKER / "AGENTS.md"

#: Ezeknek a szakaszoknak MINDKÉT szabálykönyvben szerepelniük kell. A lista
#: bővíthető: ha új, eszközfüggetlen szabály kerül az egyikbe, ide is vedd fel.
_KOTELEZO_SZAKASZOK = (
    "## 🗣️ Nyelv: a felhasználóval MINDIG magyarul",
    "## ⚠️ Párhuzamos sessionök",
    "## 🗺️ Sávtérkép — párhuzamos munka és szerződések",
    "## Fejlesztés",
)

#: Ezek a szakaszok SZÓ SZERINT egyezzenek. Olyan tartalom való ide, aminek az
#: eltérése két eszköz eltérő viselkedését okozná (pl. eltérő sávtérkép esetén
#: a két eszköz mást tartana párhuzamosíthatónak).
_SZO_SZERINT_EGYEZO = ("## 🗺️ Sávtérkép — párhuzamos munka és szerződések",)


def _szakasz(szoveg: str, cim: str) -> str:
    """Egy `## ` szakasz tartalma a következő `## ` címig."""
    kezdet = szoveg.index(cim)
    kovetkezo = szoveg.find("\n## ", kezdet + len(cim))
    return szoveg[kezdet : kovetkezo if kovetkezo != -1 else len(szoveg)].strip()


@pytest.mark.parametrize("cim", _KOTELEZO_SZAKASZOK)
def test_a_szakasz_mindket_szabalykonyvben_megvan(cim: str) -> None:
    hianyzik = [
        ut.name
        for ut in (_CLAUDE, _AGENTS)
        if cim not in ut.read_text(encoding="utf-8")
    ]
    assert not hianyzik, (
        f"a(z) „{cim}” szakasz hiányzik innen: {', '.join(hianyzik)} — "
        "amit csak az egyik szabálykönyvbe írsz, azt a másik eszköz "
        "munkamenetei sosem látják"
    )


@pytest.mark.parametrize("cim", _SZO_SZERINT_EGYEZO)
def test_a_szakasz_szo_szerint_egyezik(cim: str) -> None:
    claude = _szakasz(_CLAUDE.read_text(encoding="utf-8"), cim)
    agents = _szakasz(_AGENTS.read_text(encoding="utf-8"), cim)
    assert claude == agents, (
        f"a(z) „{cim}” szakasz ELTÉR a két szabálykönyvben. Ez nem stílus "
        "kérdése: a két eszköz mást tartana igaznak ugyanarról a kódról. "
        "Másold át a szakaszt változtatás nélkül."
    )


def test_a_savterkep_a_meresi_alapjat_is_hordozza() -> None:
    """A sávtérkép a MÉRT forrófájlokkal együtt ér valamit, nem önmagában."""
    for ut in (_CLAUDE, _AGENTS):
        szakasz = _szakasz(ut.read_text(encoding="utf-8"), _SZO_SZERINT_EGYEZO[0])
        assert "Main.qml" in szakasz, f"{ut.name}: hiányzik a forrófájl-lista"
        assert "szerződés" in szakasz.lower(), f"{ut.name}: hiányoznak a szerződések"
