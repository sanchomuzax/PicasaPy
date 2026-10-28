"""A kollázs PISZKOZATA (#1072, spec 3.3 és 9.) - a `collage_save.py` szelete.

A piszkozat `.cxf`-ként a Kollázsok mappába kerül (`saveCollageDraft`). A
mellé írt helykitöltő kép teszi láthatóvá az albumban
(`_write_draft_placeholder`), a véglegesítéskor pedig a piszkozatot takarítja
el (`_discard_draft_after_render`). A visszatöltés (`restoreCollageDraft`) a
közös `_apply_cxf_project`-et hívja, ami a `collage_save_open.py`-ban él.
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.collage import draft_placeholder, write_collage
from picasapy.collage.autosave import discard_autosave, read_autosave, write_autosave
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.picasa_render import render_nodes

from . import collage_output as output
from . import collage_prefs as prefs

logger = logging.getLogger(__name__)

class CollageSaveDraftMixin:
    """A piszkozat mentése és visszatöltése (spec 3.3, 9.) - a `CollageSaveMixin` részeként."""

    def _discard_draft_after_render(self) -> None:
        """A kész kollázs mellől ELTAKARÍTJUK a piszkozatot (#1100).

        ⚠️ Nem rendrakás: a valódi Picasa az ottfelejtett `autosave.cxf`-et
        **elárvult automentésként** ismeri fel, és a saját 640 × 480-as,
        egyszínű sötétszürke helykitöltőjét írja mellé `autosave.jpg` néven
        - a felhasználó Kollázsok mappájába. A tulajdonos ezt látta a
        v0.8.23-ban, és a mi kimenetünknek hitte.

        Vagyis a mi maradékunk SZEMETET GYÁRTAT a valódi Picasával. A
        piszkozat a véglegesítéssel betöltötte a szerepét.

        ⚠️ #1387: a takarítás a piszkozat TÉNYLEGES mappájából dob el, NEM a
        jelenleg BEÁLLÍTOTT Kollázsok-mappából. A kettő szétválhat, ha a
        felhasználó a piszkozat mentése UTÁN, a befejezés ELŐTT átállítja a
        kimeneti mappát (`finishCollageDraft` egy MÁSHOL fekvő piszkozatot
        nyit meg és véglegesít, ld. `openCollageProject`/`saveCollageDraft`
        - mindkettő frissíti `_collage_panel_draft_source_dir`-t). Ha nincs
        ismert tényleges hely (a panel még sosem mentett/nyitott piszkozatot
        ebben a menetben), a beállított mappa marad a válasz - ez az eredeti,
        egyszerű eset, ahol a kettő úgyis ugyanaz.

        A beállításból is kivezetjük: ha csak a fájlt törölnénk, a program
        indításkor még mindig felajánlaná a helyreállítást, és a felhasználó
        egy nem létező munkát „állítana helyre".

        ⚠️ A már ott lévő, PICASA által írt `autosave.jpg`-hez NEM nyúlunk -
        az nem a mi fájlunk, a felhasználó mappájában van (#1100 döntése;
        #1387 alatt is érvényben marad, hiszen csak az `autosave.cxf`-et
        töröljük néven, nem a mappa teljes tartalmát).

        A hiba nyelt: a kollázs ekkor már a lemezen van, és egy takarítási
        gond nem teheti kudarccá a mentést."""
        mappa = self._collage_panel_draft_source_dir or self._collage_panel_draft_dir()
        try:
            discard_autosave(mappa)
        except OSError as hiba:
            logger.warning("A piszkozat nem takarítható el: %s", hiba)
            return
        finally:
            self._collage_panel_draft_source_dir = None
        beallitas = self._get_settings()
        beallitas.remove(prefs.AUTOSAVE_KEY)
        # #1125: a helykitöltő szerepe is véget ért - a kész kollázs
        # foglalja a helyét. A jelölő itt szűnik meg, nem a fájl.
        beallitas.remove(prefs.PLACEHOLDER_KEY)

    # -- piszkozat (3.3, 9.) -----------------------------------------------

    def _collage_panel_draft_dir(self) -> Path:
        """A piszkozat mappája: a „Kollázsok" album.

        ⚠️ A név szándékosan `_collage_panel_*`: a `CreateMixin` a
        `_collage_draft_dir` nevet MÁR használja, és a két szelet ugyanabban
        az `AppController`-ben él - az azonos név néma felülírás volna."""
        return output.output_dir(self._get_settings().value(prefs.OUTPUT_DIR_KEY))

    @Slot()
    def saveCollageDraft(self) -> None:
        """„Piszkozat mentése" (spec 3.3): a vászon `.cxf`-ként a lemezre.

        Csomópont nélkül NEM ír: egy üres piszkozat visszaállítva üres lapot
        adna, ami rosszabb annál, mintha nem ajánlanánk fel semmit. A hiba
        naplózott, de nyelt - a piszkozat baja sosem viheti el a
        felhasználó kollázsát.

        ⚠️ #1168 (spec 16.2/a): a kép nélküli ág eddig NÉMÁN tért vissza. Az
        eredeti ilyenkor a **„Mentés mellőzve"** dobozt mutatja
        (`collageUI::noimages_title` / `collageUI::noimages`) - ugyanaz a
        `collageNoImages` jelzés, amit a végleges mentés is kiad, tehát a
        felületnek nem kell új ágat írnia hozzá. A jelzés egyben azt is
        eldönti, hogy a lap NYITVA marad: a felhasználó vegyen fel egy
        képet, és próbálkozzon újra."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        if not nodes:
            self.collageNoImages.emit()
            return
        try:
            ut = write_autosave(
                self._collage_panel_draft_dir(),
                project_from_nodes(
                    output.render_nodes_of(nodes, theme=self._collage_panel_theme),
                    self._render_settings(),
                    album_title=self._collage_panel_title,
                    album_date=self._collage_panel_album_date,
                    album_uid=self._collage_panel_album_uid,
                    album_id=self._collage_panel_album_id,
                    background_image=self._background_image_for_cxf(),
                    format_key=self._collage_panel_format,
                    node_uids=self._collage_panel_node_uids,
                    node_scales=self._collage_panel_node_scales,
                ),
            )
        except (OSError, ValueError) as hiba:
            logger.warning("A kollázs-piszkozat nem írható: %s", hiba)
            return
        self._get_settings().setValue(prefs.AUTOSAVE_KEY, str(ut))
        # #1387: ez a mappa a piszkozat TÉNYLEGES helye, függetlenül attól,
        # hogy a beállítás később megváltozik-e - a befejezéskori takarítás
        # ezt használja, nem a mindenkori beállítást.
        self._collage_panel_draft_source_dir = ut.parent
        self._write_draft_placeholder(nodes, ut.parent)
        self.collageDraftSaved.emit(str(ut))

    def _write_draft_placeholder(self, nodes, mappa: Path) -> None:
        """A piszkozat HELYKITÖLTŐ képe - ettől látszik a Kollázsok albumban.

        A tulajdonos jelentése: *„A friss képkollázs piszkozat mentése nem
        jelenik meg a PicasaPy és Picasa alatt sem."* Az eredeti a mentéskor
        AZONNAL ír egy képet a `.cxf` mellé (mérve a képernyőképéről:
        `AI10.jpg`, 640 × 453), és ettől jelenik meg a piszkozat.

        A kép a kollázs **végleges nevét** kapja - nem `autosave.jpg`-t. Ez
        egyben lefoglalja a nevet: a „Létrehozás" innentől a meglévő fájlt
        látja, és a felület felteszi a *„Lecseréli a meglévőt, vagy újat hoz
        létre?"* kérdést (spec 9.2), ahogy az eredeti is. Így a befejezés
        nem hagy maga után szemetet.

        ⚠️ A hiba **nyelt**: a piszkozat `.cxf`-je már a lemezen van, és egy
        helykitöltő baja nem viheti el a felhasználó munkáját. Naplózva
        viszont igen - a #1075 tanulsága, hogy a néma ág miatt vakon
        állunk."""
        if not nodes:
            return
        try:
            meglevo = self.collageSavedPath
            cel = (
                Path(meglevo)
                if meglevo
                else self._draft_placeholder_path(mappa)
            )
            szeles, magas = draft_placeholder.placeholder_size(
                self.collagePageRatio
            )
            beallitas = dataclasses.replace(
                self._render_settings(), width=szeles, height=magas
            )
            jelentes = render_nodes(
                output.render_nodes_of(nodes, theme=self._collage_panel_theme),
                beallitas,
            )
            kep = draft_placeholder.draw_draft_label(
                jelentes.image, self._piszkozat_felirat()
            )
            write_collage(cel, kep, quality=output.JPEG_QUALITY)
        except Exception:  # noqa: BLE001 - a piszkozat baja nem vihet el munkát
            logger.warning(
                "A piszkozat helykitöltő képe nem írható (%s)", mappa, exc_info=True
            )
            return
        self._set_saved_path(str(cel))
        # #1125: JEGYEZZÜK FEL, melyik fájl a mi helykitöltőnk. A
        # véglegesítés csak ezt írhatja felül - a „nincs `.cxf` párja"
        # önmagában egy IDEGEN képre is igaz volna.
        self._get_settings().setValue(prefs.PLACEHOLDER_KEY, str(cel))
        self._index_saved_collage(cel)

    def _draft_placeholder_path(self, mappa: Path) -> Path:
        """A piszkozat helykitöltőjének célfájlja - ÚJRAÍRHATÓ, nem szaporodó.

        A tulajdonos szava: *„A »PISZKOZAT« felirat akkor jelenik meg …
        amikor a »Bezárás« gombot megnyomom … De csak addig van ott, amíg le
        nem menti."* - vagyis a piszkozatnak EGYETLEN képe van. Ha a
        visszaállítás után újra bezár, ugyanazt kell felülírnunk, különben
        minden körben új `Kollázs1.jpg`, `Kollázs2.jpg` keletkezne.

        A megkülönböztető a `.cxf` PÁR: a KÉSZ kollázs mellett ott áll a
        projektfájlja (#1002 ezen az egy jelen áll), a helykitöltő mellett
        nem - a piszkozat `.cxf`-je az `autosave.cxf`. Tehát ha a név
        szabad, vagy már a MI helykitöltőnk ül rajta, azt írjuk felül; ha
        egy kész kollázs foglalja, az `output_path` sorszámoz."""
        alap = mappa / f"{output.safe_stem(self._collage_panel_title)}.jpg"
        if not alap.exists() or not alap.with_suffix(".cxf").exists():
            return alap
        return output.output_path(mappa, self._collage_panel_title)

    @Slot()
    def restoreCollageDraft(self) -> None:
        """A piszkozat visszatöltése - a lap UGYANAZT a vásznat mutatja.

        A téma, az árnyék, a képfeliratok és a tájolás a `.cxf`-ből jönnek,
        de a mezőket KÖZVETLENÜL állítjuk: a `setCollageTheme` újraszámolná
        az elrendezést, és pont a visszaállítandó kézi helyeket dobná el.

        Az oldalFORMÁTUM nem áll vissza (a `.cxf` arányt tárol, nem
        menü-kulcsot) - a lap alakja a tájolásból és a jelenlegi formátumból
        áll össze. A csomópontok arányosan érkeznek, tehát a kép a lapon
        marad akkor is, ha a formátum közben más lett.

        #1387: a beolvasott mappa itt a TÉNYLEGES piszkozat-hely is -
        eltároljuk, hogy a befejezéskori takarítás akkor is ide nyúljon
        vissza, ha a beállított Kollázsok-mappa időközben megváltozik."""
        self._ensure_collage_panel()
        mappa = self._collage_panel_draft_dir()
        projekt = read_autosave(mappa)
        if projekt is None:
            return
        self._collage_panel_draft_source_dir = mappa
        self._apply_cxf_project(projekt, saved_path="")
        meglevo = self._draft_placeholder_path(mappa)
        if meglevo.exists():
            self._set_saved_path(str(meglevo))
