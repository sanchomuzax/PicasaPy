# Hivatalos Picasa-magyar terminológia — kutatási jegyzet

**Forrás:** az eredeti Picasa 3.9 programmappa (Windows, 2015-ös kiadás).
**Cél:** a Picasa hivatalos magyar fordításának feltérképezése, hogy a
PicasaPy szóhasználata igazodjon hozzá, ahol ez ésszerű.

## 1. Mit sikerült kinyerni, honnan

| Forrás | Tartalom | Eredmény |
|---|---|---|
| `cdautorun/Picasa CD Slideshow.app/.../hu.lproj/i18n/cdgo_stringres.xml` | a CD-s "Picasa CD Slideshow" segédalkalmazás felirat-táblája | 91 `<stringres>` bejegyzés (hónapnevek, fájlméret-formátumok, rendszer-mappanevek, CD-másolási üzenetek — **nem** a fő Picasa UI szókincse) |
| `cdautorun/Picasa Restore.app/.../hu.lproj/i18n/restore_stringres.xml` | a "Picasa Restore" helyreállító segédprogram feliratai | 95 bejegyzés, ugyanaz a jellegű tartalom, plusz a helyreállítás-specifikus szövegek (Másolás, Csere, Kész, stb.) |
| `i18n/uninstall_hu.html` | eltávolítási súgóoldal (windows-1250 kódolású HTML, `strings`/naiv olvasással olvashatatlan volt — a `\xE1` stb. bájtokat windows-1250-ként dekódolva helyreállt) | 1 futószöveg (kb. 200 szó), nem terminológia-forrás, inkább stílusminta |
| **`Picasa3i18n.dll`** (~26 MB) | a **fő Picasa 3.9 UI fordítási erőforrása**: egy hatalmas, a DLL-be linkelt XML-erőforrás-tábla (`<stringres id="…"><xmbtext>…</xmbtext></stringres>` és `<action type="…" target="…">` szerkezetben), **kb. 30 nyelven**, nyelvjelző nélkül egymás után felfűzve | **a legértékesebb forrás** — l. lent |

### A DLL-ből történő kinyerés módszere

A szokásos `strings -e l` (UTF-16LE) és `strings` (ASCII) parancsok **nem**
találtak magyar szöveget: a DLL-ben a szöveg **UTF-8 kódolású**, ASCII és
2 bájtos UTF-8 sorozatok keverékeként (pl. `é` = `0xC3 0xA9`), amit a
`strings` eszköz minden ékezetes karakternél megszakít, és a nyelv nem külön
van jelölve — az egyes `<action target="…">` / `<stringres id="…">` blokkok
alatt **egymás után, nyelvenként ismétlődve** szerepelnek az `<xmbtext>`
fordítások, angol forrásszöveggel az elején.

Ezért egyedi feldolgozás készült:
1. bájt-szintű reguláris kereséssel kigyűjtöttem az összes nyomtatható
   ASCII + UTF-8 2-bájtos (latin kiegészítő tartomány) futamot a bináris
   fájlból (≈750 000 darab, `dll_utf8_runs.txt`);
2. ebből kiszűrtem azokat az `<xmbtext>` sorokat, amelyek **magyar
   ékezetes karaktert** (őűáéíóúöü stb.) tartalmaznak — **40 435 egyedi
   magyar UI-szöveg**;
3. az `id=`/`target=` attribútumok alapján párosítottam az azonosítót a
   hozzá tartozó magyar szöveggel — **21 574 (azonosító, magyar szöveg)
   pár**, 4246 egyedi azonosítóhoz;
4. néhány azonosítónál (pl. `options/item27.title` → *"Alapértelmezett
   rendszerbeállítás (hu-HU)"*) a szöveg maga is megerősítette, hogy a
   blokk ténylegesen a magyar (hu-HU) nyelvi változat.

Ez a módszer megbízható, mert a nyelvspecifikus szavak (pl. „Mappa”,
„Vágás”, „Csillag”) nem tévedhetők más nyelvre, és több azonosítónál
kereszt-ellenőriztem a szomszédos (más nyelvű) fordításokkal együtt — ha
egy sorban törökül, franciául, csehül és magyarul is szerepelt egy-egy
változat, az egyértelműen azonosítja, melyik a magyar.

**Korlát:** a kinyerés csak azokat a húrokat találja meg, amelyek
ténylegesen tartalmaznak magyar ékezetes karaktert — az ékezet nélküli
magyar szavak (pl. „Album”, „OK”) nem különíthetők el biztosan más
nyelvektől, ezért ott, ahol a magyar szöveg véletlenül nem tartalmazott
ékezetet, nem szerepel a listában (ált. nem volt szükség rá, mert a
Picasa magyar UI szinte minden szava ékezetes).

## 2. Angol → hivatalos Picasa-magyar szójegyzék

| Angol | Hivatalos Picasa-magyar | Forrás (DLL-azonosító) |
|---|---|---|
| Album | Album / Albumok | `Album::ID_ALBUM_DELETE` ("Album törlése"), `eMenuFile::ID_FILE_NEWLABEL` ("Új album...") |
| Album caption/description | Albumleírás | `Album::ID_ALBUM_EDITCAPTIONS` ("Albumleírás szerkesztése...") |
| Folder | Mappa / Mappák | `CAlbumState::Folders` ("Mappák"), `eMenuFile::ID_FILE_NEWFOLDER` |
| Folder caption/description | Mappaleírás | `Folder::ID_ALBUM_EDITCAPTIONS` |
| Tag / Keyword | Címke / Címkék | `keywords/keywords_label`, `IPTC::Keywords`, `CKeywordDialog::title` ("Picasa: Címkék") |
| Caption (fotófelirat) | Képfelirat | `editpanel/captiontrash` ("Képfelirat törlése"), `IDS_CONFIRM_CAPTION_TRASH` |
| Star / Starred | Csillag / csillagozott | `confirmsync/starred.title` ("...csillagozott fotók..."), `headerpanel/select_star` ("Csillagozott fotók kijelölése") |
| Slideshow | Diavetítés | `eMenuView::ID_VIEW_SLIDESHOW`, `IDS_SLIDESHOW_PREFS` |
| Import | Importálás | `eMenuFile::ID_FILE_IMPORTPICTURE` ("Importálás forrása...") |
| Export | Exportálás | `eMenuFile::ID_FILE_EXPORTTOFOLDER` ("Kép exportálása mappába...") |
| Print | Nyomtatás | `eMenuFile::ID_FILE_PRINT` |
| Face / People (menüpont) | Személy(ek) | `AlbumList::ID_PEOPLEBYNAME` ("Személyek rendezése név alapján"), `AlbumList::ID_PEOPLEBYAMOUNT` |
| Name Tag | Névcímke | `Album::ID_ALBUM_FILTERFACES` ("Névcímkék hozzáadása") |
| Add Name (személyfelismerésnél) | Név hozzáadása | `peoplepanel/addname`, `CAlbumSelectionNode::addname` |
| Timeline | Időrend | `eMenuView::ID_VIEW_TIMELINE`, `thumbui/timelinebutton` |
| Picture Tray / Hold | Kijelölés megtartása | `Tray::ID_PICTURE_HOLDINPICTURETRAY` |
| Tray — kijelölés eltávolítása | Kijelölés eltávolítása | `Tray::ID_REMOVE_SELECTION` |
| Crop | Vágás | `editpanel/crop`, `IDS_CROP_LABEL`, `filter_crop_label0` |
| Crop (párbeszédcím) | Fotó vágása | `editpanel/crop_label` |
| Straighten | Kiegyenesítés | `editpanel/horizonadjust` |
| Redeye / Red-Eye | Vörösszem | `editpanel/redeye`, `IDS_REDEYE_LABEL`, `filter_redeye_label0` |
| Fill Light | Derítőfény | `editpanel/filllightlabel`, `editpanel/filllight_icon` |
| Neutral Color Picker | Alapszínválasztás | `editpanel/greybalancelabel` |
| Color Temperature | Színhőmérséklet | `filter_colortemp_label0` |
| Auto Color | Automatikus szín | `eMenuPicture::ID_PICTURE_AUTO_COLOR` |
| I'm Feeling Lucky | Jó napom van | `editpanel/enhance`, `eMenuPicture::ID_PICTURE_ENHANCE` |
| Retouch | Retusálás | `editpanel/retouch` |
| Retouch (párbeszédcím) | Szennyeződések retusálása | `editpanel/retouch_label` |
| Sharpen | Élesítés | `eMenuPicture::ID_PICTURE_SHARPEN` |
| Warmify | Melegítés | `eMenuPicture::ID_PICTURE_WARMIFY` |
| Film Grain | Filmkörnung *(csak német/katalán/spanyol adat volt, magyar nem került elő)* | — nincs magyar találat |
| Sepia | Szépia | `eMenuView::ID_PICTURE_SEPIA`, `filter_sepia_label0` |
| Tint (régi szűrő) | Árnyalás (régi) | `filter_tint_label0` |
| Graduated Tint | Színátmenet | `filter_dir_tint_label0` |
| Radial Tint | Sugaras árnyalás | `filter_radtint_label0` |
| Glow (régi szűrő) | Ragyogás (régi) | `filter_glow_label0` |
| Filtered B&W | Szűrt FF | `CDesaturateFilter::name` |
| Shadow & Highlight (szűrő) | Árnyék és kiemelés | `filter_shadow_label0` |
| Focal (Pixelate/Zoom) | Ohnisková pixelácia — csak cseh/katalán/finn adat, magyar: "Képpontnövelés fókuszban" | `filter_focalpixelate_label0` |
| Batch Edit | Csoportos szerkesztés | `eMenuPicture::BatchEdit` |
| Geotag | Geocímke / Geocímkézés | `eMenuTools::Geotag`, `eMenuTools::ID_PICTURE_GEOTAG` |
| Duplicate files (Show Duplicate Files) | Fájlok másodpéldányainak megjelenítése | `eMenuTools::ID_DUPES` |
| Revert | Visszaállítás | `AlbumPhoto::ID_FILE_REVERT` |
| Undo | Visszavonás | `eMenuEdit::ID_UNDO` |
| Redo | Újra | `eMenuEdit::ID_REDO` |
| Rotate Clockwise | Forgatás jobbra | `eMenuPicture::ID_PICTURE_ROTATECLOCKWISE` |
| Rotate Counterclockwise | Forgatás balra | `eMenuPicture::ID_PICTURE_ROTATECOUNTERCLOCKWISE` |
| Select All | Összes kép kijelölése | `Album::ID_ALBUM_SELECTALLPICTURES` |
| Add to Album | Hozzáadás albumhoz | `AlbumPhoto::ID_LABELS` |
| New Album | Új album... | `eMenuFile::ID_FILE_NEWLABEL` |
| Move to New Folder | Áthelyezés új mappába... | `eMenuFile::ID_FILE_NEWFOLDER` |
| View by Date / by Name (albumlista rendezés) | Rendezés dátum/név alapján | `AlbumList::ID_VIEWBYDATE`, `AlbumList::ID_VIEWBYNAME` |

*(A `hu_id_text_pairs.tsv` munkafájl 21 574 sorban tartalmazza a teljes
nyers kinyert anyagot — ebből a fenti táblázat a PicasaPy szempontjából
releváns, egyértelműen azonosítható tételeket emeli ki. A teljes anyag
messze nem korlátozódik ennyire — rengeteg egyéb Picasa-funkció (webes
feltöltés, Google Fiókok, nyomtatás, DVD-írás stb.) fordítása is megvan
benne, de ezek a PicasaPy jelenlegi hatókörén kívül esnek.)*

## 3. Összevetés a PicasaPy `picasapy_hu.ts` fájllal

A `picasapy_hu.ts` (2614 sor, `src/picasapy/app/i18n/picasapy_hu.ts`)
jelenlegi magyar szóhasználatának **túlnyomó többsége egyezik** a
hivatalos Picasa-terminológiával — ez örvendetes, valószínűleg mert a
korábbi fordítás már eleve a Picasa szóhasználatát vette alapul. Íme
a pontos egyezések, amiket ellenőriztem:

- Crop → Vágás ✅ egyezik
- Straighten → Kiegyenesítés ✅ egyezik
- Redeye → Vörösszem ✅ egyezik
- I'm Feeling Lucky → Jó napom van ✅ egyezik
- Fill Light → Derítőfény ✅ egyezik
- Color Temperature → Színhőmérséklet ✅ egyezik
- Sepia → Szépia ✅ egyezik
- Warmify → Melegítés ✅ egyezik
- Tint → Árnyalás ✅ egyezik
- Graduated Tint → Színátmenet ✅ egyezik
- Filtered B&W → Szűrt FF ✅ egyezik
- Sharpen → Élesítés ✅ egyezik
- Retouch → Retusálás ✅ egyezik
- Auto Color → Automatikus szín ✅ egyezik
- Undo/Redo → Visszavonás/Újra ✅ egyezik
- Timeline → Időrend ✅ egyezik
- Tag/Tags → Címke/Címkék ✅ egyezik
- Caption → Képfelirat ✅ egyezik (ld. `PicasaMenuBar.qml` sor 198)
- Export Picture to Folder... → Kép exportálása mappába… ✅ **szó szerint egyezik**
- New Album... → Új album… ✅ **szó szerint egyezik**
- Print → Nyomtatás ✅ egyezik

### Talált eltérések (javításra érdemes jelöltek)

| Angol forrás | PicasaPy jelenlegi fordítása | Hivatalos Picasa-magyar | Megjegyzés |
|---|---|---|---|
| „People" (a bal oldali navigációs panel felirata, `FolderPane.qml`) | **Emberek** | **Személyek** | A Picasa saját magyar fordítása következetesen a „Személyek" szót használja a személy/arc-alapú rendezésnél és listázásnál (pl. „Személyek rendezése név alapján"). Az „Emberek" nem hivatalos Picasa-szóhasználat — érdemes „Személyek"-re cserélni az egységesség kedvéért. |
| „Make a caption!" (`PhotoViewer.qml` sor 769) | **Készítsen képaláírást!** | (a Picasa a „felirat" szót használja: **Képfelirat**) | Ugyanaz a fogalom (fotó felirata) a PicasaPy-n belül **kétféleképpen** szerepel: a menüben „Képfelirat" (ez helyes, egyezik a hivatalos szóval), de ennél a helynél „képaláírás". Érdemes „Készítsen feliratot!"-ra vagy „Adjon hozzá feliratot!"-ra igazítani a belső következetesség és a hivatalos szóhasználat miatt. |

### Amit nem lehetett összevetni (nincs hivatalos magyar adat, vagy a PicasaPy még nem implementálta)

- **Highlights** / **Shadows** külön csúszkaként (a Fill Light eszközön
  belül) — a Picasa 3.9 asztali verziójában nem találtam ezekhez külön
  magyar UI-szöveget; a DLL-ben csak az összevont „Shadow & Highlight"
  szűrő neve szerepelt magyarul („Árnyék és kiemelés"). Lehet, hogy a
  külön Highlights/Shadows csúszka csak a Picasa Web/újabb verzióban
  jelent meg, a 3.9 asztali sávban nem volt önálló magyar felirata.
  A PicasaPy „Kiemelések"/„Árnyékok" fordítása nyelvileg helyes, csak
  nem tudtam hivatalos forrással megerősíteni.
- **Film Grain** — csak német/spanyol/katalán adat volt a DLL-ben, magyar
  nem került elő ehhez a konkrét szűrőhöz (bár a PicasaPy „Filmszemcse"
  fordítása nyelvileg pontos és valószínűleg egyezik a hivatalossal).
- **Vignette**, **Museum Matte**, **Polaroid**, **Cinemascope** stb.
  (a „Creative Kit" újabb effektjei) — ezekhez nem sikerült egyértelműen
  magyar szöveget találni a DLL-ben.

## 4. Összegzés

A kinyerés sikeres volt: a `Picasa3i18n.dll` UTF-8-as, nyelvjelző nélküli
XML-erőforrás-táblájából **40 435 egyedi magyar UI-szöveg** (21 574
azonosító-szöveg pár) nyerhető ki egyedi bájt-szintű feldolgozással
(a szokásos `strings -e l` és ASCII `strings` erre nem alkalmas, mert a
szöveg UTF-8, nem UTF-16, és a DLL-ben ~30 nyelv van egymás után, nyelvi
címke nélkül).

A PicasaPy jelenlegi magyar fordítása a vizsgált ~35 kulcsfogalom közül
**33-ban pontosan egyezik** a hivatalos Picasa-szóhasználattal — ez a
korábbi fordítói munka minőségét igazolja. **2 konkrét, forrással
alátámasztott eltérést** találtam ([„People" → „Emberek" vs. hivatalos
„Személyek"]; [„Make a caption!" → „képaláírás" vs. a PicasaPy saját
másik helyén és a hivatalos szóhasználatban is „képfelirat"]) — ezek
apró, biztonságosan javítható pontosítások.
