# Útlevélkép

Az **Útlevélkép** a képen lévő arcra vágja a fotót — útlevélhez és
igazolványképhez való méretben —, majd átadja a nyomtatási nézetnek. A
képet **nem módosítja**: a kivágás egy külön, ideiglenes fájlba készül,
és a fotókönyvtárban semmi nem változik.

## Használata

1. Jelölj ki **egy** képet, amin **egyetlen** arc van.
2. **Eszközök ▸ Kísérleti ▸ Útlevélkép…**
3. A program megkeresi az arcot, kivágja a képet, és megnyitja vele a
   [Nyomtatás](nyomtatas.md) párbeszédet.

Ha több képet jelöltél ki, a parancs a **kijelölés első** képére
dolgozik. Kijelölés nélkül szürke.

Az arc keresése **a háttérben** fut, ezért nagy képnél sem fagy be
közben a program: a könyvtár közben is használható.

## Hogyan vágja ki a program

A kivágás **négyzet**, és az arc **vízszintes közepére** igazodik: fölé
fejtérnek kerül az arc magasságának a harmada, alá — a vállnak — a hat
tizede. Ha az arc közel van a kép széléhez, a kivágás a kép határáig
megy, tehát ott nem lesz teljesen négyzet. Ez nem hiba: az eredeti
Picasa is így viselkedik.

Ha a képet a PicasaPy-ban **elforgattad**, a kivágás a forgatott képből
készül — azt látod, amit a nézőben is.

## A nyomtatási nézet útlevél-módban

A megnyíló nyomtatási párbeszéd három dologban tér el a szokásostól:

- a **Nyomatméret** mezőben **Útlevél** áll: 2 × 2 hüvelykes, azaz
  körülbelül 5 × 5 cm-es nyomat. Ez a méret **nincs benne** a kész
  méretek listájában — csak ez a parancs állítja be;
- az **Illesztés a laphoz** **Lapkitöltés (vágással)**;
- a **Példány képenként** egy.

Egy lapra annyi útlevélkép kerül, amennyi elfér — a nyomatok rácsba
rendeződnek, ahogy a többi méretnél is.

Az itteni beállítás **nem ragad meg**: a nyomtatási nézet következő,
szokásos megnyitása visszakapja a korábbi illesztésedet és
példányszámodat, és a megjegyzett nyomatméretet.

## Ha nem sikerül

| üzenet | mit jelent |
|---|---|
| **Nem találhatók arcok** | a program egy arcot sem talált a képen |
| **Úgy tűnik, több arc van a képen.** | egynél több arcot talált — útlevélképhez egy arc kell |
| **A kép nem olvasható be.** | a képfájlt nem tudta megnyitni |
| **A kivágott kép nem menthető.** | a kivágást nem tudta ideiglenes fájlba kiírni |

Az első kettő fölött **Megpróbálkozik egy másik képpel?** áll: válassz
olyan képet, amin egyetlen, jól látható arc van. A párbeszédet az **OK**
zárja, és semmi nem történik — a kép érintetlen marad.

Ha a program az arcot nem találja meg, de te látod, hol van, a
[néző arckeret-szerkesztésével](emberek.md) felvett arc **nem** segít:
az Útlevélkép mindig magától keresi meg az arcot.
