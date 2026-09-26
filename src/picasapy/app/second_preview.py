"""A kettős nézet MÁSODIK felének előnézet-hídja (#3187).

A második fél ma **csak előnézet**: AB módban a másik fotót kell mutatnia, a
mentett `filters=` láncával — ahogy a rácsban és az egy képes nézetben is
látszik. A szerkesztő parancsai továbbra is az ELSŐ vezérlőn dolgoznak; a
parancs-irányítás (melyik oldalra hat a mentés, a visszavonás, a forgatás) a
jegy következő lépése.

⚠️ **Miért nem az `EditController` megy ki a QML-nek közvetlenül.** Egy teljes
`EditController` kontextus-objektumként **125 bekötetlen tagot** adott volna a
felületnek (mérve a `kepesseg_or.py`-jal), és a QML-oldali felület azt
ígérné, hogy a második oldal ugyanúgy szerkeszthető, mint az első — ami MA
nem igaz. Ez a híd pontosan annyit ad, amennyi a mai képességhez kell:
`previewSource`, `beginEdit`, `endEdit`.

A rekeszt (`slot`) a becsomagolt vezérlő hordozza: enélkül ugyanarra a fotóra
nyitott két munkamenet felülírná egymás képét a szolgáltató
gyorsítótárában (a kulcs a fotó azonosítója)."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from .edit_controller import EditController


class SecondPreview(QObject):
    """Szűk felület a második előnézet-rekeszhez (#3187)."""

    previewSourceChanged = Signal()

    def __init__(self, controller: EditController, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        # a rekesz képének minden frissülése a `revision`-ön jön át (a
        # `previewSource` `?rev=` cache-bustere ezért változik)
        self._controller.revisionChanged.connect(self.previewSourceChanged)

    @property
    def controller(self) -> EditController:
        """A becsomagolt vezérlő — a tesztek és a lebontás ezen át érik el."""
        return self._controller

    @Property(str, notify=previewSourceChanged)
    def previewSource(self) -> str:
        """A második rekesz előnézeti URL-je (üres, ha nincs munkamenet)."""
        return self._controller.previewSource

    @Slot(str, str)
    def beginEdit(self, photo_id: str, image_path: str) -> None:
        """Munkamenet a második rekeszben — a mentett lánc betöltésével."""
        self._controller.beginEdit(photo_id, image_path)

    @Slot()
    def endEdit(self) -> None:
        """A rekesz munkamenetének zárása (a szolgáltató bejegyzését is)."""
        self._controller.endEdit()

    # -- #3014: az „aa" mód második fele ---------------------------------
    #
    # Az „aa" módban a második fél ugyanazt a fotót szerkeszti, mint az első,
    # de CSAK MEMÓRIÁBAN (a két fél ugyanazt a `filters=` sort írná). A
    # fókuszváltás a két fél láncát cseréli, a kilépéskori döntés pedig
    # kiírja, ha ezt a felet kell megtartani.

    @Property(str, notify=previewSourceChanged)
    def chainValue(self) -> str:
        """A rekesz jelenlegi `filters=` értéke."""
        return self._controller.chainValue

    @Slot(str, str)
    def beginEditInMemory(self, photo_id: str, image_path: str) -> None:
        """Munkamenet a mentett lánccal, ini-írás nélkül."""
        self._controller.beginEditInMemory(photo_id, image_path)

    @Slot(str)
    def setChainValue(self, value: str) -> None:
        """A rekesz láncának lecserélése (memóriás munkamenetben nem ír)."""
        self._controller.setChainValue(value)

    @Slot()
    def persistChain(self) -> None:
        """A rekesz memóriában élő láncának kiírása."""
        self._controller.persistChain()
