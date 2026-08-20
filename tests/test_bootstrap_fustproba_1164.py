"""A Session-bootstrap PR-en FÜSTPRÓBÁT fut, hetente a teljeset (#1164).

## Miért

A job azt bizonyítja, hogy a hook által épített környezet HASZNÁLHATÓ.
Ehhez a teljes tesztkészletet futtatta — 19 percet MINDEN olyan PR-től,
amely a környezet-leíró fájlokhoz nyúlt. A teljes készletet a `ci.yml`
amúgy is lefuttatja, négy gépen: kétszer ugyanazt futtatni nem ad több
biztonságot.

⚠️ **A mély garancia nem veszett el, csak áthelyeződött**: a heti
ütemezett futás továbbra is a teljes készletet viszi. Ez az őr pontosan
ezt a két állítást védi — enélkül a következő szerkesztés vagy a
füstpróbát bővítené vissza teljessé, vagy a heti teljeset ejtené el.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

_UT = (
    pathlib.Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "ci-bootstrap.yml"
)


@pytest.fixture(scope="module")
def lepesek() -> list[dict]:
    adat = yaml.safe_load(_UT.read_text(encoding="utf-8"))
    return adat["jobs"]["bootstrap"]["steps"]


def test_a_PR_agon_NEM_fut_a_teljes_keszlet(lepesek):
    """A `run_tests.py` (teljes készlet) nem futhat pull_request-en."""
    for lepes in lepesek:
        parancs = str(lepes.get("run", ""))
        if "run_tests.py" not in parancs:
            continue
        felteteI = str(lepes.get("if", ""))
        assert "pull_request" in felteteI and "!=" in felteteI, (
            "a teljes készlet PR-en is futna — 19 perc minden ilyen PR-től"
        )


def test_a_heti_futas_a_TELJES_keszletet_viszi(lepesek):
    """⚠️ A mély garancia nem eshet ki: hetente végig kell futnia."""
    teljes = [
        lepes for lepes in lepesek if "run_tests.py" in str(lepes.get("run", ""))
    ]
    assert teljes, (
        "eltűnt a teljes tesztkészlet futtatása — a hook-környezet mély "
        "ellenőrzése enélkül semmit nem bizonyít"
    )


def test_a_fustproba_MIND_A_NEGY_reteget_erinti(lepesek):
    """Qt/QML · képkezelés · OpenCV · fájlfigyelés — egyik sem hiányozhat.

    Ha a füstpróba egy réteget kihagy, a hiányzó csomagot (ahogy annak
    idején a `libpulse0`-t) ez a job nem fogja megfogni."""
    fust = [
        str(lepes.get("run", ""))
        for lepes in lepesek
        if str(lepes.get("if", "")).strip() == "github.event_name == 'pull_request'"
    ]
    assert fust, "nincs PR-ági füstpróba"
    szoveg = "\n".join(fust)
    for reteg, minta in (
        ("Qt/QML", "qml_functional/"),
        ("képkezelés", "test_thumbnail_async.py"),
        ("OpenCV", "tests/render/"),
        ("fájlfigyelés", "tests/scanner"),
    ):
        assert minta in szoveg, f"a füstpróbából hiányzik a(z) {reteg} rétege"
