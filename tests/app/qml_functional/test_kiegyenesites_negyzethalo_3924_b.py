"""#3924 — a Kiegyenesítés rácsa a valódi nézőképen, képpont szerint (2. rész).

A #4351 óta két fájl: egyben a csúcs-RSS a memóriaplafon közelébe ért. A
segédfüggvények az első részben (`test_kiegyenesites_negyzethalo_3924.py`).
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QSize, Qt
from PySide6.QtTest import QTest
import pytest

from tests.app.qml_functional.test_kiegyenesites_negyzethalo_3924 import (
    ABLAK,
    _assert_racs_csempe,
    _assert_racs_szelen,
    _assert_rgb,
    _beallit_ablak,
    _felvetel,
    _forrasok,
    _item,
    _kattint,
    _kep_kivagas_scene,
    _kep_mentese,
    _kulonbozo_pixelek,
    _nezobe_lep,
    _pont,
    _racs_mintapontok,
    _rgb,
    _vezerlo_rect,
)


def test_a_csempe_44_logikai_pixel_es_vonalai_elesek_minden_dpi_n(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """A rögzített csempe 1×, 1,5× és 2× kijelzőn is élesen rajzolódik."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, masodik_szin="black")
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app)
    area = _item(window, "viewerPhotoArea")
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    meretarany = float(window.devicePixelRatio())
    vart_arany = float(os.environ.get("QT_SCALE_FACTOR", "1"))
    assert meretarany == pytest.approx(vart_arany)
    assert meretarany >= 1

    grid_image = _item(window, "straightenGridImage")
    assert grid_image.property("sourceSize") == QSize(44, 44), (
        "a megjelenített csempét fix 44×44-es forrásméretre kell kérni"
    )

    overlay = _item(window, "straightenGridOverlay")
    overlay.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    hatterkep = _felvetel(window, tmp_path / f"racs-nelkul-{meretarany:g}x.png")
    overlay.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()
    racsos = _felvetel(window, tmp_path / f"racs-{meretarany:g}x.png")
    assert racsos.width() == round(window.width() * meretarany)
    assert racsos.height() == round(window.height() * meretarany)

    kozep = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))
    y0 = math.trunc(kozep.y() - 153)
    kep_bal, kep_fent, kep_szel, kep_mag = _kep_kivagas_scene(
        _item(window, "viewerImage")
    )
    kep_jobb = kep_bal + kep_szel
    kep_lent = kep_fent + kep_mag
    y_sor = next(
        (
            y
            for y in range(racsos.height())
            if y0 + 43 <= (y + 0.5) / meretarany < y0 + 44
        ),
        None,
    )
    assert y_sor is not None, "nem található a szürke vonal vizsgálható sora"
    elso_x = max(0, math.ceil((kep_bal + 2) * meretarany))
    utolso_x = min(racsos.width(), math.floor((kep_jobb - 2) * meretarany))
    vonalszakaszok: list[tuple[int, int]] = []
    elozo_vonal = False
    for x in range(elso_x, utolso_x):
        if not kep_fent <= (y_sor + 0.5) / meretarany < kep_lent:
            continue
        alap = _rgb(hatterkep, QPoint(x, y_sor))
        kapott = _rgb(racsos, QPoint(x, y_sor))
        if kapott != alap:
            vart = tuple(((csatorna * 128) >> 8) + 128 for csatorna in alap)
            _assert_rgb(racsos, QPoint(x, y_sor), vart)
            if elozo_vonal:
                kezdet, szel = vonalszakaszok[-1]
                vonalszakaszok[-1] = (kezdet, szel + 1)
            else:
                vonalszakaszok.append((x, 1))
            elozo_vonal = True
        else:
            elozo_vonal = False
    assert len(vonalszakaszok) >= 6, "nem látszik elég függőleges rácsvonal"
    cella = round(44 * meretarany)
    for _, szel in vonalszakaszok:
        assert math.floor(meretarany) <= szel <= math.ceil(meretarany), (
            f"az 1 logikai képpontos vonal szélessége {szel} raszterpixel"
        )
    for (x1, _), (x2, _) in zip(
        vonalszakaszok, vonalszakaszok[1:], strict=False
    ):
        assert abs((x2 - x1) - cella) <= 1, (
            f"a csempék távolsága {x2 - x1}, nem 44×{meretarany:g}"
        )


def test_nagyitas_kozben_az_eszkozsav_a_kep_aljahoz_igazodik(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller)
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    image = _item(window, "viewerImage")
    toolbar = _item(window, "editorToolBar")

    image.setProperty("scale", 1.3)
    image.setProperty("x", image.x() + 31)
    image.setProperty("y", image.y() - 17)
    for _ in range(8):
        qt_app.processEvents()

    x = (image.width() - toolbar.width()) / 2 + toolbar.width() / 2
    y = (image.height() + image.property("paintedHeight")) / 2
    y -= toolbar.height() / 2 + 10
    vart = image.mapToScene(QPointF(x, y))
    kapott = toolbar.mapToScene(QPointF(toolbar.width() / 2, toolbar.height() / 2))
    _felvetel(window, tmp_path / "racs-nagyitott-eszkozsav.png")
    assert abs(vart.x() - kapott.x()) <= 1 and abs(vart.y() - kapott.y()) <= 1, (
        "a nagyított kép elmozdult az eszközsáv alól"
    )


def test_a_racs_all_es_a_kep_fordul_a_valodi_csuszka_huzasakor(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app)
    area = _item(window, "viewerPhotoArea")
    image = _item(window, "viewerImage")
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    kezdo = _felvetel(window, tmp_path / "huzas-elott.png")
    vonalpont, arnyekpont, _, _ = _racs_mintapontok(area)
    nyitott = _felvetel(window, tmp_path / "racs-nyitva-huzas-elott.png")
    _assert_rgb(nyitott, vonalpont, (255, 128, 128))
    _assert_racs_csempe(nyitott, area, image, (255, 0, 0))

    slider = _item(window, "tiltSlider")
    apply = _item(window, "tiltApplyButton")
    cancel = _item(window, "tiltCancelButton")
    toolbar_geometria = tuple(
        (elem.width(), elem.height(), _vezerlo_rect(elem))
        for elem in (slider, apply, cancel)
    )

    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(slider, slider.width() / 2, slider.height() / 2),
    )
    QTest.mouseMove(
        window,
        _pont(slider, slider.width() * 0.78, slider.height() / 2),
        10,
    )
    for _ in range(8):
        qt_app.processEvents()
    assert slider.property("pressed") is True, "a próba nem húzás közben készült"
    assert abs(float(slider.property("value"))) >= 0.2
    huzas_kozben = _felvetel(window, tmp_path / "huzas-kozben.png")

    racs_elem = _item(window, "straightenGridOverlay")
    racs_elem.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()

    kep_a_racs_alatt = _felvetel(window, tmp_path / "fordult-kep-racs-nelkul.png")
    hatter = _rgb(kep_a_racs_alatt, vonalpont)
    vart_vonal = tuple(((csatorna * 128) >> 8) + 128 for csatorna in hatter)
    _assert_rgb(huzas_kozben, vonalpont, vart_vonal)
    alap_hatter = _rgb(kep_a_racs_alatt, arnyekpont)
    vart_arnyek = tuple((csatorna * 179) >> 8 for csatorna in alap_hatter)
    _assert_rgb(huzas_kozben, arnyekpont, vart_arnyek)

    area_scene = area.mapToScene(QPointF(0, 0))
    area_rect = QRect(
        round(area_scene.x()),
        round(area_scene.y()),
        round(area.width()),
        round(area.height()),
    )
    assert _kulonbozo_pixelek(kezdo, kep_a_racs_alatt, area_rect) > 200, (
        "a kép nem változott a Kiegyenesítés csúszkájának húzásakor"
    )

    racs_elem.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()

    racs_ujra = _felvetel(window, tmp_path / "huzas-kozben-racs.png")
    for elem, (szelesseg, magassag, rect) in zip(
        (slider, apply, cancel), toolbar_geometria, strict=True
    ):
        assert (elem.width(), elem.height(), _vezerlo_rect(elem)) == (
            szelesseg,
            magassag,
            rect,
        ), "a csúszka vagy a gomb elmozdult a rács kirajzolásakor"
    assert _kulonbozo_pixelek(
        racs_ujra, kep_a_racs_alatt, _vezerlo_rect(slider)
    ) > 0, "a csúszka sávja fölött eltűnt a Picasában látható rács"
    apply_rect = _vezerlo_rect(apply)
    cancel_rect = _vezerlo_rect(cancel)
    gombpar = QRect(
        min(apply_rect.left(), cancel_rect.left()),
        min(apply_rect.top(), cancel_rect.top()),
        max(apply_rect.right(), cancel_rect.right())
        - min(apply_rect.left(), cancel_rect.left())
        + 1,
        max(apply_rect.bottom(), cancel_rect.bottom())
        - min(apply_rect.top(), cancel_rect.top())
        + 1,
    )
    assert _kulonbozo_pixelek(racs_ujra, kep_a_racs_alatt, gombpar) == 0, (
        "a gombpár befoglaló téglalapján — a rést is beleértve — "
        "átlátszik a háló"
    )

    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(slider, slider.width() * 0.78, slider.height() / 2),
    )
    for _ in range(5):
        qt_app.processEvents()


def test_a_paratlan_meretu_kep_nem_mozditja_el_a_racsot(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, masodik_meret=1023, masodik_szin="black")
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app, index=1)
    area = _item(window, "viewerPhotoArea")
    panel = _item(window, "viewerEditorPanel")
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    assert viewer.property("currentIndex") == 1
    assert panel.property("tiltActive") is True
    kep = _felvetel(window, tmp_path / "paratlan-meretu-kep-racs.png")
    vonalpont, arnyekpont, vonal_elotti, vonal_ures = _racs_mintapontok(area)
    _assert_rgb(kep, vonalpont, (128, 128, 128))
    _assert_rgb(kep, arnyekpont, (0, 0, 0))
    _assert_rgb(kep, vonal_elotti, (0, 0, 0))
    _assert_rgb(kep, vonal_ures, (0, 0, 0))


def test_tort_illesztesu_700x467_kepen_mindket_iranyu_vonal_megjelenik(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, masodik_meret=(700, 467), masodik_szin="black")
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app, index=1)
    image = _item(window, "viewerImage")
    assert image.property("paintedHeight") % 1 != 0, (
        "a 700×467-es próbának tört illesztési magasságot kell adnia"
    )
    area = _item(window, "viewerPhotoArea")
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    racsos = _felvetel(window, tmp_path / "700x467-tort-illesztes.png")

    _assert_racs_csempe(racsos, area, image, (0, 0, 0))


def _forgatott_300x500_kepek(lib: Path) -> None:
    _kep_mentese(lib / "a.jpg", (300, 500), szin="black")
    _kep_mentese(lib / "b.jpg", (800, 600), szin="black")
    (lib / ".picasa.ini").write_text(
        "[a.jpg]\nrotate=rotate(1)\n", encoding="utf-8"
    )


@pytest.fixture
def qml_app_forgatott_kep(qt_app, tmp_path):
    from tests.app.qml_functional.conftest import _build_qml_app

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_forgatott_300x500_kepek,
    )


@pytest.mark.parametrize(
    "ablak",
    [
        pytest.param((1280, 1000), id="tort-szelen-ugyanaz-a-hiba"),
        pytest.param((1280, 1002), id="magassag-minusz-3"),
        pytest.param((1280, 1004), id="magassag-minusz-1"),
        pytest.param((1279, 1005), id="szelesseg-minusz-1"),
        pytest.param(ABLAK, id="alap"),
        pytest.param((1281, 1005), id="szelesseg-plusz-1"),
        pytest.param((1280, 1006), id="magassag-plusz-1"),
    ],
)
def test_rotate_1_300x500_kepehez_igazodik_a_negy_oldali_kivagas(
    qml_app_forgatott_kep, qt_app, tmp_path, ablak
):
    window, _controller, _ = qml_app_forgatott_kep
    _beallit_ablak(window, qt_app, ablak)
    _nezobe_lep(window, qt_app)
    image = _item(window, "viewerImage")
    assert image.property("iniSteps") == 1
    area = _item(window, "viewerPhotoArea")
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    toolbar = _item(window, "editorToolBar")
    overlay = _item(window, "straightenGridOverlay")
    area.setProperty("clip", False)
    overlay.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    racs_nelkul = _felvetel(window, tmp_path / "rotate-1-racs-nelkul.png")
    overlay.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()
    racsos = _felvetel(window, tmp_path / "rotate-1-racs.png")

    clip_x, clip_y, clip_szel, clip_mag = _kep_kivagas_scene(image)
    bal_fent = overlay.mapToScene(QPointF(0, 0))
    jobb_lent = overlay.mapToScene(QPointF(overlay.width(), overlay.height()))
    assert (math.floor(bal_fent.x()), math.floor(bal_fent.y())) == (clip_x, clip_y)
    assert (math.floor(jobb_lent.x()), math.floor(jobb_lent.y())) == (
        clip_x + clip_szel,
        clip_y + clip_mag,
    )
    _assert_racs_csempe(racsos, area, image, racs_nelkul)
    _assert_racs_szelen(racsos, racs_nelkul, area, image, toolbar)
