"""#3503 — az Ajándék CD lemezképe a képtálca elemeiből.

## Amit a spec kimért (`docs/specs/ajandek-cd-kimenet.md`)

- a lemezen a képek a honosított `Képek` mappában állnak
  (`il_BurnPanel::picfolder`, 4. szakasz);
- a méretválasztó négy fokozata: eredeti · 640 · 800 · 1600
  (`0x0066f658`–`0x0066f670`, 12.4);
- `option_jpegquality = 85`, `option_preservemovies = 1`,
  `option_createhtml = 0`, és az Ajándék-CD ágon nincs `option_inifile`
  (12.4 tábla) — a lemezre nem kerül `.picasa.ini`;
- a CD neve legfeljebb 16 karakter (`publish/namelimitext`).

A lemezképet — ahogy a #2074 próbái is — a FÜGGETLEN `7z` bontja ki; a
kötetnevet az ECMA-119 szerinti helyéről olvassuk (16. szektor, 40. bájt).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.burn.ajandek_cd import (
    CD_NEV_HOSSZ,
    MERETEK,
    ajandek_cd_lemezkep,
)
from picasapy.export import ExportItem
from support.jpeg_factory import make_jpeg

_HETZ = shutil.which("7z") or shutil.which("7za")
_SZEKTOR = 2048


def _kicsomagol(kep: Path, cel: Path) -> None:
    assert _HETZ, "nincs `7z` a gépen — a lemezkép ellenőrzése így nem mérés"
    cel.mkdir(parents=True, exist_ok=True)
    kesz = subprocess.run(
        [_HETZ, "x", "-y", f"-o{cel}", str(kep)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120,
    )
    assert kesz.returncode == 0, kesz.stdout + kesz.stderr


def _kep(ut: Path):
    """A `cv2.imread` Windowson ékezetes útra `None`-t ad — bájtból dekódolunk."""
    return cv2.imdecode(np.frombuffer(ut.read_bytes(), np.uint8), cv2.IMREAD_COLOR)


def _joliet_kotetnev(kep: Path) -> str:
    """A Joliet-kötetleíró (17. szektor) kötetneve, UTF-16BE."""
    with kep.open("rb") as f:
        f.seek(17 * _SZEKTOR + 40)
        return f.read(32).decode("utf-16-be").rstrip("\x00 ")


@pytest.fixture
def talca(tmp_path: Path) -> list[ExportItem]:
    forras = tmp_path / "forras"
    forras.mkdir()
    make_jpeg(forras / "nyár.jpg", size=(2000, 1500))
    make_jpeg(forras / "tél.jpg", size=(300, 200))
    (forras / "film.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"x" * 500)
    return [
        ExportItem(source=forras / "nyár.jpg", caption="Balaton"),
        ExportItem(source=forras / "tél.jpg"),
        ExportItem(source=forras / "film.mp4"),
    ]


class TestAMertAllandok:
    def test_negy_meretfokozat(self):
        assert MERETEK == (0, 640, 800, 1600)

    def test_a_cd_neve_legfeljebb_16(self):
        assert CD_NEV_HOSSZ == 16


class TestALemezTartalma:
    def test_a_kepek_mappaba_kerul_minden_elem(self, tmp_path, talca):
        cel = tmp_path / "ki" / "ajandek.iso"

        eredmeny = ajandek_cd_lemezkep(
            talca, cel, meret_index=0, cd_nev="Nyaralás", kepek_mappa="Képek"
        )

        assert eredmeny.lemezkep == cel
        assert eredmeny.darab == 3
        kibontva = tmp_path / "bontas"
        _kicsomagol(cel, kibontva)
        nevek = sorted(p.name for p in (kibontva / "Képek").iterdir())
        assert nevek == ["film.mp4", "nyár.jpg", "tél.jpg"]

    def test_nincs_picasa_ini_a_lemezen(self, tmp_path, talca):
        """Az Ajándék-CD ágon nincs `option_inifile` — a felirat attól még
        nem kerülhet ini-be a lemezen."""
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=0, cd_nev="X", kepek_mappa="Képek"
        )

        kibontva = tmp_path / "bontas"
        _kicsomagol(cel, kibontva)
        assert not list(kibontva.rglob(".picasa.ini"))

    def test_eredeti_meretnel_a_jpeg_bajthu(self, tmp_path, talca):
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=0, cd_nev="X", kepek_mappa="Képek"
        )

        kibontva = tmp_path / "bontas"
        _kicsomagol(cel, kibontva)
        assert (kibontva / "Képek" / "nyár.jpg").read_bytes() == (
            talca[0].source.read_bytes()
        )

    @pytest.mark.parametrize("index,oldal", [(1, 640), (2, 800), (3, 1600)])
    def test_a_valasztott_meret_a_hosszabb_oldal_korlatja(
        self, tmp_path, talca, index, oldal
    ):
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=index, cd_nev="X", kepek_mappa="Képek"
        )

        kibontva = tmp_path / "bontas"
        _kicsomagol(cel, kibontva)
        nagy = _kep(kibontva / "Képek" / "nyár.jpg")
        kicsi = _kep(kibontva / "Képek" / "tél.jpg")
        assert max(nagy.shape[:2]) == oldal
        # a korlátnál kisebb kép nem nő
        assert kicsi.shape[:2] == (200, 300)

    def test_a_film_bajthuen_marad(self, tmp_path, talca):
        """`option_preservemovies = 1` — a méretválasztás a filmet nem
        érinti."""
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=1, cd_nev="X", kepek_mappa="Képek"
        )

        kibontva = tmp_path / "bontas"
        _kicsomagol(cel, kibontva)
        assert (kibontva / "Képek" / "film.mp4").read_bytes() == (
            talca[2].source.read_bytes()
        )


class TestAKotetnev:
    def test_a_cd_neve_a_kotetnev(self, tmp_path, talca):
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=0, cd_nev="Nyaralás 2026", kepek_mappa="Képek"
        )

        assert _joliet_kotetnev(cel) == "Nyaralás 2026"

    def test_a_16_karakter_folott_levagja(self, tmp_path, talca):
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=0, cd_nev="A" * 20, kepek_mappa="Képek"
        )

        assert _joliet_kotetnev(cel) == "A" * 16

    def test_ures_nevnel_a_fajlnev(self, tmp_path, talca):
        cel = tmp_path / "Karácsony.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=0, cd_nev="  ", kepek_mappa="Képek"
        )

        assert _joliet_kotetnev(cel) == "Karácsony"


class TestHibak:
    def test_ures_talcabol_nincs_lemezkep(self, tmp_path):
        cel = tmp_path / "ajandek.iso"

        eredmeny = ajandek_cd_lemezkep(
            [], cel, meret_index=0, cd_nev="X", kepek_mappa="Képek"
        )

        assert eredmeny.lemezkep is None
        assert not cel.exists()

    def test_a_hibas_elem_nem_allitja_le_a_tobbit(self, tmp_path, talca):
        cel = tmp_path / "ajandek.iso"
        hianyzo = ExportItem(source=tmp_path / "nincs.jpg")

        eredmeny = ajandek_cd_lemezkep(
            [*talca, hianyzo], cel, meret_index=1, cd_nev="X",
            kepek_mappa="Képek",
        )

        assert eredmeny.darab == 3
        assert eredmeny.hibas == (hianyzo.source,)

    def test_ervenytelen_meret_index(self, tmp_path, talca):
        with pytest.raises(ValueError):
            ajandek_cd_lemezkep(
                talca, tmp_path / "a.iso", meret_index=4, cd_nev="X",
                kepek_mappa="Képek",
            )

    def test_nem_marad_munkamappa(self, tmp_path, talca):
        """A köztes (átméretezett) fájlok a lemezkép mellett készülnek, és a
        végén eltűnnek — a 8 GB-os tmpfs-t nem tölthetik."""
        cel_mappa = tmp_path / "ki"
        cel = cel_mappa / "ajandek.iso"

        ajandek_cd_lemezkep(
            talca, cel, meret_index=1, cd_nev="X", kepek_mappa="Képek"
        )

        assert sorted(p.name for p in cel_mappa.iterdir()) == ["ajandek.iso"]


def _elsodleges_nevek(kep: Path, konyvtar: str | None = None) -> list[str]:
    """Az ELSŐDLEGES (ISO 9660) fa neveit olvassa ki — a `7z` a Joliet-fát
    mutatja, a régi olvasók (tévé, DVD-lejátszó) viszont ezt látják.

    ECMA-119: a PVD a 16. szektorban, a gyökér-rekord a 156. bájton; egy
    rekord: hossz, …, kiterjedés (2. bájt, LE), méret (10. bájt, LE),
    jelzők (25.), névhossz (32.), név (33.-tól)."""
    adat = kep.read_bytes()

    def rekordok(szektor: int, meret: int):
        kezdet = szektor * _SZEKTOR
        poz = kezdet
        while poz < kezdet + meret:
            hossz = adat[poz]
            if hossz == 0:  # a szektor maradéka üres
                poz = (poz // _SZEKTOR + 1) * _SZEKTOR
                continue
            nevhossz = adat[poz + 32]
            nev = adat[poz + 33: poz + 33 + nevhossz]
            yield (
                nev,
                int.from_bytes(adat[poz + 2: poz + 6], "little"),
                int.from_bytes(adat[poz + 10: poz + 14], "little"),
                bool(adat[poz + 25] & 2),
            )
            poz += hossz

    gyoker = 16 * _SZEKTOR + 156
    sz = int.from_bytes(adat[gyoker + 2: gyoker + 6], "little")
    m = int.from_bytes(adat[gyoker + 10: gyoker + 14], "little")
    if konyvtar is not None:
        for nev, alsz, alm, kvt in rekordok(sz, m):
            if kvt and nev.decode("ascii", "replace") == konyvtar:
                sz, m = alsz, alm
                break
        else:
            raise AssertionError(f"nincs {konyvtar} könyvtár az elsődleges fában")
    return [
        nev.decode("ascii")
        for nev, *_ in rekordok(sz, m)
        if nev not in (b"\x00", b"\x01")
    ]


class TestElsodlegesFa:
    """Az átnézés lelete: az ISO 9660 8.3-as nevek ÜTKÖZHETNEK. Két azonos
    nevű kép két mappából — az exportáló `IMG_0001-1.jpg`-t ad a másodiknak
    —, és mindkettő `IMG_0001.JPG;1` lett volna."""

    def test_az_utkozo_83_nevek_egyediek(self, tmp_path):
        forras = tmp_path / "forras"
        (forras / "a").mkdir(parents=True)
        (forras / "b").mkdir(parents=True)
        make_jpeg(forras / "a" / "IMG_0001.jpg")
        make_jpeg(forras / "b" / "IMG_0001.jpg")
        make_jpeg(forras / "a" / "DSC_12345.jpg")
        make_jpeg(forras / "a" / "DSC_12346.jpg")
        cel = tmp_path / "ajandek.iso"

        ajandek_cd_lemezkep(
            [ExportItem(source=p) for p in (
                forras / "a" / "IMG_0001.jpg", forras / "b" / "IMG_0001.jpg",
                forras / "a" / "DSC_12345.jpg", forras / "a" / "DSC_12346.jpg",
            )],
            cel, meret_index=0, cd_nev="X", kepek_mappa="Pictures",
        )

        nevek = _elsodleges_nevek(cel, "PICTURES")
        assert len(nevek) == 4
        assert len(set(nevek)) == 4, nevek
        assert nevek == sorted(nevek), "az elsődleges fa rekordjai rendezettek"
        # a Joliet-fa (a valódi nevek) ettől érintetlen
        kibontva = tmp_path / "bontas"
        _kicsomagol(cel, kibontva)
        assert sorted(p.name for p in (kibontva / "Pictures").iterdir()) == [
            "DSC_12345.jpg", "DSC_12346.jpg", "IMG_0001-1.jpg", "IMG_0001.jpg",
        ]


class TestAtomikusIras:
    def test_hibanal_a_regi_lemezkep_megmarad(self, tmp_path, talca, monkeypatch):
        """Az átnézés lelete: a kép írás közbeni hibája (tele lemez) nem
        hagyhat csonka `.iso`-t, és nem teheti tönkre a korábbit."""
        import picasapy.burn.ajandek_cd as modul

        cel = tmp_path / "ajandek.iso"
        cel.write_bytes(b"REGI")

        def _elszall(tetelek, ut, **_kw):
            Path(ut).write_bytes(b"csonka")
            raise OSError("No space left on device")

        monkeypatch.setattr(modul, "iso_kiirasa", _elszall)

        with pytest.raises(OSError):
            ajandek_cd_lemezkep(
                talca, cel, meret_index=0, cd_nev="X", kepek_mappa="Képek"
            )

        assert cel.read_bytes() == b"REGI"
        assert sorted(p.name for p in tmp_path.iterdir()) == [
            "ajandek.iso", "forras",
        ]


class TestTulNagyFajl:
    def test_a_4_gib_os_fajlt_kimondja(self, tmp_path):
        """ISO 9660 1. szinten egy fájl legfeljebb 4 GiB − 1 bájt: a 32 bites
        méretmezőbe nem fér több. A nagyobbat nem némán (és nem
        `OverflowError`-ral), hanem `ValueError`-ral kell elutasítani.

        A fájl RITKA (sparse): a `truncate` lemezhelyet nem foglal."""
        from picasapy.burn import iso

        nagy = tmp_path / "nagy.bin"
        with nagy.open("wb") as f:
            f.truncate(1 << 32)

        with pytest.raises(ValueError):
            iso.iso_kiirasa([("nagy.bin", nagy)], tmp_path / "ki.iso")
        assert not (tmp_path / "ki.iso").exists()
