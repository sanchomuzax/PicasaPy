"""PicasaImportController: a db3-adatok átvételének felhasználói kiváltója
(#3132) — QML-híd a `pmpimport.db3_atvetel` magjához.

## Miért külön vezérlő

A MAG a #2336/#3002/#3184 óta kész és tesztelt: a db3 kulcsszavai, helyadata
és arcai `.picasa.ini`-be írhatók, mappánként egyetlen írásban, és ahol már
áll adat, ott hozzá sem nyúlunk („A" szabály). Ami hiányzott, az a BELÉPÉSI
PONT: a `rekordokat_atvesz`-t semmi nem hívta a `src/` alól, tehát az adat a
felhasználónál nem mozdult.

## A HELYE a tulajdonos döntése volt (2026-09-18)

Három lehetőséget kapott — menüpont / első indításkor magától / mappánként
ajánlva —, és az **A**-t választotta:

> `A menüpont (Eszközök ▸ Import a Picasából…)`

Ez azért is a helyes irány, mert az átvétel a fotók mellé ír
(`.picasa.ini`), tehát maradandó változás a gyűjteményben — ilyet kérésre
indítunk, nem magától. Az „első indításkor magától" ág ezért NEM létezik
ebben a vezérlőben; ha valaha kell, az külön jegy lesz.

Szándékosan ÖNÁLLÓ QObject (a `DiscoveryController` mintájára), nem az
`AppController` mixinje: a `controller.py`/`Main.qml` forró fájlok csak a
bekötést kapják.

A munka HÁTTÉRSZÁLON fut (`BackgroundWorkerMixin`): a db3 beolvasása és a
mappánkénti ini-írás lassú, a UI-szálat nem foglalhatja.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from picasapy.pmpimport.db3_atvetel import AtvetelJelentes, rekordokat_atvesz
from picasapy.pmpimport.importer import iter_photo_records
from picasapy.pmpimport.remap import PathRemapper
from picasapy.scanner import discover_installations

from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)

#: Ugyanaz az alapértelmezett leképezés, amit a `DiscoveryController` használ:
#: a Wine `Z:\` meghajtója a helyi gyökeret tükrözi. Más eredetű (NAS-ra
#: másolt) telepítésnél ez nem illeszkedik — akkor a rekordok kimaradnak, és
#: a jelentés nullát mond, nem hazudik sikert.
_ALAP_REMAP = PathRemapper.from_dict({"Z:\\": "/"})


class PicasaImportController(BackgroundWorkerMixin, QObject):
    """`Eszközök ▸ Import a Picasából…` — a db3 adatainak átvétele."""

    #: (mappák, kulcsszó, hely, arc, kihagyott) — a felhasználónak szóló
    #: számok. A `kihagyott` azt mondja meg, hány fotón volt db3-adat, de az
    #: ini-ben már állt érték: ott SZÁNDÉKOSAN nem nyúltunk hozzá.
    importFinished = Signal(int, int, int, int, int)
    #: a db3 olvasása vagy az írás hibára futott — a szöveg a felhasználóé
    importFailed = Signal(str)
    #: nincs mit átvenni: nem találtunk db3-könyvtárat. ⚠️ Ez NEM hiba —
    #: külön jelzés, mert a felületnek mást kell mondania rá.
    noInstallationFound = Signal()
    runningChanged = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        felderito: Callable[[], Iterable] | None = None,
        olvaso: Callable[..., Iterable] | None = None,
        atvevo: Callable[..., AtvetelJelentes] | None = None,
        remapper: PathRemapper | None = None,
    ) -> None:
        super().__init__(parent)
        self._felderito = felderito or discover_installations
        self._olvaso = olvaso or iter_photo_records
        self._atvevo = atvevo or rekordokat_atvesz
        self._remapper = remapper or _ALAP_REMAP
        self._running = False

    def _set_running(self, ertek: bool) -> None:
        if self._running != ertek:
            self._running = ertek
            self.runningChanged.emit()

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        """Fut-e épp az átvétel — a párbeszéd ebből tudja, mit mutasson."""
        return self._running

    def _db3_konyvtarak(self) -> tuple[Path, ...]:
        """A felismert telepítések db3-könyvtárai, sorrendhelyesen.

        A `Picasa2Albums` önmagában NEM elég: a fotó-rekordok a `Picasa2`
        könyvtárban élnek. Az ilyen telepítés ezért nem számít találatnak.
        """
        utak: list[Path] = []
        for telepites in self._felderito():
            db3 = getattr(telepites, "picasa2_dir", None)
            if db3 is not None:
                utak.append(Path(db3))
        return tuple(utak)

    @Slot()
    def startImport(self) -> None:
        """Az átvétel elindítása — a menüpont ezt hívja.

        Ismételhető: a mag idempotens (7. rögzített döntés), és ami már
        bent van, azt nem írja felül. Aki később új mappákat vesz fel,
        nyugodtan lefuttathatja újra.
        """
        self._set_running(True)

        def worker() -> None:
            try:
                konyvtarak = self._db3_konyvtarak()
                if not konyvtarak:
                    self.noInstallationFound.emit()
                    return
                osszes = AtvetelJelentes()
                for db3 in konyvtarak:
                    rekordok = tuple(self._olvaso(db3, self._remapper))
                    osszes = osszes + self._atvevo(rekordok)
                self.importFinished.emit(
                    osszes.mappak,
                    osszes.kulcsszo,
                    osszes.hely,
                    osszes.arc,
                    osszes.kihagyott,
                )
            except Exception as hiba:  # a felhasználónak szól, nem elnyeljük
                _log.exception("A Picasa-import elakadt")
                self.importFailed.emit(str(hiba))
            finally:
                self._set_running(False)

        self._start_background(worker, name="picasapy-db3-import")
