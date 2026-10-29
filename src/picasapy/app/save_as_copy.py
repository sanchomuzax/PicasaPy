"""„Másolat mentése" és „Mentés másként…": a szerkesztések beégetése ÚJ fájlba
(#1527, #1566, #1648)."""


from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QUrl, Signal, Slot

from picasapy.edit.save_copy import FileNameCollisionError, next_copy_path, save_copy
from picasapy.edit.session import EditSession

from .save_error_kind import save_error_kind
from .save_errors import _SAVE_ERRORS
from .save_render import _render_for_save


class SaveCopyMixin:
    """A másolat-mentés parancsai és jelzései."""

    # ── #1527 ─────────────────────────────────────────────────────────
    #: „Másolat mentése" / „Mentés másként…" vége: (sikeres, sikertelen)
    saveCopyFinished = Signal(int, int)

    # ── #1566 ─────────────────────────────────────────────────────────
    #: A másolat-mentés FELÜLETI visszajelzése: (hány sikerült, az utolsó
    #: célfájl útja). A lebegő értesítősáv (#1129) fogadja.
    #:
    #: Miért KÜLÖN jelzés, és nem a `saveCopyFinished` bővítése:
    #:
    #: 1. A `saveCopyFinished(int, int)` szignatúráját két beolvadt jegy
    #:    kötései és tesztjei rögzítik (#1527 menüpont-tesztjei, #1539
    #:    újraolvasás-kötése) - a bővítése azokat törné.
    #: 2. A sávnak a darabszámon felül a CÉLÚTVONAL is kell, különben a
    #:    cella kattintása néma no-op: a `NotifierCell` a hasznos adat
    #:    MAPPÁJÁRA navigál. Épp ez a jegy tétje - a „Mentés másként…"
    #:    bárhova írhat, és ott a fájlnak a rácsban sem marad nyoma.
    #:
    #: Ugyanaz az alak, mint a kollázsnál: a gépies befejezés-jelzés és a
    #: felhasználónak szóló, ÚTVONALAT vivő jelzés
    #: (`collageDesktopBackgroundReady`) ott is két külön jelzés.
    saveCopyReady = Signal(int, str)

    # ── #1527: „Másolat mentése" és „Mentés másként…" ────────────────
    #
    # A két parancs a MÉRÉS szerint ugyanaz a művelet, egyetlen
    # kapcsolóval (a bináris `0x005e6a20` bájt-paramétere) - ld.
    # `picasapy.edit.save_copy` modul-docstringjét. Nálunk ez a kapcsoló
    # az, hogy a hívó ad-e célútvonalat:
    #
    #   * `saveCopyRows(rows)`  - nem ad ⇒ a mért `-001` minta,
    #     kérdés nélkül, TÖBB képre is (a menüpont felirata ellipszis
    #     nélküli: `Save a Cop&y`).
    #   * `saveRowAs(row, url)` - ad ⇒ a fájlválasztóból jött út, EGY
    #     képre (`Save &As...`, ellipszissel).

    @Slot(int, result=str)
    def suggestedCopyUrl(self, row) -> str:  # noqa: N802 - QML-stílus
        """A „Mentés másként…" fájlválasztójának alapértelmezett célja.

        A mért `-001` mintát ajánljuk fel: a felhasználó átírhatja, de a
        felkínált név sosem a forrásé - az eredeti is elutasítaná
        (`IDS_CANT_SAVE_TO_SAME`)."""
        records = self._selected_records([row])
        if not records:
            return ""
        record = records[0]
        return QUrl.fromLocalFile(
            str(next_copy_path(Path(record.folder_path) / record.name))
        ).toString()

    @Slot(list)
    def saveCopyRows(self, rows) -> None:  # noqa: N802 - QML-stílus
        """„Másolat mentése": a szerkesztések beégetve ÚJ fájlba.

        A forrás - se a képe, se az ini-bejegyzése - nem változik."""
        self._save_copies(self._selected_records(rows), target=None)

    @Slot(int, str)
    def saveRowAs(self, row, target_url: str) -> None:  # noqa: N802 - QML-stílus
        """„Mentés másként…": a felhasználó választotta célútvonalra."""
        cel = QUrl(target_url).toLocalFile() if target_url else ""
        if not cel:
            # A fájlválasztó megszakítása NEM hiba - de a hívó (és a
            # teszt) a befejezés-jelzésre vár, némán nem térhetünk vissza.
            self.saveCopyFinished.emit(0, 0)
            return
        self._save_copies(self._selected_records([row]), target=Path(cel))

    def _save_copies(self, records, *, target: Path | None) -> None:
        """A másolat-mentés közös háttérszálas útja."""
        items = [
            (Path(r.folder_path) / r.name, int(r.rotate_steps or 0),
             r.filters or "", int(getattr(r, "flip_flags", 0) or 0),
             self._festes_vonasai(Path(r.folder_path) / r.name))
            for r in records
        ]
        if not items:
            self.saveCopyFinished.emit(0, 0)
            return
        self._ensure_save_progress()
        self._saveProgressTick.emit(0, len(items), 1)

        def worker():
            done, failed = 0, 0
            # #1566: az UTOLSÓ ténylegesen kiírt célfájl - ez lesz az
            # értesítés kattintási célja. Több képnél a mappájuk közös (a
            # `-001` minta a forrás mellé ír), a „Mentés másként…" pedig
            # eleve EGY képre hat, tehát az utolsó út mindig jó mappára
            # mutat.
            utolso_cel = ""
            jelentett_agak: set[str] = set()
            # #1648: (másolat útja, a FORRÁS származás-kulcsa) párok. Egyben
            # megy be az indexbe a ciklus UTÁN - képenként külön kapcsolatot
            # nyitni fölösleges lemezmunka lenne.
            orokolt_kulcsok: list[tuple[str, int]] = []
            for index, (path, rotate_steps, filters, flip, vonasok) in enumerate(items):
                try:
                    rendered = _render_for_save(
                        path, rotate_steps, filters, flip, paint_strokes=vonasok
                    )
                    eredmeny = save_copy(
                        path,
                        rendered,
                        EditSession.from_value(filters),
                        target_path=target,
                    )
                except (*_SAVE_ERRORS, FileNameCollisionError) as error:
                    failed += 1
                    ag = save_error_kind(error)
                    if ag not in jelentett_agak:
                        jelentett_agak.add(ag)
                        self._report_save_error(error, target or path)
                else:
                    done += 1
                    utolso_cel = str(eredmeny.target_path)
                    if eredmeny.inherited_origin_key is not None:
                        orokolt_kulcsok.append(
                            (utolso_cel, eredmeny.inherited_origin_key)
                        )
                    # #1539: a TÉNYLEGES célút megy be, nem a látott mappa
                    self.noteOutputWritten(utolso_cel)
                self._saveProgressTick.emit(index + 1, len(items), 1)
            self._saveProgressTick.emit(len(items), len(items), 0)
            self._orokit_szarmazas_kulcsokat(orokolt_kulcsok)
            # #1566: a FELÜLETI visszajelzés ELŐBB megy ki, mint a gépies
            # befejezés-jelzés. Mindkettő a GUI-szálra sorolódik, sorrendben
            # - így a `saveCopyFinished`-re váró hívó (és teszt) számára az
            # értesítés már kézbesítve van, nem versenyeznek.
            self.saveCopyReady.emit(done, utolso_cel)
            self.saveCopyFinished.emit(done, failed)

        self._start_background(worker, name="picasapy-save-copy")

    def _orokit_szarmazas_kulcsokat(
        self, parok: list[tuple[str, int]]
    ) -> None:
        """#1648: a másolatok a FORRÁS `originfast` kulcsát öröklik.

        A mező **származást** azonosít, nem tartalmat: a valódi Picasa a
        „Másolat mentése" kimenetének a forrás értékét adja, akkor is, ha a
        szerkesztés bele van égetve (mérve a tulajdonos élő adatbázisán,
        `docs/specs/picasa-tartalomkulcs.md`). A tárolás az indexé.

        Hiba esetén CSAK naplózunk: az öröklés kényelmi nyilvántartás, a
        felhasználó fájljai már a lemezen vannak, és a mentés sikere nem
        múlhat az indexen. A hívó a háttérszálon van, ahol egy kiszökő
        kivétel a szálat vinné el.
        """
        if not parok:
            return
        from picasapy.index import open_index
        from picasapy.index.origin import inherit_origin_key

        try:
            with open_index(self._db_path) as conn:
                for ut, kulcs in parok:
                    inherit_origin_key(conn, ut, kulcs)
        except Exception:  # noqa: BLE001 - ld. a docstringet
            logging.getLogger(__name__).exception(
                "A másolatok származás-kulcsának öröklése nem sikerült (%d db)",
                len(parok),
            )

