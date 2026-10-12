"""A CI Qt-verziója és az összevetés a futtató Pythonnal (#4834).

Igazságforrás: `packaging/ci-constraints.txt` (`név==verzió` sorok). Ezt
olvassa a CI (`pip install -c …`), a `scripts/ci_venv.py` és a
`scripts/run_tests.py`. Nincs Qt-importja: a metaadatból olvas, így a
`run_tests.py` indulását nem lassítja.

Őr: `tests/test_ci_azonos_qt_4834.py`.
"""

from __future__ import annotations

import re
from importlib import metadata
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
CONSTRAINT_FAJL = GYOKER / "packaging" / "ci-constraints.txt"

_SOR = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)$")

EGYEZIK = "egyezik"
ELTER = "elter"
HIANYZIK = "hianyzik"


def _normal(nev: str) -> str:
    return re.sub(r"[-_.]+", "-", nev).lower()


def olvasd_a_rogzitest(szoveg: str) -> dict[str, str]:
    """A constraint-fájl szövege -> {normalizált név: pontos verzió}.

    Kommentet és üres sort kihagy; minden más sornak `név==verzió` alakúnak
    kell lennie, különben ValueError (a rögzítés nem lehet néma).
    """
    eredmeny: dict[str, str] = {}
    for nyers in szoveg.splitlines():
        sor = nyers.split("#", 1)[0].strip()
        if not sor:
            continue
        talalat = _SOR.match(sor)
        if not talalat:
            raise ValueError(f"nem `név==verzió` alakú constraint-sor: {nyers!r}")
        eredmeny[_normal(talalat.group(1))] = talalat.group(2)
    return eredmeny


def ci_verzio(csomag: str = "PySide6", fajl: Path = CONSTRAINT_FAJL) -> str | None:
    """A CI rögzített verziója; `None`, ha a fájl vagy a tétel hiányzik."""
    try:
        szoveg = fajl.read_text(encoding="utf-8")
    except OSError:
        return None
    return olvasd_a_rogzitest(szoveg).get(_normal(csomag))


def futo_verzio(csomag: str = "PySide6") -> str | None:
    """A futtató Python csomagverziója; `None`, ha nincs telepítve."""
    try:
        return metadata.version(csomag)
    except metadata.PackageNotFoundError:
        pass
    if csomag != "PySide6":
        return None
    try:  # rendszercsomagos PySide6-nak lehet, hogy nincs dist-info
        import PySide6  # noqa: PLC0415

        return str(PySide6.__version__)
    except Exception:  # noqa: BLE001 — az összevetés nem dönthet le semmit
        return None


def hasonlit(futo: str | None, ci: str | None) -> str:
    """EGYEZIK / ELTER / HIANYZIK (a futtatón nincs PySide6)."""
    if futo is None:
        return HIANYZIK
    if ci is None or futo == ci:
        return EGYEZIK  # nincs mihez mérni -> nincs mit jelezni
    return ELTER


CI_VENV_PARANCS = "python3 scripts/ci_venv.py"
CI_FUTTATAS_PARANCS = ".venv-ci/bin/python scripts/run_tests.py"


def figyelmeztetes_sorai(futo: str | None, ci: str | None) -> list[str]:
    """Üres lista, ha egyezik (a CI-n nem zajlunk); különben látható blokk."""
    allapot = hasonlit(futo, ci)
    if allapot == EGYEZIK:
        return []
    mi = (
        "nincs PySide6 a futtató Pythonban"
        if allapot == HIANYZIK
        else f"a futtató PySide6-ja {futo}"
    )
    return [
        "!" * 70,
        f"FIGYELEM: NEM CI-AZONOS A QT — {mi}, a CI-é {ci} (#4834).",
        "A CI-only hibák helyben nem jönnek elő, a zöld futás félrevezethet.",
        f"CI-azonos környezet egy paranccsal:  {CI_VENV_PARANCS}",
        f"majd:  {CI_FUTTATAS_PARANCS}",
        "!" * 70,
    ]


def figyelmeztetes_a_futora() -> list[str]:
    return figyelmeztetes_sorai(futo_verzio(), ci_verzio())
