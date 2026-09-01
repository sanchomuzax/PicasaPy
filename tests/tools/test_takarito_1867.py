"""#1867 — a takarító FOGA: mikor NEM szabad törölnie.

## Miért ezek a tesztek, és nem „töröl-e"

Egy takarító akkor veszélyes, ha téved: a `--torol` kérdés nélkül dolgozik,
és a tévedés visszafordíthatatlan. Ezért a készlet súlypontja a NEM-eken
van. Mindegyik eset VALÓDI, az első futásból:

1. **a fő munkamásolat** „elvihető"-ként jelent meg (6,3 GB!), mert éppen
   egy beolvadt ágon állt — `--torol` mellett a projektet vitte volna el;
2. **idegen munkamenet fája** elvihetőnek látszott, holott a másiké;
3. **`bundled-skills/2.1.227`** scratchpadnek látszott — pedig készlet.

## A hamis negatív, ami miatt a jegy megszületett

A `git branch --merged` / `merge-base --is-ancestor` az összevont
beolvasztást NEM látja: mérve 20/20 hamis negatív. Ezért a takarító a
PR-ÁLLAPOTOT kérdezi. Az itteni tesztek ezt kívülről adják be
(`allapot=`), tehát a `gh` elérhetősége nélkül is mérnek.
"""

from __future__ import annotations

import os
import time

import pytest

from scripts import takarito


@pytest.fixture
def most() -> float:
    return time.time()


def _korral(ut, most: float, ora: float):
    """A könyvtár mtime-ja PONTOSAN `ora` órával ezelőtt.

    Nem hagyatkozunk a létrehozás pillanatára: a `most` fixture és a
    `mkdir()` sorrendje fixture-függő, és fordított sorrendben a kor
    NEGATÍV lesz — ezen bukott el az első változatom."""
    os.utime(ut, (most - ora * 3600, most - ora * 3600))
    return ut


class TestBasetempek:
    """Árva `run_tests.py`-basetempek."""

    def test_a_tul_friss_MARAD(self, tmp_path, most):
        p = tmp_path / (takarito.TESZT_ELOTAG + "friss")
        p.mkdir()
        _korral(p, most, ora=1)
        talalt = takarito.basetempek(most, ora=6, gyoker=tmp_path,
                                     hasznalja=lambda _u: False)
        assert talalt == [], "a friss maradékot elvihetőnek jelöltük"

    def test_a_regi_ELVIHETO(self, tmp_path, most):
        p = tmp_path / (takarito.TESZT_ELOTAG + "regi")
        p.mkdir()
        _korral(p, most, ora=24)
        talalt = takarito.basetempek(most, ora=6, gyoker=tmp_path,
                                     hasznalja=lambda _u: False)
        assert len(talalt) == 1 and talalt[0].elvihetjuk

    def test_amit_FOLYAMAT_HASZNAL_nem_vihetjuk(self, tmp_path, most):
        """A kor ÖNMAGÁBAN nem elég: futó teszt basetempje régi is lehet."""
        p = tmp_path / (takarito.TESZT_ELOTAG + "hasznalt")
        p.mkdir()
        _korral(p, most, ora=24)
        talalt = takarito.basetempek(most, ora=6, gyoker=tmp_path,
                                     hasznalja=lambda _u: True)
        assert len(talalt) == 1
        assert not talalt[0].elvihetjuk
        assert "HASZNÁLJA" in talalt[0].indok


class TestMunkamasolatok:
    def test_a_FO_munkamasolat_sosem_vihetjuk_el(self):
        """A `git worktree list` első tétele a fő checkout.

        Ez az eset ÉLESBEN előfordult: a fő checkout egy beolvadt ágon
        állt, és 6,3 GB-os »elvihető« tételként jelent meg."""
        talalt = takarito.munkamasolatok(allapot=lambda _ag: "MERGED")
        fo = takarito.REPO.resolve()
        assert all(t.ut.resolve() != fo for t in talalt)
        # a valódi fő checkout (a repó szülője alatt) sem lehet közte
        nevek = {t.ut.name for t in talalt}
        assert "PicasaPy" not in nevek, "a fő munkamásolat elvihetőnek jelölve"

    def test_idegen_munkamenet_fajat_CSAK_jelentjuk(self, monkeypatch):
        """Beolvadt ág IDEGEN munkamenet scratchpadjében: csak jelentés.

        A `git worktree list` kimenetét SZINTETIKUSAN adjuk be, nem a gép
        valódi állapotát nézzük — különben a teszt üres napon zölden
        hallgatna, és épp ez a mutáció csúszna át (mérve: enélkül a
        »minden fa elvihető« mutáció NEM bukott el).
        """
        idegen = (
            "/tmp/claude-1000/-home-sancho-Documents-PicasaPy/"
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/scratchpad/wt-valami"
        )
        kimenet = (
            f"worktree {takarito.REPO}\nbranch refs/heads/main\n\n"
            f"worktree {idegen}\nbranch refs/heads/feat/valami\n\n"
        )

        class Valasz:
            returncode = 0
            stdout = kimenet

        # a MODULSZINTŰ fogantyút cseréljük, nem a globális
        # `subprocess.run`-t: az minden más modulra átszivárogna,
        # amíg a teszt fut (#1375 — a projekt őre ezt fogta meg).
        monkeypatch.setattr(takarito, "_run", lambda *a, **k: Valasz())
        monkeypatch.setattr(takarito, "meret", lambda _u: 0)
        talalt = takarito.munkamasolatok(allapot=lambda _ag: "MERGED")
        assert len(talalt) == 1, "a szintetikus fa nem jutott át a szűrőn"
        assert not talalt[0].elvihetjuk, (
            "idegen munkamenet fáját elvihetőnek jelöltük"
        )
        assert "IDEGEN" in talalt[0].indok

    def test_nyitott_PR_fajat_nem_visszuk_el(self):
        assert takarito.munkamasolatok(allapot=lambda _ag: "OPEN") == []

    def test_ismeretlen_allapotnal_MARAD(self):
        """`None` = nincs PR vagy a `gh` nem elérhető — ilyenkor NEM
        találgatunk. A csendes irányba tévedni javítható; a másikba nem."""
        assert takarito.munkamasolatok(allapot=lambda _ag: None) == []

    def test_a_git_merged_kerdest_NEM_hasznaljuk(self):
        """A megbízhatatlan git-kérdés nem szerepelhet FUTTATOTT parancsban.

        AST-tel nézzük a `subprocess.run` argumentumlistáit, nem
        szövegkereséssel: a docstring és a komment SZÁNDÉKOSAN említi a
        `--merged`-et és a `merge-base --is-ancestor`-t (azt magyarázza,
        miért nem használjuk), egy nyers grep tehát a saját indoklásunkon
        bukna el. Ez a #1052 tanulsága: a komment sem hazudhat, de az őr
        se olvassa kommentnek a kódot."""
        import ast

        fa = ast.parse(
            (takarito.REPO / "scripts" / "takarito.py").read_text(encoding="utf-8")
        )
        tiltott = {"--merged", "merge-base", "--is-ancestor"}
        talalt: list[str] = []
        for csomopont in ast.walk(fa):
            if not isinstance(csomopont, ast.Call):
                continue
            for arg in csomopont.args:
                if not isinstance(arg, (ast.List, ast.Tuple)):
                    continue
                for elem in arg.elts:
                    if isinstance(elem, ast.Constant) and elem.value in tiltott:
                        talalt.append(str(elem.value))
        assert not talalt, f"megbízhatatlan git-kérdés a parancsban: {talalt}"


class TestScratchpadek:
    UUID_A = "aaaaaaaa-1111-2222-3333-444444444444"
    UUID_B = "bbbbbbbb-1111-2222-3333-444444444444"

    @pytest.fixture
    def gyoker(self, tmp_path):
        """SZINTETIKUS fa — a gép valódi állapota nem befolyásolhatja.

        Az első változatom a `/tmp/claude-1000`-t nézte, és a CI-n
        (ahol nincs scratchpad) ÜRES listán állított — a teszt így nem
        mondott semmit, és el is bukott."""
        p = tmp_path / "claude-1000" / "-projekt"
        p.mkdir(parents=True)
        (p / self.UUID_A).mkdir()
        (p / self.UUID_B).mkdir()
        (p / "bundled-skills").mkdir()   # NEM munkamenet
        for gyerek in p.iterdir():
            os.utime(gyerek, (time.time() - 5 * 86400,) * 2)
        return tmp_path / "claude-1000"

    def test_idegen_munkamenetet_CSAK_jelentunk(self, gyoker, most):
        """Akkor sem törlünk idegen fát, ha minden jel halottnak mutatja."""
        talalt = takarito.scratchpadek(most, nap=0, sajat="nincs-ilyen",
                                       gyoker=gyoker, hasznalja=lambda _u: False)
        assert len(talalt) == 2
        assert all(not t.elvihetjuk for t in talalt)

    def test_a_sajatot_elvihetjuk(self, gyoker, most):
        talalt = takarito.scratchpadek(most, nap=0, sajat=self.UUID_A,
                                       gyoker=gyoker, hasznalja=lambda _u: False)
        enyem = [t for t in talalt if t.ut.name == self.UUID_A]
        masikok = [t for t in talalt if t.ut.name != self.UUID_A]
        assert enyem and enyem[0].elvihetjuk
        assert masikok and not any(t.elvihetjuk for t in masikok)

    def test_a_hasznalatban_levot_kihagyjuk(self, gyoker, most):
        assert takarito.scratchpadek(most, nap=0, sajat=None, gyoker=gyoker,
                                     hasznalja=lambda _u: True) == []

    def test_a_tul_friss_MARAD(self, gyoker, most):
        for gyerek in (gyoker / "-projekt").iterdir():
            os.utime(gyerek, (most, most))
        assert takarito.scratchpadek(most, nap=2, sajat=None, gyoker=gyoker,
                                     hasznalja=lambda _u: False) == []

    def test_csak_UUID_nevu_konyvtar_szamit_munkamenetnek(self, gyoker, most):
        """A `bundled-skills/2.1.227` az első futáson scratchpadnek
        látszott — pedig az a KÉSZLET, nem maradék."""
        talalt = takarito.scratchpadek(most, nap=0, sajat=None, gyoker=gyoker,
                                       hasznalja=lambda _u: False)
        assert {t.ut.name for t in talalt} == {self.UUID_A, self.UUID_B}


class TestATorlesKapuja:
    def test_amit_nem_vihetunk_el_azt_nem_torli(self, tmp_path):
        p = tmp_path / "idegen"
        p.mkdir()
        tetel = takarito.Tetel(p, "scratchpad", "idegen", 0, elvihetjuk=False)
        assert takarito.torol(tetel) is False
        assert p.exists(), "a torol() elvitte, amit nem lett volna szabad"

    def test_a_jelentes_alapertelmezes(self, capsys, monkeypatch, tmp_path):
        """`--torol` nélkül semmi nem tűnhet el — SZINTETIKUS tétellel.

        Az első változatom a gép valódi állapotára támaszkodott, és a
        CI-n (ahol nincs mit takarítani) »Nincs takarítanivaló«-t kapott,
        tehát épp azt nem mérte, amit állított."""
        proba = tmp_path / "proba"
        proba.mkdir()
        tetel = takarito.Tetel(proba, "scratchpad", "próba", 1, elvihetjuk=True)
        monkeypatch.setattr(takarito, "munkamasolatok", lambda **_k: [tetel])
        monkeypatch.setattr(takarito, "basetempek", lambda *a, **k: [])
        monkeypatch.setattr(takarito, "scratchpadek", lambda *a, **k: [])
        assert takarito.main([]) == 0
        assert "csak jelentés" in capsys.readouterr().out
        assert proba.exists(), "a jelentő ág törölt"


class TestPlatformFuggetlenseg:
    """A takarító a windows-lábon is FUT — ott is csak jelent.

    ⚠️ Ez a készlet a #1868 beolvadása UTÁN született, mert a windows-láb
    **11 tesztet buktatott** rajta:

        scripts\\takarito.py:308: in tmp_szazalek
            st = os.statvfs("/tmp")
        AttributeError: module 'os' has no attribute 'statvfs'

    Az `os.statvfs` **POSIX-only**, és az `except OSError` nem fogja meg —
    az `AttributeError` nem `OSError`. A hiba csak azért derült ki, mert a
    #1865 óta a windows-láb bukása LÁTSZIK; korábban hetekig elült volna.

    ⚠️ Ezt **nem lehet Linuxon hűen szimulálni**: az `os.statvfs`
    törlésével a `shutil.disk_usage` is elhasal, holott Windowson az más
    úton dolgozik. Ezért FORRÁS-szintű az őr — azt nézi, hívunk-e
    POSIX-only nevet —, nem viselkedésit.
    """

    #: POSIX-only nevek, amelyek Windowson `AttributeError`-t adnak.
    POSIX_ONLY = ("statvfs", "getuid", "geteuid", "fork", "getppid", "setuid")

    def test_nincs_posix_only_hivas(self):
        import ast

        forras = (takarito.REPO / "scripts" / "takarito.py").read_text(encoding="utf-8")
        talalt = [
            f"os.{csomopont.attr}"
            for csomopont in ast.walk(ast.parse(forras))
            if isinstance(csomopont, ast.Attribute)
            and csomopont.attr in self.POSIX_ONLY
            and isinstance(csomopont.value, ast.Name)
            and csomopont.value.id == "os"
        ]
        assert not talalt, (
            f"POSIX-only hívás a takarítóban: {talalt}. Windowson ez "
            "AttributeError, amit az `except OSError` NEM fog meg."
        )

    def test_a_tmp_gyoker_a_platformtol_jon(self):
        """Beégetett `/tmp` helyett `tempfile.gettempdir()`.

        ⚠️ FORRÁS-szintű, szándékosan. Az első változatom az ÉRTÉKET
        hasonlította a `tempfile.gettempdir()`-hez — Linuxon mindkettő
        `/tmp`, tehát a teszt akkor is zöld maradt, ha a konstans BEÉGETETT
        `/tmp` volt. Mutációval mérve: átcsúszott.
        """
        import ast

        forras = (takarito.REPO / "scripts" / "takarito.py").read_text(encoding="utf-8")
        ertek = next(
            csomopont.value
            for csomopont in ast.walk(ast.parse(forras))
            if isinstance(csomopont, ast.Assign)
            and any(
                isinstance(cel, ast.Name) and cel.id == "TMP_GYOKER"
                for cel in csomopont.targets
            )
        )
        szoveg = ast.unparse(ertek)
        assert "gettempdir" in szoveg, (
            f"a TMP_GYOKER nem a platformtól jön: {szoveg}"
        )

    def test_a_szazalek_mindig_szamot_ad(self):
        szazalek = takarito.tmp_szazalek()
        assert isinstance(szazalek, int)
        assert 0 <= szazalek <= 100
