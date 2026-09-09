"""Az áthelyezés NEM hagyhat másolatot, ha a forrást nem tudta törölni (#998).

## A mért baj

A `shutil.move` először `os.rename`-t próbál; ha az elbukik (más
fájlrendszer, **vagy zárolt/nem törölhető fájl**), átvált `copy2 + unlink`-re.
Ha ekkor az `unlink` bukik, a **másolat MÁR ott van** a célban, a forrás
pedig megmarad — a kép **megkettőződik**, és a hibaüzenet erről nem szól.

Mérve (2026-09-09, Linux, írásvédett forrásmappa — POSIX-on a törléshez a
MAPPÁRA kell írásjog):

```
move_photo(...) -> PermissionError
a forrás megvan:                 True
a célban ott maradt egy másolat: True     ← ez a hiba
```

Ez a #998 windowsos leletének (`assert not copy_path.exists()` a
duplikátum-feloldás után) **platformfüggetlen magyarázata**: Windowson a
nyitva tartott fájl `os.rename`-je bukik, és ugyanez a másolat-marad ág fut.
A duplikátum-feloldásnál ez különösen kellemetlen: a felhasználó épp
duplikátumot akart megszüntetni, és kap egy újat.

## Amit ez a fájl őriz

1. a bukott áthelyezés **NEM hagy** másolatot a célban (visszagörgetés) — a
   közös `picasapy.fileops.safe_move` szerződése;
2. a forrás és a hozzá tartozó ini-szekció érintetlen marad;
3. a JOGOS `copy2 + unlink` út (más fájlrendszer) továbbra is működik.
"""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path

import pytest

from picasapy.fileops.move import move_photo
from picasapy.ini import load_document
from support.platform_marks import csak_posix_jogosultsag

_INI = ".picasa.ini"


@pytest.fixture
def fa(tmp_path: Path):
    """Forrásmappa egy képpel és ini-szekcióval + célmappa."""
    forras = tmp_path / "forras"
    forras.mkdir()
    kep = forras / "a.jpg"
    kep.write_bytes(b"kep-adat")
    (forras / _INI).write_text(
        "[a.jpg]\nstar=yes\nfilters=enhance=1;\n", encoding="utf-8"
    )
    cel = tmp_path / "Duplikatumok"
    cel.mkdir()
    return kep, cel


class TestABukottAthelyezesNemHagyMasolatot:
    @csak_posix_jogosultsag
    def test_nem_torolheto_forras(self, fa) -> None:
        kep, cel = fa
        kep.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)  # nem törölhető belőle
        try:
            with pytest.raises(OSError):
                move_photo(kep, cel)
            assert kep.exists(), "a forrás nem tűnhet el"
            assert not (cel / kep.name).exists(), (
                "#998: a bukott áthelyezés MÁSOLATOT hagyott a célban — a kép "
                "megkettőződött, pedig a művelet hibával tért vissza"
            )
        finally:
            kep.parent.chmod(stat.S_IRWXU)

    @csak_posix_jogosultsag
    def test_a_forras_ini_szekcioja_erintetlen(self, fa) -> None:
        kep, cel = fa
        kep.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)
        try:
            with pytest.raises(OSError):
                move_photo(kep, cel)
        finally:
            kep.parent.chmod(stat.S_IRWXU)
        szakasz = load_document(kep.parent / _INI).section("a.jpg")
        assert szakasz is not None and szakasz.get("star") == "yes"
        assert not (cel / _INI).exists(), "a célmappa ini-je nem születhet meg"

    def test_a_torles_bukasa_UTAN_sincs_masolat(self, fa, monkeypatch) -> None:
        """Ugyanaz jogosultság nélkül: a törlés a hibás lépés (a windowsos
        fájlzár is így viselkedik), a másolás előtte sikerül."""
        kep, cel = fa
        import picasapy.fileops.safe_move as move_modul

        monkeypatch.setattr(
            move_modul, "_rename", lambda s, t: (_ for _ in ()).throw(
                OSError(errno.EXDEV, "más fájlrendszer")
            )
        )
        # CSAK a FORRÁS törlése bukik — a frissen készült másolaté nem. Ez a
        # windowsos fájlzár alakja: a zárolt fájl nem törölhető, a másolat igen.
        # (Ha mindkettőt elrontanánk, a próba a visszagörgetést tenné
        # lehetetlenné, és nem azt mérné, amit állít.)
        igazi_unlink = move_modul._unlink

        def csak_a_forras_zarolt(ut):
            if Path(ut) == kep:
                raise PermissionError(errno.EACCES, "zárolt fájl")
            igazi_unlink(ut)

        monkeypatch.setattr(move_modul, "_unlink", csak_a_forras_zarolt)
        with pytest.raises(OSError):
            move_photo(kep, cel)
        assert kep.exists()
        assert not (cel / kep.name).exists(), (
            "#998: a törlés bukása után a másolatot vissza kell törölni"
        )


class TestAJogosMasolasUtElo:
    def test_mas_fajlrendszer_eseten_is_athelyez(self, fa, monkeypatch) -> None:
        """A `copy2 + unlink` út a más-fájlrendszeres áthelyezés JOGOS módja —
        a visszagörgetés nem törheti el."""
        kep, cel = fa
        import picasapy.fileops.safe_move as move_modul

        monkeypatch.setattr(
            move_modul, "_rename", lambda s, t: (_ for _ in ()).throw(
                OSError(errno.EXDEV, "más fájlrendszer")
            )
        )
        uj = move_photo(kep, cel)
        assert uj == cel / "a.jpg"
        assert uj.read_bytes() == b"kep-adat"
        assert not kep.exists(), "a forrásnak el kell tűnnie"
        szakasz = load_document(cel / _INI).section("a.jpg")
        assert szakasz is not None and szakasz.get("star") == "yes"

    def test_egyszeru_athelyezes_valtozatlan(self, fa) -> None:
        kep, cel = fa
        uj = move_photo(kep, cel)
        assert uj.exists() and not kep.exists()
        assert os.path.samefile(uj, cel / "a.jpg")
