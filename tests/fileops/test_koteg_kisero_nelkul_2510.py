"""#2510 — kísérő NÉLKÜLI képnél a köteg ne jelentsen ütközést, és ne nevezzen át.

A `batch.py` (`_conflicts`, `_free_name`) a szélesebb, eredeti-mappára is
kiterjedő foglaltság-vizsgálatot kísérő NÉLKÜLI képnél is elvégezte.

⚠️ A fejléc korábbi változata a `copy.py`-t hozta helyes mintának. Ez
TÉVES volt: ott a vizsgálat kísérő nélkül teljesen elmaradt, és a másolat
örökbe fogadta a célban heverő árva eredetit (#2569). A két út azóta
ugyanazt a kaput használja (`moving_companions`).

MÉRVE (2026-09-06), `forras/x.jpg`-nek NINCS megőrzött eredetije, a célban
önálló `x.1.jpg` áll a saját eredetijével::

    originals_slot_free(dest,'x.jpg') = False
    conflicting_names -> ['x.jpg']
    move_photos done  -> [('x.jpg', 'x-1.jpg')]

A felhasználó ütközés-párbeszédet kapott ott, ahol nincs ütközés, és a képe
`x-1.jpg`-ként landolt. Adatvesztés nincs — a kár a fölösleges kérdés és a
néma átnevezés.

Az őrök MINDKÉT irányt kimondják: a kapu ne engedjen át fölösleges
ütközést, de a VALÓDI (kísérős) ütközést továbbra is fogja meg.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.edit import ORIGINALS_DIR_NAME
from picasapy.fileops.batch import RENAME, SKIP, conflicting_names, move_photos
from picasapy.fileops.originals import companions_of, originals_slot_free


def _kep(mappa: Path, nev: str, tartalom: bytes = b"kep") -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    path = mappa / nev
    path.write_bytes(tartalom)
    return path


def _eredeti(mappa: Path, nev: str) -> Path:
    directory = mappa / ORIGINALS_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / nev
    path.write_bytes(b"erintetlen")
    return path


class TestKiseroNelkuliKep:
    def test_a_jegy_reprodukcioja_nincs_utkozes_es_nincs_atnevezes(self, tmp_path):
        """A célban álló `x.1.jpg` egy ÖNÁLLÓ kép, a saját eredetijével — az
        a hely a mi képünknek sosem kellett volna."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg")
        _kep(cel, "x.1.jpg")
        _eredeti(cel, "x.1.jpg")

        # A mérés kiindulópontja: a hely foglaltnak LÁTSZIK…
        assert not originals_slot_free(cel, "x.jpg")
        # …de a mi képünknek nincs mit odatenni.
        assert companions_of(photo) == ()

        assert conflicting_names([photo], cel) == ()

        eredmeny = move_photos([photo], cel, RENAME)

        assert eredmeny.failed == ()
        assert [(a.name, b.name) for a, b in eredmeny.done] == [("x.jpg", "x.jpg")]
        assert (cel / "x.jpg").is_file()
        assert not (cel / "x-1.jpg").exists()
        # Az idegen kép eredetijéhez nem nyúltunk.
        assert (cel / ORIGINALS_DIR_NAME / "x.1.jpg").is_file()

    def test_a_kihagyas_hazirend_sem_hagyja_ki(self, tmp_path):
        """A `SKIP` ág ugyanazt a `_conflicts`-ot hívja: kísérő nélküli
        képet nem szabad kihagyni egy nem létező ütközés miatt."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg")
        _kep(cel, "x.1.jpg")
        _eredeti(cel, "x.1.jpg")

        eredmeny = move_photos([photo], cel, SKIP)

        assert eredmeny.skipped == ()
        assert [b.name for _, b in eredmeny.done] == ["x.jpg"]

    def test_a_valodi_nevutkozest_tovabbra_is_feloldja(self, tmp_path):
        """A kapu nem törölheti el a névütközés-vizsgálatot: azonos nevű kép
        a célban továbbra is pótnevet kap."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg", b"az enyem")
        _kep(cel, "x.jpg", b"mar ott volt")

        assert [p.name for p in conflicting_names([photo], cel)] == ["x.jpg"]

        eredmeny = move_photos([photo], cel, RENAME)

        assert [b.name for _, b in eredmeny.done] == ["x-1.jpg"]
        assert (cel / "x.jpg").read_bytes() == b"mar ott volt"
        assert (cel / "x-1.jpg").read_bytes() == b"az enyem"


class TestPotnevKiseroNelkul:
    """A `_free_name` ugyanazt a kaput viszi — külön mérendő, mert külön
    kódág (`batch.py::_free_name`), és a `_conflicts` őrei nem érnek el
    ide."""

    def test_a_gazdas_pillanatkep_nev_nem_zarja_ki_a_potnevet(self, tmp_path):
        """Kísérő nélküli képnél az `x-1.1.jpg` ÖNÁLLÓ kép eredetije nem
        teheti foglalttá az `x-1.jpg` pótnevet: a mi képünk semmit nem
        helyez el, és a gazdás példányt nem is örökölné."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg", b"az enyem")
        _kep(cel, "x.jpg", b"mar ott volt")  # névütközés -> pótnév kell
        _kep(cel, "x-1.1.jpg")  # ÖNÁLLÓ kép…
        _eredeti(cel, "x-1.1.jpg")  # …a saját eredetijével

        eredmeny = move_photos([photo], cel, RENAME)

        assert eredmeny.failed == ()
        assert [b.name for _, b in eredmeny.done] == ["x-1.jpg"]
        assert (cel / "x-1.jpg").read_bytes() == b"az enyem"


class TestOrokbefogadasEllen:
    """A kapu NEM gyengítheti az örökbefogadás elleni védelmet.

    A célnéven álló ÁRVA eredetit a mozgatott kép azonnal a sajátjának
    látná (`find_original_backup`), és a „Vissza az eredetihez" egy
    vadidegen kép bájtjait tenné a helyére — ez adatvesztés, nem
    kényelmetlenség. A `copy.py` ezt ma nem védi (mérve 2026-09-06), a
    kötegelt út viszont igen, és marad is.
    """

    def test_az_azonos_nevu_arva_eredeti_utkozes_marad(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg", b"az enyem")
        _eredeti(cel, "x.jpg")  # ÁRVA: nincs `cel/x.jpg` kép

        assert [p.name for p in conflicting_names([photo], cel)] == ["x.jpg"]

        eredmeny = move_photos([photo], cel, RENAME)

        assert [b.name for _, b in eredmeny.done] == ["x-1.jpg"]
        assert (cel / ORIGINALS_DIR_NAME / "x.jpg").read_bytes() == b"erintetlen"

    def test_a_potnev_sem_vezethet_orokbefogadashoz_a_celban(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg", b"az enyem")
        _kep(cel, "x.jpg", b"mar ott volt")
        _eredeti(cel, "x-1.jpg")  # az első pótnév eredetije ÁRVÁN áll ott

        eredmeny = move_photos([photo], cel, RENAME)

        assert [b.name for _, b in eredmeny.done] == ["x-2.jpg"]
        assert (cel / ORIGINALS_DIR_NAME / "x-1.jpg").read_bytes() == b"erintetlen"

    def test_a_potnev_sem_vezethet_orokbefogadashoz_a_FORRASBAN(self, tmp_path):
        """Az átnevezés a FORRÁS mappában történik (`rename_photo`), tehát a
        kép ott is örökbe fogadhatna egy árvát — még mielőtt elindulna."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg", b"az enyem")
        _kep(cel, "x.jpg", b"mar ott volt")
        _eredeti(forras, "x-1.jpg")  # árva a FORRÁS eredeti-mappájában

        eredmeny = move_photos([photo], cel, RENAME)

        assert [b.name for _, b in eredmeny.done] == ["x-2.jpg"]
        assert (forras / ORIGINALS_DIR_NAME / "x-1.jpg").read_bytes() == b"erintetlen"
        assert not (cel / ORIGINALS_DIR_NAME / "x-2.jpg").exists()


class TestKiserovelRendelkezoKep:
    """#1430/#1448 nem gyengülhet: akinek VAN megőrzött eredetije, annál a
    foglalt eredeti-hely továbbra is ütközés, és a pótnév továbbra is
    olyan, ahol az eredeti helye is szabad."""

    def test_a_foglalt_eredeti_hely_utkozes_marad(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg")
        _eredeti(forras, "x.jpg")  # a mi képünknek VAN eredetije
        _kep(cel, "x.1.jpg")
        _eredeti(cel, "x.1.jpg")  # ez teszi foglalttá az `x.` pillanatkép-helyet

        assert [p.name for p in conflicting_names([photo], cel)] == ["x.jpg"]

        eredmeny = move_photos([photo], cel, RENAME)

        assert eredmeny.failed == ()
        assert [b.name for _, b in eredmeny.done] == ["x-1.jpg"]
        # A kép és az eredetije EGYÜTT, a pótnéven.
        assert (cel / "x-1.jpg").is_file()
        assert (cel / ORIGINALS_DIR_NAME / "x-1.jpg").is_file()
        # Az idegen kép eredetije érintetlen.
        assert (cel / ORIGINALS_DIR_NAME / "x.1.jpg").read_bytes() == b"erintetlen"

    def test_a_potnev_az_eredeti_helyet_is_nezi(self, tmp_path):
        """A `_free_name` kapuzása nem eshet szét: kísérős képnél az első
        pótnév akkor sem jó, ha csak az EREDETI helye foglalt."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "x.jpg")
        _eredeti(forras, "x.jpg")
        _kep(cel, "x.jpg")  # a képnév foglalt -> pótnév kell
        _eredeti(cel, "x-1.jpg")  # az első pótnév EREDETI-helye foglalt

        eredmeny = move_photos([photo], cel, RENAME)

        assert eredmeny.failed == ()
        assert [b.name for _, b in eredmeny.done] == ["x-2.jpg"]
        assert (cel / ORIGINALS_DIR_NAME / "x-2.jpg").is_file()
        assert (cel / ORIGINALS_DIR_NAME / "x-1.jpg").read_bytes() == b"erintetlen"
