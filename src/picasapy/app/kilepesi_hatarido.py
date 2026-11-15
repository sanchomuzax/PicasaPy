"""Kilépési határidő (#6945): a rendezett leállás nem tarthatja vissza a
folyamatot korlátlanul.

A kilépés (`app.exec()` utáni lánc) háttérmunkára és szálakra vár: a
szerkesztő, az induláskori karbantartás és a folyamat-szintű bevárás 2-2 mp-ig,
a mappa-figyelő szálai akár 30 mp-ig, az átnevező szálakra pedig a
`controller.shutdown()` szándékosan KORLÁTLANUL (hogy az objektumok ne
semmisüljenek meg futó átnevezés mellett). Ha ezek egyike elakad, a program az
eseményhurok UTÁN fagy le, ablak nélkül, és csak kívülről lehet megölni.

Az őrszál az `aboutToQuit`-tól számolja a határidőt. Ha a folyamat addig nem ér
véget, a naplóba kerül, hol áll a fő szál és mely háttérmunkák futnak, a
beállítások lemezre mennek, és a program kényszerítve kilép. A `.picasa.ini` és
az indexírás ezt kibírja: az ini-írás atomikus (`ioutil.write_atomic`: ideiglenes
fájl + csere), az SQLite pedig tranzakciónként commitol.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import traceback
from collections.abc import Callable

_log = logging.getLogger(__name__)

#: Az `aboutToQuit`-tól számított határidő. A rendezett lánc időkorlátos
#: várakozásai (3 x 2 mp) belefutnak; ami ennél tovább tart, az elakadt.
KILEPESI_HATARIDO_S = 8.0
#: A kényszerített kilépés kódja: a felhasználó a kilépést kérte, ez sikeres kilépés.
KENYSZERITETT_KILEPESI_KOD = 0
#: A beállítások utolsó mentésére az őrszál legfeljebb ennyit vár.
_MENTES_IDOKORLAT_S = 1.0
#: Az őrszál naplójába kerülő veremkép mélysége (főszál / többi szál).
_FO_SZAL_VEREM_MELYSEG = 30
_TOBBI_SZAL_VEREM_MELYSEG = 4

_ZAR = threading.Lock()
_orszem: threading.Thread | None = None
#: A várakozás megszakítója: éles futásban sosem kap jelet, a tesztek ezzel
#: állítják le a hosszú határidőre indított őrszálat.
_leallitas_jelzo = threading.Event()
_os_exit = os._exit


def _platform() -> str:
    """A futó platform fogantyúja (a tesztek ezt cserélik, nem a `sys.platform`-ot)."""
    return sys.platform


def _kernel32():
    """A Windows kernel32 fogantyúja (a tesztek ezt cserélik, nem a `ctypes.windll`-t)."""
    import ctypes

    return ctypes.windll.kernel32


def _azonnali_kilepes(kod: int) -> None:
    """Kilépés a bontás és (Windowson) a DLL-leválasztás nélkül.

    A Windowson az `ExitProcess` minden betöltött DLL-t leválaszt, és ez
    lefagyhat; a `TerminateProcess` ezt kihagyja."""
    if _platform() == "win32":
        kernel32 = _kernel32()
        kernel32.TerminateProcess(kernel32.GetCurrentProcess(), kod)
    _os_exit(kod)


#: A kényszerített kilépés fogantyúja: a tesztek ezt cserélik.
_kilep: Callable[[int], None] = _azonnali_kilepes


def _beallitasok_mentese() -> None:
    """A függő beállítások lemezre írása.

    Az azonos fájlra mutató `QSettings`-példányok közös állapotot tartanak, ezért
    egy új példány `sync()`-je az összes függő módosítást kiírja."""
    from PySide6.QtCore import QSettings

    QSettings("PicasaPy", "PicasaPy").sync()


def _vedett(feladat: Callable[[], None], leiras: str) -> None:
    try:
        feladat()
    except Exception:  # noqa: BLE001 (a kilépést a mentés hibája nem akaszthatja meg)
        _log.exception("%s nem sikerült", leiras)


def _mentes_idokorlattal() -> None:
    """A mentés külön szálon, korlátozott várakozással: egy beragadt zár se
    akadályozhassa a kilépést."""
    szal = threading.Thread(
        target=_vedett,
        args=(_beallitasok_mentese, "A beállítások mentése kilépéskor"),
        name="picasapy-kilepesi-mentes",
        daemon=True,
    )
    szal.start()
    szal.join(_MENTES_IDOKORLAT_S)


def _veremkepek() -> str:
    """A fő szál és a többi élő szál helye: ebből látszik, mi tartotta vissza a kilépést."""
    keretek = sys._current_frames()
    fo_azonosito = threading.main_thread().ident
    sorok: list[str] = []
    fo_keret = keretek.get(fo_azonosito)
    if fo_keret is not None:
        sorok.append("A fő szál itt áll:")
        sorok.extend(
            "".join(traceback.format_stack(fo_keret, limit=_FO_SZAL_VEREM_MELYSEG))
            .rstrip()
            .splitlines()
        )
    sajat = threading.current_thread().ident
    for szal in threading.enumerate():
        if szal.ident in (fo_azonosito, sajat) or szal.ident not in keretek:
            continue
        sorok.append(f"Szál {szal.name}:")
        sorok.extend(
            "".join(
                traceback.format_stack(
                    keretek[szal.ident], limit=_TOBBI_SZAL_VEREM_MELYSEG
                )
            )
            .rstrip()
            .splitlines()
        )
    return "\n".join(sorok)


def _futo_hattermunkak() -> str:
    from .worker_thread import running_background_workers

    nevek = running_background_workers()
    return ", ".join(nevek) if nevek else "nincs nyilvántartott"


def _kenyszeritsd_a_kilepest() -> None:
    """Napló, mentés, majd a folyamat azonnali vége."""
    try:
        _log.error(
            "A rendezett leállás a határidőn belül nem fejeződött be: "
            "kényszerített kilépés. Futó háttérmunkák: %s\n%s",
            _futo_hattermunkak(),
            _veremkepek(),
        )
    except Exception:  # noqa: BLE001 (a naplózás hibája sem tarthatja vissza a kilépést)
        pass
    _mentes_idokorlattal()
    _kilep(KENYSZERITETT_KILEPESI_KOD)


def _orszem_szala(hatarido_s: float) -> None:
    if _leallitas_jelzo.wait(hatarido_s):
        return
    _kenyszeritsd_a_kilepest()


def inditsd_a_hatarido_orzot(
    hatarido_s: float = KILEPESI_HATARIDO_S,
) -> threading.Thread:
    """Elindítja az őrszálat, és a függő beállításokat rögtön lemezre írja.

    Az őrszál indul előbb: egy elakadó mentés a hívó szálon se akaszthassa meg.
    Idempotens: az első hívás indítja a szálat, a többi azt adja vissza."""
    global _orszem
    with _ZAR:
        if _orszem is not None:
            return _orszem
        szal = threading.Thread(
            target=_orszem_szala,
            args=(hatarido_s,),
            name="picasapy-kilepesi-hatarido",
            daemon=True,
        )
        _orszem = szal
        szal.start()
    _vedett(_beallitasok_mentese, "A beállítások mentése kilépéskor")
    return szal


def figyeld_a_kilepest(app, hatarido_s: float = KILEPESI_HATARIDO_S) -> None:
    """Az `aboutToQuit`-ra köti az őrszálat.

    Elsőként kell bekötni (a vezérlők regisztrálása ELŐTT): a többi
    `aboutToQuit`-kezelő is elakadhat, és a Qt a bekötés sorrendjében hívja őket."""
    app.aboutToQuit.connect(lambda: inditsd_a_hatarido_orzot(hatarido_s))
