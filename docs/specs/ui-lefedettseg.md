# UI-lefedettség — az eredeti Picasa panelei ↔ a PicasaPy QML-fája

**Generálva:** 2026-09-02 — **ezt a fájlt ne írd kézzel**, újragenerálható.

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

Elem-státuszok: `parositva`, `masutt-megvan` (a felirat nem a panelhez rendelt QML-ekben van, hanem a fa más pontján — tipikusan a menüsorban; vagyis a funkció megvan, de **nem ezen a felületen**), `hianyzik`, `bizonytalan` (vezérlő-gyanús, de nem dönthető el gépi úton — kézi felülbírálásra vár), `nem-ertekelheto` (rajzoló elem).

**A `hianyzik` óvatosan olvasandó:** azt jelenti, hogy az eredeti elem felirata/azonosítója nem található a panelhez rendelt QML-fájljainkban. Ha a funkció nálunk máshogy hívódik, az elem-felülbírálás CSV-be kell felvenni — ez a tábla karbantartásának a rendes menete.

## Összesítés

| mutató | darab |
|---|---:|
| eredeti UI-elem összesen | 2020 |
| panel összesen | 74 |
| ebből értékelhető elem (`feliratos` + `vezerlo`) | 733 |
| párosítva | 174 |
| másutt megvan (nem ezen a felületen) | 47 |
| hiányzik | 364 |
| bizonytalan | 150 |
| nem értékelhető (rajzoló elem) | 1285 |
| **lefedettség az értékelhető elemeken** | **23.7%** |

## Rangsor — a tíz legnagyobb fehér folt

Jegynyitáshoz ez a sorrend: a hiányzó és a bizonytalan elemek száma panelenként.

| # | panel | hiány + bizonytalan | mit takar |
|---:|---|---:|---|
| 1 | `editpanel` | 61 | A szerkesztő teljes bal oldali panelje minden fülével |
| 2 | `makemoviepanel` | 49 | Csak a filmkészítő párbeszéd van meg; interaktív filmkészítő panel nincs |
| 3 | `thumbui` | 33 | A fő könyvtárnézet egésze |
| 4 | `publish` | 30 | Biztonsági mentés / Ajándék-CD / webre töltés — nincs nálunk |
| 5 | `printpanel` | 25 | Nyomtatási panel és előnézet — nálunk csak a tálca „Print” indítógombja van meg |
| 6 | `printoptions` | 22 | Nyomtatási keret/felirat beállítások — nincs nálunk (a Beállítások „Nyomtatás” füle más panel) |
| 7 | `upload` | 21 | Picasa Web Albums feltöltő párbeszéd — nincs nálunk |
| 8 | `buzzupload` | 21 | Google Buzz feltöltés — a szolgáltatás megszűnt, nem cél |
| 9 | `compose_share` | 16 | Megosztási meghívó szerkesztő — nincs nálunk |
| 10 | `quicktagconfig` | 13 | Gyorscímke-beállító |

## Panelenkénti lefedettség

| panel | eredeti elem | értékelhető | párosítva | másutt | hiányzik | bizonytalan | rajzoló | megfeleltetés |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `editpanel` | 312 | 125 | 58 | 6 | 21 | 40 | 187 | `EditorPanel.qml`, `EditorTabBar.qml`, `EditorTabCommonFixes.qml`, `EditorFinetunePanel.qml`, `EditorEffectsTab1.qml`, `EditorEffectsTab2.qml`, `EditorEffectsTab3.qml`, `EditorEffectsTab4.qml`, `EditorLegacyTab.qml`, `EditorCropPanel.qml`, `EditorRedeyePanel.qml`, `EditorRetouchPanel.qml`, `EditorParamPanel.qml`, `EditorDialogs.qml`, `EditTabButton.qml`, `EditTabIcon.qml`, `CropOverlay.qml`, `HistogramBox.qml`, `AddCustomAspectRatioDialog.qml`, `EditOverwriteDialog.qml`, `BatchEditProgressPanel.qml`, `ToolTile.qml` |
| `makemoviepanel` | 111 | 55 | 1 | 5 | 34 | 15 | 56 | `CreateDialogs.qml` |
| `thumbui` | 140 | 46 | 10 | 3 | 22 | 11 | 94 | `MainToolbar.qml`, `LightboxFeed.qml`, `ThumbDelegate.qml`, `TrayBar.qml`, `TimelineView.qml`, `PicasaScrollBar.qml`, `FolderPane.qml`, `FolderTreeItem.qml`, `FolderStateBadge.qml`, `SlideshowView.qml`, `Main.qml` |
| `publish` | 125 | 30 | 0 | 0 | 30 | 0 | 95 | **nincs-megfeleltetes** — Biztonsági mentés / Ajándék-CD / webre töltés — nincs nálunk |
| `printpanel` | 73 | 33 | 0 | 8 | 25 | 0 | 40 | **nincs-megfeleltetes** — Nyomtatási panel és előnézet — nálunk csak a tálca „Print” indítógombja van meg |
| `printoptions` | 49 | 29 | 0 | 7 | 22 | 0 | 20 | **nincs-megfeleltetes** — Nyomtatási keret/felirat beállítások — nincs nálunk (a Beállítások „Nyomtatás” füle más panel) |
| `upload` | 61 | 21 | 0 | 0 | 21 | 0 | 40 | **nincs-megfeleltetes** — Picasa Web Albums feltöltő párbeszéd — nincs nálunk |
| `buzzupload` | 55 | 22 | 0 | 1 | 21 | 0 | 33 | **nem-cel** — Google Buzz feltöltés — a szolgáltatás megszűnt, nem cél |
| `compose_share` | 49 | 16 | 0 | 0 | 16 | 0 | 33 | **nincs-megfeleltetes** — Megosztási meghívó szerkesztő — nincs nálunk |
| `quicktagconfig` | 33 | 15 | 3 | 0 | 2 | 11 | 17 | `QuickTagsConfigDialog.qml` |
| `buttonmgr` | 29 | 13 | 0 | 0 | 13 | 0 | 16 | **nincs-megfeleltetes** — Gombsáv-testreszabó párbeszéd — nincs nálunk |
| `choose_mail` | 24 | 13 | 0 | 0 | 13 | 0 | 11 | **nincs-megfeleltetes** — Levelezőprogram-választó párbeszéd — nincs nálunk |
| `acquirepanel` | 67 | 24 | 12 | 0 | 7 | 5 | 43 | `PicasaImportDialog.qml`, `ImportSourceDialog.qml`, `ImportProgressPanel.qml`, `ImportDropArea.qml` |
| `faceheaderpanel` | 39 | 13 | 0 | 1 | 12 | 0 | 26 | `LightboxHeader.qml`, `UnnamedFacesView.qml`, `FacesOverlay.qml`, `PeopleAlbumContextMenu.qml` |
| `capturemoviepanelpopup` | 45 | 12 | 0 | 1 | 11 | 0 | 33 | **nincs-megfeleltetes** — Webkamerás videofelvétel — nincs nálunk |
| `edittextpanel` | 45 | 19 | 9 | 0 | 8 | 2 | 26 | `EditorTextPanel.qml`, `TextColorSwatches.qml` |
| `compose_mail` | 41 | 10 | 0 | 0 | 10 | 0 | 31 | **nincs-megfeleltetes** — Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül |
| `collab` | 23 | 10 | 0 | 0 | 10 | 0 | 13 | **nem-cel** — Picasa Web Albums közös album — a szolgáltatás megszűnt, nem cél |
| `headerpanel` | 30 | 11 | 3 | 0 | 8 | 0 | 19 | `LightboxHeader.qml` |
| `collagepanel` | 108 | 55 | 48 | 0 | 0 | 7 | 53 | `CreateDialogs.qml`, `CollagePanel.qml`, `CollagePanelTabBar.qml`, `CollagePanelTabButton.qml`, `CollageSettingsTab.qml`, `CollageClipsTab.qml`, `CollageActionRow.qml`, `CollageZOrderColumn.qml`, `CollageSnapColumn.qml`, `CollageRandomRow.qml`, `CollageContextMenus.qml`, `CollageCanvas.qml`, `CollageFormatMenu.qml`, `CollageThemePopup.qml`, `CollageBorderPicker.qml`, `CollageBackgroundBox.qml`, `CollageNode.qml`, `CollageGroupNode.qml`, `CollageSheet.qml`, `CollageRing.qml`, `CollageProgressOverlay.qml`, `CollageDialogs.qml`, `CollageDraftDialog.qml`, `CollageDoneNotice.qml` |
| `titledialog` | 18 | 7 | 0 | 0 | 7 | 0 | 11 | **nincs-megfeleltetes** — Filmes címdia-szerkesztő párbeszéd — nincs nálunk |
| `searchcontainer` | 25 | 11 | 5 | 0 | 3 | 3 | 14 | `MainToolbar.qml`, `SearchSuggestions.qml` |
| `video_control_bar` | 24 | 6 | 0 | 0 | 3 | 3 | 18 | `VideoPlayerView.qml` |
| `keywords` | 18 | 7 | 1 | 0 | 5 | 1 | 11 | `TagsPanel.qml` |
| `uploadmgr` | 17 | 7 | 0 | 1 | 6 | 0 | 10 | **nincs-megfeleltetes** — Feltöltés-kezelő (szüneteltetés/folytatás) — nincs nálunk |
| `searchoptions` | 9 | 6 | 0 | 0 | 2 | 4 | 3 | `SearchGroupHeader.qml`, `MainToolbar.qml` |
| `canoncapturemoviepanelpopup` | 45 | 5 | 0 | 0 | 5 | 0 | 40 | **nem-cel** — Canon SDK-s kamerafelvétel — nem cél |
| `geopanel` | 14 | 5 | 0 | 0 | 1 | 4 | 9 | `PlacesPanel.qml`, `PlacesMap.qml` |
| `outputlayout` | 31 | 9 | 4 | 1 | 4 | 0 | 22 | `TrayBar.qml` |
| `initialscan` | 18 | 4 | 0 | 0 | 0 | 4 | 14 | `InitialScanDialog.qml` |
| `video_control_bar2` | 18 | 4 | 0 | 0 | 2 | 2 | 14 | `VideoPlayerView.qml` |
| `panelroot` | 14 | 7 | 2 | 1 | 2 | 2 | 7 | `Main.qml`, `MainToolbar.qml` |
| `throttle` | 10 | 4 | 1 | 0 | 0 | 4 | 5 | `PicasaScrollBar.qml` |
| `movieeditpanel` | 7 | 4 | 0 | 0 | 4 | 0 | 3 | `VideoPlayerView.qml` |
| `editoneup` | 34 | 5 | 0 | 2 | 0 | 3 | 29 | `PhotoViewer.qml` |
| `oneup` | 33 | 5 | 0 | 2 | 0 | 3 | 28 | `PhotoViewer.qml` |
| `peoplepanel` | 14 | 6 | 1 | 2 | 2 | 1 | 8 | `PeoplePanel.qml`, `PeoplePanelRow.qml` |
| `gedialog` | 13 | 5 | 1 | 1 | 1 | 2 | 8 | `PlacesPanel.qml`, `PlacesMap.qml` |
| `rightdrawerpanel` | 9 | 3 | 0 | 0 | 3 | 0 | 6 | `PropertiesPanel.qml` |
| `foldermgr` | 32 | 11 | 4 | 5 | 1 | 1 | 21 | `FolderManagerDialog.qml` |
| `tagpanel` | 24 | 8 | 6 | 0 | 0 | 2 | 16 | `TagsPanel.qml` |
| `unknownfaceheaderpanel` | 18 | 6 | 4 | 0 | 2 | 0 | 12 | `UnnamedFacesView.qml` |
| `instructionpanel` | 7 | 2 | 0 | 0 | 2 | 0 | 5 | **nincs-megfeleltetes** — Betanító buborék („Learn more…”) — nincs nálunk |
| `activity` | 6 | 1 | 0 | 0 | 1 | 0 | 5 | **nincs-megfeleltetes** — Töltésjelző pörgettyű a rácson — nálunk nincs külön elem |
| `nav` | 6 | 1 | 0 | 0 | 1 | 0 | 5 | **nincs-megfeleltetes** — Nagyítás-navigátor („floater”) a szerkesztőben — nálunk csak a PhotoViewer nagyítás-állapotgépe van, navigátor-ablak nincs |
| `uploadallinstructionpanel` | 5 | 1 | 0 | 0 | 1 | 0 | 4 | **nincs-megfeleltetes** — Feltöltési betanító buborék — nincs nálunk |
| `propertiespanel` | 3 | 1 | 0 | 0 | 0 | 1 | 2 | `PropertiesPanel.qml` |
| `bigslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `brushslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `burstslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `durationslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `editslider1` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `editslider2` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `editslider3` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `editslider4` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `flightslider1` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `lengthslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `outlineweightslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `printborderslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `scaleslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `spacing_slider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `textopacityslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `timeslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `toolslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `transitionslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `zoomslider` | 2 | 1 | 0 | 0 | 0 | 1 | 1 | `PicasaSlider.qml` |
| `wait_dialog` | 13 | 1 | 1 | 0 | 0 | 0 | 12 | `BatchEditProgressPanel.qml`, `ConfirmDialog.qml` |
| `pickerpanel` | 9 | 0 | 0 | 0 | 0 | 0 | 9 | `TextColorSwatches.qml` |
| `modalprogress` | 7 | 0 | 0 | 0 | 0 | 0 | 7 | `ImportProgressPanel.qml`, `BatchEditProgressPanel.qml` |
| `scratch` | 7 | 0 | 0 | 0 | 0 | 0 | 7 | **nincs-megfeleltetes** — Belső rajzfelület (album-előnézet összeállítása) — nem felhasználói felület |
| `moviecontrols` | 5 | 0 | 0 | 0 | 0 | 0 | 5 | `VideoPlayerView.qml` |
| `nerdview` | 5 | 0 | 0 | 0 | 0 | 0 | 5 | `PerfMonitorPanel.qml`, `HistogramBox.qml` |
| `editpanelactivity` | 3 | 0 | 0 | 0 | 0 | 0 | 3 | **nincs-megfeleltetes** — Belső töltésjelző a szerkesztőben — nincs külön elemünk |
| `slideshowctrls` | 2 | 0 | 0 | 0 | 0 | 0 | 2 | `SlideshowView.qml` |

## A legnagyobb fehér foltok — a hiányzó elemek panelenként, névvel

Csak az értékelhető elemek. `bizonytalan` = nem dönthető el gépi úton, kézi ellenőrzésre vár.

### `editpanel` — 61 hiány · panel-megfeleltetés: `parositva`

A szerkesztő teljes bal oldali panelje minden fülével

- `aa_2up_toggle` buboréksúgó: „View the same image twice”
- `ab_2up_toggle` buboréksúgó: „View two different images”
- `captionbutton` buboréksúgó: „Show/Hide Caption”
- `captiontrash` buboréksúgó: „Delete this caption”
- `editcheckbox1` — *bizonytalan*
- `editcheckbox2` — *bizonytalan*
- `editcircle1` — *bizonytalan*
- `editcircle1_well` — *bizonytalan*
- `editcontrol_well` — *bizonytalan*
- `editcontrols` — *bizonytalan*
- `edithelpbutton` buboréksúgó: „Help”
- `editslideshow` „Edit Movie” (magyarul: „Mozgófilm szerkesztése”)
- `edittextghost` — *bizonytalan*
- `edittextpanel` — *bizonytalan*
- `eraserbutton` — *bizonytalan*
- `fxpreview10` — *bizonytalan*
- `fxpreview11` — *bizonytalan*
- `fxpreview12` — *bizonytalan*
- `fxpreview2` — *bizonytalan*
- `fxpreview3` — *bizonytalan*
- `fxpreview4` — *bizonytalan*
- `fxpreview5` — *bizonytalan*
- `fxpreview6` — *bizonytalan*
- `fxpreview7` — *bizonytalan*
- `fxpreview8` — *bizonytalan*
- `fxpreview9` — *bizonytalan*
- `magic_color` buboréksúgó: „One-click fix for color”
- `magic_lighting` buboréksúgó: „One-click fix for lighting”
- `modaldialogblur` — *bizonytalan*
- `movietab` — *bizonytalan*
- `movietabpanel` — *bizonytalan*
- `next` — *bizonytalan*
- `only_1up_toggle` buboréksúgó: „View only one image”
- `picnik` „Edit in Creative Kit” (magyarul: „Szerkesztés a Kreatív készletben”)
- `picnik_fx` buboréksúgó: „Try more effects at Creative Kit”
- `picnik_fx_label` „Effects by” (magyarul: „Effektusok a következőtől:”)
- `picnikapply` — *bizonytalan*
- `prev` — *bizonytalan*
- `preview` — *bizonytalan*
- `preview2` — *bizonytalan*
- `previewimage` — *bizonytalan*
- `previewimage2` — *bizonytalan*
- `quickupload` buboréksúgó: „Upload to your Web Albums Drop Box”
- `selection_label` „Selected” (magyarul: „Kijelölve”)
- `selection_label_zoom` „Selected” (magyarul: „Kijelölve”)
- `showtextcheckbox` buboréksúgó: „Toggle to show or hide text on a photo”
- `slidercircle0` — *bizonytalan*
- `slidercircle1` — *bizonytalan*
- `swap_2up_focus` buboréksúgó: „Switch which image has focus”
- `swap_2up_layout` buboréksúgó: „Switch between horizontal and vertical layout”
- `tab_bkg` — *bizonytalan*
- `tabpanel1` — *bizonytalan*
- `tabpanel2` — *bizonytalan*
- `tabpanel3` — *bizonytalan*
- `tabpanel4` — *bizonytalan*
- `tabpanel5` — *bizonytalan*
- `tabs` — *bizonytalan*
- `toggle_left_drawer` buboréksúgó: „Show/Hide Edit Controls”
- `uploadchanges` buboréksúgó: „Update online copy with this version”
- `weblink` buboréksúgó: „Go to the website associated with this Photo”
- `zoomsliderrect` — *bizonytalan*

### `makemoviepanel` — 49 hiány · panel-megfeleltetés: `parositva`

Csak a filmkészítő párbeszéd van meg; interaktív filmkészítő panel nincs

- `add_audio` „Load...” (magyarul: „Betöltés...”)
- `addtomovie` buboréksúgó: „Add the selected clip(s) to the end of the movie”
- `album_order_label` „Album Order” (magyarul: „Album szerint”)
- `album_order_radio` — *bizonytalan*
- `aoptions_label` „Options” (magyarul: „Opciók”)
- `audio_label` „Audio Track:” (magyarul: „Hangsáv:”)
- `bkg_picker_panel` — *bizonytalan*
- `bold` buboréksúgó: „Bold”
- `burstslider_label` „Don't filter by time taken” (magyarul: „Ne legyen szűrés a készítés ideje alapján”)
- `cancel` „Close” (magyarul: „Bezárás”)
- `chronological_order_label` „Chronological” (magyarul: „Időrend”)
- `chronological_order_radio` — *bizonytalan*
- `crop_to_fit_label` „Full frame photo crop” (magyarul: „Teljes képkockás fotó körbevágása”)
- `deleteclips` buboréksúgó: „Remove the selected clip(s) from the tray”
- `durationslider_label` „Slide Duration” (magyarul: „Dia időtartama”)
- `export_youtube` „YT” (magyarul: „YouTube”)
- `font_label` „Font:” (magyarul: „Betűtípus:”)
- `inputtext` — *bizonytalan*
- `insert_slide` buboréksúgó: „Add a new text slide”
- `italic` buboréksúgó: „Italic”
- `lengthslider_label` „Total Photos” (magyarul: „Összes fénykép”)
- `moviesize_label` „Dimensions” (magyarul: „Méretek”)
- `ordering_header_label` „Ordering of Slides:” (magyarul: „Diák rendezése:”)
- `outline` buboréksúgó: „Automatic Outline (like movie subtitles)”
- `previewimage` — *bizonytalan*
- `previewpanel` — *bizonytalan*
- `recompute` „Apply” (magyarul: „Alkalmaz”)
- `remove_audio` „Clear” (magyarul: „Törlés”)
- `remove_low_res_faces_label` „Remove Low Resolution Faces” (magyarul: „Kis felbontású arcok eltávolítása”)
- `remove_slide` buboréksúgó: „Remove the selected slide”
- `render` „Create Movie” (magyarul: „Mozgófilm létrehozása”)
- `rewind` „Back to selected slide” (magyarul: „Vissza a kijelölt diához”)
- `size_label` „Size:” (magyarul: „Méret:”)
- `sizelist`
- `smart_order_label` „Best Transitions” (magyarul: „A legjobb átmenetek”)
- `smart_order_radio` — *bizonytalan*
- `style_label` „Style:” (magyarul: „Stílus:”)
- `tab2` „Slide” (magyarul: „Dia”)
- `tab3` „Options” (magyarul: „Klipek”)
- `tabpanel1` — *bizonytalan*
- `tabpanel2` — *bizonytalan*
- `tabpanel3` — *bizonytalan*
- `tabs` — *bizonytalan*
- `templatelist` — *bizonytalan*
- `text_picker_panel` — *bizonytalan*
- `transitionslider_label` „Overlap” (magyarul: „Átfedés”)
- `transtype_label` „Transition Style” (magyarul: „Képváltási stílus”)
- `txcolorpicker_bevel` — *bizonytalan*
- `viewedit` — *bizonytalan*

### `thumbui` — 33 hiány · panel-megfeleltetés: `parositva`

A fő könyvtárnézet egésze

- `acquirebutton` — *bizonytalan*
- `addtobuttcon` buboréksúgó: „Add selected items to an Album”
- `backup` „Backup” (magyarul: „Biztonsági mentés”)
- `buttonbarsets` — *bizonytalan*
- `buttongroup1` — *bizonytalan*
- `cdmode` „Gift CD” (magyarul: „Ajándék CD”)
- `editpanel` — *bizonytalan*
- `flatview` buboréksúgó: „Set view to show flat folder structure”
- `folderview` buboréksúgó: „Set view to show folder tree structure”
- `folderviewpopup` buboréksúgó: „View options”
- `fullview` „Edit photos” (magyarul: „Fotók szerkesztése”)
- `hlisthandle` — *bizonytalan*
- `hlistsizer` — *bizonytalan*
- `hviewtoggle` — *bizonytalan*
- `lightbox_esolo_button` „Search All” (magyarul: „Keresés mindenhol”)
- `lightbox_esolo_text` „No results found in this album” (magyarul: „Nincs találat ebben az albumban”)
- `listdecrect` — *bizonytalan*
- `listdetail` — *bizonytalan*
- `loupehit` buboréksúgó: „Click and drag over photos to magnify them”
- `next` buboréksúgó: „View the next Photo”
- `people_toggle` buboréksúgó: „Show/Hide People Panel”
- `places_toggle` buboréksúgó: „Show/Hide Places Panel”
- `prev` buboréksúgó: „View the previous Photo”
- `properties_toggle` buboréksúgó: „Show/Hide Properties Panel”
- `searchgroup` — *bizonytalan*
- `single_action_close` buboréksúgó: „Cancel "Get more"”
- `single_action_message` „Select items to add to your project's clips tray, then press the "Back" button to return to your project” (magyarul: „Jelölje ki azokat az elemeket, amelyeket a projekt kliptálcájára fel szeretne venni, majd a "Vissza" gombra kattintva térjen vissza a projekthez”)
- `single_action_return` buboréksúgó: „Go back to what you were editing”
- `startoggle` buboréksúgó: „Add/Remove Star”
- `tags_toggle` buboréksúgó: „Show/Hide Tags Panel”
- `toggle_right_drawer` — *bizonytalan*
- `visitweb` „Web View” (magyarul: „Internetes nézet”)
- `webcambutton` buboréksúgó: „Capture photos or video from a webcam or other video device”

### `publish` — 30 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Biztonsági mentés / Ajándék-CD / webre töltés — nincs nálunk

- `addmore` „Add More...” (magyarul: „Továbbiak hozzáadása...”)
- `backup_cancel` „Cancel” (magyarul: „Mégse”)
- `backup_eject` „Eject” (magyarul: „Kiadás”)
- `backup_go` „Burn Disc” (magyarul: „Lemezre írás”)
- `backup_help` „Help” (magyarul: „Súgó”)
- `backupcdheader2` „Choose folders & albums to back up” (magyarul: „Mappák és albumok kijelölése biztonsági másolat készítéséhez”)
- `backuptext2` „Picasa is now showing the files you have not previously backed up.” (magyarul: „A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem készült biztonsági másolat.”)
- `backuptext3` „Check the folders you want to back up, or choose 'Select All' to choose everything.” (magyarul: „Jelölje ki azokat a mappákat, amelyekről biztonsági másolatot szeretne készíteni, vagy "Az összes kijelölése" gombra kattintva az összes elemet jelölje ki.”)
- `deletebackupset` „Delete Set” (magyarul: „Készlet törlése”)
- `editbackupset` „Edit Set” (magyarul: „Készlet szerkesztése”)
- `giftcdtext` „The items selected with a checkmark above will be included on your Gift CD.   To add more items click the "Add More" button below.” (magyarul: „A program a fent pipával kijelölt elemeket másolja az ajándék CD-re. További elemek felvételéhez kattintson az alábbi "Továbbiak hozzáadása" gombra.”)
- `label_rpoptionbox1` „Upload” (magyarul: „Feltöltés”)
- `label_rpoptionbox2` „Change options” (magyarul: „Opciók módosítása”)
- `label_rpoptionbox3` „Remove online” (magyarul: „Eltávolítás: online elemek”)
- `newbackupset` „New Set” (magyarul: „Új készlet”)
- `picsizemenu`
- `presentcd_cancel` „Cancel” (magyarul: „Mégse”)
- `presentcd_eject` „Eject” (magyarul: „Kiadás”)
- `presentcd_go` „Burn Disc” (magyarul: „Lemezre írás”)
- `presentcd_help` „Help” (magyarul: „Súgó”)
- `replicate_button_group`
- `replicate_cancel` „Cancel” (magyarul: „Mégse”)
- `replicate_go` „OK” (magyarul: „OK”)
- `rpoptionbox1` buboréksúgó: „Selected folder and/or albums will be uploaded”
- `rpoptionbox2` buboréksúgó: „Selected folders and/or albums will be updated online with the options specified in the menus to the right”
- `selectall` „Select All” (magyarul: „Az összes kijelölése”)
- `selectnone` „Select None” (magyarul: „Az összes kijelölés megszüntetése”)
- `upgradestorage` „Upgrade storage” (magyarul: „Tárhely bővítése”)
- `uploadallsync` buboréksúgó: „Change the sync setting for the selected folders and/or albums”
- `webpublish_cancel`

### `printpanel` — 25 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Nyomtatási panel és előnézet — nálunk csak a tálca „Print” indítógombja van meg

- `3x5button` „3.5 x 5” (magyarul: „3,5x5”)
- `addprintsbutton` buboréksúgó: „Add another copy of each Photo to be printed”
- `captionoptionsbutton` buboréksúgó: „Configure borders and text for Photos to be printed”
- `captionoptionslabel` „Border and Text Options” (magyarul: „Szegély- és szövegopciók”)
- `copieslabel` „Copies per Photo” (magyarul: „Példányszám fotónként”)
- `croptoggle` buboréksúgó: „Crop photos to match the selected print dimensions”
- `croptogglelabel` „Crop to Fit” (magyarul: „Kép méretre vágása”)
- `fittoggle` buboréksúgó: „Preserve the original dimensions of the photos”
- `fittogglelabel` „Shrink to Fit” (magyarul: „Kép kicsinyítése, hogy elférjen”)
- `froogle` „Search Froogle for Supplies” (magyarul: „Tartozékok keresése a Froogle-en”)
- `nextbutton` buboréksúgó: „View the next preview page”
- `pcancelbutton` „Cancel” (magyarul: „Mégse”)
- `phelpbutton` „Help” (magyarul: „Súgó”)
- `prevbutton` buboréksúgó: „View the previous preview page”
- `preview`
- `previewlabel` „Preview” (magyarul: „Előnézet”)
- `previewnumber`
- `printlayoutlabel` „Print Layout” (magyarul: „Nyomtatási elrendezés”)
- `printsetuplabel` „Printer Settings” (magyarul: „Nyomtatóbeállítások”)
- `psetupbutton` buboréksúgó: „Open printer setup controls for the selected printer”
- `reviewnowbutton` „Review” (magyarul: „Ellenőrzés”)
- `reviewnowbutton2` „Review” (magyarul: „Ellenőrzés”)
- `selectprinterbutton` buboréksúgó: „Provides a list of available printers”
- `setuplabel` „Printer Setup” (magyarul: „Nyomtató telepítése”)
- `subprintsbutton` buboréksúgó: „Subtract a copy of each Photo to be printed”

### `printoptions` — 22 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Nyomtatási keret/felirat beállítások — nincs nálunk (a Beállítások „Nyomtatás” füle más panel)

- `apply` „Apply” (magyarul: „Alkalmaz”)
- `border_color_label` „Border color” (magyarul: „Szegély színe”)
- `bottomonly_checkbox`
- `bottomonly_checkbox_label` „Bottom only” (magyarul: „Csak alul”)
- `cancel` „Cancel” (magyarul: „Mégse”)
- `caption_font_label` „Font” (magyarul: „Betűtípus”)
- `caption_label` „Captions” (magyarul: „Képfeliratok”)
- `caption_size_label` „Size” (magyarul: „Méret”)
- `colorpicker_bevel`
- `disabled_label` „Sorry, but these options cannot be used when printing contact sheets.” (magyarul: „Ezek a beállítások indexképek nyomtatásakor nem használhatók.”)
- `evenwidth_checkbox`
- `evenwidth_checkbox_label` „Even width border” (magyarul: „Egyenletes szélességű szegély”)
- `ok` „OK” (magyarul: „OK”)
- `sizelist`
- `text_picker_panel`
- `textbelowimage_label` „Below image” (magyarul: „A kép alatt”)
- `textonborder_label` „On border” (magyarul: „A szegélyen”)
- `textonimage_label` „On image” (magyarul: „A képen”)
- `useexif_label` „Exif information” (magyarul: „Exif-adatok”)
- `usenotext_label` „No text” (magyarul: „Nincs szöveg”)
- `wrap_checkbox`
- `wrap_checkbox_label` „Wrap text” (magyarul: „Szöveg tördelése”)

### `upload` — 21 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Picasa Web Albums feltöltő párbeszéd — nincs nálunk

- `add_groups_button`
- `cancel` „Cancel” (magyarul: „Mégse”)
- `collab_checkbox`
- `collab_label` „Let these people contribute to my album” (magyarul: „Ezek a személyek együttműködhetnek az albumom kialakításán”)
- `contact_album_list`
- `contact_edit`
- `contact_edit_active`
- `contact_list`
- `contact_lists_active`
- `edit_active`
- `error_button`
- `newalbum2` „New” (magyarul: „Új”)
- `ok` „Upload” (magyarul: „Feltöltés”)
- `quickpreview0`
- `sharing_label` „Share With:” (magyarul: „Megosztás a következővel:”)
- `storagetext` „Learn more...” (magyarul: „További információ...”)
- `upgrade` „Upgrade” (magyarul: „Tárhely bővítése”)
- `uploadinfo_link`
- `uploadsize_menu`
- `visibility_menu`
- `webalbums_menu`

### `buzzupload` — 21 hiány · panel-megfeleltetés: `nem-cel`

Google Buzz feltöltés — a szolgáltatás megszűnt, nem cél

- `also_send_email_checkbox`
- `also_send_email_label` „Send email notifications” (magyarul: „Értesítések küldése e-mailben”)
- `cancel` „Cancel” (magyarul: „Mégse”)
- `collab_checkbox`
- `collab_label` „Let these people contribute to my album” (magyarul: „Ezek a személyek együttműködhetnek az albumom kialakításán”)
- `edit_active`
- `error_button`
- `newalbum2` „New” (magyarul: „Új”)
- `ok` „Upload” (magyarul: „Feltöltés”)
- `options_button`
- `quickpreview0`
- `quickpreview1`
- `quickpreview2`
- `quickpreview3`
- `quickpreview4`
- `quickpreview5`
- `quickpreview6`
- `uploadinfo_link`
- `visibility_button`
- `visibility_label` „Album visibility” (magyarul: „Album láthatósága”)
- `webalbums_menu`

### `compose_share` — 16 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Megosztási meghívó szerkesztő — nincs nálunk

- `add_groups_button`
- `cancel` „Cancel” (magyarul: „Mégse”)
- `changeuser` „Change User” (magyarul: „Felhasználóváltás”)
- `collab_checkbox`
- `collab_label` „Let these people contribute to my album” (magyarul: „Ezek a személyek együttműködhetnek az albumom kialakításán”)
- `discard` „Discard” (magyarul: „Elvetés”)
- `discardb` „Discard” (magyarul: „Elvetés”)
- `group_text` „Groups:” (magyarul: „Csoportok:”)
- `infotext` „Ready to share!  Please choose recipients for your invitation below.” (magyarul: „Megosztásra kész! Jelölje ki alább a meghívó címzettjeit.”)
- `preview`
- `send` „Send” (magyarul: „Küldés”)
- `sendb` „Send” (magyarul: „Küldés”)
- `subject_text` „Subject:” (magyarul: „Tárgy:”)
- `to_text` „To:” (magyarul: „Címzett:”)
- `visibility_label` „Album visibility:” (magyarul: „Album láthatósága:”)
- `visibility_menu`

### `quicktagconfig` — 13 hiány · panel-megfeleltetés: `parositva`

Gyorscímke-beállító

- `cancel` — *bizonytalan*
- `cancel-label` „Cancel” (magyarul: „Mégse”)
- `edit_0` — *bizonytalan*
- `edit_1` — *bizonytalan*
- `edit_2` — *bizonytalan*
- `edit_3` — *bizonytalan*
- `edit_4` — *bizonytalan*
- `edit_5` — *bizonytalan*
- `edit_6` — *bizonytalan*
- `edit_7` — *bizonytalan*
- `edit_8` — *bizonytalan*
- `edit_9` — *bizonytalan*
- `ok-label` „OK” (magyarul: „OK”)

### `buttonmgr` — 13 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Gombsáv-testreszabó párbeszéd — nincs nálunk

- `add` „Add >>” (magyarul: „Hozzáadás >>”)
- `browse` „Find buttons online...” (magyarul: „Gombok keresése az interneten...”)
- `cancel` „Cancel” (magyarul: „Mégse”)
- `done` „Done” (magyarul: „Kész”)
- `leftlist`
- `leftlist_text` (magyarul: „Rendelkezésre álló gombok:”)
- `movedown` „Move Down” (magyarul: „Mozgatás lefelé”)
- `moveup` „Move Up” (magyarul: „Mozgatás felfelé”)
- `ok` „OK” (magyarul: „OK”)
- `remove` „<< Remove” (magyarul: „<< Eltávolítás”)
- `rightlist`
- `rightlist_text` (magyarul: „Jelenlegi gombok:”)
- `usedefaults` „Reset to Defaults” (magyarul: „Visszaállítás alapértelmezettre”)

### `choose_mail` — 13 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Levelezőprogram-választó párbeszéd — nincs nálunk

- `cancelbutton`
- `checkbox`
- `gmailsignup1` „Don't have Gmail? Get a free account.” (magyarul: „Nincs Gmail-fiókja? Nyisson egy fiókot ingyen.”)
- `help` „Help” (magyarul: „Súgó”)
- `helpbutton`
- `mail1` „MAIL CLIENT” (magyarul: „LEVELEZŐPROGRAM”)
- `mail1a` „Use my default email program.” (magyarul: „Az alapértelmezett levelezőprogram használata”)
- `mail2` „Google Mail” (magyarul: „Google Mail”)
- `mail2a` „Use my Gmail or Google account.” (magyarul: „A Gmail-fiók vagy a Google Fiók használata”)
- `mailcancel` „Cancel” (magyarul: „Mégse”)
- `picker`
- `remember` „Remember this setting, don't display this dialog again.” (magyarul: „Jegyezze meg ezt a beállítást, ne jelenítse meg a párbeszédpanelt újra.”)
- `selecttext` „Select how you want to e-mail your photos.” (magyarul: „Válassza ki, hogyan szeretné e-mailben elküldeni fotóit.”)

### `acquirepanel` — 12 hiány · panel-megfeleltetés: `parositva`

Importáló panel — nálunk párbeszédablak, nem teljes értékű bal oldali panel

- `add_groups_button` buboréksúgó: „Add people to share albums with”
- `buttons` — *bizonytalan*
- `import_folder_menu` — *bizonytalan*
- `import_from_menu` — *bizonytalan*
- `nextbutton` buboréksúgó: „View the next Photo”
- `previousbutton` buboréksúgó: „View the previous Photo”
- `selected_groups_label` „Nobody” (magyarul: „Senki”)
- `share_with_label` „Share with:” (magyarul: „Megosztás a következővel:”)
- `sync_options_button` „Options” (magyarul: „Opciók”)
- `togglegroup` — *bizonytalan*
- `upload_checkbox` — *bizonytalan*
- `upload_label` „Upload” (magyarul: „Feltöltés”)

### `faceheaderpanel` — 12 hiány · panel-megfeleltetés: `parositva`

Névvel ellátott arc-album fejléce

- `confirmsug` „Confirm all” (magyarul: „Az összes jóváhagyása”)
- `create_collage` buboréksúgó: „Create Photo Collage”
- `create_face_movie` buboréksúgó: „Create Face Movie”
- `create_movie` buboréksúgó: „Create Movie Presentation”
- `face_zoom` buboréksúgó: „View zoomed in to the face”
- `moresug` „Find more suggestions” (magyarul: „További javaslatok keresése”)
- `picture_zoom` buboréksúgó: „View zoomed out to the full picture”
- `play` buboréksúgó: „Play Fullscreen Slideshow”
- `pwa_button` buboréksúgó: „Open PWA web page”
- `removesel` „Remove” (magyarul: „Eltávolítás”)
- `set_thumbnail` buboréksúgó: „Set as People Album Thumbnail”
- `sug_filter` buboréksúgó: „Show only suggestions (when toggled on)”

### `capturemoviepanelpopup` — 11 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Webkamerás videofelvétel — nincs nálunk

- `audio_label` „Audio” (magyarul: „Hang”)
- `camchange` „Settings” (magyarul: „Beállítások”)
- `capture` „Record” (magyarul: „Felvétel”)
- `done` „Done” (magyarul: „Kész”)
- `live_video` „Camera” (magyarul: „Fényképezőgép”)
- `next`
- `prev`
- `settings_apply` „Apply” (magyarul: „Alkalmaz”)
- `settings_cancel` „Cancel” (magyarul: „Mégse”)
- `size_label` „Size” (magyarul: „Méret”)
- `video_label` „Video” (magyarul: „Videoklip”)

### `edittextpanel` — 10 hiány · panel-megfeleltetés: `parositva`

Szöveg-eszköz panelje

- `align_label` „Alignment:” (magyarul: „Igazítás:”)
- `centeralign` buboréksúgó: „Center justify text”
- `colorpicker_bevel` — *bizonytalan*
- `edittext_label` „Edit Text” (magyarul: „Szöveg szerkesztése”)
- `leftalign` buboréksúgó: „Left justify text”
- `rightalign` buboréksúgó: „Right justify text”
- `size_label` „Size:” (magyarul: „Méret:”)
- `sizelist` — *bizonytalan*
- `style_label` „Style:” (magyarul: „Stílus:”)
- `transparency_label` „Transparency” (magyarul: „Átlátszóság”)

### `compose_mail` — 10 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül

- `changeuser` „Change User” (magyarul: „Felhasználóváltás”)
- `discard` „Discard” (magyarul: „Elvetés”)
- `discardb` „Discard” (magyarul: „Elvetés”)
- `discardimage` buboréksúgó: „Remove selected image from attachment”
- `preview`
- `send` „Send” (magyarul: „Küldés”)
- `sendb` „Send” (magyarul: „Küldés”)
- `subject_text` „Subject:” (magyarul: „Tárgy:”)
- `to_text` „To:” (magyarul: „Címzett:”)
- `topentry`

### `collab` — 10 hiány · panel-megfeleltetés: `nem-cel`

Picasa Web Albums közös album — a szolgáltatás megszűnt, nem cél

- `cancel` „Cancel” (magyarul: „Mégse”)
- `contact_album_list`
- `contact_edit`
- `contact_edit_active`
- `contact_list`
- `contact_lists_active`
- `ok` „Upload” (magyarul: „Feltöltés”)
- `storagetext` „Learn more...” (magyarul: „További információ...”)
- `uploadinfo_link`
- `uploadsize_menu`

### `headerpanel` — 8 hiány · panel-megfeleltetés: `parositva`

Album- és mappafejléc a rács fölött

- `create_collage` buboréksúgó: „Create Photo Collage”
- `create_movie` buboréksúgó: „Create Movie Presentation”
- `play` buboréksúgó: „Play Fullscreen Slideshow”
- `sync_label` „Sync to Web” (magyarul: „Szinkronizálás az internettel”)
- `sync_options` buboréksúgó: „Online options”
- `view_online` „View on Web” (magyarul: „Megtekintés az interneten”)
- `websync0` buboréksúgó: „Upload and sync future changes to the web”
- `websync1` buboréksúgó: „Stop syncing changes to the web”

### `collagepanel` — 7 hiány · panel-megfeleltetés: `parositva`

A kollázs-szerkesztő panel MEGVAN (2026-08-31 mérés): 23 Collage*.qml. A korábbi sor egyetlen fájlra mutatott és azt írta, hogy nincs interaktív szerkesztő — ez ELAVULT volt, és a panel mind a 36 elemét hiánynak jelezte.

- `picker_panel` — *bizonytalan*
- `previewinset` — *bizonytalan*
- `previewroot` — *bizonytalan*
- `tabpanel1` — *bizonytalan*
- `tabpanel2` — *bizonytalan*
- `tabs` — *bizonytalan*
- `view_and_edit` — *bizonytalan*

### `titledialog` — 7 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Filmes címdia-szerkesztő párbeszéd — nincs nálunk

- `add` „Add”
- `cancel` „Cancel”
- `captionchk`
- `previewimage`
- `previewtext`
- `sizelist`
- `stylelist`

### `searchcontainer` — 6 hiány · panel-megfeleltetés: `parositva`

Keresősáv és szűrőgombjai

- `facesearch` buboréksúgó: „Show only photos with faces”
- `search` — *bizonytalan*
- `searchautocomplete` — *bizonytalan*
- `searchbutton` — *bizonytalan*
- `timecontainer_label` buboréksúgó: „Filter by date range”
- `webview` buboréksúgó: „Show uploads to web albums only”

### `video_control_bar` — 6 hiány · panel-megfeleltetés: `parositva`

Videó vezérlősáv (vágás is)

- `moviemode1` buboréksúgó: „Play full screen”
- `scaleslider` — *bizonytalan*
- `setin` buboréksúgó: „Create a new starting point”
- `setout` buboréksúgó: „Create a new ending point”
- `trimslider` — *bizonytalan*
- `volumeslider` — *bizonytalan*

### `keywords` — 6 hiány · panel-megfeleltetés: `parositva`

Címkeszerkesztő

- `addbutton` „Add” (magyarul: „Hozzáadás”)
- `addkeywords_label` „Add Tag:” (magyarul: „Címke hozzáadása:”)
- `closebutton` „Done” (magyarul: „Kész”)
- `keywordlist` — *bizonytalan*
- `readonly_label` „Tags cannot be modified because one or more items are read-only.” (magyarul: „A címkéket nem lehet módosítani, mert egy vagy több elem írásvédett.”)
- `removebutton` „Remove” (magyarul: „Eltávolítás”)

### `uploadmgr` — 6 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Feltöltés-kezelő (szüneteltetés/folytatás) — nincs nálunk

- `cleanup` „Clear Completed” (magyarul: „A feltöltöttek törlése a listából”)
- `itemlist`
- `minibutton`
- `pause` „Pause” (magyarul: „Felfüggesztés”)
- `resume` „Resume” (magyarul: „Folytatás”)
- `throttlechk`

### `searchoptions` — 6 hiány · panel-megfeleltetés: `parositva`

Keresési eredmény fejléce

- `dupesearch` — *bizonytalan*
- `facesearch` — *bizonytalan*
- `label_searchresult` „Search Result:” (magyarul: „Keresési eredmény:”)
- `searchcenter` — *bizonytalan*
- `searchresult` — *bizonytalan*
- `viewallbutton` „Back to View All” (magyarul: „Az összes megtekintése”)

### `canoncapturemoviepanelpopup` — 5 hiány · panel-megfeleltetés: `nem-cel`

Canon SDK-s kamerafelvétel — nem cél

- `done` „OK”
- `facepreviewbc`
- `livepreview`
- `settings_apply`
- `settings_cancel`

### `geopanel` — 5 hiány · panel-megfeleltetés: `parositva`

Helyek panel

- `map_menu` — *bizonytalan*
- `search` — *bizonytalan*
- `search_group` — *bizonytalan*
- `search_label` „Search for an address:” (magyarul: „Cím keresése:”)
- `searchinput` — *bizonytalan*

### `outputlayout` — 4 hiány · panel-megfeleltetés: `parositva`

A tálca alatti kimeneti gombsáv

- `blogger` „Blogger” (magyarul: „Blogger”)
- `morebutton` „More...” (magyarul: „További lehetőségek...”)
- `orderbutton` „Shop” (magyarul: „Vásárlás”)
- `sharewith` „Hello” (magyarul: „Hello”)

### `initialscan` — 4 hiány · panel-megfeleltetés: `parositva`

Első indítás — mit vizsgáljunk át

- `cancel` — *bizonytalan*
- `radio_complete` — *bizonytalan*
- `radio_limited` — *bizonytalan*
- `radiogroup` — *bizonytalan*

### `video_control_bar2` — 4 hiány · panel-megfeleltetés: `parositva`

Videó vezérlősáv második változata

- `1to1` buboréksúgó: „Show actual movie size (don't stretch)”
- `fullscreen` buboréksúgó: „Play full screen”
- `scaleslider` — *bizonytalan*
- `volumeslider` — *bizonytalan*

### `panelroot` — 4 hiány · panel-megfeleltetés: `parositva`

Legfelső panelváltó (Könyvtár / Import / Kollázs / Film / Felvétel)

- `capturemovietab` „Capture” (magyarul: „Rögzítés”)
- `globaltabs` — *bizonytalan*
- `makemovietab` „Movie Maker” (magyarul: „Mozgófilmkészítés”)
- `youtab` — *bizonytalan*

### `throttle` — 4 hiány · panel-megfeleltetés: `parositva`

Gyorsgörgető a rács jobb szélén

- `albumscrollbottom` — *bizonytalan*
- `albumscrolltop` — *bizonytalan*
- `nextalbum` — *bizonytalan*
- `prevalbum` — *bizonytalan*

### `movieeditpanel` — 4 hiány · panel-megfeleltetés: `parositva`

Videovágó panel

- `capture_frame` „Take Snapshot” (magyarul: „Pillanatfelvétel készítése”)
- `export_movie` „Export Clip” (magyarul: „Klip exportálása”)
- `export_youtube` „Upload to YouTube” (magyarul: „Feltöltés a YouTube webhelyre”)
- `reset_trim` „Reset Start and End” (magyarul: „Kezdés és befejezés alaphelyzetbe állítása”)

### `editoneup` — 3 hiány · panel-megfeleltetés: `parositva`

Egyképes nézet szerkesztés közben

- `captionbutton` — *bizonytalan*
- `next` — *bizonytalan*
- `prev` — *bizonytalan*

### `oneup` — 3 hiány · panel-megfeleltetés: `parositva`

Egyképes nézet a könyvtárban

- `captionbutton` — *bizonytalan*
- `next` — *bizonytalan*
- `prev` — *bizonytalan*

### `peoplepanel` — 3 hiány · panel-megfeleltetés: `parositva`

Emberek oldalsó panel

- `manual_cancel` „Cancel” (magyarul: „Mégse”)
- `peoplelist` — *bizonytalan*
- `status_label` „Select a folder to display faces” (magyarul: „Válasszon ki egy mappát az arcok megjelenítéséhez”)

### `gedialog` — 3 hiány · panel-megfeleltetés: `parositva`

Google Earth-ös geocímkéző párbeszéd — nálunk a Helyek panel fedi

- `done` „Done” (magyarul: „Kész”)
- `next` — *bizonytalan*
- `prev` — *bizonytalan*

### `rightdrawerpanel` — 3 hiány · panel-megfeleltetés: `parositva`

Jobb oldali fiók kerete

- `close` buboréksúgó: „Close this side panel”
- `size_toggle` buboréksúgó: „Switch between small/large side panel”
- `title_text` „Metadata” (magyarul: „Metaadatok”)

### `foldermgr` — 2 hiány · panel-megfeleltetés: `parositva`

Mappakezelő

- `cancel` — *bizonytalan*
- `instructions_text` „For each folder, you can choose whether or not to have Picasa find pictures inside it.  You can also pick folders to watch for new pictures.” (magyarul: „Minden mappa esetében megadhatja, hogy a Picasa keressen-e bennük képeket. Kijelölhet egyes mappákat is, és beállíthatja, hogy a program figyelje bennük az új képek megjelenését.”)

### `tagpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Címke oldalsó panel

- `input_group` — *bizonytalan*
- `taglist_group` — *bizonytalan*

### `unknownfaceheaderpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Névtelen arcok fejléce

- `showignored` „Show ignored faces” (magyarul: „Mellőzött arcok megjelenítése”)
- `showunknown` „Back to Unnamed” (magyarul: „Vissza ide: Név nélküliek”)

### `instructionpanel` — 2 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Betanító buborék („Learn more…”) — nincs nálunk

- `close` „Close” (magyarul: „Bezárás”)
- `learn_more` „Learn more...” (magyarul: „További információ...”)

### `activity` — 1 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Töltésjelző pörgettyű a rácson — nálunk nincs külön elem

- `activitybutton`

### `nav` — 1 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Nagyítás-navigátor („floater”) a szerkesztőben — nálunk csak a PhotoViewer nagyítás-állapotgépe van, navigátor-ablak nincs

- `close`

### `uploadallinstructionpanel` — 1 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Feltöltési betanító buborék — nincs nálunk

- `close` „Close” (magyarul: „Bezárás”)

### `propertiespanel` — 1 hiány · panel-megfeleltetés: `parositva`

Tulajdonságlista a jobb oldali fiókban

- `propertieslist` — *bizonytalan*

### `bigslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `bigslider` — *bizonytalan*

### `brushslider` — 1 hiány · panel-megfeleltetés: `parositva`

Ecsetméret-csúszka (retusálás)

- `scaleslider` — *bizonytalan*

### `burstslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `durationslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `editslider1` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `editslider` — *bizonytalan*

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

- `scaleslider` — *bizonytalan*

### `lengthslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `outlineweightslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `printborderslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `scaleslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `spacing_slider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `bigslider` — *bizonytalan*

### `textopacityslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

### `timeslider` — 1 hiány · panel-megfeleltetés: `parositva`

Közös csúszka-komponens

- `scaleslider` — *bizonytalan*

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

### `editpanel` — 6

- `albumview` — „Back to Library” itt: PicasaPy/PhotoViewer.qml, PicasaPy/ViewerContextMenu.qml
- `editcollage` — „Edit Collage” itt: PicasaPy/PhotoViewer.qml
- `in_progress_label` — „In Progress...” itt: PicasaPy/PhotoViewer.qml
- `render_now` — „Create Now” itt: PicasaPy/PhotoViewer.qml
- `sbutton` — „Play” itt: PicasaPy/PhotoViewer.qml
- `showtextlabel` — „Show Text” itt: PicasaPy/PicasaMenuBar.qml

### `makemoviepanel` — 5

- `addclips` — „Get More...” itt: PicasaPy/CollageClipsTab.qml
- `back_color_label` — „Background color” itt: PicasaPy/EditorParamPanel.qml
- `show_captions_label` — „Show Captions” itt: PicasaPy/CollageSettingsTab.qml
- `templatetext` — „Template:” itt: PicasaPy/WebExportDialog.qml
- `text_color_label` — „Text color” itt: PicasaPy/EditorTextPanel.qml

### `thumbui` — 3

- `albumview` — „Back To Library” itt: PicasaPy/PhotoViewer.qml, PicasaPy/ViewerContextMenu.qml
- `librarylabel` — „Library” itt: PicasaPy/DocumentTabStrip.qml
- `sbutton` — „Slideshow” itt: PicasaPy/OptionsDialog.qml, PicasaPy/PicasaMenuBar.qml

### `printpanel` — 8

- `4x6button` — „4 x 6” itt: PicasaPy/CollageFormatMenu.qml, PicasaPy/EditorPanel.qml
- `5x7button` — „5 x 7” itt: PicasaPy/CollageFormatMenu.qml, PicasaPy/EditorPanel.qml
- `8x10button` — „8 x 10” itt: PicasaPy/CollageFormatMenu.qml, PicasaPy/EditorPanel.qml
- `fullbutton` — „Full Page” itt: PicasaPy/CollageFormatMenu.qml, PicasaPy/EditorPanel.qml
- `pnowbutton` — „Print” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/PrintDialog.qml, PicasaPy/TrayBar.qml
- `pnowbutton2` — „Print” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/PrintDialog.qml, PicasaPy/TrayBar.qml
- `printerlabel` — „Printer” itt: PicasaPy/PrintDialog.qml
- `walletbutton` — „Wallet” itt: PicasaPy/PrintDialog.qml

### `printoptions` — 7

- `border_label` — „Border” itt: PicasaPy/EditorEffectsTab3.qml
- `border_max_label` — „Max.” itt: PicasaPy/CollageSettingsTab.qml
- `border_none_label` — „None” itt: PicasaPy/CollageBorderPicker.qml, PicasaPy/CollageContextMenus.qml, PicasaPy/CollageSettingsTab.qml
- `border_size_label` — „Border width” itt: PicasaPy/EditorParamPanel.qml
- `caption_color_label` — „Text Color” itt: PicasaPy/EditorTextPanel.qml
- `usecaption_label` — „Caption” itt: PicasaPy/PicasaMenuBar.qml
- `usefilename_label` — „File name” itt: PicasaPy/PicasaMenuBar.qml

### `buzzupload` — 1

- `options_label` — „Image size” itt: PicasaPy/ExportDialogs.qml

### `faceheaderpanel` — 1

- `confirmsel` — „Confirm” itt: PicasaPy/CollageDialogs.qml, PicasaPy/DocumentTabStrip.qml

### `capturemoviepanelpopup` — 1

- `stop` — „Stop” itt: Main.qml

### `uploadmgr` — 1

- `hide` — „Hide” itt: PicasaPy/PhotoContextMenu.qml, PicasaPy/PicasaMenuBar.qml, PicasaPy/ViewerContextMenu.qml

### `outputlayout` — 1

- `makemovie` — „Movie” itt: PicasaPy/CreateDialogs.qml, PicasaPy/PicasaMenuBar.qml

### `panelroot` — 1

- `picasatab` — „Library” itt: PicasaPy/DocumentTabStrip.qml

### `editoneup` — 2

- `bcklabel` — „Exit” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/SlideshowView.qml
- `tllabel` — „Timeline” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/TimelineView.qml

### `oneup` — 2

- `bcklabel` — „Exit” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/SlideshowView.qml
- `tllabel` — „Timeline” itt: PicasaPy/PicasaMenuBar.qml, PicasaPy/TimelineView.qml

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

## A mi többletünk — nálunk van, az eredetiben nincs ilyen szöveg

A QML `qsTr(...)` feliratai, amelyeknek nincs párja sem a `.tre` leltárban, sem a `stringres` szövegtárban. Ez **nem automatikusan hiba**: lehet jogos új funkció (pl. teljesítménymérő) vagy más szóhasználat — de **idegen elemet is jelezhet**, mint a #704-ben a „Kreatív”/„Effektek” fejlécsáv.

Összesen **442 felirat** 83 fájlban.

### `PicasaPy/PicasaMenuBar.qml` — 30

- „Sign in with your Google Account”
- „TEST MODE — logging startup”
- „Open File(s) in Editor”
- „Undo Paste All Effects”
- „Undo Batch Edit”
- „Show Editing Controls”
- „Thumbnails Only”
- „Dark Theme”
- „Recent &changes”
- „Show”
- „Print Thumbnails...”
- „Auto Redeye Fix”
- „Rotate Right”
- „Rotate Left”
- „Reset Face Positions”
- „Set as Desktop Background...”
- „Make a Gift CD...”
- „New Movie...”
- „Find Duplicates...”
- „Find Faces...”
- „Move Database...”
- „Compact Database...”
- „Language”
- „English”
- „Online Information”
- „Product Release Notes”
- „Performance Monitor”
- „Test Mode (logs the next startup)”
- „Send Log...”
- „About PicasaPy”

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

### `PicasaPy/PrintDialog.qml` — 20

- „3.5 x 5 in”
- „4 x 6 in”
- „5 x 7 in”
- „8 x 10 in”
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

### `PicasaPy/OptionsTabGeneral.qml` — 19

- „User interface:”
- „Use special effects”
- „Show tooltips”
- „Single click to exit the editing view”
- „Language:”
- „English”
- „Files:”
- „Detect duplicates on import”
- „Clear Cache...”
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

### `PicasaPy/CreateDialogs.qml` — 15

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
- „Video size:”
- „Seconds per picture:”
- „MP4 videos (*.mp4)”
- „The collage could not be created.”
- „The movie could not be created.”

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

### `PicasaPy/ImportSourceDialog.qml` — 15

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
- „WARNING! You have chosen to delete ALL FILES…”

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

### `PicasaPy/MoveDatabaseDialog.qml` — 12

- „Move Database”
- „Move the photo index and thumbnail cache to a new folder. ”
- „Network drives (e.g. a NAS) are fully supported and are ”
- „Current database location:”
- „New database location:”
- „(none selected)”
- „Browse...”
- „Move cancelled — nothing was changed.”
- „PicasaPy is moving the database.”
- „Database moved. Restart PicasaPy for the change to take effect.”
- „Move on next restart”
- „Choose new database location...”

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

### `Main.qml` — 10

- „This will remove all edits you have made to the”
- „This will remove all edits you have made to ALL of”
- „Red eye fixes have been applied. If you”
- „View All”
- „Clear Sample”
- „Updating similarity database ”
- „This folder is currently unavailable (for example a disconnected drive or network share). Its photos stay in the database and thumbnails come from the cache, but the original files cannot be opened or edited right now.”
- „Picasa had a problem loading this file(s). Would you ”
- „New person's name:”
- „WARNING! This will move all the faces back to the ”

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

### `PicasaPy/EditorTextPanel.qml` — 10

- „Type your text, then click on the photo to place it.”
- „B”
- „I”
- „U”
- „Align left”
- „Align center”
- „Align right”
- „Outline color”
- „Outline thickness”
- „Opacity”

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

### `PicasaPy/OptionsTabEmail.qml` — 9

- „Choose your mail client:”
- „Use this computer's default email program”
- „Let me choose each time I send a picture”
- „Multiple photo size:”
- „Single photo size:”
- „Send movies as:”
- „First frame”
- „Full movie”
- „Send embedded pictures and captions (Outlook only)”

### `PicasaPy/SaveDialogs.qml` — 9

- „A backup of this file will be made.”
- „A backup of these files will be made.”
- „Don't ask again”
- „JPEG Files (*.jpg)”
- „WebP Files (*.webp)”
- „Saving writes the picture without them, and the settings are lost. This cannot be undone.”
- „This cannot be undone and all changes will be lost.”
- „To undo the last save and keep edits click 'Undo Save'.”
- „File operation failed”

### `PicasaPy/EditorTabBar.qml` — 8

- „Common Fixes”
- „Fine Tuning”
- „Effects”
- „Creative”
- „More Effects”
- „Glimmer effects beyond the three known tabs”
- „Legacy Effects”
- „Filters left in the Picasa engine but not on its surface”

### `PicasaPy/PhotoViewer.qml` — 8

- „Start slideshow”
- „Retouch fixes cannot be recovered with redo.”
- „Redeye fixes cannot be recovered with redo.”
- „The caption will replace the text you have ”
- „Video playback requires the Qt Multimedia module.”
- „Render the final collage from this draft”
- „Show Faces”
- „Edit Faces”

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

### `PicasaPy/PhotoContextMenu.qml` — 7

- „Add to People Album”
- „Rotate Right”
- „Rotate Left”
- „Find Similar Pictures”
- „File on Disk”
- „Locate Original on Disk”
- „Block Upload”

### `PicasaPy/PicasaImportDialog.qml` — 7

- „Import from Picasa”
- „Looking for a previous Picasa installation…”
- „We found your previous Picasa installation. It ”
- „We couldn't find a previous Picasa installation ”
- „Browse manually...”
- „Not now”
- „Adopt”

### `PicasaPy/CollageDialogs.qml` — 6

- „The collage could not be saved”
- „The collage cannot be saved because all of the pictures ”
- „The current page format of the collage does not ”
- „Would you like to replace the existing one, or ”
- „The current collage contains unsaved changes.\n\n”
- „Please select the single image you want to place in ”

### `PicasaPy/EditorPanel.qml` — 6

- „Close crop to faces”
- „Compose around faces”
- „Crop by horizon”
- „Crop by color”
- „Crop by detail”
- „Full page (A4)”

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

- „Choose a size below, then drag on the picture to ”
- „This image's orientation has been modified by the ”
- „Delete this custom aspect ratio?”
- „Suggested crops”
- „Top left”

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

### `PicasaPy/TrayBar.qml` — 5

- „Waiting for the collage to be created…”
- „Add the pictures in the tray to an album”
- „This will clear your entire tray.”
- „Order Prints (service discontinued)”
- „Publish to Blogger (service discontinued)”

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

### `PicasaPy/OptionsTabSlideshow.qml` — 4

- „Loop slideshow”
- „Play MP3 music during slideshow”
- „Select a music folder:”
- „Browse...”

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

### `PicasaPy/EditorLegacyTab.qml` — 3

- „These filters come from older versions of Picasa. They are not available in today's Picasa, but your old edits may contain them.”
- „This name is a leftover from an old configuration. Picasa 3.9 has no processor for it either, so it cannot be applied.”
- „Picasa can read this filter from an old .picasa.ini, but its exact pixel operation has not been decoded yet, so it cannot be applied.”

### `PicasaPy/EditorRedeyePanel.qml` — 3

- „You can also draw a square around any red eye that”
- „Picasa has found and corrected red eye(s).”
- „No red eye was found automatically.”

### `PicasaPy/EmailChoiceDialog.qml` — 3

- „Send pictures by email”
- „The pictures will be attached to a new message in ”
- „Remember this choice and do not ask again”

### `PicasaPy/MainToolbar.qml` — 3

- „Tree folder view”
- „Search”
- „Kiadások megtekintése a GitHubon”

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

### `PicasaPy/PlacesPanel.qml` — 3

- „The map component (QtLocation) is not available. Geotags can still be edited.”
- „Right-click the map to place the selected pictures.”
- „Remove Geotag”

### `PicasaPy/QuickTagsConfigDialog.qml` — 3

- „Edit the 10 quick tag buttons shown at the bottom of the ”
- „Reserve the top two buttons for recently used tags”
- „Fill the empty boxes above with frequently used tags”

### `PicasaPy/TagContextMenu.qml` — 3

- „Add Tag to Entire Selection”
- „Find Items Tagged This Way”
- „Remove Tag”

### `PicasaPy/UnnamedFacesView.qml` — 3

- „Stop ignoring”
- „Move the selected people to the ignored ”
- „Are you sure you want to move this person to the ”

### `PicasaPy/ViewerContextMenu.qml` — 3

- „Rotate Right”
- „Rotate Left”
- „Block Upload”

### `PicasaPy/AboutDialog.qml` — 2

- „About PicasaPy”
- „A modern, open Picasa successor.”

### `PicasaPy/CollageClipsTab.qml` — 2

- „Load more pictures from the library”
- „Remove the selected pictures from the tray”

### `PicasaPy/CollagePanel.qml` — 2

- „Save the picture as a JPG in the Collages album, then set ”
- „Save as a JPG in the Collages album (in the Projects ”

### `PicasaPy/EditorRetouchPanel.qml` — 2

- „Click to select the area to fix. Then, move the”
- „Refining…”

### `PicasaPy/FolderPane.qml` — 2

- „Currently unavailable — the folder stays in the database, thumbnails come from the cache.”
- „Folders on Disk”

### `PicasaPy/PerfMonitorPanel.qml` — 2

- „Performance monitor”
- „Save diagnostics...”

### `PicasaPy/PicasaNotifier.qml` — 2

- „The collage is ready (click here)”
- „Copy saved”

### `PicasaPy/TagsPanel.qml` — 2

- „Add a tag...”
- „Select pictures to tag them.”

### `PicasaPy/TesztuzemNaploDialog.qml` — 2

- „Save Log As...”
- „Text Files”

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

### `PicasaPy/ConfirmDialog.qml` — 1

- „Don't ask again”

### `PicasaPy/DocumentTabStrip.qml` — 1

- „The current collage contains unsaved changes.\n\n”

### `PicasaPy/EditorEffectsTab1.qml` — 1

- „Focal Saturation”

### `PicasaPy/EditorEffectsTab3.qml` — 1

- „Comicize”

### `PicasaPy/EditorEffectsTab4.qml` — 1

- „Film Grain (Fine)”

### `PicasaPy/FacesOverlay.qml` — 1

- „Drag a rectangle over the face you want to add, then ”

### `PicasaPy/FolderStatePanel.qml` — 1

- „Select a folder on the left.”

### `PicasaPy/HistogramBox.qml` — 1

- „Histogram and camera information”

### `PicasaPy/ImportProgressPanel.qml` — 1

- „Importing”

### `PicasaPy/LightboxHeader.qml` — 1

- „Sync to the web”

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

### `PicasaPy/TrayContextMenu.qml` — 1

- „Keep Selection”

### `PicasaPy/VideoPlayerView.qml` — 1

- „Unable to play this video.”

