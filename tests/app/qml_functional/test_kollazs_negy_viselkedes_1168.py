r"""#1168: a kollázs négy hiányzó viselkedése — a FELÜLET oldala.

Spec: `docs/specs/kollazs-eletciklus.md` **16.** A kutatói kör négy olyan
viselkedést talált, amit egyik kollázs-spec-lap sem írt le. Ebből három a
QML-ben dől el:

1. **A kész értesítés KATTINTHATÓ** (16.1). A `CollageDoneNotice` komponens
   MEGVOLT, a szövege is — csak SENKI nem mutatta meg: a
   `collageDesktopBackgroundReady` jelzésnek nem volt fogadója (#1119
   kommentje szó szerint kimondja). Az értesítés a #1119 szerint az
   **„Asztali háttérkép"** ágé, nem a rendes létrehozásé — ezt a fájl
   őrizni is fogja.
2. **„Mentés mellőzve" a PISZKOZAT ágán** (16.2/a): a „Piszkozat mentése"
   gomb üres vászonnal eddig némán bezárta a lapot.
3. **A várakozó sor a FŐABLAKBAN** (16.3): „Várakozás a kollázs
   elkészítésére…" — a könyvtárnézet is jelez, nem csak a panel.

A negyedik lelet (`hascollage`) nem felületi: album-szintű, származtatott
jelző, ld. `tests/index/test_album_collage_1168.py`.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Q_ARG, Qt

#: A kattintható értesítés és a szövege (a #1028 óta változatlan nevek).
ERTESITES = "collageDoneNotice"


def _panel(window):
    return window.findChild(QObject, "collagePanel")


def _keres(window, nev):
    return window.findChild(QObject, nev)


def _nyisd_a_kollazst(window, qt_app, controller=None, klipek=(0, 1)):
    """A Kollázs lap megnyitása — alapból KLIPEKKEL.

    A `qml_app` indulásakor nincs kijelölés, a `collageSourceRows()` így
    üres listát adna, és a panel klip nélkül nyílna — abból meg minden
    piszkozat-állítás hamisan zöld lenne."""
    if controller is not None:
        controller.openCollage(list(klipek))
    window.metaObject().invokeMethod(window, "openCollageTab")
    qt_app.processEvents()


def _kattints(elem):
    """Igazi kattintás a vezérlőre — a metódus közvetlen hívása zöld tud
    lenni akkor is, ha a gomb kattinthatatlan (MEMORY: „a vezérlőre
    KATTINTS")."""
    QMetaObject.invokeMethod(elem, "clicked", Qt.ConnectionType.DirectConnection)


class TestKattinthatoKeszErtesites:
    """16.1 — a „kész" értesítésnek VAN fogadója."""

    def test_az_asztali_hatterkep_aga_megmutatja(self, qml_app, qt_app, tmp_path):
        """A jelzésnek VAN fogadója — de hogy MELYIK felület mutatja, az a
        #1129 óta attól függ, jelen van-e a lebegő értesítősáv.

        A `Main.qml` mostantól példányosítja a `PicasaNotifier`-t, és az a
        `NotifierBus.attached` kapun át **elhallgattatja** a régi
        `CollageDoneNotice`-t — különben ugyanaz az esemény kétszer, két
        helyen szólalna meg. A régi doboz szándékosan a fában marad (a sáv
        nélküli üzemmód tartaléka), ezért a `visible: True` állítás
        önmagában már nem a hibát mérné.

        Az állítás ezért a FELHASZNÁLÓI kimenetre szól: az esemény
        valamelyik felületen megjelenik, a helyes célútvonallal."""
        window, controller, _engine = qml_app
        cel = str(tmp_path / "kepek" / "a.jpg")

        controller.collageDesktopBackgroundReady.emit(cel)
        qt_app.processEvents()

        regi_doboz = _keres(window, ERTESITES)
        assert regi_doboz is not None, "a régi értesítő-doboz eltűnt a fából"

        sav = _keres(window, "picasaNotifier")
        if sav is not None:
            # a sáv jelen van: ŐNEKI kell mutatnia, a réginek hallgatnia
            assert regi_doboz.property("visible") is False, (
                "a sáv mellett a régi doboz is megszólalt — kétszeres értesítés"
            )
            # a `Repeater` delegáltjait `findChild` nem találja meg, ezért a
            # sáv saját olvasóin át kérdezünk (`cellCount` / `payloadAt`)
            assert sav.property("cellCount") == 1, (
                "a sáv nem vette fel az értesítést"
            )
            assert sav.property("lastPayload") == cel, (
                "a sáv nem a helyes célútvonalat kapta"
            )
        else:
            # sáv nélküli üzemmód: a régi doboz a fogadó
            assert regi_doboz.property("visible") is True
            assert regi_doboz.property("path") == cel

    def test_a_szovege_a_collage_done_kulcse(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app

        controller.collageDesktopBackgroundReady.emit(
            str(tmp_path / "kepek" / "a.jpg")
        )
        qt_app.processEvents()

        felirat = _keres(window, "collageDoneNoticeText")
        assert felirat.property("text") == "The collage is ready (click here)"

    def test_a_RENDES_letrehozas_utan_tovabbra_sincs(self, qml_app, qt_app, tmp_path):
        """#1119: a tulajdonos HÁROMSZOR jelezte, hogy ilyen gomb a rendes
        kollázs-készítés után a Picasa 3-ban nincs. A #1168 ezt nem
        írhatja felül — csak a háttérkép-ágat kötjük be."""
        window, _controller, _engine = qml_app
        _nyisd_a_kollazst(window, qt_app)

        QMetaObject.invokeMethod(
            _panel(window), "finishSave", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", str(tmp_path / "kepek" / "a.jpg")),
        )
        qt_app.processEvents()

        ertesites = _keres(window, ERTESITES)
        assert ertesites is None or ertesites.property("visible") is False

    def test_ures_utvonalra_nem_villan_fel(self, qml_app, qt_app):
        window, controller, _engine = qml_app

        controller.collageDesktopBackgroundReady.emit("")
        qt_app.processEvents()

        ertesites = _keres(window, ERTESITES)
        assert ertesites is None or ertesites.property("visible") is False


class TestPiszkozatMentesMellozve:
    """16.2/a — „Piszkozat mentése" üres vásznon: doboz, és a lap MARAD."""

    def _ures_vaszon_bezarasa(self, window, controller, qt_app):
        _nyisd_a_kollazst(window, qt_app, controller)
        assert controller.collageClipCount > 0, "a panel klip nélkül nyílt"
        controller.selectAllNodes()
        controller.removeSelectedNodes()
        qt_app.processEvents()
        assert controller.collageDirty is True
        _kattints(_keres(window, "collageCloseButton"))
        qt_app.processEvents()
        _kattints(_keres(window, "collageSaveDraftButton"))
        qt_app.processEvents()

    def test_a_mentes_mellozve_doboz_jelenik_meg(self, qml_app, qt_app):
        window, controller, _engine = qml_app

        self._ures_vaszon_bezarasa(window, controller, qt_app)

        doboz = _keres(window, "collageSaveSkippedDialog")
        assert doboz is not None and doboz.property("visible") is True

    def test_a_lap_NYITVA_marad(self, qml_app, qt_app):
        """A dobozban az áll, hogy „Vegyen fel legalább egy képet, és
        próbálkozzon újra" — becsukott lapon ez üres ígéret volna."""
        window, controller, _engine = qml_app

        self._ures_vaszon_bezarasa(window, controller, qt_app)

        assert controller.collageOpen is True

    def test_klippel_a_lap_TOVABBRA_is_bezarul(self, qml_app, qt_app):
        """Az őr foga: a rendes piszkozat-ág nem sérülhet."""
        window, controller, _engine = qml_app
        _nyisd_a_kollazst(window, qt_app, controller)
        controller.setCollageSpacing(3.0)  # legyen mentetlen módosítás
        qt_app.processEvents()

        _kattints(_keres(window, "collageCloseButton"))
        qt_app.processEvents()
        _kattints(_keres(window, "collageSaveDraftButton"))
        qt_app.processEvents()

        assert controller.collageOpen is False


class TestVarakozasAFoablakban:
    """16.3 — `CThumbUI::CreateCollageWait` a könyvtárnézet alsó sávjában."""

    #: A `0x007f7120` szövege, angol forrásalakban.
    VARAKOZAS = "Waiting for the collage to be created…"

    def test_rajzolas_kozben_a_varakozas_latszik(self, qml_app, qt_app):
        window, controller, _engine = qml_app

        controller._set_rendering(True)
        qt_app.processEvents()

        assert _keres(window, "trayInfoText").property("text") == self.VARAKOZAS

    def test_rajzolas_nelkul_nem_latszik(self, qml_app, qt_app):
        window, controller, _engine = qml_app

        controller._set_rendering(True)
        qt_app.processEvents()
        controller._set_rendering(False)
        qt_app.processEvents()

        assert _keres(window, "trayInfoText").property("text") != self.VARAKOZAS


class TestFormatumFigyelmeztetes:
    """16.2/b — a szöveg a jegy szerinti, a ZÁRÓ KÉRDÉSSEL együtt."""

    def test_a_zaro_kerdes_is_kint_van(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd_a_kollazst(window, qt_app)

        uzenet = _keres(window, "collageFormatMismatchMessage").property("text")

        assert "Are you sure you want to continue?" in uzenet

    def test_a_tipp_a_jelenlegi_megjelenitest_ajanlja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd_a_kollazst(window, qt_app)

        uzenet = _keres(window, "collageFormatMismatchMessage").property("text")

        assert "Current display" in uzenet

    def test_a_ket_gomb_a_helyen_van(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd_a_kollazst(window, qt_app)

        assert _keres(window, "collageFormatSetAnywayButton") is not None
        assert _keres(window, "collageFormatDontSetButton") is not None
