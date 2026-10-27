"""A QML-jelzések sima Python-mixinben."""

from PySide6.QtCore import Signal


class EditControllerSignalsMixin:
    """A végső QObject-vezérlő által örökölt jelzések."""

    revisionChanged = Signal()

    toolsChanged = Signal()

    pickerRecentColorsChanged = Signal()

    gpuRevisionChanged = Signal()

    shiftAktivChanged = Signal()

    editSaveReadOnly = Signal()

    editSaveFailed = Signal(str)

    editChainRejected = Signal(str)

    _previewRendered = Signal()

    chainSaved = Signal(str, str)

