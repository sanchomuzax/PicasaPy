# Nyomtatás

Két nyomtatási mód van: **nyomatméret szerint** (a választott méretű
nyomatok a papíron), és **indexkép** (sok kis kép egy lapon). A kettő
közt nincs külön választó: az **indexkép a nyomatméretek listájának
egyik tétele**, ahogy az eredeti Picasában is.

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
- **Nyomatméret** — magyar felületen nyolc, angol felületen kilenc tétel.
  Magyar felületen hét méret metrikus:
  **5 × 8 cm**, **9 × 13 cm**, **10 × 15 cm**, **13 × 18 cm**,
  **15 × 20 cm**, **20 × 25 cm** és a **FullPage** (a teljes oldal);
  angol felületen nyolc méret jelenik meg (**Tárcaméret**, 3 × 4,
  3,5 × 5, 4 × 5, 4 × 6, 5 × 7, 8 × 10 és a FullPage). Az **Indexképek**
  mindkét listában a méretválasztó további tétele — ez
  nem méret, hanem a sok kis kép egy lapra (lásd lentebb). A lista
  **alapból a FullPage**-en áll; a választásod megmarad a következő
  nyomtatásig.

  A **FullPage** felirata magyar felületen is angolul áll: az eredeti
  Picasa is így írta, és ezen nem változtatunk.
- **Tájolás**: **Automatikus**, **Álló** vagy **Fekvő**. A nyomtatási
  feladat egyetlen lapállást használ. **Automatikus** beállításnál a
  papír **álló** marad, és a program a nyomatot fordítja el, ha úgy
  kevesebb lap kell; **Álló** vagy **Fekvő** választásával te döntöd el.
- **Illesztés a laphoz**: **A teljes kép**, vagy a **Lapkitöltés
  (vágással)** — utóbbinál a kép kitölti a helyét, a széle pedig
  levágódik.
- **Példány képenként**.

Ha a nyomatméret helyén az **Indexképek** áll, a **Példány képenként**, a
kis előnézet és a képminőség két sora **eltűnik** — indexképnél ezeknek
nincs értelme, ott mindig a teljes kép kerül a cellába. Helyettük az
**Oszlopok** mező jelenik meg. A nyomtató, a tájolás és az illesztés
marad.

A nyomtató neve alatt egy sor mutatja, **milyen lapra** fogsz nyomtatni:
a papír neve, a mérete milliméterben és a tájolása — például
`A4 — 210 × 297 mm, álló`. Ez a sor a nyomtató beállításait követi, tehát
a **Nyomtató telepítése** ablak bezárása után rögtön frissül.

A párbeszéd kiírja, hány képet fog nyomtatni. Alatta két sor a
képminőségről: **Legkisebb kép: *N* képpont/hüvelyk**, és új sorban vagy
**Készen áll a nyomtatásra.**, vagy — ha van kevés felbontású kép —
**Nézze át nyomtatás előtt.** és hogy hány kis kép van. Egy kép akkor
számít kicsinek, ha a választott nyomatméretre kevesebb mint **150
képpont jut hüvelykenként**.

Ha a beállításokból nem jön ki érvényes nyomtatás, a program megnevezi a
hibát: **Érvénytelen nyomtatási beállítás:** és utána, mi a baj.

## Ahogy a nyomatok a lapra kerülnek

A választott **nyomatméret** nem az egész lapot jelenti: a program
ekkora **helyeket** rak a papírra, **rácsban**, sorfolytonosan. Ha egy
sor betelt, új sort kezd; ha a lapon már nem fér el több sor, **új lapon
folytatja** ott, ahol abbahagyta. Egy A4-es lapra így például két 10×15
cm-es nyomat is felkerül, nem csak egy.

A maradék helyet a program laponként egyenletesen osztja szét a nyomatok
közt. Egy félig teli utolsó sor a teli sorok oszlopaihoz igazodik, balra
zárva.

A **példány képenként** ezt a rácsot tölti: két kép × két példány négy
helyet kér, és hogy ez hány lap, a nyomatmérettől és a papírtól függ.
Egy kép példányai egymás után jönnek.

Ha a választott nyomatméret **egyáltalán nem fér el** a papíron — ilyen
a **FullPage**, vagy egy A4-nél alig nagyobb méret —, a program
visszatér a régi működéshez: **egy kép egy lapra**, a teljes
nyomtatható területre.

## Útlevélkép

Az **Eszközök ▸ Kísérleti ▸ Útlevélkép…** szintén ezt a párbeszédet
nyitja meg, arcra vágott képpel és **Útlevél** nyomatmérettel — a
részletek: [Útlevélkép](utlevelkep.md).

## Az előnézet és a lapszám

A nyomtató alatti kis előnézet a **tényleges lapot** mutatja, a rácsba
rendezett nyomatokkal. Ha több lap lesz, az előnézet alatt lapozó áll,
középen a **jelenlegi lap / összes lap** számmal — ebből tudod meg
előre, hány lapot fogsz elhasználni.

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

Ugyanide jutsz a szokásos nyomtatási párbeszédből is: válaszd a
**Nyomatméret** lista utolsó tételét, az **Indexképek**-et. Ilyenkor
lapozható előnézet nincs, de a darabszám-sor megmondja, **hány lap** lesz
belőle.

Az indexkép-mód **nem ragad meg**: ha a nyomtatást bezárod, a következő
Ctrl+P megint méret szerinti nyomtatással nyílik.

## Megjegyzés a nyomtató-választóhoz

A PicasaPy saját, egyszerű nyomtató-választót használ a rendszer natív
nyomtatási ablaka helyett. A papírméretet, a tájolást és a margókat a
**Nyomtató telepítése** gombbal éred el. A további, nyomtatóra jellemző
beállításokat (kétoldalas nyomtatás, papírtálca) a nyomtató saját
kezelőfelületén vagy a PDF-be nyomtatás után a PDF-olvasóban tudod
megadni.
