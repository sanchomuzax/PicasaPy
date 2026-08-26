# Néma vezérlő-tagok: a #1052 huszonhat kérdéses tagjának döntése

*Mérve 2026-08-26 a `docs/1052-nema-tagok` ágon. A #1052 gyűjtőjegy 31
tagot sorolt fel; négy már jegyen volt (#1051, #1002), egy megvizsgálva
nem hiba (`collageFrameCenter`). **Ez a lap a maradék 26-ról dönt.***

## 0. Miért nem elég a lánc-szakadások leltára

A projektben két mérés fut ugyanarra a témára, és **nem ugyanazt mérik** —
ezt előre ki kell mondani, különben a két lista összekeverhető:

| mérés | mit néz | eszköz |
|---|---|---|
| [`lanc-szakadasok-leltar.md`](lanc-szakadasok-leltar.md) | mit **nem ér el a QML** minősített (`<objektum>.<tag>`) alakban — akkor is felveszi, ha Pythonból hívjuk | `scripts/kepesseg_or.py` (CI-őr) |
| **#1052** | mit nem hív **sem a QML, sem a Python** | `eszkozok/nema_slotok.py` (privát agent-repó) |

A #1052 halmaza tehát **szűkebb** kellene, hogy legyen — de a gyakorlatban
nem részhalmaz, mert a két mérés más időpontban, más módszerrel futott.
Ennek két mérhető következménye van:

1. **Négy tag ma már be van kötve**, tehát a leltárban nem is szerepel
   (ld. 2. szakasz). A #1052 listája ennyivel elavult.
2. **Egy tagnál a #1052 tévedett:** a `setSimplified`-et Pythonból
   **hívjuk** (`folder_hierarchy_controller.py:171`, a `toggleSimplified`
   testéből). „Sem QML, sem Python" — ez az egy sor nem állta meg a helyét.

**Megfeleltetés számokban:** a 26-ból **22 szerepel** a leltárban — 14-nek
`MÉRVE`, 5-nek `#1475`, 3-nak `FELVÁLTVA` indoklással —, **4 nem**, mert
azok azóta bekötést kaptak. A leltár 49 tételéből tehát 27 esik ezen a
lapon kívülre.

## 1. A módszer

Minden tagra **kétféle alakú** keresés futott a `src/` egészén (Python +
QML + JS), a definíciós sort kizárva:

```
grep -rn  "<tag>"        src/     # csupasz alak (elkapja a QML-oldali aliast is)
grep -rnE "\.<tag>\b"    src/     # minősített alak
grep -rniE "on<Tag>Changed|\"<tag>\"|'<tag>'"  src/   # QML-jelzés / sztringes hívás
```

A negatív eredményt tehát nem egyetlen keresés adja. Ahol a csupasz alak
talált valamit, az **mindig más tag** volt (`movePhotos`, `expandAll`,
`collapsed`, `setFolderDescriptionOf`, `collageTitleChanged`) — ezeket a
táblában néven nevezem.

**Amit a mérés nem zár ki:** a `getattr`/`QMetaObject.invokeMethod`
alakú, futásidőben összerakott hívásokat. A `src/` alatt egyik sincs
(`grep -rn "invokeMethod\|getattr(.*Controller" src/` → 0 találat a
vizsgált tagokra), de ez a korlát elvi.

## 2. Ami MA MÁR BE VAN KÖTVE — a jegy elavult négy sora

A #1052 2026 nyarán készült; azóta a #1472 (nyomtatás) és a #1473
(arckeresés) mindkét vezérlőnek felületet adott.

| tag | hely | a mai bekötés |
|---|---|---|
| `renderPrintPreviewPdf` | `app/print_controller.py` | `PrintDialog.qml:120` — `printWindow.printCtl.renderPrintPreviewPdf(…)` |
| `isAvailable` | `app/face_scan_controller.py` | `FaceScanDialog.qml:104` |
| `isEmbeddingAvailable` | `app/face_scan_controller.py` | `FaceScanDialog.qml:106` |
| `unnamedAlbum` | `app/face_scan_controller.py` | `FaceScanDialog.qml:115` |

Ezek egyike sincs a lánc-szakadások leltárában — **a két mérés itt egyet
mond**, és a mai kód a helyes forrás.

## 3. A döntések — mind a 26 tag

Jelölés: **HIBA** = a felhasználónak létező funkciónak kellene lennie ·
**SZÁNDÉKOS** = jogos, hogy nincs hivatkozva · **HALOTT** = semmi nem
használja és nem is fogja · **BEKÖTVE** = a jegy óta felületet kapott.

| tag | hely | döntés | bizonyíték | jegy |
|---|---|---|---|---|
| `copyEffects` | `app/effects_controller.py` | **SZÁNDÉKOS** (a #1052 HIBA-verdiktje MEGDŐLT) | ld. 3.1 szakasz | **#1534** (eldöntve) |
| `hasEffectsClipboard` | `app/effects_controller.py` | **SZÁNDÉKOS** | ugyanaz a vágólap, a jelzője | **#1534** |
| `canUndoPasteEffects` | `app/effects_controller.py` | **SZÁNDÉKOS** | ugyanaz, a visszavonás jelzője | **#1534** |
| `undoPasteEffects` | `app/effects_controller.py` | **SZÁNDÉKOS** | ugyanaz, a művelet | **#1534** |
| `canUndoPasteAllEffects` | `app/photo_ops_controller.py` | HIBA | a „Paste All Effects" elvégezhető (`Main.qml:769`), a visszavonása nem | **#1475** |
| `hasCrop` | `app/edit_controller.py` | **HIBA** | ld. 4. szakasz | **új** (A) |
| `clearCrop` | `app/edit_controller.py` | **HIBA** | ld. 4. szakasz | **új** (A) |
| `enhanceActive` | `app/edit_controller.py` | **HALOTT** | ld. 5. szakasz | **új** (B) |
| `autolightActive` | `app/edit_controller.py` | **HALOTT** | ld. 5. szakasz | **új** (B) |
| `autocolorActive` | `app/edit_controller.py` | **HALOTT** | ld. 5. szakasz | **új** (B) |
| `hasRetouch` | `app/edit_controller.py` | SZÁNDÉKOS | a docstring két célja közül a felirat az `undoLabel`-é (#465, `_push_undo("retouch")` a `:1294`-en), a csempe kiemelése pedig a NYITOTT eszközt jelzi (`EditorTabCommonFixes.qml:153` → `panel.retouchActive`), nem a mentett retusálást | — |
| `canRenderEffect` | `app/edit_controller.py` | SZÁNDÉKOS | az „Örökség" fül a `legacyEffects` katalógus `enabled` mezőjét olvassa (`EditorLegacyTab.qml:82`), amit ugyanez a `can_offer_filter_control` tölt (`edit_controller.py:490`) | — |
| `isDeadLegacyEffect` | `app/edit_controller.py` | SZÁNDÉKOS | ugyanaz a katalógus `dead` mezője (`EditorLegacyTab.qml:99`, `edit_controller.py:491`) | — |
| `movePhoto` | `app/fileops_controller.py` | SZÁNDÉKOS | a felület a többes alakot hívja: `FileOpsDialogs.qml:49` → `fileOpsController.movePhotos(paths, dest, policy)` | — |
| `renderPrintPreviewPdf` | `app/print_controller.py` | BEKÖTVE | `PrintDialog.qml:120` | #1472 |
| `expand` | `app/folder_hierarchy_controller.py` | **HALOTT** | ld. 6. szakasz | **új** (C) |
| `collapse` | `app/folder_hierarchy_controller.py` | **HALOTT** | ld. 6. szakasz | **új** (C) |
| `setSimplified` | `app/folder_hierarchy_controller.py` | SZÁNDÉKOS | **a jegy tévedett**: Pythonból hívjuk, `folder_hierarchy_controller.py:171` (`toggleSimplified` → `self.setSimplified(not self._simplified)`), a menü pedig a `toggleSimplified`-et | — |
| `locationOfRow` | `app/geo_controller.py` | SZÁNDÉKOS | ugyanez az adat a `geoMarkers` listában megy át egyben (`geo_controller.py:37`, `PlacesMap.qml:11/46`); a bélyegkép pin-jelvénye a modell `hasGeo` mezőjéből jön (`ThumbDelegate.qml:34`) | — |
| `isAvailable` | `app/face_scan_controller.py` | BEKÖTVE | `FaceScanDialog.qml:104` | #1473 |
| `isEmbeddingAvailable` | `app/face_scan_controller.py` | BEKÖTVE | `FaceScanDialog.qml:106` | #1473 |
| `unnamedAlbum` | `app/face_scan_controller.py` | BEKÖTVE | `FaceScanDialog.qml:115` | #1473 |
| `setFolderDescription` | `app/controller.py` | SZÁNDÉKOS | a felület a mappát is átadó alakot hívja (`FolderPane.qml:1047`, `LightboxFeed.qml:554`), amit ez a slot maga is meghív (`controller.py:645`) | — |
| `wastedPercent` | `app/compact_controller.py` | **HALOTT** | ld. 7. szakasz | **új** (D) |
| `collageTitle` | `app/collage_save.py` | SZÁNDÉKOS | a felhasználó nem nevezi el a kollázst: a fájlnév a FORRÁSMAPPÁBÓL jön (`kollazs-eletciklus.md` 8.6, megerősítve exportált `.cxf`-fel); a `PISZKOZAT -- <név>` cím-előtagot a spec kifejezetten **tiltja** (ugyanott, 260. sor) | — |
| `collageSeed` | `app/create_controller.py` | SZÁNDÉKOS | a magot a `shuffleCollage` lépteti (`create_controller.py:249`), a hatása a vásznon látszik; a felület a `shufflePictures`/`shuffleCollage` gombokat köti (`CollageRandomRow.qml:72`, `CreateDialogs.qml:124`) | — |

**Összesítés:** 7 HIBA (ebből **5 a meglévő #1475-ön**, 2 új jegyet kér) ·
9 SZÁNDÉKOS · 6 HALOTT · 4 MA MÁR BEKÖTVE. Új jegy-javaslat: **4**.

A kilenc SZÁNDÉKOS eset **kódkommentet kapott** a tag fölé, hogy a
következő olvasó ne tegye fel újra a kérdést.

### 3.1 A négy effektus-vágólap tag verdiktje MEGVÁLTOZOTT (#1534, 2026-08-26)

A #1052 ezt a négy tagot **HIBA**-ként könyvelte el: „két párhuzamos
effekt-vágólap van, a menü a kötegelt úton megy, ez a kép-specifikus ág UI
nélkül áll". A #1534 visszafejtette az eredeti kezelőket — és **két
meglepetést** hozott.

**1. Nincs külön menüpont, amit ez a réteg kiszolgálhatna.**

A menüépítő kódjából kinyert TELJES parancstérképben
(`picasa-menu-parancsok.csv`, proveniencia: `picasa-menu-leltar.md` 7.)
**pontosan két** effektus-vágólap parancs van, mindkettő a **Szerkesztés**
menüben (`ID_EDIT_COPYALLEFFECTS` / `ID_EDIT_PASTEALLEFFECTS`); a Kép
menüben (`eMenuPicture`, 19 parancs) egy sincs.

Az eredeti ráadásul **egy** parancsot ad **kétágú** kezelővel: a
diszpécser (`0x005cb990`) ugyanazt a kezelőpárt hívja, és a kezelő
megnézi, látszik-e az `"editpanel/preview"` — ha igen, a **nyitott
egyetlen** képre dolgozik az élő szűrővermen, ha nem, a **kijelölésre**
(másolásnál pontosan egy kép, `IDS_SELECT_ONE_ONLY`). Vagyis nem két
funkció, hanem egy parancs két ága. ⇒ A négy tagnak **nem hiba**, hogy a
QML nem hivatkozza; saját menüpontot adni nekik **hiba lenne**.

**2. A réteg tartalmi viselkedése viszont a HŰSÉGES — a bekötötté nem.**

A másoló (`0x005fecd0`) és a beillesztő (`0x005fefc0`) a `filters` láncot
**egészben** mozgatja; a teljes hívási úton **nincs egyetlen szűrő-névre
vonatkozó összehasonlítás sem**. Függetlenül ellenőrizve a bináris-indexből:
a `"filters"` sztringnek 33 kódhivatkozása van (köztük a getter/setter
`0x006af3e0`/`0x006af650`), a **`crop64` sztringnek NULLA** — a program
sehol nem hasonlít össze semmit ezzel a névvel.

⇒ **Az eredeti beillesztés átviszi a vágást.** A bekötött kötegelt réteg
(`photo_ops_controller.py:633/648/724`) viszont **kiszűri** — a
`filterdesc.xml` `mode="history"` oszlopából következtetve, holott a
másolás kezelője ezt az attribútumot soha nem olvassa. Ez a kötegelt réteg
**hibája**, önálló jegyet kíván; a #152-es réteg addig a helyes viselkedés
egyetlen megvalósítása, ezért **nem törölhető**.

⚠️ A `_effects_undo_stack` többszintűsége viszont az eredetiben **nem
létezik**: a könyvtárnézeti beillesztés ott visszavonhatatlan (a binárisban
nulla olyan felirat van, amiben az „undo" és a „paste" együtt szerepel).

A döntés, a mérés és a nyitott kérdések:
**`docs/decisions/effektus-vagolap-ket-reteg.md` (ADR-007)**.

## 4. (A) A vágás „Alaphelyzet" gombja nem szünteti meg a mentett vágást

Ez a lap egyetlen **új, felhasználót érintő** lelete.

- A vágás-panelen **van** „Alaphelyzet" gomb: `EditorCropPanel.qml:320`
  (`cropResetButton`), az eredetiből átvéve (`ui-audit-editor.md` 858:
  „**Alaphelyzet** — önálló, teljes szélességű gomb, középen").
- A gomb `panel.cropResetRequested()`-et küld, amit a néző így kezel:
  `PhotoViewer.qml:771` → **`cropOverlay.resetSelection()`**. Ez csak a
  húzott kijelölést nullázza (`CropOverlay.qml:36–39`).
- Utána az „Alkalmaz" **nem csinál semmit**: `PhotoViewer.qml:237–240`
  kijelölés nélkül azonnal visszatér, és csak becsukja az eszközt.
- Közben az előnézet a **vágatlan** képet mutatja (`enterCropTool`,
  `edit_controller.py:1127` — `self._session.clear_crop()`), tehát a
  felület azt ígéri, hogy nincs vágás. Alkalmazás után mégis marad.

⚠️ **Amit nem tudok bizonyítani:** hogy az eredeti Picasa
„Alaphelyzet"-je a MENTETT vágást szünteti-e meg, vagy csak a kijelölést.
A `docs/specs/vagas-eszkoz-allapot.md` 190. sora csak felsorolja a
gombot, a szemantikáját nem írja le. A testvér-vezérlő viszont mellette
szól: a vörösszem-panel `redeyediscard` gombja az `ui-audit-editor.md`
975. sora szerint „**Reset** — Undo Red-Eye changes", tehát ott a Reset a
ténylegesen alkalmazott korrekciót veszi le.

**Ettől függetlenül a mai állapot önmagában is ellentmondásos**: az
előnézet vágatlan képet mutat, az Alkalmaz mégis meghagyja a vágást.

A hiányzó két hívás pontosan a két néma tag: `clearCrop`
(`edit_controller.py:1060`) és `hasCrop` (`:845`, a gomb tiltásához).

**Enyhítő körülmény:** a vágás nem vész el véglegesen — a `crop64` a
láncban ül (`session.py:100–115`), az undo-verem pedig a mentett láncból
épül újra (`_seed_undo_from_chain`, `edit_controller.py:1848`), tehát a
Visszavonás gombbal **visszabontható** — de csak úgy, hogy a fölötte lévő
összes réteg is lejön. Ezért P3, nem P2.

## 5. (B) A négy „gomb aktív állapota" property — a jegy feltevése MEGDŐLT

A #1052 azt vetette fel, hogy az eredeti Picasa a Fényerő/Színek/
Retusálás gombokat **kiemelve** mutatja, ha az adott korrekció él, és ha
ezt nálunk senki nem olvassa, a felhasználó nem látja, mi van
bekapcsolva. **Ez ebben a formában nem áll.**

A **#116** (lezárva) kifejezetten az ellenkezőjét mondta ki, és a kódban
végre is hajtotta:

> „A gomb **letiltott (szürke)**, ha ugyanez a szűrő a lánc **utolsó**
> eleme. […] Kontroller-oldalon `*Active` helyett a QML-nek »nyomható-e«
> jelentésű property kell (pl. `autolightEnabled`)."

Ezt a kód is kimondja, `EditorTabCommonFixes.qml:116`:

> „egygombos javítások (#116): nincs »benyomva« állapot — a gomb tiltott
> (halvány), amíg ugyanez a szűrő a lánc utolsó eleme"

Az élő lánc tehát: `edit_controller.py:783/787/791` (`enhanceEnabled`,
`autolightEnabled`, `autocolorEnabled`) → `PhotoViewer.qml:291–293` →
`EditorPanel.qml:224–226` → `EditorTabCommonFixes.qml:123/133/143`.

**Verdikt tagonként:**

| tag | verdikt |
|---|---|
| `enhanceActive`, `autolightActive`, `autocolorActive` | **HALOTT** — a #116 leváltotta őket, de a törlésük elmaradt. Nulla hivatkozás a `src/` alatt, mindkét keresési alakkal. A jelentésük (»szerepel-e a láncban«) amúgy is elérhető: `effectChainCounts` (`edit_controller.py:507`), ami **be van kötve**. |
| `hasRetouch` | **SZÁNDÉKOS**, nem ugyanaz az eset — ld. a 3. szakasz sorát. |

⚠️ **A leltár indoklása HIBÁS VOLT, ezért javítottam.** A
`kepesseg_or_baseline.txt` mind a háromra azt írta: „MÉRVE — ugyanaz a
minta: a panel a saját állapotát tartja". Ez a `redeyeActive`-ra igaz
(`EditorPanel.qml:132` valóban tart saját `property bool redeyeActive`-ot),
a másik háromra **nem**: a panelben nincs `enhanceActive`/
`autolightActive`/`autocolorActive` — egyetlen előfordulásuk sincs a
QML-fában. Az indoklás mostantól `FELVÁLTVA`, a valódi párt megnevezve.
Hamis szerződést adni rosszabb, mint nem adni.

## 6. (C) `expand` / `collapse` — párhuzamos, hívó nélküli ág

A mappafa nyitogatásának **négy** kész útja van a vezérlőn; a felület
hármat használ:

| tag | hívó |
|---|---|
| `toggle(path)` | `FolderHierarchyView.qml:52/120/162/165` (háromszög, dupla kattintás) |
| `expandAll()` | `FolderHierarchyView.qml:58/181` (helyi menü) |
| `collapseAll()` | `FolderHierarchyView.qml:63/186` (helyi menü) |
| `revealPath(path)` | `FolderPane.qml:282/294` |
| **`expand(path)` / `collapse(path)`** | **nincs** |

Nem hiánypótló ág: az egy ág nyitása/csukása a `toggle`-lel elvégezhető, a
`toggle` viszont **nem is hívja** őket, hanem maga írja a `_expanded`
halmazt (`folder_hierarchy_controller.py:183–190`) — ez duplikáció.

Billentyűs igény sincs mögötte: a `picasa-gyorsbillentyuk.md` a bal/jobb
nyilat a **képváltásra** köti (208–219. sor), a mappafa ág-nyitogatására
nincs átképezhető rekesz.

## 7. (D) `wastedPercent` — az eredeti dialógus nem mutatja

- A tömörítés-dialógus **hű másolat**: `compacting.fen` = `appicon` +
  magyarázó `label` + `label name="status"` — **százalék nincs benne**
  (`picasa-fen-dialogs.md` 326–329).
- A döntést („érdemes-e egyáltalán") az `isWorthCompacting()` hozza meg,
  és **az be van kötve**: `CompactDatabaseDialog.qml:45`.
- A `wastedPercent`-nek **nulla** hivatkozása van: se QML, se Python, és
  **teszt sincs rá** (a 26 közül ez az egyetlen ilyen).

A leltár indoklása („a tömörítés-párbeszéd nem mutatja, mennyi hely
nyerhető") tényszerűen igaz, de **hiánynak sugallja azt, ami az
eredetiben sincs**.

## 8. Amit NEM vizsgáltam — és miért

| terület | miért maradt ki |
|---|---|
| A #1052 további 5 tagja (`restoreCollageDraft`, `refreshCollageDraft`, `discardCollageDraft`, `setCollageSavedPath`, `collageFrameCenter`) | a jegy már eldöntötte őket (#1051, #1002, illetve „nem hiba") — a feladat kifejezetten a maradék 26 |
| A lánc-szakadások leltárának másik **27** tétele (pl. `folderDateText`, `setExportMovieFull`, `revision`, `hasFinetune`, `startupStatus.busy`) | nincsenek a #1052 listáján: ezeket **Pythonból hívjuk**, vagy a leltár már elhatárolta őket. Külön kör kellene hozzájuk |
| A **jelzés-irány** (kimenő `Signal`, amit senki nem fogad) | azt a `scripts/check_dead_signals.py` és a privát `nema_jelzesek.py` méri; ez a lap a bejövő irányról szól |
| Az eredeti Picasa „Alaphelyzet"-jének natív szemantikája | binárisvisszafejtést kívánna (`0x…` kezelő a `cropreset` gombhoz); a 4. szakasz nyitott kérdésként rögzíti, és a javasolt (A) jegy első pontja |
| Futásidőben, sztringből összerakott hívások (`invokeMethod`, `getattr`) | a `src/` alatt nincs ilyen a vizsgált tagokra, de a keresés elvi korlátja |
| A tesztek által hívott, de terméken kívüli tagok „lefedettsége" | a kérdés a felületi elérhetőség volt, nem a tesztlefedettség |

## 9. Nyitott kérdések mérlege

| kérdés | állapot |
|---|---|
| Mind a 26 taghoz van-e döntés? | **LEZÁRVA** — 3. szakasz, 7 + 9 + 6 + 4 = 26 |
| Igaz-e a „gomb aktív állapota" feltevés? | **LEZÁRVA** — megdőlt, a #116 az ellenkezőjét rendelte el (5.) |
| Hány tag maradt ki a lánc-szakadások leltárából? | **LEZÁRVA** — négy, mert azóta bekötést kapott (2.) |
| Mit csinál az eredeti „Alaphelyzet" gomb? | **BLOKKOLT** — binárisvisszafejtést kíván; a javasolt (A) jegy első pontja (4.) |
| Törölhetők-e a HALOTT tagok? | **HATÓKÖRÖN KÍVÜL** — a törlésről jegy dönt, ez a lap nem töröl (a feladat kikötése) |

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```
