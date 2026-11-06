"""#6618: a tört `distance` natív padló-kerekítése őrzi a kép helyét."""

from __future__ import annotations

import numpy as np

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


def test_a_job_403_drop_shadow_a_kepet_y_61_helyezi():
    """A job-403 paraméterláncán a képtartalom Picasához illő doboza 59,61–1339,868.

    A teljesen fehér, szöveg nélküli bemenet színe nem keveredhet az árnyék
    vagy háttér színével, ezért a kirajzolt képdobozt közvetlenül mérjük.
    """
    kep = np.full((807, 1280, 3), 255, dtype=np.uint8)
    ops = parse_filters(
        "DropShadow=1,5.692017,241.473639,41.331983,"
        "00c9dd31,005df725,98.258864;"
    )

    kimenet = apply_filters(kep, ops).image
    sorok, oszlopok = np.where(np.all(kimenet == (255, 255, 255), axis=2))

    assert kimenet.shape == (919, 1392, 3)
    assert (
        int(oszlopok.min()),
        int(sorok.min()),
        int(oszlopok.max()) + 1,
        int(sorok.max()) + 1,
    ) == (59, 61, 1339, 868)
