# UX-alapelvek — „a Picasa lelke"

A források (felhasználói visszajelzések + replikációs kézikönyv) szerint ezek
tették a Picasát pótolhatatlanná. Minden UI-döntést ezekhez mérünk.

## 1. Megszakítás nélküli sorozat-munkafolyamat

A Picasa leghiányoltabb képessége: crop → **Enter** → a következő kép azonnal
betöltődik, a vágóeszköz aktív marad. Nincs visszalépés a galériába. 200 kép
kézi vágása így percek alatt megvan.

- Billentyűzet-központú vezérlés, minimális menürendszer.
- Ugyanez az elv minden sorozat-műveletre (csillagozás, forgatás, arc-címkézés).

## 2. Egygombos automatika

„I'm Feeling Lucky" — egyetlen kattintás, automatikus tónus/kontraszt/szín-
javítás, ami a képek ~99%-án azonnali javulást ad. A csúszkák (finetune) csak
opcionális finomhangolás, nem kötelező lépés.

## 3. Észrevétlen eredeti-megőrzés

Nincs „kép_v2_final.jpg" verziókáosz és nincs kötelező export-lépés:

- A szerkesztések alapból csak paraméterként léteznek (ini), az eredeti fájl
  érintetlen; megtekintéskor röptében renderelünk.
- „Mentéskor" a renderelt kép az eredeti *helyére* kerül a fájlrendszerben,
  az érintetlen eredeti a rejtett `.picasaoriginals/` mappába — a felhasználónak
  nem kell verziókkal foglalkoznia, mégis bármikor visszaállíthat.
- Más szerkesztők (Lightroom stb.) máig nem ezt csinálják — ez megkülönböztető.

## 4. Mindig reszponzív UI

- A könyvtárkezelés villámgyors marad 100k+ képnél is (ez volt a Picasa fő
  erénye a központi index miatt).
- GPU-alapú renderelő csatorna a szerkesztőben (shader-lánc, ping-pong
  textúrák); CPU-s pixelciklus nagy képeknél tilos a UI-útvonalon.
- Aszinkron kép-előbetöltés (a következő kép már a GPU-n, mire Enter-t nyomsz).
- A scanner soha nem blokkolja a felületet.

## 5. Bizalom és adatbiztonság

- A felhasználó évtizedes kurálási munkája (csillagok, arcnevek, feliratok)
  szent: minden írás atomikus, backup-olt, round-trip-biztos.
- Ami a formátumból nem értelmezhető, azt megőrizzük, nem dobjuk el.
- Export mindig nyitva: XMP MWG-RS sidecar bármikor generálható, hogy az adat
  soha többé ne ragadjon halott formátumba.
