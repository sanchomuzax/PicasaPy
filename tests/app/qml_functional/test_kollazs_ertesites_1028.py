"""A kész kollázs MEGTALÁLÁSA: odaugrás + kattintható értesítés (#1028).

A felhasználó a v0.8.4-en jelezte, hogy a „Kollázs létrehozása" után a lap
bezáródik — és ennyi. A kész képet nem látja sehol.

## Az eredeti négy záró lépése

A végleges mentő (`0x0083ba60`) sorban: **indexelés** → miniatűr-munka →
**a lap bezárja magát** (a „Bezárás" gombot nyomja meg programból, a
mentetlen-módosítás kérdés elnyomva) → **`locate` az új fájlra**. Ezen
felül a kész-értesítés kezelője (`0x0088a020`) kiírja a `collage::done` =
**„A kollázs kész (kattintson ide)"** szöveget.

Nálunk a lapzárás megvolt, az odaugrás és az értesítés nem.

## Miért nem elég, hogy a szöveg MÁR MEGVAN

A `collage_save.py` a kész-üzenetet a **folyamatjelző sávba** írja, amit a
`CollagePanel` a rá következő pillanatban elrejt. A felhasználó tehát a
helyes szöveget egy haldokló folyamatjelzőben kapta, egy villanásra,
kattinthatatlanul.

## Miért a `collageSaved` jelzésre kötünk

A `CollagePanel` már ma is kiadja a `collageSaved(path)` jelzést a
`finishSave`-ben — és **egyetlen hallgatója sem volt**. A lapzárás és a
navigáció felelőse külön: a panel jelez, a gazda navigál.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Q_ARG, Qt

#: A kattintható értesítés és a szövege.
ERTESITES = "collageDoneNotice"
ERTESITES_SZOVEG = "collageDoneNoticeText"


def _panel(window):
    return window.findChild(QObject, "collagePanel")


def _ertesites(window):
    return window.findChild(QObject, ERTESITES)


def _mentes_kesz(window, qt_app, utvonal: str):
    """A panel `finishSave`-je — ide fut be a `collageDone` is."""
    window.metaObject().invokeMethod(window, "openCollageTab")
    qt_app.processEvents()
    panel = _panel(window)
    QMetaObject.invokeMethod(
        panel, "finishSave", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", utvonal),
    )
    qt_app.processEvents()


def _kep_utvonala(tmp_path) -> str:
    """A teszt-könyvtár első képe — ez játssza a kész kollázst.

    A `qml_app` fixture a `tmp_path/kepek` alá teszi az `a.jpg`-t; a
    modellnek nincs sor→útvonal slotja, ezért a fixture szerződésére
    támaszkodunk."""
    return str(tmp_path / "kepek" / "a.jpg")


class TestAzOdaugras:
    """A könyvtár a kész kollázsra ugrik, kijelölve."""

    def test_a_kesz_kollazs_lesz_a_kijelolt(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        cel = _kep_utvonala(tmp_path)

        _mentes_kesz(window, qt_app, cel)

        assert window.property("selectedIndex") == controller.photos.rowOfPath(cel)

    def test_a_kijeloles_egyetlen_kepre_szukul(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        cel = _kep_utvonala(tmp_path)

        _mentes_kesz(window, qt_app, cel)

        # a QML-tömb `QJSValue`-ként jön át — a `toVariant()` fordítja
        kijeloles = window.property("selectedIndexes").toVariant()
        assert [int(x) for x in kijeloles] == [controller.photos.rowOfPath(cel)]

    def test_a_konyvtar_lapja_lesz_az_aktiv(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        sav = window.findChild(QObject, "documentTabStrip")
        assert sav.property("activeTabId") == sav.property("libraryTabId")

    def test_a_nezo_NEM_nyilik_meg_magatol(self, qml_app, qt_app, tmp_path):
        """⚠️ Az eredeti `locate`-el, nem nyit nézőt — a nagyban megnyitás a
        felhasználó kattintása. Automatikus navigációt itt építeni azt
        jelentené, hogy elvesszük tőle a döntést."""
        window, controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        assert window.property("viewerOpen") is False


class TestAzErtesites:
    """„A kollázs kész (kattintson ide)" — kattintható, és megmarad."""

    def test_megjelenik_a_mentes_utan(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        ertesites = _ertesites(window)
        assert ertesites is not None
        assert ertesites.property("visible") is True

    def test_a_lap_bezarasa_UTAN_is_latszik(self, qml_app, qt_app, tmp_path):
        """A jegy lényege: a szöveg eddig a haldokló folyamatjelzőben volt."""
        window, controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        assert controller.collageOpen is False
        assert _ertesites(window).property("visible") is True

    def test_a_szovege_a_hivatalos_magyar_forras(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        szoveg = _ertesites(window).findChild(QObject, ERTESITES_SZOVEG)
        assert szoveg is not None
        assert "click" in str(szoveg.property("text")).lower()

    def test_kattintasra_nagyban_megnyitja(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        cel = _kep_utvonala(tmp_path)
        _mentes_kesz(window, qt_app, cel)

        QMetaObject.invokeMethod(
            _ertesites(window), "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert window.property("viewerOpen") is True

    def test_kattintas_utan_eltunik(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        QMetaObject.invokeMethod(
            _ertesites(window), "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert _ertesites(window).property("visible") is False

    def test_indulaskor_nem_latszik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        ertesites = _ertesites(window)

        assert ertesites is None or ertesites.property("visible") is False


class TestAJelzesnekVanFogadoja:
    """A `collageSaved` jelzést eddig SENKI nem hallgatta.

    Ugyanaz a hibaosztály, mint a #1051-nél: a jelzés kiadódik, a felület
    nem reagál rá, és a funkció a felhasználó számára nem létezik."""

    def test_a_collageSaved_jelzesnek_van_kezeloje(self):
        import picasapy.app

        main = (
            Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
        ).read_text(encoding="utf-8")

        assert "onCollageSaved" in main
