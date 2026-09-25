"""#3576 — a verziószám buboréksúgójának forrásszövege angol.

A projektben a `qsTr` forrásszövege angol, a magyar a `.ts`-ből jön. A
verziószám súgója (`MainToolbar.qml`) magyar forrással fordult, ezért
minden más nyelvű felületen is magyarul látszott.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_APP = Path(picasapy.app.__file__).parent
_FORRAS = "View releases on GitHub"
_MAGYAR = "Kiadások megtekintése a GitHubon"


def test_a_forras_angol():
    qml = (_APP / "qml" / "PicasaPy" / "MainToolbar.qml").read_text(encoding="utf-8")

    assert f'qsTr("{_FORRAS}")' in qml
    assert f'qsTr("{_MAGYAR}")' not in qml


def test_a_magyar_felulet_valtozatlan(qt_app):
    from PySide6.QtCore import QCoreApplication, QTranslator

    forditas = QTranslator()
    assert forditas.load(str(_APP / "i18n" / "picasapy_hu.qm"))
    QCoreApplication.installTranslator(forditas)
    try:
        assert QCoreApplication.translate("MainToolbar", _FORRAS) == _MAGYAR
    finally:
        QCoreApplication.removeTranslator(forditas)
