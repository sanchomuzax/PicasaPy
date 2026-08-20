"""A CI-kör ne pörögjön feleslegesen (#1127).

## Miért van erre őr

Egy jegy végigvitele ~1 óra CI-időt vitt, és a tulajdonos ezt közvetlenül
érzi: *„Az 1-2 órája futó szarjaid miatt miért nekem kell szólni?"* és
*„Tilos 2-3 órás teszt köröket futni!"*

Két beállítás ebből sokat levesz, és mindkettő NÉMÁN tűnhet el egy későbbi
szerkesztésnél — a workflow-fájlt nem futtatja teszt, tehát csak ez az őr
szól, ha kikerül.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

CI = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def ci() -> dict:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))


def test_a_PR_uj_commitja_leallitja_az_elozo_futast(ci):
    """Új commit → a régi futás elhal. Enélkül a sor torlódik.

    ⚠️ A `main`-en ez NEM lehet bekapcsolva: ott minden commit
    CI-bizonyítéka kell, és a kiadási automatika is erre épül. Ezért a
    feltétel a `pull_request` eseményre szűkít, és a csoportkulcs a refet is
    tartalmazza."""
    egyidejuseg = ci.get("concurrency")
    assert egyidejuseg, "nincs `concurrency` — minden push külön futást pörget"

    csoport = str(egyidejuseg.get("group", ""))
    assert "github.ref" in csoport, (
        "a csoportkulcsban nincs benne a ref — két KÜLÖNBÖZŐ ág futása "
        "oltaná ki egymást"
    )

    megszakit = str(egyidejuseg.get("cancel-in-progress", ""))
    assert "pull_request" in megszakit, (
        "a megszakítás nincs `pull_request`-re szűkítve — a main futásai is "
        "elhalnának, és a kiadási automatika bizonyíték nélkül maradna"
    )


def test_minden_python_lepes_gyorsitotarazza_a_pipet(ci):
    """A pip-letöltés jobonként 1–2 perc; a gyorsítótár ezt levágja."""
    hianyzo = []
    for nev, job in (ci.get("jobs") or {}).items():
        for lepes in job.get("steps") or []:
            if not str(lepes.get("uses", "")).startswith("actions/setup-python"):
                continue
            with_ = lepes.get("with") or {}
            if with_.get("cache") != "pip":
                hianyzo.append(nev)
    assert not hianyzo, f"gyorsítótár nélküli Python-lépés ezekben: {hianyzo}"


class TestFelosztas:
    """A felosztás nem veszíthet el tesztet (#1127).

    ⚠️ A legveszélyesebb hibaalak itt a NÉMA kihagyás: ha egy egység
    egyetlen darabba sem kerül be, a CI zöld marad, miközben azt a fájlt
    senki nem futtatta. Ez rosszabb, mint egy piros CI.
    """

    @staticmethod
    def _egysegek():
        import sys

        sys.path.insert(0, str(CI.parents[2] / "scripts"))
        import run_tests

        gyoker = run_tests._ROOT
        app = sorted((gyoker / "tests" / "app").glob("test_*.py")) + sorted(
            (gyoker / "tests" / "app" / "qml_functional").glob("test_*.py")
        )
        return run_tests, [run_tests._NEM_APP] + [
            str(p.relative_to(gyoker)) for p in app
        ]

    def test_minden_egyseg_PONTOSAN_egy_darabba_kerul(self):
        """Sem kimaradás, sem kétszeres futtatás."""
        run_tests, egysegek = self._egysegek()
        darab = 4
        osszes: list[str] = []
        for i in range(1, darab + 1):
            osszes += sorted(run_tests._kiegyensulyozott_darab(egysegek, i, darab))
        assert sorted(osszes) == sorted(egysegek), (
            "a felosztás egységet veszített vagy duplázott"
        )

    def test_a_darabok_kiegyensulyozottak(self):
        """A leghosszabb/legrövidebb arány 2× alatt — különben a felosztás
        fele haszna elveszik a leglassabb darabon."""
        run_tests, egysegek = self._egysegek()
        idok = run_tests._mert_idok()
        if not idok:
            pytest.skip("nincs mért futásidő-térkép")
        terhek = []
        for i in range(1, 5):
            resz = run_tests._kiegyensulyozott_darab(egysegek, i, 4)
            terhek.append(sum(idok.get(nev, 0.0) for nev in resz))
        assert min(terhek) > 0
        assert max(terhek) / min(terhek) < 2.0, f"egyenetlen darabok: {terhek}"

    def test_egy_darab_eseten_MINDEN_fut(self):
        """`--shard 1/1` (és a hiányzó kapcsoló) a teljes készletet adja."""
        run_tests, egysegek = self._egysegek()
        assert run_tests._kiegyensulyozott_darab(egysegek, 1, 1) == set(egysegek)
        assert run_tests._shard_parameter([]) == (1, 1)
        assert run_tests._shard_parameter(["--shard", "3/4"]) == (3, 4)
        assert run_tests._shard_parameter(["--shard=2/4"]) == (2, 4)


def test_a_futtato_UTF8_kimenetet_kenyszerit():
    """A windowsos konzol cp1252-je nem ismeri a magyar `ő`/`ű` betűket.

    ⚠️ Egy `print()` rajtuk `UnicodeEncodeError`-rel elhasal, és a JOB
    azonnal elbukik — még mielőtt egyetlen teszt elindulna. A #1127-ben
    pontosan ez buktatta el MIND A NÉGY windows-darabot, egy „-ből" szótagon.

    Az őr a forrásra néz, mert a hatást csak windowsos konzolon lehetne
    előidézni; a szabály viszont platformfüggetlenül kimondható."""
    forras = (CI.parents[2] / "scripts" / "run_tests.py").read_text(encoding="utf-8")
    assert 'reconfigure(encoding="utf-8"' in forras, (
        "a futtató nem kényszerít UTF-8 kimenetet — egy magyar `ő` a "
        "windows-lábon elviszi az egész jobot"
    )
