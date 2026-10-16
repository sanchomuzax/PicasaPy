"""#4332: a régi indexfelülírás szinkronizálás után is megmarad.

Kompatibilitási teszt a már létező `taken_at_override` értékhez. A jelenlegi
Dátum és idő menüút már közvetlenül az EXIF `DateTimeOriginal` mezőt írja
(#4693), és új felülírást nem hoz létre.
"""

from __future__ import annotations

import os

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


def test_a_beallitott_datum_a_fajl_atirasa_utan_is_megmarad(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    kep = root / "a.jpg"
    make_jpeg(kep, taken_at="2020:03:01 10:00:00")
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, root)
        conn.execute(
            "UPDATE photos SET taken_at_override = ? WHERE name = 'a.jpg'",
            ("2019-03-01T10:00:00",),
        )
        conn.commit()

        make_jpeg(kep, taken_at="2020:03:01 10:00:00", size=(96, 64))
        st = kep.stat()
        os.utime(kep, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
        sync_tree(conn, root)

        override = conn.execute(
            "SELECT taken_at_override FROM photos WHERE name = 'a.jpg'"
        ).fetchone()[0]
    assert override == "2019-03-01T10:00:00"
