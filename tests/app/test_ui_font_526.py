"""#526: a felület betűtípusa — csomagolt Open Sans, MÉRÉSSEL választva.

Az eredeti Picasa a kereskedelmi Praxis családot használta, ezért
helyettesítő kell. A választás nem ízlés kérdése volt: a tulajdonos két
Picasa-képernyőképéről leolvasott tíz magyar felirat képpont-szélességét
vetettük össze az öt jelölttel (ld. `application._install_ui_font`
megjegyzését a számokkal).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app.application as app_module

_FONT_DIR = Path(app_module.__file__).parent / "assets" / "fonts"


class TestBundledFontFiles:
    @pytest.mark.parametrize("name", app_module._UI_FONT_FILES)
    def test_font_file_is_packaged(self, name: str) -> None:
        assert (_FONT_DIR / name).is_file(), f"hiányzik a csomagolt {name}"

    def test_license_is_packaged(self) -> None:
        """Az OFL 1.1 megköveteli a licencszöveg mellékelését."""
        license_file = _FONT_DIR / "OFL.txt"
        assert license_file.is_file()
        text = license_file.read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE" in text.upper()

    def test_the_fonts_reach_the_installed_package(self) -> None:
        """A telepített csomagba is bekerüljön — enélkül a felület a
        rendszer-betűtípusra esne vissza egy `pip install` után.

        #651: ez az állítás korábban a `pyproject.toml` SZÖVEGÉT
        ellenőrizte (`'"assets/fonts/*.ttf"' in pyproject`), vagyis a
        deklarációt, nem az eredményt. Két baja volt: a tételes
        mintalista megszűnésekor akkor is elbukott, amikor a betűtípusok
        rendben bekerültek (#646), és fordítva — egy meglévő minta mellett
        is zöld maradt volna, ha a fájl közben eltűnik. Most a
        csomagleltárt kérdezi, a tényleges ellenőrzés pedig a CI
        `package` jobjában fut, a FELÉPÍTETT wheelen.
        """
        import sys

        sys.path.insert(
            0, str(Path(__file__).resolve().parents[2] / "scripts")
        )
        from check_package_contents import (
            is_intentionally_excluded,
            source_data_files,
        )

        inventory = source_data_files()
        expected = [
            f"picasapy/app/assets/fonts/{name}"
            for name in (*app_module._UI_FONT_FILES, "OFL.txt")
        ]

        for name in expected:
            assert name in inventory, f"{name} nincs a csomagleltárban"
            assert is_intentionally_excluded(name) is None, (
                f"{name} kivételként van jelölve — a felület a "
                "rendszer-betűtípusra esne vissza telepítve"
            )


class TestFontRegistration:
    def test_family_is_registered_and_applied(self, qt_app) -> None:
        from PySide6.QtGui import QFontDatabase

        app_module._install_ui_font(qt_app)
        assert app_module._UI_FONT_FAMILY in QFontDatabase.families()
        assert qt_app.font().family() == app_module._UI_FONT_FAMILY

    def test_missing_files_fall_back_silently(self, qt_app, monkeypatch) -> None:
        """Csonka telepítésnél némán a rendszer betűtípusánál maradunk —
        a felület ettől még használható."""
        monkeypatch.setattr(app_module, "_UI_FONT_FILES", ("nincs-ilyen.ttf",))
        before = qt_app.font().family()
        app_module._install_ui_font(qt_app)
        assert qt_app.font().family() == before
