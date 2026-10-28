"""Kompatibilitási hidak a régi `people_controller` modul patch-célpontjaihoz."""

from pathlib import Path

from picasapy.ini import IniConflictError, IniSaveError


WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)


def load_ini(ini_path: Path):
    """A régi modul `load_document` neve marad a beolvasás patch-célpontja."""
    from . import people_controller

    return people_controller._load_ini(ini_path)


def generate_contact_id() -> str:
    """A régi modul `generate_contact_id` patch-célpontját hívja."""
    from . import people_controller

    return people_controller.generate_contact_id()


def update_document(*args, **kwargs):
    """A régi modul `update_document` patch-célpontját hívja."""
    from . import people_controller

    return people_controller.update_document(*args, **kwargs)
