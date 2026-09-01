"""#1798b — az e-mail-előkészítés ne dolgozzon némán.

## A lelet (párhuzamos UI-kutatás, `compose_mail` panel)

Az eredeti Picasa a **„Preparing attachments…”** sorral jelez, amíg a
mellékleteket készíti. Nálunk a `prepareAttachments()` a beállított
méretre **kicsinyíti** a képeket — nagy fájloknál ez másodpercekig tart —,
és eddig **némán** dolgozott alatta: a felhasználó azt látta, hogy nem
történik semmi.

A panel maga hatókörön kívül (a Gmail-ág megszűnt), de ez a részlete
**nem** ahhoz kötődik.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app.email_controller import EmailController

from support.jpeg_factory import make_jpeg


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _Foto:
    folder_path: str
    name: str
    rotate_steps: int = 0
    filters: str | None = None


def _vezerlo(fotok, tmp_path):
    return EmailController(
        photo_source=lambda: fotok,
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )


def _kep(tmp_path: Path) -> _Foto:
    mappa = tmp_path / "kepek"
    mappa.mkdir(exist_ok=True)
    make_jpeg(mappa / "a.jpg", (800, 600))
    return _Foto(folder_path=str(mappa), name="a.jpg")


class TestAJelzes:
    def test_elkezdodik_es_vegetER(self, qt_app, tmp_path):
        vezerlo = _vezerlo([_kep(tmp_path)], tmp_path)
        naplo: list[bool] = []
        vezerlo.preparingChanged.connect(naplo.append)

        vezerlo.prepareAttachments([0], True)

        assert naplo == [True, False], (
            f"a jelzés nem indult el és/vagy nem ért véget: {naplo}"
        )

    def test_ures_kijelolesre_NEM_villan(self, qt_app, tmp_path):
        """Nincs mit előkészíteni — egy azonnal eltűnő jelző csak zavarna."""
        vezerlo = _vezerlo([], tmp_path)
        naplo: list[bool] = []
        vezerlo.preparingChanged.connect(naplo.append)

        vezerlo.prepareAttachments([], True)

        assert naplo == []

    def test_HIBA_eseten_is_veget_er(self, qt_app, tmp_path, monkeypatch):
        """Az őr foga: `finally` nélkül a jelző BERAGADNA, és a felület
        örökre „dolgozom" állapotban maradna."""
        vezerlo = _vezerlo([_kep(tmp_path)], tmp_path)
        naplo: list[bool] = []
        vezerlo.preparingChanged.connect(naplo.append)

        def robban(*_a, **_kw):
            raise OSError("lemezhiba")

        monkeypatch.setattr(
            "picasapy.app.email_controller.export_photos", robban
        )
        with pytest.raises(OSError):
            vezerlo.prepareAttachments([0], True)

        assert naplo == [True, False], (
            f"a jelző beragadt a hiba után: {naplo}"
        )
