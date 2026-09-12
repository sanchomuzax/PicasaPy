# Képek biztonsági mentése

A PicasaPy át tudja másolni a fotóidat egy másik meghajtóra vagy egy
hálózati megosztásra. A másolás **nem mozdítja el** az eredetiket, és nem
is módosítja őket.

Indítás: **Eszközök ▸ Képek biztonsági mentése…**

## Mit ment el

A mentés a **figyelt mappáid** teljes tartalmát veszi alapul — ugyanazokat
a mappákat, amiket a [Mappakezelőben](mappakezelo.md) állítottál be. Nem
a kijelölésed és nem az éppen látott mappa számít. Hogy ezekből mi kerül
át, azt a készlet fájlszűrője dönti el.

## A mentés-készlet

A mentés egy **készlethez** tartozik. A készlet megjegyzi, hova mentett és
mit mentett már el, így a következő futás **csak az újat és a
megváltozottat** másolja át. Egy nagy fotótár első mentése így hosszú, a
másodiktól kezdve viszont gyors.

Több készletet is létrehozhatsz — például egy teljeset a külső
merevlemezre, és egy szűkebbet egy hálózati mappába.

Az ablakban a készletek listája látszik, mindegyik alatt a mentés helye és
az utolsó futás ideje. Ha még egy sincs, ezt írja: „Még nincs
mentés-készlet."

## Új készlet

Az **Új készlet…** gombbal három dolgot adsz meg:

- **Név** — amit a listában látsz majd.
- **Mentés ide** — a célmappa. A **Tallózás…** gombbal ki is válaszd.
- **Fájlok** — mi kerüljön át:
  - **Minden fájltípus** — fotók, RAW-fájlok és videók;
  - **Minden kép (videók nélkül)**;
  - **Csak JPEG-ek fényképezőgép-adatokkal** — azok a JPEG-ek, amikben
    benne van a fényképezőgép neve. Ezzel a képernyőképek és a letöltött
    képek kimaradnak a mentésből.

A **Készlet módosítása…** ugyanezt a három mezőt nyitja meg egy meglévő
készleten. A **Készlet törlése** rákérdez; **a már elmentett fájlokat nem
bántja**, csak a nyilvántartást szünteti meg.

## A mentés futtatása

Válaszd ki a készletet a listában, majd **Mentés**.

A program először **megszámolja**, hány fájl menne át, és ezt kiírja.
Ha közben semmi nem változott, ezt az üzenetet kapod: „Minden el volt már
mentve." A végén megmondja, hány fájl ment át.

Csak a **sikeresen** átmásolt fájl kerül a nyilvántartásba. Ha a mentés
félbeszakad — például megtelik a cél, vagy megszűnik a hálózati
kapcsolat —, a következő futás pótolja a hiányzót.

## Mi kerül a célmappába

- A képek, az eredeti **mappaszerkezetet megtartva**.
- A képek mellé a `.picasa.ini` fájlok is. Így a mentés önmagában teljes
  értékű archívum: a címkék, a csillagok és a szerkesztések a képekkel
  együtt maradnak meg.
- A cél gyökerében egy `files.txt` nevű lista arról, mi került át:
  soronként az útvonal, a méret és a módosítás ideje. Ezt bármilyen
  szövegszerkesztővel meg tudod nézni, a PicasaPy nélkül is.

## Ami nincs benne

Az eredeti Picasa CD-re és DVD-re is tudott menteni. A PicasaPy **nem ír
lemezt** — a cél mindig egy mappa: külső meghajtó, pendrive vagy hálózati
megosztás.
