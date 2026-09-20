# UI-lefedettség — az eredeti Picasa panelei ↔ a PicasaPy QML-fája

**Generálva:** 2026-09-20 — **ezt a fájlt ne írd kézzel**, újragenerálható.

**Előállító:** `eszkozok/ui_lefedettseg.py` (privát `picasapy-agent` repó).
**Bemenet (privát):** `referencia/ui-leltar.csv` (2020 elem / 74 panel, a `.tre` erőforrásokból), `referencia/panel-feliratok-hu.tsv`, `referencia/stringres-en-hu.tsv`.
**Bemenet (publikus, kézzel gondozott):** `docs/specs/ui-lefedettseg-megfeleltetes.csv` (panel → QML-fájlok) és `docs/specs/ui-lefedettseg-elemek.csv` (elemenkénti felülbírálás).
**Kapcsolódó:** `docs/specs/ui-audit-mainwindow.md` 1.6 szakasz (a leltár előállítása), `docs/specs/ui-audit-editor.md`, `docs/specs/ui-audit-menus.md`.

Újrafuttatás:

```
python3 ~/picasapy-agent/eszkozok/ui_lefedettseg.py \
    --publikus ~/Documents/PicasaPy
```

## Módszer és a számok olvasata

A párosítás **nem** puszta névegyezés: a panel → QML megfeleltetés kézzel gondozott, és minden panel szerepel benne — ami nem párosítható, az `nincs-megfeleltetes` vagy `nem-cel` állapottal, nem csendes kihagyással.

Az elemek három osztályba esnek, mert a 2020 elem nagy része rajz-primitív, nem vezérlő:

| osztály | mi ez | hogyan mérjük |
|---|---|---|
| `feliratos` | van felirata vagy buboréksúgója | a szöveg (angol vagy hivatalos magyar) megvan-e a panelhez rendelt QML-ekben |
| `vezerlo` | nincs felirata, de a neve vezérlőre utal | `objectName`/`id` egyezés |
| `rajzolo` | háttér, keret, ikon, maszk, klip, fogantyú… | **gépi úton nem értékelhető**, külön oszlopban számoljuk |

Elem-státuszok: `parositva`, `masutt-megvan` (a felirat nem a panelhez rendelt QML-ekben van, hanem a fa más pontján — tipikusan a menüsorban; vagyis a funkció megvan, de **nem ezen a felületen**), `hianyzik` (FELTÁRATLAN — nem tudjuk, mit csinál), `lekutatva` (a spec-lapjaink CÍMMEL leírják, csak nem építettük meg), `bizonytalan` (vezérlő-gyanús, de nem dönthető el gépi úton — kézi felülbírálásra vár), `nem-ertekelheto` (rajzoló elem), `nem-cel` (megszűnt vagy kimondottan nem célzott felület eleme).

**A `nem-cel` elemek KIMARADNAK a lefedettség nevezőjéből** (a tulajdonos döntése, 2026-09-02): ami sosem épül meg, az sem hiányt, sem lefedettséget nem jelent. A kihagyott elemek száma és a paneljeik a fenti összesítésben és a panelenkénti táblában külön oszlopban látszanak — a szám csökkenése tehát nem eltüntetés, hanem elszámolt kivétel.

**A hiány KÉT külön dolgot jelent** (#1878): a `hianyzik` feltáratlan — nem tudjuk, mit csinál, tehát KUTATÓI kör kell; a `lekutatva` fel van tárva, csak nem építettük meg, tehát FEJLESZTŐI kör. A besoroláshoz egy spec-lapon ugyanabban a szakaszban kell állnia az elemnévnek és egy bináris címnek (`0x…`) vagy fájl+sornak; a generált lapok — köztük EZ a lap — nem számítanak bizonyítéknak.

**A `hianyzik` óvatosan olvasandó:** azt jelenti, hogy az eredeti elem felirata/azonosítója nem található a panelhez rendelt QML-fájljainkban. Ha a funkció nálunk máshogy hívódik, az elem-felülbírálás CSV-be kell felvenni — ez a tábla karbantartásának a rendes menete.

## Összesítés

| mutató | darab |
|---|---:|
| eredeti UI-elem összesen | 2020 |
| panel összesen | 74 |
| ebből értékelhető elem (`feliratos` + `vezerlo`) | 643 |
| párosítva | 297 |
| másutt megvan (nem ezen a felületen) | 39 |
| hiányzik — **feltáratlan** (kutatói kör kell) | 0 |
| hiányzik — **lekutatva** (fejlesztői kör kell) | 291 |
| bizonytalan | 18 |
| nem értékelhető (rajzoló elem) | 1284 |
| **nem cél** (megszűnt szolgáltatás) — a nevezőből KIMARAD | 91 |
| **lefedettség az értékelhető elemeken** | **46.2%** |

> ⚠️ **A 46.2% ALSÓ BECSLÉS, nem pontos érték.** 18 elem `bizonytalan` — felirat nélküli vezérlő, amit a szkript gépi úton **nem tud eldönteni**; ezeket a nem-lefedett oldalon számoltuk. Ha mind megvolna, a lefedettség **49.0%** lenne. A valódi érték a kettő között van, és csak a bizonytalan elemek egyenkénti kimérésével szűkíthető.

## Rangsor — a tíz legnagyobb fehér folt

Jegynyitáshoz ez a sorrend: a hiányzó és a bizonytalan elemek száma panelenként.

| # | panel | hiány + bizonytalan | mit takar |
|---:|---|---:|---|
| 1 | `makemoviepanel` | 49 | Csak a filmkészítő párbeszéd van meg; interaktív filmkészítő panel nincs |
| 2 | `publish` | 27 | A panel 21 MÉRT vezérlője megvan (#2508: Ajándék-CD, biztonsági mentés, feltöltés — a mért helyeken és feliratokkal). ⚠️ A három üzemmód MŰKÖDÉSE még nincs kész, és a panel ezért szándékosan nincs bekötve a menübe; az elemenkénti párosítás ezt helyesen tükrözi (ami nincs megépítve, az nem párosul). A web_group hét eleme hatókörön kívül (online). |
| 3 | `editpanel` | 22 | A szerkesztő teljes bal oldali panelje minden fülével — ÉS a gazdája, a PhotoViewer.qml (fejléc, előnézet, nagyítás-csúszka, felirat, kettős nézet) |
| 4 | `thumbui` | 20 | A fő könyvtárnézet egésze |
| 5 | `printoptions` | 13 | Nyomtatási szegély- és feliratopciók (#1780); a Beállítások „Nyomtatás” füle MÁS panel |
| 6 | `choose_mail` | 13 | Levelezőprogram-választó párbeszéd — nincs nálunk |
| 7 | `capturemoviepanelpopup` | 11 | Webkamerás videofelvétel — nincs nálunk |
| 8 | `compose_mail` | 10 | Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül |
| 9 | `acquirepanel` | 8 | Importáló panel — nálunk párbeszédablak, nem teljes értékű bal oldali panel |
| 10 | `faceheaderpanel` | 8 | Névvel ellátott arc-album fejléce |

## Panelenkénti lefedettség

| panel | eredeti elem | értékelhető | párosítva | másutt | feltáratlan | lekutatva | bizonytalan | rajzoló | nem cél | megfeleltetés |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `makemoviepanel` | 111 | 55 | 1 | 5 | 0 | 49 | 0 | 56 | 0 | `CreateDialogs.qml` |
| `publish` | 125 | 30 | 0 | 3 | 0 | 27 | 0 | 95 | 0 | `PublishPanel.qml` |
| `editpanel` | 312 | 125 | 102 | 1 | 0 | 22 | 0 | 187 | 0 | `EditorPanel.qml`, `EditorTabBar.qml`, `EditorTabCommonFixes.qml`, `EditorFinetunePanel.qml`, `EditorEffectsTab1.qml`, `EditorEffectsTab2.qml`, `EditorEffectsTab3.qml`, `EditorEffectsTab4.qml`, `EditorLegacyTab.qml`, `EditorCropPanel.qml`, `EditorRedeyePanel.qml`, `EditorRetouchPanel.qml`, `EditorParamPanel.qml`, `EditorDialogs.qml`, `EditTabButton.qml`, `EditTabIcon.qml`, `CropOverlay.qml`, `HistogramBox.qml`, `AddCustomAspectRatioDialog.qml`, `EditOverwriteDialog.qml`, `BatchEditProgressPanel.qml`, `ToolTile.qml`, `PhotoViewer.qml` |
| `thumbui` | 140 | 44 | 20 | 4 | 0 | 20 | 0 | 93 | 3 | `MainToolbar.qml`, `LightboxFeed.qml`, `ThumbDelegate.qml`, `TrayBar.qml`, `TimelineView.qml`, `PicasaScrollBar.qml`, `FolderPane.qml`, `FolderTreeItem.qml`, `FolderStateBadge.qml`, `SlideshowView.qml`, `Main.qml` |
| `printoptions` | 49 | 29 | 13 | 3 | 0 | 13 | 0 | 20 | 0 | `PrintOptionsPanel.qml`, `PrintDialog.qml` |
| `choose_mail` | 24 | 13 | 0 | 0 | 0 | 13 | 0 | 11 | 0 | **nincs-megfeleltetes** — Levelezőprogram-választó párbeszéd — nincs nálunk |
| `capturemoviepanelpopup` | 45 | 12 | 0 | 1 | 0 | 11 | 0 | 33 | 0 | **nincs-megfeleltetes** — Webkamerás videofelvétel — nincs nálunk |
| `compose_mail` | 41 | 10 | 0 | 0 | 0 | 10 | 0 | 31 | 0 | **nincs-megfeleltetes** — Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül |
| `acquirepanel` | 67 | 20 | 12 | 0 | 0 | 6 | 2 | 43 | 4 | `PicasaImportDialog.qml`, `ImportSourceDialog.qml`, `ImportProgressPanel.qml`, `ImportDropArea.qml` |
| `faceheaderpanel` | 39 | 13 | 4 | 1 | 0 | 8 | 0 | 26 | 0 | `LightboxHeader.qml`, `UnnamedFacesView.qml`, `FacesOverlay.qml`, `PeopleAlbumContextMenu.qml` |
| `buttonmgr` | 29 | 13 | 0 | 5 | 0 | 8 | 0 | 16 | 0 | **nincs-megfeleltetes** — Gombsáv-testreszabó párbeszéd — nincs nálunk |
| `collagepanel` | 108 | 55 | 48 | 0 | 0 | 4 | 3 | 53 | 0 | `CreateDialogs.qml`, `CollagePanel.qml`, `CollagePanelTabBar.qml`, `CollagePanelTabButton.qml`, `CollageSettingsTab.qml`, `CollageClipsTab.qml`, `CollageActionRow.qml`, `CollageZOrderColumn.qml`, `CollageSnapColumn.qml`, `CollageRandomRow.qml`, `CollageContextMenus.qml`, `CollageCanvas.qml`, `CollageFormatMenu.qml`, `CollageThemePopup.qml`, `CollageBorderPicker.qml`, `CollageBackgroundBox.qml`, `CollageNode.qml`, `CollageGroupNode.qml`, `CollageSheet.qml`, `CollageRing.qml`, `CollageProgressOverlay.qml`, `CollageDialogs.qml`, `CollageDraftDialog.qml`, `CollageDoneNotice.qml` |
| `titledialog` | 18 | 7 | 0 | 0 | 0 | 7 | 0 | 11 | 0 | **nincs-megfeleltetes** — Filmes címdia-szerkesztő párbeszéd — nincs nálunk |
| `video_control_bar` | 24 | 6 | 0 | 0 | 0 | 6 | 0 | 18 | 0 | `VideoPlayerView.qml` |
| `keywords` | 18 | 7 | 0 | 1 | 0 | 5 | 1 | 11 | 0 | `TagsPanel.qml` |
| `searchoptions` | 9 | 6 | 0 | 0 | 0 | 6 | 0 | 3 | 0 | `SearchGroupHeader.qml`, `MainToolbar.qml` |
| `edittextpanel` | 45 | 19 | 14 | 0 | 0 | 5 | 0 | 26 | 0 | `EditorTextPanel.qml`, `TextColorSwatches.qml` |
| `searchcontainer` | 25 | 11 | 6 | 0 | 0 | 5 | 0 | 14 | 0 | `MainToolbar.qml`, `SearchSuggestions.qml` |
| `geopanel` | 14 | 5 | 0 | 0 | 0 | 4 | 1 | 9 | 0 | `PlacesPanel.qml`, `PlacesMap.qml` |
| `initialscan` | 18 | 4 | 0 | 0 | 0 | 4 | 0 | 14 | 0 | `InitialScanDialog.qml` |
| `video_control_bar2` | 18 | 4 | 0 | 0 | 0 | 4 | 0 | 14 | 0 | `VideoPlayerView.qml` |
| `panelroot` | 14 | 7 | 2 | 1 | 0 | 4 | 0 | 7 | 0 | `Main.qml`, `MainToolbar.qml` |
| `throttle` | 10 | 4 | 1 | 0 | 0 | 4 | 0 | 5 | 0 | `PicasaScrollBar.qml` |
| `printpanel` | 73 | 33 | 30 | 0 | 0 | 3 | 0 | 40 | 0 | `PrintDialog.qml` |
| `editoneup` | 34 | 5 | 0 | 2 | 0 | 3 | 0 | 29 | 0 | `PhotoViewer.qml` |
| `oneup` | 33 | 5 | 0 | 2 | 0 | 3 | 0 | 28 | 0 | `PhotoViewer.qml` |
| `outputlayout` | 31 | 9 | 5 | 1 | 0 | 3 | 0 | 22 | 0 | `TrayBar.qml` |
| `headerpanel` | 30 | 7 | 4 | 0 | 0 | 3 | 0 | 19 | 4 | `LightboxHeader.qml` |
| `peoplepanel` | 14 | 6 | 1 | 2 | 0 | 3 | 0 | 8 | 0 | `PeoplePanel.qml`, `PeoplePanelRow.qml` |
| `gedialog` | 13 | 5 | 1 | 1 | 0 | 3 | 0 | 8 | 0 | `PlacesPanel.qml`, `PlacesMap.qml` |
| `rightdrawerpanel` | 9 | 3 | 0 | 0 | 0 | 3 | 0 | 6 | 0 | `PropertiesPanel.qml` |
| `foldermgr` | 32 | 11 | 4 | 5 | 0 | 2 | 0 | 21 | 0 | `FolderManagerDialog.qml` |
| `tagpanel` | 24 | 8 | 6 | 0 | 0 | 0 | 2 | 16 | 0 | `TagsPanel.qml` |
| `unknownfaceheaderpanel` | 18 | 6 | 4 | 0 | 0 | 2 | 0 | 12 | 0 | `UnnamedFacesView.qml` |
| `instructionpanel` | 7 | 2 | 0 | 0 | 0 | 2 | 0 | 5 | 0 | **nincs-megfeleltetes** — Betanító buborék („Learn more…”) — nincs nálunk |
| `movieeditpanel` | 7 | 4 | 2 | 0 | 0 | 2 | 0 | 3 | 0 | `VideoPlayerView.qml` |
| `activity` | 6 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 0 | `ActivityBadge.qml` |
| `nav` | 6 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 0 | **nincs-megfeleltetes** — Nagyítás-navigátor („floater”) a szerkesztőben — nálunk csak a PhotoViewer nagyítás-állapotgépe van, navigátor-ablak nincs |
| `uploadallinstructionpanel` | 5 | 1 | 0 | 0 | 0 | 1 | 0 | 4 | 0 | **nincs-megfeleltetes** — Feltöltési betanító buborék — nincs nálunk |
| `propertiespanel` | 3 | 1 | 0 | 0 | 0 | 0 | 1 | 2 | 0 | `PropertiesPanel.qml` |
| `bigslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `brushslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `burstslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `durationslider` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `editslider1` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `editslider2` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `editslider3` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `editslider4` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `flightslider1` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `lengthslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `outlineweightslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `printborderslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `scaleslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `spacing_slider` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `textopacityslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `timeslider` | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | `PicasaSlider.qml` |
| `toolslider` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `transitionslider` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `zoomslider` | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | `PicasaSlider.qml` |
| `upload` | 61 | 0 | 0 | 0 | 0 | 0 | 0 | 40 | 21 | **nem-cel** — Picasa Web Albums feltöltő párbeszéd — a szolgáltatás 2016-ban megszűnt; a panel MINDEN eleme a PWA-hoz köt (album-lista, láthatóság, együttműködők, tárhely-bővítés) |
| `buzzupload` | 55 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 22 | **nem-cel** — Google Buzz feltöltés — a szolgáltatás megszűnt, nem cél |
| `compose_share` | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 16 | **nem-cel** — PWA megosztási meghívó szerkesztő — a szolgáltatás 2016-ban megszűnt; album-láthatóság, együttműködők, címzettek, csoportok |
| `canoncapturemoviepanelpopup` | 45 | 0 | 0 | 0 | 0 | 0 | 0 | 40 | 5 | **nem-cel** — Canon SDK-s kamerafelvétel — nem cél |
| `quicktagconfig` | 33 | 15 | 16 | 0 | 0 | 0 | 0 | 17 | 0 | `QuickTagsConfigDialog.qml` |
| `collab` | 23 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 10 | **nem-cel** — Picasa Web Albums közös album — a szolgáltatás megszűnt, nem cél |
| `uploadmgr` | 17 | 1 | 0 | 1 | 0 | 0 | 0 | 10 | 6 | **nincs-megfeleltetes** — Feltöltés-kezelő (szüneteltetés/folytatás) — nincs nálunk |
| `wait_dialog` | 13 | 1 | 1 | 0 | 0 | 0 | 0 | 12 | 0 | `BatchEditProgressPanel.qml`, `ConfirmDialog.qml` |
| `pickerpanel` | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 0 | `TextColorSwatches.qml` |
| `modalprogress` | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | `ImportProgressPanel.qml`, `BatchEditProgressPanel.qml` |
| `scratch` | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | **nincs-megfeleltetes** — Belső rajzfelület (album-előnézet összeállítása) — nem felhasználói felület |
| `moviecontrols` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | `VideoPlayerView.qml` |
| `nerdview` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | `PerfMonitorPanel.qml`, `HistogramBox.qml` |
| `editpanelactivity` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | **nincs-megfeleltetes** — Belső töltésjelző a szerkesztőben — nincs külön elemünk |
| `slideshowctrls` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | `SlideshowView.qml` |

## A legnagyobb fehér foltok — a hiányzó elemek panelenként, névvel

Csak az értékelhető elemek. `bizonytalan` = nem dönthető el gépi úton, kézi ellenőrzésre vár.

### `makemoviepanel` — 49 hiány · panel-megfeleltetés: `parositva`

Csak a filmkészítő párbeszéd van meg; interaktív filmkészítő panel nincs

- `add_audio` „Load...” (magyarul: „Betöltés...”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `addtomovie` buboréksúgó: „Add the selected clip(s) to the end of the movie” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061f62f)
- `album_order_label` „Album Order” (magyarul: „Album szerint”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `album_order_radio` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006177a3)
- `aoptions_label` „Options” (magyarul: „Opciók”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `audio_label` „Audio Track:” (magyarul: „Hangsáv:”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `bkg_picker_panel` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00621d40)
- `bold` buboréksúgó: „Bold” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00611320)
- `burstslider_label` „Don't filter by time taken” (magyarul: „Ne legyen szűrés a készítés ideje alapján”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006223b0)
- `cancel` „Close” (magyarul: „Bezárás”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061e17f)
- `chronological_order_label` „Chronological” (magyarul: „Időrend”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `chronological_order_radio` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006177a3)
- `crop_to_fit_label` „Full frame photo crop” (magyarul: „Teljes képkockás fotó körbevágása”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `deleteclips` buboréksúgó: „Remove the selected clip(s) from the tray” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061f62f)
- `durationslider_label` „Slide Duration” (magyarul: „Dia időtartama”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006223b0)
- `export_youtube` „YT” (magyarul: „YouTube”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061681e)
- `font_label` „Font:” (magyarul: „Betűtípus:”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `inputtext` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061ec18)
- `insert_slide` buboréksúgó: „Add a new text slide” — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `italic` buboréksúgó: „Italic” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00611320)
- `lengthslider_label` „Total Photos” (magyarul: „Összes fénykép”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006223b0)
- `moviesize_label` „Dimensions” (magyarul: „Méretek”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `ordering_header_label` „Ordering of Slides:” (magyarul: „Diák rendezése:”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `outline` buboréksúgó: „Automatic Outline (like movie subtitles)” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00611320)
- `previewimage` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `previewpanel` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `recompute` „Apply” (magyarul: „Alkalmaz”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `remove_audio` „Clear” (magyarul: „Törlés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061e48c)
- `remove_low_res_faces_label` „Remove Low Resolution Faces” (magyarul: „Kis felbontású arcok eltávolítása”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `remove_slide` buboréksúgó: „Remove the selected slide” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006223b0)
- `render` „Create Movie” (magyarul: „Mozgófilm létrehozása”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00400000)
- `rewind` „Back to selected slide” (magyarul: „Vissza a kijelölt diához”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061681e)
- `size_label` „Size:” (magyarul: „Méret:”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `sizelist` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `smart_order_label` „Best Transitions” (magyarul: „A legjobb átmenetek”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `smart_order_radio` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006177a3)
- `style_label` „Style:” (magyarul: „Stílus:”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `tab2` „Slide” (magyarul: „Dia”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `tab3` „Options” (magyarul: „Klipek”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `tabpanel1` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `tabpanel2` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061681e)
- `tabpanel3` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `tabs` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `templatelist` — 🔧 **lekutatva**, csak nem megépítve (picasa-gomb-es-menu-rendszer.md: collagepanel.tre:343)
- `text_picker_panel` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00621d40)
- `transitionslider_label` „Overlap” (magyarul: „Átfedés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00613b50)
- `transtype_label` „Transition Style” (magyarul: „Képváltási stílus”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `txcolorpicker_bevel` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x00621d40)
- `viewedit` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x006223b0)

### `publish` — 27 hiány · panel-megfeleltetés: `parositva`

A panel 21 MÉRT vezérlője megvan (#2508: Ajándék-CD, biztonsági mentés, feltöltés — a mért helyeken és feliratokkal). ⚠️ A három üzemmód MŰKÖDÉSE még nincs kész, és a panel ezért szándékosan nincs bekötve a menübe; az elemenkénti párosítás ezt helyesen tükrözi (ami nincs megépítve, az nem párosul). A web_group hét eleme hatókörön kívül (online).

- `addmore` „Add More...” (magyarul: „Továbbiak hozzáadása...”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `backup_cancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `backup_eject` „Eject” (magyarul: „Kiadás”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `backup_go` „Burn Disc” (magyarul: „Lemezre írás”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `backup_help` „Help” (magyarul: „Súgó”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `backupcdheader2` „Choose folders & albums to back up” (magyarul: „Mappák és albumok kijelölése biztonsági másolat készítéséhez”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `backuptext2` „Picasa is now showing the files you have not previously backed up.” (magyarul: „A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem készült biztonsági másolat.”) — 🔧 **lekutatva**, csak nem megépítve (biztonsagi-mentes.md: 0x00670b03)
- `backuptext3` „Check the folders you want to back up, or choose 'Select All' to choose everything.” (magyarul: „Jelölje ki azokat a mappákat, amelyekről biztonsági másolatot szeretne készíteni, vagy "Az összes kijelölése" gombra kattintva az összes elemet jelölje ki.”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `giftcdtext` „The items selected with a checkmark above will be included on your Gift CD.   To add more items click the "Add More" button below.” (magyarul: „A program a fent pipával kijelölt elemeket másolja az ajándék CD-re. További elemek felvételéhez kattintson az alábbi "Továbbiak hozzáadása" gombra.”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `label_rpoptionbox1` „Upload” (magyarul: „Feltöltés”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `label_rpoptionbox2` „Change options” (magyarul: „Opciók módosítása”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `label_rpoptionbox3` „Remove online” (magyarul: „Eltávolítás: online elemek”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `picsizemenu` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005ba010)
- `presentcd_cancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (biztonsagi-mentes.md: 0x00679ca0)
- `presentcd_eject` „Eject” (magyarul: „Kiadás”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `presentcd_go` „Burn Disc” (magyarul: „Lemezre írás”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0068eea0)
- `presentcd_help` „Help” (magyarul: „Súgó”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `replicate_button_group` — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `replicate_cancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (biztonsagi-mentes.md: 0x00679ca0)
- `replicate_go` „OK” (magyarul: „OK”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `rpoptionbox1` buboréksúgó: „Selected folder and/or albums will be uploaded” — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `rpoptionbox2` buboréksúgó: „Selected folders and/or albums will be updated online with the options specified in the menus to the right” — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `selectall` „Select All” (magyarul: „Az összes kijelölése”) — 🔧 **lekutatva**, csak nem megépítve (biztonsagi-mentes.md: 0x00679ca0)
- `selectnone` „Select None” (magyarul: „Az összes kijelölés megszüntetése”) — 🔧 **lekutatva**, csak nem megépítve (biztonsagi-mentes.md: 0x00679ca0)
- `upgradestorage` „Upgrade storage” (magyarul: „Tárhely bővítése”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066cb20)
- `uploadallsync` buboréksúgó: „Change the sync setting for the selected folders and/or albums” — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066cb20)
- `webpublish_cancel` — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)

### `editpanel` — 22 hiány · panel-megfeleltetés: `parositva`

A szerkesztő teljes bal oldali panelje minden fülével — ÉS a gazdája, a PhotoViewer.qml (fejléc, előnézet, nagyítás-csúszka, felirat, kettős nézet)

- `aa_2up_toggle` buboréksúgó: „View the same image twice” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `ab_2up_toggle` buboréksúgó: „View two different images” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `edithelpbutton` buboréksúgó: „Help” — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: macros.tre:7)
- `edittextghost` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: editpanel.tre:941)
- `eraserbutton` — 🔧 **lekutatva**, csak nem megépítve (filterdesc-registry.md: thumbui.tre:113)
- `modaldialogblur` — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `movietab` — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `movietabpanel` — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `only_1up_toggle` buboréksúgó: „View only one image” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `picnik` „Edit in Creative Kit” (magyarul: „Szerkesztés a Kreatív készletben”) — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: 0x0040bf70)
- `picnik_fx` buboréksúgó: „Try more effects at Creative Kit” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `picnik_fx_label` „Effects by” (magyarul: „Effektusok a következőtől:”) — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `picnikapply` — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `preview2` — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `previewimage2` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: thumbui.tre:696)
- `quickupload` buboréksúgó: „Upload to your Web Albums Drop Box” — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x00518b40)
- `showtextcheckbox` buboréksúgó: „Toggle to show or hide text on a photo” — 🔧 **lekutatva**, csak nem megépítve (ui-audit-editor.md: 0x005f6410)
- `swap_2up_focus` buboréksúgó: „Switch which image has focus” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `swap_2up_layout` buboréksúgó: „Switch between horizontal and vertical layout” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `toggle_left_drawer` buboréksúgó: „Show/Hide Edit Controls” — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: 0x0040bf70)
- `uploadchanges` buboréksúgó: „Update online copy with this version” — 🔧 **lekutatva**, csak nem megépítve (szerkeszto-felso-sav.md: 0x00cae564)
- `weblink` buboréksúgó: „Go to the website associated with this Photo” — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x00518b40)

### `thumbui` — 20 hiány · panel-megfeleltetés: `parositva`

A fő könyvtárnézet egésze

- `acquirebutton` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `buttonbarsets` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: thumbui.tre:406)
- `buttongroup1` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: macros.tre:196)
- `cdmode` „Gift CD” (magyarul: „Ajándék CD”) — 🔧 **lekutatva**, csak nem megépítve (kézi: ajandek-cd-kimenet.md)
- `editpanel` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `folderviewpopup` buboréksúgó: „View options” — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: acquirepanel.tre:210)
- `fullview` „Edit photos” (magyarul: „Fotók szerkesztése”) — 🔧 **lekutatva**, csak nem megépítve (picasa-gyorsbillentyuk.md: 0x005e6178)
- `hlisthandle` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `hlistsizer` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `hviewtoggle` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `listdecrect` — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: thumbui.tre:516)
- `listdetail` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `loupehit` buboréksúgó: „Click and drag over photos to magnify them” — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: printoptions.tre:119)
- `next` buboréksúgó: „View the next Photo” — 🔧 **lekutatva**, csak nem megépítve (konyvtar-ablak-meretek.md: respack.yt:3280882)
- `prev` buboréksúgó: „View the previous Photo” — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: thumbui.tre:43)
- `searchgroup` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: thumbui.tre:441)
- `single_action_message` „Select items to add to your project's clips tray, then press the "Back" button to return to your project” (magyarul: „Jelölje ki azokat az elemeket, amelyeket a projekt kliptálcájára fel szeretne venni, majd a "Vissza" gombra kattintva térjen vissza a projekthez”) — 🔧 **lekutatva**, csak nem megépítve (getmore-klipgyujto-mod.md: thumbui.tre:660)
- `toggle_right_drawer` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: 0x00632060)
- `visitweb` „Web View” (magyarul: „Internetes nézet”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `webcambutton` buboréksúgó: „Capture photos or video from a webcam or other video device” — 🔧 **lekutatva**, csak nem megépítve (getmore-klipgyujto-mod.md: 0x009ca5e0)

### `printoptions` — 13 hiány · panel-megfeleltetés: `parositva`

Nyomtatási szegély- és feliratopciók (#1780); a Beállítások „Nyomtatás” füle MÁS panel

- `bottomonly_checkbox` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085f7a0)
- `caption_label` „Captions” (magyarul: „Képfeliratok”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: printoptions.tre:45)
- `colorpicker_bevel` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085d550)
- `disabled_label` „Sorry, but these options cannot be used when printing contact sheets.” (magyarul: „Ezek a beállítások indexképek nyomtatásakor nem használhatók.”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085d550)
- `evenwidth_checkbox` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085f7a0)
- `sizelist` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085d550)
- `text_picker_panel` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085d550)
- `textbelowimage_label` „Below image” (magyarul: „A kép alatt”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: printoptions.tre:45)
- `textonborder_label` „On border” (magyarul: „A szegélyen”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: printoptions.tre:45)
- `textonimage_label` „On image” (magyarul: „A képen”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: printoptions.tre:45)
- `useexif_label` „Exif information” (magyarul: „Exif-adatok”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: printoptions.tre:45)
- `usenotext_label` „No text” (magyarul: „Nincs szöveg”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: printoptions.tre:45)
- `wrap_checkbox` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085f7a0)

### `choose_mail` — 13 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Levelezőprogram-választó párbeszéd — nincs nálunk

- `cancelbutton` — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `checkbox` — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `gmailsignup1` „Don't have Gmail? Get a free account.” (magyarul: „Nincs Gmail-fiókja? Nyisson egy fiókot ingyen.”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `help` „Help” (magyarul: „Súgó”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `helpbutton` — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `mail1` „MAIL CLIENT” (magyarul: „LEVELEZŐPROGRAM”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `mail1a` „Use my default email program.” (magyarul: „Az alapértelmezett levelezőprogram használata”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `mail2` „Google Mail” (magyarul: „Google Mail”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `mail2a` „Use my Gmail or Google account.” (magyarul: „A Gmail-fiók vagy a Google Fiók használata”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `mailcancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `picker` — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `remember` „Remember this setting, don't display this dialog again.” (magyarul: „Jegyezze meg ezt a beállítást, ne jelenítse meg a párbeszédpanelt újra.”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)
- `selecttext` „Select how you want to e-mail your photos.” (magyarul: „Válassza ki, hogyan szeretné e-mailben elküldeni fotóit.”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: 0x006e1100)

### `capturemoviepanelpopup` — 11 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Webkamerás videofelvétel — nincs nálunk

- `audio_label` „Audio” (magyarul: „Hang”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `camchange` „Settings” (magyarul: „Beállítások”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `capture` „Record” (magyarul: „Felvétel”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `done` „Done” (magyarul: „Kész”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `live_video` „Camera” (magyarul: „Fényképezőgép”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `next` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `prev` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `settings_apply` „Apply” (magyarul: „Alkalmaz”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `settings_cancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `size_label` „Size” (magyarul: „Méret”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)
- `video_label` „Video” (magyarul: „Videoklip”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x006274f0)

### `compose_mail` — 10 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül

- `changeuser` „Change User” (magyarul: „Felhasználóváltás”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `discard` „Discard” (magyarul: „Elvetés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `discardb` „Discard” (magyarul: „Elvetés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `discardimage` buboréksúgó: „Remove selected image from attachment” — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `preview` — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `send` „Send” (magyarul: „Küldés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `sendb` „Send” (magyarul: „Küldés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `subject_text` „Subject:” (magyarul: „Tárgy:”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `to_text` „To:” (magyarul: „Címzett:”) — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)
- `topentry` — 🔧 **lekutatva**, csak nem megépítve (picasa-email-kuldes.md: compose_mail.tre:68)

### `acquirepanel` — 8 hiány · panel-megfeleltetés: `parositva`

Importáló panel — nálunk párbeszédablak, nem teljes értékű bal oldali panel

- `buttons` — *bizonytalan*
- `import_folder_menu` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005ba010)
- `import_from_menu` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005ba010)
- `nextbutton` buboréksúgó: „View the next Photo” — 🔧 **lekutatva**, csak nem megépítve (picasa-importalas.md: 0x0051f070)
- `previousbutton` buboréksúgó: „View the previous Photo” — 🔧 **lekutatva**, csak nem megépítve (picasa-importalas.md: 0x0051f070)
- `sync_options_button` „Options” (magyarul: „Opciók”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: acquirepanel.tre:210)
- `togglegroup` — *bizonytalan*
- `upload_checkbox` — 🔧 **lekutatva**, csak nem megépítve (picasa-feltolteskezelo.md: 0x00518840)

### `faceheaderpanel` — 8 hiány · panel-megfeleltetés: `parositva`

Névvel ellátott arc-album fejléce

- `create_face_movie` buboréksúgó: „Create Face Movie” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `create_movie` buboréksúgó: „Create Movie Presentation” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `face_zoom` buboréksúgó: „View zoomed in to the face” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `picture_zoom` buboréksúgó: „View zoomed out to the full picture” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `play` buboréksúgó: „Play Fullscreen Slideshow” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `pwa_button` buboréksúgó: „Open PWA web page” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `set_thumbnail` buboréksúgó: „Set as People Album Thumbnail” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `sug_filter` buboréksúgó: „Show only suggestions (when toggled on)” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)

### `buttonmgr` — 8 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Gombsáv-testreszabó párbeszéd — nincs nálunk

- `browse` „Find buttons online...” (magyarul: „Gombok keresése az interneten...”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e14e0)
- `cancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (picasa-gyorsbillentyuk.md: 0x0052ecfc)
- `done` „Done” (magyarul: „Kész”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e2980)
- `leftlist` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e2980)
- `leftlist_text` (magyarul: „Rendelkezésre álló gombok:”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e2980)
- `ok` „OK” (magyarul: „OK”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e2980)
- `rightlist` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e2980)
- `rightlist_text` (magyarul: „Jelenlegi gombok:”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x007e2980)

### `collagepanel` — 7 hiány · panel-megfeleltetés: `parositva`

A kollázs-szerkesztő panel MEGVAN (2026-08-31 mérés): 23 Collage*.qml. A korábbi sor egyetlen fájlra mutatott és azt írta, hogy nincs interaktív szerkesztő — ez ELAVULT volt, és a panel mind a 36 elemét hiánynak jelezte.

- `picker_panel` — 🔧 **lekutatva**, csak nem megépítve (picasa-kollazs-felulet.md: 0x008364a0)
- `previewinset` — 🔧 **lekutatva**, csak nem megépítve (kollazs-panel-ui-spec.md: collagepanel.tre:242)
- `previewroot` — 🔧 **lekutatva**, csak nem megépítve (kollazs-panel-ui-spec.md: collagepanel.tre:242)
- `tabpanel1` — *bizonytalan*
- `tabpanel2` — *bizonytalan*
- `tabs` — *bizonytalan*
- `view_and_edit` — 🔧 **lekutatva**, csak nem megépítve (picasa-kollazs-felulet.md: 0x0082d570)

### `titledialog` — 7 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Filmes címdia-szerkesztő párbeszéd — nincs nálunk

- `add` „Add” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)
- `cancel` „Cancel” — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)
- `captionchk` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)
- `previewimage` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)
- `previewtext` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)
- `sizelist` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)
- `stylelist` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: titledialog.tre:20)

### `video_control_bar` — 6 hiány · panel-megfeleltetés: `parositva`

Videó vezérlősáv (vágás is)

- `moviemode1` buboréksúgó: „Play full screen” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-editor.md: video_control_bar.tre:22)
- `setin` buboréksúgó: „Create a new starting point” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `setout` buboréksúgó: „Create a new ending point” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-editor.md)
- `trimslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x005952d0)
- `volumeslider` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-editor.md: video_control_bar.tre:22)

### `keywords` — 6 hiány · panel-megfeleltetés: `parositva`

Címkeszerkesztő

- `addbutton` „Add” (magyarul: „Hozzáadás”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-beviteli-mezok.md)
- `addkeywords_label` „Add Tag:” (magyarul: „Címke hozzáadása:”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-beviteli-mezok.md)
- `closebutton` „Done” (magyarul: „Kész”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-beviteli-mezok.md)
- `keywordlist` — *bizonytalan*
- `readonly_label` „Tags cannot be modified because one or more items are read-only.” (magyarul: „A címkéket nem lehet módosítani, mert egy vagy több elem írásvédett.”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-beviteli-mezok.md)
- `removebutton` „Remove” (magyarul: „Eltávolítás”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-beviteli-mezok.md)

### `searchoptions` — 6 hiány · panel-megfeleltetés: `parositva`

Keresési eredmény fejléce

- `dupesearch` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: 0x0040bf70)
- `facesearch` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: searchoptions.tre:97)
- `label_searchresult` „Search Result:” (magyarul: „Keresési eredmény:”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-kereses-modok.md)
- `searchcenter` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: searchoptions.tre:97)
- `searchresult` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: searchoptions.tre:97)
- `viewallbutton` „Back to View All” (magyarul: „Az összes megtekintése”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-kereses-modok.md)

### `edittextpanel` — 5 hiány · panel-megfeleltetés: `parositva`

Szöveg-eszköz panelje

- `centeralign` buboréksúgó: „Center justify text” — 🔧 **lekutatva**, csak nem megépítve (picasa-ini-format.md: 0x0062d3b0)
- `colorpicker_bevel` — 🔧 **lekutatva**, csak nem megépítve (szerkeszto-panel-meretek.md: edittextpanel.tre:7)
- `leftalign` buboréksúgó: „Left justify text” — 🔧 **lekutatva**, csak nem megépítve (picasa-ini-format.md: 0x0062d3b0)
- `rightalign` buboréksúgó: „Right justify text” — 🔧 **lekutatva**, csak nem megépítve (picasa-ini-format.md: 0x0062d3b0)
- `sizelist` — 🔧 **lekutatva**, csak nem megépítve (szerkeszto-panel-meretek.md: edittextpanel.tre:7)

### `searchcontainer` — 5 hiány · panel-megfeleltetés: `parositva`

Keresősáv és szűrőgombjai

- `search` — 🔧 **lekutatva**, csak nem megépítve (picasa-keptalca.md: 0x005675d0)
- `searchautocomplete` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-mainwindow.md: searchcontainer.tre:31)
- `searchbutton` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: 0x0040bf70)
- `timecontainer_label` buboréksúgó: „Filter by date range” — 🔧 **lekutatva**, csak nem megépítve (kézi: ui-audit-mainwindow.md)
- `webview` buboréksúgó: „Show uploads to web albums only” — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: 0x00660c80)

### `geopanel` — 5 hiány · panel-megfeleltetés: `parositva`

Helyek panel

- `map_menu` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005ba010)
- `search` — *bizonytalan*
- `search_group` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: geopanel.tre:61)
- `search_label` „Search for an address:” (magyarul: „Cím keresése:”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: 0x00567a00)
- `searchinput` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: geopanel.tre:61)

### `initialscan` — 4 hiány · panel-megfeleltetés: `parositva`

Első indítás — mit vizsgáljunk át

- `cancel` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)
- `radio_complete` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)
- `radio_limited` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)
- `radiogroup` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)

### `video_control_bar2` — 4 hiány · panel-megfeleltetés: `parositva`

Videó vezérlősáv második változata

- `1to1` buboréksúgó: „Show actual movie size (don't stretch)” — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `fullscreen` buboréksúgó: „Play full screen” — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-create-features.md)
- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: video_control_bar2.tre:79)
- `volumeslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: video_control_bar2.tre:79)

### `panelroot` — 4 hiány · panel-megfeleltetés: `parositva`

Legfelső panelváltó (Könyvtár / Import / Kollázs / Film / Felvétel)

- `capturemovietab` „Capture” (magyarul: „Rögzítés”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0074c760)
- `globaltabs` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0074c760)
- `makemovietab` „Movie Maker” (magyarul: „Mozgófilmkészítés”) — 🔧 **lekutatva**, csak nem megépítve (getmore-klipgyujto-mod.md: 0x0056c140)
- `youtab` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0074c760)

### `throttle` — 4 hiány · panel-megfeleltetés: `parositva`

Gyorsgörgető a rács jobb szélén

- `albumscrollbottom` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-mainwindow.md: 0x005de13b)
- `albumscrolltop` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005c24c0)
- `nextalbum` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005c24c0)
- `prevalbum` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005c24c0)

### `printpanel` — 3 hiány · panel-megfeleltetés: `parositva`

Nyomtatási panel és előnézet — nálunk párbeszédablak (PrintDialog.qml, 631 sor), a DPI-őrrel együtt (#1782)

- `captionoptionsbutton` buboréksúgó: „Configure borders and text for Photos to be printed” — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: acquirepanel.tre:210)
- `froogle` „Search Froogle for Supplies” (magyarul: „Tartozékok keresése a Froogle-en”) — 🔧 **lekutatva**, csak nem megépítve (picasa-nyomtatas.md: 0x00743980)
- `phelpbutton` „Help” (magyarul: „Súgó”) — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: macros.tre:7)

### `editoneup` — 3 hiány · panel-megfeleltetés: `parositva`

Egyképes nézet szerkesztés közben

- `captionbutton` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0040bf70)
- `next` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: acquirepanel.tre:210)
- `prev` — 🔧 **lekutatva**, csak nem megépítve (picasa-bezaras-es-kilepes.md: editoneup.tre:40)

### `oneup` — 3 hiány · panel-megfeleltetés: `parositva`

Egyképes nézet a könyvtárban

- `captionbutton` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: oneup.tre:112)
- `next` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: acquirepanel.tre:210)
- `prev` — 🔧 **lekutatva**, csak nem megépítve (picasa-bezaras-es-kilepes.md: editoneup.tre:40)

### `outputlayout` — 3 hiány · panel-megfeleltetés: `parositva`

A tálca alatti kimeneti gombsáv

- `blogger` „Blogger” (magyarul: „Blogger”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: outputlayout.tre:99)
- `orderbutton` „Shop” (magyarul: „Vásárlás”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-program-resources.md)
- `sharewith` „Hello” (magyarul: „Hello”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-program-resources.md)

### `headerpanel` — 3 hiány · panel-megfeleltetés: `parositva`

Album- és mappafejléc a rács fölött

- `create_movie` buboréksúgó: „Create Movie Presentation” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `play` buboréksúgó: „Play Fullscreen Slideshow” — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: acquirepanel.tre:210)
- `websync0` buboréksúgó: „Upload and sync future changes to the web” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: 0x005e0f70)

### `peoplepanel` — 3 hiány · panel-megfeleltetés: `parositva`

Emberek oldalsó panel

- `manual_cancel` „Cancel” (magyarul: „Mégse”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: acquirepanel.tre:210)
- `peoplelist` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: peoplepanel.tre:8)
- `status_label` „Select a folder to display faces” (magyarul: „Válasszon ki egy mappát az arcok megjelenítéséhez”) — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: peoplepanel.tre:8)

### `gedialog` — 3 hiány · panel-megfeleltetés: `parositva`

Google Earth-ös geocímkéző párbeszéd — nálunk a Helyek panel fedi

- `done` „Done” (magyarul: „Kész”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x00853990)
- `next` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x00853990)
- `prev` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x00853990)

### `rightdrawerpanel` — 3 hiány · panel-megfeleltetés: `parositva`

Jobb oldali fiók kerete

- `close` buboréksúgó: „Close this side panel” — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: 0x00632060)
- `size_toggle` buboréksúgó: „Switch between small/large side panel” — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: 0x00632060)
- `title_text` „Metadata” (magyarul: „Metaadatok”) — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: 0x00632060)

### `foldermgr` — 2 hiány · panel-megfeleltetés: `parositva`

Mappakezelő

- `cancel` — 🔧 **lekutatva**, csak nem megépítve (picasa-mappakezelo.md: foldermgr.tre:115)
- `instructions_text` „For each folder, you can choose whether or not to have Picasa find pictures inside it.  You can also pick folders to watch for new pictures.” (magyarul: „Minden mappa esetében megadhatja, hogy a Picasa keressen-e bennük képeket. Kijelölhet egyes mappákat is, és beállíthatja, hogy a program figyelje bennük az új képek megjelenését.”) — 🔧 **lekutatva**, csak nem megépítve (picasa-mappakezelo.md: foldermgr.tre:115)

### `tagpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Címke oldalsó panel

- `input_group` — *bizonytalan*
- `taglist_group` — *bizonytalan*

### `unknownfaceheaderpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Névtelen arcok fejléce

- `showignored` „Show ignored faces” (magyarul: „Mellőzött arcok megjelenítése”) — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: unknownfaceheaderpanel.tre:38)
- `showunknown` „Back to Unnamed” (magyarul: „Vissza ide: Név nélküliek”) — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: unknownfaceheaderpanel.tre:38)

### `instructionpanel` — 2 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Betanító buborék („Learn more…”) — nincs nálunk

- `close` „Close” (magyarul: „Bezárás”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: 0x007d3f90)
- `learn_more` „Learn more...” (magyarul: „További információ...”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0074c760)

### `movieeditpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Videovágó panel

- `export_movie` „Export Clip” (magyarul: „Klip exportálása”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x005952d0)
- `export_youtube` „Upload to YouTube” (magyarul: „Feltöltés a YouTube webhelyre”) — 🔧 **lekutatva**, csak nem megépítve (picasa-feltolteskezelo.md: movieeditpanel.tre:20)

### `activity` — 1 hiány · panel-megfeleltetés: `parositva`

Háttérművelet-jelző a főablak jobb-felső sarkában (#2966); a helye és mérete a respack.yt-ból mérve (#3112)

- `activitybutton` — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: 0x007d3f90)

### `nav` — 1 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Nagyítás-navigátor („floater”) a szerkesztőben — nálunk csak a PhotoViewer nagyítás-állapotgépe van, navigátor-ablak nincs

- `close` — 🔧 **lekutatva**, csak nem megépítve (picasa-bezaras-es-kilepes.md: 0x009cd8a0)

### `uploadallinstructionpanel` — 1 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Feltöltési betanító buborék — nincs nálunk

- `close` „Close” (magyarul: „Bezárás”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: 0x007d3f90)

### `propertiespanel` — 1 hiány · panel-megfeleltetés: `parositva`

Tulajdonságlista a jobb oldali fiókban

- `propertieslist` — *bizonytalan*

### `bigslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `bigslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: editoneup.tre:148)

### `brushslider` — 1 hiány · panel-megfeleltetés: `parositva`

Ecsetméret-csúszka (retusálás)

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (filterdesc-registry.md: thumbui.tre:113)

### `burstslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061778b)

### `durationslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `editslider1` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `editslider` — 🔧 **lekutatva**, csak nem megépítve (kollazs-eletciklus.md: 0x00819f50)

### `editslider2` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `editslider` — *bizonytalan*

### `editslider3` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `editslider` — *bizonytalan*

### `editslider4` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `editslider` — *bizonytalan*

### `flightslider1` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-respack-format.md: scaleslider.tre:1)

### `lengthslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: 0x0061778b)

### `outlineweightslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-ini-format.md: 0x0062d3b0)

### `printborderslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0085d550)

### `scaleslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x00719a44)

### `spacing_slider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `bigslider` — *bizonytalan*

### `textopacityslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-ini-format.md: 0x0062d3b0)

### `timeslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: thumbui.tre:550)

### `toolslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `toolslider` — *bizonytalan*

### `transitionslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `zoomslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

## Megvan, de nem ezen a felületen

Ezeknek a feliratoknak van párja a QML-fánkban, csak **nem a panelhez rendelt fájlokban** — tipikusan a menüsorban vagy egy helyi menüben. A funkció tehát él, de az eredeti panelről hiányzik a hozzáférés.

A bizonyíték minden sornál ott van, mert a rövid feliratok véletlenül is egyezhetnek (a „4 x 6” az eredetiben lappapír-méret, nálunk vágási arány) — a sort a bizonyítékával együtt kell olvasni.

### `makemoviepanel` — 5

- `addclips` — „Get More...” itt: PicasaPy/CollageClipsTab.qml
- `back_color_label` — „Background color” itt: PicasaPy/EditorParamPanel.qml
- `show_captions_label` — „Show Captions” itt: PicasaPy/CollageSettingsTab.qml
- `templatetext` — „Template:” itt: PicasaPy/WebExportDialog.qml
- `text_color_label` — „Text color” itt: PicasaPy/EditorTextPanel.qml

### `publish` — 3

- `deletebackupset` — „Delete Set” itt: PicasaPy/BackupDialog.qml
- `editbackupset` — „Edit Set” itt: PicasaPy/BackupDialog.qml
- `newbackupset` — „New Set” itt: PicasaPy/BackupDialog.qml

### `editpanel` — 1

- `showtextlabel` — „Show Text” itt: PicasaPy/PicasaMenuBar.qml

### `thumbui` — 4

- `albumview` — „Back To Library” itt: PicasaPy/PhotoViewer.qml, PicasaPy/ViewerContextMenu.qml
- `backup` — „Backup” itt: PicasaPy/BackupDialog.qml
- `librarylabel` — „Library” itt: PicasaPy/DocumentTabStrip.qml
- `sbutton` — „Slideshow” itt: PicasaPy/OptionsDialog.qml, PicasaPy/PicasaMenuBar.qml

### `printoptions` — 3

- `border_size_label` — „Border width” itt: PicasaPy/EditorParamPanel.qml
- `usecaption_label` — „Caption” itt: PicasaPy/PicasaMenuBar.qml
- `usefilename_label` — „File name” itt: PicasaPy/PicasaMenuBar.qml

### `capturemoviepanelpopup` — 1

- `stop` — „Stop” itt: Main.qml, PicasaPy/BackupDialog.qml

### `faceheaderpanel` — 1

- `confirmsel` — „Confirm” itt: PicasaPy/CollageDialogs.qml, PicasaPy/DocumentTabStrip.qml

### `buttonmgr` — 5

- `add` — „Add >>” itt: PicasaPy/ConfigureButtonsDialog.qml
- `movedown` — „Move Down” itt: PicasaPy/ConfigureButtonsDialog.qml
- `moveup` — „Move Up” itt: PicasaPy/ConfigureButtonsDialog.qml
- `remove` — „<< Remove” itt: PicasaPy/ConfigureButtonsDialog.qml
- `usedefaults` — „Reset to Defaults” itt: PicasaPy/ConfigureButtonsDialog.qml

### `keywords` — 1

- `keywords_label` — „Tags:” itt: Main.qml, PicasaPy/PicasaMenuBar.qml, PicasaPy/TrayBar.qml

### `panelroot` — 1

- `picasatab` — „Library” itt: PicasaPy/DocumentTabStrip.qml

### `editoneup` — 2

- `bcklabel` — „Exit” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/SlideshowView.qml
- `tllabel` — „Timeline” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/TimelineView.qml

### `oneup` — 2

- `bcklabel` — „Exit” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/SlideshowView.qml
- `tllabel` — „Timeline” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/TimelineView.qml

### `outputlayout` — 1

- `makemovie` — „Movie” itt: PicasaPy/CreateDialogs.qml, PicasaPy/PicasaMenuBar.qml

### `peoplepanel` — 2

- `addname` — „Add a name” itt: PicasaPy/FacesOverlay.qml, PicasaPy/UnnamedFacesView.qml
- `ignore` — „Ignore” itt: PicasaPy/UnnamedFacesView.qml

### `gedialog` — 1

- `tag` — „Geotag” itt: PicasaPy/PicasaMenuBar.qml

### `foldermgr` — 5

- `remove_label` — „Remove from Picasa” itt: PicasaPy/FolderContextMenu.qml, PicasaPy/FolderHierarchyView.qml, PicasaPy/FolderStatePanel.qml
- `scan_once_label` — „Scan Once” itt: PicasaPy/FolderStatePanel.qml
- `status_label` — „For the current folder:” itt: PicasaPy/FolderStatePanel.qml
- `watch_label` — „Scan Always” itt: PicasaPy/FolderStatePanel.qml
- `watched_label` — „Watched Folders” itt: PicasaPy/FolderStatePanel.qml

### `uploadmgr` — 1

- `hide` — „Hide” itt: PicasaPy/PhotoContextMenu.qml, PicasaPy/PicasaMenuBar.qml, PicasaPy/ViewerContextMenu.qml

## A mi többletünk — nálunk van, az eredetiben nincs ilyen szöveg

A QML `qsTr(...)` feliratai, amelyeknek nincs párja sem a `.tre` leltárban, sem a `stringres` szövegtárban. Ez **nem automatikusan hiba**: lehet jogos új funkció (pl. teljesítménymérő) vagy más szóhasználat — de **idegen elemet is jelezhet**, mint a #704-ben a „Kreatív”/„Effektek” fejlécsáv.

Összesen **494 felirat** 91 fájlban.

### Hogyan kell ezt a listát olvasni (#2921)

A tételek **három** csoportba esnek, és csak a harmadik hiba:

1. **saját funkció** — olyasmi, ami az eredetiben nincs (Sötét téma, Teljesítmény-monitor, Duplikátum-kereső). Ezek a `#1187` konvenciója szerint `SAJÁT FUNKCIÓ` jelölőt és sort kapnak a `docs/decisions/vedett-sajat-funkciok.md`-ben.
2. **szükséges segédszöveg** — hibaüzenet, üres-állapot, megerősítő kérdés, aminek azért nincs eredeti párja, mert a helyzet sem áll elő az eredetiben.
3. **valódi eltérés** — az eredetinek VAN szövege ugyanabban a helyzetben, csak mi máshogy fogalmaztuk. Ez javítandó, nem jelölendő; az őre a `tests/app/test_hivatalos_feliratok_3358.py`.

⛔ **A `szükséges segédszöveg` szándékosan NEM kap jelölést** (#2921 döntése). A `SAJÁT FUNKCIÓ` jelölő rendeltetése, hogy egy későbbi „igazítsuk az eredetihez” kör ne törölje ki azt, amit szándékosan építettünk — egy hibaüzenet viszont nem funkció: a jelölés több száz sorral hígítaná a jegyzéket, és épp azt a jelzést oltaná ki, amiért a jegyzék van. Ez a bekezdés azért áll itt, hogy a következő kör ne olvassa végig újra ugyanezt a csoportot.

⚠️ **Ez a lista a közeli-pár mérés BEMENETE** (`eszkozok/meres/felirat_kozeli_parok.py`), tehát a mérés előtt **regeneráld a lapot**. Mérve 2026-09-20: a lista még hozta az „Add Tag to Entire Selection” tételt, amit a #3358 addigra kijavított — az elavult bemenet nem létező feliratokat soroltat be.

**Amit a korábbi körök már KIZÁRTAK** (magas hasonlóság ≠ azonos tétel; ne mérd újra):

- **téma-előtagos nevek** (`collage::grid_desc` és társai) — a név az erőforrás-azonosító része, nem felirat;
- **vezető `\n\n`** (SaveDialogs) — ugyanaz a szöveg, csak tördeléssel;
- **platform-változatok** (`CInitialScanDialog::OnlySearchWin`);
- **véletlen szóátfedés** és **más szerepű pár**: pl. a `FolderPane` „Folders on Disk” felirata 0,97-tel illeszkedik a `CAcquireUI::folderondisk` EGYES számú „Folder on Disk”-jére, ami az eredetiben a gyűjtemény alapértelmezett NEVE — ez nem bizonyítható eltérés.

### `Main.qml` — 24

- „No pictures have that tag.”
- „The search results could not be saved as an album.”
- „Background work is still running (export, web export or ”
- „Exit PicasaPy”
- „There are no files on the clipboard to paste.”
- „This will create an album with more than 1000 images.”
- „You are about to erase all geographic location information”
- „Change Location”
- „You have more than a few items selected.”
- „This will remove all edits you have made to the”
- „This will remove all edits you have made to ALL of”
- „Red eye fixes have been applied. If you”
- „Clear Sample”
- „Duplicate Files”
- „Looking for duplicate files...”
- „Updating similarity database ”
- „Do you want to stop the operation running in the background?”
- „Stop the background operation”
- „This folder is currently unavailable (for example a disconnected drive or network share). Its photos stay in the database and thumbnails come from the cache, but the original files cannot be opened or edited right now.”
- „Picasa had a problem loading this file(s). Would you ”
- „New person's name:”
- „Wrong password”
- „The password does not match. The hidden folders stay hidden.”
- „WARNING! This will move all the faces back to the ”

### `PicasaPy/ExportDialogs.qml` — 22

- „Export to Folder”
- „Preserves original image quality”
- „Good balance of quality and size”
- „Very large file size, preserves fine detail”
- „Smallest file size, some quality loss”
- „Maximum”
- „Minimum”
- „Export location:”
- „Browse...”
- „Name of exported folder:”
- „Add numbers to file names to preserve order”
- „Use original size”
- „Resize to:”
- „pixels”
- „Image quality:”
- „Export movies using:”
- „First frame”
- „Full movie (no resizing)”
- „Watermark:”
- „Add watermark”
- „Stamp photos with your name, a web domain, or a copyright notice.”
- „None of the selected pictures has a location, so no Google Earth file was written.”

### `PicasaPy/OptionsTabGeneral.qml` — 22

- „User interface:”
- „Use special effects”
- „Show tooltips”
- „Single click to exit the editing view”
- „Language:”
- „English”
- „Files:”
- „Detect duplicates on import”
- „Clear Cache...”
- „Empty the thumbnail cache? The thumbnails are ”
- „Empty”
- „Keep”
- „Delete from disk without confirmation”
- „Remove from album without confirmation”
- „Help improve PicasaPy:”
- „Send anonymous usage statistics”
- „Automatic updates:”
- „Update automatically”
- „Prompt before downloading updates”
- „Never check for updates”
- „Import destination folder:”
- „Browse...”

### `PicasaPy/PicasaMenuBar.qml` — 19

- „TEST MODE — logging startup”
- „Undo Paste All Effects”
- „Undo Batch Edit”
- „Dark Theme”
- „Recent &changes”
- „Show”
- „New Movie...”
- „Find Faces...”
- „Manage Duplicates...”
- „Compact Database...”
- „Language”
- „English”
- „Import from Picasa...”
- „Online Information”
- „Product Release Notes”
- „Performance Monitor”
- „Test Mode (logs the next startup)”
- „Send Log...”
- „About PicasaPy”

### `PicasaPy/CreateDialogs.qml` — 16

- „Select pictures in the library first, or put them in the Picture Tray.”
- „Collage type:”
- „Mosaic”
- „Frame Mosaic”
- „Grid”
- „Multiple Exposure”
- „Target file:”
- „(not selected)”
- „Browse...”
- „JPEG images (*.jpg)”
- „The movie's pictures and timing come from the ”
- „Video size:”
- „Seconds per picture:”
- „MP4 videos (*.mp4)”
- „The collage could not be created.”
- „The movie could not be created.”

### `PicasaPy/PrintDialog.qml` — 16

- „Printing is unavailable: the Qt print support ”
- „No pictures to print.”
- „Choose the target file.”
- „Layout:”
- „One picture per page”
- „Columns:”
- „Print size:”
- „Copies of each picture:”
- „Please review before printing.”
- „Print to a PDF file...”
- „(not selected)”
- „Browse...”
- „Fit to page:”
- „Whole picture”
- „Fill the page (crop)”
- „PDF documents (*.pdf)”

### `PicasaPy/DedupDialog.qml` — 15

- „Find Duplicates”
- „Select at least two pictures in the grid, or pick another scope.”
- „Comparing files...”
- „Analysing pictures...”
- „Searching...”
- „Groups of duplicate and similar pictures. Pick which one to ”
- „Search in:”
- „Selected pictures (none)”
- „This folder and its subfolders”
- „Whole library”
- „Scan for Duplicates”
- „Searching the whole library reads every picture — with tens ”
- „No duplicates found.”
- „Move others to \"Duplikátumok\"”
- „Delete others to Trash”

### `PicasaPy/BackupDialog.qml` — 14

- „All file types”
- „All pictures (no movies)”
- „Only JPEGs with camera data”
- „Everything was already backed up.”
- „Choose the backup location”
- „A backup set remembers where it saves and what it has ”
- „No backup sets yet.”
- „Save to:”
- „Browse...”
- „Files:”
- „Delete this backup set? The saved files stay ”
- „To folder”
- „To CD image (ISO)”
- „To DVD image (ISO)”

### `PicasaPy/ImportSourceDialog.qml` — 14

- „Import from Source”
- „bytes”
- „Import pictures and videos from another folder (e.g. a ”
- „(none selected)”
- „Recent sources”
- „Browse...”
- „Exclude Duplicates”
- „No pictures or videos found in this folder.”
- „Recent destinations”
- „Enter new folder title or choose existing folder to continue”
- „Import into separate folders for each date taken”
- „Import into folder with today's date”
- „Choose source folder...”
- „Choose destination folder...”

### `PicasaPy/PhotoViewer.qml` — 13

- „Edit the movie presentation”
- „Show only one picture”
- „Show two different pictures”
- „Show the same picture twice”
- „Switch focus between the pictures”
- „Start slideshow”
- „Retouch fixes cannot be recovered with redo.”
- „Redeye fixes cannot be recovered with redo.”
- „The caption will replace the text you have ”
- „Video playback requires the Qt Multimedia module.”
- „Render the final collage from this draft”
- „Show Faces”
- „Edit Faces”

### `PicasaPy/EditorParamPanel.qml` — 12

- „Inner Radius”
- „Center X”
- „Center Y”
- „Preserve Color”
- „Gradient”
- „Block Size”
- „Blur Radius”
- „Color Mix”
- „Edge Strength”
- „Smoothness”
- „Width”
- „Line Position”

### `PicasaPy/InitialScanDialog.qml` — 11

- „There is an older version of Picasa installed.  Would you like to update your existing picture library, or search your computer for pictures again?”
- „Picasa is ready to search for pictures on your computer”
- „Update my existing picture library”
- „Only search Documents, Pictures, and the Desktop”
- „Choose this option if you use keywords or custom albums in Picasa 1, and you want to preserve these in Picasa 3.”
- „Choose this option if you only store your pictures in these folders.”
- „Search my computer for pictures again”
- „Search my whole computer for pictures”
- „Choose this option for a more complete search of your computer, which includes extended picture information.  It will preserve your existing edits and organization, but it will not preserve keywords.  This search may take several minutes.”
- „Choose this option if you have pictures stored in various folders across your computer, especially if you have pictures stored on more than one hard drive.”
- „Searching for pictures never moves or copies files to new locations. You can choose which folders are displayed by Picasa by using the Folder Manager tool (available from the Tools menu)”

### `PicasaPy/OptionsTabNetwork.qml` — 11

- „Proxy username (Windows only):”
- „Proxy password:”
- „Automatically detect network settings”
- „Network logging level:”
- „Disable logging”
- „Log errors only”
- „Minimal log information”
- „Detailed log information”
- „Log all network information”
- „Log file:”
- „Browse...”

### `PicasaPy/CollageThemePopup.qml` — 10

- „Looks like a pile of scattered pictures”
- „Mosaic”
- „Automatically fit pictures into the page”
- „Frame Mosaic”
- „A mosaic with a prominent center picture”
- „Grid”
- „Arrange pictures into regular rows and columns”
- „Thumbnails with an informative header”
- „Multiple Exposure”
- „Superimpose pictures over one another”

### `PicasaPy/FaceScanDialog.qml` — 10

- „Find Faces”
- „Search cancelled. The faces found so far are kept.”
- „Grouping cancelled. The groups made so far are kept.”
- „PicasaPy goes through the pictures of your library and looks ”
- „Searching...”
- „Download the model”
- „Downloading the model...”
- „As a second step PicasaPy can compare the faces it found and ”
- „Grouping...”
- „Group Faces”

### `PicasaPy/MoveDatabaseDialog.qml` — 10

- „Move Database”
- „Move the photo index and thumbnail cache to a new folder. ”
- „Network drives (e.g. a NAS) are fully supported and are ”
- „Current database location:”
- „New database location:”
- „(none selected)”
- „Browse...”
- „PicasaPy will move the database the next time it starts.”
- „Move on next restart”
- „Cancel the move”

### `PicasaPy/OptionsTabEmail.qml` — 10

- „Mail program:”
- „Use this computer's default email program”
- „Let me choose each time I send a picture”
- „Use my Google Account”
- „Multiple photo size”
- „Single picture size:”
- „Send movies as:”
- „First frame”
- „Full movie”
- „Send embedded pictures and captions (Outlook only)”

### `PicasaPy/WebExportDialog.qml` — 10

- „Page title:”
- „Save to:”
- „(not selected)”
- „Browse...”
- „Thumbnail size:”
- „Picture size:”
- „Shadow thumbnails”
- „Shadow pictures”
- „PicasaPy is generating the web page.”
- „Choose target folder...”

### `PicasaPy/EditorTextPanel.qml` — 9

- „Type your text, then click on the photo to place it.”
- „B”
- „I”
- „U”
- „Align left”
- „Align center”
- „Align right”
- „Outline color”
- „Outline thickness”

### `PicasaPy/PublishPanel.qml` — 9

- „Selection and Settings”
- „Photo Size”
- „Name the Gift CD”
- „CD Name”
- „Limit 16 Characters”
- „Include Picasa”
- „Erase Media”
- „Visibility:”
- „Sync:”

### `PicasaPy/EditorTabBar.qml` — 8

- „Common Fixes”
- „Fine Tuning”
- „Effects”
- „Creative”
- „More Effects”
- „Glimmer effects beyond the three known tabs”
- „Legacy Effects”
- „Filters left in the Picasa engine but not on its surface”

### `PicasaPy/HiddenPasswordDialog.qml` — 8

- „Password for hidden folders”
- „Hidden folders are locked”
- „Enter a password to use for the hidden folders.”
- „Enter the password to show the hidden folders.”
- „Type the password again”
- „Stronger protection (Picasa cannot open it)”
- „Remove the password”
- „This only hides the folders inside PicasaPy. The files ”

### `PicasaPy/SaveDialogs.qml` — 8

- „A backup of this file will be made.”
- „A backup of these files will be made.”
- „JPEG Files (*.jpg)”
- „WebP Files (*.webp)”
- „Saving writes the picture without them, and the settings are lost. This cannot be undone.”
- „This cannot be undone and all changes will be lost.”
- „To undo the last save and keep edits click 'Undo Save'.”
- „File operation failed”

### `PicasaPy/FileOpsDialogs.qml` — 7

- „Please enter a new name for these files:”
- „Include in filename:”
- „Image resolution”
- „Move to Folder...”
- „This file cannot be moved to the Trash and will be deleted immediately. This cannot be undone.”
- „File operation failed”
- „File operation finished”

### `PicasaPy/OptionsTabWebAlbums.qml` — 7

- „Default upload size:”
- „Upload previews first for large files”
- „Keep original picture quality (uses more storage)”
- „Sync starred photos only”
- „Don't confirm each sync (use previous settings)”
- „Upload name tags”
- „Add a watermark to all photo uploads:”

### `PicasaPy/PicasaImportDialog.qml` — 7

- „Import from Picasa”
- „Looking for a previous Picasa installation…”
- „We found your previous Picasa installation. It ”
- „We couldn't find a previous Picasa installation ”
- „Browse manually...”
- „Not now”
- „Adopt”

### `PicasaPy/TrayBar.qml` — 7

- „Waiting for the collage to be created…”
- „This will clear your entire tray.”
- „Loupe — drag over the photos”
- „Order Prints (service discontinued)”
- „Publish to Blogger (service discontinued)”
- „Click here for more options”
- „Select the items you want to add to the ”

### `PicasaPy/CollageDialogs.qml` — 6

- „The collage could not be saved”
- „The collage cannot be saved because all of the pictures ”
- „The current page format of the collage does not ”
- „Would you like to replace the existing one, or ”
- „The current collage contains unsaved changes.\n\n”
- „Please select the single image you want to place in ”

### `PicasaPy/OptionsTabNameTags.qml` — 6

- „Enable face detection”
- „Enable suggestions:”
- „Suggestion threshold:”
- „Clustering threshold:”
- „Store name tags in the file”
- „Upload contact thumbnails to Google Contacts”

### `PicasaPy/OptionsTabPrinting.qml` — 6

- „Available print sizes:”
- „Use high resolution previews (slower)”
- „Printer quality (Windows only):”
- „Resizing algorithm quality:”
- „General (Lanczos-3)”
- „Very sharp (Lanczos-8)”

### `PicasaPy/EditorCropPanel.qml` — 5

- „Select a dimension below and then click and drag on the ”
- „This image's orientation has been modified by the ”
- „Delete this custom aspect ratio?”
- „Suggested crops”
- „Top left”

### `PicasaPy/EditorPanel.qml` — 5

- „Close crop to faces”
- „Compose around faces”
- „Crop by horizon”
- „Crop by color”
- „Crop by detail”

### `PicasaPy/FolderManagerDialog.qml` — 5

- „Watching an entire drive can slow down the system. ”
- „If you remove this folder, new items that you add to ”
- „Choose which folders PicasaPy watches. New and changed ”
- „Folder Manager — Help”
- „Scan Always keeps watching the folder: pictures you add ”

### `PicasaPy/FolderPropertiesDialog.qml` — 5

- „Automatic date”
- „Enter the date as YYYY-MM-DD.”
- „Use music for Slideshow and Movie presentation:”
- „Place taken (optional):”
- „Description (optional):”

### `PicasaPy/PhotoContextMenu.qml` — 5

- „Add to People Album”
- „Find Similar Pictures”
- „File on Disk”
- „Locate Original on Disk”
- „Block Upload”

### `PicasaPy/UnnamedFacesView.qml` — 5

- „Stop ignoring”
- „Move the selected people to the ignored ”
- „Look for more suggestions”
- „Lowers the recognition threshold once, so more names are ”
- „Are you sure you want to move this person to the ”

### `PicasaPy/CollageActionRow.qml` — 4

- „Select all the pictures (Ctrl+A)”
- „Deselect all the pictures (Ctrl+D)”
- „Remove selected items from the collage (Del)”
- „Use the selected picture as the background”

### `PicasaPy/CollageDraftDialog.qml` — 4

- „Recovered Auto Backup”
- „PicasaPy found an automatically saved collage draft ”
- „Restore Draft”
- „Discard Draft”

### `PicasaPy/EditOverwriteDialog.qml` — 4

- „Edits overwritten by another program”
- „Another program changed these pictures and removed the edits you made here:”
- „While the same folder is open in Picasa, its changes overwrite the edits made here. Restoring writes your edits back.”
- „Restore edits”

### `PicasaPy/EditorLegacyTab.qml` — 4

- „These filters come from older Picasa versions.”
- „Today's Picasa only recognises them inside your old edits.”
- „This name is a leftover from an old configuration. Picasa 3.9 has no processor for it either, so it cannot be applied.”
- „Picasa can read this filter from an old .picasa.ini, but its exact pixel operation has not been decoded yet, so it cannot be applied.”

### `PicasaPy/EditorRedeyePanel.qml` — 4

- „Click, hold, and drag the mouse around each eye separately ”
- „Note: click inside the box to undo the change.”
- „Picasa has found and corrected red eye(s).”
- „No red eye was found automatically.”

### `PicasaPy/MainToolbar.qml` — 4

- „Folder view options”
- „Show duplicate files only”
- „Search”
- „Kiadások megtekintése a GitHubon”

### `PicasaPy/OptionsTabSlideshow.qml` — 4

- „Loop slideshow”
- „Play MP3 music during slideshow”
- „Select a music folder:”
- „Browse...”

### `StartupRelocateWindow.qml` — 4

- „Moving the database”
- „PicasaPy is moving the database.”
- „Photo index…”
- „Thumbnail cache…”

### `PicasaPy/CollageSettingsTab.qml` — 3

- „Landscape: orient the collage horizontally”
- „Portrait: orient the collage vertically”
- „Show picture captions as text on pictures with the ”

### `PicasaPy/CompactDatabaseDialog.qml` — 3

- „PicasaPy is compacting its database to save disk ”
- „The database is already compact — nothing to do.”
- „Compacting cancelled. Your database is unchanged.”

### `PicasaPy/EditorDialogs.qml` — 3

- „This file is read only. In order to edit this file, ”
- „The automatic copy is not available yet. To edit this ”
- „Due to a disk error. The disk may be full or read-only.”

### `PicasaPy/EditorFinetunePanel.qml` — 3

- „One-click lighting fix”
- „Pick a neutral gray or white area of the photo to”
- „One-click color fix”

### `PicasaPy/EmailChoiceDialog.qml` — 3

- „Send pictures by email”
- „The pictures will be attached to a new message in ”
- „Remember this choice and do not ask again”

### `PicasaPy/HelpDialog.qml` — 3

- „Back”
- „Contents”
- „Search in help”

### `PicasaPy/OptionsDialog.qml` — 3

- „Printing”
- „Network”
- „Name Tags”

### `PicasaPy/OptionsTabFileTypes.qml` — 3

- „In addition to JPEG, also show these file types:”
- „RAW”
- „Supported Formats”

### `PicasaPy/PeoplePanel.qml` — 3

- „Named people who appear with the currently ”
- „People who appear in the currently selected ”
- „No people have been found yet. As faces are ”

### `PicasaPy/PicasaDataImportDialog.qml` — 3

- „Import from Picasa”
- „No Picasa data found on this computer.”
- „Copying names, keywords and places from Picasa...”

### `PicasaPy/QuickTagsConfigDialog.qml` — 3

- „Edit the 10 quick tag buttons shown at the bottom of the ”
- „Reserve the top two buttons for recently used tags”
- „Fill the empty boxes above with frequently used tags”

### `PicasaPy/AboutDialog.qml` — 2

- „About PicasaPy”
- „A modern, open Picasa successor.”

### `PicasaPy/CollageClipsTab.qml` — 2

- „Load more pictures from the library”
- „Remove the selected pictures from the tray”

### `PicasaPy/CollagePanel.qml` — 2

- „Create the collage and set it as the desktop background”
- „Save as a JPG in the Collages album (in the Projects ”

### `PicasaPy/ConfigureButtonsDialog.qml` — 2

- „Available buttons:”
- „Current buttons:”

### `PicasaPy/EditorRetouchPanel.qml` — 2

- „Click to select the area to fix. Then, move the mouse to ”
- „Refining…”

### `PicasaPy/FolderPane.qml` — 2

- „Currently unavailable — the folder stays in the database, thumbnails come from the cache.”
- „Folders on Disk”

### `PicasaPy/LightboxHeader.qml` — 2

- „Remove all suggestions”
- „Lower the recognition threshold to get more suggestions”

### `PicasaPy/PerfMonitorPanel.qml` — 2

- „Performance monitor”
- „Save diagnostics...”

### `PicasaPy/PicasaNotifier.qml` — 2

- „The collage is ready (click here)”
- „Copy saved”

### `PicasaPy/PicasaScrollBar.qml` — 2

- „Previous album”
- „Next album”

### `PicasaPy/PlacesPanel.qml` — 2

- „The map component (QtLocation) is not available. Geotags can still be edited.”
- „Right-click the map to place the selected pictures.”

### `PicasaPy/RightDrawer.qml` — 2

- „Switch between the small and large side panel”
- „Close side panel”

### `PicasaPy/SlideshowView.qml` — 2

- „Display Time”
- „ s”

### `PicasaPy/TagContextMenu.qml` — 2

- „Find Items Tagged This Way”
- „Remove Tag”

### `PicasaPy/TagsPanel.qml` — 2

- „Add a tag...”
- „Select pictures to tag them.”

### `PicasaPy/TesztuzemNaploDialog.qml` — 2

- „Save Log As...”
- „Text Files”

### `PicasaPy/ActivityBadge.qml` — 1

- „Stop the background operation”

### `PicasaPy/AddCustomAspectRatioDialog.qml` — 1

- „Width:”

### `PicasaPy/CollageBorderPicker.qml` — 1

- „Polaroid Camera”

### `PicasaPy/CollageContextMenus.qml` — 1

- „Polaroid Camera”

### `PicasaPy/CollageDoneNotice.qml` — 1

- „The collage is ready (click here)”

### `PicasaPy/CollageFormatMenu.qml` — 1

- „You can select the relative width and height of ”

### `PicasaPy/DocumentTabStrip.qml` — 1

- „The current collage contains unsaved changes.\n\n”

### `PicasaPy/FacesOverlay.qml` — 1

- „Drag a rectangle over the face you want to add, then ”

### `PicasaPy/FolderContextMenu.qml` — 1

- „&Manual order”

### `PicasaPy/FolderStatePanel.qml` — 1

- „Select a folder on the left.”

### `PicasaPy/HistogramBox.qml` — 1

- „Histogram and camera information”

### `PicasaPy/ImportProgressPanel.qml` — 1

- „Importing”

### `PicasaPy/LightboxFeed.qml` — 1

- „No photos found”

### `PicasaPy/NewCollectionDialog.qml` — 1

- „Collection name:”

### `PicasaPy/PicasaMenuItem.qml` — 1

- „This is a PicasaPy addition — the original Picasa did not have it.”

### `PicasaPy/PropertiesPanel.qml` — 1

- „Select a picture to see its properties.”

### `PicasaPy/SplashScreen.qml` — 1

- „Please note: PicasaPy is still a work in ”

### `PicasaPy/TimelineView.qml` — 1

- „No pictures yet”

### `PicasaPy/VideoPlayerView.qml` — 1

- „Unable to play this video.”

### `PicasaPy/ViewerContextMenu.qml` — 1

- „Block Upload”

## Figyelmeztetések a generáláskor

- 18 elem LEVÉLNEVE megvan horgonyzott szakaszban, a TELJES neve viszont nem — a mérés ezért »feltáratlan«-nak látja (#2504). Írd ki a teljes nevet:
-     collagepanel/action_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     collagepanel/landscape :: kollazs-atvilagitas.md: 0x00cbf878
-     collagepanel/portrait :: kollazs-atvilagitas.md: 0x00cbf878
-     collagepanel/rand_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     collagepanel/snap_rotation_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     collagepanel/z_order_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     editpanel/fx12_adorn :: filterdesc-registry.md: 0x00d67f68
-     headerpanel/album_description :: picasa-arcfelismeres.md: faceheaderpanel.tre:125
-     headerpanel/save_edits :: picasa-arcfelismeres.md: 0x005e0f70
-     headerpanel/title_fade0 :: picasa-arcfelismeres.md: faceheaderpanel.tre:125
-     keywords/thumbnail :: picasa-keptalca.md: 0x007224f0
-     makemoviepanel/addclips-label :: kollazs-panel-ui-spec.md: 0x0082dcec
-     moviecontrols/moviecontrols :: picasa-create-features.md: 0x0061e4e3
-     panelroot/acquirepanel :: binaris-regeszet-modszertan.md: acquirepanel.tre:210
-     printpanel/previewlabel :: picasa-importalas.md: 0x0051f070
-     … és még 3 elem
- 14 szakasz elemet ír le, de HORGONY NÉLKÜL — a mérés átugorja, tehát az ott leírt elemek »feltáratlan«-ként jelennek meg (22.4, #38):
-     szerkeszto-panel-meretek.md :: ### A fa és a kényszerek (6 elem)
-     szerkeszto-panel-meretek.md :: ### Amit ez kimond (6 elem)
-     binaris-regeszet-modszertan.md :: #### Ami SZÁNDÉKOSAN horgony nélkül marad — 4 szakasz (5 elem)
-     ui-audit-editor.md :: ### A szülő-lánc, sorszámmal (5 elem)
-     picasa-menu-parancsok-viselkedes.md :: ### Amit KIZÁRTAM (2 elem)
-     ui-audit-mainwindow.md :: ### Az öt szűrőgomb — mind az öt BETŰRE azonos szerkezet (2 elem)
-     binaris-regeszet-modszertan.md :: #### MÉRŐ-HIBA 1: a ```-kerítésen belüli `#` sor szakaszt nyitott (1 elem)
-     picasa-mappanezet.md :: ## 9. Amit KIZÁRTAM (1 elem)
-     picasa-megjelenitesi-modok.md :: ### 13.1 A súgószövegek helye és KULCSOLÁSA (1 elem)
-     picasa-megjelenitesi-modok.md :: ### 13.2 ⭐ A döntő próba: NULLA menü-szerű kulcs (1 elem)
-     picasa-menu-parancsok-viselkedes.md :: ### Amit KIZÁRTAM (1 elem)
-     picasa-menu-parancsok-viselkedes.md :: ### Amit KIZÁRTAM (1 elem)
-     ui-audit-editor.md :: #### A gomb HELYE és a gomb RAJZA nem ugyanaz — 132 × 28 kontra 130 ×  (1 elem)
-     ui-audit-editor.md :: ### Két helyesbítés a 4.2 forrásmegjelöléséhez (1 elem)
- ELAVULT ELEM-FELÜLBÍRÁLÁS: 'printpanel/photoindexbutton' nincs a leltárban
- GYANÚS »nem cél«: 'acquirepanel/add_groups_button' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'acquirepanel/selected_groups_label' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'acquirepanel/share_with_label' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'acquirepanel/upload_label' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'uploadmgr/cleanup' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'uploadmgr/itemlist' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'uploadmgr/minibutton' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'uploadmgr/pause' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'uploadmgr/resume' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- GYANÚS »nem cél«: 'uploadmgr/throttlechk' neve SZEREPEL a binárisban — a kód ismeri, tehát nem kivett funkció maradványa. A »nem cél« itt elnémítás; ellenőrizd az indokot.
- ÁTSOROLVA (#1970): 124 elem a `bizonytalan`-ból `lekutatva`-ra — a specek CÍMMEL megnevezik őket, tehát a kézi döntés megszületett.

