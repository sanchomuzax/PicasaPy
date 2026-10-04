# UI-lefedettség — az eredeti Picasa panelei ↔ a PicasaPy QML-fája

**Generálva:** 2026-10-04 — **ezt a fájlt ne írd kézzel**, újragenerálható.

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
| párosítva | 333 |
| másutt megvan (nem ezen a felületen) | 36 |
| hiányzik — **feltáratlan** (kutatói kör kell) | 0 |
| hiányzik — **lekutatva** (fejlesztői kör kell) | 258 |
| bizonytalan | 18 |
| nem értékelhető (rajzoló elem) | 1284 |
| **nem cél** (megszűnt szolgáltatás) — a nevezőből KIMARAD | 91 |
| **lefedettség az értékelhető elemeken** | **51.8%** |

> ⚠️ **A 51.8% ALSÓ BECSLÉS, nem pontos érték.** 18 elem `bizonytalan` — felirat nélküli vezérlő, amit a szkript gépi úton **nem tud eldönteni**; ezeket a nem-lefedett oldalon számoltuk. Ha mind megvolna, a lefedettség **54.6%** lenne. A valódi érték a kettő között van, és csak a bizonytalan elemek egyenkénti kimérésével szűkíthető.

## Rangsor — a tíz legnagyobb fehér folt

Jegynyitáshoz ez a sorrend: a hiányzó és a bizonytalan elemek száma panelenként.

| # | panel | hiány + bizonytalan | mit takar |
|---:|---|---:|---|
| 1 | `makemoviepanel` | 49 | Csak a filmkészítő párbeszéd van meg; interaktív filmkészítő panel nincs |
| 2 | `editpanel` | 22 | A szerkesztő teljes bal oldali panelje minden fülével — ÉS a gazdája, a PhotoViewer.qml (fejléc, előnézet, nagyítás-csúszka, felirat, kettős nézet) |
| 3 | `thumbui` | 18 | A fő könyvtárnézet egésze |
| 4 | `publish` | 18 | A panel 21 MÉRT vezérlője megvan (#2508: Ajándék-CD, biztonsági mentés, feltöltés — a mért helyeken és feliratokkal). ⚠️ A három üzemmód MŰKÖDÉSE még nincs kész, és a panel ezért szándékosan nincs bekötve a menübe; az elemenkénti párosítás ezt helyesen tükrözi (ami nincs megépítve, az nem párosul). A web_group hét eleme hatókörön kívül (online). |
| 5 | `printoptions` | 13 | Nyomtatási szegély- és feliratopciók (#1780); a Beállítások „Nyomtatás” füle MÁS panel |
| 6 | `choose_mail` | 12 | Levelezőprogram-választó párbeszéd — nincs nálunk |
| 7 | `capturemoviepanelpopup` | 11 | Webkamerás videofelvétel — nincs nálunk |
| 8 | `compose_mail` | 10 | Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül |
| 9 | `acquirepanel` | 8 | Importáló panel — nálunk párbeszédablak, nem teljes értékű bal oldali panel |
| 10 | `buttonmgr` | 8 | Gombsáv-testreszabó párbeszéd — nincs nálunk |

## Panelenkénti lefedettség

| panel | eredeti elem | értékelhető | párosítva | másutt | feltáratlan | lekutatva | bizonytalan | rajzoló | nem cél | megfeleltetés |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `makemoviepanel` | 111 | 55 | 1 | 5 | 0 | 49 | 0 | 56 | 0 | `CreateDialogs.qml` |
| `editpanel` | 312 | 125 | 102 | 1 | 0 | 22 | 0 | 187 | 0 | `EditorPanel.qml`, `EditorTabBar.qml`, `EditorTabCommonFixes.qml`, `EditorFinetunePanel.qml`, `EditorEffectsTab1.qml`, `EditorEffectsTab2.qml`, `EditorEffectsTab3.qml`, `EditorEffectsTab4.qml`, `EditorLegacyTab.qml`, `EditorCropPanel.qml`, `EditorRedeyePanel.qml`, `EditorRetouchPanel.qml`, `EditorParamPanel.qml`, `EditorDialogs.qml`, `EditTabButton.qml`, `EditTabIcon.qml`, `CropOverlay.qml`, `HistogramBox.qml`, `AddCustomAspectRatioDialog.qml`, `EditOverwriteDialog.qml`, `BatchEditProgressPanel.qml`, `ToolTile.qml`, `PhotoViewer.qml` |
| `thumbui` | 140 | 44 | 22 | 4 | 0 | 18 | 0 | 93 | 3 | `MainToolbar.qml`, `LightboxFeed.qml`, `ThumbDelegate.qml`, `TrayBar.qml`, `TimelineView.qml`, `PicasaScrollBar.qml`, `FolderPane.qml`, `FolderTreeItem.qml`, `FolderStateBadge.qml`, `SlideshowView.qml`, `Main.qml` |
| `publish` | 125 | 30 | 12 | 0 | 0 | 18 | 0 | 95 | 0 | `PublishPanel.qml` |
| `printoptions` | 49 | 29 | 13 | 3 | 0 | 13 | 0 | 20 | 0 | `PrintOptionsPanel.qml`, `PrintDialog.qml` |
| `choose_mail` | 24 | 13 | 0 | 1 | 0 | 12 | 0 | 11 | 0 | **nincs-megfeleltetes** — Levelezőprogram-választó párbeszéd — nincs nálunk |
| `capturemoviepanelpopup` | 45 | 12 | 0 | 1 | 0 | 11 | 0 | 33 | 0 | **nincs-megfeleltetes** — Webkamerás videofelvétel — nincs nálunk |
| `compose_mail` | 41 | 10 | 0 | 0 | 0 | 10 | 0 | 31 | 0 | **nincs-megfeleltetes** — Levélszerkesztő panel — nálunk a küldés Python-oldali, saját felület nélkül |
| `acquirepanel` | 67 | 20 | 12 | 0 | 0 | 6 | 2 | 43 | 4 | `PicasaImportDialog.qml`, `ImportSourceDialog.qml`, `ImportProgressPanel.qml`, `ImportDropArea.qml` |
| `buttonmgr` | 29 | 13 | 0 | 5 | 0 | 8 | 0 | 16 | 0 | **nincs-megfeleltetes** — Gombsáv-testreszabó párbeszéd — nincs nálunk |
| `collagepanel` | 108 | 55 | 48 | 0 | 0 | 4 | 3 | 53 | 0 | `CreateDialogs.qml`, `CollagePanel.qml`, `CollagePanelTabBar.qml`, `CollagePanelTabButton.qml`, `CollageSettingsTab.qml`, `CollageClipsTab.qml`, `CollageActionRow.qml`, `CollageZOrderColumn.qml`, `CollageSnapColumn.qml`, `CollageRandomRow.qml`, `CollageContextMenus.qml`, `CollageCanvas.qml`, `CollageFormatMenu.qml`, `CollageThemePopup.qml`, `CollageBorderPicker.qml`, `CollageBackgroundBox.qml`, `CollageNode.qml`, `CollageGroupNode.qml`, `CollageSheet.qml`, `CollageRing.qml`, `CollageProgressOverlay.qml`, `CollageDialogs.qml`, `CollageDraftDialog.qml`, `CollageDoneNotice.qml` |
| `titledialog` | 18 | 7 | 0 | 0 | 0 | 7 | 0 | 11 | 0 | **nincs-megfeleltetes** — Filmes címdia-szerkesztő párbeszéd — nincs nálunk |
| `faceheaderpanel` | 39 | 13 | 8 | 0 | 0 | 5 | 0 | 26 | 0 | `LightboxHeader.qml`, `UnnamedFacesView.qml`, `FacesOverlay.qml`, `PeopleAlbumContextMenu.qml` |
| `geopanel` | 14 | 5 | 0 | 0 | 0 | 4 | 1 | 9 | 0 | `PlacesPanel.qml`, `PlacesMap.qml` |
| `searchcontainer` | 25 | 11 | 7 | 0 | 0 | 4 | 0 | 14 | 0 | `MainToolbar.qml`, `SearchSuggestions.qml` |
| `initialscan` | 18 | 4 | 0 | 0 | 0 | 4 | 0 | 14 | 0 | `InitialScanDialog.qml` |
| `panelroot` | 14 | 7 | 2 | 1 | 0 | 4 | 0 | 7 | 0 | `Main.qml`, `MainToolbar.qml` |
| `throttle` | 10 | 4 | 1 | 0 | 0 | 4 | 0 | 5 | 0 | `PicasaScrollBar.qml` |
| `searchoptions` | 9 | 6 | 2 | 0 | 0 | 4 | 0 | 3 | 0 | `SearchGroupHeader.qml`, `MainToolbar.qml` |
| `printpanel` | 73 | 33 | 30 | 0 | 0 | 3 | 0 | 40 | 0 | `PrintDialog.qml` |
| `editoneup` | 34 | 5 | 0 | 2 | 0 | 3 | 0 | 29 | 0 | `PhotoViewer.qml` |
| `oneup` | 33 | 5 | 0 | 2 | 0 | 3 | 0 | 28 | 0 | `PhotoViewer.qml` |
| `headerpanel` | 30 | 7 | 4 | 0 | 0 | 3 | 0 | 19 | 4 | `LightboxHeader.qml` |
| `video_control_bar` | 24 | 6 | 3 | 0 | 0 | 3 | 0 | 18 | 0 | `VideoPlayerView.qml` |
| `peoplepanel` | 14 | 6 | 1 | 2 | 0 | 3 | 0 | 8 | 0 | `PeoplePanel.qml`, `PeoplePanelRow.qml` |
| `gedialog` | 13 | 5 | 1 | 1 | 0 | 3 | 0 | 8 | 0 | `PlacesPanel.qml`, `PlacesMap.qml` |
| `rightdrawerpanel` | 9 | 3 | 0 | 0 | 0 | 3 | 0 | 6 | 0 | `PropertiesPanel.qml` |
| `edittextpanel` | 45 | 19 | 17 | 0 | 0 | 2 | 0 | 26 | 0 | `EditorTextPanel.qml`, `TextColorSwatches.qml` |
| `foldermgr` | 32 | 11 | 4 | 5 | 0 | 2 | 0 | 21 | 0 | `FolderManagerDialog.qml` |
| `tagpanel` | 24 | 8 | 6 | 0 | 0 | 0 | 2 | 16 | 0 | `TagsPanel.qml` |
| `unknownfaceheaderpanel` | 18 | 6 | 4 | 0 | 0 | 2 | 0 | 12 | 0 | `UnnamedFacesView.qml` |
| `video_control_bar2` | 18 | 4 | 2 | 0 | 0 | 2 | 0 | 14 | 0 | `VideoPlayerView.qml` |
| `instructionpanel` | 7 | 2 | 0 | 0 | 0 | 2 | 0 | 5 | 0 | **nincs-megfeleltetes** — Betanító buborék („Learn more…”) — nincs nálunk |
| `movieeditpanel` | 7 | 4 | 2 | 0 | 0 | 2 | 0 | 3 | 0 | `VideoPlayerView.qml` |
| `outputlayout` | 31 | 9 | 7 | 1 | 0 | 1 | 0 | 22 | 0 | `TrayBar.qml` |
| `keywords` | 18 | 7 | 5 | 1 | 0 | 0 | 1 | 11 | 0 | `TagsPanel.qml` |
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

### `thumbui` — 18 hiány · panel-megfeleltetés: `parositva`

A fő könyvtárnézet egésze

- `acquirebutton` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `buttonbarsets` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: thumbui.tre:406)
- `buttongroup1` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: macros.tre:196)
- `cdmode` „Gift CD” (magyarul: „Ajándék CD”) — 🔧 **lekutatva**, csak nem megépítve (kézi: ajandek-cd-kimenet.md)
- `editpanel` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `fullview` „Edit photos” (magyarul: „Fotók szerkesztése”) — 🔧 **lekutatva**, csak nem megépítve (picasa-gyorsbillentyuk.md: 0x005e6178)
- `hlisthandle` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `hlistsizer` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `hviewtoggle` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `listdecrect` — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: thumbui.tre:516)
- `listdetail` — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `next` buboréksúgó: „View the next Photo” — 🔧 **lekutatva**, csak nem megépítve (konyvtar-ablak-meretek.md: respack.yt:3280882)
- `prev` buboréksúgó: „View the previous Photo” — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: thumbui.tre:43)
- `searchgroup` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: thumbui.tre:441)
- `single_action_message` „Select items to add to your project's clips tray, then press the "Back" button to return to your project” (magyarul: „Jelölje ki azokat az elemeket, amelyeket a projekt kliptálcájára fel szeretne venni, majd a "Vissza" gombra kattintva térjen vissza a projekthez”) — 🔧 **lekutatva**, csak nem megépítve (getmore-klipgyujto-mod.md: thumbui.tre:660)
- `toggle_right_drawer` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: 0x00632060)
- `visitweb` „Web View” (magyarul: „Internetes nézet”) — 🔧 **lekutatva**, csak nem megépítve (kézi: picasa-fo-ablak-elrendezes.md)
- `webcambutton` buboréksúgó: „Capture photos or video from a webcam or other video device” — 🔧 **lekutatva**, csak nem megépítve (getmore-klipgyujto-mod.md: 0x009ca5e0)

### `publish` — 18 hiány · panel-megfeleltetés: `parositva`

A panel 21 MÉRT vezérlője megvan (#2508: Ajándék-CD, biztonsági mentés, feltöltés — a mért helyeken és feliratokkal). ⚠️ A három üzemmód MŰKÖDÉSE még nincs kész, és a panel ezért szándékosan nincs bekötve a menübe; az elemenkénti párosítás ezt helyesen tükrözi (ami nincs megépítve, az nem párosul). A web_group hét eleme hatókörön kívül (online).

- `backup_eject` „Eject” (magyarul: „Kiadás”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `backup_help` „Help” (magyarul: „Súgó”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `backupcdheader2` „Choose folders & albums to back up” (magyarul: „Mappák és albumok kijelölése biztonsági másolat készítéséhez”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `backuptext3` „Check the folders you want to back up, or choose 'Select All' to choose everything.” (magyarul: „Jelölje ki azokat a mappákat, amelyekről biztonsági másolatot szeretne készíteni, vagy "Az összes kijelölése" gombra kattintva az összes elemet jelölje ki.”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `giftcdtext` „The items selected with a checkmark above will be included on your Gift CD.   To add more items click the "Add More" button below.” (magyarul: „A program a fent pipával kijelölt elemeket másolja az ajándék CD-re. További elemek felvételéhez kattintson az alábbi "Továbbiak hozzáadása" gombra.”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `label_rpoptionbox1` „Upload” (magyarul: „Feltöltés”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `label_rpoptionbox2` „Change options” (magyarul: „Opciók módosítása”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `label_rpoptionbox3` „Remove online” (magyarul: „Eltávolítás: online elemek”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `picsizemenu` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005ba010)
- `presentcd_eject` „Eject” (magyarul: „Kiadás”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `presentcd_help` „Help” (magyarul: „Súgó”) — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `replicate_button_group` — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `replicate_go` „OK” (magyarul: „OK”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066bf90)
- `rpoptionbox1` buboréksúgó: „Selected folder and/or albums will be uploaded” — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `rpoptionbox2` buboréksúgó: „Selected folders and/or albums will be updated online with the options specified in the menus to the right” — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)
- `upgradestorage` „Upgrade storage” (magyarul: „Tárhely bővítése”) — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066cb20)
- `uploadallsync` buboréksúgó: „Change the sync setting for the selected folders and/or albums” — 🔧 **lekutatva**, csak nem megépítve (ajandek-cd-kimenet.md: 0x0066cb20)
- `webpublish_cancel` — 🔧 **lekutatva**, csak nem megépítve (kézi: biztonsagi-mentes.md)

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

### `choose_mail` — 12 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

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

### `faceheaderpanel` — 5 hiány · panel-megfeleltetés: `parositva`

Névvel ellátott arc-album fejléce

- `create_face_movie` buboréksúgó: „Create Face Movie” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `create_movie` buboréksúgó: „Create Movie Presentation” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `play` buboréksúgó: „Play Fullscreen Slideshow” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `pwa_button` buboréksúgó: „Open PWA web page” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `set_thumbnail` buboréksúgó: „Set as People Album Thumbnail” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)

### `geopanel` — 5 hiány · panel-megfeleltetés: `parositva`

Helyek panel

- `map_menu` — 🔧 **lekutatva**, csak nem megépítve (picasa-eger-es-kijeloles.md: 0x005ba010)
- `search` — *bizonytalan*
- `search_group` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: geopanel.tre:61)
- `search_label` „Search for an address:” (magyarul: „Cím keresése:”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: 0x00567a00)
- `searchinput` — 🔧 **lekutatva**, csak nem megépítve (jobb-fiok-meretek.md: geopanel.tre:61)

### `searchcontainer` — 4 hiány · panel-megfeleltetés: `parositva`

Keresősáv és szűrőgombjai

- `search` — 🔧 **lekutatva**, csak nem megépítve (picasa-keptalca.md: 0x005675d0)
- `searchautocomplete` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-mainwindow.md: searchcontainer.tre:31)
- `searchbutton` — 🔧 **lekutatva**, csak nem megépítve (picasa-gyorsbillentyuk.md: 0x009cd8a0)
- `webview` buboréksúgó: „Show uploads to web albums only” — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: 0x00660c80)

### `initialscan` — 4 hiány · panel-megfeleltetés: `parositva`

Első indítás — mit vizsgáljunk át

- `cancel` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)
- `radio_complete` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)
- `radio_limited` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)
- `radiogroup` — 🔧 **lekutatva**, csak nem megépítve (picasa-elso-inditas.md: initialscan.tre:113)

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

### `searchoptions` — 4 hiány · panel-megfeleltetés: `parositva`

Keresési eredmény fejléce

- `dupesearch` — 🔧 **lekutatva**, csak nem megépítve (picasa-fo-ablak-elrendezes.md: 0x0040bf70)
- `facesearch` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: searchoptions.tre:97)
- `searchcenter` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: searchoptions.tre:97)
- `searchresult` — 🔧 **lekutatva**, csak nem megépítve (picasa-kereses-modok.md: searchoptions.tre:97)

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

### `headerpanel` — 3 hiány · panel-megfeleltetés: `parositva`

Album- és mappafejléc a rács fölött

- `create_movie` buboréksúgó: „Create Movie Presentation” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: faceheaderpaneltext.tre:44)
- `play` buboréksúgó: „Play Fullscreen Slideshow” — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: acquirepanel.tre:210)
- `websync0` buboréksúgó: „Upload and sync future changes to the web” — 🔧 **lekutatva**, csak nem megépítve (picasa-arcfelismeres.md: 0x005e0f70)

### `video_control_bar` — 3 hiány · panel-megfeleltetés: `parositva`

Videó vezérlősáv (vágás is)

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-editor.md: video_control_bar.tre:22)
- `trimslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x005952d0)
- `volumeslider` — 🔧 **lekutatva**, csak nem megépítve (ui-audit-editor.md: video_control_bar.tre:22)

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

### `edittextpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Szöveg-eszköz panelje

- `colorpicker_bevel` — 🔧 **lekutatva**, csak nem megépítve (szerkeszto-panel-meretek.md: edittextpanel.tre:7)
- `sizelist` — 🔧 **lekutatva**, csak nem megépítve (szerkeszto-panel-meretek.md: edittextpanel.tre:7)

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

### `video_control_bar2` — 2 hiány · panel-megfeleltetés: `parositva`

Videó vezérlősáv második változata

- `scaleslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: video_control_bar2.tre:79)
- `volumeslider` — 🔧 **lekutatva**, csak nem megépítve (picasa-create-features.md: video_control_bar2.tre:79)

### `instructionpanel` — 2 hiány · panel-megfeleltetés: `nincs-megfeleltetes`

Betanító buborék („Learn more…”) — nincs nálunk

- `close` „Close” (magyarul: „Bezárás”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: 0x007d3f90)
- `learn_more` „Learn more...” (magyarul: „További információ...”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x0074c760)

### `movieeditpanel` — 2 hiány · panel-megfeleltetés: `parositva`

Videovágó panel

- `export_movie` „Export Clip” (magyarul: „Klip exportálása”) — 🔧 **lekutatva**, csak nem megépítve (picasa-menu-parancsok-viselkedes.md: 0x005952d0)
- `export_youtube` „Upload to YouTube” (magyarul: „Feltöltés a YouTube webhelyre”) — 🔧 **lekutatva**, csak nem megépítve (picasa-feltolteskezelo.md: movieeditpanel.tre:20)

### `outputlayout` — 1 hiány · panel-megfeleltetés: `parositva`

A tálca alatti kimeneti gombsáv

- `blogger` „Blogger” (magyarul: „Blogger”) — 🔧 **lekutatva**, csak nem megépítve (binaris-regeszet-modszertan.md: outputlayout.tre:99)

### `keywords` — 1 hiány · panel-megfeleltetés: `parositva`

Címkeszerkesztő

- `keywordlist` — *bizonytalan*

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

### `editpanel` — 1

- `showtextlabel` — „Show Text” itt: PicasaPy/PicasaMenuBar.qml

### `thumbui` — 4

- `albumview` — „Back To Library” itt: PicasaPy/PhotoViewer.qml, PicasaPy/ViewerContextMenu.qml
- `backup` — „Backup” itt: PicasaPy/PublishPanel.qml
- `librarylabel` — „Library” itt: PicasaPy/DocumentTabStrip.qml
- `sbutton` — „Slideshow” itt: PicasaPy/OptionsDialog.qml, PicasaPy/PicasaMenuBar.qml

### `printoptions` — 3

- `border_size_label` — „Border width” itt: PicasaPy/EditorParamPanel.qml
- `usecaption_label` — „Caption” itt: PicasaPy/PicasaMenuBar.qml
- `usefilename_label` — „File name” itt: PicasaPy/PicasaMenuBar.qml

### `choose_mail` — 1

- `remember` — „Remember this setting, don't display this dialog again.” itt: PicasaPy/EmailChoiceDialog.qml

### `capturemoviepanelpopup` — 1

- `stop` — „Stop” itt: Main.qml, PicasaPy/PublishPanel.qml

### `buttonmgr` — 5

- `add` — „Add >>” itt: PicasaPy/ConfigureButtonsDialog.qml
- `movedown` — „Move Down” itt: PicasaPy/ConfigureButtonsDialog.qml
- `moveup` — „Move Up” itt: PicasaPy/ConfigureButtonsDialog.qml
- `remove` — „<< Remove” itt: PicasaPy/ConfigureButtonsDialog.qml
- `usedefaults` — „Reset to Defaults” itt: PicasaPy/ConfigureButtonsDialog.qml

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

### `outputlayout` — 1

- `makemovie` — „Movie” itt: PicasaPy/CreateDialogs.qml, PicasaPy/PicasaMenuBar.qml

### `keywords` — 1

- `keywords_label` — „Tags:” itt: Main.qml, PicasaPy/PicasaMenuBar.qml, PicasaPy/TrayBar.qml

### `uploadmgr` — 1

- `hide` — „Hide” itt: PicasaPy/PhotoContextMenu.qml, PicasaPy/PicasaMenuBar.qml, PicasaPy/ViewerContextMenu.qml

## A mi többletünk — nálunk van, az eredetiben nincs ilyen szöveg

A QML `qsTr(...)` feliratai, amelyeknek nincs párja sem a `.tre` leltárban, sem a `stringres` szövegtárban. Ez **nem automatikusan hiba**: lehet jogos új funkció (pl. teljesítménymérő) vagy más szóhasználat — de **idegen elemet is jelezhet**, mint a #704-ben a „Kreatív”/„Effektek” fejlécsáv.

Összesen **468 felirat** 86 fájlban.

Besorolás (`docs/specs/ui-tobblet-besorolas.tsv`, #2921): saját funkció: **69** · szükséges segédszöveg: **161** · valódi eltérés: **9** · a mérő vakfoltja — az eredetiben is megvan: **148** · bizonytalan: **6** · besorolatlan: **75**

### Hogyan kell ezt a listát olvasni (#2921)

A tételek **három** csoportba esnek, és csak a harmadik hiba:

1. **saját funkció** — olyasmi, ami az eredetiben nincs (Sötét téma, Teljesítmény-monitor, Duplikátum-kereső). Ezek a `#1187` konvenciója szerint védett-funkció jelölőt és sort kapnak a `docs/decisions/vedett-sajat-funkciok.md`-ben.
2. **szükséges segédszöveg** — hibaüzenet, üres-állapot, megerősítő kérdés, aminek azért nincs eredeti párja, mert a helyzet sem áll elő az eredetiben.
3. **valódi eltérés** — az eredetinek VAN szövege ugyanabban a helyzetben, csak mi máshogy fogalmaztuk. Ez javítandó, nem jelölendő; az őre a `tests/app/test_hivatalos_feliratok_3358.py`.

⛔ **A `szükséges segédszöveg` szándékosan NEM kap jelölést** (#2921 döntése). A védett-funkció jelölő rendeltetése, hogy egy későbbi „igazítsuk az eredetihez” kör ne törölje ki azt, amit szándékosan építettünk — egy hibaüzenet viszont nem funkció: a jelölés több száz sorral hígítaná a jegyzéket, és épp azt a jelzést oltaná ki, amiért a jegyzék van. Ez a bekezdés azért áll itt, hogy a következő kör ne olvassa végig újra ugyanezt a csoportot.

⚠️ **Ez a lista a közeli-pár mérés BEMENETE** (`eszkozok/meres/felirat_kozeli_parok.py`), tehát a mérés előtt **regeneráld a lapot**. Mérve 2026-09-20: a lista még hozta az „Add Tag to Entire Selection” tételt, amit a #3358 addigra kijavított — az elavult bemenet nem létező feliratokat soroltat be.

**Amit a korábbi körök már KIZÁRTAK** (magas hasonlóság ≠ azonos tétel; ne mérd újra):

- **téma-előtagos nevek** (`collage::grid_desc` és társai) — a név az erőforrás-azonosító része, nem felirat;
- **vezető `\n\n`** (SaveDialogs) — ugyanaz a szöveg, csak tördeléssel;
- **platform-változatok** (`CInitialScanDialog::OnlySearchWin`);
- **véletlen szóátfedés** és **más szerepű pár**: pl. a `FolderPane` „Folders on Disk” felirata 0,97-tel illeszkedik a `CAcquireUI::folderondisk` EGYES számú „Folder on Disk”-jére, ami az eredetiben a gyűjtemény alapértelmezett NEVE — ez nem bizonyítható eltérés.

### `PicasaPy/ExportDialogs.qml` — 22

- „Export to Folder”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Preserves original image quality”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Good balance of quality and size”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Very large file size, preserves fine detail”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Smallest file size, some quality loss”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Maximum”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Minimum”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Export location:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Browse...”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk a hivatalossal egyezik, csak …/... eltérés („Tallózás…”).
- „Name of exported folder:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Add numbers to file names to preserve order”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Use original size”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Resize to:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „pixels”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Image quality:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Export movies using:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „First frame”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Full movie (no resizing)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Watermark:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Add watermark”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „Stamp photos with your name, a web domain, or a copyright notice.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalos export.fen-fordítással.
- „None of the selected pictures has a location, so no Google Earth file was written.”
  - *szükséges segédszöveg* — Egyik kijelölt képnek sincs helyadata, ezért nem készült Google Earth-fájl állapotüzenet; a Google Earth-export hivatalos szövegei (EarthController::*) között nincs ilyen "nincs helyadat" eset — ez a mi saját visszajelzésünk.

### `Main.qml` — 21

- „No pictures have that tag.”
  - *szükséges segédszöveg* — Hibauzenet: nincs talalat a cimkere - a helyzet (ures cimke-kereses eredmenye) az eredetiben sem generalna kiirt szoveget, nem talalhato megfelelo a korpuszban.
- „The search results could not be saved as an album.”
  - *szükséges segédszöveg* — Hibauzenet a kereses-mentes sikertelensegerol; nincs talalhato eredeti megfelelo.
- „Background work is still running (export, web export or ”
  - *szükséges segédszöveg* — A kilépési figyelmeztetés az eredetiben csak a FELTÖLTÉSEKRE szól (CUploadManagerThread::message, „a Picasa legközelebbi indításakor újraindulnak”); export/webexport/arcfelismerés közbeni kilépésre nincs eredeti üzenet, ez a helyzet a miénk.
- „Exit PicasaPy”
  - *szükséges segédszöveg* — A kilepes-megerosito dialogus CIME; a Win32 MessageBox eredetiben alapertelmezetten az app nevet mutatta cimkent (nem authoralt sztringforras), nalunk a PicasaPy nev sajat dialogus-cim.
- „There are no files on the clipboard to paste.”
  - *szükséges segédszöveg* — Hibauzenet: ures vagolap beillesztesnel; nincs talalhato eredeti megfelelo.
- „This will create an album with more than 1000 images.”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „You are about to erase all geographic location information”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a ClearGeoTag::warn hivatalos magyarjával; az angol csak az összefűzés miatt tűnt eltérőnek.
- „Change Location”
  - *szükséges segédszöveg* — A helyszin-modositas megerosito dialogus CIME; nincs talalhato eredeti authoralt cim-sztring (a GeoPanel figyelmezteto uzenetnek nincs kulon cime a korpuszban).
- „You have more than a few items selected.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a GeoPanel::geotag_warning_change hivatalos magyarjával, csak a helyőrző szintaxisa (%d → %1) más.
- „This will remove all edits you have made to the”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „This will remove all edits you have made to ALL of”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „Clear Sample”
  - *szükséges segédszöveg* — A hasonlosag-minta torles gombjanak felirata; az eredetiben a clearsim vezerlo ikon-csak (nincs authoralt felirat-sztring).
- „Duplicate Files”
  - *szükséges segédszöveg* — A masodpeldany-kereses mod-felirata a also savon; az eredeti searchoptions/dupesearch ikon-csak, nincs authoralt felirat.
- „Looking for duplicate files...”
  - *szükséges segédszöveg* — Allapotszoveg a masodpeldany-kereses folyamataban; nincs talalhato eredeti megfelelo.
- „Updating similarity database ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „This folder is currently unavailable (for example a disconnected drive or network share). Its photos stay in the database and thumbnails come from the cache, but the original files cannot be opened or edited right now.”
  - *szükséges segédszöveg* — Sajat UX-kiegeszites: halozati/kulso meghajtos mappa ideiglenes elerhetetlensegenek magyarazata; nincs talalhato eredeti megfelelo egyik korpuszban sem.
- „Are you sure you want to remove the selected ”
  - ⚠️ *besorolatlan*
- „New person's name:”
  - *szükséges segédszöveg* — Uj szemely nevet kero mezo felirata; nincs talalhato eredeti megfelelo prompt-szoveg egyik korpuszban sem.
- „Wrong password”
  - *szükséges segédszöveg* — A rejtett mappak feloldasi hibajanak dialogus-cime; a CThumbUI::PassVerifyWrong ('The passwords did not match.') MAS helyzetre vonatkozik (jelszo ketszeri beirasanak eltereser jelszo-BEALLITASNAL), nem a mar tarolt jelszo elleni ELLENORZESRE feloldaskor - a helyzet nem egyezik biztosan.
- „The password does not match. The hidden folders stay hidden.”
  - *szükséges segédszöveg* — Lasd elozo sor indoklasat - ugyanaz a dialogus uzenete, mas helyzet mint a talalt CThumbUI::PassVerifyWrong.
- „WARNING! This will DELETE all people albums, ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).

### `PicasaPy/OptionsTabGeneral.qml` — 21

- „User interface:”
  - ⚠️ *besorolatlan*
- „Use special effects”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/UITransitions.title hivatalos magyarjával.
- „Show tooltips”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/ShowTooltips.title egyik hivatalos magyar változatával.
- „Single click to exit the editing view”
  - ⚠️ *besorolatlan*
- „Language:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/labelgroup25.title hivatalos magyarjával.
- „Files:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/labelgroup10.title hivatalos magyarjával.
- „Detect duplicates on import”
  - *valódi eltérés* — SZÁNDÉKOS: a kód kommentje: „a fen teljes szövegkiírása nincs a lapon — a feliratot ezért NEM írjuk át egyetlen idézet alapján”; a hivatalos magyar azóta megvan. Hivatalos magyar: „Másodpéldányok észlelése az importálás során” — nálunk: „Duplikátumok észlelése importáláskor”. (hivatalos: `options/autoexclude.title` „”)
- „Clear Cache...”
  - *szükséges segédszöveg* — Az eredeti disposepreviews egy jelölőnégyzet; a kód kommentje szerint ez a gomb annak „megfelelője”, de más vezérlő, más szöveggel.
- „Empty the thumbnail cache? The thumbnails are ”
  - *szükséges segédszöveg* — Saját megerősítő kérdés a gyorsítótár-ürítés gombjához; nincs megfelelője a forrásokban.
- „Empty”
  - *szükséges segédszöveg* — A fenti saját megerősítő kérdés Igen gombjának felirata.
- „Keep”
  - *szükséges segédszöveg* — A fenti saját megerősítő kérdés Nem gombjának felirata.
- „Delete from disk without confirmation”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/DoNotConfirmDeleteFromDisk.title hivatalos magyarjával.
- „Remove from album without confirmation”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/DoNotConfirmRemoveFromAlbum.title hivatalos magyarjával.
- „Help improve PicasaPy:”
  - ⚠️ *besorolatlan*
- „Send anonymous usage statistics”
  - ⚠️ *besorolatlan*
- „Automatic updates:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/labelgroup20.title hivatalos magyarjával.
- „Update automatically”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/item22.title hivatalos magyarjával.
- „Prompt before downloading updates”
  - ⚠️ *besorolatlan*
- „Never check for updates”
  - ⚠️ *besorolatlan*
- „Import destination folder:”
  - ⚠️ *besorolatlan*
- „Browse...”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk egyezik az options/importdest.title hivatalos magyarjával (csak …/... különbség).

### `PicasaPy/PicasaMenuBar.qml` — 18

- „TEST MODE — logging startup”
  - *saját funkció* — A tesztüzem (Test Mode) állapotjelzője a menüsorban. A fájl `#1701` megjegyzése kifejezetten kimondja: "a tesztüzem a PicasaPy saját eszköze — az eredeti Picasában nincs megfelelője".
- „Undo Paste All Effects”
  - *szükséges segédszöveg* — A funkció megvan, de a menütétel nem: a kódkomment szerint TUDATOS TÖBBLET — az eredeti Szerkesztés menüjének 11 mért kulcsa közt nincs visszavonás.
- „Undo Batch Edit”
  - *szükséges segédszöveg* — A funkció megvan, de a menütétel nem: a kódkomment szerint TUDATOS TÖBBLET — az eredeti Szerkesztés menüjében nincs visszavonás.
- „Dark Theme”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja a Sötét témát (Theme.qml, #28/#1364): "Az eredeti Picasa 3.9-nek egyetlen, világos megjelenése van." Ez a menütétel indítja a sötét témát.
- „Recent &changes”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja: "PicasaMenuBar.qml (#1595) — a Mappa ▸ Rendezés ▸ »Legutóbbi változtatások« tétel... nincs benne »legutóbbi változtatások«... Nálunk viszont működő, hasznos rendezés."
- „Show”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mért Mappa menü 3. csoportja „Elrejtés · Megjelenítés” (docs/specs/picasa-menusor-csoportok.md); a mi magyarunk („Megjelenítés”) ezzel betűre egyezik.
- „New Movie...”
  - *szükséges segédszöveg* — A Létrehozás ▸ Mozgófilm ALMENÜ egyetlen tétele. A fájl megjegyzése szerint (#324 audit) az eredetiben ez almenü volt TÖBB tétellel (pl. eMenuCreateMovie::ID_FACES "From Faces in Selection...", ID_FACESRANDOM "From People Albums..."), nálunk csak az egyetlen működő filmkészítés maradt az almenü tartalmaként — ez az összevont, saját felirat, a konkrét eredeti tételek egyikével sem azonos.
- „Find Faces...”
  - *szükséges segédszöveg* — Az arckeresés funkció megvan, de menüparancs nincs: a kódkomment szerint a „Find Faces” felirat a teljes szövegtárban nem szerepel, az Eszközök menü kimért szerkezetében nincs ilyen tétel (a „Scanning for faces...” állapotüzenet más helyzet).
- „Manage Duplicates...”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja: "PicasaMenuBar.qml (#287) — a Duplikátum-kereső párbeszéd az Eszközök menüben... önálló kereső-párbeszéd nincs. A miénk tudatos hozzáadás." (Az eredetiben helyette az eMenuTools::ID_DUPES "Show Duplicate Files" és az importáláskori/keresősávos mechanizmus él.)
- „Compact Database...”
  - *szükséges segédszöveg* — Az adatbázis-tömörítés funkció megvan (compacting.fen), de menüparancs nincs: a kimért Kísérleti almenü kilenc tétele közt nem szerepel.
- „Language”
  - *szükséges segédszöveg* — A nyelvválasztás funkció megvan, de az eredetiben a Beállítások párbeszéd „Nyelv:” mezőjében, nem menüben — a menütétel helyzete nincs meg.
- „Import from Picasa...”
  - *saját funkció* — Ez a menütétel nyitja meg a PicasaDataImportDialog.qml-t, amit a docs/decisions/vedett-sajat-funkciok.md kifejezetten véd (#3132) — az eredetinek nincs és nem is lehet ilyen parancsa, hiszen ő maga a régi adatbázis gazdája.
- „Online Information”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („&Online információ”, csak a gyorsbillentyű-jel hiányzik); az angol eltérés a magyar felületen nem látszik.
- „Product Release Notes”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („&Termékkiadási tájékoztató”, csak a gyorsbillentyű-jel hiányzik).
- „Performance Monitor”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja: "PicasaMenuBar.qml (#1364) — a Teljesítmény-monitor a Súgó menüben: fejlesztői eszköz, az eredetiben nincs ilyen menüpont."
- „Test Mode (logs the next startup)”
  - *saját funkció* — A fájl saját megjegyzése (`sajat: true`, #1701) kifejezetten kimondja: "a tesztüzem a PicasaPy saját eszköze — az eredeti Picasában nincs megfelelője."
- „Send Log...”
  - *saját funkció* — A "Napló elküldése..." menütétel a tesztüzem (Test Mode, #1701/#1654/#2553) saját eszközének a része — ugyanaz a saját funkció, mint a #142-es sor.
- „About PicasaPy”
  - *valódi eltérés* — SZÁNDÉKOS: a program neve PicasaPy, ezért „A PicasaPy névjegye” — a hivatalos szerkezet („A Picasa névjegye”) szerint, csak a terméknév más. Ugyanaz a Súgó-menütétel; a különbség csak a terméknév (kódkomment nem mondja ki szándékként). Hivatalos: „A Picasa &névjegye” → nálunk: „A PicasaPy névjegye”. (hivatalos: `eMenuHelp::ID_HELP_ABOUT` „&About Picasa”)

### `PicasaPy/CreateDialogs.qml` — 16

- „Select pictures in the library first, or put them in the Picture Tray.”
  - *szükséges segédszöveg* — Üres-állapot súgószöveg a kollázskészítő dialógusban, ha nincs kiválasztott kép; nincs rá eredeti megfelelő a forrásokban.
- „Collage type:”
  - *szükséges segédszöveg* — A kollázs funkció megvan, de az eredetiben a típus a kollázspanel téma-választóján dől el, felirat nélkül; „Kollázs típusa:” címke nincs.
- „Mosaic”
  - *a mérő vakfoltja — az eredetiben is megvan* — A téma-választó kétsoros szövegének névrésze („Mozaik: a képek automatikus illesztése…”) a mi magyarunkkal („Mozaik”) egyezik.
- „Frame Mosaic”
  - ⚠️ *besorolatlan*
- „Grid”
  - *a mérő vakfoltja — az eredetiben is megvan* — A téma-választó szövegének névrésze („Rács: a képek szabályos sorokba…”) a mi magyarunkkal („Rács”) egyezik.
- „Multiple Exposure”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Többszörös exponálás”).
- „Target file:”
  - *szükséges segédszöveg* — A kollázs célfájljának felirata egy saját, fájl-mentés-dialógus alapú létrehozási folyamathoz tartozik; az eredeti collagepanel (panel-feliratok-hu.tsv) nem ismer ilyen 'Target file:' feliratot — ott a kollázs mentése a 'Kollázs létrehozása' gombbal történik, külön célfájl-mező nélkül.
- „(not selected)”
  - *szükséges segédszöveg* — Lásd a 'Target file:' sor indoklását — ugyanahhoz a saját fájlválasztó-mezőhöz tartozó helyőrző szöveg.
- „Browse...”
  - *szükséges segédszöveg* — Az eredeti a kollázst a Kollázsok albumba menti, célfájl-tallózás nincs; a funkció megvan, ez a gomb nem.
- „JPEG images (*.jpg)”
  - *szükséges segédszöveg* — Qt FileDialog fájlszűrő-string; az eredeti natív mentési párbeszéd szűrőformátuma szerkezetileg más (pl. CThumbUI::SaveAsFilterJPG = 'JPEG Files', a minta külön mezőben), nincs egyező egysoros forrás.
- „The movie's pictures and timing come from the ”
  - *szükséges segédszöveg* — A kód-komment (#2114) kimondottan saját kiegészítésnek nevezi: 'a projektfájl a diaidőt és a képeket őrzi meg, a felbontást nem — ezt kimondjuk, nem találgatunk.'
- „Video size:”
  - *szükséges segédszöveg* — A film méretbeállítás felirata egy saját, egyszerűsített filmkészítő-dialógushoz tartozik; az eredeti makemoviepanel (panel-feliratok-hu.tsv) csúszkás vezérlőt használ ('moviesize_label' = 'Méretek', nem 'Video size:' feliratú mezőt).
- „Seconds per picture:”
  - *szükséges segédszöveg* — Lásd a 'Video size:' sor indoklását; az eredeti 'durationslider_label' = 'Dia időtartama' egy csúszka felirata, nem 'Seconds per picture:' szövegű mező.
- „MP4 videos (*.mp4)”
  - *szükséges segédszöveg* — Lásd a 'JPEG images (*.jpg)' sor indoklását — ugyanaz a saját fájlszűrő-mintázat, most a film-exportra.
- „The collage could not be created.”
  - *szükséges segédszöveg* — Saját hibaüzenet a kollázslétrehozás sikertelenségére; nincs megfelelője a forrásokban.
- „The movie could not be created.”
  - *szükséges segédszöveg* — Saját hibaüzenet a filmlétrehozás sikertelenségére; nincs megfelelője a forrásokban.

### `PicasaPy/DedupDialog.qml` — 15

- „Find Duplicates”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Select at least two pictures in the grid, or pick another scope.”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Comparing files...”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Analysing pictures...”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Searching...”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Groups of duplicate and similar pictures. Pick which one to ”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Search in:”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Selected pictures (none)”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „This folder and its subfolders”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Whole library”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Scan for Duplicates”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Searching the whole library reads every picture — with tens ”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „No duplicates found.”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Move others to \"Duplikátumok\"”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.
- „Delete others to Trash”
  - *saját funkció* — A Duplikátum-kereső párbeszéd (#287) az eredeti Picasa 3.9-ben nem létezik önálló ablakként: a docs/decisions/vedett-sajat-funkciok.md kifejezetten saját funkcióNAK sorolja fel — az eredetiben a másodpéldány-kezelés két MÁS mechanizmus (importáláskori AcquireDupeCheckThread és a keresősáv dupesearch módja), önálló kereső-dialógus nincs.

### `PicasaPy/PublishPanel.qml` — 14

- „Selection and Settings”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/selectiontext hivatalos szövegével.
- „Photo Size”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/picsizetext hivatalos szövegével.
- „Name the Gift CD”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/cdnametext hivatalos szövegével.
- „CD Name”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/label_cdname hivatalos szövegével.
- „Limit 16 Characters”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/namelimitext hivatalos szövegével.
- „Include Picasa”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/label_optionbox3 hivatalos szövegével.
- „Erase Media”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/label_optionbox2 hivatalos szövegével.
- „Create a Set or use an existing one”
  - ⚠️ *besorolatlan*
- „Create a Backup CD”
  - ⚠️ *besorolatlan*
- „A Backup Set records where to store backed-up files, and it also keeps a record of which files have been backed up already, so you don't have to back them up again.”
  - ⚠️ *besorolatlan*
- „To CD image (ISO)”
  - ⚠️ *besorolatlan*
- „To DVD image (ISO)”
  - ⚠️ *besorolatlan*
- „Visibility:”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/uploadaccess3 hivatalos szövegével.
- „Sync:”
  - *a mérő vakfoltja — az eredetiben is megvan* — Az angol és a magyar is betűre egyezik a publish/uploadsync3 hivatalos szövegével.

### `PicasaPy/PhotoViewer.qml` — 13

- „Edit the movie presentation”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (editpanel buboréksúgó); az eltérés csak az angolban van.
- „Start slideshow”
  - *szükséges segédszöveg* — A kód-komment kifejezetten kimondja (#1857): ehhez a négy gombhoz 'NINCS kimért eredeti felirat — a szöveg SAJÁT... Ez tudatos eltérés.'
- „Show only one picture”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (editpanel buboréksúgó); az eltérés csak az angolban van.
- „Show two different pictures”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (editpanel buboréksúgó); az eltérés csak az angolban van.
- „Show the same picture twice”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (editpanel buboréksúgó); az eltérés csak az angolban van.
- „Switch focus between the pictures”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (editpanel buboréksúgó); az eltérés csak az angolban van.
- „Retouch fixes cannot be recovered with redo.\n”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573), a két mondat közti sortöréssel.
- „Redeye fixes cannot be recovered with redo.\n”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573), a két mondat közti sortöréssel.
- „The caption will replace the text you have ”
  - *szükséges segédszöveg* — Más helyzethez tartozik, mint az IDS_REPLACE_CAPTION ('Are you sure you want to replace the existing caption with the contents of the clipboard?') — az a VÁGÓLAPRÓL beillesztésről szól, a mi szövegünk viszont a képfelirat MÁSOLÁSA a szövegeszközbe (más funkció, más kiváltó ok), csak a záró '(This operation is not undoable)' tagmondat egyezik.
- „Video playback requires the Qt Multimedia module.”
  - *szükséges segédszöveg* — A Qt Multimedia modul hiányára figyelmeztető szöveg; ez a helyzet az eredetiben nem állhat elő (natív Windows videólejátszó-keretet használt).
- „Render the final collage from this draft”
  - *szükséges segédszöveg* — Saját tooltip egy saját funkcióhoz (kollázs-piszkozat véglegesítése a nézőből); nincs megfelelője a forrásokban.
- „Show Faces”
  - *bizonytalan* — Hiányzik a hivatalos forrás: a szerkesztőnézet arcgombja (editpanel/faces_button) létezik, de sem felirata, sem buboréksúgója nincs a korpuszban.
- „Edit Faces”
  - *bizonytalan* — Hiányzik a hivatalos forrás: arcszerkesztő kapcsoló buboréksúgójára nincs szöveg a korpuszban (editpanel/faces_button felirat nélkül).

### `PicasaPy/PrintDialog.qml` — 13

- „Printing is unavailable: the Qt print support ”
  - *szükséges segédszöveg* — Sajat hibauzenet: a Qt nyomtatas-tamogatas hianya; ez technikai/platform-fuggo helyzet, ami az eredetiben (natív Windows nyomtatas) nem all elo.
- „No pictures to print.”
  - *szükséges segédszöveg* — Ures kijeloles hibauzenete nyomtataskor; nincs talalhato eredeti megfelelo.
- „Choose the target file.”
  - *szükséges segédszöveg* — Celfajl-valaszto dialogus utasitasa (PDF-be nyomtatasnal); nincs talalhato eredeti megfelelo - az eredetiben ezt a natív OS nyomtato-dialogus adta.
- „Print size:”
  - *szükséges segédszöveg* — Nyomtatasi meret mezo felirata; nincs talalhato eredeti megfelelo.
- „Columns:”
  - *szükséges segédszöveg* — Oszlopszam mezo felirata; nincs talalhato eredeti megfelelo.
- „Copies of each picture:”
  - *szükséges segédszöveg* — Peldanyszam mezo felirata; nincs talalhato eredeti megfelelo.
- „Print to a PDF file...”
  - *szükséges segédszöveg* — PDF-be nyomtatas gomb felirata; nincs talalhato eredeti megfelelo.
- „(not selected)”
  - *szükséges segédszöveg* — Nincs kivalasztott celfajl allapotjelzo; nincs talalhato eredeti megfelelo.
- „Browse...”
  - *szükséges segédszöveg* — 'Tallozas...' gomb - natív OS fajlvalaszto, nincs Picasa-authoralt sztring rea, ugyanaz az indoklas mint a tobbi Browse... elofordulasnal.
- „Fit to page:”
  - *szükséges segédszöveg* — Oldalhoz igazitas mezo felirata; nincs talalhato eredeti megfelelo.
- „Whole picture”
  - *szükséges segédszöveg* — Oldalhoz igazitas opcioja; nincs talalhato eredeti megfelelo.
- „Fill the page (crop)”
  - *szükséges segédszöveg* — Oldalhoz igazitas opcioja (kivagas); nincs talalhato eredeti megfelelo.
- „PDF documents (*.pdf)”
  - *szükséges segédszöveg* — Fajltipus-szuro a PDF mentes dialogusban; nincs talalhato eredeti megfelelo (natív fajl-dialogus szurője lett volna eredetileg).

### `PicasaPy/ImportSourceDialog.qml` — 11

- „Import from Source”
  - *szükséges segédszöveg* — Az import funkció megvan, de az eredetiben nem külön ablak (a főablakba épülő importpanel), így ablakcím sincs; a menüparancs „&Importálás forrása...”.
- „bytes”
  - *szükséges segédszöveg* — Az átviteli sebesség mértékegysége (fallback "bytes" a formatSpeed függvényben); technikai segédszöveg, nincs hozzá talált hivatalos forrás.
- „Import pictures and videos from another folder (e.g. a ”
  - *szükséges segédszöveg* — A párbeszéd saját magyarázó bevezető mondata ("Import pictures and videos from another folder..."); nincs hozzá talált hivatalos forrás — saját leíró szöveg.
- „(none selected)”
  - *szükséges segédszöveg* — (nincs kiválasztva) üres-állapot helykitöltő szöveg forrás-/célmappa mezőknél; saját segédszöveg.
- „Recent sources”
  - *bizonytalan* — Az eredeti a „Choose…” mellett a korábbi importokat kínálta (LastImport…), de a lenyíló feliratának szövege nincs a mért forrásokban.
- „Browse...”
  - *valódi eltérés* — SZÁNDÉKOS: a kódkomment szerint az eredeti legördülő „Choose…” tételét nálunk „a »Tallózás…« … a mellette álló gomb — így a szakaszhatár is látszik”. Hivatalos: „Kiválasztás...” → nálunk: „Tallózás…”. (hivatalos: `Acquire::ChooseFolder` „Choose...”)
- „Exclude Duplicates”
  - *szükséges segédszöveg* — Duplikátumok kihagyása jelölőnégyzet RÖVID felirata; az ui-leltar.csv `acquirepanel/excludedupesbutton` bejegyzésében a "felirat" (látható címke) mező ÜRES, csak a buborék ("Exclude photos that are already imported into Picasa") van kitöltve — vagyis az eredetiben ez ikon volt, látható szöveg nélkül; a rövid felirat a mi saját, ikont helyettesítő címkénk.
- „No pictures or videos found in this folder.”
  - *szükséges segédszöveg* — Nincs kép vagy videó ebben a mappában üres-állapot üzenet; nincs hozzá talált hivatalos forrás — saját visszajelzés.
- „Recent destinations”
  - *bizonytalan* — Mint a „Recent sources”: a korábbi célok lenyílójának eredeti felirata nincs a mért forrásokban.
- „Choose source folder...”
  - *szükséges segédszöveg* — A natív mappaválasztó (FolderDialog) ablakcíme forrás-mappához; technikai UI-szöveg, nincs hozzá talált hivatalos forrás.
- „Choose destination folder...”
  - *szükséges segédszöveg* — A natív mappaválasztó (FolderDialog) ablakcíme cél-mappához; technikai UI-szöveg, nincs hozzá talált hivatalos forrás.

### `PicasaPy/InitialScanDialog.qml` — 11

- „There is an older version of Picasa installed.  Would you like to update your existing picture library, or search your computer for pictures again?”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Picasa is ready to search for pictures on your computer”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Update my existing picture library”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Only search Documents, Pictures, and the Desktop”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal; az angolban csak a Windows-mappanév („My Documents”) tér el.
- „Choose this option if you use keywords or custom albums in Picasa 1, and you want to preserve these in Picasa 3.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Choose this option if you only store your pictures in these folders.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Search my computer for pictures again”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Search my whole computer for pictures”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Choose this option for a more complete search of your computer, which includes extended picture information.  It will preserve your existing edits and organization, but it will not preserve keywords.  This search may take several minutes.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Choose this option if you have pictures stored in various folders across your computer, especially if you have pictures stored on more than one hard drive.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).
- „Searching for pictures never moves or copies files to new locations. You can choose which folders are displayed by Picasa by using the Folder Manager tool (available from the Tools menu)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (initialscan panel).

### `PicasaPy/OptionsTabNetwork.qml` — 11

- „Proxy username (Windows only):”
  - ⚠️ *besorolatlan*
- „Proxy password:”
  - ⚠️ *besorolatlan*
- „Automatically detect network settings”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/autoproxy.title hivatalos magyarjával.
- „Network logging level:”
  - ⚠️ *besorolatlan*
- „Disable logging”
  - ⚠️ *besorolatlan*
- „Log errors only”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/item138.title hivatalos magyarjával.
- „Minimal log information”
  - ⚠️ *besorolatlan*
- „Detailed log information”
  - ⚠️ *besorolatlan*
- „Log all network information”
  - ⚠️ *besorolatlan*
- „Log file:”
  - ⚠️ *besorolatlan*
- „Browse...”
  - *szükséges segédszöveg* — 'Tallozas...' gomb a napofajl kivalasztasahoz - az eredetiben (ha volt) natív OS fajlvalaszto dialogus gombja lett volna, nem Picasa-authoralt sztring, ezert nincs a korpuszban - ugyanaz az indoklas, mint a tobbi 'Browse...' elofordulasnal a projektben.

### `PicasaPy/CollageThemePopup.qml` — 10

- „Looks like a pile of scattered pictures”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Mosaic”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Automatically fit pictures into the page”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Frame Mosaic”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „A mosaic with a prominent center picture”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Grid”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Arrange pictures into regular rows and columns”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Thumbnails with an informative header”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Multiple Exposure”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.
- „Superimpose pictures over one another”
  - *a mérő vakfoltja — az eredetiben is megvan* — A hivatalos „Név: leírás” sztring egyik fele, a magyarunk betűre egyezik vele; csak az összefűzés tér el.

### `PicasaPy/EditorParamPanel.qml` — 10

- „Inner Radius”
  - *saját funkció* — Effekt-parameter felirat, amit jelenleg egyetlen bekototott effekt sem hasznal (effect_params.py-ban nem szerepel) - csak a Regi effektek fulon (#571) meg nem drotozott szureknek fenntartott, elore felsorolt forditasi kulcs.
- „Center X”
  - *szükséges segédszöveg* — Effekt-parameter felirat (kozeppont X koordinataja); az erintett eredeti szurok (Soft Focus/Focal B&W/Soften) parameterlistajaban NINCS ilyen vezerlo - a helyzet (kozeppont kezi allitasa) az eredetiben nem all elo.
- „Center Y”
  - *szükséges segédszöveg* — Effekt-parameter felirat (kozeppont Y koordinataja); ugyanaz az indoklas mint a Center X-nel.
- „Block Size”
  - *saját funkció* — Effekt-parameter felirat, amit jelenleg egyetlen bekototott effekt sem hasznal (effect_params.py-ban nem szerepel) - a Regi effektek fulnak (#571) fenntartott forditasi kulcs.
- „Blur Radius”
  - *szükséges segédszöveg* — A Pencil Sketch szuro elmosas-parametere; az eredeti filter_PencilSketch bejegyzesnek nincs parameter-felirata (csak nev+tooltip) - az eredetiben ez a szuro egy kattintasos, allithato parameter nelkul.
- „Color Mix”
  - *szükséges segédszöveg* — A Pencil Sketch szuro szinkeveres-parametere; ugyanaz az indoklas mint a Blur Radius-nal.
- „Edge Strength”
  - *szükséges segédszöveg* — A Neon szuro elszogesseg-parametere; az eredeti filter_Neon bejegyzesnek nincs parameter-felirata (egy kattintasos szuro).
- „Smoothness”
  - *szükséges segédszöveg* — A Comicize szuro simasag-parametere; az eredeti filter_Comicize bejegyzesnek nincs parameter-felirata (egy kattintasos szuro).
- „Width”
  - *saját funkció* — Effekt-parameter felirat, amit jelenleg egyetlen bekototott effekt sem hasznal (effect_params.py-ban nem szerepel) - a Regi effektek fulnak (#571) fenntartott forditasi kulcs.
- „Line Position”
  - *saját funkció* — Effekt-parameter felirat, amit jelenleg egyetlen bekototott effekt sem hasznal (effect_params.py-ban nem szerepel) - a Regi effektek fulnak (#571) fenntartott forditasi kulcs.

### `PicasaPy/FaceScanDialog.qml` — 10

- „Find Faces”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Search cancelled. The faces found so far are kept.”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Grouping cancelled. The groups made so far are kept.”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „PicasaPy goes through the pictures of your library and looks ”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Searching...”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Download the model”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Downloading the model...”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „As a second step PicasaPy can compare the faces it found and ”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Grouping...”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.
- „Group Faces”
  - *saját funkció* — Az arckeresés-indító ablak (#1473) maga saját funkció: a fájl fejléckommentje kimondja, hogy 'Az EREDETI Picasában az arckeresésnek nem volt indítsd-el menüpontja: a BgFaceDetectThread háttérszál alapból BE volt kapcsolva... Nálunk ilyen háttérszál MA NINCS', ezért ez az egész ablak (kereséssel, modell-letöltéssel, csoportosítással) a mi hozzáadásunk.

### `PicasaPy/MoveDatabaseDialog.qml` — 10

- „Move Database”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a move_database/window1.title hivatalos magyarjával.
- „Move the photo index and thumbnail cache to a new folder. ”
  - *valódi eltérés* — SZÁNDÉKOS: a kód kommentje: „a FEN két figyelmeztető labelje helyett, átfogalmazva — nálunk a NAS/hálózati hely a NORMÁL eset”. Hivatalos magyar: „A módosítások érvénybe léptetéséhez újra kell indítania a Picasa szolgáltatást.” — nálunk: „A fotóindex és a bélyegkép-gyorsítótár áthelyezése új mappába. A PicasaPy a következő indításkor költözteti át őket.”. (hivatalos: `move_database/label3.title` „”)
- „Network drives (e.g. a NAS) are fully supported and are ”
  - *valódi eltérés* — SZÁNDÉKOS: a kód kommentje: „a FEN két figyelmeztető labelje helyett, átfogalmazva — nálunk a NAS/hálózati hely a NORMÁL eset”; az eredeti épp a hálózati helyet tiltja. Hivatalos magyar: „Megjegyzés: E kísérleti funkció kipróbálása előtt ajánlatos biztonsági másolatot készíteni az adatbázisról. SOHA ne helyezze át az adatbázist hálózatra, illetve cserélhető vagy külső meghajtóra, mert úgy adatokat veszíthet.” — nálunk: „A hálózati meghajtók (pl. NAS) teljes körűen támogatottak — a PicasaPy-nál ez a szokásos elrendezés; ügyeljen rá, hogy a meghajtó a program futása alatt elérhető maradjon.”. (hivatalos: `move_database/label5.title` „”)
- „Current database location:”
  - ⚠️ *besorolatlan*
- „New database location:”
  - ⚠️ *besorolatlan*
- „(none selected)”
  - *szükséges segédszöveg* — (nincs kiválasztva) üres-állapot helykitöltő szöveg; ugyanaz a saját segédszöveg-minta, mint az ImportSourceDialog azonos feliratánál.
- „Browse...”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk egyezik a move_database/changeloc.title hivatalos magyarjával (csak …/... különbség).
- „PicasaPy will move the database the next time it starts.”
  - *szükséges segédszöveg* — Az ütemezés utáni visszajelző szöveg; az eredeti ablakleltárában (move_database/*) nincs ilyen állapotüzenet.
- „Move on next restart”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a move_database/move.title hivatalos magyarjával.
- „Cancel the move”
  - *szükséges segédszöveg* — Az ütemezett áthelyezés visszavonása gomb; az eredetiben csak Mégse (bezárás) van, ütemezés-visszavonás nincs.

### `PicasaPy/OptionsTabEmail.qml` — 10

- „Mail program:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Levelezőprogram:”).
- „Use this computer's default email program”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal.
- „Let me choose each time I send pictures”
  - ⚠️ *besorolatlan*
- „Use my Google Account”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („A Google Fiók használata”).
- „Multiple photo size”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk a hivatalossal egyezik, csak a záró kettőspont hiányzik („Több kép mérete:”).
- „Single picture size:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Egyedülálló képek mérete:”).
- „Send videos as:”
  - ⚠️ *besorolatlan*
- „First frame”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Első képkocka”).
- „Full film”
  - ⚠️ *besorolatlan*
- „Send inline photos and captions (Outlook only)”
  - ⚠️ *besorolatlan*

### `PicasaPy/WebExportDialog.qml` — 10

- „Page title:”
  - *szükséges segédszöveg* — Weboldal-export beallitasainak mezofelirata (oldalcim); nincs talalhato eredeti megfelelo a korpuszban (a CWebExporter/WebExport csoport nem tartalmaz ilyen beallitas-feliratokat).
- „Save to:”
  - *szükséges segédszöveg* — Mentesi cel mezofelirata; nincs talalhato eredeti megfelelo.
- „(not selected)”
  - *szükséges segédszöveg* — Nincs kivalasztott cel allapotjelzo; nincs talalhato eredeti megfelelo.
- „Browse...”
  - *szükséges segédszöveg* — 'Tallozas...' gomb - natív OS fajlvalaszto, nincs Picasa-authoralt sztring rea.
- „Thumbnail size:”
  - *szükséges segédszöveg* — Bélyegkep-meret mezofelirata; nincs talalhato eredeti megfelelo.
- „Picture size:”
  - *szükséges segédszöveg* — Kepmeret mezofelirata; nincs talalhato eredeti megfelelo.
- „Shadow thumbnails”
  - *szükséges segédszöveg* — Arnyek-effekt opcio belyegkepekhez; nincs talalhato eredeti megfelelo.
- „Shadow pictures”
  - *szükséges segédszöveg* — Arnyek-effekt opcio a kepekhez; nincs talalhato eredeti megfelelo.
- „PicasaPy is generating the web page.”
  - *szükséges segédszöveg* — Allapotjelzo folyamatban levo exportnal; a CWebExporter csoport uzenetei masrol szolnak (masolas/hiba/torles), erre a konkret allapotra nincs talalhato eredeti megfelelo.
- „Choose target folder...”
  - *szükséges segédszöveg* — Celmappa-valaszto dialogus utasitasa; nincs talalhato eredeti megfelelo.

### `PicasaPy/BackupHost.qml` — 9

- „All file types”
  - ⚠️ *besorolatlan*
- „All pictures (no movies)”
  - ⚠️ *besorolatlan*
- „Only JPEGs with camera data”
  - ⚠️ *besorolatlan*
- „Choose the backup location”
  - ⚠️ *besorolatlan*
- „Backup type:”
  - ⚠️ *besorolatlan*
- „CD or DVD backup”
  - ⚠️ *besorolatlan*
- „Disk-to-disk backup (for external and network drives)”
  - ⚠️ *besorolatlan*
- „Save to:”
  - ⚠️ *besorolatlan*
- „Files:”
  - ⚠️ *besorolatlan*

### `PicasaPy/EditorTabBar.qml` — 8

- „Common Fixes”
  - *szükséges segédszöveg* — Az 1. (eredeti) effekt-ful LATHATO felirata; az eredeti tab1 elem (editpanel/tab1) csak ikon+buboreksugo, latszo szoveges cimke nelkul - hozzaferhetosegi/latszo nev, amit mi adtunk hozza.
- „Fine Tuning”
  - *szükséges segédszöveg* — A 2. (eredeti) effekt-ful lathato felirata; az eredeti tab2 elem csak ikon+buboreksugo, lathato cimke nelkul.
- „Effects”
  - *szükséges segédszöveg* — A 3. (eredeti) effekt-ful lathato felirata; az eredeti tab3 elem csak ikon+buboreksugo, lathato cimke nelkul.
- „Creative”
  - *szükséges segédszöveg* — A 4. (eredeti) effekt-ful lathato felirata; az eredeti tab4 elem csak ikon+buboreksugo, lathato cimke nelkul.
- „More Effects”
  - *saját funkció* — A '6. ful' ('Tovabbi effektek', #422) sajat funkcio: olyan Glimmer-effektek, amik nem szerepelnek a 3-5. fulon.
- „Glimmer effects beyond the three known tabs”
  - *saját funkció* — A '6. ful' (#422) leirasa - sajat funkcio, lasd elozo sor.
- „Legacy Effects”
  - *saját funkció* — A 'Regi effektek' ful (#571) sajat funkcio.
- „Filters left in the Picasa engine but not on its surface”
  - *saját funkció* — A 'Regi effektek' ful (#571) leirasa - sajat funkcio, lasd elozo sor.

### `PicasaPy/FileOpsDialogs.qml` — 8

- „Please enter a new name for these files:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A felirat betűre a hivatalos párbeszéd-sablon címkéje (rename.fen, magyarul „Kérjük, adjon új nevet ezeknek a fájloknak:”, #3573); a mérő szövegkészlete a .fen-címkéket nem tartalmazza.
- „Include in filename:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A felirat betűre a hivatalos párbeszéd-sablon címkéje (rename.fen, magyarul „Befoglalás a fájlnévbe:”, #3573); a mérő szövegkészlete a .fen-címkéket nem tartalmazza.
- „Image resolution”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Képfelbontás”, Átnevezés párbeszéd).
- „Move to Folder...”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk („Áthelyezés új mappába…”) a hivatalossal egyezik (csak …/...); az angol forrásunk rövidebb („Move to Folder...”), de a magyar felületen nem látszik.
- „Are you sure you want to send the selected file to ”
  - ⚠️ *besorolatlan*
- „Are you sure you want to permanently delete the ”
  - ⚠️ *besorolatlan*
- „File operation failed”
  - *szükséges segédszöveg* — Saját, általános állapotjelző cím a háttérben futó fájlművelet sikertelenségére; nincs megfelelője a forrásokban.
- „File operation finished”
  - *szükséges segédszöveg* — Saját, általános állapotjelző cím a háttérben futó fájlművelet befejezésére; nincs megfelelője a forrásokban.

### `PicasaPy/HiddenPasswordDialog.qml` — 8

- „Password for hidden folders”
  - *szükséges segédszöveg* — Rejtett mappak jelszo-dialogusanak cime; a funkcio (Rejtett mappak jelszava) eredeti, de erre a konkret dialogus-szovegre nincs talalhato eredeti megfelelo egyik korpuszban sem.
- „Hidden folders are locked”
  - *szükséges segédszöveg* — Rejtett mappak zarolt allapotanak felirata; nincs talalhato eredeti megfelelo.
- „Enter a password to use for the hidden folders.”
  - *szükséges segédszöveg* — Jelszo-bekero prompt (uj jelszo beallitasa); nincs talalhato eredeti megfelelo.
- „Enter the password to show the hidden folders.”
  - *szükséges segédszöveg* — Jelszo-bekero prompt (feloldas a megtekintesehez); nincs talalhato eredeti megfelelo.
- „Type the password again”
  - *szükséges segédszöveg* — Jelszo-ismetles mezo felirata; nincs talalhato eredeti megfelelo.
- „Stronger protection (Picasa cannot open it)”
  - *szükséges segédszöveg* — Erosebb vedelem opcio felirata; nincs talalhato eredeti megfelelo.
- „Remove the password”
  - *szükséges segédszöveg* — Jelszo eltavolitasa gomb felirata; nincs talalhato eredeti megfelelo.
- „This only hides the folders inside PicasaPy. The files ”
  - *szükséges segédszöveg* — Sajat magyarazo szoveg a rejtes korlatairol (csak a PicasaPy-n belul rejt); nincs talalhato eredeti megfelelo.

### `PicasaPy/OptionsTabWebAlbums.qml` — 8

- „Default upload size:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Alapértelmezett feltöltési méret:”).
- „When syncing large files, upload previews first”
  - ⚠️ *besorolatlan*
- „Preserve original image quality (uses more storage)”
  - ⚠️ *besorolatlan*
- „Sync starred photos only”
  - ⚠️ *besorolatlan*
- „Don't confirm every sync (use the above settings)”
  - ⚠️ *besorolatlan*
- „Name Tags:”
  - ⚠️ *besorolatlan*
- „Include with photo uploads”
  - ⚠️ *besorolatlan*
- „Add a watermark for all photo uploads:”
  - ⚠️ *besorolatlan*

### `PicasaPy/SaveDialogs.qml` — 8

- „A backup of this file will be made.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a hivatalossal, csak a vezető sortörés hiányzik.
- „A backup of these files will be made.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a hivatalossal, csak a vezető sortörés hiányzik.
- „JPEG Files (*.jpg)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A szöveg azonos a hivatalos szűrőnévvel; a „(*.jpg)” a Qt fájlszűrő mintaszintaxisa.
- „WebP Files (*.webp)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A szöveg azonos a hivatalos szűrőnévvel; a „(*.webp)” a Qt fájlszűrő mintaszintaxisa.
- „Saving writes the picture without them, and the settings are lost. This cannot be undone.”
  - *szükséges segédszöveg* — Az "eszközök, amiket PicasaPy még nem tud renderelni" saját technikai korlátra figyelmeztető szöveg — ez a helyzet (részlegesen renderelhetetlen effektlánc) csak nálunk állhat elő, az eredetiben nem.
- „This cannot be undone and all changes will be lost.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mondat az angolban és a magyarban is betűre a hivatalos (#3573); a hivatalos erőforrás két soremeléssel kezdődik, mert az eredeti egy üzenetbe fűzi, nálunk külön szövegsor — a mérő a soremelés miatt nem látja a párját.
- „To undo the last save and keep edits click 'Undo Save'.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mondat az angolban és a magyarban is betűre a hivatalos (#3573); a hivatalos erőforrás két soremeléssel kezdődik, mert az eredeti egy üzenetbe fűzi, nálunk külön szövegsor — a mérő a soremelés miatt nem látja a párját.
- „File operation failed”
  - *szükséges segédszöveg* — A saveResultDialog saját gyűjtő-címe hiba esetén; a konkrét mentési hibaüzenetek mind mért, hivatalos forrásúak (pl. filesaveerr2/3), de erre az összefoglaló CÍM-szövegre nincs találat — saját dialóguscím.

### `PicasaPy/PicasaImportDialog.qml` — 7

- „Import from Picasa”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio: csak egy Picasa-utodapp szamara ertelmes muvelet (a korabbi sajat telepites felderitese), az eredeti Picasaban ilyen forgatokonyv nem letezik. A dialogus cime esetlegesen egybeesik az eMenuFile::ID_GETMYSTUFF ('Import from Picasa Web Albums...') szoveggel, de az teljesen mas funkciohoz (webalbum-import) tartozik - nem bizonyithato eltérés, mas szerepu par.
- „Looking for a previous Picasa installation…”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio resze - felderites folyamatban szoveg.
- „We found your previous Picasa installation. It ”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio resze - sikeres felderites szovege.
- „We couldn't find a previous Picasa installation ”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio resze - sikertelen felderites szovege.
- „Browse manually...”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio resze - kezi tallozas gomb.
- „Not now”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio resze - elutasito gomb.
- „Adopt”
  - *saját funkció* — A 'korabbi Picasa-telepites atvetele' (#146) sajat funkcio resze - elfogado gomb.

### `PicasaPy/CollageDialogs.qml` — 6

- „The collage could not be saved”
  - *szükséges segédszöveg* — A mentés MEGHIÚSULT hibapárbeszéd — a fájl saját megjegyzése szerint (CollageDialogs.qml 73-78) ez azért született, mert a hiba az eredetiben NÉMA volt (a folyamatjelző csak eltűnt); a helyzet tehát az eredetiben nem termel szöveget.
- „The collage cannot be saved because all of the pictures ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg magyarja betűre egyezik a hivatalossal („A kollázs nem menthető, mert az összes képet eltávolították. …”).
- „The current page format of the collage does not ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött szöveg töredéke; a teljes magyar a hivatalossal egyezik, a különbség csak sortörés (a két első mondat közti \n) és idézőjel-alak.
- „You have been editing a previously created collage.\n\n”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573), a sortörésekkel együtt.
- „The current collage contains unsaved changes.\n\n”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött szöveg töredéke; a teljes magyar betűre egyezik a hivatalossal, csak az idézőjel alakja más („Kollázsok” ↔ "Kollázsok").
- „Please select the single image you want to place in ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes magyar betűre egyezik a hivatalossal („MIELŐTT erre a gombra kattintana, …”).

### `PicasaPy/EditorTextPanel.qml` — 6

- „Type your text, then click on the photo to place it.”
  - *szükséges segédszöveg* — A szövegeszköz saját, panel-szintű használati útmutatója. Az eredetiben más mechanizmus felel meg ennek: az EditText::GhostText ("Type anywhere to add text") egy a KÉPRE rajzolt "szellem-szöveg", amit a kódunk nem valósít meg — más szerepű vezérlő, nem ugyanaz a helyzet, ezért a mi külön magyarázó szövegünk saját súgó.
- „B”
  - *szükséges segédszöveg* — A Félkövér kapcsológomb egybetűs felirata ("B"); az eredetiben ez feltehetően ikonos gomb volt (a tooltip "Félkövér"/Bold külön mért), a szöveges "B" a mi saját, ikont helyettesítő hozzáférhetőségi feliratunk.
- „I”
  - *szükséges segédszöveg* — A Dőlt kapcsológomb egybetűs felirata ("I"); ugyanaz az indoklás, mint a "B"-nél — saját, ikont helyettesítő felirat.
- „U”
  - *szükséges segédszöveg* — Az Aláhúzás kapcsológomb egybetűs felirata ("U"); ugyanaz az indoklás, mint a "B"-nél — saját, ikont helyettesítő felirat.
- „Outline color”
  - *szükséges segédszöveg* — A körvonalszín-választó megvan, de az eredeti szövegpanel teljes angol és magyar leltárában (edittextpanel/*) nincs ilyen felirat.
- „Outline thickness”
  - *szükséges segédszöveg* — A körvonal-csúszka megvan, de az eredeti szövegpanel teljes angol és magyar leltárában (edittextpanel/*) nincs ilyen felirat.

### `PicasaPy/OptionsTabNameTags.qml` — 6

- „Enable face detection”
  - ⚠️ *besorolatlan*
- „Enable suggestions:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/enablefacesuggestions.title hivatalos magyarjával.
- „Suggestion threshold:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/labelgroup176.title hivatalos magyarjával.
- „Clustering threshold:”
  - ⚠️ *besorolatlan*
- „Store name tags in the file”
  - ⚠️ *besorolatlan*
- „Upload contact thumbnails to Google Contacts”
  - ⚠️ *besorolatlan*

### `PicasaPy/OptionsTabPrinting.qml` — 6

- „Available print sizes:”
  - ⚠️ *besorolatlan*
- „Use high quality previews (slower)”
  - ⚠️ *besorolatlan*
- „Printer quality:”
  - ⚠️ *besorolatlan*
- „Print resampler quality:”
  - ⚠️ *besorolatlan*
- „General (Lanczos-3)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Általános (Lanczos-3)”).
- „Extra sharp (Lanczos-8)”
  - ⚠️ *besorolatlan*

### `PicasaPy/TrayBar.qml` — 6

- „Waiting for the collage to be created…”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal (csak …/... eltérés: „Várakozás a kollázs elkészítésére…”).
- „This will clear your entire tray.”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: a qsTr darab a teljes kérdés első mondata; a teljes mondat magyarja betűre egyezik a hivatalossal („Ezzel a művelettel a teljes tálcát kiüríti. Biztosan ezt szeretné tenni?”).
- „Order Prints (service discontinued)”
  - *valódi eltérés* — SZÁNDÉKOS: a kódkomment szerint „kivezetett: a nyomat-rendelő szolgáltatás megszűnt”. A tálcagomb felirata eltér. Hivatalos: „Nyomatok rendelése” → nálunk: „Papírképek rendelése (a szolgáltatás megszűnt)”. (hivatalos: `buttonlabel:{8E6A2DAF-0069-4df2-88D2-8B24BEEC9CA1}` „Order Prints”)
- „Publish to Blogger (service discontinued)”
  - *valódi eltérés* — SZÁNDÉKOS: a kódkomment szerint „kivezetett: a Blogger-integráció megszűnt”. Ez a tálca BlogThis! gombjának buboréksúgója (a menütétel eMenuCreate::ID_EXPORT_SENDTOBLOGGER: „Közzététel a Bloggeren...”). Hivatalos: „Fotókat tehet közzé a blogján a Blogger segítségével” → nálunk: „Közzététel a Bloggeren (a szolgáltatás megszűnt)”. (hivatalos: `buttontooltip:{B9012CB2-DD50-49a5-B4CB-009344BBA285}` „Post photos to your blog via Blogger”)
- „Click here for more options”
  - *szükséges segédszöveg* — Buboreksugo a 'tovabbi lehetosegek' gombhoz; nincs talalhato eredeti megfelelo.
- „Select the items you want to add to the ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: a qsTr darab egy összefűzött mondat eleje; a teljes mondat magyarja a hivatalossal egyezik, csak az idézőjel alakja más („Vissza” ↔ "Vissza").

### `PicasaPy/EditorCropPanel.qml` — 5

- „Select a dimension below and then click and drag on the ”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az editpanel/croptext hivatalos magyarjával.
- „This image's orientation has been modified by the Straighten tool and might not crop accurately.\nIf you encounter difficulty cropping this image, try undoing the Straighten fix, then recrop, and Straighten again if necessary.”
  - ⚠️ *besorolatlan*
- „Delete this custom aspect ratio?”
  - *szükséges segédszöveg* — Egyéni méretarány törlése előtti MEGERŐSÍTŐ KÉRDÉS; a leltárakban csak a törlés-gomb buboréksúgója van meg (`editpanel/crop_delete_custom`, "Törli az aktuális méretarányt" — állítás, nem kérdés), önálló megerősítő párbeszédre nincs bizonyíték az eredetiben.
- „Suggested crops”
  - *szükséges segédszöveg* — A vágás-javaslatok CSOPORT-CÍMKÉJE. A javaslat-funkció maga eredeti (a render/crop_suggest.py szerint a bináris három stratégia-nevet őriz), de erre a szervező feliratra sehol nincs találat — feltehetően a mi saját, a gombcsoportot bevezető szövegünk.
- „Top left”
  - *szükséges segédszöveg* — A gyorsvágás gombjának felirata. A QML megjegyzése szerint ez a "Picasa három bélyegképe" — vagyis az eredetiben ez vizuálisan, KÉPI bélyegképként jelent meg, szöveg nélkül; a mi szöveges felirat a hozzáférhetőségi/leíró név, amit az eredeti ikonhoz adtunk.

### `PicasaPy/EditorPanel.qml` — 5

- „Close crop to faces”
  - *szükséges segédszöveg* — A vágás-javaslat gombok maguk megvannak az eredetiben is (ui-leltar.csv: editpanel/cropsug1, cropsug2, cropsug3 — 3 db, előnézeti bélyegképpel), de FELIRAT NÉLKÜL: a felirat- és buborék-mező mindháromnál üres. Az eredeti tehát nem ír ki szöveget ehhez a helyzethez, csak ikonos előnézetet mutat — a mi 5 elnevezett stratégiánk (a 3 helyett) saját szöveges kiegészítés.
- „Compose around faces”
  - *szükséges segédszöveg* — A vágás-javaslat gombok maguk megvannak az eredetiben is (ui-leltar.csv: editpanel/cropsug1, cropsug2, cropsug3 — 3 db, előnézeti bélyegképpel), de FELIRAT NÉLKÜL: a felirat- és buborék-mező mindháromnál üres. Az eredeti tehát nem ír ki szöveget ehhez a helyzethez, csak ikonos előnézetet mutat — a mi 5 elnevezett stratégiánk (a 3 helyett) saját szöveges kiegészítés.
- „Crop by horizon”
  - *szükséges segédszöveg* — A vágás-javaslat gombok maguk megvannak az eredetiben is (ui-leltar.csv: editpanel/cropsug1, cropsug2, cropsug3 — 3 db, előnézeti bélyegképpel), de FELIRAT NÉLKÜL: a felirat- és buborék-mező mindháromnál üres. Az eredeti tehát nem ír ki szöveget ehhez a helyzethez, csak ikonos előnézetet mutat — a mi 5 elnevezett stratégiánk (a 3 helyett) saját szöveges kiegészítés.
- „Crop by color”
  - *szükséges segédszöveg* — A vágás-javaslat gombok maguk megvannak az eredetiben is (ui-leltar.csv: editpanel/cropsug1, cropsug2, cropsug3 — 3 db, előnézeti bélyegképpel), de FELIRAT NÉLKÜL: a felirat- és buborék-mező mindháromnál üres. Az eredeti tehát nem ír ki szöveget ehhez a helyzethez, csak ikonos előnézetet mutat — a mi 5 elnevezett stratégiánk (a 3 helyett) saját szöveges kiegészítés.
- „Crop by detail”
  - *szükséges segédszöveg* — A vágás-javaslat gombok maguk megvannak az eredetiben is (ui-leltar.csv: editpanel/cropsug1, cropsug2, cropsug3 — 3 db, előnézeti bélyegképpel), de FELIRAT NÉLKÜL: a felirat- és buborék-mező mindháromnál üres. Az eredeti tehát nem ír ki szöveget ehhez a helyzethez, csak ikonos előnézetet mutat — a mi 5 elnevezett stratégiánk (a 3 helyett) saját szöveges kiegészítés.

### `PicasaPy/FolderManagerDialog.qml` — 5

- „Watching an entire drive can slow down the system. ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „If you remove a watched folder, new items that you add ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „For each folder, you can choose whether or not to have Picasa find ”
  - ⚠️ *besorolatlan*
- „Folder Manager — Help”
  - *szükséges segédszöveg* — A Mappakezelohoz tartozo KULON sugo-ablak cime - sajat 'sugo-/magyarazo szovegunk', az eredetiben nincs bizonyitottan kulon sugo-ablak erre.
- „Scan Always keeps watching the folder: pictures you add ”
  - *szükséges segédszöveg* — A fenti sugo-ablak tartalma (Scan Always / Scan Once / Remove modok magyarazata) - sajat magyarazo szoveg.

### `PicasaPy/FolderPropertiesDialog.qml` — 5

- „Automatic date”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az album/autodate.title hivatalos magyarjával.
- „Enter the date as YYYY-MM-DD.”
  - *szükséges segédszöveg* — A dátummező beviteli formátum-súgója; a leltárakban talált legközelebbi hasonló szöveg (iCAcquireUI::AutoDate, "Date Taken (YYYY-MM-DD)") más vezérlőé (az Import-panel dátummező CÍMKÉJE, nem egy validációs hibaüzenet) — más szerepű pár, nem valódi találat; ez a mi saját beviteli-hint szövegünk.
- „Use music for Slideshow and Movie presentation:”
  - ⚠️ *besorolatlan*
- „Place taken (optional):”
  - ⚠️ *besorolatlan*
- „Description (optional):”
  - ⚠️ *besorolatlan*

### `PicasaPy/PhotoContextMenu.qml` — 5

- „Ctrl+Delete”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk egyezik a ytMenu::CtrlPrefix + CMenuBar::Delete összefűzésével („Ctrl+Törlés”).
- „Add to People Album”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a PplAlbumPhoto::ID_PEOPLEALBUMS hivatalos magyarjával (csak a & jel hiányzik); az angol eltér („Move to People Album”).
- „File on Disk”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk egyezik a CThumbUI::locateondiskmenu hivatalos magyarjával (a & jel és a Ctrl+Enter gyorsbillentyű-rész nélkül).
- „Locate Original on Disk”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a CThumbUI::locateorigondiskmenu_win hivatalos magyarjával (csak a & jel hiányzik); az angolban nálunk plusz „Locate” áll.
- „Block Upload”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az AlbumPhoto::ID_SUPPRESS hivatalos magyarjával (csak a & jel hiányzik); az angol eltér („Block from Uploading”).

### `PicasaPy/UnnamedFacesView.qml` — 5

- „Select someone you know and add a name, or click ”
  - ⚠️ *besorolatlan*
- „Stop ignoring”
  - *szükséges segédszöveg* — 'Mellozes visszavonasa' gomb felirata; nincs talalhato eredeti megfelelo.
- „Look for more suggestions”
  - *szükséges segédszöveg* — 'Tovabbi javaslatok keresese' gomb felirata; nincs talalhato eredeti megfelelo.
- „Lowers the recognition threshold once, so more names are ”
  - *szükséges segédszöveg* — Buboreksugo a felismeresi kuszob lazitasarol; nincs talalhato eredeti megfelelo.
- „Are you sure you want to move this person to the ”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a PeoplePanel::ConfirmRemoveMsg hivatalos magyarjával.

### `PicasaPy/CollageDraftDialog.qml` — 4

- „Recovered Auto Backup”
  - *saját funkció* — A kollázs-piszkozat VISSZAÁLLÍTÁS-FELAJÁNLÓ párbeszéde (#1051): a fájl saját megjegyzése szerint az eredeti Picasa ilyenkor NEM kérdez — induláskor némán átnevezi és visszateszi az autosave.cxf-et a Kollázsok albumba (a #979 gazdagabb működés, ami nálunk még blokkolt). Ez a kérdező köztes megoldás, a kérdés maga a mi funkciónk.
- „PicasaPy found an automatically saved collage draft ”
  - *saját funkció* — A kollázs-piszkozat VISSZAÁLLÍTÁS-FELAJÁNLÓ párbeszéde (#1051): a fájl saját megjegyzése szerint az eredeti Picasa ilyenkor NEM kérdez — induláskor némán átnevezi és visszateszi az autosave.cxf-et a Kollázsok albumba (a #979 gazdagabb működés, ami nálunk még blokkolt). Ez a kérdező köztes megoldás, a kérdés maga a mi funkciónk.
- „Restore Draft”
  - *saját funkció* — A kollázs-piszkozat VISSZAÁLLÍTÁS-FELAJÁNLÓ párbeszéde (#1051): a fájl saját megjegyzése szerint az eredeti Picasa ilyenkor NEM kérdez — induláskor némán átnevezi és visszateszi az autosave.cxf-et a Kollázsok albumba (a #979 gazdagabb működés, ami nálunk még blokkolt). Ez a kérdező köztes megoldás, a kérdés maga a mi funkciónk.
- „Discard Draft”
  - *saját funkció* — A kollázs-piszkozat VISSZAÁLLÍTÁS-FELAJÁNLÓ párbeszéde (#1051): a fájl saját megjegyzése szerint az eredeti Picasa ilyenkor NEM kérdez — induláskor némán átnevezi és visszateszi az autosave.cxf-et a Kollázsok albumba (a #979 gazdagabb működés, ami nálunk még blokkolt). Ez a kérdező köztes megoldás, a kérdés maga a mi funkciónk.

### `PicasaPy/EditOverwriteDialog.qml` — 4

- „Edits overwritten by another program”
  - *saját funkció* — A #643 kétirányú .picasa.ini szinkron/round-trip kezelése — amit a docs/decisions/vedett-sajat-funkciok.md saját funkcióNAK sorol fel ('amíg a kétirányú átjárás nincs meg, a Picasa írása nyer') — ehhez a saját mechanizmushoz tartozó figyelmeztető párbeszéd; az eredetiben nincs ilyen konfliktus-értesítés.
- „Another program changed these pictures and removed the edits you made here:”
  - *saját funkció* — A #643 kétirányú .picasa.ini szinkron/round-trip kezelése — amit a docs/decisions/vedett-sajat-funkciok.md saját funkcióNAK sorol fel ('amíg a kétirányú átjárás nincs meg, a Picasa írása nyer') — ehhez a saját mechanizmushoz tartozó figyelmeztető párbeszéd; az eredetiben nincs ilyen konfliktus-értesítés.
- „While the same folder is open in Picasa, its changes overwrite the edits made here. Restoring writes your edits back.”
  - *saját funkció* — A #643 kétirányú .picasa.ini szinkron/round-trip kezelése — amit a docs/decisions/vedett-sajat-funkciok.md saját funkcióNAK sorol fel ('amíg a kétirányú átjárás nincs meg, a Picasa írása nyer') — ehhez a saját mechanizmushoz tartozó figyelmeztető párbeszéd; az eredetiben nincs ilyen konfliktus-értesítés.
- „Restore edits”
  - *saját funkció* — A #643 kétirányú .picasa.ini szinkron/round-trip kezelése — amit a docs/decisions/vedett-sajat-funkciok.md saját funkcióNAK sorol fel ('amíg a kétirányú átjárás nincs meg, a Picasa írása nyer') — ehhez a saját mechanizmushoz tartozó figyelmeztető párbeszéd; az eredetiben nincs ilyen konfliktus-értesítés.

### `PicasaPy/EditorLegacyTab.qml` — 4

- „These filters come from older Picasa versions.”
  - *saját funkció* — A 'Regi effektek' ful (#571) sajat funkcio: a motor ismer olyan szureket, amiket a Picasa 3.9 felulete sosem mutatott meg - ez a fejlec-magyarazat a mi hozzaadott fulunkhoz tartozik.
- „Today's Picasa only recognises them inside your old edits.”
  - *saját funkció* — A 'Regi effektek' ful (#571) sajat funkcio - magyarazo szoveg ugyanahhoz a fulhoz.
- „This name is a leftover from an old configuration. Picasa 3.9 has no processor for it either, so it cannot be applied.”
  - *saját funkció* — A 'Regi effektek' ful (#571) sajat funkcio - egy konkret nem-alkalmazhato regi szuro magyarazata.
- „Picasa can read this filter from an old .picasa.ini, but its exact pixel operation has not been decoded yet, so it cannot be applied.”
  - *saját funkció* — A 'Regi effektek' ful (#571) sajat funkcio - egy konkret, meg nem dekodolt regi szuro magyarazata.

### `PicasaPy/FolderPane.qml` — 4

- „Create a Set or use an existing one”
  - ⚠️ *besorolatlan*
- „All Files are backed up in this set”
  - ⚠️ *besorolatlan*
- „Currently unavailable — the folder stays in the database, thumbnails come from the cache.”
  - *szükséges segédszöveg* — Ugyanaz a helyzet, mint a Main.qml megfelelo sorae (mappaelerhetetlenseg magyarazata); nincs talalhato eredeti megfelelo.
- „Folders on Disk”
  - *szükséges segédszöveg* — A ui-lefedettseg.md spec kifejezetten kizarja: 0,97-es hasonlosaggal illeszkedik a CAcquireUI::folderondisk EGYES szamu 'Folder on Disk' feliratara, ami az eredetiben a gyujtemeny alapertelmezett NEVE, nem panel-cimsor - mas szerepu par, nem bizonyithato eltereres.

### `PicasaPy/OptionsTabSlideshow.qml` — 4

- „Loop slideshow”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Diavetítés ismétlése”).
- „Play music tracks during slideshow”
  - ⚠️ *besorolatlan*
- „Select a folder of music tracks:”
  - ⚠️ *besorolatlan*
- „Browse...”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk a hivatalossal egyezik, csak …/... eltérés („Tallózás…”, Beállítások ▸ Diavetítés).

### `PicasaPy/PeoplePanel.qml` — 4

- „Unnamed people in these photos:”
  - ⚠️ *besorolatlan*
- „No people have been found yet. As faces are ”
  - *szükséges segédszöveg* — Ures allapot szoveg az Emberek panelen; nincs talalhato eredeti megfelelo.
- „Named people who appear with the currently ”
  - *szükséges segédszöveg* — Az Emberek panel dinamikus instrukcio-szovege (peoplepanel/instructions); ez az elem az eredetiben futasidoben toltodik ki, a statikus .tre kinyeres nem tartalmazza a tenyleges szoveget.
- „People who appear in the currently selected ”
  - *szükséges segédszöveg* — Ugyanaz a dinamikus instrukcio-terulet, mas allapota; nincs talalhato statikus eredeti szoveg.

### `StartupRelocateWindow.qml` — 4

- „Moving the database”
  - *szükséges segédszöveg* — Az adatbázis áthelyezése az eredetiben is megvan (Eszközök ▸ Adatbázis helyének kiválasztása…), az induláskori folyamatjelző szövegének nincs eredeti párja.
- „PicasaPy is moving the database.”
  - *szükséges segédszöveg* — Az adatbázis-áthelyezés (eredeti funkció) induláskori folyamatjelzője; eredeti szövege nincs.
- „Photo index…”
  - *szükséges segédszöveg* — Az adatbázis-áthelyezés (eredeti funkció) folyamatjelzőjének lépése; eredeti szövege nincs.
- „Thumbnail cache…”
  - *szükséges segédszöveg* — Az adatbázis-áthelyezés (eredeti funkció) folyamatjelzőjének lépése; eredeti szövege nincs.

### `PicasaPy/CompactDatabaseDialog.qml` — 3

- „PicasaPy is compacting its database to save disk ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg a hivatalos, egyetlen eltéréssel: a programnév Picasa helyett PicasaPy (a saját termékünk nevét mondja, #3573).
- „The database is already compact — nothing to do.”
  - *szükséges segédszöveg* — A adatbázis már tömör – nincs teendő állapotüzenet; a panel-feliratok-hu.tsv compacting-panelje nem tartalmaz ilyen tételt, tehát ez a helyzet (már tömör az adatbázis) az eredetiben nem termel ismert szöveget.
- „Compacting cancelled. Your database is unchanged.”
  - *szükséges segédszöveg* — A tömörítés megszakítva állapotüzenet; a panel-feliratok-hu.tsv compacting-panelje nem tartalmaz ilyen tételt, ez a helyzet az eredetiben nem termel ismert szöveget.

### `PicasaPy/EditorDialogs.qml` — 3

- „This file is read only. In order to edit this file, ”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött mondat töredéke; a teljes szöveg az angolban és a magyarban is betűre a hivatalos (#3573).
- „The automatic copy is not available yet. To edit this ”
  - *szükséges segédszöveg* — A kód-komment kifejezetten kimondja: 'A második a MIÉNK, és azért kell, mert a mappa-másolás még nincs megvalósítva' — saját kiegészítő magyarázat egy funkcióhiányra.
- „Due to a disk error. The disk may be full or read-only.”
  - *szükséges segédszöveg* — A #643 round-trip őr saját elutasító üzenete (kód-komment: 'Az üzenet a kivételből jön, és önmagában teljes'), nem az eredeti általános lemezhiba-eset szövege.

### `PicasaPy/EditorFinetunePanel.qml` — 3

- „One-click lighting fix”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az editpanel/magic_lighting hivatalos magyarjával.
- „Pick a neutral gray or white area of the photo to”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az editpanel/droppertoggle hivatalos magyarjával.
- „One-click color fix”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az editpanel/magic_color hivatalos magyarjával.

### `PicasaPy/EditorRedeyePanel.qml` — 3

- „Click, hold, and drag the mouse around each eye separately ”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a vörösszem-panel editpanel/redeyetext hivatalos magyarjával (az angol is azonos).
- „Note: click inside the box to undo the change.”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a RedEye::DragToSelectMessage „Megjegyzés” mondatával; csak az angol saját fogalmazás.
- „No red eye was found automatically.”
  - *szükséges segédszöveg* — Automatikusan nem talált vörösszemet állapotüzenet; a hivatalos RedEye::* üzenetek csak a TALÁLT esetre adnak szöveget, a nem-talált állapotra nincs hivatalos megfelelő — ez a mi saját státuszjelzésünk.

### `PicasaPy/HelpDialog.qml` — 3

- „Back”
  - *szükséges segédszöveg* — A súgó funkció megvan, de az eredeti online súgót nyit; beépített súgóablak és benne „Vissza” gomb nincs.
- „Contents”
  - *szükséges segédszöveg* — A súgó funkció megvan, de az eredeti online súgót nyit; beépített súgóablak „Tartalom” eleme nincs.
- „Search in help”
  - *szükséges segédszöveg* — A súgó funkció megvan, de az eredeti online súgót nyit; beépített súgóablak keresőmezője nincs.

### `PicasaPy/MainToolbar.qml` — 3

- „Show duplicate files only”
  - *saját funkció* — A keresosav NEGYEDIK szuro-ikonja (masodpeldany-szuro): a docs/decisions/vedett-sajat-funkciok.md szerint (#839) ez a mi sajat hozzaadasunk - az eredetiben ezen a helyen a 'webview' szuro all.
- „Search”
  - *szükséges segédszöveg* — A kereses-mezo helyettesito szovege; nincs talalhato eredeti megfelelo (az eredeti searchoptions/search elem szoveg nelkuli).
- „View releases on GitHub”
  - *saját funkció* — GitHub Kiadasok linkjenek buboreksugoja - kifejezetten PicasaPy-specifikus funkcio, az eredetiben nincs ilyen.

### `PicasaPy/OptionsDialog.qml` — 3

- „Printing”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/tab106.title hivatalos magyarjával.
- „Network”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/tab128.title hivatalos magyarjával.
- „Name Tags”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az options/tab169.title hivatalos magyarjával.

### `PicasaPy/OptionsTabFileTypes.qml` — 3

- „Display JPEG files and:”
  - ⚠️ *besorolatlan*
- „RAW”
  - ⚠️ *besorolatlan*
- „Supported Formats”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Támogatott formátumok”).

### `PicasaPy/PicasaDataImportDialog.qml` — 3

- „Import from Picasa”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja: "PicasaDataImportDialog.qml (#3132) — a régi Picasa adatbázisának átvétele... Az eredetinek ilyen parancsa nincs és nem is lehet — ő MAGA a db3 gazdája."
- „No Picasa data found on this computer.”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja: "PicasaDataImportDialog.qml (#3132) — a régi Picasa adatbázisának átvétele... Az eredetinek ilyen parancsa nincs és nem is lehet — ő MAGA a db3 gazdája."
- „Copying names, keywords and places from Picasa...”
  - *saját funkció* — A docs/decisions/vedett-sajat-funkciok.md kifejezetten felsorolja: "PicasaDataImportDialog.qml (#3132) — a régi Picasa adatbázisának átvétele... Az eredetinek ilyen parancsa nincs és nem is lehet — ő MAGA a db3 gazdája."

### `PicasaPy/QuickTagsConfigDialog.qml` — 3

- „You can use Quick Tags to apply a tag with a single click.  Type in tags below that you want to have one-click access to.  By default, the top two Quick Tags are used to track recently applied tags.  Uncheck the checkbox below to manually set the top two tags.”
  - ⚠️ *besorolatlan*
- „Reserve the top two buttons for recently used tags”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik a quicktagconfig/recent_checkbox_label hivatalos magyarjával.
- „Autofill empty boxes above with commonly used tags”
  - ⚠️ *besorolatlan*

### `PicasaPy/AboutDialog.qml` — 2

- „About PicasaPy”
  - *valódi eltérés* — SZÁNDÉKOS: a program neve PicasaPy, ezért „A PicasaPy névjegye” — a hivatalos szerkezet („A Picasa névjegye”) szerint, csak a terméknév más. Ugyanaz az ablakcím; a különbség csak a terméknév (kódkomment nem mondja ki szándékként). Hivatalos: „A Picasa névjegye” → nálunk: „A PicasaPy névjegye”. (hivatalos: `about/window1.title` „About Picasa (angol forrás nincs a korpuszban, a menütétel „&About Picasa” alapján)”)
- „A modern, open Picasa successor.”
  - *szükséges segédszöveg* — Sajat termek-tagline a Nevjegy dialogusban ('a mi sajat sugo-/magyarazo szovegunk'); nincs eredeti megfelelo, mert ez kifejezetten a mi forkunk leirasa.

### `PicasaPy/CollagePanel.qml` — 2

- „Create the collage and set it as the desktop background”
  - *szükséges segédszöveg* — Kollazs-mentes mod-valaszto felirata (asztali hatterkepnek allitas); nincs talalhato eredeti szo szerinti megfelelo (bar a funkcio - IDS_CONFIRM_SET_DESKTOP/IDS_CONFIRM_DESKTOPCOLLAGE - maga eredeti).
- „Save as a JPG in the Collages album (in the Projects ”
  - *szükséges segédszöveg* — Kollazs-mentes mod-valaszto felirata (JPG mentese a Kollazsok albumba); nincs talalhato eredeti szo szerinti megfelelo.

### `PicasaPy/ConfigureButtonsDialog.qml` — 2

- „Available buttons:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Rendelkezésre álló gombok:”, gombkezelő bal lista).
- „Current buttons:”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Jelenlegi gombok:”, gombkezelő jobb lista).

### `PicasaPy/EditorRetouchPanel.qml` — 2

- „Click to select the area to fix. Then, move the mouse to ”
  - *szükséges segédszöveg* — A retusáló eszköz saját, hosszú használati útmutatója; nincs megfelelője a forrásokban.
- „Refining…”
  - *szükséges segédszöveg* — Átmeneti állapotjelző felirat ('Refining…') a retusálás véglegesítése közben; nincs megfelelője a forrásokban.

### `PicasaPy/EmailChoiceDialog.qml` — 2

- „Send pictures by email”
  - *szükséges segédszöveg* — A fájl saját megjegyzése szerint (#1798) ez egy leegyszerűsített párbeszéd: az eredeti `choose_mail` két úttal (levelezőprogram / Google Mail) kérdez, itt viszont csak az élő út (alapértelmezett levelezőprogram) marad, mert a Gmail-ág linuxon nem építhető fel. A cím emiatt saját, a leegyszerűsített helyzetre írt szöveg.
- „The pictures will be attached to a new message in ”
  - *szükséges segédszöveg* — A leegyszerűsített, egyutas párbeszéd magyarázó sora — az eredeti `choose_mail` két lehetőség közül választat ("Válassza ki, hogyan szeretné e-mailben elküldeni fotóit."), nálunk viszont csak tájékoztat az egyetlen útról; más a helyzet, saját szöveg.

### `PicasaPy/LightboxFeed.qml` — 2

- „All Files are backed up in this set”
  - ⚠️ *besorolatlan*
- „No photos found”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („A program nem talált fotókat”).

### `PicasaPy/LightboxHeader.qml` — 2

- „Remove all suggestions”
  - *valódi eltérés* — SZÁNDÉKOS: kijelölt javaslat nélkül a gomb nálunk az összesre hat, és a súgó ezt mondja; kijelölt javaslatnál a mért „Remove selected suggestions” áll (#2187). Hivatalos magyar: „Kijelölt javaslatok törlése” — nálunk: „Az összes javaslat törlése”. (hivatalos: `faceheaderpanel/removesel` „Remove selected suggestions”)
- „Lower the recognition threshold to get more suggestions”
  - *szükséges segédszöveg* — A gomb megvan, de a buboréksúgója az eredetiben ki van kommentezve (faceheaderpaneltext.tre: „#Tooltip faceheaderpanel/moresug / #Lowers matching threshold”), tehát nem jelenik meg.

### `PicasaPy/PassportErrorDialog.qml` — 2

- „The picture could not be read.”
  - ⚠️ *besorolatlan*
- „The cropped picture could not be saved.”
  - ⚠️ *besorolatlan*

### `PicasaPy/PerfMonitorPanel.qml` — 2

- „Performance monitor”
  - *saját funkció* — A Teljesítmény-monitor a docs/decisions/vedett-sajat-funkciok.md szerint saját funkció (#1364): fejlesztői eszköz, az eredeti Picasa 3.9 Súgó menüjében nincs ilyen menüpont vagy panel.
- „Save diagnostics...”
  - *saját funkció* — A Teljesítmény-monitor a docs/decisions/vedett-sajat-funkciok.md szerint saját funkció (#1364): fejlesztői eszköz, az eredeti Picasa 3.9 Súgó menüjében nincs ilyen menüpont vagy panel.

### `PicasaPy/PicasaNotifier.qml` — 2

- „The collage is ready (click here)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („A kollázs kész (kattintson ide)”).
- „Copy saved”
  - *szükséges segédszöveg* — Sikeres masolat-mentes ertesites; nincs talalhato eredeti megfelelo (a Save a Copy funkcio eredeti, de a sikeruzenet szovege nem talalhato).

### `PicasaPy/PicasaScrollBar.qml` — 2

- „Previous album”
  - *szükséges segédszöveg* — Az album-navigáció "előző" nyílgombjának felirata; feltehetően ikon-gomb hozzáférhetőségi neve, nincs hozzá talált hivatalos szöveges forrás.
- „Next album”
  - *szükséges segédszöveg* — Az album-navigáció "következő" nyílgombjának felirata; ugyanaz az indoklás, mint az előzőnél.

### `PicasaPy/PlacesPanel.qml` — 2

- „The map component (QtLocation) is not available. Geotags can still be edited.”
  - *szükséges segédszöveg* — A QtLocation térkép-modul hiányára figyelmeztető saját szöveg; ez a helyzet az eredetiben nem állhat elő.
- „Right-click the map to place the selected pictures.”
  - *szükséges segédszöveg* — Saját súgószöveg a térképre kattintás módjáról; a geopanel/geo_info elem (ui-leltar.csv) üres felirat-mezővel szerepel, tehát az eredeti nem ír ki ide szöveget.

### `PicasaPy/RightDrawer.qml` — 2

- „Switch between the small and large side panel”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Váltás a kis és a nagy oldalpanel közt”).
- „Close side panel”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Oldalpanel bezárása”).

### `PicasaPy/TagContextMenu.qml` — 2

- „Find Items Tagged This Way”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („Az ilyen címkével ellátott elemek keresése”).
- „Remove Tag”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („A címke eltávolítása”).

### `PicasaPy/TesztuzemNaploDialog.qml` — 2

- „Save Log As...”
  - *saját funkció* — A fájl fejléc-megjegyzése szerint (#1654/#2553) ez a tesztüzem (Test Mode, #1701 — a docs/decisions szerint is "PicasaPy saját eszköze") naplójának mentés-párbeszéde.
- „Text Files”
  - *saját funkció* — Ugyanannak a tesztüzem-naplónak a fájltípus-szűrője — a #142/#158-cal azonos saját funkció része.

### `PicasaPy/ActivityBadge.qml` — 1

- „Stop the background operation”
  - *szükséges segédszöveg* — Tooltip a jobb-felső háttérművelet-jelző megszakítás-gombján; a ui-leltar.csv activity/activitybutton eleme üres buborék-mezővel szerepel, az eredetihez ehhez a gombhoz nincs rögzített szöveg — saját kiegészítés.

### `PicasaPy/AddCustomAspectRatioDialog.qml` — 1

- „Width:”
  - *szükséges segédszöveg* — Az Egyéni méretarány párbeszéd megvan, de az eredetiben egy „Méretek:” csoportcímke áll „x” elválasztóval, külön „Szélesség:” felirat nincs.

### `PicasaPy/CollageDoneNotice.qml` — 1

- „The collage is ready (click here)”
  - *a mérő vakfoltja — az eredetiben is megvan* — A mi magyarunk betűre egyezik a hivatalossal („A kollázs kész (kattintson ide)”); az angol csak fogalmazásban tér el.

### `PicasaPy/CollageSettingsTab.qml` — 1

- „Show captions as text on pictures with an ”
  - *szükséges segédszöveg* — A "Feliratok mutatása" jelölőnégyzet buboréksúgója (saját magyarázó szöveg); nincs hozzá talált hivatalos forrás.

### `PicasaPy/DocumentTabStrip.qml` — 1

- „The current collage contains unsaved changes.\n\n”
  - *a mérő vakfoltja — az eredetiben is megvan* — Tördelés: összefűzött szöveg töredéke; a teljes magyar betűre egyezik a hivatalossal, csak az idézőjel alakja más („Kollázsok” ↔ "Kollázsok").

### `PicasaPy/FolderContextMenu.qml` — 1

- „&Manual order”
  - *bizonytalan* — A helyzet azonossága kérdéses: a CSelectionNode::SortPrior („Rendezés prioritás szerint”) a mért forrás szerint rendezési ÁLLAPOTSZÖVEG, nem menütétel, és a mért Mappa ▸ Rendezés almenüben nincs kézi/prioritás tétel; a kódkomment menütételnek mondja, ezt nem igazolja semmi.

### `PicasaPy/FolderStatePanel.qml` — 1

- „Select a folder on the left.”
  - *szükséges segédszöveg* — Üres-állapot súgószöveg, ha nincs kiválasztott mappa; nincs megfelelője a forrásokban.

### `PicasaPy/GiftCdHost.qml` — 1

- „The disc image could not be created.”
  - ⚠️ *besorolatlan*

### `PicasaPy/HistogramBox.qml` — 1

- „Histogram and camera information”
  - *szükséges segédszöveg* — A hisztogram+EXIF panel hozzaferhetosegi neve; az eredeti thumbui/histogram elem ikon-csak, felirat/buborek nelkul.

### `PicasaPy/ImportProgressPanel.qml` — 1

- „Importing”
  - *bizonytalan* — A lebegő import-folyamatpanel címére nincs hivatalos forrás, és az is kérdéses, hogy az eredetiben van-e ilyen panel; a talált „Importálás” sztringek fülek/gombok, más helyzet.

### `PicasaPy/PicasaMenuItem.qml` — 1

- „This is a PicasaPy addition — the original Picasa did not have it.”
  - *szükséges segédszöveg* — Ez maga a generikus "ez PicasaPy-többlet" jelölő-tooltip szövege, amit a `sajat: true` jelölésű menütételek (pl. Sötét téma, Teljesítmény-monitor) kapnak — definíció szerint saját, magyarázó/hozzáférhetőségi szöveg, nem egy konkrét funkcióhoz kötött felirat.

### `PicasaPy/PropertiesPanel.qml` — 1

- „Select a picture to see its properties.”
  - *szükséges segédszöveg* — Üres-állapot súgószöveg, ha nincs kiválasztott kép; az eredetiben ez egy állandó fejlécű oldalpanel (rightdrawerpanel, 'Metaadatok' címmel), üres-állapot szövegre nincs bizonyíték.

### `PicasaPy/SlideshowView.qml` — 1

- „Display Time”
  - ⚠️ *besorolatlan*

### `PicasaPy/SplashScreen.qml` — 1

- „Please note: PicasaPy is still a work in ”
  - *szükséges segédszöveg* — Sajat, PicasaPy-specifikus figyelmeztetes ('meg fejlesztes alatt'); nincs es nem is lehet eredeti megfelelo.

### `PicasaPy/TagsPanel.qml` — 1

- „Select pictures to tag them.”
  - *szükséges segédszöveg* — Ures kijeloles utmutato szovege a Cimkek panelen; nincs talalhato eredeti megfelelo.

### `PicasaPy/TimelineView.qml` — 1

- „No pictures yet”
  - *szükséges segédszöveg* — A fájl saját megjegyzése szerint ("Picasa Timeline: nincs vetíthető korszak → informatív üres állapot") a Timeline nézet maga eredeti, de ez a konkrét üres-állapot szöveg a mi saját visszajelzésünk arra a helyzetre, amikor nincs megjeleníthető korszak.

### `PicasaPy/VideoPlayerView.qml` — 1

- „Unable to play this video.”
  - *szükséges segédszöveg* — Saját videólejátszási hibaüzenet; nincs megfelelője a forrásokban.

### `PicasaPy/ViewerContextMenu.qml` — 1

- „Block Upload”
  - *a mérő vakfoltja — az eredetiben is megvan* — A magyar szövegünk betűre egyezik az AlbumPhoto::ID_SUPPRESS hivatalos magyarjával (csak a & gyorsbillentyű-jel hiányzik); az angol eltér („Block from Uploading”).

## Figyelmeztetések a generáláskor

- 27 elem LEVÉLNEVE megvan horgonyzott szakaszban, a TELJES neve viszont nem — a mérés ezért »feltáratlan«-nak látja (#2504). Írd ki a teljes nevet:
-     collagepanel/action_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     collagepanel/landscape :: kollazs-atvilagitas.md: 0x00cbf878
-     collagepanel/portrait :: kollazs-atvilagitas.md: 0x00cbf878
-     collagepanel/rand_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     collagepanel/snap_rotation_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     collagepanel/z_order_group :: kollazs-panel-ui-spec.md: 0x0082a670
-     editpanel/aa_2up_icon :: ui-audit-editor.md: 0x00569af0
-     editpanel/ab_2up_icon :: ui-audit-editor.md: 0x00569af0
-     editpanel/cropapply_icon :: szerkeszto-panel-meretek.md: referencia/tre-eroforrasok/editpanel.tre:
-     editpanel/cropcancel_icon :: szerkeszto-panel-meretek.md: referencia/tre-eroforrasok/editpanel.tre:
-     editpanel/fx12_adorn :: filterdesc-registry.md: 0x00d67f68
-     editpanel/only_1up_icon :: ui-audit-editor.md: 0x00569af0
-     editpanel/selection_label_bg :: ui-audit-editor.md: 0x00569af0
-     editpanel/swap_2up_focus_icon :: ui-audit-editor.md: 0x00569af0
-     editpanel/swap_2up_layout_icon :: ui-audit-editor.md: 0x00569af0
-     … és még 12 elem
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

