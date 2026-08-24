"""Újrahasznosítható, teljes életciklusú teszt-őrök (#1260).

A függvények generátor-fixture-ként használhatók. A `yield` előtti rész a
fixture felállítása előtt, a `finally` rész pedig a függő fixture-ek
lebontása után fut; így a modul-szintű `qml_app` setupja és teardownja sem
maradhat őrizetlenül.
"""

from __future__ import annotations

import pytest

from support.qml_warning_filter import is_qml_script_error
from support.valodi_mappa_or import VEDETT_MAPPAK, pillanatkep, valtozas_szovege


def qml_warning_guard():
    """QML-szkripthiba-őr a teljes függő fixture-életciklus körül."""
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    messages: list[str] = []

    def _handler(msg_type, context, message):
        if msg_type in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ) and is_qml_script_error(message):
            messages.append(message)

    previous = qInstallMessageHandler(_handler)
    try:
        yield messages
    finally:
        qInstallMessageHandler(previous)
        if messages:
            pytest.fail(
                "QML-szkripthiba jelent meg a fixture-életciklusban (#1260):\n"
                + "\n".join(messages)
            )


def user_folder_guard():
    """A valódi felhasználói mappák változását a teljes életcikluson őrzi."""
    before = {folder: pillanatkep(folder) for folder in VEDETT_MAPPAK}
    try:
        yield
    finally:
        for folder, old_state in before.items():
            message = valtozas_szovege(folder, old_state, pillanatkep(folder))
            if message:
                pytest.fail(message)
