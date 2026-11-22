"""A diavetítő vezérlősávjának méretezése a rugalmas hely szerint (#7363).

A sor rugalmas helye (`availableWidth`) a nézőszélesség mínusz a 40 px-es
szegély mínusz a sor rögzített elemeinek szélessége (`fixedWidth`). Az utóbbi a
betűtől függ: Linuxon 530 px, a windowsos CI-n a #7363 két bukása szerint kb.
150 px-szel több. Fix ablakszélességgel ezért ugyanaz a próba más tartományba
esik platformonként (bőséges, szűk, nulla hely). A segéd a MÉRT rögzített
szélességből számolja ki, mekkora ablak kell, így minden platformon ugyanaz a
tartomány áll elő, betűtől függetlenül.
"""

from __future__ import annotations

from math import ceil

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem, QQuickView

from support.qt_wait import varj_feltetelre

#: a sor bal és jobb oldali szegélye a `SlideshowControls.qml` `availableWidth`
#: képletében (`controlsLayer.width - 40 - fixedWidth`)
SZEGELY = 40


def sor(root: QObject) -> QObject:
    """A vezérlősáv gombsora (a `Row`, amely a rugalmas helyet számolja)."""
    kilepes = root.findChild(QQuickItem, "slideshowExitButton")
    assert kilepes is not None, "a(z) slideshowExitButton elem hiányzik"
    return kilepes.parentItem()


def szabad_hellyel(qt_app, view: QQuickView, root: QObject, szabad: float) -> None:
    """A nézőt úgy méretezi, hogy a sorban `szabad` px rugalmas hely marad."""
    rogzitett = float(sor(root).property("fixedWidth"))
    szelesseg = ceil(SZEGELY + rogzitett + szabad)
    view.resize(szelesseg, round(root.height()))
    assert varj_feltetelre(
        qt_app,
        lambda: round(root.width()) == szelesseg,
        masodperc=10.0,
    ), "a vetítő nem vette fel a kért ablakszélességet"
    qt_app.processEvents()
    maradt = float(sor(root).property("availableWidth"))
    assert maradt == pytest.approx(szabad, abs=1.0), (
        f"a kért {szabad} px rugalmas hely helyett {maradt:.1f} maradt"
    )
