"""#1929: a buboréksúgók az EREDETI szövegei, nem átfogalmazások.

## A lelet

A fő könyvtárnézet **31 buboréksúgójából EGY** egyezett az eredetivel
(„Create a new album"). A többi vagy más szöveg volt, vagy nem is volt
súgó — négy meglévő vezérlőn (`importbutton`, `startoggle`, `rotateleft`,
`rotateright`) egyáltalán nem.

A projekt rögzített döntése szerint a felület pontosan úgy nézzen ki, mint
az eredeti Picasa; a súgó szövege ennek része.

## ⛔ A csapda, amit egy párhuzamos kutatói szál dokumentált

A súgók **nincsenek** a `stringres-en-hu.tsv`-ben — ott mind a 31-re nulla
találat van. Ebből majdnem az a hamis lelet lett, hogy „a súgók nincsenek
honosítva". **Megdőlt:** a `referencia/i18n-hu/tooltips.xml`-ben élnek,
és NEM angol szöveg, hanem CÉLELEM szerint kulcsolva
(`target="thumbui/startoggle"`). Aki csak a szövegtárat nézi, hamis
negatívot kap.

⇒ A magyar fordítások ezért **nem a mi fogalmazásaink**: a hivatalos
alakok a `tooltips.xml`-ből.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_TRAYBAR = (_QML / "TrayBar.qml").read_text(encoding="utf-8")
_TOOLBAR = (_QML / "MainToolbar.qml").read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

#: `.tre`-elem → (az EREDETI angol súgó, a HIVATALOS magyar)
_SUGOK = {
    "scratchhold": ("Hold selected items", "Kijelölt elemek megőrzése"),
    "scratchclear": (
        "Clear items from the selection", "Elemek eltávolítása a kijelölésből",
    ),
    "addtobuttcon": (
        "Add selected items to an Album", "Kijelölt elemek hozzáadása albumhoz",
    ),
    "startoggle": ("Add/Remove Star", "Csillag hozzáadása/eltávolítása"),
    "rotateleft": ("Rotate counter-clockwise", "Forgatás balra"),
    "rotateright": ("Rotate clockwise", "Forgatás jobbra"),
    "flatview": (
        "Set view to show flat folder structure",
        "Egydimenziós mappanézet beállítása",
    ),
    "folderview": (
        "Set view to show folder tree structure",
        "Fastruktúrájú mappanézet beállítása",
    ),
    "importbutton": (
        "Get photos from a camera, scanner, or other media",
        "Fotók letöltése fényképezőgépről, képolvasóról vagy más eszközről",
    ),
    "people_toggle": (
        "Show/Hide People Panel",
        "Az Emberek párbeszédpanel megjelenítése/elrejtése",
    ),
    "places_toggle": (
        "Show/Hide Places Panel",
        "A Helyek párbeszédpanel megjelenítése/elrejtése",
    ),
    "tags_toggle": (
        "Show/Hide Tags Panel",
        "A Címkék párbeszédpanel megjelenítése/elrejtése",
    ),
    "properties_toggle": (
        "Show/Hide Properties Panel",
        "A Tulajdonságok párbeszédpanel megjelenítése/elrejtése",
    ),
}

_FORRAS = _TRAYBAR + _TOOLBAR


class TestAzAngolSugokAzEREDETIEK:
    def test_mind_ott_van_a_forrasban(self):
        hianyzik = [
            elem for elem, (en, _hu) in _SUGOK.items() if en not in _FORRAS
        ]
        assert not hianyzik, f"nincs meg az eredeti súgó: {hianyzik}"

    def test_a_regi_atfogalmazasok_nem_ternek_vissza(self):
        """Ha valaki visszaírja a rövidebb, „szebb" változatot, ez bukik."""
        tiltott = (
            'qsTr("Flat folder view")',
            'qsTr("Tree folder view")',
            'qsTr("Hold Selection")',
            'qsTr("Add the pictures in the tray to an album")',
        )
        vissza = [t for t in tiltott if t in _FORRAS]
        assert not vissza, f"visszatért a mi átfogalmazásunk: {vissza}"


class TestAMagyarAHIVATALOS:
    def test_mind_a_hivatalos_alakkal_van_forditva(self):
        rossz = []
        for elem, (en, hu) in _SUGOK.items():
            minta = re.compile(
                r"<source>" + re.escape(en)
                + r"</source>\s*<translation>(.*?)</translation>", re.S)
            m = minta.search(_TS)
            if m is None:
                rossz.append(f"{elem}: nincs .ts-bejegyzés")
            elif m.group(1) != hu:
                rossz.append(f"{elem}: {m.group(1)!r} ≠ {hu!r}")
        assert not rossz, (
            "a magyar súgó nem a `tooltips.xml` hivatalos alakja: " + str(rossz)
        )


class TestANegyHianyzoSugo:
    """A jegy szerint négy MEGLÉVŐ vezérlőn egyáltalán nem volt súgó."""

    def test_a_negy_vezerlonek_MOST_van_sugoja(self):
        for elem in ("importbutton", "startoggle", "rotateleft", "rotateright"):
            en = _SUGOK[elem][0]
            assert f'ToolTip.text: qsTr("{en}")' in _FORRAS, elem
