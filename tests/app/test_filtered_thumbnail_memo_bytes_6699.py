"""A szűrt bélyegképek memóriakorlátja bájtban működik (#6699)."""

from PySide6.QtGui import QImage

from picasapy.app.thumbnail_provider import _FilteredThumbMemo


def _rgb32(width: int, height: int) -> QImage:
    return QImage(width, height, QImage.Format.Format_RGB32)


def _stored_bytes(memo: _FilteredThumbMemo) -> int:
    return sum(image.sizeInBytes() for image in memo._items.values())


def test_a_kilakoltatas_a_kepek_bajtszamat_korlatozza():
    memo = _FilteredThumbMemo(capacity=128)
    for index in range(3):
        memo.put((index,), _rgb32(4, 4))

    assert _stored_bytes(memo) <= 128
    assert memo.get((0,)) is None
    assert memo.get((2,)) is not None


def test_a_kulcs_csere_az_uj_kep_meretet_szamolja():
    memo = _FilteredThumbMemo(capacity=160)
    memo.put(("a",), _rgb32(4, 4))
    memo.put(("b",), _rgb32(4, 4))
    memo.put(("a",), _rgb32(8, 4))

    assert _stored_bytes(memo) <= 160
    assert memo.get(("a",)) is not None
    assert memo.get(("b",)) is None


def test_a_korlatnal_nagyobb_kep_nem_marad_a_memoriatarban():
    memo = _FilteredThumbMemo(capacity=32)
    memo.put(("nagy",), _rgb32(4, 4))

    assert _stored_bytes(memo) <= 32
    assert memo.get(("nagy",)) is None
