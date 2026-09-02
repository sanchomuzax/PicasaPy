"""A törölt kép sora AZONNAL tűnjön el (#1227).

## Mit ad ma, és mi a baj vele

A törölt kép sorának eltűnése egy **célzott újraszinkronon** múlt:
`photoDeleted` → `refresh` → `resyncFolder` → háttérszál → `syncFinished`
→ nézet-újratöltés. A #1181 azt javította, hogy ez a kérés ne vesszen el,
ha épp fut egy szinkron — de a sor így is csak a szinkron **VÉGÉN** tűnt
el. Nagy könyvtárnál ez másodperc vagy perc.

Az eredetiben a **rács maga végzi a törlést** (`CThumbUI::DeleteProgress`,
`0x00894fb4`), saját folyamatjelzővel.

## ⚠️ A csoporthatárok — a jegy külön kiköti

A rács mappa-csoportjai (`feedGroups`) `start`/`count` párokkal írják le,
melyik sor melyik mappáé. A lasszó, a Shift-tartomány és a nyilas
léptetés mind ezekre épül (#1219). Ha a sor eltűnik, de a csoportok nem
mozdulnak, a határok elcsúsznak — ezért itt **együtt** állítjuk mindkettőt,
és külön eset őrzi, hogy a csoportok is követik.

Szerencsés szerkezet: a csoportokat a `build_feed_groups` a **rekordokból**
számolja, tehát a rekord kivétele után maguktól helyesek — nem kell
kézzel eltolni a `start` értékeket.
"""
from __future__ import annotations

import pytest

from picasapy.app.models import PhotoGridModel
from picasapy.index.queries import PhotoRecord


def _rec(azonosito: int, mappa: str, nev: str) -> PhotoRecord:
    return PhotoRecord(
        id=azonosito, folder_path=mappa, name=nev, kind="image", size=1,
        mtime_ns=1, star=False, caption=None, keywords=(), rotate_steps=0,
        filters=None, taken_at=None, orientation=1, width=100, height=100,
        hidden=False,
    )


@pytest.fixture
def modell() -> PhotoGridModel:
    m = PhotoGridModel()
    m.set_photos(tuple(
        _rec(i, "/a" if i < 3 else "/b", f"k{i}.jpg") for i in range(6)
    ))
    return m


class TestAModellKivesziASort:
    def test_a_torolt_sor_azonnal_eltunik(self, modell):
        assert modell.rowCount() == 6
        assert modell.remove_by_path("/a/k1.jpg") is True
        assert modell.rowCount() == 5
        nevek = [p.name for p in modell.photos]
        assert "k1.jpg" not in nevek

    def test_a_TOBBI_sor_sorrendje_marad(self, modell):
        """A kivétel nem rendezhet át — a rács görgetése és a kijelölés
        sorindexekre épül."""
        elotte = [p.name for p in modell.photos]
        modell.remove_by_path("/a/k1.jpg")
        utana = [p.name for p in modell.photos]
        assert utana == [n for n in elotte if n != "k1.jpg"]

    def test_ismeretlen_ut_eseten_HAMIS_es_nincs_valtozas(self, modell):
        """Nem dobhat: a törlés-jelzés olyan útra is jöhet, ami nincs a
        jelen nézetben (másik mappa, szűrt nézet)."""
        assert modell.remove_by_path("/nincs/ilyen.jpg") is False
        assert modell.rowCount() == 6

    def test_a_revizio_NO(self, modell):
        """A QML-kötések a `revision`-re figyelnek (#142 mintája)."""
        elotte = modell.revision
        modell.remove_by_path("/a/k1.jpg")
        assert modell.revision > elotte

    def test_beginRemoveRows_utat_hasznal_nem_teljes_resetet(self, modell):
        """⚠️ A teljes reset eldobná a delegate-eket, és a rács
        visszaugrana a tetejére — épp azt a zavart okozná, amit a #1227
        meg akar szüntetni.

        A `rowsRemoved` jelzés a bizonyíték: reset esetén nem jönne.
        """
        latott = []
        modell.rowsRemoved.connect(
            lambda _p, elso, utolso: latott.append((elso, utolso))
        )
        modell.remove_by_path("/a/k1.jpg")
        assert latott == [(1, 1)], (
            "nem sor-eltávolítás történt (teljes reset?)"
        )


class TestACsoporthatarokKovetik:
    def test_a_csoportok_a_MEGMARADT_rekordokbol_szamolodnak(self, modell):
        """A `build_feed_groups` a rekordokból dolgozik — a kivétel után
        a `start`/`count` maguktól helyes."""
        from picasapy.app import formatting
        from PySide6.QtCore import QLocale

        modell.remove_by_path("/a/k1.jpg")
        csoportok = formatting.build_feed_groups(modell.photos, QLocale())
        assert [cs["count"] for cs in csoportok] == [2, 3], (
            "a mappa-csoportok darabszáma nem követte a törlést"
        )
        # a második csoport a helyére csúszott
        assert csoportok[0]["start"] == 0
        assert csoportok[1]["start"] == 2


class TestABekotes:
    """A LÁNC: a törlés-jelzéstől a rácsig (#1227).

    A #1181 tanulsága szerint a végpontok megléte nem elég — a
    `wire_fileops` kötése az, ami a hatást eljuttatja. Itt a
    `removeDeletedRow` és a resync EGYÜTT kell fusson, ebben a
    sorrendben: előbb a látható hatás, utána az egyeztetés.
    """

    def test_a_wire_fileops_a_torlesre_a_sort_IS_kiveszi(self):
        from pathlib import Path

        import picasapy.app.application as app

        forras = Path(app.__file__).read_text(encoding="utf-8")
        assert "removeDeletedRow" in forras, (
            "a törlés-jelzés nem veszi ki a sort — a #1227 lánca hiányzik"
        )
        #: a SORREND: a látható hatás előbb, az egyeztetés utána
        i_kivesz = forras.find("controller.removeDeletedRow(path)")
        i_resync = forras.find("refresh(path)", i_kivesz)
        assert 0 < i_kivesz < i_resync, (
            "a resync megelőzi a sor kivételét — a felhasználó a szinkron "
            "végéig nézné a törölt képet"
        )

    def test_a_controller_metodusa_NEM_slot(self):
        """A QML soha nem hívja — slotként a képesség-őr joggal jelezné
        felületről elérhetetlennek (#1476)."""
        from picasapy.app.library_controller import LibraryMixin

        metodus = LibraryMixin.removeDeletedRow
        assert not hasattr(metodus, "_slots"), "slotként van kitéve"
