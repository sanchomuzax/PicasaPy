"""Címkék / kulcsszavak (#12) — az AppController címke-szelete (#150).

Mixin-osztály: az `AppController` örökli; a QML és a tesztek változatlanul
a `controller.keywordsOfRows(...)` felületet hívják."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import open_index
from picasapy.ini import update_document
from picasapy.metadata import write_iptc_keywords
from picasapy.scanner import PICASA_INI_NAME


def _split_keywords(raw: str | None) -> tuple[str, ...]:
    """A hatásos kulcsszó-CSV (index) felbontása tiszta címke-listára."""
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _clean_keyword(text: str) -> str:
    """Címke-input normalizálása: a vessző a CSV-tár (ini/index) elválasztója,
    ezért nem lehet a címke része — szóközzé simítjuk."""
    return " ".join(text.replace(",", " ").split())


class KeywordsMixin:
    """A Címkék-panel (#12) műveletei: unió-lista, hozzáadás, levétel."""

    @Slot(list, result=list)
    def keywordsOfRows(self, rows) -> list:
        """A kijelölés címkéinek uniója, névsorban — a Címkék-panel listája."""
        photos = self._photos.photos
        seen: dict[str, str] = {}  # casefold → első előfordulás (írásmód-őrző)
        for row in rows:
            if not 0 <= int(row) < len(photos):
                continue
            for keyword in _split_keywords(photos[int(row)].keywords):
                seen.setdefault(keyword.casefold(), keyword)
        return sorted(seen.values(), key=str.casefold)

    @Slot(list, str)
    def addKeywordToRows(self, rows, keyword: str) -> None:
        """Címke hozzáadása a kijelölt képekhez (már meglévőt nem duplikál)."""
        keyword = _clean_keyword(keyword)
        if not keyword:
            return

        def transform(keywords: tuple[str, ...]) -> tuple[str, ...]:
            if keyword.casefold() in (k.casefold() for k in keywords):
                return keywords
            return (*keywords, keyword)

        self._apply_keywords(rows, transform)

    @Slot(list, str)
    def removeKeywordFromRows(self, rows, keyword: str) -> None:
        """Címke levétele a kijelölt képekről (kis-nagybetű-tűrően)."""
        folded = _clean_keyword(keyword).casefold()
        if not folded:
            return

        def transform(keywords: tuple[str, ...]) -> tuple[str, ...]:
            return tuple(k for k in keywords if k.casefold() != folded)

        self._apply_keywords(rows, transform)

    def _apply_keywords(self, rows, transform) -> None:
        """Kulcsszó-módosítás a sorokra — Picasa írási szabály: JPEG-nél az
        IPTC Keywords (2:25) a tár (sikertelen írásnál defenzív ini-
        fallback), más formátumnál a .picasa.ini `keywords=` CSV kulcsa.
        Mappánként egyetlen ini-írás + resync (mint a _apply_batch)."""
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        by_folder: dict[str, list] = {}
        for photo in valid:
            by_folder.setdefault(photo.folder_path, []).append(photo)
        for folder, folder_photos in by_folder.items():
            ini_path = Path(folder) / PICASA_INI_NAME
            # Az IPTC-írás mellékhatás — az update_document mutate-je viszont
            # tiszta (újrajátszható) kell legyen (#137). Ezért az IPTC-t itt,
            # a mutate-en KÍVÜL, egyszer végezzük el, és csak az ini-be
            # kerülő (kulcs, érték|None) módosításokat gyűjtjük a mutate-nek.
            ini_edits: list[tuple[str, str | None]] = []
            for photo in folder_photos:
                current = _split_keywords(photo.keywords)
                updated = transform(current)
                if updated == current:
                    continue
                wrote_iptc = False
                if photo.name.lower().endswith((".jpg", ".jpeg")):
                    wrote_iptc = write_iptc_keywords(
                        Path(folder) / photo.name, updated
                    )
                if not wrote_iptc:
                    ini_edits.append(
                        (photo.name, ",".join(updated) if updated else None)
                    )
            if ini_edits:
                def mutate(document, edits=ini_edits):
                    for name, value in edits:
                        document = (
                            document.with_value(name, "keywords", value)
                            if value is not None
                            else document.with_removed(name, "keywords")
                        )
                    return document

                update_document(ini_path, mutate, backup=True)
            with open_index(self._db_path) as conn:
                self._sync_tree(conn, folder)
        self._refresh_view()
