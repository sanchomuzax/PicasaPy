"""#6793: a háttér-arckeresés várakozása és rövid függő sora."""

# rontás-kontroll: picasapy.app.face_scan_controller_scan_mixin._AUTOMATIC_SCAN_UNPAUSED_LIMIT = 0 → 1 failed

from __future__ import annotations

import logging
import threading
import traceback

from PySide6.QtCore import QSettings

from picasapy.app.busy_activity import munka_neve
from picasapy.app.busy_registry import get_app_busy_registry
from picasapy.index import open_index
from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre
from test_face_scan_controller import _FakeDetector, _make_controller, _run


def _make_library(tmp_path, count):
    root = tmp_path / "kepek"
    root.mkdir()
    for number in range(count):
        make_jpeg(root / f"{number:03}.jpg", size=(80, 60))
    return root


def test_automatic_scan_hides_busy_activity_while_paused(
    qt_app, tmp_path, monkeypatch
):
    root = _make_library(tmp_path, 21)
    ctl = _make_controller(qt_app, tmp_path, root, detector=_FakeDetector())
    ctl.setSuggestionsEnabled(False)

    registry = get_app_busy_registry()
    eredeti_begin = registry.begin
    eredeti_end = registry.end
    active: dict[int, str] = {}
    begin_calls = []
    end_calls = []
    active_lock = threading.Lock()

    def counted_begin(label=""):
        ticket = eredeti_begin(label)
        with active_lock:
            active[ticket] = label
            begin_calls.append(label)
        return ticket

    def counted_end(ticket=0):
        with active_lock:
            end_calls.append(ticket)
            active.pop(ticket, None)
        return eredeti_end(ticket)

    monkeypatch.setattr(registry, "begin", counted_begin)
    monkeypatch.setattr(registry, "end", counted_end)

    pause_entered = threading.Event()
    resume = threading.Event()

    def should_pause():
        pause_entered.set()
        return not resume.is_set()

    ctl._scan_should_pause = should_pause
    ctl._detect = lambda *_args, **_kwargs: ()
    ctl.scanNewFaces()

    try:
        assert pause_entered.wait(2.0), "a nagy függő készlet nem állt meg aktivitásnál"
        with active_lock:
            paused_scan_entries = [
                label
                for label in active.values()
                if label == munka_neve("picasapy-face-scan")
            ]
        assert paused_scan_entries == [], (
            "a picasapy-face-scan busy-bejegyzés aktív maradt a várakozás alatt"
        )
    finally:
        resume.set()
        assert ctl.waitForBackgroundWorkers(5.0)

    assert len(begin_calls) == len(end_calls)


def test_small_pending_set_finishes_during_continuous_user_activity(
    qt_app, tmp_path
):
    root = _make_library(tmp_path, 13)
    ctl = _make_controller(qt_app, tmp_path, root, detector=_FakeDetector())
    ctl.setSuggestionsEnabled(False)
    ctl._scan_should_pause = lambda: True
    processed = []
    ctl._detect = lambda path, **_kwargs: processed.append(path.name) or ()
    finished = threading.Event()
    result = []
    ctl.scanFinished.connect(
        lambda found, scanned: (result.append((found, scanned)), finished.set())
    )

    ctl.scanNewFaces()
    completed = var_feltetelre(qt_app, finished.is_set, 2.0)
    if not completed:
        ctl.cancelScan()
    assert ctl.waitForBackgroundWorkers(5.0)

    assert completed, "a 13 képes függő sor folyamatos bevitel mellett sem haladt"
    assert len(processed) == 13
    assert result == [(0, 13)]
    with open_index(tmp_path / "index.db") as conn:
        checked = conn.execute("SELECT COUNT(*) FROM face_scan").fetchone()[0]
    assert checked == 13


def test_unchanged_second_scan_skips_decode_and_logs_phase_times(
    qt_app, tmp_path, monkeypatch, caplog
):
    import picasapy.app.face_scan_controller_scan_mixin as scan_module

    root = _make_library(tmp_path, 2)
    # #6824: saját ini-beállítás; az alapértelmezett QSettings Windowson a
    # közös registry, és a CI-ban ott bekapcsolt javaslat elindította az
    # arcbeágyazó szálat, amely ugyanazokat a fájlokat dekódolta.
    settings = QSettings(str(tmp_path / "beallitas.ini"), QSettings.Format.IniFormat)
    ctl = _make_controller(
        qt_app, tmp_path, root, detector=_FakeDetector(), settings=settings
    )
    ctl.setSuggestionsEnabled(False)
    decoded = []
    original_decode = scan_module.dekodolj_forrast

    # #6824: Windowson ingadozva 4 dekódolás jött 2 helyett, Linuxon nem
    # reprodukálható. Bukáskor a szál neve és a hívó függvények is látszanak,
    # hogy a következő windowsos bukás megnevezze a második dekódoló utat.
    def counted_decode(*args, **kwargs):
        hivok = "<".join(
            frame.name for frame in traceback.extract_stack(limit=6)[:-1][::-1]
        )
        szal = threading.current_thread().name
        # Csak a keresés dekódolását számoljuk: a teszt a második keresés
        # kihagyását méri, nem az arcbeágyazást.
        if szal == "picasapy-face-scan":
            decoded.append((args[0], szal, hivok))
        return original_decode(*args, **kwargs)

    monkeypatch.setattr(scan_module, "dekodolj_forrast", counted_decode)
    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)
    assert len(decoded) == 2, f"dekódolások (fájl, szál, hívók): {decoded}"
    decoded.clear()

    with caplog.at_level(logging.INFO):
        _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)

    assert decoded == []
    assert any("arckeres fázisidők" in record.getMessage() for record in caplog.records)
