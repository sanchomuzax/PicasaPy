"""A képernyőkép-mérő zoom-szinkronpontjának egységtesztje (#6081)."""

from __future__ import annotations

import json

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage

from scripts import photo_viewer_screenshots as screenshot_script


class _Alkalmazas:
    def __init__(self) -> None:
        self.esemenyciklusok = 0

    def processEvents(self) -> None:
        self.esemenyciklusok += 1


class _ZoomObjektum:
    def __init__(self, alkalmazas: _Alkalmazas, ertekek: dict[str, list[float]]) -> None:
        self.alkalmazas = alkalmazas
        self.ertekek = ertekek

    def property(self, nev: str) -> float:
        mintak = self.ertekek[nev]
        index = min(self.alkalmazas.esemenyciklusok - 1, len(mintak) - 1)
        return mintak[index]


class _QtMeta:
    def __init__(self, nev: str, tulajdonsagok: dict[str, object]) -> None:
        self.nev = nev
        self.tulajdonsagok = tulajdonsagok

    def className(self) -> str:
        return self.nev

    def indexOfProperty(self, nev: str) -> int:
        return 0 if nev in self.tulajdonsagok else -1


class _QmlRajzElem:
    def __init__(
        self,
        nev: str,
        tulajdonsagok: dict[str, object],
        gyerekek: list[_QmlRajzElem] | None = None,
    ) -> None:
        self.tulajdonsagok = tulajdonsagok
        self.gyerekek = gyerekek or []
        self._meta = _QtMeta(nev, tulajdonsagok)

    def metaObject(self) -> _QtMeta:
        return self._meta

    def property(self, nev: str) -> object:
        return self.tulajdonsagok[nev]

    def findChildren(self, _tipus: type) -> list[_QmlRajzElem]:
        return [
            gyerek
            for elem in self.gyerekek
            for gyerek in (elem, *elem.findChildren(_tipus))
        ]


def test_csuszka_festesi_allapota_tartalmazza_a_szineket_es_a_megjelenesi_allapotot() -> None:
    """#6078: a képponteltérésnél a fogantyú festési állapota is legyen mérhető."""
    gradient_stop = _QmlRajzElem(
        "QQuickGradientStop", {"color": QColor("#f5f5f5")}
    )
    border = _QmlRajzElem(
        "QQuickPen", {"width": 1.0, "color": QColor("#b5b5b5")}
    )
    rectangle = _QmlRajzElem(
        "QQuickRectangle",
        {"color": QColor("#f5f5f5"), "opacity": 0.75, "width": 14.0},
    )
    handle = _QmlRajzElem(
        "QQuickItem",
        {"x": 4.0, "y": 2.0, "width": 16.0, "height": 22.0, "opacity": 0.75},
        [rectangle, gradient_stop, border],
    )
    slider = _QmlRajzElem(
        "PicasaSlider",
        {
            "handle": handle,
            "enabled": False,
            "pressed": False,
            "hovered": False,
            "activeFocus": False,
            "value": 0.0,
            "visualPosition": 0.0,
            "opacity": 1.0,
        },
    )

    allapot = screenshot_script._csuszka_festesi_allapota(slider)

    assert allapot["slider"] == {
        "enabled": False,
        "pressed": False,
        "hovered": False,
        "activeFocus": False,
        "value": 0.0,
        "visualPosition": 0.0,
        "opacity": 1.0,
    }
    assert allapot["handle"]["opacity"] == 0.75
    assert allapot["handle"]["x"] == 4.0
    festesek = {elem["type"]: elem["properties"] for elem in allapot["layers"]}
    assert festesek["QQuickGradientStop"]["color"] == "#fff5f5f5"
    assert festesek["QQuickPen"] == {"width": 1.0, "color": "#ffb5b5b5"}
    assert festesek["QQuickRectangle"]["opacity"] == 0.75


class _RacsElem:
    def __init__(
        self,
        alkalmazas: _Alkalmazas,
        nev: str,
        ertekek: dict[str, list[object] | object],
        gyerekek: list[_RacsElem] | None = None,
    ) -> None:
        self.alkalmazas = alkalmazas
        self.nev = nev
        self.ertekek = ertekek
        self.gyerekek = gyerekek or []

    def objectName(self) -> str:
        return self.nev

    def childItems(self) -> list[_RacsElem]:
        return self.gyerekek

    def isVisible(self) -> bool:
        return True

    def property(self, nev: str) -> object:
        ertek = self.ertekek[nev]
        if isinstance(ertek, list):
            index = min(self.alkalmazas.esemenyciklusok - 1, len(ertek) - 1)
            return ertek[index]
        return ertek

    def mapToItem(self, _cel: _RacsElem, _pont: QPointF) -> QPointF:
        return QPointF(float(self.property("x")), float(self.property("y")))


def test_splitter_allapot_elott_megvarja_a_stabil_layoutot_es_kesz_racskepeket() -> None:
    alkalmazas = _Alkalmazas()
    split = _RacsElem(
        alkalmazas,
        "mainSplit",
        {"x": 0.0, "y": 40.0, "width": 1024.0, "height": 660.0},
    )
    pane = _RacsElem(
        alkalmazas,
        "folderPane",
        {
            "x": 0.0,
            "y": 40.0,
            "width": [300.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0],
            "height": 660.0,
        },
    )
    image = _RacsElem(
        alkalmazas,
        "thumbImage",
        {
            "x": 36.0,
            "y": 100.0,
            "width": 128.0,
            "height": 128.0,
            "paintedWidth": [0.0, 0.0, 0.0, 0.0, 128.0, 128.0, 128.0],
            "paintedHeight": [0.0, 0.0, 0.0, 0.0, 80.0, 80.0, 80.0],
            "source": "image://thumbs/1",
        },
    )
    grid = _RacsElem(
        alkalmazas,
        "photoGrid",
        {
            "x": [300.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0],
            "y": 40.0,
            "width": [724.0, 784.0, 784.0, 784.0, 784.0, 784.0, 784.0],
            "height": 660.0,
            "contentY": 0.0,
            "contentHeight": 660.0,
            "count": 2,
        },
        [image],
    )

    screenshot_script._var_foablak_racsra(
        alkalmazas, "mainSplit-min", split, pane, grid
    )

    assert alkalmazas.esemenyciklusok >= 7


def test_compare_pixelhiba_eseten_kiirja_a_ket_csuszka_festesi_allapotot(
    tmp_path, capsys
) -> None:
    before = tmp_path / "elotte"
    after = tmp_path / "utana"
    before.mkdir()
    after.mkdir()

    for folder, image_color, handle_color in (
        (before, "#202020", "#f5f5f5"),
        (after, "#303030", "#d3d3d3"),
    ):
        image = QImage(2, 2, QImage.Format.Format_RGBA8888)
        image.fill(QColor(image_color))
        assert image.save(str(folder / "teljes-kepernyo.png"))
        manifest = {
            "states": [
                {
                    "name": "teljes-kepernyo",
                    "file": "teljes-kepernyo.png",
                    "viewer_geometry": {
                        "zoomSlider": {
                            "paint_state": {
                                "slider": {"pressed": False, "hovered": False},
                                "handle": {"opacity": 1.0},
                                "layers": [
                                    {
                                        "type": "QQuickGradientStop",
                                        "properties": {"color": QColor(handle_color).name(
                                            QColor.NameFormat.HexArgb
                                        )},
                                    },
                                    {
                                        "type": "QQuickPen",
                                        "properties": {"width": 1.0, "color": "#ffb5b5b5"},
                                    },
                                ],
                            }
                        }
                    },
                }
            ]
        }
        (folder / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    result = screenshot_script.compare(before, after, tmp_path / "kulonbseg")

    assert result == 1
    kimenet = capsys.readouterr().out
    assert "zoomSlider festési állapotok" in kimenet
    assert "#fff5f5f5" in kimenet
    assert "#ffd3d3d3" in kimenet


def test_var_illesztett_nagyitasra_megvarja_a_kotott_csuszka_stabilizalodasat() -> None:
    alkalmazas = _Alkalmazas()
    viewer = _ZoomObjektum(alkalmazas, {"zoomValue": [0.0] * 5})
    slider = _ZoomObjektum(
        alkalmazas,
        {
            "value": [0.25, 0.25, 0.0, 0.0, 0.0],
            "visualPosition": [0.25, 0.25, 0.0, 0.0, 0.0],
        },
    )

    eredmeny = screenshot_script._var_illesztett_nagyitasra(
        alkalmazas, viewer, slider, "teljes-kepernyo"
    )

    assert eredmeny == (0.0, 0.0, 0.0)
    assert alkalmazas.esemenyciklusok == 5


def test_var_illesztett_nagyitasra_jelzi_a_nem_illesztett_erteket() -> None:
    alkalmazas = _Alkalmazas()
    viewer = _ZoomObjektum(alkalmazas, {"zoomValue": [0.1] * 3})
    slider = _ZoomObjektum(
        alkalmazas,
        {"value": [0.1] * 3, "visualPosition": [0.1] * 3},
    )

    with pytest.raises(RuntimeError, match="nem illesztett nagyítás"):
        screenshot_script._var_illesztett_nagyitasra(
            alkalmazas, viewer, slider, "teljes-kepernyo"
        )
