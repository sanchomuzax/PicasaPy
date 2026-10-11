"""#351: `WebExportDialog.qml` — önállóan betöltve, fake kontrollerrel (a
`test_qml_move_database.py` mintája). A Main.qml-be illesztés (menü-
bekötés, `webExportController` context property) az integrátoré."""

from __future__ import annotations

import pytest
from PySide6.QtCore import (
    QMetaObject,
    QObject,
    Qt,
    Signal,
    Slot,
)


class FakeWebExportController(QObject):
    webExportStarted = Signal()
    webExportProgress = Signal(int, int)
    webExportFinished = Signal(str, int)
    webExportFailed = Signal(str)

    def __init__(self):
        super().__init__()
        self.generate_calls = []
        self._templates = [
            {
                "id": "feher", "name": "Fehér",
                "description": "Fehér hátterű sablon",
                "preview": "file:///tmp/feher/preview.svg",
            },
            {"id": "masik", "name": "Másik", "description": "", "preview": ""},
        ]

    @Slot(result=list)
    def listWebExportTemplates(self):
        return self._templates

    @Slot(result=str)
    def defaultWebExportTarget(self):
        return "/tmp/Kepek/Picasa HTML exportok"

    @Slot(str, str, str, int, bool)
    def generateWebExport(
        self, target_dir, template_id, album_name, size_index, movie_full,
    ):
        self.generate_calls.append(
            (target_dir, template_id, album_name, size_index, movie_full)
        )

    #: #4610: a megőrzött választás (az eredeti `WebExportSize`/`WebExportMovie`)
    prefs = {"sizeIndex": 3, "movieFull": False}

    @Slot(result="QVariantMap")
    def webExportPrefs(self):
        return dict(self.prefs)


@pytest.fixture
def fake():
    return FakeWebExportController()


@pytest.fixture
def dialog(qt_app, fake):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("webExportController", fake)
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "WebExportDialog.qml"),
    )
    item = factory.create()
    assert item is not None, factory.errorString()
    yield item, fake, qt_app
    item.deleteLater()
    qt_app.processEvents()


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click(button):
    QMetaObject.invokeMethod(button, "clicked", Qt.ConnectionType.DirectConnection)


class TestDialogWindow:
    def test_is_a_standalone_resizable_window(self, dialog):
        window, _fake, _qt_app = dialog
        assert window.property("minimumWidth") is not None
        assert window.property("minimumWidth") >= 400

    def test_starts_hidden(self, dialog):
        window, _fake, _qt_app = dialog
        assert window.property("visible") is False

    def test_open_loads_templates_and_shows_window(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert window.property("visible") is True
        templates = window.property("templates")
        if hasattr(templates, "toVariant"):
            templates = templates.toVariant()
        assert [t["id"] for t in templates] == ["feher", "masik"]

    def test_close_button_hides_the_window(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        window.setProperty("visible", True)
        qt_app.processEvents()
        _click(_child(window, "webExportCloseButton"))
        qt_app.processEvents()
        assert window.property("visible") is False


class TestGenerateButtonEnablement:
    def test_disabled_without_target_folder(self, dialog, qt_app):
        """#534: a megnyitás ELŐRE kitölti a célmappát, ezért az üres
        állapotot itt kimondottan elő kell állítani — a szabály maga
        (üres célmappa ⇒ tiltott gomb) változatlan."""
        window, _fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        window.setProperty("targetFolder", "")
        qt_app.processEvents()
        button = _child(window, "webExportGenerateButton")
        assert button.property("enabled") is False

    def test_enabled_once_target_folder_chosen(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        window.setProperty("targetFolder", "/tmp/webexport-cel")
        qt_app.processEvents()
        button = _child(window, "webExportGenerateButton")
        assert button.property("enabled") is True


class TestStartExport:
    def test_generate_button_forwards_settings_to_controller(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        window.setProperty("targetFolder", "/tmp/webexport-cel")
        window.setProperty("albumTitle", "Nyaralás")
        qt_app.processEvents()
        _click(_child(window, "webExportGenerateButton"))
        qt_app.processEvents()
        assert len(fake.generate_calls) == 1
        target, template_id, album_name = fake.generate_calls[0][:3]
        assert target == "/tmp/webexport-cel"
        assert template_id == "feher"
        assert album_name == "Nyaralás"

    def test_started_signal_shows_progress_section(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        assert window.property("exporting") is True

    def test_progress_signal_updates_progress_bar(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        fake.webExportProgress.emit(3, 10)
        qt_app.processEvents()
        fill = _child(window, "webExportProgressFill")
        track_width = fill.parent().property("width")
        assert fill.property("width") == pytest.approx(track_width * 0.3, rel=0.05)

    def test_finished_signal_shows_result_and_hides_progress(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        fake.webExportFinished.emit("/tmp/webexport-cel", 5)
        qt_app.processEvents()
        assert window.property("exporting") is False
        result_text = _child(window, "webExportResultText")
        assert result_text.property("visible") is True

    def test_failed_signal_shows_error_and_hides_progress(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        fake.webExportFailed.emit("Nincs kijelölt kép.")
        qt_app.processEvents()
        assert window.property("exporting") is False
        error_text = _child(window, "webExportErrorText")
        assert error_text.property("visible") is True
        assert "Nincs kijelölt kép" in str(error_text.property("text"))

    def test_close_disabled_while_exporting(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        close_button = _child(window, "webExportCloseButton")
        assert close_button.property("enabled") is False


class TestAzElorekitoltottCelmappa:
    """#534: az eredetinek van alapértelmezett kimeneti mappája; nálunk a
    párbeszéd „(nincs kijelölve)" állapotban nyílt, tehát minden exportnál
    tallózni kellett — és a Generálás gomb addig tiltott volt."""

    def test_megnyitaskor_kitolt(self, dialog, qt_app):
        window, _fake, _qt_app = dialog
        assert window.property("targetFolder") == ""

        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert window.property("targetFolder") == "/tmp/Kepek/Picasa HTML exportok"

    def test_a_mar_kivalasztott_mappat_NEM_irja_felul(self, dialog, qt_app):
        window, _fake, _qt_app = dialog
        window.setProperty("targetFolder", "/sajat/hely")

        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert window.property("targetFolder") == "/sajat/hely"


class TestASablonElonezete:
    """#534: a választó előnézetet mutat (az eredetiben `preview.jpg`)."""

    def test_a_kivalasztott_sablon_rajza_latszik(self, dialog, qt_app):
        window, _fake, _qt_app = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        kep = _child(window, "webExportTemplatePreview")
        assert kep.property("visible") is True
        assert kep.property("source").toString() == "file:///tmp/feher/preview.svg"

    def test_rajz_nelkuli_sablonnal_elrejtve(self, dialog, qt_app):
        """Üres `preview` esetén ne maradjon ott egy üres képkeret."""
        window, _fake, _qt_app = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        window.setProperty("templateIndex", 1)
        qt_app.processEvents()

        assert _child(window, "webExportTemplatePreview").property("visible") is False


# -- #4610: egy méretválasztó + mozgókép-mód, valódi kattintással ----------

#: `webexport.fen` 4–8. és 12–13. sor — a felület angol forrásszövegei
FEN_MERETEK = [
    "Original Size",
    "1024 pixels (for large monitors)",
    "800 pixels (for large Web pages)",
    "640 pixels (for Web pages)",
    "320 pixels (for email)",
]
FEN_MOZGOKEP = ["First frame", "Full movie"]


def _egerkattintas(qt_app, window, elem):
    """Valódi egérkattintás az elem közepén (nem `clicked`/`activated` hívás).

    Az ablakot a hívó adja: az `elem.window()` új Python-burkot adhat a
    párbeszédre, és annak felszámolása az ablakot is törölné."""
    from PySide6.QtCore import QPointF
    from PySide6.QtTest import QTest

    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep
    )
    qt_app.processEvents()


def _legordulo_sora(qt_app, combo, index):
    """A lenyitott legördülő `index`-edik sora (a delegált elem)."""
    import time

    hatarido = time.monotonic() + 5.0
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        lista = combo.findChild(QObject, "picasaComboList")
        if lista is not None:
            for gyerek in lista.property("contentItem").childItems():
                if gyerek.property("index") == index and gyerek.property("visible"):
                    return gyerek
        time.sleep(0.02)
    raise AssertionError(f"a legördülő {index}. sora nem jelent meg")


def _valassz(qt_app, window, combo, index):
    _egerkattintas(qt_app, window, combo)
    _egerkattintas(qt_app, window, _legordulo_sora(qt_app, combo, index))


@pytest.fixture
def megnyitott(dialog, qt_app):
    window, fake, _qt = dialog
    QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
    window.setProperty("targetFolder", "/tmp/webexport-cel")
    window.setProperty("width", 520)
    window.setProperty("height", 560)
    qt_app.processEvents()
    return window, fake


class TestEgyMeretvalaszto4610:
    """Spec `picasa-menu-parancsok-viselkedes.md` 6.1: EGY `sizeradio` van
    (a nagy kép mérete), bélyegkép-választó nincs."""

    def test_nincs_kulon_belyegkep_valaszto(self, megnyitott):
        window, _fake = megnyitott
        assert window.findChild(QObject, "webExportThumbSizeBox") is None
        assert window.findChild(QObject, "webExportImageSizeBox") is None

    def test_az_ot_fogas_a_fen_szovegevel(self, megnyitott):
        window, _fake = megnyitott
        combo = _child(window, "webExportSizeBox")
        assert list(combo.property("model")) == FEN_MERETEK

    def test_alaperteke_640(self, megnyitott):
        window, _fake = megnyitott
        assert _child(window, "webExportSizeBox").property("currentIndex") == 3

    def test_mozgokep_mod_ket_eleme_es_alaperteke(self, megnyitott):
        window, _fake = megnyitott
        combo = _child(window, "webExportMovieBox")
        assert list(combo.property("model")) == FEN_MOZGOKEP
        assert combo.property("currentIndex") == 0

    def test_a_megorzott_valasztasbol_indul(self, dialog, qt_app):
        window, fake, _qt = dialog
        fake.prefs = {"sizeIndex": 1, "movieFull": True}
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert _child(window, "webExportSizeBox").property("currentIndex") == 1
        assert _child(window, "webExportMovieBox").property("currentIndex") == 1

    def test_kattintott_valasztas_jut_a_vezerlohoz(self, megnyitott, qt_app):
        window, fake = megnyitott
        window.show()
        qt_app.processEvents()

        _valassz(qt_app, window, _child(window, "webExportSizeBox"), 4)
        _valassz(qt_app, window, _child(window, "webExportMovieBox"), 1)
        assert _child(window, "webExportSizeBox").property("currentIndex") == 4
        assert _child(window, "webExportMovieBox").property("currentIndex") == 1

        _egerkattintas(qt_app, window, _child(window, "webExportGenerateButton"))
        assert len(fake.generate_calls) == 1
        _cel, _sablon, _cim, size_index, movie_full = fake.generate_calls[0][:5]
        assert size_index == 4
        assert movie_full is True


class TestNincsArnyekJelolonegyzet4849:
    """#4849: a `webexport.fen`-ben nincs árnyék-jelölőnégyzet — az
    árnyékolást a sablon adja (`shadowedThumbnails`/`shadowedImages`)."""

    def test_nincs_jelolonegyzet_a_parbeszedben(self, megnyitott):
        window, _fake = megnyitott
        assert window.findChild(QObject, "webExportShadowThumbsCheck") is None
        assert window.findChild(QObject, "webExportShadowImagesCheck") is None

    def test_nincs_checkbox_tipusu_vezerlo_arnyek_felirattal(self, megnyitott):
        window, _fake = megnyitott
        from PySide6.QtQuick import QQuickItem

        for elem in window.findChildren(QQuickItem):
            felirat = str(elem.property("text") or "")
            assert "hadow" not in felirat

    def test_a_megmaradt_vezerlok_kattintasra_mukodnek(self, megnyitott, qt_app):
        window, fake = megnyitott
        window.show()
        qt_app.processEvents()
        _valassz(qt_app, window, _child(window, "webExportSizeBox"), 2)
        _egerkattintas(qt_app, window, _child(window, "webExportGenerateButton"))
        assert fake.generate_calls[-1][3:] == (2, False)
