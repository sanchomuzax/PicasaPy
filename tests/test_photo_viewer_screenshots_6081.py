"""A képernyőkép-mérő zoom-szinkronpontjának egységtesztje (#6081)."""

from __future__ import annotations

import pytest

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
