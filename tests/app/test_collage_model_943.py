"""#943: a kollázs-vászon csomópont-modellje (`app/collage_model.py`).

A modell a `kollazs-panel-ui-spec.md` 6.2 szerződése: a lista sorrendje a
RAJZOLÁSI sorrend (0. index legalul), a szerepek a QML `Repeater`-ének
adják a képet, a helyét, a szögét és a keretét.

A modul tiszta függvényei (kijelölés, kép-csere) Qt-vászon nélkül,
önmagukban tesztelhetők — a Qt-modell csak burkolat fölöttük.
"""

from __future__ import annotations

import math

import pytest

from picasapy.app.collage_model import (
    SHEET_UNITS,
    CollageNode,
    CollageNodeModel,
    Picture,
    initial_node_width,
    pictures_of,
    selected_indices,
    with_pictures,
    with_pictures_swapped,
    with_selection,
)
from picasapy.collage.themes import NOBORDER, POLAROID


def _node(path: str, **kwargs) -> CollageNode:
    alap = dict(center_x=512.0, center_y=512.0, width=300.0, height=200.0)
    alap.update(kwargs)
    return CollageNode(path=path, **alap)


class TestCollageNode:
    def test_alapertekek(self):
        n = _node("/a.jpg")
        assert n.theta == 0.0
        assert n.border == NOBORDER
        assert (n.caption, n.selected, n.missing) == ("", False, False)

    def test_ismeretlen_keret_hibat_dob(self):
        with pytest.raises(ValueError, match="képkeret"):
            _node("/a.jpg", border="aranykeret")

    def test_nem_pozitiv_meret_hibat_dob(self):
        with pytest.raises(ValueError, match="méret"):
            _node("/a.jpg", width=0.0)

    def test_a_csomopont_nem_irhato(self):
        """A fagyasztott adatosztály a mutáció ellen véd: a listát mindig
        ÚJRA kell építeni, így a Qt-modell mindig észreveszi a változást."""
        n = _node("/a.jpg")
        with pytest.raises(AttributeError):
            n.center_x = 1.0


class TestKezdoMeret:
    """Spec 6.2: `n<=1 → s=1`, egyébként `s = min(1, 1/sqrt(sqrt(n)-1))`,
    alapszélesség = `s * 1024 * 0,33`."""

    def test_egy_kep_a_lap_harmadat_kapja(self):
        assert initial_node_width(1) == pytest.approx(SHEET_UNITS * 0.33)

    def test_ures_kollazs_is_az_alapmeretet_adja(self):
        assert initial_node_width(0) == initial_node_width(1)

    def test_tiz_kepnel_kb_nulla_hatvannyolc_szoros(self):
        arany = initial_node_width(10) / initial_node_width(1)
        assert arany == pytest.approx(0.68, abs=0.005)

    def test_szaz_kepnel_kb_egyharmad(self):
        arany = initial_node_width(100) / initial_node_width(1)
        assert arany == pytest.approx(0.33, abs=0.005)

    def test_negy_kepig_nem_csokken(self):
        # `pile_scale` felül 1,0-ra vág — az 1–4. kép egyforma
        assert initial_node_width(4) == initial_node_width(1)


class TestTisztaFuggvenyek:
    def test_kijeloles_indexekbol(self):
        nodes = (_node("/a.jpg"), _node("/b.jpg"), _node("/c.jpg"))
        uj = with_selection(nodes, [0, 2])
        assert [n.selected for n in uj] == [True, False, True]
        assert selected_indices(uj) == (0, 2)

    def test_a_kijeloles_nem_irja_a_bemenetet(self):
        nodes = (_node("/a.jpg"),)
        with_selection(nodes, [0])
        assert nodes[0].selected is False

    def test_sávon_kivuli_index_kimarad(self):
        nodes = (_node("/a.jpg"), _node("/b.jpg"))
        uj = with_selection(nodes, [1, 7, -3])
        assert selected_indices(uj) == (1,)

    def test_kepcsere_csak_a_kepet_mozgatja(self):
        nodes = (
            _node("/a.jpg", width=300.0, theta=0.5, border=POLAROID, caption="A"),
            _node("/b.jpg", width=100.0, theta=-0.2, caption="B"),
        )
        uj = with_pictures_swapped(nodes, 0, 1)
        assert [n.path for n in uj] == ["/b.jpg", "/a.jpg"]
        assert [n.caption for n in uj] == ["B", "A"]
        # a HELY tulajdonságai a résnél maradnak
        assert (uj[0].width, uj[0].theta, uj[0].border) == (300.0, 0.5, POLAROID)
        assert (uj[1].width, uj[1].theta, uj[1].border) == (100.0, -0.2, NOBORDER)

    def test_kepek_ujraosztasa(self):
        nodes = (_node("/a.jpg"), _node("/b.jpg"))
        kepek = (Picture("/x.jpg", "X", True), Picture("/y.jpg", "Y", False))
        uj = with_pictures(nodes, kepek)
        assert [n.path for n in uj] == ["/x.jpg", "/y.jpg"]
        assert uj[0].missing is True
        assert pictures_of(uj) == kepek

    def test_eltero_hosszu_kep_lista_hibat_dob(self):
        with pytest.raises(ValueError):
            with_pictures((_node("/a.jpg"),), ())


class TestQtModell:
    def test_a_sorrend_a_rajzolasi_sorrend(self, qt_app):
        """0. index LEGALUL, az utolsó legfelül — a `canvas.py` iránya."""
        modell = CollageNodeModel()
        modell.set_nodes((_node("/also.jpg"), _node("/felso.jpg")))
        assert modell.rowCount() == 2
        assert modell.node_at(0).path == "/also.jpg"
        assert modell.nodes[-1].path == "/felso.jpg"

    def test_mind_a_tiz_szerep_kiolvashato(self, qt_app):
        modell = CollageNodeModel()
        modell.set_nodes(
            (
                _node(
                    "/a.jpg",
                    theta=math.radians(-90.0),
                    border=POLAROID,
                    caption="Nyár",
                    selected=True,
                    missing=True,
                ),
            )
        )
        nevek = {bytes(v).decode() for v in modell.roleNames().values()}
        assert nevek == {
            "path",
            "centerX",
            "centerY",
            "width",
            "height",
            "theta",
            "border",
            "caption",
            "selected",
            "missing",
        }
        index = modell.index(0, 0)
        ertek = {
            bytes(modell.roleNames()[role]).decode(): modell.data(index, role)
            for role in modell.roleNames()
        }
        assert ertek["path"] == "/a.jpg"
        assert ertek["centerX"] == 512.0
        assert ertek["centerY"] == 512.0
        assert ertek["width"] == 300.0
        assert ertek["height"] == 200.0
        assert ertek["theta"] == pytest.approx(math.radians(-90.0))
        assert ertek["border"] == POLAROID
        assert ertek["caption"] == "Nyár"
        assert ertek["selected"] is True
        assert ertek["missing"] is True

    def test_ervenytelen_index_none(self, qt_app):
        modell = CollageNodeModel()
        modell.set_nodes((_node("/a.jpg"),))
        assert modell.data(modell.index(5, 0), CollageNodeModel.PathRole) is None

    def test_azonos_hosszusagnal_nincs_reset_csak_dataChanged(self, qt_app):
        """Húzás közben a reset eldobná a delegate-eket (a `FolderListModel`
        #10-es tanulsága) — a vászon minden mozdulatnál villogna."""
        modell = CollageNodeModel()
        modell.set_nodes((_node("/a.jpg"), _node("/b.jpg")))
        resetek: list[int] = []
        valtozasok: list[int] = []
        modell.modelReset.connect(lambda: resetek.append(1))
        modell.dataChanged.connect(lambda *_: valtozasok.append(1))
        modell.set_nodes((_node("/a.jpg", center_x=10.0), _node("/b.jpg")))
        assert resetek == []
        assert valtozasok == [1]

    def test_valtozo_hosszusagnal_reset(self, qt_app):
        modell = CollageNodeModel()
        modell.set_nodes((_node("/a.jpg"),))
        resetek: list[int] = []
        modell.modelReset.connect(lambda: resetek.append(1))
        modell.set_nodes((_node("/a.jpg"), _node("/b.jpg")))
        assert resetek == [1]

    def test_azonos_tartalomnal_semmi_nem_tortenik(self, qt_app):
        modell = CollageNodeModel()
        nodes = (_node("/a.jpg"),)
        modell.set_nodes(nodes)
        jelzesek: list[str] = []
        modell.modelReset.connect(lambda: jelzesek.append("reset"))
        modell.dataChanged.connect(lambda *_: jelzesek.append("data"))
        modell.set_nodes(nodes)
        assert jelzesek == []

    def test_a_modell_nem_tartja_meg_a_lista_referenciajat(self, qt_app):
        modell = CollageNodeModel()
        lista = [_node("/a.jpg")]
        modell.set_nodes(lista)
        lista.append(_node("/b.jpg"))
        assert modell.rowCount() == 1
