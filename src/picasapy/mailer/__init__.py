"""E-mail küldés (#32, RÉSZLEGES kör): kijelölt képek elküldése az
alapértelmezett levelezővel.

A PicasaPy-nak nincs saját SMTP-kliense (ld. `OptionsTabEmail.qml` korábbi
docstringje) — a rendszer levelezőjét indítjuk el, csatolmányokkal, a
freedesktop.org `xdg-email` segédprogramján át (ha elérhető); ha nem, egy
`mailto:` URL a visszaesés (csatolmány nélkül — a `mailto:` séma nem
támogat fájlcsatolást egyetlen platformon sem biztonságosan). Ez a csomag a
subprocess-hívástól/tényleges küldéstől független, determinisztikus
parancs-összeállítást tartalmazza, hogy önmagában, mockolás nélkül
tesztelhető legyen."""

from .command import (
    EMAIL_SIZE_PRESETS,
    build_mailto_url,
    build_xdg_email_argv,
    resolve_email_max_dimension,
)

__all__ = [
    "EMAIL_SIZE_PRESETS",
    "build_mailto_url",
    "build_xdg_email_argv",
    "resolve_email_max_dimension",
]
