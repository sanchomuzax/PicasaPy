"""QSettings-tárolás a könyvtár fájltípus-csoportjaihoz (#4447)."""

from __future__ import annotations

from picasapy.scanner.filetypes import DEFAULT_ENABLED_FILETYPES, FILETYPE_GROUPS

SETTING_PREFIX = "library/fileTypes"


def _bool_value(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def file_type_enabled(settings, group: str) -> bool:
    """A csoport QSettings-értéke; hiányzó/hibás értéknél a scanner alapja."""
    if group not in DEFAULT_ENABLED_FILETYPES:
        if group not in FILETYPE_GROUPS:
            return False
    key = f"{SETTING_PREFIX}/{group}"
    default = group in DEFAULT_ENABLED_FILETYPES
    value = settings.value(key, default)
    return _bool_value(value, default)


def set_file_type_enabled(settings, group: str, enabled: bool) -> None:
    """Egy ismert formátumcsoport tárolása QSettings-be."""
    if group not in DEFAULT_ENABLED_FILETYPES:
        return
    settings.setValue(f"{SETTING_PREFIX}/{group}", bool(enabled))


def enabled_filetypes(settings) -> frozenset[str] | None:
    """A scannernek átadható választás; teljes készletnél nincs szűrő."""
    enabled = frozenset(
        group for group in FILETYPE_GROUPS if file_type_enabled(settings, group)
    )
    return None if enabled == frozenset(FILETYPE_GROUPS) else enabled
