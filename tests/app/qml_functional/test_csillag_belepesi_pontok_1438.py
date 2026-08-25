"""#1438: a csillagozás felületi belépési pontjai — VALÓDI kattintással.

A csillag Python-oldali útját a `tests/app/test_csillag_lanc_1438.py` méri.
Ez a fájl a KÖTÉST őrzi: hogy a felületen létező csillag-vezérlők tényleg a
helyes vezérlőparancshoz és a helyes SORHOZ vezetnek. A gombokat a saját
`clicked` jelzésükön át indítjuk — nem a Python-metódust hívjuk —, mert egy
elrontott kötés (rossz sorindex, rossz slot, letiltott gomb) csak így tud
pirosra váltani.

**Két belépési pont van, nem három.** A #1438 jegye „billentyű, helyi menü,
tálca" hármast feltételezett; a felmérés szerint a mai felületen a csillag
KÉT helyről érhető el:

1. a **tálca** csillag-gombja (egyes kijelölésnél `toggleStar`, többesnél
   `toggleStarMany`) — a fotónézőben is ez a gomb a csillagozás helye,
   mert a tálca a néző alatt is látszik,
2. a **diavetítés** csillag-gombja.

Sem gyorsbillentyű, sem helyi menüpont nem köt a csillagozásra (a Szerkesztés
menü „Csillagozottak kijelölése" tétele KIJELÖL, nem csillagoz). Az utolsó
teszt ezt a leltárt mondja ki, hogy ha egy jövőbeli kör harmadik belépési
pontot ad hozzá, ez a fájl emlékeztessen: oda is őr kell.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.index import open_index
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.qt_wait import wait_for_photo_op

#: A projekt QML-forrásai — a belépési pontok leltárához olvassuk őket.
_QML_DIR = (
    Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"
)


def _child(root, name: str) -> QObject:
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _tray_star_button(window) -> QObject:
    """A tálca csillag-gombja.

    A gombnak magának nincs `objectName`-je, a felirata (`trayStarLabel`) a
    `contentItem`-je, tehát a QObject-szülője maga a gomb. A `targetRow`
    tulajdonság ellenőrzése a szerkezeti kapocs: ha a felépítés megváltozik,
    ez a sor mondja meg, miért nem találjuk a gombot.
    """
    button = _child(window, "trayStarLabel").parent()
    assert button is not None and button.property("targetRow") is not None, (
        "a trayStarLabel szülője már nem a csillag-gomb — a keresést "
        "igazítani kell"
    )
    return button


def _click(obj) -> None:
    """Kattintás megfelelője: a vezérlő saját `clicked` jelzése."""
    QMetaObject.invokeMethod(obj, "clicked", Qt.ConnectionType.DirectConnection)


def _select(window, qt_app, index: int, modifiers: int = 0) -> None:
    QMetaObject.invokeMethod(
        window,
        "handleThumbClick",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
        Q_ARG("QVariant", modifiers),
    )
    qt_app.processEvents()


def _folder(controller) -> Path:
    return Path(controller.photos.photos[0].folder_path)


def _ini_text(controller) -> str:
    ini = _folder(controller) / ".picasa.ini"
    return ini.read_text(encoding="utf-8") if ini.exists() else ""


def _index_star(controller, name: str) -> int:
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT star FROM photos WHERE name = ?", (name,)
        ).fetchone()
    assert row is not None, f"{name} nincs az indexben"
    return int(row[0])


def _starred_names(controller) -> list[str]:
    controller.showStarred()
    return [photo.name for photo in controller.photos.photos]


class TestATalcaCsillagGombja:
    def test_egyes_kijeloles_csillagot_ir_es_a_nezetben_latszik(
        self, qml_app, qt_app
    ) -> None:
        window, controller, _engine = qml_app
        _select(window, qt_app, 0)
        button = _tray_star_button(window)
        assert button.property("enabled") is True
        assert button.property("targetRow") == 0
        assert button.property("multi") is False

        wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)

        assert "star=yes" in _ini_text(controller).split("[a.jpg]")[1]
        assert _index_star(controller, "a.jpg") == 1
        assert _starred_names(controller) == ["a.jpg"]

    def test_a_gomb_a_KIJELOLT_sort_csillagozza(self, qml_app, qt_app) -> None:
        """A rossz sorindex a legvalószínűbb kötési hiba — ezt mondjuk ki."""
        window, controller, _engine = qml_app
        _select(window, qt_app, 1)
        button = _tray_star_button(window)
        assert button.property("targetRow") == 1

        wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)

        assert _index_star(controller, "b.jpg") == 1
        assert _index_star(controller, "a.jpg") == 0
        assert _starred_names(controller) == ["b.jpg"]

    def test_tobbes_kijeloles_mindet_csillagozza(self, qml_app, qt_app) -> None:
        window, controller, _engine = qml_app
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        _select(window, qt_app, 0)
        _select(window, qt_app, 1, ctrl)
        button = _tray_star_button(window)
        assert button.property("multi") is True, (
            "két kijelölt képnél a gombnak a kötegelt útra kell váltania"
        )

        # a kötegelt út (`toggleStarMany`) szinkron, nincs mire várni
        _click(button)
        qt_app.processEvents()

        assert _index_star(controller, "a.jpg") == 1
        assert _index_star(controller, "b.jpg") == 1
        assert _starred_names(controller) == ["a.jpg", "b.jpg"]

    def test_kijeloles_nelkul_a_gomb_tiltott(self, qml_app, qt_app) -> None:
        """Enélkül a gomb a -1 sorra tüzelne: néma, jelzés nélküli no-op."""
        window, _controller, _engine = qml_app
        QMetaObject.invokeMethod(
            window, "clearSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        button = _tray_star_button(window)
        assert button.property("enabled") is False


class TestADiavetitesCsillagGombja:
    def test_a_vetitett_kepet_csillagozza(self, qml_app, qt_app) -> None:
        window, controller, _engine = qml_app
        QMetaObject.invokeMethod(
            window,
            "startSlideshow",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1),
        )
        qt_app.processEvents()
        show = _child(window, "slideshowView")
        assert show.property("visible") is True
        assert show.property("currentIndex") == 1

        button = _child(window, "slideshowStarButton")
        try:
            wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)

            # a vetített (második) kép kapja a csillagot, nem a rács-kijelölés
            assert "star=yes" in _ini_text(controller).split("[b.jpg]")[1]
            assert _index_star(controller, "b.jpg") == 1
            assert _index_star(controller, "a.jpg") == 0
            assert _starred_names(controller) == ["b.jpg"]
        finally:
            QMetaObject.invokeMethod(
                show, "stop", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()


class TestABelepesiPontokLeltara:
    """Ha új csillag-vezérlő születik, ez a teszt kéri hozzá az őrt."""

    def test_csak_a_ket_ismert_hivo_van(self) -> None:
        hivok = sorted(
            str(path.relative_to(_QML_DIR))
            for path in _QML_DIR.rglob("*.qml")
            if "controller.toggleStar" in path.read_text(encoding="utf-8")
        )
        assert hivok == ["Main.qml", "PicasaPy/TrayBar.qml"], (
            "új csillag-belépési pont került a felületre — ehhez a fájlhoz "
            "őr-teszt is kell (a Main.qml a diavetítés gombját közvetíti, a "
            "TrayBar.qml a tálcáét)"
        )
