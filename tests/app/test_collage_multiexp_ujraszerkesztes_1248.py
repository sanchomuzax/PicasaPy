"""A Többszörös exponálás kollázsa ÚJRASZERKESZTHETŐ (#1248).

## A tulajdonos jelentése (v0.8.45, Windows)

> „A Képkollázs funkcióban létrehozott »Többszörös exponálás…« funkció
> működik. Azonban a kollázs újraszerkesztésekor fekete a lap, és ha a
> »Bezárás« funkcióval el akarom menteni, akkor jelzi is, hogy azért nem,
> mert az összes képet eltávolították. Ami tévedés."

A jegy UNC-útvonalra gyanakodott (`\\\\DS215j\\lemez\\My Pictures\\…`). A
beküldött minta (`AI15.cxf`) ezt **cáfolta**: a háttér `src`-je szabályos
`$My Pictures\\…` kódolt alak, tehát a kódolás/feloldás rendben van. Ami
hiányzott: a fájlban **egyetlen `<node>` sem** volt.

Az eredeti Picasa írja őket — mérve a `referencia/kollazs-golden/AI7.cxf`
mintán: képenként EGY csomópont, mind teljes lapos
(`x=0 y=0 w=1 h=1 theta=0 scale=1`, `noborder`).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.app.collage_output import render_collage, render_settings
from picasapy.collage.cxf import loads
from picasapy.collage.draft import nodes_from_project
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.themes import MULTIEXP, NOBORDER


@pytest.fixture
def kepek(tmp_path):
    utak = []
    for i in range(3):
        kep = np.full((40 + i * 7, 60 + i * 11, 3), 40 * (i + 1), dtype=np.uint8)
        ut = tmp_path / f"kep{i}.png"
        cv2.imwrite(str(ut), kep)
        utak.append(ut)
    return utak


def _beallitas():
    """A panel állapotának megfelelő renderelő-beállítás, `multiexp`-re."""
    return render_settings(
        theme=MULTIEXP,
        border=NOBORDER,
        spacing=0.0,
        shadows=False,
        page_ratio=0.75,
        background_rgb=(255, 255, 255),
        frame_center=-1,
        seed=1,
        width=400,
    )


def _vaszon_csomopontok(utak, magassag_arany=0.75):
    """A vászon csomópontjai — a `multiexp` felületén is van geometria."""
    lap_magassag = SHEET_UNITS * magassag_arany
    return tuple(
        CollageNode(
            path=str(ut),
            center_x=SHEET_UNITS / 2.0,
            center_y=lap_magassag / 2.0,
            width=SHEET_UNITS,
            height=lap_magassag,
            border=NOBORDER,
        )
        for ut in utak
    )


class TestMultiexpPiszkozat:
    def test_a_mentett_cxf_minden_kepet_felsorol(self, tmp_path, kepek):
        beallitas = _beallitas()
        cel = tmp_path / "ki" / "kollazs.jpg"

        eredmeny = render_collage(_vaszon_csomopontok(kepek), beallitas, cel)

        assert eredmeny.path is not None
        projekt = loads(cel.with_suffix(".cxf").read_bytes())
        assert len(projekt.nodes) == len(kepek), (
            "a .cxf nem tudja, melyik képekből készült a kollázs — "
            "újraszerkesztéskor fekete lap lesz belőle"
        )

    def test_az_ujraszerkesztes_ugyanazokat_a_kepeket_kapja_vissza(
        self, tmp_path, kepek
    ):
        beallitas = _beallitas()
        cel = tmp_path / "ki" / "kollazs.jpg"
        render_collage(_vaszon_csomopontok(kepek), beallitas, cel)

        vissza = nodes_from_project(loads(cel.with_suffix(".cxf").read_bytes()))

        assert [Path(n.path) for n in vissza] == [Path(u) for u in kepek]

    def test_a_csomopont_alakja_az_AI7_mintat_koveti(self, tmp_path, kepek):
        beallitas = _beallitas()
        cel = tmp_path / "ki" / "kollazs.jpg"
        render_collage(_vaszon_csomopontok(kepek), beallitas, cel)

        projekt = loads(cel.with_suffix(".cxf").read_bytes())

        # ⚠️ enélkül a teszt ÜRES listán is zöld volna — pontosan azon az
        # állapoton, amit meg kell fognia
        assert len(projekt.nodes) == len(kepek)
        for csomopont in projekt.nodes:
            assert (csomopont.x, csomopont.y, csomopont.w, csomopont.h) == (
                0.0,
                0.0,
                1.0,
                1.0,
            )
            assert (csomopont.theta, csomopont.scale) == (0.0, 1.0)
            assert csomopont.theme == NOBORDER
