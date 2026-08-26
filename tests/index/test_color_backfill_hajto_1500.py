"""#1500: a színkeresés gyorsítótárát feltöltő `backfill_colors` HAJTHATÓ
legyen — a hívó „hívd, amíg 0-t nem ad" ciklusa érjen véget, és lehessen
megmondani, hol tart.

## Miért ez a három állítás

A #1500 élővé teszi a `color:`/`szín:` keresést: egy háttérszál addig
hívja a `backfill_colors`-t, amíg az 0-t nem ad. Ehhez a magnak két olyan
tulajdonsága kell, ami eddig NEM volt meg:

1. **Véges futás.** A dekódolhatatlan fájlhoz (törött JPEG, kiterjesztés
   szerint fényképnek látszó nem-kép) a régi kód SEMMIT nem tárolt, a
   jelölt-lista viszont ugyanezt a sort adta vissza minden körben — a
   visszatérési érték így SOHA nem lett 0. A háttérszál végtelen ciklusba
   futott volna, körönként 81 ms/kép áron (#1480 mérése).
2. **Mérhető haladás.** A haladásjelzéshez és ahhoz, hogy a keresés meg
   tudja mondani „a feltöltés még nem futott le", kell egy (kész, összes)
   pár.
3. **Elavulás követése.** A jelölt-listát az útvonal MELLETT az
   mtime/méret is szűri, különben egy átszerkesztett kép örökre a régi
   színével maradna a gyorsítótárban.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.index import (
    backfill_colors,
    color_index_progress,
    load_color_tokens,
    open_index,
    sync_tree,
)


def _tomor_jpeg(path, bgr: tuple[int, int, int]) -> None:
    kep = np.zeros((32, 32, 3), dtype=np.uint8)
    kep[:, :] = bgr
    assert cv2.imwrite(str(path), kep)


def _vegig_feltolt(conn, *, max_kor: int = 20) -> int:
    """A #1500 háttérszálának ciklusa, KORLÁTTAL.

    A korlát nem kényelmi elem: korlát nélkül a régi (hibás) mag itt
    végtelen ciklusba fut, és a tesztfutás időtúllépéssel hal meg
    ahelyett, hogy megnevezné a hibát."""
    korok = 0
    while backfill_colors(conn, limit=10):
        korok += 1
        assert korok < max_kor, (
            "a feltöltés nem ér véget — a dekódolhatatlan fájl minden "
            "körben újra jelöltként jön vissza"
        )
    return korok



@pytest.fixture
def fa(tmp_path):
    """Két ép fénykép + egy dekódolhatatlan, `.jpg` nevű fájl."""
    root = tmp_path / "kepek"
    root.mkdir()
    _tomor_jpeg(root / "piros.jpg", (0, 0, 255))
    _tomor_jpeg(root / "kek.jpg", (255, 0, 0))
    (root / "torott.jpg").write_bytes(b"ez nem JPEG, csak ugy hivjak")
    return root


@pytest.fixture
def conn(tmp_path, fa):
    with open_index(tmp_path / "index.db") as kapcsolat:
        sync_tree(kapcsolat, fa)
        yield kapcsolat


class TestVegesFutas:
    def test_a_hajto_ciklus_veget_er(self, conn):
        """A „hívd, amíg 0-t nem ad" ciklus a törött fájl ellenére leáll.

        ⚠️ Ez a teszt a #1500 háttérszálának PONTOS ciklusa. Ha elbukik,
        az nem elméleti hiba: a felhasználó gépén egy processzormag
        pörögne a munkamenet végéig."""
        assert _vegig_feltolt(conn) >= 1, "el sem indult a feltöltés"

    def test_a_dekodolhatatlan_fajl_megjelolve_marad(self, conn):
        """A törött fájlhoz is kerül sor a táblába — üres tokenlistával.

        Enélkül nem a ciklus végességét javítanánk, hanem elrejtenénk a
        tünetet: a következő indításnál újra 81 ms-ot költenénk rá."""
        _vegig_feltolt(conn)
        sor = conn.execute(
            "SELECT color_tokens FROM photo_colors WHERE path LIKE '%torott.jpg'"
        ).fetchone()
        assert sor is not None, "a dekódolhatatlan fájl nem kapott bejegyzést"
        assert sor["color_tokens"] == "", "üres tokenlista kell, nem színtoken"


class TestHaladas:
    def test_ures_gyorsitotarnal_nulla_a_kesz(self, conn):
        assert color_index_progress(conn) == (0, 3)

    def test_reszleges_feltoltes_utan_a_kesz_no(self, conn):
        backfill_colors(conn, limit=2)
        kesz, osszes = color_index_progress(conn)
        assert (kesz, osszes) == (2, 3)

    def test_teljes_feltoltes_utan_kesz_egyenlo_osszes(self, conn):
        _vegig_feltolt(conn)
        kesz, osszes = color_index_progress(conn)
        assert kesz == osszes == 3


class TestElavulas:
    def test_megvaltozott_kep_ujra_jelolt_lesz(self, conn, fa, tmp_path):
        """Átszerkesztett kép: a gyorsítótár sora elavul, újra kell számolni.

        A régi jelölt-lista CSAK az útvonalra illesztett, tehát a
        megváltozott képet soha többé nem nézte meg — a `load_color_tokens`
        viszont (helyesen) érvénytelennek látta a sorát. A két oldal
        ellentmondott egymásnak: a kép örökre a régi színével kereshető."""
        _vegig_feltolt(conn)
        # a piros kép kékre cserélése (más méret is, hogy a `size` is váltson)
        kek = np.zeros((48, 48, 3), dtype=np.uint8)
        kek[:, :] = (255, 0, 0)
        assert cv2.imwrite(str(fa / "piros.jpg"), kek)
        sync_tree(conn, fa)

        assert backfill_colors(conn, limit=10) >= 1, (
            "a megváltozott kép nem került vissza a jelöltek közé"
        )
        kulcs = conn.execute(
            "SELECT f.path || ? || p.name AS teljes, p.mtime_ns, p.size "
            "FROM photos p JOIN folders f ON f.id = p.folder_id "
            "WHERE p.name = 'piros.jpg'",
            (__import__("os").sep,),
        ).fetchone()
        talalt = load_color_tokens(
            conn, [(kulcs["teljes"], kulcs["mtime_ns"], kulcs["size"])]
        )
        assert talalt, "a friss számítás nem került be érvényes sorként"
        assert "blue" in next(iter(talalt.values()))
