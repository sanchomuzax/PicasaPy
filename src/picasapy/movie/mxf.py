"""A `.mxf` mozgófilm-projektfájl — írás és olvasás (#3191).

Forrás: `docs/specs/picasa-create-features.md` 2.4 és **2.4/b** — a
formátum a **binárisból** van megfejtve (két író: `0x00816b00` a gyökér és
az album-szintű mezők, `0x00816440` egy átmenet-bejegyzés), tehát mintára
nincs szükség.

A `.mxf` a film **szerkeszthető** állapota — a kollázs `.cxf`-jének
megfelelője. A kirenderelt videó mellett ez őrzi meg, hogy a film később is
módosítható maradjon; az automatikus mentés neve `autosave.mxf`
(`MakeMoviePanel::autosave`), a helye a `Movies` mappa (`0x0068a4b0`).

## Három dolog, amit könnyű elrontani

1. ⭐ **Minden mező GYEREKELEM, nem attribútum.** Az író végig a
   `0x009c0640`-et hívja — ez a `.cxf`-fel szemben **eltérő stílus** (ott a
   geometria attribútumként megy ki). Ugyanaz a szerializáló, más hívás.
2. ⭐ **A `defaulttrans` és a `trans` UGYANAZT a szerkezetet írja** (közös
   író), tehát a diánkénti bejegyzés felül tudja írni az album-szintű
   alapértelmezést — ezért állítható a Picasában a diaidő és az átmenet
   képenként is.
3. ⭐ **Az arc-téglalap (`facerect*`) MINDEN dián ott van**, nem csak
   arc-filmnél: az arc-film a szokásos dia-rekordot használja, és a
   kivágást ezekkel a mezőkkel rögzíti.

A `blacktime` **külön mező** az átmenet hossza mellett — a Picasa a diák
közé fekete szünetet is tud tenni.

## Amit a formátumról NEM tudunk

A fájl-szintű keret (XML-fejléc, sorvégek) a `.cxf` mintájából
következtetve **UTF-8 + CRLF** — ugyanaz a szerializáló írja, de a
bizonyítottsági fok itt „erős", nem „megerősített" (a spec kimondja).

A `<filename>` útvonalát **érintetlenül** őrizzük (`$My Pictures\\…`,
windowsos fordított perjelekkel): a változó feloldása az útvonal-réteg
dolga. Ha itt „megjavítanánk", a fájl az eredeti Picasában használhatatlan
lenne — ugyanaz a szabály, mint a `.cxf` `<src>`-jénél.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape

#: A Picasa automatikus mentésének neve (`MakeMoviePanel::autosave`).
AUTOSAVE_NEV = "autosave.mxf"

#: A gyökérelem neve (`0x00816b08`).
GYOKER = "CTransTimeline"

_XML_DEKLARACIO = '<?xml version="1.0" encoding="utf-8" ?>'
_SORVEG = "\r\n"


def _f(ertek: float) -> str:
    """A Picasa `%f`-je: mindig hat tizedes (a `.cxf` szabálya)."""
    return f"{ertek:.6f}"


def _flag(ertek: bool) -> str:
    return "1" if ertek else "0"


@dataclass(frozen=True)
class MxfSzovegParam:
    """A szöveges dia betűparaméterei (`textparm`).

    A `styleid` a tizenegy mért stílus egyike (a spec 2.3); a `facerect*`
    mezők az arc-film kivágását rögzítik, és MINDEN dián ott vannak.
    """

    fontname: str = ""
    size: int = 0
    color: int = 0
    weight: int = 0
    italic: bool = False
    outline: bool = False
    styleid: int = 0
    facerectx0: int = 0
    facerecty0: int = 0
    facerectx1: int = 0
    facerecty1: int = 0
    facemoviesrc: int = 0


@dataclass(frozen=True)
class MxfForras:
    """Egy dia forrása (`src`) — kép, szöveges dia vagy videó."""

    tipus: int = 0
    bkcolor: int = 0
    index: int = 0
    text: str = ""
    filename: str = ""
    showflags: int = 0
    szovegparam: MxfSzovegParam = field(default_factory=MxfSzovegParam)


@dataclass(frozen=True)
class MxfAtmenet:
    """Egy átmenet-bejegyzés — a `defaulttrans` és a `trans` KÖZÖS alakja."""

    transition: int = 0
    advanceinterval: float = 0.0
    transitiontime: float = 0.0
    blacktime: float = 0.0
    forras: MxfForras = field(default_factory=MxfForras)


@dataclass(frozen=True)
class MxfProjekt:
    """A teljes film-projekt: album-szintű beállítások + a diák."""

    curresolution: int = 0
    musicfile: str = ""
    audiooption: int = 0
    facemovie: bool = False
    showcaption: bool = False
    cropfit: int = 0
    showdates: bool = False
    removelowresfaces: bool = False
    ordering: int = 0
    burstmodethresh: int = 0
    albumid: int = 0
    defaulttrans: MxfAtmenet = field(default_factory=MxfAtmenet)
    atmenetek: tuple[MxfAtmenet, ...] = ()


# --- Írás -------------------------------------------------------------------


def _elem(behuzas: str, nev: str, ertek: str) -> str:
    return f"{behuzas}<{nev}>{escape(ertek)}</{nev}>"


def _szovegparam_sorok(param: MxfSzovegParam, behuzas: str) -> list[str]:
    b = behuzas + " "
    return [
        f"{behuzas}<textparm>",
        _elem(b, "fontname", param.fontname),
        _elem(b, "size", str(param.size)),
        _elem(b, "color", str(param.color)),
        _elem(b, "weight", str(param.weight)),
        _elem(b, "italic", _flag(param.italic)),
        _elem(b, "outline", _flag(param.outline)),
        _elem(b, "styleid", str(param.styleid)),
        _elem(b, "facerectx0", str(param.facerectx0)),
        _elem(b, "facerecty0", str(param.facerecty0)),
        _elem(b, "facerectx1", str(param.facerectx1)),
        _elem(b, "facerecty1", str(param.facerecty1)),
        _elem(b, "facemoviesrc", str(param.facemoviesrc)),
        f"{behuzas}</textparm>",
    ]


def _forras_sorok(forras: MxfForras, behuzas: str) -> list[str]:
    b = behuzas + " "
    return [
        f"{behuzas}<src>",
        _elem(b, "type", str(forras.tipus)),
        _elem(b, "bkcolor", str(forras.bkcolor)),
        _elem(b, "index", str(forras.index)),
        _elem(b, "text", forras.text),
        _elem(b, "filename", forras.filename),
        _elem(b, "showflags", str(forras.showflags)),
        *_szovegparam_sorok(forras.szovegparam, b),
        f"{behuzas}</src>",
    ]


def _atmenet_sorok(atmenet: MxfAtmenet, nev: str, behuzas: str) -> list[str]:
    """Egy átmenet-bejegyzés — a `defaulttrans` és a `trans` KÖZÖS írója."""
    b = behuzas + " "
    return [
        f"{behuzas}<{nev}>",
        _elem(b, "transition", str(atmenet.transition)),
        _elem(b, "advanceinterval", _f(atmenet.advanceinterval)),
        _elem(b, "transitiontime", _f(atmenet.transitiontime)),
        _elem(b, "blacktime", _f(atmenet.blacktime)),
        *_forras_sorok(atmenet.forras, b),
        f"{behuzas}</{nev}>",
    ]


def dumps(projekt: MxfProjekt) -> bytes:
    """A projekt `.mxf` bájtsorozattá alakítása (UTF-8, CRLF)."""
    b = " "
    sorok = [
        _XML_DEKLARACIO,
        f"<{GYOKER}>",
        _elem(b, "curresolution", str(projekt.curresolution)),
        _elem(b, "musicfile", projekt.musicfile),
        _elem(b, "audiooption", str(projekt.audiooption)),
        _elem(b, "facemovie", _flag(projekt.facemovie)),
        _elem(b, "showcaption", _flag(projekt.showcaption)),
        _elem(b, "cropfit", str(projekt.cropfit)),
        _elem(b, "showdates", _flag(projekt.showdates)),
        _elem(b, "removelowresfaces", _flag(projekt.removelowresfaces)),
        _elem(b, "ordering", str(projekt.ordering)),
        _elem(b, "burstmodethresh", str(projekt.burstmodethresh)),
        _elem(b, "albumid", str(projekt.albumid)),
        *_atmenet_sorok(projekt.defaulttrans, "defaulttrans", b),
    ]
    for atmenet in projekt.atmenetek:
        sorok.extend(_atmenet_sorok(atmenet, "trans", b))
    sorok.append(f"</{GYOKER}>")
    return (_SORVEG.join(sorok) + _SORVEG).encode("utf-8")


def write_mxf(cel: Path | str, projekt: MxfProjekt) -> Path:
    """A projekt kiírása fájlba, **bájt-alapon**.

    Szövegmódú írásnál a Python a platform sorvégét használná (Linuxon LF),
    ami elrontaná a CRLF-et — ugyanaz a csapda, mint a `write_cxf`-nél.
    """
    ut = Path(cel)
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_bytes(dumps(projekt))
    return ut


# --- Olvasás ----------------------------------------------------------------


def _szoveg(szulo: ElementTree.Element, nev: str) -> str:
    gyerek = szulo.find(nev)
    return "" if gyerek is None or gyerek.text is None else gyerek.text


def _egesz(szulo: ElementTree.Element, nev: str) -> int:
    nyers = _szoveg(szulo, nev).strip()
    try:
        return int(float(nyers)) if nyers else 0
    except ValueError:
        # #301 elve: egy hibás mező nem viheti el az egész beolvasást
        return 0


def _tort(szulo: ElementTree.Element, nev: str) -> float:
    nyers = _szoveg(szulo, nev).strip()
    try:
        return float(nyers) if nyers else 0.0
    except ValueError:
        return 0.0


def _logikai(szulo: ElementTree.Element, nev: str) -> bool:
    return _egesz(szulo, nev) != 0


def _szovegparam(szulo: ElementTree.Element) -> MxfSzovegParam:
    elem = szulo.find("textparm")
    if elem is None:
        return MxfSzovegParam()
    return MxfSzovegParam(
        fontname=_szoveg(elem, "fontname"),
        size=_egesz(elem, "size"),
        color=_egesz(elem, "color"),
        weight=_egesz(elem, "weight"),
        italic=_logikai(elem, "italic"),
        outline=_logikai(elem, "outline"),
        styleid=_egesz(elem, "styleid"),
        facerectx0=_egesz(elem, "facerectx0"),
        facerecty0=_egesz(elem, "facerecty0"),
        facerectx1=_egesz(elem, "facerectx1"),
        facerecty1=_egesz(elem, "facerecty1"),
        facemoviesrc=_egesz(elem, "facemoviesrc"),
    )


def _forras(szulo: ElementTree.Element) -> MxfForras:
    elem = szulo.find("src")
    if elem is None:
        return MxfForras()
    return MxfForras(
        tipus=_egesz(elem, "type"),
        bkcolor=_egesz(elem, "bkcolor"),
        index=_egesz(elem, "index"),
        text=_szoveg(elem, "text"),
        filename=_szoveg(elem, "filename"),
        showflags=_egesz(elem, "showflags"),
        szovegparam=_szovegparam(elem),
    )


def _atmenet(elem: ElementTree.Element) -> MxfAtmenet:
    return MxfAtmenet(
        transition=_egesz(elem, "transition"),
        advanceinterval=_tort(elem, "advanceinterval"),
        transitiontime=_tort(elem, "transitiontime"),
        blacktime=_tort(elem, "blacktime"),
        forras=_forras(elem),
    )


def loads(adat: bytes | str) -> MxfProjekt:
    """Egy `.mxf` tartalmának értelmezése.

    Raises:
        ValueError: ha a gyökérelem nem a mért `CTransTimeline`.
    """
    szoveg = adat.decode("utf-8") if isinstance(adat, bytes) else adat
    gyoker = ElementTree.fromstring(szoveg)
    if gyoker.tag != GYOKER:
        raise ValueError(
            f"nem {GYOKER} a gyökérelem, hanem {gyoker.tag!r} — "
            "ez nem mozgófilm-projektfájl"
        )
    alap = gyoker.find("defaulttrans")
    return MxfProjekt(
        curresolution=_egesz(gyoker, "curresolution"),
        musicfile=_szoveg(gyoker, "musicfile"),
        audiooption=_egesz(gyoker, "audiooption"),
        facemovie=_logikai(gyoker, "facemovie"),
        showcaption=_logikai(gyoker, "showcaption"),
        cropfit=_egesz(gyoker, "cropfit"),
        showdates=_logikai(gyoker, "showdates"),
        removelowresfaces=_logikai(gyoker, "removelowresfaces"),
        ordering=_egesz(gyoker, "ordering"),
        burstmodethresh=_egesz(gyoker, "burstmodethresh"),
        albumid=_egesz(gyoker, "albumid"),
        defaulttrans=MxfAtmenet() if alap is None else _atmenet(alap),
        atmenetek=tuple(_atmenet(e) for e in gyoker.findall("trans")),
    )


def read_mxf(forras: Path | str) -> MxfProjekt:
    """Egy `.mxf` beolvasása fájlból."""
    return loads(Path(forras).read_bytes())


__all__ = [
    "AUTOSAVE_NEV",
    "piszkozat_utvonal",
    "projekt_utvonal",
    "van_piszkozat",
    "van_projektje",
    "GYOKER",
    "MxfAtmenet",
    "MxfForras",
    "MxfProjekt",
    "MxfSzovegParam",
    "dumps",
    "loads",
    "read_mxf",
    "write_mxf",
]


# --- A kép ↔ projekt megfeleltetés -------------------------------------------


def projekt_utvonal(kep_ut: Path | str) -> Path | None:
    """A képhez tartozó `.mxf`, ha van és olvasható fájl.

    A `collage_save._collage_project_path` párja a film ágán: a projektfájl
    a kirenderelt videó/kép MELLETT áll, azonos alapnévvel. A tulajdonos
    szava a kollázs-gombról: *„Ez a gomb mindig megjelenik, ha megnyitom a
    kollázst"* — tehát nem a létrehozás emléke kapcsolja be a szerkesztő
    gombját, hanem a fájl mellett álló projektfájl (#1002, #2114).
    """
    if not kep_ut:
        return None
    try:
        ut = Path(str(kep_ut)).with_suffix(".mxf")
    except (OSError, ValueError):  # pragma: no cover - platformfüggő
        return None
    try:
        return ut if ut.is_file() else None
    except OSError:  # pragma: no cover - elérhetetlen hálózati út
        return None


def van_projektje(kep_ut: Path | str) -> bool:
    """Van-e a képnek `.mxf` párja — vagyis mozgófilm-kimenet-e."""
    return projekt_utvonal(kep_ut) is not None


def piszkozat_utvonal(mappa: Path | str) -> Path:
    """A mappa automatikus mentésének útvonala (`autosave.mxf`).

    A név MÉRT (`MakeMoviePanel::autosave`), a helye a film célmappája
    (`0x0068a4b0`: a `Movies` mappa). A kollázs `autosave.cxf`-jének párja.
    """
    return Path(mappa) / AUTOSAVE_NEV


def van_piszkozat(mappa: Path | str) -> bool:
    """Áll-e befejezetlen film-piszkozat a mappában."""
    try:
        return piszkozat_utvonal(mappa).is_file()
    except OSError:  # pragma: no cover - elérhetetlen hálózati út
        return False
