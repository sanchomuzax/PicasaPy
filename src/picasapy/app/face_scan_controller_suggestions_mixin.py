"""Személyjavaslatok lekérdezése és kezelése."""

from __future__ import annotations

from .face_scan_controller_shared import (
    Path,
    Slot,
    _log,
    javaslatokat_ujraszamol,
    lazitott_lepcso,
    open_index,
    set_suggested_name,
    step_to_threshold,
    suggested_faces_for,
)


class FaceScanControllerSuggestionsMixin:
    """Személyjavaslatok lekérdezése és kezelése."""


    @Slot(int, result=bool)
    def acceptSuggestion(self, face_id: int) -> bool:  # noqa: N802
        """A név-javaslat ELFOGADÁSA (pipa): a javasolt nevet ténylegesen
        ráírjuk az arcra — ugyanazon az úton, mint a kézi névadás."""
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT suggested_name FROM face WHERE id = ?", (int(face_id),)
            ).fetchone()
            name = row["suggested_name"] if row is not None else None
        if not name:
            return False
        accepted = self.assignNameToFaces([int(face_id)], name)
        if accepted:
            self.faceSuggestionsChanged.emit()
        return accepted


    @Slot(int, result=bool)
    def rejectSuggestion(self, face_id: int) -> bool:  # noqa: N802
        """Egyetlen arc név-javaslatának elvetése, az arc mellőzése nélkül."""
        azonosito = int(face_id)
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT suggested_name FROM face WHERE id = ?", (azonosito,)
            ).fetchone()
            if row is None or not row["suggested_name"]:
                return False
            set_suggested_name(conn, azonosito, None)
            conn.commit()
        self.unnamedCountChanged.emit()
        self.faceSuggestionsChanged.emit()
        return True


    @Slot(str, result=int)
    def personSuggestionCount(self, name: str) -> int:  # noqa: N802
        """Hány MÉG EL NEM DÖNTÖTT javaslat tartozik ehhez a személyhez
        (#2187) — ebből lesz a személy-album fejlécének darabszáma.

        Üres névre nulla: a fejléc kötése akkor is hívja, amikor nem
        személy-album van nyitva."""
        if not name:
            return 0
        with open_index(self._db_path) as conn:
            return len(suggested_faces_for(conn, name))


    @Slot(str, result="QVariantList")
    def personSuggestionPaths(self, name: str) -> list[str]:  # noqa: N802
        """A személy függő javaslatait tartalmazó fotók útvonala (#4588).

        A fejléc egy fotósor-kijelölésen keresztül éri el a javaslatokat;
        ugyanazon a fotón több egyező arc is lehet, ezért az útvonalak
        egyediek. Az üres név nem tartozik személy-albumhoz.
        """
        if not name:
            return []
        with open_index(self._db_path) as conn:
            return list(dict.fromkeys(
                str(arc.photo_path) for arc in suggested_faces_for(conn, name)
            ))


    def _szemely_javaslatai(
        self, name: str, face_ids: list | None
    ) -> list[int]:
        """A művelet HATÓKÖRE: a személy függő javaslatai, opcionálisan a
        megadott arcokra szűkítve (#2187).

        A mérés szerint a `confirmsug` és a `confirmsel` UGYANAZ a kezelő
        (`0x00602640`), egyetlen logikai argumentummal — nálunk ezért egy
        művelet van, és ez a metódus dönti el a hatókört. A szűkítés
        MINDIG a személy javaslatain belül marad: idegen arc azonosítója
        nem hat, akkor sem, ha a hívó odaadja."""
        if not name:
            return []
        with open_index(self._db_path) as conn:
            sajat = [arc.id for arc in suggested_faces_for(conn, name)]
        if face_ids is None:
            return sajat
        kert = {int(azonosito) for azonosito in face_ids}
        return [azonosito for azonosito in sajat if azonosito in kert]


    @Slot(str, "QVariantList", result="QVariantList")
    def personSuggestionIdsForPaths(  # noqa: N802
        self, name: str, paths: list
    ) -> list[int]:
        """A kijelölt FOTÓKON ülő, e személyre szóló függő javaslatok
        arc-azonosítói — a `confirmsel`/`removesel` hatóköre (#2187).

        A rács sora a fotó, a művelet viszont arcokra hat: egy képen több
        arc is javasolhatja ugyanazt a nevet, és a kijelölés mindegyiküket
        lefedi. Idegen személy javaslata nem kerül bele."""
        if not name or not paths:
            return []
        kijelolt = {Path(ut) for ut in paths if ut}
        with open_index(self._db_path) as conn:
            return [
                arc.id
                for arc in suggested_faces_for(conn, name)
                if Path(arc.photo_path) in kijelolt
            ]


    @Slot(str, result=int)
    @Slot(str, "QVariantList", result=int)
    def confirmPersonSuggestions(  # noqa: N802
        self, name: str, face_ids: list | None = None
    ) -> int:
        """A személy javaslatainak JÓVÁHAGYÁSA — `confirmsug` (mind) és
        `confirmsel` (a kijelöltek) egyetlen műveletként.

        A jóváhagyás a nevet TÉNYLEGESEN ráírja az arcra, ugyanazon az
        úton, mint az egy arcra szóló `acceptSuggestion`. Visszatérési
        érték: hány javaslatot hagytunk jóvá."""
        celok = self._szemely_javaslatai(name, face_ids)
        if not celok:
            return 0
        return len(celok) if self.assignNameToFaces(celok, name) else 0


    @Slot(str, result=int)
    @Slot(str, "QVariantList", result=int)
    def removePersonSuggestions(  # noqa: N802
        self, name: str, face_ids: list | None = None
    ) -> int:
        """A személy javaslatainak ELVETÉSE — `removesel`.

        Az elvetés nem névadás és nem mellőzés: a javaslat eltűnik, az arc
        NÉVTELEN marad, hogy egy későbbi futás újra megvizsgálhassa. (A
        „Névtelenek" album csempéjének „x"-e ezzel szemben a MELLŐZÉS,
        #3670 — `ignoreFaces`.)"""
        celok = self._szemely_javaslatai(name, face_ids)
        if not celok:
            return 0
        with open_index(self._db_path) as conn:
            for azonosito in celok:
                set_suggested_name(conn, azonosito, None)
            conn.commit()
        return len(celok)


    @Slot(result=int)
    def moreSuggestions(self) -> int:  # noqa: N802 — QML-slot-stílus
        """„További javaslatok keresése" — a lépcső TÍZZEL lejjebb (#3237).

        Az eredeti `moresug` a felismerési küszöböt `0,1`-del csökkenti, és a
        beállítást **nem írja vissza**: egy kattintás több javaslatot hoz, de
        a program alapviselkedése változatlan.

        ⚠️ A bináris `0,75`-ös SZÁMÁT nem vesszük át: nálunk a küszöb a
        `step_to_threshold` skáláján él, tehát a **lépcsőt** csökkentjük
        tízzel (`85 → 75`), és abból számolunk küszöböt — a vezérlőt vesszük
        át, nem a számot (#2187).

        Visszatérési érték: hány arcra került ÚJ javaslat.
        """
        if not self.suggestionsEnabled():
            return 0
        lepcso = self._javaslat_lepcso()
        lazitott = lazitott_lepcso(lepcso)
        kuszob = step_to_threshold(lazitott)
        try:
            with open_index(self._db_path) as conn:
                irt = javaslatokat_ujraszamol(conn, kuszob)
                conn.commit()
        except Exception as hiba:  # noqa: BLE001 — a nézet ne fagyjon le
            _log.exception("javaslat-lazítás hiba: %s", self._db_path)
            self.embeddingFailed.emit(str(hiba))
            return 0
        #: ⛔ A beállítást SZÁNDÉKOSAN nem írjuk vissza — ez a lazítás egyszeri.
        if irt:
            self.unnamedCountChanged.emit()
        return irt


    def _javaslat_lepcso(self) -> int:
        """A tárolt javaslat-lépcső (alapértéken a mért `85`)."""
        return self.suggestionThreshold()
