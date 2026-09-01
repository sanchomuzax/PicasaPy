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

import time

import pytest

from scripts import takarito


@pytest.fixture
def most() -> float:
    return time.time()


class TestBasetempek:
    """Árva `run_tests.py`-basetempek."""

    def test_a_tul_friss_MARAD(self, tmp_path, monkeypatch, most):
        p = tmp_path / (takarito.TESZT_ELOTAG + "friss")
        p.mkdir()
        monkeypatch.setattr(takarito, "Path", takarito.Path)
        talalt = takarito.basetempek(
            most, ora=6, hasznalja=lambda _u: False
        )
        assert all(t.ut != p for t in talalt), "a friss maradék nem vihető el"

    def test_amit_FOLYAMAT_HASZNAL_nem_vihetjuk(self, monkeypatch, most):
        """A kor ÖNMAGÁBAN nem elég: futó teszt basetempje régi is lehet."""
        talalt = takarito.basetempek(most, ora=0, hasznalja=lambda _u: True)
        assert all(not t.elvihetjuk for t in talalt), (
            "használatban lévő basetempet jelöltünk elvihetőnek"
        )
        assert all("HASZNÁLJA" in t.indok for t in talalt)


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

        monkeypatch.setattr(takarito.subprocess, "run",
                            lambda *a, **k: Valasz())
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
    def test_idegen_munkamenetet_CSAK_jelentunk(self, most):
        """Akkor sem törlünk idegen fát, ha minden jel halottnak mutatja."""
        talalt = takarito.scratchpadek(
            most, nap=0, sajat="nincs-ilyen-munkamenet", hasznalja=lambda _u: False
        )
        assert all(not t.elvihetjuk for t in talalt), (
            "idegen munkamenet scratchpadjét elvihetőnek jelöltük"
        )

    def test_a_sajatot_elvihetjuk(self, most):
        talalt = takarito.scratchpadek(most, nap=0, sajat=None,
                                       hasznalja=lambda _u: False)
        assert talalt, "a mérés üres — a teszt nem mondana semmit"
        sajat_nev = talalt[0].ut.name
        ujra = takarito.scratchpadek(most, nap=0, sajat=sajat_nev,
                                     hasznalja=lambda _u: False)
        enyem = [t for t in ujra if t.ut.name == sajat_nev]
        assert enyem and enyem[0].elvihetjuk

    def test_a_hasznalatban_levot_kihagyjuk(self, most):
        assert takarito.scratchpadek(most, nap=0, sajat=None,
                                     hasznalja=lambda _u: True) == []

    def test_csak_UUID_nevu_konyvtar_szamit_munkamenetnek(self, most):
        """A `bundled-skills/2.1.227` az első futáson scratchpadnek
        látszott — pedig az a KÉSZLET, nem maradék."""
        talalt = takarito.scratchpadek(most, nap=0, sajat=None,
                                       hasznalja=lambda _u: False)
        assert all(takarito._UUID.match(t.ut.name) for t in talalt)


class TestATorlesKapuja:
    def test_amit_nem_vihetunk_el_azt_nem_torli(self, tmp_path):
        p = tmp_path / "idegen"
        p.mkdir()
        tetel = takarito.Tetel(p, "scratchpad", "idegen", 0, elvihetjuk=False)
        assert takarito.torol(tetel) is False
        assert p.exists(), "a torol() elvitte, amit nem lett volna szabad"

    def test_a_jelentes_alapertelmezes(self, capsys):
        """`--torol` nélkül semmi nem tűnhet el."""
        assert takarito.main([]) == 0
        assert "csak jelentés" in capsys.readouterr().out
