"""#3830: a diavetítés forgatás-gombja — GYORS, egymást követő kattintás.

A `.picasa.ini`-írás és a hozzá tartozó index-frissítés háttérszálon fut
(`PhotoOpsMixin._run_photo_write`, #141); a modell (`self._photos`) csak a
befejezéskor frissül. A `_apply_rotate` a KÖVETKEZŐ lépésszámot eddig a
MODELLBŐL olvasta ki minden hívásnál — egy második forgatás-kattintás, ami
az első írás befejezése ELŐTT érkezik, ezért a RÉGI (még nem frissült)
lépésszámból számolt, és a kattintás elveszett.

Ez a fájl a gomb SAJÁT `clicked` jelzésén át reprodukálja a jelenséget (a
`test_csillag_belepesi_pontok_1438.py` mintája — nem a Python-metódust
hívjuk, mert egy elrontott kötés csak így tudna pirosra váltani; a nyers
képernyő-kattintás a diavetítés önmagát elrejtő vezérlősávjának
lebegés-időzítőjétől függne, ami a valódi versenyhelyzet szempontjából
lényegtelen bonyodalom). Az ini-írást egy `threading.Event`-tel tartjuk
fel (ugyanaz a minta, mint a `test_csillag_lanc_1438.py`-ban), hogy a
második kattintás GARANTÁLTAN az első írás befejeződése ELŐTT érkezzen —
nem egy időzítéstől függő ablakra hagyatkozva."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.qt_wait import varj_feltetelre


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _start_slideshow(window, qt_app, index: int):
    QMetaObject.invokeMethod(
        window, "startSlideshow", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
    )
    qt_app.processEvents()
    return _child(window, "slideshowView")


def _click(obj) -> None:
    """Kattintás megfelelője: a vezérlő saját `clicked` jelzése."""
    QMetaObject.invokeMethod(obj, "clicked", Qt.ConnectionType.DirectConnection)


def _ini_text(controller) -> str:
    folder = Path(controller.photos.photos[0].folder_path)
    ini = folder / ".picasa.ini"
    return ini.read_text(encoding="utf-8") if ini.exists() else ""


class TestDiavetitesGyorsForgatas:
    def test_ket_gyors_forgatas_egyik_sem_veszik_el(
        self, qml_app, qt_app, monkeypatch
    ) -> None:
        from picasapy.app import photo_ops_controller as ops

        window, controller, _engine = qml_app
        show = _start_slideshow(window, qt_app, 0)
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0
        assert controller.photos.rotateAt(0) == 0

        eredeti_update_document = ops.update_document
        engedd_tovabb = threading.Event()

        def feltartott(*args, **kwargs):
            # #3830: a valódi NAS-írás/vírusirtós Windows-CI lassúságát
            # szimuláljuk — a második kattintás GARANTÁLTAN az első írás
            # befejezése ELŐTT ér célba, nem egy időzítésre bízva.
            engedd_tovabb.wait(30.0)
            return eredeti_update_document(*args, **kwargs)

        monkeypatch.setattr(ops, "update_document", feltartott)

        gomb = _child(window, "slideshowRotateRightButton")
        try:
            _click(gomb)   # 1. kattintás: 0 -> 1, ELAKAD az ini-írásban
            qt_app.processEvents()
            _click(gomb)   # 2. kattintás: a modell MÉG 0-t mutat
            qt_app.processEvents()
        finally:
            engedd_tovabb.set()

        assert varj_feltetelre(
            qt_app, lambda: controller.photos.rotateAt(0) == 2, 15.0
        ), (
            "két gyors '+1' forgatás után a lépésszámnak 2-nek kell "
            "lennie — ha 1, a második kattintás elveszett (#3830)"
        )
        assert "rotate(2)" in _ini_text(controller).split("[a.jpg]")[1]

        QMetaObject.invokeMethod(show, "stop", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
