"""A paritás-felvevő lépésfajtáinak végrehajtása a főablakon (#6845).

Minden lépés VALÓDI egér- vagy billentyűesemény: a bélyegkép-delegátum
`thumbMouseArea` területére, a bal hasáb `folderRowMouse` sorára, a megnyitott
menü tételére kattintunk. A tétel `triggered` jelét vagy a slotját soha nem
hívjuk, mert akkor a kattintás útja (hit-test, takarás, tiltott tétel)
mérés nélkül maradna.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import paritas_qt as qt
else:
    from . import paritas_qt as qt

from PySide6.QtCore import QObject, Qt

_MENU_NEVEK_LISTAJA_MAX = 40
_MENU_MEGNYILAS_MP = 0.3
_FOMENU_MEGNYILAS_MP = 1.5
_FOMENU_KISERLET = 2
_MODOSITO_GOMB = {
    "ctrl": Qt.KeyboardModifier.ControlModifier,
    "shift": Qt.KeyboardModifier.ShiftModifier,
}


@dataclass(frozen=True)
class Kontextus:
    """A futó alkalmazás elemei, amelyeken a lépések dolgoznak."""

    alkalmazas: Any
    ablak: Any
    vezerlo: Any
    konyvtar: Path
    munka: Path


def vegrehajt(kon: Kontextus, lepes: Any) -> None:
    """Egy ellenőrzött lépést végrehajt; `FuttatasiHiba`, ha a felület nem engedi."""
    kezelo = _KEZELOK[lepes.fajta]
    kezelo(kon, lepes)


# --- rács ---------------------------------------------------------------------


def _delegalt_index(elem: Any) -> int | None:
    szulo = elem
    while szulo is not None and szulo.property("index") is None:
        szulo = szulo.parentItem()
    return None if szulo is None else int(szulo.property("index"))


def _belyegkep_terulet(kon: Kontextus, index: int) -> Any:
    ismert: set[int] = set()
    for elem in qt.vizualis_bejaras(kon.ablak.contentItem()):
        if elem.objectName() != "thumbMouseArea":
            continue
        sor = _delegalt_index(elem)
        if sor == index:
            return elem
        if sor is not None:
            ismert.add(sor)
    if not ismert:
        raise qt.FuttatasiHiba(
            f"A {index}. rácsindexű bélyegkép nem található: a rácson nincs bélyegkép "
            "(a thumbMouseArea elemek hiányoznak)."
        )
    raise qt.FuttatasiHiba(
        f"A {index}. rácsindexű bélyegkép nem található: a példányosított "
        f"indexek {min(ismert)} és {max(ismert)} között vannak."
    )


def _racs_kattintas(
    kon: Kontextus, index: int, gomb: Qt.MouseButton, modosito: Qt.KeyboardModifier
) -> None:
    terulet = _belyegkep_terulet(kon, index)
    qt.lathatova_tesz(kon.alkalmazas, terulet)
    qt.kattint(kon.alkalmazas, kon.ablak, terulet, gomb, modosito)


def _kijelol(kon: Kontextus, lepes: Any) -> None:
    _racs_kattintas(
        kon, lepes.racsindex, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    )


def _kijelol_mod(kon: Kontextus, lepes: Any) -> None:
    _racs_kattintas(
        kon,
        lepes.racsindex,
        Qt.MouseButton.LeftButton,
        _MODOSITO_GOMB[lepes.modosito],
    )


def _jobbklikk(kon: Kontextus, lepes: Any) -> None:
    _racs_kattintas(
        kon,
        lepes.racsindex,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
    )
    _megnyilt_menu(kon, "photoContextMenu", f"a(z) {lepes.racsindex}. kép jobb klikkje")


def _megnyilt_menu(kon: Kontextus, menunev: str, mi: str) -> None:
    menu = kon.ablak.findChild(QObject, menunev)
    if menu is None:
        raise qt.FuttatasiHiba(f"{mi} után a {menunev} menü objektuma nem létezik.")
    if not qt.var_feltetelre(
        kon.alkalmazas,
        lambda: bool(menu.property("visible")),
        qt.KATTINTAS_HATARIDO_MP,
    ):
        raise qt.FuttatasiHiba(f"{mi} nem nyitotta meg a {menunev} menüt.")


# --- bal hasáb ------------------------------------------------------------------


def _mappasorok(kon: Kontextus) -> list[tuple[str, Any]]:
    sorok = []
    for elem in qt.vizualis_bejaras(kon.ablak.contentItem()):
        if (
            elem.objectName() == "folderRowMouse"
            and qt.lathato_e(elem)
            and str(elem.property("folderPath"))
        ):
            sorok.append((str(elem.property("folderPath")), elem))
    return sorok


def _jobbklikk_mappa(kon: Kontextus, lepes: Any) -> None:
    sorok = _mappasorok(kon)
    for ut, elem in sorok:
        if Path(ut).name == lepes.mappanev or ut == lepes.mappanev:
            qt.lathatova_tesz(kon.alkalmazas, elem)
            qt.kattint(kon.alkalmazas, kon.ablak, elem, Qt.MouseButton.RightButton)
            _megnyilt_menu(
                kon, "folderContextMenu", f"a(z) {lepes.mappanev} mappa jobb klikkje"
            )
            return
    nevek = ", ".join(sorted({Path(ut).name for ut, _elem in sorok})) or "(egy sem)"
    raise qt.FuttatasiHiba(
        f"Nincs {lepes.mappanev!r} nevű látható mappasor a bal hasábon. Látható mappák: {nevek}."
    )


# --- menük ----------------------------------------------------------------------


def _normalizalt_cim(cim: object) -> str:
    return str(cim).replace("&", "").strip().lower()


def _menusor_elem(kon: Kontextus, menu: str) -> Any:
    keresett = {_normalizalt_cim(menu)}
    objektum = kon.ablak.findChild(QObject, menu)
    if objektum is not None and objektum.property("title") is not None:
        keresett.add(_normalizalt_cim(objektum.property("title")))
    elemek = [
        elem
        for elem in qt.vizualis_bejaras(kon.ablak.contentItem())
        if "MenuBarItem" in elem.metaObject().className() and qt.lathato_e(elem)
    ]
    for elem in elemek:
        if _normalizalt_cim(elem.property("text")) in keresett:
            return elem
    cimek = ", ".join(_normalizalt_cim(elem.property("text")) for elem in elemek)
    raise qt.FuttatasiHiba(
        f"Nincs {menu!r} nevű főmenü a menüsoron. Látható főmenük: {cimek or '(egy sem)'}."
    )


def _popup_cimmel(kon: Kontextus, cim: str) -> Any:
    """A megadott című popup-objektum (menü); `None`, ha nem található."""
    for objektum in kon.ablak.findChildren(QObject):
        if (
            "Menu" in objektum.metaObject().className()
            and objektum.property("opened") is not None
            and objektum.property("title") is not None
            and _normalizalt_cim(objektum.property("title")) == cim
        ):
            return objektum
    return None


def _fomenu_megnyitasa(kon: Kontextus, menu: str) -> None:
    """A menüsor elemére kattint, és megvárja a menü megnyílását.

    Terhelt gépen az első kattintás elveszhet (az ablak aktiválása késik), ezért
    egyszer újrapróbáljuk; ha a menü így sem nyílik meg, az hiba."""
    sor = _menusor_elem(kon, menu)
    objektum = _popup_cimmel(kon, _normalizalt_cim(sor.property("text")))
    for _kiserlet in range(_FOMENU_KISERLET):
        kon.ablak.requestActivate()
        qt.kattint(kon.alkalmazas, kon.ablak, sor)
        if objektum is None:
            qt.pergetes(kon.alkalmazas, _MENU_MEGNYILAS_MP)
            return
        if qt.var_feltetelre(
            kon.alkalmazas,
            lambda: bool(objektum.property("visible")),
            _FOMENU_MEGNYILAS_MP,
        ):
            return
    raise qt.FuttatasiHiba(f"A(z) {menu!r} főmenü nem nyílt meg a menüsor kattintására.")


def _almenu_sora(kon: Kontextus, almenu: Any) -> tuple[Any, Any] | None:
    cim = almenu.property("title")
    for ablak in qt.lathato_ablakok(kon.ablak):
        for elem in qt.vizualis_bejaras(ablak.contentItem()):
            if (
                "MenuItem" in elem.metaObject().className()
                and elem.property("text") == cim
                and qt.lathato_e(elem)
            ):
                return ablak, elem
    return None


def _menupont(kon: Kontextus, lepes: Any) -> None:
    if lepes.fomenu:
        _fomenu_megnyitasa(kon, lepes.fomenu)
    nev = lepes.objektumnev
    talalat: list[Any] = []

    def _megvan() -> bool:
        talalat[:] = [qt.keres_lathato(kon.ablak, nev)]
        return talalat[0] is not None

    if qt.var_feltetelre(kon.alkalmazas, _megvan, qt.KATTINTAS_HATARIDO_MP):
        ablak, elem = talalat[0]
        qt.kattint(kon.alkalmazas, ablak, elem)
        return
    if _almenu_megnyitasa(kon, nev):
        return
    raise qt.FuttatasiHiba(_nincs_menupont(kon, nev))


def _almenu_megnyitasa(kon: Kontextus, nev: str) -> bool:
    """Ha a név egy almenüé, a szülőmenü sorára kattint, és megvárja a megnyílását."""
    almenu = kon.ablak.findChild(QObject, nev)
    if almenu is None or almenu.property("title") is None:
        return False
    sor = _almenu_sora(kon, almenu)
    if sor is None:
        return False
    qt.kattint(kon.alkalmazas, sor[0], sor[1])
    return qt.var_feltetelre(
        kon.alkalmazas,
        lambda: bool(almenu.property("visible")),
        qt.KATTINTAS_HATARIDO_MP,
    )


def _nincs_menupont(kon: Kontextus, nev: str) -> str:
    if kon.ablak.findChild(QObject, nev) is not None:
        ok = "az objektum létezik, de nem látható (nincs megnyitva a menü, vagy rejtett)"
    else:
        ok = "nincs ilyen objectName a főablak objektumfájában"
    menunevek = [
        elem
        for elem in qt.lathato_elemnevek(kon.ablak)
        if "enu" in elem
    ]
    lista = ", ".join(menunevek[:_MENU_NEVEK_LISTAJA_MAX]) or "(nincs látható menütétel)"
    if len(menunevek) > _MENU_NEVEK_LISTAJA_MAX:
        lista += ", ..."
    return f"A {nev!r} menüpont nem kattintható: {ok}. Látható menü-objektumok: {lista}."


# --- billentyűzet és várakozás -----------------------------------------------------


def _gepel(kon: Kontextus, lepes: Any) -> None:
    qt.szoveg_gepelese(kon.alkalmazas, kon.ablak, lepes.szoveg)


def _billentyu(kon: Kontextus, lepes: Any) -> None:
    qt.billentyu_kuldese(kon.alkalmazas, kon.ablak, lepes.billentyu)


def _var(kon: Kontextus, lepes: Any) -> None:
    qt.var(kon.alkalmazas, lepes.masodperc)


_KEZELOK = {
    "kijelol": _kijelol,
    "kijelol_mod": _kijelol_mod,
    "jobbklikk": _jobbklikk,
    "jobbklikk_mappa": _jobbklikk_mappa,
    "menupont": _menupont,
    "gepel": _gepel,
    "billentyu": _billentyu,
    "var": _var,
}
