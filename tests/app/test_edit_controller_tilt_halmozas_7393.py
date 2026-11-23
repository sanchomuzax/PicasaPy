"""#7393: a Kiegyenesítés halmoz - újranyitáskor a csúszka 0-ról indul, az Apply
új `tilt` tagot fűz a lánc végére, és a render-lánc a két tagot sorban alkalmazza.

Felvétel: job-913 (`__16`: újranyitás, `__18`: a második húzás). A záró
eredeti-mappa ini: `filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;`.
"""

from __future__ import annotations

import numpy as np
import pytest

from support.jpeg_factory import make_jpeg

ELSO = 0.391249
MASODIK = -0.399233


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _ini_lanc(photo) -> str:
    szoveg = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
    for sor in szoveg.splitlines():
        if sor.startswith("filters="):
            return sor
    return ""


def test_a_masodik_alkalmaz_uj_tilt_tagot_fuz_a_lanc_vegere(controller, photo) -> None:
    controller.beginEdit("1", str(photo))

    controller.setTilt(ELSO)
    controller.setTilt(MASODIK)

    assert _ini_lanc(photo) == (
        "filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;"
    )


def test_az_alkalmaz_a_nem_tilt_tagok_utan_a_lanc_vegere_fuz(controller, photo) -> None:
    controller.beginEdit("1", str(photo))
    controller.setTilt(ELSO)
    controller.toggleTool("autocolor")

    controller.setTilt(MASODIK)

    nevek = [resz.split("=")[0] for resz in _ini_lanc(photo)[len("filters="):].split(";") if resz]
    assert nevek == ["tilt", "autocolor", "tilt"]


def test_minden_alkalmaz_egy_visszavonas_lepes(controller, photo) -> None:
    controller.beginEdit("1", str(photo))
    controller.setTilt(ELSO)
    controller.setTilt(MASODIK)

    controller.undo()

    assert _ini_lanc(photo) == "filters=tilt=1,0.391249,0.000000;"


def test_az_elonezet_a_mentett_lanc_vegere_fuz_es_nem_cserel(
    controller, provider, photo, qt_app
) -> None:
    """A húzás közbeni előnézet = a már alkalmazott lánc + az új tilt (#7393):
    a mentett tilt tag a képben marad, az ini és a munkamenet érintetlen."""
    controller.beginEdit("1", str(photo))
    controller.setTilt(ELSO)
    ini_elotte = _ini_lanc(photo)
    lanc_elotte = controller._session.ops

    controller.previewTilt(MASODIK)

    assert controller.waitForBackgroundWorkers(10.0)
    assert _ini_lanc(photo) == ini_elotte
    assert controller._session.ops == lanc_elotte
    assert controller.canUndo is True
    assert controller.undoAction == "tilt"
    assert not provider.requestImage("1", None, None).isNull()


def test_az_elonezet_munkamenete_ket_tilt_tagot_tartalmaz(
    controller, photo, monkeypatch
) -> None:
    lathatott = []
    eredeti = controller._register_preview

    def kem(session=None):
        lathatott.append(session)
        return eredeti(session) if session is not None else eredeti()

    monkeypatch.setattr(controller, "_register_preview", kem)
    controller.beginEdit("1", str(photo))
    controller.setTilt(ELSO)
    lathatott.clear()

    controller.previewTilt(MASODIK)

    elonezet = [s for s in lathatott if s is not None][-1]
    assert [op.params[1] for op in elonezet.ops if op.name == "tilt"] == [
        f"{ELSO:.6f}",
        f"{MASODIK:.6f}",
    ]


def test_a_render_lanc_a_ket_tilt_tagot_sorban_alkalmazza() -> None:
    """`tilt;tilt` = az első tilt képén a második: a két forgatás NEM olvad
    össze, és egyik sem marad ki (a lánc `_HANDLERS`-e minden tagot lefuttat)."""
    from picasapy.ini.filters import parse_filters
    from picasapy.render.chain import apply_filters
    from picasapy.render.ops import apply_tilt

    kep = np.tile(np.linspace(0, 255, 256, dtype=np.uint8), (64, 1))[:, :, None]
    kep = np.repeat(kep, 3, axis=2)
    szog = 0.2  # radián / Picasa-egység (a lánc `_TILT_RADIANS_PER_UNIT`)

    lanc_kep, kihagyott = apply_filters(
        kep, parse_filters(f"tilt=1,{ELSO:.6f},0.000000;tilt=1,{MASODIK:.6f},0.000000;")
    )

    varhato = apply_tilt(apply_tilt(kep, ELSO * szog), MASODIK * szog)
    csak_az_elso = apply_tilt(kep, ELSO * szog)
    assert not kihagyott
    assert np.array_equal(np.asarray(lanc_kep), varhato)
    assert not np.array_equal(varhato, csak_az_elso)
