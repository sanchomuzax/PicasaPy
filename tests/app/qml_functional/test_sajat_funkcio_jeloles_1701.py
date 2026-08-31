"""#1701 — a PicasaPy SAJÁT parancsai látható jelölést kapnak a menüben.

A tulajdonos döntése (2026-08-28,
`docs/decisions/sajat-funkciok-jelolese.md`), közvetlenül azután, hogy a
duplikátum-áthelyezésről (#1697) kiderült: nem az eredeti viselkedése,
hanem a mi bővítésünk.

**A jelölés a felirat KÉK SZÍNE, nem pötty a jobb szélen.** A döntéslap
kimondja, miért: a jobb szél már foglalt, a feliratok gyorsbillentyűt
hordoznak, és azt a Qt oda igazítja.

**A szín önmagában nem elég** — színvakság miatt a buboréksúgó kötelező.
Ezt a teszt külön állítja.

⚠️ Három KÜLÖN fogalom, nem keverendő:
`placeholder` = még nem működik · `retired` = volt, de kivezettük ·
`sajat` = az eredetiben soha nem is létezett.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject

import picasapy.app

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"

#: A ma megjelölt saját parancsaink. A teljes leltár a jegy szerint
#: hatókörön kívül — de ami MEG VAN jelölve, arra az őr érvényes.
SAJAT_TETELEK = ("menuHelpTesztuzem", "menuHelpSendLog")

#: Eredeti Picasa-parancsok — ezeken NEM lehet jelölés.
EREDETI_TETELEK = ("menuFileSave", "menuFileExit", "menuToolsDedup")


class TestAJelolesLatszik:
    @pytest.mark.parametrize("nev", SAJAT_TETELEK)
    def test_a_sajat_tetel_kek(self, qml_app, nev):
        window, _controller, _engine = qml_app
        tetel = window.findChild(QObject, nev)
        assert tetel is not None, f"{nev} nem található"
        assert tetel.property("sajat") is True, (
            f"{nev} nincs saját funkcióként megjelölve (#1701)"
        )
        tartalom = tetel.property("contentItem")
        assert tartalom is not None
        szin = tartalom.property("color")
        ink = window.findChild(QObject, "menuFileExit").property(
            "contentItem"
        ).property("color")
        assert szin != ink, (
            f"{nev} felirata ugyanolyan színű, mint egy eredeti parancsé — "
            "a jelölés nem látszik"
        )

    @pytest.mark.parametrize("nev", SAJAT_TETELEK)
    def test_a_sajat_tetel_buboreksugoja_kimondja(self, qml_app, nev):
        """A szín önmagában nem hordozhat információt (színvakság)."""
        window, _controller, _engine = qml_app
        tetel = window.findChild(QObject, nev)
        # a csatolt `ToolTip.text` nem olvasható ki `property()`-vel,
        # ezért a komponens saját tulajdonságban is tartja (ld. ott)
        sugo = tetel.property("sajatSugo")
        assert sugo, (
            f"{nev} buboréksúgója üres — a jelölés színvakok számára "
            "semmit nem mond (#1701)"
        )
        assert "PicasaPy" in sugo, (
            f"a súgó nem mondja ki, hogy ez a PicasaPy kiegészítése: {sugo!r}"
        )

    @pytest.mark.parametrize("nev", EREDETI_TETELEK)
    def test_az_eredeti_parancs_nincs_megjelolve(self, qml_app, nev):
        """A jelölés NEM jár olyanra, ami az eredetiben létezik."""
        window, _controller, _engine = qml_app
        tetel = window.findChild(QObject, nev)
        assert tetel is not None, f"{nev} nem található"
        assert tetel.property("sajat") is not True, (
            f"{nev} eredeti Picasa-parancs, mégis saját funkcióként van "
            "megjelölve (#1701)"
        )


class TestADontesKotese:
    def test_a_dontes_kotes_szakasza_ki_van_toltve(self):
        """A döntéslap `## Kötés` szakasza nem maradhat üresen — enélkül a
        döntés és a megvalósítás nem találna egymásra."""
        # tests/app/qml_functional/<ez a fájl> → a repó gyökere
        lap = (
            Path(__file__).resolve().parents[3]
            / "docs" / "decisions" / "sajat-funkciok-jelolese.md"
        )
        assert lap.exists(), f"a döntéslap nincs meg: {lap}"
        szoveg = lap.read_text(encoding="utf-8")
        assert "nincs megvalósítva" not in szoveg, (
            "a döntéslap még mindig „nincs megvalósítva\"-t ír"
        )
        assert "nincs őr" not in szoveg, (
            "a döntéslap még mindig „nincs őr\"-t ír"
        )
        assert "PicasaMenuItem.qml" in szoveg, (
            "a `Megvalósítja` sor nem nevezi meg a komponenst"
        )
