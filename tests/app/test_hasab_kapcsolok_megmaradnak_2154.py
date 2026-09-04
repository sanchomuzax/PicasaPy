"""#2154 — a bal hasáb három nézet-kapcsolója maradjon meg újraindításig.

Az eredetiben mindhárom tartós felhasználói beállítás (`Preferences`):
`SimplifiedHierarchy`, `ShowAlbumThumbnails2` és a nézetmód. Nálunk
egyikük sem élte túl az újraindítást — a `folder_hierarchy_controller`
egyáltalán nem nyúlt a `QSettings`-hez.

⚠️ Az őr ÚJ vezérlő-példányt épít ugyanazzal a beállítás-objektummal:
ez az újraindítás gépi megfelelője. Ha csak a property-t olvasnánk vissza
ugyanazon a példányon, a próba a memóriabeli mezőt mérné, nem a mentést.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.folder_hierarchy_controller import FolderHierarchyController


@pytest.fixture
def beallitasok(tmp_path, qt_app):
    """Saját, eldobható beállítás-fájl — a felhasználóé érintetlen marad."""
    settings = QSettings(str(tmp_path / "proba.ini"), QSettings.Format.IniFormat)
    yield settings
    settings.clear()


#: (kapcsoló-property, átbillentő hívás) — a három nézet-kapcsoló.
#: A `treeView`-nak nincs `toggle`-ja: a `Nézet ▸ Mappanézet` két
#: RÁDIÓTÉTELE (#1454) hívja a `setTreeView(bool)`-t, ezért itt is így
#: billentjük.
def _billents(ctl, prop):
    if prop == "treeView":
        ctl.setTreeView(not ctl.treeView)
    elif prop == "simplified":
        ctl.toggleSimplified()
    else:
        ctl.toggleAlbumThumbs()


KAPCSOLOK = ["treeView", "simplified", "albumThumbs"]


class TestAKapcsoloTuleliAzUjrainditast:
    @pytest.mark.parametrize("prop", KAPCSOLOK)
    def test_a_billentett_ertek_uj_peldanyban_is_megvan(self, beallitasok, prop):
        elso = FolderHierarchyController(settings=beallitasok)
        eredeti = elso.property(prop)
        _billents(elso, prop)
        billentett = elso.property(prop)
        assert billentett != eredeti, f"a {prop} nem billent át"

        # „újraindítás”: új példány, ugyanaz a beállítás-fájl
        masodik = FolderHierarchyController(settings=beallitasok)
        assert masodik.property(prop) == billentett, (
            f"a {prop} nem élte túl az újraindítást"
        )

    @pytest.mark.parametrize("prop", KAPCSOLOK)
    def test_a_ketszer_billentes_visszaall(self, beallitasok, prop):
        elso = FolderHierarchyController(settings=beallitasok)
        eredeti = elso.property(prop)
        _billents(elso, prop)
        _billents(elso, prop)
        masodik = FolderHierarchyController(settings=beallitasok)
        assert masodik.property(prop) == eredeti


class TestAzAlapertekekAzEredetitKovetik:
    def test_az_indexkepek_KIKAPCSOLVA_indulnak(self, beallitasok):
        """`ShowAlbumThumbnails2` alapértéke 0 (`0x00761870`, mérve)."""
        ctl = FolderHierarchyController(settings=beallitasok)
        assert ctl.albumThumbs is False

    @pytest.mark.parametrize("prop", ["treeView", "simplified"])
    def test_a_masik_ketto_is_kikapcsolva_indul(self, beallitasok, prop):
        ctl = FolderHierarchyController(settings=beallitasok)
        assert ctl.property(prop) is False


class TestAKapcsolokNemZavarjakEgymast:
    """Három külön kulcs — az egyik billentése ne mozdítsa a másikat."""

    def test_az_egyik_billentese_a_masikat_nem_mozditja(self, beallitasok):
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.toggleAlbumThumbs()
        masodik = FolderHierarchyController(settings=beallitasok)
        assert masodik.albumThumbs is True
        assert masodik.treeView is False
        assert masodik.simplified is False


class TestABeallitasNelkuliHasznalatValtozatlan:
    """⚠️ A vezérlőt ma paraméter nélkül hozza létre az `application.py`."""

    def test_settings_nelkul_is_felepul(self, qt_app):
        ctl = FolderHierarchyController()
        assert ctl.treeView is False
        assert ctl.albumThumbs is False
