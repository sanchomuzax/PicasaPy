"""#4212 — a közzétételi méret tényleges főablakos kiválasztása."""

from __future__ import annotations

import time
import csv
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app

_KEEP_ALIVE = []
_GYOKER = Path(__file__).resolve().parents[3]


def _varj(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _elem(window, nev):
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található a főablakban"
    return elem


def _kattints(window, elem: QQuickItem) -> None:
    center = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(center.x(), center.y()),
    )


def _nyisd_meg_ajandek_cd(window, qt_app):
    sor = list(window.contentItem().childItems())
    create_menu = None
    while sor:
        elem = sor.pop()
        if (
            "MenuBarItem" in elem.metaObject().className()
            and elem.property("text") == "&Create"
        ):
            create_menu = elem
            break
        sor.extend(elem.childItems())
    assert create_menu is not None, "a Létrehozás menü nem található"
    _kattints(window, create_menu)
    menu_item = window.findChild(QQuickItem, "menuCreateGiftCd")
    assert menu_item is not None
    assert _varj(qt_app, lambda: menu_item.property("visible") is True), (
        "a Létrehozás menü nem nyílt ki"
    )
    _kattints(window, menu_item)
    host = window.findChild(QQuickItem, "giftCdHost")
    assert host is not None
    assert _varj(qt_app, lambda: host.property("visible") is True), (
        "az Ajándék-CD panel nem nyílt meg"
    )
    return host


def _gyerekek(elem: QQuickItem):
    for child in elem.childItems():
        yield child
        yield from _gyerekek(child)


def _popup_proba(engine, combo: QQuickItem):
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetCombo
    readonly property bool popupVisible:
        targetCombo && targetCombo.popup ? targetCombo.popup.visible : false
    readonly property Item popupContent:
        targetCombo && targetCombo.popup ? targetCombo.popup.contentItem : null
}""",
        QUrl(),
    )
    assert component.isReady(), [error.toString() for error in component.errors()]
    probe = component.createWithInitialProperties({"targetCombo": combo})
    assert probe is not None, [error.toString() for error in component.errors()]
    _KEEP_ALIVE.extend((component, probe))
    return probe


def _valasztott_sor(tartalom: QQuickItem, index: int):
    cel = ("Original Size", "640 x 480", "800 x 600", "1600 x 1200")[index]
    sorok = [
        item for item in _gyerekek(tartalom)
        if item.property("text") == cel and item.width() > 0 and item.height() > 0
    ]
    assert sorok, f"a legördülőben nem található a(z) {cel!r} sor"
    # A delegate maga és a benne levő Text is hordozhatja ugyanazt a feliratot;
    # a legnagyobb QQuickItem a ténylegesen kattintható sor.
    return max(sorok, key=lambda item: item.width() * item.height())


def test_a_800x600_valasztas_kattintasbol_a_lemezkepvezerlohoz_er(
    qt_app, tmp_path, monkeypatch
):
    gen = _build_qml_app(qt_app, tmp_path)
    window, controller, engine = next(gen)
    try:
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        assert _varj(qt_app, lambda: controller.heldCount > 0), (
            "a próbakép kijelölése nem került a képtálcára"
        )

        kezdeti_magassag = window.height()
        for eltolás in (-5, 0, 5):
            window.setHeight(kezdeti_magassag + eltolás)
            assert _varj(
                qt_app,
                lambda eltolás=eltolás: window.height()
                == kezdeti_magassag + eltolás,
            ), f"a főablak magassága nem állt be ({eltolás:+} px)"

            host = _nyisd_meg_ajandek_cd(window, qt_app)
            combo = _elem(window, "publishPicSizeMenu")
            popup = _popup_proba(engine, combo)
            _kattints(window, combo)
            assert _varj(
                qt_app, lambda popup=popup: popup.property("popupVisible") is True
            ), (
                "a tényleges kattintás nem nyitotta le a méretválasztót"
            )
            tartalom = popup.property("popupContent")
            assert isinstance(tartalom, QQuickItem)
            tetel = _valasztott_sor(tartalom, 2)
            popup_window = tetel.window()
            assert popup_window is not None
            _kattints(popup_window, tetel)
            assert _varj(
                qt_app, lambda combo=combo: combo.property("currentIndex") == 2
            ), (
                "a valódi 800 x 600 menüsor-kattintás nem választódott ki"
            )

            hivasok = []

            def inline(
                target,
                *,
                args=(),
                kwargs=None,
                name=None,
                cancel=None,
                calls=hivasok,
            ):
                calls.append((tuple(args), name))
                return target(*args, **(kwargs or {}))

            monkeypatch.setattr(controller, "_start_background", inline)
            _kattints(window, _elem(window, "publishPresentCdGo"))
            fajlvalaszto = window.findChild(QObject, "giftCdTargetDialog")
            assert fajlvalaszto is not None
            assert _varj(
                qt_app,
                lambda fajlvalaszto=fajlvalaszto: fajlvalaszto.property(
                    "visible"
                ) is True,
            ), (
                "a Lemezre írás kattintása nem nyitotta meg a célválasztót"
            )
            QMetaObject.invokeMethod(fajlvalaszto, "close")
            assert _varj(
                qt_app,
                lambda fajlvalaszto=fajlvalaszto: fajlvalaszto.property(
                    "visible"
                ) is False,
            )

            cel = tmp_path / f"meret-{eltolás:+}.iso"
            assert QMetaObject.invokeMethod(
                host, "indit", Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", cel.as_uri()),
            )
            assert hivasok and hivasok[-1][0][2] == 2, (
                "a vezérlő nem kapta meg a kiválasztott 800 x 600 fokozatot"
            )
            assert cel.is_file() and cel.stat().st_size > 0, (
                "a főablakos méretválasztás nem készített lemezkép-kimenetet"
            )
            done = window.findChild(QObject, "giftCdDoneDialog")
            assert done is not None
            assert _varj(
                qt_app, lambda done=done: done.property("visible") is True
            ), (
                "a lemezkép vezérlője nem jelezte a kész kimenetet"
            )
            QMetaObject.invokeMethod(done, "close")
            _kattints(window, _elem(window, "publishPresentCdCancel"))
            assert _varj(qt_app, lambda host=host: host.property("visible") is False)
    finally:
        try:
            gen.close()
        except RuntimeError:
            pass


def test_a_picsizemenu_lefedettsegi_sora_a_kattintasi_probat_nevezi_meg():
    tablazat = _GYOKER / "docs" / "specs" / "ui-lefedettseg-elemek.csv"
    with tablazat.open(encoding="utf-8", newline="") as fajl:
        talalatok = [
            sor for sor in csv.DictReader(fajl)
            if sor["elem"] == "publish/picsizemenu"
        ]

    assert len(talalatok) == 1, "a picsizemenu CSV-sora hiányzik vagy ismétlődik"
    sor = talalatok[0]
    assert sor["allapot"] == "megvan"
    assert "PicasaPy/PublishPanel.qml" in sor["bizonyitek"]
    assert "PicasaPy/GiftCdHost.qml" in sor["bizonyitek"]
    assert (
        "tests/app/qml_functional/test_publish_fomenu_meret_4212.py"
        in sor["bizonyitek"]
    )
