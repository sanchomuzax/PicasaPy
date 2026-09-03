"""#1612: segéd a HALASZTVA épülő párbeszédek felépítéséhez a tesztekben.

A `DeferredDialog` (#1720) `Loader`-e induláskor inaktív, ezért a benne lakó
párbeszéd és minden unokája `findChild`-dal `None`. A FELHASZNÁLÓI út a
hívóhelyeken `ensure()`-rel megy (pl. `createDialogs.ensure().openMovie()`);
az a teszt, amely a párbeszéd VISELKEDÉSÉT méri — nem a felépülés pillanatát
—, ugyanezt teszi meg előre, és onnantól változatlanul kereshet.

A felépülés pillanatát a #1720 őre méri
(`tests/app/test_qml_peldanyositas_or_1720.py`), ezért ezt a segédet ott
tilos használni.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def epitsd_fel(window: QObject, object_name: str) -> QObject:
    """Felépíti a megnevezett `DeferredDialog` tartalmát, és visszaadja azt.

    :param window: a főablak
    :param object_name: a `DeferredDialog` `objectName`-je
    :raises AssertionError: ha a burkoló nincs meg (elgépelt név, átnevezés)
    """
    halasztott = window.findChild(QObject, object_name)
    assert halasztott is not None, f"a(z) {object_name} DeferredDialog nincs meg"
    halasztott.metaObject().invokeMethod(halasztott, "ensure")
    return halasztott
