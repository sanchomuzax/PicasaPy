"""A bukott MAPPA-áthelyezés nem hagy félkész fát a célban (#2785).

## A mért baj

A `shutil.move` könyvtárnál `copytree` + `rmtree`-t végez, ha az `os.rename`
nem megy (más fájlrendszer). Ha a `copytree` menet közben bukik, a célban
**félig átmásolt fa** marad, a forrás pedig a helyén.

Mérve (2026-09-09, cross-device szimulációval, olvashatatlan alkönyvtárral):

```
shutil.move(...) -> shutil.Error
a forrás megvan:   True
a CÉL létrejött:   True      ← félkész: csak a gyökér fájlja van benne
```

A felhasználó egy hibaüzenetet kap, mellette egy fél mappát a célban — és a
következő próbálkozás már „Ilyen nevű mappa már létezik"-kel áll meg. A
`move_folder` docstringje közben azt ígéri, hogy „a mozgatás vagy TELJESEN
sikerüljön, vagy sehogy": az ígéret és a viselkedés eltért.

## A megvalósított menet

1. `os.rename` — ha megy, kész (atomi, ugyanazon a fájlrendszeren);
2. különben `copytree` egy **ideiglenes névre** a cél MELLÉ;
3. a forrás törlése;
4. az ideiglenes fa átnevezése a végleges névre.

Bukás a 2. vagy a 3. lépésben → az ideiglenes fa törlődik, a forrás
érintetlen, a célban **semmi**. A 4. lépés bukása az egyetlen, ami nem
görgethető vissza (a forrás már nincs); ott a hibaüzenet **megnevezi**, hol
van az áthelyezett tartalom.
"""

from __future__ import annotations

import errno
import importlib
import os
import shutil
from pathlib import Path

import pytest

from picasapy.fileops.move_folder import FolderMoveError, move_folder


def _modul():
    """A MODUL, nem a `picasapy.fileops.move_folder` FÜGGVÉNY.

    ⚠️ A csomag `__init__`-je újraexportálja a függvényt ugyanezen a néven,
    tehát az `import picasapy.fileops.move_folder as mf` a FÜGGVÉNYT adja —
    a `monkeypatch.setattr(mf, "_rename", …)` ott `AttributeError`-t dob.
    """
    return importlib.import_module("picasapy.fileops.move_folder")


@pytest.fixture
def fa(tmp_path: Path):
    """Forrásmappa két szinten + célszülő."""
    forras = tmp_path / "nyaralas"
    (forras / "alkonyvtar").mkdir(parents=True)
    (forras / "a.jpg").write_bytes(b"kep")
    (forras / "alkonyvtar" / "b.jpg").write_bytes(b"kep2")
    (forras / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
    celszulo = tmp_path / "cel"
    celszulo.mkdir()
    return forras, celszulo


def _mas_fajlrendszer(monkeypatch, forras: Path) -> None:
    """Az `os.rename` bukása CSAK a forrásra — ez tereli a copy+remove útra.

    ⚠️ Az ideiglenes fa VÉGLEGES nevére való átnevezés ugyanezt a fogantyút
    használja, és az a cél oldalán, ugyanazon a fájlrendszeren történik: ha
    azt is elrontanánk, a más-fájlrendszeres HAPPY PATH sem tudna lefutni,
    és a próba nem azt mérné, amit állít.
    """
    igazi = os.rename

    def csak_a_forrasra(s, t):
        if Path(s) == forras:
            raise OSError(errno.EXDEV, "más fájlrendszer")
        return igazi(s, t)

    monkeypatch.setattr(_modul(), "_rename", csak_a_forrasra)


class TestAzEgyszeruUtValtozatlan:
    def test_ugyanazon_a_fajlrendszeren_athelyez(self, fa) -> None:
        forras, celszulo = fa
        uj = move_folder(forras, celszulo)
        assert uj == celszulo / "nyaralas"
        assert (uj / "alkonyvtar" / "b.jpg").read_bytes() == b"kep2"
        assert (uj / ".picasa.ini").exists(), "a kísérőfájl vele megy"
        assert not forras.exists()

    def test_mas_fajlrendszeren_is_athelyez(self, fa, monkeypatch) -> None:
        forras, celszulo = fa
        _mas_fajlrendszer(monkeypatch, forras)
        uj = move_folder(forras, celszulo)
        assert (uj / "alkonyvtar" / "b.jpg").read_bytes() == b"kep2"
        assert (uj / ".picasa.ini").exists()
        assert not forras.exists()
        assert sorted(p.name for p in celszulo.iterdir()) == ["nyaralas"], (
            "ideiglenes fa nem maradhat a célszülőben"
        )


class TestABukottMasolasNemHagyNyomot:
    def test_a_masolas_kozbeni_bukas_utan_a_cel_URES(self, fa, monkeypatch) -> None:
        forras, celszulo = fa
        _mas_fajlrendszer(monkeypatch, forras)
        monkeypatch.setattr(
            _modul(),
            "_copytree",
            lambda s, t: (_ for _ in ()).throw(OSError("olvashatatlan alkönyvtár")),
        )
        with pytest.raises(FolderMoveError):
            move_folder(forras, celszulo)
        assert forras.is_dir(), "a forrásnak érintetlenül kell maradnia"
        assert (forras / "alkonyvtar" / "b.jpg").exists()
        assert list(celszulo.iterdir()) == [], (
            "#2785: a bukott áthelyezés félkész fát hagyott a célban"
        )

    def test_a_forras_torlesenek_bukasa_utan_sincs_nyom(self, fa, monkeypatch) -> None:
        """A forrás nem törölhető (zárolt fájl, írásvédett szülő): ilyenkor a
        MÁSOLAT sem maradhat — különben a mappa megkettőződne."""
        forras, celszulo = fa
        _mas_fajlrendszer(monkeypatch, forras)
        # CSAK a FORRÁS törlése bukik — az ideiglenes fáé nem. Ha mindkettőt
        # elrontanánk, a visszagörgetést tennénk lehetetlenné, és a próba nem
        # azt mérné, amit állít (ugyanaz a hiba, mint a #998 fájl-ágán).
        igazi = shutil.rmtree

        def csak_a_forras_zarolt(ut):
            if Path(ut) == forras:
                raise PermissionError("zárolt fájl")
            igazi(ut)

        monkeypatch.setattr(_modul(), "_rmtree", csak_a_forras_zarolt)
        with pytest.raises(FolderMoveError):
            move_folder(forras, celszulo)
        assert forras.is_dir(), "a forrásnak érintetlenül kell maradnia"
        assert (forras / "alkonyvtar" / "b.jpg").exists()
        maradek = [p.name for p in celszulo.iterdir()]
        assert maradek == [], f"a célban maradt valami: {maradek}"


class TestAzUtolsoLepesBukasaBESZEDES:
    """A végleges névre átnevezés bukása az EGYETLEN nem visszagörgethető
    pont (a forrás már nincs) — ott a hibaüzenet mondja meg, hol az adat."""

    def test_a_hibauzenet_megnevezi_hol_van_a_tartalom(self, fa, monkeypatch) -> None:
        forras, celszulo = fa
        hivasok = {"n": 0}
        igazi = os.rename

        def masodikra_bukik(s, t):
            hivasok["n"] += 1
            if hivasok["n"] == 1:
                raise OSError(errno.EXDEV, "más fájlrendszer")
            raise OSError(errno.EACCES, "a végleges név nem elérhető")

        monkeypatch.setattr(_modul(), "_rename", masodikra_bukik)
        monkeypatch.setattr(_modul(), "_rmtree", lambda p: shutil.rmtree(p))
        with pytest.raises(FolderMoveError) as hiba:
            move_folder(forras, celszulo)
        uzenet = str(hiba.value)
        assert "nyaralas" in uzenet
        maradek = [p for p in celszulo.iterdir()]
        assert maradek, "az adatnak meg kell lennie valahol"
        assert maradek[0].name in uzenet, (
            "#2785: a nem visszagörgethető bukásnál a hibaüzenetnek meg kell "
            f"nevezni, hol van az áthelyezett tartalom — üzenet: {uzenet!r}"
        )
        assert (maradek[0] / "alkonyvtar" / "b.jpg").exists()
        assert igazi is os.rename, "a valódi os.rename nem cserélődhetett ki"
