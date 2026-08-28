"""#1654: `Súgó ▸ Tesztüzem` és `Súgó ▸ Napló elküldése` — élő QML-fa.

A projekt szabálya: a VEZÉRLŐRE kattints, ne a metódust hívd. A menütételt
ezért a kattintás MINDKÉT lépésével működtetjük (`toggle()` **és**
`triggered`) — a puszta jelzés-kibocsátás nem járja be azt az utat, amin a
`checkable` + kötött `checked` rádió-csapda (#1468) jelentkezik.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, QPoint, Q_ARG, Qt
from PySide6.QtTest import QTest

from picasapy.app import tesztuzem_controller as modul


def _tetel(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a QML-fában"
    return obj


def _kattints(tetel):
    """A valódi kattintás mindkét lépése, a QML sorrendjében.

    ⚠️ A `checkable: true` tétel a kattintáskor ELŐBB billenti át a
    `checked`-et, és csak UTÁNA emittál `triggered`-et. Aki csak a
    `triggered`-et bocsátja ki, egy törött menü fölött is zöldet mér."""
    QMetaObject.invokeMethod(tetel, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)


class TestATesztuzemMenupont:
    def test_a_menupont_LETEZIK_es_kapcsolhato(self, qml_app):
        window, _controller, _engine = qml_app
        tetel = _tetel(window, "menuHelpTesztuzem")
        assert tetel.property("checkable") is True
        assert tetel.property("enabled") is True

    def test_alapbol_nincs_pipa(self, qml_app):
        window, controller, _engine = qml_app
        assert controller.tesztuzemEnabled is False
        assert _tetel(window, "menuHelpTesztuzem").property("checked") is False

    def test_a_KATTINTAS_bekapcsolja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        tetel = _tetel(window, "menuHelpTesztuzem")
        try:
            _kattints(tetel)
            qt_app.processEvents()
            assert controller.tesztuzemEnabled is True
            assert tetel.property("checked") is True
        finally:
            controller.setTesztuzemEnabled(False)

    def test_ketszeri_kattintas_utan_a_pipa_KOVETI_az_allapotot(
        self, qml_app, qt_app
    ):
        """⚠️ A #1468 rádió-csapdájának ellenőrzése ezen a tételen.

        Ugyanarra a tételre kétszer kattintva a `checked`-nek a vezérlő
        állapotát kell mutatnia — nem szabad „elszakadnia" a kötéstől."""
        window, controller, _engine = qml_app
        tetel = _tetel(window, "menuHelpTesztuzem")
        try:
            for _kor in range(3):
                _kattints(tetel)
                qt_app.processEvents()
                assert tetel.property("checked") is controller.tesztuzemEnabled, (
                    "a pipa és a vezérlő állapota elvált egymástól"
                )
        finally:
            controller.setTesztuzemEnabled(False)


class TestANaploElkuldeseCsakTesztuzemben:
    """A jegy: „`Súgó ▸ Napló elküldése` (csak tesztüzemben látszik)"."""

    def test_tesztuzemen_KIVUL_nem_latszik(self, qml_app):
        """⚠️ A `visible` a QQuickItemnél az EFFEKTÍV láthatóság — csukott
        menünél mindig hamis, tehát önmagában semmit nem bizonyítana. A
        kötés a tétel saját `tesztuzemAktiv` tulajdonságán mérhető, a
        LÁTHATÓ következménye (nulla magasság) pedig mellette."""
        window, controller, _engine = qml_app
        tetel = _tetel(window, "menuHelpSendLog")
        assert controller.tesztuzemEnabled is False
        assert tetel.property("tesztuzemAktiv") is False
        assert tetel.property("visible") is False

    def test_tesztuzemen_kivul_nem_is_FOGLAL_helyet(self, qml_app):
        """A rejtett menütétel magassága nulla — különben a Súgó menüben
        egy üres sáv tátongana."""
        window, _controller, _engine = qml_app
        assert _tetel(window, "menuHelpSendLog").property("height") == 0

    def test_tesztuzemben_LATSZIK_es_helyet_is_kap(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        tetel = _tetel(window, "menuHelpSendLog")
        try:
            controller.setTesztuzemEnabled(True)
            qt_app.processEvents()
            assert tetel.property("tesztuzemAktiv") is True
            assert tetel.property("height") > 0, (
                "a tétel bekapcsolt tesztüzemben sem kap helyet a menüben"
            )
        finally:
            controller.setTesztuzemEnabled(False)
            qt_app.processEvents()
            assert tetel.property("height") == 0

    def test_a_tetel_KATTINTASA_a_vezerlot_hivja(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        """Nem a metódust hívjuk: a menütételt működtetjük, és a vezérlő
        MEGFIGYELHETŐ kimenetét (az üzenetét) nézzük."""
        window, controller, _engine = qml_app
        monkeypatch.setattr(modul, "_naplo_mappa", lambda: tmp_path / "ures")
        uzenetek = []
        controller.tesztuzemUzenet.connect(uzenetek.append)
        try:
            controller.setTesztuzemEnabled(True)
            uzenetek.clear()
            qt_app.processEvents()
            QMetaObject.invokeMethod(
                _tetel(window, "menuHelpSendLog"),
                "triggered",
                Qt.ConnectionType.DirectConnection,
            )
            qt_app.processEvents()
            assert uzenetek, "a menütétel nem ér el a vezérlőig"
            assert "napló" in uzenetek[0].casefold()
        finally:
            controller.setTesztuzemEnabled(False)


class TestLathatoAllapot:
    """„A tesztüzem legyen LÁTHATÓ állapot: a felhasználó ne felejtse
    bekapcsolva észrevétlenül." — a menüben ülő pipa ehhez kevés, mert a
    menüt ki kell nyitni hozzá."""

    def test_a_jelzes_alapbol_rejtve_van(self, qml_app):
        window, _controller, _engine = qml_app
        assert _tetel(window, "menuBarTesztuzemBadge").property("visible") is False

    def test_bekapcsolva_a_MENUSAVBAN_latszik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        try:
            controller.setTesztuzemEnabled(True)
            qt_app.processEvents()
            jelzes = _tetel(window, "menuBarTesztuzemBadge")
            assert jelzes.property("visible") is True
            assert jelzes.property("text")
        finally:
            controller.setTesztuzemEnabled(False)

    def test_a_jelzesre_VALODI_EGERREL_kattintva_kikapcsol(self, qml_app, qt_app):
        """⚠️ A projekt szabálya: új vezérlőre VALÓDI egéreseményt kell
        küldeni. A `setTesztuzemEnabled(false)` közvetlen hívása akkor is
        zöld lenne, ha a felirat takarásban, nulla méretű vagy letiltott."""
        window, controller, _engine = qml_app
        controller.setTesztuzemEnabled(True)
        qt_app.processEvents()
        jelzes = _tetel(window, "menuBarTesztuzemBadge")
        kozep = jelzes.mapToScene(jelzes.boundingRect().center())

        # #1676: a windows-lábon a kattintás némán elment a semmibe — a
        # `QTest.mouseClick` nem jelez hibát, ha a pont az ablakon KÍVÜL
        # esik, csak a lenti "nem kapcsolt ki" állítás bukik, beszédes ok
        # nélkül. Ez az ellenőrzés a pontot MÉRI a kattintás előtt, hogy a
        # hiba a valódi okára (geometria) mutasson, ne a tünetére.
        assert (
            0 <= kozep.x() <= window.width() and 0 <= kozep.y() <= window.height()
        ), (
            "PicasaMenuBar.qml:57 — a TESZTÜZEM felirat középpontja "
            f"({kozep.x():.1f}, {kozep.y():.1f}) az ablakon kívül esik "
            f"(ablak: {window.width()}x{window.height()}, felirat "
            f"x={jelzes.property('x'):.1f} szélesség="
            f"{jelzes.property('width'):.1f})"
        )

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(kozep.x()), round(kozep.y())),
        )
        qt_app.processEvents()

        assert controller.tesztuzemEnabled is False, (
            "a menüsáv TESZTÜZEM feliratára kattintva nem kapcsolt ki a mód"
        )
        assert jelzes.property("visible") is False


class TestAVisszajelzesEsATartalek:
    """A Main.qml bekötése: a felhasználó LÁTJA, mi történt.

    ⚠️ A natív fájlválasztó offscreen platformon nem nyitható meg és nem
    szimulálható kattintással, ezért a „Mentés másként…" hatását — a
    #1633 mintája szerint — a párbeszéd saját `mentsdIde()` függvényén át
    mérjük, nem a rendszerválasztón keresztül."""

    def test_a_tajekoztatas_a_kozos_savban_jelenik_meg(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.tesztuzemUzenet.emit("Tesztüzem bekapcsolva. Próbaszöveg.")
        qt_app.processEvents()
        assert (
            "Próbaszöveg"
            in _tetel(window, "errorBannerText").property("text")
        )

    def test_az_elerhetetlen_megosztas_uzenete_is_latszik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.tesztuzemMentesMaskentKert.emit("A közös mappa nem érhető el.")
        qt_app.processEvents()
        assert (
            "nem érhető el"
            in _tetel(window, "errorBannerText").property("text")
        )

    def test_a_tartalek_parbeszed_LETEZIK_es_a_vezerlot_hivja(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, controller, _engine = qml_app
        naplok = tmp_path / "perf"
        naplok.mkdir()
        (naplok / "indulas-20260827-204105.txt").write_text(
            "PicasaPy — próbanapló\n", encoding="utf-8"
        )
        monkeypatch.setattr(modul, "_naplo_mappa", lambda: naplok)
        monkeypatch.setattr(modul, "_megosztas_gyokere", lambda: None)
        controller.tesztuzemNaploAtadasa()  # ez teszi el a napló szövegét

        parbeszed = _tetel(window, "tesztuzemNaploDialog")
        cel = tmp_path / "mentve.txt"
        QMetaObject.invokeMethod(
            parbeszed,
            "mentsdIde",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", str(cel)),
        )
        qt_app.processEvents()

        assert cel.read_text(encoding="utf-8") == "PicasaPy — próbanapló\n"
