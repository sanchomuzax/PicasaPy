"""A #707 UI-lefedettség megfeleltetés-tábláinak épsége.

A lefedettség-táblát (`docs/specs/ui-lefedettseg.md`) a privát repó
`eszkozok/ui_lefedettseg.py` szkriptje generálja, de a **kézzel gondozott
megfeleltetés** itt, a publikus repóban él — ott, ahol a QML is. Ezért itt kell
őrizni is: ha valaki átnevez vagy töröl egy QML-fájlt, a megfeleltetés némán
elavulna, és a következő generálás rosszul mutatná, mi van meg nálunk.

Ezek a tesztek NEM igényelnek semmit a privát repóból.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]
QML_GYOKER = GYOKER / "src" / "picasapy" / "app" / "qml"
MEGFELELTETES = GYOKER / "docs" / "specs" / "ui-lefedettseg-megfeleltetes.csv"
ELEM_MEGFELELTETES = GYOKER / "docs" / "specs" / "ui-lefedettseg-elemek.csv"

PANEL_ALLAPOTOK = {"parositva", "nincs-megfeleltetes", "nem-cel"}
ELEM_ALLAPOTOK = {"megvan", "hianyzik"}


def _sorok(ut: Path) -> list[dict]:
    with ut.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def panel_sorok() -> list[dict]:
    return _sorok(MEGFELELTETES)


@pytest.fixture(scope="module")
def elem_sorok() -> list[dict]:
    return _sorok(ELEM_MEGFELELTETES)



def _bizonyitek_hibai(hivatkozas: str) -> list[str]:
    """Üres lista, ha a `fájl` / `fájl:sor` hivatkozás megáll a fán.

    Külön függvény, hogy a sorszám-leválasztás EGY helyen éljen, és a
    hibaüzenet megmondja, MELYIK fele bukott — a „nincs ilyen fájl" és a
    „rövidebb a fájl, mint a hivatkozott sor" két különböző hiba, és
    másképp kell javítani.
    """
    fajl, _, sor_szoveg = hivatkozas.partition(":")
    ut = QML_GYOKER / fajl
    if not ut.is_file():
        return ["nincs ilyen fájl"]
    if not sor_szoveg:
        return []
    try:
        sorszam = int(sor_szoveg)
    except ValueError:
        return [f"a sorszám nem szám: {sor_szoveg!r}"]
    if sorszam < 1:
        return [f"a sorszám nem pozitív: {sorszam}"]
    sorok = ut.read_text(encoding="utf-8").splitlines()
    if sorszam > len(sorok):
        return [f"a fájl {len(sorok)} soros, a hivatkozás {sorszam}"]
    return []

class TestPanelMegfeleltetes:
    def test_letezik(self):
        assert MEGFELELTETES.is_file()
        assert ELEM_MEGFELELTETES.is_file()

    def test_nincs_tobbletoszlop(self, panel_sorok):
        """Idézőjel nélküli vessző a megjegyzésben — némán csonkítana."""
        hibas = [sor["panel"] for sor in panel_sorok if None in sor]
        assert not hibas, f"idézőjelezetlen vessző ezekben a sorokban: {hibas}"

    def test_ervenyes_allapotok(self, panel_sorok):
        rosszak = {
            sor["panel"]: sor["allapot"]
            for sor in panel_sorok
            if sor["allapot"] not in PANEL_ALLAPOTOK
        }
        assert not rosszak

    def test_nincs_ismetlodo_panel(self, panel_sorok):
        nevek = [sor["panel"] for sor in panel_sorok]
        assert len(nevek) == len(set(nevek))

    def test_minden_hivatkozott_qml_letezik(self, panel_sorok):
        hianyzo: list[str] = []
        for sor in panel_sorok:
            for fajl in filter(None, sor["qml_fajlok"].split(";")):
                if not (QML_GYOKER / fajl.strip()).is_file():
                    hianyzo.append(f"{sor['panel']} -> {fajl.strip()}")
        assert not hianyzo, (
            "a megfeleltetés nem létező QML-re hivatkozik (átnevezés után "
            f"frissíteni kell): {hianyzo}"
        )

    def test_parositott_panelhez_van_fajl(self, panel_sorok):
        uresek = [
            sor["panel"]
            for sor in panel_sorok
            if sor["allapot"] == "parositva" and not sor["qml_fajlok"].strip()
        ]
        assert not uresek

    def test_nem_parositott_panelhez_nincs_fajl(self, panel_sorok):
        """A „nincs megfeleltetés” állapot ne rejtsen el mégis egy fájlt."""
        ellentmondasok = [
            sor["panel"]
            for sor in panel_sorok
            if sor["allapot"] != "parositva" and sor["qml_fajlok"].strip()
        ]
        assert not ellentmondasok

    def test_minden_panelnek_van_megjegyzese_ha_nem_parositott(
        self, panel_sorok
    ):
        """Az indoklás nélküli kihagyás pont az a csendes kimaradás, ami ellen
        az egész #707 szól."""
        indoklatlan = [
            sor["panel"]
            for sor in panel_sorok
            if sor["allapot"] != "parositva"
            and not (sor.get("megjegyzes") or "").strip()
        ]
        assert not indoklatlan


class TestElemFelulbiralasok:
    def test_nincs_tobbletoszlop(self, elem_sorok):
        hibas = [sor["elem"] for sor in elem_sorok if None in sor]
        assert not hibas

    def test_ervenyes_allapotok(self, elem_sorok):
        rosszak = {
            sor["elem"]: sor["allapot"]
            for sor in elem_sorok
            if sor["allapot"] not in ELEM_ALLAPOTOK
        }
        assert not rosszak

    def test_elemnev_panel_elotaggal(self, elem_sorok, panel_sorok):
        panelek = {sor["panel"] for sor in panel_sorok}
        rosszak = [
            sor["elem"]
            for sor in elem_sorok
            if "/" not in sor["elem"]
            or sor["elem"].split("/", 1)[0] not in panelek
        ]
        assert not rosszak, f"ismeretlen panel-előtagú elem: {rosszak}"

    def test_megvan_allapothoz_letezo_bizonyitek_kell(self, elem_sorok):
        """A „megvan” állítást létező QML-fájllal kell alátámasztani.

        A bizonyíték `fájl` vagy `fájl:sor` alakú lehet. A sorszám nem
        díszítés: enélkül a „megvan” állítás egy 2000 soros fájlra mutat,
        és ellenőrizni éppolyan drága, mint elölről megkeresni. Ezért ha
        van sorszám, azt is ellenőrizzük — a fájlnak legalább annyi sora
        kell legyen.

        ⚠️ Ez az ág a #1858-cal került be, és a `main`-t PIROSRA vitte:
        az őr a teljes `fájl:sor` szöveget adta át az `is_file()`-nak,
        ami sosem lehet igaz. A javítás a sorszámot LEVÁLASZTJA, és
        külön ellenőrzi — a bizonyíték pontosabb lett, nem gyengébb.
        """
        hibas: list[str] = []
        for sor in elem_sorok:
            if sor["allapot"] != "megvan":
                continue
            bizonyitekok = [
                darab.strip()
                for darab in (sor.get("bizonyitek") or "").split(";")
                if darab.strip()
            ]
            if not bizonyitekok:
                hibas.append(f"{sor['elem']}: nincs bizonyíték")
                continue
            for hivatkozas in bizonyitekok:
                hibas.extend(
                    f"{sor['elem']} -> {hivatkozas} ({ok})"
                    for ok in _bizonyitek_hibai(hivatkozas)
                )
        assert not hibas

    def test_nincs_ismetlodo_elem(self, elem_sorok):
        nevek = [sor["elem"] for sor in elem_sorok]
        assert len(nevek) == len(set(nevek))
