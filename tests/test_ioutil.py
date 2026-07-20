"""Közös atomikus fájlírás (#129) — tartósság, jogmegőrzés, hibautak.

A négy írási hely (ini, IPTC, thumbnail, export) közös helpere: temp fájl
+ fsync + meglévő jogok megőrzése + os.replace, paraméterezhető
viselkedéssel (retry zárolt célra, direkt-írás fallback, verseny-tűrés).
"""

import os
import stat

import pytest

import picasapy.ioutil as ioutil
from picasapy.ioutil import write_atomic


class TestBasics:
    def test_writes_payload(self, tmp_path):
        target = tmp_path / "a.bin"
        write_atomic(target, b"tartalom")
        assert target.read_bytes() == b"tartalom"

    def test_overwrites_existing(self, tmp_path):
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        write_atomic(target, b"uj")
        assert target.read_bytes() == b"uj"

    def test_no_temp_leftovers(self, tmp_path):
        target = tmp_path / "a.bin"
        write_atomic(target, b"x")
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_make_parents(self, tmp_path):
        target = tmp_path / "al" / "konyvtar" / "a.bin"
        write_atomic(target, b"x", make_parents=True)
        assert target.read_bytes() == b"x"

    def test_missing_parent_without_make_parents(self, tmp_path):
        with pytest.raises(OSError):
            write_atomic(tmp_path / "nincs" / "a.bin", b"x")


class TestDurability:
    def test_fsync_called_before_replace(self, tmp_path, monkeypatch):
        # Crash-biztonság: a temp fájl tartalma fsync-kel lemezen legyen,
        # MIELŐTT a rename a cél helyére teszi (csonka fájl tilos).
        events = []
        original_fsync, original_replace = os.fsync, os.replace

        def spy_fsync(fd):
            events.append("fsync")
            return original_fsync(fd)

        def spy_replace(src, dst):
            events.append("replace")
            return original_replace(src, dst)

        monkeypatch.setattr(ioutil.os, "fsync", spy_fsync)
        monkeypatch.setattr(ioutil.os, "replace", spy_replace)
        write_atomic(tmp_path / "a.bin", b"x")
        assert "fsync" in events
        assert events.index("fsync") < events.index("replace")

    def test_durable_false_skips_fsync(self, tmp_path, monkeypatch):
        # Thumbnail-cache: a tartósság nem szempont (újragenerálható),
        # az fsync a NAS-on csak lassítana.
        calls = []
        monkeypatch.setattr(ioutil.os, "fsync", lambda fd: calls.append(fd))
        write_atomic(tmp_path / "a.bin", b"x", durable=False)
        assert calls == []


@pytest.mark.skipif(
    os.name != "posix", reason="Windowson a chmod csak a read-only bitet kezeli"
)
class TestModePreservation:
    def test_existing_mode_preserved(self, tmp_path):
        # NAS-on más kliens (az eredeti Picasa) is olvassa a fájlt: a csere
        # nem szűkítheti a jogokat a mkstemp-féle 0600-ra.
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        target.chmod(0o664)
        write_atomic(target, b"uj")
        assert stat.S_IMODE(target.stat().st_mode) == 0o664

    def test_preserve_mode_false_leaves_default(self, tmp_path):
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        target.chmod(0o604)
        write_atomic(target, b"uj", preserve_mode=False)
        assert stat.S_IMODE(target.stat().st_mode) != 0o604


class TestFailurePaths:
    def test_temp_removed_on_write_error(self, tmp_path, monkeypatch):
        def boom(fd, mode):
            raise OSError("nincs hely")

        monkeypatch.setattr(ioutil.os, "fdopen", boom)
        with pytest.raises(OSError):
            write_atomic(tmp_path / "a.bin", b"x")
        assert list(tmp_path.iterdir()) == []

    def test_replace_error_propagates_and_cleans_temp(self, tmp_path, monkeypatch):
        def denied(src, dst):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(ioutil.os, "replace", denied)
        with pytest.raises(PermissionError):
            write_atomic(tmp_path / "a.bin", b"x")
        assert list(tmp_path.iterdir()) == []

    def test_lock_retries_then_success(self, tmp_path, monkeypatch):
        # Windows: a célfájl átmenetileg zárolt (a néző épp tölti) → retry.
        original_replace = os.replace
        calls = {"n": 0}

        def flaky(src, dst):
            calls["n"] += 1
            if calls["n"] < 3:
                raise PermissionError(13, "Access is denied")
            return original_replace(src, dst)

        monkeypatch.setattr(ioutil.os, "replace", flaky)
        target = tmp_path / "a.bin"
        write_atomic(target, b"x", lock_retries=5, lock_retry_delay=0.001)
        assert target.read_bytes() == b"x"
        assert calls["n"] == 3

    def test_fallback_direct_write(self, tmp_path, monkeypatch):
        # Ha a zár nem enged fel, nem-atomikus közvetlen írás (képfájlnál
        # elfogadható fallback; az ini nem kéri).
        def denied(src, dst):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(ioutil.os, "replace", denied)
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        write_atomic(
            target, b"uj", lock_retries=2, lock_retry_delay=0.001,
            fallback_direct=True,
        )
        assert target.read_bytes() == b"uj"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_replace_race_tolerated(self, tmp_path, monkeypatch):
        # Párhuzamos thumbnail-írók: ha a cél közben (a másik írótól)
        # létrejött, a vesztes fél hibája lenyelhető.
        def sharing_violation(src, dst):
            raise OSError(22, "sharing violation")

        monkeypatch.setattr(ioutil.os, "replace", sharing_violation)
        target = tmp_path / "a.bin"
        target.write_bytes(b"gyoztes")
        write_atomic(target, b"vesztes", ignore_replace_race=True)
        assert target.read_bytes() == b"gyoztes"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_replace_race_tolerates_permission_error(self, tmp_path, monkeypatch):
        # Windowson a sharing violation PermissionError-ként jön (#66).
        def sharing_violation(src, dst):
            raise PermissionError(13, "sharing violation")

        monkeypatch.setattr(ioutil.os, "replace", sharing_violation)
        target = tmp_path / "a.bin"
        target.write_bytes(b"gyoztes")
        write_atomic(target, b"vesztes", ignore_replace_race=True)
        assert target.read_bytes() == b"gyoztes"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_replace_race_without_existing_target_raises(self, tmp_path, monkeypatch):
        def sharing_violation(src, dst):
            raise OSError(22, "sharing violation")

        monkeypatch.setattr(ioutil.os, "replace", sharing_violation)
        with pytest.raises(OSError):
            write_atomic(tmp_path / "a.bin", b"x", ignore_replace_race=True)
        assert list(tmp_path.iterdir()) == []
