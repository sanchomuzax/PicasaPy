"""A FileOpsController clipboard mixin felelősségének mixinje."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

from PySide6.QtCore import QMimeData, Slot


def _controller_module():
    """A régi modul fogantyúihoz irányít, monkeypatch-kompatibilisen."""
    return import_module("picasapy.app.fileops_controller")


class FileOpsControllerClipboardMixin:
    def _paste_folder_identities(self, folder_paths: list[str]) -> dict:
        """Mappaút-kulcs -> azonosító: az indexbeli mappa-id, ennek híján az út."""
        from picasapy.paths import normalize_path, path_key

        normalizalt_utak = {}
        for path in folder_paths:
            normalizalt = normalize_path(path)
            normalizalt_utak.setdefault(path_key(normalizalt), normalizalt)

        azonositok = {kulcs: ("path", kulcs) for kulcs in normalizalt_utak}
        database = getattr(self, "_library_db_path", None)
        if database:
            from picasapy.index import open_index

            with open_index(database) as conn:
                for kulcs, path in normalizalt_utak.items():
                    row = conn.execute(
                        "SELECT id FROM folders WHERE path = ?", (path,)
                    ).fetchone()
                    if row is not None:
                        azonositok[kulcs] = ("id", int(row["id"]))
        return azonositok

    def _paste_sources_outside(self, paths: list[str], dest_folder: str) -> list[str]:
        """A vágólap azon fájljai, amelyek mappaazonosítója eltér a céltól (#7143).

        Az eredeti a Beillesztést csak eltérő forrás- és célmappánál futtatja
        (`0x0056ec92`, `0x00784100`); azonos mappában nincs fájlművelet. A
        PicasaPy vágólapján külső program vegyes mappájú fájljai is lehetnek,
        ezért fájlonként döntünk: a célmappában már ott lévő fájl kimarad."""
        _compat = _controller_module()
        from picasapy.paths import normalize_path, path_key

        destination = _compat._to_local_path(dest_folder) or dest_folder
        forras_mappak = [
            str(Path(_compat._to_local_path(path) or path).parent) for path in paths
        ]
        azonositok = self._paste_folder_identities([destination, *forras_mappak])
        celazonosito = azonositok[path_key(normalize_path(destination))]
        return [
            path
            for path, mappa in zip(paths, forras_mappak, strict=True)
            if azonositok[path_key(normalize_path(mappa))] != celazonosito
        ]

    def _paste_has_different_folder(self, paths: list[str], dest_folder: str) -> bool:
        """Igaz, ha legalább egy forrásmappa azonosítója eltér a céltól."""
        return bool(self._paste_sources_outside(paths, dest_folder))

    @Slot(str, result=bool)
    def clipboardOnlyInFolder(self, dest_folder: str) -> bool:  # noqa: N802
        """Igaz, ha a vágólap fájljai MIND a megadott mappában vannak (#7143).

        Ilyenkor a Beillesztés az eredeti szerint szürke és hatástalan (nincs
        fájlművelet, `0x0056ec92`). Üres vágólapra és üres célra hamis: az
        előbbinél a tétel amúgy is szürke, az utóbbinál a cél nélküli üzenet
        (`IDS_NEED_SELECTED_ALBUM`) dolga a jelzés."""
        if not dest_folder:
            return False
        fajlok, _muvelet = _controller_module().vagolap_fajlok(self._vagolap_adata())
        if not fajlok:
            return False
        # A QML-kötés a nézetállapot minden változására újraértékeli ezt a
        # kaput, az azonosítókeresés pedig az indexet nyitja: egy bejegyzéses
        # memo elég, a kulcs a vágólap tartalma és a célmappa.
        kulcs = (tuple(fajlok), dest_folder)
        if getattr(self, "_vagolap_kapu_memo", (None, None))[0] != kulcs:
            self._vagolap_kapu_memo = (
                kulcs,
                not self._paste_sources_outside(fajlok, dest_folder),
            )
        return self._vagolap_kapu_memo[1]

    def _tegyd_a_vagolapra(self, paths, muvelet: str) -> None:
        """A megadott fájlok a vágólapra, `copy`/`cut` jelzéssel (#1526).

        A binárisból mérve: a Picasa a Windows shell-fájlátvitel
        formátumait teszi fel, köztük a **`Preferred DropEffect`**-et — ez
        bizonyítja, hogy a Kivágás és a Másolás UGYANAZT az adatot teszi
        fel, és csak ez a formátum különbözteti meg őket.

        Linuxon ennek a párja az `x-special/gnome-copied-files`, aminek az
        ELSŐ sora `copy` vagy `cut`. A `text/uri-list`-et is feltesszük,
        mert azt minden fájlkezelő érti.

        Az időközben eltűnt fájl kimarad: a beillesztés ott hibára futna, és
        a felhasználó nem értené, miért. Üres listára nem nyúlunk a
        vágólaphoz — ne söpörjük el, ami rajta van."""
        _compat = _controller_module()
        letezok = [_compat.Path(_compat._to_local_path(p) or p) for p in paths or ()]
        letezok = [p for p in letezok if p.exists()]
        if not letezok:
            return

        def epits() -> QMimeData:
            adat = _compat.QMimeData()
            urlek = [_compat.QUrl.fromLocalFile(str(p)) for p in letezok]
            adat.setUrls(urlek)
            sorok = [muvelet, *(u.toString() for u in urlek)]
            adat.setData(
                _compat._GNOME_VAGOLAP_FORMATUM,
                _compat.QByteArray("\n".join(sorok).encode("utf-8")),
            )
            return adat

        # ⚠️ KÉT KÜLÖN példány, szándékosan. A `setMimeData` ÁTVESZI a
        # tulajdonjogot: a Qt a vágólapra tett objektumot a következő
        # vágólap-művelettel törli. Ha ugyanarra a példányra Python-oldali
        # referenciát is tartanánk, az a törlés után halott objektumra
        # mutatna — CI-n ez SZEGMENSHIBÁVAL (`exit -11`) állította meg a
        # tesztfájlt, nem szép hibaüzenettel.
        self._vagolap_adat = epits()

        # ⚠️ FEJ NÉLKÜLI KÖRNYEZETBEN NEM ÍRUNK a vágólapra. Az `offscreen`
        # és a `minimal` Qt-platform teszt-/CI-környezet: nincs mögötte
        # vágólap-tulajdonos, és a `setMimeData` ott a CI-n
        # SZEGMENSHIBÁVAL állította meg a tesztfájlt (`exit -11`) — nem
        # kivétellel, amit el lehetne kapni. Helyben (valódi
        # munkamenet-kezelővel) ugyanez lefut, ezért a hiba csak a CI-n
        # jött elő.
        #
        # A művelet így sem lesz néma: a `_vagolap_adat` mindig elkészül,
        # tehát az őr azt méri, AMIT feltennénk — a valódi vágólapra írás
        # pedig ott történik meg, ahol van vágólap.
        self.clipboardFilesChanged.emit()
        if _compat.QGuiApplication.platformName() in ("offscreen", "minimal"):
            return
        vagolap = _compat.QGuiApplication.clipboard()
        if vagolap is not None:
            vagolap.setMimeData(epits())

    @Slot(list)
    def copyFilesToClipboard(self, paths) -> None:  # noqa: N802
        """A kijelölt képek fájljai a vágólapra, MÁSOLÁSKÉNT (#1526)."""
        self._tegyd_a_vagolapra(paths, "copy")

    @Slot(list)
    def cutFilesToClipboard(self, paths) -> None:  # noqa: N802
        """Ugyanaz, de MOZGATÁSKÉNT — a `Preferred DropEffect` párja."""
        self._tegyd_a_vagolapra(paths, "cut")

    def _vagolap_adata(self):
        """A vágólap tartalma — a próbák EZT a metódust térítik el.

        Fej nélküli környezetben (`offscreen`/`minimal`) a saját, legutóbb
        létrehozott MIME-adatot olvassuk vissza. A Qt-rendszervágólaphoz nem
        nyúlunk: ott nincs tulajdonos, és a natív lekérdezés a CI-n
        szegmenshibát okozott."""
        _compat = _controller_module()
        if _compat.QGuiApplication.platformName() in ("offscreen", "minimal"):
            return self._vagolap_adat
        vagolap = _compat.QGuiApplication.clipboard()
        return None if vagolap is None else vagolap.mimeData()

    @Slot(str, list, str, str)
    def runPasteBatch(  # noqa: N802
        self, operation: str, paths: list, dest_folder: str, policy: str
    ) -> None:
        """A jóváhagyott Beillesztés köteg (#7112), a választott ütközési
        szabállyal; az első végleges fájlhibánál megáll (#7114)."""
        if operation == "cut" or operation == "move":
            eredmeny = self._move_batch(paths, dest_folder, policy, stop_on_failure=True)
        else:
            eredmeny = self._copy_batch(paths, dest_folder, policy, stop_on_failure=True)
        self._urit_sikeres_beillesztes_utan(eredmeny, paths)

    def _urit_sikeres_beillesztes_utan(self, eredmeny, fajlok) -> None:
        """A köteg hibátlan lefutása után a SAJÁT vágólap kiürül (#7143).

        Az eredetiben a sikeres beillesztés a belső listát kiüríti, a Mégse
        megtartja (`0x005feaeb-0x005feb05`). Hibás vagy el sem indult köteg
        (`None`) után a lista marad, hogy a felhasználó újra próbálhassa."""
        if eredmeny is None or eredmeny.failed:
            return
        self._urit_a_sajat_vagolapot(fajlok)

    def _urit_a_sajat_vagolapot(self, fajlok) -> None:
        """Kiüríti a PicasaPy saját fájl-vágólapját, ha még azt a tartalmat hordja.

        Csak ami a miénk: fej nélküli környezetben a `_vagolap_adat` mindig a
        saját adatunk; valódi munkamenetben a rendszervágólapot csak akkor
        töröljük, ha mi birtokoljuk (`ownsClipboard`). Külső program (fájlkezelő,
        böngésző) vágólapjához nem nyúlunk: az a PicasaPy felülhalmaza. Ha időközben
        új Másolás történt (más fájlok vannak a vágólapon, mint a beillesztetteké),
        azt sem töröljük."""
        _compat = _controller_module()
        from picasapy.paths import normalize_path, path_key

        def kulcsok(utak) -> set:
            return {path_key(normalize_path(str(path))) for path in utak}

        aktualis, _muvelet = _compat.vagolap_fajlok(self._vagolap_adata())
        if not aktualis or not kulcsok(fajlok) <= kulcsok(aktualis):
            return
        if _compat.QGuiApplication.platformName() not in ("offscreen", "minimal"):
            vagolap = _compat.QGuiApplication.clipboard()
            if vagolap is None or not vagolap.ownsClipboard():
                return
            vagolap.clear()
        self._vagolap_adat = None
        self.clipboardFilesChanged.emit()

    def _paste_into_album(self, fajlok: list[str], album_token: str) -> bool:
        """A vágólap képei az album tagjai lesznek, fájlművelet nélkül (#7142).

        Az írót a `wire_fileops` köti be (`_album_tagsag_iro`, a vezérlő
        `addPathsToAlbum`-ja): a `.picasa.ini`-t az `ini` API-n át a
        meglévő albumtagság-út írja. Bekötetlen íróval NEM esünk vissza a
        fájlműveletre: albumnézetben az tilos, és a hívó az üres eredményből
        üzenetet ad. `True`, ha volt a könyvtárban kép (a művelet elindult)."""
        iro = getattr(self, "_album_tagsag_iro", None)
        if iro is None:
            return False
        return bool(iro(fajlok, album_token))

    @Slot(str, result=bool)
    @Slot(str, bool, result=bool)
    @Slot(str, bool, str, result=bool)
    def pasteFilesFromClipboard(  # noqa: N802
        self,
        dest_folder: str,
        ordinary_folder_target: bool = True,
        album_token: str = "",
    ) -> bool:
        """A vágólapon lévő fájlok beillesztése a megadott mappába (#1526).

        A `cut` jelzésű tartalom ÁTHELYEZ, a `copy` MÁSOL. A meglévő
        köteg-utakat hívja (`_copy_batch`/`_move_batch`, a `copyPhotos`/
        `movePhotos` slotok közös magját), tehát az
        ütközéskezelés, a haladásjelzés és az összegző jelzés ugyanaz, mint a
        fogd-és-vidd műveleteknél — nem külön ág, amit külön kellene őrizni.

        Visszatérés: elindult-e művelet. Üres vágólapra `False`, és a hívó
        ebből tud üzenetet adni, tehát a hatástalanság nem néma.

        #7142: közönséges album célnál (`album_token`) az eredeti
        `0x00784100` kihagyja a fájlműveleti ágat: nincs megerősítő kérdés
        és nincs másolás/áthelyezés, a képek az album tagjai lesznek, a
        Kivágás sem töröl a forrásból (`_paste_into_album`). Ilyenkor a
        `dest_folder` és az `ordinary_folder_target` figyelmen kívül marad."""
        _compat = _controller_module()
        fajlok, muvelet = _compat.vagolap_fajlok(self._vagolap_adata())
        if album_token:
            beillesztve = bool(fajlok) and self._paste_into_album(fajlok, album_token)
            if beillesztve:
                self._urit_a_sajat_vagolapot(fajlok)
            return beillesztve
        if not fajlok or not dest_folder:
            return False
        # #7143: azonos mappában nincs fájlművelet (`0x0056ec92`): a célmappában
        # már ott lévő fájl kimarad, és ha minden ilyen, a Beillesztés
        # hatástalan. Fizikai másolat (`név-1`) azonos mappába nem készül.
        fajlok = self._paste_sources_outside(fajlok, dest_folder)
        if not fajlok:
            return False
        # ⚠️ `rename`, nem `skip` és nem felülírás: ütközésnél a beillesztés
        # ÚJ nevet ad, tehát semmi nem vész el. Az eredeti ilyenkor
        # párbeszédet nyit (ugyanazt a rename/skip kérdést, mint az
        # áthelyezésnél); a párbeszéd bekötése önálló lépés, de a
        # felülírás-mentesség nem várhat rá.
        #
        # #7114: a Beillesztés köteg az ELSŐ végleges fájlhibánál megáll
        # (az eredeti `0x005350b0` ciklusa a `0xf4242` eredménynél kilép):
        # a korábbi másolatok megmaradnak, a későbbi képeket el sem kezdi, és
        # EGY összegző jelzés (`batchFinished`) nevezi meg a hibát. A
        # fogd-és-vidd és a menüs köteg (#301/#459) ettől függetlenül
        # folytatja a hibás kép után.
        # #7112: eltérő mappaazonosítónál a felület csak a felhasználói
        # jóváhagyás után indítja a köteget és annak ütközésválasztóját.
        if ordinary_folder_target and self._paste_has_different_folder(
            fajlok, dest_folder
        ):
            self.clipboardPasteConfirmationRequested.emit(
                fajlok, dest_folder, muvelet
            )
            return True

        # Nem közönséges mappacél (keresés, címke stb.): nincs megerősítés,
        # a köteg azonnal indul, és hibátlan lefutás után a vágólap ürül.
        if muvelet == "cut":
            eredmeny = self._move_batch(
                fajlok, dest_folder, "rename", stop_on_failure=True
            )
        else:
            eredmeny = self._copy_batch(
                fajlok, dest_folder, "rename", stop_on_failure=True
            )
        self._urit_sikeres_beillesztes_utan(eredmeny, fajlok)
        return True
