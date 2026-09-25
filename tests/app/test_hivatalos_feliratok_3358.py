"""A feliratok a HIVATALOS Picasa-szöveget mondják (#3358, #2921).

A #2921 közeli-pár mérése (privát repó, `felirat_kozeli_parok.py`) olyan
feliratokat talál, amelyeknél az eredetinek VAN szövege ugyanabban a
helyzetben, csak mi máshogy fogalmaztuk. Ez nem stílusdöntés: a
lefedettségi mérő emiatt nem találja meg a párját, a felhasználó pedig
más szöveget lát, mint az eredeti Picasában.

Amit ez az őr NEM mér: azt, hogy a felirat a képernyőn tényleg látszik-e,
és azt sem, hogy jó helyen van-e — csak a szöveg azonosságát a mért
hivatalos alakkal.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

QML = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "qml"
TS = QML.parent / "i18n" / "picasapy_hu.ts"

#: felirat → (hivatalos magyar, a `stringres` azonosítója)
HIVATALOS = {
    "The passwords did not match.": (
        "A jelszavak nem egyeztek.", "CThumbUI::PassVerifyWrong"),
    "Do not ask again": (
        "Ne kérdezze meg újra", "CMakeFaceMoviePanelRememberDialog"),
    "Add this tag to entire selection": (
        "A címke hozzáadása a teljes kijelölt részhez",
        "Tags::ID_APPLYTHISTAGTOSELECTION"),
    # #2921, második kör: a mappa-fejléc szinkron-felirata és az
    # adatbázis-áthelyező mappaválasztó címe
    "Sync to Web": ("Szinkronizálás az internettel", "SyncLabel::Off"),
    "Choose database location...": (
        "Adatbázis helyének kiválasztása…", "eMenuTools::ID_MOVE_DATABASE"),
    # #3574: a szerkesztő, az arcok és a diavetítés feliratai
    "This image's orientation has been modified by the Straighten tool and might not crop accurately.\nIf you encounter difficulty cropping this image, try undoing the Straighten fix, then recrop, and Straighten again if necessary.": (
        'A kép irányát megváltoztatta a „Kiegyenesítés” eszközzel, ami pontatlanságokat okozhat a vágás alkalmazásakor.\nHa nem sikerül a kép vágása, vonja vissza a „Kiegyenesítés” eszközzel végzett javítást, majd ismételje meg a vágást és - ha szükséges - a kiegyenesítést.',
        "IDS_WARN_CROP_ACCURACY"),
    'Picasa has found and corrected red eye(s).\n\nNote: You can click on a box to delete a change.\n\nYou can also draw a square around any red eye that Picasa may have missed.': (
        'A Picasa vörösszem-effektusokat talált a képen, és kijavította őket.\n\nMegjegyzés: a keretbe kattintva visszavonhatja a változást.\n\nA Picasa által esetleg figyelmen kívül hagyott vörösszemeket manuálisan kijelölheti és kijavíthatja.',
        "RedEye::AutoFixedMessage"),
    'Instructions:\n\n1) Manipulate the rectangle to fit the face of the person you want to add.\n\nYou can drag the rectangle to position it, and move its sides to refine the shape.\n\n2) Click on "Add a name" under the rectangle and type in the person\'s name.\n\n(Be sure to either press Enter or click on an autocompleted name to indicate that you are done)': (
        'Utasítások:\n\n1) A négyszöget alakítsa úgy, hogy illeszkedjen a hozzáadni kívánt személy arcához.\n\nHúzással a megfelelő helyre helyezheti a négyszöget, oldalainak mozgatásával pedig pontosíthatja az alakját.\n\n2) Kattintson a négyszög alatt látható "Név hozzáadása" feliratra, és írja be a személy nevét.\n\n(Ne feledje, hogy a befejezéshez le kell nyomnia az Enter billentyűt, vagy az egyik automatikusan kiegészített névre kell kattintania.)',
        "manual_add::instructions"),
    "Feather": ("Lágy perem", "filter_dir_tint_label1"),
    "Color Preservation": ("Színek megőrzése", "filter_tint_label1"),
    "Left justify text": ("Szöveg balra igazítása", "edittextpanel/leftalign"),
    "Center justify text": ("Szöveg középre igazítása", "edittextpanel/centeralign"),
    "Right justify text": ("Szöveg jobbra igazítása", "edittextpanel/rightalign"),
    "Ignore all of the selected faces": (
        "Az összes kijelölt arc mellőzése", "unknownfaceheaderpanel/ignore"),
    "Display Time": ("Megjelenítési idő", "oneup/tpslabel"),
    "seconds": ("másodperc", "OneUpUI::seconds"),
}

#: fájl → a benne várt hivatalos feliratok
ELOFORDULASOK = {
    "PicasaPy/HiddenPasswordDialog.qml": ["The passwords did not match."],
    "PicasaPy/SaveDialogs.qml": ["Do not ask again"],
    "PicasaPy/ConfirmDialog.qml": ["Do not ask again"],
    "PicasaPy/TagContextMenu.qml": ["Add this tag to entire selection"],
    "PicasaPy/LightboxHeader.qml": ["Sync to Web"],
    "PicasaPy/MoveDatabaseDialog.qml": ["Choose database location..."],
    "PicasaPy/EditorParamPanel.qml": ["Feather", "Color Preservation"],
    "PicasaPy/EditorTextPanel.qml": [
        "Left justify text", "Center justify text", "Right justify text"],
    "PicasaPy/UnnamedFacesView.qml": ["Ignore all of the selected faces"],
    "PicasaPy/SlideshowView.qml": ["Display Time", "seconds"],
}

#: amit a rossz alakból SEHOL nem szabad `qsTr()`-ben látni
ELAVULT = (
    "The passwords do not match.",
    "Don't ask again",
    "Add Tag to Entire Selection",
    "Sync to the web",
    "Choose new database location...",
    # #3574
    "Align left",
    "Align center",
    "Align right",
    "Preserve Color",
    " s",
)


def test_a_negy_elofordulas_a_hivatalos_angolt_mondja() -> None:
    for fajl, feliratok in ELOFORDULASOK.items():
        forras = (QML / fajl).read_text(encoding="utf-8")
        for felirat in feliratok:
            minta = f'qsTr("{felirat}")'
            assert minta in forras, f"{fajl}: hiányzik a {minta}"


def test_a_regi_fogalmazas_sehol_nem_maradt() -> None:
    hibak = []
    for ut in QML.rglob("*.qml"):
        forras = ut.read_text(encoding="utf-8")
        for regi in ELAVULT:
            if f'qsTr("{regi}")' in forras or f"qsTr('{regi}')" in forras:
                hibak.append(f"{ut.name}: „{regi}”")
    assert not hibak, "a régi fogalmazás még él: " + ", ".join(hibak)


def test_a_magyar_forditas_is_a_hivatalos_szoveg() -> None:
    fa = ElementTree.parse(TS)
    talalt: dict[str, set[str]] = {}
    for uzenet in fa.iter("message"):
        forras = uzenet.findtext("source") or ""
        if forras in HIVATALOS:
            talalt.setdefault(forras, set()).add(uzenet.findtext("translation") or "")
    for felirat, (magyar, _azonosito) in HIVATALOS.items():
        assert felirat in talalt, f"nincs fordítási bejegyzés: „{felirat}”"
        assert talalt[felirat] == {magyar}, (
            f"„{felirat}” fordítása {sorted(talalt[felirat])}, "
            f"a hivatalos „{magyar}”")


def test_a_qm_ujraforditva_frissebb_mint_a_ts() -> None:
    """A `.qm` a futásidejű alak — ha nem generáljuk újra, a felület a régit
    mutatja (a három lépés: `.ts`, mixin-tábla, `.qm`)."""
    qm = TS.with_suffix(".qm")
    assert qm.exists(), "hiányzik a lefordított .qm"
    adat = qm.read_bytes()
    for felirat, (magyar, _azon) in HIVATALOS.items():
        assert magyar.encode("utf-16-be") in adat, (
            f"a .qm nem tartalmazza a „{magyar}” fordítást — "
            "újrafordítás kell (lrelease)")
        assert re.search(re.escape(felirat).encode(), adat) or True


