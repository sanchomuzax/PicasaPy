"""#896 — a kiadás-pótló őr: átmeneti hibától nem szabad némán elbuknia.

Éles bizonyíték: 2026-08-17-én a `gh release create` egyetlen 503-ba futott
(GitHub-incidens), és a **v0.7.65 kiadás elmaradt**, miközben a merge sikeres
volt és a main verziója már az újat mutatta. A workflow-ban nem volt
újrapróbálkozás.

Az itteni őrök azt rögzítik, amit a YAML-be írt shell-ciklus SOHA nem tudna
állítani: hogy az újrapróbálkozás tényleg megtörténik, hogy a meglévő
kiadásra nem készül duplikátum, és hogy a végleges bukás ZAJOS.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ensure_release import ensure_release  # noqa: E402

TRANSIENT = (
    "HTTP 503: No server is currently available to service your request. "
    "Sorry about that."
)
NOT_FOUND = "release not found"


class FakeGh:
    """`gh`-utánzat: előre megadott válaszokat ad, és naplózza a hívásokat."""

    def __init__(self, responses: dict[str, list[tuple[int, str]]]) -> None:
        self._responses = {key: list(value) for key, value in responses.items()}
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(args))
        kind = "view" if "view" in args else "create"
        queue = self._responses.get(kind) or [(0, "")]
        code, text = queue.pop(0) if len(queue) > 1 else queue[0]
        return subprocess.CompletedProcess(args, code, stdout=text, stderr=text)

    def count(self, kind: str) -> int:
        return sum(1 for call in self.calls if kind in call)


@pytest.fixture
def sleeps() -> list[float]:
    return []


def _run(gh: FakeGh, sleeps: list[float], attempts: int = 5) -> int:
    return ensure_release(
        version="0.7.65",
        target="a4256373",
        repo="sanchomuzax/PicasaPy",
        runner=gh,
        sleeper=sleeps.append,
        attempts=attempts,
    )


class TestMarLetezoKiadas:
    def test_nem_hoz_letre_duplikatumot(self, sleeps):
        gh = FakeGh({"view": [(0, "v0.7.65")]})
        assert _run(gh, sleeps) == 0
        assert gh.count("create") == 0, "meglévő kiadásra nem szabad create-et hívni"
        assert sleeps == []

    def test_ketszer_lefuttatva_sem_duplikal(self, sleeps):
        """A #878 körében kézzel újra kellett futtatni a workflow-t — a
        lépésnek ezért idempotensnek kell lennie."""
        gh = FakeGh({"view": [(1, NOT_FOUND)], "create": [(0, "")]})
        assert _run(gh, sleeps) == 0
        utana = FakeGh({"view": [(0, "v0.7.65")]})
        assert _run(utana, sleeps) == 0
        assert utana.count("create") == 0


class TestAtmenetiHiba:
    def test_a_create_503_utan_ujraprobal_es_sikerul(self, sleeps):
        """EZ a #896 lényege: pontosan ez a forgatókönyv vitte el a v0.7.65-öt."""
        gh = FakeGh(
            {"view": [(1, NOT_FOUND)], "create": [(1, TRANSIENT), (1, TRANSIENT), (0, "")]}
        )
        assert _run(gh, sleeps) == 0
        assert gh.count("create") == 3
        assert len(sleeps) == 2

    def test_a_view_503_nem_ertelmezheto_nemletezokent(self, sleeps):
        """Ha a létezés-ellenőrzés esik el, abból NEM következik, hogy nincs
        kiadás — a hurok következő körében újra kell kérdezni."""
        gh = FakeGh({"view": [(1, TRANSIENT), (0, "v0.7.65")], "create": [(0, "")]})
        assert _run(gh, sleeps) == 0
        assert gh.count("create") == 0, "503-as view után nem szabad create-et hívni"

    def test_a_varakozas_no(self, sleeps):
        gh = FakeGh(
            {"view": [(1, NOT_FOUND)], "create": [(1, TRANSIENT), (1, TRANSIENT), (0, "")]}
        )
        _run(gh, sleeps)
        assert sleeps == sorted(sleeps) and sleeps[0] < sleeps[-1], sleeps


class TestVeglegesBukas:
    def test_kifogyott_probalkozas_utan_hibaval_ter_vissza(self, sleeps):
        gh = FakeGh({"view": [(1, NOT_FOUND)], "create": [(1, TRANSIENT)]})
        assert _run(gh, sleeps, attempts=3) == 1
        assert gh.count("create") == 3

    def test_a_bukas_ZAJOS(self, sleeps, capsys):
        """Néma exit 1 nem elég: a GitHub Actions felületén `::error::`
        nélkül a bukás nem tűnik fel a futáslistában."""
        gh = FakeGh({"view": [(1, NOT_FOUND)], "create": [(1, TRANSIENT)]})
        _run(gh, sleeps, attempts=2)
        kimenet = capsys.readouterr().out
        assert "::error::" in kimenet, kimenet
        assert "v0.7.65" in kimenet


class TestCsakEllenorzes:
    """`--check-only`: az ütemezett őrfutás módja. Ez fogja meg azt is, ha a
    kiadó workflow EL SEM INDUL — amit az újrapróbálkozás nem véd."""

    def test_meglevo_kiadasra_zold(self, sleeps):
        gh = FakeGh({"view": [(0, "v0.7.65")]})
        assert ensure_release(
            version="0.7.65",
            target="x",
            repo="r",
            runner=gh,
            sleeper=sleeps.append,
            check_only=True,
        ) == 0
        assert gh.count("create") == 0

    def test_hianyzo_kiadasra_hibat_jelez_es_NEM_hoz_letre(self, sleeps, capsys):
        gh = FakeGh({"view": [(1, NOT_FOUND)]})
        kod = ensure_release(
            version="0.7.65",
            target="x",
            repo="r",
            runner=gh,
            sleeper=sleeps.append,
            check_only=True,
        )
        assert kod == 1
        assert gh.count("create") == 0
        assert "::error::" in capsys.readouterr().out


class TestChangelogJegyzet:
    """A kiadási jegyzet a CHANGELOG-ból jön, nem a gépi PR-listából.

    A tulajdonos jelzése (2026-08-22): a Releases „What's Changed" szakasza
    „gépzaj" volt — bot-PR-címek, emberi összefoglaló nélkül."""

    def _changelog(self, tmp_path, szoveg):
        utvonal = tmp_path / "CHANGELOG.md"
        utvonal.write_text(szoveg, encoding="utf-8")
        return utvonal

    def test_a_verzio_szakaszat_adja(self, tmp_path):
        from ensure_release import changelog_notes

        utvonal = self._changelog(
            tmp_path,
            "# Cím\n\n## [1.2.3] – 2026-08-22\n\n### Javítva\n- valami\n\n"
            "## [1.2.2] – 2026-08-21\n\n- régi\n",
        )
        jegyzet = changelog_notes("1.2.3", utvonal)
        assert "### Javítva" in jegyzet and "- valami" in jegyzet
        assert "régi" not in jegyzet

    def test_helykitolto_szakasznal_ures(self, tmp_path):
        from ensure_release import changelog_notes

        utvonal = self._changelog(
            tmp_path, "## [1.2.3] – 2026-08-22\n\n*(nincs felhasználói változás)*\n"
        )
        assert changelog_notes("1.2.3", utvonal) == ""

    def test_hianyzo_szakasznal_ures(self, tmp_path):
        from ensure_release import changelog_notes

        utvonal = self._changelog(tmp_path, "## [9.9.9] – 2026-01-01\n\n- x\n")
        assert changelog_notes("1.2.3", utvonal) == ""

    def test_hianyzo_fajlnal_ures(self, tmp_path):
        from ensure_release import changelog_notes

        assert changelog_notes("1.2.3", tmp_path / "nincs.md") == ""


def _CP(args, kod, kimenet):
    import subprocess
    return subprocess.CompletedProcess(args, kod, kimenet, "")


class TestAJegyzetSosemGepzaj:
    """A Releases hasábra gépi PR-lista nem mehet ki (2026-08-23).

    MÉRVE: a verzióemelő lánc körönként EGY kiadást csinál, de a CHANGELOG
    `[Nem kiadott]` szakaszát az ELSŐ emelés elviszi — a többi kiadás
    szakasz nélkül marad. A `--generate-notes` ilyenkor a bot-PR-ek címeit
    listázta, és **három egymást követő kiadás** (0.8.53–0.8.55) így ment
    ki. Pont az, amit a tulajdonos „gépzajként" kifogásolt.
    """

    def test_szakasz_nelkul_EMBERI_tartalek_megy_ki(self, sleeps, tmp_path):
        import scripts.ensure_release as modul
        from scripts.ensure_release import tartalek_jegyzet

        # CHANGELOG szakasz NÉLKÜL erre a verzióra — pontosan az az eset,
        # amit a verzióemelő lánc körönként előállít
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [0.1.0] – 2020-01-01\n", encoding="utf-8")
        gh = FakeGh({"view": [(1, "release not found")], "create": [(0, "")]})
        assert (
            modul.ensure_release(
                version="0.7.65",
                target="a4256373",
                repo="sanchomuzax/PicasaPy",
                runner=gh,
                sleeper=sleeps.append,
                attempts=5,
                changelog=naplo,
            )
            == 0
        )

        create = next(hivas for hivas in gh.calls if "create" in hivas)
        assert "--generate-notes" not in create, (
            "gépi PR-lista került volna a Releases hasábra"
        )
        assert "--notes" in create
        assert create[create.index("--notes") + 1] == tartalek_jegyzet()

    def test_a_tartalek_SOHA_nem_allithatja_hogy_nincs_valtozas(self):
        """#1340 — ez az állítás korábban HAZUDOTT, és ez a teszt őrizte.

        A v0.8.71 (a letiltott gombok megjelenése, #893) és a v0.8.72 (a
        lasszós kijelölés, #897) ezzel a mondattal ment ki:

            „Ez a kiadás nem hoz felhasználónak látszó változást."

        A tulajdonos vette észre. A régi állítás azt kérte számon a
        szövegen, hogy tartalmazza ezt a mondatot — vagyis a hazugságot
        rögzítette szerződésként, ráadásul „őszinte" néven. A szkript NEM
        TUDHATJA, hogy nem volt látható változás; amit tud, az az, hogy
        nincs hozzá emberi mondat. Csak ezt szabad kimondania."""
        from scripts.ensure_release import tartalek_jegyzet

        szoveg = tartalek_jegyzet(("a letiltott gomb halványan rajzolódik (#893)",))
        assert "nem hoz felhasználónak látszó változást" not in szoveg
        assert "nem készült emberi összefoglaló" in szoveg
        assert "a letiltott gomb halványan rajzolódik (#893)" in szoveg

    def test_a_tartalek_valtozas_nelkul_ezt_KI_IS_MONDJA(self):
        """Ha tényleg nincs mit mondani, azt tényként mérjük, nem feltesszük."""
        from scripts.ensure_release import tartalek_jegyzet

        szoveg = tartalek_jegyzet(())
        assert "verziólépés" in szoveg
        assert "nem készült emberi összefoglaló" not in szoveg

    def test_a_MERES_BUKASA_nem_valhat_allitassa(self):
        """#1340 — ugyanaz a hiba, egy szinttel feljebb.

        Ha a beolvadt munkákat nem sikerül lekérdezni, az NEM azt jelenti,
        hogy nincs mit mondani. Az éles próbán ez azonnal elő is jött: a már
        felcímkézett commitra a `git describe` magát a címkét adta vissza, a
        tartomány üres lett, és a szöveg megint azt állította volna, hogy
        „csak verziólépés" — pont az a fajta hazugság, ami miatt ez a jegy
        megnyílt."""
        from scripts.ensure_release import tartalek_jegyzet

        szoveg = tartalek_jegyzet(None)
        assert "sem sikerült megállapítani" in szoveg
        assert "csak verziólépést tartalmaz" not in szoveg

    def test_a_sajat_cimkejet_kihagyja_a_tartomanybol(self):
        """A kiadandó verzió címkéje már ott ülhet a célon (ütemezett futás)."""
        import scripts.ensure_release as modul

        hivasok = []

        def futtat(args):
            hivasok.append(args)
            if "describe" in args:
                return _CP(args, 0, "v0.8.70\n")
            return _CP(args, 0, "fix: valami (#1)\n")

        assert modul.valodi_valtozasok("abc123", version="0.8.71", runner=futtat) == (
            "valami (#1)",
        )
        describe = next(h for h in hivasok if "describe" in h)
        assert "--exclude" in describe and "v0.8.71" in describe

    def test_a_tartalek_kihagyja_az_automatika_sajat_commitjait(self):
        """A „chore: verzióemelés" sor a felhasználónak semmit nem mond."""
        from scripts.ensure_release import erdemi_valtozasok

        assert erdemi_valtozasok([
            "chore: verzióemelés a beolvadt munkához (#1127) (#1332)",
            "fix: a letiltott gomb 25%-os alfával rajzolódik (#893) (#1331)",
        ]) == ("a letiltott gomb 25%-os alfával rajzolódik (#893) (#1331)",)

    def test_szakasszal_a_CHANGELOG_szovege_megy_ki(self, sleeps, tmp_path):
        import scripts.ensure_release as modul

        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text(
            "# Változásnapló\n\n## [0.7.65] – 2026-01-01\n\n"
            "### Javítva\n- **Valami emberi mondat.**\n",
            encoding="utf-8",
        )
        gh = FakeGh({"view": [(1, "release not found")], "create": [(0, "")]})
        assert (
            modul.ensure_release(
                version="0.7.65",
                target="a4256373",
                repo="sanchomuzax/PicasaPy",
                runner=gh,
                sleeper=sleeps.append,
                attempts=5,
                changelog=naplo,
            )
            == 0
        )

        create = next(hivas for hivas in gh.calls if "create" in hivas)
        assert "Valami emberi mondat" in create[create.index("--notes") + 1]
