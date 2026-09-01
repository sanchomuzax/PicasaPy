"""Rács-nagyító — #1808.

Az eredeti Picasa fő könyvtárnézetében van egy nagyító: a rács fölött húzva
a képek nagyítva jelennek meg, **anélkül hogy megnyitnád őket**
(`thumbui/loupehit` — „Click and drag over photos to magnify them"). A
kapcsolója eszköztárgomb.

## ⚠️ Amit NEM tudunk

A nagyító VISELKEDÉSI RÉSZLETEI nincsenek mérve: mekkora a nagyítás,
követi-e folyamatosan az egeret, mit csinál a `loupe_sm`, mi történik a rács
szélén. A jegy ezt külön kimondja. A megvalósítás ezért a saját arányait
választja, és a forrásban ki is mondja, hogy az SAJÁT DÖNTÉS — ezt a
`TestASajatDontes` állítja, hogy egy későbbi kör ne higgye mértnek.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_FEED = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "LightboxFeed.qml"
).read_text(encoding="utf-8")
_TOOLBAR = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "MainToolbar.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


def _blokk(forras: str, horgony: str, hossz: int = 2600) -> str:
    kezd = forras.index(horgony)
    return forras[kezd : kezd + hossz]


class TestAKapcsolo:
    """⚠️ MEGFORDULT (#1911): a kapcsológomb NINCS az eszköztáron.

    A gomb `thumbui/loupehit`-ből mért volt, és a lánca MŰKÖDIK is — a
    valódi, kirajzolt ablakban mérve: kattintásra `loupeActive` igazra
    vált, és a rácson NYOMVA HÚZVA megjelenik a 2,5×-ös lencse. A
    tulajdonos élesben mégis azt jelentette, hogy a gomb **semmit nem
    csinál**, és igaza volt:

    1. a bekapcsolt állapotot csak egy 29×22-es, feliratlan ikon SZÍNE
       jelzi — a felületen semmi nem mondja, hogy a nagyító fel van húzva;
    2. a puszta KATTINTÁS a képen nem csinál semmit: nyomva HÚZNI kell.

    ⚠️ **Ez az osztály korábban tizennégy állítással volt „zöld", és
    egyiket sem kirajzolt ablakon mérte** — mind a QML forrásszövegét
    olvasta (0,25 mp alatt lefutott). A végpontok megvoltak, a
    felhasználói élmény nem.

    A rács oldali réteg SZÁNDÉKOSAN marad (`TestANagyitoAracson`): mérve
    van és működik; a visszakapcsolása felfedezhető felülettel külön jegy.
    """

    def test_NINCS_kapcsologomb_az_eszkoztaron(self):
        assert 'objectName: "toolbarLoupeButton"' not in _TOOLBAR

    def test_nincs_arva_jelzes(self):
        """Bekötetlen `loupeRequested` néma lánc-szakadás lenne."""
        assert "signal loupeRequested()" not in _TOOLBAR
        assert "onLoupeRequested" not in _MAIN

    def test_a_forras_KIMONDJA_miert(self):
        """A visszavonás oka a forrásban áll — hogy egy későbbi kör ne
        „hiányzó gombként" tegye vissza."""
        assert "VISSZAVONVA" in _TOOLBAR


class TestANagyitoReteg:
    def test_van_nagyito_reteg_a_racson(self):
        assert 'objectName: "feedLoupeArea"' in _FEED
        assert 'objectName: "feedLoupe"' in _FEED

    def test_CSAK_bekapcsolva_el(self):
        blokk = _blokk(_FEED, 'objectName: "feedLoupeArea"')
        assert "grid.appWindow.loupeActive === true" in blokk

    def test_elengedesre_ELTUNIK(self):
        blokk = _blokk(_FEED, 'objectName: "feedLoupeArea"')
        assert "onReleased: loupeArea.aktivSor = -1" in blokk
        assert "onCanceled: loupeArea.aktivSor = -1" in blokk

    def test_a_lencse_CSAK_nyomva_latszik(self):
        blokk = _blokk(_FEED, 'objectName: "feedLoupe"', 900)
        assert "visible: loupeArea.pressed && loupeArea.aktivSor >= 0" in blokk

    def test_NEM_nyitja_meg_a_kepet(self):
        """A réteg semmilyen megnyitás-hívást nem tartalmazhat."""
        blokk = _blokk(_FEED, 'objectName: "feedLoupeArea"')
        assert "openRequested" not in blokk
        assert "onDoubleClicked" not in blokk

    def test_NEM_valt_kijelolest(self):
        """A jegy záró pontja: bekapcsolva a húzás nem jelöl ki.

        A réteg a cellák FÖLÖTT áll és `preventStealing`-el fog — így a
        lasszó és a cella-kattintás sem fut le. A kijelölést hívó nevek
        egyike sem szerepelhet a rétegben."""
        blokk = _blokk(_FEED, 'objectName: "feedLoupeArea"')
        for tiltott in (
            "beginLasso", "updateLasso", "applyLasso",
            "applyThumbClick", "clearSelection",
        ):
            assert tiltott not in blokk, f"a nagyító-réteg {tiltott}-t hív"
        assert "preventStealing: true" in blokk

    def test_a_racs_szelen_sem_log_ki(self):
        """A lencse a képfolyamon belül marad — a jegy külön kiköti."""
        blokk = _blokk(_FEED, 'objectName: "feedLoupe"', 1200)
        assert "Math.max(0, Math.min(groupFlow.width" in blokk
        assert "Math.max(0, Math.min(groupFlow.height" in blokk

    def test_a_nagyitott_kep_NAGYOBB_felbontast_ker(self):
        """Enélkül a bélyegkép képpontjait nagyítanánk fel — a nagyító
        épp az élesség eldöntésére való."""
        blokk = _blokk(_FEED, 'objectName: "feedLoupeImage"', 900)
        assert "sourceSize.width: Math.round(loupe.width)" in blokk


class TestASajatDontes:
    def test_a_nagyitas_merteke_NEVVEL_all_a_kodban(self):
        assert "readonly property real nagyitas:" in _FEED

    def test_a_forras_KIMONDJA_hogy_sajat_dontes(self):
        """A jegy: »ne állítsa, hogy az eredetit másolja«."""
        kezd = _FEED.index("readonly property real nagyitas:")
        elotte = _FEED[max(0, kezd - 700) : kezd]
        assert "SAJÁT DÖNTÉS" in elotte
        assert "nem mért érték" in elotte
