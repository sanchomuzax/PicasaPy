"""Sor-alapú, byte-pontos .picasa.ini dokumentummodell.

A round-trip elv miatt nem a stdlib configparser-t használjuk: minden sort
(kulcs-érték, komment, üres, értelmezhetetlen) változatlanul megőrzünk, a
sorvégjelekkel (CRLF/LF) együtt. Minden objektum immutábilis; a módosító
műveletek új dokumentumot adnak vissza.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

_SPECIAL_NAMES = frozenset({"Picasa", "Contacts", "Contacts2", "encoding", "photoid"})
ALBUM_SECTION_PREFIX = ".album:"


@dataclass(frozen=True)
class Line:
    """Egy nyers sor: szöveg + sorvégjel ('' a fájl utolsó, lezáratlan soránál)."""

    text: str
    ending: str


@dataclass(frozen=True)
class KeyValueLine(Line):
    key: str
    value: str


def _make_kv_line(key: str, value: str, ending: str) -> KeyValueLine:
    return KeyValueLine(text=f"{key}={value}", ending=ending, key=key, value=value)


@dataclass(frozen=True)
class Section:
    header: Line
    name: str
    lines: tuple[Line, ...]

    @property
    def is_special(self) -> bool:
        """Nem fájlbejegyzés: [Picasa], [Contacts*], [.album:token] stb."""
        return self.name in _SPECIAL_NAMES or self.name.startswith(
            ALBUM_SECTION_PREFIX
        )

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (line.key, line.value)
            for line in self.lines
            if isinstance(line, KeyValueLine)
        )

    def get(self, key: str) -> str | None:
        """Az első egyező kulcs értéke, kis-nagybetű-tűrően."""
        folded = key.casefold()
        for line in self.lines:
            if isinstance(line, KeyValueLine) and line.key.casefold() == folded:
                return line.value
        return None


@dataclass(frozen=True)
class IniDocument:
    preamble: tuple[Line, ...]
    sections: tuple[Section, ...]
    encoding: str = "utf-8"
    bom: bool = False

    @property
    def newline(self) -> str:
        """A dokumentum domináns sorvégjele (új sorok ezt öröklik)."""
        for line in self._all_lines():
            if line.ending:
                return line.ending
        return "\n"

    def _all_lines(self) -> tuple[Line, ...]:
        lines = list(self.preamble)
        for section in self.sections:
            lines.append(section.header)
            lines.extend(section.lines)
        return tuple(lines)

    def section(self, name: str) -> Section | None:
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def file_sections(self) -> tuple[Section, ...]:
        return tuple(s for s in self.sections if not s.is_special)

    def serialize(self) -> str:
        return "".join(line.text + line.ending for line in self._all_lines())

    def with_value(self, section_name: str, key: str, value: str) -> IniDocument:
        """Új dokumentum a beállított kulccsal; hiányzó szekciót létrehozza."""
        target = self.section(section_name)
        if target is None:
            return self._with_new_section(section_name, key, value)
        updated = _section_with_value(target, key, value, self.newline)
        sections = tuple(
            updated if section is target else section for section in self.sections
        )
        return replace(self, sections=sections)

    def with_removed(self, section_name: str, key: str) -> IniDocument:
        """Új dokumentum az első egyező kulcs-sor nélkül (kis-nagybetű-tűrő).

        Ha a szekció vagy a kulcs nincs meg, változatlanul önmagát adja
        vissza — minden más sor bitre pontosan megmarad (round-trip elv).
        """
        target = self.section(section_name)
        if target is None:
            return self
        folded = key.casefold()
        lines = list(target.lines)
        for index, line in enumerate(lines):
            if isinstance(line, KeyValueLine) and line.key.casefold() == folded:
                del lines[index]
                if _section_is_empty(lines):
                    sections = tuple(
                        section for section in self.sections
                        if section is not target
                    )
                else:
                    updated = replace(target, lines=tuple(lines))
                    sections = tuple(
                        updated if section is target else section
                        for section in self.sections
                    )
                return replace(self, sections=sections)
        return self

    def with_renamed_section(self, old_name: str, new_name: str) -> IniDocument:
        """Szekció átnevezése (fájl-átnevezéskor, #15): a tartalom (kulcsok,
        ismeretlen/komment sorok) bitre pontosan megmarad, csak a
        `[szekciónév]` fejléc cserélődik.

        Ha `old_name` nincs a dokumentumban, változatlanul önmagát adja
        vissza (nincs mit átnevezni — round-trip elv).

        Raises:
            ValueError: Ha `new_name` már foglalt szekció — ütköző
                átnevezést nem hajtunk végre csendben (adatvesztés lenne).
        """
        target = self.section(old_name)
        if target is None:
            return self
        if self.section(new_name) is not None:
            raise ValueError(f"A cél szekció már létezik: {new_name!r}")
        renamed = replace(
            target, name=new_name, header=replace(target.header, text=f"[{new_name}]")
        )
        sections = tuple(
            renamed if section is target else section for section in self.sections
        )
        return replace(self, sections=sections)

    def with_section(self, section: Section) -> IniDocument:
        """Egy teljes `Section` beszúrása/cseréje (pl. fotó áthelyezésekor a
        forrás szekció átvitele a cél dokumentumba, #15) — a tartalom
        (kulcsok, komment/ismeretlen sorok) bitre pontosan megmarad.

        Ha már van `section.name` nevű szekció, azt lecseréli; különben a
        végére fűzi."""
        existing = self.section(section.name)
        if existing is not None:
            sections = tuple(
                section if s is existing else s for s in self.sections
            )
            return replace(self, sections=sections)
        return replace(
            self,
            sections=_with_closed_last_line(self.sections, self.newline) + (section,),
        )

    def without_section(self, name: str) -> IniDocument:
        """A teljes szekció eltávolítása (pl. áthelyezéskor a forrás
        iniből, #15). Ha a szekció nincs meg, változatlanul önmagát adja
        vissza."""
        target = self.section(name)
        if target is None:
            return self
        sections = tuple(section for section in self.sections if section is not target)
        return replace(self, sections=sections)

    def _with_new_section(self, name: str, key: str, value: str) -> IniDocument:
        newline = self.newline
        header = Line(text=f"[{name}]", ending=newline)
        section = Section(
            header=header, name=name, lines=(_make_kv_line(key, value, newline),)
        )
        return replace(
            self,
            sections=_with_closed_last_line(self.sections, newline) + (section,),
        )


def _section_with_value(
    section: Section, key: str, value: str, newline: str
) -> Section:
    folded = key.casefold()
    lines = list(section.lines)
    for index, line in enumerate(lines):
        if isinstance(line, KeyValueLine) and line.key.casefold() == folded:
            lines[index] = _make_kv_line(line.key, value, line.ending)
            return replace(section, lines=tuple(lines))
    insert_at = _last_kv_index(lines) + 1
    if insert_at > 0:
        if not lines[insert_at - 1].ending:
            lines[insert_at - 1] = replace(lines[insert_at - 1], ending=newline)
    elif not section.header.ending:
        # A fejléc sorvégjel nélkül állt (fájl vége): le kell zárni,
        # különben az új kulcs a fejlécsorra ragadna.
        section = replace(section, header=replace(section.header, ending=newline))
    lines.insert(insert_at, _make_kv_line(key, value, newline))
    return replace(section, lines=tuple(lines))


def _section_is_empty(lines: list[Line]) -> bool:
    """Se kulcs, se megőrzendő (nem üres) verbatim sor nem maradt."""
    return all(
        not isinstance(line, KeyValueLine) and not line.text.strip()
        for line in lines
    )


def _last_kv_index(lines: list[Line]) -> int:
    """Az utolsó kulcs-érték sor indexe; -1, ha nincs ilyen."""
    for index in range(len(lines) - 1, -1, -1):
        if isinstance(lines[index], KeyValueLine):
            return index
    return -1


def _with_closed_last_line(
    sections: tuple[Section, ...], newline: str
) -> tuple[Section, ...]:
    """Új szekció hozzáfűzése előtt az utolsó sor kapjon sorvégjelet."""
    if not sections:
        return sections
    last = sections[-1]
    if not last.lines:
        if last.header.ending:
            return sections
        header = replace(last.header, ending=newline)
        return sections[:-1] + (replace(last, header=header),)
    if last.lines[-1].ending:
        return sections
    closed = last.lines[:-1] + (replace(last.lines[-1], ending=newline),)
    return sections[:-1] + (replace(last, lines=closed),)


def parse_document(text: str) -> IniDocument:
    preamble: list[Line] = []
    sections: list[Section] = []
    current_lines: list[Line] | None = None

    def _close_section() -> None:
        nonlocal current_lines
        if current_lines is not None:
            header, *rest = current_lines
            sections[-1] = replace(sections[-1], lines=tuple(rest))
        current_lines = None

    for raw in _split_lines(text):
        line = _parse_line(raw)
        name = _section_name(line.text)
        if name is not None:
            _close_section()
            sections.append(Section(header=line, name=name, lines=()))
            current_lines = [line]
        elif current_lines is not None:
            current_lines.append(line)
        else:
            preamble.append(line)
    _close_section()
    return IniDocument(preamble=tuple(preamble), sections=tuple(sections))


def _split_lines(text: str) -> list[str]:
    """A szöveg sorokra tördelése — KIZÁRÓLAG '\\n' mentén.

    A `str.splitlines()`-t szándékosan NEM használjuk: az Unicode
    sorhatár-kódpontokat is (pl. U+0085 NEL, U+2028 LINE SEPARATOR)
    sortörésnek veszi. Régi (CP125x) `.picasa.ini` fájloknál — ha
    latin-1-ként dekódolva a "…" bájtja (0x85) U+0085-re képződik le —
    ez hamis szekciótörést/csonka mezőt okozna (#133), miközben a
    `_parse_line` csak '\\n'/'\\r\\n' sorvégjelet ismer fel; a kettőnek
    összhangban kell lennie.
    """
    if not text:
        return []
    pieces = text.split("\n")
    lines = [piece + "\n" for piece in pieces[:-1]]
    if pieces[-1]:
        lines.append(pieces[-1])
    return lines


def _parse_line(raw: str) -> Line:
    if raw.endswith("\r\n"):
        text, ending = raw[:-2], "\r\n"
    elif raw.endswith("\n"):
        text, ending = raw[:-1], "\n"
    else:
        text, ending = raw, ""
    if text.startswith(("#", ";")) or "=" not in text:
        return Line(text=text, ending=ending)
    key, _, value = text.partition("=")
    return KeyValueLine(text=text, ending=ending, key=key, value=value)


def _section_name(text: str) -> str | None:
    stripped = text.strip()
    if stripped.startswith("[") and stripped.endswith("]") and len(stripped) > 2:
        return stripped[1:-1]
    return None
