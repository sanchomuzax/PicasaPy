"""E-mail parancs-összeállítás — tiszta függvények, `subprocess`/hálózat
nélkül (ld. a csomag docstringje)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

#: #2020: a méret-csúszka NYOLC fokozata, MÉRVE — nem becslés.
#:
#: Forrás: a tulajdonos futó Picasa 3-a (`research/#2020-email/`, a csúszka
#: végigléptetve), és a dekompiláció, amely szerint a
#: `Preferences\EmailExportSize` **képpont-értéket** tárol, nem indexet
#: (`0x00743030`), és az alapértéke **480** (`0x1e0`) három független
#: helyen (`0x006e1756`, `0x006e3f2b`, `0x00743094`).
#:
#: ⚠️ A #350 öt fokozata `(640, 800, 1024, 1600, None)` **becslés volt** — a
#: kód maga is kimondta. A mérés szerint a 480 (az ALAPÉRTÉK), a 160, a 320
#: és az 1200 mind hiányzott belőle, az „eredeti méret" pedig tévesen a
#: csúszka utolsó fokozata volt.
EMAIL_SIZE_STEPS: tuple[int, ...] = (160, 320, 480, 640, 800, 1024, 1200, 1600)

#: A csúszka alapfokozata — mérve, három független helyen a binárisban.
EMAIL_SIZE_DEFAULT = 480

#: A „ne méretezz át" jelzőérték. MÉRVE: a `0` az `option_useorig` ágra megy
#: (`0x0074310f`–`0x0074311a`). Az eredetiben ez **nem a csúszkán** van,
#: hanem külön vezérlőn („Egyedülálló képek mérete: Eredeti méret").
EREDETI_MERET = 0


def resolve_email_max_dimension(size_px: int) -> int | None:
    """A tárolt KÉPPONTSZÁMBÓL a leghosszabb oldal; `None` = eredeti méret.

    ⚠️ A paraméter **nem listaindex** (#2020). Az eredeti a beállítást
    képpontban tárolja, tehát a fokozatlistán kívüli érték is érvényes —
    egy másik Picasa-verzióból vagy kézzel szerkesztett beállításból
    bármi jöhet, és azt méretként kell értelmezni, nem indexként.

    Raises:
        ValueError: negatív értékre. A 0 nem hiba, hanem „eredeti méret".
    """
    if size_px < 0:
        raise ValueError(f"Érvénytelen e-mail méret: {size_px}")
    if size_px == EREDETI_MERET:
        return None
    return size_px


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
