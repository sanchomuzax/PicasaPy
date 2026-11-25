# Mentés, visszaállítás, visszavonás

A PicasaPy alapból nem nyúl a fájljaidhoz: a szerkesztéseket a képek
melletti `.picasa.ini` fájlban tartja. Ha viszont a **fájlba** is bele
akarod égetni a változtatásokat — mert máshol nyitod meg, vagy elküldöd
—, ezek a parancsok állnak rendelkezésre.

## Mentés

**Fájl ▸ Mentés** (Ctrl+S) a kijelölt képeket a szerkesztésekkel együtt
kiírja a lemezre.

A parancs csak akkor használható, ha a kijelölt képen van **még el nem
mentett szerkesztés**, ahogy az eredeti Picasában. Különben a menütétel
és a képek fölötti fejléc **Mentés** gombja szürke, és a Ctrl+S sem
csinál semmit.

A mentés előtt a program megkérdezi: **Lemezre menti a
módosításokat?** Alatta jelzi, hogy **biztonsági másolatot készít** a
fájlról (vagy fájlokról). A **Mentés** gomb ment, a **Mégse** semmit nem
változtat. Ha a **Ne kérdezzen újra.** jelölőt bejelölöd, és a
**Mentés** gombra kattintasz, a program a továbbiakban nem kérdez rá; a
**Mégse** gombnál a jelölő nem számít.

A biztonsági másolat az eredeti mappában marad, egy külön almappában, így
később még visszaléphetsz. A másolat megőrzi az eredeti fájl módosítási
dátumát is.

Ez a megőrzött eredeti **együtt mozog a képpel**: ha átnevezed,
áthelyezed vagy lemásolod a fotót, a másolata is odakerül, és a
**Visszaállítás** az új helyen is működik. Ha a célhelyen valami útban
van, a művelet inkább el sem indul, és az üzenet megmondja, mi
akadályozza — a program soha nem ír felül egy másik kép megőrzött
eredetijét.

Ha valamelyik képen olyan szerkesztés van, amit a program még nem tud
megjeleníteni (például egy régi Picasa-változat effektje), a mentés előtt
figyelmeztet: „A mentés ezek nélkül írja ki a képet, és a beállítások
elvesznek. Ez nem vonható vissza."

Ha a mentés, a visszaállítás vagy a mentés visszavonása véget ér, a rács
és a megnyitott néző **magától frissül**: a nézőben a szerkesztő a lemezen
lévő friss fájlt és szerkesztéslistát olvassa újra, tehát azt látod, ami
most a fájlban van. Ha a művelet nem sikerül, **hibaablak** mondja meg az
okot.

Ha a mentés **lemezhiba** miatt nem sikerül (például írásvédett a fájl
vagy a mappa, vagy megtelt a lemez), a hibaablak címe **Hiba**, mint az
eredeti Picasában. Az üzenet alatt a fájl neve és egy `hiba(…)`
szám áll. Ez a szám az eredeti Picasa saját hibakódja, nem a
rendszeré: 11, ha nincs jogod írni a fájlt, 10, ha a fájl vagy a mappa
nem található, minden más esetben (a megtelt lemezt is beleértve)
többnyire 2. A **Hiba** címet kapja a névütközés és a nem menthető
formátum hibaablaka is.

Ha a kész képet nem sikerül az eredeti helyére tenni (például mert a
fájl írásvédett), a képed változatlan marad. JPEG-képnél a már
elkészült, szerkesztett változat ilyenkor nem vész el: a kép mellett
`.jpg.jpg` végű néven megtalálod (például `nyaralas.jpg.jpg`), ahogy az
eredeti Picasában is. Ha ilyen nevű fájl már van, a program nem írja
felül. Biztonsági másolat ilyenkor nem készül, mert az eredeti fájl nem
változott.

## Mentés visszavonása

A mentés után megjelenő üzenetben a **Mentés visszavonása** gombbal
visszahozod a fájl mentés előtti állapotát — a szerkesztéseid közben
megmaradnak. Az üzenet ezt így mondja: „Az utolsó mentés visszavonásához
és a szerkesztések megtartásához kattintson a »Mentés visszavonása«
gombra." Csak a legutóbbi mentésre hat.

Ha a kép a szerkesztőben van nyitva, a mentés után a szerkesztő
**Visszavonás** gombjának felirata **Mentés visszavonása** lesz. Erre
kattintva ugyanez történik: a fájl visszakapja a mentés előtti
állapotát, a szerkesztések megmaradnak. Utána a **Visszavonás** gomb
a megmaradt szerkesztéseket vonja vissza (például a kiegyenesítést); ha
csak olyan változtatás maradt, ami nem szerkesztési lépés (például a
képre írt szöveg), a gomb szürke. Az **Újra** gomb szürke.

## Mentés másként és Másolat mentése

- **Fájl ▸ Mentés másként…** — a szerkesztett képet más néven, más helyre
  írja ki. JPEG és WebP formátumot kínál.
- **Fájl ▸ Másolat mentése** — az eredeti mellé ír egy szerkesztett
  másolatot, magától adott névvel. Ha több kép van kijelölve, csak a
  kiemelt (fókuszban lévő) képről készül másolat.

Ha a választott név foglalt, a program szól: „A fájl mentése nem
lehetséges. Már van ilyen nevű fájl." Ha a másolatot lemezhiba miatt nem
lehet kiírni, ezt írja: „Lemezhiba miatt nem lehetséges a fájlok
mentése. Lehet, hogy a lemez megtelt vagy írásvédett."

Videónál, és amíg nincs kijelölt kép, mindkét menüpont szürke.

## Visszaállítás

**Fájl ▸ Visszaállítás** a fájlt az eredeti változatára állítja vissza.
Ez a mentéskor készült biztonsági másolatot használja, ezért csak akkor
kapcsolható be, ha van ilyen másolat. Mentés után a
tétel azonnal használható, nem kell hozzá a kijelölést megváltoztatni.

A program rákérdez. Egyetlen képnél a kérdés: „Visszatér a fájl eredeti
változatához?", a gombok **Visszaállítás**, **Mentés visszavonása** és
**Mégse**. A **Mentés visszavonása** itt is csak az utolsó mentést vonja
vissza, a szerkesztéseket megtartva (lásd fent). Több képnél a kérdés:
„Visszatér a fájlok eredeti változatához?", és csak a **Visszaállítás**
és a **Mégse** gomb van. Megnyitáskor a **Mégse** kapja a fókuszt, így
egy véletlen **Enter** nem állít vissza semmit.

Ha egy fájlt a mentés óta **egy másik program módosított**, a program
még egyszer figyelmeztet, mert a visszaállítás ezt a változást is
eldobja: „Ez a fájl a PicasaPy programon kívül módosult. Ha a
visszaállítást választja, a módosítások elvesznek." (több fájlnál
„Ezek a fájlok…"), alatta „Vissza szeretne térni?". A gombok
**Visszaállítás ennek ellenére** és **Mégse**; a fókusz a **Mégse**
gombon áll.

A visszaállított kép elforgatása, tükrözése és a képre írt szövege is
törlődik, tehát a kép tényleg az eredeti állapotában jelenik meg.

Visszaállítás közben ugyanaz a lebegő folyamatjelző látszik, mint
mentéskor (ott „Fájl mentése: …%" áll), itt **Fájlok visszaállítása**
felirattal. Ha a lemez hibát jelez
(például megtelt vagy írásvédett), a program ezt írja: „Lemezhiba miatt
nem lehetséges az összes fájl visszaállítása. Lehet, hogy a lemez megtelt
vagy írásvédett." Sikeres visszaállítás után külön üzenet nem jön: a rács
egyszerűen az eredeti képet mutatja.

## Összes szerkesztés visszavonása

**Kép ▸ Összes szerkesztés visszavonása** nem a fájlt, hanem a
szerkesztések listáját törli. A fájl érintetlen marad; a kép egyszerűen
újra úgy néz ki, mint eredetileg. A szerkesztések mellett a **tükrözést**,
a képre írt **szöveget** és a szerkesztési előzményeket is törli; az
**elforgatás** viszont megmarad.

A menüpont csak akkor választható, ha a kijelölésben az első szerkesztett
kép nem csupán el van forgatva. Szürke, ha nincs kijelölt kép, ha egyik
kijelölt kép sincs szerkesztve, vagy ha az első szerkesztett kép csak
elforgatott.

A program rákérdez egy **Jóváhagyás** című ablakban: „Ezzel a művelettel
eltávolít minden módosítást, amelyet az ÖSSZES kijelölt képre
alkalmazott. Folytatja?" (a nézőben, egyetlen képnél az aktuális képről
szól a kérdés). A két gomb **Szerkesztések eltávolítása** és **Nem**.
Külön figyelmeztet, ha a képen
**vörösszem-javítás** van: azt az **Újra** paranccsal sem lehet
visszahozni. A figyelmeztetés **megnevezi a képet** (több képnél
mindegyiket, vesszővel).

## Melyik mit csinál?

| parancs | mire hat | elvész-e a szerkesztés |
|---|---|---|
| Mentés | a fájlra a lemezen | nem, csak beleég |
| Mentés visszavonása | az utolsó lemezre írásra | nem |
| Visszaállítás | a fájlra a lemezen | igen |
| Összes szerkesztés visszavonása | csak a szerkesztéslistára | igen (a fájl ép) |

## Ha nem sikerül a mentés

- **„Fájlformázási hiba miatt a fájl nem menthető."** — a fájl formátumát
  a program nem tudja kiírni.
- **„A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel."** — a
  cél fájl épp foglalt vagy nem írható.
- Ha a lemez megtelt vagy csak olvasható, a program erről is szól, és
  megnevezi az érintett fájlt.
