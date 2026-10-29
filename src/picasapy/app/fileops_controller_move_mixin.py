"""A FileOpsController move mixin felelősségének mixinje."""

from __future__ import annotations

from importlib import import_module

from PySide6.QtCore import Slot


def _controller_module():
    """A régi modul fogantyúihoz irányít, monkeypatch-kompatibilisen."""
    return import_module("picasapy.app.fileops_controller")


class FileOpsControllerMoveMixin:
    @Slot(str, str)
    def renamePhoto(self, path: str, new_name: str) -> None:
        """Átnevezés (F2): a célnév- vagy forrás-hibákat `operationFailed`
        jelzi (nem emel Python-kivételt a QML felé)."""
        _compat = _controller_module()
        try:
            new_path = _compat.rename_photo(_compat.Path(path), new_name)
        except _compat._OPERATION_ERRORS as error:
            self.operationFailed.emit("rename", str(error))
            return
        self.photoRenamed.emit(path, str(new_path))

    def movePhoto(self, path: str, dest_folder: str) -> None:
        """Áthelyezés másik mappába. A célt a QML FolderDialog `file://`
        URL-ként adja — a lokális útvonallá alakítás itt történik."""
        _compat = _controller_module()
        try:
            new_path = _compat.move_photo(
                _compat.Path(path), _compat.Path(_compat._to_local_path(dest_folder))
            )
        except _compat._OPERATION_ERRORS as error:
            self.operationFailed.emit("move", str(error))
            return
        self.photoMoved.emit(path, str(new_path))

    @Slot(list, str, result=int)
    def conflictCountFor(self, paths: list, dest_folder: str) -> int:
        """Hány kijelölt fájl neve foglalt már a célmappában (#457/2).

        A felület CSAK akkor kérdez rá az átnevezés/kihagyás választásra, ha
        ez nem nulla — az eredeti Picasa sem kérdezett fölöslegesen."""
        _compat = _controller_module()
        if not paths:
            return 0
        dest = _compat.Path(_compat._to_local_path(dest_folder))
        return len(_compat.conflicting_names([_compat.Path(path) for path in paths], dest))

    @Slot(str, result=bool)
    def destinationFolderExists(self, dest_folder: str) -> bool:  # noqa: N802
        """Igaz, ha a célmappa még létezik a lemezen (#5177)."""
        _compat = _controller_module()
        local = _compat._to_local_path(dest_folder)
        return bool(local) and _compat.Path(local).is_dir()

    @Slot(list, str, str)
    def copyPhotos(self, paths: list, dest_folder: str, policy: str) -> None:
        """Kijelölés másolása a célmappába (#457/2), `policy` = rename|skip."""
        _compat = _controller_module()
        self._run_batch("copy", _compat.copy_photos, paths, dest_folder, policy)

    @Slot(list, str, str)
    def movePhotos(self, paths: list, dest_folder: str, policy: str) -> None:
        """Kijelölés áthelyezése a célmappába (#457/2).

        Az eredeti a KÉPEK áthelyezésére ugyanazt a rename/skip párbeszédet
        adta, mint a másolásra — ezért fut a kettő ugyanazon a magon.
        A már eltűnt célmappát csendben elutasítjuk: a mappasor és a lemez
        között a fájlfigyelő frissítése előtt rövid ideig eltérhet az állapot.
        """
        _compat = _controller_module()
        if not self.destinationFolderExists(dest_folder):
            return
        self._run_batch("move", _compat.move_photos, paths, dest_folder, policy)

    @Slot(list, str)
    @Slot(list, str, str, str, str, bool, str)
    def moveSelectionToNewFolder(
        self,
        paths: list,
        name: str,
        iso_date: str = "",
        location: str = "",
        description: str = "",
        use_music: bool = False,
        music_file: str = "",
    ) -> None:
        """Fájl ▸ Áthelyezés új mappába… (#1614, `ID_FILE_NEWFOLDER`).

        A parancs neve félrevezet: NEM mappát hoz létre önmagában, hanem a
        kijelölt képeket helyezi át egy ÚJ mappába, amit a felhasználó
        NEVEZ el — a helyét (a kijelölés ELSŐ elemének jelenlegi mappáját)
        a program választja. A Folder Properties párbeszéd a név mellett
        dátumot, zenét, helyet és leírást is kér; ezeket az új mappa
        .picasa.ini-jébe írjuk.

        A tényleges mozgatás a MEGLÉVŐ kötegelt úton fut (`_run_batch` →
        `move_photos`), pontosan úgy, mint a „Áthelyezés…" (#457): a
        `.picasa.ini` bejegyzések a képekkel költöznek, és a haladás-/
        összegző jelzés (`batchProgress`/`batchFinished`) is ugyanaz. Az
        index-frissítés a `wire_fileops` MÁR MEGLÉVŐ célzott resyncjén
        megy (`photoMoved` → `resyncFolder`) — ez a brand-new (még sosem
        indexelt) célmappát is kezeli, ahogy a #1522 másolás-tesztje is
        megméri.

        A mappa tulajdonságait az ini csomag meglévő
        update_document/mezőíró útján mentjük, a képek mozgatása előtt.

        Az új mappa nevét ELLENŐRIZZÜK, mielőtt bármi a lemezre kerülne
        (üres/csak szóköz/Windows-tiltott karakter — #1700 hibaosztálya),
        és azt is, hogy a célmappa MÁR NE létezzen — egyik hiba se essen
        némán, mindkettő az `operationFailed`-en át jut el a felhasználóhoz
        (`fileOpsErrorDialog`, ugyanaz a csatorna, mint minden más
        fájlművelet-hibánál)."""
        _compat = _controller_module()
        if not paths:
            self.operationFailed.emit(
                "move_to_new_folder", self.tr("Select at least one picture first.")
            )
            return
        try:
            folder_name = _compat.validate_folder_name(name)
        except _compat.InvalidFolderNameError as error:
            self.operationFailed.emit("move_to_new_folder", str(error))
            return
        parent = _compat.Path(_compat._to_local_path(paths[0]) or paths[0]).parent
        try:
            target = _compat.create_folder_for_move(parent, folder_name)

            def write_folder_properties(document):
                result = _compat.with_folder_date_override(document, iso_date)
                result = _compat.with_folder_music(
                    result, use_music, _compat.to_local_path(music_file)
                )
                result = (
                    result.with_value("Picasa", "location", location)
                    if location.strip()
                    else result.with_removed("Picasa", "location")
                )
                return (
                    result.with_value("Picasa", "description", description)
                    if description.strip()
                    else result.with_removed("Picasa", "description")
                )

            _compat.update_document(target / _compat.PICASA_INI_NAME, write_folder_properties)
        except _compat._OPERATION_ERRORS as error:
            self.operationFailed.emit("move_to_new_folder", str(error))
            return
        self._run_batch("move", _compat.move_photos, paths, str(target), _compat.RENAME)

    @Slot(list, str, str, str, str, bool, str)
    def splitFolderHere(
        self,
        paths: list,
        name: str,
        iso_date: str,
        location: str,
        description: str,
        use_music: bool,
        music_file: str,
    ) -> None:
        """A mappában kijelölt képtől a csoport végéig új testvérmappába tesz (#4534)."""
        _compat = _controller_module()
        if not paths:
            return
        source_paths = [
            _compat.Path(_compat._to_local_path(str(path)) or str(path)) for path in paths
        ]
        source_folder = source_paths[0].parent
        if any(path.parent != source_folder for path in source_paths):
            return
        try:
            target = _compat.create_unique_split_folder(source_folder.parent, name)

            def write_folder_metadata(document):
                result = _compat.with_folder_date_override(document, iso_date)
                result = _compat.with_folder_music(
                    result, use_music, _compat.to_local_path(music_file)
                )
                result = (
                    result.with_value("Picasa", "location", location)
                    if location.strip()
                    else result.with_removed("Picasa", "location")
                )
                return (
                    result.with_value("Picasa", "description", description)
                    if description.strip()
                    else result.with_removed("Picasa", "description")
                )

            _compat.update_document(target / _compat.PICASA_INI_NAME, write_folder_metadata)
            for source in source_paths:
                destination = _compat.move_photo(source, target)
                self.photoMoved.emit(str(source), str(destination))
            # A `.THM` kísérő a vele azonos nevű fájllal költözik — de csak ha
            # a forrásmappában nem marad azonos nevű másik fájl, amelyhez
            # szintén tartozhat (pl. a helyben maradó videó).
            for source in source_paths:
                for extension in (".THM", ".thm", ".Thm", ".tHm"):
                    companion = source.with_suffix(extension)
                    if not companion.is_file():
                        continue
                    marado = [
                        item
                        for item in source_folder.iterdir()
                        if item.stem == source.stem and item != companion
                    ]
                    if not marado:
                        _compat.safe_move(str(companion), str(target / companion.name))
                    break
        except _compat._OPERATION_ERRORS as error:
            self.operationFailed.emit("split_folder", str(error))

    def _run_batch(self, operation, function, paths, dest_folder, policy) -> None:
        _compat = _controller_module()
        dest = _compat.Path(_compat._to_local_path(dest_folder))

        paths_list = [_compat.Path(path) for path in paths]
        started = _compat.time.monotonic()
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
            elapsed = _compat.time.monotonic() - started
            speed = moved_bytes / elapsed if elapsed > 0 else 0.0
            self.batchProgress.emit(operation, str(dest), done, total, speed)

        try:
            result = function(paths_list, dest, policy, report)
        except _compat._OPERATION_ERRORS as error:
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
            _compat._first_failure_reason(result),
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
        _compat = _controller_module()
        target_text = _compat._to_local_path(dest_parent)
        if not target_text:
            self.operationFailed.emit("move_folder", self.tr("Choose a destination folder first."))
            return
        source = _compat.Path(_compat._to_local_path(folder) or folder)
        try:
            moved = _compat.move_folder(source, _compat.Path(target_text))
        except _compat.FolderMoveError as error:
            self.operationFailed.emit("move_folder", str(error))
            return
        # #1538: a NORMALIZÁLT forrás megy ki, nem a kapott nyers szöveg —
        # az `file://` URL-t a fogadó oldal nem tudná megtalálni.
        self.folderMoved.emit(str(source), str(moved))
