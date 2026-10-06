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
from picasapy.printing.dpi import HUVELYK_KESZLET, METRIKUS_KESZLET


def _vezerlo(tmp_path, nyelv: str | None, monkeypatch, meresi_rendszer):
    class HelyettesitettQLocale:
        MeasurementSystem = QLocale.MeasurementSystem

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
        "nyelv,meresi_rendszer,vart",
        [
            (
                "en",
                QLocale.MeasurementSystem.MetricSystem,
                METRIKUS_KESZLET,
            ),
            (
                "hu",
                QLocale.MeasurementSystem.ImperialUSSystem,
                HUVELYK_KESZLET,
            ),
        ],
    )
    def test_a_feluleti_nyelvtol_fuggetlenul_a_meresi_rendszer_dont(
        self, tmp_path, monkeypatch, nyelv, meresi_rendszer, vart
    ):
        ctl = _vezerlo(tmp_path, nyelv, monkeypatch, meresi_rendszer)
        assert ctl.printSizes() == [m.name for m in vart]

    @pytest.mark.parametrize(
        "nyelv,meresi_rendszer,vart",
        [
            (
                "en",
                QLocale.MeasurementSystem.MetricSystem,
                ["M5X8CM", "M9X13CM", "M10X15CM", "M13X18CM", "M20X25CM"],
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
            "M9X13CM",
            "M10X15CM",
            "M13X18CM",
            "M20X25CM",
        ]


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
        "nyelv,meresi_rendszer,idegen,vart",
        [
            (
                "en",
                QLocale.MeasurementSystem.MetricSystem,
                "M8X10",
                "TELJES_OLDAL",
            ),
            (
                "hu",
                QLocale.MeasurementSystem.ImperialUSSystem,
                "M20X25CM",
                "TELJES_OLDAL",
            ),
        ],
    )
    def test_a_MASIK_keszlet_erteket_nem_adja_vissza(
        self, tmp_path, monkeypatch, nyelv, meresi_rendszer, idegen, vart
    ):
        """A foga: területváltás után a régi méret bent maradna, és a
        párbeszéd olyan tételt mutatna, ami nincs a listájában."""
        ctl = _vezerlo(tmp_path, nyelv, monkeypatch, meresi_rendszer)
        ctl._settings.setValue("print/lastSize", idegen)
        assert ctl.printSize() == vart

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

    def test_a_masik_keszlet_erteket_NEM_tarolja_el(self, tmp_path, monkeypatch):
        ctl = _vezerlo(
            tmp_path,
            "hu",
            monkeypatch,
            QLocale.MeasurementSystem.MetricSystem,
        )
        ctl.setPrintSize("M13X18CM")
        ctl.setPrintSize("M8X10")
        assert ctl.printSize() == "M13X18CM"


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
            "TELJES_OLDAL": "FullPage",
            # `ytPrintSizes::ePassport` — csak az Útlevélkép állítja be (#1401)
            "PASSPORT": "Passport",
            # #3712: az Indexképek a méretlista tétele, nem külön kapcsoló —
            # a `CONTACT` a QML-only azonosító (nincs `NyomatMeret` tagja).
            # #3712-review: a felirat a HIVATALOS `ytPrintSizes::eContact`
            # szöveg ("Contact Sheet", stringres 3491) — nem saját kisbetűs
            # fogalmazás.
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
