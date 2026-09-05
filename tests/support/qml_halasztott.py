"""#2096: segéd a HALASZTVA épülő párbeszédek felépítéséhez a tesztekben.

A `DeferredDialog` (#1720) `Loader`-e induláskor inaktív, ezért a benne lakó
párbeszéd és minden unokája `findChild`-dal `None`. A FELHASZNÁLÓI út a
hívóhelyeken `ensure()`-rel megy (pl. `createDialogs.ensure().openMovie()`);
az a teszt, amely a párbeszéd VISELKEDÉSÉT méri — nem a felépülés
pillanatát —, ugyanezt teszi meg előre, és onnantól változatlanul kereshet.

A felépülés pillanatát a #1720 őre méri
(`tests/app/qml_functional/test_qml_peldanyositas_or_1720.py`), ezért ezt a
segédet ott tilos használni.
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


#: #1612: a `FileOpsDialogs` belső párbeszédei. A burok `objectName`-je
#: `fileOpsDialogs`; ezek a nevek induláskor `None`-t adnak, mert a
#: komponens csak az első `ensure()`-re épül fel.
FILEOPS_PARBESZEDEK = frozenset(
    {
        "renameDialog",
        "renameManyDialog",
        "newAlbumDialog",
        "moveToNewFolderDialog",
        "moveFolderDialog",
        "moveConfirmDialog",
        "duplicateNamesDialog",
        "deleteConfirmDialog",
        "fileOpsErrorDialog",
        "batchSummaryDialog",
        "batchProgressDialog",
    }
)


def epitsd_fel_ha_fileops(window: QObject, object_name: str) -> None:
    """Felépíti a `FileOpsDialogs`-t, ha a keresett elem oda tartozik.

    Az a teszt, amely e párbeszédek VISELKEDÉSÉT méri, ugyanazt teszi meg
    előre, amit a felhasználói út is (`fileOpsDialogs.ensure().openX(...)`),
    és onnantól változatlanul kereshet — a „nyitva van-e" állítás értelme
    nem változik. A FELÉPÜLÉS pillanatát külön őr méri
    (`test_fileops_halasztas_1612.py`), ezért ott tilos ezt használni.

    A gyerekek nevét azért soroljuk fel tételesen, mert az elgépelt vagy
    átnevezett név így AZONNAL kiderül: a hívó `findChild`-ja `None`-t ad,
    és a teszt a saját állításán bukik, nem némán megy tovább.
    """
    if object_name in FILEOPS_PARBESZEDEK:
        epitsd_fel(window, "fileOpsDialogs")
