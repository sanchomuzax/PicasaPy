"""Nem-destruktív fotó-műveletek (.picasa.ini-be írva): csillag, felirat,
forgatás, elrejtés — az AppController művelet-szelete (#150).

Mixin-osztály: az `AppController` örökli; minden írás a round-trip ini-
rétegen át történik (atomikus mentés + backup), majd célzott resync."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import open_index
from picasapy.ini import load_document, parse_document, save_document
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME


class PhotoOpsMixin:
    """Csillag, felirat, forgatás és elrejtés — egyesével és kötegelten."""

    @Slot(int)
    def toggleStar(self, row: int) -> None:
        """Csillag be/ki — a .picasa.ini-be írva (kétirányú kompatibilitás:
        a párhuzamosan futó eredeti Picasa is látja). Levételkor a kulcs
        törlődik, ahogy a Picasa csinálja."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        ini_path = Path(photo.folder_path) / PICASA_INI_NAME
        document = (
            load_document(ini_path) if ini_path.exists() else parse_document("")
        )
        if photo.star:
            document = document.with_removed(photo.name, "star")
        else:
            document = document.with_value(photo.name, "star", "yes")
        save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            self._sync_tree(conn, photo.folder_path)
        self._refresh_view()

    @Slot(int, str)
    def setCaption(self, row: int, text: str) -> None:
        """Felirat mentése — Picasa írási szabály (spec #3): JPEG-nél az
        IPTC-be (a képfájlba) írjuk, minden más formátumnál a .picasa.ini-be,
        ahogy a csillag/forgatás is. Az IPTC-írás sikertelensége esetén
        (pl. sérült fájl) defenzíven az ini-útra esünk vissza."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        text = text.strip()
        is_jpeg = photo.name.lower().endswith((".jpg", ".jpeg"))
        wrote_iptc = False
        if is_jpeg:
            path = Path(photo.folder_path) / photo.name
            wrote_iptc = write_iptc_caption(path, text)
        if not wrote_iptc:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME
            document = (
                load_document(ini_path) if ini_path.exists() else parse_document("")
            )
            if text:
                document = document.with_value(photo.name, "caption", text)
            else:
                document = document.with_removed(photo.name, "caption")
            save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            self._sync_tree(conn, photo.folder_path)
        self._refresh_view()

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
        # #103: a videókat kihagyjuk — a rotate= kulcsnak videón nincs
        # értelmes hatása; vegyes kijelölésnél csak a fotók forognak
        valid = [
            photos[int(r)]
            for r in rows
            if 0 <= int(r) < len(photos) and photos[int(r)].kind != "video"
        ]
        if not valid:
            return

        def mutate(document, photo):
            steps = (photo.rotate_steps + delta) % 4
            if steps == 0:
                return document.with_removed(photo.name, "rotate")
            return document.with_value(photo.name, "rotate", f"rotate({steps})")

        self._apply_batch(valid, mutate)

    def _apply_batch(self, photos, mutate) -> None:
        """Kötegelt ini-módosítás: mappánként egyetlen (atomikus, backupolt)
        írás és egyetlen resync — sok kijelölt képnél is gyors."""
        by_folder: dict[str, list] = {}
        for photo in photos:
            by_folder.setdefault(photo.folder_path, []).append(photo)
        for folder, folder_photos in by_folder.items():
            ini_path = Path(folder) / PICASA_INI_NAME
            document = (
                load_document(ini_path) if ini_path.exists() else parse_document("")
            )
            for photo in folder_photos:
                document = mutate(document, photo)
            save_document(document, ini_path, backup=True)
            with open_index(self._db_path) as conn:
                self._sync_tree(conn, folder)
        self._refresh_view()

    @Slot(int)
    def rotateRight(self, row: int) -> None:
        self._apply_rotate(row, 1)

    @Slot(int)
    def rotateLeft(self, row: int) -> None:
        self._apply_rotate(row, -1)

    def _apply_rotate(self, row: int, delta: int) -> None:
        """Nem-destruktív forgatás: rotate=rotate(n) az ini-be; n=0-nál a
        kulcs törlődik, így a teljes kör bitre pontos round-trip."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        if photo.kind == "video":
            return  # #103: videóra nem írunk rotate= kulcsot (QML-őr mellett)
        steps = (photo.rotate_steps + delta) % 4
        ini_path = Path(photo.folder_path) / PICASA_INI_NAME
        document = (
            load_document(ini_path) if ini_path.exists() else parse_document("")
        )
        if steps == 0:
            document = document.with_removed(photo.name, "rotate")
        else:
            document = document.with_value(photo.name, "rotate", f"rotate({steps})")
        save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            self._sync_tree(conn, photo.folder_path)
        self._refresh_view()
