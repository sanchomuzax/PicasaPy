"""A megőrzött eredeti a képpel EGYÜTT költözik (#1430).

A #371 kutatása kizárta, hogy a Picasa a szerkesztést a képfájlon kívül
bárhol tárolná: a retus és a vörösszem-javítás a JPEG-be van beleégetve.
A „Vissza az eredetihez” EGYETLEN útja tehát a kép mellé mentett, érintetlen
másolat. Ha az elszakad a képtől - mert a képet átneveztük vagy másik
mappába vittük -, a szerkesztés visszafordíthatatlanná válik, és a régi
helyén árván marad egy fájl, amiről már senki nem tudja, kihez tartozik.
Ez a modul a kísérőfájl-logika: a `rename_photo` és a `move_photo`
mozgatása (#1430), a `copy_photo` másolása (#1450), valamint a törlés
leltára (`companions_of`, #1451). Az ini-szekcióik a testvérmodulban
költöznek (`original_ini.py`, #1448).

## Modulok (a szétbontás után)

Ez a fájl csak az újraexportálást végzi: a nevek ugyanonnan importálhatók,
mint korábban. A tényleges kód a `fileops/originals_*.py` modulokban van:

* `originals_cache` - a kötegelt listázás gyorstára (`listing_cache`, #1452).
* `originals_names` - a mappanevek, a pillanatkép-keresés, a foglaltság
  és a `companions_of`.
* `originals_plan` - az `OriginalMove` és a költözés terve, ütközés-ellenőrzéssel.
* `originals_move` - a fájlok áthelyezése, a visszagörgetés és az `originals_follow`.
* `originals_copy` - a `copy_preserved_originals` és a takarítása.
* `originals_messages` - az „útban van egy fájl" és a figyelmeztető mondatok.

Egy teszt, amely a belső `_move`/`_copy` fogantyút cseréli, a modul
útvonalát a fenti listából kérje: a csere ott hat, ahol a hívás történik.

## A pillanatképeknek KÉT helyük van (#2512)

A `<név>.<N><kiterjesztés>` név egy önálló kép „szent" eredetijétől
megkülönböztethetetlen volt, ezért az ÚJ pillanatképeink az eredeti-mappán
belüli `.picasapy-snapshots` alkönyvtárba mennek
(`docs/decisions/pillanatkep-nevter.md`). A régi, KÖZÖS helyen álló
példányokat továbbra is megtaláljuk és visszük a képpel - köztük azokat is,
amelyeket a windowsos Picasa írt.

A két hely két SZABÁLYT is jelent. A régin áll a #1449 óvatossága (ha a
képmappában azonos nevű önálló kép van, békén hagyjuk a példányt); az újon
NEM, mert oda rajtunk kívül senki nem ír. A gazda-szűrés odaát csak a saját
pillanatképeinket hagyná hátra a kép költözésekor - pont az a kár, amit ez a
modul megelőzni hivatott.

Költözéskor a pillanatkép a SAJÁT szintjén marad: a `.picasapy-snapshots`-ból
induló oda érkezik, a közös helyről induló oda. Ugyanaz a gondolat, mint a
mappanévnél (lent): a régi helyen álló példány a párhuzamosan futó Picasáé is
lehet, azt nem rántjuk be a mi névterünkbe.

## A mappanév a költözéskor NEM változik

Egy `Originals`-ból induló eredeti a célmappában is `Originals` alá kerül,
nem a `.picasaoriginals`-ba. Két oka van:

* Az `ORIGINALS_DIR_NAMES` sorrendje jelentést hordoz (a régi példány nyer,
  mert az van közelebb az érintetlen eredetihez, #1425). A mappanév
  átírásával ez az információ elveszne.
* Ha a képhez MINDKÉT mappában van példány, az egy célmappába terelés
  ütközést okozna - a kettő közül az egyiket el kellene dobni.

A `.picasaoriginals`-t továbbra is csak a mentés hozza létre újonnan; itt
azért készül el a célmappában, mert egy MÁR MEGLÉVŐ eredetinek kell hely.

## Sorrend és visszagörgetés

Előbb a kísérőfájlok költöznek, és csak utána maga a kép. Így ha a kísérő
költöztetése bukik, a kép el sem indul: a felhasználó felől nézve nem
történt semmi, és a Visszaállítás a régi helyen működik tovább. Ha a KÉP
mozgatása bukik el (verseny egy párhuzamos íróval, tele lemez), az
`originals_follow` visszagörgeti a már elmozdított kísérőket.

## Ütközés: a kötegelt úton FELOLDJUK, egyébként MEGMAGYARÁZZUK

Felülírni sosem írunk felül: ha a célhelyen már van azonos nevű fájl (pl.
egy korábbi költözés árvája), a művelet EL SEM INDUL, és a hiba üzenete
megmondja, mi van útban - a néma elutasítás a projekt visszatérő
hibaosztálya (#1003, #1207, #1213). A tanács attól függ, KIÉ az útban lévő
fájl: ha egy másik, ÉLŐ kép eredetije, a törlését tanácsolni pont azt a kárt
okozná, amit ez a modul megelőzni hivatott (`_occupied_message`).

A KÖTEGELT áthelyezés (`fileops/batch.py`) viszont ide el sem jut, és ez
TUDATOS döntés (#1448 2. átnézés, 1. lelet): ott a felhasználó a művelet
indításakor KIMONDOTTAN az „átnevezés" házirendet választotta, ezért a
foglalt eredeti-hely nem megállítja a képet, hanem pótnevet ad neki
(`originals_slot_free` → `batch._free_name`). A hibaüzenet tanácsa - „adjon
inkább a képnek másik nevet" - épp az, amit a pótnév automatikusan megtesz,
és közben a célban álló idegen fájlhoz nem nyúlunk: a másik kép eredetije
és a mi pillanatképünk is a saját, ütközésmentes nevén marad. A magyarázó
üzenet így az F2-es átnevezésé, a másolásé és az egyfájlos mozgatásé marad
- azoké az utaké, ahol nincs mit feloldani, mert a nevet a felhasználó adta
meg.

Mindez arra a képre vonatkozik, amelyiknek VAN megőrzött eredetije: kísérő
nélkül nincs mit elhelyezni, ott a kötegelt út csak az ÖRÖKBEFOGADÁS ellen
őriz (`originals_slot_free(..., moving_companions=False)`, #2510) - a
foglaltnak látszó, de valójában gazdás pillanatkép-hely miatt korábban
fölösleges ütközés-párbeszéd és néma átnevezés lett belőle.

## A megnyugtatás feltételes

Ha a visszagörgetés IS elbukik, a „minden a helyén maradt" mondat HAMIS
lenne, és a következménye nem kozmetikai: a `find_original_backup` a kép
mellett ilyenkor nem talál eredetit, az `edit/save.py` pedig
`existing_backup is None` mellett a MÁR SZERKESZTETT bájtokat írja be új
„eredetiként". A megnyugtatott felhasználó egyetlen mentéssel véglegesen
elveszítené az érintetlen változatot - ezért a `_stranded_warning` ilyenkor
azt mondja meg, mit NE tegyen (`_reassurance` csak üres `stranded` mellett
szólalhat meg).

A hibaüzenetek a KÖTEGELT úton is kimennek: a felületen az áthelyezés mindig
a `movePhotos`-t hívja, ezért a `FileOpsController` a `batchFinished`-del az
első bukás okát is átadja (#1430). Amit a pótnév nem old fel
(fájlrendszer-hiba, verseny egy párhuzamos íróval), annak az oka így a
kötegelt úton is eljut a felhasználóig.
"""

from __future__ import annotations

from picasapy.fileops.originals_cache import listing_cache
from picasapy.fileops.originals_copy import copy_preserved_originals
from picasapy.fileops.originals_move import (
    move_preserved_originals,
    originals_follow,
    undo_original_moves,
)
from picasapy.fileops.originals_names import (
    ambiguous_snapshot_names,
    companions_of,
    originals_slot_free,
    snapshot_numbers,
)
from picasapy.fileops.originals_plan import (
    OriginalMove,
    _reject_unsafe_targets,  # noqa: F401 - a tesztek is használják (#1430)
    plan_original_moves,
)

__all__ = [
    "OriginalMove",
    "ambiguous_snapshot_names",
    "companions_of",
    "copy_preserved_originals",
    "listing_cache",
    "move_preserved_originals",
    "originals_follow",
    "originals_slot_free",
    "plan_original_moves",
    "snapshot_numbers",
    "undo_original_moves",
]
