"""A mappafa bontás előtti és utáni, szöveg nélküli képpontjai (#6019)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem

from picasapy.index import open_index, sync_tree
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


_ARANY = Path(__file__).parent / "golden" / "folder_pane_6019"
_ALLAPOTOK = ("ures", "mappakkal", "albummal", "kijelolt-sorral", "helyi-menuvel")


def _pixelek(kep: QImage) -> np.ndarray:
    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    sorhossz = rgba.bytesPerLine()
    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    return adat.reshape(rgba.height(), sorhossz)[:, : rgba.width() * 4].reshape(
        rgba.height(), rgba.width(), 4
    ).copy()  # a nézet a függvény végén felszabaduló rgba-ra mutatna (#6085)


def _szovegteruletek_kimaszkolasa(ablak, pane, ervenyes: np.ndarray) -> None:
    """A szövegdobozokat és 4 px környezetüket hagyja ki a pixel-őrökből."""
    magassag, szelesseg = ervenyes.shape
    for objektum in ablak.findChildren(QObject):
        if not objektum.metaObject().className().startswith("QQuickText"):
            continue
        if not isinstance(objektum, QQuickItem):
            continue
        if not objektum.isVisible() or objektum.width() <= 0 or objektum.height() <= 0:
            continue
        pont = objektum.mapToItem(pane, QPointF(0, 0))
        bal = max(0, math.floor(pont.x()) - 4)
        felso = max(0, math.floor(pont.y()) - 4)
        jobb = min(szelesseg, math.ceil(pont.x() + objektum.width()) + 4)
        also = min(magassag, math.ceil(pont.y() + objektum.height()) + 4)
        if bal < jobb and felso < also:
            ervenyes[felso:also, bal:jobb] = False


def _folder_pane_render_megmarad(ablakmagassag_delta, qml_app, qt_app, tmp_path):
    ablak, vezerlo, _engine = qml_app
    ablak.show()
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(
            lambda: ablak.isExposed()
            and ablak.findChild(QObject, "folderPane") is not None
        ),
        10.0,
    )
    pane = ablak.findChild(QObject, "folderPane")
    assert pane is not None
    alap_ablakmagassag = ablak.height()
    alap_panelmagassag = pane.height()
    delta = ablakmagassag_delta
    ablak.resize(ablak.width(), alap_ablakmagassag + delta)
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: ablak.height() == alap_ablakmagassag + delta),
        5.0,
    )
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: pane.width() > 0 and pane.height() > 0),
        5.0,
    )

    reference_size = QImage(str(_ARANY / "ures.png"))
    assert not reference_size.isNull()
    assert abs(pane.width() - reference_size.width()) <= 3
    assert abs((pane.height() - alap_panelmagassag) - delta) <= 3

    out = Path.cwd() / ".bt" / "folder-pane-6019" / "after" / f"{delta:+d}"
    out.mkdir(parents=True, exist_ok=True)

    def pillanatkep(allapot: str) -> None:
        qt_app.processEvents()
        teljes = ablak.grabWindow()
        assert not teljes.isNull()
        bal_felso = pane.mapToScene(QPointF(0, 0))
        actual = teljes.copy(
            round(bal_felso.x()),
            round(bal_felso.y()),
            round(pane.width()),
            round(pane.height()),
        )
        assert not actual.isNull()
        assert actual.save(str(out / f"{allapot}.png"))
        reference = QImage(str(_ARANY / f"{allapot}.png"))
        assert not reference.isNull()
        width = min(actual.width(), reference.width())
        height = min(actual.height(), reference.height())
        actual_pixels = _pixelek(actual)[:height, :width]
        reference_pixels = _pixelek(reference)[:height, :width]
        ervenyes = np.ones((height, width), dtype=bool)
        _szovegteruletek_kimaszkolasa(ablak, pane, ervenyes)
        eltero = np.any(actual_pixels != reference_pixels, axis=2) & ervenyes
        assert not np.any(eltero), (
            f"{allapot}, ablakmagasság-delta={delta}: "
            f"{int(np.count_nonzero(eltero))} eltérő, szövegen kívüli képpont "
            f"az összehasonlított {width}×{height} területen"
        )

    # Az üres állapothoz nem hozunk létre lemezmappákat.
    vezerlo.folders.load_matches([])
    pillanatkep("ures")

    lib = tmp_path / "kepek"
    for dirname in ("Alfa", "Beta"):
        subdir = lib / dirname
        subdir.mkdir(parents=True)
        make_jpeg(subdir / f"{dirname.lower()}.jpg", size=(32, 24))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    vezerlo._reload_after_sync()
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: vezerlo.folders.folderCount >= 2),
        10.0,
    )
    pillanatkep("mappakkal")

    token = "604c294a68b0de9cc9222c4714f289d5"
    (lib / ".picasa.ini").write_text(
        f"[.album:{token}]\nname=Album próba\ntoken={token}\n"
        f"[a.jpg]\nalbums={token}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    vezerlo._reload_after_sync()
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(
            lambda: any(album.get("token") == token for album in vezerlo.albums)
        ),
        10.0,
    )
    pillanatkep("albummal")

    selected = str(lib / "Alfa")
    vezerlo.selectFolder(selected)
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: pane.property("selectedPath") == selected),
        5.0,
    )
    pillanatkep("kijelolt-sorral")

    pane.openFolderContextMenu(selected)
    menu = ablak.findChild(QObject, "folderContextMenu")
    assert menu is not None
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: menu.property("opened")),
        5.0,
    )
    pillanatkep("helyi-menuvel")


@pytest.mark.parametrize("ablakmagassag_delta", [-5, 0, 5])
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="a referencia Linuxon, software renderrel készül; Windowson a képpont-egyezés nem értelmezhető (#3263, #6058)",
)
def test_folder_pane_render_allapotok(ablakmagassag_delta, qml_app, qt_app, tmp_path):
    """Minden referenciaállapotot a három közeli ablakmagasságon ellenőriz."""
    _folder_pane_render_megmarad(ablakmagassag_delta, qml_app, qt_app, tmp_path)
