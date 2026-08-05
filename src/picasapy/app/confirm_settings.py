"""#367: az általános megerősítő dialógus („confirm.fen") „Ne kérdezze
újra" jelölőjének perzisztenciája.

Ugyanaz a minta, mint a `window_geometry.py`-ban (#192): tiszta,
`QSettings`-példányt paraméterként kapó függvények — a beállítás-tár
forrása (valós `QSettings("PicasaPy", "PicasaPy")` vagy tesztbeli
ideiglenes fájl) a hívó dolga, itt csak az olvasás/írás logikája él.

Egy döntés-kulcs (pl. `"delete"`) a `confirm.fen` egy adott felhasználási
helyét azonosítja — amint a felhasználó egyszer bepipálja a „Don't ask
again"-t és Igennel zárja a dialógust, ugyanaz a kulcs többé nem nyit
dialógust, hanem az alapértelmezett (Igen) válasz megy vissza automatikusan.
"""

from __future__ import annotations


def confirm_setting_key(decision_key: str) -> str:
    """A `decision_key` döntéshez tartozó QSettings-kulcs."""
    return f"confirm/{decision_key}/remember"


def is_confirm_suppressed(settings, decision_key: str) -> bool:
    """True, ha a felhasználó korábban „ne kérdezze újra"-t választott
    erre a döntés-kulcsra — ilyenkor a dialógus megnyitása kimarad."""
    value = settings.value(confirm_setting_key(decision_key))
    return value in (True, "true")


def set_confirm_suppressed(settings, decision_key: str, remember: bool) -> None:
    """A „ne kérdezze újra" jelölő elmentése a döntés-kulcshoz.

    `remember=False` esetén is elmentjük (explicit "false") — így egy
    korábban bepipált, majd később kikapcsolt jelölő ténylegesen
    visszaállítja a dialógust legközelebb is."""
    settings.setValue(confirm_setting_key(decision_key), bool(remember))
