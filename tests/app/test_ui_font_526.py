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

    def test_package_data_includes_the_fonts(self) -> None:
        """A telepített csomagba is bekerüljön — enélkül a felület a
        rendszer-betűtípusra esne vissza egy `pip install` után.

        **#646: a KIMENETET nézzük, nem a mintát.** Korábban ez a teszt egy
        szó szerinti `pyproject.toml`-mintára (`"assets/fonts/*.ttf"`)
        illesztett — vagyis a szándékot mérte, nem az eredményt. A mintákat
        azóta rekurzívra cseréltük, és a betűtípusok ettől is (sőt,
        biztosabban) bekerülnek; a régi állítás mégis pirosra váltott volna.

        Azt ellenőrizzük, hogy a `package-data` mintái LEFEDIK a
        betűtípus-fájlokat. Hogy tényleg a wheelbe is bekerülnek, azt a
        `tests/test_package_data_646.py` méri — az valódi csomagot épít."""
        import fnmatch
        import tomllib

        gyoker = Path(app_module.__file__).parents[3]
        mintak = tomllib.loads(
            (gyoker / "pyproject.toml").read_text(encoding="utf-8")
        )["tool"]["setuptools"]["package-data"]["picasapy.app"]

        csomag_gyoker = Path(app_module.__file__).parent
        for fajl in (*_FONT_DIR.glob("*.ttf"), _FONT_DIR / "OFL.txt"):
            relativ = str(fajl.relative_to(csomag_gyoker))
            assert any(
                fnmatch.fnmatch(relativ, minta) for minta in mintak
            ), f"{relativ} nincs lefedve a package-data mintáival"


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
