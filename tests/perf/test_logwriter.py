"""A PerfLogWriter JSONL-formátumának tesztjei (#211)."""

import json

from picasapy.perf.collector import PerfSample
from picasapy.perf.logwriter import PerfLogWriter, sample_to_dict, session_header


def _sample(**overrides) -> PerfSample:
    defaults = dict(
        ts=1_800_000_000.0,
        cpu_percent=12.3,
        rss_bytes=104_857_600,
        thumb_active=2,
        thumb_queue=0,
        sync_folder="2018",
        sync_done=120,
        sync_total=400,
        gui_stall_ms=3.2,
    )
    defaults.update(overrides)
    return PerfSample(**defaults)


class TestSessionHeader:
    def test_has_required_fields(self):
        header = session_header("v0.7.0 (81.abc)", qt_version="6.7.2")
        assert header["type"] == "session"
        assert header["app_version"] == "v0.7.0 (81.abc)"
        assert header["qt_version"] == "6.7.2"
        assert "platform" in header
        assert "python_version" in header
        assert header["started_at"].endswith("+00:00") or "T" in header["started_at"]


class TestSampleToDict:
    def test_converts_timestamp_to_iso(self):
        data = sample_to_dict(_sample())
        assert data["type"] == "sample"
        assert data["cpu_percent"] == 12.3
        assert data["sync_folder"] == "2018"
        assert "T" in data["ts"]  # ISO-8601

    def test_no_full_path_leaks_only_folder_name(self):
        # a hívónak (perf_controller) a mappa NEVÉT kell átadnia, nem a
        # teljes útvonalat — ez a teszt a szerződést dokumentálja: a
        # logwriter maga nem vág útvonalat, csak amit kap, azt írja ki
        data = sample_to_dict(_sample(sync_folder="nyaralas"))
        assert data["sync_folder"] == "nyaralas"
        assert "/" not in data["sync_folder"]


class TestPerfLogWriterSave:
    def test_save_writes_header_then_samples(self, tmp_path):
        writer = PerfLogWriter(app_version="v0.7.0 (dev)", qt_version="6.7.2")
        writer.record(_sample(cpu_percent=1.0))
        writer.record(_sample(cpu_percent=2.0))
        path = writer.save(directory=tmp_path)
        assert path.exists()
        assert path.parent == tmp_path
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3  # 1 fejléc + 2 minta
        header = json.loads(lines[0])
        assert header["type"] == "session"
        sample1 = json.loads(lines[1])
        sample2 = json.loads(lines[2])
        assert sample1["type"] == "sample"
        assert sample1["cpu_percent"] == 1.0
        assert sample2["cpu_percent"] == 2.0

    def test_save_with_empty_buffer_writes_only_header(self, tmp_path):
        writer = PerfLogWriter(app_version="v0.7.0 (dev)")
        path = writer.save(directory=tmp_path)
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["type"] == "session"

    def test_default_directory_is_xdg_cache(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
        writer = PerfLogWriter(app_version="v0.7.0 (dev)")
        path = writer.save()
        assert path.parent == tmp_path / "picasapy" / "perf"

    def test_clear_empties_buffer(self, tmp_path):
        writer = PerfLogWriter(app_version="v0.7.0 (dev)")
        writer.record(_sample())
        assert writer.sample_count == 1
        writer.clear()
        assert writer.sample_count == 0

    def test_buffer_is_bounded(self, tmp_path):
        writer = PerfLogWriter(app_version="v0.7.0 (dev)", max_samples=3)
        for i in range(10):
            writer.record(_sample(cpu_percent=float(i)))
        assert writer.sample_count == 3
        path = writer.save(directory=tmp_path)
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        # 1 fejléc + a legutolsó 3 minta (FIFO-kilakoltatás)
        assert len(lines) == 4
        cpu_values = [json.loads(line)["cpu_percent"] for line in lines[1:]]
        assert cpu_values == [7.0, 8.0, 9.0]
