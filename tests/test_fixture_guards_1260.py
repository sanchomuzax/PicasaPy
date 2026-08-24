"""A #1260 modul-fixture-őrök életciklusának állító tesztjei."""

from __future__ import annotations

import pytest
from PySide6.QtCore import qWarning

from support import fixture_guards


def test_qml_guard_elkapja_a_teardownban_kibocsatott_hibat() -> None:
    """A handler a `yield` utáni teardown-szakaszban is még aktív."""
    guard = fixture_guards.qml_warning_guard()
    messages = next(guard)
    qWarning("TypeError: modul-fixture teardown sentinel")

    with pytest.raises(pytest.fail.Exception, match="teardown sentinel"):
        next(guard)
    assert messages == ["TypeError: modul-fixture teardown sentinel"]


def test_mappaszenyezes_or_a_teljes_eletciklusban_aktiv(
    tmp_path, monkeypatch
) -> None:
    vedett = tmp_path / "vedett"
    vedett.mkdir()
    monkeypatch.setattr(fixture_guards, "VEDETT_MAPPAK", (vedett,))

    guard = fixture_guards.user_folder_guard()
    next(guard)
    (vedett / "modul-fixture-sentinel.txt").write_text("hiba", encoding="utf-8")

    with pytest.raises(pytest.fail.Exception, match="VALÓDI mappájába írt"):
        next(guard)
