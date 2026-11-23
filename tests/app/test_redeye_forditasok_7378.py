"""#7378: a Vörösszem panel és az Info ablak fordításai mind a 41 nyelven.

A hivatalos `RedEye::DragToSelectMessage` az egész útmutató bekezdést ÉS a
megjegyzés mondatát tartalmazza, `\\n`-nel elválasztva. A panel megjegyzés-sora
csak az UTOLSÓ mondat: a TS-fordítás nem lehet az egész bekezdés (a panel az
útmutatót külön címkén már kiírja, és a literál `\\n` a felületre kerülne).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
_NYELVEK = sorted(p for p in _I18N.glob("picasapy_*.ts"))

_NOTE = "Note: You can click on a box to delete a change."
_CIM = "Redeye Repair"
_INFO_SZOVEG = "This image's orientation has been modified by the Straighten tool, "
#: egy mondat: a hivatalos fordítások az angolnál (49 jel) legfeljebb ennyivel hosszabbak
_MONDAT_FELSO_HATAR = 3 * len(_NOTE)


def _fordites(ts: Path, forras_eleje: str) -> tuple[str, str]:
    """(fordítás, típus) az adott forrásszövegű ELSŐ üzenetből."""
    szoveg = ts.read_text(encoding="utf-8")
    i = szoveg.index(f"<source>{forras_eleje}")
    egyezes = re.compile(r"<translation([^>]*)>(.*?)</translation>", re.S).search(szoveg, i)
    assert egyezes is not None, f"{ts.name}: nincs <translation> a forrás után"
    return egyezes.group(2), egyezes.group(1)


def test_van_41_nyelv():
    assert len(_NYELVEK) == 41


@pytest.mark.parametrize("ts", _NYELVEK, ids=lambda p: p.stem)
def test_a_megjegyzes_forditasa_egyetlen_mondat(ts):
    szoveg, tipus = _fordites(ts, _NOTE + "</source>")
    assert "unfinished" not in tipus
    assert szoveg.strip(), f"{ts.name}: üres a megjegyzés fordítása"
    assert "\\n" not in szoveg, f"{ts.name}: literál \\n került a megjegyzés-sorba"
    assert "\n" not in szoveg, f"{ts.name}: sortörés került a megjegyzés-sorba"
    assert len(szoveg) <= _MONDAT_FELSO_HATAR, (
        f"{ts.name}: a megjegyzés fordítása {len(szoveg)} jel, ez nem egyetlen mondat"
    )


@pytest.mark.parametrize("ts", _NYELVEK, ids=lambda p: p.stem)
def test_a_cim_es_az_info_szoveg_le_van_forditva(ts):
    for forras in (_CIM + "</source>", _INFO_SZOVEG):
        szoveg, tipus = _fordites(ts, forras)
        assert "unfinished" not in tipus, f"{ts.name}: befejezetlen: {forras[:30]}"
        assert szoveg.strip(), f"{ts.name}: üres fordítás: {forras[:30]}"
