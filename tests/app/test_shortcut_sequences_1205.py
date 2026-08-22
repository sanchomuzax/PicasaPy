"""A `StandardKey`-hez `sequences:` kell, nem `sequence:` (#1205).

## A tulajdonos jelentése (Windows, minden induláskor)

```
QML Shortcut: Only binding to one of multiple key bindings associated
with 70. Use 'sequences: [ <key> ]' to bind to all of them.
```

A `70` a `StandardKey.Cancel`. A `sequence:` (egyes szám) a szabványos
billentyűhöz tartozó kötések közül **csak az elsőt** köti be.

**Platformfüggő, ezért Linuxon nem látszik** — mérve (PySide6,
`QKeySequence.keyBindings`): a `Cancel` itt egyetlen kötés (`Esc`),
Windowson több. A #1217 tanulsága szerint az ilyen tesztnek KI KELL
MONDANIA a platformját: ez a teszt ezért nem a figyelmeztetést méri
(azt itt sosem kapnánk meg), hanem a **forrás szabályát** — így minden
platformon ugyanazt állítja.
"""

import re
from pathlib import Path

QML_GYOKER = (
    Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "qml"
)

#: `sequence:` (egyes szám), aminek az értéke `StandardKey.…`
MINTA = re.compile(r"^\s*sequence\s*:\s*StandardKey\.", re.MULTILINE)


def test_nincs_egyes_szamu_sequence_standardkey_ertekkel():
    talalatok = []
    for fajl in sorted(QML_GYOKER.rglob("*.qml")):
        szoveg = fajl.read_text(encoding="utf-8")
        for egyezes in MINTA.finditer(szoveg):
            sor = szoveg.count("\n", 0, egyezes.start()) + 1
            talalatok.append(f"{fajl.relative_to(QML_GYOKER)}:{sor}")
    assert not talalatok, (
        "StandardKey-hez `sequences: [ … ]` kell, különben Windowson csak "
        "az első kötés él (és minden induláskor figyelmeztet):\n  "
        + "\n  ".join(talalatok)
    )


class TestEscMukodik:
    """A szabály betartása mellett a VALÓDI Esc is működjön (#1205).

    A #1200 tanulsága: a forrás-szintű állítás önmagában kevés — a
    vezérlőt el is kell tudni sütni. Ezért itt valódi billentyűesemény
    megy az ablakra, nem a `cancelChanges()` közvetlen hívása."""

    def test_az_esc_bezarja_a_mappakezelot(self, qml_app, qt_app):
        from PySide6.QtCore import QEvent, QMetaObject, QObject, Qt
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtQuick import QQuickWindow

        window, _controller, _lib, _engine = qml_app
        parbeszed = window.findChild(QObject, "folderManagerDialog")
        assert parbeszed is not None, "folderManagerDialog nem található"
        QMetaObject.invokeMethod(
            parbeszed, "open", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert parbeszed.property("visible"), "a Mappakezelő nem nyílt meg"

        cel = parbeszed if isinstance(parbeszed, QQuickWindow) else window
        qt_app.sendEvent(
            cel,
            QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Escape,
                Qt.KeyboardModifier.NoModifier,
            ),
        )
        qt_app.processEvents()
        assert not parbeszed.property("visible"), (
            "az Esc nem zárta be a Mappakezelőt"
        )
