"""A csomagolt gyári sablonok felsorolása (`webexport/templates/` alatt) —
a sablonválasztó UI (`WebExportDialog.qml`) ezt kérdezi le a controlleren
keresztül."""

from __future__ import annotations

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


def list_bundled_templates() -> tuple[TemplateInfo, ...]:
    """A `templates/` alatti, `index.tpl`-lel rendelkező almappák — a
    sorrend ábécé szerinti (stabil UI-lista). A `-n`/`-d` fejléc-mezők
    hiányában a mappanév/üres leírás a visszaesés."""
    if not _TEMPLATES_DIR.is_dir():
        return ()
    infos: list[TemplateInfo] = []
    for entry in sorted(_TEMPLATES_DIR.iterdir(), key=lambda p: p.name):
        index_tpl = entry / "index.tpl"
        if not entry.is_dir() or not index_tpl.is_file():
            continue
        header = parse_header(index_tpl.read_text(encoding="utf-8"))
        infos.append(
            TemplateInfo(
                id=entry.name,
                name=header.name or entry.name,
                description=header.description,
                path=entry,
            )
        )
    return tuple(infos)
