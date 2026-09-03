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


#: A `target:` KIFEJEZÉSÉBEN keresünk vezérlő-nevet, nem csak csupasz
#: azonosítót. #2132: a naiv `(\w+)` minta két élő írásmódot átengedett —
#: a `PhotoViewer` `typeof controller !== "undefined" ? controller : null`
#: alakját (az első szó `typeof`) és a `CollagePanel` `panel.controller`
#: alakját (az első szó `panel`). Egyik sem volt a listában, tehát az őr
#: hallgatott volna, amint azok a komponensek halasztottá válnak (#1612 c).
_SZO = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

#: Indokolt kivételek: halasztott komponens, amelyben a vezérlő-hallgató
#: MÉGIS maradhat. Csak akkor, ha a jelzés elvesztése bizonyíthatóan
#: ártalmatlan — az indok ide kerül, hogy a következő kör ne találgasson.
#:
#: A kulcs `(fájl, a target kifejezés eleje)`, hogy egy komponens másik,
#: NEM indokolt hallgatója továbbra is elbukjon.
INDOKOLT_HALLGATOK = {
    ("FolderManagerDialog.qml", "typeof controller"): (
        "#2132: a kezelő ELSŐ sora `if (!folderManagerWindow.visible) return` "
        "— a jelzés csak a NYITOTT mappakezelőnek szól. Fel nem épült "
        "párbeszéd sosem látható, tehát a kezelő akkor sem tenne semmit, ha "
        "létezne: nincs mit elveszíteni. (A másik hallgatója a "
        "`folderTreeController`-re megy, az nincs a figyelt vezérlők közt.)"
    ),
}


def _melyik_vezerlo(kifejezes: str) -> str | None:
    """A `target:` kifejezésében szereplő ELSŐ vezérlő-név, ha van.

    A vizsgálat szándékosan megengedő: bármilyen alakban szerepel a
    vezérlő (csupasz, minősített, feltételes), az kizáró ok — a lényeg,
    hogy a halasztott komponens a gazdára hallgat-e.
    """
    for szo in _SZO.findall(kifejezes):
        if szo in VEZERLOK:
            return szo
    return None


def _kivetel_kulcs(fajl: str, kifejezes: str) -> tuple[str, str]:
    """A kivétel-tábla kulcsa: a fájl és a `target` kifejezés ELSŐ KÉT szava.

    Azért nem a teljes kifejezés, hogy egy sortörés vagy egy szóköz
    átírása ne érvénytelenítse a felmentést — és azért nem csak a fájl,
    hogy ugyanabban a fájlban egy MÁSIK hallgató továbbra is elbukjon.
    """
    szavak = _SZO.findall(kifejezes)
    return (fajl, " ".join(szavak[:2]))


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
                r"Connections\s*\{\s*\n\s*target:\s*([^\n]+)", szoveg
            ):
                kifejezes = m.group(1).strip()
                vezerlo = _melyik_vezerlo(kifejezes)
                if vezerlo is None:
                    continue
                kulcs = _kivetel_kulcs(f"{nev}.qml", kifejezes)
                if kulcs in INDOKOLT_HALLGATOK:
                    continue
                talalt.append(f"{nev}.qml → target: {kifejezes}")

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


class TestAzOrFoga:
    """#2132: a mintának el kell kapnia MINDEN élő írásmódot.

    A korábbi minta csak a csupasz `target: controller` alakot ismerte. Két
    írásmód átment rajta, és mindkettő ÉL a projektben — az őr tehát
    hallgatott volna, amint azok a komponensek halasztottá válnak.
    """

    @pytest.mark.parametrize(
        "kifejezes",
        [
            "controller",
            "typeof controller !== \"undefined\" ? controller : null",
            "panel.controller",
            "appWindow.editController",
            "root.fileOpsController",
        ],
    )
    def test_minden_elo_irasmodot_felismer(self, kifejezes):
        assert _melyik_vezerlo(kifejezes) is not None, (
            f"az őr NEM ismeri fel ezt a vezérlő-hivatkozást: {kifejezes!r} — "
            "ilyen alakban némán átmenne egy halasztott komponensben"
        )

    @pytest.mark.parametrize(
        "kifejezes",
        [
            "folderTreeController",
            "editorPanel",
            "appWindow",
            "null",
            "parent",
        ],
    )
    def test_a_NEM_vezerlo_celt_bekeen_hagyja(self, kifejezes):
        """Ellenkező irányú őr: ha mindenre riasztana, használhatatlan volna
        — a kapu nem büntetheti a gondos munkát (#2077)."""
        assert _melyik_vezerlo(kifejezes) is None, (
            f"az őr tévesen vezérlőnek vette: {kifejezes!r}"
        )

    def test_a_kivetel_a_MASIK_hallgatot_nem_menti_fel(self):
        """A felmentés kulcsa a fájl ÉS a kifejezés — ugyanabban a fájlban egy
        másik hallgató továbbra is lelet."""
        mentett = _kivetel_kulcs(
            "FolderManagerDialog.qml", 'typeof controller !== "undefined" ? controller : null'
        )
        masik = _kivetel_kulcs("FolderManagerDialog.qml", "controller")
        assert mentett in INDOKOLT_HALLGATOK
        assert masik not in INDOKOLT_HALLGATOK


class TestAKivetelTablaNemAvulEl:
    """A tábla foga a MÁSIK irányban: ha egy felmentés tárgya eltűnt, a
    felmentés is tűnjön el — különben a lista csendben hízik, és a következő
    bővítés már nem tűnik fel (a #1719 azonos őrének mintája)."""

    def test_minden_felmentesnek_van_ELO_targya(self):
        elavult = []
        for (fajl, eleje), _indok in INDOKOLT_HALLGATOK.items():
            ut = _QML_DIR / "PicasaPy" / fajl
            if not ut.exists():
                elavult.append(f"{fajl}: a fájl sincs meg")
                continue
            szoveg = ut.read_text(encoding="utf-8")
            talalt = False
            for m in re.finditer(
                r"Connections\s*\{\s*\n\s*target:\s*([^\n]+)", szoveg
            ):
                if _kivetel_kulcs(fajl, m.group(1).strip()) == (fajl, eleje):
                    talalt = True
                    break
            if not talalt:
                elavult.append(f"{fajl} → {eleje}")
        assert elavult == [], (
            "ezeknek a felmentéseknek már nincs tárgya, törlendők: " f"{elavult}"
        )

    def test_minden_felmentesnek_van_ERDEMI_indoka(self):
        rovid = [
            k for k, indok in INDOKOLT_HALLGATOK.items() if len(indok.strip()) < 80
        ]
        assert rovid == [], (
            "ezeknek a felmentéseknek nincs érdemi indoka — egy felmentés, "
            f"amit nem indokoltak, csendben megszünteti az őrt: {rovid}"
        )
