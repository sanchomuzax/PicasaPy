"""#1443: a csillagozott nézet KÖVESSE a csillag levételét — kattintásra.

## A tulajdonos jelentése

> „A csillagozott nézetben állva leveszem a csillagot egy képről, és a kép
> ott marad, amíg a nézet újra le nem kérdez."

## A mérés (a javítás előtt)

A csillagozott nézet nem élő szűrő, hanem **lekérdezés**: a
`showStarred()` (`app/controller.py`) egyszer lefuttatja a
`starred_photos()`-t, és az eredményt mutatja. A tagságot innentől
semmi nem tartja karban.

| út | mit tett a javítás előtt |
|---|---|
| **egyes** (`toggleStar`) | a `_run_photo_write` → `_on_photo_field_updated` CSAK a sort frissíti (`PhotoGridModel.update_photo`) — a kép `star` mezője `False` lesz, de a sor a listában marad |
| **kötegelt** (`toggleStarMany`) | az `_apply_batch` a végén `_refresh_view()`-t hív, tehát a sor MÁR ELTŰNT — a jegy diagnózisa itt nem állt |

A kötegelt úton viszont a **zöld eredménysáv** hazudott: „1 folders /
2 pictures visible", miközben nulla kép látszott — a `_refresh_view()`
nem számolta újra a `_filter_status`-t.

Ez a fájl mindkettőt őrzi, **a tálca csillag-gombjára kattintva** (nem a
Python-metódust hívva): egy elrontott kötés csak így tud pirosra váltani.

## Amit NEM őrzünk itt, és miért

Az ELLENKEZŐ irány (csillagozáskor a kép BEKERÜL a nézetbe) a felületről
nem érhető el ugyanabban a nézetben állva: a csillagozott nézet csak
csillagos képeket tartalmaz, tehát nincs olyan sor, amelyre kattintva
csillagot lehetne ADNI. Az irányt ezért a nézetbe visszatéréssel mérjük
(`test_visszacsillagozva_ujra_bekerul`) — ez azt is kizárja, hogy a
javítás „kitiltott sorok" listájával oldja meg a feladatot lekérdezés
helyett.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.qt_wait import wait_for_photo_op


def _child(root, name: str) -> QObject:
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _tray_star_button(window) -> QObject:
    """A tálca csillag-gombja (a #1438 tesztjének keresője)."""
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


def _nevek(controller) -> list[str]:
    return [photo.name for photo in controller.photos.photos]


def _csillagozz_mindkettot(window, controller, qt_app) -> None:
    """Kiinduló állapot: `a.jpg` és `b.jpg` is csillagos — a gombra
    kattintva, kötegelt úton (ez a leggyorsabb valódi út)."""
    ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
    _select(window, qt_app, 0)
    _select(window, qt_app, 1, ctrl)
    button = _tray_star_button(window)
    assert button.property("multi") is True
    _click(button)
    qt_app.processEvents()
    controller.showStarred()
    assert _nevek(controller) == ["a.jpg", "b.jpg"], (
        "a kiinduló állapot nem áll elő: nem lett mindkét kép csillagos"
    )


class TestEgyesUt:
    def test_a_csillag_levetele_azonnal_kikeruli_a_kepet(
        self, qml_app, qt_app
    ) -> None:
        """⚠️ A jegy magja: a képnek AZONNAL el kell tűnnie a nézetből."""
        window, controller, _engine = qml_app
        _csillagozz_mindkettot(window, controller, qt_app)

        _select(window, qt_app, 0)
        button = _tray_star_button(window)
        assert button.property("targetRow") == 0
        assert button.property("multi") is False

        wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)

        assert _nevek(controller) == ["b.jpg"], (
            "a csillagozott nézet nem követte a csillag levételét: a kép "
            "ottmaradt (a modellben a star már False)"
        )

    def test_a_zold_sav_darabszama_is_kovet(self, qml_app, qt_app) -> None:
        """A sáv „2 pictures visible"-t írt, miközben egy kép látszott."""
        window, controller, _engine = qml_app
        _csillagozz_mindkettot(window, controller, qt_app)
        assert "2 pictures" in controller.filterStatusText

        _select(window, qt_app, 0)
        wait_for_photo_op(
            controller,
            lambda: _click(_tray_star_button(window)),
            qt_app=qt_app,
        )

        assert "1 pictures" in controller.filterStatusText, (
            "a zöld eredménysáv darabszáma elavult: "
            f"{controller.filterStatusText!r}"
        )

    def test_mappa_nezetben_a_kep_marad(self, qml_app, qt_app) -> None:
        """Ellenkező irányú őr: a mappa-nézetben a csillag levétele NEM
        távolíthat el sort — a tagság ott nem a csillagtól függ."""
        window, controller, _engine = qml_app
        _select(window, qt_app, 0)
        button = _tray_star_button(window)
        wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)
        assert _nevek(controller) == ["a.jpg", "b.jpg"]

        wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)

        assert _nevek(controller) == ["a.jpg", "b.jpg"], (
            "a mappa-nézetből eltűnt egy kép a csillag levételekor"
        )


class TestKotegeltUt:
    def test_mindket_csillag_levetele_kiuriti_a_nezetet(
        self, qml_app, qt_app
    ) -> None:
        """Megőrző: a kötegelt út a mérés szerint MÁR jó volt."""
        window, controller, _engine = qml_app
        _csillagozz_mindkettot(window, controller, qt_app)

        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        _select(window, qt_app, 0)
        _select(window, qt_app, 1, ctrl)
        button = _tray_star_button(window)
        assert button.property("multi") is True

        _click(button)
        qt_app.processEvents()

        assert _nevek(controller) == []
        assert "0 pictures" in controller.filterStatusText, (
            "a zöld eredménysáv darabszáma elavult a kötegelt úton: "
            f"{controller.filterStatusText!r}"
        )


class TestANezobolIs:
    def test_a_nezobol_levett_csillag_is_kikeruli_a_kepet(
        self, qml_app, qt_app
    ) -> None:
        """A tálca gombja a néző alatt is látszik, és a NÉZŐ képére hat.

        Ez a kör kockázatos pontja: a frissítés a néző alatt rövidíti meg a
        listát. Az `autouse` QML-hiba-őr (ld. conftest) miatt egy „Cannot
        read property … of null" itt pirosra váltana."""
        window, controller, _engine = qml_app
        _csillagozz_mindkettot(window, controller, qt_app)

        window.setProperty("viewerOpen", True)
        viewer = _child(window, "photoViewer")
        QMetaObject.invokeMethod(
            viewer, "show", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        button = _tray_star_button(window)
        assert button.property("targetRow") == 0

        try:
            wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)
            for _ in range(5):
                qt_app.processEvents()
            assert _nevek(controller) == ["b.jpg"]
        finally:
            window.setProperty("viewerOpen", False)
            qt_app.processEvents()


class TestVisszaCsillagozas:
    def test_visszacsillagozva_ujra_bekerul(self, qml_app, qt_app) -> None:
        """A javítás lekérdezés legyen, ne „kitiltott sorok" listája."""
        window, controller, _engine = qml_app
        _csillagozz_mindkettot(window, controller, qt_app)
        _select(window, qt_app, 0)
        wait_for_photo_op(
            controller,
            lambda: _click(_tray_star_button(window)),
            qt_app=qt_app,
        )
        assert _nevek(controller) == ["b.jpg"]

        # vissza a mappához, ott újra csillagozzuk a gombbal
        controller.clearFilter()
        qt_app.processEvents()
        _select(window, qt_app, 0)
        button = _tray_star_button(window)
        assert button.property("targetRow") == 0
        wait_for_photo_op(controller, lambda: _click(button), qt_app=qt_app)

        controller.showStarred()
        assert _nevek(controller) == ["a.jpg", "b.jpg"], (
            "a visszacsillagozott kép nem került vissza a nézetbe"
        )
