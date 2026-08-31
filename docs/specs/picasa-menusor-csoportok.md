# A Picasa 3 menüsora: sorrend, csoportok, szélesség — mérve

*2026-08-31 (#1774). Ez a lap a **tulajdonos képernyőmentéseiből** készült
(`\\DS215j\lemez\My Pictures\Picasa-3-menuk`, magyar Picasa 3.9, Windows,
100/125/150/175% DPI). Ami itt szerepel, azt a kép **mutatja** — nem
következtetés.*

A lap három olyan kérdésre felel, amire sem a szövegtár, sem a bináris nem
felel: **milyen sorrendben állnak a menük**, **hol vannak az elválasztók**,
és **mekkora a menük valós szélessége**. A tételek azonosítói és feliratai
a `picasa-menu-leltar.md`-ben (#1397) vannak; ez a lap nem ismétli meg őket.

---

## 1. A menüsor sorrendje

```
Fájl · Szerkesztés · Nézet · Mappa · Kép · Létrehozás · Eszközök · Súgó
```

Mind a nyolc mentés menüsávja ugyanezt a sorrendet mutatja (a mentések a
megnyitott menütől jobbra eső részt is látni engedik, így a sorrend
**minden képen** ellenőrizhető, nem csak az elsőn).

A szövegtár ábécérendben sorolja a nyolc gyökérkulcsot, ezért a sorrend
**belőle nem olvasható ki** — a jegy ezt a mai QML-sorrend igazolatlan
feltevéseként írta le. A mérés a feltevést **megerősíti**.

---

## 2. A csoportok (elválasztók)

A `·` a tételeket, a vízszintes vonal az elválasztót jelöli. `(i)` = a
mentésen inaktív (szürke) tétel — az inaktív tételek **láthatók**, tehát a
csoportszerkezet a mentésből hiánytalanul kiolvasható.

### Fájl — 19 tétel, 9 csoport

| # | tételek |
|---|---|
| 1 | Új album… `Ctrl+N` |
| 2 | Mappa hozzáadása a Picasához… · Fájl felvétele a Picasába… `Ctrl+O` · Importálás forrása… `Ctrl+M` · Importálás a Google Fotókból… |
| 3 | Fájl(ok) megnyitása szerkesztőben `Ctrl+Shift+O` (i) |
| 4 | Áthelyezés új mappába… (i) · Átnevezés… `F2` |
| 5 | Mentés `Ctrl+S` · Visszaállítás (i) |
| 6 | Mentés másként… · Másolat mentése · Kép exportálása mappába… `Ctrl+Shift+S` |
| 7 | Keresés a lemezen `Ctrl+Enter` · Törlés lemezről `Delete` |
| 8 | Nyomtatás… `Ctrl+P` · E-mail… `Ctrl+E` · Papírképek rendelése… |
| 9 | Kilépés |

### Szerkesztés — 12 tétel, 4 csoport

| # | tételek |
|---|---|
| 1 | Kivágás `Ctrl+X` (i) · Másolás `Ctrl+C` (i) · Beillesztés `Ctrl+V` (i) |
| 2 | Az összes effektus másolása (i) · Az összes effektus beillesztése (i) |
| 3 | Szöveg másolása (i) · Szöveg beillesztése (i) |
| 4 | Az összes kijelölése `Ctrl+A` · Csillagozottak kijelölése · Kiválasztás megfordítása `Ctrl+I` · Kijelölés törlése `Ctrl+D` (i) |

**Nincs „Visszavonás" tétel a menü élén.** A szövegtárban van
`eMenuEdit::ID_UNDO` és `ID_REDO`, a mentésen viszont **egyik sem
jelenik meg** — pedig a menü többi inaktív tétele igen. Vagyis a
Visszavonás/Ismétlés nem a menüsáv Szerkesztés menüjének állandó tétele.

### Nézet — 19 tétel, 8 csoport

| # | tételek |
|---|---|
| 1 | Könyvtárnézet (i) |
| 2 | Kis indexképek `Ctrl+1` · **✓** Normál indexképek `Ctrl+2` · Szerkesztési nézet `Ctrl+3` |
| 3 | Tulajdonságok · Címkék `Ctrl+T` · Emberek · Helyek |
| 4 | **✓** Szerkesztési vezérlők megjelenítése (i) |
| 5 | Diavetítés `Ctrl+4` · Időrend `Ctrl+5` |
| 6 | Keresési opciók · **✓** Kis képek · Rejtett képek |
| 7 | Színkezelés használata · Megjelenítési mód ▸ |
| 8 | Indexkép felirata ▸ · Mappanézet ▸ |

A 2. csoport **rádiócsoport** (egy pipa a háromból), a 4. és a 6. csoport
pipái függetlenek.

### Mappa — 12 tétel, 6 csoport

| # | tételek |
|---|---|
| 1 | Leírás szerkesztése… · Diavetítés megtekintése `Ctrl+4` |
| 2 | Indexképek frissítése · Rendezés ▸ |
| 3 | Elrejtés · Megjelenítés (i) |
| 4 | Indexképek nyomtatása… `Ctrl+Shift+P` · Exportálás HTML-oldalként… |
| 5 | Keresés a lemezen `Ctrl+Enter` · Eltávolítás a Picasából… |
| 6 | Áthelyezés… · Törlés… |

### Kép — 7 tétel, 5 csoport

| # | tételek |
|---|---|
| 1 | Megjelenítés és szerkesztés `Ctrl+3` · Csoportos szerkesztés ▸ |
| 2 | Összes szerkesztés visszavonása |
| 3 | Elrejtés (i) · Megjelenítés (i) |
| 4 | Arcok alaphelyzetbe állítása |
| 5 | Tulajdonságok `Alt+Enter` |

### Létrehozás — 8 tétel, 3 csoport

| # | tételek |
|---|---|
| 1 | Beállítás háttérképként… (i) · Poszter készítése… |
| 2 | Képkollázs… · Hozzáadás a képernyővédőhöz… · Ajándék CD készítése… · Mozgófilm ▸ |
| 3 | Közzététel a Bloggeren… |

### Eszközök — 13 tétel, 5 csoport

| # | tételek |
|---|---|
| 1 | Mappakezelő… · Feltöltéskezelő… (i) · Személyek kezelése… |
| 2 | Fotómegjelenítő beállítása… · Képernyővédő konfigurálása… |
| 3 | Képek biztonsági mentése… · Csoportos feltöltés… · Dátum és idő beállítása… |
| 4 | Feltöltés ▸ · Geocímke ▸ · Kísérleti ▸ |
| 5 | Gombok konfigurálása… · Beállítások… |

A menü **nem tartalmaz** duplikátum- vagy arckereső tételt a felső szinten.
A szövegtárban a `eMenuTools::ID_DUPES` („Show Duplicate Files") megvan, a
mentésen viszont nincs a felső szinten — a **Kísérleti** almenüben lehet,
amelynek tartalmát ez a mentés nem nyitja ki.

### Súgó — 10 tétel, 4 csoport

| # | tételek |
|---|---|
| 1 | Súgó – tartalom és tárgymutató `F1` · Billentyűkódok |
| 2 | Picasa-fórumok · Online információ · Termékkiadási tájékoztató · Adatvédelmi irányelvek · Általános Szerződési Feltételek · A Picasa eltávolítása |
| 3 | Frissítések keresése |
| 4 | A Picasa névjegye |

---

## 3. Szélesség — nincs rögzített minimum

A mentések vágott képek, a menü bal szélétől a jobb széléig. A menük
szélessége **tételenként más**, és nincs közös alsó érték:

| menü | szélesség 100%-on (kp) |
|---|---|
| Fájl | 349 |
| Nézet | 315 |
| Mappa | 313 |
| Kép | 312 |
| Szerkesztés | 286 |
| Súgó | 272 |
| Létrehozás | 269 |
| Eszközök | 253 |

**A szélesség a DPI-vel arányosan nő** — a Fájl menü négy nagyításban:

| DPI | mért szélesség | a 100% szorosa |
|---|---|---|
| 100% | 349 | 1,00 |
| 125% | 433 | 1,24 |
| 150% | 520 | 1,49 |
| 175% | 604 | 1,73 |

Vagyis a szélességet **kizárólag a betűméret-arányos szövegméret** adja: a
leghosszabb felirat, plusz a bal oldali pipa-vályú, plusz a jobb oldali
gyorsbillentyű-oszlop. Rögzített képpontos minimum nincs benne — ha lenne,
az arány a kis nagyításoknál elromlana.

**Nálunk** a `PicasaMenu.qml` 200 képpontos alsó korlátot tart (#1740).
Ez a mérés szerint idegen elem, de **nem okoz csonkolást**, és a legszűkebb
mért eredeti menü is 253 képpont — a korlát a gyakorlatban sosem lép
életbe. Külön jegy nélkül nem bántjuk.

---

## 4. Amit ez a lap NEM dönt el

- a **Kísérleti**, **Feltöltés**, **Geocímke**, **Rendezés**, **Csoportos
  szerkesztés**, **Mozgófilm**, **Megjelenítési mód**, **Indexkép
  felirata** és **Mappanézet** almenük tartalma — a mentések nem nyitják ki
  őket (a Rendezés készletére a #1595 és a #1766 fut);
- a 4. menü **kontextusfüggő** címkéje (Mappa ↔ Album) — a mentés mappa-
  nézetben készült, tehát csak a „Mappa" alakot mutatja;
- a **mnemonikok**: a képen az aláhúzás nem látszik (a Windows alapból
  elrejti, amíg az `Alt`-ot le nem nyomják).
