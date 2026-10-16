"""#4894: a Border-vastagság az eredeti float32 aránnyal csonkítódik."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.render import apply_filters
from picasapy.render.elonezeti_arany import elonezeti_arany

# rontás-kontroll: a Border-segéd visszaállítva a skalazott_vastagsag-ra → 4 failed


@pytest.mark.parametrize(
    ("vastagsag", "arany", "vart"),
    [
        (10.0, 0.7, 6),
        (20.0, 0.7, 13),
        (20.0, 0.9, 17),
        (3.9, 0.9, 2),
    ],
)
def test_a_border_kulso_es_belso_vastagsaga_float32_arannyal_csonkitodik(vastagsag, arany, vart):
    kep = np.zeros((4, 5, 3), dtype=np.uint8)
    meretek = []

    with elonezeti_arany(arany):
        for outer, inner in ((vastagsag, 0), (0, vastagsag)):
            lanc = parse_filters(f"Border=1,{outer},{inner},0,000000,ffffff,0;")
            meretek.append(apply_filters(kep, lanc).image.shape)

    vart_meret = (4 + 2 * vart, 5 + 2 * vart, 3)
    assert meretek == [vart_meret, vart_meret]
