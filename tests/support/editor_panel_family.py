"""A szerkesztőpanel forrásszöveg-őreinek közös komponenscsaládja."""

from pathlib import Path


_KIEGESZITO_FAJLOK = ("EditorUndoRow.qml", "EditorTabCommonFixes.qml")


def editor_panel_family_source(qml_dir: Path) -> str:
    """A gyökér, belső EditorPanel-típusok és közvetlenül vizsgált fülek forrása."""
    fajlok = sorted(qml_dir.glob("EditorPanel*.qml"))
    for nev in _KIEGESZITO_FAJLOK:
        ut = qml_dir / nev
        if ut.is_file() and ut not in fajlok:
            fajlok.append(ut)
    return "\n".join(ut.read_text(encoding="utf-8") for ut in fajlok)
