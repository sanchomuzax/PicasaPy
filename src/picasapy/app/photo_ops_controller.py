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

from picasapy.ini import update_document as update_document

from .photo_ops_compat import (
    RENAME_USE_DATE_KEY as RENAME_USE_DATE_KEY,
    RENAME_USE_SIZE_KEY as RENAME_USE_SIZE_KEY,
    _WRITE_ERRORS as _WRITE_ERRORS,
)
from .photo_ops_album_mixin import PhotoOpsAlbumMixin
from .photo_ops_effect_clipboard_mixin import PhotoOpsEffectClipboardMixin
from .photo_ops_rename_mixin import PhotoOpsRenameMixin
from .photo_ops_transform_mixin import (
    PhotoOpsTransformMixin,
    forgatas_mutacio as forgatas_mutacio,
    tukrozes_mutacio as tukrozes_mutacio,
)
from .photo_ops_write_mixin import PhotoOpsWriteMixin
from .photo_ops_xmp_mixin import PhotoOpsXmpMixin
from .worker_thread import BackgroundWorkerMixin


# A `rename.fen` Example sora a rögzített Picasa-mintákat fűzi az alapnévhez;
# ezek szándékosan függetlenek a kijelölt fájl metaadataitól (#5702).
RENAME_SAMPLE_DATE = " 08-01-2004 2-30-45 PM"
RENAME_SAMPLE_SIZE = " 640x480"
RENAME_SAMPLE_EXTENSION = ".jpg"


class PhotoOpsMixin(
    PhotoOpsWriteMixin,
    PhotoOpsRenameMixin,
    PhotoOpsAlbumMixin,
    PhotoOpsXmpMixin,
    PhotoOpsTransformMixin,
    PhotoOpsEffectClipboardMixin,
    BackgroundWorkerMixin,
):
    """A QML-kompatibilis homlokzat a képműveletek témamixinekből."""
