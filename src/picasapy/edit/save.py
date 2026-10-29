"""Nem-destruktív mentés / Visszaállítás (#21, #5833).

A UX 3. alapelve („Észrevétlen eredeti-megőrzés", `docs/specs/ux-principles.md`):
a felhasználó sosem lát verziókáoszt, és nincs kötelező export-lépés. Mentéskor:

1. Az EREDETI (a mentés pillanatában a lemezen lévő, még "szűz" — a jelen
   mentés által még nem érintett) fájl bájtjai ELSŐ alkalommal átkerülnek a
   kép melletti rejtett `.picasaoriginals/` almappába. Ha ott már van egy
   korábbi mentésből (a képet már egyszer elmentettük), NEM írjuk felül: az
   ELSŐ eredeti a szent példány — ez garantálja, hogy több egymást követő
   mentés se veszítse el a "valódi" eredetit.
2. A renderelt (a szerkesztési lánc beleégetésével kapott — a RENDERELÉS a
   HÍVÓ feladata, ez a modul csak a perzisztenciát végzi) kép az EREDETI
   fájl HELYÉRE kerül: a felhasználó a fájlkezelőben ugyanazt a fájlnevet
   látja, csak a tartalma frissült.
3. A beégetett lánc a kiválasztott eredeti-mappa `.picasa.ini`-jének
   képnevű szakaszába kerül `filters=`-ként. Az aktuális mappa ini-jéből a
   `filters=` és `redo=` törlődik, és a #5810 szerinti `backuphash` íródik
   bele. A lánc így nem fut le újra a már beégetett képen, a `redo=` pedig
   megmarad az eredeti jelentésénél: a visszavonás utáni újra-lista.
   Minden ini-módosítás a round-trip API-n át történik, az `originhash`
   NEM íródik (ld. lent, #2675).

Ha a 3. lépés elbukik (ütközés a párhuzamosan futó Picasával, tele lemez,
zárolt ini), a 2. lépést VISSZAVONJUK: a képfájl visszakapja a mentés
előtti bájtjait (#297). Enélkül a kép a beégetett szerkesztést tartalmazná,
miközben a `filters=` bent maradt az ini-ben — a következő megnyitáskor a
renderelő MÁSODSZOR is ráfuttatná a láncot. Ugyanez a védelem a `revert`-nél
fordított irányban: ott a kulcsok törlésének bukásakor a szerkesztett kép
íródik vissza.

## `originhash` — MÉRVE: nem mentéskori kulcs, ezért NEM írjuk (#2675)

A specifikáció (`docs/specs/picasa-ini-format.md`) az `originhash`-t
„szerkesztési verem integritás-hash"-ként írta le, algoritmus nélkül, és a
#21 ezért egy józan alapértelmezést választott: a `redo=` érték SHA-256
hexdigestjét. **Ez a döntés megdőlt, két független mérésen.**

**1. Alak és képlet (#791/#2733).** A tulajdonos 859 valódi
`.picasa.ini`-jében 1 787 `originhash=` sor áll, mind pontosan **32**
kisbetűs hexa karakter — a SHA-256 64-et ad. A képlet is megvan:
`hex16(originfast) ‖ hex16(originslow)`, tehát a **fájl bájtjaiból**
számol, nem a `redo=` láncból (`picasapy.dedup.originhash`).

**2. A kulcs nem a mentéshez tartozik (#2675).** Ugyanabban a korpuszban az
`originhash` és a `redo=` **egyetlen szakaszban sem áll együtt**:
`(originhash, redo)` = (igen, igen) → **0**, (igen, nem) → 1 787,
(nem, igen) → 34. A régi PicasaPy a `redo=`-t mentésjelzőként használta;
ezt a #5833 javítja. Az eredeti Picasában a `redo=` az újra-lista kulcsa,
ezért nem vezetjük le belőle az `originhash` szerepét. A társkulcsok is a
letöltési utat mutatják: `IIDLIST_<név>_lh`
877, `backuphash` 760, `onlinechecksum` 380 — és a 10 érintett, nem
`Downloaded Albums` alatti mappa neve is átvett anyagra utal („(ovis
fotók)", „(Krisztuka fotói)").

A binárisban ugyanez: a kiírt rekord `+0x90` mezőjét az `operator=`
másolja, és a rekord-vektor `push_back`-jének (`FUN_007d53e0`) EGYETLEN
hívója a `FUN_006f9cc0` = *Download from Google Photos*
(`docs/specs/picasa-tartalomkulcs.md`, 211. kör).

⇒ **A mentés nem ír `originhash`-t**, és a `revert` nem is törli: az
`originhash` idegen (letöltési) kulcs, amelyet a round-trip szabály szerint
érintetlenül hagyunk. A #2675 eredeti kérdése („a most kiírt vagy a
szerkesztés előtti fájl bájtjai?") ezzel **tárgytalan**: a válasz egyik
sem, mert a mentés nem ír ilyen kulcsot.

Ugyanez a fordulat történt a másolat-mentésnél (#1643): ott is egy kitalált
`redo=` + `originhash` könyvelést kellett visszavonni, amikor mérés került
a feltevés helyére. Az őr: `tests/edit/test_originhash_nem_mentesi_kulcs_2675.py`.

## Két mappanév: `.picasaoriginals` és `Originals` (#1425)

A Picasa a szerkesztés előtti eredetit **két, időben elváló néven** tárolta
(`docs/specs/picasa-ini-format.md`, „Az eredeti képek mentése — KÉT
elnevezés, verzióváltással"; 181 valós mappa, *megerősített*):

| mappanév | darab a korpuszban | évek |
|---|---:|---|
| `Originals` (látható) | 127 | 2005–2009 |
| `.picasaoriginals` (rejtett) | 54 | 2009–2016 |

A #371 kutatása kizárta, hogy a retus/vörösszem régió-adata bárhol
tárolódna: a javítás a mentett képbe van beleégetve, tehát a Visszaállítás
EGYETLEN útja a megőrzött eredeti fájl. A régi név ismerete nélkül a
tulajdonos 127 mappányi eredetijéhez nem tudnánk visszatérni, ezért az
`ORIGINALS_DIR_NAMES` sorrendjében **mindkettőt** megnézzük.

**SAJÁT FUNKCIÓ (#1425):** ütközéskor — ha ugyanahhoz a képhez MINDKÉT
mappában van példány — a régi, `Originals` nyer. Ez **nem mérés**: arra,
hogy az eredeti Picasa mit tesz ilyenkor, nincs bizonyítékunk (a korpusz
csak `.picasa.ini`-szövegeket tartalmaz, és `Originals/` alatt egyetlen ini
sincs — az a név rajta van a Picasa saját kizárási listáján, ezért oda
sosem írt). A döntés két megfontoláson áll:

1. **Időrend.** A két név nem keveredik: az `Originals`-beli példány
   szükségképpen a korábbi, tehát közelebb van az érintetlen eredetihez.
   A `.picasaoriginals`-beli ilyenkor a 2005–2009 közötti szerkesztéseket
   MÁR beégetve tartalmazza.
2. **A hiba iránya.** Az újabbat választva a felhasználó egy részlegesen
   visszaállított képet kapna, **némán** — pont az, amit a Visszaállítás
   ígérete kizár. A régebbit választva „minden változás elvész", ami a
   művelet kimondott szerződése.

Ugyanez a szabály védi a mentést is: ha bármelyik mappában MÁR van
megőrzött eredeti, a `save_edited` **nem tesz mellé másodikat** — különben
az első PicasaPy-mentés egy `Originals`-os mappában a már szerkesztett
bájtokat írná a `.picasaoriginals`-ba, és (ha valaha megfordulna a
sorrend) a valódi eredeti elérhetetlenné válna.

**A sorszámozott pillanatképek (`undo_save`) KIZÁRÓLAG a
`.picasaoriginals` alatt élnek.** Ezek a MI mentéseink melléktermékei, és a
`undo_save` a felhasznált pillanatképet TÖRLI — a látható, Picasa-korabeli
`Originals` mappában fájlt törölni nem szabad.

## A pillanatképek KÜLÖN NÉVTERE (#2512)

A `<tő>.<N><kiterjesztés>` névminta (#444) kétértelmű: az `a.jpg` második
mentésének pillanatképe (`.picasaoriginals/a.2.jpg`) bitre ugyanúgy néz ki,
mint egy ÖNÁLLÓ `a.2.jpg` kép „szent" eredetije. A `find_original_backup`
a kettőt nem tudta megkülönböztetni, és az önálló `a.2.jpg` „Vissza az
eredetihez" parancsa egy IDEGEN fénykép bájtjait tette a helyére.

A #1449 sorszám-átlépése ezt nem oldotta meg: az csak a MÁR OTT ÁLLÓ fájl
felülírását akadályozta. A fordított irány — előbb `a.jpg`-t mentjük, és az
önálló `a.2.jpg` csak KÉSŐBB kerül szerkesztésre — nyitva maradt.

**SAJÁT FUNKCIÓ (#2512):** a `.picasapy-snapshots` alkönyvtár a MI
hozzáadásunk — az eredeti Picasa a sorszámozott másolatait a
`.picasaoriginals`-ba, a „szent" eredeti MELLÉ írja. A névminta (`%s.%d.jpg`)
mért és eredeti, a HELY nem: azt azért választottuk szét, mert a közös
mappában a két dolog megkülönböztethetetlen, és a tévedés ára egy idegen
fénykép bájtjainak visszaírása. Az eredetit olvasni ettől függetlenül
tudjuk, tehát a Picasa-kompatibilitás nem sérül.

Ezért a két dolog két külön helyre került:

| mi | hova | ki írja |
|---|---|---|
| a „szent" eredeti | `.picasaoriginals/<fájlnév>` | a Picasa ÉS mi |
| a mentésenkénti pillanatkép | `.picasaoriginals/.picasapy-snapshots/<tő>.<N><kit>` | csak mi |

Az OLVASÁS mindkét helyre kiterjed: a régi helyen álló példányokat — a
sajátjainkat és a Picasa írtakat egyaránt — továbbra is megtaláljuk, a
#1449 óvatossági szabályával együtt (ha a képmappában azonos nevű ÖNÁLLÓ
kép áll, békén hagyjuk). Az ÚJ helyen ez a szabály nem alkalmazandó: oda
rajtunk kívül senki nem ír, tehát ott a névminta nem kétértelmű — a
gazda-szűrés ott csak a saját visszavonásunkat némítaná el.

Az indoklás és a mérlegelt alternatívák: `docs/decisions/pillanatkep-nevter.md`.

## `.picasaoriginals` accent-path-tolerancia

A MEMORY.md #190-es tanulsága szerint a `cv2.imwrite`/`cv2.imread`
Windowson ékezetes útvonalon NÉMÁN nem ír/olvas. Ez a modul ezért SOHA nem
hív `cv2.imwrite`-ot vagy `cv2.imread`-et: az eredeti biztonsági mentés
nyers `Path.read_bytes`/`write_atomic` bájt-másolás (nincs újrakódolás,
bitre pontos), a renderelt kép írása pedig `cv2.imencode` (memóriapuffer,
NEM fájlútvonal-paraméteres) + `write_atomic` — pontosan az
`export/exporter.py`-ban már bevált mintát követve.
"""

from __future__ import annotations

import os as os
from dataclasses import dataclass
from pathlib import Path

from picasapy.lazy_cv2 import cv2 as cv2
import numpy as np

from picasapy.edit.session import EditSession
from picasapy.ini import (
    FilterWriteError,
    IniConflictError,
    IniDocument,
    IniSaveError,
    ini_source_path as ini_source_path,
    load_or_empty as load_or_empty,
    remove_ini_target_if_content_matches as remove_ini_target_if_content_matches,
    update_document as update_document,
    with_backuphash as with_backuphash,
)
from picasapy.ini.moddate import moddate_from_timestamp_ns as moddate_from_timestamp_ns
from picasapy.ini.names import INI_NAME
from picasapy.ioutil import write_atomic as write_atomic

#: Windowson a képfájlt egy olvasó (bélyegkép, néző) rövid ideig nyitva
#: tarthatja, ilyenkor a csere `PermissionError`-ral (sharing violation)
#: bukik. A metaadat-író mintájára néhányszor újrapróbáljuk (összesen ~1,8 mp).
_ZAR_UJRA = 8
_ZAR_KESLELTETES = 0.05




def _load_function(module_name: str, function_name: str):
    """A mentési részmodult csak az első műveletkor tölti be."""
    module = __import__(f"{__package__}.{module_name}", fromlist=(function_name,))
    return getattr(module, function_name)

def _kep_irasa(image_path: Path, payload: bytes) -> None:
    return _load_function('save_storage', '_kep_irasa')(image_path, payload)

#: A rejtett almappa neve, ahová az ÚJ mentéseink érintetlen eredetije kerül
#: (spec + UX #3). Írni MINDIG ide írunk.
ORIGINALS_DIR_NAME = ".picasaoriginals"

#: A 2009 ELŐTTI Picasa-verziók LÁTHATÓ mappaneve ugyanerre a célra (#1425).
#: Csak OLVASSUK — a tulajdonos gyűjteményében élesben előfordul.
LEGACY_ORIGINALS_DIR_NAME = "Originals"

#: A MI mentésenkénti pillanatképeink alkönyvtára a `.picasaoriginals`-on
#: BELÜL (#2512). Külön névtér: a `find_original_backup` útja
#: (`.picasaoriginals/<fájlnév>`) így SOHA nem eshet egybe egy
#: pillanatképével. Az indoklás: `docs/decisions/pillanatkep-nevter.md`.
#:
#: A régi helyen (`.picasaoriginals/<tő>.<N><kit>`) álló példányokat
#: továbbra is OLVASSUK — a sajátjainkat és a Picasa írtakat egyaránt —,
#: csak ÍRNI nem írunk többé oda.
SNAPSHOT_DIR_NAME = ".picasapy-snapshots"

#: A megőrzött eredeti KERESÉSI SORRENDJE — az első találat nyer.
#: A régi, `Originals` áll elöl; az indoklás a modul „Két mappanév”
#: szakaszában.
ORIGINALS_DIR_NAMES = (LEGACY_ORIGINALS_DIR_NAME, ORIGINALS_DIR_NAME)

# A mentés-visszavonáskor érintett ini-kulcsok. ⚠️ #2675: az
# `originhash` SZÁNDÉKOSAN nincs köztük — mérve nem mentéskori kulcs (a
# korpuszban 1787 előfordulásból 0 áll `redo=` mellett), hanem a web-album
# letöltés provenienciája. Sem nem írjuk, sem nem töröljük.
_FILTERS_KEY = "filters"
_REDO_KEY = "redo"
_MODDATE_KEY = "moddate"
_EDIT_BOOKKEEPING_KEYS = (_FILTERS_KEY, _REDO_KEY)

_INI_FILENAME = INI_NAME

# Az ini-könyvelés kezelt hibái (#297): a fájlrendszeré (`OSError`: tele
# lemez, zárolt fájl), a kódolásé (`IniSaveError`) és a párhuzamosan futó
# eredeti Picasa tartós ütközése (`IniConflictError`).
#
# #643: a round-trip őr visszautasítása (`FilterWriteError`) itt NEM csak
# üzenet-kérdés, hanem ADATVÉDELEM. Ha bármelyik ini frissítése elbukik,
# a képfájl ekkor MÁR a beégetett szerkesztést tartalmazza. A sikeres
# ini-írásokat és a képet visszaállítjuk, hogy a lánc ne fusson le még
# egyszer a következő megnyitáskor (#297).
_INI_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)

# JPEG-nél a mentés-minőség alapértéke magas (a felhasználó explicit
# "Mentés" szándékát tükrözi — a nem-destruktív elv ELLENÉRE ez a pillanat
# fizikailag lecseréli a fájlt, tehát a minőségvesztés minimalizálandó).
_DEFAULT_JPEG_QUALITY = 95


class SaveError(RuntimeError):
    """Mentés vagy visszaállítás nem hajtható végre.

    Pl. a renderelt kép nem kódolható a cél formátumba, vagy a
    `.picasaoriginals`-ban nincs elérhető eredeti a Visszaállításhoz.
    """


@dataclass(frozen=True)
class SaveResult:
    """A `save_edited` eredménye: mely fájlok/ini-kulcsok íródtak.

    Attributes:
        image_path: A (felülírt) kép útja.
        original_backup_path: A kiválasztott eredeti-mappabeli eredeti útja.
        backup_created_now: True, ha ELSŐ mentés volt (most jött létre az
            eredeti-mentés); False, ha egy korábbi mentésből származó
            eredeti már megvolt (és ezért nem íródott felül).
        filters_value: Az eredeti-mappa ini-jébe mentett `filters=` érték.

    ⚠️ #2675: NINCS `originhash` mező — a mentés ezt a kulcsot nem írja
    (mint a `SaveCopyResult`-nál a #1643 után), tehát nem is lenne mit
    visszaadnia.
    """

    image_path: Path
    original_backup_path: Path
    backup_created_now: bool
    filters_value: str


@dataclass
class _PhotoIniSnapshot:
    """A kompenzáló íráshoz szükséges ini-kulcsok és fájlállapot."""

    values: dict[str, str | None]
    document: IniDocument
    target_existed: bool
    written_document: IniDocument | None = None


@dataclass(frozen=True)
class RevertResult:
    """A `revert` eredménye: honnan állt vissza a kép, mely kulcsok törlődtek."""

    image_path: Path
    restored_from: Path
    removed_keys: tuple[str, ...]


def save_edited(
    image_path: str | Path,
    rendered_image: np.ndarray,
    filters: EditSession,
    *,
    jpeg_quality: int = _DEFAULT_JPEG_QUALITY,
) -> SaveResult:
    """A nem-destruktív "Mentés": a renderelt kép az eredeti helyére kerül.

    Args:
        image_path: A kép jelenlegi, fizikai elérési útja a mappában (a
            `.picasa.ini` mellette, a szülőkönyvtárban van).
        rendered_image: A szerkesztési lánc beleégetésével kapott
            képmátrix, OpenCV BGR-konvencióban (ahogy a render/export
            modulok is használják) — a RENDERELÉS a hívó feladata, ez a
            függvény csak a perzisztenciát és az ini-könyvelést végzi.
        filters: A MOST mentett szerkesztési lánc (`EditSession`); ennek
            szerializált értéke kerül az eredeti-mappa ini-jének `filters=`
            kulcsába.
        jpeg_quality: JPEG-minőség (csak `.jpg`/`.jpeg` célútnál számít).

    Returns:
        `SaveResult` a végrehajtott lépések adataival.

    Raises:
        SaveError: ha a renderelt kép nem kódolható a cél kiterjesztésbe,
            vagy ha az ini-hiba utáni képfájl-visszaállítás sem sikerült
            (#297 — ekkor a kép és az ini nyilvántartása eltér).
        OSError | IniSaveError | IniConflictError: ha az ini-könyvelés nem
            sikerült. A képfájl ilyenkor VISSZAÁLL a mentés előtti
            állapotra, hogy ne maradjon dupla-szerkesztés (#297).
    """
    return _load_function('save_operations', 'save_edited')(image_path, rendered_image, filters, jpeg_quality=jpeg_quality)


@dataclass(frozen=True)
class UndoSaveResult:
    """Az `undo_save` eredménye (#444)."""

    image_path: Path
    restored_from: Path
    #: a visszaadott szerkesztési lánc (az eredeti-mappa ini-jéből, vagy
    #: régi PicasaPy-mentésnél a `redo=`-ból a `filters=`-be)
    restored_filters: str


def undo_save(image_path: str | Path) -> UndoSaveResult:
    """„Utolsó mentés visszavonása" — a SZERKESZTÉSEK MEGMARADNAK (#444).

    Ez a Picasa négy mentés-műveletéből a köztes fokozat, és élesen KÜLÖNBÖZIK
    a `revert`-től:

    * `revert` — a kép visszaáll a „szent" eredetire, és a szerkesztési
      könyvelés is törlődik: *„This cannot be undone and all changes will be
      lost."*
    * `undo_save` — csak az UTOLSÓ lemezre írást vonja vissza: a kép a mentés
      előtti bájtjait kapja vissza, az eredeti-mappa ini-jében tárolt lánc
      pedig visszakerül az aktuális `filters=`-be. Régi PicasaPy-mentésnél a
      láncot a korábbi `redo=` értékből veszi át. Az eredeti szavakkal: *„To undo the last
      save and keep edits click 'Undo Save'."*

    A mentés előtti bájtok a mentésenként készülő, sorszámozott
    pillanatképből jönnek (`_snapshot_path`); a felhasznált pillanatkép a
    művelet végén törlődik, így többszöri hívás lépésenként halad visszafelé.

    Raises:
        SaveError: ha nincs visszavonható mentés (nincs pillanatkép).
    """
    return _load_function('save_operations', 'undo_save')(image_path)


def revert(image_path: str | Path) -> RevertResult:
    """A "Visszaállítás": a megőrzött eredeti visszamásolása.

    Az eredetit MINDKÉT ismert mappanév alatt keresi (`.picasaoriginals` és
    a 2009 előtti `Originals` — ld. a modul „Két mappanév" szakaszát), és a
    `RevertResult.restored_from` megmondja, melyikből dolgozott (#1425).

    A korábbi szerkesztés-könyvelést (`filters=`, `redo=`) az
    ini-ből törli — a fájl a szerkesztés ELŐTTI állapotba kerül vissza,
    a nem-technikai felhasználó elvárása szerint: "vissza az eredetihez".
    Minden más ini-kulcs (csillag, felirat, arcok, albumok, `backuphash`,
    `originhash` — #2675: az a letöltés provenienciája, nem a szerkesztés
    könyvelése —, ismeretlen mezők) érintetlen marad.

    Args:
        image_path: A kép jelenlegi, fizikai elérési útja a mappában.

    Returns:
        `RevertResult` a visszaállítás adataival.

    Raises:
        SaveError: ha egyik ismert mappában sincs megőrzött eredeti — az
            üzenet a felhasználónak szól, és megnevezi mindkét mappát
            (`_missing_original_message`).
    """
    return _load_function('save_operations', 'revert')(image_path)


def _restore_image_or_raise(
    image_path: Path, payload: bytes, backup_path: Path, error: Exception
) -> None:
    """A képfájl visszaállítása a művelet előtti bájtokra (#297).

    Ha maga a visszaállítás is elbukik, `SaveError`-t emel: a felhasználónak
    magyarul, cselekvésre fordíthatóan meg kell tudnia, hogy a kép fizikailag
    elmentődött, a `.picasa.ini` nyilvántartása viszont nem követte — így
    tudja, hogy a kép a következő megnyitáskor kétszer szerkesztettnek
    látszhat, és hol keresse az eredetit."""
    return _load_function('save_operations', '_restore_image_or_raise')(image_path, payload, backup_path, error)


def find_original_backup(image_path: str | Path) -> Path | None:
    """A képhez megőrzött eredeti — MINDKÉT mappanevet megnézve (#1425).

    Az `ORIGINALS_DIR_NAMES` sorrendjében keres (régi `Originals` előbb, ld.
    a modul „Két mappanév" szakaszát), és az első meglévő fájl útját adja
    vissza. Ha egyik mappában sincs példány, `None`.

    Csak a KÉT ismert nevet nézi meg, kis-nagybetű pontosan, és nem listázza
    ki a mappát: képenként így legfeljebb két `stat()` — a #1146 tanulsága
    szerint a tulajdonos gyűjteménye hálózati megosztáson él, ahol minden
    fölösleges könyvtárlistázás egy hálózati kör.
    """
    return _load_function('save_storage', 'find_original_backup')(image_path)


def _missing_original_message(image_path: Path) -> str:
    """A „nincs megőrzött eredeti" ÉRTHETŐ üzenete (#1425).

    A néma elutasítás a projekt visszatérő hibaosztálya (#1003, #1207,
    #1213): a felhasználónak — aki nem programozó — meg kell tudnia, MIT
    kerestünk, HOL, és mikor működik egyáltalán a Visszaállítás. Belső
    függvénynevek nem szivároghatnak ki ide.
    """
    return _load_function('save_storage', '_missing_original_message')(image_path)


def _backup_path_for(image_path: Path) -> Path:
    """Ahová egy ÚJ eredeti-mentés kerül: mindig a `.picasaoriginals`.

    A régi, `Originals` mappát csak OLVASSUK (ld. `find_original_backup`) —
    a Picasa-korabeli, látható mappába nem írunk.
    """
    return _load_function('save_storage', '_backup_path_for')(image_path)


def _original_ini_path(image_path: Path, backup_path: Path | None = None) -> Path:
    """A kiválasztott megőrzött eredeti-mappa `.picasa.ini`-je.

    Mentésnél a tényleges eredeti fájl mappáját kapjuk meg. Visszavonásnál
    előbb ugyanazt a fájlt keressük; ha hiányzik, a meglévő eredeti-mappa
    ini-jét választjuk, végül az új `.picasaoriginals` mappa az alapérték.
    """
    return _load_function('save_storage', '_original_ini_path')(image_path, backup_path)


def _snapshot_path(image_path: Path, number: int) -> Path:
    """Ahová egy ÚJ pillanatkép kerül: a `.picasapy-snapshots` alkönyvtárba.

    #444: a Picasa binárisában a `.picasaoriginals` névmintája `%s.%d.jpg`
    (`.mov`, `.wmv`) — vagyis a „szent" eredeti MELLETT mentésenként külön,
    SORSZÁMOZOTT másolat is készül. Ez teszi lehetővé az „Utolsó mentés
    visszavonása" parancsot (`undo_save`): az utolsó mentés visszavonható
    úgy, hogy a SZERKESZTÉSEK MEGMARADNAK.

    #2512: a NÉVMINTÁT megtartjuk, a HELYET nem. A Picasáéval közös
    mappában ez a név egy önálló kép „szent" eredetijétől
    megkülönböztethetetlen volt (ld. a modul „A pillanatképek KÜLÖN
    NÉVTERE" szakaszát), és a `find_original_backup` emiatt idegen
    bájtokat adott vissza.
    """
    return _load_function('save_storage', '_snapshot_path')(image_path, number)


def _legacy_snapshot_path(image_path: Path, number: int) -> Path:
    """A pillanatkép RÉGI, a `.picasaoriginals`-szal közös helye (#444).

    Ide már nem írunk (#2512), de a sorszám-kiosztásnál számít: ha a régi
    helyen áll ezen a néven fájl, a sorszámot átlépjük. Nem a felülírás
    ellen — az új hely miatt az kizárt —, hanem hogy ugyanaz a sorszám ne
    létezzen KÉTSZER, két különböző helyen: az `undo_save` a legnagyobb
    sorszámú példányt veszi, és egyenlőségnél nem tudná eldönteni, melyik
    a frissebb.
    """
    return _load_function('save_storage', '_legacy_snapshot_path')(image_path, number)


def _existing_snapshots(image_path: Path) -> list[tuple[int, Path]]:
    """A meglévő sorszámozott pillanatképek `(N, útvonal)` párjai, növekvő
    sorrendben.

    A keresés a `fileops.originals.snapshot_numbers` KÖZÖS szabálya (#1449) —
    itt korábban `glob()` állt, két néma hibával:

    * a fájlnévben lévő `[`, `*` vagy `?` a mintában jokerként viselkedett
      (egy `IMG[1].jpg` képnél rossz vagy nulla találat),
    * és nem nézte, hogy a `<név>.<N><kiterjesztés>` alak egy ÖNÁLLÓ kép
      megőrzött eredetije is lehet — az `undo_save` pedig a felhasznált
      pillanatképet TÖRLI, tehát egy másik kép visszaútját semmisítette
      volna meg.

    **Az óvatosságnak ára van** (#1449 átnézés, 3. lelet): ha a képmappában
    van azonos nevű önálló kép, a példány kimarad, és az `undo_save`
    elveszíti a visszavonást egy LÉTEZŐ pillanatképhez. Adat nem vész el, de
    a sorszám-átlépés (`save_edited`) miatt minden további mentés újabb
    teljes méretű JPEG-et halmoz, amit semmi nem takarít. Tisztább megoldás
    nincs: a két eset a lemezen bitre azonosan néz ki, a tévedés iránya
    pedig itt egy MÁSIK kép visszaútjának a megsemmisítése lenne. Amit
    megtehetünk, az a kimondás — ld. `_nincs_visszavonhato_mentes`.

    **Két hely, egy lista** (#2512): az ÚJ pillanatképeink a
    `.picasapy-snapshots` alkönyvtárban vannak, a korábbi verzióink (és a
    Picasa) példányai a `.picasaoriginals`-ban közvetlenül. A
    `snapshot_numbers` mindkettőt végignézi; a fenti óvatossági szabály
    csak a RÉGI helyre vonatkozik, mert az ÚJ alkönyvtárba rajtunk kívül
    senki nem ír.

    A késleltetett import szándékos: a `fileops` csomag maga is (lustán) ide
    nyúl a mappanevekért, a modulszintű import körbeérne."""
    return _load_function('save_storage', '_existing_snapshots')(image_path)


def _nincs_visszavonhato_mentes(image_path: Path) -> str:
    """A „nincs mit visszavonni" üzenet — a KÉT eset másképp szól.

    Az `_existing_snapshots` üres eredménye nem mindig azt jelenti, hogy a
    mappa üres: kimarad belőle az a példány is, aminek a KÉPMAPPÁBAN van
    azonos nevű gazdája (`a.jpg` mentése `a.1.jpg` pillanatképet ír, de
    `a.1.jpg` lehet egy önálló kép is). Az óvatosság indokolt — az
    `undo_save` a felhasznált pillanatképet TÖRLI —, de az „üres vagy
    hiányzik" ilyenkor egyszerűen nem igaz, és a felhasználó nem tudja meg,
    mit tehetne (#1449 átnézés, 3. lelet)."""
    return _load_function('save_storage', '_nincs_visszavonhato_mentes')(image_path)


def _section_name(image_path: Path) -> str:
    """A `.picasa.ini`-beli szekciónév: a fájl neve, a spec `[<fájlnév.ext>]`
    szabálya szerint (ld. `picasa-ini-format.md`)."""
    return _load_function('save_ini', '_section_name')(image_path)


def _update_ini_document(
    image_path: Path,
    mutate,
    *,
    rollback_snapshot: _PhotoIniSnapshot | None = None,
    section_name: str | None = None,
) -> IniDocument:
    """Ütközésbiztos, atomikus, backup-olt ini-frissítés (#137-minta).

    Kizárólag a round-trip réteget (`update_document`) hívja — soha nem ír
    közvetlenül fájlba —, hogy az ismeretlen kulcsok/szekciók bitre pontosan
    megmaradjanak (spec 2. írási szabálya)."""
    return _load_function('save_ini', '_update_ini_document')(image_path, mutate, rollback_snapshot=rollback_snapshot, section_name=section_name)


def _update_ini_path(
    ini_path: Path,
    mutate,
    *,
    rollback_snapshot: _PhotoIniSnapshot | None = None,
    section_name: str | None = None,
) -> IniDocument:
    """Ütközésbiztos, atomikus ini-frissítés az `ini` round-trip API-n át."""
    return _load_function('save_ini', '_update_ini_path')(ini_path, mutate, rollback_snapshot=rollback_snapshot, section_name=section_name)


def _photo_ini_values(
    ini_path: Path, section_name: str, keys: tuple[str, ...]
) -> _PhotoIniSnapshot:
    """Egy képszakasz érintett kulcsainak mentés előtti értékei."""
    return _load_function('save_ini', '_photo_ini_values')(ini_path, section_name, keys)


def _restore_photo_ini_values(
    ini_path: Path, section_name: str, snapshot: _PhotoIniSnapshot
) -> None:
    """API-n át visszaállítja a kompenzáló írással felülírt kulcsértékeket.

    Csak azt a kulcsot állítja vissza, amely a kompenzáló írás óta is a mi
    kiírt értékünkön áll. A közben érkezett külső változást megőrzi.
    """
    return _load_function('save_ini', '_restore_photo_ini_values')(ini_path, section_name, snapshot)


def _encode_image(suffix: str, image: np.ndarray, jpeg_quality: int) -> bytes:
    """A renderelt képmátrix kódolása a cél kiterjesztésének megfelelő
    formátumba — `cv2.imencode`-dal (memóriapuffer, nem fájlútvonal),
    accent-path-biztosan (MEMORY.md #190)."""
    return _load_function('save_storage', '_encode_image')(suffix, image, jpeg_quality)
