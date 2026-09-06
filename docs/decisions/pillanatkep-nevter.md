# ADR-010: A mentésenkénti pillanatképek KÜLÖN névtérbe kerülnek

Dátum: 2026-09-06 · Státusz: ELFOGADVA · jegy: #2512 (előzmények: #444, #1425, #1449)

> **Egymondatos összefoglaló:** a „szent" eredeti útja marad
> `.picasaoriginals/<fájlnév>` — azt a windowsos Picasa is oda írja —, a MI
> mentésenkénti pillanatképeink viszont a `.picasaoriginals/`
> `.picasapy-snapshots/` alkönyvtárba mennek, mert a `<tő>.<N><kiterjesztés>`
> név a közös mappában egy önálló kép eredetijétől megkülönböztethetetlen
> volt, és a „Vissza az eredetihez" ettől IDEGEN fénykép bájtjait adta.

## A helyzet

A #444 óta minden mentés két dolgot ír a kép melletti rejtett mappába:

1. a **„szent" eredetit** (`.picasaoriginals/<fájlnév>`) — csak az ELSŐ
   mentéskor, és soha nem írjuk felül; ehhez tér vissza a „Vissza az
   eredetihez" (`edit/save.revert`);
2. egy **mentésenkénti, sorszámozott pillanatképet**
   (`.picasaoriginals/<tő>.<N><kiterjesztés>`) — ez teszi visszavonhatóvá az
   utolsó mentést a szerkesztések elvesztése nélkül (`undo_save`). A
   névminta az eredeti binárisából származik (`%s.%d.jpg`).

**A két név ütközik.** Az `a.jpg` második mentésének pillanatképe
`.picasaoriginals/a.2.jpg` — ami bitre ugyanúgy néz ki, mint egy ÖNÁLLÓ
`a.2.jpg` kép „szent" eredetije. A `find_original_backup` a kettőt nem
tudja megkülönböztetni: a képmappában lévő `a.2.jpg` néven kérdez rá az
eredeti-mappára, és amit ott talál, azt az ő eredetijének hiszi.

**A kár mérve** (`tests/edit/test_pillanatkep_nevutkozes_2512.py`, a mai
main-en lefuttatva): `a.png` kétszeri mentése után az önálló `a.2.png`
szerkesztésekor

* a mentés `backup_created_now=False`-t adott — vagyis az önálló kép valódi
  eredetije **soha nem lett megőrizve**;
* a `revert(a.2.png)` az `a.png` egy régi állapotának bájtjait írta a helyére.

Mindkettő **visszafordíthatatlan**: a felhasználó képe helyett egy másik
fénykép tartalma áll a fájlban, és nincs hova visszatérni.

### Amit a #1449 megoldott — és amit nem

A #1449 a mentéskor **átlépi a foglalt sorszámokat**, hogy a `write_atomic`
ne írjon felül egy már ott álló, idegen eredetit. Ez a MÁR MEGLÉVŐ fájlt
védi. A jelen hiba a **fordított irány**: előbb mentjük az `a.jpg`-t, és az
önálló `a.2.jpg` csak KÉSŐBB kerül szerkesztésre — akkor a pillanatkép már
ott áll, és semmi nem akadályozza meg, hogy az ő eredetijének nézzük.

Ugyanez a kétértelműség hajtja a #1449 óvatossági szabályát is (ha a
képmappában azonos nevű önálló kép áll, a példányt békén hagyjuk), aminek
kimondott ára van: az `undo_save` néha egy LÉTEZŐ pillanatképhez veszíti el
a visszavonást.

## A KOMPATIBILITÁSI korlát — ez szűkíti a megoldásteret

A `.picasaoriginals/<fájlnév>` **nem a mi formátumunk**: ide írja a
szerkesztés előtti eredetit a windowsos Picasa is, és a tulajdonos
gyűjteményében 181 valós mappa van tele ilyennel (54 `.picasaoriginals`,
127 a 2009 előtti, látható `Originals` néven — #1425). A #371 kutatása
kizárta, hogy a szerkesztés bárhol máshol tárolódna: a retus a JPEG-be van
égetve, tehát ez a fájl a visszaút EGYETLEN útja.

Ebből két kötelezettség következik:

1. **Amit a Picasa ír, azt OLVASNUNK kell** — a „szent" eredetit és a
   Picasa saját, sorszámozott pillanatképeit egyaránt. Bármilyen megoldás,
   ami a régi elrendezést elhagyja, a felhasználó meglévő adatát teszi
   elérhetetlenné.
2. **Amit a Picasa olvas, azt nem rendezhetjük át** — a „szent" eredetit nem
   vihetjük saját helyre, mert a párhuzamosan futó Picasa ott keresi.

## A két megfontolt irány

### A) Más névséma a MI pillanatképeinknek

A kétértelműséget ott szüntetjük meg, ahol keletkezik: a pillanatkép ne
azon a néven álljon, amit a `find_original_backup` kérdez.

* **Külön alkönyvtár** — `.picasaoriginals/.picasapy-snapshots/<tő>.<N><kit>`.
  A név, a sorszámozás és a fájltartalom változatlan, csak a szint más.
* Elvetett alváltozat: **más kiterjesztés** ugyanabban a mappában (pl.
  `<tő>.<N>.picasapy`). Megszüntetné ugyan az ütközést, de a fájl így már
  nem nyitható meg képnézegetővel — pont a legrosszabb pillanatban, amikor
  a felhasználó kézzel akarja megmenteni a képét.

### B) Nyilvántartás: mi kié

Egy külön állomány (ini vagy JSON) sorolná fel, melyik fájl kinek a
pillanatképe, és a keresés azt kérdezné meg.

**Elvetve**, három okból:

1. **A kétértelműséget nem szünteti meg, csak takarja.** A lemezen továbbra
   is ott áll a `.picasaoriginals/a.2.jpg`, és aki NEM a nyilvántartáson át
   néz — a párhuzamosan futó Picasa, a felhasználó a fájlkezelőjében, a
   jövőbeli saját kódunk — ugyanúgy félreérti.
2. **Elcsúszhat a valóságtól.** A nyilvántartást minden mozgatásnál,
   másolásnál, törlésnél és külső beavatkozásnál karban kellene tartani; ha
   elveszik vagy megsérül, a pillanatképek árvává válnak, és a projektnek
   már van kimondott tanulsága arról, hogy a fájlállapotból utólag
   következtetni HIBÁS (#1448).
3. **A Picasa írta példányokon nem segít**: azokról nekünk sosem lesz
   bejegyzésünk, tehát a régi hely óvatossági szabályát akkor is meg kell
   tartani.

## A döntés

**Az A) irány, külön alkönyvtárral.**

| mi | hova | ki írja | ki olvassa |
|---|---|---|---|
| „szent" eredeti | `.picasaoriginals/<fájlnév>` (és a régi `Originals/`) | Picasa ÉS mi | Picasa ÉS mi |
| mentésenkénti pillanatkép — ÚJ | `.picasaoriginals/.picasapy-snapshots/<tő>.<N><kit>` | csak mi | csak mi |
| mentésenkénti pillanatkép — RÉGI helyen | `.picasaoriginals/<tő>.<N><kit>` | **már senki** | mi (és a Picasa a sajátjait) |

Négy következmény, amit ez a lap kimondottan eldönt:

1. **Az olvasás MINDKÉT helyre kiterjed.** A `snapshot_numbers` az
   alkönyvtárat és a közös helyet is végignézi, tehát a lemezen már ott álló
   példányok — a mi korábbi verzióinké és a Picasáé — továbbra is
   visszavonhatók, mozognak a képpel, és a törléssel is mennek.
2. **A #1449 óvatossági szabálya csak a RÉGI helyen érvényes.** Az ÚJ
   alkönyvtárba rajtunk kívül senki nem ír, tehát ott a névminta nem
   kétértelmű. Ha ott is szűrnénk gazdára, egy véletlenül azonos nevű önálló
   kép puszta létezése elnémítaná a saját visszavonásunkat, és a kép
   mozgatásakor hátrahagyná a saját pillanatképeinket.
3. **Költözéskor a pillanatkép a SAJÁT szintjén marad.** Ami az
   alkönyvtárból indul, oda érkezik; ami a közös helyről, az oda. Ugyanaz a
   gondolat, mint a mappanévnél (#1425, `fileops/originals.py` „A mappanév a
   költözéskor NEM változik"): a régi helyen álló példány a párhuzamosan futó
   Picasáé is lehet, azt nem rántjuk be a mi névterünkbe.
4. **A sorszám-átlépés MEGMARAD, de más okból.** A felülírás az új hellyel
   kizárt; a régi helyet azért nézzük mégis, hogy ugyanaz a sorszám ne
   létezzen kétszer, két különböző helyen — az `undo_save` a legnagyobb
   sorszámot veszi, és egyenlőségnél nem tudná eldönteni, melyik a frissebb.

## Amit ez a döntés NEM old meg

Kimondva, hogy ne látsszon nagyobbnak, mint amekkora:

* **A régi helyen MÁR ÁLLÓ pillanatképek ütközése megmarad.** Aki a mai
  előtti PicasaPy-vel mentett, annál a `.picasaoriginals/a.2.jpg` továbbra is
  ott van, és ha ő később egy önálló `a.2.jpg`-t szerkeszt, ugyanaz a kár
  éri. Visszamenőleges átköltöztetést szándékosan NEM végzünk: nem tudjuk
  megkülönböztetni a saját régi pillanatképünket a Picasa írta példánytól
  (a lemezen bitre azonosak), és egy Picasa-példány elmozgatása annak a
  programnak rontaná el a működését. Aki egyszer újramenti a képet, annak az
  új pillanatképei már a helyes helyre kerülnek.
* **A Picasa ÍRTA pillanatképek maradnak a közös helyen**, tehát rájuk a
  kétértelműség és a #1449 óvatossági szabálya (a hozzá tartozó, kimondott
  árral együtt) továbbra is érvényes. Ez nem javítható a mi oldalunkról: az
  a mappa a Picasáé is.
* **A `.picasaoriginals/.picasa.ini` szekciói.** Az új helyen álló
  pillanatképeknek nincs ini-szekciójuk (nem is írunk nekik), a régi helyen
  állókét a `fileops/original_ini.py` mozgatja változatlanul.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/edit/save.py`, `src/picasapy/fileops/originals.py`
- **Őrzi:** `tests/edit/test_pillanatkep_nevutkozes_2512.py`, `tests/fileops/test_pillanatkep_uj_helyen_koltozik_2512.py`
