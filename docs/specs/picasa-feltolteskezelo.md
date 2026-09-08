# A Feltöltéskezelő és a megszűnt online felületelemek

*Forrás: `movieeditpanel.tre:20` (`movieeditpanel/export_youtube`).*

*2026-09-06. A #2529 első köre. A UI-lefedettségi mérés 31 „feltáratlan"
eleméből ez a lap **15-öt** zár le: **14-et** `nem-cel`-re (mind a
**megszűnt Picasa Web Albums** szolgáltatáshoz tartozik), egyet pedig
`lekutatva`-ra (`movieeditpanel/export_youtube`, 5. szakasz). A viselkedésüket akkor is kimértük, ha nem
építjük meg: enélkül nem lehet kimondani, hogy valóban online funkció.*

> ⛳ **Miért van ez a lap, ha úgysem építjük meg?** Mert a
> `nem-cel` besorolás **állítás**, és állítást csak bizonyítékkal szabad
> tenni. A lap a bizonyítékot rögzíti; a döntést nem ez a lap hozta, hanem
> a tulajdonos — `src/picasapy/help/features/meg-nem-erheto-el.md`,
> „Megszűnt szolgáltatások — ezek nem is fognak elkészülni".

## 1. A Feltöltéskezelő — belépési pontok

| honnan | bizonyíték |
|---|---|
| **Eszközök ▸ „&Feltöltéskezelő…"** | `eMenuTools::ID_TOOLS_UPLOADMGR` (`stringres-en-hu.tsv:2731`), a menüépítő `0x00559150` |
| a **tevékenység-gomb** a felület jobb szélén | `activity/activitybutton` a `0x007d3f90`-ben (és `0x00572820`, `0x005de8e0`) |

Az osztály **`CUploadManagerDialog`** (RTTI-vtábla `0x00cb9054`), a mögötte
álló motor **`CUploadManager`** (`0x00ca7380`, külön `ResampleThread`
alosztállyal: `0x00ca7418`). A párbeszéd felirattára `i18n\uploadmgr.xml`
(`0x007d2130`), a címe `Upload Manager` / **„Feltöltéskezelő"**
(`uploadmgr::title`).

## 2. MIT CSINÁL — a parancs-elosztó hat ága

Az elosztó a **`0x007d2400`** (1509 b). Minden ág az elemnevet hasonlítja
(`0x009c2fc0`), és a **feltöltés-motoron** (`[this+0x26c]`) dolgozik.

| elem | felirat (EN / HU) | mit tesz | cím |
|---|---|---|---|
| `uploadmgr/pause` | „Pause" / **„Felfüggesztés"** | `[motor+0x102] := 1`, majd a `[[motor+0x50]+0x20]` virtuális hívás | `0x007d2820`–`0x007d2836` |
| `uploadmgr/resume` | „Resume" / **„Folytatás"** | `0x00685c20(motor)` | `0x007d286a`–`0x007d2870` |
| `uploadmgr/cleanup` | „Clear Completed" / **„A feltöltöttek törlése a listából"** | végigmegy a `[motor+0x274]` sorlistán, és amelyik elem **állapota 7** (`cmp dword ptr [edi+ecx+0x10], 7`), azt kiveszi | `0x007d28ab`–`0x007d2914` |
| `uploadmgr/throttlechk` | — (jelölőnégyzet) | `0x00917ce0(állapot)` ⇒ **registry-írás**, ld. 3. szakasz | `0x007d298d`–`0x007d29b5` |
| `uploadmgr/hide` | „Hide" / **„Elrejtés"** | `[[this+0x258]+0xc]()` — a párbeszéd elrejtése | `0x007d294e`–`0x007d2959` |
| `uploadmgr/minibutton` | — | `0x007d2d80`: **`"%s:%d"`** alakú nevet gyárt (`0x00cb8e2c`), és azzal keres elemet a felületi fában (`0x00c07db2`); ha nincs, a puszta `uploadmgr/minibutton` névre esik vissza (`0x00cb8e34`) | `0x007d2d80` |

Az elosztó ismeretlen névre **`0xF4241`**-gyel tér vissza (`0x007d29dc`),
a kezelt ágak `0xF4240`-nel — ez a Picasa általános „kezeltem" kódja.

### `uploadmgr/itemlist` — a sor MAGA

Az `itemlist` nem gomb, hanem a **feltöltési sor listaeleme**: a
`0x007d2130` panelépítő hozza létre, a soronkénti műveleteket pedig a
`0x007d2e60` (2282 b) osztja szét, generált elemnevekkel:

```
upmgrlist-view            upmgrlist-cancel      upmgrlist-retry
upmgrlist-clear           upmgrlist-showerr     upmgrlist-showerr/%d
upmgrlist-showerr-textnode/%d
```

⇒ soronként **megtekintés · megszakítás · újrapróbálás · törlés ·
hibarészletek**. A megerősítő párbeszédek:
`uploadmgr::confirmremove` („Biztosan eltávolítja ezt a feltöltést?"),
folyamatban lévő feltöltésnél `uploadmgr::confirmabort`
(„Ezzel a művelettel megszakítja a jelenleg folyó feltöltést…").

## 3. AZ EGYETLEN TARTÓS ÁLLAPOT: `Preferences\AutoBandwidthThrottle`

A hat vezérlő közül **csak a `throttlechk` ír tartós tárolóba.**

```
0x00917ceb  push 0xcd1a88            ; "AutoBandwidthThrottle"
0x00917cf0  push 0xc7eafc            ; "Preferences"
0x00917d00  mov  dword ptr [esp+0x14], 0   ; ALAPÉRTÉK = 0
0x00917d08  call 0x00407a20          ; beállítás-objektum
0x00917d1e  call 0x00401900          ; ÍRÁS
0x00917d25  call 0x004019b0          ; azonnali visszaolvasás
0x00917d2e  mov  byte ptr [esi+0xd4], al   ; a globális állapotba
```

| | mérve |
|---|---|
| tároló | `HKEY_CURRENT_USER\SOFTWARE\Google\Picasa\Picasa2\Preferences\AutoBandwidthThrottle` |
| **alapérték** | **0 (kikapcsolva)** — `0x00917d00` |
| mikor íródik | **azonnal**, a jelölőnégyzet átbillentésekor |
| memóriabeli állapot | a globális objektum (`0x00d676dc`) `+0xd4` bájtja |

A többi öt vezérlő **futásidejű** állapotot állít (a motor `+0x102`
felfüggesztés-jelzője, illetve a sorlista) — kilépés után nem marad
nyoma.

## 4. A HU feliratkészlet — teljes, 30 tétel

A `stringres-en-hu.tsv` `uploadmgr::` névtere hiánytalanul le van
fordítva (`:3304`–`:3333`), például:

| kulcs | EN | HU |
|---|---|---|
| `uploadmgr::format::running` | „Uploading %1$d of %2$d" | „%2$d / %1$d feltöltése" |
| `uploadmgr::format::numqueued_plural` | „%d items queued" | „%d elem a sorban" |
| `uploadmgr::format::secondstext` | „Approximate time remaining: %s" | „Megközelítőleg hátralévő idő: %s" |
| `uploadmgr::format::retrywait` | „Retry in %s" | „Próbálja újra itt:%s" |
| `uploadmgr::Paused` | „Paused" | „Felfüggesztve" |
| `uploadmgr::completed` | „Completed" | „Kész" |

⇒ **a fordítás megvan**; ha valaha mégis kellene egy helyi feltöltési sor
(pl. exportáláshoz), a feliratok készen állnak.

## 5. A tizennégy elem, amit ez a lap `nem-cel`-re tesz

Mindegyik a **Picasa Web Albums** feltöltéshez/megosztáshoz tartozik, amit
a Google 2016-ban leállított.

| panel | elem | felirat (EN / HU) |
|---|---|---|
| `uploadmgr` | `pause` | „Pause" / „Felfüggesztés" |
| `uploadmgr` | `resume` | „Resume" / „Folytatás" |
| `uploadmgr` | `cleanup` | „Clear Completed" / „A feltöltöttek törlése a listából" |
| `uploadmgr` | `itemlist` | — (a feltöltési sor) |
| `uploadmgr` | `minibutton` | — (kicsinyített nézet gombja) |
| `uploadmgr` | `throttlechk` | — (sávszélesség-korlát jelölőnégyzet) |
| `headerpanel` | `sync_label` | „Sync to Web" / „Szinkronizálás az internettel" |
| `headerpanel` | `sync_options` | „Online options" |
| `headerpanel` | `view_online` | „View on Web" / „Megtekintés az interneten" |
| `headerpanel` | `websync1` | „Stop syncing changes to the web" |
| `acquirepanel` | `add_groups_button` | „Add people to share albums with" |
| `acquirepanel` | `selected_groups_label` | „Nobody" / „Senki" |
| `acquirepanel` | `share_with_label` | „Share with:" / „Megosztás a következővel:" |
| `acquirepanel` | `upload_label` | „Upload" / „Feltöltés" |

**Az `acquirepanel` négyese** az importáló panel megosztás-blokkja
(`acquirepanel/share_container`, `acquirepanel/groups_container`,
`acquirepanel/upload_checkbox` —
`0x00518840`, `0x005154f0`); az `add_groups_button` az importáló
parancs-elosztójában (`0x0051f070`) ül, a `sync_options_button` mellett.

### A tizenötödik: `movieeditpanel/export_youtube` — feltárva, de a DÖNTÉS nyitva

*Forrás: `movieeditpanel.tre:20` (`movieeditpanel/export_youtube`).*

⛔ **NEM tettem `nem-cel`-re** a `movieeditpanel/export_youtube`-ot: a
felirata „Upload to YouTube" / **„Feltöltés a YouTube webhelyre"**
(`referencia/ui-leltar.csv`), tehát **tudjuk, mit csinál** — a klipvágó
panel a kész klipet a YouTube-ra tölti fel. A besorolása ezért
**`lekutatva`** (fel van tárva, nem építettük meg), nem „feltáratlan".

Amit NEM dönthet el ez a lap: **megépítjük-e valaha.** A YouTube ma is
létezik, a tulajdonosi „megszűnt szolgáltatások" lista viszont a Picasa
**saját** Google-szolgáltatásait sorolja, nem minden feltöltést. Ez
**termékdöntés**, nem kutatás — a #2529-en marad, és ha a válasz „nem",
akkor `nem-cel`-re kell tenni, ugyanígy dokumentálva.

⛳ **Módszertani mellékleletként ezt is ki kell mondani:** az elem azért
került át a „feltáratlan" oszlopból, mert ez a lap **teljes néven** említi
egy horgonyzott szakaszban — pontosan az a mechanizmus, amit a #2504
figyelmeztetője mér. Itt szándékos: az elem tényleg fel van tárva. De a
mérőnek nincs módja megkülönböztetni a szándékos említést a véletlentől,
ezért a besorolást a szöveg **állítja**, nem bizonyítja.

## 6. MIT ADUNK MA — mérve

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| Eszközök ▸ Feltöltéskezelő… | működő párbeszéd | a menütétel megvan, **`retired: true`** (`app/qml/PicasaPy/PicasaMenuBar.qml:1596`, #638) | — |
| a funkció | Web Albums feltöltési sor | **nincs, és nem is lesz** — `help/features/meg-nem-erheto-el.md` | — |
| a HU feliratok | 30 kulcs | a `stringres` megvan, a mi `.ts`-ünkbe nem került át | — (nem kell) |
| `AutoBandwidthThrottle` | registry-kulcs, alap 0 | nincs — nincs mit korlátozni | — |

⇒ **A fejlesztő holnap ettől semmit nem csinál másképp.** Ennek a lapnak a
haszna a mérőn látszik: 14 elem kikerül a „feltáratlan" oszlopból, tehát a
kutatói körök nem mennek neki még egyszer.

## 7. Bizonyítottsági fok

**Megerősített** minden cím és felirat (bináris + `stringres-en-hu.tsv`).
**Megerősített** a `nem-cel` besorolás is, de nem bináris alapon: a
tulajdonosi döntés írott helye a `meg-nem-erheto-el.md` és a `#638`.

## 8. Nyitott kérdések mérlege

**0 nyílt · 15 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva"**
— tizennégy `nem-cel`, egy (`export_youtube`) `lekutatva`. A #2529 maradék
**16** eleme tételes listával a jegyen marad; a `export_youtube`
**termékdöntése** is ott, külön pontként.

**A mérés a javítás után** (`ui-lefedettseg.md`, 2026-09-06):
feltáratlan **31 → 16**, nem cél **77 → 91**, lekutatva **273 → 274**,
lefedettség **41,2% → 42,1%**.
