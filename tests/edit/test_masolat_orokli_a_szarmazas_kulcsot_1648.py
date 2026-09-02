"""#1648 — a „Másolat mentése" a FORRÁS származás-kulcsát adja tovább.

A valódi Picasa a másolat `originfast` mezőjébe a **forrás** értékét írja,
nem a másolat saját tartalmából számoltat. Mérve a tulajdonos élő
adatbázisán (`research/testdata/1557-masolat-mentese/db3.zip`): négy,
egymástól bájtban eltérő másolat KÖZÖS értéket visel, és az a forrás saját
bájtjaiból jön ki a mi képletünkkel. Levezetés:
`docs/specs/picasa-tartalomkulcs.md`.

Ezek a tesztek a MAGOT nézik (`save_copy`): visszaadja-e az öröklendő
kulcsot. A tárolás az indexé — arra a `tests/test_index_origin_1648.py`
való.
"""

from __future__ import annotations

import numpy as np

from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.edit.save_copy import save_copy
from picasapy.edit.session import EditSession


def _kep(path, ertek: int = 128) -> None:
    import cv2

    cv2.imwrite(str(path), np.full((64, 64, 3), ertek, dtype=np.uint8))


def test_a_visszaadott_kulcs_a_forrase(tmp_path):
    forras = tmp_path / "kep.jpg"
    _kep(forras, 100)
    varhato = picasa_fast_key(forras)

    eredmeny = save_copy(
        forras, np.full((64, 64, 3), 200, dtype=np.uint8), EditSession()
    )

    assert eredmeny.inherited_origin_key == varhato


def test_a_kulcs_ELTER_a_masolat_sajat_kulcsatol(tmp_path):
    """A jegy lényege: a másolat NEM a saját tartalmából kapja a kulcsot.

    Fog: ha valaki „egyszerűsítésként" a célfájlra számolná a kulcsot, ez
    a teszt bukik — a beégetett szerkesztés miatt a két érték eltér.
    """
    forras = tmp_path / "kep.jpg"
    _kep(forras, 100)

    eredmeny = save_copy(
        forras, np.full((64, 64, 3), 240, dtype=np.uint8), EditSession()
    )

    sajat = picasa_fast_key(eredmeny.target_path)
    assert sajat is not None
    assert eredmeny.inherited_origin_key != sajat
    assert eredmeny.inherited_origin_key == picasa_fast_key(forras)


def test_ugyanannak_a_forrasnak_minden_masolata_ugyanazt_kapja(tmp_path):
    """A mérésben NÉGY másolat osztozott egyetlen értéken."""
    forras = tmp_path / "chart.jpg"
    _kep(forras, 100)

    kulcsok = {
        save_copy(
            forras,
            np.full((64, 64, 3), 60 + 40 * i, dtype=np.uint8),
            EditSession(),
        ).inherited_origin_key
        for i in range(4)
    }

    assert kulcsok == {picasa_fast_key(forras)}


def test_a_forras_fajlja_valtozatlan_marad(tmp_path):
    """A kulcs kiolvasása CSAK olvas — a forrás bájtra ugyanaz marad."""
    forras = tmp_path / "kep.jpg"
    _kep(forras, 100)
    elotte = forras.read_bytes()

    save_copy(forras, np.full((64, 64, 3), 200, dtype=np.uint8), EditSession())

    assert forras.read_bytes() == elotte
