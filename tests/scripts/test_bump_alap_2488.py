"""A verzióemelés alapja — a sorrend-versenyhelyzet őrei (#2488).

## Mit fog meg

A `release.yml` verzióemelő lépése abból döntött, hogy van-e már kiadás a
jelenlegi verzióhoz (`gh release view v$verzio`). Ez a lekérdezés UGYANANNAK
a futásnak a KIADÓ lépése ELŐTT fut, tehát a döntés a saját futása későbbi
mellékhatására támaszkodott. Mérve (2026-08-23): a kérdés tíz másodperccel a
`v0.8.58` létrejötte ELŐTT hangzott el, a válasz „még nincs" lett, a lépés
„nincs mit emelni" döntéssel továbbment — és a #1274 javítása kiadatlan
maradt a main-en.

A `scripts/bump_alap.py` a döntés alapját az ELŐZMÉNYBŐL veszi: melyik commit
állította be a jelenlegi verziót. Ez a kérdés a futás mellékhatásaitól
független.

Az őrök három rétege: a tiszta döntésfüggvény, a git-lekérdezés (itt dől el,
hogy tényleg NEM kérdezünk kiadást), és a `release.yml`-be kötés — a
munkafolyamatot semmilyen teszt nem futtatja, tehát a bekötés némán
kikerülhetne.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_UT = Path(__file__).resolve()
sys.path.insert(0, str(_UT.parents[2] / "scripts"))

import bump_alap  # noqa: E402
import kiadas_szukseges  # noqa: E402

RELEASE_YML = _UT.parents[2] / ".github" / "workflows" / "release.yml"


def _valasz(kimenet: str = "", *, kod: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=kod, stdout=kimenet, stderr="")


def _pyproject(verzio: str) -> str:
    return f'[project]\nname = "picasapy"\nversion = "{verzio}"\n'


def _futtato(elozmeny: dict[str, str | None], *, naplo: list[list[str]] | None = None):
    """Hamis git: az `elozmeny` a fejtől visszafelé rendezett sha → verzió."""

    def futtato(args: list[str]) -> subprocess.CompletedProcess[str]:
        if naplo is not None:
            naplo.append(list(args))
        if args[:2] == ["git", "log"]:
            return _valasz("".join(f"{sha}\n" for sha in elozmeny))
        if args[:2] == ["git", "show"]:
            sha = args[2].split(":", 1)[0]
            verzio = elozmeny.get(sha)
            if verzio is None:
                return _valasz(kod=1)
            return _valasz(_pyproject(verzio))
        raise AssertionError(f"váratlan hívás: {args}")

    return futtato


class TestDontes:
    """A tiszta döntésfüggvény — `(sha, verzió)` párok a fejtől visszafelé."""

    def test_a_verziot_beallito_commitot_adja(self):
        assert (
            bump_alap.alap_a_verziokbol(
                [("c", "0.8.58"), ("b", "0.8.58"), ("a", "0.8.57")]
            )
            == "b"
        )

    def test_ha_a_FEJ_allitotta_be_akkor_a_fej(self):
        """A napi útvonal: a beolvadt kód-PR maga hozta a verzióemelést —
        azóta nincs semmi, tehát nincs mit emelni. Enélkül a javítás
        minden beolvadás után kapna egy fölösleges második emelést."""
        assert (
            bump_alap.alap_a_verziokbol([("c", "0.8.58"), ("b", "0.8.57")]) == "c"
        )

    def test_az_olvashatatlan_regi_commit_hatarnak_szamit(self):
        """A `pyproject.toml` nem létezett mindig — a hiánya verzióváltás."""
        assert (
            bump_alap.alap_a_verziokbol([("c", "0.8.0"), ("b", "0.8.0"), ("a", None)])
            == "b"
        )

    def test_az_olvashatatlan_FEJ_a_tajekozodas_bukasa(self):
        """⚠️ Itt NEM tévedhetünk a kiadás felé: vakon emelve minden kör új
        verziót adna, és a rekurzió sosem állna meg. A `None` a
        munkafolyamatot a korábbi útra teszi vissza."""
        assert bump_alap.alap_a_verziokbol([("c", None), ("b", "0.8.57")]) is None
        assert bump_alap.alap_a_verziokbol([]) is None

    def test_verziovaltas_nelkuli_ablak_a_legregebbit_adja(self):
        """Tágabb diff = legfeljebb egy fölösleges patch-kiadás; az elmaradt
        kiadás a drágább hiba (`kiadas_szukseges.py` fejléce)."""
        assert (
            bump_alap.alap_a_verziokbol([("c", "0.8.58"), ("b", "0.8.58")]) == "b"
        )


class TestVersenyhelyzet:
    """A jegy mért esete, végig: kód érkezett a verzióemelés UTÁN, és a
    kiadás ebben a másodpercben születik meg."""

    def test_a_dontes_akkor_is_EMEL_ha_a_kiadas_meg_nem_letezik(self):
        elozmeny = {"kod": "0.8.58", "emeles": "0.8.58", "regi": "0.8.57"}
        naplo: list[list[str]] = []
        alap = bump_alap.alap_commit("HEAD", futtato=_futtato(elozmeny, naplo=naplo))

        assert alap == "emeles", "nem a verziót beállító commit lett az alap"
        # A `kod` commit a `src/` alatt módosított — azóta kiadatlan a munka.
        assert kiadas_szukseges.kiadasra_erdemes(["src/picasapy/app/valami.py"]) is True

        assert not any(a[0] == "gh" for a in naplo), (
            "a döntés még mindig kiadás-létét kérdez — pontosan ez a "
            "versenyhelyzet forrása (#2488)"
        )

    def test_a_kiadas_letere_semmi_nem_tamaszkodik(self):
        """Ugyanaz az előzmény kétszer ugyanazt adja — determinizmus."""
        elozmeny = {"kod": "0.8.58", "emeles": "0.8.58", "regi": "0.8.57"}
        elso = bump_alap.alap_commit("HEAD", futtato=_futtato(elozmeny))
        masodik = bump_alap.alap_commit("HEAD", futtato=_futtato(elozmeny))
        assert elso == masodik == "emeles"


class TestLekerdezes:
    def test_az_ELSO_SZULO_utjan_halad(self):
        """Összefésülő commitnál a PR SAJÁT emelése nem számít „azóta gyűlt
        munkának" — különben minden beolvadás után születne egy fölösleges
        második emelés."""
        naplo: list[list[str]] = []
        bump_alap.elso_szulok("HEAD", futtato=_futtato({"c": "0.8.1"}, naplo=naplo))
        assert "--first-parent" in naplo[0]

    def test_a_git_bukasa_None(self):
        assert bump_alap.alap_commit("HEAD", futtato=lambda args: _valasz(kod=1)) is None

    def test_a_main_a_shat_irja_ki(self, capsys):
        """A `release.yml` a STDOUT-ot olvassa be az alapnak."""
        elozmeny = {"kod": "0.8.58", "emeles": "0.8.58", "regi": "0.8.57"}
        assert bump_alap.main([], futtato=_futtato(elozmeny)) == 0
        assert capsys.readouterr().out.strip() == "emeles"

    def test_bukaskor_URES_a_stdout(self, capsys):
        """⚠️ A munkafolyamat üres kimenetből tudja, hogy vissza kell esnie —
        egy ide keveredő magyarázó sor commit-azonosítónak látszana."""
        assert bump_alap.main([], futtato=lambda args: _valasz(kod=1)) == 1
        assert capsys.readouterr().out.strip() == ""


class TestWorkflowBekotes:
    """A munkafolyamatot semmilyen teszt nem futtatja — ez az őr szól, ha a
    bekötés némán kikerül."""

    @staticmethod
    def _szoveg() -> str:
        return RELEASE_YML.read_text(encoding="utf-8")

    def test_az_alap_be_van_kotve(self):
        assert "scripts/bump_alap.py" in self._szoveg(), (
            "a verzióemelés alapja kikerült a release.yml-ből — a döntés újra "
            "a saját futása kiadására támaszkodik (#2488)"
        )

    def test_a_dontes_az_ALAPHOZ_hasonlit_nem_a_kiadashoz(self):
        szoveg = self._szoveg()
        assert 'kiadas_szukseges.py --base "$alap"' in szoveg, (
            "a kiadás-szükségesség még mindig a v$verzio taghez hasonlít — "
            "az a kiadás létére támaszkodik (#2488)"
        )

    def test_a_kiadas_lete_csak_TARTALEK(self):
        """A `gh release view` maradhat, de csak akkor, ha az alap nem
        állapítható meg — ha a fő útvonalon dönt, a versenyhelyzet visszatér."""
        szoveg = self._szoveg()
        alap = szoveg.index("scripts/bump_alap.py")
        kiadas = szoveg.index('gh release view "v$verzio"')
        assert alap < kiadas, (
            "a kiadás-lekérdezés az alap megállapítása ELŐTT dönt — "
            "a #2488 versenyhelyzete visszatért"
        )
        assert 'if [ -z "$alap" ]; then' in szoveg, (
            "a kiadás-lekérdezés nem tartalék ágban áll"
        )

    def test_a_kiadasi_job_TELJES_elozmenyt_hoz(self):
        """⚠️ A `bump_alap.py` a git-ELŐZMÉNYBŐL dolgozik — sekély
        checkouttal NÉMÁN elromlik.

        Sekély (`fetch-depth: 1`) checkoutnál a `git log --first-parent`
        egyetlen commitot ad vissza; a döntésfüggvény ilyenkor a fejet adja
        alapnak, a `kiadas_szukseges.py --base HEAD --head HEAD` üres diffet
        lát, és „nincs mit emelni" születik — pontosan az a néma elmaradás,
        amit a #2488 megszüntetett, csak más okból. Hibaüzenet SEHOL nem
        keletkezne: a szkript rendben lefut, csak rosszat mond.

        Ezért a mélység nem stílusdöntés, hanem a megoldás előfeltétele.
        """
        import re

        szoveg = self._szoveg()
        kiadasi_job = szoveg[szoveg.index("jobs:"):]
        checkout = kiadasi_job.index("actions/checkout")
        # a checkout utáni néhány sorban kell állnia a mélységnek
        korny = kiadasi_job[checkout:checkout + 200]
        talalat = re.search(r"fetch-depth:\s*(\S+)", korny)
        assert talalat is not None, (
            "a kiadási job checkoutja nem ad meg fetch-depth-et — az "
            "alapértelmezett sekély előzményen a bump_alap.py némán rosszat "
            "mond (#2488)"
        )
        assert talalat.group(1) == "0", (
            f"fetch-depth: {talalat.group(1)} — a bump_alap.py TELJES "
            "előzményt igényel; sekély checkouton némán „nincs mit emelni” "
            "születik (#2488)"
        )


class TestValodiGittel:
    """⚠️ A hamis futtató nem tudja, hogy a `git log` hívása helyes-e. Ez az
    egyetlen őr, ami VALÓDI előzményen méri le a jegy versenyhelyzetét."""

    @staticmethod
    def _git(mappa: Path, *args: str) -> None:
        eredmeny = subprocess.run(
            ["git", "-C", str(mappa), *args], capture_output=True, text=True, check=False
        )
        assert eredmeny.returncode == 0, eredmeny.stderr

    def _repo(self, mappa: Path) -> None:
        self._git(mappa, "init", "--quiet", "-b", "main")
        self._git(mappa, "config", "user.email", "or@example.invalid")
        self._git(mappa, "config", "user.name", "Őr")

    def test_a_kod_a_verzioemeles_UTAN_erkezett(self, tmp_path):
        """A #1274 esete: a kiadás még nem létezik (ez a futás hozza majd
        létre), a kód mégis kiadatlan — a döntésnek EMELNIE kell."""
        self._repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(_pyproject("0.8.57"), encoding="utf-8")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        self._git(tmp_path, "add", "-A")
        self._git(tmp_path, "commit", "--quiet", "-m", "regi")

        (tmp_path / "pyproject.toml").write_text(_pyproject("0.8.58"), encoding="utf-8")
        self._git(tmp_path, "commit", "--quiet", "-am", "chore: verzióemelés")
        emeles = subprocess.run(
            ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()

        (tmp_path / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        self._git(tmp_path, "commit", "--quiet", "-am", "fix: kiadatlan javítás")

        def futtato(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", "-C", str(tmp_path), *args[1:]],
                capture_output=True, text=True, check=False,
            )

        alap = bump_alap.alap_commit("HEAD", futtato=futtato)
        assert alap == emeles

        fajlok = kiadas_szukseges.valtozott_fajlok(alap, "HEAD", runner=futtato)
        assert kiadas_szukseges.kiadasra_erdemes(fajlok) is True, (
            "a verzióemelés óta érkezett kód nem indokolt emelést — a #2488 "
            "versenyhelyzete visszatért"
        )

    def test_a_beolvadt_emeles_utan_NINCS_mit_emelni(self, tmp_path):
        """A rekurzió korlátossága: a fej maga állította be a verziót."""
        self._repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(_pyproject("0.8.57"), encoding="utf-8")
        self._git(tmp_path, "add", "-A")
        self._git(tmp_path, "commit", "--quiet", "-m", "regi")
        (tmp_path / "pyproject.toml").write_text(_pyproject("0.8.58"), encoding="utf-8")
        self._git(tmp_path, "commit", "--quiet", "-am", "chore: verzióemelés")

        def futtato(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", "-C", str(tmp_path), *args[1:]],
                capture_output=True, text=True, check=False,
            )

        fej = subprocess.run(
            ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        alap = bump_alap.alap_commit("HEAD", futtato=futtato)
        assert alap == fej
        fajlok = kiadas_szukseges.valtozott_fajlok(alap, "HEAD", runner=futtato)
        assert kiadas_szukseges.kiadasra_erdemes(fajlok) is False
