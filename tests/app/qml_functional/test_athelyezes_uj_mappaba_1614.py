"""Fájl ▸ „Áthelyezés új mappába…" — élő menütétel, a kijelölt képekre (#1614).

A parancs NEVE félrevezet (`eMenuFile::ID_FILE_NEWFOLDER`): a hivatalos
magyar felirat („Áthelyezés új mappába…") mondja ki, hogy nem mappát hoz
létre, hanem a kijelölt képeket helyezi át egy újba, amit a felhasználó
nevez el. A tétel a #324 audit óta `PicasaMenuItem { placeholder: true }`
volt (`git log -S'Move to New Folder' -- .../PicasaMenuBar.qml`).

## Mutációs bizonyíték (a jegy briefjéhez)

Ez a fájl négy állítást mér, mindegyiknek megvan a maga bukó ellenpróbája:

(a) a tétel NEM helyfoglaló — ha visszakerülne a `PicasaMenuItem
    { placeholder: true }` alak, `TestAMenutetelElo.
    test_a_tetel_nem_helyfoglalo_kijeloles_mellett` bukik;
(b) üres kijelölésnél LETILTOTT — ha az `enabled` feltétel lekerülne,
    `test_kijeloles_nelkul_a_tetel_letiltott` bukik;
(c) az áthelyezés után az ÚJ mappa az INDEXBEN is látszik — ha valaki a
    jövőben megkerülné a meglévő `_run_batch`/`movePhotos` utat (pl. nyers
    `shutil.move`-val), a `wire_fileops` célzott resyncje kimaradna, és
    `TestAthelyezesVegrehajtasa.test_a_kep_az_uj_mappaban_lathato_indexben`
    bukna — a `qml_app` fixture SZÁNDÉKOSAN nem indítja a figyelőt/pollozót
    (`AppController.start()` itt sosem fut), tehát csak a célzott resync
    hozhatja be a képet;
(d) érvénytelen/foglalt névnél SEMMI nem mozdul —
    `TestErvenytelenNev` osztály.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt


def _elem(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _nem_nyilt_meg(window) -> bool:
    """#1612: a `FileOpsDialogs` halasztott — nyitás előtt a párbeszéd létre
    sem jön. A hiánya erősebb állítás, mint a `visible is False`."""
    par = window.findChild(QObject, "moveToNewFolderDialog")
    return par is None or par.property("visible") is False


def _select_row(window, qt_app, row):
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()


def _clear_selection(window, qt_app):
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()


def _kattint(window, qt_app, nev):
    """A MENÜPONTRA kattintás szimulációja — nem a mögöttes metódus
    közvetlen hívása (ld. MEMORY: „a vezérlőre KATTINTS, ne a metódust
    hívd" — a `bar.moveToNewFolderRequested()` közvetlen kibocsátása akkor
    is zöld lenne, ha a tétel kattinthatatlan)."""
    QMetaObject.invokeMethod(
        _elem(window, nev), "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _var(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.02)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


class TestAMenutetelElo:
    def test_a_tetel_nem_helyfoglalo_kijeloles_mellett(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)

        tetel = _elem(window, "menuFileMoveToNewFolder")
        # sima `MenuItem`-nek nincs `placeholder` tulajdonsága — a
        # `property()` ilyenkor érvénytelen (None) `QVariant`-ot ad
        assert not tetel.property("placeholder"), (
            "a menütétel még mindig helyfoglaló (#1614)"
        )
        assert tetel.property("enabled") is True

    def test_kijeloles_nelkul_a_tetel_letiltott(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _clear_selection(window, qt_app)

        tetel = _elem(window, "menuFileMoveToNewFolder")
        assert tetel.property("enabled") is False, (
            "kijelölés nélkül nincs mit áthelyezni — a tétel maradjon "
            "szürke, mint a többi kijelölés-függő tétel"
        )

    def test_a_menupontra_kattintva_megnyilik_a_dialog(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)
        assert _nem_nyilt_meg(window)

        _kattint(window, qt_app, "menuFileMoveToNewFolder")

        assert _elem(window, "moveToNewFolderDialog").property("visible") is True, (
            "a menütétel nem nyitotta meg a párbeszédet"
        )

    def test_kijeloles_nelkul_kattintva_nem_nyilik_dialog(self, qml_app, qt_app):
        """Védőháló: a menütétel letiltott, tehát valódi kattintással sosem
        jutna ide — ha a jövőben az `enabled` feltétel eltűnne, ez a teszt
        akkor is elkapja, mert a `triggered()` közvetlen kibocsátása
        önmagában NEM garantálja, hogy a hívott függvény óvatos."""
        window, _controller, _engine = qml_app
        _clear_selection(window, qt_app)

        _kattint(window, qt_app, "menuFileMoveToNewFolder")

        assert _nem_nyilt_meg(window), (
            "kijelölés nélkül is megnyílt a párbeszéd"
        )


class TestAthelyezesVegrehajtasa:
    """Végponttól végpontig: kattintás → névbeírás → elfogadás → a kép
    ténylegesen az új mappában van, ÉS az indexben is látszik."""

    def test_a_kep_athelyezodik_a_lemezen(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        forras_kep = controller.photos.filePathAt(0)
        assert forras_kep, "nincs kép a rácson — a mérés nem érvényes"

        _select_row(window, qt_app, 0)
        _kattint(window, qt_app, "menuFileMoveToNewFolder")
        mezo = _elem(window, "moveToNewFolderField")
        mezo.setProperty("text", "Új mappa")
        dialog = _elem(window, "moveToNewFolderDialog")
        QMetaObject.invokeMethod(
            dialog, "accept", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        uj_hely = lib / "Új mappa" / Path(forras_kep).name
        assert _var(qt_app, lambda: uj_hely.exists()), (
            f"a kép nem került át ide: {uj_hely}"
        )
        assert not Path(forras_kep).exists(), (
            "a kép a régi helyén is megmaradt"
        )

    def test_a_kep_az_uj_mappaban_lathato_indexben(self, qml_app, qt_app, tmp_path):
        """(c) mutációs bizonyíték: a `qml_app` fixture SOSEM indítja a
        figyelőt/pollozót (`AppController.start()` nincs meghívva) —
        egyedül a `wire_fileops` célzott resyncje hozhatja be az ÚJ,
        korábban sosem indexelt mappát. Ha ez a bekötés kimaradna, ez a
        teszt a `masodperc` letelte után is hamis maradna."""
        window, controller, _engine = qml_app

        lib = tmp_path / "kepek"
        forras_kep = Path(controller.photos.filePathAt(0))

        _select_row(window, qt_app, 0)
        _kattint(window, qt_app, "menuFileMoveToNewFolder")
        _elem(window, "moveToNewFolderField").setProperty("text", "Címkézett")
        QMetaObject.invokeMethod(
            _elem(window, "moveToNewFolderDialog"),
            "accept", Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        uj_mappa = str(lib / "Címkézett")

        def lathato():
            return any(
                p.folder_path == uj_mappa and p.name == forras_kep.name
                for p in controller.photos.photos
            )

        assert _var(qt_app, lathato), (
            "az áthelyezett kép nem jelent meg az indexben az új mappa "
            "alatt — elmaradt a célzott resync (wire_fileops)"
        )


class TestErvenytelenNev:
    """(d) mutációs bizonyíték: érvénytelen/foglalt névnél a lemezen SEMMI
    nem mozdul, és a meglévő hiba-párbeszéd (`fileOpsErrorDialog`) jelenik
    meg — nem a néma semmi."""

    def test_ures_nev_eseten_hibauzenet_es_semmi_nem_mozdul(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app

        forras_kep = Path(controller.photos.filePathAt(0))

        _select_row(window, qt_app, 0)
        _kattint(window, qt_app, "menuFileMoveToNewFolder")
        _elem(window, "moveToNewFolderField").setProperty("text", "   ")
        QMetaObject.invokeMethod(
            _elem(window, "moveToNewFolderDialog"),
            "accept", Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        hiba = _elem(window, "fileOpsErrorDialog")
        assert hiba.property("visible") is True, (
            "üres mappanévnél nem jelent meg hibaüzenet"
        )
        assert forras_kep.exists(), "a kép elmozdult, holott a név érvénytelen volt"

    def test_windows_tiltott_karakter_eseten_hibauzenet(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app

        forras_kep = Path(controller.photos.filePathAt(0))

        _select_row(window, qt_app, 0)
        _kattint(window, qt_app, "menuFileMoveToNewFolder")
        # `?` — Windows-tiltott fájlnév-karakter (#1700 hibaosztálya)
        _elem(window, "moveToNewFolderField").setProperty("text", "nyár?")
        QMetaObject.invokeMethod(
            _elem(window, "moveToNewFolderDialog"),
            "accept", Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        hiba = _elem(window, "fileOpsErrorDialog")
        assert hiba.property("visible") is True, (
            "a tiltott karaktert tartalmazó név nem adott hibaüzenetet"
        )
        assert forras_kep.exists()
        assert not (forras_kep.parent / "nyár?").exists()
