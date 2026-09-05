"""Ne legyen kötési hurok a fájlművelet-párbeszédeken (#1185).

## A tulajdonos konzolnaplója (v0.8.29, Windows)

```
FileOpsDialogs.qml:384:5: QML Dialog: Binding loop detected for property
"implicitWidth": qrc:/qt-project.org/imports/QtQuick/Controls/Fusion/Dialog.qml:14:5
```

## A hurok

A párbeszédek EGYETLEN gyereke egy tördelő `Text`, ami így a `Dialog`
`contentItem`-je lesz. A `Dialog` a saját `implicitWidth`-ét a
`contentItem` implicit szélességéből számolja, a tördelő `Text` implicit
szélessége viszont a KAPOTT szélességtől függ — a `width: 380` ezt nem
töri meg, mert a `Dialog` a `contentItem` méretét maga állítja be.

**Nem Windows-specifikus** (mérve Linuxon is, offscreen), csak a
tulajdonos ott vette észre a konzolon.

## Miért így tesztelünk

A #305 őre (`qml_warning_filter`) SZÁNDÉKOSAN szűk: csak
szkripthiba-mintákra hasal el, hogy a platformfüggő Qt-zaj ne buktassa a
CI-t. A kötési hurok viszont **mindig a mi hibánk** és
platformfüggetlen — ez a teszt ezért célzottan erre figyel, a
párbeszédek tényleges megnyitása közben.
"""

from PySide6.QtCore import (
    QMetaObject,
    QObject,
    Qt,
    qInstallMessageHandler,
)

from support.qml_halasztott import epitsd_fel_ha_fileops

#: a fájlművelet-párbeszédek, amiknek tördelő szövegük van
PARBESZEDEK = (
    "moveConfirmDialog",
    "duplicateNamesDialog",
    "fileOpsErrorDialog",
    "batchSummaryDialog",
)


def _megnyit_es_figyel(window, qt_app, nevek):
    """A párbeszédeket sorra nyitja, és gyűjti a kötési hurok üzeneteket."""
    hurkok: list[str] = []

    def kezelo(_tipus, _ctx, uzenet):
        if "Binding loop" in uzenet:
            hurkok.append(uzenet)

    elozo = qInstallMessageHandler(kezelo)
    try:
        for nev in nevek:
            epitsd_fel_ha_fileops(window, nev)  # #1612
            parbeszed = window.findChild(QObject, nev)
            assert parbeszed is not None, f"{nev} nem található"
            if parbeszed.property("message") is not None:
                parbeszed.setProperty(
                    "message", "Elég hosszú üzenet ahhoz, hogy tördelni kelljen. " * 3
                )
            QMetaObject.invokeMethod(
                parbeszed, "open", Qt.ConnectionType.DirectConnection
            )
            for _ in range(10):
                qt_app.processEvents()
            QMetaObject.invokeMethod(
                parbeszed, "close", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()
    finally:
        qInstallMessageHandler(elozo)
    return hurkok


def test_a_fajlmuvelet_parbeszedek_nem_hurkolnak(qml_app, qt_app):
    window, _controller, _ = qml_app
    hurkok = _megnyit_es_figyel(window, qt_app, PARBESZEDEK)
    assert not hurkok, "kötési hurok a párbeszédeken:\n  " + "\n  ".join(
        sorted({h.split(": QML")[0] for h in hurkok})
    )
