"""FileOpsController: fájlműveletek (átnevezés/áthelyezés/lomtár/fájlkezelő,
#15) QML-hídja.

Szándékosan útvonal-alapú (nem index-sor-alapú), hogy az `AppController`-től
(forró fájl, ld. CONTRIBUTING.md) függetlenül fejleszthető és tesztelhető
legyen — a QML a `photosModel.filePathAt(index)`-szel már meglévő
elérésiút-lekérdezést adja át. A rácshoz kötés (context-menü, index-
frissítés a sikeres műveletek után) az integrátor feladata."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication

from picasapy.edit.save import find_original_backup
from picasapy.fileops import (
    RENAME,
    InvalidFolderNameError,
    conflicting_names,
    copy_photos,
    create_folder_for_move,
    delete_permanently,
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
from picasapy.fileops.move_folder import FolderMoveError
from picasapy.ini import IniConflictError, IniSaveError

from .controller import _to_local_path

# #295: az átnevezés/áthelyezés `.picasa.ini`-írása is elbukhat a
# párhuzamosan futó eredeti Picasa miatt (`IniConflictError`) vagy kódolási
# hibán (`IniSaveError`). Ezek nem `OSError`-ok, így a korábbi szűrő mellett
# néma bukásként (kezeletlen kivételként) tűntek volna el a QML felé — a
# `photo_ops_controller` mintájára itt is kezelt írási hibák.
_OPERATION_ERRORS = (ValueError, OSError, IniSaveError, IniConflictError)


class FileOpsController(QObject):
    """A QML fájlművelet-kontextusmenüjéhez tervezett híd."""

    photoRenamed = Signal(str, str)  # (régi_út, új_út)
    photoMoved = Signal(str, str)  # (régi_út, új_út)
    # #1522: (forrás_út, másolat_út) — a másolat célzott indexelése. Külön
    # jelzés, nem a `photoMoved`: ott a FORRÁS is megváltozik (eltűnik), itt
    # érintetlen marad, tehát a forrásmappa újraolvasása fölösleges munka.
    photoCopied = Signal(str, str)
    photoDeleted = Signal(str)  # (törölt_út)
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

    @Slot(str, str)
    def renamePhoto(self, path: str, new_name: str) -> None:
        """Átnevezés (F2): a célnév- vagy forrás-hibákat `operationFailed`
        jelzi (nem emel Python-kivételt a QML felé)."""
        try:
            new_path = rename_photo(Path(path), new_name)
        except _OPERATION_ERRORS as error:
            self.operationFailed.emit("rename", str(error))
            return
        self.photoRenamed.emit(path, str(new_path))

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a felület a TÖBBES
    # `movePhotos` alakot hívja (FileOpsDialogs.qml:49); ez az egyes alak
    # a Pythonból/tesztből induló egyfájlos úthoz marad.
    @Slot(str, str)
    def movePhoto(self, path: str, dest_folder: str) -> None:
        """Áthelyezés másik mappába. A célt a QML FolderDialog `file://`
        URL-ként adja — a lokális útvonallá alakítás itt történik."""
        try:
            new_path = move_photo(Path(path), Path(_to_local_path(dest_folder)))
        except _OPERATION_ERRORS as error:
            self.operationFailed.emit("move", str(error))
            return
        self.photoMoved.emit(path, str(new_path))

    @Slot(list, str, result=int)
    def conflictCountFor(self, paths: list, dest_folder: str) -> int:
        """Hány kijelölt fájl neve foglalt már a célmappában (#457/2).

        A felület CSAK akkor kérdez rá az átnevezés/kihagyás választásra, ha
        ez nem nulla — az eredeti Picasa sem kérdezett fölöslegesen."""
        if not paths:
            return 0
        dest = Path(_to_local_path(dest_folder))
        return len(conflicting_names([Path(path) for path in paths], dest))

    @Slot(list, str, str)
    def copyPhotos(self, paths: list, dest_folder: str, policy: str) -> None:
        """Kijelölés másolása a célmappába (#457/2), `policy` = rename|skip."""
        self._run_batch("copy", copy_photos, paths, dest_folder, policy)

    @Slot(list, str, str)
    def movePhotos(self, paths: list, dest_folder: str, policy: str) -> None:
        """Kijelölés áthelyezése a célmappába (#457/2).

        Az eredeti a KÉPEK áthelyezésére ugyanazt a rename/skip párbeszédet
        adta, mint a másolásra — ezért fut a kettő ugyanazon a magon."""
        self._run_batch("move", move_photos, paths, dest_folder, policy)

    @Slot(list, str)
    def moveSelectionToNewFolder(self, paths: list, name: str) -> None:
        """Fájl ▸ Áthelyezés új mappába… (#1614, `ID_FILE_NEWFOLDER`).

        A parancs neve félrevezet: NEM mappát hoz létre önmagában, hanem a
        kijelölt képeket helyezi át egy ÚJ mappába, amit a felhasználó
        NEVEZ el — a helyét (a kijelölés ELSŐ elemének jelenlegi mappáját)
        a program választja, ezért a dialógus csak egy nevet kér, mint az
        „Új album…" (`newAlbumDialog`).

        A tényleges mozgatás a MEGLÉVŐ kötegelt úton fut (`_run_batch` →
        `move_photos`), pontosan úgy, mint a „Áthelyezés…" (#457): a
        `.picasa.ini` bejegyzések a képekkel költöznek, és a haladás-/
        összegző jelzés (`batchProgress`/`batchFinished`) is ugyanaz. Az
        index-frissítés a `wire_fileops` MÁR MEGLÉVŐ célzott resyncjén
        megy (`photoMoved` → `resyncFolder`) — ez a brand-new (még sosem
        indexelt) célmappát is kezeli, ahogy a #1522 másolás-tesztje is
        megméri.

        Az új mappa nevét ELLENŐRIZZÜK, mielőtt bármi a lemezre kerülne
        (üres/csak szóköz/Windows-tiltott karakter — #1700 hibaosztálya),
        és azt is, hogy a célmappa MÁR NE létezzen — egyik hiba se essen
        némán, mindkettő az `operationFailed`-en át jut el a felhasználóhoz
        (`fileOpsErrorDialog`, ugyanaz a csatorna, mint minden más
        fájlművelet-hibánál)."""
        if not paths:
            self.operationFailed.emit(
                "move_to_new_folder", self.tr("Select at least one picture first.")
            )
            return
        try:
            folder_name = validate_folder_name(name)
        except InvalidFolderNameError as error:
            self.operationFailed.emit("move_to_new_folder", str(error))
            return
        parent = Path(_to_local_path(paths[0]) or paths[0]).parent
        try:
            target = create_folder_for_move(parent, folder_name)
        except OSError as error:
            self.operationFailed.emit("move_to_new_folder", str(error))
            return
        self._run_batch("move", move_photos, paths, str(target), RENAME)

    def _run_batch(self, operation, function, paths, dest_folder, policy) -> None:
        dest = Path(_to_local_path(dest_folder))

        paths_list = [Path(path) for path in paths]
        started = time.monotonic()
        moved_bytes = 0

        def report(done: int, total: int) -> None:
            nonlocal moved_bytes
            index = done - 1
            if 0 <= index < len(paths_list):
                try:
                    moved_bytes += paths_list[index].stat().st_size
                except OSError:
                    # a mozgatott fájl a forráson már nincs meg — a
                    # sebesség csak tájékoztatás, nem érdemes hibázni rajta
                    pass
            elapsed = time.monotonic() - started
            speed = moved_bytes / elapsed if elapsed > 0 else 0.0
            self.batchProgress.emit(operation, str(dest), done, total, speed)

        try:
            result = function(paths_list, dest, policy, report)
        except _OPERATION_ERRORS as error:
            self.operationFailed.emit(operation, str(error))
            return
        if operation == "move":
            # MINDKÉT mappa változott, ezért mindkét út kimegy: a forrásból
            # eltűnt, a célban megjelent a kép. A jelzésnek nincs QML-oldali
            # feliratkozója — a rácsot a `wire_fileops` célzott resyncje
            # frissíti (#15).
            for source, target in result.done:
                self.photoMoved.emit(str(source), str(target))
        elif operation == "copy":
            # #1522: a másolás UGYANÚGY célzott újraolvasást kér, mint az
            # áthelyezés — a figyelőre itt sem építünk.
            #
            # Mérés (valódi vezérlő, produkciós FOLDER_POLL_MS): a másolat a
            # LÁTOTT mappában a #1275 lekérdezéssel ~9,8 s alatt jött be, a
            # feedben MÁR SZEREPLŐ mappában a #1435 sweep-pel ugyanennyi
            # alatt — de egy MÉG NEM INDEXELT célmappát egyik sem nézi,
            # ezért ott a másolat az ötperces rescanig láthatatlan maradt.
            # Ugyanaz áthelyezéssel: 0,06 s.
            #
            # A figyelő ezt csak akkor fedi el, ha él: a `LibraryWatcher`
            # csak az INDULÁSKOR létező gyökereket veszi fel, és az inotify
            # figyelőkerete nagy gyűjteménynél elfogyhat. Őr:
            # `tests/app/test_masolas_resync_1522.py`.
            for source, target in result.done:
                self.photoCopied.emit(str(source), str(target))
        # #459: EGY összegzés a köteg végén, nem fájlonkénti ablak
        self.batchFinished.emit(
            operation,
            len(result.done),
            len(result.skipped),
            len(result.failed),
            _first_failure_reason(result),
        )

    @Slot(str, str)
    def moveFolder(self, folder: str, dest_parent: str) -> None:  # noqa: N802
        """Mappa áthelyezése a KÍSÉRŐFÁJLOKKAL együtt (#457).

        Az eredeti `Folder::ID_MOVEFOLDER` parancsa. Nálunk ez több, mint
        kényelem: a `.picasa.ini` az igazságforrás, tehát a mappával
        együtt kell mennie — enélkül a képek elveszítenék a feliratukat, a
        címkéiket és az arc-hozzárendeléseiket.

        Hiba esetén `operationFailed` megy ki emberi üzenettel, a forrás
        érintetlen marad."""
        target_text = _to_local_path(dest_parent)
        if not target_text:
            self.operationFailed.emit(
                "move_folder", self.tr("Choose a destination folder first.")
            )
            return
        source = Path(_to_local_path(folder) or folder)
        try:
            moved = move_folder(source, Path(target_text))
        except FolderMoveError as error:
            self.operationFailed.emit("move_folder", str(error))
            return
        # #1538: a NORMALIZÁLT forrás megy ki, nem a kapott nyers szöveg —
        # az `file://` URL-t a fogadó oldal nem tudná megtalálni.
        self.folderMoved.emit(str(source), str(moved))

    @Slot(str)
    def deleteFolder(self, folder: str, trash_dir: Path | None = None) -> None:  # noqa: N802
        """A MAPPA a lomtárba, a tartalmával együtt (#1638).

        Az eredeti `Folder::ID_ALBUM_DELETE` parancsa. Hogy a lomtár a cél,
        és nem a végleges törlés, azt az eredeti megerősítő szövege mondja
        ki: *„…move the folder »%s« and its contents to the Recycle Bin?"*

        A `.picasa.ini` a mappával megy — nincs vele külön dolgunk —, tehát
        egy visszaállítás a feliratokat, címkéket és arc-hozzárendeléseket
        is visszahozza.

        A `trash_dir` CSAK a tesztek fogantyúja (a valódi lomtárba nem
        írunk próbaképp); a felületről mindig alapértelmezéssel hívjuk.

        Hiba esetén `operationFailed` megy ki emberi üzenettel, és a mappa
        érintetlen marad — néma bukás nincs."""
        source = Path(_to_local_path(folder) or folder)
        try:
            delete_to_trash(source, trash_dir=trash_dir)
        except OSError as error:
            self.operationFailed.emit("delete_folder", str(error))
            return
        self.folderDeleted.emit(str(source))

    @Slot(str)
    def deletePhoto(self, path: str) -> None:
        """Törlés a lomtárba (freedesktop.org Trash-specifikáció)."""
        try:
            delete_to_trash(Path(path))
        except OSError as error:
            self.operationFailed.emit("delete", str(error))
            return
        self.photoDeleted.emit(path)

    @Slot(str)
    def deletePhotoPermanently(self, path: str) -> None:
        """Végleges, azonnali törlés — akkor hívandó, ha a `path`-hoz nincs
        elérhető lomtár (#457: hálózati meghajtó/NAS), és a felhasználó a
        `deleteConfirmDialog` erre figyelmeztető, külön szövegű ágán mégis
        megerősítette a törlést."""
        try:
            delete_permanently(Path(path))
        except OSError as error:
            self.operationFailed.emit("delete", str(error))
            return
        self.photoDeleted.emit(path)

    @Slot(list, result=bool)
    def trashAvailableFor(self, paths: list) -> bool:
        """True, ha MINDEN megadott útvonalhoz van elérhető lomtár (#457).
        Kevert kijelölésnél (van, ami nem) a szigorúbb ág nyer — `False` —,
        hogy a `deleteConfirmDialog` a végleges-törlés szövegét mutassa,
        és az ne törölje csendben azt is, amihez lett volna lomtár."""
        if not paths:
            return True
        return all(trash_available(Path(path)) for path in paths)

    @Slot(str)
    def revealPhoto(self, path: str) -> None:
        """A fájlt tartalmazó mappa megnyitása a fájlkezelőben.

        Sikertelen megnyitás (hiányzó `xdg-open` vagy nemnulla kilépési
        kód) esetén `operationFailed`-et jelez, hogy a felhasználó ne
        maradjon visszajelzés nélkül (#112)."""
        try:
            reveal_in_file_manager(Path(path))
        except OSError as error:
            self.operationFailed.emit("reveal", str(error))

    @Slot(str, result=bool)
    def hasOriginalOnDisk(self, path: str) -> bool:  # noqa: N802
        """Van-e a képnek megőrzött EREDETIJE a `.picasaoriginals`-ban (#1613).

        Az „Eredeti a lemezen" tétel ettől él vagy szürkül: az eredetiben is
        letiltott, ha nincs mit megmutatni."""
        cel = _to_local_path(path) or path
        if not cel:
            return False
        return find_original_backup(Path(cel)) is not None

    @Slot(str)
    def revealOriginal(self, path: str) -> None:  # noqa: N802
        """A `.picasaoriginals`-beli EREDETI megmutatása a fájlkezelőben (#1613).

        Az eredeti `CThumbUI::locateorigondiskmenu_win` parancsa. Nem a
        szerkesztett fájlt mutatja meg — épp az a lényege, hogy a megőrzött
        eredetihez lehessen eljutni.

        Ha nincs eredeti, a felhasználó üzenetet kap; a menütétel ilyenkor
        amúgy is szürke (`hasOriginalOnDisk`), de a néma bukást akkor sem
        engedjük, ha valaki mégis idejut."""
        cel = _to_local_path(path) or path
        eredeti = find_original_backup(Path(cel)) if cel else None
        if eredeti is None:
            self.operationFailed.emit(
                "locate_original",
                self.tr("This picture has no preserved original on disk."),
            )
            return
        try:
            reveal_in_file_manager(eredeti)
        except OSError as error:
            self.operationFailed.emit("locate_original", str(error))

    @Slot(str)
    def revealFolder(self, folder_path: str) -> None:
        """MAGÁNAK a mappának a megnyitása a fájlkezelőben (#422: „Keresés a
        lemezen" a mappa kontextusmenüjéből).

        A `revealPhoto` a kapott ÚT SZÜLŐJÉT nyitja (fájlra van szabva) —
        mappánál az a szülőmappát nyitná meg, ami nem az elvárt viselkedés.
        Ezért a mappa alatti álnevet adjuk át, aminek a szülője maga a
        mappa."""
        local = _to_local_path(folder_path)
        if not local:
            return
        try:
            open_folder_in_file_manager(Path(local))
        except OSError as error:
            self.operationFailed.emit("reveal", str(error))

    @Slot(str)
    def openPhoto(self, path: str) -> None:
        """A fájl megnyitása a rendszer társított alkalmazásával (#422:
        „Fájl megnyitása", `Ctrl+Shift+O` a néző kontextusmenüjében).

        A `revealPhoto` párja: az a fájlkezelőt nyitja a fájlra, ez magát a
        fájlt adja át a társított programnak. Hiba esetén ugyanúgy
        `operationFailed`, nem kivétel a QML felé (#112)."""
        local = _to_local_path(path)
        if not local or not Path(local).exists():
            self.operationFailed.emit("open", f"nincs ilyen fájl: {path}")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(local)):
            self.operationFailed.emit("open", f"nem sikerült megnyitni: {local}")

    @Slot(str)
    def copyFullPath(self, path: str) -> None:
        """A teljes elérési út a vágólapra (#422: „Teljes elérési út
        másolása"). Vágólap hiányában (fej nélküli környezet) csendben
        kimarad — nem hibaág, csak nincs hova másolni."""
        local = _to_local_path(path)
        if not local:
            return
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(local)


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
