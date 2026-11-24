"""A kikapcsolt fájltípusok kizárása az indexből számolt darabszámokból (#7414).

A kikapcsolt típus sorai az indexben MEGMARADNAK (a visszakapcsolás
újraolvasás nélkül működjön), ezért minden, az indexből SQL-lel számolt
darabszámnak ki kell hagynia őket, különben a bal hasáb másik számot mutat,
mint a rács.
"""

from __future__ import annotations

from collections.abc import Collection

from picasapy.scanner.filetypes import disabled_extensions


def enabled_type_clause(
    enabled_filetypes: Collection[str] | None, alias: str = "p"
) -> tuple[str, list[str]]:
    """` AND NOT (...)` SQL-részlet és paraméterei; nincs szűrő esetén üres.

    Az `alias` a `photos` tábla álneve a hívó lekérdezésében."""
    extensions = disabled_extensions(enabled_filetypes)
    if not extensions:
        return "", []
    feltetel = " OR ".join(f"{alias}.name LIKE ?" for _ in extensions)
    return f" AND NOT ({feltetel})", [f"%{extension}" for extension in extensions]
