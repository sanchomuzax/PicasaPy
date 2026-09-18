"""Az album-fejléc gombsorának testreszabása (#1792) — tiszta réteg.

Az eredeti Picasa fejléce (`headerpanel`) testreszabható volt: a
felhasználó eldönthette, mely gombok látszanak és milyen sorrendben. Két
registry-kulcs tárolta (`docs/specs/picasa-menu-parancsok-viselkedes.md`
44.): a `Preferences\\Buttons\\UserConfig` az összeállítást, a
`Preferences\\Buttons\\Exclude` a KIHAGYOTT gombokat.

⇒ A gombok nemcsak átrendezhetők, hanem **elrejthetők** is. Nálunk ehhez
egyetlen lista is elég: ami a sorban van, az látszik — abban a
sorrendben; ami nincs, az kimaradt. A két kulcs információtartalma ebben
benne van, és nincs az az állapot, amiben a kettő ellentmondana egymásnak.

⛔ A GUID→gombnév megfeleltetés nincs meg (a `#buttons\\` adatmappából
jönne, az a mentésünkben nincs), és nem is kell: nálunk a gomb saját
**objektumneve** az azonosító — a jegy törzse kimondja, hogy
kompatibilitási kötelezettségünk nincs, mert a gombkészlet más.

A visszatöltés az értelmezhetetlen értéknél az ALAPÉRTELMEZÉSRE esik
vissza (a `collage_prefs.py` elve): egy kézzel átírt vagy régi verzióból
maradt beállítás sosem omlaszthatja el a fejlécet.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings

#: A tárolás kulcsa. Egy kulcs, nem kettő — ld. a modul fejlécét.
SORREND_KULCS = "toolbar/headerButtons"

#: Az elválasztó a tárolt sorban. Az objektumnevekben nem fordul elő.
_ELVALASZTO = ","

#: A testreszabható MŰVELET-gombok — a `headerpanel` élő vezérlőiből
#: (spec 56.1) azok, amelyek nálunk meg is vannak.
#:
#: ⛔ NEM tagja:
#: - `headerUploadButton` — megszűnt szolgáltatás (Picasa Webalbumok,
#:   2016), a gomb tiltott; egy testreszabó lista nem kínálhat olyat,
#:   ami úgysem működik;
#: - a személy-album javaslat-vezérlői (#2187) — azok ÁLLAPOTFÜGGŐK
#:   (akkor látszanak, ha van eldöntetlen javaslat), nem a felhasználó
#:   állítja őket;
#: - a cím, a dátum és a leírás — nem gombok.
TESTRESZABHATO: tuple[str, ...] = (
    "headerPlayButton",
    "headerSelectStarredButton",
    "headerSaveEditsButton",
    "headerCollageButton",
)

#: Alapállapotban MINDEN testreszabható gomb látszik, a mért sorrendben —
#: az eredetiben is a teljes készlet az alap (a `Exclude` üresen indul).
ALAP_SORREND: tuple[str, ...] = TESTRESZABHATO


def visszaall_alapra() -> list[str]:
    """„Visszaállítás alapértelmezettre" — mindig ÚJ lista, hogy a hívó
    későbbi módosítása ne írja át a modul állandóját."""
    return list(ALAP_SORREND)


def elerheto_gombok(sorrend: list[str]) -> list[str]:
    """A bal lista tartalma: ami a készletben van, de a sorban nincs."""
    return [nev for nev in TESTRESZABHATO if nev not in sorrend]


def hozzaad(sorrend: list[str], nev: str) -> list[str]:
    """Gomb a sor VÉGÉRE. Ismeretlen azonosítót és ismétlést elutasít."""
    if nev not in TESTRESZABHATO or nev in sorrend:
        return list(sorrend)
    return [*sorrend, nev]


def torold(sorrend: list[str], nev: str) -> list[str]:
    """Gomb ki a sorból (attól még elérhető marad, csak nem látszik)."""
    return [meglevo for meglevo in sorrend if meglevo != nev]


def _mozgat(sorrend: list[str], nev: str, irany: int) -> list[str]:
    if nev not in sorrend:
        return list(sorrend)
    honnan = sorrend.index(nev)
    hova = honnan + irany
    if not 0 <= hova < len(sorrend):
        return list(sorrend)
    uj = list(sorrend)
    uj[honnan], uj[hova] = uj[hova], uj[honnan]
    return uj


def feljebb(sorrend: list[str], nev: str) -> list[str]:
    """Egy hellyel előbbre. A lista elejéről nincs hova."""
    return _mozgat(sorrend, nev, -1)


def lejjebb(sorrend: list[str], nev: str) -> list[str]:
    """Egy hellyel hátrébb. A lista végéről nincs hova."""
    return _mozgat(sorrend, nev, 1)


def mentsd(beallitasok: QSettings, sorrend: list[str]) -> None:
    """A sor kiírása. Az ÜRES sor is érvényes állapot (minden gomb
    elrejtve), ezért üres sztringként megy ki — nem törlésként."""
    beallitasok.setValue(SORREND_KULCS, _ELVALASZTO.join(sorrend))
    beallitasok.sync()


def betoltsd(beallitasok: QSettings) -> list[str]:
    """A sor visszaolvasása.

    Három eset, mind szándékos:

    - **nincs kulcs** → az alapértelmezett (teljes) készlet;
    - **üres sztring** → ÜRES sor (a felhasználó mindent elrejtett) — ez
      nem esik vissza az alapra, mert kimondott döntés volt;
    - **értelmezhetetlen tartalom** → alapértelmezés; az ismeretlen
      azonosítók pedig kiesnek (régi verzióból maradt gombnév ne kerüljön
      a fejlécre).
    """
    nyers = beallitasok.value(SORREND_KULCS, None)
    if nyers is None:
        return visszaall_alapra()
    if isinstance(nyers, (list, tuple)):
        elemek = [str(elem) for elem in nyers]
    elif isinstance(nyers, str):
        elemek = [darab.strip() for darab in nyers.split(_ELVALASZTO)]
    else:
        return visszaall_alapra()
    szurt = [nev for nev in elemek if nev in TESTRESZABHATO]
    if not szurt and any(elemek) and not any(
        nev in TESTRESZABHATO for nev in elemek
    ):
        #: volt benne tartalom, de EGYIK sem ismert azonosító — ez sérült
        #: vagy idegen beállítás, nem „mindent elrejtettem"
        return visszaall_alapra()
    return szurt
