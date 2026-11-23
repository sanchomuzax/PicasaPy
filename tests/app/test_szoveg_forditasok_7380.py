"""#7380: a Szöveg eszköz új és átnevezett szövegei minden nyelven készek.

Az eredeti Picasa `edittextpanel/clearall` vezérlője „Clear All” feliratú,
a „Remove all existing text” ennek a tooltipje; a képre gépelhető szöveg
hintje az `EditText::GhostText` (`Type anywhere to add text`). A fordítások
az eredeti nyelvi erőforrásból jönnek, nem a mi fordításunk.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import picasapy.app

_I18N = Path(picasapy.app.__file__).parent / "i18n"
_NYELVEK = sorted(_I18N.glob("picasapy_*.ts"))


def _uzenetek(ts: Path, kontextus: str) -> dict[str, ET.Element]:
    gyoker = ET.parse(ts).getroot()
    for ctx in gyoker.findall("context"):
        if ctx.findtext("name") == kontextus:
            return {m.findtext("source"): m for m in ctx.findall("message")}
    return {}


def test_mind_a_negyvenegy_nyelv_megvan() -> None:
    assert len(_NYELVEK) == 41


@pytest.mark.parametrize("ts", _NYELVEK, ids=lambda p: p.stem)
def test_minden_nyelven_megvan_a_harom_szoveg_befejezett_forditassal(
    ts: Path,
) -> None:
    panel = _uzenetek(ts, "EditorTextPanel")
    hint = _uzenetek(ts, "PhotoViewerTextInput")
    for forras, uzenet in (
        ("Clear All", panel.get("Clear All")),
        ("Remove all existing text", panel.get("Remove all existing text")),
        ("Type anywhere to add text", hint.get("Type anywhere to add text")),
    ):
        assert uzenet is not None, f"{ts.name}: hiányzik: {forras}"
        fordites = uzenet.find("translation")
        assert fordites is not None and (fordites.text or "").strip(), (
            f"{ts.name}: üres fordítás: {forras}"
        )
        assert fordites.get("type") != "unfinished", (
            f"{ts.name}: befejezetlen fordítás: {forras}"
        )
        assert "picasapy-origin: picasa" in (uzenet.findtext("extracomment") or ""), (
            f"{ts.name}: a(z) {forras} nem az eredeti erőforrásból jelölt"
        )


@pytest.mark.parametrize("ts", _NYELVEK, ids=lambda p: p.stem)
def test_a_regi_magyarazo_sor_kikerult_a_panel_szotarabol(ts: Path) -> None:
    assert (
        "Type your text, then click on the photo to place it."
        not in _uzenetek(ts, "EditorTextPanel")
    )


def test_a_magyar_szovegek_az_eredeti_picasa_eroforrasabol_vannak() -> None:
    ts = _I18N / "picasapy_hu.ts"
    panel = _uzenetek(ts, "EditorTextPanel")
    hint = _uzenetek(ts, "PhotoViewerTextInput")
    assert panel["Clear All"].findtext("translation") == "Az összes törlése"
    assert (
        panel["Remove all existing text"].findtext("translation")
        == "Az összes meglévő szöveg eltávolítása"
    )
    assert (
        hint["Type anywhere to add text"].findtext("translation")
        == "Szöveg elhelyezéséhez kezdjen el gépelni"
    )
