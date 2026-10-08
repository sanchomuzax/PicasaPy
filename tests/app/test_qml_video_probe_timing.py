"""Időzítési regressziótesztek a külön processzben futó videópróbához."""

import importlib.util
from pathlib import Path


_PROBE_UT = Path(__file__).with_name("qml_video_probe.py")
_SPEC = importlib.util.spec_from_file_location("qml_video_probe_timing", _PROBE_UT)
assert _SPEC is not None and _SPEC.loader is not None
_PROBE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROBE)


def test_varj_kattintasablak_vege_a_duplakattintas_intervallum_es_tartalek_utan():
    ido = 10.0
    alvasok = []

    class Alkalmazas:
        feldolgozasok = 0

        def processEvents(self):
            self.feldolgozasok += 1

    def alvas(masodperc):
        nonlocal ido
        alvasok.append(masodperc)
        ido += masodperc

    app = Alkalmazas()
    _PROBE.varj_kattintasablak_vegere(
        app,
        utolso_kattintas=10.0,
        intervallum_ms=500,
        ora=lambda: ido,
        alvas=alvas,
        tartalek_ms=100,
    )

    assert ido >= 10.6
    assert app.feldolgozasok > 0
    assert alvasok and max(alvasok) <= 0.05
