# Nyomtatás

Két nyomtatási mód van: **képenként egy lap**, és **indexkép** (sok kis
kép egy lapon).

## Képek nyomtatása

Jelöld ki a képeket, majd **Fájl ▸ Nyomtatás…** (Ctrl+P), vagy a képtálca
**Nyomtatás** gombja.

A párbeszédben beállítható:

- **Nyomtató** — a rendszeren elérhető nyomtatók listájából. A
  **Nyomtatás PDF-fájlba…** választásával fájlba nyomtatsz; ekkor meg
  kell adni a cél PDF nevét.
- **Nyomtató telepítése** gomb — a kiválasztott nyomtató **saját**
  lapbeállító ablakát nyitja meg (papírméret, tájolás, margók). Amit ott
  elfogadsz, azt a következő nyomtatás használni fogja. PDF-be
  nyomtatásnál a gomb szürke: ott nincs nyomtató, amit beállíts.
- **Elrendezés**: **Képenként egy lap** vagy **Indexképek**.
- **Nyomatméret**: 9×13, 10×15, 13×18, 20×25 cm, illetve a
  hüvelykes méretek (3,5×5, 4×6, 5×7, 8×10) és a **teljes oldal**.
- **Tájolás**: **Automatikus**, **Álló** vagy **Fekvő**. A nyomtatási
  feladat egyetlen tájolást használ; automatikus beállításnál a
  kijelölés első képéhez igazodik.
- **Illesztés a laphoz**: a **Lapkitöltés (vágással)** választásával a
  kép kitölti a lapot, a széle pedig levágódik.
- **Példány képenként**.

A nyomtató neve alatt egy sor mutatja, **milyen lapra** fogsz nyomtatni:
a papír neve, a mérete milliméterben és a tájolása — például
`A4 — 210 × 297 mm, álló`. Ez a sor a nyomtató beállításait követi, tehát
a **Nyomtató telepítése** ablak bezárása után rögtön frissül.

A párbeszéd kiírja, hány képet fog nyomtatni. Ha a felbontás a
választott mérethez kevés, figyelmeztet, hány kis méretű kép van, és
hogy nyomtatás előtt érdemes ellenőrizni őket. Egy kép akkor számít
kicsinek, ha a választott nyomatméretre kevesebb mint **150 képpont
jut hüvelykenként**.

## Szegély és felirat

A **Szegély- és szövegopciók…** gombbal külön lap nyílik, ahol a
nyomtatott kép szegélyét és feliratát állítod be:

- **Felirat forrása** — *Nincs szöveg*, *Képfeliratok*, *Fájlnév* vagy
  *Exif-adatok*;
- **Felirat helye** — *A kép alatt*, *A képen* vagy *A szegélyen*;
- **Betűtípus** és **méret**, valamint a **Szöveg tördelése** kapcsoló;
- **Szegély** — *Egyik sem*, *Maximális*, *Csak alul*, illetve
  **Egyenletes szélességű szegély**;
- **Szöveg színe** és **Szegély színe**.

Az **Alkalmaz** után az előnézet rögtön megmutatja az eredményt. A
beállítások megmaradnak a következő indításig.

Indexképek nyomtatásakor ezek a beállítások nem használhatók — a lap ezt
ki is írja.

## A nyomtatás haladása

Nyomtatás közben a párbeszéd kiírja, hol tart („Nyomtatás: 2 / 12"),
laponként lépve, és az alsó sáv is jelzi a munkát. Ez a nyomtatóra
küldésre és a PDF-be mentésre egyaránt áll. Amíg fut, a **Nyomtatás**
gomb nem indít újabb feladatot.

## Indexképek nyomtatása

**Mappa ▸ Indexképek nyomtatása…** (Ctrl+Shift+P) egy lapra sok kis képet
tesz. Az **Oszlopok** mezővel állítod, hány kép legyen egy sorban.

Ugyanez az **Elrendezés ▸ Indexképek** beállítással a szokásos
nyomtatási párbeszédből is elérhető.

## Megjegyzés a nyomtató-választóhoz

A PicasaPy saját, egyszerű nyomtató-választót használ a rendszer natív
nyomtatási ablaka helyett. A papírméretet, a tájolást és a margókat a
**Nyomtató telepítése** gombbal éred el. A további, nyomtatóra jellemző
beállításokat (kétoldalas nyomtatás, papírtálca) a nyomtató saját
kezelőfelületén vagy a PDF-be nyomtatás után a PDF-olvasóban tudod
megadni.
