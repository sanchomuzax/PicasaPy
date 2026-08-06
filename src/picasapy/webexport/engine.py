"""A `.tpl` sablon teljes futtatása: a `tpl_lang` nyelvi motor + a
`context` változó-táblák + az `images` képgenerálás összefésülése.

Bemenet: egy `AlbumExportData` (a kiválasztott mappa/album fényképeivel,
már legenerált bélyegkép/nagyméretű képpel — ld. `images.py`), egy sablon-
könyvtár (`index.tpl` a gyökerében) és egy célkönyvtár. A kimenet a
célkönyvtárba írt HTML/XML fájlok + másolt statikus erőforrások."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .context import (
    AlbumExportData,
    WebExportSettings,
    album_variables,
    command_variables,
    image_loop_variables,
    target_page_variables,
)
from .tpl_lang import (
    Command,
    CopyCommand,
    DefineCommand,
    IncludeCommand,
    LoopCommand,
    TargetLoopCommand,
    TplSyntaxError,
    parse_tpl,
    render,
)


@dataclass(frozen=True)
class WebExportReport:
    """A teljes webexport-futás eredménye."""

    output_files: tuple[Path, ...]
    warnings: tuple[str, ...] = ()


class TemplateNotFoundError(FileNotFoundError):
    """Hiányzó `index.tpl` vagy egy `include`/`loop`/`targetloop` által
    hivatkozott fájl a sablonkönyvtárban."""


def run_tpl(
    tpl_path: Path,
    template_dir: Path,
    target_dir: Path,
    variables: dict[str, str],
    album: AlbumExportData,
    warnings: list[str],
    generated_files: list[Path],
) -> None:
    """Egyetlen `.tpl` fájl végrehajtása a kapott (már album-változókkal
    feltöltött, MUTÁLHATÓ — a `define` ezt írja) `variables` szótárral.

    A `variables["exportFileName"]` a hívás VÉGÉN tartalmazza a kimeneti
    fájl nevét — a `targetloop` ezt olvassa ki a sorszámozott
    (`index0.html`, `index1.html`, …) cél-fájlnevek előállításához."""
    try:
        text = tpl_path.read_text(encoding="utf-8")
    except OSError as error:
        raise TemplateNotFoundError(f"sablonfájl nem olvasható: {tpl_path}") from error
    try:
        commands = parse_tpl(text)
    except TplSyntaxError as error:
        raise TplSyntaxError(f"{tpl_path.name}: {error}") from error

    output = _OutputBuffer()
    for command in commands:
        _run_command(
            command, template_dir, target_dir, variables, album, output, warnings,
            generated_files,
        )

    target_name = variables.get("exportFileName") or "index.html"
    target_path = target_dir / target_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(output.text, encoding="utf-8")
    generated_files.append(target_path)


class _OutputBuffer:
    """A jelenleg épülő kimeneti fájl tartalma — a `.tpl` parancsok sorban
    ide fűzik hozzá a beillesztett/hurkolt tartalmat."""

    def __init__(self) -> None:
        self.text = ""

    def append(self, text: str) -> None:
        self.text += text


def _run_command(
    command: Command,
    template_dir: Path,
    target_dir: Path,
    variables: dict[str, str],
    album: AlbumExportData,
    output: _OutputBuffer,
    warnings: list[str],
    generated_files: list[Path],
) -> None:
    if isinstance(command, DefineCommand):
        # "Csak az utolsó define érvényes" (2.3.) — a dict-be írás ezt
        # automatikusan biztosítja.
        variables[command.name] = command.value
        return
    if isinstance(command, IncludeCommand):
        output.append(_render_include(template_dir, command.file_name, variables))
        return
    if isinstance(command, LoopCommand):
        _run_loop(command, template_dir, variables, album, output)
        return
    if isinstance(command, TargetLoopCommand):
        _run_targetloop(
            command, template_dir, target_dir, variables, album, output, warnings,
            generated_files,
        )
        return
    if isinstance(command, CopyCommand):
        _run_copy(command, template_dir, target_dir)
        return
    raise TplSyntaxError(f"nem kezelt parancstípus: {command!r}")  # pragma: no cover — védőháló


def _render_include(template_dir: Path, file_name: str, variables: dict[str, str]) -> str:
    path = template_dir / file_name
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise TemplateNotFoundError(f"include-fájl nem található: {path}") from error
    return render(text, variables)


def _run_loop(
    command: LoopCommand,
    template_dir: Path,
    variables: dict[str, str],
    album: AlbumExportData,
    output: _OutputBuffer,
) -> None:
    for index in range(len(album.photos)):
        loop_vars = {**variables, **image_loop_variables(album.photos, index)}
        output.append(_render_include(template_dir, command.per_image_file, loop_vars))


def _run_targetloop(
    command: TargetLoopCommand,
    template_dir: Path,
    target_dir: Path,
    variables: dict[str, str],
    album: AlbumExportData,
    output: _OutputBuffer,
    warnings: list[str],
    generated_files: list[Path],
) -> None:
    """Képenként külön fájlt exportál (`index0.html`, `index1.html`, …, a
    tartalmazó oldal `exportFileName`-je alapján), és a tartalmazó oldalba
    `targetIncludeFile`-t illeszti be `<%targetPath%>`-tal.

    A cél-fájlnevek előre, EGYBEN generálódnak (nem képenként), hogy a
    `nextTarget`/`prevTarget`/`firstTarget`/`lastTarget` (2.4.) helyesen
    töltődjön minden cél-oldalon — ehhez ismerni kell a TELJES sorozatot,
    nem csak az aktuális elemet."""
    referrer = variables.get("exportFileName") or "index.html"
    stem, _dot, suffix = referrer.rpartition(".")
    if not stem:
        stem, suffix = referrer, "html"
    target_names = tuple(f"{stem}{i}.{suffix}" for i in range(len(album.photos)))

    for index in range(len(album.photos)):
        target_vars = {
            **variables,
            **image_loop_variables(album.photos, index),
            **target_page_variables(target_names, index, referrer),
            "exportFileName": target_names[index],
        }
        target_tpl_path = template_dir / command.target_template_file
        run_tpl(
            target_tpl_path, template_dir, target_dir, target_vars, album, warnings,
            generated_files,
        )
        include_vars = {**target_vars, "targetPath": target_names[index]}
        output.append(
            _render_include(template_dir, command.target_include_file, include_vars)
        )


def _run_copy(command: CopyCommand, template_dir: Path, target_dir: Path) -> None:
    # a Windows-stílusú záró backslash (2.3.: "záró backslash kötelező a
    # könyvtárspecifikációnál") mindkét irányból elfogadva — Linuxon a
    # forrás-sablonok is gyakran ezzel a jelöléssel érkeznek
    source_name = command.source.rstrip("\\/")
    source = template_dir / source_name
    dest_name = (command.destination or command.source).rstrip("\\/")
    destination = target_dir / PurePosixPath(dest_name.replace("\\", "/"))
    if not source.exists():
        raise TemplateNotFoundError(f"copy forrás nem található: {source}")
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def run_web_export(
    template_dir: Path,
    target_dir: Path,
    album: AlbumExportData,
    settings: WebExportSettings | None = None,
) -> WebExportReport:
    """A teljes webexport: `template_dir/index.tpl` futtatása `target_dir`-be.

    `album.photos`-nak MÁR tartalmaznia kell a legenerált bélyegkép/
    nagyméretű kép útvonalait (ld. `images.prepare_photo_exports`) — ez a
    függvény nem generál képet, csak a `.tpl`-t futtatja le."""
    settings = settings or WebExportSettings()
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    variables = {**command_variables(settings), **album_variables(album)}
    warnings: list[str] = []
    generated_files: list[Path] = []
    index_tpl = Path(template_dir) / "index.tpl"
    run_tpl(
        index_tpl, Path(template_dir), target_dir, variables, album, warnings,
        generated_files,
    )
    return WebExportReport(output_files=tuple(generated_files), warnings=tuple(warnings))
