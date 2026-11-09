"""#6697: a cache-takarítás csak az első főablak-képkocka után indul."""

from __future__ import annotations

from pathlib import Path

from picasapy.thumbs import ThumbnailCache


def test_cache_peldanyositas_nem_indit_takaritast(tmp_path: Path):
    """A gyorstár létrehozása az első képkocka előtt nem indíthat takarítást."""
    root = tmp_path / "thumbs"
    shard = root / "aa"
    shard.mkdir(parents=True)
    existing = shard / "regi.jpg"
    existing.write_bytes(b"x" * 100)

    cache = ThumbnailCache(root, size=64, max_bytes=10)

    assert cache._prune_thread is None, "a konstruktor takarító háttérszálat indított"
    assert existing.exists(), "a konstruktor az induló képkocka előtt törölt cache-fájlt"


def test_takaritas_a_frame_callback_utani_startup_sorban_van():
    """A takarítás csak az első képkocka callbackjéből indított sorba kerül."""
    root = Path(__file__).resolve().parents[2]
    source = (root / "src/picasapy/app/application.py").read_text(encoding="utf-8")
    preparation = (
        root / "src/picasapy/app/application_startup_prepare.py"
    ).read_text(encoding="utf-8")
    first_frame = source.split("def _on_first_frame()", 1)[1].split(
        "    app = state.app", 1
    )[0]
    startup_batch = source.split("def _start_and_finish()", 1)[1].split(
        "def _maintenance_batch_finished", 1
    )[0]
    maintenance_finished = source.split(
        "def _maintenance_batch_finished", 1
    )[1].split("state.startup_maintenance.batchFinished.connect", 1)[0]

    assert "QTimer.singleShot(0, _start_and_finish)" in first_frame
    assert "maybe_prune" not in startup_batch
    assert 'key="thumb_cache_prune"' in maintenance_finished
    assert "state.thumb_cache.maybe_prune" in maintenance_finished
    assert maintenance_finished.index("_start_initial_scan(") < maintenance_finished.index(
        'key="thumb_cache_prune"'
    )
    assert "maybe_prune" not in preparation
