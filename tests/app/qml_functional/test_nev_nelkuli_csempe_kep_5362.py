"""#5362: a Név nélküliek csempéin az arckép betöltődik és látszik.

A tulajdonos Windows 11-en (0.9.158) mind a 17 csempét üresen látta; Linuxon a
képek megjelennek. Ez a teszt a CI Windows-lábán is fut, ezért ott derül ki,
mi történik: minden `faceImage_<id>` elemnek `Image.Ready` állapotba kell jutnia
(nem `Error`-ba), és a csempe képterülete nem lehet egyszínű.

A bukó üzenet az összes csempe állapotát és forrását kiírja, hogy a Windows-
futó naplójából a hiba oka (betöltési hiba, üres kép, rossz URL) olvasható legyen.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from tests.support.varakozas import var_feltetelre

_minta = importlib.util.spec_from_file_location(
    "nev_nelkuli_torzs_hatter_5352_minta",
    Path(__file__).with_name("test_nev_nelkuli_torzs_hatter_5352.py"),
)
_m = importlib.util.module_from_spec(_minta)
_minta.loader.exec_module(_m)

# a #5352 tesztjének környezete (hat arc, valódi bélyegképek) újrahasznosítva
qml_app_5352 = _m.qml_app_5352

def _arckepek(window) -> list:
    talalt = []

    def bejar(item):
        for gyerek in item.childItems():
            if gyerek.objectName().startswith("faceImage_") and gyerek.isVisible():
                talalt.append(gyerek)
            bejar(gyerek)

    bejar(window.contentItem())
    return talalt


def _kesz(kep) -> bool:
    """Betöltve és van kirajzolható tartalma (a `status` enumot a PySide nem
    alakítja át, ezért a haladást és a kirajzolt méretet nézzük)."""
    return float(kep.property("progress")) >= 1.0 and float(kep.property("paintedWidth")) > 0


def _allapotok(kepek) -> str:
    return "; ".join(f"{k.objectName()}: progress={k.property('progress')}, "
                     f"painted={k.property('paintedWidth')}x{k.property('paintedHeight')}, "
                     f"forras={k.property('source')}"
                     for k in kepek)


def test_a_nev_nelkuli_csempek_arckepe_betoltodik_es_latszik(qml_app_5352, qt_app):
    window, controller, engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    _m._nevnelkuliek_megnyitasa(window, qt_app, engine, controller)

    assert var_feltetelre(qt_app, lambda: len(_arckepek(window)) >= 6, 5.0), (
        f"a csempék arcképei nem jöttek létre: {len(_arckepek(window))} db"
    )
    kepek = _arckepek(window)
    assert var_feltetelre(qt_app, lambda: all(_kesz(k) for k in kepek), 15.0), (
        f"a csempék képe nem töltődött be: {_allapotok([k for k in kepek if not _kesz(k)])}"
    )

    kep = _m._kepkocka(window, qt_app, "kep_5362.png")
    for k in kepek[:3]:
        x, y = _m._scene_xy(k)
        szinek = {_m._rgb(kep, x + dx, y + dy)
                  for dx in range(10, int(k.width()) - 10, 9)
                  for dy in range(10, int(k.height()) - 10, 9)}
        assert len(szinek) > 20, (
            f"{k.objectName()} képterülete egyszínű ({len(szinek)} szín): "
            f"a kép betöltődött, de nem rajzolódott ki ({_allapotok([k])})"
        )
