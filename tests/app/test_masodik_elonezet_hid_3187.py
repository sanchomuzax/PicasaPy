"""A második előnézet HÍDJA szűk felületet ad (#3187).

Egy teljes `EditController` kontextus-objektumként **125 bekötetlen tagot**
adott volna a QML-nek (mérve a `kepesseg_or.py`-jal), és azt ígérte volna,
hogy a második oldal ugyanúgy szerkeszthető, mint az első — ami ma nem igaz.
A híd pontosan annyit ad, amennyi a mai képességhez kell.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def hid(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.second_preview import SecondPreview

    szolgaltato = EditPreviewProvider()
    return SecondPreview(EditController(szolgaltato, slot="masodik"))


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


class TestAFelulet:
    def test_csak_harom_tagot_ad_a_QML_nek(self, hid):
        """A híd felülete SZŰK — ez a lényege."""
        from PySide6.QtCore import QMetaMethod

        meta = hid.metaObject()
        sajat = {
            meta.property(i).name()
            for i in range(
                meta.propertyOffset(), meta.propertyCount()
            )
        }
        slotok = {
            bytes(meta.method(i).name()).decode()
            for i in range(meta.methodOffset(), meta.methodCount())
            if meta.method(i).methodType() == QMetaMethod.MethodType.Slot
        }
        assert sajat == {"previewSource"}
        assert slotok == {"beginEdit", "endEdit"}

    def test_munkamenet_nelkul_ures_a_forras(self, hid):
        assert hid.previewSource == ""


class TestADelegalas:
    def test_a_beginEdit_a_REKESZES_kulcsot_adja(self, hid, photo):
        hid.beginEdit("42", str(photo))
        assert hid.previewSource.startswith("image://editpreview/42@masodik?rev=")

    def test_az_endEdit_zarja_a_munkamenetet(self, hid, photo):
        hid.beginEdit("42", str(photo))
        hid.endEdit()
        assert hid.previewSource == ""

    def test_a_kep_frissulese_jelzest_ad(self, hid, photo):
        """A `previewSource` `?rev=` bustere változik — a QML enélkül nem
        töltené újra a képet."""
        hid.beginEdit("42", str(photo))
        elotte = hid.previewSource
        valtozott = []
        hid.previewSourceChanged.connect(lambda: valtozott.append(1))
        hid.controller.applyEffect("bw")
        assert valtozott
        assert hid.previewSource != elotte
