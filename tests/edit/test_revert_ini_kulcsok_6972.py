"""#6972: a Revert az ini-ből a `filters` mellett a `rotate`, `flipped` és
`textactive` sort is törli (az eredeti `0x0046d7d0`), a többi kulcsot nem."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from picasapy.edit import EditSession, revert, save_edited
from picasapy.ini import load_document

_NEV = "IMG_6972.png"
_FILTERS = "enhance=1;autolight=1;"
_TORLENDO = ("filters", "redo", "rotate", "flipped", "textactive")
_MEGMARADO = (
    ("star", "yes"),
    ("caption", "Nyaralás"),
    ("backuphash", "12345"),
    ("originhash", "0123456789abcdef0123456789abcdef"),
    ("keywords", "tenger"),
    ("faces", "rect64(27c00680d8ffdb3f),ffffffffffffffff"),
)


def _png(szin: tuple[int, int, int]) -> bytes:
    ok, kodolt = cv2.imencode(".png", np.full((8, 8, 3), szin, dtype=np.uint8))
    assert ok
    return kodolt.tobytes()


def _kep_ini_szerkesztesekkel(mappa: Path) -> Path:
    kep = mappa / _NEV
    kep.write_bytes(_png((10, 20, 30)))
    sorok = [
        f"[{_NEV}]",
        f"filters={_FILTERS}",
        "redo=sepia=1;",
        "rotate=rotate(1)",
        "flipped=1",
        "textactive=1",
        *(f"{kulcs}={ertek}" for kulcs, ertek in _MEGMARADO),
    ]
    (mappa / ".picasa.ini").write_text("\n".join(sorok) + "\n", encoding="utf-8")
    return kep


def test_forgatas_mentes_revert_utan_nincs_szerkesztesi_sor_az_iniben(tmp_path):
    kep = _kep_ini_szerkesztesekkel(tmp_path)
    save_edited(kep, np.full((8, 8, 3), (40, 50, 60), dtype=np.uint8),
                EditSession.from_value(_FILTERS))
    ini = tmp_path / ".picasa.ini"

    eredmeny = revert(kep)

    szakasz = load_document(ini).section(_NEV)
    assert szakasz is not None
    for kulcs in _TORLENDO:
        assert szakasz.get(kulcs) is None, f"a Revert után bent maradt: {kulcs}"
    assert set(eredmeny.removed_keys) == set(_TORLENDO)


def test_revert_a_tobbi_kulcsot_erintetlenul_hagyja(tmp_path):
    kep = _kep_ini_szerkesztesekkel(tmp_path)
    save_edited(kep, np.full((8, 8, 3), (40, 50, 60), dtype=np.uint8),
                EditSession.from_value(_FILTERS))

    revert(kep)

    szakasz = load_document(tmp_path / ".picasa.ini").section(_NEV)
    assert szakasz is not None
    for kulcs, ertek in _MEGMARADO:
        if kulcs == "backuphash":
            continue  # a mentés frissíti, nem a Revert vizsgálata
        assert szakasz.get(kulcs) == ertek, f"megváltozott: {kulcs}"


def test_revert_a_kep_bajtjait_az_eredetire_allitja(tmp_path):
    kep = _kep_ini_szerkesztesekkel(tmp_path)
    eredeti = kep.read_bytes()
    save_edited(kep, np.full((8, 8, 3), (40, 50, 60), dtype=np.uint8),
                EditSession.from_value(_FILTERS))
    assert kep.read_bytes() != eredeti

    revert(kep)

    assert kep.read_bytes() == eredeti
