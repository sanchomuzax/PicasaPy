"""#2984 — a borító-lekérdezés VALÓDI indexből, valódi rekordokkal.

A hiba: az `application.py` lezárása `rekord.path`-t olvasott, a
`PhotoRecord`-nak viszont `folder_path` + `name` mezője van. MINDEN
mappán `AttributeError` keletkezett, amit a szolgáltató „nincs
borító"-vá nyelt — a bal hasáb bekapcsolt „Indexképek megjelenítése a
könyvtárban" mellett is mappaikont mutatott. A tulajdonos **többször**
jelezte; a #2215 javítása a visszaesést rendbe tette, de a lekérdezést
nem érintette.

⛔ **Miért csúszott át zölden:** a #2049 és a #2215 őre egyaránt
`lambda`-val adta be a fájllistát, tehát a VALÓDI lekérdezés sosem
futott le tesztben. Ezért került a lezárás modul-szintre
(`folder_cover_provider.borito_fajljai`), és ezért mér ez a fájl
indexből — nem kitalált rekordokból.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.folder_cover_provider import (
    BORITO_FOTOK_MAXIMUMA,
    FolderCoverProvider,
    borito_fajljai,
)
from picasapy.index import open_index, photos_in_folder, sync_tree
from support.jpeg_factory import make_jpeg


@pytest.fixture
def indexelt(tmp_path: Path):
    """Öt valódi JPEG egy mappában, valódi indexszel."""
    mappa = tmp_path / "kepek" / "nyar"
    mappa.mkdir(parents=True)
    for i in range(5):
        make_jpeg(mappa / f"k{i}.jpg", size=(120, 90))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, tmp_path / "kepek")
    return db, mappa


class TestARekordbolLESZUtvonal:
    """A `PhotoRecord`-nak nincs `path` mezője — ezt a teszt kimondja."""

    def test_a_PhotoRecord_nem_ismeri_a_path_mezot(self, indexelt):
        db, mappa = indexelt
        with open_index(db) as conn:
            rekord = photos_in_folder(conn, str(mappa))[0]
        assert not hasattr(rekord, "path"), (
            "ha a `PhotoRecord` kap `path` mezőt, ez az őr elavul — "
            "de a #2984 hibája épp az volt, hogy NINCS ilyen mező"
        )
        assert rekord.folder_path and rekord.name

    def test_a_lekerdezes_LETEZO_fajlokat_ad(self, indexelt):
        db, mappa = indexelt
        utvonalak = borito_fajljai(db, str(mappa))
        assert utvonalak, "a lekérdezés üres listát adott egy öt fotós mappára"
        for ut in utvonalak:
            assert ut.is_file(), f"a lekérdezés nem létező útvonalat adott: {ut}"

    def test_legfeljebb_negy_fajl_es_NEVSORBAN(self, indexelt):
        db, mappa = indexelt
        utvonalak = borito_fajljai(db, str(mappa))
        assert len(utvonalak) == BORITO_FOTOK_MAXIMUMA
        assert [u.name for u in utvonalak] == ["k0.jpg", "k1.jpg", "k2.jpg", "k3.jpg"]

    def test_ismeretlen_mappara_ures_lista(self, indexelt, tmp_path):
        db, _mappa = indexelt
        assert borito_fajljai(db, str(tmp_path / "nincs-ilyen")) == []


class TestAFELULETENIsMEGJELENIK:
    """A teljes lánc: index → lekérdezés → szolgáltató → nem-null kép."""

    def test_a_szolgaltato_VALODI_kepet_ad_indexelt_mappara(
        self, qt_app, indexelt
    ):
        db, mappa = indexelt
        szolgaltato = FolderCoverProvider(lambda m: borito_fajljai(db, m))
        kep = szolgaltato.requestImage(str(mappa), None, None)
        assert not kep.isNull(), (
            "a szolgáltató NULL képet adott egy öt fotós, indexelt mappára — "
            "a QML ilyenkor a mappaikonra esik vissza, és a felhasználó "
            "bekapcsolt kapcsolóval sem lát kupacot (#2984)"
        )
        assert kep.width() > 1 and kep.height() > 1

    def test_MAGVETES_ha_a_lekerdezes_hibas_a_kep_NULL_lesz(
        self, qt_app, indexelt
    ):
        """A #2984 hibájának pontos utánzata — ennek BUKNIA kell tudni.

        Ha a lekérdezés a nem létező `path` mezőt olvassa, a szolgáltató
        néma null képet ad. Ez a próba rögzíti, hogy a fenti sikeres eset
        tényleg a lekérdezésen múlik, nem véletlenül zöld.
        """
        db, mappa = indexelt

        def hibas(m):
            with open_index(db) as conn:
                return [Path(r.path) for r in photos_in_folder(conn, m)[:4]]

        szolgaltato = FolderCoverProvider(hibas)
        assert szolgaltato.requestImage(str(mappa), None, None).isNull()
