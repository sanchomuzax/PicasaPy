"""A nyomtatásvezérlő QML-jelzései külön, QObject előtti mixinben."""

from PySide6.QtCore import Signal


class PrintControllerSignalsMixin:
    """A végső QObject-vezérlő által örökölt jelzések."""

    printFinished = Signal(str)  # kimeneti fájl vagy nyomtató neve

    printFailed = Signal(str)
    #: #3016: LAPONKÉNTI haladás — `(kész, összes)`. A #514 háttérszálas
    #: javaslatát a mérés megdöntötte (12 MP-es fotók, PDF): a festés a
    #: munka kétharmada, és a Qt festő-/nyomtató-API-ja a **GUI-szálhoz
    #: kötött**, tehát nem tolható át. A megoldás ezért nem a szál, hanem a
    #: VISSZAJELZÉS. A jelzés a festés KÖZBEN jön, nem a végén.
    printProgress = Signal(int, int)
    #: #1472: a feladatból KIMARADT képek fájlneve. A `QImage` nem nyit meg
    #: videót és a legtöbb RAW-t — a rácsban viszont MINDKETTŐ látszik (a
    #: bélyegkép elkészül), és a képtálca nyomtatás-gombja rájuk is élő.
    #: Enélkül a felhasználó „Kész"-t látott, miközben egy kép kimaradt.
    printSkipped = Signal(list)
