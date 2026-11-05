"""Közös atomikus fájlírás (#129) — tartósság, jogmegőrzés, hibautak.

A négy írási hely (ini, IPTC, thumbnail, export) közös helpere: temp fájl
+ fsync + meglévő jogok megőrzése + os.replace, paraméterezhető
viselkedéssel (retry zárolt célra, a direkt-fallback tiltása, verseny-tűrés).
"""

import errno
import os
import select
import signal
import stat
import subprocess
import sys
from pathlib import Path

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

    def test_missing_parent_without_make_parents(self, tmp_path, monkeypatch):
        with pytest.raises(OSError):
            write_atomic(tmp_path / "nincs" / "a.bin", b"x")
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")

        def denied(*_args, **_kwargs):
            raise PermissionError(errno.EACCES, "írásvédett mappa")

        monkeypatch.setattr(ioutil, "_mkstemp", denied)
        with pytest.raises(PermissionError):
            write_atomic(target, b"uj", fallback_direct=True)
        assert target.read_bytes() == b"regi"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]


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

        monkeypatch.setattr(ioutil, "_fsync", spy_fsync)
        monkeypatch.setattr(ioutil, "_replace", spy_replace)
        write_atomic(tmp_path / "a.bin", b"x")
        assert "fsync" in events
        assert events.index("fsync") < events.index("replace")

        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")

        def fail_fsync(fd):
            raise OSError(errno.EIO, "fsync hiba")

        monkeypatch.setattr(ioutil, "_fsync", fail_fsync)
        with pytest.raises(OSError):
            write_atomic(target, b"uj")
        assert target.read_bytes() == b"regi"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_durable_false_skips_fsync(self, tmp_path, monkeypatch):
        # Thumbnail-cache: a tartósság nem szempont (újragenerálható),
        # az fsync a NAS-on csak lassítana.
        calls = []
        monkeypatch.setattr(ioutil, "_fsync", lambda fd: calls.append(fd))
        target = tmp_path / "a.bin"
        write_atomic(target, b"x", durable=False)
        assert calls == []

        def fail_replace(src, dst):
            raise OSError(errno.EIO, "cserélési hiba")

        monkeypatch.setattr(ioutil, "_replace", fail_replace)
        with pytest.raises(OSError):
            write_atomic(target, b"uj", durable=False)
        assert target.read_bytes() == b"x"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]


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
    @pytest.mark.parametrize("error_number", [errno.ENOSPC, errno.EACCES, errno.EIO])
    def test_temp_removed_on_write_error(self, tmp_path, monkeypatch, error_number):
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        original_fdopen = ioutil._fdopen

        class PartialWriter:
            def __init__(self, fd, mode):
                self.handle = original_fdopen(fd, mode)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def write(self, payload):
                self.handle.write(payload[:2])
                self.handle.flush()
                raise OSError(error_number, "tesztelt tempírási hiba")

        monkeypatch.setattr(
            ioutil, "_fdopen", lambda fd, mode: PartialWriter(fd, mode)
        )
        with pytest.raises(OSError):
            write_atomic(target, b"uj tartalom", fallback_direct=True)
        assert target.read_bytes() == b"regi"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_replace_error_propagates_and_cleans_temp(self, tmp_path, monkeypatch):
        def denied(src, dst):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(ioutil, "_replace", denied)
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

        monkeypatch.setattr(ioutil, "_replace", flaky)
        target = tmp_path / "a.bin"
        write_atomic(target, b"x", lock_retries=5, lock_retry_delay=0.001)
        assert target.read_bytes() == b"x"
        assert calls["n"] == 3

    def test_fallback_direct_does_not_overwrite_after_replace_error(
        self, tmp_path, monkeypatch
    ):
        # Az atomikus cserét nem szabad közvetlen írással megkerülni: egy
        # összeomlás / megtelt lemez ilyenkor a korábbi tartalmat csonkítaná.
        def denied(src, dst):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(ioutil, "_replace", denied)
        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        with pytest.raises(PermissionError):
            write_atomic(
                target, b"uj", lock_retries=2, lock_retry_delay=0.001,
                fallback_direct=True,
            )
        assert target.read_bytes() == b"regi"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    @pytest.mark.parametrize("error_number", [errno.ENOSPC, errno.EACCES, errno.EIO])
    def test_fallback_direct_write_failure_preserves_old_bytes(
        self, tmp_path, monkeypatch, error_number
    ):
        def denied(src, dst):
            raise PermissionError(errno.EACCES, "cél zárolt")

        target = tmp_path / "a.bin"
        target.write_bytes(b"regi tartalom")
        original_write_bytes = type(target).write_bytes
        direct_calls = []

        def partial_direct_write(path, payload):
            if path == target:
                direct_calls.append(path)
                with path.open("wb") as handle:
                    handle.write(payload[:3])
                raise OSError(error_number, "tesztelt írási hiba")
            return original_write_bytes(path, payload)

        monkeypatch.setattr(ioutil, "_replace", denied)
        monkeypatch.setattr(type(target), "write_bytes", partial_direct_write)
        with pytest.raises(PermissionError, match="cél zárolt"):
            write_atomic(
                target, b"uj tartalom", lock_retries=1, lock_retry_delay=0,
                fallback_direct=True,
            )

        assert direct_calls == []
        assert target.read_bytes() == b"regi tartalom"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_lock_retries_exhausted_legacy_fallback_preserves_target(
        self, tmp_path, monkeypatch
    ):
        calls = {"count": 0}

        def denied(src, dst):
            calls["count"] += 1
            raise PermissionError(errno.EACCES, "cél zárolt")

        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        monkeypatch.setattr(ioutil, "_replace", denied)
        with pytest.raises(PermissionError):
            write_atomic(
                target, b"uj", lock_retries=2, lock_retry_delay=0,
                fallback_direct=True,
            )
        assert calls["count"] == 3
        assert target.read_bytes() == b"regi"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    @pytest.mark.skipif(os.name != "nt", reason="Windows célzárolás")
    def test_windows_locked_target_never_uses_direct_write(self, tmp_path, monkeypatch):
        import ctypes

        target = tmp_path / "a.bin"
        target.write_bytes(b"regi")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.argtypes = (
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        )
        create_file.restype = ctypes.c_void_p
        handle = create_file(
            str(target), 0x80000000 | 0x40000000, 0, None, 3, 0x80, None
        )
        invalid_handle = ctypes.c_void_p(-1).value
        assert handle != invalid_handle
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (ctypes.c_void_p,)
        close_handle.restype = ctypes.c_int
        original_write_bytes = type(target).write_bytes
        direct_calls = []

        def observe_direct_write(path, payload):
            if path == target:
                direct_calls.append(path)
            return original_write_bytes(path, payload)

        monkeypatch.setattr(type(target), "write_bytes", observe_direct_write)
        try:
            with pytest.raises(PermissionError):
                write_atomic(
                    target, b"uj", lock_retries=1, lock_retry_delay=0,
                    fallback_direct=True,
                )
        finally:
            close_handle(ctypes.c_void_p(handle))

        assert direct_calls == []
        assert target.read_bytes() == b"regi"

    def test_replace_race_tolerated(self, tmp_path, monkeypatch):
        # Párhuzamos thumbnail-írók: ha a cél közben (a másik írótól)
        # létrejött, a vesztes fél hibája lenyelhető.
        def sharing_violation(src, dst):
            raise OSError(22, "sharing violation")

        monkeypatch.setattr(ioutil, "_replace", sharing_violation)
        target = tmp_path / "a.bin"
        target.write_bytes(b"gyoztes")
        write_atomic(target, b"vesztes", ignore_replace_race=True)
        assert target.read_bytes() == b"gyoztes"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_replace_race_tolerates_permission_error(self, tmp_path, monkeypatch):
        # Windowson a sharing violation PermissionError-ként jön (#66).
        def sharing_violation(src, dst):
            raise PermissionError(13, "sharing violation")

        monkeypatch.setattr(ioutil, "_replace", sharing_violation)
        target = tmp_path / "a.bin"
        target.write_bytes(b"gyoztes")
        write_atomic(target, b"vesztes", ignore_replace_race=True)
        assert target.read_bytes() == b"gyoztes"
        assert [p.name for p in tmp_path.iterdir()] == ["a.bin"]

    def test_replace_race_without_existing_target_raises(self, tmp_path, monkeypatch):
        def sharing_violation(src, dst):
            raise OSError(22, "sharing violation")

        monkeypatch.setattr(ioutil, "_replace", sharing_violation)
        with pytest.raises(OSError):
            write_atomic(tmp_path / "a.bin", b"x", ignore_replace_race=True)
        assert list(tmp_path.iterdir()) == []


_CRASH_CHILD = r"""
import sys
from pathlib import Path
import picasapy.ioutil as ioutil

stage, target = sys.argv[1], Path(sys.argv[2])
payload = b"uj tartalom, ami hosszabb a felnel"
original_fdopen = ioutil._fdopen
original_fsync = ioutil._fsync
original_replace = ioutil._replace

def pause():
    print("PAUSED", flush=True)
    sys.stdin.buffer.read(1)

if stage == "write":
    class PartialWriter:
        def __init__(self, fd, mode):
            self.handle = original_fdopen(fd, mode)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return self.handle.__exit__(*args)
        def write(self, data):
            count = max(1, len(data) // 2)
            result = self.handle.write(data[:count])
            self.handle.flush()
            pause()
            return result
        def flush(self):
            return self.handle.flush()
        def fileno(self):
            return self.handle.fileno()
    ioutil._fdopen = lambda fd, mode: PartialWriter(fd, mode)
elif stage == "fsync":
    calls = 0
    def gated_fsync(fd):
        global calls
        result = original_fsync(fd)
        calls += 1
        if calls == 1:
            pause()
        return result
    ioutil._fsync = gated_fsync
elif stage == "replace":
    def gated_replace(source, destination):
        result = original_replace(source, destination)
        pause()
        return result
    ioutil._replace = gated_replace

ioutil.write_atomic(target, payload, durable=True)
"""


@pytest.mark.skipif(os.name != "posix", reason="SIGKILL-es rendszerhívás-próba")
@pytest.mark.parametrize("stage,expected", [
    ("write", b"regi tartalom"),
    ("fsync", b"regi tartalom"),
    ("replace", b"uj tartalom, ami hosszabb a felnel"),
])
def test_sigkill_at_write_fsync_replace_keeps_whole_target(tmp_path, stage, expected):
    target = tmp_path / ".picasa.ini"
    target.write_bytes(b"regi tartalom")
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(project_root / "src"), env.get("PYTHONPATH", "")]
    )
    process = subprocess.Popen(
        [sys.executable, "-c", _CRASH_CHILD, stage, str(target)],
        cwd=project_root,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        ready, _, _ = select.select([process.stdout], [], [], 15)
        assert ready, f"a gyermek nem érte el a {stage} határt"
        assert process.stdout.readline().strip() == "PAUSED"
        os.kill(process.pid, signal.SIGKILL)
        assert process.wait(timeout=15) == -signal.SIGKILL
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=15)

    assert target.read_bytes() == expected
    from picasapy.scanner import scan_tree

    scan_tree(tmp_path)
    assert list(tmp_path.iterdir()) == [target], (
        "az új indulás mappabejárása eltakarítja a megszakadt írás tempfájlját"
    )
