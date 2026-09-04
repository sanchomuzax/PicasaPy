"""#1471: a fiók-lapok menüpipája a panel VALÓDI állapotát mutassa.

## Mit mértem, és mit NEM

A jegy eredeti leletét (— „a `Main.qml` egyik jelzést sem köti be") a mai
kódon ELLENŐRIZTEM: **elavult**. Mind a négy jelzésnek van fogadója
(`Main.qml:1036-1044`), és a teljes lánc él: jelzés → `valtsFiokLapot`
→ `activeDrawerTab` → `*PanelOpen` → a panel `visible`-je és a menüpipa.

Ami VALÓBAN romlik, az a pipa. A `MenuItem` `checkable: true` esetén
kattintásra ELŐSZÖR maga billenti a `checked`-et (`AbstractButton.toggle`),
és ez az imperatív írás **eldobja** a `checked: bar.tagsPanelOpen`
kötést. Billenő tételnél ez nem tűnik fel (a művelet úgyis átbillenti az
állapotot), a fiók-lapoknál viszont igen: az AKTÍV lapra kattintva a
panel — helyesen, a #1773 bináris mérése szerint — NYITVA MARAD, a pipa
viszont lekapcsol.

**Lemérve a javítás előtt** (`menuViewTags`, kétszer kattintva):

```
open = True   checked = False
```

## A minta

A `FolderListContextMenu.qml:66-71` már ezt csinálja: az `onTriggered`
végén `checked = Qt.binding(...)` visszaállítja a kötést. Ez a javítás
ugyanazt viszi a négy fiók-lapra.

## Amit ez az őr NEM állít

Nem állítja, hogy a menüsáv MINDEN `checkable` tétele rendben van — nyolc
további tétel köti a `checked`-et visszaállítás nélkül. Azok ma azért
konzisztensek, mert a műveletük mindig átbillenti az állapotot; ez
szerencse, nem szerkezet (külön jegy).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

#: menütétel-objectName → az ablak állapot-tulajdonsága
LAPOK = [
    ("menuViewProperties", "propertiesPanelOpen"),
    ("menuViewTags", "tagsPanelOpen"),
    ("menuViewPeople", "peoplePanelOpen"),
    ("menuViewPlaces", "placesPanelOpen"),
]


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _kattints(item, qt_app) -> None:
    """VALÓDI kattintás: az `AbstractButton` előbb billent, aztán jelez.

    Szándékosan nem csak a `triggered`-et bocsátjuk ki — épp a `toggle`
    az, ami a kötést eldobja, tehát enélkül a hiba láthatatlan maradna.
    """
    QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


@pytest.mark.parametrize("menu,tulajdonsag", LAPOK)
def test_az_aktiv_lapra_kattintva_a_pipa_nem_hazudik(
    qml_app, qt_app, menu, tulajdonsag
):
    window, _controller, _engine = qml_app
    tetel = _gyerek(window, menu)

    _kattints(tetel, qt_app)
    assert window.property(tulajdonsag) is True, (
        f"a(z) {menu} megnyitása nem hatott"
    )
    assert tetel.property("checked") is True

    # MÉGEGYSZER ugyanarra: a panel nyitva marad (#1773), a pipának is
    _kattints(tetel, qt_app)
    assert window.property(tulajdonsag) is True, (
        "az aktív lapra kattintás nem zárhatja be a panelt (#1773)"
    )
    assert tetel.property("checked") is True, (
        f"a(z) {menu} pipája lekapcsolt, pedig a panel nyitva maradt — "
        "a checked kötését az AbstractButton.toggle eldobta"
    )
