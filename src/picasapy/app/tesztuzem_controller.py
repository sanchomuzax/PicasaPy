"""Tartós **tesztüzem** (#1654) — az AppController vezérlő-szelete.

A `perf_controller.py` (#211) mintája: a szelet a `Súgó` menüből
kapcsolható, és a `PerfMonitorMixin`-hez hasonlóan **kikapcsolt állapotban
semmit nem futtat**.

## Mit ad hozzá a #211-hez

A Teljesítmény-monitor csak MENETKÖZBEN kapcsolható be — mire a felhasználó
eléri a menüt, az indulás rég lezajlott. A tesztüzem ezzel szemben
**tartós**: `QSettings`-ben él, túléli a kilépést, és a **következő**
indulás mér, az első ezredmásodperctől (ld. `application._indulasi_idovonal`).

## Átadás — a FELHASZNÁLÓ választja meg a helyét (#2553)

`Súgó ▸ Napló elküldése` megnyitja a mentés-párbeszédet, időbélyeges
fájlnév-javaslattal, és a mentett útvonalat a vágólapra is felteszi. A
választott mappát megjegyezzük: a következő átadás már ott nyílik.
**Semmilyen hálózati feltöltés, külső szolgáltatás vagy hitelesítés nincs
benne** — sima fájlírás oda, ahova a felhasználó mutat.

⚠️ A #1654 még egy BEÉGETETT helyre másolt (`/mnt/nas`, Windowson
`//DS215j/lemez`), és a párbeszéd csak akkor jött elő, ha az nem volt
elérhető. Az a hely egyetlen gépre volt szabva, és MÉRVE (2026-09-06) a
fejlesztői gépről nem is látszott: onnan a megosztásnak csak egy MÁSIK
almappája van csatolva. A napló kiment — és senki nem érte el. A
kiinduló hely ma is lehet a megosztás, de már csak JAVASLATKÉNT.

## ⚠️ A fogantyúk (seam)

A közös mappa útvonala, a vágólap, az óra, a naplómappa és a Dokumentumok
mappa MODULSZINTŰ függvények — a teszt EZEKET cseréli. A `/mnt/nas` éles
családi adat: a tesztkészlet soha nem írhat oda.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QUrl, Signal, Slot

from picasapy.perf.logwriter import default_log_dir
from picasapy.perf.tesztuzem import (
    NAPLO_MAPPA_BEALLITAS_KULCS,
    TESZTUZEM_BEALLITAS_KULCS,
    kiindulo_naplo_mappa,
    legutobbi_indulasi_naplo,
    megosztas_elerheto,
    megosztas_gyokere,
    naplo_fajlneve,
    tesztuzem_bekapcsolva,
)

#: A bekapcsolás visszajelzése. A jegy kimondottan kéri, hogy a felület
#: mondja ki: a hatás a KÖVETKEZŐ indításnál látszik, és a mód bekapcsolva
#: marad. A felhasználó nem fejlesztő — a teendő lépésenként szerepel.
UZENET_BEKAPCSOLVA = (
    "Tesztüzem bekapcsolva. A naplózás a KÖVETKEZŐ indításnál kezdődik: "
    "lépj ki a PicasaPy-ból, és indítsd el újra. A mód bekapcsolva marad, "
    "amíg ki nem kapcsolod."
)

UZENET_KIKAPCSOLVA = (
    "Tesztüzem kikapcsolva. A következő indítás már nem készít naplót."
)

UZENET_NINCS_NAPLO = (
    "Még nincs indulási napló. A tesztüzem a KÖVETKEZŐ indítást naplózza: "
    "lépj ki a PicasaPy-ból, indítsd el újra, és utána küldd el a naplót."
)

#: #2553: a mentés-párbeszéd megnyitását kísérő sáv-üzenet. Nem hiba, hanem
#: a normál menet — a felhasználó választja meg, hova kerüljön a napló.
UZENET_VALASSZ_HELYET = "Válaszd ki, hova mentsük az indulási naplót."


def _argv() -> list[str]:
    """A processz parancssora — a teszt EZT cserélje (#1217 mintája).

    A `--tesztuzem`-mel indított futásban a menü is legyen pipálva és a
    „Napló elküldése" is látsszon: különben a felhasználó nem tudná átadni
    azt a naplót, amit a program épp az imént készített."""
    return list(sys.argv)


def _platform() -> str:
    """A futó platform (`sys.platform`) — cserélhető fogantyú (#1217)."""
    return sys.platform


def _most() -> datetime:
    """A jelen pillanat — cserélhető, hogy a fájlnév teszttel állítható."""
    return datetime.now()


def _naplo_mappa() -> Path:
    """A helyi naplómappa (`~/.cache/picasapy/perf/`) — cserélhető."""
    return default_log_dir()


def _megosztas_gyokere(
    gyoker: Path | None = None,
    *,
    ismount: Callable[[str], bool] = os.path.ismount,
) -> Path | None:
    """Az ELÉRHETŐ közös mappa gyökere, vagy `None`.

    ⚠️ Ez a produkciós útvonal EGYETLEN eldöntési helye, és szándékosan
    cserélhető: a `/mnt/nas` éles családi adat, a tesztkészlet nem írhat
    oda. A csatolás-ellenőrzésről ld. `perf/tesztuzem.megosztas_elerheto`."""
    gyoker = gyoker if gyoker is not None else megosztas_gyokere(_platform())
    return gyoker if megosztas_elerheto(gyoker, ismount=ismount) else None


def _dokumentumok() -> Path:
    """A rendszer Dokumentumok mappája — a mentés-párbeszéd VÉGSŐ
    kiinduló helye (#2553).

    Fogantyú (seam): a teszt ezt cseréli, hogy a valódi felhasználói
    mappára soha ne mutasson."""
    from PySide6.QtCore import QStandardPaths

    hely = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    return Path(hely) if hely else Path.home()


def _vagolapra(szoveg: str) -> None:
    """Az útvonal a vágólapra — így a felhasználónak nem kell begépelnie.

    Hibáját elnyeljük: a napló ATTÓL még átment, hogy a vágólap nem
    elérhető (pl. headless futás)."""
    try:
        from PySide6.QtGui import QGuiApplication

        vagolap = QGuiApplication.clipboard()
        if vagolap is not None:
            vagolap.setText(szoveg)
    except Exception:  # noqa: BLE001 - a vágólap sosem viheti el a műveletet
        pass


def _url_utvonala(cel: str) -> Path | None:
    """A QML `FileDialog` `file://…` URL-jéből (vagy sima útvonalból) `Path`."""
    if not cel:
        return None
    if cel.startswith("file:"):
        helyi = QUrl(cel).toLocalFile()
        return Path(helyi) if helyi else None
    return Path(cel)


class TesztuzemMixin:
    """`tesztuzemEnabled` tartós kapcsoló + egykattintásos naplóátadás."""

    tesztuzemChanged = Signal()
    #: Tájékoztatás a felhasználónak (a Main.qml borostyán sávja mutatja).
    tesztuzemUzenet = Signal(str)
    #: #2553: a felület nyissa meg a mentés-párbeszédet. Három adat megy
    #: vele: a sávban mutatandó üzenet, a kiinduló MAPPA (`file://…`
    #: URL-ként, ahogy a `FileDialog` várja) és a javasolt FÁJLNÉV.
    #:
    #: ⚠️ Ez MINDEN átadásnál elhangzik, nem csak hibánál — a #1654-ben a
    #: párbeszéd tartalék volt, és a beégetett cél miatt a napló olyan
    #: helyre ment, amit a fejlesztés nem ért el.
    tesztuzemMentesKert = Signal(str, str, str)

    def _init_tesztuzem(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        `__init__`-et — ez a konvenció a repóban).

        Kikapcsolt állapotban ez a KÉT olcsó olvasás minden, ami lefut:
        se szál, se időzítő, se fájlművelet."""
        self._tesztuzem = tesztuzem_bekapcsolva(self._get_settings()) or (
            "--tesztuzem" in _argv()
        )
        #: A „Mentés másként…" tartalékhoz eltett naplószöveg.
        self._tesztuzem_fuggo_szoveg = ""

    # -- QML-nek kitett állapot ---------------------------------------------

    @Property(bool, notify=tesztuzemChanged)
    def tesztuzemEnabled(self) -> bool:
        """Be van-e kapcsolva a tesztüzem.

        LÁTHATÓ állapot: a menüsáv jobb szélén figyelmeztető jelzés ül,
        amíg igaz — a felhasználó ne felejtse bekapcsolva észrevétlenül."""
        return self._tesztuzem

    # -- kapcsoló -------------------------------------------------------------

    @Slot()
    def toggleTesztuzem(self) -> None:
        self.setTesztuzemEnabled(not self._tesztuzem)

    @Slot(bool)
    def setTesztuzemEnabled(self, enabled: bool) -> None:
        """A kapcsoló átállítása — TARTÓSAN.

        A `sync()` nem elhagyható: enélkül a beállítás csak a Qt belső
        pufferében élne, és egy váratlan kilépés (vagy épp a mérendő,
        elszálló indulás) elnyelné — a felhasználó pedig hiába indítaná
        újra a programot."""
        enabled = bool(enabled)
        if enabled == self._tesztuzem:
            return
        self._tesztuzem = enabled
        settings = self._get_settings()
        settings.setValue(TESZTUZEM_BEALLITAS_KULCS, enabled)
        settings.sync()
        self.tesztuzemChanged.emit()
        self.tesztuzemUzenet.emit(
            UZENET_BEKAPCSOLVA if enabled else UZENET_KIKAPCSOLVA
        )

    # -- egykattintásos átadás ------------------------------------------------

    @Slot(result=bool)
    def tesztuzemNaploAtadasa(self) -> bool:
        """A napló átadása: MINDIG a felhasználó választja meg a helyét.

        `True`, ha a párbeszéd megnyitását kértük; `False`, ha nincs mit
        átadni. A #1654-ben ez egy beégetett mappába másolt, és a
        párbeszéd csak TARTALÉK volt — a beégetett hely viszont egyetlen
        gépre volt szabva, és mérve (2026-09-06) a fejlesztői gépről nem
        is látszott: a napló kiment, de senki nem érte el.

        A hiányzó naplóról továbbra is HANGOSAN szólunk: néma bukás itt a
        legrosszabb kimenet — a felhasználó azt hinné, átadta."""
        forras = legutobbi_indulasi_naplo(_naplo_mappa())
        if forras is None:
            self.tesztuzemUzenet.emit(UZENET_NINCS_NAPLO)
            return False

        self._tesztuzem_elteszi(forras)
        mappa = kiindulo_naplo_mappa(
            megjegyzett=self._tesztuzem_megjegyzett_mappa(),
            megosztas=_megosztas_gyokere(),
            dokumentumok=_dokumentumok(),
        )
        self.tesztuzemMentesKert.emit(
            UZENET_VALASSZ_HELYET,
            QUrl.fromLocalFile(str(mappa)).toString(),
            naplo_fajlneve(_most()),
        )
        return True

    def _tesztuzem_megjegyzett_mappa(self) -> str | None:
        """A legutóbb választott célmappa, ha van (#2553)."""
        ertek = self._get_settings().value(NAPLO_MAPPA_BEALLITAS_KULCS)
        return str(ertek) if ertek else None

    @Slot(str, result=bool)
    def tesztuzemNaploMentese(self, cel: str) -> bool:
        """A napló a felhasználó által választott fájlba (#2553).

        Siker esetén a MAPPÁT megjegyezzük: a következő átadás már ott
        nyílik, tehát a második alkalom is egy mozdulat. Az útvonal a
        vágólapra is felkerül — a #1654 kényelme megmarad."""
        utvonal = _url_utvonala(cel)
        if utvonal is None or not self._tesztuzem_fuggo_szoveg:
            return False
        try:
            utvonal.parent.mkdir(parents=True, exist_ok=True)
            utvonal.write_text(self._tesztuzem_fuggo_szoveg, encoding="utf-8")
        except OSError as hiba:
            self.tesztuzemUzenet.emit(
                f"A napló mentése nem sikerült: {hiba.strerror or hiba}"
            )
            return False
        self._tesztuzem_megjegyez_mappat(utvonal.parent)
        _vagolapra(str(utvonal))
        self.tesztuzemUzenet.emit(
            f"A napló ide került: {utvonal} — az útvonalat a vágólapra is "
            "másoltuk."
        )
        return True

    def _tesztuzem_megjegyez_mappat(self, mappa: Path) -> None:
        """A választott célmappa eltárolása (#2553).

        A `sync()` itt sem elhagyható: enélkül a választás csak a Qt belső
        pufferében élne, és egy váratlan kilépés elnyelné — a felhasználó
        pedig a következő átadásnál megint a beégetett helyen kötne ki."""
        settings = self._get_settings()
        settings.setValue(NAPLO_MAPPA_BEALLITAS_KULCS, str(mappa))
        settings.sync()

    def _tesztuzem_elteszi(self, forras: Path) -> None:
        """A napló SZÖVEGÉT tesszük el, nem a fájl útvonalát: a tartalék
        mentés így akkor is működik, ha a gyorstár közben kiürül."""
        try:
            self._tesztuzem_fuggo_szoveg = Path(forras).read_text(encoding="utf-8")
        except OSError:
            self._tesztuzem_fuggo_szoveg = ""


__all__ = [
    "UZENET_BEKAPCSOLVA",
    "UZENET_KIKAPCSOLVA",
    "UZENET_NINCS_NAPLO",
    "TesztuzemMixin",
]
