"""HTML-webexport a Picasa `.tpl` sablonnyelvével (#351).

A csomag a Picasa eredeti `web/templates/` sablonrendszerét valósítja meg
Pythonban — a nyelv teljes leírása `docs/specs/picasa-program-resources.md`
2. fejezete. A cél a **kétirányú kompatibilitás**: az eredeti (és a
közösségi) Picasa-sablonok változtatás nélkül feldolgozhatók legyenek.

Nyilvános felület:

- `tpl_lang` — a `.tpl` parancsnyelv (define/include/loop/targetloop/copy)
  és a `<%var%>`/`<%if%>` behelyettesítés motorja.
- `context` — az album-, kép-hurok- és cél-oldal-változó táblák.
- `images` — bélyegkép/nagyméretű kép generálás a meglévő export-
  infrastruktúrára (`picasapy.export`) építve.
- `engine` — a teljes sablon-futtatás (a fentiek összefésülése).
- `catalog` — a csomagolt gyári sablonok felsorolása.
"""

from __future__ import annotations

from .catalog import TemplateInfo, list_bundled_templates
from .context import AlbumExportData, PhotoExportData, WebExportSettings
from .engine import WebExportReport, run_web_export

__all__ = [
    "AlbumExportData",
    "PhotoExportData",
    "TemplateInfo",
    "WebExportSettings",
    "WebExportReport",
    "list_bundled_templates",
    "run_web_export",
]
