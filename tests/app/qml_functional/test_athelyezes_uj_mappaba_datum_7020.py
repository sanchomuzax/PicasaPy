"""Az Áthelyezés új mappába ablak dátuma a kijelölt kép dátuma + 1 mp (#7020).

Az eredeti Picasa 3.9-ben (#7008) a `0x005e9a42` a `0x004ae0a0`-val lekéri a
kép idejét, a `0x005e9a47` hozzáad `0xcf50c8` = 1/86400 napot. Több kijelölt
képnél az eredeti az aktuális elemet olvassa (`[ebp+0xeac]+0x3c0`); nálunk
ennek a fókuszban lévő (utoljára aktív, `selectedIndex`) kép felel meg.

A forrás: `photos.itemAt(sor).takenAt`, a kézi felülírás vagy az EXIF ideje,
ugyanaz, amit a rács mutat (a Tulajdonságok „Camera Date” sora is a kézi
felülírást részesíti előnyben).

Minden próba valódi kattintással indul: a Fájl menü „Áthelyezés új mappába”
tételére, illetve a kép helyi menüjének megfelelő sorára. Az ablak dátummezőjét
olvassuk vissza, parancsot közvetlenül nem indítunk.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QDate, QMetaObject, Qt

from picasapy.ini import load_or_empty, read_folder_date_override

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA, app_epitese, gyerek, mappa_ut, tetel_kattintasa, varj,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    jobbklikk_fotón, kattints,
)
from tests.support.jpeg_factory import make_jpeg

#: képnév -> (EXIF DateTimeOriginal, a +1 mp utáni nap)
KEPEK = {
    "a_regi.jpg": ("2019:07:04 10:20:30", "2019-07-04"),
    "b_ejfel.jpg": ("2021:12:31 23:59:59", "2022-01-01"),
    "c_kesobbi.jpg": ("2022:05:06 08:09:10", "2022-05-06"),
}
#: dátum nélküli kép: a mai napra esik vissza, ahogy eddig
DATUMTALAN = "d_datumtalan.jpg"


def _keszit(lib: Path) -> None:
    fotok = lib / MAPPA
    fotok.mkdir()
    for nev, (felvetel, _nap) in KEPEK.items():
        make_jpeg(fotok / nev, size=(64, 48), taken_at=felvetel)
    make_jpeg(fotok / DATUMTALAN, size=(64, 48))


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_keszit)


def _sor(controller, nev: str) -> int:
    for i in range(controller.photos.rowCount()):
        if Path(controller.photos.filePathAt(i)).name == nev:
            return i
    raise AssertionError(f"{nev} nincs a rácson")


def _betolt(window, qt_app, controller) -> None:
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(mappa_ut(controller)))
    assert varj(qt_app, lambda: controller.photos.rowCount() == len(KEPEK) + 1), (
        "a teszt mappája nem töltődött be"
    )


def _kijelol(window, qt_app, sorok, aktiv: int) -> None:
    """A kijelölés és a fókuszban lévő (utoljára aktív) kép külön adható."""
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", aktiv)
    qt_app.processEvents()


def _ablak_a_menubol(window, qt_app):
    tetel_kattintasa(window, qt_app, "&File", "menuFileMoveToNewFolder")
    dialog = gyerek(window, "moveToNewFolderDialog")
    assert varj(qt_app, lambda: dialog.property("opened") is True), (
        "a Fájl ▸ Áthelyezés új mappába nem nyitott ablakot"
    )
    return dialog


def _mezo_iso(dialog) -> str:
    """A dátummező szövegének ISO-alakja, az ablak saját olvasójával."""
    mezo = gyerek(dialog, "folderPropertiesDateField")
    assert mezo.property("text"), "a dátummező üres"
    return str(QMetaObject.invokeMethod(
        dialog, "_fieldToIso", Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", mezo.property("text")),
    ))


@pytest.mark.parametrize("nev", sorted(KEPEK))
def test_menubol_nyitott_ablak_a_kijelolt_kep_napjat_mutatja(app, qt_app, nev):
    window, controller, _ = app
    _betolt(window, qt_app, controller)
    sor = _sor(controller, nev)
    assert controller.photos.itemAt(sor)["takenAt"][:10] == (
        KEPEK[nev][0][:10].replace(":", "-")
    ), "a fixture képe nem a várt felvételi idővel került az indexbe"
    _kijelol(window, qt_app, [sor], sor)

    dialog = _ablak_a_menubol(window, qt_app)

    elvart = KEPEK[nev][1]
    assert dialog.property("currentDate") == elvart
    assert _mezo_iso(dialog) == elvart


def test_ejfel_elotti_egy_masodperces_kep_a_kovetkezo_napot_adja(app, qt_app):
    """A +1 másodperc a napi határt átlépi: 2021-12-31 23:59:59 -> 2022-01-01."""
    window, controller, _ = app
    _betolt(window, qt_app, controller)
    sor = _sor(controller, "b_ejfel.jpg")
    _kijelol(window, qt_app, [sor], sor)

    dialog = _ablak_a_menubol(window, qt_app)

    assert "2021-12-31" in controller.photos.itemAt(sor)["takenAt"]
    assert _mezo_iso(dialog) == "2022-01-01"


@pytest.mark.parametrize("aktiv", ["a_regi.jpg", "c_kesobbi.jpg"])
def test_tobb_kijelolt_kepnel_a_fokuszban_levo_kep_datuma_szamit(
    app, qt_app, aktiv
):
    window, controller, _ = app
    _betolt(window, qt_app, controller)
    sorok = [_sor(controller, "a_regi.jpg"), _sor(controller, "c_kesobbi.jpg")]
    _kijelol(window, qt_app, sorok, _sor(controller, aktiv))

    dialog = _ablak_a_menubol(window, qt_app)

    assert _mezo_iso(dialog) == KEPEK[aktiv][1]
    assert len(dialog.property("splitPaths").toVariant()) == 2


def test_helyi_menubol_nyitott_ablak_is_a_kep_napjat_mutatja(app, qt_app):
    window, controller, _ = app
    _betolt(window, qt_app, controller)
    sor = _sor(controller, "a_regi.jpg")
    _kijelol(window, qt_app, [sor], sor)

    jobbklikk_fotón(window, qt_app, sor)
    kattints(window, qt_app, gyerek(window, "contextMenuMove"))
    dialog = gyerek(window, "moveToNewFolderDialog")
    assert varj(qt_app, lambda: dialog.property("opened") is True)

    assert _mezo_iso(dialog) == KEPEK["a_regi.jpg"][1]


def test_datum_nelkuli_kepnel_marad_a_mai_nap(app, qt_app):
    window, controller, _ = app
    _betolt(window, qt_app, controller)
    sor = _sor(controller, DATUMTALAN)
    assert controller.photos.itemAt(sor)["takenAt"] == ""
    _kijelol(window, qt_app, [sor], sor)

    dialog = _ablak_a_menubol(window, qt_app)

    assert _mezo_iso(dialog) == QDate.currentDate().toString(Qt.DateFormat.ISODate)


def test_ok_a_kep_napjat_irja_a_uj_mappa_ini_jebe(app, qt_app):
    """Végig: a kép napja kerül a létrejött mappa `.picasa.ini` dátumába."""
    window, controller, _ = app
    _betolt(window, qt_app, controller)
    sor = _sor(controller, "b_ejfel.jpg")
    _kijelol(window, qt_app, [sor], sor)

    dialog = _ablak_a_menubol(window, qt_app)
    kattints(window, qt_app, gyerek(dialog, "folderPropertiesOkButton"))

    cel = mappa_ut(controller) / "Untitled"
    assert varj(qt_app, lambda: (cel / "b_ejfel.jpg").is_file())
    assert varj(qt_app, lambda: (cel / ".picasa.ini").is_file())
    dokumentum = load_or_empty(cel / ".picasa.ini")
    assert read_folder_date_override(dokumentum) == "2022-01-01"
