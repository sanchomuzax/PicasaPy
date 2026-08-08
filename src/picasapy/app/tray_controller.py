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
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import open_index, photo_by_id
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
