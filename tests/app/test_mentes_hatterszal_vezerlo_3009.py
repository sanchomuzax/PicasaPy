"""#3009: a mentés-vezérlő háttérszálon másol, és megszakítható.

A mag (haladás, megszakítás) próbái a `tests/backup/` alatt futnak; itt a
VEZÉRLŐ szál-viselkedése a kérdés: a másolás nem foghatja meg a felület
szálát, különben az ablak a művelet idejére megáll.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa


@pytest.fixture
def kornyezet(tmp_path):
    forras = tmp_path / "kepek"
    forras.mkdir()
    for i in range(4):
        (forras / f"IMG_{i}.jpg").write_bytes(b"\xff\xd8\xff" + bytes([i]) * 64)
    cel = tmp_path / "mentes"
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        keszlet_id = keszlet_letrehozasa(conn, "Teszt", str(cel)).id
        conn.commit()
    jeloltek = tuple(sorted(str(p) for p in forras.glob("*.jpg")))
    return db, keszlet_id, jeloltek, str(forras), cel


class TestAVezerlo:
    """A vezérlő NEM a hívó szálon másol."""

    @pytest.fixture
    def vezerlo(self, qt_app, kornyezet, monkeypatch):
        from picasapy.app import backup_controller as modul

        db, keszlet_id, jeloltek, gyoker, cel = kornyezet
        ctl = modul.BackupController(db, (gyoker,))
        monkeypatch.setattr(ctl, "_jeloltek", lambda: jeloltek)
        return ctl, keszlet_id, cel

    def test_a_MASOLAS_hatterszalon_megy(self, vezerlo, qt_app, monkeypatch):
        """A MÁSOLÁS szálát mérjük, nem a jelzés-fogadóét.

        ⚠️ A `haladas` fogadója akkor is a fő szálon fut, ha a másolás a
        háttérben megy: a Qt a szálak közti jelzést sorba állítja. Az első
        változat ezt mérte, és hamisan „hívó szálon futott"-at mondott."""
        import threading

        from picasapy.app import backup_controller as modul

        ctl, keszlet_id, _cel = vezerlo
        fo_szal = threading.current_thread().ident
        szalak: list[int] = []
        eredeti = modul.futtasd

        def jelolo(*args, **kwargs):
            szalak.append(threading.current_thread().ident)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "futtasd", jelolo)

        ctl.futtasdMost(keszlet_id)
        assert ctl.waitForBackgroundWorkers(20.0), "a háttérszál nem állt le"
        qt_app.processEvents()

        assert szalak, "a másolás el sem indult"
        assert all(azonosito != fo_szal for azonosito in szalak), (
            "a másolás a hívó szálon futott — az ablak megállna"
        )

    def test_a_megszakitas_ELJUT_a_masolohoz(self, vezerlo, qt_app, monkeypatch):
        """A `szakitsdMeg()` a MÁSOLÓ ciklust állítja meg.

        A megszakítást a másoló szál kérdezi meg fájlonként; a jelzés-
        fogadón át megszakítani nem volna mérhető, mert az a fő szálon,
        a `processEvents`-nél fut — addigra a másolás rég kész. Ezért azt
        mérjük, hogy a `futtasd` MEGKAPJA a kérdezőt, és az a
        `szakitsdMeg()` után igazat mond."""
        from picasapy.app import backup_controller as modul

        ctl, keszlet_id, _cel = vezerlo
        kerdezok: list = []
        eredeti = modul.futtasd

        def jelolo(*args, **kwargs):
            kerdezok.append(kwargs.get("megszakitva"))
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "futtasd", jelolo)

        ctl.futtasdMost(keszlet_id)
        assert ctl.waitForBackgroundWorkers(20.0)

        assert kerdezok and kerdezok[0] is not None, (
            "a másoló nem kapott megszakítás-kérdezőt"
        )
        assert kerdezok[0]() is False
        ctl.szakitsdMeg()
        assert kerdezok[0]() is True

    def test_az_uj_futas_TORLI_a_korabbi_megszakitast(self, vezerlo, qt_app):
        """Különben egy megszakított mentés után soha többé nem indulna el
        a másolás — a jelző beragadna."""
        ctl, keszlet_id, cel = vezerlo
        ctl.szakitsdMeg()

        ctl.futtasdMost(keszlet_id)
        assert ctl.waitForBackgroundWorkers(20.0)
        qt_app.processEvents()

        assert len(list(cel.rglob("*.jpg"))) == 4, (
            "a beragadt megszakítás-jelző megakadályozta a mentést"
        )


class TestAParbeszed:
    """A felület: haladás-sáv és Megszakítás gomb a másolás alatt."""

    def test_a_parbeszed_KOTI_a_haladast(self):
        """Forrás-szintű állítás: a `BackupDialog` a három új jelzést
        fogadja. A párbeszéd viselkedési próbái a #440 fájljában futnak;
        itt az a kérdés, hogy az új jelzéseknek VAN fogadója — enélkül a
        háttérszál némán dolgozna."""
        from pathlib import Path

        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "BackupDialog.qml"
        ).read_text(encoding="utf-8")

        assert "function onHaladas(" in forras
        assert "function onFutasIndult(" in forras
        assert "backupCancelRun" in forras, "nincs Megszakítás gomb"
        assert "backupProgressTrack" in forras, "nincs haladás-sáv"

    def test_a_megszakitas_gombja_a_VEZERLOT_hivja(self):
        from pathlib import Path

        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "BackupDialog.qml"
        ).read_text(encoding="utf-8")
        szakasz = forras[forras.index("backupCancelRun"):]
        szakasz = szakasz[: szakasz.index("backupRun")]
        assert "szakitsdMeg()" in szakasz
