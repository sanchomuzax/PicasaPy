"""A megerősítő párbeszédek HALASZTVA épülnek fel (#1612).

## Miért

A `Main.qml` fája induláskor 13 142 QObjectet épített fel a próba-
környezetben, és ennek nagy része olyan párbeszéd, amit a felhasználó a
legtöbb indulásnál meg sem nyit. A #1720 gépezete (`DeferredDialog`) ezt
megoldja, de **magától nem terjed**: minden új párbeszéd újra eagerré
válhat, és ez semmilyen próbán nem látszik.

Mérve ezzel a hét megerősítéssel: **13 142 → 12 626 objektum (−516,
−3,9%)**, ugyanazon a próba-harnesse-en, két futás minimumával.

## Mit állít ez a fájl — két oldalról, mutációra érzékenyen

1. **Induláskor NINCS példány.** Ha valaki visszaírja a párbeszédet
   közvetlen (eager) alakra, ez a próba elbukik — nem elég, hogy a
   viselkedés változatlan marad, a NYERESÉG elveszik némán.
2. **Az `ensure()` valóban felépíti.** Ha a burkolás elromlik (elírt
   `sourceComponent`, hiányzó `objectName`), a párbeszéd soha nem jönne
   létre: az `ensure()` utáni keresés fogja meg. Enélkül az 1. pont
   önmagában úgy is „zöld" lenne, hogy a párbeszéd EGYÁLTALÁN nem működik.

⚠️ Amit ez NEM mér: hogy a felhasználói út (menüpont, panelgomb, vezérlő-
jelzés) tényleg meghívja-e az `ensure()`-t. Azt a saját jegyeik próbái
mérik a valódi úton — `test_geocimke_torles_1404`,
`test_hely_megerosites_2013`, `test_broken_photo_and_diskspace_459`,
`test_racs_ctrl_delete_1619`, `test_album_delete_billentyu_1608` —, és a
szerkezeti tilalmat (vezérlőre kötött `Connections` halasztott
párbeszédben) a `test_halasztott_jelzesek_1743` őrzi.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

#: `(burok objectName, a BELSŐ párbeszéd objectName-je)`.
#:
#: A belső nevek a `ConfirmDialog` szokása szerint alakulnak: vagy kiírt
#: `objectName`, vagy a bázis `namePrefix + "Dialog"` alakja.
HALASZTOTT = (
    ("clearGeotagDialogLoader", "clearGeotagConfirm"),
    ("setGeotagDialogLoader", "setGeotagConfirm"),
    ("panelClearGeotagDialogLoader", "panelClearGeotagConfirm"),
    ("undoAllEditsDialogLoader", "undoAllEditsDialog"),
    ("brokenPhotoDialogLoader", "brokenPhotoDialog"),
    ("removePeopleFacesDialogLoader", "removePeopleFacesDialog"),
    ("resetFacesConfirmLoader", "resetFacesConfirm"),
)

#: ALSÓ KORLÁT: ha valaki kiüríti a listát, az őr néma maradna.
MIN_HALASZTOTT = 7


def test_a_lista_nem_urulhet_ki():
    assert len(HALASZTOTT) >= MIN_HALASZTOTT


class TestIndulaskorNincsPeldany:
    @pytest.mark.parametrize("burok,belso", HALASZTOTT)
    def test_a_parbeszed_nem_epul_fel_indulaskor(self, qml_app, qt_app, burok, belso):
        window = qml_app[0]
        qt_app.processEvents()

        assert window.findChild(QObject, burok) is not None, (
            f"a halasztó burok ({burok}) nincs meg — elnevezés változott? "
            "az őr így semmit nem mér"
        )
        assert window.findChild(QObject, belso) is None, (
            f"a {belso} párbeszéd MÁR induláskor felépült — a halasztás "
            "elveszett (visszaírták eager alakra?), és vele a mért "
            "−516 objektum"
        )


class TestAzEnsureFelepiti:
    @pytest.mark.parametrize("burok,belso", HALASZTOTT)
    def test_az_ensure_utan_all_a_parbeszed(self, qml_app, qt_app, burok, belso):
        window = qml_app[0]
        loader = window.findChild(QObject, burok)
        assert loader is not None

        QMetaObject.invokeMethod(loader, "ensure", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert window.findChild(QObject, belso) is not None, (
            f"az `ensure()` nem építette fel a {belso} párbeszédet — a "
            "burkolás elromlott, tehát a párbeszéd SOHA nem jelenne meg"
        )
