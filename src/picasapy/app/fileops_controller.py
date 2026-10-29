"""FileOpsController: fájlműveletek (átnevezés/áthelyezés/lomtár/fájlkezelő,
#15) QML-hídja.

Szándékosan útvonal-alapú (nem index-sor-alapú), hogy az `AppController`-től
(forró fájl, ld. CONTRIBUTING.md) függetlenül fejleszthető és tesztelhető
legyen — a QML a `photosModel.filePathAt(index)`-szel már meglévő
elérésiút-lekérdezést adja át. A rácshoz kötés (context-menü, index-
frissítés a sikeres műveletek után) az integrátor feladata."""

# Az importok a korábbi modulnév és monkeypatch-fogantyúk kompatibilitásához is kellenek.
# ruff: noqa: F401

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtCore import QByteArray, QMimeData
from PySide6.QtGui import QDesktopServices, QGuiApplication

from picasapy.edit.save import find_original_backup
from picasapy.fileops import (
    CompanionLeftBehindError,
    RENAME,
    InvalidFolderNameError,
    conflicting_names,
    copy_photos,
    create_folder_for_move,
    create_unique_split_folder,
    delete_photo_permanently,
    delete_photo_to_trash,
    delete_to_trash,
    move_folder,
    move_photo,
    move_photos,
    open_folder_in_file_manager,
    rename_photo,
    reveal_in_file_manager,
    trash_available,
    validate_folder_name,
)
from picasapy.fileops import open_with
from picasapy.fileops.move_folder import FolderMoveError
from picasapy.ini import (
    IniConflictError,
    IniSaveError,
    update_document,
    with_folder_date_override,
    with_folder_music,
)
from picasapy.fileops.safe_move import safe_move
from picasapy.scanner import PICASA_INI_NAME

from .controller import _to_local_path
from .formatting import to_local_path
from .fileops_controller_move_mixin import FileOpsControllerMoveMixin
from .fileops_controller_delete_mixin import FileOpsControllerDeleteMixin
from .fileops_controller_clipboard_mixin import FileOpsControllerClipboardMixin
from .fileops_controller_open_mixin import FileOpsControllerOpenMixin

#: #4330: a teszt ezt a Qt-fogantyút cseréli, így az asztali alkalmazás
#: elindítása nélkül ellenőrizhető a fájlmegnyitási kérés.
_open_url = QDesktopServices.openUrl

# #295: az átnevezés/áthelyezés `.picasa.ini`-írása is elbukhat a
# párhuzamosan futó eredeti Picasa miatt (`IniConflictError`) vagy kódolási
# hibán (`IniSaveError`). Ezek nem `OSError`-ok, így a korábbi szűrő mellett
# néma bukásként (kezeletlen kivételként) tűntek volna el a QML felé — a
# `photo_ops_controller` mintájára itt is kezelt írási hibák.
_OPERATION_ERRORS = (ValueError, OSError, IniSaveError, IniConflictError)


#: A linuxos fájlkezelők vágólap-formátuma: az ELSŐ sora `copy` vagy `cut`.
_GNOME_VAGOLAP_FORMATUM = "x-special/gnome-copied-files"


def vagolap_fajlok(adat) -> tuple[list[str], str]:
    """A vágólap tartalmából a fájlok és a művelet (`copy`/`cut`) (#1526).

    A művelet forrása az `x-special/gnome-copied-files` ELSŐ sora — ez a
    linuxos fájlkezelők konvenciója, és a windowsos `Preferred DropEffect`
    párja (a mérés szerint a Picasa ugyanazt az adatot teszi fel másoláskor
    és kivágáskor, csak ez a formátum különbözteti meg őket).

    Ha a jelzés hiányzik, a művelet **`copy`** — a másolás a biztonságos
    alapértelmezés: egy félreértett `cut` a felhasználó tudta nélkül
    MOZGATNÁ a fájlt.

    Csak a helyi (`file://`) útvonalak jönnek vissza: távoli URL-t nem tudunk
    beilleszteni.
    """
    if adat is None or not adat.hasUrls():
        return ([], "copy")
    fajlok = [url.toLocalFile() for url in adat.urls() if url.isLocalFile()]
    muvelet = "copy"
    if adat.hasFormat(_GNOME_VAGOLAP_FORMATUM):
        sorok = bytes(adat.data(_GNOME_VAGOLAP_FORMATUM)).decode("utf-8", "replace").splitlines()
        if sorok and sorok[0].strip() == "cut":
            muvelet = "cut"
    return (fajlok, muvelet)


class FileOpsController(
    FileOpsControllerMoveMixin,
    FileOpsControllerDeleteMixin,
    FileOpsControllerClipboardMixin,
    FileOpsControllerOpenMixin,
    QObject,
):
    """A QML fájlművelet-kontextusmenüjéhez tervezett híd."""

    photoRenamed = Signal(str, str)  # (régi_út, új_út)
    photoMoved = Signal(str, str)  # (régi_út, új_út)
    # #1522: (forrás_út, másolat_út) — a másolat célzott indexelése. Külön
    # jelzés, nem a `photoMoved`: ott a FORRÁS is megváltozik (eltűnik), itt
    # érintetlen marad, tehát a forrásmappa újraolvasása fölösleges munka.
    photoCopied = Signal(str, str)
    photoDeleted = Signal(str)  # (törölt_út)
    #: #1526: a vágólap fájl-tartalma változott — ettől él/szürkül a
    #: Beillesztés menütétel. A Qt vágólapjának `dataChanged`-jére kötjük.
    clipboardFilesChanged = Signal()
    operationFailed = Signal(str, str)  # (művelet, hibaüzenet)
    # (művelet, kész, kihagyott, hibás, első_hiba_oka) — a köteg EGYETLEN
    # összegzése (#457/2). #1430: az OK is kimegy, nem csak a darabszám. A
    # felületen az áthelyezés MINDIG ezen az úton fut (a `Main.qml` az
    # `openMove` → `startBatch("move")` láncot hívja, egyetlen kijelölt
    # képnél is), tehát a magok magyarázó hibaüzenetei kizárólag itt tudnak
    # eljutni a felhasználóhoz — enélkül némán elvesznének.
    batchFinished = Signal(str, int, int, int, str)
    # #457: haladás a kötegelt másolás/áthelyezés alatt — (művelet, cél,
    # kész, összes). Az eredeti is SZÁMLÁLÓT mutatott
    # (`CAcquireUI::copying` = „Copying %1$d of %2$d files"), nem csak egy
    # pörgő sávot; a címe `CThumbUI::CopyProgress`/`::MoveProgress`.
    # #457: (művelet, cél, kész, összes, bájt/mp). Az eredeti a
    # SEBESSÉGET is kiírta („Moving %d of %d (%s/s)") — egy nagy köteg
    # alatt ez mondja meg, hogy érdemes-e várni, vagy elment kávéért.
    batchProgress = Signal(str, str, int, int, float)
    # #457: mappa áthelyezve — (régi út, új út). MINDKÉT út LOKÁLIS,
    # normalizált alakban megy ki (#1538): a QML `FolderDialog` `file://`
    # URL-t is adhat, és egy `file:///…` alakú „mappát" a fogadó oldal sem
    # a lemezen, sem az indexben nem találná meg.
    #
    # Fogyasztó: `wire_fileops` → `resyncMovedFolder` (#1538) — a régi ÉS
    # az új hely RÉSZFÁJA is célzott újraolvasást kap. QML-oldali
    # feliratkozó szándékosan nincs: a bal hasábot és a rácsot az
    # újraolvasás utáni modellfrissítés hozza rendbe.
    folderMoved = Signal(str, str)
    #: #1638: a lomtárba tett MAPPA útja — az index innen tudja, mit vegyen ki
    folderDeleted = Signal(str)

    _vagolap_adat = None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._vagolap_adat = None
        # A Menü Beillesztés tétele a jelzésből tudja, hogy a vágólap
        # tartalma megváltozott. Külső program másolását is követjük, a
        # fej nélküli tesztplatformon viszont nem kérdezzük le a Qt-vágólapot.
        if QGuiApplication.instance() is not None and QGuiApplication.platformName() not in (
            "offscreen",
            "minimal",
        ):
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.dataChanged.connect(self._clipboard_data_changed)

    @Slot()
    def _clipboard_data_changed(self) -> None:
        self.clipboardFilesChanged.emit()

    @Property(bool, notify=clipboardFilesChanged)
    def clipboardHasFiles(self) -> bool:
        """Van-e FÁJL a vágólapon — ettől él a Beillesztés menütétel.

        Szándékosan nem gyorstárazzuk: a vágólapot más program is átírhatja,
        és a menü megnyitásakor a FRISS állapot kell."""
        return bool(vagolap_fajlok(self._vagolap_adata())[0])


def _first_failure_reason(result) -> str:
    """Az ELSŐ bukás fájlneve és oka — a köteg összegzéséhez (#1430).

    A `BatchResult.failed` (forrás, hibaüzenet) párokat tart; a darabszám
    önmagában nem cselekvésre fordítható („1 fájlt nem sikerült
    feldolgozni"). A fájlnevet elé tesszük, mert a mag üzenete nem mindig
    nevezi meg a forrást. Üres sztring, ha nem volt bukás.

    Csak az elsőt mutatjuk: a köteg összegzése SZÁNDÉKOSAN egyetlen
    párbeszéd (#459), nem fájlonkénti ablak — a többi bukás darabszáma a
    saját sorában szerepel.
    """
    if not result.failed:
        return ""
    source, reason = result.failed[0]
    return f"{Path(source).name}: {reason}"
