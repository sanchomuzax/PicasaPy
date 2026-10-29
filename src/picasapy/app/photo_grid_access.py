"""A képrács soraihoz tartozó QML-adatok és útvonal-lekérdezések."""

from __future__ import annotations

import os
from urllib.parse import quote

from PySide6.QtCore import QUrl

from picasapy.metadata import megjelenitett_meret
from picasapy.paths import path_key
from picasapy.ini.movie_trim import trim_from_filters

from .display_mode_paint import current_display_mode_suffix, display_mode_url_suffix
from .model_helpers import _felbontas, _has_edits


class PhotoGridAccess:
    def thumbUrlAt(self, row: int) -> str:
        """Thumbnail-URL a kijelölés-tálca miniatűrjeihez."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return self._sor_url(photo)

    def itemAt(self, row: int) -> dict:
        """Egy sor teljes rács-adata a feed-delegate-nek (#64) — a
        csoportokra bontott rács Repeater-e nem modell-szerepekből köt,
        hanem ebből a dict-ből (a photos.revision-nel együtt kötve)."""
        if not 0 <= row < len(self._photos):
            return {}
        photo = self._photos[row]
        return {
            "name": photo.name,
            "thumbUrl": self._sor_url(photo),
            # #4332: a rács feedje is a kézi indexfelülírást mutassa.
            "takenAt": photo.taken_at or "",
            "star": photo.star,
            "caption": photo.caption or "",
            "isVideo": photo.kind == "video",
            "keywords": photo.keywords or "",
            #: #2996: a MEGJELENÍTETT felbontás — az index a tárolt méretet
            #: őrzi, a kép viszont az EXIF-orientációval jelenik meg.
            "resolution": _felbontas(photo),
            "hasEdits": _has_edits(photo),
            "hidden": photo.hidden,
            # #463: piros geo-pin jelvény — a `PhotoRecord.location` az
            # ini `geotag=` és az EXIF GPS-t is feloldja (ld. metadata/gps.py),
            # itt csak a meglétét kérdezzük.
            "hasGeo": photo.location is not None,
            # #463: arc-jelvények — „van rajta felismert arc", illetve
            # „van jóváhagyásra váró névjavaslat". A kettő KÜLÖN jelvény
            # volt az eredetiben is: az utóbbi azt jelzi, hogy elintézetlen
            # dolgod van a képpel.
            "hasFaces": photo.face_count > 0,
            "hasFaceSuggestion": photo.unnamed_face_count > 0,
        }

    def starAt(self, row: int) -> bool:
        """A sor csillag-állapota (a tálca ★ gombjának színezéséhez)."""
        return 0 <= row < len(self._photos) and self._photos[row].star

    def isVideoAt(self, row: int) -> bool:
        """Videó-e a sor (#14) — a néző erre vált lejátszó-nézetre."""
        return 0 <= row < len(self._photos) and self._photos[row].kind == "video"

    def movieTrimAt(self, row: int) -> dict:
        """A sor videó-VÁGÁSPONTJAI ezredmásodpercben (#1838).

        `{"start": <ms|-1>, "end": <ms|-1>}` — a **−1 jelenti, hogy azon az
        oldalon NINCS vágás**. Nem 0-t és nem a hosszt adunk: a hiányzó token
        más, mint a nulla pontra állított kezdés, és a QML-oldalon a `null`
        egy `int` kötésben némán 0-vá lapulna.

        A vágáspontok a `.picasa.ini` `filters=` láncából jönnek, és a
        round-trip őrzi őket akkor is, ha nem mi írtuk (`ini.movie_trim`).
        """
        if not 0 <= row < len(self._photos):
            return {"start": -1, "end": -1}
        trim = trim_from_filters(self._photos[row].filters or "")
        kezdet, veg = trim.start_ms(), trim.end_ms()
        return {
            "start": -1 if kezdet is None else kezdet,
            "end": -1 if veg is None else veg,
        }

    def captionAt(self, row: int) -> str:
        """A sor felirata (üres, ha nincs vagy az index érvénytelen) — a
        néző szerkeszthető felirat-mezőjének."""
        if not 0 <= row < len(self._photos):
            return ""
        return self._photos[row].caption or ""

    def fileUrlAt(self, row: int) -> str:
        """A kép file:// URL-je a nézőnek; üres, ha az index érvénytelen."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return QUrl.fromLocalFile(f"{photo.folder_path}/{photo.name}").toString()

    def displayUrlAt(self, row: int, mode: str = "") -> str:
        """A kép URL-je a DIAVETÍTÉSNEK — a megjelenítési móddal (#1640).

        Aktív mód nélkül a sima `file://` URL (bájtra a mód bevezetése
        előtti), tehát a mindennapi használat semmivel nem lassul. Ha a mód
        képpontot mozdít, a `displayphoto` szolgáltató URL-je jön, a móddal
        a lekérdezésben — az URL így egyértelműen meghatározza a képpontokat
        (ugyanaz az elv, mint a bélyegkép-úton, #1596).

        ⚠️ A nyers fájl URL-jét a diavetítés korábban KÖZVETLENÜL töltötte
        be, ezért a mód rajta soha nem látszott (#1640) — pedig a Projektor
        mód épp a kivetítéshez való.
        """
        fajl_url = self.fileUrlAt(row)
        if not fajl_url:
            return ""
        # ⚠️ #1640: a módot a hívó ADJA ÁT, nem innen olvassuk. A QML-kötés
        # csak akkor értékelődik újra módváltáskor, ha a mód VALÓDI
        # ARGUMENTUM: egy eldobott `controller.displayMode` referencia
        # (`(mod, url)` alakú vessző-kifejezés) nem hoz létre kötés-
        # függőséget — mérve (#1640): a dia URL-je a módváltás után is a
        # nyers fájlé maradt. Argumentum nélkül a modul-szintű mód a
        # tartalék (a többi hívónak).
        cimke = display_mode_url_suffix(mode) if mode else current_display_mode_suffix()
        if not cimke:
            return fajl_url
        if not 0 <= row < len(self._photos):
            return fajl_url
        photo = self._photos[row]
        utvonal = quote(f"{photo.folder_path}/{photo.name}")
        # a cimke `&d=<mód>` alakú (a bélyegkép-URL-ekhez illeszkedve), itt
        # ez az ELSŐ paraméter, ezért a `&`-et `?`-re cseréljük
        return f"image://displayphoto/{utvonal}?{cimke[1:]}"

    def _megjelenitett(self, row: int):
        """A sor MEGJELENÍTETT mérete (#2996) — EXIF-orientációval.

        ⚠️ A `.picasa.ini` `rotate=` forgatása NEM tartozik ide: azt a
        felület alkalmazza külön (`rotateAt`), a már EXIF-helyes képre."""
        photo = self._photos[row]
        return megjelenitett_meret(
            photo.width, photo.height, getattr(photo, "orientation", None)
        )

    def pixelWidthAt(self, row: int) -> int:
        """A kép VALÓDI képpont-szélessége (0, ha ismeretlen) — #2492.

        ⚠️ A néző eddig a `Image.sourceSize.width`-ből számolta az „1:1"
        arányát, csakhogy a Qt olvasáskor a BEÁLLÍTOTT `sourceSize`-t adja
        vissza (a `PhotoViewer.qml` 2560-as plafonját), nem a betöltött
        kép méretét — így a valódi mérettől függetlenül mindig 2560-cal
        számolt, és többszörösen nagyított.

        Az adat az indexben már megvan; a `resolution` szerep csak
        FORMÁZOTT sztringként adta ki (`"896x1344"`), amit QML-ben
        szétszedni törékeny lenne."""
        if not 0 <= row < len(self._photos):
            return 0
        return int(self._megjelenitett(row)[0] or 0)

    def pixelHeightAt(self, row: int) -> int:
        """A kép VALÓDI képpont-magassága (0, ha ismeretlen) — #2492.

        A szélesség párja, az EXIF-orientáció szerint megjelenített
        alakban. A néző „1:1" aránya NEM ebből számol: a `.picasa.ini`
        forgatása a kirajzolt kép `paintedWidth`-jét nem cseréli fel, az a
        forgatástól függetlenül a szélességgel arányos (#3760)."""
        if not 0 <= row < len(self._photos):
            return 0
        return int(self._megjelenitett(row)[1] or 0)

    def pixelSidesSwappedAt(self, row: int) -> bool:
        """Az EXIF-orientáció felcseréli-e a kép oldalait (5–8 állás) — #3832.

        A diavetítés a `sourceSize`-t a megjelenített méretből számolja, de
        a Qt fájlbetöltője (`PreserveAspectFit` + `autoTransform`) a kért
        méretet a fájlban TÁROLT tájolásra alkalmazza (mérve: egy 6-os
        állású, 5333×3000-es képnek 1440×2560-at kérve 2560×4551 jött
        vissza, 2560×1440-et kérve a helyes 1440×2560). Ehhez kell tudnia,
        hogy a kettő mikor tér el."""
        if not 0 <= row < len(self._photos):
            return False
        allas = getattr(self._photos[row], "orientation", None)
        return megjelenitett_meret(1, 2, allas) == (2, 1)

    def idAt(self, row: int) -> str:
        """A sor fotó-azonosítója — az EditController/editpreview kulcsa."""
        if not 0 <= row < len(self._photos):
            return ""
        return str(self._photos[row].id)

    def rowOfId(self, photo_id: int) -> int:
        """A fotó sor-indexe id alapján (#135): a QML ezzel képezi újra a
        kijelölést háttér-frissítés (reset) után — -1, ha a fotó már nincs
        a jelen nézetben (törölve/kiszűrve)."""
        return self.row_of_id(photo_id)

    def rowOfPath(self, path: str) -> int:
        """A kép sor-indexe ABSZOLÚT ÚTVONAL alapján; -1, ha nincs a nézetben.

        #1001: a kollázs a kép ÚTVONALÁT ismeri (a `.cxf` is azt tárolja), a
        néző és a szerkesztő viszont sorindexet vár — ez a kettő közti
        fordító. A `Main.qml` `collageSourceRows()`-a ezt a nevet már hívta
        a képtálcára (#985), csak a modellben nem volt meg: a tálcás ág néma
        QML-hibába futott.

        Az összehasonlítás NORMALIZÁLT útvonalon megy: a kollázs `Path`-ból
        építi a sztringet (Windowson fordított perjellel), a modell viszont
        `/`-t használ — a nyers egyenlőség a windows-lábon némán bukna."""
        if not path:
            return -1
        # Az index a mappákat `normalize_path()`-szal tárolja, a hívó viszont
        # adhat symlink/junction aliason át érkező Path/string alakot. A cél
        # feloldása hozza ugyanarra a tárolt útvonalra; a jelöltek már az
        # index kanonikus mappájából épülnek.
        cel = path_key(path)
        for i, photo in enumerate(self._photos):
            jelolt = os.path.normcase(
                os.path.normpath(os.path.join(photo.folder_path, photo.name))
            )
            if jelolt == cel:
                return i
        return -1

    def filePathAt(self, row: int) -> str:
        """A kép abszolút útvonala (EditController.beginEdit-hez); üres, ha
        az index érvénytelen."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return f"{photo.folder_path}/{photo.name}"

