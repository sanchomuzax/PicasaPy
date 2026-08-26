# ADR-007: Az effektus-vágólap két rétege — melyik a hűséges, és melyik kap felületet

Dátum: 2026-08-26 · Státusz: ELFOGADVA · jegy: **#1534**

> **Egymondatos összefoglaló:** a felületen ma a **rosszabb** réteg van
> bekötve — az eredeti Picasa a `filters=` láncot **egészben** viszi át
> (a vágással együtt), a mi bekötött kötegelt rétegünk viszont **szűr**.
> A #152-es réteg tartalmi viselkedése a hűséges; a többszintű undo-verme
> viszont az eredetiben nem létezik.

## A helyzet

A programban **két, egymástól független effektus-vágólap** él:

| | „kötegelt" (#426) | „kép-specifikus" (#152) |
|---|---|---|
| tiszta logika | `src/picasapy/edit/effect_clipboard.py` | `EditSession.copy_effects()` / `paste_effects()` (`src/picasapy/edit/session.py:524–560`) |
| vezérlő | `EffectClipboardMixin` (`src/picasapy/app/photo_ops_controller.py:599–770`) | `EffectsClipboardMixin` (`src/picasapy/app/effects_controller.py`) |
| bekötve | `controller.py:100` (`PhotoOpsMixin`) | `controller.py:106` |
| QML-hivatkozás | `Main.qml:767–775`, `PicasaMenuBar.qml:296–325` | **nulla** |

A #152-es réteg tehát **élő kód** (az `AppController`-be van keverve, hét
teszt futtatja), de a felületről **elérhetetlen**.

## A mérés — mit tud ma a két réteg

A `filters=` lánccal
`crop64=1,45930000ba03defe;bw=1;sepia=1;redeye=1,abc;tilt=1,0.500000,0.200000;`
mérve (2026-08-26):

* **kötegelt (#426):** `bw=1;sepia=1;tilt=1,0.500000,0.200000;` — eldobja a
  `crop64`-et **és a `redeye`-t** is;
* **kép-specifikus (#152):** a teljes láncot változtatás nélkül átviszi, és
  a `crop=` tükör-kulcsot is kiírja (`effects_controller._write_session`).

Visszavonás: a #152 verme valódi LIFO (`_effects_undo_stack.append()` /
`.pop()`), tehát **többszintű**; a kötegelté egyetlen, felülírt rekesz
(`_effect_clipboard_undo`). A többszintűséget **lemértük** (két beillesztés
ugyanarra a képre, majd két visszavonás):

| lépés | a célkép `filters=` lánca | `canUndoPasteEffects` |
|---|---|---|
| kiindulás | `bw=1;` | — |
| 1. beillesztés | `sepia=1;` | igaz |
| 2. beillesztés | `warm=1;` | igaz |
| 1. visszavonás | `sepia=1;` | igaz |
| 2. visszavonás | `bw=1;` | hamis |

⇒ a képesség **valóban működik**, két szinten igazolva.

⚠️ **A „kép-specifikus" elnevezés félrevezető.** Mindkét réteg
kijelölés-alapú és kötegképes: a `pasteEffects` is végigmegy a kapott
sorokon, mappánként egy ini-írással. A két réteg között **csak két
különbség van**: mit szűr a másolás, és milyen mély a verem.

## A bizonyíték az eredeti Picasáról

A `Picasa3.exe`
(`research/copy_Picasa_3_7/Picasa3/Picasa3.exe`, sha256 egyezik a
bináris-index `meta.json`-jával) diszasszemblálva.

### 1. EGY parancs, KÉT ág — nem két külön funkció

A teljes, menüépítő kódból kinyert parancstérképben
(`docs/specs/picasa-menu-parancsok.csv`, proveniencia:
`picasa-menu-leltar.md` 7.) **pontosan két** effektus-vágólap parancs van,
és mindkettő a **Szerkesztés** menüben:
`eMenuEdit,ID_EDIT_COPYALLEFFECTS` és `eMenuEdit,ID_EDIT_PASTEALLEFFECTS`.
A **Kép menüben** (`eMenuPicture`, 19 parancs) egy sincs.

A főablak parancs-diszpécsere (`0x005cb990`) **egyetlen kezelőpárt** hív
mind a négy vágólap-parancsra, `bool` kapcsolóval — `flag=0` = effektus,
`flag=1` = szöveg; két külön puffer (`[this+0xc78]` az effektusé):

```
0x005cc5d5  push edi (0)  ; call 0x5fecd0   ⇒ COPY ALL EFFECTS
0x005cc5e2  push edi (0)  ; call 0x5fefc0   ⇒ PASTE ALL EFFECTS
0x005cc5ee  push 1        ; call 0x5fecd0   ⇒ COPY TEXT
0x005cc5fc  push 1        ; call 0x5fefc0   ⇒ PASTE TEXT
```

Mindkét kezelő ugyanúgy nyit: megnézi, látszik-e az `"editpanel/preview"`
(`0x005fed2f`, ill. `0x005ff050`), és **elágazik**:

* **szerkesztő nyitva** → a benne nyitott **egyetlen** képre dolgozik, az
  **élő szűrővermen** (a getter `InterlockedCompareExchange`-dzsel teszteli,
  hogy a cél a nyitott kép-e);
* **könyvtárnézet** → a kijelölésre. A **másolás pontosan EGY** kijelölt
  képet enged (`and ebp,0xfffffffe; cmp ebp,2` → különben
  `IDS_SELECT_ONE_ONLY`), a **beillesztés ≥1**-et, a mozgóképeket kihagyva
  (hét típuskód → `IDS_SOME_EDITS_FAILED_TYPE`).

⇒ **Az eredetiben nem két funkció van, hanem EGY parancs kétágú
kezelővel**, amit a szerkesztő nyitottsága választ ki. Nálunk ez a két ág
két külön, párhuzamos rétegként létezik, és csak az egyik van bekötve.

### 2. A vágás ÁTMEGY — a másolás semmit nem szűr

A másoló (`0x005fecd0`) a **teljes** `filters` sztringet, illetve az élő
szűrőverem klónját veszi; a beillesztő (`0x005fefc0`) a **teljes** láncot
írja vissza. A `"filters"` tulajdonságkulcs a `0x00c80b04` címen ül, és a
getter/setter párja `0x006af3e0` / `0x006af650`.

🔑 **A teljes hívási úton nincs egyetlen szűrő-azonosítóra vonatkozó
összehasonlítás sem** — nincs `crop64`-kivétel, nincs fehér- vagy
feketelista.

Ezt **függetlenül ellenőriztük** a bináris-indexből (nem a diszasszemblátum
átirata):

* `string_xrefs.csv` — a `"filters"` sztringnek **33** kódhivatkozása van,
  közte **pontosan** a `0x006af3e0` és a `0x006af650`;
* a `crop64` sztring **létezik** a binárisban, de **NULLA** kódhivatkozása
  van ⇒ a program sehol nem hasonlít össze semmit ezzel a névvel, tehát a
  másolás nem is szűrhet rá.

⇒ **Az eredeti „Az összes effektus beillesztése" ÁTVISZI a vágást.**

⚠️ **Ez megdönti a #426 jegy szűrési szabályát.** A kötegelt réteg a
`filterdesc.xml` `mode="history"` / `persist` oszlopaiból **következtette**
a kizárást (`edit/effect_clipboard.py` modul-docstring). A `mode` attribútum
valóban létezik (`filterdesc.xml`: `id="crop64" mode="history"`), de a
**másolás/beillesztés kezelője soha nem olvassa** — a `mode` a szerkesztési
előzmény megjelenítését vezérli, nem a vágólapot. A következtetés
kézenfekvő volt, de a kód nem támasztja alá.

### 3. Visszavonás: az eredetiben NINCS a beillesztéshez

* A binárisban **nulla** olyan felirat van, amiben az „undo" és a „paste"
  együtt szerepel (függetlenül ellenőrizve: `strings | grep -i undo |
  grep -ic paste` → `0`).
* A beillesztő `0x005fefc0` diszasszemblátumában **nincs
  visszavonás-rekord létrehozása** — csak foglaltság-/frissítés-számlálók.
* A Szerkesztés menüben **egyetlen, általános** `eMenuEdit::ID_UNDO`
  („Visszavonás") áll, művelet szerinti megnevezés nélkül.
* Az egyetlen **rétegzett** visszavonás a szerkesztő szűrővermének a
  visszavonása (`CFilterStackUI::undoname` = „Visszavonás: `<szűrőnév>`";
  `editpanel/filter_undo` súgója: „Remove the latest fix or edit") — az
  **képenkénti és szűrőnkénti**, a szerkesztőben.
* **A könyvtárnézeti (kötegelt) beillesztés az eredetiben
  visszavonhatatlan.** Az egyetlen menekülőút az „Összes szerkesztés
  visszavonása" (`ID_PICTURE_REVERT`), ami az egész láncot eldobja.

⇒ A #152 réteg **többszintű undo-verme az eredetiben nem létezik**. (Ahogy
a #1475 két nevesített visszavonás-tétele sem — az is tudatos többlet, ld.
`ui-audit-menus.md:64`.)

## A döntés

**1. A #152-es réteg NEM kap saját menüpontot.**

Az eredetiben **egy** parancspár van, azt a felület már kiszolgálja. Egy
külön menüpont olyan parancsot találna ki, ami az eredetiben nincs — ez
sértené a projekt alapszabályát, és a #1475 döntését is.

**2. A réteget NEM töröljük — mert a TARTALMI viselkedése a hűséges.**

A 2. pont fényében a #152 réteg „mindent átviszünk" szemantikája
**egyezik az eredetivel**, a bekötött kötegelt rétegé pedig **nem**. A
törlés éppen a helyes referencia-megvalósítást dobná el.

**3. A #152 többszintű undo-verme NEM kap felületet, és nem is példa.**

Az eredetiben nincs megfelelője. Ha a réteg egyszer a felület mögé kerül, a
vermet **nem** kell átvinni.

**4. A valódi hiba a KÖTEGELT rétegben van — külön jegyet kíván.**

A ma élő „Az összes effektus beillesztése" **elveszíti a vágást** (és a
`redeye`/`retouch` régiókat), miközben az eredeti átviszi őket. Ez a
felhasználónál látható eltérés, és **nem** ennek az ADR-nek a hatóköre: a
javítás a `edit/effect_clipboard.py` szűrési szabályát és a hozzá tartozó
tesztkészletet érinti, ezért önálló jegyben végzendő.

Az illeszkedő végállapot: **egyetlen** menüparancs, amely — az eredeti
kétágú kezelőjéhez hasonlóan — a szerkesztő nyitottsága szerint választ
ágat, és **mindkét** ágon a teljes láncot viszi át.

## Ami nyitva marad — és mi döntené el

1. **Vágott-e ténylegesen a célkép a beillesztés után?** A renderelést nem
   a `filters=`-beli `crop64`, hanem a külön `crop=rect64(...)` kulcs hajtja
   (`docs/specs/filters-decoded.md:14–26`). Hogy a **könyvtárnézeti** ág
   frissíti-e a rekord rect-mezőjét (amiből a `0x0068b320` a `crop=` sort
   írja), nem sikerült kimérni. Az élő korpuszban 763 láncból 761-hez
   tartozik `crop=` kulcs is, a fordított irányban nulla kivétel — ez
   **összefér** azzal, hogy a Picasa mindkettőt írja, de nem bizonyítja.
   *Eldöntené:* referencia-kör a windowsos Picasával a közös NAS-mappán —
   vágott képről másolás, beillesztés vágatlan képre, majd a cél
   `.picasa.ini` szekciójának elolvasása (van-e `crop=`), és ránézés az
   indexképre.
2. **Rétegesen bomlik-e a beillesztett lánc a szerkesztő vermében?** A
   szerkesztő-ág a `0x006b4820`-on ciklusban viszi át a vágólap-vektor
   elemeit, ami **valószínűsíti**, hogy külön verem-tételek lesznek — nem
   bizonyított, és nem a *beillesztés* visszavonása, hanem a *veremé*.
   *Eldöntené:* dekompilátum a `0x006b4820`-ról.

Egyik nyitott kérdés sem érinti a fenti döntéseket: az 1. a **kötegelt**
réteg javításának részletkérdése, a 2. a szerkesztő vermét illeti.
