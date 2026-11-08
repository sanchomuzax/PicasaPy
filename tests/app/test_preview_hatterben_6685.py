"""#6685: az előnézeti láncok a felület szála helyett háttérben futnak."""

from __future__ import annotations

import sys
import threading
from dataclasses import replace

import pytest

from picasapy.ini.filters import FilterOp


_LASSU_MINTAK = (
    "radblur",
    "LocalContrast",
    "Pixelate",
    "finetune2",
    "autocolor",
    "TwoTone",
    "sat",
    "dir_brite",
    "tilt",
)


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from tests.support.jpeg_factory import make_jpeg

    photo = make_jpeg(tmp_path / "IMG_1.jpg", size=(64, 48))
    controller = EditController(EditPreviewProvider())
    controller.beginEdit("1", str(photo))
    yield controller
    controller.cancelPendingPreview()
    assert controller.waitForBackgroundWorkers(10.0)


@pytest.mark.parametrize("filter_name", _LASSU_MINTAK)
def test_elonezeti_lanc_mindig_hatterbe_megy(vezerlo, monkeypatch, filter_name):
    """Egyik szűrő sem kap nevére épülő szinkron kivételt."""
    provider = vezerlo._provider
    hivo_szal = threading.current_thread()
    hivott_szala = []
    elindult = threading.Event()

    def register(**_request):
        hivott_szala.append(threading.current_thread())
        elindult.set()

    monkeypatch.setattr(provider, "register", register)
    vezerlo._session = replace(
        vezerlo._session,
        ops=(FilterOp(filter_name, ()),),
    )

    vezerlo._register_preview()

    assert elindult.wait(3.0), f"nem indult render: {filter_name}"
    assert hivott_szala[0] is not hivo_szal, (
        f"{filter_name} előnézete a felület szálán futott"
    )
    assert vezerlo.waitForBackgroundWorkers(3.0)


def test_a_gyors_elonezeti_kontextus_atkerul_a_hatterbe(vezerlo, monkeypatch):
    """A csúszka alatti gyorsított render háttérszálon is megőrzi a mintát."""
    from picasapy.render.elonezeti_arany import gyors_elonezet, gyors_elonezet_aktiv

    provider = vezerlo._provider
    hivo_szal = threading.current_thread()
    eredmeny = []
    elkeszult = threading.Event()

    def register(**_request):
        eredmeny.append((threading.current_thread(), gyors_elonezet_aktiv()))
        elkeszult.set()

    monkeypatch.setattr(provider, "register", register)
    with gyors_elonezet():
        vezerlo._register_preview()

    assert elkeszult.wait(3.0), "az előnézeti render nem futott le"
    assert eredmeny == [(eredmeny[0][0], True)]
    assert eredmeny[0][0] is not hivo_szal
    assert vezerlo.waitForBackgroundWorkers(3.0)


def test_render_kozben_a_gui_gil_idot_kap_es_visszaall(vezerlo, monkeypatch):
    """A CPU-s worker sűrűbben ad GIL-t a felület szálának, majd visszaállít."""
    assert vezerlo.waitForBackgroundWorkers(10.0)
    provider = vezerlo._provider
    eredeti_idokoz = sys.getswitchinterval()
    worker_idokoz = []
    elkeszult = threading.Event()

    def register(**_request):
        worker_idokoz.append(sys.getswitchinterval())
        elkeszult.set()

    monkeypatch.setattr(provider, "register", register)
    vezerlo._register_preview()

    assert elkeszult.wait(3.0), "az előnézeti render nem indult el"
    assert worker_idokoz == [min(eredeti_idokoz, 0.001)]
    assert vezerlo.waitForBackgroundWorkers(3.0)
    assert sys.getswitchinterval() == eredeti_idokoz
