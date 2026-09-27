"""#3681: a mentés-panel „Készlet módosítása…" gombja a hivatalos
„Készlet szerkesztése" feliratot kapja.

A `publish/editbackupset` gomb angol forrása (`Edit Set...`) marad — csak a
magyar FORDÍTÁS változik. A `docs/specs/biztonsagi-mentes.md` 10.2 szakasza
a szerkesztő PÁRBESZÉD címét („Mentési készlet szerkesztése") és gombját
(„Módosítás") rögzíti; a #3681 jegy a PANEL „Edit Set..." gombjára kéri
ugyanezt az igét („szerkeszt…") a korábbi „módosítás" helyett.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_TS = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"


def _kontextus_blokk(nev: str) -> str:
    szoveg = _TS.read_text(encoding="utf-8")
    kezd = szoveg.index(f"<name>{nev}</name>")
    return szoveg[kezd:szoveg.index("</context>", kezd)]


def test_a_szerkesztes_gomb_forditasa_HIVATALOS():
    blokk = _kontextus_blokk("PublishPanel")
    kezd = blokk.index("<source>Edit Set...</source>")
    uzenet = blokk[kezd:blokk.index("</message>", kezd)]
    assert "<translation>Készlet szerkesztése</translation>" in uzenet, (
        "a hivatalos felirat 'Készlet szerkesztése', nem 'Készlet módosítása…'"
    )


def test_a_qm_bol_is_a_hivatalos_felirat_jon():
    from PySide6.QtCore import QCoreApplication, QTranslator

    QCoreApplication.instance() or QCoreApplication([])
    fordito = QTranslator()
    assert fordito.load("picasapy_hu", str(_TS.parent))
    assert fordito.translate("PublishPanel", "Edit Set...") == "Készlet szerkesztése"
