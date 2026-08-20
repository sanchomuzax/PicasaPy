r"""A rendes kollázs-készítés után NINCS értesítés (#1119).

## A tulajdonos jelentése (v0.8.26, képernyőképpel)

> „Ez a gomb egy tévedés, ilyen nincsen a Picasa 3-ban. Ezt már jeleztem
> sokszor, és még mindig nincsen javítva."

**Háromszor** jelezte. Reggel is szóvá tette („Ebből semmit sem értek,
nincsen kontextusom rá"), és akkor magyarázatot kapott, nem javítást.

## A bizonyíték: rossz ághoz kötöttük

A `collage::done` értesítő (`0x0088a020`) a `0x0057aa10`-et hívja, amiben a
`Control Panel\Desktop\` registrykulcs és a `picasabackground.bmp`
szerepel — vagyis az értesítés az **„Asztali háttérkép"** funkcióé, nem a
rendes kollázs-készítésé. A tulajdonos megfigyelése és a bináris összeér.

## ⚠️ A komponens MARAD

A `CollageDoneNotice` **nem törlendő**: az eredetiben LÉTEZIK ez az
értesítés, csak máshol. A bekötése külön jegy (ma a
`collageDesktopBackgroundReady` jelzésnek nincs fogadója). A törlés
visszafejlesztés volna — ezért a teszt a komponens LÉTÉT is állítja.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

QML = Path(picasapy.app.__file__).parent / "qml"


def _main_qml() -> str:
    return (QML / "Main.qml").read_text(encoding="utf-8")


def _kodsorok(forras: str) -> list[str]:
    """A megjegyzés-sorok nélkül — a magyarázat nem hívás."""
    return [
        sor
        for sor in forras.splitlines()
        if not sor.lstrip().startswith(("//", "/*", "*"))
    ]


class TestNincsErtesitesAKeszitesUtan:
    def test_a_locateSavedCollage_NEM_mutat_ertesitest(self):
        forras = _main_qml()
        kezdet = forras.index("function locateSavedCollage")
        veg = forras.index("function folderOfPath")

        assert "collageDoneNotice.showFor" not in "\n".join(
            _kodsorok(forras[kezdet:veg])
        ), "a rendes létrehozás után értesítés jelenik meg (#1119)"

    def test_SEHOL_a_QML_faban_nincs_showFor_hivas(self):
        """Olcsó keresés — a hívás máshonnan se kerüljön vissza."""
        talalatok = [
            f"{ut.name}:{szam}"
            for ut in QML.rglob("*.qml")
            for szam, sor in enumerate(_kodsorok(ut.read_text(encoding="utf-8")), 1)
            if "collageDoneNotice.showFor" in sor
        ]

        assert not talalatok, "visszakerült az értesítés-hívás: " + ", ".join(talalatok)


class TestAKomponensMARAD:
    """Az eredetiben LÉTEZIK ez az értesítés — csak az „Asztali háttérkép"
    ágán. A törlése visszafejlesztés volna (#1119, #1028)."""

    def test_a_CollageDoneNotice_fajl_letezik(self):
        assert (QML / "PicasaPy" / "CollageDoneNotice.qml").is_file()

    def test_a_Main_qml_tovabbra_is_peldanyositja(self):
        assert "CollageDoneNotice {" in _main_qml()


class TestAFolyamatszoveg:
    """A 100%-os szöveg se hívjon kattintásra."""

    def test_nincs_kattintson_ide_a_forrasszovegben(self):
        from picasapy.app import collage_save

        forras = Path(collage_save.__file__).read_text(encoding="utf-8")

        assert "click here" not in forras
        assert 'self.tr("The collage is ready")' in forras
