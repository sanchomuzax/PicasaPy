"""#4083: nagyított kettős nézetben a másik félre kattintva fókuszt vált (#4829: bontva)."""

from __future__ import annotations

import pytest

from tests.app.qml_functional import _nagyitott_atfedok_4083 as _proba


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
@pytest.mark.parametrize("layout", ("aa", "ab"))
def test_nagyitott_kettos_nezetben_a_masik_felre_kattintva_fokuszt_valt(
    qml_app_negyzet_kepek, qt_app, tmp_path, height_delta, layout
):
    _proba.kettos_nezet_proba(qml_app_negyzet_kepek, qt_app, tmp_path, height_delta, layout)
