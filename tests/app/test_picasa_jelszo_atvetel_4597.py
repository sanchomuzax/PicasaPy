"""#4597 — a Picasában beállított rejtett-jelszó átvétele az importkor.

A db3 `catdata` `Hidden Folders` sorának `info` értéke (32 jegyű hex MD5) a
rejtett-jelszó lesz, DE csak ha nálunk még nincs — a meglévőt az átvétel nem
írja felül. A jelzés háttérszálból érkezik; az átvétel a fő szálon fut.
"""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Qt

from picasapy.app.picasa_import_controller import PicasaImportController
from picasapy.pmpimport.db3_atvetel import AtvetelJelentes
from picasapy.scanner.discovery import PicasaInstallation

_MD5 = "5f4dcc3b5aa765d61d8327deb882cf99"


def _import_vezerlo(db3: Path, jelszo_olvaso=lambda _db3: _MD5) -> PicasaImportController:
    return PicasaImportController(
        felderito=lambda: (
            PicasaInstallation(
                label="próba",
                picasa2_dir=db3,
                picasa2albums_dir=None,
                watched_folders_file=None,
            ),
        ),
        olvaso=lambda db3_dir, remapper: (),
        atvevo=lambda rek, *, backup=True: AtvetelJelentes(),
        jelszo_olvaso=jelszo_olvaso,
    )


def _lefuttat(qt_app, vezerlo) -> None:
    vezerlo.startImport()
    assert vezerlo.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()
    qt_app.processEvents()


def test_a_picasas_jelszo_lenyomata_atvetelre_kerul_a_fo_szalon(
    qml_app, qt_app, tmp_path
):
    _window, controller, *_ = qml_app
    controller.clearHiddenPassword()
    szalak: list[int] = []
    eredeti = controller.adoptHiddenPasswordHash

    def figyelt(lenyomat: str) -> None:
        szalak.append(threading.get_ident())
        eredeti(lenyomat)

    vezerlo = _import_vezerlo(tmp_path)
    vezerlo.hiddenPasswordFound.connect(figyelt, Qt.ConnectionType.QueuedConnection)
    _lefuttat(qt_app, vezerlo)
    vezerlo.waitForBackgroundWorkers(5.0)

    assert controller.hiddenPasswordHash == _MD5
    assert szalak == [threading.get_ident()], "az átvétel nem a fő szálon futott"
    assert controller.unlockHidden("password") is True
    controller.clearHiddenPassword("password")


def test_meglevo_jelszot_az_atvetel_nem_irja_felul(qml_app, qt_app, tmp_path):
    _window, controller, *_ = qml_app
    controller.setHiddenPassword("sajat", False)
    sajat = controller.hiddenPasswordHash
    vezerlo = _import_vezerlo(tmp_path)
    vezerlo.hiddenPasswordFound.connect(
        controller.adoptHiddenPasswordHash, Qt.ConnectionType.QueuedConnection
    )
    _lefuttat(qt_app, vezerlo)
    assert controller.hiddenPasswordHash == sajat
    controller.clearHiddenPassword("sajat")


def test_jelszo_nelkuli_db3_nem_kuld_jelzest(qt_app, tmp_path):
    vezerlo = PicasaImportController(
        felderito=lambda: (
            PicasaInstallation(
                label="próba",
                picasa2_dir=tmp_path,
                picasa2albums_dir=None,
                watched_folders_file=None,
            ),
        ),
        olvaso=lambda db3_dir, remapper: (),
        atvevo=lambda rek, *, backup=True: AtvetelJelentes(),
        jelszo_olvaso=lambda db3_dir: None,
    )
    jelzesek: list[str] = []
    vezerlo.hiddenPasswordFound.connect(jelzesek.append)
    _lefuttat(qt_app, vezerlo)
    assert jelzesek == []


def test_hibas_jelszoolvaso_nem_allitja_meg_az_importot(qt_app, tmp_path):
    def hiba(_db3):
        raise RuntimeError("sérült catdata")

    vezerlo = _import_vezerlo(tmp_path, hiba)
    kesz: list[tuple] = []
    hibak: list[str] = []
    vezerlo.importFinished.connect(lambda *a: kesz.append(a))
    vezerlo.importFailed.connect(hibak.append)
    _lefuttat(qt_app, vezerlo)
    assert len(kesz) == 1
    assert hibak == []
