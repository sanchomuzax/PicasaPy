"""#6067 — az Opciók alapértékei frissítésállóan kerülnek mentésre."""

from PySide6.QtCore import QSettings

from picasapy.app.option_settings import (
    OPTION_SETTING_KEYS,
    initialize_option_settings,
)


_EFFECTIVE_DEFAULTS = {
    "import/autoexclude": True,
    "library/fileTypes/bmp": True,
    "library/fileTypes/psd": True,
    "library/fileTypes/tiff": True,
    "library/fileTypes/webp": True,
    "library/fileTypes/png": True,
    "library/fileTypes/gif": True,
    "library/fileTypes/movies": True,
    "printing/printerQuality": 2,
    "printing/resamplerQuality": 5,
    "printing/proxyPreview": True,
    "faces/automaticDetection": True,
    "faces/suggestionsEnabled": True,
    "faces/suggestStep": 85,
    "faces/clusterStep2": 85,
    "updates/autoCheck": True,
}


def _settings(tmp_path):
    return QSettings(str(tmp_path / "options.ini"), QSettings.Format.IniFormat)


class _ImportController:
    autoExclude = True


class _LibraryController:
    file_types_enabled = {group: True for group in ("bmp", "psd", "tiff", "webp", "png", "gif", "movies")}

    def fileTypeEnabled(self, group):
        return self.file_types_enabled[group]


class _PrintController:
    printer_quality = 2
    resampler_quality = 5
    proxy_preview = True

    def printerQuality(self):
        return self.printer_quality

    def printResamplerQuality(self):
        return self.resampler_quality

    def printProxyPreview(self):
        return self.proxy_preview


class _FaceScanController:
    automatic_detection = True
    suggestions_enabled = True
    suggest_step = 85
    cluster_step = 85

    def automaticDetectionEnabled(self):
        return self.automatic_detection

    def suggestionsEnabled(self):
        return self.suggestions_enabled

    def suggestionThreshold(self):
        return self.suggest_step

    def clusterThreshold(self):
        return self.cluster_step


def _initialize(settings, library=None):
    initialize_option_settings(
        settings,
        import_source_controller=_ImportController(),
        library_controller=library or _LibraryController(),
        print_controller=_PrintController(),
        face_scan_controller=_FaceScanController(),
    )


def test_tiszta_profilban_indulaskor_mind_a_tizenhat_kulcs_elmentodik(tmp_path):
    settings = _settings(tmp_path)

    _initialize(settings)

    assert set(settings.allKeys()) == set(OPTION_SETTING_KEYS)
    assert {key: settings.value(key) for key in OPTION_SETTING_KEYS} == _EFFECTIVE_DEFAULTS


def test_meglevo_egyedi_erteket_es_a_korabb_mar_mentett_alaperteket_megoriz(tmp_path):
    settings = _settings(tmp_path)
    settings.setValue("library/fileTypes/png", False)
    settings.setValue("printing/printerQuality", 3)

    _initialize(settings)

    changed_defaults = _LibraryController()
    changed_defaults.file_types_enabled = dict(changed_defaults.file_types_enabled)
    changed_defaults.file_types_enabled["bmp"] = False
    changed_defaults.file_types_enabled["png"] = True
    _initialize(settings, changed_defaults)

    assert set(settings.allKeys()) == set(OPTION_SETTING_KEYS)
    assert settings.value("library/fileTypes/png") is False
    assert settings.value("printing/printerQuality") == 3
    assert settings.value("library/fileTypes/bmp") is True
