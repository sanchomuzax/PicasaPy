"""#3472: a keretes kép bélyegképén a keret arányos a mentett képpel.

A szerkesztett bélyegkép (`get_or_create_edited`) és az effektcsempe is
kicsinyített alapon futtatja a láncot. A `Border` két vastagsága eddig nyers
képpontban került a kis képre, így a bélyegképen sokszorosan vastagabb volt,
mint a mentett képen. Az eredeti a vastagságot `imageWidth /
fullResImageWidth` tényezővel szorozza (#3377, `render/elonezeti_arany.py`).

A mérce LÁTOTT: a bélyegkép felső fekete sávja, összevetve a teljes
felbontású render ugyanakkora kicsinyítésével.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.lazy_cv2 import cv2
from picasapy.render import apply_filters

KERET = "Border=1,20,5,0,000000,ffffff,0;"


def _fekete_sav(kep: np.ndarray) -> int:
    """A felső, sötét sáv magassága a középső oszlopban, képpontban."""
    oszlop = kep[:, kep.shape[1] // 2].astype(int).mean(axis=1)
    return int(np.argmax(oszlop > 60))


@pytest.fixture
def nagy_foto(tmp_path):
    ut = tmp_path / "nagy.jpg"
    cv2.imwrite(str(ut), np.full((3000, 4000, 3), 128, dtype=np.uint8))
    return ut


def _mentett_kicsiben(ut, magassag: int) -> int:
    """A teljes felbontású render, a bélyegkép magasságára kicsinyítve."""
    teljes = cv2.cvtColor(cv2.imread(str(ut)), cv2.COLOR_BGR2RGB)
    kimenet = apply_filters(teljes, parse_filters(KERET)).image
    arany = magassag / kimenet.shape[0]
    kicsi = cv2.resize(
        kimenet, (round(kimenet.shape[1] * arany), magassag), interpolation=cv2.INTER_AREA
    )
    return _fekete_sav(kicsi)


def test_a_szerkesztett_belyegkep_kerete_a_mentett_kepevel_egyezik(tmp_path, nagy_foto):
    from picasapy.thumbs import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "cache", size=256)
    info = nagy_foto.stat()
    ut = cache.get_or_create_edited(
        nagy_foto, info.st_mtime_ns, info.st_size, parse_filters(KERET)
    )
    belyeg = cv2.imread(str(ut))
    vart = _mentett_kicsiben(nagy_foto, belyeg.shape[0])
    # A 25 képpontos keret 3050-ből 256-ra kicsinyítve ~2 képpont; javítás
    # nélkül a 2048-as alapon rajzolt keret ~3 képpont volt.
    assert abs(_fekete_sav(belyeg) - vart) <= 1


def test_a_regi_belyegkepek_ujragenerálodnak():
    """A lemez-cache kulcsa verziót visel: a korábbi, túl vastag keretes
    bélyegképek nem adhatnak találatot."""
    from picasapy.thumbs import cache as cache_modul

    assert cache_modul._EDIT_CACHE_VERSION >= 3
