"""Az export-párbeszéd feliratai — SZÓ SZERINT a honosításból (#1138).

Forrás: `docs/specs/export-parbeszed.md` 2. szakasz — a `Picasa3i18n.dll`
`54978`-as erőforrása. A spec kimondja: **„Ezeket kell használni, nem
újrafordítani."** Ez a teszt a betelepített `.qm`-et tölti be, tehát azt
méri, amit a felhasználó ténylegesen lát — nem a `.ts` forrását.

A #1138 előtt NÉGY felirat tért el:

| eredeti | ami nálunk volt |
|---|---|
| Exportálás mappába | „Exportálás mappába**…**" |
| Exportálási hely: | „Exportálás helye:" |
| Számok hozzáadása a fájlnevekhez a sorrend megőrzése érdekében | „Sorszámozás a fájlnevekben a sorrend megőrzéséhez" |
| Maximum / Minimum | „Maximális" / „Minimális" |

…és a vízjel kis betűs magyarázata egyáltalán nem volt meg.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_I18N_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
)

#: a spec 2. szakaszának teljes táblája, a `.fen` vezérlőneveivel
_FELIRATOK = {
    "Export to Folder": "Exportálás mappába",                  # window1.title
    "Export location:": "Exportálási hely:",                   # labelgroup2
    "Browse...": "Tallózás…",                                  # changeloc
    "Name of exported folder:": "Az exportált mappa neve:",    # labelgroup6
    "Add numbers to file names to preserve order":             # addnumbers
        "Számok hozzáadása a fájlnevekhez a sorrend megőrzése érdekében",
    "Image size:": "Képméret:",                                # labelgroup9
    "Use original size": "Eredeti méret használata",           # radio11
    "Resize to:": "Átméretezés:",                              # radio12
    "pixels": "képpont",                                       # label18
    "Image quality:": "Képminőség:",                           # labelgroup20
    "Automatic": "Automatikus",                                # item23
    "Normal": "Normál",                                        # item24
    "Maximum": "Maximum",                                      # item25
    "Minimum": "Minimum",                                      # item26
    "Preserves original image quality":                        # label30
        "Megőrzi az eredeti képminőséget",
    "Good balance of quality and size":                        # label31
        "A minőség és méret megfelelő egyensúlya",
    "Very large file size, preserves fine detail":             # label32
        "Nagyon nagy méretű fájl, az apró részleteket is megőrzi",
    "Smallest file size, some quality loss":                   # label33
        "Legkisebb fájlméret, némi minőségvesztés",
    "Export movies using:": "Filmek exportálása:",             # labelgroup35
    "First frame": "Első képkocka",                            # radio37
    "Full movie (no resizing)": "Teljes film (nincs átméretezés)",  # radio38
    "Watermark:": "Vízjel:",                                   # labelgroup39
    "Add watermark": "Vízjel hozzáadása",                      # usewatermark
    "Stamp photos with your name, a web domain, or a copyright notice.":
        "A fotókra rábélyegezheti saját nevét, egy internetes domain nevét "
        "vagy egy szerzői jogi közleményt.",                   # label44
    "Export": "Exportálás",                                    # export.title
}


@pytest.fixture(scope="module")
def forditas():
    from PySide6.QtCore import QCoreApplication, QTranslator

    QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N_DIR)), (
        "a picasapy_hu.qm nem tölthető be — lefuttattad a pyside6-lrelease-t?"
    )
    return translator


class TestFeliratokSzoSzerint:
    def test_minden_felirat_a_honositasbol_valo(self, forditas):
        elteres = {
            forras: (forditas.translate("ExportDialogs", forras), varhato)
            for forras, varhato in _FELIRATOK.items()
            if forditas.translate("ExportDialogs", forras) != varhato
        }

        assert not elteres, (
            "a következő feliratok nem egyeznek a honosítás szó szerinti "
            f"szövegével (kapott / várt): {elteres}"
        )

    def test_az_ablakcim_vegen_NINCS_harom_pont(self, forditas):
        """Spec 5.: az eredeti címe „Exportálás mappába" — pont nélkül.
        Az app korábbi elnevezési konvenciója (három pont) itt HIBA volt."""
        cim = forditas.translate("ExportDialogs", "Export to Folder")

        assert not cim.endswith("…") and not cim.endswith("...")

    def test_az_egyeni_fokozat_felirata_szamot_fogad(self, forditas):
        """`„Custom (%d)"` — a `%d` helyén a csúszka tényleges száma
        (`0x0073a0c0`). Nálunk `%1`, a Qt `.arg()`-jához."""
        szoveg = forditas.translate("ExportDialogs", "Custom (%1)")

        assert "%1" in szoveg, szoveg
        assert szoveg.startswith("Egyéni"), szoveg


class TestAlapertelmezettCelmappa:
    """Spec 4.: az alapértelmezett célmappa `Picasa\\Exportálások\\`
    (`CExportPrefsDialog::deffolder`), a mappanév tartaléka `exportálás`
    (`CExportPrefsDialog::exportname`).

    A mérés a MIXIN `self.tr()`-jén megy át, mert a szövegeket az
    `ExportMixin` adja — a `.ts`-t olvasva nem látszik, hogy a
    futásidejű kontextus-feloldás valóban odatalál-e."""

    def test_a_mixin_trje_futasidoben_is_magyarul_ad(self, forditas):
        from PySide6.QtCore import QCoreApplication, QObject

        from picasapy.app.export_controller import ExportMixin

        app = QCoreApplication.instance()
        app.installTranslator(forditas)
        try:
            probe = type("AppController", (QObject, ExportMixin), {})()

            assert probe.tr("Exports") == "Exportálások"
            assert probe.tr("export") == "exportálás"
        finally:
            app.removeTranslator(forditas)
