"""A „Megtekintés a Google Earth programban…" útja VÉGIG: menüpont →
célmappa → vezérlő → LEMEZRE ÍRT KML → a társított program indítása (#1589).

## A lelet

A KML-előállítás kész volt (`export/earth.py:67`, `export/kml.py:157`), és
az `Exportálás Google Earth-fájlba` menüpont is élt — a **második**
menütétel viszont hiányzott. Az eredetiben `eMenuTools` névtérben KÉT
Google Earth-tétel van: az `ID_EXPORT_EARTH` **csak kiírja** a fájlt, az
`ID_VIEW_EARTH` kiírja **és megnyitja**.

## Miért ilyen ez a teszt

A vezérlő metódusait közvetlenül hívni itt semmit nem érne: a hibaosztály
pontosan az, hogy a kész motorhoz nem vezet felületi út (#1472/#1476).
Ezért a VALÓDI menütételt aktiválja, a VALÓDI célmappa-párbeszédet fogadja
el, és a végén a **lemezre írt** `doc.kml`-t méri.

## A külső program

A megnyitást a termék modulszintű `_open_url` fogantyúja végzi
(`export_controller.py`). A teszt EZT cseréli ki — a `QDesktopServices`
globális osztályát átírni tilos (#1375), és egy elszabadult teszt valódi
Google Earth-öt indítana a fejlesztő gépén.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path, PureWindowsPath

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl

import picasapy.app.export_controller as export_controller
import picasapy.app.formatting as formatting
from picasapy.export.earth import EarthExportReport

#: #1700: Windowson tiltott fájlnév-karakterek: `<>:"/\|?*`. Ez a fájl
#: LEMEZRE ír, ezért a `?` esetét ott ki kell hagyni — az URL-kerekítést
#: viszont lemez nélkül a `tests/app/test_windows_csapdak_1082.py` méri rá.
_WINDOWSON = sys.platform.startswith("win")


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kijelol(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _var(qt_app, feltetel, masodperc=20.0, uzenet="időtúllépés"):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert feltetel(), uzenet


def _menubol_nyit(window, qt_app, nev="menuToolsViewEarth"):
    """A VALÓDI menütétel aktiválása — előbb megkövetelve, hogy a
    felhasználó egyáltalán rá tudjon kattintani."""
    tetel = _elem(window, nev)
    assert tetel.property("enabled") is True, (
        f"a(z) {nev} menüpont le van tiltva — a felhasználó nem éri el"
    )
    assert not tetel.property("placeholder"), (
        f"a(z) {nev} menüpont helyfoglaló (#416), tehát halott"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "earthTargetDialog")


def _celmappat_valaszt(parbeszed, qt_app, mappa: Path):
    """A célmappa-párbeszéd elfogadása — a felhasználó „Kiválaszt" gombja."""
    mappa.mkdir(parents=True, exist_ok=True)
    parbeszed.setProperty("selectedFolder", QUrl.fromLocalFile(str(mappa)))
    QMetaObject.invokeMethod(
        parbeszed, "accepted", Qt.ConnectionType.DirectConnection
    )
    parbeszed.setProperty("visible", False)
    qt_app.processEvents()


@pytest.fixture
def megnyitasok(monkeypatch):
    """A társított program indításának fogantyúja — nem indul semmi.

    Az utat `Path`-ként jegyezzük fel, nem sztringként. A
    `QUrl.toLocalFile()` Windowson is PER-jeles alakot ad
    (`C:/Users/…/doc.kml`), a `str(Path(...))` viszont visszaperjelest —
    ugyanaz a fájl, kétféle írásmód (a #1082 2. csapdája). Sztringként
    összevetve a windows-láb elbukott (#1634, futás `33085887241`);
    `Path`-ot `Path`-tal mérve a mérce platformfüggetlen, és a fájl
    AZONOSSÁGÁRA kérdez, nem az írásmódjára."""
    hivasok: list[Path] = []

    def hamis_open_url(url):
        hivasok.append(Path(url.toLocalFile()))
        return True

    monkeypatch.setattr(export_controller, "_open_url", hamis_open_url)
    return hivasok


def _geocimkez(controller, qt_app, sorok, szelesseg=47.4979, hosszusag=19.0402):
    """A kijelölés geocímkézése a TERMÉK útján (`.picasa.ini` `geotag=`)."""
    controller.setGeotagRows(list(sorok), szelesseg, hosszusag)
    qt_app.processEvents()
    _var(
        qt_app,
        lambda: controller.photos.photos[sorok[0]].location is not None,
        uzenet="a geocímke nem került a képre",
    )


class TestBelepesiPont:
    def test_a_menupont_megnyitja_a_celmappa_valasztot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])

        parbeszed = _menubol_nyit(window, qt_app)

        assert parbeszed.property("visible") is True
        assert parbeszed.property("viewAfter") is True, (
            "a Megtekintés… ág az EXPORT útjára tévedt"
        )
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()

    def test_az_export_tetel_ugyanezt_a_valasztot_MEGNYITAS_NELKUL_nyitja(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])

        parbeszed = _menubol_nyit(window, qt_app, "menuToolsExportEarth")

        assert parbeszed.property("viewAfter") is False
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()


class TestKimenet:
    """A lánc utolsó szeme: a menüpont LEMEZRE ÍRT fájlt ad, és megnyitja."""

    def test_a_menupont_kiirja_a_doc_kml_t_es_MEGNYITJA(
        self, qml_app, qt_app, tmp_path, megnyitasok
    ):
        window, controller, _engine = qml_app
        _geocimkez(controller, qt_app, [0])
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "earth-megtekintes"

        _celmappat_valaszt(parbeszed, qt_app, cel)

        kml = cel / "doc.kml"
        _var(qt_app, kml.exists, uzenet="a menüpont NEM írt KML-t a lemezre")
        szoveg = kml.read_text(encoding="utf-8")
        # a kiírt KML valóban a geocímkézett képet hordozza
        assert "<Placemark" in szoveg
        assert "19.0402" in szoveg, szoveg[:400]

        _var(
            qt_app,
            lambda: bool(megnyitasok),
            uzenet="a KML elkészült, de a program NEM nyitotta meg",
        )
        assert megnyitasok == [kml]

    @pytest.mark.parametrize(
        "jel",
        [
            pytest.param("#", id="kettoskereszt"),
            pytest.param("%", id="szazalek"),
            # ⚠️ #1700: a `?` Windowson TILTOTT fájlnév-karakter — a mappa
            # létrehozása `WinError 123`-mal elhasal, mielőtt a mérés
            # egyáltalán elkezdődne. Ez a teszt LEMEZRE ír, ezért itt nem
            # szerepelhet. Az URL-kerekítést viszont rá is mérjük, csak
            # lemez nélkül: `tests/app/test_windows_csapdak_1082.py`.
            pytest.param(
                "?", id="kerdojel",
                marks=pytest.mark.skipif(
                    _WINDOWSON, reason="a `?` Windowson tiltott fájlnévben"
                ),
            ),
            pytest.param("+", id="plusz"),
            pytest.param(" ", id="szokoz"),
            pytest.param("é", id="ekezet"),
            pytest.param("[", id="szogletes"),
            pytest.param("&", id="es-jel"),
        ],
    )
    def test_a_kettoskeresztes_mappanev_is_celba_er(
        self, qml_app, qt_app, tmp_path, megnyitasok, jel
    ):
        """#1626 mellékfogása: URL-veszélyes karakterek a mappanévben.

        A célmappát URL-ként kapjuk. A régi kód a `file://` előtagot nyersen
        levágta, a MARADÉK viszont URL maradt — benne a `%23`-ra kódolt
        `#`-tel —, tehát a KML egy `nyár %231` nevű, ÚJ mappába került
        volna. Most a `QUrl.toLocalFile()` dekódol, ezért a fájl oda kerül,
        ahova a felhasználó mutatott. (Ez az ág Linuxon is hibás volt, csak
        nem mérte senki.)

        #1687: ez a teszt korábban a KML **elkészülte** után rögtön a
        `megnyitasok`-ot vizsgálta, anélkül hogy MEGVÁRTA volna, hogy a
        `earthViewReady` — egy háttérszálról érkező, ezért Qt-queued —
        jelzés ténylegesen célba érjen a főszálon. A fájlírás és a jelzés
        kiadása a worker-szálon szekvenciális, de a jelzés KÉZBESÍTÉSE a
        főszál eseményhurkán át külön lépés — a kml.exists() tehát MINDIG
        korábban vagy egyidejűleg válik igazzá, mint ahogy `megnyitasok`
        feltöltődik, sosem később. Mért rés (ezen a gépen, terhelés
        nélkül): 0,0003–1,8 ms — apró, de NEM nulla, tehát valódi
        verseny, amit egy lassabb/foglaltabb gép (pl. Windows-runner)
        kitágíthat. Mutáció: a hiányzó várakozást visszaállítva, 2
        könnyű CPU-terhelő szállal szimulálva a foglalt CI-gépet, 15
        futásból 9 elszállt (60%) — pontosan az #1687-ben látott
        `assert megnyitasok == []` mintával, hozzáadva a második
        `_var`-t 15/15 zöld lett. A `#` tehát NEM az útvonalkezelésben,
        hanem a teszt SORRENDJÉBEN okozta a hibát."""
        window, controller, _engine = qml_app
        _geocimkez(controller, qt_app, [0])
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / f"nyár {jel}1"

        _celmappat_valaszt(parbeszed, qt_app, cel)

        kml = cel / "doc.kml"
        _var(
            qt_app,
            kml.exists,
            uzenet=(
                f"a(z) {jel!r} karaktert tartalmazó nevű célmappába nem "
                "került KML — a százalékos kódolás feloldatlan maradt "
                "(#1626)"
            ),
        )
        _var(
            qt_app,
            lambda: bool(megnyitasok),
            uzenet=(
                "a KML elkészült, de a program NEM nyitotta meg — "
                f"a mappanévben lévő {jel!r} karakter miatt (#1687)"
            ),
        )
        assert megnyitasok == [kml]

    def test_az_EXPORT_tetel_ugyanazt_irja_ki_de_NEM_nyitja_meg(
        self, qml_app, qt_app, tmp_path, megnyitasok
    ):
        """A két tétel különbsége MÉRVE: ugyanaz a fájl, más folytatás."""
        window, controller, _engine = qml_app
        _geocimkez(controller, qt_app, [0])
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app, "menuToolsExportEarth")
        cel = tmp_path / "earth-export"

        _celmappat_valaszt(parbeszed, qt_app, cel)

        _var(
            qt_app,
            (cel / "doc.kml").exists,
            uzenet="az export menüpont NEM írt KML-t",
        )
        # …és az exportálás után SEMMIT nem indít el
        qt_app.processEvents()
        assert megnyitasok == [], "az Exportálás… megnyitotta a fájlt"


class TestNemaElutasitasNincs:
    """A projekt visszatérő hibaosztálya: a felület elfogadja a parancsot,
    aztán némán nem történik semmi."""

    def test_kijeloles_nelkul_a_menupont_MEGSZOLAL(self, qml_app, qt_app):
        """Az eredeti sem tilt, hanem beszél (`PublishToEarth::NoTagged`)."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])

        tetel = _elem(window, "menuToolsViewEarth")
        assert tetel.property("enabled") is True
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        szoveg = _elem(window, "earthResultText")
        assert "No geotagged images to export." in str(szoveg.property("text")), (
            "kijelölés nélkül a menüpont némán nem csinált semmit"
        )

    def test_geocimke_nelkuli_kijelolesnel_MEGSZOLAL(
        self, qml_app, qt_app, tmp_path, megnyitasok
    ):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "nincs-geo"

        _celmappat_valaszt(parbeszed, qt_app, cel)

        szoveg = _elem(window, "earthResultText")
        _var(
            qt_app,
            lambda: "No geotagged images to export."
            in str(szoveg.property("text")),
            uzenet="geocímke nélkül a menüpont némán nem csinált semmit",
        )
        assert not (cel / "doc.kml").exists()
        assert megnyitasok == []

    def test_ha_nincs_tarsitott_program_a_felulet_KIMONDJA(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        """A `QDesktopServices.openUrl` hamisat ad, ha nincs mivel megnyitni
        a fájlt. A felhasználónak ilyenkor is tudnia kell, hogy a fájl KÉSZ."""
        window, controller, _engine = qml_app
        monkeypatch.setattr(export_controller, "_open_url", lambda url: False)
        _geocimkez(controller, qt_app, [0])
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "nincs-program"

        _celmappat_valaszt(parbeszed, qt_app, cel)

        szoveg = _elem(window, "earthResultText")
        _var(
            qt_app,
            lambda: "no program associated" in str(szoveg.property("text")),
            uzenet=(
                "nem volt mivel megnyitni a KML-t, és a felület NEM szólt róla"
            ),
        )
        assert (cel / "doc.kml").exists(), "a fájlnak akkor is el kell készülnie"
        assert str(cel / "doc.kml") in str(szoveg.property("text")), (
            "az üzenet nem mondja meg, hova került a fájl"
        )


class TestAWindowsosCelmappaUt:
    """#1626: a célmappa-URL windowsos alakja — LINUXON mérve.

    ## A mért hiba

    A windows-CI-láb (futás `33079269994`, `windows-latest 1/4`) nem
    „lassú"-t jelzett, hanem KIVÉTELT a háttérszálon::

        OSError: [WinError 123] The filename, directory name, or volume
        label syntax is incorrect:
        '\\C:\\Users\\runneradmin\\…\\earth-megtekintes'

    A vezető backslash a `\\C:` előtt a lelet. A `FolderDialog`
    `file:///C:/Users/…` alakú URL-t ad; az `ExportDialogs.qml` ebből a
    `file://`-t NYERSEN levágta, így `/C:/Users/…` maradt, amiből a
    `Path` `\\C:\\Users\\…`-t csinál. A `mkdir` ezen elhasal, tehát a
    `doc.kml` SOHA nem készült el — nem teszthiba volt, hanem termékhiba.

    ## Miért mérhető ez Linuxon

    A `QUrl.toLocalFile()` a meghajtóbetű elé tett perjelet csak Windowson
    szedi le (`#ifdef Q_OS_WIN`), ezért a `to_local_path` ezt a lépést a
    `_platform()` fogantyún át MAGA is elvégzi (#1217 mintája). A fogantyú
    átállításával itt, Linuxon fut a windowsos ág — a #1560 hibáját
    (windowsos ág, ami a windows-lábon üresen zöld) elkerülve.

    Mutációval mérve: a QML-beli `file://`-levágó `replace(…)` visszatétele
    ezt az állítást megbuktatja (`/C:/Temp/pp-1626`), és ugyanígy a
    `formatting.to_local_path` meghajtóbetű-levágásának törlése is — az őr
    tehát valóban ezt az ágat fogja.

    ## #1634 — a várt értéket ELŐÁLLÍTJUK

    Az állítás eredetileg a per-jeles `"C:/Temp/pp-1626"` sztringet égette
    be, és a windows-lábon elbukott: a `to_local_path` `str(Path(...))`-ot
    ad, ott tehát `C:\\Temp\\pp-1626`-ot. A mérce most ugyanazon a
    normalizáláson megy át, mint a termék kimenete, a lényeget pedig egy
    szeparátor-független `PureWindowsPath`-állítás mondja ki.
    """

    def test_a_meghajtobetus_URL_bol_meghajtobetus_ut_lesz(
        self, qml_app, qt_app, monkeypatch, megnyitasok
    ):
        window, controller, _engine = qml_app
        monkeypatch.setattr(formatting, "_platform", lambda: "win32")
        rogzitett: list[str] = []

        def hamis_export(records, cel, folder_name=""):
            """A motor NEM ír lemezre — csak az utat rögzítjük.

            Windowson a valódi `mkdir` itt hasalt el; Linuxon egy
            `C:/…` út a munkakönyvtárba írna szemetet."""
            rogzitett.append(str(cel))
            return EarthExportReport(
                kml_path=None, placemarks=0, skipped_without_location=0
            )

        monkeypatch.setattr(
            export_controller, "export_google_earth", hamis_export
        )
        _geocimkez(controller, qt_app, [0])
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)

        # a windowsos FolderDialog PONT ezt az alakot adja vissza
        parbeszed.setProperty(
            "selectedFolder", QUrl("file:///C:/Temp/pp-1626")
        )
        QMetaObject.invokeMethod(
            parbeszed, "accepted", Qt.ConnectionType.DirectConnection
        )
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()

        _var(
            qt_app,
            lambda: bool(rogzitett),
            uzenet="a vezérlő el sem jutott a motorig",
        )
        # a várt értéket ELŐÁLLÍTJUK, nem beégetjük: a `to_local_path`
        # `str(Path(...))`-ot ad, ami Windowson visszaperjeles (#1634)
        assert rogzitett == [str(Path("C:/Temp/pp-1626"))], (
            "a windowsos célmappa-URL-ből hibás út lett — a vezető perjel "
            "miatt Windowson `\\C:\\Temp\\…` keletkezik, amin a `mkdir` "
            "`WinError 123`-mal elhasal, és a KML nem készül el (#1626)"
        )
        # …és a szeparátortól függetlenül: a meghajtóbetű az út ELEJÉN áll
        assert PureWindowsPath(rogzitett[0]).drive == "C:"
        assert megnyitasok == [], (
            "a KML el sem készült, mégis megnyitást kísérelt a program"
        )

