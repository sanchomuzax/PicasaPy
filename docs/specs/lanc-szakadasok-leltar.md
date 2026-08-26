# Lánc-szakadások leltára — ahol a háttér kész, de a felület nem éri el

*A mérést a **`scripts/kepesseg_or.py`** végzi (#1476), a CI `lint` jobjában is. Az alábbi 4. szakasz generált — a kézi pillanatkép ideje lejárt.*

A **#1454** (a `Nézet ▸ Mappanézet` félreértése) mellett kiderült, hogy a
mérés a lánc **két végét** nézte, a közepét nem: a vezérlő kész volt, a
menü hiányzott, és közben egy beégetett érték is elvágta az utat. Ez a lap
azt méri fel, **hol van még ilyen** — rendszeresen, nem szemre.

## A módszer és a korlátja

Minden `@Property` és `@Slot` tagra, ami regisztrált vezérlőn ül,
megnéztem, hivatkozik-e rá a QML. Ahol nem, ott megszámoltam, hívja-e
**Python** vagy csak **teszt**.

⚠️ **A puszta `.tagnév` keresés FÉLREVEZET**, ha két vezérlőn ugyanaz a
tagnév. Mérve **négy** ilyen név van:

| tagnév | gazdák |
|---|---|
| `cancelScan` | `dedup_controller.py`, `face_scan_controller.py` |
| `revision` | `edit_controller.py`, `models.py` |
| `statusText` | `controller.py`, `startup_status.py` |
| `toggleStar` | `import_source_controller.py`, `photo_ops_controller.py` |

**A saját mérésem is beleesett:** a `faceScanController.cancelScan`-t
élőnek látta, mert a `dedupController.cancelScan` hívásait számolta oda.
Minősített kereséssel (`<objektum>.<tag>`) derült ki, hogy **nincs
bekötve**. Aki ezt a leltárt frissíti, **objektumnévvel együtt keressen.**

## 1. Amit a mérés NEM talált

**Nincs holt kontextus-objektum.** Mind a 18 regisztrált QObject-re
(`application.py`; a 19. regisztráció, az `appVersion`, sztring)
hivatkozik a QML. A szakadás mindig **tagszinten** van.

## 2. Négy megerősített lelet — mind önállóan megvalósítható

| # | terület | a háttér | a felület | jegy |
|---|---|---|---|---|
| A | **Nyomtatás** | `print_controller.py`, **213 sor**, 2 tesztfájl | ~~**soha nem példányosul** a termékkódban, nincs `setContextProperty`, **0** QML-hivatkozás; a `Print…` (Ctrl+P) és `Print Thumbnails…` menüpont `placeholder`~~ — **BEKÖTVE (#1472)**: `PrintDialog.qml`, élő `Fájl ▸ Nyomtatás…`, élő Ctrl+P, és a képtálca gombja. A `Print Thumbnails…` SZÁNDÉKOSAN maradt helyfoglaló: az kontaktlap (több kép egy oldalon), amihez nincs motor | #1472 |
| B | **Arcfelismerés indítása** | `scanForFaces`, `cancelScan`, `computeEmbeddings`, `cancelEmbedding`, `isAvailable`, `isEmbeddingAvailable`, `unnamedAlbum` | egyik sincs bekötve — közben a **névadó felület él**, és a `scanPercent` **haladást jelenít meg** egy indíthatatlan keresésről | #1473 |
| C | **E-mail küldés** | `prepareAttachments`, `sendRows` | a QML az `emailController`-t **csak** a beállítás-fül kliensválasztójához köti (`OptionsTabEmail.qml`) | #1474 |
| D | **Visszavonás UI nélkül** | `undoPasteAllEffects`, `canUndoPasteAllEffects`, `canUndoBatchEdit` | nincs gomb; a `Main.qml:754` **ki is mondja**: „csak a vezérlőn elérhető, UI-gomb nélkül". A hivatkozott **#426 és #152 LEZÁRVA** | #1475 |

## 3. Elhatárolások — ezeket NE vegye fel senki hibaként

| tag | miért nem hiba |
|---|---|
| `library_controller.removeWatchedFolder` | a **#1249** felváltotta a szélesebb `removeFolder`-rel; a QML azt hívja |
| `fileops_controller.movePhoto` | egyes alak; a QML a `movePhotos` többes alakot használja |
| `controller.statusText` | **él**, aliason át: `tray.ctl.statusText` (`TrayBar.qml:117`) |
| `controller.setShowHidden` | a menü a `toggleShowHidden`-t hívja — szándékos |
| `effects_controller` tagjai | **nem árva modul**: az `EffectsClipboardMixin` a `controller.py:47`-en át be van építve. A **kép-specifikus** vágólap (#152) áll UI nélkül, miközben a menü „Copy/Paste All Effects" a **kötegelt** úton megy (`photo_ops_controller.py:545/560`). Ez **döntést kíván**, nem hibajavítást — ld. #1475 |

## 4. A teljes mért lista — GENERÁLT

A táblát a `python scripts/kepesseg_or.py --leltar --ir` írja, az
indoklásokat a `scripts/kepesseg_or_baseline.txt` adja. Kézzel ne
szerkeszd: a `tests/tools/test_kepesseg_or_1476.py` összeveti a kettőt.

⚠️ A 2026-08-25-i **kézi** mérés 52 tagot talált; az őr ugyanezen a fán
**56**-ot. A különbség nem a fa változása, hanem a minősített keresés: a
kézi mérés nem látta az `editController.revision`-t (a `photos.revision`
kötések elfedték), a `faceScanController.cancelScan`-t (a `dedupController`
azonos nevű tagja fedte el), és nem nézte a `startup_status.py`-t sem.

<!-- KEPESSEG_OR:KEZDET -->

*Ezt a blokkot a `python scripts/kepesseg_or.py --leltar --ir` írja.*
*Kézzel ne szerkeszd: a `tests/tools/test_kepesseg_or_1476.py` őrzi.*

- vizsgált Python-fájl: **83**
- vizsgált QML/JS-fájl: **141**
- regisztrált kontextus-objektum: **19** (+1 nem QObject)
- feloldott alias: **11**
- kontextuson elérhető `@Slot`/`@Property` tag: **499**
- ebből QML-ből NEM elérhető: **56**

| kontextus-objektum | tag | fajta | hely | indoklás |
|---|---|---|---|---|
| `compactController` | `wastedPercent` | Property | `app/compact_controller.py:56` | MÉRVE — a tömörítés-párbeszéd nem mutatja, mennyi hely nyerhető |
| `controller` | `setDarkTheme` | Slot | `app/appearance_controller.py:61` | FELVÁLTVA — a menü a toggleDarkTheme-et hívja (PicasaMenuBar.qml) |
| `controller` | `canUndoBatchEdit` | Property | `app/batch_effect_controller.py:158` | #1475 — a kötegelt szerkesztés visszavonása gomb nélkül áll |
| `controller` | `undoBatchEdit` | Slot | `app/batch_effect_controller.py:388` | #1475 — ugyanaz, a művelet maga |
| `controller` | `collageFrameCenter` | Property | `app/collage_controller.py:335` | MÉRVE — kollázs-keret középpont; a vászon nem köti |
| `controller` | `collageTitle` | Property | `app/collage_save.py:114` | MÉRVE — a kollázs címe a felületen nem jelenik meg |
| `controller` | `setCollageTitle` | Slot | `app/collage_save.py:136` | BELSŐ — a kollázs-vezérlő állítja (collage_controller.py:437, collage_save.py:918) |
| `controller` | `setCollageSavedPath` | Slot | `app/collage_save.py:153` | MÉRVE — a mentett kollázs útja bekötetlen |
| `controller` | `folderDateText` | Property | `app/controller.py:284` | MÉRVE — a mappa dátumfelirata bekötetlen (párja sincs …Of alakban) |
| `controller` | `folderDescription` | Property | `app/controller.py:289` | FELVÁLTVA — a felület a mappánkénti folderDescriptionOf(path) alakot hívja |
| `controller` | `setShowHidden` | Slot | `app/controller.py:489` | FELVÁLTVA — a menü a toggleShowHidden-t hívja (PicasaMenuBar.qml) |
| `controller` | `restoreSession` | Slot | `app/controller.py:501` | BELSŐ — a controller.py:876 és a library_controller.py:346 hívja induláskor |
| `controller` | `setFolderDescription` | Slot | `app/controller.py:632` | FELVÁLTVA — a felület a setFolderDescriptionOf(path, …) alakot hívja |
| `controller` | `collageSeed` | Property | `app/create_controller.py:253` | MÉRVE — a véletlen elrendezés magja bekötetlen |
| `controller` | `hasEffectsClipboard` | Property | `app/effects_controller.py:38` | #1475 — a kép-specifikus effekt-vágólap (#152) UI nélkül áll |
| `controller` | `canUndoPasteEffects` | Property | `app/effects_controller.py:45` | #1475 — ugyanannak a vágólapnak a visszavonás-jelzője |
| `controller` | `copyEffects` | Slot | `app/effects_controller.py:50` | #1475 — a menü a KÖTEGELT úton megy (photo_ops_controller), ez a kép-specifikus ág |
| `controller` | `pasteEffects` | Slot | `app/effects_controller.py:65` | #1475 — ugyanaz, a beillesztés |
| `controller` | `undoPasteEffects` | Slot | `app/effects_controller.py:141` | #1475 — ugyanaz, a visszavonás |
| `controller` | `exportMovieFull` | Slot | `app/export_controller.py:144` | BELSŐ — a beállítást az export_controller.py:371 olvassa vissza |
| `controller` | `setExportMovieFull` | Slot | `app/export_controller.py:154` | MÉRVE — a beállítás írása bekötetlen; a párja BELSŐ |
| `controller` | `locationOfRow` | Slot | `app/geo_controller.py:129` | MÉRVE — a sor helyadata bekötetlen |
| `controller` | `removeWatchedFolder` | Slot | `app/library_controller.py:682` | FELVÁLTVA — a #1249 óta a bővebb removeFolder megy a QML-ből |
| `controller` | `faceDetectionEnabledFor` | Slot | `app/library_controller.py:721` | MÉRVE — a QML SAJÁT tükrét számolja (FolderStatePanel.qml:40, FolderManagerDialog.qml:198) |
| `controller` | `canUndoPasteAllEffects` | Property | `app/photo_ops_controller.py:540` | #1475 — a Paste All Effects visszavonása gomb nélkül áll |
| `controller` | `undoPasteAllEffects` | Slot | `app/photo_ops_controller.py:636` | #1475 — ugyanaz, a művelet maga |
| `editController` | `revision` | Property | `app/edit_controller.py:426` | MÉRVE — a QML a photos.revision-t köti; ez a szerkesztő SAJÁT változásszáma |
| `editController` | `redeyeActive` | Property | `app/edit_controller.py:530` | MÉRVE — az EditorPanel.qml:132 SAJÁT `property bool redeyeActive`-ot tart |
| `editController` | `enhanceActive` | Property | `app/edit_controller.py:534` | MÉRVE — ugyanaz a minta: a panel a saját állapotát tartja |
| `editController` | `autolightActive` | Property | `app/edit_controller.py:538` | MÉRVE — ugyanaz a minta |
| `editController` | `autocolorActive` | Property | `app/edit_controller.py:542` | MÉRVE — ugyanaz a minta |
| `editController` | `hasRetouch` | Property | `app/edit_controller.py:548` | MÉRVE — a retusálás megléte bekötetlen |
| `editController` | `hasFinetune` | Property | `app/edit_controller.py:837` | MÉRVE — a finomhangolás megléte bekötetlen |
| `editController` | `hasCrop` | Property | `app/edit_controller.py:842` | MÉRVE — a vágás megléte bekötetlen |
| `editController` | `redoAction` | Property | `app/edit_controller.py:875` | BELSŐ — az edit_controller.py:892 ebből képzi a QML-nek szánt redoLabel-t |
| `editController` | `clearCrop` | Slot | `app/edit_controller.py:1057` | MÉRVE — a vágás törlése bekötetlen |
| `editController` | `canRenderEffect` | Slot | `app/edit_controller.py:1702` | MÉRVE — a renderelhetőség kérdezése bekötetlen |
| `editController` | `isDeadLegacyEffect` | Slot | `app/edit_controller.py:1718` | MÉRVE — az elavult effektek felismerése bekötetlen |
| `editController` | `cancelPendingPreview` | Slot | `app/edit_controller.py:2130` | BELSŐ — az application.py:892 hívja leálláskor |
| `emailController` | `prepareAttachments` | Slot | `app/email_controller.py:199` | #1474 — a QML csak a beállítás-fül kliensválasztóját köti |
| `emailController` | `sendRows` | Slot | `app/email_controller.py:231` | #1474 — a tényleges küldés sehonnan nem hívódik |
| `faceScanController` | `isAvailable` | Slot | `app/face_scan_controller.py:155` | #1473 — az arckeresésnek nincs belépési pontja |
| `faceScanController` | `isEmbeddingAvailable` | Slot | `app/face_scan_controller.py:160` | #1473 — az arclenyomatolásnak nincs belépési pontja |
| `faceScanController` | `scanForFaces` | Slot | `app/face_scan_controller.py:178` | #1473 — a keresés maga; se menü, se gomb nem indítja |
| `faceScanController` | `cancelScan` | Slot | `app/face_scan_controller.py:197` | #1473 — a megszakítás; a naiv keresés a dedupController.cancelScan miatt élőnek látta |
| `faceScanController` | `unnamedAlbum` | Slot | `app/face_scan_controller.py:204` | #1473 — a Névtelenek album lekérdezése bekötetlen |
| `faceScanController` | `computeEmbeddings` | Slot | `app/face_scan_controller.py:422` | #1473 — a lenyomatolás indítása bekötetlen |
| `faceScanController` | `cancelEmbedding` | Slot | `app/face_scan_controller.py:439` | #1473 — a lenyomatolás megszakítása bekötetlen |
| `fileOpsController` | `movePhoto` | Slot | `app/fileops_controller.py:82` | FELVÁLTVA — a QML a többes movePhotos alakot hívja |
| `folderHierarchyController` | `setFolders` | Slot | `app/folder_hierarchy_controller.py:104` | BELSŐ — az application.py:704 tölti fel a fát |
| `folderHierarchyController` | `setSimplified` | Slot | `app/folder_hierarchy_controller.py:157` | FELVÁLTVA — a menü a toggleSimplified-et hívja, az hívja ezt |
| `folderHierarchyController` | `expand` | Slot | `app/folder_hierarchy_controller.py:191` | MÉRVE — a fa egy ágának kinyitása bekötetlen (a toggle/expandAll be van kötve) |
| `folderHierarchyController` | `collapse` | Slot | `app/folder_hierarchy_controller.py:195` | MÉRVE — a fa egy ágának becsukása bekötetlen |
| `startupStatus` | `busy` | Property | `app/startup_status.py:63` | MÉRVE — a SplashScreen.qml:42 a saját `busy: !root.ready` alakját számolja |
| `startupStatus` | `report` | Slot | `app/startup_status.py:77` | BELSŐ — az indítás lépéseit az application.py jelenti be |
| `startupStatus` | `finish` | Slot | `app/startup_status.py:89` | BELSŐ — az indítás végét az application.py jelenti be |

**QML-tagot hordozó, de kontextusból el nem ért osztályok:**

| osztály | hely | tag | indoklás |
|---|---|---:|---|
| `FolderListModel` | `app/models.py` | 3 | BELSŐ — a QML a controller.folders tulajdonságon át kapja meg a modellt |
| `PhotoGridModel` | `app/models.py` | 15 | BELSŐ — a QML a controller.photos tulajdonságon át kapja meg a modellt |

<!-- KEPESSEG_OR:VEGE -->

## 5. Nyitott kérdések mérlege

| kérdés | állapot |
|---|---|
| Van-e holt kontextus-objektum? | **LEZÁRVA** — nincs (1.) |
| Hol szakad a lánc tagszinten? | **LEZÁRVA** — 2. és 4. |
| Melyik szakadás valódi hiba? | **LEZÁRVA** — négy, jeggyel (2.); a többi elhatárolva (3.) |
| Megismételhető-e a mérés? | **LEZÁRVA** — igen, de objektumnévvel; a naiv keresés négy néven félrevisz |
| Legyen-e rá automatikus őr? | **LEZÁRVA** — igen, #1476 |

```
Nyitott kérdések: 0 nyílt · 5 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```
