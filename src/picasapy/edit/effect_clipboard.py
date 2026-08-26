"""„Az összes effektus másolása/beillesztése" — a `filters=` lánc átvitele
képek között (#426, Picasa `ID_EDIT_COPYALLEFFECTS`/`ID_EDIT_PASTEALLEFFECTS`).

Ez a modul KIZÁRÓLAG tiszta logikát tartalmaz (nincs fájl-I/O, nincs Qt-
függés). Az alkalmazás-szintű vágólap ÁLLAPOTA (mit másoltunk utoljára) és
a mappánkénti kötegelt ini-írás a vezérlő-oldalon van
(`picasapy.app.photo_ops_controller.EffectClipboardMixin`).

## A lánc EGÉSZBEN megy át — és miért nem szűrünk (#1544)

A #426 eredeti megvalósítása a `crop64`/`crop` (geometria),
`redeye`/`retouch` (régió-adat), `save`/`rot`/`picnik` (könyvelés) és
`moviestart`/`movieend` (klip-vágópont) bejegyzéseket KIHAGYTA a másolásból.
Ezt a szabályt a `filterdesc.xml` `mode="history"`/`persist` oszlopaiból
KÖVETKEZTETTÜK — nem mérésből. A következtetés kézenfekvő volt, de **téves**:

* a `Picasa3.exe` másolójának (`0x005fecd0`) és beillesztőjének
  (`0x005fefc0`) teljes hívási útján **nincs szűrő-névre vonatkozó
  összehasonlítás** — sem fehér-, sem feketelista;
* függetlenül, a bináris-indexből ellenőrizve: a `"filters"` sztringnek
  **33** kódhivatkozása van (köztük a `0x006af3e0`/`0x006af650`
  getter/setter), a `crop64` sztringnek **nulla** ⇒ a program sehol nem
  hasonlít össze semmit ezzel a névvel, tehát nem is szűrhet rá;
* a `mode` attribútum valóban létezik, de a szerkesztési ELŐZMÉNY
  megjelenítését vezérli, nem a vágólapot.

A szűrés tehát saját találmány volt, és funkciót vett el: a felhasználó azt
hitte, átvitte a szerkesztést, és némán mást kapott. Bizonyíték és döntés:
`docs/decisions/effektus-vagolap-ket-reteg.md` (#1534), jegy: #1544.

## A `crop=` tükör-kulcs

A `filters=` láncban ülő `crop64` az EREDETI Picasában önmagában nem vág —
a renderelést a képszekció külön `crop=rect64(...)` kulcsa hajtja
(`docs/specs/filters-decoded.md` 1. kör). Ezért a lánc átvitelekor a
tükör-kulcsot is követni kell; az értékét a `crop_mirror_value()` adja.
(A `.picasa.ini`-be írás maga a vezérlő dolga, az `ini/` csomag API-ján át.)
"""

from __future__ import annotations

from picasapy.edit.session import EditSession
from picasapy.ini.filters import parse_filters, serialize_filters
from picasapy.ini.rect64 import encode_rect64


def copy_all_effects(filters_value: str | None) -> str:
    """„Az összes effektus másolása": a `filters=` lánc vágólap-tartalma.

    A láncot EGÉSZBEN veszi át — a vágást (`crop64`), a régió-adatokat
    (`redeye`/`retouch`) és az ismeretlen (jövőbeli/idegen) bejegyzéseket is
    —, ahogy az eredeti Picasa másolója teszi a teljes `filters` sztringgel.
    Az egyetlen normalizálás a parse/serialize körúté: a hiányzó záró
    pontosvessző pótlása (a Picasa maga is mindig kiírja).

    Args:
        filters_value: A forráskép nyers `filters=` értéke (`None`/üres
            string üres láncot jelent).

    Returns:
        A vágólapra teendő `filters=` érték (üres eredmény esetén üres
        string).
    """
    return serialize_filters(parse_filters(filters_value or ""))


def paste_all_effects(clipboard_value: str) -> str:
    """„Az összes effektus beillesztése": a cél `filters=` értéke a
    beillesztés UTÁN.

    A beillesztés TELJES CSERE, nem rétegzés: a célkép meglévő lánca —
    a saját vágásával és régió-adataival együtt — eltűnik, a helyére a
    vágólap lánca kerül. Ez az eredeti Picasa viselkedése (a beillesztő a
    teljes `filters` sztringet írja vissza), és a művelet a
    `undoPasteAllEffects`-szel visszavonható.

    Args:
        clipboard_value: Egy korábbi `copy_all_effects()` hívás eredménye.

    Returns:
        A célkép új `filters=` értéke (megegyezik `clipboard_value`-val —
        a függvény a szemantika dokumentálására és a jövőbeli
        finomításokra hagy egy nevesített csatlakozási pontot).
    """
    return clipboard_value


def crop_mirror_value(filters_value: str | None) -> str | None:
    """A lánchoz tartozó `crop=` tükör-kulcs értéke, vagy `None`.

    A renderelést az eredeti Picasában nem a láncbeli `crop64`, hanem a
    képszekció külön `crop=rect64(...)` kulcsa hajtja
    (`docs/specs/filters-decoded.md`). A tükrözés szabálya MÉRVE, az éles
    korpuszon (18 801 szekció, 5658 `filters=` lánc):

    * 763 láncban van `crop64`, ebből **761**-hez tartozik `crop=` kulcs, és
      mind a 761 esetben az értéke **pontosan a lánc UTOLSÓ `crop64`-je**;
    * a 38 darab TÖBB `crop64`-et tartalmazó láncnál is **38/38** az
      utolsót tükrözi, az elsőt **nulla** — ugyanaz az „utolsó nyer"
      szabály, amit a render-lánc is követ (#130, `render/chain.py`);
    * `crop64` nélküli láncnál egyetlen `crop=` kulcs sincs (0/761).

    **#1550:** ez a függvény korábban maga kereste ki az utolsó `crop64`-et,
    mert az `EditSession.crop()` akkor még az ELSŐT adta. A #1550 a
    `crop()`-ot ugyanerre a szabályra állította, ezért a másolat megszűnt:
    innentől a KÖZÖS úton megy. Így a felület (`hasCrop`, `cropSelection`),
    a szerkesztő mentése és a beillesztés tükör-kulcsa nem tud elcsúszni
    egymástól.

    Args:
        filters_value: Egy `filters=` lánc (`None`/üres = nincs lánc).

    Returns:
        `"rect64(<hex>)"`, ha a láncban van érvényes `crop64`; egyébként
        `None`. Sérült/idegen hex-paraméternél is `None` (nem dob) — a
        #301-elv szerint.
    """
    rect = EditSession.from_value(filters_value).crop()
    return None if rect is None else f"rect64({encode_rect64(rect)})"
