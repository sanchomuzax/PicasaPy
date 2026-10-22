"""#5559: az Időrend saját spec-lapon marad olvasható."""

from __future__ import annotations

from pathlib import Path

from scripts import menu_lefedettseg as menu
from scripts import nagy_fajl_or

GYOKER = Path(__file__).resolve().parents[2]
REGI_LAP = GYOKER / "docs/specs/picasa-menu-parancsok-viselkedes.md"
UJ_LAP = GYOKER / "docs/specs/picasa-idorend-viselkedes.md"


def test_a_teljes_38_2_szakasz_a_kulon_idorend_lapon_van():
    uj = UJ_LAP.read_text(encoding="utf-8")
    regi = REGI_LAP.read_text(encoding="utf-8")

    assert "#### 38.2.1 " in uj
    assert "#### 38.2.60 " in uj
    assert "#### 38.2.1 " not in regi
    assert "#### 38.2.60 " not in regi
    assert "[picasa-idorend-viselkedes.md](picasa-idorend-viselkedes.md)" in regi
    assert "### 38.3 " in regi


def test_a_lefedettsegmero_mindket_viselkedesi_lapot_olvassa():
    assert "picasa-idorend-viselkedes.md" in menu.VISELKEDES_LAP

    lefedettseg = menu.merd()["viselkedes"]
    assert "ID_VIEW_BW" in lefedettseg
    assert "ID_VIEW_TIMELINE" in lefedettseg


def test_az_index_felsorolja_az_uj_lapot():
    index = (GYOKER / "docs/specs/00-index.md").read_text(encoding="utf-8")

    assert "[picasa-idorend-viselkedes.md](picasa-idorend-viselkedes.md)" in index


def test_a_ket_spec_a_nagyfajl_kuszob_alatt_marad_kivetel_nelkul():
    regi_ut = "docs/specs/picasa-menu-parancsok-viselkedes.md"
    assert regi_ut not in nagy_fajl_or.KIVETELEK
    assert REGI_LAP.stat().st_size < nagy_fajl_or.KUSZOB
    assert UJ_LAP.stat().st_size < nagy_fajl_or.KUSZOB


def test_a_bemutato_kutatas_masodik_lapon_folytatodik_5599():
    masodik = GYOKER / "docs/specs/picasa-idorend-bemutato-kutatas.md"
    szoveg = masodik.read_text(encoding="utf-8")

    assert "#### 38.2.61 " in szoveg
    assert "#### 38.2.61 " not in UJ_LAP.read_text(encoding="utf-8").replace(
        "#### 38.2.61 és a további szakaszok", ""
    )
    assert masodik.stat().st_size < nagy_fajl_or.KUSZOB
    assert "picasa-idorend-bemutato-kutatas.md" in menu.VISELKEDES_LAP
