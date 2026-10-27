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

import os
from dataclasses import dataclass
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.edit.session import EditSession
from picasapy.ini import (
    FilterWriteError,
    IniConflictError,
    IniDocument,
    IniSaveError,
    ini_source_path,
    load_or_empty,
    remove_ini_target_if_content_matches,
    update_document,
    with_backuphash,
)
from picasapy.ini.moddate import moddate_from_timestamp_ns
from picasapy.ini.names import INI_NAME
from picasapy.ioutil import write_atomic

#: Windowson a képfájlt egy olvasó (bélyegkép, néző) rövid ideig nyitva
#: tarthatja, ilyenkor a csere `PermissionError`-ral (sharing violation)
#: bukik. A metaadat-író mintájára néhányszor újrapróbáljuk (összesen ~1,8 mp).
_ZAR_UJRA = 8
_ZAR_KESLELTETES = 0.05


def _kep_irasa(image_path: Path, payload: bytes) -> None:
    write_atomic(
        image_path,
        payload,
        lock_retries=_ZAR_UJRA,
        lock_retry_delay=_ZAR_KESLELTETES,
    )

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
    image_path = Path(image_path)
    # #1425: a „szent" eredeti bármelyik ismert mappanév alatt ott lehet —
    # ha van, azt tekintjük megőrzöttnek, és nem teszünk mellé másodikat.
    existing_backup = find_original_backup(image_path)
    backup_path = existing_backup or _backup_path_for(image_path)
    filters_value = filters.to_value()
    section = _section_name(image_path)
    current_ini_path = image_path.parent / _INI_FILENAME
    original_ini_path = backup_path.parent / _INI_FILENAME
    # Minden ini-olvasás és visszaállítási állapotfelvétel a kép cseréje
    # ELŐTT történjen: olvasási hiba esetén ne maradjon beégetett, de el nem
    # könyvelt kép.
    current_before = _photo_ini_values(
        current_ini_path,
        section,
        (_FILTERS_KEY, _REDO_KEY, "backuphash", _MODDATE_KEY),
    )
    original_before = _photo_ini_values(
        original_ini_path, section, (_FILTERS_KEY, _MODDATE_KEY)
    )

    # A (b) lépés ELŐTTI bájtok — ezekre kell visszaállni, ha a (c) elbukik
    # (#297). Első mentésnél ez maga az eredeti (ugyanaz, ami a
    # `.picasaoriginals`-ba kerül), ismételt mentésnél a KORÁBBI mentés
    # renderelt tartalma.
    source_stat = image_path.stat()
    original_mtime_ns = source_stat.st_mtime_ns
    moddate_value = moddate_from_timestamp_ns(original_mtime_ns)
    bytes_before_write = image_path.read_bytes()

    # (a) Az eredeti megőrzése — KIZÁRÓLAG ha még nincs korábbi mentésből
    # (sem a mai, sem a 2009 előtti nevű mappában).
    backup_created_now = existing_backup is None
    backup_mtime_ns = (
        original_mtime_ns if backup_created_now else backup_path.stat().st_mtime_ns
    )
    if backup_created_now:
        write_atomic(backup_path, bytes_before_write, make_parents=True)

    # (a2) #444: MENTÉSENKÉNTI, sorszámozott pillanatkép a mentés ELŐTTI
    # bájtokról — ez teszi visszavonhatóvá az utolsó mentést a szerkesztések
    # elvesztése nélkül (`undo_save`). A „szent" eredeti (fent) ettől
    # függetlenül megmarad a Visszaállításhoz.
    snapshots = _existing_snapshots(image_path)
    next_number = (snapshots[-1][0] + 1) if snapshots else 1
    # A foglalt sorszámokat átlépjük — MINDKÉT helyen nézve.
    #
    # #1449 (a régi hely): a `<név>.<N>` alak kétértelmű, ott állhat egy
    # MÁSIK, önálló kép megőrzött eredetije (`a.jpg` pillanatképe és
    # `a.1.jpg` eredetije azonos nevű). #2512 óta ODA MÁR NEM ÍRUNK, tehát
    # felülírni nem tudnánk; a régi hely mégis számít, mert ugyanaz a
    # sorszám nem létezhet kétszer, két különböző helyen — az `undo_save` a
    # legnagyobb sorszámot veszi, és egyenlőségnél nem tudná eldönteni,
    # melyik a frissebb (`_legacy_snapshot_path`).
    #
    # Az ÚJ helyen a vizsgálat egy korábbi mentés árváját fogja meg (pl. ha
    # a kép azóta más nevet kapott és vissza).
    while (
        _snapshot_path(image_path, next_number).exists()
        or _legacy_snapshot_path(image_path, next_number).exists()
    ):
        next_number += 1
    write_atomic(
        _snapshot_path(image_path, next_number), bytes_before_write, make_parents=True
    )

    # (b) A renderelt kép az eredeti HELYÉRE.
    payload = _encode_image(image_path.suffix, rendered_image, jpeg_quality)
    _kep_irasa(image_path, payload)

    # (c) A lánc és a mentés előtti fájlidő az eredeti-mappa ini-jébe kerül,
    # a #5810 szerinti backuphash pedig az aktuális mappa ini-jébe. Két ini
    # frissítése nem atomikus, ezért a már sikeres írásokat visszagörgetjük,
    # ha a következő lépés hibázik.
    completed_ini_writes: list[tuple[Path, _PhotoIniSnapshot]] = []
    try:
        current_before.written_document = _update_ini_document(
            image_path,
            lambda document: with_backuphash(
                document.with_removed(_section_name(image_path), _FILTERS_KEY)
                .with_removed(_section_name(image_path), _REDO_KEY),
                _section_name(image_path),
            ),
            rollback_snapshot=current_before,
            section_name=section,
        )
        completed_ini_writes.append((current_ini_path, current_before))
        original_before.written_document = _update_ini_path(
            original_ini_path,
            lambda document: (
                document.with_value(
                    _section_name(image_path), _FILTERS_KEY,
                    filters_value, carried=True,
                )
                if filters_value
                else document.with_removed(_section_name(image_path), _FILTERS_KEY)
            ).with_value(
                _section_name(image_path), _MODDATE_KEY, moddate_value, carried=True
            ),
            rollback_snapshot=original_before,
            section_name=section,
        )
        completed_ini_writes.append((original_ini_path, original_before))
        # Az eredeti-mappa ini-frissítése a #643 szerint megérinti a
        # képfájlokat; a megőrzött eredeti másolatán ezt vissza kell állítani
        # az előzőleg rögzített mtime-ra. Első mentésnél ez a forrásé, későbbi
        # mentéseknél a változatlanul megőrzött eredetié.
        os.utime(
            backup_path,
            ns=(backup_path.stat().st_atime_ns, backup_mtime_ns),
        )
    except _INI_WRITE_ERRORS as error:
        rollback_errors = []
        for ini_path, previous_state in reversed(completed_ini_writes):
            try:
                _restore_photo_ini_values(
                    ini_path, section, previous_state
                )
            except _INI_WRITE_ERRORS as rollback_error:
                rollback_errors.append(rollback_error)
        image_restore_error = None
        try:
            _restore_image_or_raise(image_path, bytes_before_write, backup_path, error)
        except SaveError as restore_error:
            image_restore_error = restore_error
        if rollback_errors or image_restore_error:
            details = [str(item) for item in rollback_errors]
            if image_restore_error is not None:
                details.append(str(image_restore_error))
            raise SaveError(
                "A mentés meghiúsult, és a korábbi fájlállapot teljes "
                f"visszaállítása sem sikerült: {'; '.join(details)}"
            ) from error
        raise

    return SaveResult(
        image_path=image_path,
        original_backup_path=backup_path,
        backup_created_now=backup_created_now,
        filters_value=filters_value,
    )


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
    image_path = Path(image_path)
    snapshots = _existing_snapshots(image_path)
    if not snapshots:
        raise SaveError(_nincs_visszavonhato_mentes(image_path))
    number, snapshot = snapshots[-1]
    del number

    section = _section_name(image_path)
    current_ini_path = image_path.parent / _INI_FILENAME
    original_backup = find_original_backup(image_path)
    original_ini_path = _original_ini_path(image_path, original_backup)
    current_before = _photo_ini_values(
        current_ini_path, section, (_FILTERS_KEY, _REDO_KEY, "backuphash", _MODDATE_KEY)
    )
    original_before = _photo_ini_values(
        original_ini_path, section, (_FILTERS_KEY, _MODDATE_KEY)
    )
    current_section = current_before.document.section(section)
    original_section = original_before.document.section(section)
    original_filters = (
        original_section.get(_FILTERS_KEY) if original_section is not None else None
    )
    original_moddate = (
        original_section.get(_MODDATE_KEY) if original_section is not None else None
    )
    legacy_redo = (
        current_section.get(_REDO_KEY) if current_section is not None else None
    )
    restored_filters = (original_filters or legacy_redo or "")

    bytes_before = image_path.read_bytes()
    _kep_irasa(image_path, snapshot.read_bytes())
    completed_ini_writes: list[tuple[Path, _PhotoIniSnapshot]] = []
    try:
        def restore_current_metadata(document: IniDocument) -> IniDocument:
            # #643: a `redo=`-ból VISSZAforgatott lánc, átvitt tartalom.
            updated = (
                document.with_value(section, _FILTERS_KEY, restored_filters, carried=True)
                if restored_filters
                else document.with_removed(section, _FILTERS_KEY)
            ).with_removed(section, _REDO_KEY)
            # A régi mentések eredeti ini-jében nincs feltétlenül moddate.
            # Ilyenkor megőrizzük az aktuális ini esetleges értékét, és nem
            # találunk ki újat. #2675: az `originhash`-t nem töröljük.
            if original_moddate is not None:
                updated = updated.with_value(
                    section, _MODDATE_KEY, original_moddate, carried=True
                )
            return with_backuphash(updated, section)

        current_before.written_document = _update_ini_document(
            image_path,
            restore_current_metadata,
            rollback_snapshot=current_before,
            section_name=section,
        )
        completed_ini_writes.append((current_ini_path, current_before))
        if original_filters is not None:
            original_before.written_document = _update_ini_path(
                original_ini_path,
                lambda doc: doc.with_removed(section, _FILTERS_KEY),
                rollback_snapshot=original_before,
                section_name=section,
            )
            completed_ini_writes.append((original_ini_path, original_before))
    except _INI_WRITE_ERRORS as error:
        rollback_errors = []
        for ini_path, previous_state in reversed(completed_ini_writes):
            try:
                _restore_photo_ini_values(ini_path, section, previous_state)
            except _INI_WRITE_ERRORS as rollback_error:
                rollback_errors.append(rollback_error)
        image_restore_error = None
        try:
            _restore_image_or_raise(image_path, bytes_before, snapshot, error)
        except SaveError as restore_error:
            image_restore_error = restore_error
        if rollback_errors or image_restore_error:
            details = [str(item) for item in rollback_errors]
            if image_restore_error is not None:
                details.append(str(image_restore_error))
            raise SaveError(
                "A visszavonás meghiúsult, és a korábbi fájlállapot teljes "
                f"visszaállítása sem sikerült: {'; '.join(details)}"
            ) from error
        raise

    snapshot.unlink(missing_ok=True)
    return UndoSaveResult(
        image_path=image_path,
        restored_from=snapshot,
        restored_filters=restored_filters,
    )


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
    image_path = Path(image_path)
    backup_path = find_original_backup(image_path)
    if backup_path is None:
        raise SaveError(_missing_original_message(image_path))

    section = _section_name(image_path)
    current_ini_path = image_path.parent / _INI_FILENAME
    original_ini_path = backup_path.parent / _INI_FILENAME
    # Az ini előzetes olvasása a képfájl cseréje előtt történik. Így ha az
    # ini olvashatatlan, a Visszaállítás még nem változtatta meg a képet.
    current_before = _photo_ini_values(
        current_ini_path, section, _EDIT_BOOKKEEPING_KEYS
    )
    original_before = _photo_ini_values(
        original_ini_path, section, (_FILTERS_KEY,)
    )
    original_section = original_before.document.section(section)
    original_filters = (
        original_section.get(_FILTERS_KEY)
        if original_section is not None
        else None
    )

    # A visszaállítás ELŐTTI (szerkesztett) bájtok — ezekre kell visszaállni,
    # ha az ini-kulcsok törlése elbukik (#297, fordított irányú rés). Ha a
    # képfájl közben eltűnt, nincs mire visszaállni: ilyenkor a `revert`
    # pótolja a fájlt, és hiba esetén ott is hagyja.
    edited_bytes = image_path.read_bytes() if image_path.exists() else None

    original_bytes = backup_path.read_bytes()
    _kep_irasa(image_path, original_bytes)

    completed_ini_writes: list[tuple[Path, _PhotoIniSnapshot]] = []

    try:
        current_before.written_document = _update_ini_document(
            image_path,
            lambda document: (
                document.with_removed(section, _FILTERS_KEY).with_removed(
                    section, _REDO_KEY
                )
            ),
            rollback_snapshot=current_before,
            section_name=section,
        )
        completed_ini_writes.append((current_ini_path, current_before))
        if original_filters is not None:
            original_before.written_document = _update_ini_path(
                original_ini_path,
                lambda document: document.with_removed(section, _FILTERS_KEY),
                rollback_snapshot=original_before,
                section_name=section,
            )
            completed_ini_writes.append((original_ini_path, original_before))
    except _INI_WRITE_ERRORS as error:
        rollback_errors = []
        for ini_path, previous_state in reversed(completed_ini_writes):
            try:
                _restore_photo_ini_values(ini_path, section, previous_state)
            except _INI_WRITE_ERRORS as rollback_error:
                rollback_errors.append(rollback_error)
        image_restore_error = None
        if edited_bytes is not None:
            try:
                _restore_image_or_raise(image_path, edited_bytes, backup_path, error)
            except SaveError as restore_error:
                image_restore_error = restore_error
        if rollback_errors or image_restore_error:
            details = [str(item) for item in rollback_errors]
            if image_restore_error is not None:
                details.append(str(image_restore_error))
            raise SaveError(
                "A visszaállítás meghiúsult, és a korábbi fájlállapot teljes "
                f"visszaállítása sem sikerült: {'; '.join(details)}"
            ) from error
        raise

    return RevertResult(
        image_path=image_path,
        restored_from=backup_path,
        removed_keys=_EDIT_BOOKKEEPING_KEYS,
    )


def _restore_image_or_raise(
    image_path: Path, payload: bytes, backup_path: Path, error: Exception
) -> None:
    """A képfájl visszaállítása a művelet előtti bájtokra (#297).

    Ha maga a visszaállítás is elbukik, `SaveError`-t emel: a felhasználónak
    magyarul, cselekvésre fordíthatóan meg kell tudnia, hogy a kép fizikailag
    elmentődött, a `.picasa.ini` nyilvántartása viszont nem követte — így
    tudja, hogy a kép a következő megnyitáskor kétszer szerkesztettnek
    látszhat, és hol keresse az eredetit."""
    try:
        _kep_irasa(image_path, payload)
    except OSError as restore_error:
        raise SaveError(
            f"A kép elmentődött ({image_path}), de a .picasa.ini "
            f"nyilvántartása nem frissült ({error}), és a kép mentés előtti "
            f"állapotát sem sikerült visszaállítani ({restore_error}). A kép "
            f"a következő megnyitáskor kétszer szerkesztettnek látszhat; az "
            f"érintetlen eredeti itt található: {backup_path} "
            f"(a(z) {ORIGINALS_DIR_NAME} mappában)."
        ) from error


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
    image_path = Path(image_path)
    for dir_name in ORIGINALS_DIR_NAMES:
        candidate = image_path.parent / dir_name / image_path.name
        if candidate.is_file():
            return candidate
    return None


def _missing_original_message(image_path: Path) -> str:
    """A „nincs megőrzött eredeti" ÉRTHETŐ üzenete (#1425).

    A néma elutasítás a projekt visszatérő hibaosztálya (#1003, #1207,
    #1213): a felhasználónak — aki nem programozó — meg kell tudnia, MIT
    kerestünk, HOL, és mikor működik egyáltalán a Visszaállítás. Belső
    függvénynevek nem szivároghatnak ki ide.
    """
    mappak = " és ".join(f"„{name}”" for name in ORIGINALS_DIR_NAMES)
    return (
        f"Ehhez a képhez nincs megőrzött eredeti: {image_path.name}. "
        f"A kép melletti {mappak} nevű almappák egyikében sem találtuk meg "
        f"a mentés előtti változatát. A Visszaállítás csak olyan képnél "
        f"működik, amelyről készült ilyen másolat — a PicasaPy és a Picasa "
        f"is az első mentéskor készíti el. "
        f"(Keresett hely: {image_path.parent})"
    )


def _backup_path_for(image_path: Path) -> Path:
    """Ahová egy ÚJ eredeti-mentés kerül: mindig a `.picasaoriginals`.

    A régi, `Originals` mappát csak OLVASSUK (ld. `find_original_backup`) —
    a Picasa-korabeli, látható mappába nem írunk.
    """
    return image_path.parent / ORIGINALS_DIR_NAME / image_path.name


def _original_ini_path(image_path: Path, backup_path: Path | None = None) -> Path:
    """A kiválasztott megőrzött eredeti-mappa `.picasa.ini`-je.

    Mentésnél a tényleges eredeti fájl mappáját kapjuk meg. Visszavonásnál
    előbb ugyanazt a fájlt keressük; ha hiányzik, a meglévő eredeti-mappa
    ini-jét választjuk, végül az új `.picasaoriginals` mappa az alapérték.
    """
    if backup_path is None:
        backup_path = find_original_backup(image_path)
    if backup_path is not None:
        return backup_path.parent / _INI_FILENAME

    for directory_name in ORIGINALS_DIR_NAMES:
        directory = image_path.parent / directory_name
        if ini_source_path(directory / _INI_FILENAME) is not None:
            return directory / _INI_FILENAME
    return image_path.parent / ORIGINALS_DIR_NAME / _INI_FILENAME


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
    directory = image_path.parent / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME
    return directory / f"{image_path.stem}.{number}{image_path.suffix}"


def _legacy_snapshot_path(image_path: Path, number: int) -> Path:
    """A pillanatkép RÉGI, a `.picasaoriginals`-szal közös helye (#444).

    Ide már nem írunk (#2512), de a sorszám-kiosztásnál számít: ha a régi
    helyen áll ezen a néven fájl, a sorszámot átlépjük. Nem a felülírás
    ellen — az új hely miatt az kizárt —, hanem hogy ugyanaz a sorszám ne
    létezzen KÉTSZER, két különböző helyen: az `undo_save` a legnagyobb
    sorszámú példányt veszi, és egyenlőségnél nem tudná eldönteni, melyik
    a frissebb.
    """
    directory = image_path.parent / ORIGINALS_DIR_NAME
    return directory / f"{image_path.stem}.{number}{image_path.suffix}"


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
    from picasapy.fileops.originals import snapshot_numbers

    directory = image_path.parent / ORIGINALS_DIR_NAME
    return sorted(
        (szam, path) for szam, _, path in snapshot_numbers(directory, image_path)
    )


def _nincs_visszavonhato_mentes(image_path: Path) -> str:
    """A „nincs mit visszavonni" üzenet — a KÉT eset másképp szól.

    Az `_existing_snapshots` üres eredménye nem mindig azt jelenti, hogy a
    mappa üres: kimarad belőle az a példány is, aminek a KÉPMAPPÁBAN van
    azonos nevű gazdája (`a.jpg` mentése `a.1.jpg` pillanatképet ír, de
    `a.1.jpg` lehet egy önálló kép is). Az óvatosság indokolt — az
    `undo_save` a felhasznált pillanatképet TÖRLI —, de az „üres vagy
    hiányzik" ilyenkor egyszerűen nem igaz, és a felhasználó nem tudja meg,
    mit tehetne (#1449 átnézés, 3. lelet)."""
    from picasapy.fileops.originals import ambiguous_snapshot_names

    directory = image_path.parent / ORIGINALS_DIR_NAME
    ketertelmuek = ambiguous_snapshot_names(directory, image_path)
    if not ketertelmuek:
        return (
            f"Nincs visszavonható mentés: {image_path.name} "
            f"({ORIGINALS_DIR_NAME} üres vagy hiányzik)"
        )
    nevek = ", ".join(ketertelmuek)
    return (
        f"A legutóbbi mentést nem tudjuk visszavonni ennél a képnél: "
        f"{image_path.name}. A(z) „{ORIGINALS_DIR_NAME}” mappában van hozzá "
        f"illő fájl ({nevek}), de a képmappában UGYANEZEN a néven önálló kép "
        f"is áll — így nem dönthető el, hogy az a kép mentés előtti "
        f"állapota-e, vagy a másik kép megőrzött eredetije. Biztonságból "
        f"békén hagyjuk: a visszavonás azt a fájlt törölné, és ha a másik "
        f"képhez tartozik, annak a visszaútja veszne el. Ha vissza szeretné "
        f"kapni a visszavonás lehetőségét, adjon a(z) {nevek} nevű képnek "
        f"másik nevet."
    )


def _section_name(image_path: Path) -> str:
    """A `.picasa.ini`-beli szekciónév: a fájl neve, a spec `[<fájlnév.ext>]`
    szabálya szerint (ld. `picasa-ini-format.md`)."""
    return image_path.name


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
    return _update_ini_path(
        image_path.parent / _INI_FILENAME,
        mutate,
        rollback_snapshot=rollback_snapshot,
        section_name=section_name,
    )


def _update_ini_path(
    ini_path: Path,
    mutate,
    *,
    rollback_snapshot: _PhotoIniSnapshot | None = None,
    section_name: str | None = None,
) -> IniDocument:
    """Ütközésbiztos, atomikus ini-frissítés az `ini` round-trip API-n át."""
    if rollback_snapshot is None:
        return update_document(ini_path, mutate, backup=True)
    if section_name is None:
        raise ValueError("A visszagörgetéshez ini-szekciónév szükséges")

    # Az update_document minden ütközésnél újra meghívja a tiszta mutátort,
    # és a nyertes próbálkozás `mutated` objektumát adja vissza. Az azonos
    # objektumhoz rögzítjük a tényleges előtti dokumentumot és forrást, hogy
    # a kompenzáció ne az előzetes (esetleg elavult) olvasást írja vissza.
    attempts: list[tuple[IniDocument, Path | None, IniDocument]] = []

    def capture_attempt(document: IniDocument) -> IniDocument:
        updated = mutate(document)
        attempts.append((updated, ini_source_path(ini_path), document))
        return updated

    written = update_document(ini_path, capture_attempt, backup=True)
    for candidate, source, before in reversed(attempts):
        if candidate is written:
            section = before.section(section_name)
            rollback_snapshot.values = {
                key: section.get(key) if section is not None else None
                for key in rollback_snapshot.values
            }
            rollback_snapshot.document = before
            rollback_snapshot.target_existed = source == ini_path
            rollback_snapshot.written_document = written
            return written
    raise RuntimeError("Az ini-frissítés nyertes előállapota nem található")


def _photo_ini_values(
    ini_path: Path, section_name: str, keys: tuple[str, ...]
) -> _PhotoIniSnapshot:
    """Egy képszakasz érintett kulcsainak mentés előtti értékei."""
    target_existed = ini_path.is_file()
    document = load_or_empty(ini_path)
    section = document.section(section_name)
    return _PhotoIniSnapshot(
        values={
            key: section.get(key) if section is not None else None
            for key in keys
        },
        document=document,
        target_existed=target_existed,
    )


def _restore_photo_ini_values(
    ini_path: Path, section_name: str, snapshot: _PhotoIniSnapshot
) -> None:
    """API-n át visszaállítja a kompenzáló írással felülírt kulcsértékeket.

    Csak azt a kulcsot állítja vissza, amely a kompenzáló írás óta is a mi
    kiírt értékünkön áll. A közben érkezett külső változást megőrzi.
    """

    written_section = (
        snapshot.written_document.section(section_name)
        if snapshot.written_document is not None
        else None
    )

    def mutate(document):
        current_section = document.section(section_name)
        for key, value in snapshot.values.items():
            written_value = (
                written_section.get(key) if written_section is not None else None
            )
            current_value = (
                current_section.get(key) if current_section is not None else None
            )
            if current_value != written_value:
                continue
            if value is None:
                document = document.with_removed(section_name, key)
            else:
                document = document.with_value(
                    section_name,
                    key,
                    value,
                    carried=key in (_FILTERS_KEY, _REDO_KEY),
                )
        return document

    if snapshot.target_existed:
        update_document(ini_path, mutate, backup=False)
        return

    # A mentés hozhatta létre a cél `.picasa.ini`-t (esetleg egy régi
    # `Picasa.ini` forrásból kiindulva). Ha a sikeres írás óta bájtra pontosan
    # változatlan maradt, törölhető a művelet előtti hiányállapot visszaállításához.
    if snapshot.written_document is not None and remove_ini_target_if_content_matches(
        ini_path, snapshot.written_document
    ):
        return
    if not ini_path.is_file():
        return

    # Közben módosított célfájlnál nem törlünk: az érintett kulcsokat API-n
    # át visszaállítjuk, az esetleges idegen sorokat pedig megőrizzük.
    update_document(ini_path, mutate, backup=False)


def _encode_image(suffix: str, image: np.ndarray, jpeg_quality: int) -> bytes:
    """A renderelt képmátrix kódolása a cél kiterjesztésének megfelelő
    formátumba — `cv2.imencode`-dal (memóriapuffer, nem fájlútvonal),
    accent-path-biztosan (MEMORY.md #190)."""
    ext = suffix.lower() or ".jpg"
    params: list[int] = []
    if ext in (".jpg", ".jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
    # #1527: az OpenCV NEM mindig `ok=False`-szal jelez. Ismeretlen
    # kiterjesztésnél `cv2.error`-t DOB („could not find encoder for the
    # specified extension"), ami eddig NYERSEN szökött ki a mentésből — a
    # `save_controller._SAVE_ERRORS` sem fogta, mert a `cv2.error` nem
    # `OSError`/`ValueError`. Ez a hivatalos „fájlformázási hiba" ága
    # (`CFileSaveThread:filesaveerr3`), tehát ide `SaveError` való.
    try:
        ok, encoded = cv2.imencode(ext, image, params)
    except cv2.error as hiba:
        raise SaveError(f"A renderelt kép nem kódolható ide: {ext!r}") from hiba
    if not ok:
        raise SaveError(f"A renderelt kép nem kódolható ide: {ext!r}")
    return encoded.tobytes()
