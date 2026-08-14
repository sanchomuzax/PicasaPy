"""A gyűjtemény BEZÁRÁSA (#461) — a tiszta réteg tesztjei.

Az eredeti Picasában a gyűjtemény nem csak összecsukható, hanem **bezárható**
is, és ez két különböző dolog: az összecsukás csak a fát hajtja össze, a
bezárás viszont a gyűjtemény képeit **kiveszi a rácsból** is. Az eredeti
figyelmeztetése mondja ki: „Az indexképek területén egyetlen kép sem lesz
látható."

Ez a modul a tiszta függvényeket fedi le (a QSettings-I/O és a nézet-szűrés a
hívóé). Külön figyelem a VISSZAFELÉ KOMPATIBILITÁSRA: a már mentett
gyűjtemény-listákban nincs `closed` mező, azokat nyitottnak kell olvasni.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.custom_collections import (
    CustomCollection,
    closed_collection_folders,
    move_folder_to_collection,
    parse_custom_collections,
    rename_collection,
    serialize_custom_collections,
    set_collection_closed,
)


class TestBackCompat:
    def test_a_regi_mentes_nyitottnak_olvasodik(self) -> None:
        """A `closed` mező nélküli (korábbi verzióval mentett) bejegyzés
        nyitott — a frissítés nem tüntetheti el a felhasználó képeit."""
        regi = '[{"name": "Archívum", "folders": ["/data/2019"]}]'

        collections = parse_custom_collections(regi)

        assert collections == (
            CustomCollection(name="Archívum", folders=("/data/2019",)),
        )
        assert collections[0].closed is False

    def test_a_serialize_parse_korbejar(self) -> None:
        eredeti = (
            CustomCollection(name="Nyitott", folders=("/a",)),
            CustomCollection(name="Zárt", folders=("/b", "/c"), closed=True),
        )

        assert parse_custom_collections(
            serialize_custom_collections(eredeti)
        ) == eredeti

    def test_a_hibas_closed_ertek_nyitottnak_szamit(self) -> None:
        """Sérült beállítás-fájl nem rejtheti el némán a képeket."""
        nyers = '[{"name": "A", "folders": [], "closed": "igen"}]'

        assert parse_custom_collections(nyers)[0].closed is False


class TestSetCollectionClosed:
    def test_bezaras_es_nyitas(self) -> None:
        collections = (CustomCollection(name="A", folders=("/a",)),)

        zart = set_collection_closed(collections, "A", True)
        assert zart[0].closed is True

        ujra = set_collection_closed(zart, "A", False)
        assert ujra[0].closed is False

    def test_a_tagmappak_megmaradnak(self) -> None:
        """A bezárás NEM törlés: a mappák a gyűjteményben maradnak."""
        collections = (CustomCollection(name="A", folders=("/a", "/b")),)

        assert set_collection_closed(collections, "A", True)[0].folders == (
            "/a",
            "/b",
        )

    def test_ismeretlen_nevre_nincs_teendo(self) -> None:
        collections = (CustomCollection(name="A"),)

        assert set_collection_closed(collections, "Nincs ilyen", True) == collections

    def test_a_tobbit_nem_bantja(self) -> None:
        collections = (
            CustomCollection(name="A"),
            CustomCollection(name="B", closed=True),
        )

        eredmeny = set_collection_closed(collections, "A", True)

        assert eredmeny[1] == collections[1]


class TestClosedCollectionFolders:
    def test_csak_a_zartak_mappai(self) -> None:
        collections = (
            CustomCollection(name="Nyitott", folders=("/nyitott",)),
            CustomCollection(name="Zárt", folders=("/zart1", "/zart2"), closed=True),
        )

        assert closed_collection_folders(collections) == frozenset(
            {"/zart1", "/zart2"}
        )

    def test_ures_ha_semmi_sincs_zarva(self) -> None:
        collections = (CustomCollection(name="A", folders=("/a",)),)

        assert closed_collection_folders(collections) == frozenset()


class TestAZartAllapotTuleliAMasMuveleteket:
    """A `closed` mezőt a többi művelet sem veszítheti el — a `CustomCollection`
    újraépítésekor könnyű kifelejteni."""

    def test_atnevezes_megorzi(self) -> None:
        collections = (
            CustomCollection(name="Régi", folders=("/a",), closed=True),
        )

        uj = rename_collection(collections, "Régi", "Új")

        assert uj[0].name == "Új"
        assert uj[0].closed is True
        assert uj[0].folders == ("/a",)

    def test_mappa_athelyezes_megorzi(self) -> None:
        collections = (
            CustomCollection(name="Forrás", folders=("/a",), closed=True),
            CustomCollection(name="Cél", folders=(), closed=True),
        )

        uj = move_folder_to_collection(collections, "/a", "Cél")

        assert [c.closed for c in uj] == [True, True]
        assert uj[0].folders == ()
        assert uj[1].folders == ("/a",)


# --- a controller-szelet: bezárás, nézetfrissítés, figyelmeztetés ---------
#
# A mixin ÖNÁLLÓAN, minimális host-osztályon tesztelt — a
# `test_custom_collections_controller_320.py` mintája szerint.


class _Rekord:
    """A PhotoRecord-ból csak az kell, amit a szűrés néz."""

    def __init__(self, folder_path: str) -> None:
        self.folder_path = folder_path


class _Modell:
    def __init__(self, records=()) -> None:
        self.photos = tuple(records)


@pytest.fixture
def host(tmp_path):
    from picasapy.app.custom_collections_controller import CustomCollectionsMixin

    class _Host(CustomCollectionsMixin, QObject):
        def __init__(self, settings):
            super().__init__()
            self._settings = settings
            self._photos = _Modell()
            self.refresh_count = 0

        def _get_settings(self):
            return self._settings

        def _refresh_view(self) -> None:
            self.refresh_count += 1

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return _Host(settings)


class TestSetCollectionClosedSlot:
    def test_bezaras_megjelenik_a_listaban(self, host) -> None:
        host.createCollection("Archívum")
        host.moveFolderToCollection("/data/2019", "Archívum")

        host.setCollectionClosed("Archívum", True)

        assert host.customCollections == [
            {"name": "Archívum", "folders": ["/data/2019"], "closed": True}
        ]

    def test_frissiti_a_nezetet(self, host) -> None:
        """A bezárás azonnal látszódjon — enélkül a rács a régi tartalmat
        mutatná a következő mappaváltásig."""
        host.createCollection("A")
        elotte = host.refresh_count

        host.setCollectionClosed("A", True)

        assert host.refresh_count == elotte + 1

    def test_a_bezart_mappai_a_szurolistaban_vannak(self, host) -> None:
        host.createCollection("Zárt")
        host.moveFolderToCollection("/zart", "Zárt")
        host.createCollection("Nyitott")
        host.moveFolderToCollection("/nyitott", "Nyitott")

        host.setCollectionClosed("Zárt", True)

        assert host._closed_collection_folders() == frozenset({"/zart"})


class TestClosingHidesEverything:
    """#461: az eredeti figyelmeztetése — „az indexképek területén egyetlen
    kép sem lesz látható"."""

    def _keszit(self, host, mappak_a_gyujtemenyben, latszo_mappak):
        host.createCollection("A")
        for mappa in mappak_a_gyujtemenyben:
            host.moveFolderToCollection(mappa, "A")
        host._photos = _Modell([_Rekord(m) for m in latszo_mappak])

    def test_igaz_ha_minden_eltunne(self, host) -> None:
        self._keszit(host, ["/a"], ["/a", "/a"])

        assert host.closingHidesEverything("A") is True

    def test_hamis_ha_marad_kep(self, host) -> None:
        self._keszit(host, ["/a"], ["/a", "/mas"])

        assert host.closingHidesEverything("A") is False

    def test_hamis_ures_racsnal(self, host) -> None:
        """Üres rácsnál nincs mit elrejteni — ne kérdezzünk feleslegesen."""
        self._keszit(host, ["/a"], [])

        assert host.closingHidesEverything("A") is False

    def test_hamis_ha_mar_zart(self, host) -> None:
        self._keszit(host, ["/a"], ["/a"])
        host.setCollectionClosed("A", True)

        assert host.closingHidesEverything("A") is False

    def test_hamis_ismeretlen_nevre(self, host) -> None:
        assert host.closingHidesEverything("Nincs ilyen") is False
