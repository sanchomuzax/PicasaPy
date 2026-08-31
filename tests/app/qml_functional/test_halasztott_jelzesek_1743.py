"""#1743 — a halasztott párbeszédek nem nyelhetik el a vezérlő jelzését.

**A kockázat.** A #1720 óta tizenhárom párbeszéd HALASZTOTT: csak az első
megnyitáskor épül fel. Kettőben azonban `Connections` ült a vezérlő
jelzéseire (`SaveDialogs`, `ExportDialogs`) — amíg a párbeszéd nem állt, a
kezelő NEM LÉTEZETT, tehát a jelzés senkihez nem ért el.

A felületen ez ma nem fordult elő, mert minden belépő az `ensure()`-ön át
ment. De egy ÚJ belépő (gyorsbillentyű, tálcagomb, kötegelt művelet) némán
elnyelte volna a hibaüzenetet — és **semmilyen teszt nem bukott volna el rá**.

**A javítás.** A hallgató a mindig felépülő `Main.qml`-be került, és az
`ensure()` a jelzés pillanatában építi fel a párbeszédet.

Ez a fájl két oldalról fog:

1. `TestJelzesMegnyitasNelkul` — a MŰKÖDÉS: a vezérlő jelzése megnyitja a
   párbeszédet AKKOR IS, ha azt előtte soha senki nem nyitotta meg.
2. `TestNincsVezerloreKotottConnections` — a SZERKEZET: halasztott
   párbeszédben nem LEHET vezérlőre kötött `Connections`, különben a
   kockázat némán visszatér.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject

import picasapy.app

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"

#: A vezérlő-szerű context property-k: ezekre kötött `Connections` az, ami
#: elveszhet, ha a befoglaló párbeszéd még nem épült fel.
VEZERLOK = ("controller", "editController", "fileOpsController")


def _halasztott_komponensek() -> list[str]:
    """A `Main.qml`-ből olvassuk ki, mi van `DeferredDialog`-ba csomagolva —
    így az őr akkor is igaz marad, ha a halasztottak köre változik."""
    main = (_QML_DIR / "Main.qml").read_text(encoding="utf-8")
    return sorted(
        set(re.findall(r"sourceComponent:\s*Component\s*\{\s*(\w+)", main))
    )


class TestJelzesMegnyitasNelkul:
    """A vezérlő jelzése megnyitja a párbeszédet előzetes megnyitás NÉLKÜL."""

    def test_a_mentesi_hiba_akkor_is_megjelenik_ha_a_parbeszed_meg_nem_allt(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app

        # a kiindulás: a párbeszéd tényleg NEM létezik (ez a #1720 nyeresége)
        assert window.findChild(QObject, "saveErrorDialog") is None, (
            "a SaveDialogs már a jelzés előtt felépült — a próba így nem "
            "bizonyítana semmit"
        )

        controller.saveErrorOccurred.emit("nevutkozes", "kep.jpg", 0)
        qt_app.processEvents()

        parbeszed = window.findChild(QObject, "saveErrorDialog")
        assert parbeszed is not None, (
            "a mentési hiba jelzésére NEM épült fel a párbeszéd — a #1720 "
            "halasztása elnyelte a jelzést (#1743)"
        )
        assert parbeszed.property("visible") is True, (
            "a párbeszéd felépült, de nem nyílt meg — a felhasználó néma "
            "hibát kapna"
        )
        assert parbeszed.property("fileName") == "kep.jpg", (
            "a jelzés adatai nem jutottak el a párbeszédig"
        )


class TestNincsVezerloreKotottConnections:
    """Szerkezeti őr: a kockázat forrása ne kerülhessen vissza."""

    def test_halasztott_parbeszedben_nincs_vezerlore_kotott_connections(self):
        halasztott = _halasztott_komponensek()
        assert len(halasztott) >= 10, (
            f"csak {len(halasztott)} halasztott komponenst találtunk — a "
            "mérés romlott el, nem a halasztás szűnt meg"
        )

        talalt: list[str] = []
        for nev in halasztott:
            fajl = _QML_DIR / "PicasaPy" / f"{nev}.qml"
            if not fajl.exists():
                continue
            szoveg = fajl.read_text(encoding="utf-8")
            for m in re.finditer(
                r"Connections\s*\{\s*\n\s*target:\s*(\w+)", szoveg
            ):
                if m.group(1) in VEZERLOK:
                    talalt.append(f"{nev}.qml → target: {m.group(1)}")

        assert talalt == [], (
            "halasztott párbeszédben vezérlőre kötött `Connections` van "
            f"(#1743): {talalt}\n"
            "Amíg a párbeszéd nem áll, ez a kezelő nem létezik — a jelzés "
            "némán elvész. A hallgató a `Main.qml`-be való, és onnan "
            "`ensure()`-rel hívja a párbeszéd függvényét."
        )

    @pytest.mark.parametrize(
        "fajl, fuggveny",
        [
            ("SaveDialogs.qml", "jelezdAmentesiHibat"),
            ("SaveDialogs.qml", "jelezdAbukottMentest"),
            ("ExportDialogs.qml", "jelezdAzExportVeget"),
            ("ExportDialogs.qml", "nyisdMegAzEarthFajlt"),
        ],
    )
    def test_a_main_az_ensure_utan_hivja_a_fuggvenyt(self, fajl, fuggveny):
        """A `Main.qml` hallgatója NEM nyúlhat a `Loader.item`-hez közvetlenül:
        az `ensure()` nélkül a párbeszéd nem épülne fel, és a hívás némán
        `undefined`-en történne."""
        assert f"function {fuggveny}(" in (
            _QML_DIR / "PicasaPy" / fajl
        ).read_text(encoding="utf-8"), f"{fuggveny} nincs a {fajl}-ban"

        main = (_QML_DIR / "Main.qml").read_text(encoding="utf-8")
        assert f"ensure().{fuggveny}(" in main, (
            f"a Main.qml nem az `ensure()`-ön át hívja a(z) {fuggveny}-t"
        )
