"""Hálózati (UNC) útvonal elérhetősége — időkorláttal és gyorsítótárral (#6344, #6349).

## Miért

A tulajdonos gépén a felület 41 s-ig épült fel, futás közben pedig 11–38 s-os
fagyások jöttek; a fő szál-figyelő szerint (#6349) mindegyik egy `stat()` volt
a fő szálon: a navigáció exportcéljain (`existing_exported_folders`) és egy
`.picasa.ini` keresésén (`ini_source_path`). Az indexben `\\\\NAS\\megosztás\\…`
alakú exportmappák vannak; ha a NAS nem érhető el, a Windows MINDEN ilyen
hívásnál kivárja a hálózati időkorlátot (20–40 s).

## Hogyan

Az ellenőrzés a megosztás GYÖKERÉRE megy (`\\\\szerver\\megosztás\\`), egy
háttérszálon, `IDOKORLAT_S` határidővel. Ha addig nem válaszol, a gyökér
elérhetetlennek számít — `ELERHETETLEN_TTL_S` ideig minden további kérdés
azonnal választ kap. Ez UGYANAZ a kimenet, amit a hívó eddig is kapott
(`is_file()`/`is_dir()` hamis), csak nem 20–40 s, hanem legfeljebb fél
másodperc múlva, és utána egy percig semennyi.

Nem hálózati útvonalra (helyi lemez, Linux-csatolás) a válasz azonnali igen,
lemezművelet nélkül.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path, PureWindowsPath

#: ennyit vár a fő szál egy ismeretlen állapotú megosztás válaszára
IDOKORLAT_S = 0.5
#: ennyi ideig hisszük el, hogy egy megosztás elérhetetlen / elérhető
ELERHETETLEN_TTL_S = 60.0
ELERHETO_TTL_S = 300.0

#: a gyökér létezésének lekérdezése — modulszintű fogantyú a tesztnek (#1375)
_letezik = os.path.isdir
_ora = time.monotonic

_zar = threading.Lock()
#: gyökér → (elérhető-e, meddig érvényes)
_allapot: dict[str, tuple[bool, float]] = {}
#: gyökér → a folyamatban lévő próba vége
_folyamatban: dict[str, threading.Event] = {}


def halozati_gyoker(path: str | Path) -> str | None:
    """A UNC-útvonal megosztás-gyökere (`\\\\szerver\\megosztás\\`), kisbetűsen;
    nem hálózati útvonalra `None`."""
    szoveg = str(path)
    if not szoveg.startswith(("\\\\", "//")):
        return None
    horgony = PureWindowsPath(szoveg).anchor
    if not horgony or horgony.strip("\\/") == "":
        return None
    return horgony.lower()


def elerheto(path: str | Path, *, idokorlat_s: float | None = None) -> bool:
    """Elérhető-e az útvonal megosztása. Nem hálózati útvonalra mindig igaz.

    Legfeljebb `idokorlat_s` másodpercig blokkol (alapból `IDOKORLAT_S`),
    utána a választ a gyorsítótárból adja."""
    gyoker = halozati_gyoker(path)
    if gyoker is None:
        return True
    most = _ora()
    with _zar:
        tarolt = _allapot.get(gyoker)
        if tarolt is not None and most < tarolt[1]:
            return tarolt[0]
        esemeny = _folyamatban.get(gyoker)
        if esemeny is None:
            esemeny = threading.Event()
            _folyamatban[gyoker] = esemeny
            threading.Thread(
                target=_probald, args=(gyoker, esemeny), name="picasapy-halozati-ut",
                daemon=True,
            ).start()
    esemeny.wait(IDOKORLAT_S if idokorlat_s is None else idokorlat_s)
    with _zar:
        tarolt = _allapot.get(gyoker)
        if tarolt is not None and esemeny.is_set():
            return tarolt[0]
        # a határidőn túl: elérhetetlennek számít, amíg a próba be nem fejeződik
        _allapot[gyoker] = (False, _ora() + ELERHETETLEN_TTL_S)
        return False


def _probald(gyoker: str, esemeny: threading.Event) -> None:
    try:
        ok = bool(_letezik(gyoker))
    except OSError:
        ok = False
    with _zar:
        _allapot[gyoker] = (ok, _ora() + (ELERHETO_TTL_S if ok else ELERHETETLEN_TTL_S))
        _folyamatban.pop(gyoker, None)
    esemeny.set()


def _alaphelyzet() -> None:
    """Csak teszteknek: a gyorsítótár ürítése."""
    with _zar:
        _allapot.clear()
        _folyamatban.clear()
