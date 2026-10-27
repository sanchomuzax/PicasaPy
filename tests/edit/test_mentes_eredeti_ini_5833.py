"""#5833: mentéskor a filterlánc az eredeti-mappa ini-jébe kerül."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.edit import EditSession, revert, save_edited
from picasapy.edit.save import LEGACY_ORIGINALS_DIR_NAME, undo_save
from picasapy.ini import load_document, parse_document, update_document
from picasapy.ini.backuphash import backuphash_for_local_datetime


_FILENAME = "IMG_0001.png"
_FILTERS = "enhance=1;autolight=1;"
_LEGACY_REDO = "sepia=1;"
_NOW = datetime(2026, 10, 25, 12, 34, 56)


class _FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 25, 12, 34, 56)


def _image(color: tuple[int, int, int]) -> np.ndarray:
    return np.full((8, 8, 3), color, dtype=np.uint8)


def _png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def _new_photo(tmp_path: Path) -> tuple[Path, bytes]:
    path = tmp_path / _FILENAME
    before = _png(_image((10, 20, 30)))
    path.write_bytes(before)
    (tmp_path / ".picasa.ini").write_text(
        f"[{_FILENAME}]\nfilters={_FILTERS}\nredo={_LEGACY_REDO}\n",
        encoding="utf-8",
    )
    return path, before


def test_save_moves_filters_to_original_ini_and_writes_backuphash(
    tmp_path, monkeypatch
):
    import picasapy.ini.backuphash as backuphash_module

    monkeypatch.setattr(backuphash_module, "datetime", _FrozenDateTime)
    image_path, _before = _new_photo(tmp_path)

    save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    current = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    original_ini = load_document(
        tmp_path / ".picasaoriginals" / ".picasa.ini"
    ).section(_FILENAME)
    assert current is not None
    assert current.items() == (("backuphash", str(backuphash_for_local_datetime(_NOW))),)
    assert original_ini is not None
    assert original_ini.get("filters") == _FILTERS


def test_save_uses_selected_legacy_originals_folder_ini(tmp_path):
    image_path, before = _new_photo(tmp_path)
    legacy_originals = tmp_path / LEGACY_ORIGINALS_DIR_NAME
    legacy_originals.mkdir()
    (legacy_originals / _FILENAME).write_bytes(before)

    save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    original_ini = load_document(legacy_originals / ".picasa.ini").section(_FILENAME)
    assert original_ini is not None and original_ini.get("filters") == _FILTERS
    assert not (tmp_path / ".picasaoriginals" / ".picasa.ini").exists()


def test_original_ini_write_failure_rolls_back_current_ini_and_image(
    tmp_path, monkeypatch
):
    from picasapy.edit import save as save_module

    image_path, before = _new_photo(tmp_path)
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_update = save_module.update_document

    def fail_original_ini(path, mutate, **kwargs):
        if Path(path) == original_ini_path:
            raise OSError("teszt: eredeti-mappa ini nem írható")
        return real_update(path, mutate, **kwargs)

    monkeypatch.setattr(save_module, "update_document", fail_original_ini)
    with pytest.raises(OSError, match="eredeti-mappa ini"):
        save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    current = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    assert image_path.read_bytes() == before
    assert current is not None
    assert current.get("filters") == _FILTERS
    assert current.get("redo") == _LEGACY_REDO
    assert current.get("backuphash") is None


def test_save_ini_preflight_read_failure_does_not_change_image(tmp_path, monkeypatch):
    from picasapy.edit import save as save_module

    image_path, before = _new_photo(tmp_path)
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_read = save_module._photo_ini_values

    def fail_original_read(path, section, keys):
        if Path(path) == original_ini_path:
            raise OSError("teszt: eredeti-mappa ini nem olvasható")
        return real_read(path, section, keys)

    monkeypatch.setattr(save_module, "_photo_ini_values", fail_original_read)
    with pytest.raises(OSError, match="eredeti-mappa ini nem olvasható"):
        save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    assert image_path.read_bytes() == before


def test_revert_ini_preflight_read_failure_does_not_change_image(tmp_path, monkeypatch):
    from picasapy.edit import save as save_module

    image_path, _before = _new_photo(tmp_path)
    save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))
    edited_bytes = image_path.read_bytes()
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_read = save_module._photo_ini_values

    def fail_original_read(path, section, keys):
        if Path(path) == original_ini_path:
            raise OSError("teszt: eredeti-mappa ini nem olvasható")
        return real_read(path, section, keys)

    monkeypatch.setattr(save_module, "_photo_ini_values", fail_original_read)
    with pytest.raises(OSError, match="eredeti-mappa ini nem olvasható"):
        revert(image_path)

    assert image_path.read_bytes() == edited_bytes


def test_save_rollback_removes_ini_that_did_not_exist_before(tmp_path, monkeypatch):
    from picasapy.edit import save as save_module

    image_path = tmp_path / _FILENAME
    before = _png(_image((10, 20, 30)))
    image_path.write_bytes(before)
    current_ini_path = tmp_path / ".picasa.ini"
    assert not current_ini_path.exists()
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_update = save_module.update_document

    def fail_original_ini(path, mutate, **kwargs):
        if Path(path) == original_ini_path:
            raise OSError("teszt: eredeti-mappa ini nem írható")
        return real_update(path, mutate, **kwargs)

    monkeypatch.setattr(save_module, "update_document", fail_original_ini)
    with pytest.raises(OSError, match="eredeti-mappa ini"):
        save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    assert image_path.read_bytes() == before
    assert not current_ini_path.exists()


def test_save_rollback_keeps_legacy_ini_as_only_ini_source(tmp_path, monkeypatch):
    from picasapy.edit import save as save_module

    image_path = tmp_path / _FILENAME
    before = _png(_image((10, 20, 30)))
    image_path.write_bytes(before)
    current_ini_path = tmp_path / ".picasa.ini"
    legacy_ini_path = tmp_path / "Picasa.ini"
    legacy_bytes = (
        f"[{_FILENAME}]\nstar=yes\nfilters={_FILTERS}\n"
        f"caption=maradjon\nredo={_LEGACY_REDO}\n"
    ).encode("utf-8")
    legacy_ini_path.write_bytes(legacy_bytes)
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_update = save_module.update_document

    def fail_original_ini(path, mutate, **kwargs):
        if Path(path) == original_ini_path:
            raise OSError("teszt: eredeti-mappa ini nem írható")
        return real_update(path, mutate, **kwargs)

    monkeypatch.setattr(save_module, "update_document", fail_original_ini)
    with pytest.raises(OSError, match="eredeti-mappa ini"):
        save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    assert image_path.read_bytes() == before
    assert legacy_ini_path.read_bytes() == legacy_bytes
    assert not current_ini_path.exists()


def test_save_rollback_preserves_ini_values_changed_after_preflight(
    tmp_path, monkeypatch
):
    from picasapy.edit import save as save_module

    image_path, before = _new_photo(tmp_path)
    current_ini_path = tmp_path / ".picasa.ini"
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_update = save_module.update_document
    injected_external_write = False
    external_values = {
        "filters": "autolight=1;",
        "redo": "enhance=1;",
        "backuphash": "12345",
    }

    def update_with_external_change(path, mutate, **kwargs):
        nonlocal injected_external_write
        if Path(path) == current_ini_path and not injected_external_write:
            injected_external_write = True
            real_update(
                path,
                lambda document: _with_values(
                    document, external_values
                ),
                backup=False,
            )
        if Path(path) == original_ini_path:
            raise OSError("teszt: eredeti-mappa ini nem írható")
        return real_update(path, mutate, **kwargs)

    monkeypatch.setattr(save_module, "update_document", update_with_external_change)
    with pytest.raises(OSError, match="eredeti-mappa ini"):
        save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    current = load_document(current_ini_path).section(_FILENAME)
    assert image_path.read_bytes() == before
    assert current is not None
    assert {key: current.get(key) for key in external_values} == external_values


def _with_values(document, values: dict[str, str]):
    for key, value in values.items():
        document = document.with_value(_FILENAME, key, value, carried=True)
    return document


def test_save_rollback_preserves_ini_values_changed_after_our_write(
    tmp_path, monkeypatch
):
    from picasapy.edit import save as save_module

    image_path, before = _new_photo(tmp_path)
    current_ini_path = tmp_path / ".picasa.ini"
    original_ini_path = tmp_path / ".picasaoriginals" / ".picasa.ini"
    real_update = save_module.update_document
    external_values = {
        "filters": "autolight=1;",
        "redo": "enhance=1;",
        "backuphash": "12345",
    }
    current_write_done = False

    def update_with_external_change(path, mutate, **kwargs):
        nonlocal current_write_done
        if Path(path) == original_ini_path:
            assert current_write_done
            real_update(
                current_ini_path,
                lambda document: _with_values(document, external_values),
                backup=False,
            )
            raise OSError("teszt: eredeti-mappa ini nem írható")
        result = real_update(path, mutate, **kwargs)
        if Path(path) == current_ini_path and not current_write_done:
            current_write_done = True
        return result

    monkeypatch.setattr(save_module, "update_document", update_with_external_change)
    with pytest.raises(OSError, match="eredeti-mappa ini"):
        save_edited(image_path, _image((40, 50, 60)), EditSession.from_value(_FILTERS))

    current = load_document(current_ini_path).section(_FILENAME)
    assert image_path.read_bytes() == before
    assert current is not None
    assert {key: current.get(key) for key in external_values} == external_values


def test_ini_rollback_cleanup_keeps_replacement_created_during_check(
    tmp_path, monkeypatch
):
    from picasapy.ini import io as ini_io
    from picasapy.ini import remove_ini_target_if_content_matches

    ini_path = tmp_path / ".picasa.ini"
    expected = parse_document("[IMG_0001.png]\nstar=yes\n")
    ini_path.write_bytes(expected.serialize().encode(expected.encoding))
    replacement = b"[IMG_0001.png]\nstar=external\n"
    real_read_bytes = ini_io._read_bytes
    replacement_written = False

    def read_then_replace(path):
        nonlocal replacement_written
        content = real_read_bytes(path)
        candidate = Path(path)
        if (
            not replacement_written
            and (
                candidate == ini_path
                or candidate.name.startswith("..picasa.ini.rollback-")
            )
        ):
            replacement_written = True
            ini_path.write_bytes(replacement)
        return content

    monkeypatch.setattr(ini_io, "_read_bytes", read_then_replace)
    remove_ini_target_if_content_matches(ini_path, expected)

    assert ini_path.read_bytes() == replacement


def test_undo_save_prefers_original_ini_filters_over_legacy_redo(tmp_path):
    image_path, before = _new_photo(tmp_path)
    save_edited(image_path, _image((70, 80, 90)), EditSession.from_value(_FILTERS))

    # A régi PicasaPy-verziók mentésjelzője nem írhatja felül az új forrást.
    update_document(
        tmp_path / ".picasa.ini",
        lambda document: document.with_value(_FILENAME, "redo", _LEGACY_REDO),
        backup=False,
    )

    result = undo_save(image_path)

    current = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    original_ini = load_document(
        tmp_path / ".picasaoriginals" / ".picasa.ini"
    ).section(_FILENAME)
    assert image_path.read_bytes() == before
    assert current is not None and current.get("filters") == _FILTERS
    assert current.get("redo") is None
    assert original_ini is None or original_ini.get("filters") is None
    assert result.restored_filters == _FILTERS


def test_undo_save_uses_legacy_redo_if_original_ini_has_no_chain(tmp_path):
    image_path = tmp_path / _FILENAME
    before = _png(_image((10, 20, 30)))
    image_path.write_bytes(_png(_image((70, 80, 90))))
    originals = tmp_path / ".picasaoriginals"
    originals.mkdir()
    (originals / _FILENAME).write_bytes(before)
    (originals / ".picasa.ini").write_text(
        f"[{_FILENAME}]\nfilters=\nstar=yes\n", encoding="utf-8"
    )
    snapshots = originals / ".picasapy-snapshots"
    snapshots.mkdir()
    (snapshots / "IMG_0001.1.png").write_bytes(before)
    (tmp_path / ".picasa.ini").write_text(
        f"[{_FILENAME}]\nredo={_LEGACY_REDO}\n", encoding="utf-8"
    )

    result = undo_save(image_path)

    current = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    original = load_document(originals / ".picasa.ini").section(_FILENAME)
    assert current is not None and current.get("filters") == _LEGACY_REDO
    assert current.get("redo") is None
    assert original is not None and original.get("filters") is None
    assert result.restored_filters == _LEGACY_REDO


def test_undo_save_restores_latest_chain_after_multiple_saves(tmp_path):
    image_path, _before = _new_photo(tmp_path)
    first_chain = "enhance=1;"
    second_chain = "bw=1;"
    first_render = _image((40, 50, 60))

    save_edited(image_path, first_render, EditSession.from_value(first_chain))
    first_saved_bytes = image_path.read_bytes()
    save_edited(image_path, _image((70, 80, 90)), EditSession.from_value(second_chain))

    undo_save(image_path)
    original_ini = load_document(
        tmp_path / ".picasaoriginals" / ".picasa.ini"
    ).section(_FILENAME)
    current_ini = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    assert image_path.read_bytes() == first_saved_bytes
    assert current_ini is not None and current_ini.get("filters") == second_chain
    assert original_ini is None or original_ini.get("filters") is None


def test_undo_save_visszaallitja_a_moddate_et_es_frissiti_a_backuphash_t(
    tmp_path, monkeypatch
):
    import picasapy.ini.backuphash as backuphash_module

    monkeypatch.setattr(backuphash_module, "datetime", _FrozenDateTime)
    image_path, _before = _new_photo(tmp_path)
    mtime_ns = 1_792_923_189_017_039_200
    os.utime(image_path, ns=(mtime_ns, mtime_ns))

    save_edited(image_path, _image((70, 80, 90)), EditSession.from_value(_FILTERS))
    original_ini = load_document(
        tmp_path / ".picasaoriginals" / ".picasa.ini"
    ).section(_FILENAME)
    assert original_ini is not None
    assert original_ini.get("moddate") == "1842276f6964dd01"

    # Az Undo Save is írja a kulcsot, nem csak a korábbi Mentés értékét őrzi.
    update_document(
        tmp_path / ".picasa.ini",
        lambda document: document.with_removed(_FILENAME, "backuphash"),
        backup=False,
    )
    undo_save(image_path)

    current = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    assert current is not None
    assert current.get("filters") == _FILTERS
    assert current.get("moddate") == "1842276f6964dd01"
    assert current.get("backuphash") == str(backuphash_for_local_datetime(_NOW))


def test_regi_eredeti_ini_moddate_hianyaban_az_undo_nem_ir_moddate_et(tmp_path):
    image_path = tmp_path / _FILENAME
    image_path.write_bytes(_png(_image((70, 80, 90))))
    originals = tmp_path / ".picasaoriginals"
    originals.mkdir()
    (originals / _FILENAME).write_bytes(_png(_image((10, 20, 30))))
    (originals / ".picasa.ini").write_text(
        f"[{_FILENAME}]\nfilters={_FILTERS}\n", encoding="utf-8"
    )
    snapshots = originals / ".picasapy-snapshots"
    snapshots.mkdir()
    (snapshots / "IMG_0001.1.png").write_bytes(_png(_image((10, 20, 30))))
    (tmp_path / ".picasa.ini").write_text(
        f"[{_FILENAME}]\n", encoding="utf-8"
    )

    undo_save(image_path)

    current = load_document(tmp_path / ".picasa.ini").section(_FILENAME)
    assert current is not None
    assert current.get("filters") == _FILTERS
    assert current.get("moddate") is None
    assert (current.get("backuphash") or "").isdecimal()
