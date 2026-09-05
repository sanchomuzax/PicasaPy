"""#1527: a mentés-család MAGYAR feliratai a HIVATALOS szövegek legyenek.

A feliratokat nem mi fogalmazzuk: a Picasa saját magyar erőforrásaiból
valók (`stringres-en-hu.tsv`, a jegyben *megerősített* fokozattal). Egy
átfogalmazott mondat itt nem stíluskérdés — a projekt célja az eredeti
felület pontos újraépítése, és a felhasználó ezeket a mondatokat ismeri.

A QML-funkcionális teszt (`qml_functional/test_mentes_parancsok_1527.py`)
nem tudja ezt mérni: a teszt-fixture nem telepít `QTranslator`-t, tehát ott
a `qsTr()` az ANGOL forrássztringet adja vissza. Ez a fájl ezért közvetlenül
a `picasapy_hu.ts`-t olvassa.

## Az egyes és a többes szám KÉT külön erőforrás

`CThumbUI::FileSave::messagetag1` és `messagetagX` — az eredetiben is két
bejegyzés, és a magyar mondat sem egyetlen szó cseréjével áll elő
(„erről a fájlról" ↔ „ezekről a fájlokról"). Ezért tiltja a teszt, hogy
valaki egyetlen, `%1`-es sztringgé vonja össze őket.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_TS_PATH = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.ts"
)

#: (kontextus, forrássztring) -> a HIVATALOS magyar felirat.
#: A jobb oldal a `stringres-en-hu.tsv` magyar oszlopa, szó szerint.
HIVATALOS: dict[tuple[str, str], str] = {
    # CThumbUI::FileSave::message
    ("SaveDialogs", "Save changes to disk?"): "Lemezre menti a módosításokat?",
    # CThumbUI::FileSave::messagetag1 — EGY fájl
    (
        "SaveDialogs",
        "A backup of this file will be made.",
    ): "A program biztonsági másolatot készít erről a fájlról.",
    # CThumbUI::FileSave::messagetagX — TÖBB fájl
    (
        "SaveDialogs",
        "A backup of these files will be made.",
    ): "A program biztonsági másolatot készít ezekről a fájlokról.",
    # CFileSaveThread:filesaveerr2
    (
        "SaveDialogs",
        "Unable to save file due to filename collision.",
    ): "A fájl mentése nem lehetséges. Már van ilyen nevű fájl.",
    # CFileSaveThread:filesaveerr3
    (
        "SaveDialogs",
        "Unable to save file due to a file format error.",
    ): "Fájlformázási hiba miatt a fájl nem menthető.",
    # IDS_CANT_SAVE_TO_SAME
    (
        "SaveDialogs",
        "Cannot replace image. Please try again with a different filename.",
    ): "A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel.",
    # CThumbUI::SaveAsFilterJPG / SaveAsFilterWebP — a fájlválasztó szűrői
    ("SaveDialogs", "JPEG Files (*.jpg)"): "JPEG-fájlok (*.jpg)",
    ("SaveDialogs", "WebP Files (*.webp)"): "WebP-fájlok (*.webp)",
    # CThumbUI::FileSave::progfile / progfiles — EGY tizedesjegy (%.1f)
    ("SaveProgressPanel", "Saving file %1%"): "Fájl mentése: %1%",
    ("SaveProgressPanel", "Saving %1 files %2%"): "%1 fájl mentése %2%",
    # eMenuFile::ID_FILE_SAVEAS / ID_FILE_SAVEACOPY
    # #2152: a felirat mnemonikot kapott az eredeti honosításából
    ("PicasaMenuBar", "Save &As..."): "Mentés &másként…",
    ("PicasaMenuBar", "Save a Cop&y"): "&Másolat mentése",
    # eMenuFile::ID_FILE_EXIT
    ("PicasaMenuBar", "E&xit"): "&Kilépés",
}


def _forditasok() -> dict[tuple[str, str], str]:
    gyokér = ET.parse(_TS_PATH).getroot()
    ki: dict[tuple[str, str], str] = {}
    for context in gyokér.findall("context"):
        nev = (context.findtext("name") or "").strip()
        for message in context.findall("message"):
            forras = message.findtext("source")
            forditas = message.find("translation")
            if forras is None or forditas is None:
                continue
            ki[(nev, forras)] = forditas.text or ""
    return ki


@pytest.mark.parametrize(("kulcs", "vart"), sorted(HIVATALOS.items()))
def test_a_hivatalos_magyar_felirat_all_a_ts_ben(kulcs, vart):
    forditasok = _forditasok()
    kontextus, forras = kulcs
    assert kulcs in forditasok, (
        f"[{kontextus}] {forras!r} nincs a picasapy_hu.ts-ben"
    )
    assert forditasok[kulcs] == vart, (
        f"[{kontextus}] {forras!r} magyar felirata nem a hivatalos szöveg"
    )


def test_a_lemezhiba_kiirja_a_fajlnevet_es_a_hibakodot():
    """`CFileSaveThread::filesaveerr-win` — a fájlnév és a hibakód a
    hivatalos mondat RÉSZE, nem díszítés: csak ebből derül ki, melyik
    fájlon és milyen rendszerhibával bukott el a mentés."""
    forditasok = _forditasok()
    kulcs = (
        "SaveDialogs",
        "Unable to save all files due to a disk error. The disk may be "
        "full or read-only.\n\n%1\nerror(%2)",
    )
    assert kulcs in forditasok, "a lemezhiba-üzenet hiányzik a .ts-ből"
    szoveg = forditasok[kulcs]
    assert szoveg.startswith(
        "Lemezhiba miatt nem lehetséges az összes fájl mentése."
    ), szoveg
    assert "megtelt vagy írásvédett" in szoveg, szoveg
    assert "%1" in szoveg and "hiba(%2)" in szoveg, (
        "a fájlnév vagy a hibakód helyőrzője kimaradt"
    )


def test_az_egyes_es_a_tobbes_szam_KET_kulon_bejegyzes():
    """Az összevonás tiltása: ha valaki egyetlen `%1`-es sztringre cseréli
    a kettőt, ez a teszt bukik."""
    forditasok = _forditasok()
    egyes = forditasok.get(("SaveDialogs", "A backup of this file will be made."))
    tobbes = forditasok.get(("SaveDialogs", "A backup of these files will be made."))
    assert egyes and tobbes, "az egyik alak hiányzik a .ts-ből"
    assert egyes != tobbes, "a két alak azonos — összevonták őket"
