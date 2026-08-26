"""#1527: a mentés-hibák besorolása a három hivatalos ágra.

A `save_error_kind` tiszta függvény — az ága dönti el, MELYIK hivatalos
mondatot látja a felhasználó. Egy elrontott sorrend itt nem hibaüzenetet
ad, hanem ROSSZ hibaüzenetet: a „már van ilyen nevű fájl" helyett
„lemezhiba", amiből a felhasználó rossz következtetést von le.
"""

from __future__ import annotations

import errno

import pytest

from picasapy.app.save_error_kind import (
    KIND_COLLISION,
    KIND_DISK,
    KIND_FORMAT,
    KIND_SAME,
    save_error_code,
    save_error_kind,
)
from picasapy.edit.save import SaveError
from picasapy.edit.save_copy import FileNameCollisionError
from picasapy.ini import IniConflictError, IniSaveError


class TestAgak:
    def test_nevutkozes(self):
        hiba = FileNameCollisionError("Már van ilyen nevű fájl: kep-001.jpg")
        assert save_error_kind(hiba) == KIND_COLLISION

    def test_a_cel_azonos_a_forrassal_MASIK_ag(self):
        """Két külön hivatalos mondat, ugyanaz a kivétel-osztály."""
        hiba = FileNameCollisionError("A cél azonos a forrással: kep.jpg")
        assert save_error_kind(hiba) == KIND_SAME

    def test_a_beepitett_FileExistsError_is_utkozes(self):
        assert save_error_kind(FileExistsError("van már")) == KIND_COLLISION

    def test_formatumhiba(self):
        assert save_error_kind(SaveError("nem kódolható")) == KIND_FORMAT

    def test_a_ValueError_is_formatumhiba(self):
        assert save_error_kind(ValueError("nem dekódolható kép")) == KIND_FORMAT

    @pytest.mark.parametrize(
        "hiba",
        [
            OSError(errno.ENOSPC, "No space left on device"),
            PermissionError(errno.EACCES, "Permission denied"),
            IniSaveError("az ini nem írható"),
            IniConflictError("párhuzamos Picasa írta"),
        ],
    )
    def test_lemezhiba(self, hiba):
        assert save_error_kind(hiba) == KIND_DISK

    def test_az_utkozes_ELOBB_dol_el_mint_a_formatum(self):
        """A `FileNameCollisionError` a `SaveError` LESZÁRMAZOTTJA — ha a
        sorrend megfordul, a felhasználó „fájlformázási hibát" olvas egy
        névütközésre."""
        assert issubclass(FileNameCollisionError, SaveError)
        assert save_error_kind(FileNameCollisionError("x")) != KIND_FORMAT


class TestHibakod:
    def test_az_OSError_errno_ja_megy_at(self):
        assert save_error_code(OSError(errno.ENOSPC, "tele")) == errno.ENOSPC

    def test_errno_nelkuli_hibanal_nulla(self):
        assert save_error_code(SaveError("nincs kódja")) == 0

    def test_az_ini_hibanal_sem_TALALGATUNK(self):
        assert save_error_code(IniSaveError("x")) == 0
