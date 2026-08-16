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


def _fail_ini_write(monkeypatch, error=None):
    """Az ini-frissítés elbuktatása (tele lemez / zárolt fájl / párhuzamos
    Picasa-írás modellje) — a képfájl írása ettől még sikerül."""
    from picasapy.edit import save as save_module
    from picasapy.ini import IniConflictError

    failure = error if error is not None else IniConflictError("teszt: ütközés")

    def raise_error(path, mutate, **kwargs):
        raise failure

    monkeypatch.setattr(save_module, "update_document", raise_error)
    return failure


class TestSaveEditedIniFailureRollsBackImage:
    """#297: ha az ini-könyvelés ((c) lépés) elbukik, a kép már a beégetett
    szerkesztést tartalmazná, miközben a `filters=` bent maradt — a következő
    megnyitáskor a renderelő MÁSODSZOR is ráfuttatná a láncot. Ezért a
    képfájlt vissza kell állítani, és a hibát tovább kell dobni."""

    def test_first_save_restores_image_bytes(self, photo, monkeypatch):
        from picasapy.ini import IniConflictError

        image_path, original_bytes = photo
        _fail_ini_write(monkeypatch)

        with pytest.raises(IniConflictError):
            save_edited(
                image_path,
                _solid_image((99, 88, 77)),
                EditSession.from_value("enhance=1;"),
            )

        assert image_path.read_bytes() == original_bytes
        # A filters= bent maradt, de a kép is a szerkesztés ELŐTTI —
        # nincs dupla-szerkesztés a következő megnyitáskor.
        section = load_document(image_path.parent / _INI_NAME).section("IMG_0001.png")
        assert section.get("filters") == "enhance=1;"
        assert section.get("redo") is None

    def test_repeated_save_restores_previous_rendered_bytes(self, photo, monkeypatch):
        from picasapy.ini import IniConflictError

        image_path, original_bytes = photo
        save_edited(
            image_path, _solid_image((11, 22, 33)), EditSession.from_value("enhance=1;")
        )
        before_second = image_path.read_bytes()
        assert before_second != original_bytes

        _fail_ini_write(monkeypatch)
        with pytest.raises(IniConflictError):
            save_edited(
                image_path,
                _solid_image((44, 55, 66)),
                EditSession.from_value("enhance=1;autolight=1;"),
            )

        # NEM az eredetire, hanem az ELŐZŐ mentés bájtjaira áll vissza.
        assert image_path.read_bytes() == before_second

    def test_failed_restore_reports_both_problems(self, photo, monkeypatch):
        """Ha a visszaállítás is bukik, az üzenet mondja meg magyarul, hogy a
        kép elmentődött, de a nyilvántartás nem."""
        image_path, _original_bytes = photo
        _fail_ini_write(monkeypatch)

        from picasapy.edit import save as save_module

        real_write_atomic = save_module.write_atomic
        state = {"n": 0}

        def flaky_write_atomic(path, payload, **kwargs):
            if Path(path) == image_path:
                # A MÁSODIK képfájl-írás a visszaállítás — az bukik el.
                state["n"] += 1
                if state["n"] > 1:
                    raise OSError("teszt: a visszaállítás sem sikerült")
            return real_write_atomic(path, payload, **kwargs)

        monkeypatch.setattr(save_module, "write_atomic", flaky_write_atomic)

        with pytest.raises(SaveError) as excinfo:
            save_edited(
                image_path,
                _solid_image((99, 88, 77)),
                EditSession.from_value("enhance=1;"),
            )
        message = str(excinfo.value)
        assert str(image_path) in message
        assert ORIGINALS_DIR_NAME in message


class TestRevertIniFailureRollsBackImage:
    """#297 fordított irányban: a `revert` előbb a képet állítja vissza, és
    csak utána törli az ini-kulcsokat — ha a törlés bukik, a kép visszaáll
    az eredetire, miközben az ini szerint még szerkesztett. A képfájlt ezért
    vissza kell írni a `revert` előtti állapotra."""

    def test_ini_failure_restores_edited_image(self, photo, monkeypatch):
        from picasapy.ini import IniConflictError

        image_path, _original_bytes = photo
        save_edited(
            image_path, _solid_image((11, 22, 33)), EditSession.from_value("enhance=1;")
        )
        edited_bytes = image_path.read_bytes()

        _fail_ini_write(monkeypatch)
        with pytest.raises(IniConflictError):
            revert(image_path)

        assert image_path.read_bytes() == edited_bytes
        section = load_document(image_path.parent / _INI_NAME).section("IMG_0001.png")
        assert section.get("redo") is not None  # a nyilvántartás változatlan


class TestNumberedSnapshotsAndUndoSave:
    """#444: a Picasa NÉGY mentés-műveletet ismer; ezek közül az „Utolsó
    mentés visszavonása" a köztes fokozat — visszavonja a lemezre írást, de
    a SZERKESZTÉSEKET MEGTARTJA.
    """

    @staticmethod
    def _photo(tmp_path: Path) -> Path:
        path = tmp_path / "kep.png"
        path.write_bytes(_encode_png(_solid_image((10, 20, 30))))
        return path

    def test_every_save_leaves_a_numbered_snapshot(self, tmp_path):
        from picasapy.edit.save import ORIGINALS_DIR_NAME as originals

        path = self._photo(tmp_path)
        session = EditSession().append_effect("bw", ("1",))
        save_edited(path, _solid_image((1, 2, 3)), session)
        save_edited(path, _solid_image((4, 5, 6)), session)

        names = sorted(p.name for p in (tmp_path / originals).iterdir())
        # a „szent" eredeti + két, mentésenkénti sorszámozott pillanatkép
        assert names == ["kep.1.png", "kep.2.png", "kep.png"]

    def test_undo_save_restores_the_pixels_and_keeps_the_edits(self, tmp_path):
        from picasapy.edit.save import undo_save

        path = self._photo(tmp_path)
        before = path.read_bytes()
        session = EditSession().append_effect("bw", ("1",))
        save_edited(path, _solid_image((200, 200, 200)), session)
        assert path.read_bytes() != before

        result = undo_save(path)

        # a képpontok visszaálltak…
        assert path.read_bytes() == before
        # …a szerkesztés viszont MEGMARADT (a redo=-ból vissza a filters=-be)
        document = load_document(tmp_path / _INI_NAME)
        stored = document.section("kep.png")
        assert stored.get("filters") == session.to_value()
        assert stored.get("redo") is None
        assert result.restored_filters == session.to_value()

    def test_undo_save_steps_back_one_save_at_a_time(self, tmp_path):
        from picasapy.edit.save import undo_save

        path = self._photo(tmp_path)
        session = EditSession().append_effect("bw", ("1",))
        save_edited(path, _solid_image((100, 100, 100)), session)
        after_first = path.read_bytes()
        save_edited(path, _solid_image((200, 200, 200)), session)

        undo_save(path)
        assert path.read_bytes() == after_first

    def test_undo_save_without_a_save_is_refused(self, tmp_path):
        from picasapy.edit.save import undo_save

        path = self._photo(tmp_path)
        with pytest.raises(SaveError):
            undo_save(path)

    def test_revert_still_reaches_the_untouched_original(self, tmp_path):
        """A `revert` továbbra is a „szent" eredetihez visz vissza — az
        `undo_save` csak egy lépést lép, a `revert` az egészet."""
        path = self._photo(tmp_path)
        original = path.read_bytes()
        session = EditSession().append_effect("bw", ("1",))
        save_edited(path, _solid_image((100, 100, 100)), session)
        save_edited(path, _solid_image((200, 200, 200)), session)

        revert(path)
        assert path.read_bytes() == original


class TestGuardRejectionRollsBackImage:
    """#643: a round-trip őr visszautasítása (`FilterWriteError`) ugyanúgy
    KEZELT ini-írási hiba, mint a lemezhiba vagy a párhuzamos Picasa-ütközés.

    Ez nem stílus-kérdés, hanem adatvédelem: a kivétel a (c) lépésben, a
    képfájl felülírása UTÁN keletkezne, tehát ha nem tartozna a kezelt hibák
    közé, a kép a beégetett szerkesztéssel maradna, miközben a `filters=`
    bent van az iniben — a következő megnyitáskor a lánc MÁSODSZOR is
    lefutna (#297 dupla-szerkesztés).
    """

    def test_filter_write_error_restores_image_bytes(self, photo, monkeypatch):
        from picasapy.ini import FilterWriteError

        image_path, original_bytes = photo
        _fail_ini_write(monkeypatch, FilterWriteError("teszt: elvetendő lánc"))

        with pytest.raises(FilterWriteError):
            save_edited(
                image_path,
                _solid_image((99, 88, 77)),
                EditSession.from_value("enhance=1;"),
            )

        assert image_path.read_bytes() == original_bytes
        section = load_document(image_path.parent / _INI_NAME).section("IMG_0001.png")
        assert section.get("filters") == "enhance=1;"
        assert section.get("redo") is None
