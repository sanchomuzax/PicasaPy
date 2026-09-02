"""A PISZKOZAT nem osztható meg és nem nyomtatható (#1072).

A tiltás nem a mi használhatósági ötletünk, hanem a
`projectutils::draft_collage` erőforrás-szöveg KIMONDOTT tartalma:

> „Ez a kollázs még nem készült el teljesen. A kollázs befejezéséhez (ami a
> megosztás és a nyomtatás feltétele) kattintson a »Létrehozás« gombra.
> Megjegyzendő, hogy később bármikor módosíthatja a kollázst, akár még a
> mentése után is."

A spec ezt normatívának mondja ki (`kollazs-eletciklus.md` 4.2).

## Miért a VEZÉRLŐBEN mérünk, és nem a gombon

A Nyomtatás/E-mail tálcagombok jelzése (`TrayBar.printRequested`,
`emailRequested`) a mai fában **nincs bekötve** — a `print_controller.py`
és az `email_controller.py` docstringje maga sorolja fel az integrátor
teendőit. Ha a tiltást a gombra tennénk, az a bekötés napján elveszne, és
a felhasználó egy PISZKOZAT-feliratos képet nyomtatna ki. A kapu ezért ott
áll, ahol a művelet TÉNYLEGESEN elindul: a nyomtatás rajzoló ágán és az
e-mail csatolmány-előkészítésén.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app.collage_draft_guard import CollageDraftGuard
from picasapy.app.email_controller import EmailController
from picasapy.collage.autosave import AUTOSAVE_NAME
from support.jpeg_factory import make_jpeg

try:
    from picasapy.app.print_controller import PrintController

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover - hiányos Debian-telepítésen
    PrintController = None
    _QTPRINTSUPPORT_VAN = False


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _Foto:
    folder_path: str
    name: str
    rotate_steps: int = 0
    filters: str = ""


@pytest.fixture
def kollazsok(tmp_path):
    """Egy PISZKOZAT (kép + `autosave.cxf`) és egy KÉSZ kollázs egy mappában."""
    mappa = tmp_path / "Kollazsok"
    mappa.mkdir()
    piszkozat = mappa / "AI10.jpg"
    make_jpeg(piszkozat, size=(64, 48))
    kesz = mappa / "AI9.jpg"
    make_jpeg(kesz, size=(64, 48))
    kesz.with_suffix(".cxf").write_text("<collage/>", encoding="utf-8")
    (mappa / AUTOSAVE_NAME).write_text("<collage/>", encoding="utf-8")
    return mappa, piszkozat, kesz


class TestAzUzenet:
    """A szöveg SZÓ SZERINT az erőforrásból való, nem a mi fogalmazásunk."""

    def test_az_uzenet_a_draft_collage_szovege(self, qt_app):
        uzenet = CollageDraftGuard().restriction_message()

        assert uzenet == (
            "This collage was not completed. To finalize this collage "
            '(required for sharing or printing), please select the "Create '
            'Now" button. Please note that you can always change your '
            "collage later, even after it has been saved."
        )

    def test_a_piszkozatot_megtalalja_a_kijelolesben(self, qt_app, kollazsok):
        _mappa, piszkozat, kesz = kollazsok
        orzo = CollageDraftGuard()

        assert orzo.first_draft([kesz, piszkozat]) == piszkozat
        assert orzo.first_draft([kesz]) is None


@pytest.mark.skipif(not _QTPRINTSUPPORT_VAN, reason="nincs QtPrintSupport")
class TestNyomtatas:
    def test_piszkozatot_NEM_nyomtat(self, qt_app, kollazsok, tmp_path):
        mappa, piszkozat, _kesz = kollazsok
        vezerlo = PrintController(
            photo_source=lambda: [_Foto(str(mappa), piszkozat.name)]
        )
        hibak: list[str] = []
        vezerlo.printFailed.connect(hibak.append)
        cel = tmp_path / "nyomat.pdf"

        siker = vezerlo.renderPrintPreviewPdf([0], "fit", "auto", str(cel))

        assert siker is False, "a piszkozat kinyomtatható maradt"
        assert not cel.exists(), "félkész nyomat keletkezett"
        assert hibak == [CollageDraftGuard().restriction_message()]

    def test_KESZ_kollazst_nyomtat(self, qt_app, kollazsok, tmp_path):
        """Az ellenkező irányú őr: a tiltás CSAK a piszkozatra vonatkozik."""
        mappa, _piszkozat, kesz = kollazsok
        vezerlo = PrintController(
            photo_source=lambda: [_Foto(str(mappa), kesz.name)]
        )
        cel = tmp_path / "nyomat.pdf"

        assert vezerlo.renderPrintPreviewPdf([0], "fit", "auto", str(cel)) is True


class TestEmail:
    def test_piszkozatot_NEM_csatol(self, qt_app, kollazsok, tmp_path):
        mappa, piszkozat, _kesz = kollazsok
        vezerlo = EmailController(
            photo_source=lambda: [_Foto(str(mappa), piszkozat.name)],
            settings=QSettings(
                str(tmp_path / "mail.ini"), QSettings.Format.IniFormat
            ),
        )
        hibak: list[str] = []
        vezerlo.emailFailed.connect(hibak.append)

        csatolmanyok = vezerlo.prepareAttachments([0], False)

        assert csatolmanyok == []
        assert hibak == [CollageDraftGuard().restriction_message()]

    def test_KESZ_kollazst_csatol(self, qt_app, kollazsok, tmp_path):
        mappa, _piszkozat, kesz = kollazsok
        vezerlo = EmailController(
            photo_source=lambda: [_Foto(str(mappa), kesz.name)],
            settings=QSettings(
                str(tmp_path / "mail.ini"), QSettings.Format.IniFormat
            ),
        )

        # #2020: a MÉRT alapérték szerint egy kép ugyanakkora, mint több
        # (`EmailSinglePicture` alapja 0), tehát alapból ÁTMÉRETEZÉS történne,
        # és a visszaadott út egy ideiglenes másolaté lenne. Ez a teszt nem a
        # méretről szól, hanem arról, hogy a KÉSZ kollázst nem tiltja a
        # piszkozat-őr — ezért az eredeti méretet kérjük, ahol a forrásút
        # változatlanul jön vissza, és az állítás továbbra is éles marad.
        vezerlo.setSinglePictureOriginal(True)

        assert vezerlo.prepareAttachments([0], False) == [str(kesz)]
