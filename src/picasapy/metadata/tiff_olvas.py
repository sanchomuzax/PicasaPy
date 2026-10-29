"""A TIFF-blokk olvasása és a visszaolvasásos önellenőrzés (#3961, #3968, #3989).

Az olvasók a `_Blokk` bájtjaiból dolgoznak; az önellenőrzés a kimenetet olvassa
vissza, és `TiffHiba`-t ad, ha egy nem szándékolt tag megváltozott.
"""

from __future__ import annotations

from picasapy.metadata.tiff_blokk import (
    LONG,
    _ELONEZET_BAJTOK,
    _EXIF_MUTATO,
    _GPS_MUTATO,
    _IFD1_TAGEK,
    _INTEROP_MUTATO,
    _JPEG_ELONEZET,
    _JPEG_ELONEZET_HOSSZ,
    _TIPUS_MERET,
    TiffHiba,
    Valtozas,
    _Bejegyzes,
    _Blokk,
)


def _ellenoriz(forras: bytes, blokk: _Blokk, csonk: int) -> None:
    """A forrás bájtjai - a helyben írt tartományokon, az IFD0-mutatón és a
    lecserélt előnézeten kívül - változatlanok."""
    szabad = sorted(blokk.irt + [(4, 8), (csonk, len(forras))])
    pos = 0
    for kezdet, veg in szabad + [(len(forras), len(forras))]:
        if kezdet > pos and blokk.buf[pos:kezdet] != forras[pos:kezdet]:
            raise TiffHiba("önellenőrzés: elmozdult forrásbájt")
        pos = max(pos, veg)


def _tartalom(blokk: _Blokk, b: _Bejegyzes, forras_hossz: int) -> tuple[int, int, bytes]:
    """(típus, darab, érték-bájtok); ismeretlen típusnál, és ha az érték a
    `forras_hossz`-on túlra mutat, a nyers 4 bájtos mező (a forrásból kilógó
    mutatónál a kimenetbe hozzáfűzött adat nem különbözhet a forrás üres
    szeletétől)."""
    mezo = bytes(blokk.buf[b.hely + 8 : b.hely + 12])
    elem = _TIPUS_MERET.get(b.tipus)
    if elem is None or elem * b.darab <= 4:
        return b.tipus, b.darab, mezo
    off = blokk.u32(b.hely + 8)
    if off + elem * b.darab > forras_hossz:
        return b.tipus, b.darab, mezo
    return b.tipus, b.darab, bytes(blokk.buf[off : off + elem * b.darab])


def _mutatott_ifd(blokk: _Blokk, mutato: _Bejegyzes | None) -> list[_Bejegyzes]:
    """A mutató által kijelölt IFD tagjei; érvénytelen mutatónál üres (kimarad)."""
    if mutato is None or mutato.tipus not in (LONG, 13) or mutato.darab != 1:
        return []
    try:
        return blokk.ifd(blokk.u32(mutato.hely + 8))[0]
    except TiffHiba:
        return []


def _ifd1_tagek(blokk: _Blokk, ifd1_off: int) -> list[_Bejegyzes]:
    """Az IFD1 tagjei; olvashatatlan vagy hiányzó IFD1-nél üres („nincs IFD1”)."""
    if not ifd1_off:
        return []
    try:
        return blokk.ifd(ifd1_off)[0]
    except TiffHiba:
        return []


def _elonezet_bajtok(blokk: _Blokk, ifd1: list[_Bejegyzes], forras_hossz: int) -> bytes | None:
    tagek = {b.tag: b for b in ifd1}
    hely, hossz = tagek.get(_JPEG_ELONEZET), tagek.get(_JPEG_ELONEZET_HOSSZ)
    if not hely or not hossz or {hely.tipus, hossz.tipus} != {LONG}:
        return None
    if hely.darab != 1 or hossz.darab != 1:
        return None
    kezdet = blokk.u32(hely.hely + 8)
    veg = kezdet + blokk.u32(hossz.hely + 8)
    if kezdet >= veg or veg > forras_hossz or veg > len(blokk.buf):
        return None
    return bytes(blokk.buf[kezdet:veg])


def _szerkezet(
    tiff: bytes, forras_hossz: int
) -> dict[tuple[str, int], list[tuple[int, int, bytes]]]:
    """A blokk tagjei visszaolvasva: IFD0 → Exif (→ Interop) → GPS → IFD1, és az
    előnézet bájtjai. Kulcsonként LISTA: a kétszer szereplő tag minden példánya
    külön elem, sorrendben (#3968)."""
    blokk = _Blokk(tiff)
    ifd0, ifd1_off = blokk.ifd(blokk.u32(4))
    out: dict[tuple[str, int], list[tuple[int, int, bytes]]] = {}

    def felvesz(nev: str, tagek: list[_Bejegyzes]) -> None:
        for b in tagek:
            out.setdefault((nev, b.tag), []).append(_tartalom(blokk, b, forras_hossz))

    felvesz("0th", ifd0)
    mutato = next((b for b in ifd0 if b.tag == _EXIF_MUTATO), None)
    if mutato is not None and mutato.tipus in (LONG, 13) and mutato.darab == 1:
        exif = blokk.ifd(blokk.u32(mutato.hely + 8))[0]
        felvesz("Exif", exif)
        interop = _mutatott_ifd(blokk, next((b for b in exif if b.tag == _INTEROP_MUTATO), None))
        felvesz("Interop", interop)
    gps = _mutatott_ifd(blokk, next((b for b in ifd0 if b.tag == _GPS_MUTATO), None))
    felvesz("GPS", gps)
    ifd1 = _ifd1_tagek(blokk, ifd1_off)
    felvesz("1st", ifd1)
    kep = _elonezet_bajtok(blokk, ifd1, forras_hossz)
    if kep is not None:
        out[("1st", _ELONEZET_BAJTOK)] = [(0, len(kep), kep)]
    return out


def _ellenoriz_szerkezet(
    forras: bytes,
    kimenet: bytes,
    szandekolt: set[tuple[str, int]],
    ifd1_ujra: bool = False,
) -> None:
    """Minden forrás-tag - a szándékosan írtakon kívül - típusra, darabra és
    értékre változatlanul olvasható vissza a kimenetből (az előnézet bájtjai is,
    ha nem cserélődtek). `ifd1_ujra`: az IFD1 tagjai (és az előnézet bájtjai)
    szándékosan mind eldobódnak; az újat a `_ellenoriz_ifd1` nézi."""
    regi, uj = _szerkezet(forras, len(forras)), _szerkezet(kimenet, len(forras))
    for kulcs, ertek in regi.items():
        if ifd1_ujra and kulcs[0] == "1st":
            continue
        if kulcs not in szandekolt and uj.get(kulcs) != ertek:
            raise TiffHiba(f"önellenőrzés: megváltozott tag {kulcs[0]}/{kulcs[1]:#06x}")


def _szandekolt(
    valtozasok: list[Valtozas],
    elonezet_csere: bool,
    interop_mutato: bool,
) -> set[tuple[str, int]]:
    kulcsok = {(v.ifd, v.tag) for v in valtozasok if not v.csak_ha_hianyzik}
    kulcsok.add(("0th", _EXIF_MUTATO))
    if interop_mutato:
        kulcsok.add(("Exif", _INTEROP_MUTATO))
    if elonezet_csere:
        kulcsok |= {("1st", _JPEG_ELONEZET), ("1st", _JPEG_ELONEZET_HOSSZ)}
        kulcsok.add(("1st", _ELONEZET_BAJTOK))
    return kulcsok


def _ellenoriz_ifd1(kimenet: bytes, jpeg: bytes | None) -> None:
    """Az újraépített IFD1 visszaolvasva: bélyegkép nélkül nincs IFD1; egyébként
    pontosan a hat tag, és a bélyegkép bájtra a helyén, a blokk végén."""
    blokk = _Blokk(kimenet)
    _, kovetkezo = blokk.ifd(blokk.u32(4))
    if jpeg is None:
        if kovetkezo:
            raise TiffHiba("önellenőrzés: az IFD1 nem maradhat")
        return
    if not kovetkezo:
        raise TiffHiba("önellenőrzés: hiányzik az új IFD1")
    tagek, kov1 = blokk.ifd(kovetkezo)
    if [b.tag for b in tagek] != list(_IFD1_TAGEK) or kov1:
        raise TiffHiba("önellenőrzés: az IFD1 tagjai")
    kezdet = blokk.u32(tagek[4].hely + 8)
    hossz = blokk.u32(tagek[5].hely + 8)
    if hossz != len(jpeg) or kimenet[kezdet : kezdet + hossz] != jpeg:
        raise TiffHiba("önellenőrzés: a bélyegkép bájtjai")
    if kimenet[kezdet + hossz :] != (b"\x00" if len(jpeg) % 2 else b""):
        raise TiffHiba("önellenőrzés: a bélyegkép nem a blokk végén áll")


def _exif_ifd(
    blokk: _Blokk, exif_mutato: _Bejegyzes | None
) -> tuple[list[_Bejegyzes], int]:
    if exif_mutato is None:
        return [], 0
    if exif_mutato.tipus not in (LONG, 13) or exif_mutato.darab != 1:
        raise TiffHiba("ExifIFD-mutató típusa")
    return blokk.ifd(blokk.u32(exif_mutato.hely + 8))


def _interop_ifd(
    blokk: _Blokk, exif: list[_Bejegyzes]
) -> tuple[_Bejegyzes | None, list[_Bejegyzes], int] | None:
    """Az Exif IFD `0xa005` mutatója, a mutatott Interop IFD tagjei és
    következő-mutatója. `(None, [], 0)`: nincs mutató; `None`: a mutató
    érvénytelen, kétszer szerepel, vagy a táblája nem olvasható - ilyenkor az
    Interop IFD-hez nem nyúlunk (második mutatót sem adunk mellé)."""
    mutatok = [b for b in exif if b.tag == _INTEROP_MUTATO]
    if not mutatok:
        return None, [], 0
    if len(mutatok) > 1:
        # az első mutató táblája ettől még olvasott: a `_cel_szabad` védi
        _mutatott_ifd(blokk, mutatok[0])
        return None
    if mutatok[0].tipus not in (LONG, 13) or mutatok[0].darab != 1:
        return None
    try:
        tagek, kovetkezo = blokk.ifd(blokk.u32(mutatok[0].hely + 8))
    except TiffHiba:
        return None
    return mutatok[0], tagek, kovetkezo
