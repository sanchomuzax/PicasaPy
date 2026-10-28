"""A kollázskészítés belső műveletei a stabil `create_controller` felület mögött.

A modult a régi CreateMixin csak az első kollázsművelet idején importálja,
így nem növeli az alkalmazás indulási importláncát.
"""
from __future__ import annotations

from pathlib import Path

from . import create_controller as _legacy


class CollageCreationOperations:
    def _selected_sources(self, rows) -> tuple[Path, ...]:
        """A kijelölt sorokból forrás-útvonalak, a rács sorrendjében."""
        photos = self._photos.photos
        return tuple(
            Path(photos[int(r)].folder_path) / photos[int(r)].name
            for r in rows
            if 0 <= int(r) < len(photos)
        )

    def _tray_sources(self) -> tuple[Path, ...]:
        """A KÉPTÁLCA tartalma forrás-útvonalként, beszúrási sorrendben
        (#455, 3. teendő).

        Az eredetiben a tálca alatti műveletsor a tálca tartalmán futott,
        nem a pillanatnyi kijelölésen. A tálca mappákon átnyúlik, ezért itt
        nem rács-sorokból, hanem a `heldPaths`-ből dolgozunk — az a globális
        indexből olvas, és az időközben eltűnt képeket kihagyja.
        """
        return tuple(Path(path) for path in (self.heldPaths or ()))

    def _sources_for(self, rows) -> tuple[Path, ...]:
        """A művelet forrása: a TÁLCA, ha van benne kép; egyébként a
        kijelölés (így az üres tálcás, mai viselkedés nem romlik el)."""
        tray = self._tray_sources()
        return tray if tray else self._selected_sources(rows)

    def requestCollagePreview(self, rows, kind: str, border: str = _legacy.NOBORDER) -> None:
        """#920: élő előnézet a jelenlegi beállításokkal, háttérszálon.

        A Kollázs eddig VAKON dolgozott: a felhasználó választott, a program
        fájlba renderelt, és csak utána derült ki, mit kapott. Az eredetiben
        a panel jobb oldalán élő vászon áll.

        Az előnézet szándékosan KICSI (`_PREVIEW_SIZE`): a Képkupac pakolója
        időkorlátos keresést futtat, és a teljes felbontású renderelés minden
        csúszka-mozdulatnál használhatatlanná tenné a felületet.
        """
        self._ensure_collage_wired()
        sources = self._sources_for(rows)[:_legacy._MAX_ITEMS]
        if not sources:
            self._collage_preview.clear()
            self._collage_preview_revision += 1
            self.collagePreviewReady.emit(self._collage_preview_revision)
            return
        if kind not in _legacy.COLLAGE_THEMES or border not in _legacy.BORDER_THEMES:
            self.collagePreviewFailed.emit(self.tr("Unknown collage type."))
            return

        settings = _legacy.PicasaCollageSettings(
            theme=kind,
            border=border,
            width=_legacy._PREVIEW_SIZE[0],
            height=_legacy._PREVIEW_SIZE[1],
            seed=self._collage_seed,
        )

        def worker():
            try:
                report = _legacy.make_picasa_collage(sources, settings)
            except (ValueError, OSError) as error:
                self.collagePreviewFailed.emit(str(error))
                return
            self._collage_preview.set_image(report.image)
            # #960: az élő előnézet a SZERKESZTÉS állapota — a piszkozat
            # innen kapja a vászon valódi geometriáját
            self._save_collage_draft(report.nodes, settings)
            self._collage_preview_revision += 1
            self.collagePreviewReady.emit(self._collage_preview_revision)

        self._start_background(worker, name="picasapy-collage-preview")

    def shuffleCollage(self) -> None:
        """#920: a két véletlenszerűsítő gomb magja — új elrendezés ugyanazokból
        a képekből. A Képkupac szórása és a Mozaik pakolója is a magból dolgozik.
        """
        self._ensure_collage_wired()
        self._collage_seed += 1

    def makeCollage(self, rows, kind: str, target_url: str, border: str = _legacy.NOBORDER) -> None:
        """Kollázs a kijelölt képekből a megadott célfájlba (JPEG).

        `kind`: a `picasapy.collage.themes.COLLAGE_THEMES` egyike — a HAT
        Picasa-elrendezés. `border`: a `BORDER_THEMES` egyike.

        **#431: ez a slot a #29-es, saját tervezésű négy elrendezésről a
        Picasa-hű hatra állt át.** A mag (`picasa_render`) 2026-08-16 óta
        készen állt, de senki nem hívta — a felület a régi rajzolót
        használta, tehát a kollázs működött, csak nem a Picasa
        elrendezéseivel.
        """
        self._ensure_collage_wired()
        # #1539: a bekötés a GUI-szálon, a háttérszál indítása ELŐTT
        self._ensure_output_resync_wired()
        if rows and isinstance(rows[0], str):
            sources = tuple(Path(_legacy.to_local_path(str(row))) for row in rows)[:_legacy._MAX_ITEMS]
        else:
            sources = self._sources_for(rows)[:_legacy._MAX_ITEMS]
        target = _legacy.to_local_path(target_url)
        if not sources:
            self.collageFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            self.collageFailed.emit(self.tr("No target file was chosen."))
            return
        if kind not in _legacy.COLLAGE_THEMES:
            self.collageFailed.emit(self.tr("Unknown collage type."))
            return
        if border not in _legacy.BORDER_THEMES:
            self.collageFailed.emit(self.tr("Unknown picture frame."))
            return

        settings = _legacy.PicasaCollageSettings(
            theme=kind,
            border=border,
            width=_legacy._COLLAGE_SIZE[0],
            height=_legacy._COLLAGE_SIZE[1],
            # #920: amit az előnézeten LÁT, azt kapja mentéskor is
            seed=self._collage_seed,
        )

        def worker():
            try:
                report = _legacy.make_picasa_collage(sources, settings)
                if not report.used:
                    self.collageFailed.emit(
                        self.tr("None of the selected pictures could be read.")
                    )
                    return
                # #960: a piszkozat a mentés ELŐTT készül el — épp az az
                # eset a lényeg, amikor a hosszú írás közben vész el minden
                self._save_collage_draft(report.nodes, settings)
                path = _legacy.write_collage(Path(target), report.image)
            except (ValueError, OSError) as error:
                self.collageFailed.emit(str(error))
                return
            # a mentés sikerült: a piszkozat betöltötte a szerepét
            self._drop_collage_draft()
            # #1539: a kollázs a figyelt gyökér alatti, MÉG NEM INDEXELT
            # mappába is mehet (a fájlválasztó nincs korlátozva). Mérve: a
            # figyelő nélkül 25 s alatt sem jelent meg — a #1275 lekérdezés
            # a LÁTOTT mappát nézi, a kollázs viszont egy másikba került.
            self.noteOutputWritten(str(path))
            self.collageFinished.emit(
                str(path),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-collage")
