"""#6441/#6442: a termékkód nem mutat régi, az eredeti Picasából átvett helyre.

A tulajdonos 2026-11-02-i döntése: a PicasaPy nem gyűjt használati
statisztikát, a Beállítások „Részvétel a fejlesztésben” sora és a Google
adatvédelmi oldalára mutató „Adatvédelem…” hivatkozás kikerült. Ez az őr azt
is megakadályozza, hogy régi Picasa/Google-oldalra mutató link visszakerüljön."""

from __future__ import annotations

import re
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src" / "picasapy"
_TILTOTT = re.compile(
    r"picasa\.google|picasaweb\.google|support\.google\.com|policies\.google\.com"
    r"|google\.com/(?:privacy|intl|support|picasa)|goo\.gl/|http://mail\.google\.com",
    re.IGNORECASE,
)
_KIVETEL_MAPPAK = ("i18n",)


def _forrasok():
    for ut in _SRC.rglob("*"):
        if not ut.is_file() or ut.suffix not in {".py", ".qml", ".js", ".html", ".tpl"}:
            continue
        if any(resz in _KIVETEL_MAPPAK for resz in ut.parts):
            continue
        yield ut


def test_nincs_regi_picasa_vagy_google_oldalra_mutato_hivatkozas():
    talalatok = []
    for ut in _forrasok():
        for sorszam, sor in enumerate(ut.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if _TILTOTT.search(sor):
                talalatok.append(f"{ut.relative_to(_SRC)}:{sorszam}: {sor.strip()[:120]}")
    assert not talalatok, "régi helyre mutató hivatkozás:\n" + "\n".join(talalatok)


def test_a_beallitasokban_nincs_statisztika_sor():
    qml = (_SRC / "app/qml/PicasaPy/OptionsTabGeneral.qml").read_text(encoding="utf-8")
    for nev in (
        "optionsUsageStatsCheck",
        "optionsPrivacyLink",
        "optionsGeneralParticipationHeading",
        "optionsGeneralParticipationDivider",
        "Send anonymous usage statistics",
    ):
        assert nev not in qml, f"a statisztika sor eleme maradt: {nev}"
