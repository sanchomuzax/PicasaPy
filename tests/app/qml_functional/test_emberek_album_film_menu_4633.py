"""#4633: a Film menü az összes nem üres Emberek-albumot használja."""

# rontás-kontroll: menuCreateMovieFromPeopleAlbums hiánya → 1 failed

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QUrl, Qt
from PySide6.QtTest import QTest

from picasapy.ini import parse_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg


_ANNA = "1111111111111111"
_ZOE = "2222222222222222"
_RECT = "1e00280045006e00"


def _emberek_album_kepei(lib: Path) -> None:
    for name in ("anna.jpg", "zoe-a.jpg", "zoe-b.jpg"):
        make_jpeg(lib / name, size=(640, 400))
    ini = (
        "[Contacts2]\n"
        f"{_ANNA}=Anna;;\n"
        f"{_ZOE}=Zoe Zed;;\n"
        "[anna.jpg]\n"
        f"faces=rect64({_RECT}),{_ANNA}\n"
        "[zoe-a.jpg]\n"
        f"faces=rect64({_RECT}),{_ZOE}\n"
        "[zoe-b.jpg]\n"
        f"faces=rect64({_RECT}),{_ZOE}\n"
    )
    update_document(
        lib / ".picasa.ini", lambda _old: parse_document(ini), backup=False
    )


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _variant(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _popup_kattintas(elem, qt_app) -> None:
    assert elem.isVisible() and elem.isEnabled(), (
        f"{elem.objectName()} nem látható vagy le van tiltva"
    )
    ablak = elem.window()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(ablak, kozep, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep
    )
    qt_app.processEvents()


def test_film_menu_nyitott_szemelyalbum_es_kijeloles_nelkul_minden_albumot_atad(
    qt_app, tmp_path
):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_emberek_album_kepei)
    ablak, vezerlo, _motor = next(gen)
    film = None
    try:
        assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3), (
            "a próbaképek nem kerültek a fő rácsba"
        )
        assert vezerlo.currentPersonName == "", "a próba személyalbum nézetben indult"
        vezerlo.setPeopleSort("count")
        assert [person["name"] for person in vezerlo.people] == ["Zoe Zed", "Anna"]

        forrasok = vezerlo.personMovieSourceUrls()
        vart_fajlnevek = ["anna.jpg", "zoe-a.jpg", "zoe-b.jpg"]
        assert [Path(QUrl(str(url)).toLocalFile()).name for url in forrasok] == (
            vart_fajlnevek
        ), "a forráslista nem a tárolt személyalbum-sorrendet követi"

        ablak.setProperty("selectedIndexes", [])
        ablak.setProperty("selectedIndex", -1)
        eredeti_magassag = ablak.height()
        for eltolás in (-5, 0, 5):
            ablak.setHeight(eredeti_magassag + eltolás)
            assert _varj(
                qt_app,
                lambda eltolás=eltolás: ablak.height()
                == eredeti_magassag + eltolás,
            ), f"a főablak magassága nem állt be ({eltolás:+} px)"

            create_menu = ablak.findChild(QObject, "menuCreateRoot")
            assert create_menu is not None, "a Létrehozás menü nem található"
            create_menu.open()
            assert _varj(
                qt_app, lambda m=create_menu: m.property("visible")
            ), "a Létrehozás menü nem nyílt meg"

            movie_menu = ablak.findChild(QObject, "menuCreateMovieMenu")
            assert movie_menu is not None, "a Film almenü nem található"
            movie_menu.open()
            people_movie = ablak.findChild(
                QObject, "menuCreateMovieFromPeopleAlbums"
            )
            assert people_movie is not None, (
                "hiányzik a Film ▸ From People Albums... menüpont"
            )
            assert _varj(
                qt_app, lambda m=people_movie: m.property("visible")
            ), "az Emberek-albumok film-menüpontja nem jelent meg"
            assert people_movie.property("text") == "From People Albums..."
            _popup_kattintas(people_movie, qt_app)

            if film is None:
                assert _varj(
                    qt_app,
                    lambda: ablak.findChild(QObject, "movieDialog") is not None,
                ), "a menüpont nem építette fel a Filmkészítőt"
                film = ablak.findChild(QObject, "movieDialog")
            assert _varj(qt_app, lambda f=film: f.property("visible")), (
                "a menüpont nem nyitotta meg a Filmkészítőt"
            )
            sources = _variant(film.property("movieClipSources"))
            assert [
                Path(QUrl(str(url)).toLocalFile()).name for url in sources
            ] == vart_fajlnevek, (
                f"nem minden Emberek-album képei jutottak a filmhez: {sources!r}"
            )
            assert _variant(film.property("movieClipIndexes")) == [], (
                "a film a kijelölésből, nem az Emberek-albumokból indult"
            )
            assert film.property("personMovieMode") is True
            film.close()
            assert _varj(qt_app, lambda f=film: not f.property("visible")), (
                "a Filmkészítő nem zárult be a következő magasságpróbához"
            )
    finally:
        if film is not None:
            film.close()
            qt_app.processEvents()
        try:
            gen.close()
        except RuntimeError:
            pass
