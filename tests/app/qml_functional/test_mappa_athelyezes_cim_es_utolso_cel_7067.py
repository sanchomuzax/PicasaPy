"""A Mappa áthelyezése célválasztójának címe és megjegyzett útja (#7109).

Az eredeti a `Browse for Folder` rendszercímet használja, és a
`Preferences/MoveFolderLastPath` kulcsban megjegyzi a kiválasztott célt.
Itt valódi egérkattintással nyitjuk a menüből a választót, és valódi
áthelyezéssel írjuk a megjegyzett utat.

## Mit mér, és mit nem

A Qt 6.8 `FolderDialog`-ja a tartalék (nem natív, offscreen) megvalósításban
az ELSŐ megnyitás után a `currentFolder` módosítást figyelmen kívül hagyja
(mérve: egy önálló próbában az `open()` előtti és utáni írás is hatástalan).
Ezért a "következő megnyitás a megjegyzett célból indul" olvasási ágat egy
ÚJ munkamenet első nyitásán mérjük: a beállítás a build ELŐTT kerül a
tárolóba, ahogy egy korábbi futás hagyná. Az írási ágat külön teszt méri
(valódi áthelyezés, utána a tárolt érték), a kettő összekötését a vezérlő
tesztje (`tests/app/test_athelyezes_utolso_cel_7067.py`) fedi.

A natív mappaválasztó saját megjelenését ez a teszt nem méri; csak azokat a
tulajdonságokat, amiket a QML ad neki.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QSettings, Qt, QUrl

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek,
    jobbklikk_mappan,
    kattints,
    nyitott,
    zar,
)

_KULCS = "Preferences/MoveFolderLastPath"


def _beallitasok() -> QSettings:
    return QSettings("PicasaPy", "PicasaPy")


def _konyvtar(library: Path) -> None:
    make_jpeg(library / "a.jpg", size=(160, 120))
    source = library / "atmozgatando"
    other = library / "masik"
    target = library / "cel"
    for folder in (source, other, target):
        folder.mkdir()
    make_jpeg(source / "kep.jpg", size=(80, 60))
    make_jpeg(other / "kep.jpg", size=(80, 60))
    make_jpeg(target / "celkep.jpg", size=(80, 60))


def _epit(qt_app, tmp_path, request, megjegyzett_ut: str | None):
    """Az app felépítése a megadott (vagy üres) megjegyzett úttal."""
    from conftest import _build_qml_app

    beallitas = _beallitasok()
    if megjegyzett_ut is None:
        beallitas.remove(_KULCS)
    else:
        beallitas.setValue(_KULCS, megjegyzett_ut)
    beallitas.sync()
    try:
        yield from _build_qml_app(
            qt_app, tmp_path, kepeket_keszit=_konyvtar, keep_modul=request.module
        )
    finally:
        # a közös beállításokban nem marad nyom a többi teszt útjában
        _beallitasok().remove(_KULCS)


@pytest.fixture
def athelyezes_app(qt_app, tmp_path, request):
    """Első futás: nincs megjegyzett út."""
    yield from _epit(qt_app, tmp_path, request, None)


@pytest.fixture
def korabbi_futas_utan_app(qt_app, tmp_path, request):
    """Egy korábbi futás megjegyzett célmappájával (létező mappa)."""
    korabbi = tmp_path / "korabbi_cel"
    korabbi.mkdir()
    yield from _epit(qt_app, tmp_path, request, str(korabbi))


@pytest.fixture
def eltunt_cel_utan_app(qt_app, tmp_path, request):
    """Megjegyzett út, de a mappa már nincs meg."""
    yield from _epit(qt_app, tmp_path, request, str(tmp_path / "mar_nincs_meg"))


def _megnyit_menuvel(window, qt_app, mappa: Path):
    jobbklikk_mappan(window, qt_app, mappa)
    kattints(window, qt_app, gyerek(window, "folderMenuMoveFolder"))
    dialog = gyerek(window, "moveFolderDialog")
    assert varj_feltetelre(qt_app, lambda: nyitott(dialog), 5.0), (
        "a Mappa áthelyezése menü nem nyitotta meg a célválasztót"
    )
    return dialog


def _kezdomappa(dialog) -> Path:
    url = dialog.property("currentFolder")
    assert url is not None, "a célválasztó kezdőmappája hiányzik"
    return Path(url.toLocalFile())


def _indit(app, qt_app) -> Path:
    window, controller, _engine = app
    window.show()
    qt_app.processEvents()
    return Path(controller.currentFolder)


def test_a_celvalaszto_cime_browse_for_folder(athelyezes_app, qt_app):
    library = _indit(athelyezes_app, qt_app)
    window = athelyezes_app[0]

    dialog = _megnyit_menuvel(window, qt_app, library / "atmozgatando")

    assert dialog.property("title") == "Browse for Folder"
    zar(qt_app, dialog)


def test_a_cim_nem_valtozik_a_mozgatott_mappaval(athelyezes_app, qt_app):
    library = _indit(athelyezes_app, qt_app)
    window = athelyezes_app[0]

    elso = _megnyit_menuvel(window, qt_app, library / "atmozgatando")
    assert elso.property("title") == "Browse for Folder"
    zar(qt_app, elso)

    masodik = _megnyit_menuvel(window, qt_app, library / "masik")
    assert masodik.property("title") == "Browse for Folder"
    zar(qt_app, masodik)


def test_megjegyzett_cel_nelkul_a_kezdohely_a_mozgatott_mappa(
    athelyezes_app, qt_app
):
    library = _indit(athelyezes_app, qt_app)
    window = athelyezes_app[0]

    dialog = _megnyit_menuvel(window, qt_app, library / "atmozgatando")

    assert _kezdomappa(dialog) == library / "atmozgatando"
    zar(qt_app, dialog)


def test_a_korabbi_futas_celmappajabol_indul_az_elso_nyitas(
    korabbi_futas_utan_app, qt_app, tmp_path
):
    library = _indit(korabbi_futas_utan_app, qt_app)
    window = korabbi_futas_utan_app[0]

    dialog = _megnyit_menuvel(window, qt_app, library / "atmozgatando")

    assert _kezdomappa(dialog) == tmp_path / "korabbi_cel", (
        "a célválasztó nem a megjegyzett célmappából indult"
    )
    assert dialog.property("title") == "Browse for Folder"
    zar(qt_app, dialog)


def test_eltunt_megjegyzett_cel_utan_a_mozgatott_mappa_a_kezdohely(
    eltunt_cel_utan_app, qt_app
):
    library = _indit(eltunt_cel_utan_app, qt_app)
    window = eltunt_cel_utan_app[0]

    dialog = _megnyit_menuvel(window, qt_app, library / "atmozgatando")

    assert _kezdomappa(dialog) == library / "atmozgatando"
    zar(qt_app, dialog)


def test_sikeres_athelyezes_megjegyzi_a_valasztott_celmappat(athelyezes_app, qt_app):
    library = _indit(athelyezes_app, qt_app)
    window = athelyezes_app[0]
    source = library / "atmozgatando"
    target = library / "cel"

    dialog = _megnyit_menuvel(window, qt_app, source)
    assert _beallitasok().value(_KULCS) is None
    dialog.setProperty("selectedFolder", QUrl.fromLocalFile(str(target)))
    QMetaObject.invokeMethod(dialog, "accepted", Qt.ConnectionType.DirectConnection)
    assert varj_feltetelre(
        qt_app,
        lambda: (target / "atmozgatando").is_dir() and not source.exists(),
        20.0,
    ), "az áthelyezés nem ment végig"
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)
    zar(qt_app, dialog)

    tarolt = _beallitasok().value(_KULCS)
    assert tarolt is not None, "a sikeres áthelyezés nem jegyezte meg a célmappát"
    assert Path(str(tarolt)) == target


def test_megszakitott_valasztas_nem_jegyzi_meg_a_celt(athelyezes_app, qt_app):
    library = _indit(athelyezes_app, qt_app)
    window = athelyezes_app[0]

    dialog = _megnyit_menuvel(window, qt_app, library / "atmozgatando")
    dialog.setProperty("selectedFolder", QUrl.fromLocalFile(str(library / "cel")))
    zar(qt_app, dialog)

    assert _beallitasok().value(_KULCS) is None
    assert (library / "atmozgatando").is_dir()
