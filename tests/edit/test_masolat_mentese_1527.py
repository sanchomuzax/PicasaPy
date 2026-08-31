"""#1527: a `Mentés másként` és a `Másolat mentése` MAGJA.

## A mért különbség (nem következtetés)

A jegy kimondja, hogy a két parancs fájlkezelési eltérését **nem mérte**.
Ez a kör lemérte, a bináris-indexből és a helyi diszasszemblálásból:

* A diszpécser (`0x005cb990`) **ugyanazt** a függvényt hívja mindkét
  parancsra — `0x005e6a20`, `call_count = 2` (bináris-index `xrefs`).
* A függvény egyetlen bájt-paraméterre ágazik el
  (`0x005e6b6a  cmp byte ptr [esp+0x14d4], bl` → `je 0x5e6bb1`):

  | ág | mit tesz |
  |---|---|
  | param **== 0** | felépíti a `JPEG Files`/`*.jpg` + `WebP Files`/`*.webp` szűrőlistát, **fájlválasztó párbeszédet nyit** (`0x0097f1d0`, benne `"SaveFile"`, `"ytApp::JPEGFilter"`), majd ellenőrzi, hogy a cél nem AZONOS a forrással (`IDS_CANT_SAVE_TO_SAME`), és hogy létezik-e már (`0x00992ed0`, `"Exists"`) |
  | param **!= 0** | `call 0x00993650` — a függvény egyetlen sztringje **`%s-%03lu`** —, majd **`jmp 0x5e6f24`**: átugorja a fájlválasztót ÉS az azonosság-ellenőrzést |

⇒ A **`Mentés másként…`** (felirata pontokra végződik: `Save &As...`)
fájlválasztót nyit. A **`Másolat mentése`** (`Save a Cop&y`, **nincs**
ellipszis) nem kérdez: a célnevet a `%s-%03lu` minta adja, tehát
`kep.jpg` → `kep-001.jpg`, ütközésnél `kep-002.jpg`, és így tovább.

Mindkét ág ugyanoda fut össze: a cél mappájának `.picasa.ini`-je
(`0x005e6f33`), majd a közös hibaüzenet (`CThumbUI::FileSaveCopy:err`).

## Ami DÖNTÉS, nem mérés

Hogy a cél `.picasa.ini`-jébe MELYIK kulcsok kerülnek, a sztringekből nem
derül ki (a `0x005aafd0` nem tartalmaz kulcsnevet). Döntés: a másolat a
`save_edited`-del azonos könyvelést kap (`redo=` + `originhash`), mert a
lánc a pixelekbe van égetve — `filters=` odaírása dupla-szerkesztés lenne
(#297). A FORRÁS fájl és annak ini-bejegyzése **érintetlen** marad: ez a
„másolat" jelentése.
"""

from __future__ import annotations

import configparser
from pathlib import Path

import numpy as np
import pytest

from picasapy.edit.save import SaveError
from picasapy.edit.save_copy import (
    FileNameCollisionError,
    next_copy_path,
    save_copy,
)
from picasapy.edit.session import EditSession


def _kep(ut: Path, szin=(10, 20, 30)) -> np.ndarray:
    import cv2

    tomb = np.zeros((8, 8, 3), dtype=np.uint8)
    tomb[:, :] = szin
    ut.write_bytes(cv2.imencode(".jpg", tomb)[1].tobytes())
    return tomb


class TestNextCopyPath:
    """A `%s-%03lu` minta — a MÉRT névadás."""

    def test_elso_masolat_001_toldalekot_kap(self, tmp_path):
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        assert next_copy_path(forras) == tmp_path / "kep-001.jpg"

    def test_utkozeskor_a_kovetkezo_sorszam(self, tmp_path):
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        (tmp_path / "kep-001.jpg").write_bytes(b"x")
        (tmp_path / "kep-002.jpg").write_bytes(b"x")
        assert next_copy_path(forras) == tmp_path / "kep-003.jpg"

    def test_a_kiterjesztes_megmarad(self, tmp_path):
        forras = tmp_path / "kep.png"
        forras.write_bytes(b"x")
        assert next_copy_path(forras).name == "kep-001.png"


class TestSaveCopy:
    """A másolat kiírása — és amit NEM tesz."""

    def test_a_masolat_letrejon_a_forras_valtozatlan(self, tmp_path):
        forras = tmp_path / "kep.jpg"
        eredeti_bajtok = _kep(forras)
        assert eredeti_bajtok is not None
        elotte = forras.read_bytes()

        rendered = np.full((8, 8, 3), 200, dtype=np.uint8)
        eredmeny = save_copy(
            forras, rendered, EditSession.from_value("crop64=1,0,0,ffff,ffff;")
        )

        assert eredmeny.target_path == tmp_path / "kep-001.jpg"
        assert eredmeny.target_path.exists()
        assert forras.read_bytes() == elotte, "a FORRÁS fájl megváltozott"

    def test_a_forras_ini_bejegyzese_erintetlen_marad(self, tmp_path):
        """#1643: a cél NEM kap szakaszt — a #1527 döntése megdőlt.

        Akkor a másolat `redo=` + `originhash` könyvelést kapott, józan
        alapértelmezésként. A tulajdonos referencia-mérése (valódi Picasa
        3.9) megcáfolta: a másolás semmit nem ír az ini-be. A forrás
        érintetlensége viszont VÁLTOZATLANUL követelmény, ezért ez a teszt
        megmarad — csak a cél-oldali állítás fordult meg.

        A teljes mérést a `test_masolat_nem_ir_inibe_1643.py` őrzi."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[kep.jpg]\nfilters=crop64=1,0,0,ffff,ffff;\n", encoding="utf-8")

        rendered = np.full((8, 8, 3), 200, dtype=np.uint8)
        save_copy(
            forras, rendered, EditSession.from_value("crop64=1,0,0,ffff,ffff;")
        )

        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.read(ini, encoding="utf-8")
        assert parser["kep.jpg"]["filters"] == "crop64=1,0,0,ffff,ffff;", (
            "a FORRÁS ini-bejegyzése megváltozott"
        )
        assert not parser.has_section("kep-001.jpg"), (
            "a cél szakaszt kapott az ini-ben — az eredeti nem ír "
            "semmit (#1643, mérve)"
        )

    def test_megadott_cel_eseten_ODA_ir(self, tmp_path):
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        cel = tmp_path / "sajat-nev.jpg"

        rendered = np.full((8, 8, 3), 200, dtype=np.uint8)
        eredmeny = save_copy(
            forras, rendered, EditSession.from_value(""), target_path=cel
        )

        assert eredmeny.target_path == cel
        assert cel.exists()

    def test_letezo_celt_SOHA_nem_ir_felul(self, tmp_path):
        """`CFileSaveThread:filesaveerr2` — „Már van ilyen nevű fájl."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        cel = tmp_path / "foglalt.jpg"
        cel.write_bytes(b"NE-IRD-FELUL")

        rendered = np.full((8, 8, 3), 200, dtype=np.uint8)
        with pytest.raises(FileNameCollisionError):
            save_copy(forras, rendered, EditSession.from_value(""), target_path=cel)

        assert cel.read_bytes() == b"NE-IRD-FELUL"

    def test_a_forrast_mint_celt_visszautasitja(self, tmp_path):
        """`IDS_CANT_SAVE_TO_SAME` — a cél nem lehet a forrás."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        rendered = np.full((8, 8, 3), 200, dtype=np.uint8)
        with pytest.raises(FileNameCollisionError):
            save_copy(forras, rendered, EditSession.from_value(""), target_path=forras)

    def test_ismeretlen_formatum_SaveError(self, tmp_path):
        """`CFileSaveThread:filesaveerr3` — fájlformázási hiba."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        rendered = np.full((8, 8, 3), 200, dtype=np.uint8)
        with pytest.raises(SaveError):
            save_copy(
                forras,
                rendered,
                EditSession.from_value(""),
                target_path=tmp_path / "kep-001.nincsilyen",
            )
