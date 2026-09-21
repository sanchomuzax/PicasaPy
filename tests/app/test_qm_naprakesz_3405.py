"""#3405: a lefordított `.qm` a `.ts`-szel NAPRAKÉSZ.

A futásidő a `.qm`-et tölti be, nem a `.ts`-t. Ha egy jegy a `.ts`
`<source>` szövegét módosítja, de a `.qm`-et nem építi újra, az új
forrásszövegnek nincs fordítása: a felület magyarul is angolul mutatja. Így
ment ki a v0.8.534 (#3408) — a kollázs hat feliratáé —, mert a meglévő
teljességi őr (`test_i18n_completeness.py`) a `.ts`-t nézi.

Ez az őr minden kész, egyes számú `.ts`-fordítást a TÉNYLEGESEN betöltött
`.qm`-en keresztül kérdez le. Javítás bukáskor:

    pyside6-lrelease src/picasapy/app/i18n/picasapy_hu.ts \\
        -qm src/picasapy/app/i18n/picasapy_hu.qm
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"


def _kesz_forditasok():
    for context in ET.parse(_I18N / "picasapy_hu.ts").getroot().iter("context"):
        nev = context.findtext("name")
        for msg in context.iter("message"):
            if msg.get("numerus") == "yes":
                continue
            forditas = msg.find("translation")
            if forditas is None or forditas.get("type") in ("unfinished", "obsolete", "vanished"):
                continue
            if not (forditas.text or ""):
                continue
            yield nev, msg.findtext("source") or "", msg.findtext("comment"), forditas.text


def test_minden_kesz_forditas_a_qm_bol_is_betoltodik():
    pytest.importorskip("PySide6.QtCore")
    from PySide6.QtCore import QCoreApplication, QTranslator

    _app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N)), "a picasapy_hu.qm nem tölthető be"

    hianyzo = [
        f"[{ctx}] {forras!r}"
        for ctx, forras, megj, forditas in _kesz_forditasok()
        if translator.translate(ctx, forras, megj) != forditas
    ]
    assert not hianyzo, (
        f"{len(hianyzo)} kész .ts-fordítás nem jön a .qm-ből — építsd újra "
        "(ld. a modul docstringjét):\n" + "\n".join(hianyzo[:20])
    )
