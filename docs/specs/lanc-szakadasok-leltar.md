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
| B | **Arcfelismerés indítása** | `scanForFaces`, `cancelScan`, `computeEmbeddings`, `cancelEmbedding`, `isAvailable`, `isEmbeddingAvailable`, `unnamedAlbum` | ~~egyik sincs bekötve — közben a **névadó felület él**, és a `scanPercent` **haladást jelenít meg** egy indíthatatlan keresésről~~ — **BEKÖTVE (#1473)**: `FaceScanDialog.qml`, élő `Eszközök ▸ Arcok keresése…`, megszakítható keresés és csoportosítás, hiányzó modellnél INDOKOLT tiltás. ⚠️ A modellfájl beszerzésére viszont továbbra sincs felületi út — a funkció friss telepítésen ezért végig szürke marad (külön jegy kell rá) | #1473 |
| C | **E-mail küldés** | `prepareAttachments`, `sendRows` | a QML az `emailController`-t **csak** a beállítás-fül kliensválasztójához köti (`OptionsTabEmail.qml`) | #1474 |
| D | **Visszavonás UI nélkül** | `undoPasteAllEffects`, `canUndoPasteAllEffects`, `canUndoBatchEdit` | nincs gomb; a `Main.qml:754` **ki is mondja**: „csak a vezérlőn elérhető, UI-gomb nélkül". A hivatkozott **#426 és #152 LEZÁRVA** | #1475 |

## 3. Elhatárolások — ezeket NE vegye fel senki hibaként

| tag | miért nem hiba |
|---|---|
| `library_controller.removeWatchedFolder` | a **#1249** felváltotta a szélesebb `removeFolder`-rel; a QML azt hívja |
| `fileops_controller.movePhoto` | egyes alak; a QML a `movePhotos` többes alakot használja |
| `controller.statusText` | **él**, aliason át: `tray.ctl.statusText` (`TrayBar.qml:117`) |
| `controller.setShowHidden` | a menü a `toggleShowHidden`-t hívja — szándékos |
| `effects_controller` tagjai | **nem árva modul**: az `EffectsClipboardMixin` a `controller.py:106`-on át be van építve. A #152-es réteg áll UI nélkül, miközben a menü „Copy/Paste All Effects" a **kötegelt** úton megy (`photo_ops_controller.py:633/648/724`). A **#1534 eldöntötte**: saját menüpontot nem kap (az eredetiben EGY parancs van, kétágú kezelővel), de nem is törölhető — a láncot egészben átvivő szemantikája a **hűséges**, a bekötött kötegelté nem. Ld. `docs/decisions/effektus-vagolap-ket-reteg.md` (ADR-007) |

## 4. A teljes mért lista — GENERÁLT

A táblát a `python scripts/kepesseg_or.py --leltar --ir` írja, az
indoklásokat a `scripts/kepesseg_or_baseline.txt` adja. Kézzel ne
szerkeszd: a `tests/tools/test_kepesseg_or_1476.py` összeveti a kettőt.

### Ami erről a lapról SZÁNDÉKOSAN hiányzik — és hol van helyette

| kimarad | miért | hol találod |
|---|---|---|
| a mérés terjedelme (hány fájl, tag, alias) | #1508 — minden új `.py`/QML-fájltól elavult | az őr futásának kimenete (CI `lint`-napló) |
| a tagok **pontos sora** | #1523 — egy fölötte beszúrt sortól elavult | `python scripts/kepesseg_or.py --list`, és az új szakadás hibaüzenete |
| az árva osztályok **tagszáma** | #1523 — a `models.py` forró fájl, minden új modell-tagtól elavult | ugyanott, `--list` |

Amíg ezek itt álltak, a bitre egyezést kérő teszt olyan ágakat is
megbuktatott, amelyek **szakadást nem okoztak**: a #1508 előtt minden ág,
amelyik egyetlen fájlt hozzáadott (egy nap alatt négy PR, három
merge-ütközés); utána minden ág, amelyik **egyetlen sort beszúrt** egy
szakadást tartalmazó fájlba (2026-08-26: #1520 és #1521, fejenként egy
fölösleges piros CI → `--ir` → új push kör).

**A fájlnév marad** — tagnévvel együtt `grep -n "<tagnév>" src/picasapy/app/<fájl>`
pontos találatot ad, és nem mozdul el egy fölötte beszúrt sortól.

**A védelem nem gyengült.** Ami a lapon áll, az bitre egyezik: a szakadás
azonossága — kontextus-objektum, tag, fajta, fájl és **indoklás**. Új vagy
eltűnt szakadásra, sőt átírt indoklásra is bukik a készlet, az őr pedig
1-es kilépőkóddal áll meg (`python scripts/kepesseg_or.py`).

⚠️ A 2026-08-25-i **kézi** mérés 52 tagot talált; az őr ugyanezen a fán
**56**-ot. A különbség nem a fa változása, hanem a minősített keresés: a
kézi mérés nem látta az `editController.revision`-t (a `photos.revision`
kötések elfedték), a `faceScanController.cancelScan`-t (a `dedupController`
azonos nevű tagja fedte el), és nem nézte a `startup_status.py`-t sem.

<!-- KEPESSEG_OR:KEZDET -->

*Ezt a blokkot a `python scripts/kepesseg_or.py --leltar --ir` írja.*
*Kézzel ne szerkeszd: a `tests/tools/test_kepesseg_or_1476.py` őrzi.*

*Ami ezen a lapon SZÁNDÉKOSAN nem áll: a mérés terjedelme (hány*
*Python-, hány QML-fájl, hány tag, hány alias — #1508), a tagok*
*PONTOS SORA és az árva osztályok tagszáma (#1523). Mindhárom a*
*futás kimenetében van (CI-napló, `--list`), mert a verziózott szám*
*minden érintetlen kódmozdulattól elavult — valódi szakadás nélkül.*
*A fájlnév marad: tagnévvel együtt `grep -n`-nel pontos, és stabil.*

**Felületről el nem ért vezérlő-tag: 43.**

| kontextus-objektum | tag | fajta | hely | indoklás |
|---|---|---|---|---|
| `compactController` | `wastedPercent` | Property | `app/compact_controller.py` | MÉRVE — a tömörítés-párbeszéd nem mutatja, mennyi hely nyerhető |
| `controller` | `setDarkTheme` | Slot | `app/appearance_controller.py` | FELVÁLTVA — a menü a toggleDarkTheme-et hívja (PicasaMenuBar.qml) |
| `controller` | `collageFrameCenter` | Property | `app/collage_controller.py` | MÉRVE — kollázs-keret középpont; a vászon nem köti |
| `controller` | `collageTitle` | Property | `app/collage_save.py` | MÉRVE — a kollázs címe a felületen nem jelenik meg |
| `controller` | `setCollageTitle` | Slot | `app/collage_save.py` | BELSŐ — a kollázs-vezérlő állítja (collage_controller.py:437, collage_save.py:918) |
| `controller` | `setCollageSavedPath` | Slot | `app/collage_save.py` | MÉRVE — a mentett kollázs útja bekötetlen |
| `controller` | `folderDateText` | Property | `app/controller.py` | MÉRVE — a mappa dátumfelirata bekötetlen (párja sincs …Of alakban) |
| `controller` | `folderDescription` | Property | `app/controller.py` | FELVÁLTVA — a felület a mappánkénti folderDescriptionOf(path) alakot hívja |
| `controller` | `setShowHidden` | Slot | `app/controller.py` | FELVÁLTVA — a menü a toggleShowHidden-t hívja (PicasaMenuBar.qml) |
| `controller` | `restoreSession` | Slot | `app/controller.py` | BELSŐ — a controller.py:876 és a library_controller.py:346 hívja induláskor |
| `controller` | `setFolderDescription` | Slot | `app/controller.py` | FELVÁLTVA — a felület a setFolderDescriptionOf(path, …) alakot hívja |
| `controller` | `collageSeed` | Property | `app/create_controller.py` | MÉRVE — a véletlen elrendezés magja bekötetlen |
| `controller` | `hasEffectsClipboard` | Property | `app/effects_controller.py` | ELDÖNTVE (#1534) — nincs külön menüpont hozzá az eredetiben; a réteg a HŰSÉGES tartalmi viselkedés referenciája, ezért marad; ADR-007 |
| `controller` | `canUndoPasteEffects` | Property | `app/effects_controller.py` | ELDÖNTVE (#1534) — a verem többszintűsége az eredetiben nem létezik; nem kap felületet; ADR-007 |
| `controller` | `copyEffects` | Slot | `app/effects_controller.py` | ELDÖNTVE (#1534) — a másolás; a felületé a KÖTEGELT copyAllEffects; ADR-007 |
| `controller` | `pasteEffects` | Slot | `app/effects_controller.py` | ELDÖNTVE (#1534) — a beillesztés; a felületé a KÖTEGELT pasteAllEffects; ADR-007 |
| `controller` | `undoPasteEffects` | Slot | `app/effects_controller.py` | ELDÖNTVE (#1534) — a visszavonás; az eredetiben nincs megfelelője; ADR-007 |
| `controller` | `exportMovieFull` | Slot | `app/export_controller.py` | BELSŐ — a beállítást az export_controller.py:371 olvassa vissza |
| `controller` | `setExportMovieFull` | Slot | `app/export_controller.py` | MÉRVE — a beállítás írása bekötetlen; a párja BELSŐ |
| `controller` | `locationOfRow` | Slot | `app/geo_controller.py` | MÉRVE — a sor helyadata bekötetlen |
| `controller` | `removeWatchedFolder` | Slot | `app/library_controller.py` | FELVÁLTVA — a #1249 óta a bővebb removeFolder megy a QML-ből |
| `controller` | `faceDetectionEnabledFor` | Slot | `app/library_controller.py` | MÉRVE — a QML SAJÁT tükrét számolja (FolderStatePanel.qml:40, FolderManagerDialog.qml:198) |
| `editController` | `revision` | Property | `app/edit_controller.py` | MÉRVE — a QML a photos.revision-t köti; ez a szerkesztő SAJÁT változásszáma |
| `editController` | `redeyeActive` | Property | `app/edit_controller.py` | MÉRVE — az EditorPanel.qml:132 SAJÁT `property bool redeyeActive`-ot tart |
| `editController` | `enhanceActive` | Property | `app/edit_controller.py` | FELVÁLTVA — a #116 az egygombos javításokról LEVETTE a „benyomva" állapotot; a csempe a párját, az enhanceEnabled-et köti (PhotoViewer.qml:291) |
| `editController` | `autolightActive` | Property | `app/edit_controller.py` | FELVÁLTVA — ugyanaz: a csempe az autolightEnabled-et köti (PhotoViewer.qml:292) |
| `editController` | `autocolorActive` | Property | `app/edit_controller.py` | FELVÁLTVA — ugyanaz: a csempe az autocolorEnabled-et köti (PhotoViewer.qml:293) |
| `editController` | `hasRetouch` | Property | `app/edit_controller.py` | MÉRVE — #1052: SZÁNDÉKOS; a feliratot az undoLabel adja (#465), a csempe kiemelése a nyitott eszközt jelzi (#116) |
| `editController` | `hasFinetune` | Property | `app/edit_controller.py` | MÉRVE — a finomhangolás megléte bekötetlen |
| `editController` | `redoAction` | Property | `app/edit_controller.py` | BELSŐ — az edit_controller.py:892 ebből képzi a QML-nek szánt redoLabel-t |
| `editController` | `canRenderEffect` | Slot | `app/edit_controller.py` | MÉRVE — a renderelhetőség kérdezése bekötetlen |
| `editController` | `isDeadLegacyEffect` | Slot | `app/edit_controller.py` | MÉRVE — az elavult effektek felismerése bekötetlen |
| `editController` | `cancelPendingPreview` | Slot | `app/edit_controller.py` | BELSŐ — az application.py:892 hívja leálláskor |
| `emailController` | `prepareAttachments` | Slot | `app/email_controller.py` | #1474 — a QML csak a beállítás-fül kliensválasztóját köti |
| `emailController` | `sendRows` | Slot | `app/email_controller.py` | #1474 — a tényleges küldés sehonnan nem hívódik |
| `fileOpsController` | `movePhoto` | Slot | `app/fileops_controller.py` | FELVÁLTVA — a QML a többes movePhotos alakot hívja |
| `folderHierarchyController` | `setFolders` | Slot | `app/folder_hierarchy_controller.py` | BELSŐ — az application.py:704 tölti fel a fát |
| `folderHierarchyController` | `setSimplified` | Slot | `app/folder_hierarchy_controller.py` | FELVÁLTVA — a menü a toggleSimplified-et hívja, az hívja ezt |
| `folderHierarchyController` | `expand` | Slot | `app/folder_hierarchy_controller.py` | MÉRVE — a fa egy ágának kinyitása bekötetlen (a toggle/expandAll be van kötve) |
| `folderHierarchyController` | `collapse` | Slot | `app/folder_hierarchy_controller.py` | MÉRVE — a fa egy ágának becsukása bekötetlen |
| `startupStatus` | `busy` | Property | `app/startup_status.py` | MÉRVE — a SplashScreen.qml:42 a saját `busy: !root.ready` alakját számolja |
| `startupStatus` | `report` | Slot | `app/startup_status.py` | BELSŐ — az indítás lépéseit az application.py jelenti be |
| `startupStatus` | `finish` | Slot | `app/startup_status.py` | BELSŐ — az indítás végét az application.py jelenti be |

**QML-tagot hordozó, de kontextusból el nem ért osztályok:**

| osztály | hely | indoklás |
|---|---|---|
| `FolderListModel` | `app/models.py` | BELSŐ — a QML a controller.folders tulajdonságon át kapja meg a modellt |
| `PhotoGridModel` | `app/models.py` | BELSŐ — a QML a controller.photos tulajdonságon át kapja meg a modellt |

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
