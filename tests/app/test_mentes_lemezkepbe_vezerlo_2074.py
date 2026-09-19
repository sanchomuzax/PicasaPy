"""#2074 — a mentés lemezképbe: a VEZÉRLŐ bekötése.

A tulajdonos 2026-09-18-án a **(b)** ágat választotta: „a gyűjtemény mentése
több lemezképre". Az ISO-írót és a lemezekre osztást a `tests/burn/` méri (a
kiírt képet `7z`-vel, független megvalósítással olvassa vissza); ez a fájl a
BEKÖTÉST: a felületről indítható-e, háttérszálon fut-e, és a nyilvántartás a
kiírás UTÁN frissül-e (`WriteProgress::13` — „Mentési készlet frissítése" az
írás VÉGÉN).
"""

from __future__ import annotations

import shutil
import subprocess
import threading

import pytest

from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa, keszletek

_HETZ = shutil.which("7z") or shutil.which("7za")


@pytest.fixture
def kornyezet(tmp_path):
    forras = tmp_path / "kepek"
    (forras / "2020").mkdir(parents=True)
    for i in range(3):
        (forras / "2020" / f"IMG_{i}.jpg").write_bytes(b"\xff\xd8\xff" + bytes([i]) * 4000)
    cel = tmp_path / "lemezkepek"
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        keszlet_id = keszlet_letrehozasa(conn, "Teszt", str(cel)).id
        conn.commit()
    jeloltek = tuple(sorted(str(p) for p in (forras / "2020").glob("*.jpg")))
    return db, keszlet_id, jeloltek, str(forras), cel


@pytest.fixture
def vezerlo(qt_app, kornyezet, monkeypatch):
    from picasapy.app import backup_controller as modul

    db, keszlet_id, jeloltek, gyoker, cel = kornyezet
    ctl = modul.BackupController(db, (gyoker,))
    monkeypatch.setattr(ctl, "_jeloltek", lambda: jeloltek)
    yield ctl, keszlet_id, cel, db
    ctl.waitForBackgroundWorkers(20.0)


def _lefut(ctl, qt_app, keszlet_id, media="cd") -> None:
    ctl.futtasdLemezkepbe(keszlet_id, media)
    assert ctl.waitForBackgroundWorkers(60.0), "a háttérszál nem állt le"
    qt_app.processEvents()


class TestALemezkepIras:
    def test_KEPEK_keszulnek_a_celmappaban(self, vezerlo, qt_app):
        ctl, keszlet_id, cel, _db = vezerlo
        _lefut(ctl, qt_app, keszlet_id)
        kepek = sorted(cel.glob("*.iso"))
        assert kepek, "egyetlen lemezkép sem készült el"
        assert kepek[0].name == "picasapy-mentes-01.iso"

    def test_a_kep_tartalmazza_a_fotokat(self, vezerlo, qt_app, tmp_path):
        assert _HETZ, "nincs `7z` — az ellenőrzés önigazolás lenne"
        ctl, keszlet_id, cel, _db = vezerlo
        _lefut(ctl, qt_app, keszlet_id)
        ki = tmp_path / "bontva"
        ki.mkdir()
        kesz = subprocess.run(
            [_HETZ, "x", "-y", f"-o{ki}", str(sorted(cel.glob("*.iso"))[0])],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        assert kesz.returncode == 0, kesz.stdout + kesz.stderr
        nevek = {ut.name for ut in ki.rglob("*") if ut.is_file()}
        assert {"IMG_0.jpg", "IMG_1.jpg", "IMG_2.jpg"} <= nevek

    def test_a_jelzes_SZAMOKAT_ad(self, vezerlo, qt_app):
        ctl, keszlet_id, _cel, _db = vezerlo
        fogott: list[tuple[int, int]] = []
        ctl.lemezkepekKeszek.connect(lambda a, b: fogott.append((a, b)))
        _lefut(ctl, qt_app, keszlet_id)
        assert fogott, "a felület nem kapott visszajelzést"
        lemezek, fajlok = fogott[-1]
        assert lemezek >= 1
        assert fajlok == 3

    def test_HATTERSZALON_fut(self, vezerlo, qt_app, monkeypatch):
        from picasapy.app import backup_controller as modul

        ctl, keszlet_id, _cel, _db = vezerlo
        fo_szal = threading.current_thread().ident
        szalak: list[int] = []
        eredeti = modul.lemezkepekbe

        def jelolo(*args, **kwargs):
            szalak.append(threading.current_thread().ident)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "lemezkepekbe", jelolo)
        _lefut(ctl, qt_app, keszlet_id)
        assert szalak, "a lemezkép-írás el sem indult"
        assert all(a != fo_szal for a in szalak), (
            "a lemezkép-írás a hívó szálon futott — az ablak megállna"
        )


class TestANyilvantartas:
    def test_a_futas_a_KIIRAS_UTAN_kerul_be(self, vezerlo, qt_app):
        """`WriteProgress::13`: a készlet frissítése az írás VÉGÉN fut."""
        ctl, keszlet_id, _cel, db = vezerlo
        with open_index(db) as conn:
            elotte = [k for k in keszletek(conn) if k.id == keszlet_id][0]
        assert not elotte.utolso_futas
        _lefut(ctl, qt_app, keszlet_id)
        with open_index(db) as conn:
            utana = [k for k in keszletek(conn) if k.id == keszlet_id][0]
        assert utana.utolso_futas, "a futás nem került a nyilvántartásba"

    def test_a_MASODIK_futas_mar_nem_visz_semmit(self, vezerlo, qt_app):
        """Az elmentett állapot rögzül — a következő futás a hiányzókat viszi."""
        ctl, keszlet_id, cel, _db = vezerlo
        _lefut(ctl, qt_app, keszlet_id)
        elso = sorted(ut.name for ut in cel.glob("*.iso"))
        fogott: list[tuple[int, int]] = []
        ctl.lemezkepekKeszek.connect(lambda a, b: fogott.append((a, b)))
        _lefut(ctl, qt_app, keszlet_id)
        assert fogott[-1] == (0, 0), "a második futás újra kiírta volna mindent"
        assert sorted(ut.name for ut in cel.glob("*.iso")) == elso

    def test_a_kiiras_BUKASAKOR_nem_jegyzunk_fel_futast(
        self, vezerlo, qt_app, monkeypatch
    ):
        """Ha a képírás elszáll, a következő futás ugyanazt viszi újra."""
        from picasapy.app import backup_controller as modul

        ctl, keszlet_id, _cel, db = vezerlo

        def bukik(*args, **kwargs):
            raise OSError("nincs hely")

        monkeypatch.setattr(modul, "lemezkepekbe", bukik)
        hibak: list[str] = []
        ctl.hibatJelez.connect(hibak.append)
        _lefut(ctl, qt_app, keszlet_id)
        assert hibak, "a hiba némán elnyelődött"
        with open_index(db) as conn:
            keszlet = [k for k in keszletek(conn) if k.id == keszlet_id][0]
        assert not keszlet.utolso_futas, (
            "bukott írás után is késznek jelöltük a mentést"
        )
