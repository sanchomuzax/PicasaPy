"""A PerfCollector mintavétel-logikájának tesztjei (#211) — mock-olt
CPU/RSS-forrással és órával, valódi szál/processz nélkül."""

from picasapy.perf.collector import PerfCollector, PerfSample, read_proc_cpu_rss


def _make_collector(**overrides):
    # _tick EGYETLEN cpu_rss_fn/clock hívást tesz — ezek a „jelen" mintát
    # adják vissza; a `prev_*` paramétereket a hívó (a teszt) adja meg
    cpu_rss = overrides.pop("cpu_rss", (1.0, 2000))
    wall = overrides.pop("wall", 1.0)
    defaults = dict(
        cpu_rss_fn=lambda: cpu_rss,
        clock=lambda: wall,
        wall_clock=lambda: wall,
        cpu_count=1,
    )
    defaults.update(overrides)
    return PerfCollector(**defaults)


class TestTick:
    def test_computes_cpu_percent_from_delta(self):
        # 1 mp alatt 1 mp cpu-idő fogyott el (1 magon) -> 100%
        collector = _make_collector()
        sample, cpu_time, wall = collector._tick(prev_cpu_time=0.0, prev_wall=0.0)
        assert isinstance(sample, PerfSample)
        assert sample.cpu_percent == 100.0
        assert sample.rss_bytes == 2000
        assert cpu_time == 1.0
        assert wall == 1.0

    def test_normalizes_by_cpu_count(self):
        # ugyanaz a delta, de 4 magon -> 25%
        collector = _make_collector(cpu_count=4)
        sample, _, _ = collector._tick(prev_cpu_time=0.0, prev_wall=0.0)
        assert sample.cpu_percent == 25.0

    def test_negative_cpu_delta_is_clamped_to_zero(self):
        # elméletileg nem történhetne meg (monoton cpu-idő), de védőháló
        collector = _make_collector(cpu_rss=(5.0, 1000))
        sample, _, _ = collector._tick(prev_cpu_time=10.0, prev_wall=0.0)
        assert sample.cpu_percent == 0.0

    def test_activity_fn_populates_sample(self):
        activity = {
            "thumb_active": 3,
            "thumb_queue": 7,
            "sync_folder": "2018",
            "sync_done": 12,
            "sync_total": 40,
            "gui_stall_ms": 4.5,
        }
        collector = _make_collector(activity_fn=lambda: activity)
        sample, _, _ = collector._tick(prev_cpu_time=0.0, prev_wall=0.0)
        assert sample.thumb_active == 3
        assert sample.thumb_queue == 7
        assert sample.sync_folder == "2018"
        assert sample.sync_done == 12
        assert sample.sync_total == 40
        assert sample.gui_stall_ms == 4.5

    def test_missing_activity_fn_defaults_to_idle(self):
        collector = _make_collector(activity_fn=None)
        sample, _, _ = collector._tick(prev_cpu_time=0.0, prev_wall=0.0)
        assert sample.thumb_active == 0
        assert sample.sync_folder == ""


class TestStartStop:
    def test_idempotent_start(self):
        collector = _make_collector()
        collector.start()
        thread1 = collector._thread
        collector.start()  # no-op, nem indít másodikat
        assert collector._thread is thread1
        collector.stop()
        assert collector._thread is None

    def test_stop_without_start_is_noop(self):
        collector = _make_collector()
        collector.stop()  # nem dobhat kivételt

    def test_real_thread_emits_samples(self):
        import threading
        import time as time_module

        samples = []
        done = threading.Event()

        def on_sample(sample):
            samples.append(sample)
            done.set()

        collector = PerfCollector(
            interval=0.01,
            cpu_rss_fn=lambda: (time_module.monotonic(), 1000),
            on_sample=on_sample,
        )
        collector.start()
        assert done.wait(2.0), "nem érkezett mintavétel a háttérszálból"
        collector.stop()
        assert not collector.is_running
        assert samples


class TestReadProcCpuRss:
    def test_returns_positive_values_for_self(self):
        cpu_time, rss_bytes = read_proc_cpu_rss()
        assert cpu_time >= 0.0
        assert rss_bytes > 0  # a futó teszt-processznek biztosan van RSS-e

    def test_unknown_pid_falls_back(self):
        # egy szinte biztosan nem-létező PID -> a /proc olvasás elhasal,
        # a tartalék (resource-alapú) útra esik, kivétel nélkül
        cpu_time, rss_bytes = read_proc_cpu_rss(pid=2**30)
        assert cpu_time >= 0.0
        assert rss_bytes >= 0
