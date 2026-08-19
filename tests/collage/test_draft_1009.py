"""A háttérkép átvezetése a vászonról a `.cxf`-be (#1009).

A `project_from_nodes` eddig MINDEN kollázsnak egyszínű hátteret írt, mert
a vezérlő nem is tudott képhátteret választani. A #1009 óta tud — és ha a
projektfájl ezt nem viszi át, a piszkozat visszatöltve más kollázst ad,
mint amit a felhasználó mentett.
"""

from __future__ import annotations

from picasapy.collage.draft import nodes_from_project, project_from_nodes
from picasapy.collage.nodes import CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import PICTUREPILE


def _beallitas() -> PicasaCollageSettings:
    return PicasaCollageSettings(
        theme=PICTUREPILE, width=1600, height=1200, background=(255, 255, 255)
    )


def _vaszon() -> list[CollageNode]:
    return [
        CollageNode(path="/képek/a.jpg", width=100.0, height=80.0),
        CollageNode(path="/képek/b.jpg", width=100.0, height=80.0),
    ]


def test_a_hatterkep_kimegy_a_projektbe():
    projekt = project_from_nodes(
        _vaszon(), _beallitas(), background_image="/képek/a.jpg"
    )
    assert projekt.background.type == "image"
    assert projekt.background.src == "/képek/a.jpg"


def test_hatterkep_nelkul_egyszinu_marad():
    """A #431 alapesete: ami eddig egyszínű volt, az marad az."""
    projekt = project_from_nodes(_vaszon(), _beallitas())
    assert projekt.background.type == "solid"
    assert projekt.background.src == ""
    assert projekt.background.color == "FFFFFFFF"


def test_a_hatterkep_a_kollazs_sajat_kepe():
    """A háttér a csomópontok EGYIKE (`0x00830a00`: indexszel hivatkozik)."""
    projekt = project_from_nodes(
        _vaszon(), _beallitas(), background_image="/képek/a.jpg"
    )
    assert projekt.background.src in [csomopont.src for csomopont in projekt.nodes]


def test_a_kephatter_nem_bantja_a_csomopontok_visszaallitasat():
    csomopontok = nodes_from_project(
        project_from_nodes(_vaszon(), _beallitas(), background_image="/képek/a.jpg")
    )
    assert [csomopont.path for csomopont in csomopontok] == [
        "/képek/a.jpg",
        "/képek/b.jpg",
    ]
