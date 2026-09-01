"""#1759 — a három rendezés HÁROM külön dolog, és a leírásuk se mossa össze.

## Miért ér tesztet egy docstring

A #1595 kutatása **téves következtetést vont le** a `setFolderSort`
docstringjéből („a RÁCS rendezése”): úgy tűnt, hogy a menüsáv és a mappa
helyi menüje ugyanazt csinálja kétféle felirattal, és a jegy a menüsáv
ötös készletének lecserélését javasolta a helyi menü négyesére. Az
összevonás egy működő szempontot („legutóbbi változtatások”) vett volna
el. A megvalósító kör csak azért nem hajtotta végre, mert a QML-komment
ellentmondott a docstringnek.

## ⚠️ A jegy állítása is pontatlan volt — MÉRVE

A jegy szerint a `setFolderSort` „a **mappákat** rendezi **a bal
hasábon**”. Ez sem igaz: a bal hasáb sorrendjét a `paneSort` adja
(`_reload_folders`). A `folderSort` a **rácson** dönti el, milyen
sorrendben követik egymást a mappa-blokkok (`_feed_records` →
`folder_order`).

Vagyis a régi leírás és a jegy javaslata **két különböző irányba**
tévedett ugyanabból a pontból.
"""

from __future__ import annotations

import inspect

from picasapy.app.controller import AppController


def _doc(nev: str) -> str:
    return " ".join((getattr(AppController, nev).__doc__ or "").split())


class TestAHaromRendezesKulon:
    def test_a_folderSort_a_RACS_mappa_blokkjait_rendezi(self):
        szoveg = _doc("setFolderSort")
        assert "MAPPA-BLOKKOK" in szoveg, (
            "a docstring nem mondja meg, MIT rendez ez a beállítás"
        )

    def test_a_docstring_megnevezi_MINDHAROM_rendezest(self):
        """Az összemosás ellen: aki ezt olvassa, lássa a másik kettőt is."""
        szoveg = _doc("setFolderSort")
        for tars in ("folderPhotoSort", "paneSort"):
            assert tars in szoveg, f"nincs megnevezve a párja: {tars}"

    def test_a_regi_felrevezeto_mondat_ELTUNT(self):
        szoveg = _doc("setFolderSort")
        assert "A RÁCS rendezése (Mappa" not in szoveg


class TestAMertUtvonal:
    def test_a_folderSort_a_feed_mappa_sorrendjet_adja(self):
        """A mérés, amire a docstring épül — ha a kód elmozdul, ez bukik,
        és a leírás nem marad némán hamis."""
        forras = inspect.getsource(AppController._feed_records)
        assert "folder_order(conn, self.folderSort" in forras, (
            "a `folderSort` már nem a rács mappa-sorrendjét adja — a "
            "docstringet újra kell mérni (#1759)"
        )

    def test_a_bal_hasab_a_paneSort_ot_hasznalja(self):
        forras = inspect.getsource(AppController._reload_folders)
        assert "self.paneSort" in forras, (
            "a bal hasáb már nem a `paneSort`-ot használja — a #1759 "
            "megkülönböztetése újramérendő"
        )
        assert "self.folderSort" not in forras, (
            "a bal hasáb a `folderSort`-ot olvassa — akkor a jegy "
            "állítása lenne igaz, és a docstring rossz"
        )
