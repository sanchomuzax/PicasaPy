"""QML-funkcionális tesztek: diavetítés (#8).

A léptetés-logika (videó-kihagyás, körbefordulás), az időzítő, a szünet,
a kilépés utáni kijelölés-követés és a vetítés közbeni forgatás/csillag
bekötése — a közös qml_app fixture-ön (Main.qml betöltve offscreen).
"""


import threading
from pathlib import Path

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer

from support.qt_wait import varj_feltetelre, wait_for_photo_op

#: #673: a videó-dekódolás mostantól a `cv2.CAP_FFMPEG` hátteret KÉNYSZERÍTI,
#: ezért az OpenCV nem eshet vissza a GStreamerre — az a visszaesés vitte el
#: SIGSEGV-vel az egész processzt, ha két szál egyszerre nyitott meg egy
#: sérült videót (#664 tárta fel, #673 javította). A korábbi, GStreamer-
#: háttérhez kötött kihagyás ezzel tárgytalan: az alábbi osztály minden
#: gépen fut.


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


def _start_szunetelve(window, qt_app, index=-1):
    """Diavetítés indítása, a léptető időzítő szüneteltetésével (#3830).

    A `stepTimer` alapból 3 mp után a következő képre lép. A fotóművelet
    befejeződésére váró eseményhurok ezt is lefuttatja, így a lassú
    windowsos futón a második művelet már a MÁSIK képet érte (mérve:
    `rotateAt(0)` 1 maradt, `rotateAt(1)` 3 lett). A művelet-tesztek a
    műveletet mérik, nem a léptetést — ezért szüneteltetünk.
    """
    show = _start(window, qt_app, index)
    show.setProperty("playing", False)
    qt_app.processEvents()
    return show


def _wait_ms(qt_app, ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    qt_app.processEvents()


def _invoke_photo_op(qt_app, controller, obj, name, *args):
    """A vetítés közbeni fotóművelet végéig vár, és külön gyűjti a hibát."""
    hibak: list[str] = []

    def hiba_erkezett(message: str) -> None:
        hibak.append(message)

    controller.photoOpFailed.connect(hiba_erkezett)
    try:
        wait_for_photo_op(
            controller,
            lambda: _invoke(qt_app, obj, name, *args),
            qt_app=qt_app,
        )
    finally:
        controller.photoOpFailed.disconnect(hiba_erkezett)
    assert not hibak, f"a(z) {name!r} művelet HIBÁRA futott: {hibak}"


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
        window, controller, _lib, _engine = qml_app
        controller.setSlideshowLoop(True)   # az ismétlés alapból ki (#4377)
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
        controller.setSlideshowLoop(True)   # az ismétlés alapból ki (#4377)
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
        controller.setSlideshowLoop(True)   # az ismétlés alapból ki (#4377)
        show = _start(window, qt_app, 2)   # videó-soron indítva
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0   # az első fotóra ugrik
        _invoke(qt_app, show, "stop")


class TestSlideshowActions:
    def test_rotate_during_show_writes_ini(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start_szunetelve(window, qt_app, 0)
        _invoke_photo_op(qt_app, controller, show, "rotateCurrent", 1)
        assert controller.photos.rotateAt(0) == 1
        _invoke_photo_op(qt_app, controller, show, "rotateCurrent", -1)
        assert controller.photos.rotateAt(0) == 0
        _invoke(qt_app, show, "stop")

    def test_star_during_show(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start_szunetelve(window, qt_app, 0)
        _invoke_photo_op(qt_app, controller, show, "starCurrent")
        assert controller.photos.starAt(0) is True
        _invoke_photo_op(qt_app, controller, show, "starCurrent")
        assert controller.photos.starAt(0) is False
        _invoke(qt_app, show, "stop")

    def test_ket_gyors_forgatas_egyik_sem_veszik_el(
        self, qml_app, qt_app, monkeypatch
    ):
        """#3830: a forgatás-gomb GYORS, egymást követő kattintása.

        A `.picasa.ini`-írás háttérszálon fut (`_run_photo_write`, #141), a
        modell csak a befejezéskor frissül. A második kattintás, ami az első
        írás befejezése ELŐTT érkezik, korábban a RÉGI lépésszámból
        számolt, és elveszett. A gomb SAJÁT `clicked` jelzésén át kattint (a
        `test_csillag_belepesi_pontok_1438.py` mintája — egy elrontott kötés
        csak így vált pirosra); az ini-írást egy `threading.Event` tartja
        fel, így a második kattintás GARANTÁLTAN a futó írás alatt érkezik,
        nem egy időzítéstől függő ablakban."""
        from picasapy.app import photo_ops_controller as ops

        window, controller, _lib, _engine = qml_app
        show = _start_szunetelve(window, qt_app, 0)
        assert show.property("currentIndex") == 0
        assert controller.photos.rotateAt(0) == 0

        eredeti_update_document = ops.update_document
        engedd_tovabb = threading.Event()

        def feltartott(*args, **kwargs):
            engedd_tovabb.wait(30.0)
            return eredeti_update_document(*args, **kwargs)

        monkeypatch.setattr(ops, "update_document", feltartott)
        gomb = _child(window, "slideshowRotateRightButton")
        try:
            # 1. kattintás: 0 -> 1, ELAKAD az ini-írásban; a 2. kattintáskor
            # a modell MÉG 0-t mutat
            for _ in range(2):
                QMetaObject.invokeMethod(
                    gomb, "clicked", Qt.ConnectionType.DirectConnection
                )
                qt_app.processEvents()
        finally:
            engedd_tovabb.set()

        assert varj_feltetelre(
            qt_app, lambda: controller.photos.rotateAt(0) == 2, 15.0
        ), (
            "két gyors '+1' forgatás után a lépésszámnak 2-nek kell "
            "lennie — ha 1, a második kattintás elveszett (#3830)"
        )
        ini = Path(controller.photos.photos[0].folder_path) / ".picasa.ini"
        assert "rotate(2)" in ini.read_text(encoding="utf-8").split("[a.jpg]")[1]
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


def _negy_kep(controller, lib, qt_app):
    """A fixture két képe (a, b) mellé c és d — négy kép, hogy a „következő"
    és az „előző" kép különbözzön (két képnél a kettő egybeesik)."""
    from picasapy.index import open_index, sync_tree
    from support.jpeg_factory import make_jpeg

    make_jpeg(lib / "c.jpg", size=(100, 100))
    make_jpeg(lib / "d.jpg", size=(100, 100))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, lib)
    controller._reload()
    qt_app.processEvents()
    nevek = [
        controller.photos.filePathAt(i).rsplit("/", 1)[-1]
        for i in range(controller.photos.rowCount())
    ]
    assert nevek == ["a.jpg", "b.jpg", "c.jpg", "d.jpg"]


def _torol(controller, qt_app, nev):
    for sor in range(controller.photos.rowCount()):
        ut = controller.photos.filePathAt(sor)
        if ut.endswith("/" + nev):
            assert controller.photos.remove_by_path(ut) is True
            qt_app.processEvents()
            return
    raise AssertionError(f"{nev} nincs a modellben")


def _lathato(window):
    return _child(window, "slideshowImage").property("source").toString()


def _nincs_atmenet(window):
    """Az átmenet NEM indult: az animáció áll, a kimenő másolat rejtve."""
    assert _child(window, "slideshowTransition").property("running") is False
    assert _child(window, "slideshowPrevImage").property("opacity") == 0


class TestSlideshowModelFollows:
    """#3881: a látott kép a modell törlésére/átrendezésére reagál — nem
    ragad a törölt vagy elmozdult sor eredeti indexén."""

    def test_torolt_lathato_kep_utan_tovabblep(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 1)   # b.jpg
        _torol(controller, qt_app, "b.jpg")
        assert show.property("visible") is True
        assert show.property("currentIndex") == 1
        assert "c.jpg" in _lathato(window)
        _invoke(qt_app, show, "stop")

    def test_korabbi_sor_torlesekor_a_kep_marad_atmenet_nelkul(
        self, qml_app, qt_app
    ):
        # a leggyakoribb eset: egy MÁSIK, korábbi kép törlődik — az index
        # eggyel csökken, a látott kép marad, és nem indul áttűnés
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 2)   # c.jpg
        _nincs_atmenet(window)
        _torol(controller, qt_app, "a.jpg")
        assert show.property("currentIndex") == 1
        assert "c.jpg" in _lathato(window)
        _nincs_atmenet(window)
        _invoke(qt_app, show, "stop")

    def test_ujrainditas_ugyanarra_az_indexre_a_latott_kepet_koveti(
        self, qml_app, qt_app
    ):
        # a PR #3887 átnézésében próbával igazolt sorozat: a `start()`
        # ugyanarra a számra indít, tehát az `onCurrentIndexChanged` nem fut
        # le — a követett útvonal nem maradhat a REJTVE törölt sor előtti
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 1)   # b.jpg
        _invoke(qt_app, show, "stop")
        _torol(controller, qt_app, "a.jpg")           # rejtve: b, c, d
        show = _start_szunetelve(window, qt_app, 1)   # c.jpg
        assert "c.jpg" in _lathato(window)
        _torol(controller, qt_app, "d.jpg")           # független kép
        assert show.property("currentIndex") == 1
        assert "c.jpg" in _lathato(window)
        _invoke(qt_app, show, "stop")

    def test_ujrainditas_utan_az_atrendezes_is_a_latott_kepet_koveti(
        self, qml_app, qt_app
    ):
        # ugyanaz a sorozat, de a végén teljes reset (átrendezés): ott a
        # követett útvonal dönt, tehát az elavult útvonal a RÉGI képre ugrana
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 1)   # b.jpg
        _invoke(qt_app, show, "stop")
        _torol(controller, qt_app, "a.jpg")           # rejtve: b, c, d
        show = _start_szunetelve(window, qt_app, 1)   # c.jpg
        b, c, d = controller.photos.photos
        controller.photos.set_photos((d, b, c))
        qt_app.processEvents()
        assert show.property("currentIndex") == 2
        assert "c.jpg" in _lathato(window)
        _invoke(qt_app, show, "stop")

    def test_utolso_sor_torlesekor_korbe_az_elso_kepre_lep(
        self, qml_app, qt_app
    ):
        # ahogy az `advance()`: a lista végén a KÖVETKEZŐ kép a 0. sor
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 3)   # d.jpg
        _torol(controller, qt_app, "d.jpg")
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0
        assert "a.jpg" in _lathato(window)
        _invoke(qt_app, show, "stop")

    def test_utolso_lathato_kep_torlese_leallitja_a_vetitest(
        self, qml_app, qt_app
    ):
        window, controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 1)   # b.jpg (2 fotó: a, b)
        assert show.property("currentIndex") == 1
        b_path = controller.photos.filePathAt(1)
        assert controller.photos.remove_by_path(b_path) is True
        qt_app.processEvents()
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0   # a.jpg-re lép
        window.setProperty("selectedIndex", -1)
        window.setProperty("selectedIndexes", [])
        a_path = controller.photos.filePathAt(0)
        assert controller.photos.remove_by_path(a_path) is True
        qt_app.processEvents()
        assert show.property("visible") is False
        assert show.property("playing") is False
        # üres listán nincs látott kép: a kilépés nem jelöl ki nem létező sort
        assert show.property("currentIndex") == -1
        assert window.property("selectedIndex") == -1

    def test_atrendezeskor_ugyanaz_a_fajl_marad_lathato(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start_szunetelve(window, qt_app, 0)   # a.jpg
        assert show.property("currentIndex") == 0
        atrendezve = tuple(reversed(controller.photos.photos))   # b, a
        controller.photos.set_photos(atrendezve)
        qt_app.processEvents()
        assert show.property("currentIndex") == 1
        assert "a.jpg" in _lathato(window)
        _nincs_atmenet(window)
        _invoke(qt_app, show, "stop")

    def test_reset_utan_helyben_maradt_kepnel_friss_az_elobetolto(
        self, qml_app, qt_app
    ):
        # a látott kép a helyén marad, de a következő más lett — az
        # elő-betöltő a FRISS következőt tartsa
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 0)   # a.jpg, utána b
        elotolto = _child(window, "slideshowPreloadImage")
        assert "b.jpg" in elotolto.property("source").toString()
        a, b, c, d = controller.photos.photos
        controller.photos.set_photos((a, c, b, d))
        qt_app.processEvents()
        assert show.property("currentIndex") == 0
        assert "c.jpg" in elotolto.property("source").toString()
        _invoke(qt_app, show, "stop")

    def test_reset_utan_eltunt_utolso_kepnel_korbe_lep(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        _negy_kep(controller, lib, qt_app)
        show = _start_szunetelve(window, qt_app, 3)   # d.jpg
        a, b, c, _d = controller.photos.photos
        controller.photos.set_photos((a, b, c))
        qt_app.processEvents()
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0
        assert "a.jpg" in _lathato(window)
        _invoke(qt_app, show, "stop")


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
