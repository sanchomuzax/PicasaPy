"""Forrás-szintű kapu: `chmod`-os teszt ne futhasson Windowson (#1864).

## A baj, amit megelőz

Windowson a `chmod` a POSIX-biteket **nem érvényesíti**: az „írásvédett"
mappába a Python továbbra is ír, a `chmod(0)` alatti mappa listázható. Egy
`chmod`-dal előállított hibahelyzet ott tehát **nem áll elő**, és a rá épülő
állítás vagy elbukik, vagy — rosszabb esetben — más okból lesz zöld.

Mérve (#1864): a `tests/export/test_export_hibaagak_1617.py` négy próbája a
windows-lábon 2026-09-01-ig **minden PR-en elbukott**, és nem tűnt fel, mert
az a láb `continue-on-error`. Négy hibaág hetekig mérés nélkül állt.

## Amit ez a kapu ellenőriz

Minden `tests/` alatti `.chmod(...)` hívás olyan hatókörben álljon, amelyet
egy **kimondott** platform-kapu véd: a hívást tartalmazó függvényen, annak
osztályán vagy a modul `pytestmark`-ján legyen `skipif`, amelynek forrása a
POSIX-feltételek egyikére hivatkozik.

⚠️ **A kapu FORRÁST néz**, nem futásidőt: azt méri, hogy a jelölés ott van-e.
Azt nem méri, hogy a jelölt teszt tartalmilag helyes-e.

## Az 1. pont mérése, amiért a jegy nyitva volt (#1864)

Az öt „gyanús" fájl (`test_ioutil.py`, `fileops/test_trash.py`,
`ini/test_writer.py`, `index/test_sync.py`, `metadata/test_iptc_writer.py`)
átnézve: **egyikben sincs hamisan zöld eset.** Négyben a `chmod`-os teszt
kimondott `skipif`-et kapott (`os.name != "posix"`, illetve a #1864-re
hivatkozó indok), az ötödikben (`test_trash.py`) a `chmod` a
`TestFindTrashDir` osztályban áll, amelyet az `os.getuid` hiánya zár ki
Windowson — a mount-specifikus lomtár POSIX-fogalom. Ez a kapu attól
mostantól nem is tud visszacsúszni.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]

#: A POSIX-kizárás felismert alakjai. Mind KIMONDOTT: vagy a platformra, vagy
#: egy POSIX-only függvény hiányára hivatkozik.
_POSIX_KAPUK = (
    '.name != "posix"',  # `os.name` és `__import__("os").name` alakban is
    ".name != 'posix'",
    "_WINDOWS",
    'hasattr(os, "getuid")',
    "hasattr(os, 'getuid')",
    'sys.platform == "win32"',
    "sys.platform == 'win32'",
    'sys.platform.startswith("win")',
    "sys.platform.startswith('win')",
)

#: Fájlon belüli marker-ALIASOK: ezek maguk `pytest.mark.skipif(...)`
#: értékek, a POSIX-feltétellel a definíciójukban (a `chmod`-os fájl a saját
#: nevén hivatkozik rájuk). A kapu a nevet is elfogadja jelölésnek.
#: A közös, `tests/support/platform_marks.py`-beli jelölés neve. A fájlon
#: BELÜL definiált aliasokat a kapu magától felismeri (`_alias_nevek`), ezt
#: viszont import hozza be, ezért itt kell megnevezni.
_MARKER_ALIASOK = ("csak_posix_jogosultsag",)

#: Indokolt kivételek: `(fájl, függvény)`, a MIÉRT-tel. A lista zárt.
_KIVETELEK: set[tuple[str, str]] = set()


def _forras(ut: Path) -> tuple[str, list[str], ast.Module]:
    szoveg = ut.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        # idegen tesztfájlok escape-hibás docstringjei nem a mi dolgunk
        warnings.simplefilter("ignore", SyntaxWarning)
        return szoveg, szoveg.splitlines(), ast.parse(szoveg)


def _dekorator_szoveg(csomopont, sorok: list[str]) -> str:
    return "\n".join(
        "\n".join(sorok[d.lineno - 1 : (d.end_lineno or d.lineno)])
        for d in getattr(csomopont, "decorator_list", [])
    )


def _alias_nevek(fa: ast.Module, sorok: list[str]) -> tuple[str, ...]:
    """Modul-szintű `X = pytest.mark.skipif(<POSIX-feltétel>, …)` nevek.

    Enélkül a kapu HAMISAN jelezne minden olyan fájlt, amely a jelölést egy
    saját néven tartja (`_SKIP_READONLY`, `_jogosultsag_kihagy`) — és épp ez
    a bevett alak a készletben.
    """
    nevek: list[str] = []
    for cs in fa.body:
        if not isinstance(cs, ast.Assign):
            continue
        ertek = "\n".join(sorok[cs.lineno - 1 : (cs.end_lineno or cs.lineno)])
        if "skipif" in ertek and any(kapu in ertek for kapu in _POSIX_KAPUK):
            nevek.extend(cel.id for cel in cs.targets if isinstance(cel, ast.Name))
    # …és az ÁTNEVEZÉSEK (`_root_kihagy = _jogosultsag_kihagy`): a készletben
    # ez a bevett alak, ha egy fájl régi nevet is megtart.
    valtozott = True
    while valtozott:
        valtozott = False
        for cs in fa.body:
            if not (
                isinstance(cs, ast.Assign)
                and isinstance(cs.value, ast.Name)
                and (cs.value.id in nevek or cs.value.id in _MARKER_ALIASOK)
            ):
                continue
            for cel in cs.targets:
                if isinstance(cel, ast.Name) and cel.id not in nevek:
                    nevek.append(cel.id)
                    valtozott = True
    return tuple(nevek)


def _vedett(szoveg: str, aliasok: tuple[str, ...] = ()) -> bool:
    if any(alias in szoveg for alias in _MARKER_ALIASOK + aliasok):
        return True
    return "skipif" in szoveg and any(kapu in szoveg for kapu in _POSIX_KAPUK)


def _skope_vedett(cs, szulok, sorok, modul_vedett: bool, aliasok=()) -> tuple[bool, str]:
    """A csomópontot körülvevő függvény/osztály kapuzott-e; és a nevük."""
    vedett = modul_vedett
    nev = "<modul>"
    elso = True
    aktualis = cs
    while aktualis is not None:
        if isinstance(aktualis, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if elso:
                nev = aktualis.name
                elso = False
            if _vedett(_dekorator_szoveg(aktualis, sorok), aliasok):
                vedett = True
        aktualis = szulok.get(id(aktualis))
    return vedett, nev


def chmod_leletek(gyoker: Path | None = None) -> list[str]:
    """A védelem nélküli `chmod`-helyek listája — a kapu és a próbái is ezt hívják.

    A `chmod`-ot **segédfüggvényben** végző fájloknál (pl. `_olvashatatlanna`)
    nem a segéd, hanem a HÍVÓI a mérce: a segéd önmagában nem tudja, milyen
    platformon futtatják. Ha bármelyik hívója kapu nélkül áll, az a lelet.
    """
    gyoker = gyoker or GYOKER
    leletek: list[str] = []
    for ut in sorted((gyoker / "tests").rglob("*.py")):
        szoveg, sorok, fa = _forras(ut)
        if ".chmod(" not in szoveg:
            continue
        aliasok = _alias_nevek(fa, sorok)
        modul_vedett = any(
            _vedett("\n".join(sorok[cs.lineno - 1 : (cs.end_lineno or cs.lineno)]))
            for cs in fa.body
            if isinstance(cs, ast.Assign)
            and any(
                isinstance(c, ast.Name) and c.id == "pytestmark" for c in cs.targets
            )
        )
        szulok: dict[int, ast.AST] = {}
        for cs in ast.walk(fa):
            for gyermek in ast.iter_child_nodes(cs):
                szulok[id(gyermek)] = cs

        segedek: set[str] = set()
        for cs in ast.walk(fa):
            if not (
                isinstance(cs, ast.Call)
                and isinstance(cs.func, ast.Attribute)
                and cs.func.attr == "chmod"
            ):
                continue
            vedett, nev = _skope_vedett(cs, szulok, sorok, modul_vedett, aliasok)
            if nev.startswith("_"):
                segedek.add(nev)  # a hívóinál mérünk
                continue
            kulcs = (ut.relative_to(gyoker).as_posix(), nev)
            if not vedett and kulcs not in _KIVETELEK:
                leletek.append(f"{kulcs[0]}:{cs.lineno} {nev}")

        for cs in ast.walk(fa):
            if not (
                isinstance(cs, ast.Call)
                and isinstance(cs.func, ast.Name)
                and cs.func.id in segedek
            ):
                continue
            vedett, nev = _skope_vedett(cs, szulok, sorok, modul_vedett, aliasok)
            kulcs = (ut.relative_to(gyoker).as_posix(), nev)
            if not vedett and kulcs not in _KIVETELEK:
                leletek.append(
                    f"{kulcs[0]}:{cs.lineno} {nev} (a {cs.func.id}() segéden át)"
                )
    return leletek


class TestChmodPlatformKapu:
    def test_minden_chmod_posix_kapu_alatt_all(self) -> None:
        leletek = chmod_leletek()
        assert not leletek, (
            "#1864: `chmod`-os teszt platform-kapu NÉLKÜL. Windowson a "
            "`chmod` a POSIX-biteket nem érvényesíti, tehát a hibahelyzet nem "
            "áll elő, és az állítás vagy elbukik, vagy hamisan zöld. Tegyél rá "
            "kimondott `skipif`-et (pl. `os.name != \"posix\"`):\n  "
            + "\n  ".join(leletek)
        )

    def test_a_kapu_MEGFOGJA_a_vedelem_nelkuli_esetet(self, tmp_path: Path) -> None:
        """Ismert pozitív: a kapu nulla lelete csak akkor jelent valamit, ha
        egy VALÓDI szabálysértést fel is ismer (a minta hibája ugyanígy nézne
        ki)."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_szabalysertes.py").write_text(
            "from pathlib import Path\n"
            "\n"
            "def test_valami(tmp_path: Path) -> None:\n"
            "    (tmp_path / 'a').mkdir()\n"
            "    (tmp_path / 'a').chmod(0)\n",
            encoding="utf-8",
        )
        leletek = chmod_leletek(tmp_path)
        assert len(leletek) == 1, leletek
        assert "test_valami" in leletek[0]

    def test_a_kapu_ELFOGADJA_a_jelolt_esetet(self, tmp_path: Path) -> None:
        """…és a kimondott jelöléssel ugyanaz a kód már nem lelet."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_jelolt.py").write_text(
            "import os\n"
            "from pathlib import Path\n"
            "\n"
            "import pytest\n"
            "\n"
            '@pytest.mark.skipif(os.name != "posix", reason="POSIX-bitek")\n'
            "def test_valami(tmp_path: Path) -> None:\n"
            "    (tmp_path / 'a').mkdir()\n"
            "    (tmp_path / 'a').chmod(0)\n",
            encoding="utf-8",
        )
        assert chmod_leletek(tmp_path) == []
