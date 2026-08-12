"""Kép-tálca (Picture Tray, #455) — az AppController mixin-szelete.

Az eredeti Picasa alsó sávjában ült a **képtálca** (belső neve `scratch`,
UI-felirata „Selection"): ide gyűjtötted a képeket böngészés közben,
**mappákon átnyúlóan**, és a „Kijelölés megtartása" (Hold Selection)
gombbal rögzítetted, hogy egy újabb kijelölés ne söpörje el a korábbit.

Ez a szelet a tálca **állapot-magját** adja: a `PhotoRecord.id` (int)
alapján tartott, beszúrási sorrendű halmazt — NEM a rács sor-indexét,
mert az a mappaváltással elveszik (a #150 `selection.js` row-alapú
kijelölése emiatt önmagában NEM alkalmas mappákon átnyúló gyűjtésre).

Hatókör (első, önállóan szállítható lépcső — a #455 „Teendő" 1–2. pontja):
    - a tálca-állapot (megtartott fotó-id-k) + „megtartás" (`holdRows`)
    - jelvény-lekérdezés a rácshoz (`isHeldAt`)
    - ürítés (`clearHeld`)
    - a tálca-előnézet thumb-URL-je akkor is, ha a kép NEM a jelenlegi
      mappában van (`heldThumbUrlAt`) — a globális indexből.

NINCS ebben a lépcsőben (a jegyben nyitva marad):
    - a nyomtatás/e-mail/exportálás stb. műveletsor a tálca TARTALMÁN
      dolgozzon, ne a pillanatnyi kijelölésen (a jegy szerint ez a
      lényegi különbség — külön lépcső, mert minden érintett
      controller-szeletet átjárna);
    - „Add to" gomb (a tálca tartalma egyenesen albumhoz adható);
    - ürítéskor a Picasa saját szövegű rákérdezése („Would you like to
      clear your old held items from the tray?" → „Clear Tray"/„Don't
      Clear") — a mai `ConfirmDialog` Igen/Nem/Mégse gombfelirata NEM
      egyezik ezekkel, egyedi dialógus kellene hozzá;
    - fogd-és-vidd (albumlistára ejtés → új album, kétértelműség-menü).

A #422-es körben elkészült: az „Add to" gomb (`addHeldToAlbum`) és a
tálca-tartalom útvonal-listája (`heldPaths`) — utóbbi az a bemenet, amire a
műveletsor (nyomtatás/e-mail/export) átállítható, amikor az érintett
controller-szeletek útvonalat is elfogadnak.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import open_index, photo_by_id
from picasapy.ini.albums import with_album
from picasapy.app.models import _thumb_url


class TrayMixin:
    """A képtálca (`scratch`) állapota — fotó-id-k, mappától függetlenül."""

    heldChanged = Signal()

    def _ensure_tray_wired(self) -> None:
        """Lusta, egyszeri állapot-inicializálás (a `PhotoOpsMixin.
        _ensure_photo_ops_wired` mintája) — a controller.py (forró fájl)
        `__init__`-jét emiatt nem kell módosítani, a szelet önmagában is
        működőképes marad."""
        if getattr(self, "_tray_wired", False):
            return
        self._tray_wired = True
        self._held_ids: list[int] = []  # beszúrási sorrend

    @Property(int, notify=heldChanged)
    def heldCount(self) -> int:
        self._ensure_tray_wired()
        return len(self._held_ids)

    @Slot(list)
    def holdRows(self, rows: list) -> None:
        """„Kijelölés megtartása" (Hold Selection): a megadott (jelenlegi
        mappabeli) sorok fotóit hozzáadja a tálcához, ha még nincsenek
        benne. A tálca ettől kezdve TÚLÉLI a mappaváltást."""
        self._ensure_tray_wired()
        changed = False
        for row in rows:
            photo_id = self._photos.idAt(int(row))
            if not photo_id:
                continue
            pid = int(photo_id)
            if pid not in self._held_ids:
                self._held_ids.append(pid)
                changed = True
        if changed:
            self.heldChanged.emit()

    @Slot(int, result=bool)
    def isHeldAt(self, row: int) -> bool:
        """Jelvényhez (rács): a `row` (jelenlegi mappa) fotója a tálcán
        van-e."""
        self._ensure_tray_wired()
        photo_id = self._photos.idAt(row)
        if not photo_id:
            return False
        return int(photo_id) in self._held_ids

    @Slot()
    def clearHeld(self) -> None:
        """A tálca teljes ürítése (rákérdezés nélkül — ld. modul-docstring
        „NINCS ebben a lépcsőben")."""
        self._ensure_tray_wired()
        if self._held_ids:
            self._held_ids = []
            self.heldChanged.emit()

    @Property("QVariant", notify=heldChanged)
    def heldPaths(self):
        """A tálcán tartott képek fájl-útvonalai, beszúrási sorrendben.

        **Ez a #455 lényegi pontja (3. teendő):** a tálca alatti műveletsor
        (nyomtatás · e-mail · exportálás · kollázs · film · feltöltés) az
        eredetiben a TÁLCA TARTALMÁN dolgozott, nem a pillanatnyi
        kijelölésen — a Picasa buboréksúgói is végig „a képtálca képeire"
        hivatkoznak. Útvonalat adunk vissza (nem rács-sort), mert a tartott
        kép lehet, hogy nem a jelenleg megnyitott mappában van.

        A globális indexből olvas; az időközben eltűnt (törölt/áthelyezett)
        képek egyszerűen kimaradnak — nem hiba, és nem is akaszt meg egy
        műveletet.
        """
        self._ensure_tray_wired()
        if not self._held_ids:
            return []
        paths = []
        with open_index(self._db_path) as conn:
            for photo_id in self._held_ids:
                record = photo_by_id(conn, photo_id)
                if record is not None:
                    paths.append(
                        str(Path(record.folder_path) / record.name)
                    )
        return paths

    @Slot(str, result=bool)
    def addHeldToAlbum(self, token: str) -> bool:
        """„Add to" (#455): a TÁLCA TARTALMA egy meglévő albumba.

        Az eredetiben a tálcán külön gomb kínálta ezt — a gyűjtött képek
        egyenesen albumhoz adhatók, felfelé nyíló menüből. A tálca
        mappákon átnyúlik, ezért az `addRowsToAlbum` (rács-sor alapú)
        útja itt nem járható: a tartott fotókat a GLOBÁLIS indexből
        oldjuk fel, és mappánként egyetlen ini-írással írjuk (ugyanaz a
        `_write_album_batch`, mint a sor-alapú úton).

        Üres tálcánál/tokennél `False` (nincs mit tenni), egyébként az
        írás sikerét adja vissza.
        """
        self._ensure_tray_wired()
        token = (token or "").strip()
        if not token or not self._held_ids:
            return False
        with open_index(self._db_path) as conn:
            photos = [
                record
                for record in (
                    photo_by_id(conn, photo_id) for photo_id in self._held_ids
                )
                if record is not None
            ]
        if not photos:
            return False
        return self._write_album_batch(
            photos, lambda document, photo: with_album(document, photo.name, token)
        )

    @Slot(int, result=str)
    def heldThumbUrlAt(self, index: int) -> str:
        """A tálca-előnézet `index`. elemének thumb-URL-je — a GLOBÁLIS
        indexből (`photo_by_id`), mert a tartott kép lehet, hogy nem a
        jelenleg megnyitott mappában van."""
        self._ensure_tray_wired()
        if not 0 <= index < len(self._held_ids):
            return ""
        with open_index(self._db_path) as conn:
            record = photo_by_id(conn, self._held_ids[index])
        if record is None:
            return ""
        return _thumb_url(record)
