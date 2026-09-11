"""#1620: a golden-készlet hiánya NEM maradhat néma.

A valódi golden-kitek (`research/golden-kit*/`) a fejlesztői gépen élnek,
a repóban nincsenek — a CI tehát soha nem vet össze semmit az eredeti
Picasa kimenetével. Ez önmagában rendben van; ami NEM volt rendben, hogy a
hiány *sikernek* látszott: a nulla összevetésből „0 eltér" összegzés lett.

Két eset, két jelzés:

| a kit-könyvtár | a válasz |
|---|---|
| nem létezik | `ValueError` — már korábban is |
| létezik, de üres | `UresKeszlet` — ez az új (#1620) |
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "golden" / "compare_render.py"
)


def _modul():
    spec = importlib.util.spec_from_file_location("compare_render", _MODULE_PATH)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["compare_render"] = modul
    spec.loader.exec_module(modul)
    return modul


class TestAHianyJelez:
    def test_a_NEM_LETEZO_konyvtar_hibat_ad(self, tmp_path):
        cr = _modul()
        with pytest.raises(ValueError):
            cr.run_kit(
                tmp_path / "nincs-ilyen", cr.Thresholds(), cr.load_luts(None)
            )

    def test_az_URES_konyvtar_sem_csendes(self, tmp_path):
        """Ez volt a néma ág: létező, de üres kitre `[]` jött vissza, és a
        riport „0 eltér"-t írt — sikernek olvasva."""
        ures = tmp_path / "kit"
        ures.mkdir()
        cr = _modul()
        with pytest.raises(cr.UresKeszlet) as hiba:
            cr.run_kit(ures, cr.Thresholds(), cr.load_luts(None))
        assert str(ures) in str(hiba.value), "a jelzés nem nevezi meg az utat"

    def test_a_HIBAUZENET_megmondja_mi_hianyzik(self, tmp_path):
        ures = tmp_path / "kit"
        ures.mkdir()
        cr = _modul()
        with pytest.raises(cr.UresKeszlet) as hiba:
            cr.run_kit(ures, cr.Thresholds(), cr.load_luts(None))
        assert ".picasa.ini" in str(hiba.value)
