"""StartupStatus egységtesztek (#189): a splash Python-oldali állapot-hídja.

Property-k (statusText, ready, busy), a `report`/`finish` szemantika és a
jelzés-emittálás (nincs fölösleges emit, idempotens finish) ellenőrzése.
"""

from picasapy.app.startup_status import StartupStatus


def _count_signal(obj_signal) -> list:
    """Egy jelzésre feliratkozó számláló-lista (append minden emitkor)."""
    hits: list = []
    obj_signal.connect(lambda *_: hits.append(1))
    return hits


class TestDefaults:
    def test_starts_busy_with_optional_text(self, qt_app):
        status = StartupStatus("Indulás…")
        assert status.property("statusText") == "Indulás…"
        assert status.property("ready") is False
        assert status.property("busy") is True

    def test_empty_default_text(self, qt_app):
        status = StartupStatus()
        assert status.property("statusText") == ""
        assert status.property("busy") is True


class TestReport:
    def test_report_updates_text_and_emits(self, qt_app):
        status = StartupStatus()
        hits = _count_signal(status.statusTextChanged)
        status.report("Mappák beolvasása…")
        assert status.property("statusText") == "Mappák beolvasása…"
        assert len(hits) == 1

    def test_report_same_text_does_not_emit(self, qt_app):
        status = StartupStatus("azonos")
        hits = _count_signal(status.statusTextChanged)
        status.report("azonos")
        assert hits == []

    def test_report_none_becomes_empty(self, qt_app):
        status = StartupStatus("volt")
        status.report(None)
        assert status.property("statusText") == ""


class TestFinish:
    def test_finish_sets_ready_and_clears_text(self, qt_app):
        status = StartupStatus("Kész mindjárt…")
        ready_hits = _count_signal(status.readyChanged)
        text_hits = _count_signal(status.statusTextChanged)
        status.finish()
        assert status.property("ready") is True
        assert status.property("busy") is False
        assert status.property("statusText") == ""
        assert len(ready_hits) == 1
        assert len(text_hits) == 1  # a nem-üres szöveg üresre váltása

    def test_finish_is_idempotent(self, qt_app):
        status = StartupStatus()
        status.finish()
        ready_hits = _count_signal(status.readyChanged)
        status.finish()
        assert ready_hits == []
        assert status.property("ready") is True

    def test_finish_without_text_does_not_emit_text_change(self, qt_app):
        status = StartupStatus()  # üres szöveg
        text_hits = _count_signal(status.statusTextChanged)
        status.finish()
        assert text_hits == []


class TestRequiresConfirmation:
    """#243: a megerősítés-kapcsoló a hídon utazik a QML felé."""

    def test_default_is_false(self):
        from picasapy.app.startup_status import StartupStatus

        assert StartupStatus().property("requiresConfirmation") is False

    def test_true_when_requested(self):
        from picasapy.app.startup_status import StartupStatus

        status = StartupStatus(requires_confirmation=True)
        assert status.property("requiresConfirmation") is True
