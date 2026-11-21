"""#7341 - a három rendezés HÁROM külön dolog, és a leírásuk se mossa össze.

## Miért ér tesztet egy docstring

Az eredeti Mappa-menü négy tétele a mappa képeit rendezi egyszer, ugyanazzal
a `sortFolderBy` művelettel, amelyet a mappasor helyi menüje használ.
`paneSort` rendezi a bal hasábot és a rács mappa-blokkjait. A korábbi
`folderSort` értékek megmaradnak, a védett „Recent &changes” pedig továbbra
is saját `changed` módban rendezi a rácsot.
"""

from __future__ import annotations

import inspect

from picasapy.app.controller import AppController


def _doc(nev: str) -> str:
    return " ".join((getattr(AppController, nev).__doc__ or "").split())


class TestAHaromRendezesKulon:
    def test_a_folderSort_a_sajat_recent_changes_modot_orzi(self):
        szoveg = _doc("setFolderSort")
        assert "Recent &changes" in szoveg
        assert "changed" in szoveg

    def test_a_docstring_megnevezi_MINDHAROM_rendezest(self):
        """Az összemosás ellen: aki ezt olvassa, lássa a másik kettőt is."""
        szoveg = _doc("setFolderSort")
        for tars in ("kézi sorrend", "paneSort"):
            assert tars in szoveg, f"nincs megnevezve a párja: {tars}"

    def test_a_regi_felrevezeto_mondat_ELTUNT(self):
        szoveg = _doc("setFolderSort")
        assert "A RÁCS rendezése (Mappa" not in szoveg


class TestAMertUtvonal:
    def test_a_feed_a_paneSortot_hasznalja_a_changed_kivetellel(self):
        forras = inspect.getsource(AppController._feed_records)
        assert 'folder_sort == "changed"' in forras
        assert "(pane_sort, pane_sort_reverse)" in forras

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

    def test_a_paneSort_valtozasa_a_racsot_is_frissiti(self):
        forras = inspect.getsource(AppController.setPaneSort)
        assert "self._refresh_view()" in forras
