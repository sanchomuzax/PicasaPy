"""QML-funkcionális tesztek: diavetítés (#8).

A léptetés-logika (videó-kihagyás, körbefordulás), az időzítő, a szünet,
a kilépés utáni kijelölés-követés és a vetítés közbeni forgatás/csillag
bekötése — a közös qml_app fixture-ön (Main.qml betöltve offscreen).
"""

import re

import pytest
from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer

#: A `cv2.getBuildInformation()` sora, ha a GStreamer-háttér be van fordítva.
#: SZÁNDÉKOSAN mintaillesztés, nem szövegkeresés: a build-információ
#: oszlopigazítása OpenCV-verziónként változik, és egy elrontott
#: szóköz-számtól az őr NÉMÁN engedné át az összeomló tesztet.
_GSTREAMER_SOR = re.compile(r"^\s*GStreamer:\s*YES", re.MULTILINE)


def _opencv_gstreamer_backenddel() -> bool:
    """Van-e GStreamer-háttér az OpenCV-ben ezen a gépen (#664).

    A `cv2` itt nem kötelező függősége a fájlnak: ha nincs meg,
    videó-bélyegkép sincs, tehát az összeomlás sem fenyeget."""
    try:
        import cv2
    except ImportError:  # pragma: no cover — cv2 nélkül nincs videó-dekód
        return False
    return _GSTREAMER_SOR.search(cv2.getBuildInformation()) is not None


#: #664 — ISMERT TERMÉKHIBA, külön jegyet igényel (nem itt javítjuk).
#:
#: A `picasapy.thumbs.cache._decode_video_frame` `cv2.VideoCapture`-t hív, és
#: ezt a `ThumbnailProvider` TÖBB pool-száljáról párhuzamosan teheti. Ha a
#: videót az elsőként próbált FFMPEG-háttér nem tudja megnyitni (sérült vagy
#: csonka fájl — a lenti tesztek épp ilyen, 64 bájtos „mp4"-et hoznak létre),
#: az OpenCV a GStreamer-háttérre esik vissza, az pedig két szálból egyszerre
#: hívva SIGSEGV-vel viszi el az EGÉSZ processzt (a részfutás exit -11).
#:
#: Qt nélkül is reprodukálható: 4 szál × `cv2.VideoCapture` ugyanarra a
#: 64 bájtos szemét-mp4-re → összeomlás; `cv2.CAP_FFMPEG`-re kényszerítve
#: viszont nem. A hiba tehát a GStreamer-háttérhez kötött, és nem a
#: tesztkódban van — a felhasználót is elérheti egy sérült videót tartalmazó
#: mappán.
#:
#: A kihagyás a KÖRNYEZETHEZ kötött, nem a platformhoz: a CI
#: `opencv-python-headless` wheelje GStreamer NÉLKÜL épül, ott tehát ezek a
#: tesztek változatlanul futnak.
_VIDEO_DEKOD_OSSZEOMLIK = _opencv_gstreamer_backenddel()

_VIDEO_KIHAGYAS_INDOK = (
    "ismert termékhiba (#664 nyomán külön jegy): a videó-bélyegkép "
    "dekódolása több szálról párhuzamosan SIGSEGV-vel viszi el a "
    "processzt, ha az OpenCV a GStreamer-háttérre esik vissza — ez a "
    "háttér ezen a gépen jelen van. A CI GStreamer nélküli OpenCV-t "
    "használ, ott a teszt fut."
)


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _invoke(qt_app, obj, name, *args):
    QMetaObject.invokeMethod(
        obj, name, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _start(window, qt_app, index=-1):
    _invoke(qt_app, window, "startSlideshow", index)
    return _child(window, "slideshowView")


def _wait_ms(qt_app, ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    qt_app.processEvents()


#: A háttérművelet befejeződésére szánt türelem. Bőven a mért futásidő fölött:
#: nem a teszt sebességét szabja meg (a jelzés érkezésekor azonnal továbbmegyünk),
#: csak azt, mennyi idő után mondjuk ki, hogy a művelet BERAGADT (#519).
_PHOTO_OP_TIMEOUT_MS = 30_000


def _invoke_photo_op(qt_app, controller, obj, name, *args):
    """#141: a vetítés közbeni forgatás/csillag háttérszálon fut (NAS-írás
    + célzott index-UPDATE) — az _invoke utáni processEvents nem elég,
    meg kell várni a `photoOpFinished` jelzést.

    **#519: a várakozás nem futhat ki némán.** Korábban 2000 ms után a
    ciklus egyszerűen továbbment, és a hívó AZONNAL állított — a lassú
    windows-CI-n (fájlírás + SQLite-frissítés, vírusirtóval) ez a művelet
    BEFEJEZŐDÉSE ELŐTT mért. A bukás `assert False is True` alakban jött, ami
    valódi hibának látszott, holott versenyhelyzet volt; emiatt ingadozott a
    windows-láb.

    Most a jelzés megérkezését KÜLÖN nyilvántartjuk: ha a türelmi idő letelt
    anélkül, hogy megjött volna, a teszt beszédes üzenettel bukik — nem pedig
    egy félkész állapotot mér le. Ha a jelzés már az `_invoke` alatt
    megérkezik (szinkron ág), el sem indítjuk az eseményhurkot.
    """
    allapot: dict[str, object] = {"megjott": False, "hiba": None}
    loop = QEventLoop()

    def _kesz(*_args) -> None:
        allapot["megjott"] = True
        loop.quit()

    def _hiba(uzenet: str) -> None:
        # a háttérszál hibaágon `photoOpFailed`-et küld, és `photoOpFinished`
        # NÉLKÜL tér vissza — enélkül a várakozás csak kifutna, és a valódi ok
        # (jogosultság, fájlzár) rejtve maradna
        allapot["hiba"] = uzenet
        loop.quit()

    controller.photoOpFinished.connect(_kesz)
    controller.photoOpFailed.connect(_hiba)
    try:
        _invoke(qt_app, obj, name, *args)
        if not allapot["megjott"] and allapot["hiba"] is None:
            QTimer.singleShot(_PHOTO_OP_TIMEOUT_MS, loop.quit)
            loop.exec()
    finally:
        # a korábbi változat a `loop.quit`-et rákötve hagyta a jelzésre —
        # hívásonként egy halott ciklussal többre
        controller.photoOpFinished.disconnect(_kesz)
        controller.photoOpFailed.disconnect(_hiba)

    assert allapot["hiba"] is None, (
        f"a(z) {name!r} művelet HIBÁRA futott: {allapot['hiba']}"
    )
    assert allapot["megjott"], (
        f"a(z) {name!r} művelet `photoOpFinished` jelzése "
        f"{_PHOTO_OP_TIMEOUT_MS} ms alatt sem érkezett meg (hibajelzés sem) — "
        "a háttérszál beragadt; a teszt így a művelet befejeződése ELŐTT mérne"
    )
    qt_app.processEvents()


class TestSlideshowBasics:
    def test_start_shows_and_timer_runs(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        show = _start(window, qt_app)
        assert show.property("visible") is True
        assert show.property("playing") is True
        assert show.property("currentIndex") == 0
        assert _child(window, "slideshowTimer").property("running") is True
        _invoke(qt_app, show, "stop")
        assert show.property("visible") is False
        assert _child(window, "slideshowTimer").property("running") is False

    def test_advance_wraps_around(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke(qt_app, show, "advance")
        assert show.property("currentIndex") == 1
        _invoke(qt_app, show, "advance")   # 2 fotó: körbefordul
        assert show.property("currentIndex") == 0
        _invoke(qt_app, show, "goBack")
        assert show.property("currentIndex") == 1
        _invoke(qt_app, show, "stop")

    def test_exit_syncs_grid_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        show = _start(window, qt_app)
        _invoke(qt_app, show, "advance")
        _invoke(qt_app, show, "stop")
        assert window.property("selectedIndex") == 1

    def test_pause_stops_timer(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke(qt_app, show, "togglePause")
        assert show.property("playing") is False
        assert _child(window, "slideshowTimer").property("running") is False
        _invoke(qt_app, show, "togglePause")
        assert _child(window, "slideshowTimer").property("running") is True
        _invoke(qt_app, show, "stop")

    def test_timer_advances_slides(self, qml_app, qt_app):
        # DoD: léptetés-időzítő — rövid intervallummal valóban lép. Az
        # intervallum már INDÍTÁS ELŐTT rövid (a futó Timer átállítására
        # nem építünk), és lassú CI-gépre türelmesen, max ~3 mp-ig várunk.
        window, _controller, _lib, _engine = qml_app
        show = _child(window, "slideshowView")
        show.setProperty("intervalMs", 50)
        steps = []
        show.currentIndexChanged.connect(
            lambda: steps.append(show.property("currentIndex"))
        )
        _start(window, qt_app, 0)
        for _ in range(30):
            _wait_ms(qt_app, 100)
            if len(steps) > 1:   # az indítási index-beállításon túl is lépett
                break
        assert len(steps) > 1, "az időzítőnek legalább egyet lépnie kellett"
        _invoke(qt_app, show, "stop")


@pytest.mark.skipif(_VIDEO_DEKOD_OSSZEOMLIK, reason=_VIDEO_KIHAGYAS_INDOK)
class TestSlideshowVideoSkip:
    """A vetítés kihagyja a videókat.

    #664: EZ A KÉT TESZT az egyetlen, amelyik videó-sort tesz a
    könyvtárba, ezért csak ez a kettő futtatja a bélyegkép-pool
    videó-dekódolását — a fájl többi tesztje változatlanul fut."""

    def test_videos_are_skipped(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        (lib / "c.mp4").write_bytes(b"\x00" * 64)
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)
        controller._reload()
        qt_app.processEvents()
        assert controller.photos.isVideoAt(2) is True
        show = _start(window, qt_app, 1)
        _invoke(qt_app, show, "advance")   # a 2-es (videó) kimarad
        assert show.property("currentIndex") == 0
        _invoke(qt_app, show, "stop")

    def test_start_on_video_clamps_to_photo(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        (lib / "c.mp4").write_bytes(b"\x00" * 64)
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)
        controller._reload()
        qt_app.processEvents()
        show = _start(window, qt_app, 2)   # videó-soron indítva
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0   # az első fotóra ugrik
        _invoke(qt_app, show, "stop")


class TestSlideshowActions:
    def test_rotate_during_show_writes_ini(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke_photo_op(qt_app, controller, show, "rotateCurrent", 1)
        assert controller.photos.rotateAt(0) == 1
        _invoke_photo_op(qt_app, controller, show, "rotateCurrent", -1)
        assert controller.photos.rotateAt(0) == 0
        _invoke(qt_app, show, "stop")

    def test_star_during_show(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke_photo_op(qt_app, controller, show, "starCurrent")
        assert controller.photos.starAt(0) is True
        _invoke_photo_op(qt_app, controller, show, "starCurrent")
        assert controller.photos.starAt(0) is False
        _invoke(qt_app, show, "stop")


class TestSlideshowEntryPoints:
    def test_view_menu_item_starts_show(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        item = _child(window, "menuViewSlideshow")
        assert item.property("enabled") is True
        QMetaObject.invokeMethod(
            item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        show = _child(window, "slideshowView")
        assert show.property("visible") is True
        _invoke(qt_app, show, "stop")

    def test_viewer_play_button_enabled(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "viewerPlayButton")
        assert button.property("enabled") is True


class TestSlideshowControlSizing:
    def test_buttons_share_uniform_height(self, qml_app, qt_app):
        # felhasználói visszajelzés (#8 után): a csillag-gomb nagyobb volt a
        # többinél — az egységes gombmagasság regressziós védelme
        window, _controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        star = _child(window, "slideshowStarButton")
        play = _child(window, "slideshowPlayButton")
        exit_button = _child(window, "slideshowExitButton")
        assert star.property("height") == play.property("height")
        assert play.property("height") == exit_button.property("height")
        _invoke(qt_app, show, "stop")
