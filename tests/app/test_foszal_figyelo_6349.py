"""#6349: a fő szál-figyelő megmondja, hol állt a felület, amikor nem válaszolt."""

from __future__ import annotations

import logging
import time
from types import SimpleNamespace

from picasapy.perf import foszal_figyelo as modul
from picasapy.perf.foszal_figyelo import FoszalFigyelo, verem_kulcs


def _figyelo(kuszob_s: float) -> tuple[FoszalFigyelo, list[str]]:
    sorok: list[str] = []

    class Gyujto(logging.Handler):
        def emit(self, record):
            sorok.append(record.getMessage())

    log = logging.getLogger(f"teszt-foszal-{id(sorok)}")
    log.propagate = False
    log.addHandler(Gyujto())
    log.setLevel(logging.WARNING)
    return FoszalFigyelo(kuszob_s=kuszob_s, mintavetel_s=0.02, log=log), sorok


def _lassu_lepes():
    time.sleep(0.4)


def test_a_blokkolo_szakasz_helye_a_naploba_kerul():
    figyelo, sorok = _figyelo(kuszob_s=0.2)
    try:
        with figyelo.szakasz("Main.qml betöltése"):
            _lassu_lepes()
    finally:
        figyelo.leallitas()
    assert len(sorok) == 1, sorok
    assert "Main.qml betöltése" in sorok[0]
    assert "test_foszal_figyelo_6349.py:_lassu_lepes:" in sorok[0]
    assert "/" not in sorok[0].split("—", 1)[1], "útvonal nem kerülhet a naplóba"


def test_rovid_szakasz_nem_naploz():
    figyelo, sorok = _figyelo(kuszob_s=5.0)
    try:
        with figyelo.szakasz("gyors"):
            time.sleep(0.05)
    finally:
        figyelo.leallitas()
    assert sorok == []


def test_a_verem_kulcs_a_sajat_kodsort_is_megnevezi():
    def keret(fajl, fuggveny, sor, vissza=None):
        return SimpleNamespace(
            f_code=SimpleNamespace(co_filename=fajl, co_name=fuggveny),
            f_lineno=sor,
            f_back=vissza,
        )

    sajat = keret("/x/src/picasapy/app/exportcelok.py", "vedett", 42)
    kulso = keret("/usr/lib/python3.12/genericpath.py", "exists", 19, sajat)
    assert verem_kulcs(kulso) == "genericpath.py:exists:19 ← exportcelok.py:vedett:42"
    assert verem_kulcs(sajat) == "exportcelok.py:vedett:42"


def test_futas_kozbeni_fagyas_a_szivveresbol(qt_app, monkeypatch):
    monkeypatch.setattr(modul, "ELAVULT_S", 0.2)
    monkeypatch.setattr(modul, "SZIVVERES_MS", 50)
    figyelo, sorok = _figyelo(kuszob_s=0.3)
    try:
        figyelo.szivveres_inditasa(qt_app)
        hatarido = time.monotonic() + 0.3
        while time.monotonic() < hatarido:
            qt_app.processEvents()
            time.sleep(0.01)
        _lassu_lepes()
        hatarido = time.monotonic() + 1.0
        while not sorok and time.monotonic() < hatarido:
            qt_app.processEvents()
            time.sleep(0.01)
    finally:
        figyelo.leallitas()
    assert len(sorok) == 1, sorok
    assert "a felület nem válaszolt" in sorok[0]
    assert "_lassu_lepes" in sorok[0]


def test_a_figyelo_nem_telepit_qt_uzenetkezelot():
    """⛔ A Python-oldali Qt-üzenetkezelő a QML-betöltés alatt HOLTPONTOT okozott
    (a `qml_betoltes_bontas.py` gyermeke 180 s után időtúllépés) — tilos."""
    from pathlib import Path

    forras = Path(modul.__file__).read_text(encoding="utf-8")
    kod = forras.split('"""', 2)[2]  # a modul leírása (ami a tilalmat elmondja) nélkül
    assert "qInstallMessageHandler" not in kod
