"""A »Rejtett mappák« jelszava: Picasa-kompatibilis ÉS modern alak (#1637).

## Mit tárol az EREDETI — mérve a binárisból

A windowsos Picasa a jelszó **hex-kódolt MD5**-ét teszi el:

| lépés | cím |
|---|---|
| a jelszó-beállító ág | `0x005eb910` |
| **MD5** — mind a négy init-konstans | `0x00ab3640` (`0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476`) |
| 16 bájt → 32 kisbetűs hex | `0x00a4d420`, ábécé `0x00cd8f5c` = `"0123456789abcdef"` |
| tárolás | `0x005ebc52`, a `state` / `info` kulcs alá |

⚠️ **Sózatlan MD5.** Mai mércével gyenge: azonos jelszó azonos lenyomatot ad
(szivárványtábla), és az MD5 gyors, tehát a nyers erő olcsó.

## Miért van MÉGIS benne — a tulajdonos döntése (2026-09-03)

> „A régi kompatibilitás maradjon meg, és legyen egy modern változat is,
> plusz feature-ként."

Ezért **két** alak él egymás mellett:

- **Picasa-kompatibilis**: a windowsos Picasában beállított jelszó nálunk is
  nyit, és fordítva;
- **modern**: sózott PBKDF2-HMAC-SHA256, felismerhető előtaggal. Ezt a
  windowsos Picasa NEM tudja megnyitni — a felületnek ezt ki kell mondania.

Az **ellenőrzés mindkettőt elfogadja**, hogy az átállás fokozatos lehessen, és
egy régi jelszó ne zárja ki a felhasználót.

## ⚠️ Amit ez a modul NEM véd

A rejtett mappák a lemezen **változatlanul ott vannak**. A jelszó a PicasaPy
felületén belüli megjelenítést kapuzza, nem a fájlokat. A felület ezt mondja
ki; ez a modul csak a lenyomatot kezeli.

## Nyitott kérdés

A Picasa MD5-je a jelszó **bájtjaira** megy (`0x00a4cdd0` NUL-ig számol
hosszt). Hogy a nem ASCII jelszót milyen kódolással adja át, **nincs mérve** —
itt UTF-8-cal számolunk. ASCII jelszónál a kettő azonos; ékezetesnél a
kompatibilitás nem igazolt.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re

#: A modern alak előtagja. Szándékosan NEM 32 hex jegy, hogy a windowsos
#: Picasa összehasonlítása biztosan ne találjon egyezést.
MODERN_ELOTAG = "picasapy-pbkdf2-sha256$"

#: A PBKDF2 körszáma. MÉRVE a fejlesztői gépen (RPi5, 2026-09-03):
#: 100k → 29 ms · 200k → 58 ms · 400k → 115 ms · 600k → 172 ms.
#: A 400 000 az OWASP mai ajánlásának nagyságrendjében van, és a
#: felhasználó számára még észrevehetetlen egy jelszó-bekérésnél.
MODERN_KOROK = 400_000

#: A só hossza bájtban.
SO_HOSSZ = 16

_PICASA_ALAK = re.compile(r"\A[0-9a-f]{32}\Z")


def picasa_lenyomat(jelszo: str) -> str:
    """A jelszó Picasa-kompatibilis lenyomata: hex-kódolt MD5.

    Args:
        jelszo: a felhasználó által beírt jelszó.

    Returns:
        32 karakteres kisbetűs hex sztring — bitre az, amit az eredeti tárol.
    """
    return hashlib.md5(jelszo.encode("utf-8"), usedforsecurity=False).hexdigest()


def modern_lenyomat(jelszo: str, *, so: bytes | None = None) -> str:
    """A jelszó modern, SÓZOTT lenyomata (PBKDF2-HMAC-SHA256).

    Args:
        jelszo: a felhasználó által beírt jelszó.
        so: csak tesztekhez; alapból friss véletlen só.

    Returns:
        `picasapy-pbkdf2-sha256$<körszám>$<só>$<lenyomat>` alakú sztring.
    """
    so_bajtok = os.urandom(SO_HOSSZ) if so is None else so
    nyers = hashlib.pbkdf2_hmac(
        "sha256", jelszo.encode("utf-8"), so_bajtok, MODERN_KOROK
    )
    return (
        f"{MODERN_ELOTAG}{MODERN_KOROK}$"
        f"{base64.b64encode(so_bajtok).decode('ascii')}$"
        f"{base64.b64encode(nyers).decode('ascii')}"
    )


def modern_alak_e(tarolt: str) -> bool:
    """Igaz, ha a tárolt érték a modern (sózott) alak."""
    return tarolt.startswith(MODERN_ELOTAG)


def picasa_alak_e(tarolt: str) -> bool:
    """Igaz, ha a tárolt érték a Picasa-kompatibilis alak (32 kisbetűs hex)."""
    return bool(_PICASA_ALAK.match(tarolt))


def egyezik(tarolt: str, jelszo: str) -> bool:
    """A megadott jelszó nyitja-e a tárolt lenyomatot — MINDKÉT alakra.

    Args:
        tarolt: a `.picasa.ini`-ből vagy az indexből olvasott érték.
        jelszo: a most beírt jelszó.

    Returns:
        `True`, ha egyezik. Üres vagy értelmezhetetlen tárolt értékre `False`
        — „nincs jelszó" nem azt jelenti, hogy bármi jó; azt a hívónak kell
        eldöntenie, hogy egyáltalán kér-e jelszót.
    """
    if not tarolt:
        return False
    if modern_alak_e(tarolt):
        return _modern_egyezik(tarolt, jelszo)
    if picasa_alak_e(tarolt):
        return hmac.compare_digest(tarolt, picasa_lenyomat(jelszo))
    return False


def _modern_egyezik(tarolt: str, jelszo: str) -> bool:
    darabok = tarolt[len(MODERN_ELOTAG) :].split("$")
    if len(darabok) != 3:
        return False
    korok_szoveg, so_b64, lenyomat_b64 = darabok
    try:
        korok = int(korok_szoveg)
        so = base64.b64decode(so_b64, validate=True)
        vart = base64.b64decode(lenyomat_b64, validate=True)
    except (ValueError, TypeError):
        return False
    if korok < 1 or not so or not vart:
        return False
    nyers = hashlib.pbkdf2_hmac("sha256", jelszo.encode("utf-8"), so, korok)
    return hmac.compare_digest(nyers, vart)
