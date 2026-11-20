# A személyek (arcok) kezelésének teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

Ez a specifikáció a #7289 kutatási feladat alapján összegzi a személyek (arcok) kezelésének teljes futásidejű folyamatát az eredeti Picasa 3.9 (Picasa3.exe 3.9.141.259) bináris vizsgálata, élő futásidejű mérések (job-61, job-64, job-66, job-68, job-113, job-180, job-325) és a PicasaPy megvalósítása alapján.

## 1. Belépési pontok és feltételeik

### 1.1 Menüsáv és főmenüpontok

1. **Eszközök > Beállítások > Névcímkék fül (Tools > Options > Name Tags):**
   - Eredeti: `0x006e3990` (mentés) és `0x006e0ead` (regisztráció). Beállítási kulcsok olvasása a Windows Registry-ből (`HKCU\Software\Google\Picasa\Picasa2\Preferences\`).
   - Feltétel: Mindig elérhető, feltétel nélküli.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaToolsMenu.qml:442` (`menuToolsOptions`), `src/picasapy/app/qml/PicasaPy/OptionsTabNameTags.qml:41`.

2. **Eszközök > Kísérleti > Arcinformációk írása XMP-adatokba... (Tools > Experimental > Write faces to XMP...):**
   - Eredeti: `eMenuTools::ID_WRITE_XMP_FACES` (`0x9e2a`, cím `0xd6e838`). Végrehajtó: `0x004852e0` `PersistFaceToFile`, folyamatjelző `0x006b9dd0` (`FaceTagJob`).
   - Feltétel: Mindig elérhető a kísérleti almenüben.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaToolsMenu.qml:308` (`menuToolsWriteXmpFaces`), `src/picasapy/app/photo_ops_xmp_mixin.py:50`.

3. **Eszközök > Személyek kezelője... (Tools > People Manager...):**
   - Eredeti: `eMenuTools::ID_PEOPLE_MANAGER` (`0x9e0e`, menüből indul: `0x0056d0a0`, párbeszédablak: `0x006443e0` / `0x00644010`).
   - Feltétel: Mindig elérhető.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaToolsMenu.qml:24` (`menuToolsPeopleManager`), `src/picasapy/app/qml/PicasaPy/PeopleManagerDialog.qml:7`.

4. **Kép > Arcok alaphelyzetbe állítása (Picture > Reset Faces):**
   - Eredeti: `eMenuPicture::ID_PICTURE_RESET_FACES` (`0x9e11`, cím `0xd6e538`). Kezelő: `0x005cc83c`. Mentés előtti vizsgálat `GetAsyncKeyState`-cel (`0x00c406f8`):
     - Normál kattintás: `0x0057daa0` (csak a kijelölt fotók arcainak alaphelyzetbe állítása).
     - Ctrl + kattintás: `0x006038b0` (`RemoveAllFaceData` - összes arc-adat és személyalbum törlése, teljes újrakeresés).
     - Shift + kattintás: `0x00603a20` (`ResetAllFaces` - összes személyalbum törlése, arcok visszakerülnek a Név nélküliek albumba).
   - Feltétel: Kijelölés szükséges normál esetben (`hasSelection`).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaPictureMenu.qml:150` (`menuPictureResetFaces`), `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:67`, `src/picasapy/app/face_scan_controller_reset_mixin.py:93` (`resetFacesForPhotos`), billentyűmódosítók leképezése a `resetFacesConfirmDialog`-ra.

5. **Létrehozás > Film > A kijelölésben lévő arcokból... / Az Emberek albumból... (Create > Movie > From Faces in Selection... / From People Albums...):**
   - Eredeti: `eMenuCreateMovie::ID_FACES` (`0x9d59`), `eMenuCreateMovie::ID_FACESRANDOM` (`0x9d5a`), vezérlő: `0x00603660`.
   - Feltétel: Arcok a kijelölésben, illetve létezik személyalbum.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:150`.

6. **Eszközök > Névcímkék letöltése a Picasa Webalbumokból (Tools > Download Name Tags from PWA):**
   - Eredeti: `eMenuTools::ID_TOOLS_DOWNLOAD_FACES` (`0x9e10`, cím `0xd6e918`), de a menü megnyitásakor a Picasa önmaga azonnal törli (`RemoveMenu`, `0x0056f69e`, ld. `picasa-menu-parancsok-viselkedes.md` 36.1). A felhasználó soha nem látja.
   - Nálunk: Nincs a menüben (helyesen követi az eredetit).

7. **Eszközök > Arckeresés... (Find Faces):**
   - Eredeti: NINCS ilyen menüpont. Az eredetiben a `BgFaceDetectThread` (`0x0069fc78`) háttérben futott.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaToolsMenu.qml:23` (`menuToolsFindFaces`), `src/picasapy/app/qml/PicasaPy/FaceScanDialog.qml:33`. Szándékos saját UX többlet (#1473).

### 1.2 Helyi menük (Context Menus)

1. **Fotó helyi menü (mappanézet, albumnézet, egyképes nézet):**
   - Eredeti: `AlbumPhoto::ID_PICTURE_RESET_FACES` (`0x9e11`, kezeli: `0x005cc83c`).
   - Feltétel: Van kijelölt fotó.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:541`, `src/picasapy/app/qml/PicasaPy/ViewerContextMenu.qml:318`.

2. **Mappa és Album fejléc helyi menü:**
   - Eredeti: `Album::ID_ALBUM_FILTERFACES` (`0x9e1c`, címek `0x007319f0`, `0x00732160`). Felirat: "&Add name tags" / "Névcímkék hozzáadása".
   - Feltétel: Mappára vagy albumra kattintva; a mappa/album tagjaira indítja el a háttér arckeresést (#4535).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml:369`, `src/picasapy/app/qml/PicasaPy/AlbumContextMenu.qml:68`, `src/picasapy/app/qml/PicasaPy/RecentlyUpdatedContextMenu.qml:121`.

3. **Emberek-album fotó helyi menü (`PplAlbumPhoto::`):**
   - Eredeti:
     - `PplAlbumPhoto::ID_PEOPLEALBUMSNEW` (`0xa0cc`): "Move to &New Person..." / "Áthelyezés új személyhez...".
     - `PplAlbumPhoto::ID_PEOPLEALBUMS` (`0xa0cd`): "Hozzáadás az Emberek albumhoz" / "Move to People Album" (`0x0056d11a`-`0x0056d159` dinamikus almenü-horgony a többi személlyel, nem önálló parancs).
     - `PplAlbumPhoto::ID_SETPEOPLEALBUMCOVER` (`0x9e39`): "Beállítás az Emberek album indexképeként" (`0x00603660`).
     - Eltávolítás az Emberek-albumból (`0x007355c0`, "Remove from People Album", gyorsbillentyű: Ctrl+Delete).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:250-318` (`contextMenuRemoveFromPeopleAlbum`, `contextMenuAddToPeopleAlbumMenu`, `contextMenuMoveToNewPerson`, `contextMenuSetAsPeopleAlbumThumbnail`).

4. **Személyalbum bal hasábbeli gyűjtemény-sorának helyi menüje:**
   - Eredeti: "Edit People Album..." / "Delete People Album" (`0x005c9b00`).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/PeopleAlbumContextMenu.qml:28-66`.

### 1.3 Eszköztár, gombsor és fejlécek

1. **Jobb fiók - Emberek gomb:**
   - Eredeti: `rightdrawerpanel/peoplepanel` gomb, amely kinyitja az Emberek panelt (döntési fa `0x00647df0`).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/RightDrawer.qml`, `src/picasapy/app/qml/PicasaPy/PeoplePanel.qml`.

2. **Személy-album fejlécsávja (`faceheaderpanel`, `0x0074ad40`):**
   - Eredeti: 25 parancs a `0x005e0f70` elosztóban:
     - `face_zoom` / `picture_zoom` (`0x005e5290`, arc-közelítés 35x21 px vs. teljes kép).
     - `confirmsug` (`0x00602640`, push 1: "Az összes jóváhagyása").
     - `confirmsel` (`0x00602640`, push 0: "Jóváhagyás" - kijelöltekre).
     - `removesel` (`0x005c9b00`: kijelölt javaslat elvetése / törlése).
     - `moresug` (`0x00602890`: További javaslatok keresése - küszöb lazítása 0.1-gyel).
     - `sug_filter`: Csak javaslatok szűrése.
     - `set_thumbnail`: Borítókép beállítása (`0x00603660`).
     - `create_face_movie`: Mozgófilm készítése arcokból (`0x00603660`).
     - `addname` (`0x00602970`) és `ignore` (`0x005c9b00`).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml:66-100`, `src/picasapy/app/qml/PicasaPy/LightboxHeaderButtons.qml`, `src/picasapy/app/qml/PicasaPy/LightboxHeaderSuggestionRow.qml`.
   - Helyesbítés (#7296): a `faceheaderpanel` geometriájában (`picasa-arcfelismeres.md` 15.5) nincs `addname` és `ignore` elem; a `0x005e0f70` elosztó a három fejlécpanel közös kezelője, ezért a két parancs ismerete nem jelent gombot a személyalbum fejlécén. Nincs eltérés.

3. **"Név nélküliek" album fejlécsávja (`unknownfaceheaderpanel`, `0x0074ad40`):**
   - Eredeti:
     - `showall` / `cluster` (`clustering_container`, 120x27 px): csoportosított vs. egyedi arcok.
     - `showunknown` / `showignored` (`viewtype_container`, 120x27 px): ismeretlenek vs. figyelmen kívül hagyottak.
     - `addname` (`0x00602970`, 163x20 px): Név hozzáadása.
     - `ignore` (`0x005c9b00`, 120x27 px): Elvetés / mellőzés.
   - Nálunk: `src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml:20`, `UnnamedFacesViewGrid.qml`, `UnnamedFacesViewIgnoredGroups.qml`.

4. **Képszerkesztő - Kézi arc hozzáadása:**
   - Eredeti: `editpanel/addfaceselection` (téglalap rajzolása az arcra).
   - Nálunk: `src/picasapy/app/qml/PicasaPy/FacesOverlay.qml`.

### 1.4 Gyorsbillentyűk

- Eredeti: A menürekordokban és az alkalmazás-szintű gyorsítótáblában NINCS gyorsbillentyű az arckezeléshez (`+0x04` mező = 0 minden menürekordban, megerősítve a `picasa-arcfelismeres.md` 14.1-ben).
- Nálunk: Nincs alkalmazás-szintű gyorsbillentyű. Egyezik.

---

## 2. Ablakok, nézetek, mezők, alapértékek és megerősítések

### 2.1 Személyek kezelője párbeszédablak (People Manager)

- Eredeti (`0x006443e0`, `0x00644010`):
  - Méret: 632 x 372 px.
  - Bal hasáb: Személyek listája felül keresőmezővel, alul "New Person..." és "Delete Person" gombokkal. A lista **egyszeres kijelölésű** (job-325, 58. szakasz: Ctrl és Shift kattintás nem tesz többes kijelölést).
  - Jobb hasáb: Kijelölt személy adatlapja:
    - Név (Name) szöveges beviteli mező.
    - E-mail cím (Email) beviteli mező.
    - Bélyegkép + fotók száma (`%d photos`).
  - Megerősítések és kérdések:
    - Személy törlésekor: megerősítő kérdés a személyalbum törléséről (az arcok visszakerülnek a Név nélküliek közé).
    - Név módosításakor: ha a megadott új név megegyezik egy létező személy nevével, felugrik az egyesítési megerősítés (`Merge People`: "Szeretné egyesíteni ezt a két személyt?").
- Nálunk: `src/picasapy/app/qml/PicasaPy/PeopleManagerDialog.qml:8-17` (szélesség 632, magasság 372, `selectedKey`, `contactList`, `nameField`, `emailField`, egyesítési logika). Egyezik.

### 2.2 Új személy / Név hozzáadása (New Person)

- Eredeti: Párbeszédablak új név és opcionális e-mail cím bevitelhez.
- Nálunk: `src/picasapy/app/qml/PicasaPy/NameInputDialog.qml` és a `PeopleManagerDialog.qml` beágyazott funkciói. Egyezik.

### 2.3 Mellőzés megerősítése (Ignore People Confirm)

- Eredeti (`0x005c9b00`, `PeoplePanel::ConfirmRemove*`):
  - Cím: "Személyek mellőzése" (`PeoplePanel::ConfirmRemoveTitle`).
  - Üzenet: "Biztosan áthelyezi ezt a személyt a Mellőzött emberek albumba?" (`PeoplePanel::ConfirmRemoveMsg`).
  - Jelölőnégyzet: "Ne kérdezzen újból, mindig hagyja figyelmen kívül" (`PeoplePanel::ConfirmRemoveCheck`).
  - Gombok: "Személy mellőzése" / "Mégse".
  - Megjegyzett állapot: A Windows Registry `HKCU\Software\Google\Picasa\Picasa2\Preferences\ConfirmIgnorePerson` értéke. Ha be van jelölve, a következő alkalommal kérdés nélkül azonosítható a mellőzés.
- Nálunk: `src/picasapy/app/qml/PicasaPy/UnnamedFacesViewGrid.qml` és `ConfirmDialog.qml`. Egyezik.

### 2.4 Arcok alaphelyzetbe állítása megerősítés (Reset Faces Confirm)

- Eredeti (`0x006038b0`, `0x00603a20`, `0x00603bb0`):
  - Ctrl mód: "WARNING! This will DELETE all face data, people albums, and rescan all photos for faces again. This can REMOVE name tags on synced web albums. Do you want to do this?"
  - Shift mód: "WARNING! This will DELETE all people albums, and move all the faces to the unnamed album. This can REMOVE name tags on synced web albums also. Do you want to do this?"
  - Normál mód: Csak a kijelölt fotók arcait törli, nem rombol globális albumot.
- Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:80-86` (`resetFacesConfirmDialog.openFor(mode)`), szóról szóra a binárisbeli figyelmeztető szövegekkel. Egyezik.

### 2.5 Beállítások > Névcímkék fül

- Eredeti (`0x006e3990`, `0x006e0ead`):
  - Arcfelismerés engedélyezése (`enablefacedetection` / `BgFaceDetectThread`): alapértelmezett 1 (BE).
  - Javaslatok engedélyezése (`enablefacesuggestions` / `FRAddSuggesetions`): alapértelmezett 1 (BE).
  - Arcinformációk írása a fájlokba (`persistfacetofile` / `PersistFaceToFile`): alapértelmezett 1 (BE).
  - Javaslati küszöb (`facethresh0` / `FRSuggestionThreshold`): 10 fokozatú csúszka (50..95), alapértelmezett 85 (7. index).
  - Rendezési küszöb (`facethresh1` / `FRSortThreshold`): 10 fokozatú csúszka (50..95), alapértelmezett 85 (7. index).
  - Tárolás helye: Windows Registry (`Preferences`).
- Nálunk: `src/picasapy/app/qml/PicasaPy/OptionsTabNameTags.qml:41-80`. Egyezik.

---

## 3. Hatás: fájlok, .picasa.ini, index, felület, kijelölés és háttérmunka

### 3.1 Fájlok és fájlrendszer

1. **Képfájl maga (XMP):**
   - Ha a `PersistFaceToFile` be van kapcsolva (`0x004852e0`, alapértelmezetten 1), a felismert és elnevezett arcok téglalapjai és nevei beírásra kerülnek az XMP metaadatba (`mwg-rs:Regions`).
   - Nálunk: `src/picasapy/export/xmp.py:165`, `src/picasapy/app/photo_ops_xmp_mixin.py:50`.
2. **`.picasa.ini` fájl:**
   - `[Contacts2]` szakasz: `contact_id=name;email;` (pl. `bf1dfa69cbadd03d=Teszt Elek;;`).
   - `faces=rect64(...),<contact_id>;...`:
     - Elnevezett arc: `faces=rect64(...),<16 jegyu hex contact_id>` (job-66).
     - Mellőzött arc: `faces=rect64(...),ffffffffffffffff` (szentinel érték, job-64).
     - Névtelen arc: NEM írják a `.picasa.ini`-be, az érintetlen névtelen arc csak a lokális adatbázisban él (job-61).
     - Visszavonás/eltávolítás: a `faces=` sor törlődik a szakaszból (job-68).
     - `backuphash=...`: a koordináták 64 bites XOR hash-e.
     - `facedata=...`: csak akkor írják, ha a `FRWriteFaceDataINI` be van kapcsolva (`0x00484de7`, alapból 0).
   - Nálunk: `src/picasapy/ini/faces.py` (`serialize_faces`, `parse_faces`, #3792).
3. **`contacts.xml`:** A Picasa által szinkronizált Google-kapcsolatok lokális XML tárolója (`0x0068c030`).

### 3.2 Index és adatbázis

- Eredeti: `db3` mappa PMP állományai:
  - `imagedata.pmp`: `facerect`, `personalbumid`, `suggestionpersonalbumid`, `facequality`, `facerectdata`, `personalbumrecs`, `personalbumrecvalues`, `peoplealbumchecksum` (konstans 34).
  - `albumdata.pmp`: `albumpeoplechecksum` (`acc = rol(acc, 7) XOR kepindex`, 14.6), `albumcontactids`.
- Nálunk: SQLite séma: `people`, `photo_people`, `faces_detected` táblák (`src/picasapy/index/people.py`, `faces_detected.py`).

### 3.3 Bal hasáb (Gyűjtemények / FolderPane)

- `People` (Emberek) kategória:
  - Beépített védett album: `Unnamed` (Név nélküliek, `]unknownface` / `]ignoreface`), amely törölhetetlen (`0x004ac650`).
  - Megnevezett személyek albumai: az arc bélyegképével és a talált fotók számával.
  - Rendezés: név vagy fotószám szerint (`Preferences\peoplesort`).
  - Elnevezés hatására: új személyalbum jelenik meg a listában, a számláló növekszik.
  - Törlés hatására: a személyalbum eltűnik, a fotók visszakerülnek a Név nélküliek közé.
- Nálunk: `src/picasapy/app/people_album_controller.py:78` (`_load_people`, `peopleChanged`), `FolderPane.qml`.

### 3.4 Rács (Grid / Lightbox)

- Arcra nagyítás kapcsolva (`face_zoom`): a bélyegképek négyzetesen az arc körül vágva jelennek meg (`&fz=` paraméter).
- Teljes kép kapcsolva (`picture_zoom`): a teljes fotó látható a cellában.
- Javaslat-adorner: ha van függő javaslat, a rácsbeli bélyegképen megjelenik a `suggestionfaceadorner` jelvény.
- Nálunk: `src/picasapy/app/arc_nagyitas_url.py`, `LightboxHeaderButtons.qml`, `ThumbDelegate.qml`.

### 3.5 Kijelölés

- Személy-album fejlécben: kijelölés nélkül "Az összes jóváhagyása" (`confirmsug`), kijelölt javaslat esetén "Jóváhagyás" (`confirmsel`) és "Eltávolítás" (`removesel`).
- People Manager: egyszeres kijelölés (`selectedKey`).
- Név nélküliek nézet: többes kijelölés lehetséges (Ctrl/Shift-tel, job-180).
- Nálunk: `LightboxHeader.qml:80-85`, `PeopleManagerDialog.qml:49-75`.

### 3.6 Háttérmunka és állapotsor

- Eredeti: `BgFaceDetectThread` (`0x0069fc78`) háttérben fut. Állapotjelzések az Emberek panelen:
  - "Arcok betöltése..." (`Loading1` / `Loading2`)
  - "Arcok rendezése..." / "Arcok adatainak rendezése, %.0f%%" (`PeoplePanel::SortingData`, `0x00647ea9`)
  - "További személyek keresése..." (`PeoplePanel::Looking`, `0x00648070`)
  - ", %d ellenőrizetlen fájl." (`PeoplePanel::Unchecked`, `0x0064810b`)
- Nálunk: `FaceScanController` (`src/picasapy/app/face_scan_controller.py`), haladás a `FolderPane.faceScanPercent`-en és a `FaceScanDialog.qml`-en.

---

## 4. Hibaesetek, megszakítás, hálózati/írásvédett hely és visszavonás

### 4.1 Hibaesetek és üzenetek

1. **Csak olvasható fájl (Read-only file):**
   - Eredeti (`0x004852e0` / `0x00485382`): `Face tag write failed for read only file: %s`.
   - Viselkedés: Az XMP mentés meghiúsul, de az adatbázis (`db3`) és a `.picasa.ini` (ha a mappa írható) frissül.
   - Nálunk: `src/picasapy/app/photo_ops_xmp_mixin.py` kezeli a kivételt.
2. **Általános fájlírási hiba:**
   - Eredeti: `Face tag write failed for: %s`.
3. **Kontakt-írás elbukása:**
   - Eredeti (`0x007d55f0`): `PersistContactToINI failed: err %d`.
   - Viselkedés: Tranzakciós integritás: ha a kontakt kiírása elbukik, a `faces=` sor sem íródik ki a `.picasa.ini`-be.
   - Nálunk: `src/picasapy/ini/` tranzakciós dokumentum-mentés garantálja.
4. **Nem található arc / Több arc:**
   - Eredeti: `Can't find any faces` ("Nem találhatók arcok"), `There appear to be multiple faces.` ("Úgy tűnik, több arc van a képen.").
5. **Védett album törlési kísérlete:**
   - Eredeti (`0x004ac650`, `CThumbUI::DeleteFacesAlbum`): `The found people album cannot be deleted.` ("A talált személyi album nem törölhető.").
   - Nálunk: A beépített `Unnamed` albumon a törlés le van tiltva.
6. **Duplikált művelet:**
   - Eredeti: `Duplicate face operation: photo_id=%llu, contact_id=%llu, rect=(%d,%d,%d,%d)`.

### 4.2 Megszakítás (Cancellation)

- Eredeti:
  - `FaceTagJob` megszakítható a felhasználó által (`FaceTagJob::cancelled`, `0x006b9dd0`).
  - `BgFaceDetectThread` leállítható a Beállításokban az arckeresés kikapcsolásával vagy a kilépéskor; az adatbázis tranzakció az utolsó kész képnél biztonságosan zárul.
- Nálunk: `FaceScanController.cancelScan()`, folyamatjelző és Mégse gomb a `FaceScanDialog.qml`-ben.

### 4.3 Hálózati vagy írásvédett hely

- Eredeti:
  - Hálózati meghajtón (UNC/SMB) vagy CD/DVD-n lévő képeknél: az XMP és `.picasa.ini` nem írható, de a helyi profilbeli `db3` indexbe bekerülnek az arcok és a felületen láthatók maradnak.
  - Mappakezelő: a `frexclude` kapcsolóval a mappa és almappái öröklődően kizárhatók az arckeresésből (`0x006e3990`, `docs/specs/picasa-mappakezelo.md` 5.3).
- Nálunk: Az SQLite index lokális (`~/.local/share/picasapy/`), így írásvédett forrás esetén is működik a felület.

### 4.4 Visszavonás (Undo)

- Eredeti:
  - Nincs globális Szerkesztés > Visszavonás az arcok elnevezésére.
  - Visszavonási utak:
    1. Személyalbumban: a fotó kijelölése és "Eltávolítás" (`removesel`, `0x005c9b00`) -> a fotó arca visszakerül a Név nélküliek közé, a `.picasa.ini`-ből törlődik a `faces=` bejegyzés (job-68).
    2. Fotó áthelyezése másik személyhez: helyi menü "Move to New Person..." (`0xa0cc`) vagy "Move to People Album" (`0xa0cd`).
    3. Arcok törlése a fotón: "Reset Faces" (`0x9e11`).
    4. Mellőzés visszavonása: Név nélküliek nézetben `showignored` nézetre váltás, majd a fotó elnevezése.
- Nálunk: `PhotoContextMenu.qml:250` (`contextMenuRemoveFromPeopleAlbum`), `LightboxHeader.qml:93` (`removeSuggestionsRequested`), `UnnamedFacesViewIgnoredGroups.qml`.

---

## 5. Összevetési táblázat: Eredeti | Nálunk | Teendő

| Eredeti (bináris cím / lelet) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Options > Name Tags beállítások (`0x006e3990`, `0x006e0ead`) | `src/picasapy/app/qml/PicasaPy/OptionsTabNameTags.qml:41` | Egyezik. Nincs teendő. |
| Write faces to XMP... (`0x9e2a`, `0xd6e838`, `0x004852e0`) | `src/picasapy/app/qml/PicasaPy/PicasaToolsMenu.qml:308`, `photo_ops_xmp_mixin.py:50` | Egyezik. Nincs teendő. |
| People Manager ablak (`0x9e0e`, `0x006443e0`, 632x372 px) | `src/picasapy/app/qml/PicasaPy/PeopleManagerDialog.qml:7` | Egyezik. Nincs teendő. |
| Reset Faces háromfelé ágazó logika (`0x9e11`, `0x005cc83c`) | `src/picasapy/app/face_scan_controller_reset_mixin.py:93`, `PicasaMenuBar.qml:67` | Egyezik (Ctrl/Shift esetén modális megerősítés). Nincs teendő. |
| From Faces in Selection... / People Albums (`0x9d59`, `0x9d5a`) | `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:150` | Egyezik. Nincs teendő. |
| Fotó helyi menü Reset Faces (`0x9e11`) | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:541` | Egyezik. Nincs teendő. |
| Mappa/Album helyi menü Add name tags (`0x9e1c`, `0x007319f0`) | `src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml:369`, `AlbumContextMenu.qml:68` | Egyezik. Nincs teendő. |
| PplAlbumPhoto: Move to New Person (`0xa0cc`) | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:293` | Egyezik. Nincs teendő. |
| PplAlbumPhoto: Move to People Album almenü-horgony (`0xa0cd`) | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:277` | Egyezik. Nincs teendő. |
| PplAlbumPhoto: Set as People Album Thumbnail (`0x9e39`) | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:301` | Egyezik. Nincs teendő. |
| PplAlbumPhoto: Remove from People Album (`0x007355c0`) | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:250` | Egyezik. Nincs teendő. |
| People album bal hasáb helyi menü (`0x005c9b00`) | `src/picasapy/app/qml/PicasaPy/PeopleAlbumContextMenu.qml:28` | Egyezik. Nincs teendő. |
| Emberek panel (Right drawer) nyitás és feliratok (`0x00647df0`) | `src/picasapy/app/qml/PicasaPy/PeoplePanel.qml:1` | Egyezik. Nincs teendő. |
| Személy-album fejléc: confirmsug / confirmsel (`0x00602640`) | `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml:88` | Egyezik. Nincs teendő. |
| Személy-album fejléc: removesel (`0x005c9b00`) | `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml:93` | Egyezik. Nincs teendő. |
| Személy-album fejléc: moresug (`0x00602890`, küszöb -0.1) | `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml:95` | Egyezik. Nincs teendő. |
| Személy-album fejléc: face_zoom 35x21 px (`0x005e5290`) | `src/picasapy/app/qml/PicasaPy/LightboxHeaderButtons.qml` | Egyezik. Nincs teendő. |
| Személy-album fejléc: addname (`0x00602970`) és ignore (`0x005c9b00`) | `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml` | Egyezik: a `faceheaderpanel` geometriájában (15.5) nincs ilyen gomb; a két parancs a közös `0x005e0f70` elosztóé (#7296). Nincs teendő. |
| Név nélküliek fejléc: clustering / viewtype (`0x0074ad40`) | `src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml:20` | Egyezik. Nincs teendő. |
| Név nélküliek: addname és ignore csempén (`0x00602970`, `0x005c9b00`) | `src/picasapy/app/qml/PicasaPy/UnnamedFacesViewGrid.qml` | Egyezik. Nincs teendő. |
| Kézi arc-hozzáadás a szerkesztőben (`editpanel/addfaceselection`) | `src/picasapy/app/qml/PicasaPy/FacesOverlay.qml` | Egyezik. Nincs teendő. |
| Alkalmazás-szintű gyorsbillentyűk hiánya (`picasa-arcfelismeres.md` 14.1) | Nálunk sincs | Egyezik. Nincs teendő. |
| People Manager egyszeres kijelölése (job-325, 58. szakasz) | `src/picasapy/app/qml/PicasaPy/PeopleManagerDialog.qml:49` | Egyezik. Nincs teendő. |
| Ignore People megerősítő párbeszéd (`PeoplePanel::ConfirmRemove*`) | `src/picasapy/app/qml/PicasaPy/UnnamedFacesViewGrid.qml` | Egyezik. Nincs teendő. |
| Reset Faces figyelmeztető szövegek (`0x006038b0`, `0x00603a20`) | `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:80` | Egyezik. Nincs teendő. |
| `.picasa.ini` `faces=` rect64 alak, hex contact_id (job-66) | `src/picasapy/ini/faces.py:40` | Egyezik. Nincs teendő. |
| `.picasa.ini` `ffffffffffffffff` mellőzött szentinel (job-64) | `src/picasapy/ini/faces.py:80` | Egyezik. Nincs teendő. |
| Névtelen arc NEM íródik `.picasa.ini`-be (job-61) | `src/picasapy/ini/faces.py:90` | Egyezik. Nincs teendő. |
| Eltávolításkor `faces=` bejegyzés törlődik (job-68) | `src/picasapy/ini/faces.py:110` | Egyezik. Nincs teendő. |
| `[Contacts2]` szakasz kontakt tárolás (`0x007d55f0`) | `src/picasapy/ini/faces.py:120` | Egyezik. Nincs teendő. |
| Védett Unnamed album törölhetetlensége (`0x004ac650`) | `src/picasapy/app/people_album_controller.py:78` | Egyezik. Nincs teendő. |
| Csak olvasható fájl hibajelzése (`0x004852e0` / `0x00485382`) | `src/picasapy/app/photo_ops_xmp_mixin.py` | Egyezik. Nincs teendő. |
| `FRExclude` mappánkénti kizárás (`0x006e3990`) | `src/picasapy/scanner/` | Egyezik. Nincs teendő. |
| Arckeresés manuális indítóablaka (`FaceScanDialog.qml:33`) | `src/picasapy/app/qml/PicasaPy/PicasaToolsMenu.qml:23` | Szándékos saját UX többlet (#1473). Nincs teendő. |

---

## 6. Helyesbítés: nincs igazolt eltérés

A kör első változata a személyalbum fejlécéből hiányzó `addname` és `ignore` gombra fejlesztői jegyet javasolt (#7296). Ez téves volt: a `docs/specs/picasa-arcfelismeres.md` 15.5 szakasza a `faceheaderpanel` teljes, `respack.yt`-ből mért geometriáját sorolja, és abban ez a két elem nem szerepel. A `0x005e0f70` elosztó a `headerpanel`, a `faceheaderpanel` és az `unknownfaceheaderpanel` közös kezelője, a parancsnevek ismerete tehát nem panelhez kötött. A #7296 ezért nem tervezett jeggyel zárult.

**Következtetés:** a személyek kezelésének folyamata a vizsgált belépési pontokon, ablakokban és hatásokban egyezik az eredetivel; fejlesztői teendő ebből a körből nem következik.

## 7. Bizonyítottsági fok és lezárás

- **Bizonyítottsági fok: MEGERŐSÍTETT.**
- **A két független út:**
  - Út A: A Picasa3.exe diszasszemblálása, a PE erőforrások (`.tre`), a menü- és függvénystruktúra (`0x00647df0`, `0x00602640`, `0x005c9b00`, `0x00602890`, `0x004852e0`, `0x006e3990`, `0x0074ad40`, `0x004ac650`).
  - Út B: Élő futásidejű mérések (Colab-korpusz és felvételek: job-61, job-64, job-66, job-68 a `.picasa.ini` viselkedésére; job-113 a People panel felirataira; job-180 a többes kijelölésre; job-325 a People Manager egyszeres kijelölésére; a `picasa-arcfelismeres.md` és naplóinak már igazolt mérési leletei).
- **Cáfoló kísérlet:** Megvizsgáltuk azt a feltevést, hogy az eredeti Picasában létezett-e külön menü az arckeresés indítására, vagy létezett-e többes kijelölés a People Managerben. Mindkét feltevés megdőlt: a binárisban nincs kezdeti arckereső menüpont (`BgFaceDetectThread` örökké járt), és a job-325 mérés szerint a People Managerben a Ctrl és Shift kattintás nem bővíti a kijelölést (egyszeres kijelölés).
