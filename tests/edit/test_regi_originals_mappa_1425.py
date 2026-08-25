"""#1425 — a „Vissza az eredetihez" ismerje a RÉGI `Originals` mappanevet is.

A Picasa a szerkesztés előtti eredetit két, időben élesen elváló néven
tárolta (`docs/specs/picasa-ini-format.md`, „Az eredeti képek mentése — KÉT
elnevezés, verzióváltással”):

| mappanév | darab a korpuszban | évek |
|---|---:|---|
| `Originals` (látható) | 127 | 2005–2009 |
| `.picasaoriginals` (rejtett) | 54 | 2009–2016 |

A #371 kutatása kizárta, hogy a retus/vörösszem régió-adata bárhol
tárolódna: a javítás a mentett JPEG-be van beleégetve, tehát a
visszaállítás EGYETLEN útja az eredeti fájl megőrzött másolata. Ha a régi
nevet nem ismerjük, a tulajdonos 127 mappányi eredetijéhez nem tudunk
visszatérni.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.edit import (
    LEGACY_ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAME,
    EditSession,
    SaveError,
    find_original_backup,
    revert,
    save_edited,
)

_INI_NAME = ".picasa.ini"


def _solid_image(color: tuple[int, int, int], size: int = 8) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[:, :] = color
    return image


def _encode_png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


@pytest.fixture
def photo(tmp_path):
    """Egy „már szerkesztett” kép + a hozzá tartozó ini (mentés nélkül)."""
    image_path = tmp_path / "IMG_0001.png"
    image_path.write_bytes(_encode_png(_solid_image((99, 99, 99))))
    (tmp_path / _INI_NAME).write_text(
        "[IMG_0001.png]\nstar=yes\nfilters=enhance=1;\n", encoding="utf-8"
    )
    return image_path


def _place_backup(image_path: Path, dir_name: str, color) -> bytes:
    """Egy megőrzött eredeti elhelyezése a megadott nevű mappában."""
    directory = image_path.parent / dir_name
    directory.mkdir(exist_ok=True)
    payload = _encode_png(_solid_image(color))
    (directory / image_path.name).write_bytes(payload)
    return payload


class TestRegiMappanevbolIsVisszaallit:
    def test_a_regi_Originals_mappabol_visszaall_az_eredeti(self, photo):
        eredeti = _place_backup(photo, LEGACY_ORIGINALS_DIR_NAME, (10, 20, 30))

        revert(photo)

        assert photo.read_bytes() == eredeti

    def test_megmondja_melyik_mappabol_dolgozott(self, photo):
        _place_backup(photo, LEGACY_ORIGINALS_DIR_NAME, (10, 20, 30))

        eredmeny = revert(photo)

        assert eredmeny.restored_from == (
            photo.parent / LEGACY_ORIGINALS_DIR_NAME / photo.name
        )

    def test_az_uj_mappanev_valtozatlanul_mukodik(self, photo):
        eredeti = _place_backup(photo, ORIGINALS_DIR_NAME, (1, 2, 3))

        eredmeny = revert(photo)

        assert photo.read_bytes() == eredeti
        assert eredmeny.restored_from == (
            photo.parent / ORIGINALS_DIR_NAME / photo.name
        )


class TestUtkozesKimondottSzabaly:
    """Ha MINDKETTŐ létezik, a régi, `Originals` az elsőbbségi (SAJÁT
    FUNKCIÓ-döntés, ld. `edit/save.py` „Két mappanév” szakasza): az a példány
    időben korábbi, tehát közelebb áll az érintetlen eredetihez."""

    def test_a_regi_Originals_nyer(self, photo):
        regi = _place_backup(photo, LEGACY_ORIGINALS_DIR_NAME, (10, 20, 30))
        uj = _place_backup(photo, ORIGINALS_DIR_NAME, (40, 50, 60))

        eredmeny = revert(photo)

        assert photo.read_bytes() == regi
        assert photo.read_bytes() != uj
        assert eredmeny.restored_from.parent.name == LEGACY_ORIGINALS_DIR_NAME


class TestNemaElutasitasTilos:
    """Ha egyik mappa sincs, a felhasználó ÉRTHETŐ üzenetet kap — ez a
    projekt visszatérő hibaosztálya (#1003, #1207, #1213)."""

    def test_a_hibauzenet_mindket_mappanevet_megnevezi(self, photo):
        with pytest.raises(SaveError) as hiba:
            revert(photo)

        uzenet = str(hiba.value)
        assert ORIGINALS_DIR_NAME in uzenet
        assert LEGACY_ORIGINALS_DIR_NAME in uzenet
        assert photo.name in uzenet

    def test_a_hibauzenet_nem_szivarogtat_fejlesztoi_zsargont(self, photo):
        with pytest.raises(SaveError) as hiba:
            revert(photo)

        assert "save_edited" not in str(hiba.value)


class TestMentesNemKeszitMasodikSzentEredetit:
    """A modul alapszabálya: „az ELSŐ eredeti a szent példány”. Ez a
    mappanévtől független — ha a régi `Originals`-ban már ott az érintetlen
    eredeti, a mentés NEM tehet mellé egy másodikat a már szerkesztett
    bájtokból, mert azzal a valódi eredeti elérhetetlenné válna."""

    def test_a_regi_mappaban_talalt_eredetit_nem_dublikalja(self, photo):
        eredeti = _place_backup(photo, LEGACY_ORIGINALS_DIR_NAME, (10, 20, 30))

        eredmeny = save_edited(
            photo, _solid_image((7, 7, 7)), EditSession.from_value("enhance=1;")
        )

        assert eredmeny.backup_created_now is False
        assert eredmeny.original_backup_path == (
            photo.parent / LEGACY_ORIGINALS_DIR_NAME / photo.name
        )
        assert not (photo.parent / ORIGINALS_DIR_NAME / photo.name).exists()
        # …és a visszaállítás továbbra is az IGAZI eredetit hozza vissza
        revert(photo)
        assert photo.read_bytes() == eredeti


class TestFindOriginalBackup:
    def test_nincs_egy_mappa_sem(self, photo):
        assert find_original_backup(photo) is None

    def test_ures_mappa_nem_talalat(self, photo):
        (photo.parent / LEGACY_ORIGINALS_DIR_NAME).mkdir()

        assert find_original_backup(photo) is None

    def test_a_talalt_utvonalat_adja_vissza(self, photo):
        _place_backup(photo, LEGACY_ORIGINALS_DIR_NAME, (10, 20, 30))

        assert find_original_backup(photo) == (
            photo.parent / LEGACY_ORIGINALS_DIR_NAME / photo.name
        )
