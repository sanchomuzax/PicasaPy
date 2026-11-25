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
    KIND_COPY_DISK,
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

    @pytest.mark.parametrize(
        "hiba",
        [
            OSError(errno.ENOSPC, "No space left on device"),
            PermissionError(errno.EACCES, "Permission denied"),
            IniSaveError("az ini nem irhato"),
            IniConflictError("parhuzamos Picasa irta"),
        ],
    )
    def test_masolat_mentes_lemezhiba_copy_disk_agat_ad(self, hiba):
        assert save_error_kind(hiba, is_copy=True) == KIND_COPY_DISK
        assert save_error_kind(hiba, is_copy=False) == KIND_DISK

    def test_az_utkozes_ELOBB_dol_el_mint_a_formatum(self):
        """A `FileNameCollisionError` a `SaveError` LESZÁRMAZOTTJA — ha a
        sorrend megfordul, a felhasználó „fájlformázási hibát" olvas egy
        névütközésre."""
        assert issubclass(FileNameCollisionError, SaveError)
        assert save_error_kind(FileNameCollisionError("x")) != KIND_FORMAT


def _winhiba(winerror: int, *, errno_: int | None = None) -> OSError:
    """Windows-hibát utánzó `OSError`: Linuxon a `winerror` nem állítható a
    konstruktorral, ezért attribútumként kapja (ahogy Windowson olvassuk)."""
    hiba = OSError(errno_, "szimulált Windows-hiba") if errno_ is not None else OSError("szimulált")
    hiba.winerror = winerror  # type: ignore[attr-defined]
    return hiba


class TestHibakod:
    """#7449: a hibaablak `hiba(%d)` száma az eredeti BELSŐ státusza, nem az
    `errno` (a `0x0099cd30` leképezése; `job-957` írásvédett cél: `error(11)`)."""

    @pytest.mark.parametrize(
        "hiba",
        [
            PermissionError(errno.EACCES, "Permission denied"),
            PermissionError(errno.EPERM, "Operation not permitted"),
            OSError(errno.EROFS, "Read-only file system"),
            OSError(errno.EACCES, "Permission denied"),
        ],
        ids=["EACCES", "EPERM", "EROFS", "OSError-EACCES"],
    )
    def test_az_iras_elleni_vedelem_11(self, hiba):
        assert save_error_code(hiba) == 11

    @pytest.mark.parametrize(
        "hiba",
        [
            FileNotFoundError(errno.ENOENT, "No such file or directory"),
            OSError(errno.ENOENT, "No such file or directory"),
        ],
        ids=["FileNotFoundError", "OSError-ENOENT"],
    )
    def test_a_hianyzo_ut_10(self, hiba):
        assert save_error_code(hiba) == 10

    @pytest.mark.parametrize("winerror", [5, 32])
    def test_windows_hozzaferes_es_megosztas_11(self, winerror):
        assert save_error_code(_winhiba(winerror)) == 11
        assert save_error_code(_winhiba(winerror, errno_=errno.EACCES)) == 11

    @pytest.mark.parametrize("winerror", [2, 3])
    def test_windows_hianyzo_fajl_vagy_ut_10(self, winerror):
        assert save_error_code(_winhiba(winerror)) == 10
        assert save_error_code(_winhiba(winerror, errno_=errno.ENOENT)) == 10

    def test_a_HANDLE_DISK_FULL_12(self):
        """#7462: Windows `ERROR_HANDLE_DISK_FULL` (39) a bináris mindkét
        leképezőjében (`0x0099cd30`, `0x00991330`) 12."""
        assert save_error_code(_winhiba(39)) == 12
        assert save_error_code(_winhiba(39, errno_=errno.ENOSPC)) == 12
        assert save_error_code(_winhiba(39, errno_=errno.EINVAL)) == 12

    @pytest.mark.parametrize(
        "hiba",
        [
            OSError(errno.ENOSPC, "tele"),
            _winhiba(112),
            _winhiba(112, errno_=errno.ENOSPC),
        ],
        ids=["ENOSPC", "winerror-112", "winerror-112-ENOSPC"],
    )
    def test_minden_mas_tele_lemez_2(self, hiba):
        """#7462: az írási út leképezője (`0x0099cd30`) a 112-t az alapágra, 2-re
        viszi; az `errno` (28) nem jelenhet meg a hibaablakban."""
        assert save_error_code(hiba) == 2

    @pytest.mark.parametrize(
        "hiba",
        [
            OSError(errno.EIO, "Input/output error"),
            OSError(errno.EMFILE, "Too many open files"),
            OSError("errno nélküli"),
            _winhiba(80),
            _winhiba(1117, errno_=errno.EIO),
        ],
        ids=["EIO", "EMFILE", "errno-nelkuli", "winerror-80", "winerror-1117"],
    )
    def test_minden_mas_OSError_2_az_eredeti_alapaga(self, hiba):
        assert save_error_code(hiba) == 2

    def test_errno_nelkuli_hibanal_nulla(self):
        assert save_error_code(SaveError("nincs kódja")) == 0

    def test_az_ini_hibanal_sem_TALALGATUNK(self):
        assert save_error_code(IniSaveError("x")) == 0
        assert save_error_code(IniConflictError("x")) == 0

    def test_a_nem_OSError_errno_attributuma_nem_szamit(self):
        """Csak a fájlrendszer-hibának van belső státusza; más kivétel 0."""
        hiba = SaveError("nincs kódja")
        hiba.errno = errno.EACCES  # type: ignore[attr-defined]
        assert save_error_code(hiba) == 0

    def test_a_besorolas_nem_valtozott(self):
        """A hibakód leképezése nem érinti az ágat: az írásvédett cél továbbra
        is lemezhiba, a névütközés és a formátumhiba külön ág marad."""
        assert save_error_kind(PermissionError(errno.EACCES, "x")) == KIND_DISK
        assert save_error_kind(FileNotFoundError(errno.ENOENT, "x")) == KIND_DISK
        assert save_error_kind(FileNameCollisionError("x")) == KIND_COLLISION
        assert save_error_kind(SaveError("x")) == KIND_FORMAT
