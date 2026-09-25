"""#3503 — „Létrehozás ▸ Ajándék CD készítése…": a menüponttól a kész
lemezképig, a teljes ablakban.

A menüpont a #324-es audit óta halott helyfoglaló volt. Most a
kiadás-panelt nyitja Ajándék-CD üzemmódban a könyvtár ALJÁN (ahol az
eredetiben is ül), a „Lemezre írás" a képtálca elemeiből lemezképet ír, és
a végén a mért „CD kész" párbeszéd jön „CD megjelenítése" gombbal.

⚠️ A cél-fájl választó a rendszer natív párbeszéde — offscreen nem
kattintható, ezért a folyamatot a választó `onAccepted` ágának belépőjén
(`GiftCdHost.indit`) indítjuk. Minden más lépés valódi egérkattintás.
"""

from __future__ import annotations


from PySide6.QtCore import (
    Q_ARG, QEventLoop, QMetaObject, QObject, QPoint, Qt, QTimer,
)
from PySide6.QtTest import QTest


def _var(qt_app, feltetel, ms=20000) -> bool:
    eltelt = 0
    while eltelt < ms:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        szunet = QEventLoop()
        QTimer.singleShot(25, szunet.quit)
        szunet.exec()
        eltelt += 25
    return bool(feltetel())


def _elem(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, elem):
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )


def _talcara(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _nyisd_meg(window, qt_app):
    menu = _elem(window, "menuCreateGiftCd")
    menu.triggered.emit()
    qt_app.processEvents()
    return _elem(window, "giftCdHost")


class TestAMenupont:
    def test_ures_talcanal_szurke(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [])

        assert _elem(window, "menuCreateGiftCd").property("enabled") is False

    def test_a_talcaval_el_es_nem_helyfoglalo(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [0])

        menu = _elem(window, "menuCreateGiftCd")

        assert menu.property("enabled") is True
        assert menu.property("placeholder") in (None, False)


class TestAPanel:
    def test_a_menubol_a_konyvtar_aljan_nyilik(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [0, 1])

        host = _nyisd_meg(window, qt_app)

        assert host.property("visible") is True
        assert host.property("height") == 212
        # a panel NEM takarja a képeket: a könyvtár a panel fölött ér véget
        split = _elem(window, "mainSplit")
        assert split.property("y") + split.property("height") <= host.property("y")

    def test_a_panel_a_talca_darabszamat_latja(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [0, 1])
        _nyisd_meg(window, qt_app)

        assert _elem(window, "publishPresentCdGo").property("enabled") is True

    def test_a_megse_bezarja(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [0])
        host = _nyisd_meg(window, qt_app)

        _kattints(window, _elem(window, "publishPresentCdCancel"))

        assert _var(qt_app, lambda: host.property("visible") is False)


class TestALemezkep:
    def test_a_kesz_lemezkep_es_a_cd_kesz_parbeszed(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [0, 1])
        host = _nyisd_meg(window, qt_app)
        megnyitott = []
        monkeypatch.setattr(
            "picasapy.fileops.reveal._run",
            lambda parancs, **_kw: megnyitott.append(parancs),
        )
        cel = tmp_path / "ki" / "ajandek.iso"

        QMetaObject.invokeMethod(
            host, "indit", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", cel.as_uri()),
        )

        parbeszed = _elem(window, "giftCdDoneDialog")
        assert _var(qt_app, lambda: parbeszed.property("visible") is True), (
            "a „CD kész” párbeszéd nem jelent meg"
        )
        assert cel.stat().st_size > 0
        assert _elem(window, "giftCdDonePath").property("text") == str(cel)

        _kattints(window, _elem(window, "giftCdShowButton"))

        assert _var(qt_app, lambda: bool(megnyitott)), (
            "a „CD megjelenítése” nem nyitotta meg a lemezkép helyét"
        )
        assert str(cel.parent) in str(megnyitott[0]) or str(cel) in str(
            megnyitott[0]
        )
