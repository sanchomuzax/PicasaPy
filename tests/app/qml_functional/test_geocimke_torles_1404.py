"""A geocímke-törlés MENÜPONTJA és a megerősítés (#1404).

## Mérve — a teljes lánc a binárisból

| elem | azonosító / cím | angol | magyar |
|---|---|---|---|
| menütétel | `eMenuTools::ID_PICTURE_GEOUNTAG`, épül: `0x00559150` | `Clear Geotags` | **Geocímkék törlése** |
| megerősítés | `ClearGeoTag::warn`, hívó: `0x00600670` | *„You are about to erase all geographic location information (i.e., latitude and longitude) from the selected photos.\\n\\nOK to proceed?"* | *„Törölni készül a kijelölt fotók összes, földrajzi helyre utaló adatát (a szélességet és a hosszúságot).\\n\\nFolytatja?"* |
| Helyek-panel gombja | `geopanel/cleargeotag`, `GeotagPanel::clearbutton`, `0x00650390` | `Clear %d Geotag(s)` | **`%d geocímke törlése`** |

⇒ **KÉT belépési pont** van, és a gomb felirata a DARABSZÁMOT is kiírja.

## Mit adott ez előtt nálunk

| | eredeti | nálunk (mérve) |
|---|---|---|
| menütétel | van, az `Eszközök ▸ Geocímke` almenüben | **nincs sehol** |
| Helyek-panel gombja | `Clear %d Geotag(s)` | „Remove Geotag" — **saját fogalmazás, darabszám nélkül** |
| megerősítés törlés előtt | **van** | **NINCS** — a törlés szó nélkül lefutott |

A harmadik a legsúlyosabb: **visszafordíthatatlan műveletet végeztünk
kérdés nélkül.** A geocímke az ini-ből kikerül; ha a felhasználó
véletlenül nyomta meg, nincs mit visszavonni.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_MENU = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_PLACES = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PlacesPanel.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")


class TestAMenupont:
    def test_van_menupont(self):
        assert 'objectName: "menuToolsClearGeotag"' in _MENU, (
            "az Eszközök ▸ Geocímke almenüből hiányzik a törlés"
        )

    def test_az_EREDETI_feliratot_hasznalja(self):
        """`eMenuTools::ID_PICTURE_GEOUNTAG` — nem saját fogalmazás."""
        kezdet = _MENU.index('objectName: "menuToolsClearGeotag"')
        assert 'qsTr("Clear Geotags")' in _MENU[kezdet : kezdet + 400]

    def test_a_GEOCIMKE_almenuben_all(self):
        """Az eredetiben az `Eszközök ▸ Geocímke` alatt — a Google Earth
        tételek testvéreként."""
        geo = _MENU.index('objectName: "menuToolsExportEarth"')
        vege = _MENU.index('title: qsTr("Experimental")')
        assert geo < _MENU.index('objectName: "menuToolsClearGeotag"') < vege

    def test_a_menupont_NEM_nema(self):
        """A #1798 osztálya: legyen jelzése, és a Main.qml fogja is el."""
        kezdet = _MENU.index('objectName: "menuToolsClearGeotag"')
        assert "clearGeotagRequested()" in _MENU[kezdet : kezdet + 400]
        assert "signal clearGeotagRequested()" in _MENU
        assert "onClearGeotagRequested" in _MAIN, (
            "a menüpont jelzését senki nem fogja el"
        )


class TestAMegerosites:
    def test_van_megerosito_parbeszed(self):
        """⚠️ Visszafordíthatatlan művelet: a geocímke az ini-ből kikerül."""
        assert 'objectName: "clearGeotagConfirm"' in _MAIN, (
            "a geocímke-törlés megerősítés nélkül fut — az eredeti KÉRDEZ"
        )

    def test_az_EREDETI_szoveget_hasznalja(self):
        """`ClearGeoTag::warn` — szó szerint, nem átfogalmazva."""
        assert (
            "You are about to erase all geographic location information"
            in _MAIN
        )

    def test_a_torles_CSAK_a_megerosites_utan_fut(self):
        """A foga: ha a párbeszéd csak dísz, és a gomb közvetlenül töröl,
        ez bukik."""
        kezdet = _MAIN.index('objectName: "clearGeotagConfirm"')
        blokk = _MAIN[kezdet : kezdet + 900]
        assert "clearGeotagRows(" in blokk, (
            "a törlés nem a megerősítés elfogadásához van kötve"
        )


class TestAHelyekPanelGombja:
    def test_a_felirat_a_DARABSZAMOT_is_kiirja(self):
        """`GeotagPanel::clearbutton` = `Clear %d Geotag(s)`."""
        kezdet = _PLACES.index('objectName: "placesClearButton"')
        blokk = _PLACES[kezdet : kezdet + 600]
        assert 'qsTr("Clear %1 Geotag(s)")' in blokk, (
            "a gomb felirata nem a mért, darabszámos alak"
        )
        assert ".arg(" in blokk, "a darabszám nincs behelyettesítve"

    def test_a_sajat_fogalmazas_ELTUNT(self):
        assert 'qsTr("Remove Geotag")' not in _PLACES

    def test_a_panel_gombja_IS_megerosit(self):
        """Két belépési pont, EGY szabály: mindkettő kérdez."""
        kezdet = _PLACES.index('objectName: "placesClearButton"')
        blokk = _PLACES[kezdet : kezdet + 600]
        assert "clearGeotagRows(" not in blokk, (
            "a panel gombja a megerősítés MEGKERÜLÉSÉVEL töröl"
        )
