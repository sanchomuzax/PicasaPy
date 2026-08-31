"""#1566: a „Mentés másként…" és a „Másolat mentése" VISSZAJELZÉST ad.

## Mit mér ez a fájl, és mit NEM

A #1527 tesztje azt méri, hogy a két menüpont **elvégzi** a munkát (a
másolat a lemezen van, a forrás sértetlen). Ez a fájl a másik felét méri:
a művelet végén a **felhasználó lát-e bármit**. A kettő független — a
#1566 kiinduló állapotában a lemezre írás hibátlan volt, a felület mégis
néma maradt, és a `saveCopyFinished` jelzésnek csak GÉPI fogyasztója volt
(a #1539 újraolvasás-kötése), ami a nyilvántartást frissíti, nem a
felhasználót tájékoztatja.

Ezért az állítások SEHOL nem a jelzés kibocsátására szólnak: a jelzést
kiváltó menüpontot sütjük el, és utána a **lebegő értesítősáv** (#1129)
állapotát olvassuk — azt, ami a képernyőn megjelenik.

## Miért a sáv olvasóin át kérdezünk

A sáv celláit egy `Repeater` állítja elő, azokat a `findChild` NEM találja
meg (a #1168 tesztje ugyanezt írja le). A sáv ezért saját olvasókat ad
(`cellCount`, `lastTitle`, `lastHint`, `lastPayload`) — az állításaink
azokra szólnak.

## Miért ANGOL szövegeket állít

A fixture nem telepít `QTranslator`-t, tehát a `qsTr()` a FORRÁSSZTRINGET
adja vissza (ugyanaz a helyzet, mint a #1527-nél). A magyar feliratot
ezért az utolsó osztály közvetlenül a `picasapy_hu.ts`-ből méri.

## A várt szöveg KIÍRT literál

A #1576 első köre azért nyelte el a hibát, mert a várt szöveget a termék
saját konstansából olvasta — így az elrontott felirat mellett is zöld
maradt. Itt minden várt szöveg betű szerint ki van írva.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from support.halasztott_parbeszed import epitsd_fel
from support.qt_wait import wait_for_signal


def _elem(root, nev: str) -> QObject:
    # #1720: az itt keresett elemek a HALASZTOTT párbeszéd
    # belsejében ülnek — előbb fel kell épülnie, a valódi
    # menüponton át (ld. support/halasztott_parbeszed.py).
    epitsd_fel(root, "saveDialogs")
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _sav(window) -> QObject:
    """A lebegő értesítősáv — enélkül az egész jegynek nincs értelme."""
    sav = window.findChild(QObject, "picasaNotifier")
    assert sav is not None, (
        "a lebegő értesítősáv nincs a fában — a mentés visszajelzésének "
        "nincs hova megjelennie"
    )
    return sav


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _elsut(window, qt_app, nev: str) -> None:
    """A VALÓDI menütétel aktiválása (MEMORY: „a vezérlőre KATTINTS")."""
    tetel = _elem(window, nev)
    assert tetel.property("enabled") is True, (
        f"a(z) {nev} menüpont le van tiltva — a felhasználó nem éri el"
    )
    assert not tetel.property("placeholder"), (
        f"a(z) {nev} menüpont helyfoglaló (#416), tehát halott"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _mappa(controller, sor: int = 0) -> Path:
    return Path(str(controller.photos.filePathAt(sor))).parent


def _masolat_mentese(window, controller, qt_app) -> None:
    wait_for_signal(
        controller.saveCopyFinished,
        lambda: _elsut(window, qt_app, "menuFileSaveCopy"),
        description="a Másolat mentése",
        process_events_with=qt_app,
    )
    qt_app.processEvents()


def _mentes_maskent(controller, qt_app, cel: Path) -> None:
    wait_for_signal(
        controller.saveCopyFinished,
        lambda: controller.saveRowAs(0, cel.as_uri()),
        description="a Mentés másként",
        process_events_with=qt_app,
    )
    qt_app.processEvents()


class TestMasolatMenteseErtesit:
    """1. „Kész, ha": a menüpontról indított másolat-mentés végén a
    felhasználó LÁT valamit."""

    def test_a_menupontrol_megjelenik_egy_ertesites(self, qml_app, qt_app):
        """Ez a jegy magja: a #1566 előtt itt 0 cella volt."""
        window, controller, _engine = qml_app
        sav = _sav(window)
        assert sav.property("cellCount") == 0, "a sáv nem üresen indult"
        _kijelol(window, qt_app, [0])

        _masolat_mentese(window, controller, qt_app)

        assert sav.property("cellCount") == 1, (
            "a Másolat mentése után a felhasználó SEMMIT nem lát: "
            f"{sav.property('cellCount')} értesítés a sávban"
        )

    def test_az_ertesites_felirata_a_MENTETT_MASOLATROL_szol(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        sav = _sav(window)
        _kijelol(window, qt_app, [0])

        _masolat_mentese(window, controller, qt_app)

        assert sav.property("lastTitle") == "Copy saved", (
            sav.property("lastTitle")
        )

    def test_az_ertesites_a_KATTINTASI_tippet_is_mutatja(self, qml_app, qt_app):
        """`CThumbUI::clickview` — hivatalos felirat, ugyanaz, amit az
        importálás kész-értesítése is használ."""
        window, controller, _engine = qml_app
        sav = _sav(window)
        _kijelol(window, qt_app, [0])

        _masolat_mentese(window, controller, qt_app)

        assert sav.property("lastHint") == "click to view", (
            sav.property("lastHint")
        )

    def test_az_ertesites_a_MASOLAT_utjara_mutat(self, qml_app, qt_app):
        """A cellára kattintva a sáv a hasznos adat MAPPÁJÁRA navigál —
        ha az üres, a kattintás néma no-op, tehát a tipp hazudik."""
        window, controller, _engine = qml_app
        sav = _sav(window)
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))

        _masolat_mentese(window, controller, qt_app)

        vart = forras.parent / f"{forras.stem}-001{forras.suffix}"
        assert vart.exists(), "a másolat nem jött létre — az alap hiányzik"
        assert sav.property("lastPayload") == str(vart), (
            sav.property("lastPayload")
        )

    def test_KET_kepnel_a_TOBBES_szamu_felirat(self, qml_app, qt_app):
        """Az eredeti mentés-családja végig két külön alakot tart
        (`progfile`/`progfiles`, `messagetag1`/`messagetagX`) — a
        visszajelzés sem mondhat „1 másolat”-ot kettőre."""
        window, controller, _engine = qml_app
        sav = _sav(window)
        _kijelol(window, qt_app, [0, 1])

        _masolat_mentese(window, controller, qt_app)

        assert sav.property("cellCount") == 1, "kép-darabonként külön értesítés"
        assert sav.property("lastTitle") == "2 copies saved", (
            sav.property("lastTitle")
        )


class TestMentesMaskentErtesit:
    """2. A „Mentés másként…" — ITT a legnagyobb a tét: a cél MÁS mappa is
    lehet, ahol a felhasználó a fájlt a rácsban sem látja meg."""

    def test_MAS_mappaba_mentve_is_van_ertesites(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        sav = _sav(window)
        _kijelol(window, qt_app, [0])
        maskeppen = tmp_path / "mashova"
        maskeppen.mkdir()
        cel = maskeppen / "sajat-nevem.jpg"

        _mentes_maskent(controller, qt_app, cel)

        assert cel.exists(), "a választott célra nem íródott fájl"
        assert sav.property("cellCount") == 1, (
            "a más mappába mentett kép se a rácsban, se a sávban nem "
            "jelenik meg — a felhasználónak semmi nyoma nincs"
        )
        assert sav.property("lastTitle") == "Copy saved"
        assert sav.property("lastPayload") == str(cel), (
            sav.property("lastPayload")
        )

    def test_a_MEGSZAKITOTT_fajlvalaszto_NEM_ertesit(self, qml_app, qt_app):
        """Üres célút = a felhasználó elvetette a párbeszédet. A „kész"
        értesítés ilyenkor hazugság volna."""
        window, controller, _engine = qml_app
        sav = _sav(window)
        _kijelol(window, qt_app, [0])

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: controller.saveRowAs(0, ""),
            description="a megszakított Mentés másként",
            process_events_with=qt_app,
        )
        qt_app.processEvents()

        assert sav.property("cellCount") == 0, (
            "a megszakított mentésre is „kész” értesítés jött"
        )


class TestBukottMentesNemJelentKeszet:
    """3. A hibaágnak MÁR VAN felülete (#1527 `saveErrorDialog`) — a
    kész-értesítés nem szólalhat meg mellé."""

    def test_nevutkozesnel_hibaparbeszed_van_kesz_ertesites_NINCS(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        # #1720: a SaveDialogs HALASZTOTT, és a hibaüzenetet egy
        # `Connections` kapja el a vezérlő jelzéséből. Ez a teszt a
        # vezérlőt KÖZVETLENÜL hívja (a felületet megkerülve), ezért a
        # párbeszédnek a művelet ELŐTT állnia kell — különben a jelzés
        # senkihez nem ér el. A felületen ez nem fordul elő: minden
        # mentés-belépő az `ensure()`-ön át megy.
        epitsd_fel(window, "saveDialogs")
        sav = _sav(window)
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))
        cel = forras.parent / f"{forras.stem}-001{forras.suffix}"
        cel.write_bytes(b"foglalt")

        _mentes_maskent(controller, qt_app, cel)

        assert _elem(window, "saveErrorDialog").property("visible") is True, (
            "a névütközés hibaága néma maradt"
        )
        assert sav.property("cellCount") == 0, (
            "a bukott mentésre „kész” értesítés jött"
        )
        _elem(window, "saveErrorDialog").setProperty("visible", False)
        qt_app.processEvents()


class TestMagyarFelirat:
    """4. A magyar szöveg — a fixture fordítás nélkül fut, ezért a
    `picasapy_hu.ts`-ből mérve.

    ⚠️ A két cím a MI DÖNTÉSÜNK, nem hivatalos Picasa-erőforrás: a
    `stringres` mentés-családjában (25 bejegyzés) folyamatjelzés,
    megerősítés, formátumváltás és hibaágak vannak, **befejezés-üzenet
    nincs**. A tipp (`click to view`) viszont hivatalos
    (`CThumbUI::clickview`), és a fenti mondatok az eredeti alakját
    követik (külön egyes és többes szám).
    """

    #: (kontextus, forrássztring) -> a várt magyar felirat, KIÍRVA.
    VART = {
        ("PicasaNotifier", "Copy saved"): "A másolat mentve",
        ("PicasaNotifier", "%1 copies saved"): "%1 másolat mentve",
        # CThumbUI::clickview — HIVATALOS, a #1129 óta megvan
        (
            "PicasaNotifier",
            "click to view",
        ): "a megtekintéshez kattintson ide",
    }

    def test_a_ket_uj_felirat_magyarul_is_megvan(self):
        ts = (
            Path(__file__).resolve().parents[3]
            / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.ts"
        )
        gyoker = ET.parse(ts).getroot()
        forditasok: dict[tuple[str, str], str] = {}
        for context in gyoker.findall("context"):
            nev = (context.findtext("name") or "").strip()
            for message in context.findall("message"):
                forras = (message.findtext("source") or "").strip()
                forditas = message.find("translation")
                szoveg = (forditas.text or "").strip() if forditas is not None else ""
                forditasok[(nev, forras)] = szoveg

        for kulcs, vart in self.VART.items():
            assert kulcs in forditasok, f"{kulcs} nincs a picasapy_hu.ts-ben"
            assert forditasok[kulcs] == vart, (
                f"{kulcs}: {forditasok[kulcs]!r} != {vart!r}"
            )
