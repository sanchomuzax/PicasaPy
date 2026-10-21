"""A People-lista és a csempe javaslatainak névegyezése (#5437)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _lower(value: str) -> str:
    """Unicode kisbetűs alak, ékezet-összevonás nélkül."""
    return str(value or "").lower()


def _word_char(character: str) -> bool:
    """A bináris szókarakter-térképe: ASCII alfanumerikus, `:`, nem-ASCII."""
    return ord(character) >= 128 or character == ":" or (
        character.isascii() and character.isalnum()
    )


def _words(value: str) -> tuple[str, ...]:
    parts: list[str] = []
    current: list[str] = []
    for character in _lower(value):
        if _word_char(character):
            current.append(character)
        elif current:
            parts.append("".join(current))
            current.clear()
    if current:
        parts.append("".join(current))
    return tuple(parts)


def match_people_name(typed: str, full_name: str) -> bool:
    """A gépelt szavak egymás után, névszó-eleji prefixként egyezzenek.

    Az első n-1 keresőszó teljesen egyezik a név megfelelő szavaival; az
    utolsó keresőszó a következő névszó eleje. Egyetlen keresőszó a név
    bármelyik szavának prefixe lehet. Üres keresés minden nevet elfogad.
    """
    query_words = _words(typed)
    if not query_words:
        return True
    name_words = _words(full_name)
    if len(name_words) < len(query_words):
        return False

    for start in range(len(name_words) - len(query_words) + 1):
        if any(
            query_words[index] != name_words[start + index]
            for index in range(len(query_words) - 1)
        ):
            continue
        if name_words[start + len(query_words) - 1].startswith(query_words[-1]):
            return True
    return False


def _ascii_lower(value: str) -> str:
    """Az eredeti rendező összehasonlításához csak ASCII-ban hajt kisbetűt."""
    return str(value or "").translate(_ASCII_LOWER)


def filter_and_sort_people(
    entries: Iterable[Mapping], typed: str
) -> list[Mapping]:
    """Szűr és bináris kulcssorrenddel rendez, stabilan és másolás nélkül."""
    query = str(typed or "").strip()
    query_lower = _lower(query)
    query_words = _words(query)
    matching = [
        entry
        for entry in entries
        if match_people_name(query, str(entry.get("name", "")))
    ]

    if not query_words:
        return sorted(
            matching,
            key=lambda entry: _ascii_lower(str(entry.get("name", ""))),
        )

    def sort_key(entry: Mapping) -> tuple[int, int, int, str]:
        name = str(entry.get("name", ""))
        is_new = bool(entry.get("isNew"))
        return (
            0 if is_new else 1,
            0 if _lower(name).startswith(query_lower) else 1,
            0 if match_people_name(query, name) else 1,
            _ascii_lower(name),
        )

    return sorted(matching, key=sort_key)
