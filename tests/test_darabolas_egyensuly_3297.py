"""#3297 — a windows-darabok kiegyensúlyozottsága a MÉRT táblából.

## A lelet

A windows-láb 1/4 darabja **28,6 percet** futott, a másik három 18–19-et
(main `cfd25b3f`, 2026-09-18) — a 30 perces határidő szélén, és egy
korábbi körben át is lépte (`exit 124`).

⛔ A jegy törzse azt mondta, „a darabolás ma fájlszám vagy névsor szerint
oszt". **Ez elavult:** a `_kiegyensulyozott_darab` MÉRT időkkel, mohó
kiosztással dolgozik (#3117). A baj nem a módszer volt, hanem a TÁBLA:

| | |
|---|---|
| a tábla mérve | main `4e2c6dd6`, 2026-09-15 |
| azóta hozzájött | **50** tesztfájl, ami a táblában nem szerepelt |
| a meglévők lassultak | pl. `test_editor.py` 25 → **52** mp |

Az ismeretlen fájl a mediánt kapja — ötven ilyen viszont már elmozdítja a
kiosztást.

## Amit ez a fájl őriz

Nem a konkrét másodperceket (azok körönként változnak), hanem hogy

1. a tábla **lefedi** a mai tesztfájlokat (a hiányzók mediánt kapnának);
2. a táblából számolt négy darab **kiegyensúlyozott**;
3. a leghosszabb darab a windows-határidő **felén** belül marad — ez a
   tartalék a gépek napi ingadozására.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import run_tests  # noqa: E402

#: A windows-job határideje percben (`teszt-darabok.yml`).
HATARIDO_PERC = 30

#: A leghosszabb darab ennél nem lehet nagyobb.
#:
#: ⚠️ A szám nem fejből van: a teljes windows-készlet MÉRT ideje 83 perc
#: (2026-09-18), tehát négy darabbal a **matematikai** alsó határ 20,8
#: perc — a „határidő fele" (15 perc) elérhetetlen, azt csak több darab
#: adná. A 80% az a tartalék, ami a gépek napi ingadozását még elnyeli:
#: a 2026-09-18-i körben a leghosszabb darab 28,6 perc volt (95%), és az
#: előző körben át is lépte a határt.
PLAFON_PERC = HATARIDO_PERC * 0.8

#: A darabok száma (a CI-mátrix).
DARABOK = 4


@pytest.fixture(scope="module")
def idok() -> dict[str, float]:
    return json.loads(
        (_ROOT / "scripts" / "teszt_idok.json").read_text(encoding="utf-8")
    )


def _egysegek() -> list[str]:
    """A futtató SAJÁT egységei — nem minden tesztfájl.

    ⚠️ A `tests/app`-on kívüli készlet EGYETLEN részfutás
    (`_NEM_APP`), nem fájlonkénti: a táblában ezért nem szerepel az 1176
    tesztfájl mind. A lefedettséget tehát a futtató egységlistájához kell
    mérni, különben az őr a saját téves nevezőjén bukik (mérve: 468
    „hiányzó" fájl, holott egyik sem külön egység)."""
    gyoker = run_tests._ROOT
    app = sorted((gyoker / "tests" / "app").glob("test_*.py")) + sorted(
        (gyoker / "tests" / "app" / "qml_functional").glob("test_*.py")
    )
    return [run_tests._NEM_APP] + [
        str(ut.relative_to(gyoker)).replace("\\", "/") for ut in app
    ]


def _terhelesek(idok: dict[str, float]) -> list[float]:
    egysegek = _egysegek()
    return [
        sum(idok.get(nev, 0.0) for nev in run_tests._kiegyensulyozott_darab(
            egysegek, i, DARABOK
        ))
        for i in range(1, DARABOK + 1)
    ]


class TestATablaFRISS:
    def test_lefedi_a_mai_egysegeket(self, idok):
        """Az ismeretlen egység mediánt kap — ötven ilyen már elmozdítja a
        kiosztást, és pont ez vitte a határidőre az 1/4 darabot.

        ⚠️ A meglévő #1127-es őr 90%-ot követel; ez SZIGORÚBB (98%),
        mert a #3297 mérése szerint már a 7%-nyi ismeretlen is elég volt
        a 28,6 perces darabhoz."""
        tablaban = {nev.replace("\\", "/") for nev in idok}

        hianyzo = sorted(nev for nev in _egysegek() if nev not in tablaban)
        egysegek = _egysegek()

        assert len(hianyzo) <= len(egysegek) * 0.02, (
            f"{len(hianyzo)} egység hiányzik a futásidő-táblából "
            f"({len(egysegek)}-ből): " + ", ".join(hianyzo[:8])
        )


class TestAzEgyensuly:
    def test_a_negy_darab_kiegyensulyozott(self, idok):
        terhelesek = _terhelesek(idok)

        arany = max(terhelesek) / min(terhelesek)

        assert arany <= 1.15, (
            f"a darabok aránya {arany:.2f}× — "
            + ", ".join(f"{t/60:.1f}p" for t in terhelesek)
        )

    def test_a_leghosszabb_darab_a_hatarido_FELEN_belul(self, idok):
        """A tartalék nem fényűzés: a 2026-09-18-i körben a leghosszabb
        darab 28,6 perc volt a 30-as határidőnél."""
        leghosszabb = max(_terhelesek(idok)) / 60

        assert leghosszabb <= PLAFON_PERC, (
            f"a leghosszabb darab {leghosszabb:.1f} perc, a plafon "
            f"{PLAFON_PERC:.0f} perc ({HATARIDO_PERC} perces határidő fele)"
        )


class TestAJelentes:
    def test_az_idotullepest_KIMONDJA(self, capsys):
        """A puszta `exit 124` tesztbukásnak látszik — pedig nem az."""
        run_tests.jelentsd_a_bukasokat([("tests (tests/app nélkül)", 124)])

        kimenet = capsys.readouterr().out

        assert "IDŐTÚLLÉPÉS" in kimenet
        assert "nem tesztbukás" in kimenet

    def test_a_VALODI_bukas_marad_a_regi_alakban(self, capsys):
        """Ellenpróba: a tesztbukás nem kaphat időtúllépés-címkét."""
        run_tests.jelentsd_a_bukasokat([("tests/app/valami.py", 1)])

        kimenet = capsys.readouterr().out

        assert "exit 1" in kimenet
        assert "IDŐTÚLLÉPÉS" not in kimenet
