"""A telepített csomag tartalmazza a futáshoz kellő nem-Python fájlokat — #646.

**A hiba, ami ellen ez az őr szól.** A `pyproject.toml` `package-data`
blokkja a mintákat TÉTELESEN sorolta fel, és két teljes ág kimaradt: a 23
ikon (`qml/PicasaPy/icons/`) és a webexport teljes sablonja. Forrásból minden
működött, ezért **hónapokig észrevétlen maradt** — a CI is forrásból fut
(`pythonpath = ["src"]`), a telepített csomag viszont használhatatlan volt.

**Ez a teszt VALÓDI wheelt épít**, és összeveti a forrásfával. Egy
mintalista-alapú ellenőrzés nem lenne elég: az azt mérné, amit a
`pyproject.toml` állít, nem azt, ami tényleg a csomagba kerül.

A szerződés szándékosan kivétel nélküli: **a `src/picasapy/` alatt minden
nem-Python fájlnak benne kell lennie a wheelben.** Kivétel-lista nélkül nincs
mit elfelejteni karbantartani — épp az elfelejtés okozta a hibát.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

_GYOKER = Path(__file__).resolve().parents[1]
_SRC = _GYOKER / "src"

#: A build saját melléktermékei a forrásfában — nem a csomag tartalma.
_MELLEKTERMEK_MAPPAK = ("__pycache__", "picasapy.egg-info")


def _forras_nem_python_fajlok() -> set[str]:
    return {
        str(p.relative_to(_SRC))
        for p in _SRC.rglob("*")
        if p.is_file()
        and p.suffix != ".py"
        and not any(k in p.parts for k in _MELLEKTERMEK_MAPPAK)
    }


@pytest.fixture(scope="module")
def wheel_tartalma(tmp_path_factory) -> set[str]:
    """A felépített wheel fájllistája.

    `--no-deps --no-build-isolation`: nincs hálózati letöltés, a build a
    meglévő setuptools-szal fut — így a teszt zárt környezetben is működik.
    """
    cel = tmp_path_factory.mktemp("wheel")
    # #646: a build KORÁBBI állapotából a setuptools újrahasznosít — a
    # `build/lib/…`-ba egyszer bemásolt adatfájlok és az `egg-info`
    # `SOURCES.txt`-je a HIBÁS mintákkal is beletennék a fájlokat a wheelbe.
    # Az őr ilyenkor zöldet adna egy törött csomagolásra; kipróbálva: pontosan
    # ez történt, amíg ez a takarítás nem volt itt. Mindkettő gitignore-olt és
    # a build újragenerálja őket.
    for maradek in (_GYOKER / "build", _SRC / "picasapy.egg-info"):
        shutil.rmtree(maradek, ignore_errors=True)
    futas = subprocess.run(  # noqa: S603 — saját, rögzített parancs
        [
            sys.executable, "-m", "pip", "wheel",
            "--no-deps", "--no-build-isolation",
            # #646: gyorsítótár NÉLKÜL — különben a pip egy KORÁBBI wheelt
            # szolgálna ki, és az őr egy régi csomagra adna zöldet
            "--no-cache-dir",
            "-w", str(cel), str(_GYOKER),
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    if futas.returncode != 0:
        pytest.fail(
            "a wheel építése nem sikerült — ez önmagában is hiba:\n"
            f"{futas.stdout[-2000:]}\n{futas.stderr[-2000:]}"
        )
    wheelek = list(cel.glob("*.whl"))
    assert len(wheelek) == 1, f"egy wheelt vártam, {len(wheelek)} lett"
    return set(zipfile.ZipFile(wheelek[0]).namelist())


class TestACsomagTeljes:
    def test_minden_nem_python_fajl_bekerul(self, wheel_tartalma) -> None:
        hianyzo = sorted(_forras_nem_python_fajlok() - wheel_tartalma)

        assert not hianyzo, (
            f"{len(hianyzo)} nem-Python fájl kimarad a telepített csomagból "
            "(a `pyproject.toml` `package-data` mintái nem fedik le):\n  "
            + "\n  ".join(hianyzo)
        )

    @pytest.mark.parametrize(
        "fajl",
        [
            # a #646-ban ténylegesen hiányzott három csoport egy-egy tagja —
            # nevesítve, hogy a hibajelentés visszakereshető maradjon
            "picasapy/app/qml/PicasaPy/icons/deritofeny.svg",
            "picasapy/app/qml/PicasaPy/Gpu/PointFilter.frag",
            "picasapy/webexport/templates/feher/index.tpl",
        ],
    )
    def test_a_bejelentett_hianyok_benne_vannak(
        self, wheel_tartalma, fajl: str
    ) -> None:
        assert fajl in wheel_tartalma


class TestAMintakRekurzivak:
    """A tételes whitelist volt a hiba oka: egy ÚJ alkönyvtár felvételekor
    senki nem gondolt a `pyproject.toml`-ra. A mintáknak ezért rekurzívnak
    kell lenniük, hogy az új alkönyvtár magától a helyére kerüljön."""

    def test_nincs_teteles_alkonyvtar_minta(self) -> None:
        import tomllib

        adat = tomllib.loads(
            (_GYOKER / "pyproject.toml").read_text(encoding="utf-8")
        )
        mintak = adat["tool"]["setuptools"]["package-data"]

        assert "picasapy.webexport" in mintak, (
            "a webexport sablonjára nem volt kulcs — 14 fájl maradt ki"
        )
        for csomag, lista in mintak.items():
            for minta in lista:
                assert "**" in minta, (
                    f"{csomag}: a(z) {minta!r} nem rekurzív — egy új "
                    "alkönyvtár némán kimaradna a telepítésből"
                )
