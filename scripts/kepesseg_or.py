#!/usr/bin/env python3
"""A felületről elérhetetlen vezérlő-képességek őre — #1476.

**A hibaosztály.** A vezérlőn kész a képesség (`@Slot`/`@Property`), a
felület nem éri el, és a **tesztkészlet zöld marad** — mert a teszt
közvetlenül a vezérlőt hívja, nem a felületet. Egyetlen napon (2026-08-25)
négyszer harapott meg minket: #1454 (fanézet), #1468 (menüpipa), #1471
(Címkék/Helyek), #1472 (Nyomtatás). A mérést mindannyiszor kézzel kellett
elvégezni, és a leltár másnapra elavult.

**Mit mér.** Minden `setContextProperty`-vel regisztrált objektum minden
`@Slot`/`@Property` tagjára (az öröklött mixin-tagokat is beleértve)
megnézi, hivatkozik-e rá a QML. Ami nincs hivatkozva, az **szakadás**.

**Minősített keresés — ez a lényeg.** A puszta ``.tagnév`` keresés
FÉLREVEZET: négy tagnév két vezérlőn is szerepel (`cancelScan`,
`revision`, `statusText`, `toggleStar`), és a naiv keresés ilyenkor
**élőnek látja a halottat** — a #1476 jegy szerzője maga is beleesett, a
`faceScanController.cancelScan`-t a `dedupController.cancelScan` hívásai
tartották látszólag életben. Ezért az őr mindig ``<objektum>.<tag>``
alakot keres.

**Aliasok.** A QML gyakran nem a kontextus-objektumot írja le, hanem egy
saját tulajdonságba köti (``readonly property var ctl: controller``), és
azt is továbbadja a gyerek-komponensnek
(``FolderHierarchyView { hierarchy: pane.hierarchyController }``). Az őr
ezért **tranzitívan** feloldja az aliasokat: alias csak az a kötés lehet,
aminek a jobb oldala a null-őr idiómán kívül SEMMI mást nem tartalmaz
(``typeof x !== "undefined" ? x : null``). Egy értékkötés
(``visible: controller ? controller.searchActive : true``) NEM alias — de
nem is vész el, mert abban a ``controller.searchActive`` hivatkozás
minősített alakban ott van.

**Az alias hatóköre a FÁJL (#1490).** A QML-ben egy tulajdonság annak a
komponensnek — azaz annak a fájlnak — a névterébe tartozik, amelyik
DEKLARÁLJA. Az őr ezért fájlonként külön névteret tart. Enélkül egy
gyakori rövidítés (`ctl`) két fájlban két különböző vezérlőre mutatva
kétértelműnek látszott, és az őr — konzervatívan — MINDKETTŐT eldobta:
egyetlen új fájl 20 élő hivatkozást tüntetett el a látóköréből, azaz
ugyanennyi tagot mutatott volna hamisan „elérhetetlennek". Ez a ROSSZ
irány: nem elhallgat hibát, hanem nem létezőt jelent.

**Keresztfájlos átadás.** A `Main.qml`-ben álló
``FolderHierarchyView { hierarchy: pane.hierarchyController }`` értékadás
NEM a `Main.qml` névterét bővíti: a `hierarchy` tulajdonságot a
`FolderHierarchyView.qml` deklarálja, tehát az álnév OTT él — ott is
használják. Az őr ezért az ÉRTÉKADÁST a tulajdonságot DEKLARÁLÓ fájl(ok)
névterébe könyveli, a jobb oldalát viszont az értékadás saját fájljának
névterében oldja fel (így marad meg a `Main` → `FolderPane` →
`FolderHierarchyView` lánc).

Ha egy aliasnév EGY FÁJLON BELÜL több kontextus-objektumra is mutat (ilyen
a `Connections` ``target``-je, vagy ugyanannak a komponensnek két, más-más
vezérlőt kapó példánya), az őr eldobja: onnantól a rajta keresztüli
hivatkozás nem számít élőnek. Ez a **konzervatív** irány — inkább hamis
szakadást jelentsen, mint hamis életet.

**Amit szándékosan NEM néz.** A Pythonból hívott, ``_``-sal kezdődő belső
slotokat (jelzés-fogadók, nem felületi tagok). A tesztekből érkező
hivatkozás SOHA nem számít életnek: pontosan ettől marad ma zöld a
készlet.

**Az alapállapot.** A bevezetéskor a fában több tucat szakadás állt;
azokra azonnal pirosra váltani a main-t nem lehet. A mai állapot tételes,
INDOKLÁSSAL ellátott listában áll (``kepesseg_or_baseline.txt``). Az őr
akkor bukik, ha

* **ÚJ** szakadás keletkezik (nincs a listán), vagy
* a listán olyan tétel van, ami már nem szakadás (**elavult** bejegyzés),
  vagy
* a lista hosszabb a bevezetéskori méretnél (``MAX_BASELINE_ENTRIES``) —
  egy sor beírásával az őr különben kikerülhető lenne.

Így a lista rövidülhet, de nem hízhat észrevétlenül.

**ALSÓ KORLÁT — enélkül az őr üresen is zöld.** A „0 elérhetetlen tag"
elgépelt minta, rossz útvonal és megváltozott mappaszerkezet mellett is
igaz. Ez a hibafajta 2026-08-25-én háromszor harapott meg minket. Az őr
ezért minden futáskor kimondja, hogy talált kontextus-objektumot, tagot,
QML-fájlt ÉS élő hivatkozást is; ha bármelyik nulla, **2-es kilépési
kóddal megáll**, nem „hibátlant" jelent.

**A generált leltárba nem kerül volatilis szám (#1508).** A blokk sokáig
fájl- és tagszámot is hordozott, és egy teszt bitre egyezést követelt tőle.
Ettől **minden ág elbukott, amelyik akár egyetlen `.py`- vagy QML-fájlt
hozzáadott** — valódi szakadás nélkül; egy nap alatt négy PR és három
merge-ütközés jött belőle. A számok azóta a futás KIMENETÉBEN állnak
(CI-napló), ahol nincs mit karbantartani; a lapon csak a lényegi tartalom
marad: maga a szakadás-lista. A védelmet ez nem gyengíti — az új szakadást
az őr **kilépőkódja** fogja meg, nem a dokumentum szövege.

**A generált leltárban a POZÍCIÓ nem egyenlőségi feltétel (#1523).** A #1508
kivette a terjedelmi számokat, de a rothadás másik alakja megmaradt: a tábla
`hely` oszlopa `fájl:sor` volt, az árva osztályoké darabszámot hordozott, és a
`test_a_leltar_generalt_blokkja_naprakesz` bitre egyezést kért. Ettől **egyetlen
sor beszúrása** egy olyan fájlba, amelyben történetesen van szakadás, megbuktatta
a készletet — szakadás nélkül. 2026-08-26-án két PR (#1520, #1521) fizetett
ezért egy fölösleges kört (piros CI → `--ir` → új push → új CI), és merge-ütközést
is termelt.

A szabály tehát: **a lapon a szakadás AZONOSSÁGA áll** (kontextus-objektum, tag,
fajta, fájl, indoklás) — ez a valódi védelem, és ez bitre egyezik. A **pontos sor
és a tagszám a futás kimenetében** van (`--list`, illetve az új szakadás
hibaüzenete), ahol minden futáskor frissen mérve áll, és nincs mit karbantartani.
A fájlnév azért MARAD a lapon, mert tagnévvel együtt `grep -n`-nel pontos
találatot ad, és nem mozdul el egy fölötte beszúrt sortól.

Aki vissza akarja tenni a sorszámot: a lapra írt sor a következő idegen ág
piros CI-jában bukik ki, nem itt. Két visszacsúszás-őr tiltja
(`test_a_valodi_leltar_blokkban_nincs_sorszam`,
`…_nincs_osztaly_tagszam`).

Használat::

    python scripts/kepesseg_or.py            # ellenőrzés (CI)
    python scripts/kepesseg_or.py --list     # a mai szakadások
    python scripts/kepesseg_or.py --leltar   # a leltár-tábla (Markdown)
    python scripts/kepesseg_or.py --leltar --ir   # …a leltárba írva is

Kilépési kód: 0 ha nincs eltérés az alapállapottól, 1 ha van, 2 ha a
vizsgálat maga hibás (üres bemenet, hiányzó könyvtár, rossz lista).
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_APP = _REPO_ROOT / "src" / "picasapy" / "app"
_DEFAULT_BASELINE = Path(__file__).resolve().parent / "kepesseg_or_baseline.txt"
_DEFAULT_LELTAR = _REPO_ROOT / "docs" / "specs" / "lanc-szakadasok-leltar.md"

#: Az alapállapot FELSŐ korlátja — a bevezetéskori tételszám.
#:
#: Az „új szakadás = piros CI" szabályt egy sor beírásával ki lehetne
#: kerülni. Ez a plafon ezt TUDATOS lépéssé teszi: új tételhez a számot is
#: emelni kell, azt pedig a felülvizsgálat látja. Ahogy a lista fogy, ezt a
#: számot ÉRDEMES lejjebb vinni — csökkenteni szabad, emelni csak
#: indoklással.
# #455: 37 → 40 volt, mert a képtálca modellje EGY jeggyel a felülete előtt
# készült el. #1276: a `trayItems`/`trayUnusedCount`/`setTrayUsedRows` bekötve a
# kollázs „Klipek" lapjára, a három sor TÖRÖLVE, a plafon VISSZA 37-re —
# ahogy a #455 kommentje előírta. A szám csökkentése így nem külön döntés
# volt, hanem a jegy zárásának kötelező része.
MAX_BASELINE_ENTRIES = 37

#: Az osztály-szintű kivételek felső korlátja — ugyanaz a logika.
MAX_OSZTALY_ENTRIES = 3

#: A leltárban a generált blokk határai.
LELTAR_KEZDET = "<!-- KEPESSEG_OR:KEZDET -->"
LELTAR_VEGE = "<!-- KEPESSEG_OR:VEGE -->"

#: Sorkomment. A `(?<!:)` őrzi a `http://` és `image://` alakú URL-eket:
#: nélküle a sor maradékát — benne egy esetleges vezérlő-hivatkozással —
#: kommentnek néznénk.
_SORKOMMENT = re.compile(r"(?<!:)//[^\n]*")
_BLOKKOMMENT = re.compile(r"/\*.*?\*/", re.S)

#: Egy QML-kötés bal oldala: `név:`, akár `property var` deklarációval.
#:
#: A `(?:^|[{;])` előtag miatt az egysoros alak is látszik
#: (`Panel { ctl: controller }`), a ternáris `cond ? controller : null`
#: KÖZÉPSŐ kettőspontja viszont nem — az nem sor eleje és nem `{`/`;` után áll.
#: A jobb oldalt szándékosan NEM fogja csoportba: úgy a `finditer` egyetlen
#: soron TÖBB kötést is megtalál.
#:
#: Az 1. csoport (a `property var`/`property alias` kulcsszó) azt mondja meg,
#: DEKLARÁCIÓ-e a kötés — ettől függ az álnév hatóköre (#1490): a deklaráció
#: a saját fájljában nyit nevet, a puszta értékadás a tulajdonságot deklaráló
#: fájl(ok)ban.
_KOTES = re.compile(
    r"(?:^|[{;])\s*(?:readonly\s+)?(property\s+(?:var|alias)\s+)?(\w+)\s*:"
)

#: Tulajdonság-DEKLARÁCIÓ, kezdőérték nélkül is (`property var hierarchy`).
#: Ez adja meg, MELYIK fájl névterébe tartozik egy kívülről beállított név.
_TULAJDONSAG_DEKL = re.compile(r"\bproperty\s+(?:var|alias)\s+(\w+)\b")

#: A kötés jobb oldala folytatódik a következő sorban, ha ezekre végződik.
_FOLYTATAS_VEGE = ("?", ":", "(", "&&", "||", "!==", "===", "!=", "==", ",")

#: …vagy ha a következő sor ezekkel kezdődik (tördelt ternáris).
_FOLYTATAS_ELEJE = ("?", ".", ":", "&&", "||")

#: A null-őr idióma szótöredékei: ha a jobb oldalról ezeket ÉS a jelölt
#: objektumnevet elhagyva nem marad semmi, akkor a kötés valódi alias.
#:
#: Összehasonlító jel (`!==`) itt SZÁNDÉKOSAN nincs: az `x !== null` egy
#: LOGIKAI érték, nem alias (`enabled: root.dropController !== null`). A
#: `typeof … !== "undefined"` alakot ezért egészben, előbb töröljük.
_NULLOR_ZAJ = re.compile(r"\bundefined\b|\bnull\b|&&|\|\||[(){}?:;\s]")

#: Jelzéskezelő (`onClicked:`) — sosem alias.
_JELZESKEZELO = re.compile(r"on[A-Z]")

#: Regisztrációk, amelyek NEM QObject-ek, tehát nincs mit végignézni rajtuk.
#:
#: Tételes lista, nem minta: így minden ÚJ, osztályra vissza nem vezethető
#: regisztráció megállítja az őrt (2-es kilépési kód), ahelyett hogy némán
#: kimaradna a mérésből. Az `appVersion` a `version_string()` eredménye,
#: azaz sztring.
_NEM_QOBJECT = frozenset({"appVersion"})

#: SOSEM alias, akkor sem, ha a jobb oldala pont egy kontextus-objektum.
#:
#: A `Connections { target: controller }` a fában 12 KÜLÖNBÖZŐ objektumra
#: mutat, és a `target.valami` alak máshol (pl. `TextFieldContextMenu.qml`)
#: egy sima beviteli mezőt jelent. Aliasként kezelve az őr ezek tagjait
#: hamisan élőnek látná — a kétértelműség-szabály ma úgyis eldobná, de a
#: kimondott lista attól is véd, ha egyszer csak EGY célra mutatna.
_NEM_ALIAS = frozenset({"target"})


@dataclass(frozen=True)
class Tag:
    """Egy kontextus-objektumon elérhető `@Slot`/`@Property` tag."""

    kontextus: str
    nev: str
    fajta: str
    fajl: str
    sor: int

    @property
    def kulcs(self) -> str:
        """A kivétellistában és a hibaüzenetekben használt minősített név."""
        return f"{self.kontextus}.{self.nev}"


@dataclass(frozen=True)
class ArvaOsztaly:
    """QML-tagokat hordozó osztály, amit egyetlen kontextus-objektum sem ér el."""

    nev: str
    fajl: str
    tagszam: int


@dataclass(frozen=True)
class Kotes:
    """Egy QML-kötés: hol áll, mit köt, és deklaráció-e.

    A `deklaracio` dönti el az álnév hatókörét (#1490): a
    ``property var ctl: controller`` a SAJÁT fájljában nyit nevet, a
    puszta ``hierarchy: pane.hierarchyController`` értékadás viszont annak
    a fájlnak a névterébe, amelyik a `hierarchy` tulajdonságot deklarálja.
    """

    fajl: str
    bal: str
    jobb: str
    deklaracio: bool


@dataclass
class Elemzes:
    """Egy forrásfa mérési eredménye."""

    kontextusok: dict[str, str] = field(default_factory=dict)
    nem_qobject: list[str] = field(default_factory=list)
    feloldatlan: list[str] = field(default_factory=list)
    #: (QML-fájl, aliasnév) → kontextus-objektum. A kulcs azért PÁR, mert
    #: az álnév hatóköre a fájl (#1490): ugyanaz a rövidítés két fájlban
    #: két különböző vezérlőt jelenthet.
    aliasok: dict[tuple[str, str], str] = field(default_factory=dict)
    #: (QML-fájl, aliasnév) → a fájlon BELÜL kétértelmű célok; eldobva.
    tobbertelmu_alias: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    tagok: list[Tag] = field(default_factory=list)
    hivatkozott: set[tuple[str, str]] = field(default_factory=set)
    szakadasok: list[Tag] = field(default_factory=list)
    arva_osztalyok: list[ArvaOsztaly] = field(default_factory=list)
    py_fajlok: int = 0
    qml_fajlok: int = 0

    def elo(self, kontextus: str, tag: str) -> bool:
        """Hivatkozik-e a QML a MINŐSÍTETT `<kontextus>.<tag>` alakra."""
        return (kontextus, tag) in self.hivatkozott


# -- 1. a Python oldal: kontextus-objektumok és tagjaik ---------------------


def _dekorator_neve(dekorator: ast.expr) -> str | None:
    hivott = dekorator.func if isinstance(dekorator, ast.Call) else dekorator
    if isinstance(hivott, ast.Name):
        return hivott.id
    if isinstance(hivott, ast.Attribute):
        return hivott.attr
    return None


def _osztalyok(app_gyoker: Path) -> tuple[dict[str, tuple[str, list[str], list[Tag]]], int]:
    """Osztálynév → (fájl, ősök, saját `@Slot`/`@Property` tagok).

    A tagok `kontextus` mezője itt még üres — azt a regisztráció tölti ki.
    """
    talalt: dict[str, tuple[str, list[str], list[Tag]]] = {}
    fajlok = sorted(app_gyoker.rglob("*.py"))
    for py in fajlok:
        fa = ast.parse(py.read_text(encoding="utf-8"))
        for csomopont in ast.walk(fa):
            if not isinstance(csomopont, ast.ClassDef):
                continue
            osok = [
                os_.id if isinstance(os_, ast.Name) else getattr(os_, "attr", None)
                for os_ in csomopont.bases
            ]
            tagok: list[Tag] = []
            for elem in csomopont.body:
                if not isinstance(elem, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                for dekorator in elem.decorator_list:
                    fajta = _dekorator_neve(dekorator)
                    if fajta in ("Slot", "Property"):
                        tagok.append(
                            Tag(
                                kontextus="",
                                nev=elem.name,
                                fajta=fajta,
                                fajl=str(py.relative_to(app_gyoker)),
                                sor=elem.lineno,
                            )
                        )
                        break
            talalt[csomopont.name] = (
                str(py.relative_to(app_gyoker)),
                [os_ for os_ in osok if os_],
                tagok,
            )
    return talalt, len(fajlok)


def _regisztraciok(application_py: Path) -> dict[str, str | None]:
    """`setContextProperty("név", objektum)` → QML-név → JELÖLT osztálynév.

    A `None` azt jelenti: az érték nem vezethető vissza konstruktorhívásra.
    Hogy melyik jelöltből lesz valódi kontextus-objektum, azt az `elemez()`
    dönti el — csak az, amit meg is talál osztályként. A többit NEM nyeli
    le: a fel nem oldott regisztrációt az `also_korlat_hibai()` jelenti,
    mert egy némán kihagyott objektum tagjai észrevétlenül szakadnának el.
    """
    fa = ast.parse(application_py.read_text(encoding="utf-8"))
    valtozo_osztalya: dict[str, str] = {}
    for csomopont in ast.walk(fa):
        if (
            isinstance(csomopont, ast.Assign)
            and len(csomopont.targets) == 1
            and isinstance(csomopont.targets[0], ast.Name)
        ):
            ertek = csomopont.value
            # ⚠️ FELTÉTELES példányosítás (#1472): a védett importú
            # vezérlők így születnek —
            #     x = Osztaly(...) if Osztaly is not None else None
            # mert a modulja (pl. `QtPrintSupport`) Debianon külön csomag
            # (#664). Az osztályt a POZITÍV ág adja; enélkül az őr „fel nem
            # oldott regisztrációt" jelentene, és a vezérlő MINDEN tagja
            # némán kimaradna a méréséből.
            if isinstance(ertek, ast.IfExp):
                ertek = ertek.body
            if isinstance(ertek, ast.Call):
                hivott = ertek.func
                nev = (
                    hivott.id
                    if isinstance(hivott, ast.Name)
                    else getattr(hivott, "attr", None)
                )
                if nev:
                    valtozo_osztalya[csomopont.targets[0].id] = nev
        if isinstance(csomopont, ast.FunctionDef):
            # A `main(controller: AppController, ...)` alakú paraméterek is
            # kontextusba kerülhetnek — az annotáció adja az osztályt.
            for parameter in [*csomopont.args.args, *csomopont.args.kwonlyargs]:
                jelzes = parameter.annotation
                if isinstance(jelzes, ast.Name):
                    valtozo_osztalya.setdefault(parameter.arg, jelzes.id)
                elif isinstance(jelzes, ast.Constant) and isinstance(jelzes.value, str):
                    valtozo_osztalya.setdefault(parameter.arg, jelzes.value)

    jeloltek: dict[str, str | None] = {}
    for csomopont in ast.walk(fa):
        if not (
            isinstance(csomopont, ast.Call)
            and isinstance(csomopont.func, ast.Attribute)
            and csomopont.func.attr == "setContextProperty"
            and len(csomopont.args) == 2
            and isinstance(csomopont.args[0], ast.Constant)
        ):
            continue
        qml_nev = csomopont.args[0].value
        ertek = csomopont.args[1]
        if isinstance(ertek, ast.Name):
            jeloltek[qml_nev] = valtozo_osztalya.get(ertek.id)
        elif isinstance(ertek, ast.Call) and isinstance(ertek.func, ast.Name):
            jeloltek[qml_nev] = ertek.func.id
        else:
            jeloltek[qml_nev] = None
    return jeloltek


def _orokolt_tagok(
    osztaly: str,
    osztalyok: dict[str, tuple[str, list[str], list[Tag]]],
    latott: set[str] | None = None,
) -> list[Tag]:
    """Az osztály saját ÉS örökölt tagjai (a mixinek is idetartoznak)."""
    latott = set() if latott is None else latott
    if osztaly in latott or osztaly not in osztalyok:
        return []
    latott.add(osztaly)
    _, osok, tagok = osztalyok[osztaly]
    eredmeny = list(tagok)
    for os_ in osok:
        eredmeny.extend(_orokolt_tagok(os_, osztalyok, latott))
    return eredmeny


# -- 2. a QML oldal: aliasok és minősített hivatkozások ---------------------


def _qml_szoveg(ut: Path) -> str:
    """A fájl kommentek nélkül — a kikommentelt kód NEM bekötés."""
    return _SORKOMMENT.sub("", _BLOKKOMMENT.sub(" ", ut.read_text(encoding="utf-8")))


def _kotes_jobb_oldala(sorok: list[str], index: int, kezdet: str) -> str:
    """A kötés jobb oldala, legfeljebb két folytatósorral összefűzve."""
    darab = kezdet.strip()
    kovetkezo = index + 1
    lepes = 0
    while lepes < 2 and kovetkezo < len(sorok):
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


def _alias_e(jobb_oldal: str, nevter_elem: str) -> bool:
    """Csak az objektumot (és a null-őr idiómát) tartalmazza-e a jobb oldal?

    `ctl: controller` → igen. `visible: controller ? controller.x : true` →
    nem: ott a `controller.x` már minősített hivatkozás, nem alias.
    """
    nev = re.escape(nevter_elem)
    if not re.search(rf"\b{nev}\b", jobb_oldal):
        return False
    # 1. A `typeof x !== "undefined"` őr EGÉSZBEN tűnjön el — így az
    #    `x !== null` alakú LOGIKAI kötés nem látszik aliasnak.
    maradek = re.sub(
        rf"typeof\s+(?:\w+\s*\.\s*)?{nev}\s*[!=]==?\s*[\"']undefined[\"']", "", jobb_oldal
    )
    # 2. A `pane.hierarchyController` alakú, id-del minősített hivatkozás is
    #    alias-forrás: a bal oldal ilyenkor a gyerek-komponens tulajdonsága
    #    (`FolderHierarchyView { hierarchy: pane.hierarchyController }`).
    maradek = re.sub(rf"(?:\b\w+\s*\.\s*)?\b{nev}\b", "@", maradek)
    maradek = _NULLOR_ZAJ.sub("", maradek)
    return bool(maradek) and set(maradek) <= {"@"}


def _kotesek(qml_szovegek: dict[str, str], kontextusok: set[str]) -> list[Kotes]:
    """A fa ÖSSZES alias-jelölt kötése, a fájljával és a fajtájával együtt.

    Kimarad, ami eleve nem lehet alias: a kontextus-objektum nevének
    újrakötése, a `_NEM_ALIAS` tételei és a jelzéskezelők.
    """
    kotesek: list[Kotes] = []
    for fajl, szoveg in qml_szovegek.items():
        sorok = szoveg.splitlines()
        for index, sor in enumerate(sorok):
            for egyezes in _KOTES.finditer(sor):
                bal = egyezes.group(2)
                if bal in kontextusok or bal in _NEM_ALIAS or _JELZESKEZELO.match(bal):
                    continue
                kotesek.append(
                    Kotes(
                        fajl=fajl,
                        bal=bal,
                        jobb=_kotes_jobb_oldala(sorok, index, sor[egyezes.end() :]),
                        deklaracio=egyezes.group(1) is not None,
                    )
                )
    return kotesek


def _deklaralo_fajlok(qml_szovegek: dict[str, str]) -> dict[str, set[str]]:
    """Tulajdonságnév → azok a fájlok, amelyek DEKLARÁLJÁK.

    Ez adja meg egy kívülről beállított név hatókörét: a `PrintDialog
    { printCtl: printController }` értékadás a `Main.qml`-ben áll, de a
    `printCtl` a `PrintDialog.qml` tulajdonsága — a rajta át vezető
    hivatkozások is ott lesznek.
    """
    talalt: dict[str, set[str]] = {}
    for fajl, szoveg in qml_szovegek.items():
        for egyezes in _TULAJDONSAG_DEKL.finditer(szoveg):
            talalt.setdefault(egyezes.group(1), set()).add(fajl)
    return talalt


def _ures_nevterek(
    qml_szovegek: dict[str, str], kontextusok: set[str]
) -> dict[str, dict[str, str]]:
    """Fájlonkénti kiindulási névtér: a kontextus-objektumok önmagukra.

    A `setContextProperty`-vel regisztrált nevek MINDEN fájlban látszanak —
    csak az aliasok fájlfüggők.
    """
    alap = {nev: nev for nev in kontextusok}
    return {fajl: dict(alap) for fajl in qml_szovegek}


def _aliasok(
    qml_szovegek: dict[str, str], kontextusok: set[str]
) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], set[str]]]:
    """(fájl, aliasnév) → kontextus-objektum, tranzitívan és FÁJLONKÉNT.

    Két külön kérdést kell megválaszolni minden kötésre:

    * **melyik fájl névterébe kerül a bal oldal?** Deklarációnál a sajátjába,
      értékadásnál a tulajdonságot deklaráló fájl(ok)éba (#1490);
    * **mit jelent a jobb oldal?** Azt mindig a kötés SAJÁT fájljának
      névterében kell feloldani — így marad élő a `Main.qml` → `FolderPane`
      → `FolderHierarchyView` lánc, ahol minden lépés más fájlban áll.

    A fájlon BELÜL több kontextus-objektumra mutató neveket az őr eldobja,
    és külön visszaadja — azokon át nem számít élőnek semmi.
    """
    kotesek = _kotesek(qml_szovegek, kontextusok)
    deklaralok = _deklaralo_fajlok(qml_szovegek)

    jelolt: dict[tuple[str, str], set[str]] = {}
    nevterek = _ures_nevterek(qml_szovegek, kontextusok)
    for _ in range(5):  # a fában a láncok legfeljebb 2-3 hosszúak
        valtozott = False
        for kotes in kotesek:
            cel_fajlok = (
                {kotes.fajl} if kotes.deklaracio else deklaralok.get(kotes.bal, set())
            )
            if not cel_fajlok:
                continue
            for forras, cel in nevterek[kotes.fajl].items():
                if kotes.bal == forras or not _alias_e(kotes.jobb, forras):
                    continue
                for cel_fajl in cel_fajlok:
                    kulcs = (cel_fajl, kotes.bal)
                    if cel not in jelolt.get(kulcs, set()):
                        jelolt.setdefault(kulcs, set()).add(cel)
                        valtozott = True
        nevterek = _ures_nevterek(qml_szovegek, kontextusok)
        for (fajl, nev), celok in jelolt.items():
            if len(celok) == 1:
                nevterek[fajl][nev] = next(iter(celok))
        if not valtozott:
            break
    aliasok = {kulcs: next(iter(celok)) for kulcs, celok in jelolt.items() if len(celok) == 1}
    tobbertelmu = {kulcs: celok for kulcs, celok in jelolt.items() if len(celok) > 1}
    return aliasok, tobbertelmu


def _hivatkozasok(
    qml_szovegek: dict[str, str], nevterek: dict[str, dict[str, str]]
) -> set[tuple[str, str]]:
    """A QML-ben MINŐSÍTETT alakban előforduló `(kontextus, tag)` párok.

    Minden fájlt a SAJÁT névterével néz végig (#1490): ugyanaz a rövidítés
    a szomszéd fájlban másik vezérlőt — vagy semmit — jelenthet.
    """
    talalt: set[tuple[str, str]] = set()
    for fajl, szoveg in qml_szovegek.items():
        for nev, kontextus in nevterek[fajl].items():
            for egyezes in re.finditer(rf"\b{re.escape(nev)}\s*\.\s*(\w+)", szoveg):
                talalt.add((kontextus, egyezes.group(1)))
    return talalt


# -- 3. a mérés ------------------------------------------------------------


def elemez(app_gyoker: Path) -> Elemzes:
    """Végigméri a vezérlők tagjait és a QML-ből való elérhetőségüket."""
    application_py = app_gyoker / "application.py"
    if not application_py.is_file():
        raise FileNotFoundError(f"nincs application.py itt: {app_gyoker}")

    osztalyok, py_fajlok = _osztalyok(app_gyoker)
    kontextusok: dict[str, str] = {}
    nem_qobject: list[str] = []
    feloldatlan: list[str] = []
    for qml_nev, jelolt in _regisztraciok(application_py).items():
        if jelolt in osztalyok:
            kontextusok[qml_nev] = jelolt
        elif qml_nev in _NEM_QOBJECT:
            nem_qobject.append(qml_nev)
        else:
            feloldatlan.append(qml_nev)

    qml_szovegek: dict[str, str] = {}
    for minta in ("*.qml", "*.js"):
        for ut in sorted((app_gyoker / "qml").rglob(minta)):
            qml_szovegek[str(ut.relative_to(app_gyoker))] = _qml_szoveg(ut)

    aliasok, tobbertelmu = _aliasok(qml_szovegek, set(kontextusok))
    nevterek = _ures_nevterek(qml_szovegek, set(kontextusok))
    for (fajl, nev), cel in aliasok.items():
        nevterek[fajl][nev] = cel
    hivatkozott = _hivatkozasok(qml_szovegek, nevterek)

    tagok: list[Tag] = []
    for qml_nev, osztaly in sorted(kontextusok.items()):
        egyedi: dict[str, Tag] = {}
        for tag in _orokolt_tagok(osztaly, osztalyok):
            # A `_`-sal kezdődő slot Python-belső jelzésfogadó, nem felületi tag.
            if not tag.nev.startswith("_"):
                egyedi.setdefault(tag.nev, tag)
        for tag in egyedi.values():
            tagok.append(
                Tag(
                    kontextus=qml_nev,
                    nev=tag.nev,
                    fajta=tag.fajta,
                    fajl=tag.fajl,
                    sor=tag.sor,
                )
            )

    szakadasok = sorted(
        (tag for tag in tagok if (tag.kontextus, tag.nev) not in hivatkozott),
        key=lambda tag: (tag.kontextus, tag.fajl, tag.sor),
    )

    elert: set[str] = set()

    def _bejar(osztaly: str) -> None:
        if osztaly in elert or osztaly not in osztalyok:
            return
        elert.add(osztaly)
        for os_ in osztalyok[osztaly][1]:
            _bejar(os_)

    for osztaly in kontextusok.values():
        _bejar(osztaly)
    arvak = [
        ArvaOsztaly(nev=nev, fajl=adat[0], tagszam=len(adat[2]))
        for nev, adat in sorted(osztalyok.items())
        if nev not in elert and adat[2]
    ]

    return Elemzes(
        kontextusok=kontextusok,
        nem_qobject=nem_qobject,
        feloldatlan=feloldatlan,
        aliasok=aliasok,
        tobbertelmu_alias=tobbertelmu,
        tagok=tagok,
        hivatkozott=hivatkozott,
        szakadasok=szakadasok,
        arva_osztalyok=arvak,
        py_fajlok=py_fajlok,
        qml_fajlok=len(qml_szovegek),
    )


def also_korlat_hibai(elemzes: Elemzes) -> list[str]:
    """A „üresen is zöld" csapda ellen: mit KELLETT volna találnia.

    A „0 elérhetetlen tag" elgépelt minta és rossz útvonal mellett is igaz.
    Ezért a nulla eredmény itt HIBA, nem siker.
    """
    hibak: list[str] = []
    if not elemzes.kontextusok:
        hibak.append("egyetlen setContextProperty-regisztrációt sem találtam")
    if not elemzes.py_fajlok:
        hibak.append("egyetlen Python-fájlt sem néztem át")
    if not elemzes.qml_fajlok:
        hibak.append("egyetlen QML-fájlt sem néztem át")
    if not elemzes.tagok:
        hibak.append("egyetlen @Slot/@Property tagot sem találtam a vezérlőkön")
    if not elemzes.hivatkozott:
        hibak.append("egyetlen ÉLŐ QML-hivatkozást sem találtam — a keresés maga romlott el")
    if elemzes.feloldatlan:
        hibak.append(
            "fel nem oldott kontextus-regisztráció (a tagjait némán kihagynám): "
            + ", ".join(sorted(elemzes.feloldatlan))
        )
    return hibak


# -- 4. az alapállapot -----------------------------------------------------


def baseline_osztalyok_olvas(ut: Path) -> dict[str, str]:
    """Az `[OSZTALY]` szakasz: QML-tagot hordozó, de el nem ért osztályok."""
    tetelek: dict[str, str] = {}
    szakaszban = False
    for nyers in ut.read_text(encoding="utf-8").splitlines():
        sor = nyers.strip()
        if sor == "[OSZTALY]":
            szakaszban = True
            continue
        if sor.startswith("[") and sor.endswith("]"):
            szakaszban = False
            continue
        if not szakaszban or not sor or sor.startswith("#"):
            continue
        kulcs, _, indoklas = sor.partition(" ")
        if not indoklas.strip():
            raise ValueError(f"indoklás nélküli osztály-sor: {sor!r}")
        tetelek[kulcs] = indoklas.strip()
    return tetelek


def baseline_olvas(ut: Path) -> dict[str, str]:
    """A tag-szakasz: `kontextus.tag  indoklás`. Indoklás nélküli sor HIBA."""
    tetelek: dict[str, str] = {}
    szakaszban = True
    for nyers in ut.read_text(encoding="utf-8").splitlines():
        sor = nyers.strip()
        if sor.startswith("[") and sor.endswith("]"):
            szakaszban = sor != "[OSZTALY]"
            continue
        if not szakaszban or not sor or sor.startswith("#"):
            continue
        kulcs, _, indoklas = sor.partition(" ")
        if not indoklas.strip():
            raise ValueError(f"indoklás nélküli sor az alapállapotban: {sor!r}")
        if "." not in kulcs:
            raise ValueError(f"nem `kontextus.tag` alakú kulcs: {sor!r}")
        tetelek[kulcs] = indoklas.strip()
    return tetelek


def elteresek(elemzes: Elemzes, baseline: dict[str, str]) -> tuple[list[str], list[str]]:
    """(új szakadások, elavult listatételek) — mindkettő bukás."""
    maiak = {tag.kulcs for tag in elemzes.szakadasok}
    ujak = sorted(maiak - set(baseline))
    elavultak = sorted(set(baseline) - maiak)
    return ujak, elavultak


# -- 5. a leltár -----------------------------------------------------------


def leltar_tabla(
    elemzes: Elemzes,
    baseline: dict[str, str],
    osztaly_baseline: dict[str, str] | None = None,
) -> str:
    """A leltár generált blokkja — hogy ne kézi pillanatkép maradjon."""
    osztaly_baseline = osztaly_baseline or {}
    sorok = [
        LELTAR_KEZDET,
        "",
        "*Ezt a blokkot a `python scripts/kepesseg_or.py --leltar --ir` írja.*",
        "*Kézzel ne szerkeszd: a `tests/tools/test_kepesseg_or_1476.py` őrzi.*",
        "",
        "*Ami ezen a lapon SZÁNDÉKOSAN nem áll: a mérés terjedelme (hány*",
        "*Python-, hány QML-fájl, hány tag, hány alias — #1508), a tagok*",
        "*PONTOS SORA és az árva osztályok tagszáma (#1523). Mindhárom a*",
        "*futás kimenetében van (CI-napló, `--list`), mert a verziózott szám*",
        "*minden érintetlen kódmozdulattól elavult — valódi szakadás nélkül.*",
        "*A fájlnév marad: tagnévvel együtt `grep -n`-nel pontos, és stabil.*",
        "",
        f"**Felületről el nem ért vezérlő-tag: {len(elemzes.szakadasok)}.**",
        "",
        "| kontextus-objektum | tag | fajta | hely | indoklás |",
        "|---|---|---|---|---|",
    ]
    for tag in elemzes.szakadasok:
        indoklas = baseline.get(tag.kulcs, "**ÚJ — nincs indoklás**")
        sorok.append(
            # A PONTOS SOR SZÁNDÉKOSAN HIÁNYZIK (#1523) — ld. a modul
            # docstringjét. A fájlnév + tagnév `grep -n`-nel pontos, és
            # nem avul el minden fölötte beszúrt sortól.
            f"| `{tag.kontextus}` | `{tag.nev}` | {tag.fajta} "
            f"| `app/{tag.fajl}` | {indoklas} |"
        )
    if elemzes.arva_osztalyok:
        sorok += [
            "",
            "**QML-tagot hordozó, de kontextusból el nem ért osztályok:**",
            "",
            "| osztály | hely | indoklás |",
            "|---|---|---|",
        ]
        for arva in elemzes.arva_osztalyok:
            # A tagszám is volatilis volt (#1523): a `models.py` mért forró
            # fájl, egy új modell-tag elmozdította a lapot — miközben az őr
            # összevetése csak az osztály NEVÉT nézi. A darabszám a futás
            # kimenetében áll (`--list`).
            sorok.append(
                f"| `{arva.nev}` | `app/{arva.fajl}` "
                f"| {osztaly_baseline.get(arva.nev, '**ÚJ — nincs indoklás**')} |"
            )
    return "\n".join([*sorok, "", LELTAR_VEGE])


def leltar_ir(ut: Path, blokk: str) -> None:
    """A generált blokk cseréje a leltárban (a jelölők közt)."""
    szoveg = ut.read_text(encoding="utf-8")
    if LELTAR_KEZDET in szoveg and LELTAR_VEGE in szoveg:
        eleje = szoveg.split(LELTAR_KEZDET)[0]
        vege = szoveg.split(LELTAR_VEGE)[1]
        ut.write_text(f"{eleje}{blokk}{vege}", encoding="utf-8")
    else:
        ut.write_text(f"{szoveg.rstrip()}\n\n{blokk}\n", encoding="utf-8")


# -- 6. parancssor ---------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ertelmezo.add_argument("--app", type=Path, default=_DEFAULT_APP)
    ertelmezo.add_argument("--baseline", type=Path, default=_DEFAULT_BASELINE)
    ertelmezo.add_argument("--leltar-ut", type=Path, default=_DEFAULT_LELTAR)
    ertelmezo.add_argument("--list", action="store_true", help="a mai szakadások")
    ertelmezo.add_argument("--leltar", action="store_true", help="leltár-tábla")
    ertelmezo.add_argument("--ir", action="store_true", help="a leltárt írja is")
    beallitas = ertelmezo.parse_args(argv)

    try:
        elemzes = elemez(beallitas.app)
    except (FileNotFoundError, SyntaxError) as hiba:
        print(f"HIBA: {hiba}", file=sys.stderr)
        return 2

    korlat_hibak = also_korlat_hibai(elemzes)
    if korlat_hibak:
        print("HIBA — az ellenőrzés maga romlott el, nem a kód tiszta:", file=sys.stderr)
        for hiba in korlat_hibak:
            print(f"  * {hiba}", file=sys.stderr)
        return 2

    # A mérés terjedelme ITT jelenik meg, és NEM a verziózott leltárban
    # (#1508): a napló magától frissül, a dokumentumot kézzel kellett
    # utánaigazítani minden új fájl után.
    print(
        f"átnézve: {elemzes.py_fajlok} Python-fájl, {elemzes.qml_fajlok} QML/JS-fájl, "
        f"{len(elemzes.kontextusok)} kontextus-objektum "
        f"(+{len(elemzes.nem_qobject)} nem QObject), {len(elemzes.aliasok)} feloldott alias, "
        f"{len(elemzes.tagok)} tag, {len(elemzes.hivatkozott)} élő minősített hivatkozás, "
        f"{len(elemzes.szakadasok)} szakadás"
    )

    if beallitas.list:
        for tag in elemzes.szakadasok:
            print(f"{tag.kulcs}  {tag.fajta}  app/{tag.fajl}:{tag.sor}")
        for arva in elemzes.arva_osztalyok:
            print(f"[osztály] {arva.nev}  app/{arva.fajl}  ({arva.tagszam} tag)")
        return 0

    try:
        baseline = baseline_olvas(beallitas.baseline)
        osztaly_baseline = baseline_osztalyok_olvas(beallitas.baseline)
    except (OSError, ValueError) as hiba:
        print(f"HIBA az alapállapotban: {hiba}", file=sys.stderr)
        return 2

    if beallitas.leltar:
        blokk = leltar_tabla(elemzes, baseline, osztaly_baseline)
        if beallitas.ir:
            leltar_ir(beallitas.leltar_ut, blokk)
            print(f"a leltár frissítve: {beallitas.leltar_ut}")
        else:
            print(blokk)
        return 0

    ujak, elavultak = elteresek(elemzes, baseline)
    mai_arvak = {arva.nev for arva in elemzes.arva_osztalyok}
    uj_arvak = sorted(mai_arvak - set(osztaly_baseline))
    elavult_arvak = sorted(set(osztaly_baseline) - mai_arvak)

    baj = False
    if ujak:
        baj = True
        print("\nÚJ, felületről elérhetetlen vezérlő-tag:", file=sys.stderr)
        for kulcs in ujak:
            tag = next(t for t in elemzes.szakadasok if t.kulcs == kulcs)
            print(f"  * {kulcs}  ({tag.fajta}, app/{tag.fajl}:{tag.sor})", file=sys.stderr)
        print(
            "  Kösd be a QML-ből, töröld a tagot, vagy — ha a bekötetlenség "
            "TUDATOS — vedd fel indoklással a kepesseg_or_baseline.txt-be.",
            file=sys.stderr,
        )
    if elavultak:
        baj = True
        print("\nELAVULT listatétel (már el van érve, a sorát törölni kell):", file=sys.stderr)
        for kulcs in elavultak:
            print(f"  * {kulcs}", file=sys.stderr)
    if uj_arvak:
        baj = True
        print("\nÚJ, kontextusból el nem ért, QML-tagokat hordozó osztály:", file=sys.stderr)
        for nev in uj_arvak:
            print(f"  * {nev}", file=sys.stderr)
    if elavult_arvak:
        baj = True
        print("\nELAVULT osztály-tétel (már el van érve):", file=sys.stderr)
        for nev in elavult_arvak:
            print(f"  * {nev}", file=sys.stderr)
    if len(baseline) > MAX_BASELINE_ENTRIES:
        baj = True
        print(
            f"\nAz alapállapot {len(baseline)} tételre nőtt, a plafon "
            f"{MAX_BASELINE_ENTRIES} (MAX_BASELINE_ENTRIES a kepesseg_or.py-ban). "
            "A lista rövidülhet, de nem hízhat észrevétlenül.",
            file=sys.stderr,
        )
    if len(osztaly_baseline) > MAX_OSZTALY_ENTRIES:
        baj = True
        print(
            f"\nAz osztály-lista {len(osztaly_baseline)} tételre nőtt, a plafon "
            f"{MAX_OSZTALY_ENTRIES}.",
            file=sys.stderr,
        )

    if baj:
        return 1
    print(
        f"rendben: {len(elemzes.szakadasok)} ismert szakadás, mind indoklással "
        f"(plafon {MAX_BASELINE_ENTRIES})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
