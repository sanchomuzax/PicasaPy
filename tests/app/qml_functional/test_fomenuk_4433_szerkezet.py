"""#4433: a főmenü-bejárás külön tesztfájlt kap minden felső menühöz."""

from __future__ import annotations

import ast
from pathlib import Path


_MENUNKENTI_TESZTEK = {
    "test_fomenuk_4420_view.py": ("View", "&View"),
    "test_fomenuk_4420_view_folder.py": ("View", "&View"),
    "test_fomenuk_4420_folder.py": ("Folder", "F&older"),
    "test_fomenuk_4420_picture.py": ("Picture", "&Picture"),
    "test_fomenuk_4420_edit.py": ("Edit", "&Edit"),
    "test_fomenuk_4420_tools.py": ("Tools", "&Tools"),
    "test_fomenuk_4420_tools_language.py": ("Tools", "&Tools"),
    "test_fomenuk_4420_tools_language_masodik.py": ("Tools", "&Tools"),
    "test_fomenuk_4420_create.py": ("Create", "&Create"),
    "test_fomenuk_4420_help.py": ("Help", "&Help"),
    "test_fomenuk_4420_file.py": ("File", "&File"),
}


def test_minden_fomenut_sajat_rovid_bejarasi_fajl_fed_le():
    gyoker = Path(__file__).parent
    assert {path.name for path in gyoker.glob("test_fomenuk_4420_*.py")} == set(
        _MENUNKENTI_TESZTEK
    )

    for fajlnev, vart_menu in _MENUNKENTI_TESZTEK.items():
        fa = ast.parse((gyoker / fajlnev).read_text(encoding="utf-8"))
        menu_kijelolesek = [
            csomopont
            for csomopont in fa.body
            if isinstance(csomopont, ast.Assign)
            and any(
                isinstance(cel, ast.Name) and cel.id == "MENU"
                for cel in csomopont.targets
            )
        ]
        assert len(menu_kijelolesek) == 1, (
            f"{fajlnev}: pontosan egy MENU konstans szükséges"
        )
        assert ast.literal_eval(menu_kijelolesek[0].value) == vart_menu, fajlnev
