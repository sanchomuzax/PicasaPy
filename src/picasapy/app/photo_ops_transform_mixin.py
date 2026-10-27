"""A forgatás, tükrözés és kötegelt láthatóság témamixinje."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.ini import with_backuphash
from picasapy.render.flip import (
    FLIP_MASK,
    FLIP_HORIZONTAL,
    FLIP_VERTICAL,
    toggled_flip,
)
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_compat import update_document


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


class PhotoOpsTransformMixin:
    rotationTypeFailed = Signal(int)
    rotationNeedsSelection = Signal()

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
            return with_backuphash(
                forgatas_mutacio(document, photo.name, steps), photo.name
            )

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
        round-tripet.

        #3830: az írás háttérszálon fut (`_run_photo_write`), a modell
        (`self._photos`) pedig csak a befejezéskor frissül. Egy GYORS
        második forgatás — mielőtt az első írás jelezne — a RÉGI
        `photo.rotate_steps`-ből számolna, és elveszne (lassú, NAS-ra vagy
        vírusirtó mögé írásnál ez nem elméleti). Ezért a
        célértéket (`_rotate_target`) magunk tartjuk nyilván a fotó
        `id`-jére kulcsolva: a futó írásra érkező újabb kérés csak ezt
        frissíti, és a befejezés után (`after`) azonnal indul a következő
        írás a LEGFRISSEBB célértékkel — egyetlen kattintás sem vész el,
        és nem is indul kattintásonként külön szál."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        if photo.kind == "video":
            return  # #103: videóra nem írunk rotate= kulcsot (QML-őr mellett)
        self._ensure_photo_ops_wired()
        base = self._rotate_target.get(photo.id, photo.rotate_steps)
        self._rotate_target[photo.id] = (base + delta) % 4
        if photo.id in self._rotate_running:
            return  # a futó írás `after`-je a friss célértékkel folytatja
        self._start_rotate_write(photo)

    def _start_rotate_write(self, photo) -> None:
        """`_apply_rotate` egy írás-lépése — a legfrissebb célértékkel."""
        steps = self._rotate_target[photo.id]
        self._rotate_running.add(photo.id)

        def perform() -> dict:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME

            def mutate(document):
                return with_backuphash(
                    forgatas_mutacio(document, photo.name, steps), photo.name
                )

            update_document(ini_path, mutate, backup=True)
            return {"rotate_steps": steps}

        photo_id = photo.id

        def after() -> bool:
            self._rotate_running.discard(photo_id)
            cel = self._rotate_target.get(photo_id)
            if cel is None or cel == steps:
                self._rotate_target.pop(photo_id, None)
                return False
            # #3830: közben újabb forgatás érkezett — a FRISS rekorddal
            # folytatjuk (a kép közben átnevezés/áthelyezés miatt
            # megváltozhatott); ha kikerült a nézetből, a célérték elvész.
            friss = next(
                (p for p in self._photos.photos if p.id == photo_id), None
            )
            if friss is None:
                self._rotate_target.pop(photo_id, None)
                return False
            self._start_rotate_write(friss)
            return True

        def on_error() -> None:
            # #3830: a modellbeli (lemezre ténylegesen kiírt) érték marad az
            # igazság — a függő célérték elvész, a kép újra forgatható
            self._rotate_running.discard(photo_id)
            self._rotate_target.pop(photo_id, None)

        self._run_photo_write(photo_id, perform, after=after, on_error=on_error)
