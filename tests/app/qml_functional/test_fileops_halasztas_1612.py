"""#1612: a fájlművelet-párbeszédek halasztva épülnek — de a hibájuk NEM
veszhet el.

## Miért van erre külön őr

A `FileOpsDialogs` induláskor 571 QObjectet épített fel (a fa 4,2%-a),
holott a felhasználó a legtöbb indulásnál egyet sem nyit meg. A halasztás
viszont pontosan úgy tudna elromlani, ahogy a #2096-ban: a komponens egy
`Connections { target: fileOpsController }` blokkot tartott, és a
`fileOpsController.operationFailed` NEM csak a saját párbeszédeiből
indulhat — a **mappafa** áthelyezés/törlés útja
(`FolderPane.qml` `moveFolder` / `deleteFolder`) is ezen jelez. Halasztva,
belső hallgatóval a hibaüzenet NÉMÁN elmaradna.

Ezért a hallgatók a `Main.qml`-ben állnak, mindig, és `ensure()`-t hívnak.
Ez az őr a VALÓDI utat méri: a vezérlő jelét adja ki úgy, hogy a
párbeszédeket előtte senki nem nyitotta meg.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject


def _settle(qt_app, korok=4):
    for _ in range(korok):
        qt_app.processEvents()


def _fileops(window):
    return window.findChild(QObject, "fileOpsDialogs")


class TestIndulaskorNemEpulFel:
    def test_a_parbeszedek_INDULASKOR_nincsenek_meg(self, qml_app):
        """A nyereség forrása: egyetlen belső párbeszéd sem áll induláskor."""
        window, _controller, _engine = qml_app
        for nev in (
            "renameDialog",
            "deleteConfirmDialog",
            "batchProgressDialog",
            "fileOpsErrorDialog",
        ):
            assert window.findChild(QObject, nev) is None, (
                f"a(z) {nev} felépült induláskor — a halasztás nem hat (#1612)"
            )

    def test_a_halasztott_burok_VISZONT_megvan(self, qml_app):
        """A burok kell, különben a hívóhelyek `null`-ra futnának."""
        window, _controller, _engine = qml_app
        assert _fileops(window) is not None


class TestAMappafarolInditottMuveletHibaja:
    """A #2096 hibaosztálya: a jelzés nem a párbeszédből indul."""

    def test_az_operationFailed_MEGJELENIK_nyitas_nelkul(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        fileops = engine.rootContext().contextProperty("fileOpsController")
        fileops.operationFailed.emit("move_folder", "a cél írásvédett")
        _settle(qt_app)
        par = window.findChild(QObject, "fileOpsErrorDialog")
        assert par is not None, (
            "a hibapárbeszéd nem épült fel — a mappafáról indított művelet "
            "hibája némán elveszett (#1612)"
        )
        assert "a cél írásvédett" in str(par.property("message") or "")
        assert par.property("visible") is True

    def test_a_koteg_VEGE_is_atjut(self, qml_app, qt_app):
        _window, _controller, engine = qml_app
        fileops = engine.rootContext().contextProperty("fileOpsController")
        fileops.batchFinished.emit("copy", 5, 1, 0, "")
        _settle(qt_app)
        par = _window.findChild(QObject, "batchSummaryDialog")
        assert par is not None, "a köteg összegzője némán elmaradt (#1612)"
        assert par.property("visible") is True

    def test_a_koteg_HALADASA_is_atjut(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        fileops = engine.rootContext().contextProperty("fileOpsController")
        fileops.batchProgress.emit("move", "/cel", 2, 10, 1024.0)
        _settle(qt_app)
        par = window.findChild(QObject, "batchProgressDialog")
        assert par is not None, "a haladásjelző némán elmaradt (#1612)"


class TestANyitasiUtakElnek:
    def test_a_torles_megerositoje_MEGNYILIK(self, qml_app, qt_app):
        """Az `ensure()` valóban felépíti a párbeszédeket — nem helyfoglaló."""
        window, _controller, _engine = qml_app
        burok = _fileops(window)
        assert QMetaObject.invokeMethod(burok, "ensure"), (
            "az `ensure()` nem hívható a burkon — nem a DeferredDialog áll ott"
        )
        _settle(qt_app)
        belso = window.findChild(QObject, "deleteConfirmDialog")
        assert belso is not None, "az ensure() nem építette fel a párbeszédet"
