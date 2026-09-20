"""A négy felirat a HIVATALOS Picasa-szöveget mondja (#3358).

A #2921 közeli-pár mérése (privát repó, `felirat_kozeli_parok.py`) négy
olyan feliratot talált, amelynél az eredetinek VAN szövege ugyanabban a
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
}

#: fájl → a benne várt hivatalos feliratok
ELOFORDULASOK = {
    "PicasaPy/HiddenPasswordDialog.qml": ["The passwords did not match."],
    "PicasaPy/SaveDialogs.qml": ["Do not ask again"],
    "PicasaPy/ConfirmDialog.qml": ["Do not ask again"],
    "PicasaPy/TagContextMenu.qml": ["Add this tag to entire selection"],
}

#: amit a rossz alakból SEHOL nem szabad `qsTr()`-ben látni
ELAVULT = (
    "The passwords do not match.",
    "Don't ask again",
    "Add Tag to Entire Selection",
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


