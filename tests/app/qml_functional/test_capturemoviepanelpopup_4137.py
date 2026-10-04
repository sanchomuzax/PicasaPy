"""#4137: a webkamerás felvétel panelje a főablakból használható és látszik.

A teszt a valódi Main.qml-t tölti be, a főablak eszköztárára kattint, majd a
kirajzolt panelt méri. A kattintási pontot és a képpontmintát is a tényleges
QML-geometriából számolja, ezért a Pi/CI ablakkeret- és betűeltérése nem
része az elvárásnak.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QTranslator, QUrl, Qt
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest


def _obj(window, name: str):
    found = window.findChild(QObject, name)
    assert found is not None, f"{name} nem található a főablak QML-fájában"
    return found


def _kattints(qt_app, window, target) -> None:
    """A vezérlő közepére küldött valódi egéresemény."""
    point = target.mapToScene(
        QPointF(target.property("width") / 2, target.property("height") / 2)
    )
    assert 0 <= point.x() < window.width()
    assert 0 <= point.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    for _ in range(12):
        qt_app.processEvents()


def _nyisd_meg_a_panelt(qt_app, window):
    button = _obj(window, "toolbarWebcamCaptureButton")
    assert not button.property("enabled"), "a vezérlő nélküli tesztablak aktív gombot mutat"
    # A fixture nem ad át médiavezérlőt. A QML elem engedélyezett állapotát a
    # tesztben felülírjuk, majd valódi egéreseménnyel járjuk be a főablaki utat.
    button.setProperty("enabled", True)
    _kattints(qt_app, window, button)
    return _obj(window, "captureMoviePanelPopup")


@pytest.fixture
def magyar_forditas(qt_app):
    import picasapy.app.application as app_module

    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(app_module._I18N_DIR))
    qt_app.installTranslator(translator)
    yield translator
    qt_app.removeTranslator(translator)


class TestCaptureMoviePanelPopup:
    def test_fenykepezogep_modra_kattintva_visszater_az_elo_kephez(
        self, magyar_forditas, qml_app, qt_app
    ):
        window, _, _ = qml_app
        _ = magyar_forditas
        popup = _nyisd_meg_a_panelt(qt_app, window)
        popup.setProperty("clipIndex", 1)
        _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/live_video"))
        assert popup.property("clipIndex") == -1

    def test_foablakbol_kattintva_megjelenik_es_kirajzolodik(
        self, magyar_forditas, qml_app, qt_app
    ):
        """A panel kimenetét üres, szöveg nélküli háttérképponton is mérjük."""
        window, _, _ = qml_app
        _ = magyar_forditas  # életben tartjuk a QML-fa lebontásáig

        original_height = window.height()
        # A program geometriájából vett alapmagasságot három külön ablakban
        # ±5 képponttal eltolva is ellenőrizzük.
        for delta in (-5, 0, 5):
            window.resize(window.width(), original_height + delta)
            qt_app.processEvents()
            assert window.height() == original_height + delta

            # Regressziós kontroll: a panel nyitása előtt a szomszédos Import
            # gomb továbbra is valódi, látható eszköztár-vezérlő.
            assert _obj(window, "toolbarImportButton").isVisible()
            button = _obj(window, "toolbarWebcamCaptureButton")
            assert button.isVisible()
            popup = _nyisd_meg_a_panelt(qt_app, window)
            assert popup.property("visible"), "a valódi főablak-kattintás nem nyitotta meg a panelt"

            surface = _obj(window, "captureMoviePanelSurface")
            image = window.grabWindow()
            assert not image.isNull(), "a főablak renderelt kimenete üres"

            # A pontot a Rectangle geometriája adja; a sarok üres felület,
            # nem felirat- vagy betűkészlet-függő terület.
            point = surface.mapToScene(
                QPointF(surface.property("width") - 8, surface.property("height") - 8)
            )
            ratio = image.devicePixelRatio()
            x, y = round(point.x() * ratio), round(point.y() * ratio)
            assert 0 <= x < image.width() and 0 <= y < image.height()
            actual = image.pixelColor(x, y)
            expected = surface.property("color")
            assert all(
                abs(a - b) <= 5
                for a, b in zip(actual.getRgb()[:3], expected.getRgb()[:3], strict=True)
            ), f"a panel üres sarkának kitöltése eltér: {actual.name()} != {expected.name()}"

            _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/done"))
            assert not popup.property("visible"), "a Kész gomb nem zárta be a panelt"
            button.setProperty("enabled", False)

    def test_a_tizenegy_spec_elem_es_a_beallitasok_valodi_kattintasa(
        self, magyar_forditas, qml_app, qt_app, record_property
    ):
        """A feliratokat és az Alkalmaz/Mégse útvonalat a főablakban mérjük."""
        window, _, _ = qml_app
        _ = magyar_forditas
        popup = _nyisd_meg_a_panelt(qt_app, window)

        expected_labels = {
            "capturemoviepanelpopup/capture": "Felvétel",
            "capturemoviepanelpopup/live_video": "Fényképezőgép",
            "capturemoviepanelpopup/video_label": "Videoklip",
            "capturemoviepanelpopup/audio_label": "Hang",
            "capturemoviepanelpopup/size_label": "Méret",
            "capturemoviepanelpopup/camchange": "Beállítások",
            "capturemoviepanelpopup/settings_apply": "Alkalmaz",
            "capturemoviepanelpopup/settings_cancel": "Mégse",
            "capturemoviepanelpopup/done": "Kész",
        }
        for name, label in expected_labels.items():
            assert _obj(window, name).property("text") == label
        for name in ("capturemoviepanelpopup/next", "capturemoviepanelpopup/prev"):
            assert _obj(window, name).isVisible()

        title = _obj(window, "captureMoviePanelTitle")
        assert title.property("text") == "Rögzítés"
        import picasapy.app.application as app_module

        panel_qml = Path(
            app_module._APP_DIR, "qml", "PicasaPy", "CaptureMoviePanelPopup.qml"
        ).read_text(encoding="utf-8")
        assert "font.pixelSize: Theme.fontSize" in panel_qml
        assert "font.pixelSize: Theme.fontSize + 2" in panel_qml
        # Csak jelentésadat: a CI-n gépenként eltérő szövegdoboz nem elvárás.
        record_property(
            "helyi_felirat_doboz_px",
            f"{title.property('width')}x{title.property('height')}",
        )
        initial_size = popup.property("selectedSize")
        _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/camchange"))
        settings = _obj(window, "capturemoviepanelpopup/settingspanel")
        assert settings.isVisible()
        size_combo = _obj(window, "capturemoviepanelpopup/outputsize")
        assert size_combo.property("count") >= 2
        size_combo.setProperty("currentIndex", (size_combo.property("currentIndex") + 1) % size_combo.property("count"))
        _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/settings_cancel"))
        assert popup.property("selectedSize") == initial_size, "a Mégse elmentette az ideiglenes méretet"

        _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/camchange"))
        size_combo = _obj(window, "capturemoviepanelpopup/outputsize")
        size_combo.setProperty("currentIndex", (size_combo.property("currentIndex") + 1) % size_combo.property("count"))
        pending_size = size_combo.property("currentText")
        _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/settings_apply"))
        assert popup.property("selectedSize") == pending_size
        _kattints(qt_app, window, _obj(window, "capturemoviepanelpopup/done"))
        assert not popup.property("visible")

    def test_filmszalag_a_kovetkezo_es_elozo_klipre_lep(
        self, magyar_forditas, qml_app, qt_app
    ):
        window, _, _ = qml_app
        _ = magyar_forditas
        popup = _nyisd_meg_a_panelt(qt_app, window)
        popup.setProperty("clips", ["elso.mp4", "masodik.mp4"])
        kovetkezo = _obj(window, "capturemoviepanelpopup/next")
        elozo = _obj(window, "capturemoviepanelpopup/prev")
        assert _obj(window, "capturevbar/moviecontrols/play") is not None
        assert _obj(window, "capturevbar/moviecontrols/pause") is not None

        assert kovetkezo.isEnabled()
        _kattints(qt_app, window, kovetkezo)
        assert popup.property("clipIndex") == 0
        _kattints(qt_app, window, kovetkezo)
        assert popup.property("clipIndex") == 1
        _kattints(qt_app, window, elozo)
        assert popup.property("clipIndex") == 0

    def test_a_media_komponens_lefordul_es_nem_indit_eszkozt(self, qml_app):
        """A QML-kötések ellenőrizhetők kamera/hangkimenet létrehozása nélkül."""
        _, _, engine = qml_app
        import picasapy.app.application as app_module

        fajl = Path(app_module._APP_DIR) / "qml" / "PicasaPy" / "CaptureMovieMedia.qml"
        komponens = QQmlComponent(engine, QUrl.fromLocalFile(str(fajl)))
        assert komponens.status() == QQmlComponent.Status.Ready, (
            komponens.errorString()
        )
