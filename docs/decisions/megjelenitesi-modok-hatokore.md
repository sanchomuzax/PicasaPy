# ADR-008: A `Nézet ▸ Megjelenítési mód` tizenegy tétele — mit valósítunk meg, és mit nem

**Állapot:** eldöntve · **Dátum:** 2026-09-01 · **Jegy:** #1579
(feltárás: #1409, mérések: #1580, megvalósítás: #1575, #1656, #1658, #1730)

## A helyzet

A `Nézet ▸ Megjelenítési mód` almenü az eredetiben **egyetlen, tizenegy
tagú kizáró rádiócsoport** (`docs/specs/picasa-megjelenitesi-modok.md` 2.).
A tizenegyből több a mai Linux-környezetben **értelmét vesztette** vagy
**nem reprodukálható**. Ha ezt nem írjuk le döntésként, minden későbbi kör
újra elkezdi kideríteni — és a lefedettségi táblákban örökre
„hiányzik"-ként fog látszani.

## A döntés — tételenként

A **hatókörön kívül** és a **helyfoglaló** között az a különbség, hogy az
elsőt SOSEM kötjük be (a szolgáltatás, amire épült, nem létezik), a
másodikat pedig akkor, ha értelmet nyer. Ez a különbség a felületen is
látszik (`PicasaMenuItem.qml`: `retired` vs `placeholder`).

| tétel | döntés | miért | hol |
|---|---|---|---|
| `Automatikus` | ✅ **megvalósítva, no-opként** | az eredetiben is csak 16 bites képernyőn csinál bármit; ez az eredeti alapértelmezés, ezért a rádiócsoportnak kell egy ilyen tagja | 5.2 |
| `24 bites` | ✅ **megvalósítva, no-opként** | az eredetiben sincs átalakítója (`NULL` mutató) | 5.1 |
| `16 bites (szemcsézett)` | 🟡 **helyfoglaló** | a szabály **mérve van** (MT-zaj +0…7/0…3/0…7, telítő), tehát megvalósítható — de **16 bites képernyő ma nincs**, a mód semmit nem jelentene. Ha egyszer értelmet nyer, bekötjük | 5.3 |
| `Távoli asztal` | ⛔ **hatókörön kívül** | RDP-munkamenet sávszélesség-takarékossága: 3-3-3 bites levágás. A mi nézőnk nem tud a távoli munkamenetről, és a mód **nem javítana** semmin — nincs értelmezhető megfelelője. Nyugdíjazott, nem helyfoglaló | 5.11 |
| `LCD fehérpont` | ✅ **megvalósítva** | ×246/256 mindhárom csatornán — egyszerű, pixelhű | 5.4 |
| `Projektor mód` | ✅ **megvalósítva** | ×220/256 mindhárom csatornán | 5.5 |
| `Túlcsordult képpontok` | ✅ **megvalósítva** | a tiszta fehér → `#FF7F7F`; a felhasználónak **valódi haszna** van (levágás-jelzés) | 5.6 |
| `Mac gamma (1.6)` | ✅ **megvalósítva** | ld. lentebb — a #1579 jegy „kihagyás, amíg nincs referencia-mérés" javaslata **elavult** | 5.10 |
| `Lineáris gamma (2.2)` | ✅ **megvalósítva** | a bináris 256 bájtos LUT-ja **bemásolva**; a „miért 1,44" nyitott, de a megvalósításhoz nem kell: **a mért tábla a szerződés** | 5.9 |
| `Szépia` (nézet) | ✅ **megvalósítva** | ld. lentebb — nem duplikátum | 5.8 |
| `Fekete-fehér` (nézet) | ✅ **megvalósítva** | ld. lentebb — nem duplikátum | 5.7 |

**Kilenc megvalósítva, egy helyfoglaló, egy hatókörön kívül.**

## Két kérdés, amit a jegy nyitva hagyott — és a válasz

### 1. `Szépia` / `Fekete-fehér` nézetmódként, ha effektként már megvan?

**IGEN, kellenek** — nem duplikátumok. Ugyanaz a **fordítási kulcs** két
külön parancson ül: a Kép menüben effektust alkalmaz (a képre, mentve), a
Megjelenítési módban a képsort alakítja (csak a képernyőre, nem mentve).

A #1581 kinyerése ezt **függetlenül igazolta**: az `eMenuView::ID_VIEW_BW`
kulcs **három** menürekordon szerepel, három azonosítóval — `0x9d1c`
(Nézet), `0x9d4c` (Kép), `0x9da9` (Eszközök) —, és a szomszédos
azonosítók számtani folytonossága igazolja, hogy három külön parancs.
⇒ **A push-olt sztring a FELIRATOT nevezi meg, nem a parancsot.** Egy
felirat-egyezésből tehát nem következik, hogy ugyanaz a funkció.

### 2. `Mac gamma (1.6)` — a jegy javaslata elavult

A #1579 azt javasolta: *„kihagyás, amíg nincs referencia-mérés"*. **A
referencia-mérés azóta megvan** (#1580, a tulajdonos teljes képernyős
felvételeiből), és a mód **meg is épült** (#1730).

⚠️ **A mérés egyúttal megcáfolta a spec korábbi értelmezését.** A mért
világosodás a központi fotón 133,5 → 154,5. Ebből a tényleges kitevő:

```
ln(154,5/255) / ln(133,5/255) = 0,7743      →  gamma 1,292
```

Az `x^(1/1,6)` (azaz 0,625) kitevő 170,2-t adna, nem 154,5-öt. A
megvalósítás ezért a **mért** kitevővel dolgozik
(`render/display_modes.py`: `MAC_GAMMA_EXPONENT = 0.7743`), nem a
felirat 1,6-os számával. A felirat a Picasa saját elnevezése; a mérés a
szerződés.

## Amit ez a döntés NEM mond ki

- **Nem** dönt a mód hatóköréről a felületen belül. Az külön kérdés
  (#1656: idővonal, keresés, tálca — megoldva; a szerkesztő-előnézet és a
  teljes képernyő nem).
- **Nem** dönt a 16 bites szemcsézés **pixelhű** reprodukálhatóságáról
  (NY-6): a statisztika mérve van, az MT19937 vetőmagozása nincs. A
  helyfoglaló státusz ettől független.

## Következmény a lefedettségi lapokra

A `Távoli asztal` a táblákban **„hatókörön kívül"**, nem „hiányzik"; a
`16 bites (szemcsézett)` **„helyfoglaló"**. A `docs/specs/picasa-megjelenitesi-modok.md`
7. táblázatának „nálunk ma" oszlopa ezzel a körrel a **mai kódra**
frissült — korábban minden sorában „nincs" állt, ami a #1575/#1656/#1658/#1730
körök óta nem volt igaz.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/render/display_modes.py` (a tizenegy mód
  képpont-átalakítói és a `MODES` névsora),
  `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml` (az almenü, a
  rádiócsoport és a `placeholder`/`retired` jelölés),
  `src/picasapy/app/display_mode_paint.py` (az aktuális mód egyetlen forrása)
- **Őrzi:** `tests/render/test_display_modes_1576.py`,
  `tests/render/test_display_modes_1577_1578.py`,
  `tests/render/test_display_modes_szepia_bw_1657.py`,
  `tests/app/test_display_mode_controller_1575.py`
