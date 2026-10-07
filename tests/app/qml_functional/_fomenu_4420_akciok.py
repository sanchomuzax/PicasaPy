"""A főmenü-bejárás párbeszéd- és parancsműveletei."""

from __future__ import annotations

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QMetaObject,
    QObject,
    QSettings,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtQuick import QQuickItem

from picasapy.app import collage_output, movie_output
from picasapy.app.worker_thread import wait_for_all_background_workers
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._fomenu_4420_menu import (
    _ABLAK_ALAPMAGASSAG,
    _DIALOG_ELEMEK,
    _LETILTOTT_A_TISZTA_MINTABAN,
    _LOADER_ELEMEK,
    _MENU_ELEMEK,
    _MENU_FEJLECEK,
    _MENU_UTVONAL_DARAB,
    _NINCS_LATHATO_HATAS,
    _NINCS_LATHATO_HATAS_UTVONAL,
    _NYELV_ALMENU_MIN_MAGASSAG,
    _QML_ELEMEK,
    _UI_ELEMEK,
    _UTAK,
    _allapot,
    _elero_menu,
    _feluleti_allapot,
    _frissitsd_a_halasztott_objektumokat,
    _kattints,
    _kattints_qobject,
    _kepernyokep,
    _kepernyout,
    _kulonbsegek,
    _megnyit,
    _menuk,
    _normalizal,
    _parancsok,
    _rendszergyoker_hianyzik,
    _szoveg,
    _varj,
    _zarj_menuket,
)


def _lathato_dialogusok(ablak):
    # A DeferredDialog a QML Loader `item` tulajdonságába teszi a párbeszédet;
    # az új fa nem feltétlenül lesz QObject-gyereke a főablaknak.
    ablak_azon = id(ablak)
    if ablak_azon not in _UI_ELEMEK:
        _feluleti_allapot(ablak)
    else:
        _frissitsd_a_halasztott_objektumokat(ablak)
    elemek = _DIALOG_ELEMEK.get(ablak_azon, ())
    talalatok = []
    latott = set()
    for elem in elemek:
        try:
            if not shiboken6.isValid(elem):
                continue
            azon = shiboken6.getCppPointer(elem)[0]
            osztaly = elem.metaObject().className()
            nev = elem.objectName()
        except RuntimeError:
            continue
        if azon in latott or "Menu" in osztaly:
            continue
        latott.add(azon)
        tipus = (nev + osztaly).casefold()
        if "dialog" not in tipus or any(
            resz in tipus
            for resz in ("loader", "buttonbox", "deferreddialog", "dialogs")
        ):
            continue
        if elem.property("opened") is True or elem.property("visible") is True:
            talalatok.append(elem)
    return talalatok


def _parbeszed_gombok(dialogus):
    """A párbeszéd gombjait a QObject- és QML-vizuális fából is összegyűjti."""
    objektumok = []
    latott = set()

    def hozzaad(elem):
        # #4503: a `footer`/`contentItem` tulajdonság a CI-n néha QMetaObject-et
        # ad vissza — csak valódi QObject lehet gomb.
        if not isinstance(elem, QObject):
            return
        try:
            if not shiboken6.isValid(elem):
                return
            azon = shiboken6.getCppPointer(elem)[0]
        except (RuntimeError, TypeError):
            return
        if azon not in latott:
            latott.add(azon)
            objektumok.append(elem)

    try:
        for elem in dialogus.findChildren(QObject):
            hozzaad(elem)
    except (AttributeError, RuntimeError):
        pass

    gyokerek = [dialogus]
    for nev in ("footer", "contentItem"):
        try:
            elem = dialogus.property(nev)
        except (AttributeError, RuntimeError):
            elem = None
        if elem is not None:
            gyokerek.append(elem)

    varakozo = list(gyokerek)
    while varakozo:
        elem = varakozo.pop()
        hozzaad(elem)
        try:
            if isinstance(elem, QQuickItem):
                varakozo.extend(elem.childItems())
        except (AttributeError, RuntimeError):
            continue

    eredmeny = []
    for elem in objektumok:
        try:
            if (
                "Button" in elem.metaObject().className()
                and bool(elem.property("visible"))
                and bool(elem.property("enabled"))
            ):
                eredmeny.append(elem)
        except RuntimeError:
            continue
    return eredmeny


def _zarj_parbeszedeket(ablak, qt_app, naplo: list[str]) -> None:
    for _ in range(4):
        dialogusok = _lathato_dialogusok(ablak)
        if not dialogusok:
            return
        kezelt_nevek = set()
        for dialogus in dialogusok:
            if not shiboken6.isValid(dialogus):
                continue
            nev = dialogus.objectName() or dialogus.metaObject().className()
            if nev in kezelt_nevek:
                continue
            kezelt_nevek.add(nev)
            keres_fut = dialogus.property("scanning") is True
            gombok = []
            for elem in _parbeszed_gombok(dialogus):
                gombnev = elem.objectName().casefold()
                felirat = _normalizal(_szoveg(elem, "text"))
                dedup_ablak = "dedup" in nev.casefold()
                if any(szo in gombnev for szo in ("cancel", "megse")) or (
                    felirat in {"cancel", "mégse"}
                ):
                    rang = 1 if dedup_ablak else 0
                    gombok.append((rang, elem))
                elif "close" in gombnev or felirat == "close":
                    rang = 0 if dedup_ablak else 1
                    gombok.append((rang, elem))
            if gombok:
                gombok.sort(key=lambda adat: adat[0])
                gomb = gombok[0][1]
                gombnev = gomb.objectName().casefold()
                if isinstance(gomb, QQuickItem):
                    _QML_ELEMEK.append(gomb)
                    _kattints(qt_app, gomb)
                else:
                    _kattints_qobject(qt_app, gomb)
                if keres_fut and "close" not in gombnev:
                    naplo.append(f"{nev}: Cancel gombbal a keresés megszakítva")
                    _varj(
                        qt_app,
                        lambda dialogus=dialogus: dialogus.property("scanning")
                        is False,
                        3.0,
                    )
                elif keres_fut:
                    naplo.append(
                        f"{nev}: Close gombbal bezárva; a keresés megszakítása is elindult"
                    )
                else:
                    naplo.append(f"{nev}: Mégse/Close gombbal bezárva")
                continue

            # A natív Qt Quick FolderDialogban nincs QML Mégse-gomb, a close()
            # viszont a visszautasító útvonalon zárja be.
            if QMetaObject.invokeMethod(
                dialogus, "close", Qt.ConnectionType.DirectConnection
            ):
                qt_app.processEvents()
                naplo.append(f"{nev}: close() útvonalon, Mégse-ként bezárva")
                continue

            celablak = next(
                (
                    masik
                    for masik in QGuiApplication.allWindows()
                    if masik.objectName() == nev
                    and masik.property("visible") is True
                ),
                None,
            )
            if celablak is None:
                masodlagos_ablakok = [
                    masik
                    for masik in QGuiApplication.allWindows()
                    if masik is not ablak and masik.property("visible") is True
                ]
                celablakok = masodlagos_ablakok or [ablak]
            else:
                celablakok = [celablak]
            for celablak in celablakok:
                QTest.keyClick(celablak, Qt.Key.Key_Escape)
            qt_app.processEvents()
            naplo.append(f"{nev}: Escape billentyűvel, Mégse útvonalon bezárva")
        if not _varj(qt_app, lambda: not _lathato_dialogusok(ablak), 3.0):
            naplo.append("Mégse útvonal után is nyitva maradt párbeszédablak")


def _zarj_nezot_es_fiokot(ablak, qt_app) -> None:
    if ablak.property("viewerOpen") is True:
        vissza = ablak.findChild(QObject, "viewerBackButton")
        if (
            vissza is not None
            and vissza.property("visible") is True
            and vissza.property("enabled") is True
        ):
            _kattints(qt_app, vissza)
        else:
            ablak.setProperty("viewerOpen", False)
            qt_app.processEvents()
    if ablak.property("slideshowRunning") is True:
        QTest.keyClick(ablak, Qt.Key.Key_Escape)
        _varj(qt_app, lambda: ablak.property("slideshowRunning") is False)
    ablak.setProperty("activeDrawerTab", "")
    qt_app.processEvents()
    tabsor = ablak.findChild(QObject, "documentTabStrip")
    konyvtar_ful = ablak.findChild(QObject, "documentTabLibrary")
    if (
        tabsor is not None
        and tabsor.property("libraryActive") is False
        and konyvtar_ful is not None
        and konyvtar_ful.property("visible") is True
        and konyvtar_ful.property("enabled") is True
    ):
        _kattints_qobject(qt_app, konyvtar_ful)


def _zarj_ertesitosavot(ablak, vezerlo, qt_app) -> None:
    """A keresési művelet után zárja le a maradó jelzést és munkát.

    A színkeresés a fotók gyorsítótárát háttérben tölti fel. A menühatás
    képernyőképe már elkészült, ezért a tiszta következő parancs érdekében a
    valódi Leállítás/Bezárás vezérlővel zárjuk le a sávot.
    """
    szoveg = ablak.findChild(QObject, "errorBannerText")
    if szoveg is None or not _szoveg(szoveg, "text"):
        return

    leallitas = ablak.findChild(QObject, "errorBannerStopButton")
    if leallitas is not None and leallitas.property("visible") is True:
        _kattints_qobject(qt_app, leallitas)
        assert vezerlo.waitForBackgroundWorkers(3.0), (
            "a színkeresés háttérmunkája nem állt le a tiszta visszaállításra"
        )
    else:
        bezaras = ablak.findChild(QObject, "errorBannerCloseButton")
        assert bezaras is not None and bezaras.property("visible") is True, (
            "a látható tájékoztató sávnak nincs bezáró vezérlője"
        )
        _kattints_qobject(qt_app, bezaras)

    assert _varj(qt_app, lambda: _szoveg(szoveg, "text") == ""), (
        "a tájékoztató sáv nem záródott be"
    )
    assert vezerlo.color_index_fut() is False, (
        "a színkeresés háttérmunkája a sáv bezárása után is fut"
    )


def _allitsd_vissza_a_mintamappat(
    ablak, vezerlo, minta: Path, menu_bar, qt_app, *, parancs_nev: str = ""
) -> None:
    """Zárja a felületi rétegeket, ürítse a keresőt, majd álljon a mintamappára."""
    _zarj_menuket(menu_bar, qt_app)
    _zarj_parbeszedeket(ablak, qt_app, [])
    _zarj_nezot_es_fiokot(ablak, qt_app)
    ablak.setProperty("unnamedFacesOpen", False)
    for nev in ("giftCdHost", "backupHost"):
        host = ablak.findChild(QObject, nev)
        if host is not None and host.property("nyitva") is True:
            host.setProperty("nyitva", False)

    if vezerlo.property("tesztuzemEnabled") is True:
        vezerlo.setTesztuzemEnabled(False)

    # A Hide/Unhide és a korábbi parancsok rejtett fotó-állapotát a következő
    # megfigyelés előtt visszaállítjuk. Az Unhide saját előfeltételét az
    # _akcio készíti elő külön, így maga a kattintás is mérhető.
    rejtett_sorok = [
        index
        for index, photo in enumerate(vezerlo.photos.photos)
        if photo.hidden
    ]
    if rejtett_sorok:
        vezerlo.toggleHiddenRows(rejtett_sorok)
    if vezerlo.showHidden:
        vezerlo.setShowHidden(False)

    toolbar = ablak.findChild(QObject, "mainToolbar")
    assert toolbar is not None, "a keresősáv hiányzik"
    assert QMetaObject.invokeMethod(
        toolbar, "clearSearch", Qt.ConnectionType.DirectConnection
    ), "a próba nem tudta kiüríteni a keresőmezőt"
    vezerlo.search("")
    _zarj_ertesitosavot(ablak, vezerlo, qt_app)

    minta_ut = str(minta)
    if vezerlo.isFolderHidden(minta_ut):
        vezerlo.toggleFolderHidden(minta_ut)
    if vezerlo.property("showHidden") is True:
        vezerlo.setShowHidden(False)
    vezerlo.selectFolder(minta_ut)

    # A „Show” parancs csak rejtett mappán tesztelhető. A rejtett mappák
    # listájának engedélyezése után ugyanazt a mintamappát jelöljük ki.
    if parancs_nev == "menuFolderShow":
        vezerlo.toggleFolderHidden(minta_ut)
        vezerlo.setShowHidden(True)
        vezerlo.selectFolder(minta_ut)

    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    assert _varj(
        qt_app,
        lambda: _szoveg(toolbar, "searchText") == ""
        and vezerlo.property("searchActive") is False
        and vezerlo.property("currentFolder") == minta_ut
        and minta_ut in tuple(vezerlo.folders.folder_paths())
        and not any(
            menu.property("opened") is True for menu in _menuk(menu_bar)
        ),
    ), "a bejáró nem állt vissza a kereső és a mintamappa alaphelyzetébe"


def _akcio(
    ablak, vezerlo, minta, menu_bar, qt_app, cim, leiras, cel, kulsok,
    *, passport_vezerlo=None,
):
    nev = str(leiras.get("nev", ""))
    nyelvi_parancs = nev.startswith("menuLanguage")
    if nyelvi_parancs and not (
        _NYELV_ALMENU_MIN_MAGASSAG - 5
        <= ablak.height()
        <= _NYELV_ALMENU_MIN_MAGASSAG + 5
    ):
        celmagassag = _NYELV_ALMENU_MIN_MAGASSAG
        ablak.setHeight(celmagassag)
        assert _varj(qt_app, lambda: ablak.height() == celmagassag), (
            f"az ablakmagasság nem állt be a {celmagassag} px értékre"
        )
    elif not nyelvi_parancs and ablak.height() > 1000:
        ablak.setHeight(_ABLAK_ALAPMAGASSAG)
        assert _varj(qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG)
    _allitsd_vissza_a_mintamappat(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        parancs_nev=str(leiras.get("nev", "")),
    )
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    if nev == "menuPictureUnhide":
        vezerlo.toggleHiddenRows([0])
        vezerlo.setShowHidden(True)
        vezerlo.selectFolder(str(minta))
        assert vezerlo.photos.photos[0].hidden is True, (
            "az Unhide parancs előfeltétele nem állt elő"
        )
        ablak.setProperty("selectedIndexes", [0])
        ablak.setProperty("selectedIndex", 0)
        qt_app.processEvents()
    qt_app.processEvents()
    sor = _elero_menu(menu_bar, qt_app, cim, leiras["utvonal"])
    nev = sor.objectName()
    parancs = " › ".join(leiras["feliratok"])
    keput = _kepernyout(cel, cim, leiras)
    if sor.property("visible") is not True:
        kepkesz = _kepernyokep(ablak, keput)
        _allitsd_vissza_a_mintamappat(ablak, vezerlo, minta, menu_bar, qt_app)
        indok = _LETILTOTT_A_TISZTA_MINTABAN.get(nev)
        return {
            "menu": cim,
            "utvonal": tuple(leiras["utvonal"]),
            "parancs": parancs,
            "eredmeny": "rejtett állapotban maradt; nem kattintható"
            + (f"; indoklás: {indok}" if indok else ""),
            "kep": str(keput) if kepkesz else "",
            "hiba": indok is None,
        }
    if sor.property("enabled") is not True:
        kepkesz = _kepernyokep(ablak, keput)
        _allitsd_vissza_a_mintamappat(ablak, vezerlo, minta, menu_bar, qt_app)
        indok = _LETILTOTT_A_TISZTA_MINTABAN.get(nev)
        return {
            "menu": cim,
            "utvonal": tuple(leiras["utvonal"]),
            "parancs": parancs,
            "eredmeny": "feltételesen letiltott; nem kattintható"
            + (f"; indoklás: {indok}" if indok else ""),
            "kep": str(keput) if kepkesz else "",
            "hiba": indok is None,
        }

    elotte = _allapot(ablak, vezerlo, minta)
    dialogusok_elotte = {
        dialogus.objectName() or dialogus.metaObject().className()
        for dialogus in _lathato_dialogusok(ablak)
    }
    kulso_elotte = len(kulsok)
    elsult = []
    sor.triggered.connect(lambda *_args: elsult.append(True))
    _kattints(qt_app, sor)

    _varj(
        qt_app,
        lambda: bool(_lathato_dialogusok(ablak))
        or _feluleti_allapot(ablak) != elotte["felulet"],
        1.0,
    )
    # #4503: a háttérmunkás parancsok (kötegelt szerkesztés, XMP-írás) hatása a
    # munka VÉGÉN látszik; a CI lassabb gépén az 1 mp kevés volt, és a bejáró
    # véletlenszerűen „nem látszott változás”-t mondott. Ha nincs futó munka,
    # azonnal visszatér.
    wait_for_all_background_workers(15.0)
    qt_app.processEvents()
    if nev == "menuToolsPassportPhoto":
        assert passport_vezerlo is not None, (
            "az útlevélkép háttérmunkájának vezérlője hiányzik"
        )
        assert passport_vezerlo.waitForBackgroundWorkers(3.0), (
            "az útlevélkép háttérmunkája nem fejeződött be"
        )
        qt_app.processEvents()
    if nyelvi_parancs and ablak.height() > _ABLAK_ALAPMAGASSAG + 5:
        # A hosszú nyelvlistát ideiglenesen magas ablakban kattintjuk; a
        # párbeszéd középre igazodik, így a lementett bizonyító kép normál
        # méretű marad és nem foglal nyelvenként nagy képkocka-puffert.
        ablak.setHeight(_ABLAK_ALAPMAGASSAG)
        assert _varj(qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG), (
            "a nyelvparancs utáni ablakméret-visszaállítás nem sikerült"
        )
    utana = _allapot(ablak, vezerlo, minta)
    hatasok = _kulonbsegek(elotte, utana)
    for dialogus in _lathato_dialogusok(ablak):
        dialogusnev = dialogus.objectName() or dialogus.metaObject().className()
        if dialogusnev not in dialogusok_elotte:
            hatasok.append(f"megnyílt párbeszédablak: {dialogusnev}")
    if len(kulsok) > kulso_elotte:
        hatasok.append("külső művelet átadva: " + "; ".join(kulsok[kulso_elotte:]))

    kepkesz = _kepernyokep(ablak, keput)
    hiba = False
    if not elsult:
        eredmeny = "a menüsori kattintás nem bocsátott ki aktiválást"
        hiba = True
    elif not hatasok:
        if bool(sor.property("checkable")) and sor.property("checked") is True:
            eredmeny = "már kiválasztott állapot; az érték nem változott"
        elif nev in _NINCS_LATHATO_HATAS or (cim, parancs) in _NINCS_LATHATO_HATAS_UTVONAL:
            eredmeny = _NINCS_LATHATO_HATAS.get(
                nev, _NINCS_LATHATO_HATAS_UTVONAL.get((cim, parancs), "")
            )
        elif _rendszergyoker_hianyzik(nev):
            eredmeny = (
                "a rendszermappa ezen a gépen nem létezik: visszaesés a teljes "
                "fára, az eredeti szerint (spec 4.6)"
            )
        elif nev == "menuFileExit":
            eredmeny = "a kilépési parancs a kattintásra elsült"
        else:
            eredmeny = "kattintás után nem látszott ablak-, panel- vagy állapotváltozás"
            hiba = True
    else:
        eredmeny = "; ".join(hatasok[:4])
    if not kepkesz:
        eredmeny += "; nem sikerült képernyőképet menteni"
        hiba = True

    bezaras = []
    _zarj_parbeszedeket(ablak, qt_app, bezaras)
    _zarj_nezot_es_fiokot(ablak, qt_app)
    if bezaras:
        eredmeny += "; " + ", ".join(bezaras)
        if any("nyitva maradt" in sor for sor in bezaras):
            hiba = True

    allapot_menulista = utana["mappalista"]
    allapot_mappa_rejtett = utana["mappa_rejtett"]
    _allitsd_vissza_a_mintamappat(ablak, vezerlo, minta, menu_bar, qt_app)

    return {
        "menu": cim,
        "utvonal": tuple(leiras["utvonal"]),
        "parancs": parancs,
        "eredmeny": eredmeny,
        "kep": str(keput),
        "hiba": hiba,
        "mappalista": allapot_menulista,
        "mappa_rejtett": allapot_mappa_rejtett,
    }


def _minta_kepek(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(400, 300))
    make_jpeg(lib / "b.jpg", size=(500, 400))
    make_jpeg(lib / "c.jpg", size=(640, 480))


@pytest.fixture
def tiszta_menuproba(qt_app, tmp_path, monkeypatch):
    from tests.app.qml_functional.conftest import _build_qml_app

    epito = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_minta_kepek,
        email_vezerlo=True,
        show_only_big_images=None,
    )
    ablak, vezerlo, motor = next(epito)
    # A közös fixture teszt-alapértékeit töröljük: a bejárás tiszta
    # profilból indul, a képernyőképek és az index kivételével.
    beallitas = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    beallitas.clear()
    beallitas.sync()
    assert not beallitas.allKeys(), "a próba felhasználói profilja nem üres"

    # A funkcionális QML-építő az alkalmazás többi vezérlőjét beköti, de a
    # DedupController-t a legtöbb meglévő próba nem használja. A menü teljes
    # bejárása viszont megnyitja a DedupDialogot, ezért a produkciós
    # context propertyt is meg kell adni a tiszta tesztalkalmazásnak.
    from picasapy.app.dedup_controller import DedupController

    dedup_controller = DedupController(tmp_path / "index.db", vezerlo._provider)
    motor.rootContext().setContextProperty("dedupController", dedup_controller)
    from picasapy.app.backup_controller import BackupController

    backup_controller = BackupController(tmp_path / "index.db", (str(tmp_path / "kepek"),))
    motor.rootContext().setContextProperty("backupController", backup_controller)

    # A kimenő kép/fájl műveletek a mintamappát használják; asztali programot
    # és fájlkezelőt nem indítunk el.
    monkeypatch.setattr(collage_output, "pictures_dir", lambda: tmp_path / "kepek")
    monkeypatch.setattr(movie_output, "pictures_dir", lambda: tmp_path / "kepek")
    import picasapy.app.fileops_controller as fileops_module

    kulso = []
    monkeypatch.setattr(
        fileops_module,
        "_open_url",
        lambda url: kulso.append(f"megnyitás: {url.toString()}") or True,
    )
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: kulso.append(f"fájlkezelő: {path}"),
    )
    monkeypatch.setattr(
        fileops_module,
        "open_folder_in_file_manager",
        lambda path: kulso.append(f"mappakezelő: {path}"),
    )
    import picasapy.app.wallpaper as wallpaper_module

    monkeypatch.setattr(
        wallpaper_module,
        "set_desktop_background",
        lambda path: kulso.append(f"asztali háttérkép: {path}") or "",
    )
    try:
        yield ablak, vezerlo, motor, tmp_path, kulso
    finally:
        # A közös építő bevárja a háttérmunkát és deleteLater-rel bontja le a
        # QQmlApplicationEngine-t. A motorhoz célzott deferred delete eseményt
        # még a Python-GC előtt kiürítjük, így a gyökérablak a motor tulajdonosi
        # sorrendjében semmisül meg.
        try:
            next(epito, None)
        finally:
            if shiboken6.isValid(motor):
                QCoreApplication.sendPostedEvents(motor, QEvent.Type.DeferredDelete)
            qt_app.processEvents()
        _QML_ELEMEK.clear()
        _UI_ELEMEK.clear()
        _DIALOG_ELEMEK.clear()
        _LOADER_ELEMEK.clear()
        _MENU_ELEMEK.clear()
        _MENU_FEJLECEK.clear()


@pytest.fixture(scope="module", autouse=True)
def scratch_jelentes(tmp_path_factory):
    _UTAK.clear()
    gyoker = tmp_path_factory.getbasetemp()
    yield gyoker
    sorok = [
        "# #4433 főmenü-bejárás — futási jegyzék",
        "",
        "A felvételek a scratch könyvtárban vannak; a teszt a tiszta, ideiglenes profilt használta.",
        "",
    ]
    alap_futasok = list(_UTAK)
    parancsok = {}
    for futas in alap_futasok:
        for ut in futas["eredmenyek"]:
            parancsok[
                (
                    futas["magassag"],
                    ut["menu"],
                    tuple(ut.get("utvonal", ())),
                )
            ] = ut
    osszes = list(parancsok.values())
    egyedi_utvonalak = {
        (ut["menu"], tuple(ut.get("utvonal", ()))) for ut in osszes
    }
    elteresek = [ut for ut in osszes if ut.get("hiba")]
    sorok.extend(
        [
            f"Egyedi menüútvonalak: {len(egyedi_utvonalak)}; ismételt megfigyelések összevonva: "
            f"{sum(len(futas['eredmenyek']) for futas in alap_futasok) - len(egyedi_utvonalak)}; "
            f"eltérésként jelölve: {len(elteresek)}.",
            "A jegyben említett 195 a korábbi futás ismétlésekkel számolt megfigyelésszáma; "
            "a #4331 új Film parancsával a menüsorban 186 különböző útvonal van.",
            "",
            "## Működési eltérések",
            "",
        ]
    )
    if elteresek:
        for ut in elteresek:
            sorok.append(
                f"- **{ut['menu']} › {ut['parancs']}** — {ut['eredmeny']}"
            )
    else:
        sorok.append("Nem észlelt működési eltérést.")
    sorok.append("")
    for futas in alap_futasok:
        eredmenyek = futas["eredmenyek"]
        sorok.append(f"## {futas['menu']} menü, ablakmagasság-eltolás: {futas['magassag']} px")
        sorok.append("")
        sorok.append("| Parancs | Megfigyelt eredmény | Képernyőkép |")
        sorok.append("|---|---|---|")
        for ut in eredmenyek:
            kep = Path(str(ut["kep"]))
            kepnev = str(kep.relative_to(gyoker)) if ut["kep"] else "—"
            sorok.append(
                f"| {ut['menu']} › {ut['parancs']} | {ut['eredmeny']} | {kepnev} |"
            )
        sorok.append("")
    cel = gyoker / "4433-fomenuk-futas.md"
    cel.write_text("\n".join(sorok), encoding="utf-8")
    print(f"[#4420] képernyőképek és futási jegyzék: {cel}")


def _bejarja_menu(
    tiszta_menuproba,
    qt_app,
    scratch_jelentes,
    rovid_nev: str,
    cim: str,
    *,
    magassag_eltolas: int = 0,
    parancsnev_prefix: str | None = None,
    parancsnev_kizaro_prefix: str | None = None,
    parancs_szelet: tuple[int, int] | None = None,
    felirat_elso: str | None = None,
    felirat_elso_kizaro: str | None = None,
    vart_darabszam: int | None = None,
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    _QML_ELEMEK.clear()
    celmagassag = _ABLAK_ALAPMAGASSAG + magassag_eltolas
    ablak.setHeight(celmagassag)
    assert _varj(qt_app, lambda: ablak.height() == celmagassag), (
        f"az ablak magassága nem állt be a {magassag_eltolas} px eltérésre"
    )
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    menu_bar = ablak.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    passport_vezerlo = _motor.rootContext().contextProperty("passportController")
    assert passport_vezerlo is not None, "a passportController nincs bekötve"
    parancsazonositok = set()
    for menu_rovid_nev, menu_cim in ((rovid_nev, cim),):
        menu = _megnyit(menu_bar, qt_app, menu_cim)
        kihagyott = {"placeholder": 0, "nyugdijazott": 0}
        parancsok = _parancsok(menu, menu_bar, kihagyas=kihagyott)
        if parancsnev_prefix is not None:
            parancsok = [
                parancs
                for parancs in parancsok
                if parancs["nev"].startswith(parancsnev_prefix)
            ]
        if parancsnev_kizaro_prefix is not None:
            parancsok = [
                parancs
                for parancs in parancsok
                if not parancs["nev"].startswith(parancsnev_kizaro_prefix)
            ]
        if felirat_elso is not None:
            parancsok = [
                parancs
                for parancs in parancsok
                if parancs["feliratok"]
                and parancs["feliratok"][0] == felirat_elso
            ]
        if felirat_elso_kizaro is not None:
            parancsok = [
                parancs
                for parancs in parancsok
                if not parancs["feliratok"]
                or parancs["feliratok"][0] != felirat_elso_kizaro
            ]
        if parancs_szelet is not None:
            parancsok = parancsok[slice(*parancs_szelet)]
        parancsazonositok.update(
            (menu_rovid_nev, tuple(parancs["utvonal"])) for parancs in parancsok
        )
        varakozo = list(parancsok)
        eredmenyek = []
        kor = 0
        while varakozo and kor < 4:
            kor += 1
            kesobbre = []
            tortent_kattintas = False
            for parancs in varakozo:
                try:
                    ut = _akcio(
                        ablak,
                        vezerlo,
                        tmp_path / "kepek",
                        menu_bar,
                        qt_app,
                        menu_rovid_nev,
                        parancs,
                        tmp_path / "kepernyokepek",
                        kulsok,
                        passport_vezerlo=passport_vezerlo,
                    )
                except Exception as exc:  # a hátralévő menütételeket is végigjárjuk
                    keput = _kepernyout(
                        tmp_path / "kepernyokepek", menu_rovid_nev, parancs
                    )
                    kepkesz = _kepernyokep(ablak, keput)
                    ut = {
                        "menu": menu_rovid_nev,
                        "utvonal": tuple(parancs["utvonal"]),
                        "parancs": " › ".join(parancs["feliratok"]),
                        "eredmeny": f"kattintási hiba: {type(exc).__name__}: {exc}",
                        "kep": str(keput) if kepkesz else "",
                        "hiba": True,
                    }
                    _allitsd_vissza_a_mintamappat(
                        ablak, vezerlo, tmp_path / "kepek", menu_bar, qt_app
                    )
                if parancs["nev"] == "menuFolderHide":
                    assert str(tmp_path / "kepek") not in ut.get("mappalista", ()), (
                        "a Folder ▸ Hide nem vette ki a mintamappát a mappalistából"
                    )
                    assert ut.get("mappa_rejtett") is True
                elif parancs["nev"] == "menuFolderShow":
                    assert str(tmp_path / "kepek") in ut.get("mappalista", ()), (
                        "a Folder ▸ Show nem tette vissza a mintamappát a mappalistába"
                    )
                    assert ut.get("mappa_rejtett") is False
                eredmenyek.append(ut)
                if (
                    ut["hiba"]
                    and (
                        "feltételesen letiltott" in ut["eredmeny"]
                        or "rejtett állapotban" in ut["eredmeny"]
                    )
                ):
                    kesobbre.append(parancs)
                else:
                    tortent_kattintas = True
            if not tortent_kattintas:
                break
            varakozo = kesobbre

        for parancs in varakozo:
            utvonal = " › ".join(parancs["feliratok"])
            korabbi = next(
                (
                    adat
                    for adat in eredmenyek
                    if adat["menu"] == menu_rovid_nev and adat["parancs"] == utvonal
                ),
                None,
            )
            if korabbi is not None:
                korabbi["eredmeny"] += "; a bejárás végéig letiltva/rejtve maradt"
                continue
            eredmenyek.append(
                {
                    "menu": menu_rovid_nev,
                    "utvonal": tuple(parancs["utvonal"]),
                    "parancs": utvonal,
                    "eredmeny": "a tiszta mintában végig letiltva vagy rejtve maradt"
                    + (
                        "; indoklás: "
                        + _LETILTOTT_A_TISZTA_MINTABAN[parancs["nev"]]
                        if parancs["nev"] in _LETILTOTT_A_TISZTA_MINTABAN
                        else ""
                    ),
                    "kep": "",
                    "hiba": parancs["nev"] not in _LETILTOTT_A_TISZTA_MINTABAN,
                }
            )

        _UTAK.append(
            {
                "menu": menu_rovid_nev,
                "magassag": magassag_eltolas,
                "kihagyott": kihagyott,
                "eredmenyek": eredmenyek,
            }
        )
        for ut in eredmenyek:
            if not ut["kep"]:
                continue
            assert Path(str(ut["kep"])).is_file(), (
                f"hiányzik a képernyőkép: {ut['menu']} › {ut['parancs']}"
            )
    vart_darabszam = (
        _MENU_UTVONAL_DARAB[rovid_nev]
        if vart_darabszam is None
        else vart_darabszam
    )
    assert len(parancsazonositok) == vart_darabszam, (
        f"a {rovid_nev} menü útvonalainak száma eltér a {vart_darabszam}-től: "
        f"{len(parancsazonositok)}"
    )
    vegso_eredmenyek = {}
    for futas in _UTAK:
        if futas["menu"] != rovid_nev:
            continue
        for eredmeny in futas["eredmenyek"]:
            vegso_eredmenyek[(eredmeny["menu"], tuple(eredmeny.get("utvonal", ())))] = eredmeny
    hibak = [
        f"{eredmeny['menu']} › {eredmeny['parancs']}: {eredmeny['eredmeny']}"
        for eredmeny in vegso_eredmenyek.values()
        if eredmeny.get("hiba")
    ]
    assert not hibak, "a menü-bejárás észlelt hibái:\n" + "\n".join(hibak)
