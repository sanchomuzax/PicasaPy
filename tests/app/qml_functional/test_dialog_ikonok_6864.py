"""A másolási Info és a Picasa eltávolítási megerősítő saját ikonjai (#6864)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    gyerek,
    kijelol,
    tetel_kattintasa,
    varj,
    zar,
)


@pytest.fixture
def dialog_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _ablakmagassag(window, qt_app, eltolás: int) -> None:
    cel = int(window.height()) + eltolás
    window.setProperty("height", cel)
    assert varj(qt_app, lambda: int(window.height()) == cel), (
        f"az ablakmagasság nem állt be {cel} képpontra"
    )


def _ikon_pixelei(window, ikon: QQuickItem) -> list[QColor]:
    kep = window.grabWindow()
    assert not kep.isNull(), "a főablakról nem készült képkocka"
    pont = ikon.mapToScene(QPointF(0, 0))
    bal, felso = round(pont.x()), round(pont.y())
    szelesseg, magassag = round(ikon.width()), round(ikon.height())
    assert szelesseg > 0 and magassag > 0, "az ikon területe üres"
    return [
        kep.pixelColor(x, y)
        for y in range(felso, felso + magassag)
        for x in range(bal, bal + szelesseg)
    ]


def _ikon_es_szoveg_melletti(
    window, qt_app, prefix: str, ikon_tipus: str, szoveg_nev: str | None = None
) -> None:
    parbeszed = gyerek(window, prefix + "Dialog")
    assert varj(qt_app, lambda: parbeszed.property("visible") is True), (
        f"a(z) {prefix} párbeszéd nem látható"
    )
    ikon = gyerek(window, prefix + "Icon")
    szoveg = gyerek(window, szoveg_nev or prefix + "MessageLabel")
    assert isinstance(ikon, QQuickItem)
    assert isinstance(szoveg, QQuickItem)
    assert parbeszed.property("iconType") == ikon_tipus
    assert varj(qt_app, lambda: float(ikon.property("paintedWidth") or 0) > 0), (
        f"a(z) {prefix} ikon nem rajzolódott ki"
    )

    ikon_pont = ikon.mapToScene(QPointF(0, 0))
    szoveg_pont = szoveg.mapToScene(QPointF(0, 0))
    assert szoveg_pont.x() >= ikon_pont.x() + ikon.width() - 3, (
        "az üzenet szövege nem az ikon mellett áll"
    )
    assert abs(
        (szoveg_pont.y() + szoveg.height() / 2)
        - (ikon_pont.y() + ikon.height() / 2)
    ) <= 2, "az ikon és az üzenet függőleges középvonala eltér"

    # A képi ellenőrzés kizárólag az ikont vágja ki; a platformfüggő betűk
    # egyetlen képpontja sem kerül a mérésbe.
    szines = [p for p in _ikon_pixelei(window, ikon) if p.alpha() > 0]
    if ikon_tipus == "info":
        kekek = [p for p in szines if p.blue() > p.red() + 30]
        assert len(kekek) >= 20, "a kék információikon nem látszik a képkockán"
    else:
        szinek = {
            "piros-narancs": lambda p: p.red() > 150 and 55 < p.green() < 190 and p.blue() < 110,
            "zöld": lambda p: p.green() > 130 and p.red() < 130 and p.blue() < 150,
            "kék": lambda p: p.blue() > 130 and p.red() < 150 and p.green() < 190,
            "lila": lambda p: p.red() > 130 and p.blue() > 130 and p.green() < 150,
            "cián": lambda p: p.green() > 130 and p.blue() > 130 and p.red() < 150,
            "sárga": lambda p: p.red() > 150 and p.green() > 130 and p.blue() < 130,
        }
        látható = {nev for nev, feltétel in szinek.items() if any(feltétel(p) for p in szines)}
        assert len(látható) >= 5, (
            f"a saját Picasa-logó színei nem látszanak a képkockán: {látható}"
        )


@pytest.mark.parametrize("eltolás", (-5, 0, 5))
def test_tobb_kepnel_a_copy_all_effects_info_ikont_mutat(dialog_app, qt_app, eltolás):
    window, controller, _engine = dialog_app
    elokeszit(window, qt_app, controller)
    _ablakmagassag(window, qt_app, eltolás)
    kijelol(window, qt_app, [0, 1])

    tetel_kattintasa(window, qt_app, "&Edit", "menuEditCopyEffects")

    _ikon_es_szoveg_melletti(
        window, qt_app, "copyAllEffectsInfo", "info", "copyAllEffectsInfoText"
    )
    zar(qt_app, gyerek(window, "copyAllEffectsInfoDialog"))


@pytest.mark.parametrize("eltolás", (-5, 0, 5))
def test_remove_from_picasa_a_sajat_logot_mutatja(dialog_app, qt_app, eltolás):
    window, controller, _engine = dialog_app
    elokeszit(window, qt_app, controller)
    _ablakmagassag(window, qt_app, eltolás)

    # Más ConfirmDialog-hívók alapértéke továbbra is ikon nélküli.
    torles = gyerek(window, "deleteFolderConfirmDialog")
    assert torles.property("iconType") == "none"

    tetel_kattintasa(window, qt_app, "F&older", "menuFolderRemoveFromPicasa")

    _ikon_es_szoveg_melletti(
        window, qt_app, "removeFolderConfirm", "picasa"
    )
    zar(qt_app, gyerek(window, "removeFolderConfirmDialog"))
