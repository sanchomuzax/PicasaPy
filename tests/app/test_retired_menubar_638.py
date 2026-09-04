"""A felső menüsáv megszűnt webes tételei — #638.

A #422 vezette be a `retired` jelölést (véglegesen szürke, pont nélkül, nem
hátralévő munka) és alkalmazta a jobbklikk-menűkre; ez a készlet a felső
menüsáv ugyanolyan tételeit rögzíti.

**A tulajdonos döntése (2026-08-14):** a megszűnt Picasa-szolgáltatások ÉS a
külső Google-integrációk kapják meg a végleges szürkét. Ami nálunk
megvalósítható maradna (Frissítések keresése, Súgó), az **helyfoglaló marad**
— erre külön ellenpróba van, mert egy megvalósítható funkció „véglegesen
halottnak" jelölése ugyanolyan hiba, mint fordítva.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_QML = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
)

#: Megszűnt szolgáltatás — véglegesen szürke.
NYUGDIJAZOTT = (
    # a Picasa Webalbumok (2016) feltöltési útjai
    "Upload Manager...",
    "Batch Upload...",
    # a Picasa termékoldalai
    "Picasa Forums",
    "Online Information",
    "Product Release Notes",
    "Privacy Policy",
    "Terms of Service",
    # külső Google-integrációk, amiknek a Picasa-oldali kapcsolata megszűnt
    "Publish to Blogger...",
    "Order Prints...",
    "Import From Google Photos...",
)

#: Nálunk MEGVALÓSÍTHATÓ — marad helyfoglaló.
#:
#: ⚠️ #2054: a „Help Contents and Index" KIKERÜLT innen, mert **elkészült**.
#: A súgó szövege a csomagban van (`picasapy/help/`), a menütétel valódi
#: `MenuItem`, és az F1 is él. A lista tehát azért rövidült, mert javult
#: valami — nem azért, mert engedtünk a mércéből. Ha a tétel valaha
#: visszaesne helyfoglalóvá, a `TestAmiMegvalosithato` már nem szólna;
#: azt a `test_sugo_bekotes_2054.py` fogja meg (a tétel engedélyezett, és
#: kattintásra megnyílik a néző).
HELYFOGLALO_MARAD = (
    "Check for Updates",
    "Set as Desktop Background...",
    "Make a Gift CD...",
)


@pytest.fixture(scope="module")
def forras() -> str:
    # #2152: az `&` a MNEMONIK jelölése, nem a felirat tartalma — ez a
    # fájl a kivezetett menütételek MEGLÉTÉT méri, arra nézve jelölés.
    return _QML.read_text(encoding="utf-8").replace("&", "")


def _tetel_sora(forras: str, felirat: str) -> str:
    minta = re.compile(
        r"^.*qsTr\(\"" + re.escape(felirat) + r"\"\).*$", re.M
    )
    talalat = minta.findall(forras)
    assert len(talalat) == 1, f"{felirat!r}: {len(talalat)} találat"
    return talalat[0]


class TestANyugdijazottak:
    @pytest.mark.parametrize("felirat", NYUGDIJAZOTT)
    def test_retired_es_nem_helyfoglalo(self, forras: str, felirat: str) -> None:
        sor = _tetel_sora(forras, felirat)

        assert "retired: true" in sor, f"{felirat}: megszűnt szolgáltatás"
        assert "placeholder: true" not in sor, (
            f"{felirat}: helyfoglalóként egy későbbi kör hátralévő munkának "
            "olvasná"
        )


class TestAmiMegvalosithato:
    """Ellenpróba: ami nálunk megépíthető, azt nem temetjük el."""

    @pytest.mark.parametrize("felirat", HELYFOGLALO_MARAD)
    def test_helyfoglalo_marad(self, forras: str, felirat: str) -> None:
        sor = _tetel_sora(forras, felirat)

        assert "placeholder: true" in sor
        assert "retired: true" not in sor


class TestAKetFeluletUgyanaztMondja:
    """#422 + #638: a jobbklikk-menü és a menüsáv nem mondhat mást ugyanarról
    a fajta tételről — ez volt a jegy indoka."""

    def test_a_feltoltes_mindket_helyen_nyugdijazott(self, forras: str) -> None:
        kontextus = (
            _QML.parent / "PhotoContextMenu.qml"
        ).read_text(encoding="utf-8")

        assert "retired: true" in kontextus
        assert "retired: true" in forras
