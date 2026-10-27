"""A QML-jelzések sima Python-mixinben, a QObject közös osztálya előtt."""

from PySide6.QtCore import Signal


class FaceScanControllerSignalsMixin:
    """A végső QObject-vezérlő által örökölt jelzések."""


    scanStarted = Signal()

    scanProgress = Signal(int, int)  # (kész, összes)

    scanFinished = Signal(int, int)  # (talált arc, átvizsgált fotó)

    scanCancelled = Signal()

    scanFailed = Signal(str)

    #: #1403: az arc elnevezése után AUTOMATIKUS XMP-írás hibája — az
    #: eredetiben is megnevezett hibaeset („Face tag write failed for read
    #: only file: %s"), ezért nem nyeljük el.
    xmpAutoWriteFailed = Signal(str)

    # A modell hiányzik/nem tölthető be — a szkennelés el sem indul, ez
    # NEM hiba (a funkció tervezett, hiánytűrő kikapcsolása).
    modelUnavailable = Signal()

    _scanWorkerStopped = Signal()


    # #26 (2. lépcső): lenyomat-számítás + csoportosítás — a detektálásnál
    # ALACSONYABB PRIORITÁSÚ, KÜLÖN indítható sor (ld. osztály-docstring).
    embeddingStarted = Signal()

    embeddingProgress = Signal(int, int)  # (kész, összes)

    embeddingFinished = Signal(int, int)  # (lenyomatolt arc, csoportba került arc)

    embeddingCancelled = Signal()

    embeddingFailed = Signal(str)

    embeddingModelUnavailable = Signal()


    # #26 (3. lépcső): a „Névtelenek" album mérete változott (szkennelés,
    # csoportosítás, vagy sikeres tömeges névadás után) — a bal hasáb
    # sorának darabszáma ezt figyeli.
    unnamedCountChanged = Signal()

    # A függő név-javaslat változott; a főnézet erre frissíti a panelt és a
    # személy-album fejlécének javaslatszámát.
    faceSuggestionsChanged = Signal()


    # #4627: a menüsor és a helyi menük Ctrl/Shift ágának megerősítése.
    faceResetConfirmationRequested = Signal(str)


    # #449: a háttér-beolvasás haladása az ALBUMLISTÁBAN jelenik meg
    # („Scanning for faces… %d%% complete"), nem modális ablakban — semmi
    # nem blokkolja a felhasználót. A `scanProgress` jelzés erre kevés: a
    # bal hasáb sorának DEKLARATÍV kötés kell, ezért a százalék NOTIFY-
    # property is (−1 = épp nem fut).
    scanPercentChanged = Signal()

    #: #4586: az Emberek panel állapot-sora (spec 9/b) ezekből él — a futó
    #: keresés hátralévő fájljainak száma és a lenyomat-számítás haladása.
    uncheckedFilesChanged = Signal()

    sortingPercentChanged = Signal()

    #: #4586: a keresés új arcot mentett — a panel listája frissülhet a
    #: keresés KÖZBEN, nem csak a végén.
    facesStored = Signal()


    # #1496: a modellfájl LETÖLTÉSE a felületről. A #1473 óta a párbeszéd
    # megmondja, mi hiányzik — de a felhasználó (aki nem programozó) ettől
    # még nem jutott modellhez, mert a `download_model()` a termékkódból
    # sehonnan nem hívódott.
    #: (siker, felhasználói mondat) — megszakításnál és hibánál is szól,
    #: néma bukás SEHOL.
    #:
    #: „Elindult" jelzés SZÁNDÉKOSAN NINCS (#1496 felülvizsgálat): a
    #: letöltést egyedül a párbeszéd `startDownload()`-ja indítja, ami maga
    #: állítja a `downloading` jelzőt — egy indulás-jelzés ugyanazt mondaná
    #: el másodszor. Az indulást a `modelDownloadPercent` 0-ra váltása is
    #: mutatja.
    modelDownloadFinished = Signal(bool, str)

    modelDownloadPercentChanged = Signal()
