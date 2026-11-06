"""A fuzz-tesztek közös, Hypothesis nélküli gyűjteményre is biztonságos kerete."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
import os
from pathlib import Path
import sys
from typing import Iterator

import pytest

try:
    import resource
except ImportError:  # Windows
    resource = None

try:
    from hypothesis import settings
    from hypothesis.database import DirectoryBasedExampleDatabase
except ImportError:  # a tesztmodulok pytest.importorskip-szel kimaradnak
    settings = None
    DirectoryBasedExampleDatabase = None

_MEMORIA_BOVITES = 512 * 1024 * 1024
_HIVAS_HATARIDO_MASODPERC = 2
_KIHAGYASOK: Counter[str] = Counter()
_ALAP_CIMTER: int | None = None
_WINDOWS_JELZES = False

if settings is not None:
    _gyoker = Path(__file__).resolve().parents[2]
    _adatbazis = Path(
        os.environ.get(
            "PICASAPY_HYPOTHESIS_DB", str(_gyoker / ".tmp" / "hypothesis")
        )
    )
    _adatbazis.mkdir(parents=True, exist_ok=True)
    _database = DirectoryBasedExampleDatabase(str(_adatbazis))
    settings.register_profile(
        "ci",
        max_examples=100,
        derandomize=True,
        deadline=_HIVAS_HATARIDO_MASODPERC * 1_000,
        # A determinisztikus futás a Hypothesis szabálya szerint nem használ
        # példaadatbázist; a minimalizált leleteket az éjszakai profil menti.
        database=None,
    )
    settings.register_profile(
        "ejszakai",
        max_examples=20_000,
        derandomize=False,
        deadline=_HIVAS_HATARIDO_MASODPERC * 1_000,
        database=_database,
    )
    _profil = os.environ.get("PICASAPY_FUZZ_PROFIL", "ci")
    if _profil not in {"ci", "ejszakai"}:
        raise pytest.UsageError(
            "A PICASAPY_FUZZ_PROFIL csak 'ci' vagy 'ejszakai' lehet."
        )
    settings.load_profile(_profil)


def jegyezd_kihagyasokat(nevek: tuple[str, ...]) -> None:
    """Összesíti a renderlánc által kihagyott szűrőket a fuzz-mérőszámhoz."""
    _KIHAGYASOK.update(nevek)


def _cimter_meret() -> int:
    """A folyamat aktuális virtuális címtér-mérete bájtban (Linux)."""
    try:
        lapmeret = os.sysconf("SC_PAGE_SIZE")
        lapok = int(Path("/proc/self/statm").read_text(encoding="ascii").split()[0])
    except (OSError, ValueError, IndexError):
        return 0
    return lapok * lapmeret


@contextmanager
def fuzz_hivas_keret() -> Iterator[None]:
    """Egy fuzz-hívás címtér-növekedését 512 MiB-ra korlátozza Linuxon.

    A `RLIMIT_AS` a már lefoglalt címteret is számolja, ezért a plafon a
    fuzz-készlet indulásakor mért folyamatméret fölé kerül. Az eredeti
    korlátot minden hívás után visszaállítjuk.
    """
    global _ALAP_CIMTER, _WINDOWS_JELZES
    if resource is None or not hasattr(resource, "RLIMIT_AS"):
        if not _WINDOWS_JELZES:
            print(
                "Fuzz erőforrás-őr: Windows alatt az RLIMIT_AS nem érhető el.",
                file=sys.stderr,
            )
            _WINDOWS_JELZES = True
        yield
        return

    if _ALAP_CIMTER is None:
        _ALAP_CIMTER = _cimter_meret()
    if _ALAP_CIMTER <= 0:
        yield
        return

    regi_lagy, regi_kemeny = resource.getrlimit(resource.RLIMIT_AS)
    cel = _ALAP_CIMTER + _MEMORIA_BOVITES
    if regi_kemeny != resource.RLIM_INFINITY:
        cel = min(cel, regi_kemeny)
    if regi_lagy != resource.RLIM_INFINITY:
        cel = min(cel, regi_lagy)
    resource.setrlimit(resource.RLIMIT_AS, (cel, regi_kemeny))
    try:
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_AS, (regi_lagy, regi_kemeny))


@pytest.fixture
def fuzz_keret():
    """Kontekstusmenedzser, amelyet a property minden egyes hívás köré tehet."""
    return fuzz_hivas_keret


@pytest.fixture
def fuzz_kihagyas_merese():
    return jegyezd_kihagyasokat


def pytest_terminal_summary(terminalreporter) -> None:
    if not _KIHAGYASOK:
        terminalreporter.write_line("Fuzz kihagyásmérő: 0 szűrő-kihagyás.")
        return
    sor = ", ".join(f"{nev}={darab}" for nev, darab in sorted(_KIHAGYASOK.items()))
    terminalreporter.write_line(
        f"Fuzz kihagyásmérő: {sum(_KIHAGYASOK.values())} összes ({sor})."
    )
