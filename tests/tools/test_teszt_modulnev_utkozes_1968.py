"""Két tesztfájl nem kaphat azonos MODULNEVET (#1968).

## A hiba, amit ez az őr kizár

A pytest `__init__.py` nélküli könyvtárban a fájl **alapnevét** használja
modulnévnek. Két azonos alapnevű tesztfájl így ugyanarra a modulnévre
képződik, és a második gyűjtése elszáll:

```
import file mismatch:
imported module 'test_export_mukodes_1166' has this __file__ attribute:
  tests/app/qml_functional/test_export_mukodes_1166.py
which is not the same as the test file we want to collect:
  tests/export/test_export_mukodes_1166.py
```

## Miért maradt észrevétlen

A projekt futtatója (`scripts/run_tests.py`) **fájlonként darabolva** futtat,
és egy fájl önmagában hibátlanul gyűjthető — az ütközés csak EGYÜTTES
gyűjtésnél jelentkezik. Ezért a teljes tesztkészlet zöld volt, miközben a
`docs_olvaso_tesztek.py --mer` (ami egyben gyűjt) hónapok óta **üres
eredményt** adott, és ezt érvényesnek látszó kimenettel tette (#1968).

## A projekt saját megoldása

A `tests/render/test_retouch.py` és a `tests/ini/test_retouch.py` ugyanígy
azonos alapnevű — mégsem ütköznek, mert a `tests/render/` **csomag**
(`__init__.py`-ja van), így a modulneve `render.test_retouch`. Az őr ezt a
mintát kényszeríti ki: ütközésnél az egyik könyvtárat csomaggá kell tenni.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "tests"


def modulnev(fajl: Path) -> str:
    """A pytest által képzett modulnév — a `rootdir`-alapú import szerint.

    A pytest a fájltól FELFELÉ lépked, amíg `__init__.py`-t talál: minden
    ilyen szint a modulnév része lesz. Az első csomag nélküli szintnél
    megáll, tehát a név a legfelső CSOMAG-könyvtártól számít.
    """
    reszek = [fajl.stem]
    konyvtar = fajl.parent
    while (konyvtar / "__init__.py").is_file():
        reszek.insert(0, konyvtar.name)
        konyvtar = konyvtar.parent
    return ".".join(reszek)


def utkozesek() -> dict[str, list[str]]:
    """Modulnév → a rá képződő fájlok, ha egynél több van."""
    szerint: dict[str, list[str]] = defaultdict(list)
    for fajl in sorted(TESTS.rglob("test_*.py")):
        szerint[modulnev(fajl)].append(str(fajl.relative_to(REPO)))
    return {nev: utak for nev, utak in szerint.items() if len(utak) > 1}


class TestNincsModulnevUtkozes:
    def test_minden_tesztfajl_egyedi_modulnevet_kap(self):
        talalt = utkozesek()
        assert talalt == {}, (
            "Két tesztfájl UGYANARRA a modulnévre képződik — az együttes "
            "gyűjtés ezen elszáll (a fájlonkénti futtatás elfedi):\n"
            + "\n".join(
                f"  {nev}:\n" + "".join(f"      {u}\n" for u in utak)
                for nev, utak in sorted(talalt.items())
            )
            + "\nMegoldás a projekt saját mintájával: tedd az egyik "
            "könyvtárat csomaggá (`__init__.py`), ahogy a `tests/render/` "
            "van — vagy adj a fájlnak egyedi alapnevet."
        )

    def test_az_or_ISMERI_a_csomag_kivetelt(self):
        """A `render`/`ini` pár azonos alapnevű, mégsem ütközik.

        Ha az őr csak az ALAPNEVET nézné, ezt a két, jogos párt is
        hibásnak jelezné — és a zaj miatt kikapcsolnánk.
        """
        parok = [
            (TESTS / "render" / "test_retouch.py",
             TESTS / "ini" / "test_retouch.py"),
            (TESTS / "render" / "test_text_overlay.py",
             TESTS / "ini" / "test_text_overlay.py"),
        ]
        for a, b in parok:
            if not (a.is_file() and b.is_file()):
                continue
            assert a.stem == b.stem, "a próba alapja megszűnt"
            assert modulnev(a) != modulnev(b), (
                f"{a} és {b} azonos modulnevet kapna"
            )
