# Lánc-szakadások leltára — ahol a háttér kész, de a felület nem éri el

*Mérve 2026-08-25, `src/picasapy/app/` + `src/picasapy/app/qml/`.*

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

**Nincs holt kontextus-objektum.** Mind a 19 regisztrált objektumra
(`application.py`) hivatkozik a QML. A szakadás mindig **tagszinten** van.

## 2. Négy megerősített lelet — mind önállóan megvalósítható

| # | terület | a háttér | a felület | jegy |
|---|---|---|---|---|
| A | **Nyomtatás** | `print_controller.py`, **213 sor**, 2 tesztfájl | **soha nem példányosul** a termékkódban, nincs `setContextProperty`, **0** QML-hivatkozás; a `Print…` (Ctrl+P) és `Print Thumbnails…` menüpont `placeholder` | #1472 |
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

## 4. A teljes mért lista

A „Python" oszlop a **más fájlból** jövő hivatkozásokat számolja, a
„teszt" a tesztkészletet. Ahol **Python = 0 és teszt > 0**, ott a tag
**csak a tesztek miatt zöld** — ez a keresett minta.

| fájl | sor | fajta | tag | Python | teszt |
|---|---:|---|---|---:|---:|
| `edit_controller.py` | 534 | Property | `enhanceActive` | 0 | 7 |
| `edit_controller.py` | 538 | Property | `autolightActive` | 0 | 0 |
| `edit_controller.py` | 542 | Property | `autocolorActive` | 0 | 0 |
| `edit_controller.py` | 548 | Property | `hasRetouch` | 0 | 2 |
| `edit_controller.py` | 837 | Property | `hasFinetune` | 0 | 3 |
| `edit_controller.py` | 842 | Property | `hasCrop` | 0 | 3 |
| `edit_controller.py` | 875 | Property | `redoAction` | 0 | 1 |
| `edit_controller.py` | 1057 | Slot | `clearCrop` | 0 | 1 |
| `edit_controller.py` | 1702 | Slot | `canRenderEffect` | 0 | 0 |
| `edit_controller.py` | 1718 | Slot | `isDeadLegacyEffect` | 0 | 0 |
| `edit_controller.py` | 2130 | Slot | `cancelPendingPreview` | 1 | 2 |
| `face_scan_controller.py` | 155 | Slot | `isAvailable` | 0 | 1 |
| `face_scan_controller.py` | 160 | Slot | `isEmbeddingAvailable` | 0 | 2 |
| `face_scan_controller.py` | 178 | Slot | `scanForFaces` | 0 | 17 |
| `face_scan_controller.py` | 204 | Slot | `unnamedAlbum` | 0 | 3 |
| `face_scan_controller.py` | 422 | Slot | `computeEmbeddings` | 0 | 3 |
| `face_scan_controller.py` | 439 | Slot | `cancelEmbedding` | 0 | 0 |
| `controller.py` | 284 | Property | `folderDateText` | 0 | 2 |
| `controller.py` | 289 | Property | `folderDescription` | 0 | 3 |
| `controller.py` | 489 | Slot | `setShowHidden` | 0 | 7 |
| `controller.py` | 501 | Slot | `restoreSession` | 1 | 4 |
| `controller.py` | 632 | Slot | `setFolderDescription` | 0 | 6 |
| `effects_controller.py` | 38 | Property | `hasEffectsClipboard` | 0 | 3 |
| `effects_controller.py` | 45 | Property | `canUndoPasteEffects` | 0 | 0 |
| `effects_controller.py` | 50 | Slot | `copyEffects` | 0 | 11 |
| `effects_controller.py` | 65 | Slot | `pasteEffects` | 4 | 14 |
| `effects_controller.py` | 141 | Slot | `undoPasteEffects` | 0 | 2 |
| `folder_hierarchy_controller.py` | 58 | Slot | `setFolders` | 1 | 10 |
| `folder_hierarchy_controller.py` | 111 | Slot | `setSimplified` | 0 | 4 |
| `folder_hierarchy_controller.py` | 145 | Slot | `expand` | 0 | 2 |
| `folder_hierarchy_controller.py` | 149 | Slot | `collapse` | 0 | 0 |
| `collage_save.py` | 114 | Property | `collageTitle` | 0 | 4 |
| `collage_save.py` | 136 | Slot | `setCollageTitle` | 1 | 1 |
| `collage_save.py` | 153 | Slot | `setCollageSavedPath` | 0 | 2 |
| `print_controller.py` | 83 | Slot | `listPrinters` | 0 | 1 |
| `print_controller.py` | 98 | Slot | `renderPrintPreviewPdf` | 0 | 8 |
| `print_controller.py` | 118 | Slot | `printRows` | 0 | 3 |
| `email_controller.py` | 199 | Slot | `prepareAttachments` | 0 | 6 |
| `email_controller.py` | 231 | Slot | `sendRows` | 0 | 6 |
| `export_controller.py` | 144 | Slot | `exportMovieFull` | 0 | 4 |
| `export_controller.py` | 154 | Slot | `setExportMovieFull` | 0 | 4 |
| `library_controller.py` | 682 | Slot | `removeWatchedFolder` | 0 | 11 |
| `library_controller.py` | 721 | Slot | `faceDetectionEnabledFor` | 0 | 13 |
| `photo_ops_controller.py` | 540 | Property | `canUndoPasteAllEffects` | 0 | 3 |
| `photo_ops_controller.py` | 636 | Slot | `undoPasteAllEffects` | 0 | 4 |
| `appearance_controller.py` | 61 | Slot | `setDarkTheme` | 0 | 21 |
| `batch_effect_controller.py` | 158 | Property | `canUndoBatchEdit` | 0 | 8 |
| `collage_controller.py` | 335 | Property | `collageFrameCenter` | 0 | 5 |
| `compact_controller.py` | 56 | Property | `wastedPercent` | 0 | 0 |
| `create_controller.py` | 253 | Property | `collageSeed` | 0 | 5 |
| `fileops_controller.py` | 82 | Slot | `movePhoto` | 0 | 8 |
| `geo_controller.py` | 129 | Slot | `locationOfRow` | 0 | 2 |

**Összesen 52 tag, 18 fájlban.**

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
