"""A törölt kép indexképe akkor is eltűnjön, ha épp fut egy szinkron (#1181).

## A tulajdonos jelentése (v0.8.29)

> „Az index képre állva »Delete« billentyűt nyomva törlést kérve (kukába)
> lemegy a művelet látszólag, de az indexkép ott marad. Nem frissül a feed?"

## A mérés

A törlés lánca ép: `deleteConfirmDialog` → `fileOpsController.deletePhoto`
→ `photoDeleted` → `wire_fileops.refresh` → `resyncFolder`. Nyugalmi
állapotban végig is fut — a fájl eltűnik a lemezről ÉS a sor a rácsból
(mérve, Linux, offscreen).

A `resyncFolder` viszont a `_on_folders_dirty`-be fut, aminek az ELSŐ sora:

```python
if self._sync_running:
    return  # a futó teljes szinkron úgyis lefedi
```

Ez a feltevés **nem igaz**: ha a futó szinkron az adott mappán MÁR
túlment, a törlést senki nem vezeti át — a sor a következő periodikus
(ötperces) rescanig ottmarad. Nagy könyvtárnál (a bejelentő NAS-a) a
szinkron sokat fut, ezért ütközik gyakran.

Az őr ezért a **függőben maradt frissítést** méri: ha a törlés szinkron
közben történt, a szinkron végén be kell hoznia a lemaradást.
"""

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


def _varj(controller, qt_app, korok=100):
    for _ in range(korok):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _torolj(window, controller, qt_app, ut):
    """Törlés a VALÓDI úton: a megerősítő párbeszéd `confirmed` jelzésén át."""
    dialogus = window.findChild(QObject, "deleteConfirmDialog")
    assert dialogus is not None, "deleteConfirmDialog nem található"
    QMetaObject.invokeMethod(
        dialogus,
        "openFor",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", [ut]),
    )
    qt_app.processEvents()
    assert dialogus.property("trashAvailable"), (
        "a teszt-környezetben nincs lomtár — a mérés nem érvényes"
    )
    QMetaObject.invokeMethod(
        dialogus, "confirmed", Qt.ConnectionType.DirectConnection
    )
    _varj(controller, qt_app)


class TestTorlesFrissites:
    def test_nyugalomban_azonnal_eltunik(self, qml_app, qt_app):
        """Megőrző: a jelenleg is működő eset ne romoljon el."""
        window, controller, _ = qml_app
        ut = controller.photos.filePathAt(0)
        elotte = controller.photos.rowCount()

        _torolj(window, controller, qt_app, ut)

        assert not Path(ut).exists(), "a fájl nem törlődött"
        assert controller.photos.rowCount() == elotte - 1

    def test_futo_szinkron_kozben_torolve_a_szinkron_vegen_frissul(
        self, qml_app, qt_app
    ):
        """⚠️ A jegy magja: eddig a frissítés NÉMÁN elveszett."""
        window, controller, _ = qml_app
        ut = controller.photos.filePathAt(0)
        elotte = controller.photos.rowCount()

        # a periodikus/indulási szinkron fut, amikor a felhasználó töröl
        controller._sync_running = True
        _torolj(window, controller, qt_app, ut)
        assert not Path(ut).exists(), "a fájl nem törlődött"

        # a szinkron befejeződik — innentől a lemaradást be kell hozni
        controller._sync_running = False
        controller.syncFinished.emit()
        _varj(controller, qt_app)

        assert controller.photos.rowCount() == elotte - 1, (
            "a törölt kép sora ottmaradt: a szinkron alatt kért frissítés "
            "elveszett, és a szinkron vége sem hozta be"
        )
