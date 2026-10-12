"""#4083: nagyítva a szöveg és az arcjelölés átfedője kapja az egeret (#4829: bontva)."""

from __future__ import annotations

import pytest

from tests.app.qml_functional import _nagyitott_atfedok_4083 as _proba


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
@pytest.mark.parametrize("device", ("szoveg", "arc"))
def test_nagyitva_az_aktiv_atfedo_kapja_az_egeret_es_modositja_a_kimenetet(
    qml_app_negyzet_kepek, qt_app, tmp_path, height_delta, device
):
    _proba.eszkoz_proba(qml_app_negyzet_kepek, qt_app, tmp_path, height_delta, device)
