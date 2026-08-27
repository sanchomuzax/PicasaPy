# A szerkesztő 1. füljének („Gyakori javítások") gombsorrendje — VÉGLEGES

**Állapot:** eldöntve, lezárva. **Dátum:** 2026-08-16. **Döntő:** a tulajdonos,
az eredeti Picasa 3.9 (Windows) képernyőképe alapján. **Jegy:** #464.

## A sorrend — ez az érvényes, ehhez kell igazodni

Három sor, soronként három csempe, **alattuk** a Derítőfény-csúszka:

```
Vágás            Kiegyenesítés          Vörösszem
Jó napom van     Automatikus kontraszt  Automatikus szín
Retusálás        Szöveg
─────────────────────────────────────────────────────────
[kis kép]  ──────●────────  Derítőfény
─────────────────────────────────────────────────────────
Visszavonás: <lépés>            Újra
```

Kódban (`EditorTabCommonFixes.qml`, ebben a forrás-sorrendben):

| # | `objectName` | felirat |
|---:|---|---|
| 1 | `editToolCrop` | Vágás |
| 2 | `editToolTilt` | Kiegyenesítés |
| 3 | `editToolRedeye` | Vörösszem |
| 4 | `editToolEnhance` | Jó napom van |
| 5 | `editToolAutolight` | Automatikus kontraszt |
| 6 | `editToolAutocolor` | Automatikus szín |
| 7 | `editToolRetouch` | Retusálás |
| 8 | `editToolText` | Szöveg |
| 9 | `fixesFillSlider` | Derítőfény (csúszka, a rács ALATT) |

**Kreatív készlet (`picnik`) nincs** — halott online funkció, tudatosan
kihagyva (ld. `ui-audit-editor.md`).

## ⚠️ Amit ez a lap egyszer s mindenkorra eldönt

**Nem „hiányzó bizonyíték" volt — ROSSZ FÁJLT néztünk.** A Picasa felületét
két forrás írja le, és a korábbi körök a rosszabbikból következtettek:

| forrás | mit ad meg | mit NEM |
|---|---|---|
| `editpanel.tre` | a gombok **viselkedését** (mi nyílik kattintásra) | a helyüket |
| **`respack.yt`** | a tervezővászon **koordinátáit, képpontra pontosan** | — |

Az 1. fülön mind a tíz gomb `.tre`-sora **szó szerint azonos** — ha az volna a
teljes elrendezés, mind egymáson ülne. A körök a fájlban szereplő
FELSOROLÁSI sorrendet olvasták kirajzolási sorrendnek. Az nem az.

A `respack.yt`-ból kiolvasva a rács **betűre a tulajdonos képernyőképe**:

```
1. sor:  Vágás          Kiegyenlítés           Vörösszem
2. sor:  Jó napom van   Automatikus kontraszt  Automatikus szín
3. sor:  Retusálás      Szöveg                 (üres)
4. sor:  Derítőfény
```

Három oszlop (**x 37 · 118 · 198**), négy sor (**y 91 · 155 · 223 · 290**),
gombméret **44 × 30**.

A 3. sor harmadik helye azért üres, mert a **Kreatív készlet** gombját a
csomag kikommentezi (`#` előzi meg) — a szolgáltatás 2012-ben megszűnt.

## Miért csúszott vissza kétszer

**A helyes sorrend már két hónapja benne volt a méretspecifikációnkban,
ugyanígy.** Egy későbbi kör a `.tre`-ből mondott ellent neki, és **nem volt
megjelölve, melyik forrás az erősebb.** Ez a lap és a spec „egyetlen érvényes
forrás" jelölése ezt zárja be: a `respack.yt` a helyre nézve az igazságforrás,
a `.tre`-ből **sorrendre következtetni tilos**.

**És a tulajdonos futó Picasájából készült képernyőkép erősebb bizonyíték a mi
következtetésünknél** — a képet megkérdőjelezni tilos (#464, 2026-08-16):
*„Ez a valódi és végleges effekt sorrend az első fülön! TILOS
megkérdőjelezned újra!"*

## Miért kellett ezt külön lapra írni

A sorrend **kétszer** került napirendre újra:

1. Egyszer a jegy szövege alapján (feljegyzésből készült, téves sorrend) — a
   tulajdonos képernyőképe felülírta;
2. másodszor egy 2026-08-16-i bináris-kutatás alapján, ami az erőforrás-
   sorrendet hozta, és ismét ellentmondott a kódnak.

A tulajdonos ekkor jelezte, hogy ezt már **húsznál többször** megadta. Ez a lap
a végleges hivatkozási pont; a `PROTOKOLL.md` szerint elvetett irányt csendben
visszahozni tilos, és **ez itt egy elvetett irány**.

## Az őr

`tests/app/qml_functional/test_editor_464.py` → `TestTab1ButtonOrder` állítja a
forrás-sorrendet, és külön teszt őrzi, hogy a Kreatív készlet csempéje nincs
jelen. **Ha egy jövőbeli kör „javítani" akarja a sorrendet, ez a teszt fog
elbukni — és akkor ezt a lapot kell elolvasni, nem a tesztet átírni.**

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/EditorTabCommonFixes.qml`
- **Őrzi:** `tests/app/qml_functional/test_editor_464.py`
