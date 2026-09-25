"""#3503 — a kiadás-panel Ajándék-CD üzemmódjának MŰKÖDŐ vezérlői.

## A mérés (`respack.yt` rétegfejlécek, 1024 × 212-es vászon)

| elem | hely | méret | felirat (`publish_text.tre`) |
|---|---|---|---|
| `publish/giftcdtext` | 35,74 | 271 × 51 | „The items selected with a checkmark above…" |
| `publish/addmore` | 35,130 | 88 × 28 | „Add More..." |
| `publish/picsizemenu` | 177,168 | 129 × 21 | a négy `CPublishSizeList` fokozat |
| `publish/presentcd_go` | 664,37 | 98 × 28 | „Burn Disc" |
| `publish/presentcd_cancel` | 664,111 | 98 × 28 | „Cancel" |

A gombokat VALÓDI egérrel nyomjuk meg (`QTest.mouseClick` a jelenet
koordinátáján) — a metódushívás nem bizonyítaná, hogy a gomb a helyén van
és kattintható.

Amit ez a fájl NEM mér: a lemezkép tartalmát (`tests/burn/...`) és a gazda
bekötését (`test_ajandek_cd_bekotes_3503.py`).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

import picasapy.app.application as app_module

_KEEP_ALIVE: list = []

MERT_GEOMETRIA = {
    "publishGiftCdText": (35, 74, 271, 51),
    "publishAddMore": (35, 130, 88, 28),
    "publishPicSizeMenu": (177, 168, 129, 21),
    "publishPresentCdGo": (664, 37, 98, 28),
    "publishPresentCdCancel": (664, 111, 98, 28),
}


def _ablak(engine, elemek: int = 3):
    """A panel egy saját ablakban — a valódi kattintáshoz jelenet kell."""
    url = QUrl.fromLocalFile(
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "PublishPanel.qml")
    ).toString()
    qml = f"""import QtQuick
import QtQuick.Window
Window {{
    width: 1024; height: 212; visible: true
    property alias panel: betolto.item
    Loader {{ id: betolto; source: "{url}" }}
}}"""
    comp = QQmlComponent(engine)
    comp.setData(qml.encode(), QUrl())
    ablak = comp.create()
    assert comp.errors() == [], comp.errors()
    _KEEP_ALIVE.extend([comp, ablak])
    panel = ablak.property("panel")
    assert panel is not None
    panel.setProperty("elemekSzama", elemek)
    return ablak, panel


def _elem(panel, nev):
    elem = panel.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(ablak, elem):
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )


class TestAMertHely:
    @pytest.mark.parametrize("nev", sorted(MERT_GEOMETRIA))
    def test_kepontra_a_mert_ertek(self, qml_app, nev):
        _, _, engine = qml_app
        _, panel = _ablak(engine)

        elem = _elem(panel, nev)

        assert tuple(
            elem.property(t) for t in ("x", "y", "width", "height")
        ) == MERT_GEOMETRIA[nev]


class TestFeliratok:
    def test_a_gombok_mert_feliratai(self, qml_app):
        _, _, engine = qml_app
        _, panel = _ablak(engine)

        assert _elem(panel, "publishPresentCdGo").property("text") == "Burn Disc"
        assert _elem(panel, "publishPresentCdCancel").property("text") == "Cancel"
        assert _elem(panel, "publishAddMore").property("text") == "Add More..."

    def test_a_negy_meretfokozat(self, qml_app):
        _, _, engine = qml_app
        _, panel = _ablak(engine)

        menu = _elem(panel, "publishPicSizeMenu")

        assert menu.property("count") == 4
        assert menu.property("currentIndex") == 0
        assert menu.property("currentText") == "Original Size"


class TestAKattintas:
    def test_a_lemezre_iras_a_valasztott_meretet_es_nevet_adja(self, qml_app):
        _, _, engine = qml_app
        ablak, panel = _ablak(engine)
        _elem(panel, "publishPicSizeMenu").setProperty("currentIndex", 2)
        _elem(panel, "publishCdName").setProperty("text", "Család")
        kaptunk = []
        panel.lemezreIrasKert.connect(lambda i, n: kaptunk.append((i, n)))

        _kattints(ablak, _elem(panel, "publishPresentCdGo"))

        assert kaptunk == [(2, "Család")]

    def test_ures_talcanal_a_lemezre_iras_nem_nyomhato(self, qml_app):
        _, _, engine = qml_app
        ablak, panel = _ablak(engine, elemek=0)
        kaptunk = []
        panel.lemezreIrasKert.connect(lambda i, n: kaptunk.append((i, n)))

        _kattints(ablak, _elem(panel, "publishPresentCdGo"))

        assert kaptunk == []

    def test_iras_kozben_nem_nyomhato_ujra(self, qml_app):
        _, _, engine = qml_app
        ablak, panel = _ablak(engine)
        panel.setProperty("dolgozik", True)
        kaptunk = []
        panel.lemezreIrasKert.connect(lambda i, n: kaptunk.append((i, n)))

        _kattints(ablak, _elem(panel, "publishPresentCdGo"))

        assert kaptunk == []

    @pytest.mark.parametrize(
        "nev,jel",
        [("publishPresentCdCancel", "megseKert"),
         ("publishAddMore", "tovabbiakKert")],
    )
    def test_a_visszalepo_gombok_jeleznek(self, qml_app, nev, jel):
        _, _, engine = qml_app
        ablak, panel = _ablak(engine)
        kaptunk = []
        getattr(panel, jel).connect(lambda: kaptunk.append(1))

        _kattints(ablak, _elem(panel, nev))

        assert kaptunk == [1]
