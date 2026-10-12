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

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from picasapy.pmpimport.db3_atvetel import (
    AtvetelJelentes,
    rekordokat_atvesz,
    videodatumokat_atvesz,
)
from picasapy.pmpimport.importer import iter_photo_records
from picasapy.pmpimport.remap import PathRemapper
from picasapy.scanner import discover_installations

from .index_writer_queue import IndexWriterQueue
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)

#: Ugyanaz az alapértelmezett leképezés, amit a `DiscoveryController` használ:
#: a Wine `Z:\` meghajtója a helyi gyökeret tükrözi. Más eredetű (NAS-ra
#: másolt) telepítésnél ez nem illeszkedik — akkor a rekordok kimaradnak, és
#: a jelentés nullát mond, nem hazudik sikert.
_ALAP_REMAP = PathRemapper.from_dict({"Z:\\": "/"})
_MANUAL_SOURCE_REQUIRED = "picasapy-manual-source-required"
_MANUAL_MAPPING_REQUIRED = "picasapy-manual-mapping-required"


class PicasaImportController(BackgroundWorkerMixin, QObject):
    """`Eszközök ▸ Import a Picasából…` — a db3 adatainak átvétele."""

    #: (mappák, kulcsszó, hely, arc, kihagyott, videódátum, videódátum-hiba) — a felhasználónak
    #: szóló számok. A `kihagyott` azt mondja meg, hány fotón volt db3-adat, de az
    #: ini-ben már állt érték: ott SZÁNDÉKOSAN nem nyúltunk hozzá.
    importFinished = Signal(int, int, int, int, int, int, int)
    #: #4591: a videók dátuma az indexbe került — a rács/mappalista frissítendő
    datesApplied = Signal()
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
        index_path: Path | None = None,
        videodatum_atvevo: Callable[..., AtvetelJelentes] | None = None,
        writer_queue: IndexWriterQueue | None = None,
    ) -> None:
        super().__init__(parent)
        #: #4591: az index útvonala — a videók módosított dátuma ide megy
        self._index_path = index_path
        self._videodatum_atvevo = videodatum_atvevo or videodatumokat_atvesz
        #: az index írója — ha van, az index-lépés a soron fut (egyetlen
        #: íróként, mint a tömörítés), különben a saját háttérszálon
        self._writer_queue = writer_queue
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

    @Slot(QUrl, result=str)
    def localPathFromUrl(self, url: QUrl) -> str:
        """A mappaválasztó URL-jéből helyi útvonalat ad a QML-mezőnek."""
        return url.toLocalFile()

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
        self._start_import(db3_konyvtar=None, remapper=self._remapper)

    @Slot(str, str, str)
    def startManualImport(
        self, db3_konyvtar: str, meghajto_elotag: str, helyi_elotag: str
    ) -> None:
        """Kézzel választott Picasa2 mappa importja egyedi leképezéssel."""
        konyvtar = db3_konyvtar.strip()
        forras = meghajto_elotag.strip()
        cel = helyi_elotag.strip()
        if not konyvtar:
            self.importFailed.emit(_MANUAL_SOURCE_REQUIRED)
            return
        if not forras or not cel:
            self.importFailed.emit(_MANUAL_MAPPING_REQUIRED)
            return
        self._start_import(
            db3_konyvtar=Path(konyvtar),
            remapper=PathRemapper.from_dict({forras: cel}),
        )

    def _befejez(self, jelentes: AtvetelJelentes) -> None:
        self.importFinished.emit(
            jelentes.mappak,
            jelentes.kulcsszo,
            jelentes.hely,
            jelentes.arc,
            jelentes.kihagyott,
            jelentes.videodatum,
            jelentes.videodatum_hiba,
        )
        if jelentes.videodatum:
            self.datesApplied.emit()

    def _start_import(
        self, *, db3_konyvtar: Path | None, remapper: PathRemapper
    ) -> None:
        self._set_running(True)

        def worker() -> None:
            lezart = False
            try:
                konyvtarak = (
                    (db3_konyvtar,)
                    if db3_konyvtar is not None
                    else self._db3_konyvtarak()
                )
                if not konyvtarak:
                    self.noInstallationFound.emit()
                    return
                osszes = AtvetelJelentes()
                osszes_rekord: list = []
                for db3 in konyvtarak:
                    rekordok = tuple(self._olvaso(db3, remapper))
                    osszes_rekord.extend(rekordok)
                    osszes = osszes + self._atvevo(rekordok)
                if self._index_path is None:
                    self._befejez(osszes)
                    return
                # #4591: az index-lépés az ini-átvétel UTÁN, az index
                # írósorán (ha van): a videódátum hibája az ini-t nem viszi el

                def index_lepes() -> None:
                    try:
                        jelentes = osszes + self._videodatum_atvevo(
                            osszes_rekord, self._index_path
                        )
                        self._befejez(jelentes)
                    except Exception as hiba:  # a felhasználónak szól
                        _log.exception("A Picasa-import elakadt")
                        self.importFailed.emit(str(hiba))
                    finally:
                        self._set_running(False)

                if self._writer_queue is None:
                    index_lepes()
                else:
                    self._writer_queue.submit(
                        index_lepes, name="picasapy-db3-import-index"
                    )
                lezart = True  # a futás jelzőjét innentől az index_lepes zárja
            except Exception as hiba:  # a felhasználónak szól, nem elnyeljük
                _log.exception("A Picasa-import elakadt")
                self.importFailed.emit(str(hiba))
            finally:
                if not lezart:
                    self._set_running(False)

        self._start_background(worker, name="picasapy-db3-import")
