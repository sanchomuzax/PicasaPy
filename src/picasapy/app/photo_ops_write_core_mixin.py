"""A fotóíró mixin háttérírási és frissítési segédjei."""

from __future__ import annotations

from picasapy.index import open_index, photo_by_id, search_photos, update_photo_fields

from .photo_ops_compat import _WRITE_ERRORS


class PhotoOpsWriteCoreMixin:

    def _ensure_broken_photo_wired(self) -> None:
        """#459: a ThumbnailProvider `brokenImageDetected`-jét a photo-id
        alapján a REGISZTRÁLT (jelenleg betöltött) fotóra oldja fel, és
        — fotónként EGYSZER — továbbítja a QML-nek. Külön a
        `_ensure_photo_ops_wired`-től: ez böngészés közben, bármilyen
        szerkesztés NÉLKÜL is bekövetkezhet, ezért a controller
        konstruktora hívja MÁR a `self._provider` beállítása után, nem
        lustán az első íráskor."""
        if getattr(self, "_broken_photo_wired", False):
            return
        self._broken_photo_wired = True
        self._broken_photo_ids: set[int] = set()
        self._provider.brokenImageDetected.connect(self._on_broken_image_detected)

    def _ensure_photo_ops_wired(self) -> None:
        """A jelzések bekötése lusta, egyszeri — így a controller.py
        (forró fájl) __init__-jét nem kell módosítani (#150 mintakövetés:
        az integrátor köti be a végleges osztályt, a szelet önmagában is
        működőképes)."""
        if getattr(self, "_photo_ops_wired", False):
            return
        self._photo_ops_wired = True
        self._photoFieldUpdated.connect(self._on_photo_field_updated)
        self.photoOpFailed.connect(self._on_photo_write_failed)
        self._renameBatchDone.connect(self._on_rename_batch_done)
        self._photoWriteAborted.connect(self._on_photo_write_aborted)
        #: #3830: az egyképes forgatás (`rotateRight`/`rotateLeft`) FUTÓ
        #: írásainak és a rájuk közben érkezett újabb célértékeknek a
        #: nyilvántartása — ld. `_apply_rotate`.
        self._rotate_running: set[int] = set()
        self._rotate_target: dict[int, int] = {}

    def jelentsdAzIrasiHibat(self, error: BaseException | str) -> None:
        """Ini-írási hiba a LÁTHATÓ csatornán (#2506).

        ⚠️ A `photoOpFailed` önmagában NEM elég: a `syncFailed`-re (és így a
        `Main.qml` `errorBanner`-ére, #459) csak az
        `_ensure_photo_ops_wired()` köti rá, azt viszont eddig kizárólag a
        FOTÓ-írás útja hívta (`_run_photo_write`). Ha a felhasználó első
        művelete egy mappa-leírás, egy mappa-dátum vagy egy címke volt, a
        jelzés bekötetlen csatornára ment: a hiba jelezve volt, és mégsem
        látszott semmi. Ezért köt be ez a segéd, mielőtt emittál.
        """
        self._ensure_photo_ops_wired()
        self.photoOpFailed.emit(str(error))

    def _run_photo_write(
        self, photo_id: int, perform, after=None, on_error=None
    ) -> None:
        """Ini/IPTC-írás (NAS: backup+temp+fsync) + célzott index-UPDATE
        háttérszálon (#141). A `perform()` a teljes lassú munkát végzi (fájl-
        írás + a {oszlop: érték} dict összeállítása), és teljes egészében a
        munkásszálon fut. #505: a busy-jelzést a `_start_background`
        (`worker_thread.py`) intézi, nem itt.

        `after`: opcionális utómunka (#1443), amit a GUI-szálon, a rács-sor
        frissítése után hívunk. Írási hiba esetén NEM fut le — olyankor a
        nézet tartalma sem változott. A forgatás utómunkája a következő
        célértéket új háttérmunkában írja ki.
        `on_error`: opcionális hiba-utómunka (#3830) a GUI-szálon — a
        várt írási hibánál (`_WRITE_ERRORS`) ÉS nem várt kivételnél is
        lefut, hogy a hívó eldobhassa a függő állapotát."""
        self._ensure_photo_ops_wired()

        def hiba_utomunka() -> None:
            if on_error is not None:
                self._photoWriteAborted.emit(on_error)

        def worker() -> None:
            try:
                fields = perform()
                with open_index(self._db_path) as conn:
                    if fields:
                        update_photo_fields(conn, photo_id, **fields)
                    record = photo_by_id(conn, photo_id)
            except _WRITE_ERRORS as error:
                hiba_utomunka()
                self.photoOpFailed.emit(str(error))
                return
            except BaseException:
                hiba_utomunka()
                raise
            self._photoFieldUpdated.emit(photo_id, record, after)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-photowrite")

    def _run_photo_writes(self, jobs, after=None, on_error=None) -> None:
        """Több kép írása SOROSAN, EGYETLEN háttérszálon (#2915).

        Képenként külön szálat indítani versenyhelyzet: a kijelölés képei
        jellemzően EGY mappában vannak, tehát ugyanabba a `.picasa.ini`-be
        és ugyanabba az indexbe írnak. A windowsos CI ki is mutatta: a
        kijelölés egy része felirat nélkül maradt. A soros út mellékesen a
        NAS-t is kíméli (N párhuzamos backup+temp+fsync helyett egy), és a
        `_apply_batch`-hez hasonlóan EGY index-kapcsolatot használ.

        `jobs`: `(photo_id, perform)` párok; a `perform()` a teljes lassú
        munka, ugyanúgy, mint a `_run_photo_write`-nál. Az `after` utómunka
        a GUI-szálon, a KÖTEG végén fut le egyszer. Az `on_error` lezáró
        visszahívás bármilyen workerhiba esetén lefut.
        """
        self._ensure_photo_ops_wired()
        jobs = tuple(jobs)
        if not jobs:
            return

        def worker() -> None:
            try:
                with open_index(self._db_path) as conn:
                    for index, (photo_id, perform) in enumerate(jobs):
                        fields = perform()
                        if fields:
                            update_photo_fields(conn, photo_id, **fields)
                        record = photo_by_id(conn, photo_id)
                        utolso = index == len(jobs) - 1
                        self._photoFieldUpdated.emit(
                            photo_id, record, after if utolso else None
                        )
            except _WRITE_ERRORS as error:
                self.photoOpFailed.emit(str(error))
                if on_error is not None:
                    on_error()
            except BaseException:
                if on_error is not None:
                    on_error()
                raise

        self._start_background(worker, name="picasapy-photowrite-koteg")

    def _refresh_if_star_filtered(self) -> None:
        """Újralekérdezés, ha a csillag a jelen nézet tagságát dönti el.

        Szándékosan lekérdezés (`_refresh_view`) és nem sor-eltávolítás: így
        a visszacsillagozás is magától bekerül, és a zöld eredménysáv
        darabszáma is követ."""
        if self._view_mode[0] in self._CSILLAG_SZURT_NEZETEK:
            self._refresh_view()

    def _refresh_if_dropped_from_search(self, photo_id: int) -> None:
        """Újralekérdezés, ha a kép KIESETT az aktuális keresés találatai
        közül (#1515) — pl. mert töröltük a feliratot, ami miatt találat volt.

        **Miért nem kérdezzük újra mindig?** Mérve, valósághű indexen
        (140 755 kép / 3 000 mappa, a felhasználó gyűjteményének mérete):
        a teljes `search_photos` medián **597 ms** egy 27 179 találatos
        kulcsszónál, míg az EGY KÉPRE szűkített, ugyanazon a kódúton futó
        tagság-lekérdezés **6–11 ms**. A költséget a találatszám (a
        rekordépítés) viszi, nem az SQL, ezért a feliratmentésenkénti teljes
        újralekérdezés a felhasználó gyűjteményén fél másodperces
        akadásokat okozna. Összehasonlításul a #1443 csillag-nézete
        162 ms — az volt még kifizethető, ez már nem.

        **Bekerülést nem kell vizsgálni:** a szerkesztett kép a művelet
        pillanatában LÁTSZIK a rácson (a `setCaption` sorszámot kap a
        `self._photos` listájából), tehát biztosan találat VOLT. Csak az a
        kérdés maradt, találat-e még.

        Szándékosan `_refresh_view()` és nem sor-eltávolítás: így a bal
        hasáb „Search results for … (N)" darabszáma és a találatos mappák
        listája is követ, és a visszaadott felirat magától visszahozza a
        képet."""
        mode, param = self._view_mode
        if mode not in self._KERESES_SZURT_NEZETEK:
            return
        query = param if mode == "search" else param[0]
        with open_index(self._db_path) as conn:
            if search_photos(conn, query, only_id=photo_id):
                return  # találat maradt — a sor frissítése elég volt
        self._refresh_view()
