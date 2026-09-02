"""Az öt lista-rendezés tétel a `Nézet ▸ Mappanézet` almenüben (#1766).

## Hol van — és miért nem ott, ahol hittük

A jegy eredeti bizonyítéka a pipázó függvény volt: `GetSubMenu(GetMenu(hwnd), 2)`
= a harmadik felső menü, a **Nézet**. A spec **49.1** viszont kimondta,
hogy ez a menü-HOVATARTOZÁST igazolja, a menün belüli HELYET nem — egy
almenü tételei ugyanannak a felső menünek a fogantyúja alatt pipázódnak.

**A tulajdonos képernyőképe döntötte el**
(`research/#1766-nezet-mappanezet-almenu.png`): az öt tétel a
`Nézet ▸ Mappanézet` **almenüben** áll, ebben a sorrendben:

```
✓ Egyszerű mappanézet
  Fanézet
  ──────────────────────────────
✓ Rendezés létrehozási dátum alapján
  Rendezés a legutóbbi változtatások alapján
  Rendezés méret alapján
  Rendezés név alapján
  Rendezés megfordítása
```

Két külön pipa-csoport egy almenüben: a nézet-pár és a rendezés-négyes;
a „Rendezés megfordítása" ezektől független kapcsoló.

⚠️ **Az ötös a `eMenuView::` készlet — HOSSZÚ feliratokkal.** A Mappa menü
NÉGYES, rövid feliratú `ID_*SORT` készlete (#1595) más: azt ide bemásolni
ugyanaz a hiba lenne, fordítva.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app

_QML = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")

#: (objectName, angol forrásszöveg) — a felvételen mért SORRENDBEN.
OTOS = (
    ("menuViewSortByDate", "Sort by &Creation Date"),
    ("menuViewSortByRecent", "Sort by &Recent Changes"),
    ("menuViewSortBySize", "Sort by &Size"),
    ("menuViewSortByName", "Sort by &Name"),
    ("menuViewSortReverse", "Re&verse sort"),
)


def _almenu() -> str:
    """A `Mappanézet` almenü törzse — a következő azonos mélységű elemig."""
    kezdet = _QML.index('objectName: "menuViewFolderView"')
    return _QML[kezdet : kezdet + 6000]


class TestAzOtTetelOttVan:
    def test_mind_az_ot_tetel_megvan(self):
        blokk = _almenu()
        hianyzo = [nev for nev, _ in OTOS if f'objectName: "{nev}"' not in blokk]
        assert not hianyzo, f"a Mappanézet almenüből hiányzik: {hianyzo}"

    def test_az_EREDETI_hosszu_feliratokat_hasznalja(self):
        """`eMenuView::ID_VIEWBY*` — NEM a Mappa menü rövid négyese."""
        blokk = _almenu()
        for nev, felirat in OTOS:
            kezdet = blokk.index(f'objectName: "{nev}"')
            assert f'qsTr("{felirat}")' in blokk[kezdet : kezdet + 400], (
                f"{nev}: nem az eredeti hosszú feliratot kapta"
            )

    def test_a_MERT_sorrendben_allnak(self):
        """A felvétel sorrendje: dátum · legutóbbi · méret · név · megfordítás."""
        blokk = _almenu()
        helyek = [blokk.index(f'objectName: "{nev}"') for nev, _ in OTOS]
        assert helyek == sorted(helyek), (
            "a rendezés-tételek nem a felvételen mért sorrendben állnak"
        )

    def test_a_NEZET_par_UTAN_allnak(self):
        """A felvételen a nézet-pár van elöl, utána elválasztó, majd a
        rendezés."""
        blokk = _almenu()
        par_vege = blokk.index('objectName: "menuViewTreeView"')
        assert blokk.index(f'objectName: "{OTOS[0][0]}"') > par_vege


class TestABekotes:
    def test_a_negy_mod_a_KOZOS_uton_megy(self):
        """Ugyanaz a `setPaneSort`, mint a bal hasáb helyi menüjéé — a két
        menü pipája így EGYÜTT mozog."""
        blokk = _almenu()
        for nev, _ in OTOS[:4]:
            kezdet = blokk.index(f'objectName: "{nev}"')
            assert "setPaneSort(" in blokk[kezdet : kezdet + 500], (
                f"{nev} nem a közös vezérlő-utat hívja"
            )

    def test_a_megforditas_onallo_kapcsolo(self):
        kezdet = _almenu().index('objectName: "menuViewSortReverse"')
        assert "togglePaneSortReverse(" in _almenu()[kezdet : kezdet + 400]

    def test_RADIO_csapda_ellen_visszakotes(self):
        """#1464/#1468: a valódi kattintás IMPERATÍVAN átbillenti a
        `checked`-et; a MÁR aktív tételre kattintva a vezérlő állapota nem
        változik, tehát a kötés magától soha nem értékelődne újra — a menü
        újranyitásakor EGYIK tételen sem lenne pipa.

        A foga: a `Qt.binding` visszakötést kivéve ez bukik."""
        blokk = _almenu()
        for nev, _ in OTOS[:4]:
            kezdet = blokk.index(f'objectName: "{nev}"')
            reszlet = blokk[kezdet : kezdet + 600]
            assert "Qt.binding(" in reszlet, f"{nev}: nincs visszakötés"

    def test_a_pipa_a_VEZERLO_allapotara_kot(self):
        """A LÁNC mindkét szemét állítjuk, nem csak a végpontokat (#1665):
        a tétel pipája a menü `rendezes` tulajdonságára köt, az pedig a
        vezérlő `paneSort`-jára. Ha bármelyik szem elszakad, a pipa néma
        marad — a két végpont külön-külön attól még „helyesnek" látszik.
        """
        blokk = _almenu()
        assert re.search(r"rendezes:\s*\n?\s*\(controller && controller\.paneSort",
                         blokk), (
            "a menü `rendezes` tulajdonsága nem a vezérlő `paneSort`-jából jön"
        )
        assert "controller.paneSortReverse" in blokk, (
            "a megfordítás pipája nem a vezérlő állapotára köt"
        )
        for nev, _ in OTOS[:4]:
            kezdet = blokk.index(f'objectName: "{nev}"')
            assert "folderViewMenu.rendezes ===" in blokk[kezdet : kezdet + 600], (
                f"{nev}: a pipa nem a menü rendezés-állapotára köt"
            )


class TestAmitNEM_rontunk_el:
    def test_a_MAPPA_menu_rovid_negyese_VALTOZATLAN(self):
        """#1595: a Mappa menü `ID_*SORT` készlete RÖVID feliratú és
        négyes. Ha valaki a hosszú ötöst másolná oda (vagy fordítva), ez
        bukik."""
        kezdet = _QML.index('objectName: "menuFolderSortBy"')
        blokk = _QML[kezdet : kezdet + 3000]
        for rovid in ('qsTr("&Date")', 'qsTr("&Name")', 'qsTr("&Size")'):
            assert rovid in blokk, f"a Mappa menü rövid felirata eltűnt: {rovid}"
        assert 'qsTr("Sort by &Creation Date")' not in blokk, (
            "a Nézet menü HOSSZÚ felirata beszivárgott a Mappa menübe"
        )
