# A Helyek panel (geocímkézés) — a MŰKÖDÉS

Ez a lap a Picasa 3.9 **Helyek** (Places) paneljének a *működését* írja le: mit
ír a lemezre, milyen alakban, mikor kérdez rá, és hogyan beszél egymással a
natív kód meg a beágyazott Google-térkép. A geometria **nincs** benne — a panel
tartalma egy beágyazott böngészőablak, tehát nincs `respack.yt`-rétege.

Bizonyíték-alap: `Picasa3.exe` (image base `0x00400000`), a telepítő saját
`runtime\geotag\` mappája (HTML + JavaScript, 2015-10-13), és a tulajdonos élő
`.picasa.ini`-korpusza (859 fájl).

---

## 1. A `geotag=` kulcs alakja — HAT tizedesjegy, mindig

| | érték | bizonyíték |
|---|---|---|
| ini-kulcs | `geotag` | bináris `0x00456610`, `0x00477ff0`, `0x007d55f0`, `0x007da570` |
| érték-alak | `<szélesség>,<hosszúság>` | ugyanott |
| formátumsztring | `%lf,%lf` | ugyanott (MSVC: a `%lf` a `printf`-ben azonos a `%f`-fel) |
| tizedesjegyek | **pontosan 6**, záró nullákkal együtt | a `%f` alapértelmezése + mérés |
| magasság | **nincs** — a kulcs kétmezős | a formátumsztringben két mező van |

**Mérés (a tulajdonos korpusza, 2026-09-02):** a 859 `.picasa.ini`-ben **84**
`geotag=` sor van, és mind a **84 sor 6/6 tizedesjegyet** használ — kivétel
nulla. Tehát a záró nulla nem esik le: a Picasa `47.820020`-t ír, nem
`47.82002`-t.

> **Bizonyítottsági fok: megerősített.** A formátumsztring a binárisból, a
> tizedesjegyek száma 84/84 élő mérésből.

A `geotag=` **beolvasása** ugyanezekben a függvényekben `sscanf`-fal megy
(`%lf,%lf`), tehát olvasáskor a Picasa elfogadja a rövidebb alakot is. Az
eltérés **írásoldali**, és a round-trip-hűséget rontja, nem az adatot.

### Nálunk ez ma eltér — mért termékhiba

A `src/picasapy/metadata/gps.py` `format_geotag()`-je a `%.6f` után
`rstrip("0").rstrip(".")`-et futtat. A korpuszra visszamérve **84-ből 19 érték
(22,6%)** más szöveggé íródna nálunk, mint amit a Picasa írt:

| Picasa | nálunk |
|---|---|
| `47.820020,18.848376` | `47.82002,18.848376` |
| `47.817477,18.851570` | `47.817477,18.85157` |
| `47.821250,18.849855` | `47.82125,18.849855` |

A függvény docstringje a levágást azzal indokolja, hogy a kerek koordináta ne
`33.770556000` alakban íródjon vissza — ez az indok **téves**: a `%.6f` soha nem
ad hatnál több tizedest, tehát a levágás kizárólag olyan jegyeket vesz el,
amiket a Picasa megtart. → **#2012**

---

## 2. Mit ír, mikor — a két írási művelet

| művelet | mit tesz az ini-vel | natív belépési pont |
|---|---|---|
| hely beállítása | `geotag=<lat>,<lon>` felvétele/felülírása | `geotag:` parancs → `0x006520d0` |
| hely törlése | a `geotag` kulcs **eltávolítása** | `cleargeotag:` parancs → `0x006520d0` |

A törlés csak a Picasa saját címkéjét bántja; a fájl EXIF GPS-mezőihez nem nyúl
— erre külön menüparancs való (`Eszközök ▸ Geocímke ▸ Geocímkék törlése`,
`0x00559150` / `ID_PICTURE_GEOTAG` környéke), amelynek saját, keményebb
figyelmeztetése van (`ClearGeoTag::warn`, `0x00600670`):

> „You are about to erase all geographic location information (i.e., latitude
> and longitude) from the selected photos."

Ez a párbeszéd **Igen/Nem** gombos (`il_Yes` / `il_No`), és **más művelet**, mint
a panel törlőgombja: az a `.picasa.ini`-t írja, ez a fájlokat.

---

## 3. A két megerősítő kérdés — MÉRT küszöbökkel

A panel nagy kijelölésnél rákérdez. **Két külön küszöb van**, és nem ugyanazt
számolják:

| művelet | szöveg-azonosító | küszöb | mit számol | bizonyíték |
|---|---|---|---|---|
| hely **megváltoztatása** | `GeoPanel::geotag_warning_change` | **> 20** elem | a **teljes kijelölést** | `0x00652585` `cmp ebx, 0x14` + `jbe` |
| hely **törlése** | `GeoPanel::geotag_warning_clear` | **> 5** elem | csak a **geocímkézett** elemeket | `0x006527ad` `cmp esi, 5` + `jbe`; a számláló `0x006524c0` |

A szövegek (`0xca21c0`, `0xca2248` környéke):

- változtatás: *„You have more than a few items selected.\n\nAre you sure you
  want to change the location of all %d items?"*
- törlés: *„You have more than a few items selected.\n\nAre you sure you want to
  clear the locations for all %d items?"*

A `%d` a fenti számláló értéke — **törlésnél tehát a geocímkézett elemek száma
jelenik meg, nem a kijelölésé**. A `0x006524c0` végigmegy a kijelölés tömbjén
(`[edi]`, elemszám `[edi+4] >> 1`), elemenként meghív egy virtuális predikátumot
(`[+0x74]`), és a találatokat számolja.

Küszöb alatt a párbeszéd **nem jelenik meg** — a művelet kérdés nélkül lefut.

> **Bizonyítottsági fok: megerősített** (mindkét küszöb kiolvasott
> összehasonlító konstans). **Nálunk ma egyik kérdés sincs meg** → **#2013**

---

## 4. A törlőgomb felirata dinamikus

A `geopanel/cleargeotag` gomb felirata nem állandó: a
`Clear %d Geotag(s)` sablonból áll elő (`0x00650390`, azonosító
`GeotagPanel::clearbutton`), tehát a kijelöléshez igazodó darabszámot mutat.
A menübeli megfelelője állandó szövegű: `Clear Geotags` (`0x00559150`).

---

## 5. A térkép: beágyazott böngésző + kétirányú JavaScript-híd

A panel egy **helyi HTML-lapot** tölt be:

```
runtime\geotag\geopanelscript_v3.html      (0x00650ba0, 0x00651d60)
```

`file://` előtaggal, `?hl=<nyelvkód>` kiegészítéssel (`0x00650ba0`) — a
nyelvkódot a lap a Google Maps API-nak adja tovább. Jobbról balra író nyelvnél
a natív oldal külön beinjektál egy sort (`0x00651d60`):

```js
document.getElementById('map_canvas').dir='rtl';
```

A térképmotor a **Google Maps JavaScript API v3**, a lap fejlécéből:
`http://maps.googleapis.com/maps/api/js?client=google-picasa-client&sensor=false&v=3`.
**Ez hálózatot igényel** — a lap tartalmaz egy tartalék üzenetet is
(`errorDiv`): *„Picasa failed to initialize Google Maps."*

### 5.1 Natív → JavaScript (a Picasa hívja a lapot)

Minden hívás egy kész JS-utasítás-sztring, amit a natív oldal a lapon lefuttat.
A formátumsztringek a binárisból:

| hívás | cím | mikor |
|---|---|---|
| `picasa.beginAddingMarkers();` | `0x00650390` | jelölő-lista újraépítésének kezdete |
| `picasa.addMarker(%f,%f,%d,%d);` | `0x00650390` | egy jelölő (szélesség, hosszúság, ellenőrzőösszeg, index) |
| `picasa.endAddingMarkers(%s);` | `0x00650390` | a lista vége; `%s` = `true`/`false` |
| `picasa.setNumSelected(%d);` | `0x00650390` | a kijelölés darabszáma |
| `picasa.updateMarker("%d","%s");` | `0x00652ab0` | egy jelölő bélyegkép-URL-je utólag |
| `picasa.newPlaceMarker("%s","%s");` | `0x0064f090` | új hely felvétele |
| `picasa.search('%s', '%s', '%s');` | `0x0064f090` | címkeresés indítása |
| `picasa.setMapType(%d);` | `0x00650a40` | a mentett térképtípus (ld. 5.4) |
| `picasa.beginDragAndDrop(%d,%d);` | `0x00652f50` | fogd-és-vidd kezdete (képpont) |
| `picasa.updateDragAndDrop(%d,%d);` | `0x00652f50` | mozgatás közben (képpont) |
| `picasa.endDragAndDrop(%s,%d,%d,"%s","%s");` | `0x00652f50`, `0x00653110` | elengedés |

A bélyegképeket a natív oldal `%s%d.bmp` néven, `file:///` URL-lel adja át
(`0x00653370`, `geothumb` / `geotagging` előtag).

### 5.2 JavaScript → natív (a lap szól a Picasának)

A visszaút **nem** külön API: a lap egy rejtett elemre kattint, a natív oldal
pedig a `WebBrowserPicasaPlugin` bővítményen át kapja meg az eseményt. A
JS-oldali kapu (`picasa_geopanel_bin_v3.js`):

```js
picasa.notifyPicasa = function(a){
  var b = window.WebBrowserPicasaPlugin;
  if (b) try { b.elementEventNotify(a, "click") } catch(d){ alert(...) }
  document.getElementById(a).click()
};
```

Az adatot a lap a `hiddenDiv` attribútumaiban adja át (a HTML-ből):

```html
<div id="hiddenDiv" style="display:none" checksum="-1" markindex="-1" latlng=""></div>
```

— a `checksum`, `markindex` és `latlng` attribútumneveket a natív oldal is
ismeri (`0x00652ab0`).

A natív parancsértelmező a `0x006520d0` függvény; a felismert előtagok:

| parancs | törzs | jelentés |
|---|---|---|
| `geotag:` | `%u,%f,%f` — ellenőrzőösszeg, szélesség, hosszúság | **állítsd be** ezeknek a képeknek a helyét |
| `cleargeotag:` | `%u` — ellenőrzőösszeg | töröld a hely(ek)et |
| `showphotos:` | `%u` — ellenőrzőösszeg | mutasd a jelölőhöz tartozó képeket |

Mindhárom parancs **ellenőrzőösszeggel** azonosítja a jelölőt — ugyanazzal,
amit a natív oldal az `addMarker(%f,%f,%d,%d)` harmadik mezőjében küldött ki, és
amit a lap a `hiddenDiv` `checksum` attribútumában ad vissza.

A sztringek: `0xca2188` (`geotag:`), `0xca219c` (`cleargeotag:`), `0xca21b0`
(`showphotos:`); a `sscanf`-minták `0xca2190` (`%u,%f,%f`, három mezőt vár —
`cmp eax, 3` a `0x006522aa`… ágban) és `0xca21ac` (`%u`, egy mezőt vár —
`cmp eax, 1`). A függvényre nincs közvetlen hívás: a címe a `0xca2470`
vtable-bejegyzésben áll, tehát virtuális parancskezelő.

Az `addmarker.png` gombja közvetlenül ezen a kapun megy (a HTML-ből):
`onclick="picasa.notifyPicasa('addMarker');"`.

### 5.3 A buborékablak feliratai

A buborék (info window) szövegeit a natív oldal **JS-változókba írja be**
(`0x00651580`), tehát a fordítás natív oldalról jön:

| JS-változó | forrás-azonosító | angol szöveg |
|---|---|---|
| `tcSearchTip` | `geo::search_tip` | Search for these photos in Picasa |
| `tcEraseButton` | `geo::erase_button` | Erase location info |
| `tcEraseTip` | `geo::erase_tip` | Erase map coordinates(i.e., GPS information) from these photos |
| `tcPhotoHere` | `geo::photo_here` | 1 photo here: |
| `tcPhotosHere` | `geo::photos_here` | %d photos here: |
| `tcCloseTip` | `geo::close_tip` | Close this window |
| `tcMovePhoto` | `geo::move_photo_here` | Move photo here? |
| `tcMovePhotos` | `geo::move_photos_here` | Move %d photos here? |
| `tcPutPhoto` | `geo::put_photo_here` | Put photo here? |
| `tcPutPhotos` | `geo::put_photos_here` | Put %d photos here? |
| `tcOk` | `il_OKButton` | (OK) |
| `tcCancel` | `il_Cancel` | Cancel |

**A „Move" és a „Put" külön szöveg**: az elsőt már geocímkézett képre kapja a
felhasználó (a hely *áthelyezése*), a másodikat még címkézetlenre. A
fogd-és-vidd közbeni feliratot a `0x00653110` `Place %d photos here` sablonja
adja (`GeoPanel::infowindowhtml`).

### 5.4 A térképtípus beállítása a v3 lapon NEM működik — negatív lelet

A natív oldal eltárolja a választott térképtípust (`0x00650a40`: `Preferences`,
`maptype` kulcs) és át is adja a lapnak `picasa.setMapType(%d)` hívással. A
v3-as szkriptben viszont:

```js
picasa.setMapType = function(){};
```

— **üres függvény**. A régi, v2-es szkript (`picasa_geopanel_bin.js`) még
tartalmazta a valódi megvalósítást
(`[G_NORMAL_MAP, G_SATELLITE_MAP, G_HYBRID_MAP, G_PHYSICAL_MAP]`).

Két független ellenőrzés, hogy ez nem elnézés:

1. a `maptypes` tömb a v3-ban **kizárólag** a térkép saját típusválasztó
   vezérlőjének feltöltésére szolgál (`mapTypeControlOptions.mapTypeIds`),
   nem a típus beállítására;
2. a fájlban a `maptypes` összesen **kétszer** fordul elő: a definíciójában és
   ebben az egy felhasználásban.

**Következmény:** a Picasa 3.9-ben a mentett térképtípus visszatöltése néma
módon hatástalan — a felhasználó a Google saját, jobb felső sarki vezérlőjéből
választ. A típusok sorrendje (a `%d` jelentése) mindkét szkriptben azonos:
`0`=úthálózat, `1`=műhold, `2`=vegyes, `3`=domborzat.

**Ezt a hibát nem kell átvennünk.** A tanulság: a térképtípus-választás a
térképvezérlő dolga, a mentett érték visszaállítása pedig valódi funkció, amit
az eredeti elrontott.

---

## 6. Amit KIZÁRTAM

- **A `geotag=` nem tartalmaz magasságot.** A formátumsztring két mezős, és a
  korpusz 84 sorából egy sem háromtagú.
- **A panelnek nincs `respack.yt`-geometriája**: a tartalom beágyazott
  böngésző, a feliratok a HTML/CSS-ből és a natív oldalról injektált
  JS-változókból jönnek.
- **A törlés nem nyúl a fájlhoz.** A panel törlőgombja az ini-kulcsot veszi ki;
  az EXIF GPS törlése külön menüparancs, külön figyelmeztetéssel
  (`0x00600670`).

## 7. A `showphotos:` — mit vált ki, és mi van nálunk

A GeoPanel függvénycsoportjában a `0x00652950` bekapcsolja a keresősor
`searchcontainer/geotagsearch` kapcsolóját (`buttontoggle`), majd megnöveli a
`0xd35de8` alatti 64 bites keresés-számlálót, ami a bélyegrács újraszűrését
kényszeríti ki. A rács ebben az állapotban a `CThumbUI::sgeotag` / `geotagged`
feliratot mutatja (`0x00662b20`).

**Ez a mód nálunk MEGVAN**: `app/geo_controller.py:64` `showGeotagged()` — a
`geotagged_photos()` lekérdezésre vált, és a szűrősor állapotát is átállítja.
A jelölő buborékjából induló belépési pont hiánya nem külön hiány: nálunk ma
nincs buborékablak sem (ld. #2013 hatókörén kívüli része).

> **Bizonyítottsági fok: erős** — hogy a `0x00652950` pont a `showphotos:`
> kezelője, azt a címbeli szomszédság és a `geo::search_tip` felirat („Search
> for these photos in Picasa") támasztja alá, közvetlen hívási él nem (a
> parancskezelő virtuális, `0xca2470`). A megkülönböztetés a fejlesztésre nézve
> tét nélküli: a mód mindkét olvasat szerint ugyanaz, és nálunk kész.
