"""#3596: a képfüggő csúszkák a `.picasa.ini`-be SZÁZALÉKKÉNT mennek.

A felület a csúszkát továbbra is képpontban mutatja (#516/#723: a tartomány
a szerkesztett kép méretéből jön), de az eredeti `DynamicRangeSlider` a
tárolt értéket százaléknak veszi — tehát az íráskor a képpontot vissza kell
vetíteni: `t = (érték − minimum) / (maximum − minimum) · 100`.
"""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import format_param_values, resolve_effect_params

_W, _H = 960.0, 640.0


def _ini(name: str, values) -> tuple[str, ...]:
    return format_param_values(values, resolve_effect_params(name, _W, _H))


class TestKeppontbolSzazalek:
    @pytest.mark.parametrize(("px", "szazalek"), [(10.0, 0.0), (165.0, 50.0), (320.0, 100.0)])
    def test_focalzoom_radius(self, px, szazalek):
        assert float(_ini("focalzoom", [0.5, 0.5, 50.0, px, 50.0, 0.0])[3]) == pytest.approx(szazalek)

    def test_focalzoom_alapertek_a_tartomany_kozepe_50_szazalek(self):
        params = resolve_effect_params("focalzoom", _W, _H)
        assert float(_ini("focalzoom", [p.default for p in params])[3]) == pytest.approx(50.0)

    @pytest.mark.parametrize(("px", "szazalek"), [(0.0, 0.0), (160.0, 50.0), (320.0, 100.0)])
    def test_roundededges_corner_radius(self, px, szazalek):
        assert float(_ini("roundededges", [px, "#ffffff"])[0]) == pytest.approx(szazalek)

    def test_roundededges_alapertek_20_szazalek(self):
        params = resolve_effect_params("roundededges", _W, _H)
        assert float(_ini("roundededges", [params[0].default, "#ffffff"])[0]) == pytest.approx(20.0)

    def test_border_sarok_es_felirat(self):
        kimenet = _ini("border", [20.0, 5.0, 160.0, "#000000", "#ffffff", _H / 12])
        assert float(kimenet[2]) == pytest.approx(50.0)
        assert float(kimenet[5]) == pytest.approx(50.0)
        # a statikus csúszkák nyers értéke változatlan
        assert kimenet[0] == "20.000000"
        assert kimenet[1] == "5.000000"

    def test_tartomanyon_kivuli_ertek_szorul(self):
        assert float(_ini("roundededges", [999.0, "#ffffff"])[0]) == pytest.approx(100.0)
        assert float(_ini("roundededges", [-5.0, "#ffffff"])[0]) == pytest.approx(0.0)

    def test_params_nelkul_a_regi_nyers_ut(self):
        assert format_param_values([160.0]) == ("160.000000",)
