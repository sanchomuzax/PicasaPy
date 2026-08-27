"""Tartós **tesztüzem** (#1654) — az AppController vezérlő-szelete.

A `perf_controller.py` (#211) mintája: a szelet a `Súgó` menüből
kapcsolható, és a `PerfMonitorMixin`-hez hasonlóan **kikapcsolt állapotban
semmit nem futtat**.

## Mit ad hozzá a #211-hez

A Teljesítmény-monitor csak MENETKÖZBEN kapcsolható be — mire a felhasználó
eléri a menüt, az indulás rég lezajlott. A tesztüzem ezzel szemben
**tartós**: `QSettings`-ben él, túléli a kilépést, és a **következő**
indulás mér, az első ezredmásodperctől (ld. `application._indulasi_idovonal`).

## Átadás — egy kattintás, semmi hálózat

`Súgó ▸ Napló elküldése` a legutóbbi indulási naplót a NAS közös mappájába
másolja (`/mnt/nas`, Windowson `//DS215j/lemez`), a rögzített
`picasapy-naplo/` almappába, időbélyeges néven, és az útvonalat a
vágólapra is felteszi. **Semmilyen hálózati feltöltés, külső szolgáltatás
vagy hitelesítés nincs benne** — fájlmásolás egy csatolt megosztásra.

Ha a megosztás nem érhető el, a felhasználó érthető magyar üzenetet kap, és
a felület felajánlja a „Mentés másként…" tartalékot.

## ⚠️ A fogantyúk (seam)

A közös mappa útvonala, a vágólap, az óra és a naplómappa MODULSZINTŰ
függvények — a teszt EZEKET cseréli. A `/mnt/nas` éles családi adat: a
tesztkészlet soha nem írhat oda.
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
    TESZTUZEM_BEALLITAS_KULCS,
    legutobbi_indulasi_naplo,
    megosztas_elerheto,
    megosztas_gyokere,
    naplo_atadasa,
    naplo_celmappa,
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
    #: A közös mappa nem érhető el — a felület „Mentés másként…"-et nyit.
    tesztuzemMentesMaskentKert = Signal(str)

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

    @Slot(result=str)
    def tesztuzemNaploAtadasa(self) -> str:
        """A legutóbbi indulási napló a közös mappába; a cél útvonala.

        Sikertelenségnél üres sztring, és MINDIG szól: vagy a hiányzó
        naplóról, vagy a „Mentés másként…" tartalékról. Néma bukás itt a
        legrosszabb kimenet — a felhasználó azt hinné, átadta."""
        forras = legutobbi_indulasi_naplo(_naplo_mappa())
        if forras is None:
            self.tesztuzemUzenet.emit(UZENET_NINCS_NAPLO)
            return ""

        gyoker = _megosztas_gyokere()
        if gyoker is None:
            self._tesztuzem_elteszi(forras)
            self.tesztuzemMentesMaskentKert.emit(
                "A közös mappa most nem érhető el (nincs csatlakoztatva a "
                "hálózati meghajtó). Válaszd ki, hova mentsük a naplót."
            )
            return ""

        try:
            cel = naplo_atadasa(
                forras=forras, celmappa=naplo_celmappa(gyoker), most=_most()
            )
        except OSError as hiba:
            self._tesztuzem_elteszi(forras)
            self.tesztuzemMentesMaskentKert.emit(
                "A közös mappa nem érhető el, a napló nem másolható oda "
                f"({hiba.strerror or hiba}). Válaszd ki, hova mentsük."
            )
            return ""

        _vagolapra(str(cel))
        self.tesztuzemUzenet.emit(
            f"A napló a közös mappába került: {cel} — az útvonalat a "
            "vágólapra is másoltuk."
        )
        return str(cel)

    @Slot(str, result=bool)
    def tesztuzemNaploMentese(self, cel: str) -> bool:
        """A „Mentés másként…" tartalék: a napló a megadott fájlba."""
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
        self.tesztuzemUzenet.emit(f"A napló ide került: {utvonal}")
        return True

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
