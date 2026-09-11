"""Nem-destruktív fotó-műveletek (.picasa.ini-be írva): csillag, felirat,
forgatás, elrejtés, albumtagság — az AppController művelet-szelete (#150).

Mixin-osztály: az `AppController` örökli; minden írás a round-trip ini-
rétegen át történik (atomikus mentés + backup).

#141: a csillag/felirat/forgatás (egy-képes szerkesztés) a NAS-írást
(ini-mentés: backup-olvasás + temp-írás + fsync) ÉS az utána következő
index-frissítést háttérszálon végzi — a GUI-szál egy kattintásnál sem
fagy le NAS-mappán. Az érték már a hívás pillanatában ismert, ezért az
indexbe egyetlen célzott UPDATE kerül (`update_photo_fields`) a teljes
mappa-resync (`sync_tree`) helyett, a rács pedig csak az érintett sort
frissíti (`PhotoGridModel.update_photo`), nem a teljes feedet.

#9 (2. lépés): az albumtagság-írás (`addRowsToAlbum` / `removeRowsFromAlbum`
/ `createAlbum`) az `_apply_batch` kötegelt úton megy (a `setGeotagRows`
mintája, `geo_controller.py`) — az ini-réteg (`picasapy.ini.albums`) tiszta
függvényeit hívja mutate-ként.

#426: „Az összes effektus másolása/beillesztése" (Szerkesztés menü) — az
`EffectClipboardMixin` a `picasapy.edit.effect_clipboard` tiszta logikáját
köti QML-slotokká. Ez a réteg van a felületre kötve (`Main.qml:767–775`,
`PicasaMenuBar.qml:296–325`).

#1544: ez a réteg a `crop64`/`crop`/`redeye`/`retouch`/`moviestart`/
`movieend` bejegyzéseket korábban KIHAGYTA a másolásból, a `filterdesc.xml`
`mode="history"` oszlopából KÖVETKEZTETVE. A #1534 a `Picasa3.exe`
diszasszemblálásával igazolta, hogy az eredeti másolás-kezelője ezt az
attribútumot soha nem olvassa — a lánc EGÉSZÉBEN megy át, a vágással
együtt. A szűrés megszűnt; az indoklás az `effect_clipboard` modul
docstringjében, a döntés a `docs/decisions/effektus-vagolap-ket-reteg.md`-ben.

⚠️ A korábbi állítás, hogy ez és a `picasapy.app.effects_controller.
EffectsClipboardMixin` (#152) MÁS Picasa-menüponthoz (más `ID_EDIT_*`
erőforráshoz) tartozna, TÉVES volt: az eredetiben **egy** parancspár van
(`ID_EDIT_COPYALLEFFECTS`/`ID_EDIT_PASTEALLEFFECTS`, a Szerkesztés menüben),
kétágú kezelővel — a Kép menüben egy sincs. A #152 réteg felület nélküli
referencia-megvalósítás marad (ADR-007 2. döntés), a két vágólap-állapot
pedig azért független, mert a két réteg külön él, nem mert két parancs
volna."""

from __future__ import annotations

import secrets
import threading
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.export import export_sidecar_for_photo
from picasapy.edit.effect_clipboard import (
    copy_all_effects,
    crop_mirror_value,
    paste_all_effects,
)
from picasapy.fileops import RenameItem, preview_name, rename_photos_many
from picasapy.index import (
    open_index,
    photos_with_keyword,
    photo_by_id,
    search_photos,
    update_photo_fields,
)
from picasapy.ini import (
    FilterWriteError,
    IniConflictError,
    IniSaveError,
    update_document,
)
from picasapy.ini.albums import ensure_album, with_album, without_album
from picasapy.metadata import write_iptc_caption
from picasapy.render.flip import (
    FLIP_HORIZONTAL,
    FLIP_MASK,
    FLIP_VERTICAL,
    toggled_flip,
)
from picasapy.scanner import PICASA_INI_NAME

from .worker_thread import BackgroundWorkerMixin

# #137: a tartós ütközés (párhuzamos Picasa-írás) is kezelt írási hiba — a
# felhasználó a megszokott hibacsatornán kap jelzést, nem néma adatvesztés.
# #643: a round-trip őr visszautasítása (`FilterWriteError`) ugyanígy KEZELT
# hiba — a szövege már magyar, felhasználónak szóló mondat (ld.
# `ini/filter_guard.py`), tehát a hibasávban olvashatóan jelenik meg. Nélküle
# nyers Python-kivételként bukna ki a háttérszálon: néma bukás a felületen.
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)


#: A `rotate` kulcs értéke nulla lépésnél. #2004: NEM töröljük, ha a sor
#: eredetileg ott volt — a Picasa a `rotate(0)`-t tekinti alapértéknek, nem
#: a hiányzó kulcsot (`0x0068b535`–`0x0068b58c` kulcs→alapérték tábla), és
#: ki is írja: a tulajdonos gyűjteményében 1 735 ilyen sor van.
def forgatas_mutacio(document, nev: str, steps: int):
    """A forgatás ini-mutációja — MEGŐRZŐ szabállyal (#2004).

    | a fájlban volt `rotate=` sor? | 0 lépésnél |
    |---|---|
    | igen | marad, `rotate(0)` értékkel |
    | nem | nem keletkezik |

    ⚠️ Miért nem az a megoldás, hogy MINDIG kiírjuk? Mert akkor olyan
    fájlokba is bekerülne, amelyekben eredetileg nem volt `rotate=` sor —
    és az ugyanúgy eltérés. A helyes szabály a megőrzés.

    A régi viselkedés (0-nál mindig törlés) épp a Picasa-eredetű fájlokon
    rontotta el a round-tripet, tehát ott, ahol a legfontosabb."""
    if steps != 0:
        return document.with_value(nev, "rotate", f"rotate({steps})")
    szakasz = document.section(nev)
    volt_sor = szakasz is not None and szakasz.get("rotate") is not None
    if volt_sor:
        return document.with_value(nev, "rotate", "rotate(0)")
    return document.with_removed(nev, "rotate")


#: #2976: a tükrözés ini-mutációja — a `forgatas_mutacio` párja.
#:
#: A mért írói szabály (`0x0042d7e0`) két részből áll: nem nulla maszknál
#: `flipped(N)`, nulla maszknál viszont a kulcs ÜRES értéket kap
#: (`0x0042d864`) — NEM `flipped(0)`.
def tukrozes_mutacio(document, nev: str, flags: int):
    """A tükrözés ini-mutációja, MEGŐRZŐ szabállyal.

    | a fájlban volt `flipped=` sor? | 0 maszknál |
    |---|---|
    | igen | marad, ÜRES értékkel (ezt írja az eredeti) |
    | nem | nem keletkezik |

    Miért nem írunk mindig üres sort: a korpusz 859 fájljában egyetlen
    `flipped=` sor sincs, mert a tulajdonos sosem tükrözött. Egy
    feltétel nélküli kiírás minden érintett fájlba új sort vinne, és az
    ugyanúgy eltérés a round-triptől — ez a `rotate` #2004-es szabálya."""
    maszk = int(flags or 0) & FLIP_MASK
    if maszk:
        return document.with_value(nev, "flipped", f"flipped({maszk})")
    szakasz = document.section(nev)
    volt_sor = szakasz is not None and szakasz.get("flipped") is not None
    if volt_sor:
        return document.with_value(nev, "flipped", "")
    return document.with_removed(nev, "flipped")


class PhotoOpsMixin(BackgroundWorkerMixin):
    """Csillag, felirat, forgatás és elrejtés — egyesével és kötegelten."""

    # #141: a háttérszálas ini-írás/index-UPDATE eredménye — a rács-sor
    # frissítését a GUI-szálra tereli (Qt automatikusan sorba állítja a
    # más szálból jövő emitet, ahogy a watcherDirty is teszi).
    # #1443: a harmadik elem az utómunka (hívható vagy None) — a GUI-szálon,
    # a sor frissítése UTÁN, de a `photoOpFinished` ELŐTT fut le. Külön
    # jelzés helyett azért ide, mert a tesztek (és a QML busy-jelzése) a
    # `photoOpFinished`-re várnak: egy másik, később sorra kerülő jelzésen
    # érkező utómunka a várakozás UTÁN futna le — néma versenyhelyzet.
    _photoFieldUpdated = Signal(int, object, object)
    photoOpFailed = Signal(str)
    #: #1526: a SZÖVEG-vágólap tartalma változott — ettől él/szürkül a
    #: „Szöveg beillesztése" menütétel. A Qt vágólapjának `dataChanged`-jére
    #: kötjük (`_ensure_caption_clipboard`), tehát egy MÁS program írása is
    #: eljut a menühöz, nem csak a sajátunk.
    captionClipboardChanged = Signal()
    photoOpFinished = Signal()
    # #9 (2. lépés): tartós ini-ütközésnél (párhuzamos Picasa-írás) emberi
    # hibaüzenet az albumtagság-íráshoz — a geoWriteFailed mintája.
    albumWriteFailed = Signal(str)
    #: #1403: az XMP-arcírás összegzése — (kiírt, kihagyott, első hiba oka).
    #: EGY jelzés a köteg végén, a `batchFinished` mintája: a felhasználó egy
    #: üzenetet kap, nem fájlonként egyet.
    xmpFacesFinished = Signal(int, int, str)
    #: #1403: a köteg állapota változott (aktív / haladás) — a folyamat-panel
    #: ezen frissül. A haladást property-k adják, a `BatchEditProgressPanel`
    #: bevált mintája szerint.
    xmpFacesStateChanged = Signal()
    #: #1403: a köteget MEGSZAKÍTOTTÁK. Az eredetinek külön állapotszövege van
    #: rá (`FaceTagJob::cancelled` — *Cancelled writing face tags*), tehát ez
    #: NEM ugyanaz, mint a befejezés. Az argumentum a MÁR kiírt darabszám.
    xmpFacesCancelled = Signal(int)
    #: #1755: a forgatás két JELZŐ ága, az eredeti két erőforrásával.
    #: Eddig mindkettő néma visszatérés volt: vegyes fotó+videó
    #: kijelölésnél a videók hallgatólagosan kimaradtak (#103), üres
    #: kijelölésnél pedig egyszerűen nem történt semmi. A felhasználó
    #: mindkét esetben ugyanazt látta: „nem forgott el minden", magyarázat
    #: nélkül.
    #:
    #: A szöveg NEM itt él, hanem a felületen (`PicasaNotifier.qml`) —
    #: a vezérlő csak a tényt jelenti, ahogy a `saveCopyReady` is.
    rotationTypeFailed = Signal(int)   # hány elem maradt ki
    rotationNeedsSelection = Signal()
    # #366: a tömeges átnevezés (fájlrendszer-írás, lehet lassú NAS-on)
    # háttérszálon fut; ez a jelzés tereli a resync/refresh-t vissza a
    # GUI-szálra, a `_photoFieldUpdated` mintája szerint.
    _renameBatchDone = Signal(list)  # [érintett mappák]
    # #459: sérült/betölthetetlen kép(ek) — a QML ebből építi az eredeti
    # Picasa szövege szerinti elrejtés-felajánlást ("...Would you like to
    # hide the files on disk?"). Elemek: {"id": int, "name": str}.
    brokenPhotosDetected = Signal(list)

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

    @Slot(str)
    def _on_broken_image_detected(self, photo_id: str) -> None:
        try:
            pid = int(photo_id.split("?", 1)[0])
        except ValueError:
            return
        if pid in self._broken_photo_ids:
            return
        photo = next((p for p in self._photos.photos if p.id == pid), None)
        if photo is None:
            return
        self._broken_photo_ids.add(pid)
        self.brokenPhotosDetected.emit([{"id": pid, "name": photo.name}])

    @Slot(list)
    def hidePhotosByIds(self, ids) -> None:
        """#459: a sérült-kép ajánlat "Hide Files" válasza — a MEGLÉVŐ
        elrejtés-úton (`_apply_batch`, a `toggleHiddenRows` mintája) fut,
        csak nem a rács aktuális sorindexeiből, hanem közvetlenül az
        id-kból dolgozik (a törött kép ekkorra már ki is görgethetett a
        nézetből)."""
        id_set = {int(i) for i in ids}
        photos = [p for p in self._photos.photos if p.id in id_set]
        if not photos:
            return

        def mutate(document, photo):
            return document.with_value(photo.name, "hidden", "yes")

        self._apply_batch(photos, mutate)

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

    @Slot(int, object, object)
    def _on_photo_field_updated(self, photo_id: int, record, after=None) -> None:
        if record is not None:
            self._photos.update_photo(photo_id, record)
            # a thumbnail-provider saját (memóriabeli) nyilvántartását is
            # frissíteni kell (forgatás!) — ezt eddig a teljes _show()
            # tette meg; célzott frissítésnél nem fut _show(), ezért itt
            # pótoljuk (olcsó, csak a jelen nézet listáját írja újra, nem
            # lemezműveletet indít)
            self._provider.register_photos(self._photos.photos)
        # #1443: az utómunka a sor frissítése UTÁN, a befejezés-jelzés ELŐTT
        # fut — így a `photoOpFinished`-re váró hívó (QML, teszt) már a
        # végleges nézetet látja. `record is None` esetén is lefut: ha a kép
        # eltűnt az indexből, a nézetnek pláne frissülnie kell.
        if after is not None:
            after()
        self.photoOpFinished.emit()

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

    @Slot(str)
    def _on_photo_write_failed(self, message: str) -> None:
        # meglévő hibajelzési minta (#86/#150): ugyanaz a csatorna, mint a
        # háttér-szinkron hibáié
        self.syncFailed.emit(message)
        self.photoOpFinished.emit()

    def _run_photo_write(self, photo_id: int, perform, after=None) -> None:
        """Ini/IPTC-írás (NAS: backup+temp+fsync) + célzott index-UPDATE
        háttérszálon (#141). A `perform()` a teljes lassú munkát végzi (fájl-
        írás + a {oszlop: érték} dict összeállítása), és teljes egészében a
        munkásszálon fut. #505: a busy-jelzést a `_start_background`
        (`worker_thread.py`) intézi, nem itt.

        `after`: opcionális utómunka (#1443), amit a GUI-szálon, a rács-sor
        frissítése után hívunk. Írási hiba esetén NEM fut le — olyankor a
        nézet tartalma sem változott."""
        self._ensure_photo_ops_wired()

        def worker() -> None:
            try:
                fields = perform()
                with open_index(self._db_path) as conn:
                    if fields:
                        update_photo_fields(conn, photo_id, **fields)
                    record = photo_by_id(conn, photo_id)
            except _WRITE_ERRORS as error:
                self.photoOpFailed.emit(str(error))
                return
            self._photoFieldUpdated.emit(photo_id, record, after)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-photowrite")

    def _run_photo_writes(self, jobs, after=None) -> None:
        """Több kép írása SOROSAN, EGYETLEN háttérszálon (#2915).

        Képenként külön szálat indítani versenyhelyzet: a kijelölés képei
        jellemzően EGY mappában vannak, tehát ugyanabba a `.picasa.ini`-be
        és ugyanabba az indexbe írnak. A windowsos CI ki is mutatta: a
        kijelölés egy része felirat nélkül maradt. A soros út mellékesen a
        NAS-t is kíméli (N párhuzamos backup+temp+fsync helyett egy), és a
        `_apply_batch`-hez hasonlóan EGY index-kapcsolatot használ.

        `jobs`: `(photo_id, perform)` párok; a `perform()` a teljes lassú
        munka, ugyanúgy, mint a `_run_photo_write`-nál. Az `after` utómunka
        a GUI-szálon, a KÖTEG végén fut le egyszer.
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

        self._start_background(worker, name="picasapy-photowrite-koteg")

    #: #1443: azok a nézetmódok, amelyek TAGSÁGA a csillag-mezőtől függ.
    #: Ha itt állunk, a csillag ki/be kapcsolása nem egy sor megjelenését
    #: változtatja, hanem a lista TARTALMÁT — a nézetet újra le kell
    #: kérdezni. A mappa-nézetben ellenben a sornak maradnia kell.
    _CSILLAG_SZURT_NEZETEK = ("starred",)

    def _refresh_if_star_filtered(self) -> None:
        """Újralekérdezés, ha a csillag a jelen nézet tagságát dönti el.

        Szándékosan lekérdezés (`_refresh_view`) és nem sor-eltávolítás: így
        a visszacsillagozás is magától bekerül, és a zöld eredménysáv
        darabszáma is követ."""
        if self._view_mode[0] in self._CSILLAG_SZURT_NEZETEK:
            self._refresh_view()

    #: #1515: azok a nézetmódok, amelyek TAGSÁGÁT a keresés dönti el. A
    #: `search-folder` (#45: keresés közben mappára kattintva) is ide
    #: tartozik: a rács ott a találatok egy mappára szűkített része, tehát
    #: a kiesés ott is kiesés.
    _KERESES_SZURT_NEZETEK = ("search", "search-folder")

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

    @Slot(int)
    def toggleStar(self, row: int) -> None:
        """Csillag be/ki — a .picasa.ini-be írva (kétirányú kompatibilitás:
        a párhuzamosan futó eredeti Picasa is látja). Levételkor a kulcs
        törlődik, ahogy a Picasa csinálja.

        #1443: csillag-szűrt nézetben (Csillagozottak) a művelet a lista
        TARTALMÁT változtatja, ezért utómunkaként újralekérdezzük a nézetet
        — a kötegelt út (`toggleStarMany` → `_apply_batch`) ezt már eddig is
        megtette."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        new_star = not photo.star

        def perform() -> dict:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME

            def mutate(document):
                if new_star:
                    return document.with_value(photo.name, "star", "yes")
                return document.with_removed(photo.name, "star")

            update_document(ini_path, mutate, backup=True)
            return {"star": int(new_star)}

        self._run_photo_write(
            photo.id, perform, after=self._refresh_if_star_filtered
        )

    # -- Szöveg-vágólap: a FELIRATRA hat, nem a fájlra (#1526) -------------
    #
    # MÉRVE: az `eMenuEdit` névtérben a `Copy Text` / `Paste Text` a
    # feliratszöveg vágólap-műveletei — a fájl-vágólap (`Cut`/`Copy`/`Paste`,
    # `fileops_controller`) ettől KÜLÖN készlet, két külön névtérben
    # (`eMenuEdit` és `Address`). A jegy hét parancsából ez a kettő maradt.
    #
    # ⚠️ Fej nélküli környezetben (`offscreen`/`minimal`) NEM nyúlunk a
    # rendszervágólaphoz: nincs mögötte vágólap-tulajdonos, és a Qt-hívás a
    # CI-n SZEGMENSHIBÁVAL állította meg a tesztfájlt (`exit -11`) — nem
    # kivétellel, amit el lehetne kapni (ld. `fileops_controller`
    # `_tegyd_a_vagolapra`). Ilyenkor egy munkamenet-szintű szövegtár áll a
    # helyén, tehát a művelet nem lesz néma, és a próbák AZT mérik, amit
    # feltennénk.

    def _ensure_caption_clipboard(self) -> None:
        """Lusta, egyszeri bekötés a rendszervágólap `dataChanged`-jére.

        Enélkül a menütétel csak a MI írásainkról tudna, egy másik program
        vágólap-írásáról nem — a „Szöveg beillesztése" hazug állapotban
        ragadna. Fej nélküli környezetben nincs mihez kötni; ott a
        munkamenet-szintű tár változásait a saját írásunk jelzi."""
        if getattr(self, "_caption_clipboard_wired", False):
            return
        self._caption_clipboard_wired = True
        self._caption_clipboard = ""
        from PySide6.QtGui import QGuiApplication

        if QGuiApplication.platformName() in ("offscreen", "minimal"):
            return
        vagolap = QGuiApplication.clipboard()
        if vagolap is not None:
            vagolap.dataChanged.connect(self.captionClipboardChanged.emit)

    #: ⚠️ SZÁNDÉKOSAN nem `@Slot`: a felület nem a szövegtárral beszél, hanem
    #: a `copyCaptionText`/`pasteCaptionText` parancsokkal. Egy bekötetlen
    #: slot néma lánc-szakadás lenne (`scripts/kepesseg_or.py`), ez viszont
    #: a próbák és a fej nélküli környezet belépője.
    def setCaptionClipboardText(self, text: str) -> None:  # noqa: N802
        """A szöveg-vágólap FELTÖLTÉSE."""
        from PySide6.QtGui import QGuiApplication

        self._ensure_caption_clipboard()
        self._caption_clipboard = str(text or "")
        self.captionClipboardChanged.emit()
        if QGuiApplication.platformName() in ("offscreen", "minimal"):
            return
        vagolap = QGuiApplication.clipboard()
        if vagolap is not None:
            vagolap.setText(self._caption_clipboard)

    def captionClipboardText(self) -> str:  # noqa: N802
        """A szöveg-vágólap tartalma. Fej nélküli környezetben a
        munkamenet-szintű tár, egyébként a rendszervágólap.

        (Szintén nem `@Slot` — ld. a `setCaptionClipboardText` fölötti okot.)"""
        from PySide6.QtGui import QGuiApplication

        self._ensure_caption_clipboard()
        if QGuiApplication.platformName() in ("offscreen", "minimal"):
            return getattr(self, "_caption_clipboard", "")
        vagolap = QGuiApplication.clipboard()
        return "" if vagolap is None else vagolap.text()

    @Property(bool, notify=captionClipboardChanged)
    def hasCaptionTextClipboard(self) -> bool:  # noqa: N802
        """Van-e SZÖVEG a vágólapon — ettől él a „Szöveg beillesztése".

        Szándékosan nem gyorstárazzuk: a vágólapot más program is átírhatja,
        és a menü megnyitásakor a FRISS állapot kell (a `clipboardHasFiles`
        mintája)."""
        return bool(self.captionClipboardText().strip())

    @Slot(int, result=bool)
    def copyCaptionText(self, row: int) -> bool:  # noqa: N802
        """A kép FELIRATA a vágólapra („Copy Text").

        `False`, ha nincs mit másolni: érvénytelen sor, vagy a képnek nincs
        felirata. Üres szöveget feltenni annyi lenne, mint kiürítni a
        vágólapot — azt a felhasználó nem kérte."""
        photos = self._photos.photos
        if not 0 <= int(row) < len(photos):
            return False
        felirat = (self._photos.captionAt(int(row)) or "").strip()
        if not felirat:
            return False
        self.setCaptionClipboardText(felirat)
        return True

    @Slot("QVariantList", result=int)
    def pasteCaptionText(self, rows) -> int:  # noqa: N802
        """A vágólap szövege a KIJELÖLT képek feliratába („Paste Text").

        Az eredetiben a parancs a kijelölésre hat, nem egy képre. Visszaadja,
        hány képre indult írás.

        ⚠️ ÜRES vágólapra nem tesz semmit: a meglévő feliratok letörlése néma
        adatvesztés lenne — a törlésre a felirat-szerkesztő van."""
        szoveg = self.captionClipboardText().strip()
        if not szoveg:
            return 0
        photos = self._photos.photos
        kijeloles = []
        for row in rows:
            try:
                sor = int(row)
            except (TypeError, ValueError):
                continue
            if 0 <= sor < len(photos):
                kijeloles.append(photos[sor])
        if not kijeloles:
            return 0

        # #2915: EGY soros köteg, nem képenként egy szál — ugyanabba az
        # ini-be és indexbe írás párhuzamosan versenyhelyzet volt.
        azonositok = [photo.id for photo in kijeloles]

        def utomunka() -> None:
            for photo_id in azonositok:
                self._refresh_if_dropped_from_search(photo_id)

        self._run_photo_writes(
            [self._felirat_iras(photo, szoveg) for photo in kijeloles],
            after=utomunka,
        )
        return len(kijeloles)

    @Slot(int, str)
    def setCaption(self, row: int, text: str) -> None:
        """Felirat mentése — Picasa írási szabály (spec #3): JPEG-nél az
        IPTC-be (a képfájlba) írjuk, minden más formátumnál a .picasa.ini-be,
        ahogy a csillag/forgatás is. Az IPTC-írás sikertelensége esetén
        (pl. sérült fájl) defenzíven az ini-útra esünk vissza.

        #1515: a felirat FTS-mező, tehát keresési nézetben a művelet a lista
        TARTALMÁT is változtathatja — az utómunka ezért megnézi, találat
        maradt-e a kép, és csak kiesésnél kérdezi újra a nézetet."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        photo_id, perform = self._felirat_iras(photo, text)
        self._run_photo_write(
            photo_id,
            perform,
            after=lambda: self._refresh_if_dropped_from_search(photo_id),
        )

    def _felirat_iras(self, photo, text: str):
        """Egy kép felirat-írása `(photo_id, perform)` párként (#2915).

        A `perform()` a teljes lassú munka (IPTC- vagy ini-írás); így
        ugyanaz a kód szolgálja az egy képre menő `setCaption`-t és a
        kijelölésre menő, SOROS köteget (`pasteCaptionText`)."""
        text = (text or "").strip()
        is_jpeg = photo.name.lower().endswith((".jpg", ".jpeg"))

        def perform() -> dict:
            if is_jpeg:
                path = Path(photo.folder_path) / photo.name
                if write_iptc_caption(path, text):
                    return {"caption_file": text or None}
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME

            def mutate(document):
                if text:
                    return document.with_value(photo.name, "caption", text)
                return document.with_removed(photo.name, "caption")

            update_document(ini_path, mutate, backup=True)
            return {"caption_ini": text or None}

        return photo.id, perform

    # -- tömeges átnevezés (#366, rename.fen paritás) ------------------------

    @Slot(list, str, bool, bool, result=str)
    def renamePreview(
        self, rows, base_name: str, include_date: bool, include_size: bool
    ) -> str:
        """A `rename.fen` élő előnézete: a kijelölés ELSŐ fájljának végleges
        neve, ha most elfogadnák a dialógust (sorszám nélkül — ő az első a
        sorban). Tiszta lekérdezés, nem ír semmit."""
        photos = self._rows_to_photos(rows)
        if not photos or not (base_name or "").strip():
            return ""
        photo = photos[0]
        item = RenameItem(
            path=Path(photo.folder_path) / photo.name,
            date=photo.taken_at,
            width=photo.width,
            height=photo.height,
        )
        return preview_name(
            base_name.strip(), item,
            include_date=include_date, include_size=include_size, sequence=0,
        )

    @Slot(list, str, bool, bool)
    def renamePhotosMany(
        self, rows, base_name: str, include_date: bool, include_size: bool
    ) -> None:
        """Tömeges átnevezés (#366): a kijelölt N fájl közös alapnevet kap
        (+ opcionális dátum-/felbontás-utótag), Picasa-mintájú sorszámozással
        (`név`, `név-1`, `név-2`…). Az egyfájlos F2-út
        (`FileOpsController.renamePhoto`) ettől függetlenül, változatlanul
        működik — ez egy külön, kötegelt művelet. A lemezírás (potenciálisan
        lassú NAS) és az utána következő resync háttérszálon fut, a
        csillag/felirat mintáját követve (#141)."""
        base_name = (base_name or "").strip()
        photos = self._rows_to_photos(rows)
        if not base_name or not photos:
            return
        self._ensure_photo_ops_wired()

        items = [
            RenameItem(
                path=Path(photo.folder_path) / photo.name,
                date=photo.taken_at,
                width=photo.width,
                height=photo.height,
            )
            for photo in photos
        ]

        def worker() -> None:
            try:
                rename_photos_many(
                    items, base_name,
                    include_date=include_date, include_size=include_size,
                )
            except (OSError, ValueError, IniSaveError, IniConflictError) as error:
                self.photoOpFailed.emit(str(error))
                return
            folders = sorted({str(item.path.parent) for item in items})
            self._renameBatchDone.emit(folders)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-rename")

    @Slot(list)
    def _on_rename_batch_done(self, folders: list[str]) -> None:
        """A háttérszálas tömeges átnevezés után (GUI-szálon): érintett
        mappák resyncje + a nézet frissítése — az `_apply_batch` mintája,
        csak háttérszálas indítással (a lemezírás már megtörtént)."""
        with open_index(self._db_path) as conn:
            for folder in folders:
                self._sync_tree(conn, folder)
        self._refresh_view()
        self.photoOpFinished.emit()

    # -- virtuális albumok (#9, 2. lépés) ------------------------------------

    @Slot(list, str)
    def addRowsToAlbum(self, rows, token: str) -> None:
        """A kijelölés felvétele egy MEGLÉVŐ albumba: az `albums=` CSV
        bővítése minden érintett fotónál, mappánként egyetlen ütközésbiztos
        ini-írással (`_apply_batch`, a `setGeotagRows` mintája)."""
        token = (token or "").strip()
        if not token:
            return
        valid = self._rows_to_photos(rows)
        if not valid:
            return

        def mutate(document, photo):
            return with_album(document, photo.name, token)

        self._write_album_batch(valid, mutate)

    @Slot(list, str)
    def removeRowsFromAlbum(self, rows, token: str) -> None:
        """A kijelölés kivétele egy albumból (a definíció, `[.album:token]`,
        a mappában marad — csak a tagság törlődik, ahogy a Picasa is teszi)."""
        token = (token or "").strip()
        if not token:
            return
        valid = self._rows_to_photos(rows)
        if not valid:
            return

        def mutate(document, photo):
            return without_album(document, photo.name, token)

        self._write_album_batch(valid, mutate)

    @Slot(str, list, result=str)
    def createAlbum(self, name: str, rows) -> str:
        """Új virtuális album a kijelölt képekkel: véletlen (32 hex karakteres)
        token, a `[.album:<token>]` definíció MINDEN érintett mappa ini-jébe
        kiírva — a Picasa is minden mappába kiírja, ahol az albumnak van
        tagja —, a tagság pedig `with_album`-mal minden kijelölt fotónál.
        Visszaadja az új tokent (üres kijelölésnél/hibánál üres stringet)."""
        return self._albumot_keszit(name, self._rows_to_photos(rows))

    def _albumot_keszit(self, name: str, photos) -> str:
        """Album készítése MEGADOTT fotókból (a `createAlbum` magja, #1406).

        A `createAlbum` a KIJELÖLÉS soraiból hívja, a „Címke megjelenítése
        albumként" pedig a címke szerint lekérdezett fotókkal — a kettő
        ugyanezt az egyetlen írási utat használja, tehát az ini-írás, a
        hibakezelés és az albumlista-frissítés is közös."""
        if not photos:
            return ""
        token = secrets.token_hex(16)
        clean_name = (name or "").strip() or None

        def mutate(document, photo):
            document = ensure_album(document, token, clean_name)
            return with_album(document, photo.name, token)

        if not self._write_album_batch(photos, mutate):
            return ""
        return token

    # -- Beállítás asztali háttérképként (#1775) --------------------------------

    @Slot(int, result=bool)
    def setPhotoAsDesktopBackground(self, row: int) -> bool:  # noqa: N802
        """A kijelölt kép asztali háttérképnek (`eMenuCreate::ID_WALLPAPER`).

        Az eredeti (mérve, `0x0057aa10`, 1143 b) **másolatot** ír:
        `picasabackground.bmp` a `Picasa/Backgrounds` mappába — NEM az eredeti
        fájlra mutat —, majd középre teszi (`WallpaperStyle=0`,
        `TileWallpaper=0`). A másolat azért fontos, mert így a kép átnevezése
        vagy törlése nem viszi el az asztal hátterét.

        A motor közös a kollázs-ágéval (`app/wallpaper.py`, #1005): ugyanaz a
        BMP-írás, ugyanaz a beállító lánc, és ugyanaz a két visszajelzés
        (`desktopBackgroundApplied` / `desktopBackgroundFailed`) — egy hely,
        egy viselkedés.

        Visszatérés: elindult-e a művelet. Érvénytelen sorra `False`, és a
        hívó ebből tud üzenetet adni."""
        from . import collage_output as output
        from . import collage_prefs, wallpaper

        fotok = self._photos.photos
        if not 0 <= int(row) < len(fotok):
            return False
        foto = fotok[int(row)]
        forras = Path(foto.folder_path) / foto.name
        try:
            mappa = wallpaper.backgrounds_dir(
                output.output_dir(
                    self._get_settings().value(collage_prefs.OUTPUT_DIR_KEY)
                ),
                output._felulet_nyelve(),
            )
            bmp = wallpaper.write_background_bmp(forras, mappa)
        except OSError as hiba:
            self.photoOpFailed.emit(str(hiba))
            return False
        eszkoz = wallpaper.set_desktop_background(bmp)
        if eszkoz:
            self.desktopBackgroundApplied.emit(eszkoz)
        else:
            self.desktopBackgroundFailed.emit(str(bmp))
        return True

    # -- Arcinformációk írása XMP-be (#1403) -----------------------------------

    @Property(bool, notify=xmpFacesStateChanged)
    def xmpFacesActive(self) -> bool:
        """Fut-e épp az XMP-arcírás — a folyamat-panel ettől látszik."""
        return bool(getattr(self, "_xmp_faces_total", 0)) and not getattr(
            self, "_xmp_faces_done_all", True
        )

    @Property(int, notify=xmpFacesStateChanged)
    def xmpFacesDone(self) -> int:
        return int(getattr(self, "_xmp_faces_done", 0))

    @Property(int, notify=xmpFacesStateChanged)
    def xmpFacesTotal(self) -> int:
        return int(getattr(self, "_xmp_faces_total", 0))

    @Slot()
    def cancelXmpFaces(self) -> None:
        """A köteg megszakítása (#1403).

        Az eredeti kötegelt munkája megszakítható, és külön állapotszöveget ad
        rá (`FaceTagJob::cancelled`). A MÁR kiírt sidecarok érvényesek
        maradnak — a megszakítás nem visszavonás, ahogy a csoportos
        szerkesztésnél sem (`cancelBatchEdit`)."""
        esemeny = getattr(self, "_xmp_faces_cancel", None)
        if esemeny is not None:
            esemeny.set()

    @Slot()
    def writeFacesToXmp(self) -> None:
        """A LÁTOTT mappa képeinek XMP-sidecarja, arcrégiókkal (#1403).

        Az eredeti parancsa (`eMenuTools::ID_WRITE_XMP_FACES`, `.fen`
        `write_all_facetags`) kötegelt munkaként fut, és a HÁROM állapotát
        külön szöveg nevezi meg (`0x006b9dd0`): `FaceTagJob::progress` /
        `::done` / `::cancelled`. A köteg tehát **megszakítható**, a csak
        olvasható fájl pedig külön, megnevezett hibaeset:

            Face tag write failed for read only file: %s

        Ezért a köteg nem áll le az első hibán: végigmegy, és a végén EGY
        összegzést ad (kiírt · kihagyott · az első hiba oka). Megszakításnál a
        `xmpFacesCancelled` megy ki a MÁR kiírt darabszámmal — azok a
        sidecarok érvényesek maradnak.

        Az adat forrása a `.picasa.ini` (`export.export_sidecar_for_photo`),
        nem az index — így a frissen elnevezett arc is bekerül, mielőtt a
        szinkron végigfut.
        """
        utak = [
            Path(photo.folder_path) / photo.name
            for photo in self._photos.photos
        ]
        if not utak:
            self.xmpFacesFinished.emit(0, 0, "")
            return

        megszakitas = threading.Event()
        self._xmp_faces_cancel = megszakitas
        self._xmp_faces_total = len(utak)
        self._xmp_faces_done = 0
        self._xmp_faces_done_all = False
        self.xmpFacesStateChanged.emit()

        def worker() -> None:
            kiirt = 0
            kihagyott = 0
            elso_hiba = ""
            megszakitva = False
            for index, ut in enumerate(utak, start=1):
                if megszakitas.is_set():
                    megszakitva = True
                    break
                try:
                    eredmeny = export_sidecar_for_photo(ut)
                except OSError as hiba:
                    kihagyott += 1
                    if not elso_hiba:
                        elso_hiba = f"{ut.name}: {hiba}"
                else:
                    if eredmeny is None:
                        kihagyott += 1
                    else:
                        kiirt += 1
                self._xmp_faces_done = index
                self.xmpFacesStateChanged.emit()
            self._xmp_faces_done_all = True
            self.xmpFacesStateChanged.emit()
            if megszakitva:
                self.xmpFacesCancelled.emit(kiirt)
            else:
                self.xmpFacesFinished.emit(kiirt, kihagyott, elso_hiba)

        self._start_background(worker, name="picasapy-xmp-arcok")

    @Slot(str, result=str)
    def showTagAsAlbum(self, tag: str) -> str:
        """Egy CÍMKE tartalmából rendes album (#1406, `ID_SEARCHTOKEN`).

        Az eredeti a színkeresés FORDÍTOTTJA: ott a menüpont a keresőmezőbe
        ír (#1399), itt a felhasználó megad egy címkét, és abból **rendes
        album** lesz — nem élő szűrő.

        A címkét tételenként egyeztetjük (`index.photos_with_keyword`), tehát
        a „nyár" címke nem húzza be a „nyaralás"-t. Üres címkére és találat
        nélküli címkére üres stringgel térünk vissza — a felület ebből tud
        üzenetet adni (néma hatástalanság helyett)."""
        cimke = (tag or "").strip()
        if not cimke:
            return ""
        with open_index(self._db_path) as conn:
            fotok = photos_with_keyword(conn, cimke)
        return self._albumot_keszit(cimke, list(fotok))

    # -- Keresési eredmények mentése albumként (#1405) -------------------------

    #: A megerősítés küszöbe: az eredeti CSAK e FELETT kérdez
    #: (`0x005d86a0`, `CThumbUI::SaveSearchBig`). Alatta csendben létrejön az
    #: album — a kérdés nem „biztonsági", hanem a nagy album miatti
    #: figyelmeztetés.
    SAVE_SEARCH_CONFIRM_OVER = 1000

    def _mentheto_kereses(self) -> bool:
        """Menthető-e a jelenlegi nézet albumként (a `canSaveSearch` magja).

        Csak KERESÉSI nézetben él (az eredeti parancsa is az aktív keresés
        találatát mentette), és csak ha van találat — üres keresésből album
        sem lesz. A property a fővezérlőben áll, mert a `notify` jelzései
        (`statusChanged`, `feedChanged`) ott élnek.
        """
        return self._view_mode[0] in ("search", "search-folder") and bool(
            self._photos.photos
        )

    @Slot(result=str)
    def saveSearchAsAlbum(self) -> str:
        """A keresés TELJES találata új albumba (#1405).

        Az album neve a keresés szövege. ⚠️ Ez a MI döntésünk: az eredeti
        menüfelirat három pontra végződik („Save &search results..."), ami
        párbeszédet sejtet, a mért kezelő (`0x005d86a0`, 362 bájt) viszont
        CSAK az 1000 fölötti megerősítést tartalmazza — névkérő párbeszédnek
        nincs nyoma benne. A keresés szövege a legkézenfekvőbb név, és a
        felhasználó az albumot bármikor átnevezheti.

        A megerősítést a FELÜLET kéri (a küszöb fölött), mert az eredeti is
        ott kérdez; ez a slot már a döntés utáni munkát végzi. Visszatérés: az
        új album tokenje, üres stringgel jelezve, hogy nem jött létre."""
        if not self._mentheto_kereses():
            return ""
        mode, param = self._view_mode
        nev = param if isinstance(param, str) else str(param[0])
        return self.createAlbum(nev, list(range(len(self._photos.photos))))

    def _rows_to_photos(self, rows) -> list:
        photos = self._photos.photos
        return [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]

    def _write_album_batch(self, photos, mutate) -> bool:
        """Kötegelt albumtagság-írás hibakezeléssel (a `_write_geotag`
        mintája, `geo_controller.py`): sikertelen ütközésnél emberi
        hibaüzenet, nem néma adatvesztés. Sikeres írás után az albumlista
        (`controller.albums`) frissül, hogy a bal hasáb/menü azonnal lássa
        az új tagot/albumot. Visszaadja, hogy sikerült-e."""
        try:
            self._apply_batch(photos, mutate)
        except _WRITE_ERRORS as error:
            self.albumWriteFailed.emit(str(error))
            return False
        with open_index(self._db_path) as conn:
            self._load_albums(conn)
        return True

    @Slot(list)
    def toggleHiddenRows(self, rows) -> None:
        """Elrejtés/Megjelenítés a kijelölésre (Picasa): ha van még nem
        rejtett a kijelöltek közt, mindet elrejti; ha mind rejtett, mindet
        megjeleníti. Az ini-be `hidden=yes` kulcs kerül (levételkor törlődik)."""
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        hide_all = not all(p.hidden for p in valid)

        def mutate(document, photo):
            if hide_all:
                return document.with_value(photo.name, "hidden", "yes")
            return document.with_removed(photo.name, "hidden")

        self._apply_batch(valid, mutate)

    @Slot(list)
    def toggleStarMany(self, rows) -> None:
        """Csillag a teljes kijelölésre (Picasa-viselkedés): ha van még
        csillagozatlan a kijelöltek közt, mindet csillagozza; ha mind az,
        mindről leveszi. Mappánként EGY ini-írás + sync."""
        photos = self._photos.photos
        valid = [
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        ]
        if not valid:
            return
        star_all = not all(p.star for p in valid)

        def mutate(document, photo):
            if star_all:
                return document.with_value(photo.name, "star", "yes")
            return document.with_removed(photo.name, "star")

        self._apply_batch(valid, mutate)

    @Slot(list)
    def rotateRightMany(self, rows) -> None:
        self._rotate_many(rows, 1)

    @Slot(list)
    def rotateLeftMany(self, rows) -> None:
        self._rotate_many(rows, -1)

    def _rotate_many(self, rows, delta: int) -> None:
        photos = self._photos.photos
        kert = [int(r) for r in rows or () if 0 <= int(r) < len(photos)]
        # #103: a videókat kihagyjuk — a rotate= kulcsnak videón nincs
        # értelmes hatása; vegyes kijelölésnél csak a fotók forognak
        valid = [photos[r] for r in kert if photos[r].kind != "video"]

        # #1755: az eredeti Picasa ezt a két esetet MEGMONDJA
        # (`IDS_MUST_SELECT_TO_ROT`, `IDS_ROT_TYPEFAILED`); mi eddig némán
        # tértünk vissza. A jelzés a kihagyottak SZÁMÁT viszi, hogy a
        # felület el tudja dönteni, van-e mit mondani.
        if not kert:
            self.rotationNeedsSelection.emit()
            return
        kihagyott = len(kert) - len(valid)
        if kihagyott:
            self.rotationTypeFailed.emit(kihagyott)
        if not valid:
            return

        def mutate(document, photo):
            steps = (photo.rotate_steps + delta) % 4
            return forgatas_mutacio(document, photo.name, steps)

        self._apply_batch(valid, mutate)

    # -- Tükrözés (#2902): a forgatás párja, INDEX-ben tárolva ------------
    #
    # Az eredeti két billentyűt szán rá (`Ctrl+Shift+H` vízszintes,
    # `Ctrl+Shift+V` függőleges; `0x005e63d6` / `0x005e6408`), MENÜPONTOT
    # nem — a 3.9 menüiben nincs ilyen parancs, és nálunk sem lesz.
    #
    # #2976: a jelző MOSTANTÓL a `.picasa.ini`-be megy. A #2902 idejében az
    # `N` bit-jelentése feltevés volt, ezért maradt az indexben; a #2938
    # kimérte (0. bit = vízszintes, 1. bit = függőleges, nulla maszknál ÜRES
    # érték), tehát a tárolás igazolt — a forgatás útját járja.

    @Slot(list)
    def flipHorizontalMany(self, rows) -> None:  # noqa: N802
        """Vízszintes tükrözés a kijelölésre (a mért `(panel, 2)` ág)."""
        self._flip_many(rows, FLIP_HORIZONTAL)

    @Slot(list)
    def flipVerticalMany(self, rows) -> None:  # noqa: N802
        """Függőleges tükrözés a kijelölésre (a mért `(panel, 1)` ág)."""
        self._flip_many(rows, FLIP_VERTICAL)

    def _flip_many(self, rows, direction: int) -> None:
        """A jelző átváltása a kijelölés minden képén, EGY index-kapcsolaton.

        A videókat kihagyja, a forgatás mintája szerint (#103): a tükrözés
        képi művelet, videón nincs értelmes hatása. Ha a kijelölés üres, a
        forgatásnál bevált jelzést adja (`rotationNeedsSelection`), hogy a
        felület ugyanazt az eredeti üzenetet mutathassa."""
        photos = self._photos.photos
        kert = [int(r) for r in rows or () if 0 <= int(r) < len(photos)]
        valid = [photos[r] for r in kert if photos[r].kind != "video"]
        if not kert:
            self.rotationNeedsSelection.emit()
            return
        kihagyott = len(kert) - len(valid)
        if kihagyott:
            self.rotationTypeFailed.emit(kihagyott)
        if not valid:
            return

        def mutate(document, photo):
            return tukrozes_mutacio(
                document, photo.name,
                toggled_flip(photo.flip_flags, direction),
            )

        self._apply_batch(valid, mutate)

    def _apply_batch(self, photos, mutate) -> None:
        """Kötegelt ini-módosítás: mappánként egyetlen (atomikus, backupolt)
        írás és resync, de EGYETLEN index-kapcsolat a teljes köteg körül
        (#141) — nem mappánként újracsatlakozás."""
        by_folder: dict[str, list] = {}
        for photo in photos:
            by_folder.setdefault(photo.folder_path, []).append(photo)
        with open_index(self._db_path) as conn:
            for folder, folder_photos in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                # #137: a köteg egyetlen tiszta mutate-ként fut az
                # update_document alatt — ütközés esetén az egész köteg
                # újrajátszódik a friss (más író általi) dokumentumon.
                def batch_mutate(document, folder_photos=folder_photos):
                    for photo in folder_photos:
                        document = mutate(document, photo)
                    return document

                update_document(ini_path, batch_mutate, backup=True)
                self._sync_tree(conn, folder)
        self._refresh_view()

    @Slot(int)
    def rotateRight(self, row: int) -> None:
        self._apply_rotate(row, 1)

    @Slot(int)
    def rotateLeft(self, row: int) -> None:
        self._apply_rotate(row, -1)

    def _apply_rotate(self, row: int, delta: int) -> None:
        """Nem-destruktív forgatás: `rotate=rotate(n)` az ini-be.

        A nulla lépés szabályát a `forgatas_mutacio` mondja ki (#2004):
        a `rotate=` sor MEGMARAD, ha eredetileg ott volt. A korábbi
        indoklás („n=0-nál a kulcs törlődik, így a kör bitre pontos")
        MEGDŐLT: a Picasa a `rotate(0)`-t tekinti alapértéknek és ki is
        írja, tehát a törlés épp a Picasa-eredetű fájlokon rontotta el a
        round-tripet."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        if photo.kind == "video":
            return  # #103: videóra nem írunk rotate= kulcsot (QML-őr mellett)
        steps = (photo.rotate_steps + delta) % 4

        def perform() -> dict:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME

            def mutate(document):
                return forgatas_mutacio(document, photo.name, steps)

            update_document(ini_path, mutate, backup=True)
            return {"rotate_steps": steps}

        self._run_photo_write(photo.id, perform)

    # -- „Az összes effektus másolása/beillesztése" (#426) -------------------

    #: A vágólap tartalma/állapota változott (van-e másolt lánc, van-e
    #: visszavonható beillesztés) — a Szerkesztés menü két tételének
    #: engedélyezési feltétele.
    allEffectsClipboardChanged = Signal()

    def _ensure_effect_clipboard(self) -> None:
        """Lusta állapot-inicializálás (#150-minta: nem kell az __init__-et
        (forró fájl) módosítani a szelet bevezetéséhez). Szándékosan KÜLÖN
        állapot a `effects_controller.EffectsClipboardMixin`-től (#152) — a
        modul docstringje indokolja, miért két önálló funkció."""
        if not hasattr(self, "_effect_clipboard_value"):
            self._effect_clipboard_value: str | None = None
            # egyetlen visszavonási lépés (#426 elfogadási kritérium): az
            # utolsó beillesztés ELŐTTI (mappa, fájlnév, nyers filters=,
            # nyers crop=) NÉGYESEINEK listája; None = nincs (törölve/le nem
            # futott). #1544: a `crop=` tükör-kulcs is a négyesbe került —
            # enélkül a visszavonás a régi láncot adná vissza az ÚJ vágással
            # (ugyanaz a hiba, amit a #465 a köteges úton javított).
            self._effect_clipboard_undo: (
                list[tuple[str, str, str | None, str | None]] | None
            ) = None

    @Property(bool, notify=allEffectsClipboardChanged)
    def hasAllEffectsClipboard(self) -> bool:
        """Van-e másolt effektlánc — a „Beillesztés" menütétel engedélyezési
        feltétele."""
        self._ensure_effect_clipboard()
        return self._effect_clipboard_value is not None

    @Property(bool, notify=allEffectsClipboardChanged)
    def canUndoPasteAllEffects(self) -> bool:
        self._ensure_effect_clipboard()
        return self._effect_clipboard_undo is not None

    @Slot(list)
    def copyAllEffects(self, rows) -> None:
        """„Az összes effektus másolása": a kijelölés ELSŐ képének TELJES
        `filters=` lánca kerül az alkalmazás-szintű vágólapra — a vágással
        (`crop64`) és a régió-adatokkal (`redeye`/`retouch`) együtt, ahogy az
        eredeti Picasa másolója teszi (#1544; a szűrés a `mode="history"`
        oszlopból következtetett, téves szabály volt, ld.
        `picasapy.edit.effect_clipboard`). Tiszta lekérdezés — nem ír semmit."""
        self._ensure_effect_clipboard()
        photos = self._photos.photos
        valid_rows = [int(r) for r in rows if 0 <= int(r) < len(photos)]
        if not valid_rows:
            return
        photo = photos[valid_rows[0]]
        self._effect_clipboard_value = copy_all_effects(photo.filters)
        self.allEffectsClipboardChanged.emit()

    @Slot(list)
    def pasteAllEffects(self, rows) -> None:
        """„Az összes effektus beillesztése": a vágólap láncát a kijelölt
        képek MINDEGYIKÉRE alkalmazza, felülírva a meglévő láncot (#426).

        Mappánként EGYETLEN ini-írás (a `_apply_batch`/`effects_controller.
        EffectsClipboardMixin.pasteEffects` mintája): a beillesztés előtti
        nyers `filters=` és `crop=` értékek egyetlen undo-lépésként kerülnek
        a verembe, hogy a teljes köteg egy `undoPasteAllEffects()` hívással
        visszavonható legyen. Nincs háttérszál — az ini-írás gyors (nincs
        képfeldolgozás), a `_apply_batch`/`EffectsClipboardMixin.
        pasteEffects` szinkron mintáját követi.

        #1544: a lánccal EGYÜTT jár a `crop=rect64(...)` tükör-kulcs is (az
        `edit_controller._save()`/`effects_controller._write_session()`
        szabálya szerint). A `filters=`-beli `crop64` az EREDETI Picasában
        önmagában nem vág — a renderelést a `crop=` hajtja —, ezért e nélkül
        ugyanaz a NAS-mappa a windowsos Picasában vágatlan képet mutatna.
        Vágás nélküli lánc beillesztésekor a célkép meglévő `crop=` kulcsa
        TÖRLŐDIK: `crop64` nélküli `crop=` az éles korpuszban nulla esetben
        fordul elő (761-ből).

        ⚠️ **Más méretarányú célkép.** A `crop64` rect64-koordinátái
        relatívak ([0..1]), ezért a vágás a más alakú célképre is érvényes
        marad — arányosan ugyanazt a részt jelöli ki, sosem lóg ki a képből,
        és nem hibázik. A KOMPOZÍCIÓ más lesz (mérve: ugyanaz a rect 800×600
        képen 364×523, 600×800-on 273×697 kivágást ad), adat viszont nem
        vész el: az eredeti JPEG érintetlen, a `.picasa.ini` nem destruktív,
        és a művelet visszavonható. Az eredeti Picasa beillesztője sem tesz
        célkép-méret szerinti kivételt."""
        self._ensure_effect_clipboard()
        if self._effect_clipboard_value is None:
            return
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        clipboard_value = self._effect_clipboard_value
        new_value = paste_all_effects(clipboard_value)
        # #1544: a lánccal együtt járó `crop=` tükör-kulcs — minden célképre
        # ugyanaz, ezért egyszer számoljuk ki.
        new_crop = crop_mirror_value(new_value)

        by_folder: dict[str, list] = {}
        for photo in valid:
            by_folder.setdefault(photo.folder_path, []).append(photo)

        undo_batch: list[tuple[str, str, str | None, str | None]] = []
        with open_index(self._db_path) as conn:
            for folder, folder_photos in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[tuple[str, str, str | None, str | None]] = []

                # B023: az `entries` alapértelmezett argumentumként kötve —
                # a mutate szinkron fut, mielőtt a következő iteráció
                # újrakötné (az `effects_controller.pasteEffects` mintája).
                def mutate(
                    document, folder=folder, folder_photos=folder_photos, entries=entries
                ):
                    fresh: list[tuple[str, str, str | None, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        prev = section.get("filters") if section else None
                        prev_crop = section.get("crop") if section else None
                        fresh.append((folder, photo.name, prev, prev_crop))
                        if new_value:
                            # #643: a vágólapról ÁTVITT lánc — az idegen tag
                            # nem most keletkezik, ezért nem utasítjuk vissza.
                            document = document.with_value(
                                photo.name, "filters", new_value, carried=True
                            )
                        else:
                            document = document.with_removed(photo.name, "filters")
                        if new_crop is not None:
                            document = document.with_value(
                                photo.name, "crop", new_crop
                            )
                        else:
                            document = document.with_removed(photo.name, "crop")
                    entries[:] = fresh
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                undo_batch.extend(entries)
                # #750: a beillesztett lánc a TARTÓS naplóba is — mappánként
                # EGY naplóírással, hogy a köteget ne lassítsa. Üres
                # `new_value`-nál a bejegyzés törlődik, ahogy a `filters=`
                # kulcs is (ld. a mutate két ágát).
                self.recordSavedChains(
                    [
                        (str(Path(folder) / photo.name), new_value)
                        for photo in folder_photos
                    ]
                )
                self._sync_tree(conn, folder)

        self._effect_clipboard_undo = undo_batch
        self.allEffectsClipboardChanged.emit()
        self._refresh_view()

    @Slot()
    def undoPasteAllEffects(self) -> None:
        """Az utolsó „Az összes effektus beillesztése" visszavonása — minden
        érintett kép `filters=` ÉS `crop=` kulcsa visszaáll a beillesztés
        előtti (nyers) értékre (#426 elfogadási kritérium: egyetlen
        visszavonási lépés).

        #1544: a `crop=` azért van itt, mert a beillesztés is írja. Enélkül a
        visszavonás a RÉGI láncot adná vissza az ÚJ vágással — a célkép a
        windowsos Picasában olyan rect szerint vágódna, aminek a láncában
        nincs párja."""
        self._ensure_effect_clipboard()
        if not self._effect_clipboard_undo:
            return
        batch = self._effect_clipboard_undo
        self._effect_clipboard_undo = None

        by_folder: dict[str, list[tuple[str, str | None, str | None]]] = {}
        for folder, name, prev_filters, prev_crop in batch:
            by_folder.setdefault(folder, []).append((name, prev_filters, prev_crop))

        with open_index(self._db_path) as conn:
            for folder, entries in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                def mutate(document, entries=entries):
                    for name, prev_filters, prev_crop in entries:
                        if prev_filters is not None:
                            document = document.with_value(
                                name, "filters", prev_filters, carried=True  # #643
                            )
                        else:
                            document = document.with_removed(name, "filters")
                        if prev_crop is not None:
                            document = document.with_value(name, "crop", prev_crop)
                        else:
                            document = document.with_removed(name, "crop")
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                # #750: a visszavonás is a MI írásunk — a napló a beillesztés
                # ELŐTTI láncot védi tovább (üresnél törlődik a bejegyzés).
                self.recordSavedChains(
                    [
                        (str(Path(folder) / name), prev_filters or "")
                        for name, prev_filters, _prev_crop in entries
                    ]
                )
                self._sync_tree(conn, folder)

        self.allEffectsClipboardChanged.emit()
        self._refresh_view()
