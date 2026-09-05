"""A `text=`/`textactive=` szöveg-overlay kulcsok parse/serialize-e (#148, #371).

**A formátum MEGFEJTVE** (#371, 2026-08-15) — a 859 fájlos `.picasa.ini`-
korpusz két valódi `text=` sorából (egy egyblokkos, egy kétblokkos). A teljes
levezetés és a bizonyítottsági fokok: `docs/specs/picasa-ini-format.md`,
„A `text=` sor formátuma" szakasz.

Szerkezet — **HOSSZ-ELŐTAGOS és TÖBBBLOKKOS**::

    text=<blokkok száma>;<blokk><blokk>…
    <blokk> = <blokkhossz>;<szöveghossz>;<szöveg>;<betűtípus>;<geometria>;<stílus>;;

⚠️ **A csapda, ami miatt hossz-előtag van:** a felirat sortörése `&#010;`
alakban van kódolva — **ami maga is pontosvesszőre végződik**. Egy naiv
`;`-szerinti szétvágás tehát elrontja a szöveget (a `&#010` után elvágja).
A helyes parszer a `szöveghossz` alapján LÉPI ÁT a szövegmezőt, nem
elválasztót keres. Ugyanez véd a feliratban álló nyers `;`-től is.

Mezők:

- **szöveghossz** — a **DEKÓDOLT** (valódi újsorra cserélt) szöveg **UTF-8
  bájthossza**. *Megerősített:* mindkét valós mintán pontosan stimmel (19 és
  63), a kétblokkos minta második blokkján is (4).
- **blokkhossz** — LEVEZETHETŐ, a parszernek nincs rá szüksége. A képlet
  (`_block_length`) a három valós blokkon mind egyezik, ezért ez a modul
  **újraszámolja** kiíráskor — így egy szerkesztett blokk hossza is helyes
  marad. Ld. a függvény docsztringjét.
- **geometria** — `x,y,méret,forgatás`; `x`/`y` a képre normalizált [0..1]
  pozíció, a `méret` a kép rövidebb oldalához mért [0..1] arány, a
  **forgatás RADIÁN** (*megerősített:* a korpusz `0.000000`, `1.308997`,
  `-4.712389` értékei pontosan 0°, 75°, −270°).
- **stílus** — `v1,<kitöltő>,<körvonal>,128.0,1.0,<a>,1.0,<vastagság>,<b>,49152`;
  a két szín `0xAARRGGBB`, a vastagság a szabványos súly (mindkét mintán
  `700`). A `128.0`, az `<a>` és a `<b>` mező jelentése **NYITVA** — ez a
  modul típusosan megőrzi és változatlanul visszaírja őket.

**Round-trip garancia.** A `serialize_text(parse_text(v)) == v` a két valódi
korpusz-mintán **bájtra pontosan** teljesül (tesztelve:
`tests/ini/test_text_overlay.py::TestGoldenRoundTrip`). Amit ez a modul nem
tud értelmezni, arra `ValueError`-t dob — a hívó ilyenkor **érintetlenül
hagyja** a sort, és az ini generikus, tartalom-agnosztikus sor-rétege
(`picasapy.ini.document`) bitre pontosan megőrzi.

**Örökölt PicasaPy-alak.** A 0.8.88-ig írt saját formátum
(`1;<x*10000>;<y*10000>;<szöveg>;<betűtípus>`, geometria és stílus nélkül)
olvasható marad (`_parse_legacy_picasapy`), hogy a felhasználó korábban
mentett feliratai ne vesszenek el; a következő mentés már a valódi Picasa-
alakot írja ki.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

#: A blokkon belüli mezők száma a `szöveghossz` UTÁN (szöveg, betűtípus,
#: geometria, stílus) — a blokkot két pontosvessző zárja.
_GEOMETRY_FIELD_COUNT = 4
_STYLE_FIELD_COUNT = 10

#: A lebegőpontos mezők kiírási alakja — a Picasa `%f`-fel ír, azaz hat
#: tizedesjeggyel. A korpusz MINDEN float mezője ilyen alakú, ezért ez a
#: formátum adja vissza bájtra pontosan a valódi sorokat.
_FLOAT_FORMAT = ".6f"

#: A feliratban entitásként kódolt vezérlőkarakterek. **Csak ezt a kettőt**
#: kezeljük: a `&#010;` a korpuszban bizonyított, a `&#013;` a párja. Egy
#: általános `&#NNN;` dekódolás elrontaná a bájtpontos visszaírást, mert a
#: kiírás nem tudná, melyik karaktert kellett entitásként megőrizni.
_ENTITIES: tuple[tuple[str, str], ...] = (("\n", "&#010;"), ("\r", "&#013;"))

#: Az örökölt PicasaPy-alak (0.8.88-ig) egész-koordináta osztója.
_LEGACY_COORD_SCALE = 10000

#: A geometria `méret` mezőjének alapértéke, ha nincs honnan venni (örökölt
#: alak migrálása). A korpusz értékei 0.059–0.112 között vannak.
#: #2287: a méretválasztó 16 abszolút értéke, a `.data`-ból kiolvasva
#: (két azonos példány: `0x00c7dab8` és `0x00c7e4f0`, 16 × `int32`). Az
#: eredetiben NINCS százalék: a panel egészeket ír ki (`"%d"`,
#: `0x0062dfde`), és a listaelem a betű abszolút mérete.
BETUMERETEK: tuple[int, ...] = (
    8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96
)

#: A `.picasa.ini`-be írt szám és a listaérték közti osztó. Az átváltás a
#: `0x005b35a0`-ból, utasításról utasításra: `érték × (magasság ÷ 360)`;
#: a `360.0` a `0xcf3d50`-en. Az író `méret ÷ magasság`-ot tárol (#2271),
#: tehát a magasság kiesik: **`tárolt = érték ÷ 360`**.
_MERET_OSZTO = 360.0


def tarolt_meret(ertek: int | float) -> float:
    """A listaértékből a `.picasa.ini`-be írandó szám."""
    return float(ertek) / _MERET_OSZTO


def meret_taroltbol(tarolt: float) -> int:
    """A tárolt számból a LEGKÖZELEBBI listaérték.

    A fogantyúval átméretezett feliratok nem egész listaértéket adnak
    (a tulajdonos mintáiból: 18,678 · 40,449 · 37,667), a választónak
    viszont akkor is mutatnia kell valamit — a legközelebbit adjuk.
    """
    nyers = float(tarolt) * _MERET_OSZTO
    return min(BETUMERETEK, key=lambda e: abs(e - nyers))


#: Az alapérték az eredetiben **12** (a panel `+0x2cc` mezőjének kezdő
#: értéke). A korábbi `0,1` nem volt előállítható a választóval — bár
#: 0,1 × 360 = 36 véletlenül szerepel a listában.
DEFAULT_TEXT_SIZE = 12 / 360.0


@dataclass(frozen=True)
class TextGeometry:
    """A felirat helye és mérete — mind a négy mező a képre normalizált.

    `x`/`y`: [0..1] pozíció. `rotation`: **radián** (nem fok).

    `size`: a betűméret a kép **MAGASSÁGÁHOZ** normálva — nem a rövidebb
    oldalhoz, ahogy korábban ez a szöveg állította. Mérve (#2271): egy
    896 × 1344-es mintán `0,061111 × 1344 = 82,13`, a mért 82 képpont
    mellett; a rövidebb oldallal 54,8 jönne ki.

    A választható értékek a `BETUMERETEK` listából valók, és a tárolt szám
    a listaérték **360-ad része** (#2287).
    """

    x: float
    y: float
    size: float = DEFAULT_TEXT_SIZE
    rotation: float = 0.0


#: A 9. mező ismert bitjei (#2448). A többi bit jelentése NINCS feltárva.
_ALAHUZOTT_BIT = 0x0001
_DOLT_BIT = 0x0008


@dataclass(frozen=True)
class TextStyle:
    """A felirat színei és súlya.

    `fill_argb`/`outline_argb`: `0xAARRGGBB`. `weight`: szabványos betűsúly
    (a korpuszban mindenhol `700`, azaz félkövér).

    A többi mező jelentése **NYITVA** (#371) — típusosan megőrizzük és
    változatlanul visszaírjuk, hogy a valódi Picasa-sorok bájtpontosan
    round-trippeljenek.
    """

    fill_argb: int
    outline_argb: int
    #: #2271: az alapérték **400** (nem félkövér). A `0x0062d483` szerint a
    #: stílusblokk súly-mezője alapból 400, félkövéren 700 (a gomb
    #: `cmp …, 0x2bc` a `0x0062e31a`-n). Korábban itt fixen 700 állt, ezért
    #: MINDEN feliratunk félkövérként ment ki — a #1994 az írást javította,
    #: de az osztály alapértéke maradt, tehát egy súly nélkül épített
    #: `TextStyle` továbbra is félkövéret adott.
    weight: int = 400
    #: A KÖRVONALVASTAGSÁG (5. mező). A kutatói kör kimérte (#2271), hogy a
    #: csúszka `[0, 1]` folytonos — ugyanaz a `ytSliderHandler`, mint az
    #: átlátszatlanságé —, tehát az érték ÁTSZÁMÍTÁS NÉLKÜL kerül ide.
    #: A korpuszban `0.000000` és `0.500000`; a 0,0 a »nincs körvonal«.
    unknown_a: float = 0.0
    #: A korpuszban `0` és `258` (`0x102`).
    unknown_b: int = 0
    #: A korpuszban mindenhol `v1`.
    version: str = "v1"
    #: A korpuszban állandó `128.000000`.
    constant_128: float = 128.0
    #: A korpuszban állandó `1.000000` (a színek után).
    constant_1a: float = 1.0
    #: A korpuszban állandó `1.000000` (az `unknown_a` után).
    constant_1b: float = 1.0
    #: A `text=` blokk 9. mezője — **bitmező**, nem állandó (#2448).
    #:
    #: A korpuszban `49152` (`0xC000`) a leggyakoribb, de két bit jelentése
    #: a binárisból kiolvasva:
    #:
    #: | bit | maszk | jelentés | cím |
    #: |---:|---:|---|---|
    #: | 0 | `0x0001` | **aláhúzott** | `0x0062ebb3`–`0x0062ebb9` |
    #: | 3 | `0x0008` | **dőlt** | `0x005ba7b0` + `0x0062ea5c` |
    #:
    #: ⚠️ A többi bit (köztük a `0x4000` és a `0x8000`) jelentése **NINCS
    #: feltárva**. A szerializálás ezért a mezőt NEM építi újra a két
    #: ismert bitből, hanem a beolvasottat őrzi meg, és csak a két ismert
    #: bitet állítja — különben egy meg nem értett bit némán elveszne.
    trailer: int = 49152

    @property
    def underline(self) -> bool:
        """Aláhúzott felirat (a 9. mező **0. bitje**)."""
        return bool(self.trailer & _ALAHUZOTT_BIT)

    @property
    def italic(self) -> bool:
        """Dőlt felirat (a 9. mező **3. bitje**)."""
        return bool(self.trailer & _DOLT_BIT)

    def with_style_flags(self, *, italic: bool, underline: bool) -> TextStyle:
        """Új stílus a két ismert bit átállításával.

        ⚠️ A **többi bit változatlan marad.** Ez nem óvatoskodás: a `0x4000`
        és a `0x8000` jelentése nincs feltárva, és egy újraépített mező
        némán elvinné őket — a felhasználó `.picasa.ini`-jéből olyan
        információt, amit nem is értünk.
        """
        maradek = self.trailer & ~(_DOLT_BIT | _ALAHUZOTT_BIT)
        uj = maradek
        if italic:
            uj |= _DOLT_BIT
        if underline:
            uj |= _ALAHUZOTT_BIT
        return replace(self, trailer=uj)


@dataclass(frozen=True)
class TextBlock:
    """Egy felirat-blokk. A `content` a **dekódolt** szöveg: valódi
    újsorokkal, entitások nélkül."""

    content: str
    font: str
    geometry: TextGeometry
    style: TextStyle


@dataclass(frozen=True)
class TextOverlay:
    """A `text=` kulcs típusos alakja — nulla vagy több felirat-blokk."""

    blocks: tuple[TextBlock, ...] = ()

    @property
    def primary(self) -> TextBlock | None:
        """Az első blokk, vagy `None`. A PicasaPy szerkesztője egyblokkos
        feliratot ír, de a beolvasott többblokkos Picasa-adat nem veszhet
        el — ezért a szerkesztő ezt a blokkot módosítja, a többit hagyja."""
        return self.blocks[0] if self.blocks else None

    def with_primary(self, block: TextBlock) -> TextOverlay:
        """Az első blokk cseréje (vagy beszúrása üres overlay-be), a többi
        blokk érintetlenül hagyásával. Immutábilis: új példányt ad."""
        return replace(self, blocks=(block, *self.blocks[1:]))


def _decode_entities(stored: str) -> str:
    """A tárolt alak → valódi szöveg (`&#010;` → újsor)."""
    result = stored
    for char, entity in _ENTITIES:
        result = result.replace(entity, char)
    return result


def _encode_entities(content: str) -> str:
    """Valódi szöveg → tárolt alak (újsor → `&#010;`)."""
    result = content
    for char, entity in _ENTITIES:
        result = result.replace(char, entity)
    return result


def _byte_length(text: str) -> int:
    return len(text.encode("utf-8"))


def _take_text(rest: str, text_length: int) -> tuple[str, str]:
    """A szövegmező leválasztása a `szöveghossz` alapján.

    Karakterenként lépked, az entitásokat EGY karakternek számolva — így a
    `&#010;` záró pontosvesszője nem tévesztheti meg. A `text_length`-edik
    dekódolt bájt után álló karakternek pontosvesszőnek kell lennie,
    különben a sor sérült (`ValueError`).

    Visszatérés: (tárolt szövegmező, a mögötte álló maradék `;` nélkül).
    """
    consumed = 0
    index = 0
    while consumed < text_length:
        if index >= len(rest):
            raise ValueError("Érvénytelen text= érték: a szöveg rövidebb a jelzett hossznál")
        for char, entity in _ENTITIES:
            if rest.startswith(entity, index):
                index += len(entity)
                consumed += _byte_length(char)
                break
        else:
            consumed += _byte_length(rest[index])
            index += 1
    if consumed != text_length:
        raise ValueError("Érvénytelen text= érték: a szöveghossz nem esik karakterhatárra")
    if index >= len(rest) or rest[index] != ";":
        raise ValueError("Érvénytelen text= érték: a szöveghossz nem esik mezőhatárra")
    return rest[:index], rest[index + 1 :]


def _split_field(rest: str, what: str) -> tuple[str, str]:
    field, separator, remainder = rest.partition(";")
    if not separator:
        raise ValueError(f"Érvénytelen text= érték: hiányzó {what} mező")
    return field, remainder


def _parse_geometry(field: str) -> TextGeometry:
    parts = field.split(",")
    if len(parts) != _GEOMETRY_FIELD_COUNT:
        raise ValueError(f"Érvénytelen text= geometria: {field!r}")
    try:
        x, y, size, rotation = (float(part) for part in parts)
    except ValueError as error:
        raise ValueError(f"Érvénytelen text= geometria: {field!r}") from error
    return TextGeometry(x=x, y=y, size=size, rotation=rotation)


def _serialize_geometry(geometry: TextGeometry) -> str:
    return ",".join(
        format(value, _FLOAT_FORMAT)
        for value in (geometry.x, geometry.y, geometry.size, geometry.rotation)
    )


def _parse_style(field: str) -> TextStyle:
    parts = field.split(",")
    if len(parts) != _STYLE_FIELD_COUNT:
        raise ValueError(f"Érvénytelen text= stílus: {field!r}")
    try:
        return TextStyle(
            version=parts[0],
            fill_argb=int(parts[1]),
            outline_argb=int(parts[2]),
            constant_128=float(parts[3]),
            constant_1a=float(parts[4]),
            unknown_a=float(parts[5]),
            constant_1b=float(parts[6]),
            weight=int(parts[7]),
            unknown_b=int(parts[8]),
            trailer=int(parts[9]),
        )
    except ValueError as error:
        raise ValueError(f"Érvénytelen text= stílus: {field!r}") from error


def _serialize_style(style: TextStyle) -> str:
    return ",".join(
        (
            style.version,
            str(style.fill_argb),
            str(style.outline_argb),
            format(style.constant_128, _FLOAT_FORMAT),
            format(style.constant_1a, _FLOAT_FORMAT),
            format(style.unknown_a, _FLOAT_FORMAT),
            format(style.constant_1b, _FLOAT_FORMAT),
            str(style.weight),
            str(style.unknown_b),
            str(style.trailer),
        )
    )


def _block_length(text_length: int, font: str, geometry: str, style: str) -> int:
    """A `blokkhossz` mező — a `szöveghossz` mezőtől a blokkzáró első
    pontosvesszőig, a szöveget a **DEKÓDOLT** hosszával számolva.

    A képletet a három valós blokk mindegyike igazolja (161, 187, 126). A
    kétblokkos minta első blokkja a döntő: ott a tárolt alak `&#010;`-t
    tartalmaz (6 bájt), a dekódolt újsor 1 — a tárolt hosszal számolva
    5-tel többet kapnánk (192 helyett 187 a helyes).
    *Bizonyítottsági fok: megerősített (3/3 blokk).*
    """
    return (
        _byte_length(str(text_length))
        + 1
        + text_length
        + 1
        + _byte_length(font)
        + 1
        + _byte_length(geometry)
        + 1
        + _byte_length(style)
        + 1
    )


def _parse_legacy_picasapy(value: str) -> TextOverlay:
    """A 0.8.88-ig írt, PicasaPy-saját alak: öt mező, geometria és stílus
    nélkül, a pozíció `x*10000`/`y*10000` egészként.

    Csak akkor hívódik, ha a valódi Picasa-alak szerinti feldolgozás
    elbukott — így egy `text=` kulcs sosem esik ki csak azért, mert még a
    régi formátumban van. `ValueError`, ha erre az alakra sem illik.
    """
    parts = value.split(";")
    if len(parts) != 5:
        raise ValueError(f"Érvénytelen text= érték: {value!r}")
    _flag, x_raw, y_raw, content, font = parts
    try:
        x = int(x_raw.strip()) / _LEGACY_COORD_SCALE
        y = int(y_raw.strip()) / _LEGACY_COORD_SCALE
    except ValueError as error:
        raise ValueError(f"Érvénytelen text= érték: {value!r}") from error
    return TextOverlay(
        blocks=(
            TextBlock(
                content=content,
                font=font,
                geometry=TextGeometry(x=x, y=y),
                style=TextStyle(fill_argb=0xFFFFFFFF, outline_argb=0xFF000000),
            ),
        )
    )


def parse_text(value: str) -> TextOverlay:
    """A `text=` érték dekódolása.

    `ValueError`, ha az érték sem a valódi Picasa-alakra, sem az örökölt
    PicasaPy-alakra nem illik — a hívó felelőssége, hogy ilyenkor a
    bejegyzést **érintetlenül** hagyja (ne írja felül a generikus round-trip
    réteget).
    """
    try:
        return _parse_picasa(value)
    except ValueError:
        return _parse_legacy_picasapy(value)


def _parse_picasa(value: str) -> TextOverlay:
    count_raw, rest = _split_field(value, "blokkszám")
    try:
        count = int(count_raw.strip())
    except ValueError as error:
        raise ValueError(f"Érvénytelen text= blokkszám: {count_raw!r}") from error
    if count < 0:
        raise ValueError(f"Érvénytelen text= blokkszám: {count_raw!r}")

    blocks: list[TextBlock] = []
    for _ in range(count):
        _blocklen_raw, rest = _split_field(rest, "blokkhossz")
        textlen_raw, rest = _split_field(rest, "szöveghossz")
        try:
            text_length = int(textlen_raw.strip())
        except ValueError as error:
            raise ValueError(f"Érvénytelen text= szöveghossz: {textlen_raw!r}") from error
        if text_length < 0:
            raise ValueError(f"Érvénytelen text= szöveghossz: {textlen_raw!r}")
        stored, rest = _take_text(rest, text_length)
        font, rest = _split_field(rest, "betűtípus")
        geometry_raw, rest = _split_field(rest, "geometria")
        style_raw, rest = _split_field(rest, "stílus")
        if not rest.startswith(";"):
            raise ValueError("Érvénytelen text= érték: hiányzó blokkzáró pontosvessző")
        rest = rest[1:]
        blocks.append(
            TextBlock(
                content=_decode_entities(stored),
                font=font,
                geometry=_parse_geometry(geometry_raw),
                style=_parse_style(style_raw),
            )
        )
    if rest:
        raise ValueError(f"Érvénytelen text= érték: a blokkszám után maradék: {rest!r}")
    return TextOverlay(blocks=tuple(blocks))


def serialize_text(overlay: TextOverlay) -> str:
    """`TextOverlay` → `text=` érték, a valódi Picasa alakjában.

    A `blokkhossz` mező **újraszámolódik** (`_block_length`), ezért egy
    szerkesztett blokk hossza is helyes marad. A valós korpusz-mintákon a
    `serialize_text(parse_text(v)) == v` bájtra pontosan teljesül.
    """
    parts = [f"{len(overlay.blocks)};"]
    for block in overlay.blocks:
        stored = _encode_entities(block.content)
        text_length = _byte_length(block.content)
        geometry = _serialize_geometry(block.geometry)
        style = _serialize_style(block.style)
        block_length = _block_length(text_length, block.font, geometry, style)
        parts.append(
            f"{block_length};{text_length};{stored};{block.font};{geometry};{style};;"
        )
    return "".join(parts)


def parse_text_active(value: str) -> bool:
    """`textactive=` — a felirat-réteg láthatósága.

    A korpusz mind a 173 előfordulása `0`; az `1` értékre nincs mintánk, a
    `0`/`1` szemantika ezért feltételes (*bizonyítottsági fok: erős a
    szerep, feltételes az érték-jelentés*).
    """
    return value.strip() not in ("", "0")


def serialize_text_active(active: bool) -> str:
    return "1" if active else "0"
