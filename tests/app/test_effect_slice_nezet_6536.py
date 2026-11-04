"""Az Effekt-térszelvény nézettípusa nem „hazudik” (#6536).

A tulajdonos: Jó napom van után a Finomhangolás fülön a doboz lapos lapot
(képsík-nézet, 0,00) mutatott, visszavonás után a tónusfelületet. Az ok: az
`enhance` (Jó napom van) a képsík-nézetbe volt sorolva, a mérőképen (sakktábla)
az automatikus javítás nem változtat, és a doboz effektváltáskor a korábbi
nézettípusnál ragadt.
"""

# SAJÁT FUNKCIÓ (#6522): az eredeti Picasában nincs térszelvény.

from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QSettings

from picasapy.app.effect_slice import EffectSliceController, classify_effect


def _controller(tmp_path) -> EffectSliceController:
    settings = QSettings(str(tmp_path / "beallitas.ini"), QSettings.Format.IniFormat)
    edit = SimpleNamespace(_photo_id="", _provider=None, _image_size=None)
    return EffectSliceController(edit, settings=settings)


def test_a_jo_napom_van_tonusjavitas_nem_kepsik():
    assert classify_effect("enhance") == "tone"


def test_effektvaltaskor_az_uj_effekt_nezete_jon_nem_a_regi(qt_app, tmp_path):
    controller = _controller(tmp_path)
    controller.request("", [], 0, "image", "", "glow=1,0.5,0.5")
    assert controller.selectedViewType == "image"

    controller.request("finetune2", [0.0, 0.0, 0.0, 0.0], 0, "image", "", "glow=1,0.5,0.5")

    assert controller.selectedViewType == "tone", (
        "a Finomhangolás megnyitásakor a doboz a korábbi képsík-nézetnél ragadt"
    )


def test_ugyanannal_az_effektnel_a_kezi_nezetvaltas_megmarad(qt_app, tmp_path):
    controller = _controller(tmp_path)
    controller.request("finetune2", [0.0] * 4, 0, "", "", "glow=1,0.5,0.5")
    controller.cycleViewType()
    kezi = controller.selectedViewType
    assert kezi != "tone"

    controller.request("finetune2", [0.1, 0.0, 0.0, 0.0], 0, kezi, "", "glow=1,0.5,0.5")

    assert controller.selectedViewType == kezi


def test_a_foton_mert_tonusfelulet_atviteli_gorbe_nem_oszlopatlag():
    """#6536: a fotós mérés a bemenő szintenkénti kimenő átlag, nem a kép oszlopátlaga."""
    import numpy as np

    from picasapy.app.effect_slice_render import render_surface
    from picasapy.ini.filters import parse_filters

    rng = np.random.default_rng(6536)
    foto = rng.integers(0, 256, size=(120, 160, 3), dtype=np.uint8)
    adat = render_surface(foto, parse_filters("enhance=1"), "tone", probe_kind="photo")
    assert adat["kind"] == "tone"
    sor = adat["rows"][0]
    assert sor[0] < 0.2 and sor[-1] > 0.8, "a mért görbe lapos lap"
    assert all(b >= a - 1e-6 for a, b in zip(sor, sor[1:], strict=False))


def test_egyszinu_foton_is_mindegyik_szint_merheto():
    import numpy as np

    from picasapy.app.effect_slice_render import render_surface
    from picasapy.ini.filters import parse_filters

    foto = np.full((80, 80, 3), (200, 40, 40), dtype=np.uint8)
    adat = render_surface(foto, parse_filters("enhance=1"), "tone", probe_kind="photo")
    sor = adat["rows"][0]
    assert max(sor) - min(sor) > 0.3, "egyszínű fotón a görbe lapos lap lett"
