"""#7100: az Add to Album almenü a fotó helyi menüjében ÉS a nézőben.

Az eredeti `0x0056c5a0` a fotómenü (`0x70`, `0xa4`, `0x13d`) és a néző (`0x8a`)
almenüjét azonos sorrenddel építi: albumok, elválasztó (ha van album),
`Starred Photos`, `Screensaver`, elválasztó, `New Album...`. Az almenü albumok
nélkül is elérhető. A `Starred Photos` HOZZÁAD (nem fordít). A `New Album...`
ablak dátuma a kijelölés első képének ideje mínusz egy másodperc.

Minden próba valódi egérkattintással nyitja a menüt és az almenüt, és a RAJZOLT
sorokat olvassa (felületi pozíció + a menü tételsora), nem csak a számolt
geometriát. Az eredeti almenü képernyőképével az összevetést ez a fájl NEM
végzi: a képernyőkép nincs a gépen (a kiadási képeket a
`PICASAPY_7100_SCREENSHOT_DIR` mappába menti, ha be van állítva).

Külső program nincs a próbákban.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints as fomenu_kattints,
    _objektum as fomenu_objektum,
)
from tests.app.qml_functional._teszt_menu_6861 import megnyit_fomenu
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA,
    app_epitese,
    mappa_ut,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    _elem_ablaka,
    album_darab,
    almenu_megnyitasa,
    foto_utja,
    gyerek,
    jobbklikk_fotón,
    kattints,
    kijelol,
    keres_vizualis_mindenablakban,
    varj,
    zar,
)

#: éjfélkor készült kép: a -1 mp az ELŐZŐ napot adja (2025-04-30)
_KORAI = "a_ejfel.jpg"
#: délben készült kép: a -1 mp ugyanazt a napot adja (2025-06-15)
_KESOBBI = "b_del.jpg"
_STARRED = "contextMenuAddToStarredPhotos"
_SCREENSAVER = "contextMenuAddToScreensaver"
_NEW_ALBUM = "contextMenuNewAlbum"
_V_STARRED = "viewerMenuAddToStarredPhotos"
_V_SCREENSAVER = "viewerMenuAddToScreensaver"
_V_NEW_ALBUM = "viewerMenuNewAlbum"
_ELVALASZTO = "--"


def _kepeket_keszit(lib: Path) -> None:
    mappa = lib / MAPPA
    mappa.mkdir()
    make_jpeg(mappa / _KORAI, size=(160, 120), taken_at="2025:05:01 00:00:00")
    make_jpeg(mappa / _KESOBBI, size=(160, 120), taken_at="2025:06:15 12:00:00")


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_kepeket_keszit)


def _betolt(window, qt_app, controller) -> dict[str, int]:
    """Megjeleníti az ablakot, betölti a mappát; név -> sor."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(mappa_ut(controller)))
    assert varj(qt_app, lambda: len(controller.photos.photos) == 2), (
        "a teszt mappája nem töltődött be"
    )
    return {foto.name: sor for sor, foto in enumerate(controller.photos.photos)}


def _csillagos(controller, sor: int) -> bool:
    return bool(controller.photos.photos[sor].star)


def _ini_csillag(controller, nev: str) -> bool:
    ini = mappa_ut(controller) / ".picasa.ini"
    if not ini.is_file():
        return False
    szoveg = ini.read_text(encoding="utf-8")
    szakasz = szoveg.split(f"[{nev}]", 1)
    return len(szakasz) == 2 and "star=yes" in szakasz[1].split("[", 1)[0]


def _tetelsor(almenu) -> list[str]:
    """Az almenü LÁTSZÓ tételei sorrendben: a tétel objectName-je, az
    elválasztó `--` (a szövegtelen elem)."""
    kifejezes = QQmlExpression(qmlContext(almenu), almenu, (
        "(function () { var r = [];"
        " for (var i = 0; i < count; ++i) {"
        "   var t = itemAt(i);"
        "   if (!t.visible || t.height <= 0) continue;"
        "   r.push(typeof t.text === 'undefined' ? '--' : t.objectName)"
        " } return r.join('|') })()"
    ))
    ertek, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    return str(ertek).split("|") if str(ertek) else []


def _kiadasi_kep(window, elem, nev: str) -> None:
    mappa = os.environ.get("PICASAPY_7100_SCREENSHOT_DIR")
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    kep = _elem_ablaka(window, elem).grabWindow()
    assert not kep.isNull(), "a kiadáskép üres"
    assert kep.save(str(cel / nev), "PNG"), f"a kiadáskép nem menthető: {nev}"


def _foto_almenu(window, qt_app, sor: int):
    menu = jobbklikk_fotón(window, qt_app, sor)
    almenu_megnyitasa(window, qt_app, menu, "contextMenuAddToAlbum")
    return menu, gyerek(window, "contextMenuAddToAlbum")


def _nezo_almenu(window, qt_app, sor: int):
    window.setProperty("viewerOpen", True)
    nezo = gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", sor)
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        nezo, "openContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    menu = gyerek(window, "viewerContextMenu")
    assert varj(qt_app, lambda: menu.property("opened") is True), (
        "a néző jobbklikk-menüje nem nyílt meg"
    )
    almenu_megnyitasa(window, qt_app, menu, "viewerMenuAddToAlbum")
    return menu, gyerek(window, "viewerMenuAddToAlbum")


def _y(elem) -> float:
    return elem.mapToScene(QPointF(0, 0)).y()


def _felulet_sorrend_es_elvalaszto(window, nevek: tuple[str, str, str]) -> None:
    """A három különleges sor FELÜLETI sorrendje, és a `Screensaver` és a
    `New Album...` között elválasztó rajzolódik (a lépésköz nagyobb, mint a
    `Starred Photos` és a `Screensaver` közötti)."""
    sorok = [keres_vizualis_mindenablakban(window, nev) for nev in nevek]
    assert all(sor is not None for sor in sorok), (
        f"nem látszik az almenü minden sora: {nevek}"
    )
    assert [str(sor.property("text")) for sor in sorok] == [
        "Starred Photos", "Screensaver", "New Album...",
    ]
    y = [_y(sor) for sor in sorok]
    assert y == sorted(y) and len(set(y)) == 3, f"a sorok sorrendje eltér: {y}"
    assert (y[2] - y[1]) > (y[1] - y[0]), (
        "a Screensaver és a New Album... között nem rajzolódik elválasztó"
    )


# -- a fotó helyi menüje ----------------------------------------------------


class TestFotoAlmenu:
    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_album_nelkul_starred_screensaver_elvalaszto_new_album(
        self, mappa_app, qt_app, height_offset
    ):
        window, controller, _motor = mappa_app
        _betolt(window, qt_app, controller)
        celmagas = window.height() + height_offset
        window.setHeight(celmagas)
        assert varj(qt_app, lambda: window.height() == celmagas)
        kijelol(window, qt_app, [0])
        assert controller.albums == []

        menu, almenu = _foto_almenu(window, qt_app, 0)

        assert _tetelsor(almenu) == [_STARRED, _SCREENSAVER, _ELVALASZTO, _NEW_ALBUM]
        _felulet_sorrend_es_elvalaszto(window, (_STARRED, _SCREENSAVER, _NEW_ALBUM))
        if height_offset == 0:
            _kiadasi_kep(
                window, keres_vizualis_mindenablakban(window, _STARRED),
                "picasapy-7100-foto-almenu-album-nelkul.png")
        zar(qt_app, menu)

    def test_albumokkal_albumok_elvalaszto_starred_screensaver_elvalaszto_new_album(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        elso = controller.createAlbum("Elso", [nevek[_KORAI]])
        masodik = controller.createAlbum("Masodik", [nevek[_KESOBBI]])
        assert elso and masodik
        assert varj(qt_app, lambda: len(controller.albums) == 2)
        kijelol(window, qt_app, [0])

        menu, almenu = _foto_almenu(window, qt_app, 0)

        sorrend = _tetelsor(almenu)
        assert sorrend[2:] == [
            _ELVALASZTO, _STARRED, _SCREENSAVER, _ELVALASZTO, _NEW_ALBUM,
        ], f"az almenü sorrendje: {sorrend}"
        assert sorted(sorrend[:2]) == sorted([
            f"contextMenuAddToAlbumItem_{elso}",
            f"contextMenuAddToAlbumItem_{masodik}",
        ])
        _felulet_sorrend_es_elvalaszto(window, (_STARRED, _SCREENSAVER, _NEW_ALBUM))
        _kiadasi_kep(
            window, keres_vizualis_mindenablakban(window, _STARRED),
            "picasapy-7100-foto-almenu-albumokkal.png")
        zar(qt_app, menu)

    def test_starred_photos_ketszer_valasztva_is_csillagos_marad(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        sor = nevek[_KESOBBI]
        assert not _csillagos(controller, sor), "a próba feltétele: nincs csillag"
        kijelol(window, qt_app, [sor])

        for kor in (1, 2):
            menu, _almenu = _foto_almenu(window, qt_app, sor)
            kattints(window, qt_app, keres_vizualis_mindenablakban(window, _STARRED))
            assert varj(
                qt_app, lambda: _csillagos(controller, sor) and _ini_csillag(
                    controller, _KESOBBI)
            ), f"a {kor}. választás után a kép nem csillagos"
            zar(qt_app, menu)
            qt_app.processEvents()

        assert _csillagos(controller, sor), "a második választás megfordította a csillagot"
        assert _ini_csillag(controller, _KESOBBI)

    def test_starred_photos_a_mar_csillagos_kepet_nem_fordit_vegyes_kijelolesnel(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        elso, masodik = nevek[_KORAI], nevek[_KESOBBI]
        controller.toggleStarMany([elso])
        assert varj(qt_app, lambda: _csillagos(controller, elso))
        kijelol(window, qt_app, [elso, masodik])

        menu, _almenu = _foto_almenu(window, qt_app, elso)
        kattints(window, qt_app, keres_vizualis_mindenablakban(window, _STARRED))

        assert varj(qt_app, lambda: _csillagos(controller, masodik)), (
            "a csillagtalan kép nem kapott csillagot"
        )
        assert _csillagos(controller, elso), "a már csillagos képről levette a csillagot"
        zar(qt_app, menu)

    def test_screensaver_a_kijelolt_kepeket_a_kepernyovedohoz_adja(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        sorok = [nevek[_KORAI], nevek[_KESOBBI]]
        kijelol(window, qt_app, sorok)
        elotte = set(controller._screensaver_photo_paths())

        menu, _almenu = _foto_almenu(window, qt_app, sorok[0])
        kattints(window, qt_app, keres_vizualis_mindenablakban(window, _SCREENSAVER))

        varj(qt_app, lambda: len(controller._screensaver_photo_paths()) >= len(elotte) + 2)
        hozzaadott = {
            str(Path(ut))
            for ut in controller._screensaver_photo_paths()
        } - {str(Path(ut)) for ut in elotte}
        assert hozzaadott == {str(foto_utja(controller, sor)) for sor in sorok}
        zar(qt_app, menu)

    @pytest.mark.parametrize(
        ("sorrend", "vart_datum"),
        [
            ((_KORAI, _KESOBBI), "2025-04-30"),
            ((_KESOBBI, _KORAI), "2025-06-15"),
        ],
        ids=["korai-van-elol", "kesobbi-van-elol"],
    )
    def test_new_album_datuma_az_elso_kijelolt_kep_ideje_minusz_egy_masodperc(
        self, mappa_app, qt_app, sorrend, vart_datum
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        sorok = [nevek[nev] for nev in sorrend]
        kijelol(window, qt_app, sorok)

        menu, _almenu = _foto_almenu(window, qt_app, sorok[0])
        kattints(window, qt_app, keres_vizualis_mindenablakban(window, _NEW_ALBUM))

        parbeszed = gyerek(window, "toolbarNewAlbumPropertiesDialog")
        assert varj(qt_app, lambda: parbeszed.property("opened") is True), (
            "a New Album... nem nyitotta meg az Album Properties ablakot"
        )
        assert parbeszed.property("currentDate") == vart_datum
        mezo = gyerek(parbeszed, "folderPropertiesDateField")
        assert str(mezo.property("text")) != "", "a dátummező üres maradt"
        assert controller.albums == [], "az album az OK előtt jött létre"

        kattints(window, qt_app, gyerek(parbeszed, "folderPropertiesOkButton"))
        assert varj(qt_app, lambda: len(controller.albums) == 1)
        album = controller.albums[0]
        assert album["count"] == 2
        # #7076: az új album nyílik meg
        assert varj(qt_app, lambda: controller.currentAlbumToken == album["token"]), (
            "az OK után nem az új album nyílt meg (#7076)"
        )
        zar(qt_app, menu)

    def test_a_fajl_menu_new_album_ablaka_a_mai_datummal_nyilik_nem_az_elso_kepevel(
        self, mappa_app, qt_app
    ):
        """A Fájl menü útja (`0x005eb810`, más belépő) a létrehozás napját kapja
        (#7164), nem a kijelölés első képének idejét."""
        window, controller, _motor = mappa_app
        _betolt(window, qt_app, controller)
        kijelol(window, qt_app, [0, 1])
        elotte = date.today().isoformat()

        megnyit_fomenu(window, qt_app, "&File")
        tetel = fomenu_objektum(window, "menuFileNewAlbum")
        assert tetel is not None
        fomenu_kattints(qt_app, tetel)

        parbeszed = gyerek(window, "toolbarNewAlbumPropertiesDialog")
        assert varj(qt_app, lambda: parbeszed.property("opened") is True)
        assert parbeszed.property("currentDate") in {
            elotte, date.today().isoformat()
        }
        zar(qt_app, parbeszed)


# -- a néző helyi menüje -----------------------------------------------------


class TestNezoAlmenu:
    def test_album_nelkul_is_elerheto_es_ugyanazt_a_sorlistat_adja(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        _betolt(window, qt_app, controller)
        assert controller.albums == []

        menu, almenu = _nezo_almenu(window, qt_app, 0)

        assert almenu.property("enabled") is True, "album nélkül szürke az almenü"
        assert _tetelsor(almenu) == [_V_STARRED, _V_SCREENSAVER, _ELVALASZTO, _V_NEW_ALBUM]
        _felulet_sorrend_es_elvalaszto(window, (_V_STARRED, _V_SCREENSAVER, _V_NEW_ALBUM))
        _kiadasi_kep(
            window, keres_vizualis_mindenablakban(window, _V_STARRED),
            "picasapy-7100-nezo-almenu-album-nelkul.png")
        zar(qt_app, menu)

    def test_albumokkal_albumok_elvalaszto_starred_screensaver_elvalaszto_new_album(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        elso = controller.createAlbum("Elso", [nevek[_KORAI]])
        assert elso
        assert varj(qt_app, lambda: len(controller.albums) == 1)

        menu, almenu = _nezo_almenu(window, qt_app, 0)

        assert _tetelsor(almenu) == [
            f"viewerMenuAddToAlbumItem_{elso}", _ELVALASZTO,
            _V_STARRED, _V_SCREENSAVER, _ELVALASZTO, _V_NEW_ALBUM,
        ]
        _felulet_sorrend_es_elvalaszto(window, (_V_STARRED, _V_SCREENSAVER, _V_NEW_ALBUM))
        _kiadasi_kep(
            window, keres_vizualis_mindenablakban(window, _V_STARRED),
            "picasapy-7100-nezo-almenu-albumokkal.png")
        zar(qt_app, menu)

    def test_meglevo_albumsor_viselkedese_valtozatlan(self, mappa_app, qt_app):
        """Nem szabad: az albumsor továbbra is a nézett képet adja az albumhoz."""
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        token = controller.createAlbum("Masik", [nevek[_KESOBBI]])
        assert token
        assert varj(qt_app, lambda: album_darab(controller, token) == 1)

        menu, _almenu = _nezo_almenu(window, qt_app, nevek[_KORAI])
        kattints(
            window, qt_app,
            keres_vizualis_mindenablakban(window, f"viewerMenuAddToAlbumItem_{token}"))

        assert varj(qt_app, lambda: album_darab(controller, token) == 2)
        zar(qt_app, menu)

    def test_starred_photos_ketszer_valasztva_is_csillagos_marad(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        sor = nevek[_KESOBBI]
        assert not _csillagos(controller, sor)

        for kor in (1, 2):
            menu, _almenu = _nezo_almenu(window, qt_app, sor)
            kattints(window, qt_app, keres_vizualis_mindenablakban(window, _V_STARRED))
            assert varj(
                qt_app, lambda: _csillagos(controller, sor) and _ini_csillag(
                    controller, _KESOBBI)
            ), f"a {kor}. választás után a kép nem csillagos"
            zar(qt_app, menu)
            qt_app.processEvents()

        assert _csillagos(controller, sor), "a második választás megfordította a csillagot"

    def test_screensaver_a_nezett_kepet_a_kepernyovedohoz_adja(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)
        sor = nevek[_KESOBBI]
        elotte = {str(Path(ut)) for ut in controller._screensaver_photo_paths()}

        menu, _almenu = _nezo_almenu(window, qt_app, sor)
        kattints(window, qt_app, keres_vizualis_mindenablakban(window, _V_SCREENSAVER))

        varj(qt_app, lambda: len(controller._screensaver_photo_paths()) > len(elotte))
        utana = {str(Path(ut)) for ut in controller._screensaver_photo_paths()}
        assert utana - elotte == {str(foto_utja(controller, sor))}
        zar(qt_app, menu)

    @pytest.mark.parametrize(
        ("nev", "vart_datum"), [(_KORAI, "2025-04-30"), (_KESOBBI, "2025-06-15")]
    )
    def test_new_album_a_nezett_kepbol_nyit_es_a_datum_a_kep_ideje_minusz_egy_masodperc(
        self, mappa_app, qt_app, nev, vart_datum
    ):
        window, controller, _motor = mappa_app
        nevek = _betolt(window, qt_app, controller)

        menu, _almenu = _nezo_almenu(window, qt_app, nevek[nev])
        kattints(window, qt_app, keres_vizualis_mindenablakban(window, _V_NEW_ALBUM))

        parbeszed = gyerek(window, "toolbarNewAlbumPropertiesDialog")
        assert varj(qt_app, lambda: parbeszed.property("opened") is True), (
            "a néző New Album... sora nem nyitotta meg az Album Properties ablakot"
        )
        assert parbeszed.property("currentDate") == vart_datum
        assert controller.albums == [], "az album az OK előtt jött létre"

        kattints(window, qt_app, gyerek(parbeszed, "folderPropertiesOkButton"))
        assert varj(qt_app, lambda: len(controller.albums) == 1)
        album = controller.albums[0]
        assert album["count"] == 1, "az új albumnak a nézett képet kell tartalmaznia"
        zar(qt_app, menu)

