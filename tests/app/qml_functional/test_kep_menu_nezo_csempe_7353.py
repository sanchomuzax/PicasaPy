"""A Kép menü effektjei a nézőben a hozzájuk tartozó csempét jelölik (#7353)."""

from __future__ import annotations

import pytest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    gyerek,
    kijelol,
    szures,
    tetel_kattintasa,
    varj,
)

_BATCH = ("menuPictureBatchEdit",)

# Menütétel, filters-kulcs/vezérlőazonosító, fül, csempe.
_EFFEKTEK = (
    ("menuBatchAutoContrast", "autolight", 0, "editToolAutolight"),
    ("menuBatchAutoColor", "autocolor", 0, "editToolAutocolor"),
    ("menuBatchEnhance", "enhance", 0, "editToolEnhance"),
    ("menuBatchSepia", "sepia", 2, "effectSepia"),
    ("menuBatchSharpen", "unsharp", 2, "effectUnsharp"),
    ("menuBatchWarmify", "warm", 2, "effectWarm"),
    ("menuBatchFilmGrain", "grain2", 2, "effectGrain2"),
    ("menuBatchBlackWhite", "bw", 2, "effectBw"),
)


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def test_nezoben_a_kep_menu_a_celcsempehez_navigal_koteghatas_nelkul(
    kep_app, qt_app
):
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)

    viewer = gyerek(window, "photoViewer")
    panel = gyerek(window, "viewerEditorPanel")
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 1)
    qt_app.processEvents()

    alap_lancok = [szures(controller, sor) for sor in range(3)]
    alap_magassag = window.height()

    for index, (tetel, _kulcs, ful, celcsempe) in enumerate(_EFFEKTEK):
        # Mindkét kijelölési mód megmarad, miközben a néző a kijelöléstől
        # különböző, második képet mutat. A három magasság a menükattintást is
        # ellenőrzi platformfüggetlen geometriával.
        sorok = [0] if index % 2 == 0 else [0, 1]
        window.resize(window.width(), alap_magassag + (-5, 0, 5)[index % 3])
        kijelol(window, qt_app, sorok)
        viewer.setProperty("currentIndex", 1)
        panel.setProperty("activeTab", 2 if ful == 0 else 0)
        qt_app.processEvents()

        tetel_kattintasa(
            window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH
        )

        cel = gyerek(window, celcsempe)
        assert varj(
            qt_app,
            lambda ful=ful, cel=cel: panel.property("activeTab") == ful
            and cel.isVisible()
            and cel.property("active") is True,
        ), (
            f"a {tetel} nem a megfelelő csempét jelölte ki "
            f"(fül={panel.property('activeTab')}, csempe={celcsempe})"
        )
        for _masik_tetel, _masik_kulcs, _masik_ful, masik_csempe in _EFFEKTEK:
            if masik_csempe != celcsempe:
                assert gyerek(window, masik_csempe).property("active") is False, (
                    f"a {tetel} mellett a {masik_csempe} is kijelölt maradt"
                )

        assert window.property("viewerOpen") is True
        assert viewer.property("currentIndex") == 1
        assert window.property("selectedIndex") == sorok[0]
        assert list(window.property("selectedIndexes")) == sorok
        assert [szures(controller, sor) for sor in range(3)] == alap_lancok, (
            f"a nézőben a {tetel} módosította valamelyik filters= láncot"
        )
        assert controller.batchEditActive is False
        assert controller.canUndoBatchEdit is False

