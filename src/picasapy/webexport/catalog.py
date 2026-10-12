"""A csomagolt gyári sablonok felsorolása (`webexport/templates/` alatt) —
a sablonválasztó UI (`WebExportDialog.qml`) ezt kérdezi le a controlleren
keresztül."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .tpl_lang import parse_header

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


@dataclass(frozen=True)
class TemplateInfo:
    """Egy telepített sablon a választó-listához."""

    id: str
    name: str
    description: str
    path: Path
    #: #534: a választó előnézeti rajza (`preview.svg`), ha a sablon
    #: mellett ott van. Az eredeti `preview.jpg`-t használt; nálunk saját,
    #: sematikus SVG (paletta + csempe-stílus), nem képernyőkép.
    preview_path: Path | None = None


def user_templates_dir() -> Path:
    """A felhasználó saját sablonjainak mappája (#4611): ugyanaz a
    `XDG_DATA_HOME/picasapy` gyökér, mint a modelleké (`faces/detector.py`)."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "picasapy" / "webexport" / "templates"


def list_bundled_templates() -> tuple[TemplateInfo, ...]:
    """A `templates/` alatti, `index.tpl`-lel rendelkező almappák — a
    sorrend ábécé szerinti (stabil UI-lista). A `-n`/`-d` fejléc-mezők
    hiányában a mappanév/üres leírás a visszaesés."""
    return _templates_in(_TEMPLATES_DIR)


def list_templates(user_dir: Path | None = None) -> tuple[TemplateInfo, ...]:
    """A csomagolt gyári sablonok, UTÁNA a felhasználó saját sablonjai
    (#4611). Azonos azonosítójú saját sablon nem árnyékolja a gyárit: a
    gyári marad, a saját kimarad."""
    bundled = list_bundled_templates()
    taken = {t.id for t in bundled}
    own = tuple(
        t for t in _templates_in(user_dir or user_templates_dir()) if t.id not in taken
    )
    return bundled + own


def _templates_in(root: Path) -> tuple[TemplateInfo, ...]:
    if not root.is_dir():
        return ()
    infos: list[TemplateInfo] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        index_tpl = entry / "index.tpl"
        if not entry.is_dir() or not index_tpl.is_file():
            continue
        header = parse_header(index_tpl.read_text(encoding="utf-8"))
        preview = entry / "preview.svg"
        infos.append(
            TemplateInfo(
                id=entry.name,
                name=header.name or entry.name,
                description=header.description,
                path=entry,
                preview_path=preview if preview.is_file() else None,
            )
        )
    return tuple(infos)
