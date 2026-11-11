"""#144: méretkorlátos LRU-takarító a thumbnail-lemezcache-hez."""

import os
import time

import pytest

from picasapy.thumbs import ThumbnailCache
from picasapy.thumbs import prune as prune_module
from picasapy.thumbs.prune import prune_cache_dir, prune_if_needed, prune_in_background


def _make_entry(root, shard, name, size, age_seconds):
    """Cache-fájl adott mérettel és korral (atime+mtime visszadátumozva)."""
    folder = root / shard
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(b"\xff" * size)
    stamp = time.time() - age_seconds
    os.utime(path, (stamp, stamp))
    return path


class TestPruneCacheDir:
    def test_missing_root_is_noop(self, tmp_path):
        assert prune_cache_dir(tmp_path / "nincs", 1000) == 0

    def test_under_limit_deletes_nothing(self, tmp_path):
        keep = _make_entry(tmp_path, "aa", "a.jpg", 100, age_seconds=1000)
        assert prune_cache_dir(tmp_path, 1000) == 0
        assert keep.exists()

    def test_oldest_removed_first_until_under_limit(self, tmp_path):
        old = _make_entry(tmp_path, "aa", "regi.jpg", 100, age_seconds=3000)
        mid = _make_entry(tmp_path, "bb", "kozep.jpg", 100, age_seconds=2000)
        new = _make_entry(tmp_path, "cc", "uj.jpg", 100, age_seconds=1000)
        freed = prune_cache_dir(tmp_path, 200)
        assert freed == 100
        assert not old.exists() and mid.exists() and new.exists()

    def test_size_limit_respected(self, tmp_path):
        for i in range(10):
            _make_entry(tmp_path, "aa", f"t{i}.jpg", 50, age_seconds=100 * i)
        prune_cache_dir(tmp_path, 120)
        total = sum(p.stat().st_size for p in tmp_path.rglob("*.jpg"))
        assert total <= 120

    def test_zero_limit_clears_everything(self, tmp_path):
        _make_entry(tmp_path, "aa", "a.jpg", 10, age_seconds=10)
        _make_entry(tmp_path, "bb", "b.jpg", 10, age_seconds=20)
        assert prune_cache_dir(tmp_path, 0) == 20
        assert list(tmp_path.rglob("*.jpg")) == []

    def test_negative_limit_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            prune_cache_dir(tmp_path, -1)

    def test_empty_shard_dirs_removed(self, tmp_path):
        _make_entry(tmp_path, "aa", "a.jpg", 10, age_seconds=10)
        prune_cache_dir(tmp_path, 0)
        assert not (tmp_path / "aa").exists()

    def test_foreign_files_untouched(self, tmp_path):
        # nem-jpg fájlhoz (pl. idegen fájl a cache-mappában) nem nyúlunk
        stray = tmp_path / "idegen.txt"
        stray.write_bytes(b"x" * 500)
        _make_entry(tmp_path, "aa", "a.jpg", 100, age_seconds=10)
        prune_cache_dir(tmp_path, 0)
        assert stray.exists()

    def test_bejaras_scandirral_mukodik_rglob_nelkul(self, tmp_path, monkeypatch):
        """A teljes cache-keresés scandirrel történik, nem Path.rglobbal."""
        old = _make_entry(tmp_path, "aa", "regi.jpg", 100, age_seconds=2000)

        def nincs_rglob(*_args, **_kwargs):
            raise AssertionError("a gyorstár-takarító Path.rglobot használt")

        monkeypatch.setattr(type(tmp_path), "rglob", nincs_rglob)
        assert prune_cache_dir(tmp_path, 0) == 100
        assert not old.exists()


class TestPruneSchedule:
    def test_nem_olvas_ujra_napon_belul_valtozatlan_cache_eseten(
        self, tmp_path, monkeypatch
    ):
        _make_entry(tmp_path, "aa", "a.jpg", 50, age_seconds=10)
        # #6824: a shardmappa is legyen régi. Windowson a `time.time()` és a
        # fájlrendszer időbélyege eltérő felbontású, így a frissen létrehozott
        # mappa ideje a rögzített ellenőrzési időpont UTÁNINAK látszhat, és a
        # második hívás változásnak venné (CI 42990562883: 1 == 0).
        old = time.time() - 10
        os.utime(tmp_path / "aa", (old, old))
        assert prune_if_needed(tmp_path, 1000) == 0

        scans = 0
        original = prune_module._scan_cache_dir

        def counted_scan(root):
            nonlocal scans
            scans += 1
            return original(root)

        monkeypatch.setattr(prune_module, "_scan_cache_dir", counted_scan)
        assert prune_if_needed(tmp_path, 1000) == 0
        assert scans == 0

    def test_merettullepesnel_napon_belul_is_takarit(self, tmp_path):
        _make_entry(tmp_path, "aa", "regi.jpg", 100, age_seconds=3000)
        retained = _make_entry(tmp_path, "bb", "uj.jpg", 100, age_seconds=1000)
        assert prune_if_needed(tmp_path, 100) == 100
        assert retained.exists()

        extra = _make_entry(tmp_path, "cc", "ujabb.jpg", 100, age_seconds=1)
        future = time.time() + 5
        os.utime(extra.parent, (future, future))
        assert prune_if_needed(tmp_path, 100) == 100
        assert not retained.exists()
        assert extra.exists()


class TestCacheIntegration:
    def test_cache_prune_uses_configured_limit(self, tmp_path):
        root = tmp_path / "cache"
        _make_entry(root, "aa", "regi.jpg", 100, age_seconds=2000)
        kept = _make_entry(root, "bb", "uj.jpg", 100, age_seconds=1000)
        cache = ThumbnailCache(root, size=64, max_bytes=100)
        # #6697: a konstruktor már nem indít takarítást; a kérés explicit.
        assert cache._prune_thread is None
        cache.prune()
        assert list(root.rglob("*.jpg")) == [kept]

    def test_cache_without_limit_prune_is_noop(self, tmp_path):
        root = tmp_path / "cache"
        entry = _make_entry(root, "aa", "a.jpg", 100, age_seconds=1000)
        cache = ThumbnailCache(root, size=64)
        assert cache.prune() == 0
        assert entry.exists()

    def test_background_prune_runs_at_init(self, tmp_path):
        """#6697: a konstruktor nem takarít, karbantartási kérésre igen."""
        root = tmp_path / "cache"
        old = _make_entry(root, "aa", "regi.jpg", 100, age_seconds=2000)
        _make_entry(root, "bb", "uj.jpg", 100, age_seconds=1000)
        cache = ThumbnailCache(root, size=64, max_bytes=100)
        assert cache._prune_thread is None
        assert old.exists()
        cache.maybe_prune()
        assert len(list(root.rglob("*.jpg"))) == 1

    def test_background_thread_is_daemon(self, tmp_path):
        thread = prune_in_background(tmp_path, 1000)
        assert thread.daemon
        thread.join(5)
        assert not thread.is_alive()
