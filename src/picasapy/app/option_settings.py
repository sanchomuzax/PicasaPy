"""Az Opciók 15 tartós beállítása (#6067)."""

from __future__ import annotations

from collections.abc import Mapping

OPTION_SETTING_KEYS = (
    "import/autoexclude",
    "library/fileTypes/bmp",
    "library/fileTypes/psd",
    "library/fileTypes/tiff",
    "library/fileTypes/webp",
    "library/fileTypes/png",
    "library/fileTypes/gif",
    "library/fileTypes/movies",
    "printing/printerQuality",
    "printing/resamplerQuality",
    "printing/proxyPreview",
    "faces/automaticDetection",
    "faces/suggestionsEnabled",
    "faces/suggestStep",
    "faces/clusterStep2",
)

_FILETYPE_GROUPS = ("bmp", "psd", "tiff", "webp", "png", "gif", "movies")


def current_option_settings(
    import_source_controller,
    library_controller,
    print_controller,
    face_scan_controller,
) -> dict[str, bool | int]:
    """Az induláskor ténylegesen feloldott Opció-értékeket adja vissza."""
    values: dict[str, bool | int] = {
        "import/autoexclude": import_source_controller.autoExclude,
    }
    values.update(
        {
            f"library/fileTypes/{group}": library_controller.fileTypeEnabled(group)
            for group in _FILETYPE_GROUPS
        }
    )
    values.update(
        {
            "printing/printerQuality": print_controller.printerQuality(),
            "printing/resamplerQuality": print_controller.printResamplerQuality(),
            "printing/proxyPreview": print_controller.printProxyPreview(),
            "faces/automaticDetection": face_scan_controller.automaticDetectionEnabled(),
            "faces/suggestionsEnabled": face_scan_controller.suggestionsEnabled(),
            "faces/suggestStep": face_scan_controller.suggestionThreshold(),
            # Ez a getter a régi lépcsőértéket is átvezeti az új kulcsra,
            # így induláskor a felületen használt értéket mentjük el.
            "faces/clusterStep2": face_scan_controller.clusterThreshold(),
        }
    )
    return values


def _ellenorizd_a_kulcsokat(values: Mapping[str, object]) -> None:
    missing = set(OPTION_SETTING_KEYS) - values.keys()
    if missing:
        raise ValueError(f"Hiányzó Opció-beállítások: {', '.join(sorted(missing))}")


def persist_missing_option_settings(settings, values: Mapping[str, object]) -> None:
    """Csak a hiányzó kulcsokhoz rögzíti a feloldott, aktuális értéket."""
    _ellenorizd_a_kulcsokat(values)
    changed = False
    for key in OPTION_SETTING_KEYS:
        if not settings.contains(key):
            settings.setValue(key, values[key])
            changed = True
    if changed:
        settings.sync()


def initialize_option_settings(
    settings,
    *,
    import_source_controller,
    library_controller,
    print_controller,
    face_scan_controller,
) -> None:
    """Induláskor a vezérlők által feloldott hiányzó értékeket rögzíti."""
    persist_missing_option_settings(
        settings,
        current_option_settings(
            import_source_controller,
            library_controller,
            print_controller,
            face_scan_controller,
        ),
    )


def save_all_option_settings(settings, values: Mapping[str, object]) -> None:
    """Az Opciók elfogadásakor mind a 15 kulcsot kiírja."""
    _ellenorizd_a_kulcsokat(values)
    for key in OPTION_SETTING_KEYS:
        settings.setValue(key, values[key])
    settings.sync()
