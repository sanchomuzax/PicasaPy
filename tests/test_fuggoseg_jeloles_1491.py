"""#1491 — a rendszercsomag-lista KÖTELEZŐ és CSAK-DISZTRIBÚCIÓS tételei.

A #1472-ben egyetlen, csak a disztribúciós PySide6-hoz kellő csomag
(`python3-pyside6.qtprintsupport`) bekerült a közös listába, a CI pedig
`apt-get install`-lal futtatja azt: a telepítés elhasalt, vele a `libegl1`
sem került fel, és MINDEN teszt elbukott egy félrevezető
`ImportError: libEGL.so.1`-gyel (a 32938928311 futás).

A javítás nem második lista — a „nincs második lista" doktrína megmarad —,
hanem SZAKASZ ugyanabban a fájlban. Ezek az őrök azt mérik, hogy a
csak-disztribúciós tétel a CI listájába **nem** kerül bele.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_SZKRIPT = _GYOKER / "scripts" / "print_dependencies.py"
_APT_LISTA = _GYOKER / "packaging" / "qt-runtime-deps.txt"

#: A szakaszhatároló, ami alatt a csak-disztribúciós tételek állnak.
SZAKASZ_JELOLO = "[csak-disztribucios]"

#: A #1472 konkrét tétele — ez az egyetlen, amit ma ismerünk.
_DISZTRIBUCIOS_TETEL = "python3-pyside6.qtprintsupport"

_KOTELEZOK = ("libegl1", "libgl1", "libxkbcommon0", "libpulse0")


def _futtat(*argumentumok: str) -> list[str]:
    kimenet = subprocess.run(
        [sys.executable, str(_SZKRIPT), *argumentumok],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        check=True,
        cwd=_GYOKER,
    )
    return kimenet.stdout.split()


def test_a_lista_megkulonbozteti_a_ket_fajtat() -> None:
    """A fájl EGY marad, de szakaszhatárolóval jelöli a kétféle tételt."""
    szoveg = _APT_LISTA.read_text(encoding="utf-8")
    assert SZAKASZ_JELOLO in szoveg, (
        f"a(z) {_APT_LISTA.name} nem jelöli, mely tételek csak a "
        "disztribúciós PySide6-hoz kellenek — a kötelezőktől megkülönböztetve "
        f"(#1491). Várt szakaszhatároló: `{SZAKASZ_JELOLO}`"
    )


def test_az_apt_csak_a_kotelezoket_adja() -> None:
    """A CI ezt futtatja `apt-get install`-lal — ide tilos beengedni a
    csak-disztribúciós tételt (#1472 éles kára)."""
    csomagok = _futtat("--apt")
    assert _DISZTRIBUCIOS_TETEL not in csomagok, (
        f"a(z) `{_DISZTRIBUCIOS_TETEL}` bekerült a CI listájába — pontosan ez "
        "ölte meg a 32938928311 futást (#1472)."
    )
    hianyzik = [cs for cs in _KOTELEZOK if cs not in csomagok]
    assert not hianyzik, f"a kötelezők közül hiányzik: {hianyzik}"
    assert SZAKASZ_JELOLO not in csomagok, (
        "a szakaszhatároló magát csomagnévként adja vissza a szkript"
    )


def test_az_apt_teljes_hozza_a_disztribucios_teteleket() -> None:
    """Aki a disztribúció csomagjaiból telepít, EGY paranccsal megkapja
    mindkét fajtát — nem kell kézzel összeollóznia."""
    teljes = _futtat("--apt-teljes")
    kotelezo = _futtat("--apt")

    assert _DISZTRIBUCIOS_TETEL in teljes, (
        f"a `--apt-teljes` nem adja vissza a(z) `{_DISZTRIBUCIOS_TETEL}`-t"
    )
    # a kötelezők ELÖL maradnak, változatlan sorrendben
    assert teljes[: len(kotelezo)] == kotelezo, (
        "a `--apt-teljes` átrendezte a kötelezőket"
    )
    assert len(teljes) > len(kotelezo), "a teljes lista nem bővebb"


def test_a_ci_es_a_bootstrap_a_szuk_listat_kerdezi() -> None:
    """A `--apt-teljes` NEM szivároghat be a CI-be vagy a bootstrapbe:
    ott a szűk lista a helyes, különben visszatér a #1472 kára."""
    helyek = [
        *(_GYOKER / ".github" / "workflows").glob("*.yml"),
        _GYOKER / "scripts" / "bootstrap_env.sh",
    ]
    vetkesek = [
        h.relative_to(_GYOKER).as_posix()
        for h in helyek
        if h.exists() and "--apt-teljes" in h.read_text(encoding="utf-8")
    ]
    assert not vetkesek, (
        f"`--apt-teljes` hívás a CI-ben/bootstrapben: {vetkesek}. Ott a "
        "`--apt` (szűk) lista a helyes — a csak-disztribúciós csomag "
        "eltöri az `apt-get install`-t (#1472)."
    )
