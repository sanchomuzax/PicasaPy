"""A nyomatméret-családot a rendszer területi mértékegysége választja (#4435).

A katalógus meglévő metrikus és hüvelykes elemei, sorrendje és Teljes oldal
eleme megmarad. A területi beállítás választja ki a családot, az öt
gyorsválasztó alapértékét pedig a spec szerinti sorrendben adja; a mentett
gyorsválasztó felülírja az alapértéket.

A tárolt méret (`print/lastSize`, az eredeti `PrintLastSize`-ja) átélheti
a területi mértékegység váltását — ilyenkor a KÉSZLETEN KÍVÜLI értéket
nem szabad visszaadni, különben a párbeszéd olyan méretet mutatna, ami
nincs is a listájában.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QLocale, QSettings

import picasapy.printing.dpi as dpi
from picasapy.app.language_controller import LANGUAGE_KEY
from picasapy.app.print_controller import PrintController


def _vezerlo(tmp_path, nyelv: str | None, monkeypatch, meresi_rendszer):
    class HelyettesitettQLocale:
        MeasurementSystem = QLocale.MeasurementSystem

        @classmethod
        def system(cls):
            return cls()

        def measurementSystem(self):
            return meresi_rendszer

    monkeypatch.setattr(dpi, "QLocale", HelyettesitettQLocale, raising=False)
    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    if nyelv is not None:
        beallitasok.setValue(LANGUAGE_KEY, nyelv)
    return PrintController(photo_source=list, settings=beallitasok)


class TestATeruletiMereshezIgazodoKeszlet:
    @pytest.mark.parametrize(
        "nyelv,meresi_rendszer",
        [
            (
                "en",
                QLocale.MeasurementSystem.MetricSystem,
            ),
            (
                "hu",
                QLocale.MeasurementSystem.ImperialUSSystem,
            ),
        ],
    )
    def test_a_teljes_katalogus_fuggetlen_a_feluleti_es_teruleti_nyelvtol(
        self, tmp_path, monkeypatch, nyelv, meresi_rendszer
    ):
        ctl = _vezerlo(tmp_path, nyelv, monkeypatch, meresi_rendszer)
        assert ctl.printSizes() == [
            "M3X4", "M3_5X5", "M4X5", "M4X6", "M5X7", "M8X10",
            "M5X8CM", "M9X13CM", "M10X15CM", "M13X18CM", "M15X20CM",
            "M20X25CM", "TARCA", "CDSIZE", "PASSPORT", "CONTACT",
            "TELJES_OLDAL",
        ]

    @pytest.mark.parametrize(
        "nyelv,meresi_rendszer,vart",
        [
            (
                "en",
                QLocale.MeasurementSystem.MetricSystem,
                ["M10X15CM", "M13X18CM", "M15X20CM", "M20X25CM", "CONTACT"],
            ),
            (
                "hu",
                QLocale.MeasurementSystem.ImperialUSSystem,
                ["TARCA", "M3_5X5", "M4X6", "M5X7", "M8X10"],
            ),
        ],
    )
    def test_az_ot_gyorsvalaszto_alapmeret_a_spec_szerinti_sorrendben(
        self, tmp_path, monkeypatch, nyelv, meresi_rendszer, vart
    ):
        ctl = _vezerlo(tmp_path, nyelv, monkeypatch, meresi_rendszer)
        assert ctl.printSizePresets() == vart

    def test_a_mentett_gyorsvalaszto_felulirja_a_teruleti_alaperteket(
        self, tmp_path, monkeypatch
    ):
        ctl = _vezerlo(
            tmp_path,
            "en",
            monkeypatch,
            QLocale.MeasurementSystem.MetricSystem,
        )
        ctl._settings.setValue("printing/sizePreset1", "M8X10")
        assert ctl.printSizePresets() == [
            "M8X10",
            "M13X18CM",
            "M15X20CM",
            "M20X25CM",
            "CONTACT",
        ]

    def test_a_mentett_teljes_oldal_gyorsvalaszto_a_teruleti_alapra_esik_vissza(
        self, tmp_path, monkeypatch
    ):
        ctl = _vezerlo(
            tmp_path,
            "en",
            monkeypatch,
            QLocale.MeasurementSystem.MetricSystem,
        )
        ctl._settings.setValue("printing/sizePreset5", "TELJES_OLDAL")

        assert ctl.printSizePresets() == [
            "M10X15CM",
            "M13X18CM",
            "M15X20CM",
            "M20X25CM",
            "CONTACT",
        ]

    def test_az_opciok_meretlistaja_tizenhat_tetelu_teljes_oldal_nelkul(
        self, tmp_path, monkeypatch
    ):
        ctl = _vezerlo(
            tmp_path,
            "en",
            monkeypatch,
            QLocale.MeasurementSystem.MetricSystem,
        )

        meretek = ctl.printOptionSizes()
        assert len(meretek) == 16
        assert "TELJES_OLDAL" not in meretek


class TestATaroltMeret:
    @pytest.mark.parametrize(
        "meresi_rendszer",
        [
            QLocale.MeasurementSystem.MetricSystem,
            QLocale.MeasurementSystem.ImperialUSSystem,
        ],
    )
    def test_az_alapertelmezes_a_teljes_oldal(
        self, tmp_path, monkeypatch, meresi_rendszer
    ):
        """#3733: az eredetiben az első megnyitás alapállása FullPage
        (`docs/specs/picasa-nyomtatas.md`, a Colab EN 29/30 élő mérése:
        „az alapállás Full Page") — mindkét nyelven ugyanez."""
        ctl = _vezerlo(tmp_path, "en", monkeypatch, meresi_rendszer)
        assert ctl.printSize() == "TELJES_OLDAL"

    @pytest.mark.parametrize(
        "nyelv,meresi_rendszer,idegen",
        [
            (
                "en",
                QLocale.MeasurementSystem.MetricSystem,
                "M8X10",
            ),
            (
                "hu",
                QLocale.MeasurementSystem.ImperialUSSystem,
                "M20X25CM",
            ),
        ],
    )
    def test_a_masik_teruleti_katalogusbol_valasztott_meret_megmarad(
        self, tmp_path, monkeypatch, nyelv, meresi_rendszer, idegen
    ):
        """A teljes `ytPrintSizes` katalógus minden területen elérhető."""
        ctl = _vezerlo(tmp_path, nyelv, monkeypatch, meresi_rendszer)
        ctl._settings.setValue("print/lastSize", idegen)
        assert ctl.printSize() == idegen

    def test_a_sajat_keszletbeli_ertek_MEGMARAD(self, tmp_path, monkeypatch):
        """Az esés ne mossa el a valódi választást."""
        ctl = _vezerlo(
            tmp_path,
            "hu",
            monkeypatch,
            QLocale.MeasurementSystem.MetricSystem,
        )
        ctl.setPrintSize("M13X18CM")
        assert ctl.printSize() == "M13X18CM"

    def test_a_masik_teruleti_meretet_is_elmenti(self, tmp_path, monkeypatch):
        ctl = _vezerlo(
            tmp_path,
            "hu",
            monkeypatch,
            QLocale.MeasurementSystem.MetricSystem,
        )
        ctl.setPrintSize("M13X18CM")
        ctl.setPrintSize("M8X10")
        assert ctl.printSize() == "M8X10"


class TestAFeliratokAQMLben:
    """A vezérlő azonosítót ad, a felirat a QML-é — a lánc két vége
    külön-külön zöld lehet úgy is, hogy a felhasználó üres sort lát.
    """

    @staticmethod
    def _felirat_terkep() -> dict[str, str]:
        """A `printSizeLabelById` blokk kulcsai és `qsTr`-szövegei.

        Csak a blokkot olvassuk, hogy egy kommentben szereplő azonosító
        ne számítson találatnak."""
        import re
        from pathlib import Path

        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "PrintDialog.qml"
        ).read_text(encoding="utf-8")
        kezdet = forras.index("printSizeLabelById")
        blokk = forras[kezdet : forras.index("})", kezdet)]
        return dict(re.findall(r'"(\w+)":\s*qsTr\("([^"]+)"\)', blokk))

    def test_minden_meretnek_van_felirata(self):
        """A foga: új méret felirat nélkül itt bukik el, nem a
        felhasználónál egy üres legördülő-sorral."""
        from picasapy.printing.dpi import NyomatMeret

        terkep = self._felirat_terkep()
        hianyzo = [tag.name for tag in NyomatMeret if tag.name not in terkep]
        assert not hianyzo, f"nincs QML-felirata: {hianyzo}"

    def test_a_feliratok_a_hivatalos_szovegtarbol_valok(self):
        """`ytPrintSizes::` (`stringres` 3478–3494) — nem saját fogalmazás.

        A `FullPage` szándékosan fordítatlan: az `eFullPage` sor magyarul
        is ezt adja."""
        vart = {
            "M3X4": "3 x 4",
            "M3_5X5": "3.5 x 5",
            "M4X5": "4 x 5",
            "M4X6": "4 x 6",
            "M5X7": "5 x 7",
            "M8X10": "8 x 10",
            "TARCA": "Wallet",
            "M5X8CM": "5 x 8 cm",
            "M9X13CM": "9 x 13 cm",
            "M10X15CM": "10 x 15 cm",
            "M13X18CM": "13 x 18 cm",
            "M15X20CM": "15 x 20 cm",
            "M20X25CM": "20 x 25 cm",
            "CDSIZE": "CD Cover Size",
            "TELJES_OLDAL": "FullPage",
            # Az útlevélkép saját belépési útja az azonosítót is használja.
            "PASSPORT": "Passport",
            # A felirat eredeti; az indexkép-elrendezés külön út.
            "CONTACT": "Contact Sheet",
        }
        assert self._felirat_terkep() == vart

    def test_az_uj_meretek_magyar_forditasa_a_ts_fajlban_megvan(self):
        import xml.etree.ElementTree as ET
        from pathlib import Path

        import picasapy.app

        ts_ut = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
        kontextus = next(
            elem
            for elem in ET.parse(ts_ut).getroot().findall("context")
            if elem.findtext("name") == "PrintDialog"
        )
        forditasok = {
            uzenet.findtext("source"): uzenet.findtext("translation")
            for uzenet in kontextus.findall("message")
        }
        assert {
            "3 x 4": "3x4",
            "4 x 5": "4x5",
            "15 x 20 cm": "15x20 cm",
        } == {szoveg: forditasok[szoveg] for szoveg in (
            "3 x 4", "4 x 5", "15 x 20 cm"
        )}
