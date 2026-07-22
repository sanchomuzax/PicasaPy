"""StartupStatus: az indítóképernyő (#189) állapot-hídja a QML felé.

Kis, önálló QObject, amit az induló szekvencia (application.py) tölt föl:
minden lépésnél átadja a felhasználónak szánt állapotüzenetet
(`report`), a végén pedig készre állítja magát (`finish`). A SplashScreen.qml
erre a két property-re köt — a `statusText` a felirat-sort frissíti, a
`ready` (illetve a belőle képzett `busy`) pedig kivezérli a splash
eltűnését (opacity-animáció).

Szándékosan NEM az AppController mixinje (ld. a fileops_controller.py /
discovery_controller.py mintáját): az indulás legelső fázisában — még
mielőtt a nehéz controller egyáltalán létrejönne — is meg kell tudnunk
jeleníteni a splash-t, ezért ez a hídobjektum tőle függetlenül él és
tesztelhető."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot


class StartupStatus(QObject):
    """Induló-állapot: `statusText` felirat + `busy`/`ready` kapcsoló.

    Az igazságforrás a `_ready` jelző és a `_status_text`; a `busy` ennek
    a tükre (`not ready`), külön mezőt nem tartunk, hogy a kettő soha ne
    csússzon szét. Készre álláskor a `statusText` üresre vált, hogy a
    felirat-sor ne ragadjon be egy köztes lépés szövegén, amíg a splash
    kifakul."""

    statusTextChanged = Signal()
    readyChanged = Signal()

    def __init__(
        self,
        status_text: str = "",
        parent: QObject | None = None,
        *,
        requires_confirmation: bool = False,
    ) -> None:
        """`requires_confirmation` (#243): igaz értékkel a splash a betöltés
        végén nem tűnik el magától, hanem „félkész szoftver" figyelmeztetést
        és OK gombot mutat — az app ezt addig kapcsolja be, amíg az eredeti
        Picasa effekt-készlete nincs teljesen implementálva (#20, #190)."""
        super().__init__(parent)
        self._status_text = status_text
        self._ready = False
        self._requires_confirmation = requires_confirmation

    # -- QML-nek kitett property-k -------------------------------------------

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        """A felhasználónak szánt aktuális állapotüzenet (pl. „Mappák
        beolvasása…"). Készre álláskor üresre vált."""
        return self._status_text

    @Property(bool, notify=readyChanged)
    def ready(self) -> bool:
        """Igaz, ha az indulás befejeződött — a splash erre fakul ki."""
        return self._ready

    @Property(bool, notify=readyChanged)
    def busy(self) -> bool:
        """A `ready` tükre: igaz, amíg az indulás tart. A foglalt-sáv és a
        pontanimáció ehhez köthető, hogy készre álláskor magától megálljon."""
        return not self._ready

    @Property(bool, constant=True)
    def requiresConfirmation(self) -> bool:
        """Igaz, ha a splash a betöltés végén megerősítést (OK) kér (#243) —
        az app élettartama alatt nem változik, ezért konstans property."""
        return self._requires_confirmation

    # -- az induló szekvencia hívja ------------------------------------------

    @Slot(str)
    def report(self, text: str) -> None:
        """Új állapotüzenet beállítása. A `None`-t üres szövegként kezeli,
        hogy egy hiányzó lépéscímke se dobjon hibát indulás közben.
        Változatlan szövegre nem emittál — a QML fölösleges újrarajzolását
        elkerülve."""
        value = text or ""
        if value == self._status_text:
            return
        self._status_text = value
        self.statusTextChanged.emit()

    @Slot()
    def finish(self) -> None:
        """Az indulás lezárása: `ready` igazra vált (a `busy` hamisra), a
        `statusText` üresre. Idempotens — ismételt hívása már nem emittál,
        így a több forrásból (pl. időzítő + jel) érkező „kész" nem villog."""
        if self._ready:
            return
        self._ready = True
        if self._status_text:
            self._status_text = ""
            self.statusTextChanged.emit()
        self.readyChanged.emit()
