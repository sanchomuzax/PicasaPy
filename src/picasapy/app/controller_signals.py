"""Az AppController QML-jelzései egyszerű Python-mixinben (#5957)."""

from PySide6.QtCore import Signal


class AppControllerSignalsMixin:
    """A végső QObject-vezérlő által örökölt jelzések."""

    statusChanged = Signal()
    feedChanged = Signal()
    folderActivated = Signal(str)
    albumsChanged = Signal()
    folderUnavailable = Signal(str)
    folderHideFailed = Signal(str, str)
    hiddenPasswordOfferRequested = Signal()
