"""#3472: az effektcsempén a keret arányos a mentett képpel.

A csempe 200 képpontos forráson fut; a `Border` két vastagsága a csempe és
a teljes kép arányában skálázódik (`render/elonezeti_arany.py`). A mérce a
csempe KÉPÉN látott felső sáv, a teljes felbontású render ugyanakkora
kicsinyítésével összevetve (párja: `tests/thumbs/test_belyegkep_keret_arany_3472.py`).
"""

from __future__ import annotations

import numpy as np

from picasapy.ini import parse_filters
from picasapy.lazy_cv2 import cv2
from picasapy.render import apply_filters

KERET = "Border=1,20,5,0,000000,ffffff,0;"


def _fekete_sav(kep: np.ndarray) -> int:
    oszlop = kep[:, kep.shape[1] // 2].astype(int).mean(axis=1)
    return int(np.argmax(oszlop > 60))


def _mentett_kicsiben(ut, magassag: int) -> int:
    teljes = cv2.cvtColor(cv2.imread(str(ut)), cv2.COLOR_BGR2RGB)
    kimenet = apply_filters(teljes, parse_filters(KERET)).image
    arany = magassag / kimenet.shape[0]
    kicsi = cv2.resize(
        kimenet, (round(kimenet.shape[1] * arany), magassag), interpolation=cv2.INTER_AREA
    )
    return _fekete_sav(kicsi)


def test_az_effektcsempe_kerete_a_mentett_kepevel_egyezik(qt_app, tmp_path):
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
    from picasapy.index import open_index, photos_in_folder, sync_tree

    lib = tmp_path / "kepek"
    lib.mkdir()
    ut = lib / "nagy.jpg"
    cv2.imwrite(str(ut), np.full((1500, 2000, 3), 128, dtype=np.uint8))
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        rekordok = photos_in_folder(conn, lib)
    szolgaltato = EffectThumbnailProvider({str(r.id): r for r in rekordok}.get)
    kep = szolgaltato.requestImage(f"{rekordok[0].id}/border", None, None)
    rgb = kep.convertToFormat(kep.Format.Format_RGB888)
    tomb = np.frombuffer(rgb.constBits(), dtype=np.uint8).reshape(
        rgb.height(), rgb.bytesPerLine()
    )[:, : rgb.width() * 3].reshape(rgb.height(), rgb.width(), 3)
    vart = _mentett_kicsiben(ut, rgb.height())
    # javítás nélkül a 200 px-es forráson a 25 képpontos keret a csempe
    # magasságának ~10%-a volt (~8 képpont)
    assert abs(_fekete_sav(tomb) - vart) <= 1
