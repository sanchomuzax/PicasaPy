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

import shutil
import subprocess

import pytest
from PySide6.QtCore import (
    Q_ARG, QEventLoop, QMetaObject, QObject, QPoint, QPointF, Qt, QTimer,
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
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )


def _var_elrendezett_gombra(window, qt_app, parbeszed, nev):
    """A látható, már elrendezett párbeszédgombot adja vissza határidővel."""
    gomb = _elem(window, nev)
    elozo_geometria = None

    def elrendezve():
        nonlocal elozo_geometria
        if parbeszed.property("visible") is not True or not gomb.isVisible():
            elozo_geometria = None
            return False

        szelesseg = gomb.width()
        magassag = gomb.height()
        if szelesseg <= 0 or magassag <= 0:
            elozo_geometria = None
            return False

        kozep = gomb.mapToScene(QPointF(szelesseg / 2, magassag / 2))
        if not (0 <= kozep.x() < window.width()
                and 0 <= kozep.y() < window.height()):
            elozo_geometria = None
            return False

        geometria = (kozep.x(), kozep.y(), szelesseg, magassag)
        stabil = elozo_geometria == geometria
        elozo_geometria = geometria
        return stabil

    assert _var(qt_app, elrendezve, ms=5000), (
        f"a {nev} gomb nem lett látható és stabilan elrendezve a főablakban"
    )
    return gomb


def _talcara(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _nyisd_meg(window, qt_app):
    # A teljes út: a felső menü, majd a tényleges menütétel kattintása.
    gyoker = window.contentItem()
    sor = list(gyoker.childItems())
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
    assert create_menu is not None, "a Létrehozás menü nincs a menüsávon"
    _kattints(window, create_menu)
    assert _var(
        qt_app,
        lambda: _elem(window, "menuCreateGiftCd").property("visible") is True,
    ), "a Létrehozás menü nem nyílt ki"
    menu = _elem(window, "menuCreateGiftCd")
    _kattints(window, menu)
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
    @pytest.mark.parametrize(
        "ablak",
        [
            pytest.param(("magassag", -5), id="magassag-minusz-5"),
            pytest.param(("magassag", 0), id="alapmagassag"),
            pytest.param(("magassag", 5), id="magassag-plusz-5"),
            pytest.param(("meret", (1024, 700)), id="1024x700"),
        ],
    )
    def test_a_kesz_lemezkep_es_a_cd_kesz_parbeszed(
        self, qml_app, qt_app, tmp_path, monkeypatch, ablak
    ):
        window, controller, _ = qml_app
        if ablak[0] == "magassag":
            vart_meret = (window.width(), window.height() + ablak[1])
        else:
            vart_meret = ablak[1]
        window.setWidth(vart_meret[0])
        window.setHeight(vart_meret[1])
        assert _var(
            qt_app,
            lambda: (window.width(), window.height()) == vart_meret,
        ), f"a főablak nem vette fel a kért méretet: {vart_meret}"
        qt_app.processEvents()
        _talcara(window, qt_app, [0, 1])
        host = _nyisd_meg(window, qt_app)
        megnyitott = []
        monkeypatch.setattr(
            "picasapy.fileops.reveal._run",
            lambda parancs, **_kw: megnyitott.append(parancs),
        )
        cel = tmp_path / "ki" / "ajandek.iso"

        # A főablak „Lemezre írás” gombját valódi kattintás indítja.
        # A Qt natív fájlválasztója offscreen nem kattintható, ezért annak
        # elfogadott útját adjuk át közvetlenül a gazda QML-belépőjének.
        _kattints(window, _elem(window, "publishPresentCdGo"))
        celvalaszto = _elem(window, "giftCdTargetDialog")
        assert celvalaszto.property("visible") is True
        # Elfogadáskor a választó bezárul; nyitva hagyva a CI-n elnyeli a
        # későbbi kattintást.
        QMetaObject.invokeMethod(celvalaszto, "close")
        assert _var(qt_app, lambda: celvalaszto.property("visible") is False)
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

        hetz = shutil.which("7z") or shutil.which("7za")
        assert hetz, "nincs 7z — a főablak kimenetének független ellenőrzése nem mérhető"
        kibontas = tmp_path / "iso-bontas"
        kibontas.mkdir()
        bontas = subprocess.run(
            [hetz, "x", "-y", f"-o{kibontas}", str(cel)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        assert bontas.returncode == 0, bontas.stdout + bontas.stderr
        assert sorted(p.name for p in (kibontas / "Pictures").iterdir()) == [
            "a.jpg", "b.jpg",
        ]

        megjelenit_gomb = _var_elrendezett_gombra(
            window, qt_app, parbeszed, "giftCdShowButton",
        )
        _kattints(window, megjelenit_gomb)

        assert _var(qt_app, lambda: bool(megnyitott)), (
            "a „CD megjelenítése” nem nyitotta meg a lemezkép helyét"
        )
        assert str(cel.parent) in str(megnyitott[0]) or str(cel) in str(
            megnyitott[0]
        )

    def test_a_lemaradt_elemeket_kimondja(self, qml_app, qt_app):
        """Az átnézés lelete: ha elemek maradtak le, a „CD kész" ablak is
        mondja, nem csak a napló."""
        window, controller, _ = qml_app
        host = _elem(window, "giftCdHost")
        hiany = _elem(window, "giftCdDoneMissing")

        controller.ajandekCdKesz.emit("/tmp/x.iso", 2, 1)

        assert _var(qt_app, lambda: hiany.property("visible") is True)
        assert "1" in hiany.property("text")
        assert host.property("dolgozik") is False

    def test_hiba_utan_ujra_nyomhato(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _talcara(window, qt_app, [0])
        host = _nyisd_meg(window, qt_app)
        host.setProperty("dolgozik", True)

        controller.ajandekCdKesz.emit("", 0, 1)

        assert _var(qt_app, lambda: _elem(window, "giftCdErrorDialog").property("visible") is True)
        assert _elem(window, "publishPresentCdGo").property("enabled") is True
