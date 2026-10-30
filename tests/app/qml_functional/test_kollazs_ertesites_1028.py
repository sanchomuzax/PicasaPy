r"""A kész kollázs MEGTALÁLÁSA: odaugrás + kattintható értesítés (#1028).

A felhasználó a v0.8.4-en jelezte, hogy a „Kollázs létrehozása" után a lap
bezáródik — és ennyi. A kész képet nem látja sehol.

## Az eredeti négy záró lépése

A végleges mentő (`0x0083ba60`) sorban: **indexelés** → miniatűr-munka →
**a lap bezárja magát** (a „Bezárás" gombot nyomja meg programból, a
mentetlen-módosítás kérdés elnyomva) → **`locate` az új fájlra**. Ezen
felül a kész-értesítés kezelője (`0x0088a020`) kiírja a `collage::done` =
**„A kollázs kész (kattintson ide)"** szöveget.

Nálunk a lapzárás megvolt, az odaugrás és az értesítés nem.

## ⚠️ HELYESBÍTÉS (#1119, 2026-08-20) — az ÉRTESÍTÉS rossz ághoz került

A fenti indoklás egy pontban téves volt: a `collage::done` értesítő
(`0x0088a020`) a `0x0057aa10`-et hívja, amiben a `Control Panel\Desktop\`
registrykulcs és a `picasabackground.bmp` szerepel — vagyis az értesítés az
**„Asztali háttérkép"** ágé, **nem a rendes kollázs-készítésé**.

A tulajdonos **háromszor** jelezte, hogy „ilyen gomb a Picasa 3-ban
nincs" — és igaza volt.

Ezért ez a fájl mostantól **az ellenkezőjét állítja**: a rendes mentés után
az értesítés NEM jelenik meg. Az odaugrás (`locate`) és a lapzárás
állításai **változatlanok** — azok a jegy helyes részei voltak.

A `CollageDoneNotice` komponens **megmarad** (az „Asztali háttérkép" ágé),
és az itteni tesztek a LÉTÉT továbbra is őrzik.

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


class TestNincsErtesites:
    """#1119: a RENDES mentés után NINCS értesítés.

    A #1028 ezt az osztályt eredetileg fordítva állította. A helyesbítés
    oka a modul docstringjében: a `collage::done` az „Asztali háttérkép"
    ágé, nem a rendes kollázs-készítésé."""

    def test_a_mentes_utan_NEM_jelenik_meg(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        ertesites = _ertesites(window)
        assert ertesites is None or ertesites.property("visible") is False

    def test_a_lap_bezarasa_utan_sem_jelenik_meg(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app

        _mentes_kesz(window, qt_app, _kep_utvonala(tmp_path))

        assert controller.collageOpen is False
        ertesites = _ertesites(window)
        assert ertesites is None or ertesites.property("visible") is False

    def test_indulaskor_sem_latszik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        ertesites = _ertesites(window)

        assert ertesites is None or ertesites.property("visible") is False


class TestAKomponensMARAD:
    """⚠️ A `CollageDoneNotice` az „Asztali háttérkép" ágé — NEM törlendő.

    Az eredetiben LÉTEZIK ez az értesítés, csak máshol; a bekötése külön
    jegy (ma a `collageDesktopBackgroundReady` jelzésnek nincs fogadója).
    A törlés visszafejlesztés volna."""

    def test_a_peldany_letezik_a_gazdaban(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        assert _ertesites(window) is not None


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
