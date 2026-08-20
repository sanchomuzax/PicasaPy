"""Minden QML-ből hivatkozott vezérlőnek LÉTEZNIE kell (#1066).

## A lelet

Négy vezérlő (`EmailController`, `WebExportController`, `PeopleController`,
`SaveController`, `PrintController`) **soha nem jött létre** a futó
alkalmazásban, és egyik sem volt regisztrálva a QML felé — miközben a
felület hivatkozott rájuk.

A hivatkozások `typeof … !== "undefined"` őr mögött álltak, tehát nem
szálltak el: **némán nem csináltak semmit**. Az `OptionsTabEmail.qml` saját
kommentje ki is mondta:

> „az integrátor teendője az `emailController` context-property
> regisztrálása … amíg az hiányzik, a null-őr miatt a mezők a
> mentett/alapértékkel jelennek meg, **csak írás nem történik**."

Vagyis a felhasználó átállította az e-mail beállításokat, a felület
elfogadta, és újranyitásra minden visszaállt.

## Miért teszt, és miért ilyen

A `typeof`-őr **elrejti** a hiányt: nincs hibaüzenet, nincs kivétel, nincs
piros teszt — csak egy funkció, ami nem működik. Ránézésre soha nem derül
ki. Az egyetlen dolog, ami megfogja, egy olyan állítás, ami a **két oldalt
összeveti**: mit hivatkozik a felület, és mit regisztrál az integrátor.

⚠️ A szándékos kivételeknek **indoklással** kell szerepelniük a listában —
a néma engedély pontosan az, ami ide nem kell (a #1003 baseline-jának
ugyanez a szabálya).
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app

#: Szándékos kivételek: hivatkozott, de (még) nem regisztrált vezérlők.
#: A kulcs a név, az érték az INDOKLÁS — indoklás nélküli tétel hiba.
KIVETELEK = {
    "batchEffectController": (
        "#1003 — a kötegelt effekt-visszavonás vezérlője MÉG NEM LÉTEZIK "
        "(nincs ilyen osztály a fában). A `Main.qml` hivatkozása őrzött, "
        "tehát a menüpont némán nem csinál semmit; a megvalósítás külön jegy."
    ),
}

#: A QML-ben deklarált nevek (property, id, függvény, jelzés) — ezek NEM
#: kontextus-property-k, hanem a fájl sajátjai.
_DEKLARACIO = re.compile(
    r"\bproperty\s+(?:\w+\s+)?([A-Za-z_]\w*)\b"
    r"|\bid\s*:\s*([A-Za-z_]\w*)"
    r"|\bfunction\s+([A-Za-z_]\w*)"
    r"|\bsignal\s+([A-Za-z_]\w*)"
)

#: `xyzController` szabad azonosítóként. A tagelérést (`valami.xyzController`)
#: és a property-értékadást (`xyzController: …`) kihagyjuk: azok a HÍVÓ
#: oldalán élő nevek, nem kontextus-property-k.
_HIVATKOZAS = re.compile(r"(?<![.\w])([a-z]\w*Controller)\b(?!\s*:)")


def _qml_gyoker() -> Path:
    return Path(picasapy.app.__file__).parent / "qml"


def _regisztralt_nevek() -> set[str]:
    forras = (Path(picasapy.app.__file__).parent / "application.py").read_text(
        encoding="utf-8"
    )
    return set(
        re.findall(r'setContextProperty\(\s*"([A-Za-z_]\w*)"', forras)
    )


def _hivatkozott_nevek() -> dict[str, list[str]]:
    talalatok: dict[str, list[str]] = {}
    for ut in sorted(_qml_gyoker().rglob("*.qml")):
        forras = ut.read_text(encoding="utf-8")
        helyi = {n for m in _DEKLARACIO.finditer(forras) for n in m.groups() if n}
        for szam, sor in enumerate(forras.splitlines(), start=1):
            csupasz = sor.lstrip()
            if csupasz.startswith(("//", "/*", "*")):
                continue
            for nev in _HIVATKOZAS.findall(sor):
                if nev in helyi:
                    continue
                talalatok.setdefault(nev, []).append(f"{ut.name}:{szam}")
    return talalatok


class TestAKetOldalOsszefer:
    def test_minden_hivatkozott_vezerlo_regisztralva_van(self):
        """⚠️ Ez a jegy: az e-mail beállításfül némán nem mentett."""
        regisztralt = _regisztralt_nevek()
        hianyzok = {
            nev: helyek
            for nev, helyek in _hivatkozott_nevek().items()
            if nev not in regisztralt and nev not in KIVETELEK
        }

        assert not hianyzok, (
            "a felület hivatkozik rájuk, az integrátor nem regisztrálja őket "
            "— a funkció NÉMÁN nem működik:\n"
            + "\n".join(f"  {n}: {h[:3]}" for n, h in sorted(hianyzok.items()))
        )

    def test_a_kivetelek_INDOKLASSAL_szerepelnek(self):
        """Néma engedély nincs: aki kivételt vesz fel, indokolja meg."""
        indoklas_nelkul = [
            nev for nev, indok in KIVETELEK.items() if len(indok.strip()) < 40
        ]

        assert not indoklas_nelkul

    def test_az_elavult_kivetel_is_HIBA(self):
        """Ha egy kivétel közben regisztrálva lett, a sorát törölni kell —
        különben a lista a múltat konzerválja (a #1003 baseline szabálya)."""
        regisztralt = _regisztralt_nevek()

        elavult = sorted(set(KIVETELEK) & regisztralt)

        assert not elavult, f"már regisztrálva, a kivétel törlendő: {elavult}"

    def test_a_kereso_talal_is_valamit(self):
        """Önteszt: ha a minta elromlik, a fenti állítások NÉMÁN zöldek
        lennének — pont az a hibaosztály, ami ellen ez a fájl készült."""
        hivatkozott = _hivatkozott_nevek()

        assert "editController" in hivatkozott
        assert len(hivatkozott) >= 8


class TestAKonkretVezerlok:
    """A jegyben megnevezett két vezérlő, külön kiemelve."""

    def test_az_emailController_regisztralva_van(self):
        assert "emailController" in _regisztralt_nevek()

    def test_a_webExportController_regisztralva_van(self):
        assert "webExportController" in _regisztralt_nevek()
