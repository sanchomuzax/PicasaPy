"""#1595 — a Mappa ▸ Rendezés a NÉGYES készletet használja, nem az ötöst.

## A lelet

Az eredetiben **két** rendezés-készlet van, és a Mappa menübe a rosszat
tettük:

| | készlet | tételek | hol |
|---|---|---|---|
| **A** | `ID_*SORT` | 4, RÖVID felirat: `&Date` · `&Name` · `&Size` · `&Reverse order` | **Mappa menü**, mappa helyi menüje |
| **B** | `ID_VIEWBY*` | 5, HOSSZÚ felirat + „recent changes" | Nézet menü, bal hasáb |

A `FolderContextMenu.qml` végig az **A**-t használta — ugyanaz a rendezés
két helyen, kétféle felirattal és tételszámmal állt.

## ⚠️ A „legutóbbi változtatások" NEM tűnik el

Az `ID_*SORT` négyesben nincs ilyen tétel, nálunk viszont **működő**
rendezés (#1759 mérte ki, mit rendez). A hűségért nem vesszük el:
**SAJÁT FUNKCIÓ** jelölést kap (kék felirat + kötelező buboréksúgó), a
`docs/decisions/sajat-funkciok-jelolese.md` szerint.

Ez a különbség a „hiányzik" és a „többletünk van" között — és a menüben
látszania kell, melyik.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_MENU = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml"
)
_HELYI = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml"
)

#: Az `ID_*SORT` négyes, a `stringres` rövid feliratával.
A_KESZLET = ("&Date", "&Name", "&Size", "&Reverse order")

#: A `ID_VIEWBY*` ötös hosszú feliratai — ezek a NÉZET menüé, nem a Mappáé.
B_KESZLET_FELIRATAI = (
    "Sort by creation date",
    "Sort by recent changes",
    "Sort by size",
    "Sort by name",
    "Reverse sort",
)


def _mappa_menu_szakasz() -> str:
    """A `menuFolderSortBy` almenü forrásszövege — a ZÁRÓ tételéig.

    Fix karakterablakkal nem jó: az első változatom 2600 karakterrel
    vágott, és a `&Reverse order` — ami az almenü UTOLSÓ tétele — kimaradt
    belőle. A teszt így „hiányzó feliratot" jelentett olyanra, ami ott
    van. A vágás ezért a záró tétel után történik, nem hosszra.
    """
    forras = _MENU.read_text(encoding="utf-8")
    kezdet = forras.index('objectName: "menuFolderSortBy"')
    zaro = forras.index('objectName: "menuFolderSortReverse"', kezdet)
    veg = forras.index("}", forras.index("onTriggered", zaro))
    return forras[kezdet:veg]


class TestAHelyesKeszlet:
    def test_a_negy_rovid_felirat_mind_ott_van(self):
        szakasz = _mappa_menu_szakasz()
        hianyzik = [f for f in A_KESZLET if f'qsTr("{f}")' not in szakasz]
        assert not hianyzik, f"hiányzó A-készlet-felirat: {hianyzik}"

    def test_a_hosszu_feliratok_ELTUNTEK_a_mappa_menubol(self):
        """Ez a teszt foga: a B készlet feliratai nem maradhatnak itt."""
        szakasz = _mappa_menu_szakasz()
        bentmaradt = [f for f in B_KESZLET_FELIRATAI if f in szakasz]
        assert not bentmaradt, (
            f"a Nézet menü ötös készletének felirata a Mappa menüben: {bentmaradt}"
        )

    def test_az_almenu_cime_valtozatlan(self):
        """A CÍM nem tárgya ennek a jegynek — a tételkészlet az.

        Először `&Sort By`-ra írtam át (az `ID_SORTBY` magyar felirata
        `&Rendezés`), de a fájl saját konvenciója szerint az ALMENÜ-címek
        mnemonik nélküliek (`Display Mode`, `Batch Edit`, `Movie`), és a
        `test_qml_menubar_audit` a mnemonik nélküli alakot őrzi. Egy
        kozmetikai eltérésért nem török el egy meglévő őrt — az angol
        oldalon a `&` meglétét nem is mértem."""
        assert 'title: qsTr("Sort By")' in _mappa_menu_szakasz()


class TestASajatTobblet:
    def test_a_legutobbi_valtoztatasok_MEGMARAD(self):
        """A hűség nem járhat funkcióvesztéssel."""
        assert 'objectName: "menuFolderSortByChanged"' in _mappa_menu_szakasz()

    def test_es_SAJAT_FUNKCIOKENT_van_jelolve(self):
        """Enélkül úgy nézne ki, mintha az eredetiben is lenne."""
        szakasz = _mappa_menu_szakasz()
        kezdet = szakasz.index('objectName: "menuFolderSortByChanged"')
        blokk = szakasz[kezdet : kezdet + 400]
        assert "sajat: true" in blokk
        assert "PicasaMenuItem" in szakasz[:kezdet][-200:]


class TestAKetHelyEGYEZIK:
    def test_a_mappa_menu_es_a_helyi_menu_ugyanazt_mondja(self):
        """A #1595 lényege: ugyanaz a rendezés két helyen, kétféle
        felirattal állt. A helyi menü volt a helyes."""
        helyi = _HELYI.read_text(encoding="utf-8")
        szakasz = _mappa_menu_szakasz()
        for felirat in ("&Date", "&Name", "&Size"):
            assert f'qsTr("{felirat}")' in helyi, f"a helyi menüből hiányzik: {felirat}"
            assert f'qsTr("{felirat}")' in szakasz


class TestAzEloFaban:
    def test_mind_az_ot_tetel_letezik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for nev in (
            "menuFolderSortByDate",
            "menuFolderSortByName",
            "menuFolderSortBySize",
            "menuFolderSortByChanged",
            "menuFolderSortReverse",
        ):
            assert window.findChild(QObject, nev) is not None, nev

    def test_a_sajat_tetel_sugot_is_kap(self, qml_app, qt_app):
        """A döntés szerint a jelölés MELLETT a buboréksúgó kötelező —
        a szín önmagában nem hordozhat információt (színvakság)."""
        window, _controller, _engine = qml_app
        tetel = window.findChild(QObject, "menuFolderSortByChanged")
        assert tetel is not None
        assert tetel.property("sajat") is True
        assert tetel.property("sajatSugo")
