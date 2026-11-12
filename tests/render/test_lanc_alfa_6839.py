"""A Glimmer-rétegek alfaútja irányított fényerő után (#6839)."""
import numpy as np

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


def test_picnikgrain_nem_feherteti_ki_a_kepet():
    y, x = np.indices((64, 64))
    image = np.stack((30 + x * 3, 20 + y * 3, 50 + x + y), axis=-1).astype(np.uint8)
    report = apply_filters(image, parse_filters(
        "dir_brite=1,-0.165675,-0.653172;PicnikGrain=1,42.719945,0;"
    ))
    assert report.skipped == ()
    assert np.mean(report.image) < 240
    assert np.ptp(report.image) > 30



def test_picnikgrain_vilagosito_fehert_kever(monkeypatch):
    from picasapy.render import glimmer_artistic

    calls = []
    original = glimmer_artistic.apply_blend_mode

    def observe(base, layer, mode, alpha):
        calls.append((layer.copy(), mode))
        return original(base, layer, mode, alpha)

    monkeypatch.setattr(glimmer_artistic, "apply_blend_mode", observe)
    image = np.full((32, 32, 3), 120, dtype=np.uint8)
    report = apply_filters(image, parse_filters("PicnikGrain=1,40,1;"), input_alpha=0)
    assert report.skipped == ()
    assert np.all(report.image >= 254)
    assert len(calls) == 1
    assert np.all(calls[0][0] == 255.0)


def test_museummatte_atlatszo_kepet_sotetiti():
    image = np.full((128, 128, 3), (120, 180, 240), dtype=np.uint8)
    report = apply_filters(image, parse_filters("MuseumMatte=1,25,40;"), input_alpha=0)
    assert report.skipped == ()
    center = report.image[report.image.shape[0] // 2, report.image.shape[1] // 2]
    expected = (image[0, 0].astype(np.uint16) * 77) >> 8
    np.testing.assert_allclose(center, expected, atol=2)
