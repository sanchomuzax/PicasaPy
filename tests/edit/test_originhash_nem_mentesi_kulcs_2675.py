"""#2675: az `originhash` NEM mentéskori kulcs — a mentés ne írja.

## Miért nem „a mért képletre cseréljük"

A jegy eredetileg azt kérte, hogy a `save_edited` a #791-ben megfejtett
képletet írja, és csak az volt nyitva, MELYIK fájl bájtjait hashelje. A
mérés azt mutatta, hogy a kérdés **rossz volt**: az eredeti Picasa a
mentéskor egyáltalán nem ír `originhash`-t.

**Korpusz-mérés** (a tulajdonos 859 valódi `.picasa.ini`-je,
`referencia/ini-korpusz`): 1787 `originhash=` sor áll a korpuszban, és
**egyetlen egy sem** olyan szakaszban, amelyben `redo=` is van
(`(originhash, redo) = (igen, igen)` → **0**; `(igen, nem)` → 1787;
`(nem, igen)` → 34). A `redo=` a mentés kimondott nyoma, tehát a két kulcs
kizárja egymást. A társkulcsok is a letöltési utat mutatják:
`IIDLIST_<felhasználó>_lh` 877, `backuphash` 760, `onlinechecksum` 380.

**Bináris oldal** (`docs/specs/picasa-tartalomkulcs.md`, 211. kör): a
kiírandó rekord `+0x90` mezőjét az `operator=` másolja, a rekord-vektor
`push_back`-jének (`FUN_007d53e0`) EGYETLEN hívója pedig a
`FUN_006f9cc0` = *Download from Google Photos*. A kulcs tehát a web-album
letöltés provenienciája, nem a szerkesztés könyvelése.

Ugyanez a fordulat történt a másolat-mentésnél (#1643): ott is egy
kitalált `redo=` + `originhash` könyvelést kellett visszavonni, amikor
mérés került a józan feltevés helyére.

## Amit ez a fájl őriz

1. a mentés NEM ír `originhash`-t;
2. a MEGLÉVŐ (letöltésből örökölt) `originhash` a mentést **túléli** —
   nem a miénk, nem nyúlunk hozzá;
3. a Visszaállítás sem törli — a szerkesztés-könyvelés a `filters=` és a
   `redo=`, az `originhash` idegen kulcs.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.edit import EditSession, revert, save_edited
from picasapy.ini import load_document

_INI_NAME = ".picasa.ini"


def _kep(szin: tuple[int, int, int], meret: int = 8) -> np.ndarray:
    kep = np.zeros((meret, meret, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


def _png(kep: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", kep)
    assert ok
    return buf.tobytes()


@pytest.fixture
def letoltott_kep(tmp_path: Path) -> Path:
    """Letöltésből származó kép: van `originhash`-e, és szerkesztés vár rá."""
    kep_ut = tmp_path / "IMG_0001.png"
    kep_ut.write_bytes(_png(_kep((10, 20, 30))))
    (tmp_path / _INI_NAME).write_text(
        "[IMG_0001.png]\n"
        "star=yes\n"
        "filters=enhance=1;\n"
        "originhash=033f1132c8741a2b3c4d5e6f708192a3\n"
        "backuphash=36003\n",
        encoding="utf-8",
    )
    return kep_ut


def _szakasz(kep_ut: Path):
    dokumentum = load_document(kep_ut.parent / _INI_NAME)
    szakasz = dokumentum.section(kep_ut.name)
    assert szakasz is not None
    return szakasz


class TestAMentesNemIrOriginhasht:
    def test_uj_originhash_nem_keletkezik(self, tmp_path: Path) -> None:
        kep_ut = tmp_path / "IMG_0002.png"
        kep_ut.write_bytes(_png(_kep((1, 2, 3))))
        (tmp_path / _INI_NAME).write_text(
            "[IMG_0002.png]\nfilters=enhance=1;\n", encoding="utf-8"
        )

        save_edited(kep_ut, _kep((9, 9, 9)), EditSession.from_value("enhance=1;"))

        szakasz = _szakasz(kep_ut)
        assert szakasz.get("redo") == "enhance=1;", "a mentés nyoma megvan"
        assert szakasz.get("originhash") is None, (
            "#2675: a mentés `originhash`-t írt — az eredeti Picasa ezt a "
            "kulcsot a web-album letöltéskor írja, mentéskor SOHA "
            "(korpusz: 1787 sorból 0 áll `redo=` mellett)"
        )

    def test_a_mentes_eredmenye_sem_hordoz_originhasht(self, tmp_path: Path) -> None:
        """A `SaveResult`-nak nincs `originhash` mezője (mint a #1643 után a
        `SaveCopyResult`-nak): nincs mit visszaadnia."""
        kep_ut = tmp_path / "IMG_0003.png"
        kep_ut.write_bytes(_png(_kep((4, 5, 6))))
        (tmp_path / _INI_NAME).write_text(
            "[IMG_0003.png]\nfilters=enhance=1;\n", encoding="utf-8"
        )

        eredmeny = save_edited(
            kep_ut, _kep((7, 7, 7)), EditSession.from_value("enhance=1;")
        )

        assert not hasattr(eredmeny, "originhash")


class TestAMeglevoOriginhashTulel:
    def test_a_mentes_meghagyja(self, letoltott_kep: Path) -> None:
        save_edited(
            letoltott_kep, _kep((9, 9, 9)), EditSession.from_value("enhance=1;")
        )

        szakasz = _szakasz(letoltott_kep)
        assert szakasz.get("originhash") == "033f1132c8741a2b3c4d5e6f708192a3", (
            "a letöltésből örökölt `originhash` nem a miénk — a mentés nem "
            "írhatja át és nem törölheti"
        )
        assert szakasz.get("backuphash") == "36003"

    def test_a_visszaallitas_sem_torli(self, letoltott_kep: Path) -> None:
        eredmeny = save_edited(
            letoltott_kep, _kep((9, 9, 9)), EditSession.from_value("enhance=1;")
        )
        assert eredmeny.original_backup_path.is_file()

        revert(letoltott_kep)

        szakasz = _szakasz(letoltott_kep)
        assert szakasz.get("redo") is None, "a szerkesztés könyvelése törlődik"
        assert szakasz.get("filters") is None
        assert szakasz.get("originhash") == "033f1132c8741a2b3c4d5e6f708192a3", (
            "#2675: a Visszaállítás törölte az `originhash`-t — az a letöltés "
            "provenienciája, nem a szerkesztés könyvelése"
        )
