"""A nyomatméret-vezérlő a felület NYELVÉHEZ igazodik (#1961).

Magyar felületen a metrikus hatost kell felkínálnia (5×8 … 20×25 cm +
Teljes oldal), angolon a mért hüvelykes ötöst. A készlet-definíció és a
„miért a nyelv dönt" a `picasapy.printing.dpi`-ben áll.

A tárolt méret (`print/lastSize`, az eredeti `PrintLastSize`-ja) átélheti
a nyelvváltást — ilyenkor a KÉSZLETEN KÍVÜLI értéket nem szabad
visszaadni, különben a párbeszéd olyan méretet mutatna, ami nincs is a
listájában.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.language_controller import LANGUAGE_KEY
from picasapy.app.print_controller import PrintController
from picasapy.printing.dpi import HUVELYK_KESZLET, METRIKUS_KESZLET


def _vezerlo(tmp_path, nyelv: str | None) -> PrintController:
    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    if nyelv is not None:
        beallitasok.setValue(LANGUAGE_KEY, nyelv)
    return PrintController(photo_source=list, settings=beallitasok)


class TestAFelkinaltKeszlet:
    def test_magyarul_a_metrikus_hatos(self, tmp_path):
        ctl = _vezerlo(tmp_path, "hu")
        assert ctl.printSizes() == [m.name for m in METRIKUS_KESZLET]

    def test_angolul_a_huvelykes_otos(self, tmp_path):
        ctl = _vezerlo(tmp_path, "en")
        assert ctl.printSizes() == [m.name for m in HUVELYK_KESZLET]

    def test_beallitas_nelkul_a_huvelykes(self, tmp_path):
        """Az alapértelmezett felületi nyelv az angol."""
        ctl = _vezerlo(tmp_path, None)
        assert ctl.printSizes() == [m.name for m in HUVELYK_KESZLET]


class TestATaroltMeret:
    def test_a_magyar_alapertelmezes_a_10x15(self, tmp_path):
        """A metrikus készlet legelterjedtebb fotómérete — a hüvelykes
        4×6 megfelelője."""
        assert _vezerlo(tmp_path, "hu").printSize() == "M10X15CM"

    def test_az_angol_alapertelmezes_a_4x6(self, tmp_path):
        assert _vezerlo(tmp_path, "en").printSize() == "M4X6"

    @pytest.mark.parametrize(
        "nyelv,idegen,vart",
        [
            ("hu", "M8X10", "M10X15CM"),
            ("en", "M20X25CM", "M4X6"),
        ],
    )
    def test_a_MASIK_keszlet_erteket_nem_adja_vissza(
        self, tmp_path, nyelv, idegen, vart
    ):
        """A foga: nyelvváltás után a régi méret bent maradna, és a
        párbeszéd olyan tételt mutatna, ami nincs a listájában."""
        ctl = _vezerlo(tmp_path, nyelv)
        ctl._settings.setValue("print/lastSize", idegen)
        assert ctl.printSize() == vart

    def test_a_sajat_keszletbeli_ertek_MEGMARAD(self, tmp_path):
        """Az esés ne mossa el a valódi választást."""
        ctl = _vezerlo(tmp_path, "hu")
        ctl.setPrintSize("M13X18CM")
        assert ctl.printSize() == "M13X18CM"

    def test_a_masik_keszlet_erteket_NEM_tarolja_el(self, tmp_path):
        ctl = _vezerlo(tmp_path, "hu")
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
            "M3_5X5": "3.5 x 5",
            "M4X6": "4 x 6",
            "M5X7": "5 x 7",
            "M8X10": "8 x 10",
            "TARCA": "Wallet",
            "M5X8CM": "5 x 8 cm",
            "M9X13CM": "9 x 13 cm",
            "M10X15CM": "10 x 15 cm",
            "M13X18CM": "13 x 18 cm",
            "M20X25CM": "20 x 25 cm",
            "TELJES_OLDAL": "FullPage",
        }
        assert self._felirat_terkep() == vart
