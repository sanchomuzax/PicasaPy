"""E-mail parancs-összeállítás — tiszta függvények, `subprocess`/hálózat
nélkül (ld. a csomag docstringje)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

# #350 (OptionsTabEmail.qml, "Multiple/Single photo size" csúszka, 0..4):
# a Picasa eredeti mérete-választója öt fokozatú volt, konkrét pixelérték
# nélkül dokumentálva — ez egy jóhiszemű, olvasható közelítés (ugyanaz az
# elv, mint `export.exporter._QUALITY_PRESETS`-nél). Az utolsó fokozat
# (`None`) = eredeti méret, nincs átméretezés.
EMAIL_SIZE_PRESETS: tuple[int | None, ...] = (640, 800, 1024, 1600, None)


def resolve_email_max_dimension(size_index: int) -> int | None:
    """A csúszka indexéből (0..4) a leghosszabb oldal képpontban;
    `None` = eredeti méret. Érvénytelen indexnél `ValueError`."""
    if not 0 <= size_index < len(EMAIL_SIZE_PRESETS):
        raise ValueError(f"Érvénytelen méret-index: {size_index}")
    return EMAIL_SIZE_PRESETS[size_index]


def build_xdg_email_argv(
    subject: str, body: str, attachments: list[Path] | tuple[Path, ...] = ()
) -> list[str]:
    """Az `xdg-email` parancssor összeállítása (argv-lista, `subprocess`-nek
    közvetlenül átadható — nincs shell-idézés, ezért injektálás-biztos).
    Üres `subject`/`body` kihagyva a parancsból (az `xdg-email` a hiányzó
    kapcsolót a levelezőprogram saját alapértékére hagyja)."""
    argv = ["xdg-email", "--utf8"]
    if subject:
        argv += ["--subject", subject]
    if body:
        argv += ["--body", body]
    for attachment in attachments:
        argv += ["--attach", str(attachment)]
    return argv


def build_mailto_url(subject: str, body: str) -> str:
    """`mailto:` visszaesés, ha nincs `xdg-email` — csatolmány nélkül (a
    `mailto:` séma ezt nem támogatja biztonságosan egyetlen platformon
    sem), a tárgy/szöveg URL-kódolva."""
    params = []
    if subject:
        params.append(f"subject={quote(subject)}")
    if body:
        params.append(f"body={quote(body)}")
    query = "&".join(params)
    return f"mailto:?{query}" if query else "mailto:"
