# ADR-006: A képfájl `mtime`-jának megérintése — alapértelmezésben KI

Dátum: 2026-08-24 · Státusz: ELFOGADVA · jegy: #1320 (a #643 örökségéből)

## A helyzet

A #643 hibajelentés az volt, hogy a PicasaPy-ban végzett szerkesztés a
párhuzamosan futó, eredeti (windowsos) Picasában nem jelenik meg. Az akkori
visszafejtés arra jutott, hogy a Picasa a fotó rekordjának érvényességét a
**képfájlhoz** méri, és ebből egyetlen megkerülési utat vezetett le: ha az
ini írása mellett a **képfájl** módosítási idejét is megérintjük, a fotó
bekerülhet az újrafeldolgozandók közé.

A PicasaPy ezt megvalósította (`src/picasapy/ini/photo_touch.py`), és
**alapértelmezésben bekapcsolta**: azóta minden `.picasa.ini`-írás után
átírta a változott fotók `mtime`-ját — egy éles, családi fotógyűjteményen.

2026-08-24-én két kutatási kör ezt a képet átrajzolta.

## Amit a két kör kimért

**1. Az újraolvasás kulcsa a `.picasa.ini` SAJÁT írási ideje.** A Picasa
mappánként eltárolja a `.picasa.ini` utolsó írási idejét
(`db3/albumdata_inisync.pmp`, FILETIME), és a következő beolvasáskor ehhez
méri a lemezen lévő fájlt. A felhasználó valódi adatbázisán 787 összevethető
mappából **783 egyezett bitre** (99,5%); a négy eltérésből három olyan
mappa, ahol épp az ini az újabb, azaz újraolvasásra vár. A beolvasás
`flags = 3` értékkel fut, ami a **szerkesztéseket is** magában foglalja
(`filters`, `crop`, `rotate`, …).
*(`docs/specs/picasa-ini-format.md` → „MEGFEJTVE: az újraolvasás kulcsa az
INI FÁJL saját dátuma"; `docs/specs/pmp-database.md` →
„Az `albumdata_inisync` oszlop".)*

**2. A képfájl `mtime`-ja nem szerepel a frissesség-vizsgálatban.** Mind a
három `CompareFileTime`-hívási hely rendezés-komparátor; a könyvtárbejáró
rekordja nem tárol módosítási időt; a `GetFileAttributesExW` egyetlen
hívója csak méretküszöböt vizsgál.
*(Ugyanott, „Az mtime-megkerülés mérlege".)*

**Amit viszont NEM cáfoltunk:** az eredeti IGENIS figyel operációs rendszer
szintű változás-értesítést (`FindFirstChangeNotification` a `0x007062b9`-nél,
szűrő `0x17`, benne a `LAST_WRITE` bittel, rekurzívan —
`docs/specs/picasa-mappakezelo.md` 16.5, megerősített). Az értesítés léte
azonban nem mond semmit arról, hogy a **fotó** `mtime`-ja számít-e: a
frissességet az ini dátuma dönti el.

## A döntés

**Az érintés alapértelmezése KI. A modul megmarad, kifejezetten
bekapcsolhatóan: `PICASAPY_TOUCH_PHOTO_MTIME=1`.**

| | |
|---|---|
| alapértelmezés | **KI** — a képfájlokhoz hozzá sem nyúlunk (`stat`-tal sem) |
| bekapcsolás | `PICASAPY_TOUCH_PHOTO_MTIME=1` (`true`/`yes`/`on`/`igen`/`be` is jó) |
| bármi más érték | KI — elgépelésre a biztonságos irányba dőlünk |
| ha fut | `INFO` naplósor arról, hány képfájl időbélyegét írtuk át, melyik mappában |

### Miért ez

1. **A haszon nem mért, a kár igen.** Az időbélyeg átírása
   visszafordíthatatlan: elrontja a fájlkezelős dátumrendezést, és az
   `rsync`-féle, méret+`mtime` alapú mentéseket fölösleges újramásolásra
   kényszeríti egy sok tízezer fotós archívumon. A Picasa-oldali haszonról
   viszont ma **nem tudjuk, hogy létezik-e**.
2. **A mechanizmus ismeretében szükségtelen.** Amit a Picasa néz, azt az
   ini kiírása magától megadja. Nincs mit „segíteni" rajta.
3. **Mégsem töröljük.** A „segít-e mégis?" kérdést egyedül a felhasználó
   párhuzamos windowsos próbája döntheti el, ahhoz pedig kell egy kapcsoló,
   amivel a kísérlet elvégezhető. Ha a próba pozitív, az alapértelmezés egy
   sorral visszafordítható; ha negatív, a modul törölhető.

## A következmények

- Aki eddig az alapértelmezésre támaszkodott, most üres kézzel marad — de
  ez pontosan a lényeg: eddig sem tudtuk, hogy kap-e érte bármit.
- A #643 eredeti panasza (a `filters=` nem jelenik meg) ezzel **nem** dől
  el. A kiváltás rendben van, tehát az ok máshol van; a legvalószínűbb
  jelölt a `filters=` lánc SZIGORÚ beolvasása — ezt a szálat a **#685**
  viszi tovább.
- Nyitva marad: a windowsos próba (blokkolt, a felhasználó gépén futó
  eredeti Picasát igényel).
