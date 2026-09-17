"""A `StartupRelocateWindow.qml` — a `moving_database.fen` megfelelője (#3214).

Ez az ablak CSAK a ritka költözési úton jelenik meg (a KÖVETKEZŐ induláskor,
ha a „Move Database" párbeszéd előjegyzést hagyott), tehát a szokásos
felület-tesztek soha nem érintik: ha elromlik a QML-je, semmi más nem venné
észre.

⚠️ Miért itt, a `qml_functional` alatt: a próba `QQuickWindow`-t tölt be,
ahhoz pedig **`QGuiApplication`** kell. A `tests/app` gyökerében futó
társai közül a `test_i18n_completeness.py` egy sima `QCoreApplication`-t hoz
létre, és a közös `qt_app` fixture azt adja tovább — ilyenkor az ablak
betöltése `Fatal Python error: Aborted`-dal áll meg. Mérve: a fájl
önmagában zöld volt, a kettő EGYÜTT omlott össze (ld. a „Új tesztfájlokat
EGYÜTT futtasd" tanulságot).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import picasapy.app
from picasapy.app.startup_relocate import KoltozesHid
from picasapy.index.relocate import RelocationProgress


class TestAHaladasjelzoAblak:
    """A `StartupRelocateWindow.qml` (`moving_database.fen` megfelelője).

    Ez az ablak CSAK a ritka költözési úton jelenik meg, tehát a szokásos
    felület-tesztek soha nem érintik — ha elromlik a QML-je, azt semmi más
    nem venné észre."""

    def test_az_ablak_betoltheto_es_a_hidat_olvassa(self, qt_app, tmp_path):
        # ⚠️ NEM környezetfüggő kibúvó: a CI (és a `scripts/run_tests.py`)
        # fájlonként külön folyamatot indít, ott ez a feltétel MINDIG
        # teljesül, tehát a próba mindig lefut. A kapu csak a kézi,
        # több fájlt egy folyamatba fűző futásra való, ahol egy társ-fájl
        # (`test_i18n_completeness.py`) sima `QCoreApplication`-t hozott
        # létre — ablakot azzal betölteni azonnali `Aborted`.
        if not isinstance(QGuiApplication.instance(), QGuiApplication):
            pytest.skip(
                "ebben a folyamatban nem QGuiApplication fut — "
                "ablakot betölteni összeomlás lenne"
            )

        qml_dir = Path(picasapy.app.__file__).parent / "qml"
        hid = KoltozesHid(tmp_path / "uj-hely")
        engine = QQmlApplicationEngine()
        try:
            engine.addImportPath(str(qml_dir))
            engine.rootContext().setContextProperty("koltozes", hid)
            engine.load(str(qml_dir / "StartupRelocateWindow.qml"))

            gyokerek = engine.rootObjects()
            assert gyokerek, "a haladásjelző ablak nem töltődött be"
            ablak = gyokerek[0]
            felirat = ablak.findChild(QObject, "startupRelocateTargetText")
            assert felirat is not None
            assert str(tmp_path / "uj-hely") in felirat.property("text")

            # a sáv a hídból kapja a hosszát — a haladás LÁTSZIK, nem csak
            # mérve van
            sav = ablak.findChild(QObject, "startupRelocateProgressFill")
            assert float(sav.property("width")) == 0.0
            hid.jelentsd(RelocationProgress(phase="database", done=1, total=2))
            qt_app.processEvents()
            assert float(sav.property("width")) > 0.0
        finally:
            # ⚠️ A motort ITT kell elengedni: ha a teszt végéig él, a
            # Python-kilépéskori bontás `Fatal Python error: Aborted`-ot ad
            # (mérve: a fájl önmagában zöld volt, más fájlokkal együtt
            # összeomlott — #1260 osztálya).
            for gyoker in engine.rootObjects():
                gyoker.close()
            engine.clearComponentCache()
            engine.deleteLater()
            qt_app.processEvents()
