"""EXIF (TIFF) blokk frissítése HELYBEN - a meglévő bájtok el nem mozdulnak (#3961).

## Miért nem piexif

A `piexif.load` → `piexif.dump` oda-vissza út a valódi kamerás JPEG-en
(Xiaomi 14T) rontott és törölt: a nulla nélküli ASCII-t csonkolta
(`ExifVersion` `0220` → `022`), eldobta az ismeretlen tageket és az
InteropIFD-t, és újraírta a blokkot, így a MakerNote eltolása elcsúszott -
az abszolút eltolással dolgozó gyártói jegyzetek (Canon, Olympus,
Panasonic, Pentax) ettől érvénytelenek. A régi, bájtra másoló út mindezt
megtartotta; az új út nem veszíthet el semmit.

## Hogyan

A forrás blokkja **bájtra megmarad**, és csak két dolog történhet vele:

1. **Helyben írás:** egy MEGLÉVŐ tag értéke a saját helyén felülíródik, ha a
   típusa egyező és az új érték elfér (`DateTime` 20 bájtja, a méret SHORT/LONG
   mezője).
2. **Hozzáfűzés:** ha taget kell HOZZÁADNI (vagy a meglévő nem írható
   helyben), az érintett IFD **másolata** a blokk VÉGÉRE kerül a bővített
   bejegyzéslistával, és csak a rá mutató eltolás (a fejléc IFD0-mutatója,
   ill. az IFD0 `ExifIFD`-mutatója) változik. A régi IFD árván a helyén
   marad - semmilyen meglévő érték-eltolás nem mozdul, a MakerNote sem.

A beágyazott előnézet (IFD1) cseréje ugyanígy: ha a régi előnézet a blokk
végén ül, az helyére kerül az új; ha nem, az új a végére fűződik. Az IFD1
`JPEGInterchangeFormat`/`…Length` mezője helyben íródik.

A helyben írás célja csak a fejléc (8 bájt) utáni, a forrás hosszán belüli
tartomány lehet, amely nem fed olvasott IFD-táblát (IFD0, Exif, GPS, Interop,
IFD1), más tag értékét, sem a beágyazott előnézet bájtjait; ami nem ilyen, az
hozzáfűzéssel kerül át. A fájlból olvasott darabszám a célellenőrzés ELŐTT
nem foglalhat (#3964).

A végén két önellenőrzés fut: (1) a kimenet a forrás hosszáig bájtra egyezik
a forrással, kivéve a helyben írt tartományokat (és a lecserélt előnézetet);
(2) a kimenetet visszaolvasva (IFD0, Exif, GPS, Interop, IFD1 és a nem cserélt
előnézet bájtjai) minden forrás-tag típusa, darabszáma és értéke egyezik,
kivéve a szándékosan írtakat. Az egy IFD-ben kétszer szereplő tag minden
példánya átkerül, és az ellenőrzés listaként hasonlít (#3968).

Az InteropIFD (`"Interop"` változás, #3989) ugyanezen az úton bővül: a meglévő
Interop IFD bővített másolata a blokk végére kerül, és csak az Exif IFD
`0xa005` mutatója íródik helyben; ha nincs Interop IFD, újat fűz a végére, és
a mutató az (átmásolt) Exif IFD-be kerül. Csak `csak_ha_hianyzik` tag adható
hozzá; érvénytelen vagy kétszer szereplő `0xa005`-nél az Interop érintetlen.
Az érvénytelen (0-s vagy ismeretlen) típusú bejegyzés az áthelyezéskor a forrásbeli
relatív helyén marad (a forrás végén állók a végén), csak az érvényesek rendeződnek
tag szerint (#3999).
Az IFD1 ÚJRAÉPÍTÉSE (`uj_ifd1`, #3998, spec 16. H): az export az IFD1-et
mindig a kimenetéből készíti, a forrásé sosem kerül át. A forrás IFD1-táblája
a helyén marad (árván), a beágyazott előnézetének bájtjai kinullázódnak (vagy,
ha a blokk végén álltak, le is vágódnak), hogy a forrás bélyegképe ne
szivárogjon a kimenetbe; az új IFD1 (`0x103`, `0x11a`, `0x11b`, `0x128`,
`0x201`, `0x202`) a többi hozzáfűzés UTÁN a blokk végére kerül, utána a
bélyegkép (páratlan hossznál 1 nullbájt követi), és csak az IFD0 következő-IFD
mutatója íródik. Bélyegkép nélkül (`None`) a mutató 0: nincs IFD1. A kimenetet
külön önellenőrzés olvassa vissza.
Bármi váratlanra `TiffHiba` - a hívó ilyenkor a forrás bájtjait adja tovább.
"""

# A régi importútvonal (`from picasapy.metadata.tiff_helyben import ...`) marad
# érvényes: a nevek itt vannak akkor is, ha a definíciójuk egy részmodulban van.
# ruff: noqa: F401
from __future__ import annotations

from typing import Callable

from picasapy.metadata.tiff_athelyez import (
    _RACIONALIS,
    _athelyez,
    _ifd0_kovetkezo,
    _ifd1_epites,
    _rendez,
)
from picasapy.metadata.tiff_blokk import (
    ASCII,
    LONG,
    SHORT,
    UNDEFINED,
    _ELONEZET_BAJTOK,
    _EXIF_MUTATO,
    _GPS_MUTATO,
    _IFD1_TAGEK,
    _INTEROP_MUTATO,
    _JPEG_ELONEZET,
    _JPEG_ELONEZET_HOSSZ,
    _TAJOLAS,
    _TIPUS_MERET,
    _URES_TIFF,
    Ertek,
    TiffHiba,
    Valtozas,
    _Bejegyzes,
    _Blokk,
    ascii_ertek,
)
from picasapy.metadata.tiff_iras import (
    _alkalmaz,
    _cel_szabad,
    _elonezet_csere,
    _helyben_1st,
    _helyben_irhato,
    _nem_ketszer_szereplo,
    _nyers,
    _regi_elonezet_torlese,
)
from picasapy.metadata.tiff_olvas import (
    _ellenoriz,
    _ellenoriz_ifd1,
    _ellenoriz_szerkezet,
    _elonezet_bajtok,
    _exif_ifd,
    _ifd1_tagek,
    _interop_ifd,
    _mutatott_ifd,
    _szandekolt,
    _szerkezet,
    _tartalom,
)


def tajolas_1_helyben(tiff: bytes) -> bytes:
    """Tartalék út (#3966): az IFD0 és az IFD1 meglévő `Orientation` (0x0112)
    tagje a helyén `1`-re; semmi más nem változik. Hibánál `TiffHiba`: a helyén
    nem írható tag, és az is, ha a visszaolvasott kimenetben a tájoláson kívül
    bármi más megváltozott (ugyanaz a szerkezeti önellenőrzés, mint a fő úton)."""
    blokk = _Blokk(tiff)
    ifd0, ifd1_off = blokk.ifd(blokk.u32(4))
    ifd1 = _ifd1_tagek(blokk, ifd1_off)
    ertek = Ertek(SHORT, 1)
    for tagek in (ifd0, ifd1):
        for b in tagek:
            if b.tag == _TAJOLAS and not _helyben_irhato(blokk, b, ertek):
                raise TiffHiba("a tájolás-tag a helyén nem írható")
    kimenet = bytes(blokk.buf)
    _ellenoriz_szerkezet(tiff, kimenet, {("0th", _TAJOLAS), ("1st", _TAJOLAS)})
    return kimenet


def frissitett_tiff(
    tiff: bytes | None,
    valtozasok: list[Valtozas],
    *,
    elonezet: Callable[[], bytes | None] | None = None,
    uj_ifd1: Callable[[], bytes | None] | None = None,
) -> bytes:
    """A frissített TIFF-blokk (`tiff=None`: új, üres blokkból építve).

    `elonezet`: ha van IFD1 JPEG-előnézet, ez adja az újat (lustán, mert
    dekódolás kell hozzá); `None` visszatérésnél a forrásé marad.
    `uj_ifd1` (#3998; `elonezet`-tel nem adható meg): az IFD1 újraépül, a
    forrásé nem kerül át; a hívott függvény a bélyegkép JPEG-je, vagy `None`
    (akkor nincs IFD1).
    Hibánál `TiffHiba`."""
    if elonezet is not None and uj_ifd1 is not None:
        raise TiffHiba("elonezet és uj_ifd1 együtt nem adható meg")
    forras = tiff if tiff is not None else _URES_TIFF
    blokk = _Blokk(forras)
    ifd0_off = blokk.u32(4)
    ifd0, ifd1_off = blokk.ifd(ifd0_off)
    exif_valtozasok = [v for v in valtozasok if v.ifd == "Exif"]
    interop_valtozasok = [v for v in valtozasok if v.ifd == "Interop"]
    if any(not v.csak_ha_hianyzik for v in interop_valtozasok):
        raise TiffHiba("az Interop IFD-be csak hiányzó tag adható")
    exif_mutato = next((b for b in ifd0 if b.tag == _EXIF_MUTATO), None)
    # minden érintett IFD-tábla a helyben írás ELŐTT beolvasva: a célkorlát
    # (`_cel_szabad`) mindegyiket ismeri
    if exif_valtozasok or interop_valtozasok:
        exif, exif_kov = _exif_ifd(blokk, exif_mutato)
    else:
        exif, exif_kov = _mutatott_ifd(blokk, exif_mutato), 0
    # a GPS- és az InteropIFD táblája (és értékei) is olvasott: érvénytelen
    # mutatónál kimarad
    _mutatott_ifd(blokk, next((b for b in ifd0 if b.tag == _GPS_MUTATO), None))
    interop = _interop_ifd(blokk, exif)
    ifd1 = _ifd1_tagek(blokk, ifd1_off)
    elonezet_csere = False
    ifd1_ujra = uj_ifd1 is not None
    belyegkep = uj_ifd1() if uj_ifd1 is not None else None
    if ifd1_ujra:
        _regi_elonezet_torlese(blokk, ifd1)
    elif ifd1 and elonezet is not None:
        uj_kep = elonezet()
        if uj_kep:
            elonezet_csere = _elonezet_csere(blokk, ifd1, uj_kep)
    csonk = blokk.eredeti_hossz

    uj0 = _alkalmaz(blokk, ifd0, [v for v in valtozasok if v.ifd == "0th"])
    if not ifd1_ujra:  # az újraépülő IFD1-be a régi tagek írása fölösleges
        _helyben_1st(blokk, ifd1, [v for v in valtozasok if v.ifd == "1st"])
    uj_exif: dict[int, tuple[int, int, bytes]] = {}
    interop_mutato = False
    if exif_valtozasok:
        uj_exif = _alkalmaz(blokk, exif, exif_valtozasok)
    if interop_valtozasok and interop is not None:
        # az Interop IFD az Exif IFD ELŐTT: a mutatója az Exif IFD másolatába is
        # a JELENLEGI bájtokból kerül át
        mutato, interop_tagek, interop_kov = interop
        uj_interop = _alkalmaz(blokk, interop_tagek, interop_valtozasok)
        if uj_interop:
            interop_off = _athelyez(blokk, interop_tagek, uj_interop, interop_kov)
            interop_mutato = True
            if mutato is not None:
                blokk.ir_helyben(mutato.hely + 8, blokk.egesz(LONG, interop_off))
            else:
                uj_exif[_INTEROP_MUTATO] = (LONG, 1, blokk.egesz(LONG, interop_off))
    if uj_exif:
        uj_off = _athelyez(blokk, exif, uj_exif, exif_kov)
        if exif_mutato is not None:
            blokk.ir_helyben(exif_mutato.hely + 8, blokk.egesz(LONG, uj_off))
        else:
            uj0[_EXIF_MUTATO] = (LONG, 1, blokk.egesz(LONG, uj_off))
    ifd0_hely = ifd0_off
    if uj0:
        ifd0_hely = _athelyez(blokk, ifd0, uj0, ifd1_off)
        blokk.buf[4:8] = blokk.egesz(LONG, ifd0_hely)
    if ifd1_ujra:
        # az IFD1 és a bélyegkép a LEGVÉGÉN: minden más hozzáfűzés előttük áll
        if belyegkep:
            _ifd0_kovetkezo(blokk, ifd0_hely, _ifd1_epites(blokk, belyegkep), bool(uj0))
        elif ifd1_off:
            _ifd0_kovetkezo(blokk, ifd0_hely, 0, bool(uj0))
    kimenet = bytes(blokk.buf)
    if ifd1_ujra:
        _ellenoriz_ifd1(kimenet, belyegkep or None)
    if tiff is not None:
        _ellenoriz(forras, blokk, csonk)
        _ellenoriz_szerkezet(
            forras,
            kimenet,
            _szandekolt(valtozasok, elonezet_csere, interop_mutato),
            ifd1_ujra,
        )
    return kimenet
