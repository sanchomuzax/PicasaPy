#!/usr/bin/env python3
"""A védtelen QML-kötések őre — #1572.

**A hibaosztály.** Egy vezérlő-tulajdonságot `bool`/`int`/`real` típusú
property-be adó kötés csak az OBJEKTUM hiányára szokott védekezni::

    // HIBÁS: a `controller` hiányára véd, a `filterActive` hiányára nem
    visible: controller ? controller.filterActive : false

    // HELYES: a hiányzó TULAJDONSÁGRA is
    visible: (controller && controller.filterActive !== undefined)
        ? controller.filterActive : false

A QML-próbák nagy része **stub-vezérlővel** fut, amelyen a frissen
bevezetett tulajdonság még nincs rajta. Ilyenkor a kifejezés `undefined`, a
QML pedig ``Unable to assign [undefined] to bool`` (vagy ``to int``)
szkripthibát dob. A #1260 őre ezt a fixture-életciklusban bukásnak veszi —
méghozzá olyan tesztfájlokon is, amelyeknek a változtatáshoz semmi közük.

**Mért ár (#1526, 2026-08-27).** Négy előfordulást javítottunk egyesével, és
MINDEN kör újat talált: 8/6/7/6 CI-darab bukott, 1 → 3 → ~12 → 9 független
tesztfájlon. Négy teljes kör veszett el rá, és a jegy emiatt parkolt le.

**Mit vizsgál.** Egy kötést akkor néz meg, ha a bal oldal típusa
`bool`/`int`/`real`:

* kiírt deklaráció (``property bool x:``, ``readonly property int y:``), vagy
* a `_BEEPITETT_TIPUSOS` listán szereplő, egyértelmű típusú beépített
  tulajdonság (``visible``, ``enabled``, ``checked``, ``width``, …).

A `var`/`string`/`color` célok SZÁNDÉKOSAN kimaradnak: azok elviselik az
`undefined`-ot, ott a riasztás puszta zaj lenne.

**Mit tekint védtelennek.** Az `OBJ.TAG` hivatkozást, ha mind a négy igaz:

1. az `OBJ` a kötés jobb oldalán CSUPASZON is szerepel — ez a null-őr, tehát
   az objektum hiányával a szerző maga is számol;
2. az `OBJ` **vezérlő**: `setContextProperty`-vel regisztrált név, vagy
   olyan QML-tulajdonság, amit valahol egy vezérlőből töltenek fel
   (``readonly property var ctl: controller``, tetszőleges mélységben);
3. a jobb oldalon NINCS ``OBJ.TAG !== undefined`` (vagy ``=== undefined``,
   vagy ``typeof OBJ.TAG !== "undefined"``) őr;
4. és az `OBJ.TAG` **értékhelyzetben** áll: nem a ternáris FELTÉTELÉBEN, nem
   függvényhívás, és nem nyeli el összehasonlítás (``=== true``, ``> 0``),
   tagadás (``!x``) vagy számtani művelet — azok mind DEFINIÁLT típusú
   eredményt adnak, tehát nem hibázhatnak.

A 4. pont a legfontosabb a pontossághoz: MÉRVE a bevezetéskori fán 27
találatot ad, nélküle 51-et — a 24 különbség mind hamis riasztás lenne
(`ctl.x > 0`, `!ctl.x`, `ctl.x * 2`, `ctl.f()`). **A hamis riasztás itt
drágább, mint a kihagyás** — egy zajos őrt a következő kör kikapcsol.

**Amit NEM ismer fel** (ha ilyen kerül a kódba, némán kimarad): a
`obj["tag"]` indexes hivatkozás, a JS-függvényből (``function f() {…}``)
visszaadott érték, és a háromnál mélyebb tördelésű kötés. Az őr
SZÁNDÉKOSAN szűk: inkább hagyjon ki, mint hogy kiabáljon.

**Az alsó korlát.** Egy SZÁMOLÓ őr üres halmazon is zöld, tehát semmit nem
őriz. Ezért a szkript 2-es kóddal áll el, ha nem talál QML-fájlt, nem talál
regisztrált vezérlőt, vagy egyetlen őrzött vezérlő-hivatkozást sem lát — az
utóbbi a minta POZITÍV KONTROLLJA.

**Az alapállapot.** A mai fa TISZTA: a bevezetéskor talált 27
előfordulást a #1572 mind javította — 14 QML-fájlban, egységes alakra —,
ezért a ``qml_undefined_or_baseline.txt`` ÜRES, a plafon
(`MAX_BASELINE_ENTRIES`) nulla. A lista rövidülhet, de nem hízhat: új
tételhez a plafont is emelni kell, azt pedig a felülvizsgálat látja.

Használat::

    python scripts/qml_undefined_or.py          # ellenőrzés (CI)
    python scripts/qml_undefined_or.py --list   # a mai védtelen kötések

Kilépési kód: 0 ha nincs eltérés az alapállapottól, 1 ha van, 2 ha a
vizsgálat maga üres vagy az alapállapot-fájl hibás.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_APP = _REPO_ROOT / "src" / "picasapy" / "app"
_DEFAULT_BASELINE = Path(__file__).resolve().parent / "qml_undefined_or_baseline.txt"

#: Az alapállapot FELSŐ korlátja. Ma nulla: a bevezetéskori 27
#: előfordulást a #1572 mind javította, tehát nincs mit konzerválni. Emelni
#: csak indoklással szabad — a plafon teszi TUDATOS lépéssé, hogy valaki egy
#: sor beírásával kerülje meg az őrt.
MAX_BASELINE_ENTRIES = 0

#: Sorkomment. A `(?<!:)` őrzi a `http://` és `image://` alakú URL-eket.
_SORKOMMENT = re.compile(r"(?<!:)//[^\n]*")

#: Blokk-komment. A csere a SORTÖRÉSEKET megtartja, különben a jelentett
#: sorszám elcsúszna — márpedig sor nélkül a hibaüzenet nem cselekvésre
#: utasít, csak bosszant.
_BLOKKOMMENT = re.compile(r"/\*.*?\*/", re.S)

#: Sztringliterál (egyszeres és kétszeres idézőjellel). A benne álló pont és
#: kettőspont különben azonosítónak vagy kötésnek látszana.
_SZTRING = re.compile(r"\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'")

#: Bármely kötés bal oldala (`név:`), akár deklarációval. A `(?:^|[{;])`
#: előtag miatt a ternáris `cond ? a : b` KÖZÉPSŐ kettőspontja nem látszik
#: kötésnek, az egysoros `Item { visible: x }` viszont igen.
_KOTES = re.compile(
    r"(?:^|[{;])\s*(?:readonly\s+)?(?:property\s+(\w+)\s+)?(\w+)\s*:\s*"
)

#: Egyértelmű típusú BEÉPÍTETT tulajdonságok. Tételes lista, nem minta:
#: minden felvett név egy elkötelezettség, hogy a típusa tényleg
#: `bool`/`int`/`real`, és a hamis riasztás itt drágább, mint a kihagyás.
#:
#: A `value` SZÁNDÉKOSAN hiányzik: a `Binding.value` típusa `var`, a
#: `Slider.value`-é `real` — a puszta névből nem dönthető el, melyikről van
#: szó, tehát felvéve zajt adna.
_BEEPITETT_TIPUSOS = frozenset(
    {
        # bool
        "visible", "enabled", "checked", "checkable", "clip", "focus",
        "flat", "highlighted", "down", "hoverEnabled", "interactive",
        "readOnly", "editable", "modal", "dim", "antialiasing", "smooth",
        "mipmap", "mirror", "selectByMouse", "autoRepeat", "cached",
        "asynchronous", "persistentSelection", "activeFocusOnTab",
        "wrap", "running", "loops", "alwaysRunToEnd",
        # int
        "currentIndex", "columns", "rows", "columnSpan", "rowSpan",
        "maximumLineCount", "cursorPosition", "duration", "elide",
        # real
        "width", "height", "x", "y", "z", "opacity", "spacing", "radius",
        "rotation", "scale", "padding", "topPadding", "bottomPadding",
        "leftPadding", "rightPadding", "implicitWidth", "implicitHeight",
        "cellWidth", "cellHeight", "columnSpacing", "rowSpacing",
        "contentX", "contentY", "from", "to", "stepSize",
    }
)

#: A kötés jobb oldala folytatódik a következő sorban, ha ezekre végződik…
_FOLYTATAS_VEGE = ("?", ":", "(", "&&", "||", "!==", "===", "!=", "==", ",")

#: …vagy ha a következő sor ezekkel kezdődik (tördelt ternáris).
_FOLYTATAS_ELEJE = ("?", ".", ":", "&&", "||")

#: Legfeljebb ennyi folytatósort fűzünk össze. Háromnál mélyebb tördelés a
#: fában nincs (a leghosszabb a `typeof`-os feltétel az `ImportSourceDialog`-
#: ban); a korlát nélkül egy hiányzó pontosvessző az egész fájlt egyetlen
#: kötésnek nézné. ⚠️ Aki a fában ennél mélyebbre tördel egy kötést, annak a
#: `!== undefined` őre kieshet az összefűzött szövegből — és akkor az őr
#: HAMISAN riaszt. Ilyenkor a tördelést kell rövidíteni, nem az őrt tágítani.
_MAX_FOLYTATAS = 3

#: Egy azonosító-lánc (`a`, `a.b`, `a.b.c`), a pontok körül szóközzel is.
_LANC = re.compile(r"[A-Za-z_$]\w*(?:\s*\.\s*[A-Za-z_$]\w*)*")

#: Nyelvi kulcsszavak és globális objektumok — sosem vezérlők.
_NEM_AZONOSITO = frozenset(
    {
        "true", "false", "null", "undefined", "typeof", "new", "function",
        "var", "let", "const", "return", "if", "else", "Math", "Qt", "JSON",
        "Number", "String", "Boolean", "Object", "Array", "Date", "parseInt",
        "parseFloat", "isNaN",
    }
)

#: SOSEM alias-forrás, akkor sem, ha a jobb oldala pont egy vezérlő. A
#: `Connections { target: controller }` a fában tucatnyi KÜLÖNBÖZŐ objektumra
#: mutat, és a `target.valami` máshol egy sima beviteli mezőt jelent.
_NEM_ALIAS = frozenset({"target", "parent", "model", "modelData"})

#: A null-őr idióma zaja: ha a jobb oldalról ezt ÉS a jelölt vezérlőnevet
#: elhagyva nem marad semmi, akkor a kötés valódi alias.
_NULLOR_ZAJ = re.compile(r"\bundefined\b|\bnull\b|&&|\|\||[(){}?:;\s]")

#: Az `OBJ.TAG` után állva DEFINIÁLT típusú lesz az eredmény, tehát nem
#: hibázhat: összehasonlítás (logikai), számtani művelet (szám), hívás.
_ELNYELI_UTANA = re.compile(r"\s*(===|!==|==|!=|>=|<=|>|<|\+|-|\*|/|%|\()")

#: Ugyanez az `OBJ.TAG` ELŐTT: tagadás (logikai) vagy számtani művelet.
_ELNYELI_ELOTTE = re.compile(r"(!|\+|-|\*|/|%)\s*$")

#: Az EGÉSZ jobb oldalt logikaivá tevő előtag: `!(…)` és `!!(…)`. A
#: `TrayBar.qml` `enabled: !!(a && ctl.b && …)` alakja enélkül hamis
#: riasztás volt: a belső `&&` tényleg adhat `undefined`-ot, de a `!!` azt
#: még az értékadás előtt logikaivá teszi.
_TELJES_TAGADAS = re.compile(r"^!+\s*\(")


@dataclass(frozen=True)
class Talalat:
    """Egy védtelen kötés: hol áll, mit köt, és melyik tag a védtelen."""

    fajl: str  # az `app/` gyökérhez képest, POSIX alakban
    sor: int
    tulajdonsag: str
    objektum: str
    tag: str
    kifejezes: str

    @property
    def kulcs(self) -> str:
        """Az alapállapot-lista kulcsa — sorszám NÉLKÜL.

        A sor a kódmozgatástól változik; ha a kulcs része lenne, minden
        beszúrás „új" tételt csinálna a listán szereplőből.
        """
        return f"{self.fajl}::{self.tulajdonsag}::{self.objektum}.{self.tag}"


@dataclass(frozen=True)
class Elemzes:
    """Egy futás nyers eredménye — a számokkal együtt, hogy kiírható legyen."""

    qml_fajlok: int
    vezerlok: frozenset[str]
    tipusos_kotesek: int
    orzott_hivatkozasok: int
    vedtelenek: tuple[Talalat, ...]


def _qml_szoveg(ut: Path) -> str:
    """A fájl kommentek nélkül, a SORTÖRÉSEK megtartásával."""
    szoveg = ut.read_text(encoding="utf-8", errors="replace")
    szoveg = _BLOKKOMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), szoveg)
    return _SORKOMMENT.sub("", szoveg)


def _sztringtelen(kifejezes: str) -> str:
    """A sztringliterálok helyén azonos hosszú töltelék — az indexek állnak."""
    return _SZTRING.sub(lambda m: '"' + "_" * (len(m.group(0)) - 2) + '"', kifejezes)


def kontextus_nevek(application_py: Path) -> set[str]:
    """A `setContextProperty("név", …)` hívásokkal regisztrált QML-nevek."""
    if not application_py.is_file():
        return set()
    fa = ast.parse(application_py.read_text(encoding="utf-8"))
    nevek: set[str] = set()
    for csomopont in ast.walk(fa):
        if (
            isinstance(csomopont, ast.Call)
            and isinstance(csomopont.func, ast.Attribute)
            and csomopont.func.attr == "setContextProperty"
            and csomopont.args
            and isinstance(csomopont.args[0], ast.Constant)
            and isinstance(csomopont.args[0].value, str)
        ):
            nevek.add(csomopont.args[0].value)
    return nevek


def _jobb_oldal(sorok: list[str], index: int, kezdet: str) -> str:
    """A kötés jobb oldala, a folytatósorokkal összefűzve."""
    darab = kezdet.strip()
    kovetkezo = index + 1
    lepes = 0
    while lepes < _MAX_FOLYTATAS and kovetkezo < len(sorok):
        sor = sorok[kovetkezo].strip()
        folytatodik = (
            not darab
            or darab.endswith(_FOLYTATAS_VEGE)
            or darab.count("(") > darab.count(")")
            or sor.startswith(_FOLYTATAS_ELEJE)
        )
        if not folytatodik:
            break
        darab = f"{darab} {sor}".strip()
        kovetkezo += 1
        lepes += 1
    return darab


def _kotesek(szoveg: str) -> list[tuple[int, str | None, str, str]]:
    """A fájl összes kötése: (sorszám, kiírt típus, név, jobb oldal)."""
    sorok = szoveg.splitlines()
    talalt: list[tuple[int, str | None, str, str]] = []
    for index, sor in enumerate(sorok):
        for egyezes in _KOTES.finditer(sor):
            tipus, nev = egyezes.group(1), egyezes.group(2)
            jobb = _jobb_oldal(sorok, index, sor[egyezes.end() :])
            talalt.append((index + 1, tipus, nev, jobb))
    return talalt


def _alias_e(jobb_oldal: str, vezerlo: str) -> bool:
    """Csak a vezérlőt (és a null-őr idiómát) tartalmazza-e a jobb oldal?

    `ctl: controller` → igen. `visible: controller ? controller.x : true` →
    nem: ott a `controller.x` már minősített hivatkozás, nem alias.
    """
    nev = re.escape(vezerlo)
    if not re.search(rf"\b{nev}\b", jobb_oldal):
        return False
    # A `typeof x !== "undefined"` őr EGÉSZBEN tűnjön el, különben az
    # `x !== null` alakú LOGIKAI kötés is aliasnak látszana.
    maradek = re.sub(
        rf"typeof\s+(?:\w+\s*\.\s*)*{nev}\s*[!=]==?\s*[\"']undefined[\"']",
        "",
        jobb_oldal,
    )
    maradek = re.sub(rf"(?:\b\w+\s*\.\s*)*\b{nev}\b", "@", maradek)
    maradek = _NULLOR_ZAJ.sub("", maradek)
    return bool(maradek) and set(maradek) <= {"@"}


def vezerlo_nevek(kotesek: list[tuple[int, str | None, str, str]], kontextusok: set[str]) -> frozenset[str]:
    """A kontextus-nevek és a belőlük feltöltött QML-tulajdonságok.

    A bővítés FIXPONTIG megy: a `ctl: controller` után az `info: grid.ctl`
    is vezérlő. Enélkül a `TrayBar.qml` `tray.ctl.heldCount` alakú kötése
    kimaradna a mérésből, pedig pont az a hibaosztály.
    """
    vezerlok = set(kontextusok)
    for _ in range(5):
        uj = {
            nev
            for _, _, nev, jobb in kotesek
            if nev not in vezerlok
            and nev not in _NEM_ALIAS
            and any(_alias_e(jobb, ismert) for ismert in vezerlok)
        }
        if not uj:
            break
        vezerlok |= uj
    return frozenset(vezerlok - _NEM_ALIAS)


def _felso_ternaris(kifejezes: str) -> int:
    """A legkülső ternáris `?` helye, vagy `-1`. A zárójelmélységet nézi."""
    melyseg = 0
    for index, jel in enumerate(kifejezes):
        if jel in "([{":
            melyseg += 1
        elif jel in ")]}":
            melyseg -= 1
        elif jel == "?" and melyseg == 0:
            # `?.` optional chaining és `??` nullish — egyik sem ternáris.
            if kifejezes[index + 1 : index + 2] not in (".", "?"):
                return index
    return -1


def _egesz_logikai(kifejezes: str) -> bool:
    """A jobb oldal EGÉSZE logikaivá van-e téve (`!(…)`, `!!(…)`)?

    Ilyenkor a benne álló `undefined` már nem jut el az értékadásig, tehát a
    kötés akkor sem hibázhat, ha a vezérlőn nincs meg a tulajdonság.
    """
    tomor = kifejezes.strip()
    egyezes = _TELJES_TAGADAS.match(tomor)
    if not egyezes:
        return False
    # A nyitó zárójel a kifejezés VÉGÉIG tart-e? Ha nem, a tagadás csak egy
    # részkifejezésre vonatkozik (`!(a) && ctl.b`), és az őr dolga marad.
    melyseg = 0
    for index in range(egyezes.end() - 1, len(tomor)):
        if tomor[index] == "(":
            melyseg += 1
        elif tomor[index] == ")":
            melyseg -= 1
            if melyseg == 0:
                return index == len(tomor) - 1
    return False


def _lancok(kifejezes: str) -> list[tuple[int, int, str, bool]]:
    """A kifejezés azonosító-láncai: (kezdet, vég, normalizált lánc, hívás-e)."""
    talalt = []
    for egyezes in _LANC.finditer(kifejezes):
        lanc = re.sub(r"\s*", "", egyezes.group(0))
        if lanc.split(".")[0] in _NEM_AZONOSITO:
            continue
        hivas = kifejezes[egyezes.end() :].lstrip().startswith("(")
        talalt.append((egyezes.start(), egyezes.end(), lanc, hivas))
    return talalt


def _vedett(kifejezes: str, objektum: str, tag: str) -> bool:
    """Áll-e a jobb oldalon `OBJ.TAG`-ra vonatkozó `undefined`-őr?"""
    minosites = rf"{re.escape(objektum)}\s*\.\s*{re.escape(tag)}"
    return bool(
        re.search(rf"{minosites}\s*[!=]==?\s*undefined", kifejezes)
        or re.search(rf"typeof\s+{minosites}\s*[!=]==?\s*[\"']undefined[\"']", kifejezes)
    )


def _vedtelen_tagok(kifejezes: str, vezerlok: frozenset[str]) -> tuple[list[tuple[str, str]], int]:
    """A kötés védtelen `(objektum, tag)` párjai és az őrzött hivatkozások száma.

    „Őrzött hivatkozás" = olyan `OBJ.TAG`, ahol az `OBJ` csupaszon is ott van
    (tehát a szerző null-őrt írt) és az `OBJ` vezérlő — akár védett, akár
    nem. Ez a minta POZITÍV KONTROLLJA: ha ez a szám nulla, az őr nem őriz
    semmit, és az `also_korlat_hibai()` megállítja a futást.
    """
    tiszta = _sztringtelen(kifejezes)
    lancok = _lancok(tiszta)
    csupasz = {lanc for _, _, lanc, hivas in lancok if not hivas}
    ternaris = _felso_ternaris(tiszta)
    logikai = _egesz_logikai(tiszta)

    orzott = 0
    vedtelen: list[tuple[str, str]] = []
    latott: set[tuple[str, str]] = set()
    for kezdet, veg, lanc, hivas in lancok:
        if "." not in lanc:
            continue
        objektum, _, tag = lanc.rpartition(".")
        if objektum not in csupasz or objektum.rpartition(".")[2] not in vezerlok:
            continue
        if (objektum, tag) not in latott:
            latott.add((objektum, tag))
            orzott += 1
        if hivas or logikai or _vedett(tiszta, objektum, tag):
            continue
        # A ternáris FELTÉTELE nem kerül a property-be, tehát nem hibázhat.
        if 0 <= ternaris and kezdet < ternaris:
            continue
        if _ELNYELI_UTANA.match(tiszta[veg:]) or _ELNYELI_ELOTTE.search(tiszta[:kezdet]):
            continue
        if (objektum, tag) not in vedtelen:
            vedtelen.append((objektum, tag))
    return vedtelen, orzott


def elemez(app_gyoker: Path) -> Elemzes:
    """A teljes vizsgálat egy `app/` fán."""
    qml_utak = sorted(app_gyoker.rglob("*.qml"))
    minden_kotes: list[tuple[int, str | None, str, str]] = []
    fajlonkent: list[tuple[str, list[tuple[int, str | None, str, str]]]] = []
    for ut in qml_utak:
        kotesek = _kotesek(_qml_szoveg(ut))
        fajlonkent.append((ut.relative_to(app_gyoker).as_posix(), kotesek))
        minden_kotes.extend(kotesek)

    vezerlok = vezerlo_nevek(minden_kotes, kontextus_nevek(app_gyoker / "application.py"))

    tipusos = 0
    orzott = 0
    vedtelenek: list[Talalat] = []
    for fajl, kotesek in fajlonkent:
        for sor, tipus, nev, jobb in kotesek:
            if tipus not in ("bool", "int", "real", "double") and nev not in _BEEPITETT_TIPUSOS:
                continue
            if tipus is not None and tipus not in ("bool", "int", "real", "double"):
                continue  # `property var visible` — a kiírt típus az erősebb
            tipusos += 1
            tagok, latott = _vedtelen_tagok(jobb, vezerlok)
            orzott += latott
            for objektum, tag in tagok:
                vedtelenek.append(
                    Talalat(
                        fajl=fajl,
                        sor=sor,
                        tulajdonsag=nev,
                        objektum=objektum,
                        tag=tag,
                        kifejezes=" ".join(jobb.split())[:120],
                    )
                )

    return Elemzes(
        qml_fajlok=len(qml_utak),
        vezerlok=vezerlok,
        tipusos_kotesek=tipusos,
        orzott_hivatkozasok=orzott,
        vedtelenek=tuple(vedtelenek),
    )


def also_korlat_hibai(elemzes: Elemzes) -> list[str]:
    """A vizsgálat ÉRDEMBEN lefutott-e? Üres halmazon minden őr zöld.

    Ez a projekt visszatérő tanulsága: a „nulla találat" ugyanúgy néz ki
    akkor is, ha minden rendben van, és akkor is, ha a minta már semmire nem
    illeszkedik. A három szám mindegyike POZITÍV kell legyen.
    """
    hibak: list[str] = []
    if elemzes.qml_fajlok == 0:
        hibak.append("egyetlen QML-fájlt sem találtam — rossz gyökér?")
    if not elemzes.vezerlok:
        hibak.append(
            "egyetlen vezérlő-nevet sem találtam (setContextProperty) — "
            "az őr így semmit nem vizsgál"
        )
    if elemzes.tipusos_kotesek == 0:
        hibak.append("egyetlen bool/int/real típusú kötést sem találtam")
    if elemzes.orzott_hivatkozasok == 0:
        hibak.append(
            "egyetlen őrzött vezérlő-hivatkozást sem találtam — a minta már "
            "nem illeszkedik semmire, tehát az őrnek nincs foga"
        )
    return hibak


def baseline_olvas(ut: Path) -> dict[str, str]:
    """Az alapállapot beolvasása: kulcs → indoklás.

    Formátum soronként: a kulcs (`fájl::tulajdonság::objektum.tag`), szóköz,
    majd az indoklás. A `#`-cal kezdődő és az üres sorok megjegyzések.
    Indoklás nélküli tétel HIBA: a néma engedély pontosan az, ami ide nem kell.
    """
    if not ut.is_file():
        raise FileNotFoundError(f"nincs alapállapot-fájl: {ut}")
    tetelek: dict[str, str] = {}
    for szam, nyers in enumerate(ut.read_text(encoding="utf-8").splitlines(), start=1):
        sor = nyers.strip()
        if not sor or sor.startswith("#"):
            continue
        kulcs, _, indoklas = sor.partition(" ")
        indoklas = indoklas.strip()
        if not indoklas:
            raise ValueError(f"{ut}:{szam}: a tételhez INDOKLÁS kell — {kulcs!r}")
        if kulcs in tetelek:
            raise ValueError(f"{ut}:{szam}: kétszer szereplő tétel — {kulcs!r}")
        tetelek[kulcs] = indoklas
    if len(tetelek) > MAX_BASELINE_ENTRIES:
        raise ValueError(
            f"{ut}: {len(tetelek)} tétel, a felső korlát {MAX_BASELINE_ENTRIES} — "
            "a lista csak rövidülhet (ld. MAX_BASELINE_ENTRIES a "
            "qml_undefined_or.py-ban)"
        )
    return tetelek


_JAVITAS_MINTA = (
    "  Írd át erre az alakra (a `!== undefined` a hiányzó TULAJDONSÁGRA véd):\n"
    "      valami: (ctl && ctl.tulajdonsag !== undefined)\n"
    "          ? ctl.tulajdonsag : <tartalék>\n"
    "  Ez a fa EGYSÉGES alakja: a tartalék és az érték változatlan marad,\n"
    "  csak a feltétel bővül. Logikai célnál a `? ctl.tulajdonsag === true`\n"
    "  is jó, ha a tulajdonság tényleg szigorúan `bool`.\n"
    "  Miért kell: a QML-próbák STUB-vezérlővel futnak, azon a frissen\n"
    "  bevezetett tulajdonság nincs meg — az `undefined` értékadás\n"
    "  `Unable to assign [undefined] to bool` hibát dob, és a #1260 őre\n"
    "  ettől olyan tesztfájlokon is bukik, amelyeknek semmi közük hozzá."
)


def _szamok(elemzes: Elemzes) -> None:
    """A számok kiírása — ugyanaz a fejléc az ellenőrzésnél és a listánál."""
    print(
        f"{elemzes.qml_fajlok} QML-fájl, {len(elemzes.vezerlok)} vezérlő-név, "
        f"{elemzes.tipusos_kotesek} bool/int/real kötés, "
        f"{elemzes.orzott_hivatkozasok} őrzött vezérlő-hivatkozás, "
        f"{len(elemzes.vedtelenek)} védtelen"
    )


def ellenoriz(app_gyoker: Path, baseline_ut: Path) -> int:
    """Ellenőrzés az alapállapothoz mérve. 0 = nincs eltérés."""
    elemzes = elemez(app_gyoker)
    _szamok(elemzes)

    hibak = also_korlat_hibai(elemzes)
    if hibak:
        print("\nA VIZSGÁLAT ÜRES — így a zöld eredmény semmit nem bizonyít:")
        for hiba in hibak:
            print(f"  {hiba}")
        return 2

    baseline = baseline_olvas(baseline_ut)
    talalt = {talalat.kulcs: talalat for talalat in elemzes.vedtelenek}
    uj = sorted(set(talalt) - set(baseline))
    elavult = sorted(set(baseline) - set(talalt))

    if not uj and not elavult:
        print(f"Rendben: mind a {len(talalt)} védtelen kötés szerepel az alapállapotban.")
        return 0

    if uj:
        print(f"\nVÉDTELEN KÖTÉS ({len(uj)}) — a hiányzó tulajdonság `undefined`-ot ad:")
        for kulcs in uj:
            talalat = talalt[kulcs]
            print(f"  {talalat.fajl}:{talalat.sor}: {talalat.tulajdonsag}")
            print(f"      {talalat.kifejezes}")
            print(f"      védtelen: {talalat.objektum}.{talalat.tag}")
        print(f"\n{_JAVITAS_MINTA}")
        print(
            "  Ha a kötés tényleg nem javítható: vedd fel INDOKLÁSSAL — "
            f"{baseline_ut.name} (és emeld a plafont)."
        )
    if elavult:
        print(f"\nELAVULT bejegyzés ({len(elavult)}) — a lista tétele már védett:")
        for kulcs in elavult:
            print(f"  {kulcs}  ({baseline[kulcs]})")
        print(f"\n  Töröld a sorát: {baseline_ut.name} — a lista csak rövidülhet.")
    return 1


def main(argv: list[str] | None = None) -> int:
    """Parancssori belépési pont."""
    ertelmezo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ertelmezo.add_argument(
        "--app",
        type=Path,
        default=_DEFAULT_APP,
        help="a vizsgált felület-fa (alapértelmezés: src/picasapy/app)",
    )
    ertelmezo.add_argument(
        "--baseline",
        type=Path,
        default=_DEFAULT_BASELINE,
        help="az alapállapot-fájl útvonala",
    )
    ertelmezo.add_argument(
        "--list",
        action="store_true",
        dest="listaz",
        help="csak a mai védtelen kötések kiírása, alapállapot nélkül",
    )
    args = ertelmezo.parse_args(argv)

    if not args.app.is_dir():
        print(f"nincs ilyen könyvtár: {args.app}", file=sys.stderr)
        return 2

    if args.listaz:
        elemzes = elemez(args.app)
        _szamok(elemzes)
        for talalat in elemzes.vedtelenek:
            print(f"  {talalat.fajl}:{talalat.sor}: {talalat.kulcs}")
            print(f"      {talalat.kifejezes}")
        return 0

    try:
        return ellenoriz(args.app, args.baseline)
    except (FileNotFoundError, ValueError) as hiba:
        print(f"hibás alapállapot: {hiba}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
