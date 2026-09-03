# Az adatbázis: hol van, áthelyezés, tömörítés

## Mit tárol a program, és hol

A PicasaPy háromféle helyen tart adatot:

1. **A képek mellett, a mappában** — a `.picasa.ini` fájlban. Ide kerül
   minden, ami a képhez tartozik: a csillag, a képfelirat, a
   szerkesztések, a nevek az arcokhoz, a geocímke. Ez az **igazságforrás**:
   ha átmásolod máshova a mappát, minden vele megy.

   Ez ugyanaz a fájl, amit az eredeti Picasa is használ, ezért a két
   program **ugyanazon a fotótáron párhuzamosan is használható**. A
   PicasaPy azt is visszaírja változatlanul, amit maga nem ért — így a
   Picasa beállításai nem vesznek el.

2. **Egy kereső-adatbázis** — a gyors kereséshez és szűréshez. Ez csak
   gyorsítás: bármikor újraépíthető a képekből.

3. **Egy indexkép-gyorstár** — a bélyegképek, hogy ne kelljen minden
   nagy képet újra beolvasni.

A 2. és 3. pont a rendszer szokásos adat- és gyorstár-mappájába kerül.

## Az adatbázis áthelyezése

Ha kevés a hely a rendszerlemezen, az adatbázist és a gyorstárat át
tudod tenni máshova: **Eszközök ▸ Kísérleti ▸ Adatbázis áthelyezése…**

A párbeszéd kiírja **az adatbázis jelenlegi helyét**, és a
**Tallózás…** gombbal választhatod ki az újat. Az **Alapértelmezett**
gomb visszaáll az eredeti helyre.

Az **Áthelyezés a következő újraindításkor** gombbal indítod. Amíg a
másolás fut, haladásjelző látszik. Amikor kész, ezt írja: „Az adatbázis
áthelyezve. A változás érvényesítéséhez indítsa újra a PicasaPy-t."

A **futó példány nem költözik át menet közben** — a változás csak a
következő indításnál lép életbe. Ha megszakítod, semmi nem változik: „Az
áthelyezés megszakítva — semmi sem változott."

## Az adatbázis tömörítése

Idővel az adatbázis fájlja megnőhet a törölt bejegyzések helyétől. Az
**Eszközök ▸ Kísérleti ▸ Adatbázis tömörítése…** összehúzza.

A tömörítés megszakítható, és nem veszélyes: ha félbeszakítod, „A
tömörítés megszakítva. Az adatbázis változatlan." Ha nincs mit
felszabadítani, a program szól: „Az adatbázis már tömör — nincs teendő."

## Ha az adatbázis megsérül

A képeidet nem fenyegeti veszély: minden fontos adat a `.picasa.ini`
fájlokban van a képek mellett. Ha az adatbázis megsérül, töröld a
tartalmát, indítsd újra a programot, és hagyd, hogy újra átnézze a
figyelt mappákat.
