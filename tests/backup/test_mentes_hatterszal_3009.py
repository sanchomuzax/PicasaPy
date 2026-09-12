"""#3009: a mentés háttérszálon fut, haladást jelez, és megszakítható.

## Mi volt a baj

A #440 felülete működött, de a másolás a HÍVÓ szálon futott: nagy
gyűjteménynél az ablak a művelet idejére megállt, és a felhasználó semmit
nem látott a haladásból. Az eredeti végig beszél:
*„Copying (%d/%d) files"* → *„Updating Backup Info"* → *„Backup Complete"*.

## Amit ez a próba mér

A MAG (`backup.futtasd`) haladás- és megszakítás-kezelését, és a vezérlő
szál-viselkedését. A megszakítás után a következő futás pontosan a
hiányzókat viszi — ezt a nyilvántartás már a #440 óta tudja (csak a
sikeresen átmásolt fájl kerül bele), itt az a kérdés, hogy a megszakítás
nem rontja-e el.
"""

from __future__ import annotations

import pytest

from picasapy.backup import futtasd, tervezd_meg
from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa


@pytest.fixture
def kornyezet(tmp_path):
    """Egy készlet, négy jelölt fájllal."""
    forras = tmp_path / "kepek"
    forras.mkdir()
    for i in range(4):
        (forras / f"IMG_{i}.jpg").write_bytes(b"\xff\xd8\xff" + bytes([i]) * 64)
    cel = tmp_path / "mentes"
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        #: a készlet-azonosító a VISSZAADOTT rekordból jön — a
        #: `keszlet_letrehozasa` a teljes készletet adja, nem az id-t
        keszlet_id = keszlet_letrehozasa(conn, "Teszt", str(cel)).id
        conn.commit()
    jeloltek = tuple(sorted(str(p) for p in forras.glob("*.jpg")))
    return db, keszlet_id, jeloltek, str(forras), cel


def _keszlet(conn, keszlet_id):
    from picasapy.index.backup_sets import keszletek

    for k in keszletek(conn):
        if k.id == keszlet_id:
            return k
    raise AssertionError("nincs ilyen készlet")


class TestAHaladas:
    def test_fajlonkent_jelez(self, kornyezet):
        db, keszlet_id, jeloltek, gyoker, _cel = kornyezet
        latott: list[tuple[int, int]] = []

        with open_index(db) as conn:
            keszlet = _keszlet(conn, keszlet_id)
            terv = tervezd_meg(conn, keszlet, jeloltek, gyokerek=(gyoker,))
            futtasd(conn, keszlet, terv, haladas=latott.append)
            conn.commit()

        assert latott == [(1, 4), (2, 4), (3, 4), (4, 4)], (
            f"a haladás-jelzés nem fájlonként jött: {latott}"
        )

    def test_ures_tervnel_nincs_jelzes(self, kornyezet):
        db, keszlet_id, jeloltek, gyoker, _cel = kornyezet
        latott = []
        with open_index(db) as conn:
            keszlet = _keszlet(conn, keszlet_id)
            terv = tervezd_meg(conn, keszlet, jeloltek, gyokerek=(gyoker,))
            futtasd(conn, keszlet, terv)  # az első futás mindent átvisz
            conn.commit()
            terv2 = tervezd_meg(conn, keszlet, jeloltek, gyokerek=(gyoker,))
            futtasd(conn, keszlet, terv2, haladas=latott.append)

        assert latott == []


class TestAMegszakitas:
    def test_a_masolas_MEGALL(self, kornyezet):
        db, keszlet_id, jeloltek, gyoker, cel = kornyezet
        latott: list[tuple[int, int]] = []

        with open_index(db) as conn:
            keszlet = _keszlet(conn, keszlet_id)
            terv = tervezd_meg(conn, keszlet, jeloltek, gyokerek=(gyoker,))
            masoltak = futtasd(
                conn, keszlet, terv,
                haladas=latott.append,
                megszakitva=lambda: len(latott) >= 2,
            )
            conn.commit()

        assert len(masoltak) == 2, (
            f"a megszakítás után is másolt: {len(masoltak)} fájl"
        )
        assert len(list(cel.rglob("*.jpg"))) == 2

    def test_a_KOVETKEZO_futas_a_hianyzokat_viszi(self, kornyezet):
        """A nyilvántartásba csak a sikeresen átmásolt fájl kerül — a
        megszakítás tehát nem veszít el semmit, csak elhalaszt."""
        db, keszlet_id, jeloltek, gyoker, cel = kornyezet
        latott: list[tuple[int, int]] = []

        with open_index(db) as conn:
            keszlet = _keszlet(conn, keszlet_id)
            terv = tervezd_meg(conn, keszlet, jeloltek, gyokerek=(gyoker,))
            futtasd(
                conn, keszlet, terv,
                haladas=latott.append,
                megszakitva=lambda: len(latott) >= 2,
            )
            conn.commit()

            terv2 = tervezd_meg(conn, keszlet, jeloltek, gyokerek=(gyoker,))
            assert len(terv2.fajlok) == 2, (
                "a második terv nem a hiányzó kettőt vinné"
            )
            futtasd(conn, keszlet, terv2)
            conn.commit()

        assert len(list(cel.rglob("*.jpg"))) == 4
