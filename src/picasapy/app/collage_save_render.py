"""A kollázs LÉTREHOZÁSA és RAJZOLÁSA (#949, spec 9.1) - a `collage_save.py` szelete.

A `CollageSaveMixin` ezt a részt örökli: a „Kollázs létrehozása" és az
„Asztali háttérkép" gomb EGY kódútja (`createCollage`), a háttérszál törzse
(`_render_worker`), a kimeneti célfájl (`_target_path`) és a mentett kollázs
indexbe vétele (`_index_saved_collage`).

⚠️ A háttérszál törzse (`_render_worker`) csak belső, nyers jelzéseket
emitál; a `tr()`, az állapotírás és a nyilvános jelzések a fogadó (GUI-)
szálon, a `collage_save.py`-ban futnak (#988/#999).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import Slot

from . import collage_output as output
from . import collage_prefs as prefs

#: Az oldalformátum-egyezés tűrése az asztali háttérképnél - a képernyő
#: aránya ritkán egyezik bitre a menü tételével.
_RATIO_TOLERANCE = 0.01

logger = logging.getLogger(__name__)

class CollageSaveRenderMixin:
    """A létrehozás és a rajzolás szelete (spec 9.1) - a `CollageSaveMixin` részeként."""

    # -- létrehozás (8.2, 9.1) ---------------------------------------------

    @Slot(bool)
    @Slot(bool, bool)
    @Slot(bool, bool, bool)
    def createCollage(
        self,
        asDesktopBackground: bool,  # noqa: N803 - a spec 8.2 neve
        ignoreFormatMismatch: bool = False,  # noqa: N803
        replaceExisting: bool = False,  # noqa: N803
    ) -> None:
        """A kollázs mentése - EGY kódút a két gombhoz (spec 8.2).

        `asDesktopBackground` esetén a formátum-eltérésre előbb
        figyelmeztetünk (9.1); a „Beállítás ennek ellenére" gomb ugyanezt a
        slotot hívja `ignoreFormatMismatch=True`-val.

        `replaceExisting` a „Meglévő cseréje" ága (9.2): a korábbi kimeneti
        fájlt írjuk felül, számozás nélkül. Az „Új létrehozása" ág nem külön
        kódút - a felület előbb a `dropSavedCollagePath()`-t hívja, és utána
        ugyanezt a slotot."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        if not nodes:
            self.collageNoImages.emit()
            return
        if (
            asDesktopBackground
            and not ignoreFormatMismatch
            and abs(self.collagePageRatio - self._screen_ratio()) > _RATIO_TOLERANCE
        ):
            self.collageFormatMismatch.emit()
            return
        if not any(not node.missing for node in nodes):
            # 9.4: a kollázs minden képe eltűnt a lemezről - ez ugyanaz a
            # zsákutca, mint amikor mindet eltávolították, és a felület
            # ugyanazt a „Mentés mellőzve" üzenetet mutatja rá. Nyers
            # kivétel-szöveg semmiképp ne menjen ki a felhasználóhoz.
            self.collageNoImages.emit()
            return

        target = self._target_path(replaceExisting)
        self._collage_panel_cancel.clear()
        self._ensure_worker_bridge()  # #988/#999: a GUI-szálon, a szál ELŐTT
        self._emit_progress(0, self._progress_text_initializing())
        # #1168 (16.3): innentől a KÖNYVTÁRNÉZET is jelzi a várakozást - az
        # összes korábbi visszafordulás (nincs kép, formátum-eltérés) már
        # megtörtént, tehát innen tényleg rajzolás következik.
        self._set_rendering(True)
        self._start_background(
            self._render_worker,
            args=(
                output.render_nodes_of(nodes, theme=self._collage_panel_theme),
                self._render_settings(),
                target,
                bool(asDesktopBackground),
                # #1009: a háttérkép a GUI-szálon dől el - a háttérszál a
                # modellhez nem nyúlhat
                self._background_image_for_cxf(),
            ),
            name="picasapy-collage-panel",
        )

    def _target_path(self, replace_existing: bool) -> Path:
        """A célfájl: a meglévő útvonal, vagy a cím alapján egy új név.

        „Meglévő cseréje" esetén az EREDETI útvonalat írjuk felül, számozás
        nélkül (spec 9.1 utolsó sora) - különben minden újramentés egy újabb
        `név1.jpg`-t hagyna a Kollázsok albumban."""
        if replace_existing and self._collage_panel_saved_path:
            return Path(self._collage_panel_saved_path)
        mappa = output.output_dir(
            self._get_settings().value(prefs.OUTPUT_DIR_KEY)
        )
        sajat = self._draft_placeholder_target(mappa)
        if sajat is not None:
            return sajat
        return output.output_path(mappa, self._collage_panel_title)

    def _draft_placeholder_target(self, mappa: Path) -> Path | None:
        """A SAJÁT helykitöltőnk, ha a véglegesítés azt írja felül (#1125).

        A tulajdonos jelentése: bezárás → újranyitás → „Létrehozás" után a
        PISZKOZAT-kép OTTMARADT, a kész kollázs pedig `L1.jpg` néven
        született. A #1072 szándéka az volt, hogy a helykitöltő lefoglalja a
        nevet - de a foglalás csak a NYITOTT panelen élt
        (`collageSavedPath`), bezárás után elveszett.

        **A felülírás MÉRT viselkedés**, nem használhatósági döntés: a
        tulajdonos valódi, EREDETI Picasa által készített Kollázsok
        mappájában 11 JPEG és 11 `.cxf` áll, és a párosítatlan JPEG-ek
        száma **NULLA**. Ha az eredeti a helykitöltőt meghagyná és mellé
        sorszámozna, ott pontosan olyan árva fájlok volnának, mint amilyet
        a tulajdonos most kapott. A `%s%lu` sorszámozás használatban van
        (AI → AI1 → AI2…), de csak KÜLÖN kollázsokra, ahol a nevet egy KÉSZ
        (`.cxf`-fel párosított) kollázs foglalja.

        ⚠️ A felismerés a piszkozat-NYILVÁNTARTÁSBÓL megy, nem a névből: a
        „nincs `.cxf` párja" IGAZ egy idegen JPEG-re is, amit a felhasználó
        tett a Kollázsok mappába - azt felülírni ADATVESZTÉS volna.

        ⚠️ **Ez az idegen-fájl védőág a MI döntésünk, nem az eredeti
        rekonstrukciója.** A 11 mintában ilyen eset NINCS, tehát nem tudjuk,
        mit tenne a Picasa egy idegen, `.cxf` nélküli JPEG-gel. Óvatosabb
        irányba tértünk el, szándékosan és kimondva.

        Három feltétel EGYÜTT: a nyilvántartott útvonal (a) létezik, (b) a
        célmappában van, és (c) nincs mellette `.cxf` - vagyis időközben nem
        vált kész kollázzsá."""
        jelolt = self._get_settings().value(prefs.PLACEHOLDER_KEY)
        if not jelolt:
            return None
        ut = Path(str(jelolt))
        if not ut.is_file() or ut.with_suffix(".cxf").exists():
            return None
        if os.path.normcase(str(ut.parent)) != os.path.normcase(str(mappa)):
            return None
        return ut

    def _collage_output_width(self) -> int:
        """A kimeneti kép szélessége. Külön metódus, hogy a teszt kisebb
        vásznon dolgozhasson: az éles 5120 képpont egy tesztben másodperceket
        és tíz-megabájtos tömböket jelentene, holott az állítás a fájlnévről
        és a jelzésekről szól."""
        return output.output_width(self.collagePageRatio)

    def _render_settings(self):
        """A panel állapotából renderelő-beállítás (a színváltás a modulban)."""
        color = self._collage_panel_bg_color
        return output.render_settings(
            theme=self._collage_panel_theme,
            border=self._collage_panel_border,
            spacing=self._collage_panel_spacing,
            shadows=self._collage_panel_shadows,
            page_ratio=self.collagePageRatio,
            background_rgb=(color.red(), color.green(), color.blue()),
            frame_center=self._collage_panel_frame_center,
            seed=self._collage_panel_seed,
            width=self._collage_output_width(),
            # #1015: csak KÉP-módban - a szín- és az átlagszín-mód (#1004)
            # a `background` szín marad
            background_image=(
                self.collageBackgroundImage
                if self._collage_panel_bg_mode == "image"
                else ""
            ),
            # #1273: ugyanazok a mezők adják az Indexkép fejlécét, amelyeket
            # a #1274 már megőriz a `.cxf` körbejárásában.
            album_title=self._collage_panel_title,
            album_date=self._collage_panel_album_date,
            # #978: a „képfeliratok" kapcsoló innen jut el a rajzolóig
            captions=self._collage_panel_captions,
        )

    def _index_saved_collage(self, path: Path) -> None:
        """A mentett kollázs mappáját felvesszük az INDEXBE.

        ⚠️ Enélkül a kollázs SEHOL nem jelenik meg a bal hasábon, hiába
        tökéletes a `.picasa.ini`. A Projektek gyűjtemény lekérdezése
        (`index/project_folders.py`) így indul:

            SELECT path FROM folders WHERE has_ini = 1

        - vagyis csak a MÁR INDEXELT mappákon megy végig. A kollázs
        célmappája (`<Képek>/Picasa/Kollázsok`) viszont tipikusan egyetlen
        figyelt gyökér alatt sincs, tehát oda sem teljes újraindexeléssel,
        sem másképp nem kerül be. Mérve a valódi indexen: 68 mappa, egy sem
        a Kollázsok.

        A `sync_folder` gyökér-korlátja itt úgy teljesül, hogy a gyökér MAGA
        a célmappa - így csak ezt az egy mappát vesszük fel, a felhasználó
        figyelt gyökereihez nem nyúlunk.

        A hiba nem buktatja el a mentést: a kép már a lemezen van, és egy
        index-gond miatt nem mondjuk azt, hogy a mentés meghiúsult."""
        mappa = Path(path).parent
        try:
            from picasapy.index import open_index
            from picasapy.index.sync import sync_folder

            with open_index(self._db_path) as conn:
                enabled_filetypes = getattr(
                    self, "_filetype_scan_snapshot", None
                )
                if enabled_filetypes is None:
                    sync_folder(conn, mappa, mappa)
                else:
                    sync_folder(
                        conn,
                        mappa,
                        mappa,
                        enabled_filetypes=enabled_filetypes,
                    )
        except Exception:  # noqa: BLE001 - az indexelés soha ne bukatassa a mentést
            logger.warning(
                "A mentett kollázs mappája nem került az indexbe: %s", mappa,
                exc_info=True,
            )

    def _render_worker(
        self, nodes, settings, target, wallpaper: bool, background_image: str
    ) -> None:
        """A háttérszál törzse - a `BackgroundWorkerMixin`-en fut (#430).

        A folyamatjelzés SZAKASZOS, nem képenkénti: a rajzoló
        (`collage/picasa_render.py`) nem ad képenkénti visszajelzést, és
        kitalálni egyet rosszabb volna, mint durvábban jelezni. A három
        szakasz - indulás, rajzolás kész, kiírva - a felhasználónak azt
        mondja meg, ami tényleg igaz."""
        self._post_progress(10, self._PROGRESS_INITIALIZING)
        try:
            eredmeny = output.render_collage(
                nodes,
                settings,
                target,
                album_title=self._collage_panel_title,
                album_date=self._collage_panel_album_date,
                album_uid=self._collage_panel_album_uid,
                album_id=self._collage_panel_album_id,
                background_image=background_image,
                format_key=self._collage_panel_format,
                node_uids=self._collage_panel_node_uids,
                node_scales=self._collage_panel_node_scales,
                should_cancel=self._rendered_now_writing,
            )
        except (ValueError, OSError) as error:
            self._workerOutcome.emit({"fajta": "hiba", "uzenet": str(error)})
            return
        if eredmeny.canceled:
            self._workerOutcome.emit({"fajta": "megszakitva"})
            return
        if eredmeny.path is None:
            self._workerOutcome.emit({"fajta": "olvashatatlan"})
            return
        self._workerOutcome.emit(
            {
                "fajta": "kesz",
                "ut": str(eredmeny.path),
                "hianyzo": len(eredmeny.missing),
                "hatterkep": bool(wallpaper),
            }
        )

    def _rendered_now_writing(self) -> bool:
        """A rajzolás kész, jön a kiírás - és közben: megszakították-e?

        Ez a `render_collage` `should_cancel` horga, és SZÁNDÉKOSAN kettős
        feladatú: a rajzoló pontosan egyszer, a két szakasz HATÁRÁN kérdezi
        meg. Ez az egyetlen pillanat, amiről a vezérlő biztosan tudja, hogy a
        munka nagyja megvan - tehát ez az egyetlen hely, ahol a 90%-ot
        őszintén ki lehet írni. Két külön horog ugyanide kötve csak
        látszatra volna tisztább."""
        self._post_progress(90, self._PROGRESS_INITIALIZING)
        return self._collage_panel_cancel.is_set()
