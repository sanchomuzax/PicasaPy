"""A rajzolt helyi menük megmaradó invariánsai (#886).

## Miért

A #886 döntése (ADR-013, `docs/decisions/menuk-rajzoltak-maradnak.md`):
a menük RAJZOLTAK maradnak, és az eredeti — natív Windows-menü —
LÁTVÁNYÁHOZ igazodnak. A döntés több olyan tulajdonságot rögzít, amit
eddig semmi nem őrzött, pedig némán elveszhet:

* **ikon egyik menütételre sem kerül** — a korábbi „öt ikonos tétel"
  lelet HELYESBÍTVE lett: az a mező a módosító-maszk, nem ikon;
* a **gyorsbillentyű a felirattól `\\t`-tal elválasztva** áll, mert a
  jobb oszlopot így igazítja a Qt — nem külön elemmel rajzoljuk;
* a **panelen belüli legördülők** változatlanul saját rajzolásúak
  (az eredeti is maga rajzolta: `CPopupList`, `ytPopupListNode`);
* a tételek **pipálhatók és tilthatók** maradnak (`CheckMenuItem` 13,
  `EnableMenuItem` 17 hívóhely az eredetiben).

A félkövér alapértelmezett tételt külön őr méri
(`test_felkover_alapertelmezett_886.py`), azt ez a fájl nem ismétli.

## Amit NEM mér

Az XP-menü PONTOS méreteit (sorköz, keret, színek). Azok **nincsenek a
binárisban** — a natív menüt a Windows témamotorja rajzolja —, és mai
Windowson készült képernyőkép sem adja vissza őket. Ez a jegyben is ki
van mondva; a mai értékek a Theme tokenjeiből jönnek.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/PicasaPy"

#: A rajzolt helyi menük — a `*ContextMenu.qml` mintára illeszkedő fájlok.
HELYI_MENUK = sorted(ut.name for ut in QML.glob("*ContextMenu.qml"))


def test_van_mit_ellenorizni() -> None:
    """Üres halmazon minden állítás vakon igaz lenne."""
    assert len(HELYI_MENUK) >= 4, HELYI_MENUK


@pytest.mark.parametrize("nev", HELYI_MENUK)
def test_nincs_ikon_a_menuteteleken(nev: str) -> None:
    """Az eredetiben egyetlen menütételen sincs ikon (a korábbi lelet
    helyesbítve: a mező a módosító-maszk)."""
    forras = (QML / nev).read_text(encoding="utf-8")
    talalatok = [
        sor.strip() for sor in forras.splitlines()
        if re.search(r"^\s*icon\.(source|name)\s*:", sor)
    ]
    assert not talalatok, f"{nev}: ikon került menütételre — {talalatok}"


def test_a_gyorsbillentyu_a_felirattol_tabbal_elvalasztva_all() -> None:
    """A jobb oszlopot a Qt igazítja a `\\t` mentén — nem külön elem."""
    osszes = 0
    for nev in HELYI_MENUK:
        forras = (QML / nev).read_text(encoding="utf-8")
        osszes += len(re.findall(r'\+\s*"\\t[^"]+"', forras))
    assert osszes >= 15, (
        f"csak {osszes} gyorsbillentyű-oszlop a helyi menükben — "
        "a mért tételek egy része elveszett")


@pytest.mark.parametrize("nev", HELYI_MENUK)
def test_a_gyorsbillentyu_nem_a_forditasban_van(nev: str) -> None:
    """A billentyű NEM mehet a `qsTr()`-be: a fordító nyelvenként
    elcsúsztatná, pedig a módosító-előtag a binárisból mért bitmaszk."""
    forras = (QML / nev).read_text(encoding="utf-8")
    rosszak = re.findall(r'qsTr\("[^"]*\\t[^"]*"\)', forras)
    assert not rosszak, f"{nev}: a gyorsbillentyű a fordítandó szövegben — {rosszak}"


def test_a_panelen_beluli_legordulok_sajat_rajzolasuak() -> None:
    """Az eredeti is maga rajzolta őket — a döntés ezt nem érinti."""
    combo = QML / "PicasaComboBox.qml"
    assert combo.is_file(), "eltűnt a saját rajzolású legördülő"
    forras = combo.read_text(encoding="utf-8")
    assert "popup:" in forras, (
        "a legördülő elvesztette a saját `popup` rajzolását")


def test_a_tetelek_tilthatok_maradnak() -> None:
    """Az eredetiben 17 hívóhely tilt és 13 pipál menütételt — a
    mechanizmus tehát él, és nálunk sem veszhet el.

    ⚠️ Ez NEM fájlonkénti követelmény: mérve (2026-09-19) a nyolcból
    kettő menü — a kép- és a mappa-menü — visel állapotfüggő tételt, a
    többi statikus parancslista. A rögzített alsó korlát ezért kettő; a
    fájlonkénti állítás vakon bukna olyan menükön, ahol az eredetiben
    sincs mit tiltani.
    """
    allapotfuggo = [
        nev for nev in HELYI_MENUK
        if re.search(r"^\s*(enabled|visible)\s*:", 
                     (QML / nev).read_text(encoding="utf-8"), re.M)
    ]
    assert len(allapotfuggo) >= 2, (
        f"a tiltás/pipálás mechanizmusa eltűnt — csak {allapotfuggo}")
