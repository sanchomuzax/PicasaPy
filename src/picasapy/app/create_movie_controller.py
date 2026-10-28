"""A filmkészítés belső műveletei a stabil `create_controller` felület mögött.

A modult a régi CreateMixin csak az első filmbeállítás vagy művelet idején
importálja, így nem növeli az alkalmazás indulási importláncát.
"""
from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImageReader
from picasapy.app.movie_preview import MovieTransitionPreviewProvider
from picasapy.movie.mxf import MxfAtmenet, MxfForras, MxfProjekt, MxfSzovegParam

from . import create_controller as _legacy


class MovieCreationOperations:
    def movieResolutionIndex(self) -> int:  # noqa: N802
        """A normál film méretindexe (`Preferences\\makemovieres`)."""
        try:
            return max(0, min(6, int(self._get_settings().value("makemovieres", 1))))
        except (TypeError, ValueError):
            return 1

    def faceMovieResolutionIndex(self) -> int:  # noqa: N802
        """Az arc-film méretindexe (`facemakemovieres`), alapból 3 (#4391).

        A Picasa ezt a kulcsot olvassa, de a beállított új értéket nem írja
        vissza; a QML-ben is megmarad ez a nem mentő viselkedés.
        """
        try:
            return max(
                0,
                min(6, int(self._get_settings().value("facemakemovieres", 3))),
            )
        except (TypeError, ValueError):
            return 3

    def setMovieResolutionIndex(self, index: int) -> None:  # noqa: N802
        """A hét eredeti méret közül a választott index megőrzése."""
        index = max(0, min(6, int(index)))
        self._get_settings().setValue("makemovieres", index)
        self.moviePreferencesChanged.emit()

    def movieSlideDuration(self) -> float:  # noqa: N802
        """A filmkészítő diaideje másodpercben (`Preferences\\slideduration`)."""
        raw = self._get_settings().value(
            _legacy._MOVIE_SLIDE_DURATION_KEY, _legacy._MOVIE_SLIDE_DURATION_DEFAULT
        )
        try:
            seconds = float(raw)
        except (TypeError, ValueError, OverflowError):
            return _legacy._MOVIE_SLIDE_DURATION_DEFAULT
        if not math.isfinite(seconds):
            return _legacy._MOVIE_SLIDE_DURATION_DEFAULT
        return max(
            _legacy._MOVIE_SLIDE_DURATION_MIN,
            min(_legacy._MOVIE_SLIDE_DURATION_MAX, seconds),
        )

    def setMovieSlideDuration(self, seconds: float) -> None:  # noqa: N802
        """A diaidő mentése az eredeti 1–300 másodperces tartományban."""
        try:
            ertek = float(seconds)
        except (TypeError, ValueError, OverflowError):
            ertek = _legacy._MOVIE_SLIDE_DURATION_DEFAULT
        if not math.isfinite(ertek):
            ertek = _legacy._MOVIE_SLIDE_DURATION_DEFAULT
        ertek = max(
            _legacy._MOVIE_SLIDE_DURATION_MIN,
            min(_legacy._MOVIE_SLIDE_DURATION_MAX, ertek),
        )
        self._get_settings().setValue(_legacy._MOVIE_SLIDE_DURATION_KEY, ertek)
        self.moviePreferencesChanged.emit()

    def movieTransition(self) -> str:  # noqa: N802
        """A filmkészítő átmenetkulcsa, alapból a jelenlegi `dissolve`."""
        value = str(
            self._get_settings().value(_legacy._MOVIE_TRANSITION_KEY, "dissolve")
        )
        return value if value in _legacy._MOVIE_TRANSITIONS else "dissolve"

    def setMovieTransition(self, transition: str) -> None:  # noqa: N802
        """Az ismert átmenetkulcs mentése a `Preferences` tárba."""
        if transition not in _legacy._MOVIE_TRANSITIONS:
            return
        self._get_settings().setValue(_legacy._MOVIE_TRANSITION_KEY, transition)
        self.moviePreferencesChanged.emit()

    def movieVolume(self) -> int:  # noqa: N802
        """A videó hangerőcsúszkájának Preferences/movievolume értéke."""
        try:
            return max(0, min(1000, int(self._get_settings().value("movievolume", 500))))
        except (TypeError, ValueError):
            return 500

    def setMovieVolume(self, volume: int) -> None:  # noqa: N802
        """A hangerő elmentése az eredeti 0..1000-es tartományban."""
        volume = max(0, min(1000, int(volume)))
        self._get_settings().setValue("movievolume", volume)
        self.moviePreferencesChanged.emit()

    def moviePreference(self, name: str) -> bool:  # noqa: N802
        """A filmkészítő hivatalos Preferences-kulcsának beolvasása."""
        if name not in _legacy._MOVIE_PREFERENCES:
            return False
        key, default = _legacy._MOVIE_PREFERENCES[name]
        # Az INI-ből újraindítás után a `false` szövegként jön vissza, és a
        # bool("false") igaz lenne: ezért a közös, szöveget is értő olvasó.
        return _legacy.coerce_ui_preference_flag(
            self._get_settings().value(key, default), default=default
        )

    def setMoviePreference(self, name: str, value: bool) -> None:  # noqa: N802
        """Csak a specifikációban szereplő filmkészítő-kulcsokat írja."""
        if name not in _legacy._MOVIE_PREFERENCES:
            return
        key, _default = _legacy._MOVIE_PREFERENCES[name]
        self._get_settings().setValue(key, bool(value))
        self.moviePreferencesChanged.emit()

    def movieSourceUrls(self, rows) -> list[str]:  # noqa: N802
        """A film forrásképeinek `file:` URL-je, a dia-előnézethez."""
        if rows and isinstance(rows[0], str):
            paths = (Path(_legacy.to_local_path(str(row))) for row in rows)
        else:
            paths = self._sources_for(rows)
        return [
            QUrl.fromLocalFile(str(path)).toString()
            for path in paths
        ]

    def movieClipNames(self, rows) -> list[str]:  # noqa: N802
        """A film kliptálcáján megjelenő képfájlnevek."""
        paths = (
            (Path(_legacy.to_local_path(str(row))) for row in rows)
            if rows and isinstance(rows[0], str)
            else self._sources_for(rows)
        )
        return [Path(path).name for path in paths]

    def selectedMovieSourceUrls(self, rows) -> list[str]:  # noqa: N802
        """Új klipek a könyvtár aktuális kijelöléséből, a tálcától függetlenül."""
        return [
            QUrl.fromLocalFile(str(path)).toString()
            for path in self._selected_sources(rows)
        ]

    def movie_transition_preview_provider(self) -> MovieTransitionPreviewProvider:
        """A slideshow azonos átmenetfüggvényét használó QML-képszolgáltató."""
        if not hasattr(self, "_movie_transition_preview_provider"):
            self._movie_transition_preview_provider = MovieTransitionPreviewProvider()
            self._movie_transition_preview_provider.frameReady.connect(
                self.movieTransitionPreviewReady
            )
        return self._movie_transition_preview_provider

    def requestMovieTransitionPreview(  # noqa: N802
        self,
        outgoing_source: str,
        incoming_source: str,
        transition: str,
        progress: float,
        width: int,
        height: int,
        cropfit: bool,
        show_captions: bool,
        show_dates: bool,
        outgoing_slide_json: str,
        incoming_slide_json: str,
        actual_size: bool,
        viewport_width: int,
        viewport_height: int,
        device_pixel_ratio: float,
    ) -> int:
        """Elindítja a nézőképkocka háttérbeli renderelését."""
        return self.movie_transition_preview_provider.request_transition(
            outgoing_source,
            incoming_source,
            transition,
            progress,
            width,
            height,
            cropfit,
            show_captions,
            show_dates,
            outgoing_slide_json,
            incoming_slide_json,
            actual_size,
            viewport_width,
            viewport_height,
            device_pixel_ratio,
        )

    def prefetchMovieTransitionPreview(  # noqa: N802
        self,
        source: str,
        slide_json: str,
        width: int,
        height: int,
        cropfit: bool,
        show_captions: bool,
        show_dates: bool,
        actual_size: bool,
        viewport_width: int,
        viewport_height: int,
        device_pixel_ratio: float,
    ) -> None:
        """Kéri a film-előnézet következő dia-alapkockájának előtöltését."""
        self.movie_transition_preview_provider.prefetch_frame(
            source,
            slide_json,
            width,
            height,
            cropfit,
            show_captions,
            show_dates,
            actual_size,
            viewport_width,
            viewport_height,
            device_pixel_ratio,
        )

    def moviePreviewImageSize(self, source: str) -> list[int]:  # noqa: N802
        """A forrásméretet fejlécekből olvassa, képtartalom-dekódolás nélkül."""
        local_path = _legacy.to_local_path(source)
        reader = QImageReader(local_path or source)
        size = reader.size()
        if not size.isValid():
            return [0, 0]
        return [size.width(), size.height()]

    def _alapertelmezett_film_cel(self) -> Path:
        """A film célfájlja, ha a felhasználó nem adott meg egyet (#1977).

        A mappa a `Picasa` alatti (meglévő vagy honosított) Filmek-mappa,
        és **projekt-mappaként be is jelöljük** — enélkül a bal hasáb
        Projektek gyűjteménye nem tudja hova sorolni (ugyanaz a hiba,
        amit a kollázsnál a `write_album_ini` javított).

        A név (#5676): ha a munkamenetben már készült kimenet, annak a neve
        ÉS mappája (`0x00620998`); különben a felület nyelvének honosított
        alapneve (`CMakeMoviePanel::deffilename`). A forrásmappa neve nem
        számít, az eredeti sem abból nevez el.
        """
        from . import movie_output
        from .collage_output import _felulet_nyelve

        nyelv = _felulet_nyelve()
        elozo = self._elozo_film_cel
        if elozo is not None:
            mappa, cim = elozo.parent, elozo.stem
        else:
            # A `_get_settings()` a többi ág mintája (ld. a piszkozat-mappát
            # a 124. sorban), enélkül a próbák a VALÓDI `~/Képek`-be írnának.
            beallitott = self._get_settings().value(movie_output.OUTPUT_DIR_KEY)
            mappa = movie_output.output_dir(beallitott, nyelv)
            # üres cím: a `safe_stem` a nyelv honosított alapnevére esik
            cim = ""
        mappa = movie_output.tartalek_mappa(mappa)
        movie_output.write_album_ini(mappa, mappa.name)
        return movie_output.output_path(mappa, cim, nyelv)

    @staticmethod
    def _film_beallitas(
        width: int,
        height: int,
        seconds_per_photo: float,
        transition_seconds: float | None = None,
        transition_type: str = "dissolve",
        audio_path: Path | None = None,
        audio_option: int = 0,
        text_slides: list[dict] | None = None,
        options: dict | None = None,
    ) -> _legacy.MovieSettings:
        """A `MovieSettings` összeállítása — külön metódus, hogy mérhető legyen.

        #1977 (7. pont): a szélesség KAPOTT érték, nem 16:9-ből
        származtatott. Az eredeti hét mérete közül **öt 4:3-as**
        (320×240, 640×480, 800×600, 1024×768, 1600×1200); azokra a
        származtatás torzítana — 1024-es magasságból 1820 jönne ki 768
        helyett.

        `width=0` a RÉGI, négyargumentumos hívási alak: ilyenkor 16:9-ből
        számolunk, tehát a meglévő 720p/1080p hívások változatlanok.
        """
        if not width:
            width = (height * 16 // 9) // 2 * 2
        if transition_seconds is None:
            transition_seconds = min(_legacy._MAX_TRANSITION_S, seconds_per_photo / 3)
        return _legacy.MovieSettings(
            width=max(2, int(width)) // 2 * 2,
            height=height,
            seconds_per_photo=seconds_per_photo,
            # az áttűnés a képenkénti idő harmada, de legfeljebb 0,5 mp:
            # rövid diáknál (1 mp) a fix 0,5 mp-es áttűnés hosszabb
            # lenne, mint amennyi ideig a kép áll — az érvénytelen
            transition_seconds=min(
                max(0.0, transition_seconds), seconds_per_photo * 0.9
            ),
            transition_type=transition_type,
            audio_path=audio_path,
            audio_option=audio_option,
            text_slides=tuple(text_slides or ()),
            show_captions=bool((options or {}).get("showcaptions", False)),
            show_dates=bool((options or {}).get("showdates", False)),
            cropfit=bool((options or {}).get("cropfit", False)),
            remove_low_res_faces=bool((options or {}).get("removelowresfaces", False)),
            face_movie=bool((options or {}).get("faceMovie", False)),
            ordering=max(0, min(2, int((options or {}).get("ordering", 0)))),
            burstmodethresh=max(
                0, min(86400, int((options or {}).get("burstmodethresh", 0)))
            ),
        )

    @staticmethod
    def _film_projekt(
        sources,
        settings,
        used_face_rects=(),
    ) -> MxfProjekt:
        """A film állapota `.mxf`-projektként (#3191).

        A felület által állítható méret, hangsáv, opciók, rendezés,
        szöveges diák és áttűnés kerül a projektbe. A formátum megengedi,
        hogy a diánkénti `trans` felülírja az album-szintű `defaulttrans`-ot.
        """
        try:
            felbontas = _legacy._MOVIE_SIZES.index((settings.width, settings.height))
        except ValueError:
            felbontas = 1
        atmenet_tipus = _legacy._MOVIE_TRANSITIONS.index(settings.transition_type)
        alap = MxfAtmenet(
            transition=atmenet_tipus,
            advanceinterval=float(settings.seconds_per_photo),
            transitiontime=float(settings.transition_seconds),
        )
        atmenetek = []
        for i, ut in enumerate(sources):
            rectangle = (
                used_face_rects[i]
                if settings.face_movie and i < len(used_face_rects)
                else None
            )
            face_parameters = MxfSzovegParam()
            if rectangle is not None:
                face_parameters = MxfSzovegParam(
                    facerectx0=rectangle[0],
                    facerecty0=rectangle[1],
                    facerectx1=rectangle[2],
                    facerecty1=rectangle[3],
                    facemoviesrc=1,
                )
            atmenetek.append(
                MxfAtmenet(
                    transition=atmenet_tipus,
                    advanceinterval=alap.advanceinterval,
                    transitiontime=alap.transitiontime,
                    forras=MxfForras(
                        index=i,
                        filename=str(ut),
                        szovegparam=face_parameters,
                    ),
                )
            )
        for index, slide in enumerate(settings.text_slides):
            text_color = str(slide.get("textColor", "#ffffff")).lstrip("#")[-6:]
            try:
                packed_color = int(text_color, 16)
            except ValueError:
                packed_color = 0xFFFFFF
            background_color = str(slide.get("backgroundColor", "#000000")).lstrip("#")[-6:]
            try:
                packed_background = int(background_color, 16)
            except ValueError:
                packed_background = 0
            font = str(slide.get("font", ""))
            size = int(slide.get("size", 16))
            style = max(0, min(11, int(slide.get("style", 0))))
            weight = 700 if slide.get("bold") else 400
            forras = MxfForras(
                tipus=2,
                bkcolor=packed_background,
                index=len(sources) + index,
                text=str(slide.get("text", "")),
                szovegparam=MxfSzovegParam(
                    fontname=font,
                    size=size,
                    color=packed_color,
                    weight=weight,
                    italic=bool(slide.get("italic")),
                    outline=bool(slide.get("outline")),
                    styleid=style,
                ),
            )
            atmenetek.append(
                MxfAtmenet(
                    transition=atmenet_tipus,
                    advanceinterval=alap.advanceinterval,
                    transitiontime=alap.transitiontime,
                    forras=forras,
                )
            )
        return MxfProjekt(
            curresolution=felbontas,
            musicfile=str(settings.audio_path or ""),
            audiooption=settings.audio_option,
            facemovie=settings.face_movie,
            showcaption=settings.show_captions,
            showdates=settings.show_dates,
            cropfit=int(settings.cropfit),
            removelowresfaces=settings.remove_low_res_faces,
            ordering=settings.ordering,
            burstmodethresh=settings.burstmodethresh,
            defaulttrans=alap,
            atmenetek=tuple(atmenetek),
        )

    @staticmethod
    def _film_projekt_utja(video_path: str) -> Path | None:
        """A kimenet melletti `.mxf`, ha létezik (#2114).

        A KERESÉST a `movie.mxf.projekt_utvonal` végzi (#3191 óta megvan,
        a `collage_save_open._collage_project_path` párja); itt csak az
        URL-alakot bontjuk vissza, mert a QML `file://`-ként adja tovább a
        néző útvonalát — enélkül a gomb SOSEM jelenne meg."""
        nyers = str(video_path or "")
        if not nyers:
            return None
        if nyers.startswith("file://"):
            nyers = QUrl(nyers).toLocalFile()
        return _legacy.projekt_utvonal(nyers)

    def hasMovieProject(self, video_path: str) -> bool:  # noqa: N802
        """Van-e a filmnek `.mxf` párja — vagyis szerkeszthető-e (#2114).

        A `hasCollageProject` ikerpárja: nem a létrehozás emléke kapcsolja
        be a gombot, hanem a fájl mellett álló projektfájl."""
        return _legacy.CreateMixin._film_projekt_utja(video_path) is not None

    def movieProject(self, video_path: str):  # noqa: N802
        """A film projektje a felületnek: forrásképek + diaidő (#2114).

        Üres szótár, ha nincs (vagy nem olvasható) projektfájl — a visszaút
        nem boríthatja a felületet.

        ⛔ A **felbontás nincs benne**: a `_film_projekt` a `curresolution`
        mezőt nem tölti ki (a jelentése a mi modellünkben nincs mérve),
        ezért az újranyitás a felbontás alapértelmezését hozza. Ezt a hívó
        felület mondja ki a felhasználónak — találgatott érték nem megy a
        projektbe."""
        ut = _legacy.CreateMixin._film_projekt_utja(video_path)
        if ut is None:
            return {}
        try:
            projekt = _legacy.read_mxf(ut)
        except (OSError, ValueError, ElementTree.ParseError) as hiba:
            _legacy.logger.warning("a film projektfájlja nem olvasható: %s", hiba)
            return {}
        return {
            "sources": [
                atmenet.forras.filename
                for atmenet in projekt.atmenetek
                if atmenet.forras.filename
            ],
            "seconds": float(projekt.defaulttrans.advanceinterval),
            "burstmodethresh": int(projekt.burstmodethresh),
        }

    def exportMovie(
        self,
        rows,
        target_url: str,
        height: int,
        seconds_per_photo: float,
        width: int = 0,
        transition_type: str = "dissolve",
        overlap_seconds: float = 0.5,
        audio_url: str = "",
        audio_option: int = 0,
        text_slides: list | None = None,
        movie_options: dict | None = None,
    ) -> None:
        """Diavetítés-videó a kijelölt képekből (MP4).

        `height` a videó magassága, `width` a szélessége. #1977: a
        szélesség KÜLÖN paraméter, mert az eredeti hét mérete közül öt
        4:3-as. `width=0` ⇒ 16:9-ből (a régi hívási alak).

        ⚠️ **A kimenet MP4 (`mp4v`), az eredeti `.wmv`-jével szemben** — és
        ez SZÁNDÉKOS, nem elmaradás. A `.wmv` írásához Windows-specifikus
        kodek kellene; az OpenCV `mp4v`-je minden platformon megy, külön
        telepítés nélkül (`movie/slideshow.py:27-28`). Egy későbbi kör ne
        „javítsa vissza": a konténer eltérése a hordozhatóság ára.
        """
        # #1539: a bekötés a GUI-szálon, a háttérszál indítása ELŐTT
        self._ensure_output_resync_wired()
        # A filmprojektum saját kliptálcát ad át `file:` URL-ekkel; ne
        # olvassuk újra helyette a főablak kijelölését vagy képtálcáját.
        # A régi, sorindexeket váró hívási alak változatlan marad.
        if rows and isinstance(rows[0], str):
            sources = tuple(
                Path(_legacy.to_local_path(str(row))) for row in rows if str(row)
            )
        else:
            sources = self._sources_for(rows)
        sources = sources[:_legacy._MAX_ITEMS]
        target = _legacy.to_local_path(target_url)
        if not sources:
            self.movieFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            # #1977: cél nélkül NEM hibázunk — az eredeti sem kér célfájlt.
            # A mappát a program adja (`Picasa`/honosított Filmek), a nevet
            # a munkamenet előző kimenete vagy a nyelv honosított alapneve
            # adja (#5676), ütközésnél sorszámozva. Ha a mappa nem hozható
            # létre, a rendszer Videók mappája a tartalék
            # (`0x00620af9`–`0x00620b1d`), és ez SEM hibaüzenet.
            try:
                target = str(self._alapertelmezett_film_cel())
            except OSError as hiba:
                # A részletet NAPLÓZZUK, nem a felhasználónak mondjuk: az
                # `OSError` szövege fejlesztői (errno, útvonal), és a
                # honosítása is külön csapda volna (%1-helyettesítő).
                _legacy.logger.warning("a film mappája nem hozható létre: %s", hiba)
                self.movieFailed.emit(
                    self.tr("The movie folder could not be created.")
                )
                return
        try:
            audio_path = Path(_legacy.to_local_path(audio_url)) if audio_url else None
            settings = self._film_beallitas(
                width,
                height,
                seconds_per_photo,
                overlap_seconds,
                transition_type,
                audio_path,
                audio_option,
                text_slides,
                movie_options,
            )
        except ValueError as error:
            self.movieFailed.emit(str(error))
            return

        def worker():
            try:
                report = _legacy.export_movie(
                    sources,
                    Path(target),
                    settings,
                    progress=lambda done, total: self.movieProgress.emit(done, total),
                )
            except (ValueError, OSError, RuntimeError) as error:
                self.movieFailed.emit(str(error))
                return
            if not report.used:
                self.movieFailed.emit(
                    self.tr("None of the selected pictures could be read.")
                )
                return
            # #3191: a PROJEKTFÁJL a kimenet mellé. A kollázs ugyanezt
            # teszi a `.cxf`-fel: enélkül a kirenderelt film mellől
            # hiányzik a szerkeszthető állapot, és a szerkesztőben nem
            # jelenhet meg a „Mozgófilm szerkesztése" gomb (#2114).
            # Sosem dob: a projektfájl kudarca nem boríthatja a KÉSZ
            # videót (ugyanaz az elv, mint az ini-érintésnél, #643).
            try:
                _legacy._write_movie_project(
                    report.target,
                    self._film_projekt(
                        report.used, settings, report.used_face_rects
                    ),
                )
            except OSError as hiba:  # pragma: no cover - írásvédett cél
                _legacy.logger.warning("a film projektfájlja nem írható: %s", hiba)
            # #5676: a következő üres céllal indított film ennek a nevét
            # és mappáját kapja. A kimenet sikere után áll be, így a kudarcos
            # próba nem írja felül az előzőt.
            self._elozo_film_cel = Path(report.target)
            # #1539: az `.mp4` INDEXELT médiatípus (scanner/filetypes.py),
            # tehát a rácsra való — ugyanaz a helyzet, mint a kollázsnál.
            self.noteOutputWritten(str(report.target))
            self.movieFinished.emit(
                str(report.target),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-movie")
