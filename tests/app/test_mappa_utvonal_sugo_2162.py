"""#2162: a mappasor súgója az ELÉRÉSI UTAT mutatja.

Két különböző mappa azonos alapnévvel a lapos listán megkülönböztethetetlen
volt. Nem elméleti: a duplikátum-kereső minden forrásmappában saját
„Duplikátumok" alkönyvtárat hoz létre, tehát a felhasználónál rendszeresen
keletkezik több ilyen nevű mappa (#1909 → #1923).

⚠️ **TUDATOS ELTÉRÉS.** Az eredeti ilyenkor SEMMIT nem mutat — három
független forrásból mérve: a szövegtár 3524 bejegyzése közt nincs
mappasor-súgó; a 141 erőforrás-fa közül a mappalistát egyedül a
Mappakezelő PÁRBESZÉD definiálja (`foldermgr/foldertree`), a bal hasáb
listájának nincs saját eleme; és a panel-gyökér sem tartalmaz ilyet.

Ezért ez az őr azt is rögzíti, hogy a **látható felirat változatlan** (csak
az alapnév) — a felület az eredetivel egyező marad, a többlet csak
rámutatáskor jelenik meg.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.qml_blokk import tulajdonsag_erteke

_QML = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "FolderPane.qml"
)


@pytest.fixture(scope="module")
def forras() -> str:
    return _QML.read_text(encoding="utf-8")


def _tooltip_sor(forras: str, mezo: str) -> str:
    """A `ToolTip.<mezo>` kötésének TELJES szövege.

    #2575: korábban egyetlen SOR volt (`^\\s*ToolTip.text:(.*)$`), és a
    többsoros ternáriust levágta — ezért kellett mellé egy 400 karakteres
    ablak. A `tulajdonsag_erteke` a kötés valódi határáig olvas.
    """
    return tulajdonsag_erteke(forras, f"ToolTip.{mezo}")


def test_a_sugo_MINDEN_mappasoron_megjelenik(forras: str) -> None:
    """A foga: korábban `offline &&` volt a kapu, tehát elérhető mappán
    egyáltalán nem volt súgó — épp ott, ahol a névütközés zavar."""
    felteteI = _tooltip_sor(forras, "visible")
    assert "offline &&" not in felteteI, (
        "a súgó csak offline mappán jelenik meg — az elérhetőkön nincs "
        "névütközés-feloldás: " + felteteI.strip()
    )
    assert 'kind === "folder"' in felteteI, (
        "a súgó nem a mappasorokra van kötve: " + felteteI.strip()
    )


def test_a_sugo_szovege_az_UTVONALAT_tartalmazza(forras: str) -> None:
    szoveg = _tooltip_sor(forras, "text")
    blokk = szoveg
    assert "path" in blokk, (
        "a súgó szövege nem hivatkozik az útvonalra: " + szoveg.strip()
    )
    assert "Currently unavailable" in blokk, (
        "az offline-üzenet eltűnt — a #459/5 jelzése nem veszhet el"
    )


def test_a_LATHATO_felirat_valtozatlan_marad(forras: str) -> None:
    """A többlet CSAK a súgóban van: a sor felirata továbbra is az
    alapnév + darabszám, ahogy az eredetiben."""
    assert 'text: name + " (" + count + ")"' in forras, (
        "a mappasor látható felirata megváltozott — az eltérésnek a "
        "súgóban kell maradnia, nem a feliratban"
    )
