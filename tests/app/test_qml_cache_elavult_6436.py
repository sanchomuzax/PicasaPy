"""#6436: a régi változat előre fordított QML-gyorsítótára nem maradhat érvényben.

Mérve (helyi kísérlet): a qmlcachegen-nel fordított `.qmlc` a forrás
változása után is érvényes, a Qt a RÉGI felületet tölti be. Az 1.0.13 ilyen
fájlokat másolt a felhasználó profiljába, ezért a tulajdonos gépén az 1.0.16
kódja alatt az 1.0.13 felülete futott."""

from __future__ import annotations

from picasapy.app import qml_precompile


def _cache(tmp_path, monkeypatch):
    konyvtar = tmp_path / "qmlcache"
    konyvtar.mkdir()
    monkeypatch.setenv("QML_DISK_CACHE_PATH", str(konyvtar))
    return konyvtar


def test_belyeg_nelkul_az_elavult_forditasok_torlodnek(tmp_path, monkeypatch):
    konyvtar = _cache(tmp_path, monkeypatch)
    (konyvtar / "a.qmlc").write_bytes(b"regi")
    (konyvtar / "b.jsc").write_bytes(b"regi")
    (konyvtar / "mas.txt").write_text("marad", encoding="utf-8")

    assert qml_precompile.torold_az_elavult_cachet("1.0.21") == 2
    assert not (konyvtar / "a.qmlc").exists()
    assert not (konyvtar / "b.jsc").exists()
    assert (konyvtar / "mas.txt").exists()
    assert (konyvtar / qml_precompile.CACHE_BELYEG).read_text(encoding="utf-8") == "1.0.21"


def test_masik_verzio_belyegenel_torol(tmp_path, monkeypatch):
    konyvtar = _cache(tmp_path, monkeypatch)
    (konyvtar / qml_precompile.CACHE_BELYEG).write_text("1.0.13", encoding="utf-8")
    (konyvtar / "a.qmlc").write_bytes(b"regi")

    assert qml_precompile.torold_az_elavult_cachet("1.0.21") == 1
    assert not (konyvtar / "a.qmlc").exists()


def test_egyezo_belyegnel_megtartja_a_friss_forditast(tmp_path, monkeypatch):
    konyvtar = _cache(tmp_path, monkeypatch)
    (konyvtar / qml_precompile.CACHE_BELYEG).write_text("1.0.21", encoding="utf-8")
    (konyvtar / "a.qmlc").write_bytes(b"friss")

    assert qml_precompile.torold_az_elavult_cachet("1.0.21") == 0
    assert (konyvtar / "a.qmlc").read_bytes() == b"friss"


def test_hianyzo_konyvtarnal_nem_hibazik(tmp_path, monkeypatch):
    monkeypatch.setenv("QML_DISK_CACHE_PATH", str(tmp_path / "nincs"))
    assert qml_precompile.torold_az_elavult_cachet("1.0.21") == 0


def test_az_elofordito_beirja_a_belyeget(tmp_path, monkeypatch):
    konyvtar = _cache(tmp_path, monkeypatch)
    qml_precompile.ird_be_a_cache_belyeget("1.0.21")
    assert (konyvtar / qml_precompile.CACHE_BELYEG).read_text(encoding="utf-8") == "1.0.21"


def test_az_indulas_a_main_qml_betoltese_elott_takarit():
    """A takarításnak a QML-motor betöltése ELŐTT kell lefutnia."""
    from pathlib import Path

    forras = (
        Path(qml_precompile.__file__).resolve().parent / "application_startup_qml.py"
    ).read_text(encoding="utf-8")
    takaritas = forras.index("torold_az_elavult_cachet(")
    betoltes = forras.index('engine.load(str(_app._APP_DIR / "qml" / "Main.qml"))')
    assert takaritas < betoltes
