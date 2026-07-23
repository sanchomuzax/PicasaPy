"""Nem-destruktív mentés / Visszaállítás (#21) — save_edited/revert tesztjei.

Specifikáció: docs/specs/picasa-ini-format.md (`redo=`, `originhash`,
`backuphash`, írási szabályok) + docs/specs/ux-principles.md (3. alapelv).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.edit import (
    ORIGINALS_DIR_NAME,
    EditSession,
    RevertResult,
    SaveError,
    SaveResult,
    revert,
    save_edited,
)
from picasapy.ini import load_document

_INI_NAME = ".picasa.ini"


def _solid_image(color: tuple[int, int, int], size: int = 8) -> np.ndarray:
    """Kis, egyszínű BGR képmátrix (determinisztikus, veszteségmentes PNG-hez)."""
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[:, :] = color
    return image


def _encode_png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def _write_ini(tmp_path: Path, body: str) -> Path:
    ini_path = tmp_path / _INI_NAME
    ini_path.write_text(body, encoding="utf-8")
    return ini_path


@pytest.fixture
def photo(tmp_path):
    """Egy szintetikus "eredeti" kép a tmp mappában + hozzá tartozó ini."""
    image_path = tmp_path / "IMG_0001.png"
    original_bytes = _encode_png(_solid_image((10, 20, 30)))
    image_path.write_bytes(original_bytes)
    _write_ini(
        tmp_path,
        "[IMG_0001.png]\n"
        "star=yes\n"
        "filters=enhance=1;\n"
        "backuphash=36003\n"
        "unknownfield=valami-ismeretlen\n",
    )
    return image_path, original_bytes


class TestSaveEditedFirstTime:
    """(a) mentés → eredeti a .picasaoriginals-ban, renderelt a helyén,
    a redo=/originhash a várt módon frissül."""

    def test_original_backed_up(self, photo):
        image_path, original_bytes = photo
        rendered = _solid_image((99, 88, 77))
        session = EditSession.from_value("enhance=1;")

        result = save_edited(image_path, rendered, session)

        backup_path = image_path.parent / ORIGINALS_DIR_NAME / image_path.name
        assert backup_path.exists()
        assert backup_path.read_bytes() == original_bytes
        assert result.backup_created_now is True
        assert result.original_backup_path == backup_path

    def test_rendered_image_at_original_location(self, photo):
        image_path, _original_bytes = photo
        rendered = _solid_image((99, 88, 77))
        session = EditSession.from_value("enhance=1;")

        save_edited(image_path, rendered, session)

        decoded = cv2.imdecode(
            np.frombuffer(image_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR
        )
        assert decoded is not None
        assert tuple(int(c) for c in decoded[0, 0]) == (99, 88, 77)

    def test_ini_redo_and_originhash_written(self, photo):
        image_path, _original_bytes = photo
        rendered = _solid_image((1, 2, 3))
        session = EditSession.from_value("enhance=1;crop64=1,3f845bcb59418507;")

        result = save_edited(image_path, rendered, session)

        document = load_document(image_path.parent / _INI_NAME)
        section = document.section("IMG_0001.png")
        assert section is not None
        expected_redo = "enhance=1;crop64=1,3f845bcb59418507;"
        assert section.get("redo") == expected_redo
        assert result.redo_value == expected_redo
        expected_hash = hashlib.sha256(expected_redo.encode("utf-8")).hexdigest()
        assert section.get("originhash") == expected_hash
        assert result.originhash == expected_hash
        # filters= törlődik: a lánc már be van égetve a pixelekbe.
        assert section.get("filters") is None

    def test_returns_save_result(self, photo):
        image_path, _original_bytes = photo
        result = save_edited(
            image_path, _solid_image((5, 5, 5)), EditSession.from_value("enhance=1;")
        )
        assert isinstance(result, SaveResult)


class TestSaveEditedSecondTime:
    """(b) MÁSODIK mentés → a .picasaoriginals-beli eredeti NEM íródik felül."""

    def test_second_save_preserves_first_original(self, photo):
        image_path, original_bytes = photo
        backup_path = image_path.parent / ORIGINALS_DIR_NAME / image_path.name

        first = save_edited(
            image_path,
            _solid_image((11, 22, 33)),
            EditSession.from_value("enhance=1;"),
        )
        assert first.backup_created_now is True
        assert backup_path.read_bytes() == original_bytes

        second = save_edited(
            image_path,
            _solid_image((44, 55, 66)),
            EditSession.from_value("enhance=1;autolight=1;"),
        )
        assert second.backup_created_now is False
        # Az eredeti MÉG MINDIG az első (legelső) eredeti bájtjai.
        assert backup_path.read_bytes() == original_bytes

        # A látott fájl viszont a MÁSODIK renderelt tartalmat mutatja.
        decoded = cv2.imdecode(
            np.frombuffer(image_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR
        )
        assert tuple(int(c) for c in decoded[0, 0]) == (44, 55, 66)

    def test_second_save_updates_redo_to_new_chain(self, photo):
        image_path, _original_bytes = photo
        save_edited(
            image_path, _solid_image((1, 1, 1)), EditSession.from_value("enhance=1;")
        )
        second = save_edited(
            image_path,
            _solid_image((2, 2, 2)),
            EditSession.from_value("enhance=1;autolight=1;"),
        )
        document = load_document(image_path.parent / _INI_NAME)
        section = document.section("IMG_0001.png")
        assert section.get("redo") == "enhance=1;autolight=1;"
        assert second.redo_value == "enhance=1;autolight=1;"


class TestRevert:
    """(c) revert → az eredeti bájtjai visszaálltak, az ini-mezők törölve."""

    def test_revert_restores_original_bytes(self, photo):
        image_path, original_bytes = photo
        save_edited(
            image_path, _solid_image((9, 9, 9)), EditSession.from_value("enhance=1;")
        )
        assert image_path.read_bytes() != original_bytes

        result = revert(image_path)

        assert image_path.read_bytes() == original_bytes
        assert isinstance(result, RevertResult)
        assert result.restored_from == image_path.parent / ORIGINALS_DIR_NAME / image_path.name

    def test_revert_clears_edit_bookkeeping_keys(self, photo):
        image_path, _original_bytes = photo
        save_edited(
            image_path, _solid_image((9, 9, 9)), EditSession.from_value("enhance=1;")
        )
        revert(image_path)

        document = load_document(image_path.parent / _INI_NAME)
        section = document.section("IMG_0001.png")
        assert section is not None
        assert section.get("filters") is None
        assert section.get("redo") is None
        assert section.get("originhash") is None
        # A szerkesztéshez nem tartozó mezők (star, backuphash, ismeretlen)
        # érintetlenek maradnak.
        assert section.get("star") == "yes"
        assert section.get("backuphash") == "36003"
        assert section.get("unknownfield") == "valami-ismeretlen"

    def test_revert_without_prior_save_raises(self, photo):
        image_path, _original_bytes = photo
        with pytest.raises(SaveError):
            revert(image_path)

    def test_revert_after_second_save_restores_the_very_first_original(self, photo):
        """A revert az ELSŐ eredetit adja vissza, akárhányszor mentettünk is."""
        image_path, original_bytes = photo
        save_edited(
            image_path, _solid_image((1, 1, 1)), EditSession.from_value("enhance=1;")
        )
        save_edited(
            image_path,
            _solid_image((2, 2, 2)),
            EditSession.from_value("enhance=1;autolight=1;"),
        )
        revert(image_path)
        assert image_path.read_bytes() == original_bytes


class TestRoundTrip:
    """(d) a .picasa.ini ismeretlen mezői bitre megmaradnak mentés után."""

    def test_unknown_and_unrelated_keys_survive_save(self, photo):
        image_path, _original_bytes = photo
        save_edited(
            image_path, _solid_image((7, 7, 7)), EditSession.from_value("enhance=1;")
        )
        document = load_document(image_path.parent / _INI_NAME)
        section = document.section("IMG_0001.png")
        assert section.get("star") == "yes"
        assert section.get("backuphash") == "36003"
        assert section.get("unknownfield") == "valami-ismeretlen"

    def test_other_sections_untouched(self, tmp_path):
        image_path = tmp_path / "IMG_0002.png"
        image_path.write_bytes(_encode_png(_solid_image((1, 2, 3))))
        _write_ini(
            tmp_path,
            "[IMG_0002.png]\n"
            "filters=enhance=1;\n"
            "[IMG_9999.png]\n"
            "star=yes\n"
            "keywords=nyaralas,tenger\n",
        )

        save_edited(
            image_path, _solid_image((4, 5, 6)), EditSession.from_value("enhance=1;")
        )

        document = load_document(tmp_path / _INI_NAME)
        other = document.section("IMG_9999.png")
        assert other is not None
        assert other.get("star") == "yes"
        assert other.get("keywords") == "nyaralas,tenger"


class TestMissingIni:
    """A .picasa.ini hiánya sem akadályozza a mentést (update_document
    létrehozza, ahogy a projekt más ini-írói is teszik, #151-minta)."""

    def test_save_without_existing_ini(self, tmp_path):
        image_path = tmp_path / "IMG_0003.png"
        image_path.write_bytes(_encode_png(_solid_image((1, 1, 1))))
        # Nincs .picasa.ini a mappában.

        result = save_edited(
            image_path, _solid_image((2, 2, 2)), EditSession.from_value("enhance=1;")
        )

        assert (tmp_path / _INI_NAME).exists()
        document = load_document(tmp_path / _INI_NAME)
        assert document.section("IMG_0003.png").get("redo") == "enhance=1;"
        assert result.redo_value == "enhance=1;"
