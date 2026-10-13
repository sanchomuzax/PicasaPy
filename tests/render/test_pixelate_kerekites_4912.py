"""#4912: a Pixelate célmérete pontos fél értéknél felfelé kerekít, ahogy az eredeti.

Az eredeti `Resize` célméretét `trunc(v + 0,5)`-tel számolja (spec
`filterdesc-registry.md`, 5/c–5/e; `ResizeImageOperation`, `0x00bc3650`). A
`round()` pontos `.5` értéknél párosra kerekít (bankár-kerekítés), ezért
`round(10,5) = 10`, az eredeti viszont `11`.

A teszt a kicsinyítő `Resize` hívásait figyeli, nem a kimenet pixeleit:
a célméret a spec szerint `W/Impact`, és pontos `.5` értéknél csak a
kerekítési szabály különbözteti meg a két megvalósítást.
"""

import numpy as np
import pytest

from picasapy.render import glimmer_artistic as a


@pytest.mark.parametrize(
    ("oldal", "impact", "varhato_celmeret"),
    [
        (105, 10.0, 11),  # 10,5  → 11 (round() adná: 10)
        (5, 2.0, 3),  # 2,5   → 3  (round() adná: 2)
    ],
)
def test_pixelate_kicsinyites_felfele_kerekit_fel_ertéknél(
    monkeypatch, oldal, impact, varhato_celmeret
):
    kep = np.zeros((oldal, oldal, 3), dtype=np.uint8)
    hivasok = []
    eredeti_resize = a.resize_image

    def figyelo(image, width, height, smoothing=True, lanczos3=False):
        hivasok.append((width, height, smoothing))
        return eredeti_resize(image, width, height, smoothing=smoothing, lanczos3=lanczos3)

    monkeypatch.setattr(a, "resize_image", figyelo)

    a.apply_pixelate(kep, impact=impact)

    kicsinyites, nagyitas = hivasok
    assert kicsinyites == (varhato_celmeret, varhato_celmeret, True)
    assert nagyitas == (oldal, oldal, False)
