"""EmailController: kijelölt képek küldése a rendszer levelezőjével
(#32, RÉSZLEGES kör).

Önálló QObject — a `WebExportController`/`PrintController` mintáját
követve NEM az `AppController` mixinje (ld. `print_controller.py`
docstringje az indoklásért). Integrátor-teendők:

1. `application.py`: `EmailController(photo_source=...)` példányosítás
   (`lambda: app_controller._photos.photos`) + `setContextProperty(
   "emailController", ...)`.
2. `Main.qml`/`TrayBar.qml`: a `TrayBar.emailRequested()` jelzés (MÁR kész
   ebben a jegyben) elkapása → tárgy/szöveg bekérése (egyszerű dialógus)
   → `emailController.sendRows(...)`.
3. `OptionsDialog.qml` már ide köti (`OptionsTabEmail.qml`) a méret-
   csúszdákat és az alapértelmezett-kliens kapcsolót — ez a jegy már
   elvégezte, nincs további teendő.

A tényleges küldés a rendszer levelezőjét indítja (freedesktop.org
`xdg-email`, csatolmányokkal; ha nincs telepítve, `mailto:` URL-lel a
rendszer alapértelmezett kezelőjén át — csatolmány nélkül, ld.
`picasapy.mailer` docstringje). Ez SOSEM tesztelhető ténylegesen (nincs
determinisztikus, oldalhatás-mentes módja) — a parancs-összeállítás
(`picasapy.mailer.command`) és az átméretezés-előkészítés
(`prepareAttachments`) igen."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QUrl, Property, Signal, Slot
from PySide6.QtGui import QDesktopServices

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.index import PhotoRecord
from picasapy.mailer import (
    EMAIL_SIZE_PRESETS,
    build_mailto_url,
    build_xdg_email_argv,
    resolve_email_max_dimension,
)

_log = logging.getLogger(__name__)

# QSettings-kulcsok — a `mail/` névtér az OptionsTabEmail élő mezőié
_MULTI_SIZE_KEY = "mail/multiSizeIndex"
_SINGLE_SIZE_KEY = "mail/singleSizeIndex"
_USE_DEFAULT_CLIENT_KEY = "mail/useDefaultClient"

# alapértelmezett indexek (`EMAIL_SIZE_PRESETS`, 0..4): több fotónál a
# közepes méret ésszerű (levélméret-korlátok miatt), egy fotónál az eredeti
# — a Picasa "Single photo size" alapból is nagyobb volt, mint a többfotós
_DEFAULT_MULTI_SIZE_INDEX = 2  # 1024 px
_DEFAULT_SINGLE_SIZE_INDEX = len(EMAIL_SIZE_PRESETS) - 1  # eredeti méret

_TRUE_VALUES = ("true", "1")


def _coerce_bool(value, default: bool) -> bool:
    """A `QSettings` platformonként bool-t vagy szöveget ad vissza ugyanarra
    az írásra (ld. `appearance_controller.coerce_dark_flag` mintája);
    ismeretlen/hiányzó érték a hívott alapértékre esik vissza."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return default


def _clamp_index(value, default: int) -> int:
    try:
        index = int(value)
    except (TypeError, ValueError):
        return default
    if not 0 <= index < len(EMAIL_SIZE_PRESETS):
        return default
    return index


class EmailController(QObject):
    """A `OptionsTabEmail.qml` méret-beállításai + a küldés-előkészítés
    (átméretezés) és a tényleges elküldés (subprocess/mailto) hídja."""

    multiSizeIndexChanged = Signal()
    singleSizeIndexChanged = Signal()
    useDefaultClientChanged = Signal()
    emailFailed = Signal(str)

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        settings: QSettings | None = None,
        parent: QObject | None = None,
    ) -> None:
        """`photo_source`: ld. a modul docstringje. `settings`: teszthez
        beinjektálható `QSettings`-példány (`QSettings("...", "...")` egy
        ideiglenes fájlra) — élesben az alapértelmezett globális beállítás
        (az `application.py`-ban már beállított szervezet/app-név alatt)."""
        super().__init__(parent)
        self._photo_source = photo_source
        self._settings = settings if settings is not None else QSettings()
        self._multi_size_index = _clamp_index(
            self._settings.value(_MULTI_SIZE_KEY), _DEFAULT_MULTI_SIZE_INDEX
        )
        self._single_size_index = _clamp_index(
            self._settings.value(_SINGLE_SIZE_KEY), _DEFAULT_SINGLE_SIZE_INDEX
        )
        self._use_default_client = _coerce_bool(
            self._settings.value(_USE_DEFAULT_CLIENT_KEY), True
        )

    # -- méret-beállítások (OptionsTabEmail.qml csúszdái) ------------------

    @Property(int, notify=multiSizeIndexChanged)
    def multiSizeIndex(self) -> int:
        """Több fotó együttes küldésénél használt méret-fokozat (0..4,
        ld. `picasapy.mailer.EMAIL_SIZE_PRESETS`)."""
        return self._multi_size_index

    @Slot(int)
    def setMultiSizeIndex(self, index: int) -> None:
        index = _clamp_index(index, self._multi_size_index)
        if index == self._multi_size_index:
            return
        self._multi_size_index = index
        self._settings.setValue(_MULTI_SIZE_KEY, index)
        self.multiSizeIndexChanged.emit()

    @Property(int, notify=singleSizeIndexChanged)
    def singleSizeIndex(self) -> int:
        """Egyetlen fotó küldésénél használt méret-fokozat (0..4)."""
        return self._single_size_index

    @Slot(int)
    def setSingleSizeIndex(self, index: int) -> None:
        index = _clamp_index(index, self._single_size_index)
        if index == self._single_size_index:
            return
        self._single_size_index = index
        self._settings.setValue(_SINGLE_SIZE_KEY, index)
        self.singleSizeIndexChanged.emit()

    @Property(bool, notify=useDefaultClientChanged)
    def useDefaultClient(self) -> bool:
        """Igaz: a rendszer alapértelmezett levelezőjét használjuk kérdés
        nélkül; hamis: (jövőbeli finomítás) minden küldésnél rákérdezünk —
        a PicasaPy-ban ma mindkét eset ugyanazt az `xdg-email`/`mailto:`
        utat járja, a kapcsoló egyelőre csak a beállítás megőrzését
        szolgálja (FEN-paritás, ld. `OptionsTabEmail.qml`)."""
        return self._use_default_client

    @Slot(bool)
    def setUseDefaultClient(self, use_default: bool) -> None:
        use_default = bool(use_default)
        if use_default == self._use_default_client:
            return
        self._use_default_client = use_default
        self._settings.setValue(
            _USE_DEFAULT_CLIENT_KEY, "true" if use_default else "false"
        )
        self.useDefaultClientChanged.emit()

    # -- küldés-előkészítés + küldés ---------------------------------------

    def _resolve_items(self, rows: Sequence[int]) -> list[ExportItem]:
        photos = tuple(self._photo_source())
        items = []
        for row in rows:
            index = int(row)
            if 0 <= index < len(photos):
                photo = photos[index]
                items.append(
                    ExportItem(
                        source=Path(photo.folder_path) / photo.name,
                        rotate_steps=photo.rotate_steps,
                        filters=photo.filters,
                    )
                )
        return items

    @Slot(list, bool, result=list)
    def prepareAttachments(self, rows, multi: bool) -> list[str]:
        """A kijelölt sorok csatolmány-fájllá alakítása: a beállított
        méret-fokozatnak megfelelő átméretezéssel (a forgatás/`filters=`
        lánc a `picasapy.export.export_photos` motorral égetve bele, mint
        exportnál) egy ideiglenes mappába. `multi`: melyik méret-beállítást
        (`multiSizeIndex`/`singleSizeIndex`) alkalmazza. Eredeti méretnél
        (utolsó fokozat) a forrásfájlt közvetlenül adja vissza — nincs
        felesleges másolat."""
        items = self._resolve_items(rows)
        if not items:
            return []
        index = self._multi_size_index if multi else self._single_size_index
        max_dimension = resolve_email_max_dimension(index)
        if max_dimension is None:
            return [str(item.source) for item in items]
        target_dir = Path(tempfile.mkdtemp(prefix="picasapy-mail-"))
        settings = ExportSettings(max_dimension=max_dimension, jpeg_quality=85)
        report = export_photos(items, target_dir, settings)
        if report.failed:
            _log.warning(
                "e-mail előkészítés: %d elem sikertelen", len(report.failed)
            )
        return [str(path) for path in report.exported]

    @Slot(list, str, str, result=bool)
    def sendRows(self, attachment_paths, subject: str, body: str) -> bool:
        """A már előkészített (`prepareAttachments`) fájlok elküldése a
        rendszer levelezőjével. `xdg-email` hiányában `mailto:`
        visszaesés — csatolmány NÉLKÜL (ld. a modul docstringje), erről a
        `emailFailed` jelez, hogy a UI figyelmeztethesse a felhasználót."""
        attachments = [Path(path) for path in attachment_paths]
        xdg_email = shutil.which("xdg-email")
        if xdg_email is not None:
            argv = build_xdg_email_argv(subject, body, attachments)
            try:
                subprocess.Popen(argv)  # noqa: S603 — argv-lista, nincs shell
            except OSError as error:
                self.emailFailed.emit(str(error))
                return False
            return True

        if attachments:
            self.emailFailed.emit(
                self.tr(
                    "No email program with attachment support was found; "
                    "opening a blank email without the pictures attached."
                )
            )
        url = build_mailto_url(subject, body)
        opened = QDesktopServices.openUrl(QUrl(url))
        if not opened:
            self.emailFailed.emit(self.tr("No email program was found."))
        return bool(opened)
