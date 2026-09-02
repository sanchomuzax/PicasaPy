"""A webexport méret-lekérdezése BÁJT-alapon olvas (#1991).

## A lelet

A projekt a #65 és a #190 óta tudja, hogy a `cv2.imread` **fájlútvonalas**
alakja Windowson az ANSI kódlapon megy át, ezért ékezetes néven **némán**
nem olvas — nincs kivétel, nincs hibakód, csak `None`.

Négy modul (`collage/render.py`, `edit/save.py`, `thumbs/cache.py`,
`export/exporter.py`) ezért bájt-alapon megy. A `webexport/images.py`
kimaradt belőle: `cv2.imread(str(path))` — és **valódi felhasználói
úton** van, ahol a fájlnevek rendszeresen ékezetesek.

## A foga

Linuxon a fájlútvonalas alak is működik, tehát egy „ékezetes néven is
megy" teszt itt akkor is zöld lenne, ha a hiba bent maradna. Ezért a
`cv2.imread`-et **robbanóra** cseréljük: ha a megvalósítás azon menne, a
teszt Linuxon is bukik.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.lazy_cv2 import cv2
from picasapy.webexport.images import _image_size

from support.jpeg_factory import make_jpeg


@pytest.fixture
def ekezetes_kep(tmp_path) -> Path:
    """A tulajdonos gyűjteményében szokásos névforma."""
    return make_jpeg(tmp_path / "Nyaralás őszi képek.jpg", size=(120, 80))


class TestABajtAlapuOlvasas:
    def test_a_meret_helyes(self, ekezetes_kep):
        assert _image_size(ekezetes_kep) == (120, 80)

    def test_NEM_a_fajlutvonalas_olvasot_hasznalja(
        self, ekezetes_kep, monkeypatch
    ):
        """A foga: a `cv2.imread` robbanóra cserélve. Ha a megvalósítás
        azon menne, ez Linuxon is bukik — ott, ahol a valódi hiba nem
        jelentkezne."""

        def _tilos(*_args, **_kwargs):  # pragma: no cover - csak bukáskor fut
            raise AssertionError(
                "a webexport fájlútvonalas olvasót hív — ékezetes néven "
                "Windowson némán None-t adna (#190)"
            )

        monkeypatch.setattr(cv2, "imread", _tilos)
        assert _image_size(ekezetes_kep) == (120, 80)


class TestAHIANYZO_FAJL:
    def test_nem_dobal_kivetelt(self, tmp_path):
        """A függvény szerződése: a hiányzó/rossz fájl NEM szakítja meg az
        exportot, csak a méret marad 0."""
        assert _image_size(tmp_path / "nincs-ilyen.jpg") == (0, 0)

    def test_a_HIBA_NAPLOBA_kerul(self, tmp_path, caplog):
        """#1998 osztálya: a (0, 0) visszatérés önmagában néma — a
        felhasználó nem tudná meg, miért lett nulla a méret."""
        import logging

        with caplog.at_level(
            logging.WARNING, logger="picasapy.webexport.images"
        ):
            _image_size(tmp_path / "nincs-ilyen.jpg")
        assert any("nincs-ilyen.jpg" in r.getMessage() for r in caplog.records)
