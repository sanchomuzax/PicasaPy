"""A FileOpsController open mixin felelősségének mixinje."""

from __future__ import annotations

from importlib import import_module

from PySide6.QtCore import Slot


def _controller_module():
    """A régi modul fogantyúihoz irányít, monkeypatch-kompatibilisen."""
    return import_module("picasapy.app.fileops_controller")


class FileOpsControllerOpenMixin:
    @Slot(str, result=str)
    def toLocalPath(self, path_or_url: str) -> str:  # noqa: N802 — QML-stílus
        r"""`file://` URL vagy sima útvonal → OS-NATÍV alak, MEGJELENÍTÉSRE.

        #1629: három párbeszéd a `file://` előtagot szöveges cserével
        vágta le, ami Windowson `/C:/Users/…`-t hagy maga után — a
        felhasználó `C:\Users\…`-t vár. Tisztán QML-ből ez nem
        megoldható: a `QUrl.toLocalFile()` a meghajtóbetű elé tett
        perjelet CSAK Windowson szedi le (mérve a #1626-ban).

        A tényleges munkát a #1626 `formatting.to_local_path`-ja végzi —
        EGYETLEN helyen, a `_platform()` fogantyún át, hogy a windowsos ág
        Linuxon is mérhető maradjon."""
        _compat = _controller_module()
        return _compat.to_local_path(path_or_url)

    @Slot(str)
    def revealPhoto(self, path: str) -> None:
        """A fájlt tartalmazó mappa megnyitása a fájlkezelőben.

        Sikertelen megnyitás (hiányzó `xdg-open` vagy nemnulla kilépési
        kód) esetén `operationFailed`-et jelez, hogy a felhasználó ne
        maradjon visszajelzés nélkül (#112)."""
        _compat = _controller_module()
        try:
            _compat.reveal_in_file_manager(_compat.Path(path))
        except OSError as error:
            self.operationFailed.emit("reveal", str(error))

    @Slot(str, result=bool)
    def hasOriginalOnDisk(self, path: str) -> bool:  # noqa: N802
        """Van-e a képnek megőrzött EREDETIJE a `.picasaoriginals`-ban (#1613).

        Az „Eredeti a lemezen" tétel ettől él vagy szürkül: az eredetiben is
        letiltott, ha nincs mit megmutatni."""
        _compat = _controller_module()
        cel = _compat._to_local_path(path) or path
        if not cel:
            return False
        return _compat.find_original_backup(_compat.Path(cel)) is not None

    @Slot(str)
    def revealOriginal(self, path: str) -> None:  # noqa: N802
        """A `.picasaoriginals`-beli EREDETI megmutatása a fájlkezelőben (#1613).

        Az eredeti `CThumbUI::locateorigondiskmenu_win` parancsa. Nem a
        szerkesztett fájlt mutatja meg — épp az a lényege, hogy a megőrzött
        eredetihez lehessen eljutni.

        Ha nincs eredeti, a felhasználó üzenetet kap; a menütétel ilyenkor
        amúgy is szürke (`hasOriginalOnDisk`), de a néma bukást akkor sem
        engedjük, ha valaki mégis idejut."""
        _compat = _controller_module()
        cel = _compat._to_local_path(path) or path
        eredeti = _compat.find_original_backup(_compat.Path(cel)) if cel else None
        if eredeti is None:
            self.operationFailed.emit(
                "locate_original",
                self.tr("This picture has no preserved original on disk."),
            )
            return
        try:
            _compat.reveal_in_file_manager(eredeti)
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
        _compat = _controller_module()
        local = _compat._to_local_path(folder_path)
        if not local:
            return
        try:
            _compat.open_folder_in_file_manager(_compat.Path(local))
        except OSError as error:
            self.operationFailed.emit("reveal", str(error))

    @Slot(str)
    def openPhoto(self, path: str) -> None:
        """A fájl megnyitása a rendszer társított alkalmazásával (#422:
        „Fájl megnyitása", `Ctrl+Shift+O` a néző kontextusmenüjében).

        A `revealPhoto` párja: az a fájlkezelőt nyitja a fájlra, ez magát a
        fájlt adja át a társított programnak. Hiba esetén ugyanúgy
        `operationFailed`, nem kivétel a QML felé (#112)."""
        _compat = _controller_module()
        local = _compat._to_local_path(path)
        if not local or not _compat.Path(local).exists():
            self.operationFailed.emit("open", f"nincs ilyen fájl: {path}")
            return
        if not _compat.QDesktopServices.openUrl(_compat.QUrl.fromLocalFile(local)):
            self.operationFailed.emit("open", f"nem sikerült megnyitni: {local}")

    @Slot(result=bool)
    def hasNativeOpenWith(self) -> bool:  # noqa: N802 — QML-név
        """#4533: Windowson a héj saját „Megnyitás ezzel" párbeszéde van, nem
        a mi választónk. A QML ilyenkor a `openWithNative`-ot hívja."""
        _compat = _controller_module()
        return _compat.open_with.has_native_open_with()

    @Slot(str)
    def openWithNative(self, path: str) -> None:
        """#4533: a Windows héj „Megnyitás ezzel" párbeszédét nyitja a fájlra."""
        _compat = _controller_module()
        local = _compat._to_local_path(path)
        if not local or not _compat.Path(local).is_file():
            self.operationFailed.emit("open", f"nincs ilyen fájl: {path}")
            return
        try:
            _compat.open_with.open_with_dialog_windows(_compat.Path(local))
        except OSError:
            self.operationFailed.emit("open", self.tr("Unable to open application"))

    @Slot(str, result="QVariantList")
    def openWithChoices(self, path: str) -> list[dict]:
        """#4533: a fájltípushoz társított alkalmazások a „Társítás…" választónak
        (`id`, `name`). Nem létező fájlnál üres lista."""
        _compat = _controller_module()
        local = _compat._to_local_path(path)
        if not local or not _compat.Path(local).is_file():
            return []
        return [
            {"id": app.app_id, "name": app.name}
            for app in _compat.open_with.apps_for_file(_compat.Path(local))
        ]

    @Slot(str, str)
    def openWithApp(self, path: str, app_id: str) -> None:
        """#4533: a kijelölt alkalmazással nyitja meg a fájlt. A listát újra
        lekérdezi, így a választó nem tart a lemezen kívül állapotot."""
        _compat = _controller_module()
        local = _compat._to_local_path(path)
        if not local or not _compat.Path(local).is_file():
            self.operationFailed.emit("open", f"nincs ilyen fájl: {path}")
            return
        app = next(
            (a for a in _compat.open_with.apps_for_file(_compat.Path(local)) if a.app_id == app_id),
            None,
        )
        if app is None:
            self.operationFailed.emit("open", self.tr("Unable to open application"))
            return
        try:
            _compat.open_with.launch_app(app, _compat.Path(local))
        except OSError:
            self.operationFailed.emit("open", self.tr("Unable to open application"))

    @Slot(list)
    def openPhotosInDefaultEditor(self, paths: list[str]) -> None:
        """A kijelölt képeket a rendszer fájltársításán keresztül nyitja meg
        (#4330).

        A spec nem nevez meg külön szerkesztőprogram-beállítást, ezért a
        Qt-n keresztül az operációs rendszer alapértelmezett alkalmazását
        kérjük megnyitásra. Több fájlnál fájlonként küldünk kérést; az
        elutasított vagy hiányzó fájlokat egyetlen, darabszámos hibajelzés
        foglalja össze.
        """
        _compat = _controller_module()
        kijelolt = list(paths or [])
        if not kijelolt:
            return

        sikertelen = 0
        for path in kijelolt:
            local = _compat._to_local_path(str(path))
            if not local or not _compat.Path(local).is_file():
                sikertelen += 1
                continue
            try:
                megnyitotta = _compat._open_url(_compat.QUrl.fromLocalFile(local))
            except OSError:
                megnyitotta = False
            if not megnyitotta:
                sikertelen += 1

        if sikertelen:
            uzenet = self.tr("The system default application could not open %1/%2 selected files.")
            uzenet = uzenet.replace("%1", str(sikertelen)).replace("%2", str(len(kijelolt)))
            self.operationFailed.emit("open_editor", uzenet)

    @Slot(str)
    def copyFullPath(self, path: str) -> None:
        """A teljes elérési út a vágólapra (#422: „Teljes elérési út
        másolása"). Vágólap hiányában (fej nélküli környezet) csendben
        kimarad — nem hibaág, csak nincs hova másolni."""
        _compat = _controller_module()
        local = _compat._to_local_path(path)
        if not local:
            return
        clipboard = _compat.QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(local)
