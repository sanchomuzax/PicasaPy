"""Címkék / kulcsszavak (#12) — az AppController címke-szelete (#150).

Mixin-osztály: az `AppController` örökli; a QML és a tesztek változatlanul
a `controller.keywordsOfRows(...)` felületet hívják."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import all_photos, open_index
from picasapy.ini import update_document
from picasapy.metadata import write_iptc_keywords
from picasapy.scanner import PICASA_INI_NAME

# Gyorscímkék (#193) — a Címkék-panel alján 2×4 gombrács, a Picasa 3 mintájára.
_QUICK_TAG_SLOTS = 8
# a felső ennyi gomb foglalható le a legutóbb használt címkéknek
_QUICK_TAG_RESERVED = 2
# ennél többet a „legutóbb használt" lista nem kell hogy őrizzen (a felső
# 2 gombhoz elég, de eggyel több puffer a stabilabb sorrendhez)
_QUICK_TAG_RECENT_LIMIT = 8

_KEY_QUICK_LABELS = "quickTags/labels"
_KEY_QUICK_RESERVE_RECENT = "quickTags/reserveRecentForTop2"
_KEY_QUICK_AUTOFILL = "quickTags/autoFillFrequent"
_KEY_QUICK_RECENT = "quickTags/recentKeywords"


def _split_keywords(raw: str | None) -> tuple[str, ...]:
    """A hatásos kulcsszó-CSV (index) felbontása tiszta címke-listára."""
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _clean_keyword(text: str) -> str:
    """Címke-input normalizálása: a vessző a CSV-tár (ini/index) elválasztója,
    ezért nem lehet a címke része — szóközzé simítjuk."""
    return " ".join(text.replace(",", " ").split())


def _as_str_list(value) -> list[str]:
    """QSettings-listaérték normalizálása: 1 elemnél a Qt gyakran sima
    stringet ad vissza tömb helyett — ezt itt egyszeri listává csomagoljuk."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return [str(v) for v in value]


def _as_bool(value, default: bool) -> bool:
    if value is None:
        return default
    return value in (True, "true", "1")


class KeywordsMixin:
    """A Címkék-panel (#12) műveletei: unió-lista, hozzáadás, levétel.

    #193: a panel alján a Gyorscímkék szekció (2×4 gomb) is ide tartozik —
    a gombok konfigurációja (8 szlot + két kapcsoló) és a „legutóbb
    használt" előzmény QSettings-ben perzisztál, a `_get_settings()`
    (AppController) meglévő mintáját követve."""

    quickTagsChanged = Signal()

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
        self._record_recent_quick_tag(keyword)

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

    # -- Gyorscímkék (#193) --------------------------------------------------

    def _quick_tag_raw_labels(self) -> list[str]:
        """A 8 kézzel beállított szlot, mindig pontosan 8 elemű listaként
        (hiányzó/hibás mentésnél üres string tölti ki)."""
        stored = _as_str_list(self._get_settings().value(_KEY_QUICK_LABELS))
        labels = [_clean_keyword(v) for v in stored[:_QUICK_TAG_SLOTS]]
        labels += [""] * (_QUICK_TAG_SLOTS - len(labels))
        return labels

    def _quick_tag_recent(self) -> list[str]:
        """A legutóbb használt címkék, legfrissebb elöl."""
        return _as_str_list(self._get_settings().value(_KEY_QUICK_RECENT))

    def _record_recent_quick_tag(self, keyword: str) -> None:
        """A gyorscímke-előzmény frissítése egy sikeres/kísérelt
        hozzáadáskor (#193) — az ismételt használat a lista elejére kerül,
        duplikátum nélkül."""
        recent = [
            k for k in self._quick_tag_recent() if k.casefold() != keyword.casefold()
        ]
        recent.insert(0, keyword)
        self._get_settings().setValue(
            _KEY_QUICK_RECENT, recent[:_QUICK_TAG_RECENT_LIMIT]
        )
        self.quickTagsChanged.emit()

    def _frequent_keywords(self) -> list[str]:
        """Az egész könyvtár címkéi gyakoriság szerint csökkenő sorrendben
        (holtverseny: ábécérend) — a „gyakori címkék" automatikus
        kitöltéshez (#193). A teljes indexet olvassa, nem csak az aktuális
        nézetet."""
        counts: dict[str, list] = {}  # casefold -> [megjelenő alak, darab]
        with open_index(self._db_path) as conn:
            for record in all_photos(conn):
                for keyword in _split_keywords(record.keywords):
                    entry = counts.setdefault(keyword.casefold(), [keyword, 0])
                    entry[1] += 1
        ordered = sorted(
            counts.values(), key=lambda entry: (-entry[1], entry[0].casefold())
        )
        return [display for display, _count in ordered]

    @Property(list, notify=quickTagsChanged)
    def quickTagConfigLabels(self) -> list:
        """A 8 kézzel szerkeszthető szlot — a konfigurációs dialógus ezt
        mutatja/írja (a ténylegesen megjelenő gombokat ld. quickTagButtons)."""
        return self._quick_tag_raw_labels()

    @Slot(int, str)
    def setQuickTagLabel(self, slot: int, text: str) -> None:
        """Egy gyorscímke-szlot beállítása (0..7) — a konfigurációs
        dialógus szövegmezőinek onEditingFinished-je hívja."""
        slot = int(slot)
        if not 0 <= slot < _QUICK_TAG_SLOTS:
            return
        labels = self._quick_tag_raw_labels()
        labels[slot] = _clean_keyword(text)
        self._get_settings().setValue(_KEY_QUICK_LABELS, labels)
        self.quickTagsChanged.emit()

    @Property(bool, notify=quickTagsChanged)
    def quickTagsReserveRecent(self) -> bool:
        """Be van-e kapcsolva: a felső 2 gomb a legutóbb használt 2
        címkét mutatja (alapértelmezetten BE)."""
        return _as_bool(self._get_settings().value(_KEY_QUICK_RESERVE_RECENT), True)

    @Slot(bool)
    def setQuickTagsReserveRecent(self, value: bool) -> None:
        self._get_settings().setValue(_KEY_QUICK_RESERVE_RECENT, bool(value))
        self.quickTagsChanged.emit()

    @Property(bool, notify=quickTagsChanged)
    def quickTagsAutoFillFrequent(self) -> bool:
        """Be van-e kapcsolva: az üres szlotok gyakori címkékkel
        töltődnek ki automatikusan (alapértelmezetten KI)."""
        return _as_bool(self._get_settings().value(_KEY_QUICK_AUTOFILL), False)

    @Slot(bool)
    def setQuickTagsAutoFillFrequent(self, value: bool) -> None:
        self._get_settings().setValue(_KEY_QUICK_AUTOFILL, bool(value))
        self.quickTagsChanged.emit()

    @Property(list, notify=quickTagsChanged)
    def quickTagButtons(self) -> list:
        """A ténylegesen megjelenő 8 gombcímke (#193): a kézzel beállított
        szlotok, a felső 2 helyén — ha a kapcsoló BE — a legutóbb használt
        címkékkel felülírva, majd (ha a gyakori-kitöltés BE) az üresen
        maradt szlotok a leggyakrabban használt, még nem szereplő
        címkékkel feltöltve. Üres szlot = "" (a QML mutatja „?"-ként)."""
        labels = self._quick_tag_raw_labels()
        if self.quickTagsReserveRecent:
            recent = self._quick_tag_recent()
            for i in range(_QUICK_TAG_RESERVED):
                labels[i] = recent[i] if i < len(recent) else ""
        if self.quickTagsAutoFillFrequent and "" in labels:
            used = {label.casefold() for label in labels if label}
            for candidate in self._frequent_keywords():
                if "" not in labels:
                    break
                folded = candidate.casefold()
                if folded in used:
                    continue
                labels[labels.index("")] = candidate
                used.add(folded)
        return labels
