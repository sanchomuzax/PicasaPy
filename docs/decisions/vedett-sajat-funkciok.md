# Módszertan: SAJÁT FUNKCIÓ jelölés — a nem eredeti Picasa-funkciók jegyzéke

Állapot: élő lista (folyamatosan bővül) · Dátum: 2026-08-24 · jegy: #1187

## A szabály

A projekt módszertana a Windows-os Picasa binárisát tekinti mércének: ha a
kódunk eltér tőle, az az alapeset szerint **hiba** (ld.
`docs/specs/binaris-regeszet-modszertan.md` 17. szakasza). Ennek a
szabálynak van egy kimondott kivétele: a **szándékosan hozzáadott, nem
eredeti funkciók**. Ezeknél az eltérés nem hiba, hanem a terv — **a
bináris-egyezés ide nem vonatkozik.**

Ez a fájl az ilyen esetek **kereshető jegyzéke**. Új saját funkció
bevezetésekor:

1. tedd ki a kód (vagy a spec) érintett pontjára a `SAJÁT FUNKCIÓ`
   jelölőt (ld. lent),
2. vedd fel ide egy sort,
3. ha a tulajdonos külön döntésként hozta létre (nem apró UX-részlet), írj
   hozzá `docs/decisions/`-ADR-t is, és hivatkozz rá innen.

## A jelölő — három helyen, egyetlen szó fedi mindet

A greppelhető kulcsszó: **`SAJÁT FUNKCIÓ`** (nagybetűvel, pontosan így —
ez teszi lehetővé, hogy egyetlen kereséssel mindhárom helyet megtaláljuk:
`grep -rn "SAJÁT FUNKCIÓ" src/ docs/`).

- **Kódban** (Python-/QML-megjegyzés vagy docstring), a divergencia
  pontjánál, egy sorban a jegyszámmal:

  ```
  // SAJÁT FUNKCIÓ (#1187): <mi tér el, és miért — egy mondatban>
  ```

  ```python
  # SAJÁT FUNKCIÓ (#445): <...>
  ```

- **Specifikációban** (`docs/specs/*.md`), a bekezdés elején félkövérrel:

  ```
  **SAJÁT FUNKCIÓ (#445):** <...>
  ```

- **Jegyen**: a `sajat-feature` GitHub-címke. Jelentése: *ez a jegy
  szándékosan nem eredeti Picasa-viselkedést érint — a bináris-egyezés
  ellenőrzése ide nem vonatkozik.*

## Munkafolyamat-szabály (kutatás/kódolás/hibakeresés)

**Jegynyitás előtt, ha az érintett terület gyanúsan „hiányzik" a
binárisból, vagy „többet" csinál nála**: fusd le a fenti grepet az érintett
fájlokra és a `docs/specs/`-re, és nézd át ezt a listát. Ha a terület itt
szerepel, az eltérés **nem kutatási találat és nem hiba** — a jegyet ez
alapján zárd, ne a bináris-eltérésre hivatkozva nyisd.

Ellenőrzés: `python scripts/check_protected_features.py` — ellenőrzi, hogy
(a) minden alábbi tétel fájlja valóban tartalmazza a jelölőt, és (b) minden
`SAJÁT FUNKCIÓ` jelölésnek van itt tétele (a lista nem maradhat le a
kódtól).

## Ismert esetek

- `src/picasapy/app/qml/PicasaPy/EditorPanel.qml` (#422, #571) — A
  szerkesztő 7 effekt-füle az eredeti 5 helyett: a 2–4. index az eredeti
  három effekt-fül, az 5. („további effektek", #422) és a 6. („Régi
  effektek", #571) index a mi hozzáadásunk.
- `src/picasapy/app/qml/PicasaPy/EditorLegacyTab.qml` (#571) — a 7. fül
  maga: a motor ismer egy sor szűrőt (`radtint`, `linblur`, `dir_sat`
  stb.), amit a Picasa 3.9 felülete sosem mutatott. Mi tudatosan
  előhívhatóvá tettük. Részletes indoklás: ADR-003,
  `docs/decisions/legacy-effects-tab.md`.
- `src/picasapy/ini/photo_touch.py` (#643, #1320) — az ini-írás után a
  változott fotók `mtime`-jának megérintése. Az eredeti Picasa a
  `.picasa.ini` SAJÁT írási idejét figyeli (`albumdata_inisync`, 99,5%-os
  mért egyezés), a képfájl dátuma nála nem játszik szerepet; ez az út tehát
  a mi kiegészítésünk. Alapértelmezésben KI, kizárólag
  `PICASAPY_TOUCH_PHOTO_MTIME=0` kapcsolja KI — 2026-09-06 óta
  alapértelmezésben FUT (#2491, ADR-007). Indoklás: ADR-006,
  `docs/decisions/photo-mtime-erintes.md`.
- `src/picasapy/ini/redeye.py` (#445) — a vörösszem-jelölések saját
  `rect64(...)` paraméterezése a `redeye=` bejegyzésben. A bináris nem
  árulja el a valódi bájtformátumot (#371 nyitott kérdés); amíg az elő nem
  kerül, ez a mi kódolásunk — paraméter nélkül bájtra egyezik az eredetivel.
- `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml` (#1595) — a **Mappa ▸
  Rendezés ▸ „Legutóbbi változtatások"** tétel. Az eredeti Mappa menü
  rendezés-készlete (`ID_DATESORT` / `ID_NAMESORT` / `ID_SIZESORT` /
  `ID_REVERSESORT`) NÉGY tagú, és nincs benne „legutóbbi változtatások" —
  az az `ID_VIEWBY*` ötösben él, ami a NÉZET menüé. Nálunk viszont működő,
  hasznos rendezés (#1759), ezért a #1595 nem törölte a hűség kedvéért,
  hanem `sajat: true` jelöléssel hagyta bent: kék felirat + kötelező
  buboréksúgó. Ld. `docs/decisions/sajat-funkciok-jelolese.md`.
- `src/picasapy/app/qml/PicasaPy/TrayBar.qml` (#70) — az alsó kék
  állapotsáv (`infoBar`) `busySweep` fény-hullám animációja háttérmunka
  (indexelés, bélyegkép-gyártás) közben. Az eredetiben nincs ilyen vizuális
  visszajelzés — saját UX-kiegészítés, felhasználói panasz nyomán (ld. #70
  motivációja: hálózati mappánál a program „beragadtnak" tűnt).
- `src/picasapy/app/qml/PicasaPy/CropOverlay.qml` (#1187) — a vágó
  „Előnézet" gombjának NYOMVA TARTÁSA a vágási eredményt mutatja (ilyenkor
  a kijelölésen kívüli terület nem sötétedik, hanem a néző hátterével
  teljesen fedetté válik). Az eredetiben nincs ilyen állapot, csak az
  állandó kijelölés-sötétítés (#900).
- `src/picasapy/app/qml/PicasaPy/PicasaNotifier.qml` (#1129) — a lebegő
  értesítősáv celláinak **magától eltűnése** (`cellLifetimeMs`). Maga a sáv
  eredeti (`CNotifierPopup`), és a mérete, elhelyezése, ablakstílusa a
  binárisból mért érték; az egyes cellák ÉLETTARTAMA viszont nincs kimérve.
  A bináris importtáblája bizonyítja, hogy Win32 időzítő nem méri
  (`SetTimer`/`KillTimer`/`timeSetEvent` egyik hívója sincs a notifier
  moduljában), a `yt` keretrendszer saját ütemezője pedig nincs felderítve.
  A magától eltűnés a #1168 kimondott igénye — az érték a mi döntésünk.
- `src/picasapy/collage/uids.py` (#1092) — a `.cxf` `albumUID`-jának és
  csomópontonkénti `<uid>`-jának **IDEIGLENES származtatása**. Az ALAK
  eredeti és mért (32, illetve 16+16 nulla hexa karakter, determinisztikus:
  egy forrásalbum → egy `albumUID`, egy kép → egy `<uid>`); a KÉPZÉSI
  SZABÁLY a miénk, de **nem eldöntött saját funkció, hanem tartalék**:
  - a csomópont-`<uid>`-nál az eredeti érték a Picasa belső adatbázisából
    jön (`imagedata` `uid64`), és mérésekkel kizártuk, hogy az útvonalból
    levezethető lenne — itt a származtatás tartós;
  - az `albumUID`-nál **nyitott kérdés**: a saját specünk
    (`picasa-create-features.md` 1.6) szerint ez a `[.album:<token>]`
    token, és ezt a mai anyagból NEM lehet eldönteni (a golden kollázsok
    forrásmappájának `.picasa.ini`-je nincs meg). Ha a hipotézis
    beigazolódik, a származtatás helyére az olvasott token lép, és csak
    a token nélküli mappákra marad meg. Amíg nincs kimérve, ez a tétel
    **ideiglenes**.
- `src/picasapy/collage/draft.py` (#1092) — a fenti származtatás
  BEHELYEZÉSE a projektfájlba (`_azonositoval`): a megnyitott fájlból
  hozott azonosítót nem írjuk felül, csak az üresen maradt csomópontokat
  töltjük ki.
- `src/picasapy/edit/save.py` (#1425) — a **két eredeti-mappa ütközésének
  feloldása**. Maguk a mappanevek eredetiek és mértek (`Originals`
  2005–2009, `.picasaoriginals` 2009–2016; 181 valós mappa, ld.
  `docs/specs/picasa-ini-format.md`), a mindkettőt olvasó visszaállítás
  tehát NEM saját funkció. Az viszont a MI döntésünk, hogy melyikből
  dolgozunk, ha ugyanahhoz a képhez mindkét mappában van példány: nálunk a
  régi, `Originals` az elsőbbségi — az az időben korábbi példány, tehát az
  áll közelebb az érintetlen eredetihez, és a téves választás kára is arra
  fordul kisebbre (a másik irány NÉMÁN adna részlegesen visszaállított
  képet). Az eredeti Picasa erre az esetre nincs kimérve: a korpusz csak
  `.picasa.ini`-szöveget tartalmaz, és `Originals/` alatt egyetlen ini
  sincs, mert az a név rajta van a Picasa saját kizárási listáján. Ha
  később mérés születik rá, ez a tétel eltűnik.

## Tervezett, még nem implementált saját funkciók

Ezeket a tulajdonos nevezte meg (#1187) mint jövőbeli saját kiegészítést,
de a mai kódban **nincs hozzájuk konkrét hely** — ha valamelyik
megvalósul, a fenti jelölőt és egy sort ide is fel kell venni akkor, ne
utólag pótolandó adósságként:

- Google Fotók feltöltés/letöltés és albumkezelés egy saját (nem Google-)
  webes felületen — a mai `webexport/` csomag az eredeti `.tpl`-motort
  reprodukálja, ez NEM ugyanaz a funkció.
- további, a fentieken túli, teljesen saját ötletű effektek (nem a
  binárisban talált, csak a felületén hiányzó `Glimmer`-szűrők
  előhívása — az az `EditorLegacyTab.qml` fenti tétele).

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `scripts/check_protected_features.py`
- **Őrzi:** `tests/tools/test_check_protected_features_1187.py`
