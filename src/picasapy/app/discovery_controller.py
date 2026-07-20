"""DiscoveryController: meglévő Picasa-telepítés felismerése és átvétele
(#146) — QML-híd a `scanner/discovery.py` felderítő API-jához (#199).

Szándékosan ÖNÁLLÓ QObject, NEM az `AppController` mixinje (ld. a
`fileops_controller.py` mintáját): a `controller.py`/`Main.qml` forró fájlok
(CONTRIBUTING.md) csak a végső bekötést kapják — a felderítés/átvétel logika
itt, tőlük függetlenül fejleszthető és tesztelhető.

A felderítés (`discover_installations`) és a javaslat-számítás
(`propose_watched_folders`) HÁTTÉRSZÁLON fut: NAS-tallózás vagy sok
Wine-profil vizsgálata lassú lehet, ez nem blokkolhatja a UI-szálat (a
mintát a `LibraryMixin` háttér-szinkronja adja: worker-szálból emittált
jelzés, amit a Qt automatikusan a GUI-szálra sorol)."""

from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.pmpimport.remap import PathRemapper
from picasapy.scanner import discover_installations, propose_watched_folders

# Wine alapértelmezett meghajtó-leképezése: a Z: meghajtó a teljes helyi
# fájlrendszer-gyökeret (/) tükrözi — ez a leggyakoribb eset, amikor a
# Picasa Wine alatt fut UGYANAZON a gépen, és a figyelt mappák valójában már
# helyi (Linux) útvonalak, csak Z:\ előtaggal. Más eredetű (pl. NAS-ra
# másolt, más gépről származó) telepítéseknél ez az alapértelmezés nem fog
# illeszkedni — ott a dialógus kézi tallózás gombja a tartalék út.
_DEFAULT_REMAP = PathRemapper.from_dict({"Z:\\": "/"})


class DiscoveryController(QObject):
    """A `PicasaImportDialog.qml` háttér-hídja: felderítés + átvétel."""

    # (javasolt mappák — str lista, felismert telepítések száma)
    discoveryFinished = Signal(list, int)
    # a Mappakezelő „Picasa-mappák átvétele..." gombja kéri a dialógus
    # megnyitását — a PicasaImportDialog.qml erre iratkozik fel. A két
    # dialógus a Main.qml-ben egymástól függetlenül él (forró fájl — csak a
    # példányosításuk kerül oda), ez a globális kontextus-jelzés köti össze
    # őket, ugyanúgy, ahogy a `controller`/`fileOpsController` is elérhető
    # bármelyik QML-fájlból.
    dialogRequested = Signal()

    def __init__(
        self,
        add_folder: Callable[[str], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._add_folder = add_folder

    @Slot()
    def openImportDialog(self) -> None:
        """A Mappakezelő gombja hívja: jelzi a PicasaImportDialog-nak, hogy
        nyíljon meg és induljon újra a felderítés."""
        self.dialogRequested.emit()

    @Slot()
    def discoverPicasa(self) -> None:
        """Meglévő telepítések + javasolt mappák felderítése HÁTTÉRSZÁLON.

        Az eredményt a `discoveryFinished` jelzi: a javasolt mappák
        (útvonal-string-ek, duplikátum-mentesen) és a felismert telepítések
        száma (a dialógus ebből dönti el, mutasson-e „nem találtunk
        semmit" üzenetet). Tisztán olvasó — semmit nem ír, ismételt hívása
        mindig a jelenlegi állapotot adja (7. rögzített döntés)."""

        def worker() -> None:
            installations = discover_installations()
            proposed: list[str] = []
            seen: set[str] = set()
            for installation in installations:
                for path in propose_watched_folders(installation, _DEFAULT_REMAP):
                    text = str(path)
                    if text not in seen:
                        seen.add(text)
                        proposed.append(text)
            self.discoveryFinished.emit(proposed, len(installations))

        threading.Thread(target=worker, daemon=True).start()

    @Slot(list)
    def adoptWatchedFolders(self, paths: list) -> None:
        """A kijelölt mappák hozzáadása a figyelt gyökerekhez — a meglévő
        `addWatchedFolder` úton (ismételhetően; a duplikátum-szűrés ott
        történik, path alapján, ld. LibraryMixin.addWatchedFolder)."""
        for path in paths:
            text = str(path)
            if text:
                self._add_folder(text)
