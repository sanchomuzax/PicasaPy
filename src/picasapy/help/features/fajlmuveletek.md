# Fájlműveletek: átnevezés, áthelyezés, törlés

Ezek a parancsok a **lemezen lévő fájlokra** hatnak, nem csak a
nézetre. A PicasaPy minden ilyen műveletnél rákérdez.

## Megnyitás külső szerkesztőben

**Fájl ▸ Fájl(ok) megnyitása szerkesztőben** (Ctrl+Shift+O) a kijelölt
képeket a **rendszer alapértelmezett programjában** nyitja meg — ugyanabban,
amelyik a fájlkezelőben a képre duplán kattintva is megnyílna. Külön
szerkesztőprogramot a PicasaPy nem kér. Több képnél fájlonként nyit
ablakot. Ha valamelyik fájlt nem sikerült megnyitni, egy üzenet megmondja,
hányat a kijelölt fájlok közül: „A rendszer alapértelmezett alkalmazása nem
tudta megnyitni a kijelölt fájlok *N*/*M* részét." A menüpont szürke, amíg
nincs kijelölt kép.

## Átnevezés

**Fájl ▸ Átnevezés…** (F2), vagy a kép helyi menüjéből.

Egy és több kijelölt képnél is ugyanaz a **Fájlok átnevezése** ablak
nyílik meg. Egyetlen képnél a névmezőben már ott áll a kép mostani neve
(kiterjesztés nélkül), kijelölve, így rögtön átírhatod. Írd be az új
nevet. Több kép egyszerre is átnevezhető -
ilyenkor a program csak akkor tesz sorszámot a név végére, ha a név már
foglalt (lásd lentebb). A **Befoglalás a fájlnévbe:** alatt
bekapcsolhatod, hogy a névbe kerüljön bele a **Dátum** és a
**Képfelbontás** is. Alul a **Példa** sor mutatja a név felépítését,
az eredeti Picasa rögzített mintájával: például `Nyaralás 08-01-2004
2-30-45 PM 640x480.jpg`. A dátum, a felbontás és a `.jpg` itt mindig
ugyanaz a minta, nem a kijelölt kép saját adata; a kész nevekbe viszont
a képek valódi dátuma és felbontása kerül. A kiterjesztést nem kell
beírnod, a fájl megtartja a sajátját.

Az **Átnevezés** gomb szürke, amíg a névmező üres, vagy amíg a benne
álló név megegyezik azzal, amivel az ablak megnyílt; ilyenkor az
**Enter** sem csinál semmit. A névmezőben az **Enter** elfogadja az új
nevet (ugyanaz, mint az **Átnevezés** gomb), a **Mégse** és az **Esc** megszakítja az
átnevezést. Egyetlen kép átnevezése után a kép **kijelölve marad**, így
rögtön folytathatod vele a munkát.

- A **Dátum** a felvétel **dátumát és idejét** (másodpercre) teszi a
  névbe, a számítógéped területi beállítása szerinti formában. A
  fájlnévben nem használható jelek (például a kettőspont vagy a
  perjel) helyén kötőjel áll. Ha egy képnek nincs felvételi dátuma, a
  neve dátum nélkül készül.
- A névmezőbe nem írhatók (és nem is illeszthetők be) a fájlnévben
  tiltott karakterek: `\ / : * ? " < > |`.
- A két jelölőnégyzet állását a program **megjegyzi**, a következő
  megnyitáskor úgy találod őket, ahogy hagytad.

**Sorszám csak foglalt névnél.** A program képenként, sorban halad. Ha
a kész név szabad, a kép pontosan azt kapja, sorszám nélkül. Ha már van
ilyen nevű fájl a mappában (akár egy korábban, ugyanebben a menetben
átnevezett kép), a következő szabad sorszámot teszi a név végére,
háromjegyűen: `Nyaralás.jpg`, `Nyaralás-001.jpg`, `Nyaralás-002.jpg`.
Ha a beírt név maga is kötőjeles számra végződik (például `Nyaralás-5`), és ez a
név foglalt, a keresés a következő számmal folytatódik (`Nyaralás-006`). Ha bekapcsolod a **Dátum**ot,
és a képek más-más időpontban készültek, a nevek amúgy is különböznek,
ezért sorszám sem kerül rájuk.

Ha a művelet **menet közben** akad el (például az egyik fájl zárolt), a már
átnevezett fájlok **a helyükön maradnak**, és a hibaüzenet **megnevezi az
elkészült fájlokat**, valamint azt, amelyiknél leállt — ennek és a kívánt
új nevének az állapotát érdemes ellenőrizni. A nézet ilyenkor is
frissül, tehát azt látod, ami a lemezen van.

## Áthelyezés

- **Fájl ▸ Áthelyezés új mappába…** — a kijelölt képek új mappába
  kerülnek. A parancs a **Mappa tulajdonságai** ablakot nyitja, ahogy az
  eredeti Picasa: a név mezőben **Névtelen** áll, a dátum a mai nap, és
  itt adhatod meg a helyszínt, a leírást és a zenét is. Az **OK** után
  készül el a mappa, és kerülnek bele a képek; a **Mégse** semmit nem
  változtat. Ha a név üres, tiltott jelet tartalmaz, vagy már van ilyen
  nevű mappa, a program szól, és nem mozgat semmit.
- A képeket **húzással** is átteheted egy másik mappára a bal hasábon.

Áthelyezés közben haladásjelző mutatja, hányadik fájlnál tart.

### Húzással

Jelöld ki a képeket a rácsban, fogd meg őket az egérrel, és engedd el a
bal hasáb egyik **mappasorán**. A célsor húzás közben kiemelődik. A
képek kérdés nélkül átkerülnek abba a mappába; ha ott már van azonos
nevű fájl, a bevitt kép új nevet kap, semmi nem íródik felül. Ez a lapos
mappalistán és a **fanézetben** is ugyanígy működik.

Egy egész **mappát** is áthúzhatsz a bal hasábon egy másik mappára: a
mappa a tartalmával együtt annak a mappának az almappája lesz.

Ha a célmappában már van azonos nevű fájl, választhatsz: **Másodpéldányok
átnevezése** (a bevitt fájlok új nevet kapnak) vagy **Másodpéldányok
kihagyása**. Egy már létező célfájlt a program **soha nem ír felül és nem
töröl** — se az áthelyezés, se a félbemaradt művelet visszagörgetése: az
utóbbi is csak azt takarítja el, amit maga hozott létre.

A képpel együtt költözik a **mentéskor készült biztonsági másolata** is,
tehát a **Visszaállítás** az új helyen is működik — lásd
[Mentés, visszaállítás](mentes.md).

### Ha az áthelyezés elakad

Előfordul, hogy a program nem tudja végigvinni a költöztetést: a fájl
zárolva van, a mappára nincs írásjogod, vagy a másik lemez menet közben
eltűnik. Ilyenkor a kép **a régi helyén marad**, és a célmappában nem
keletkezik belőle másolat — a program a félbemaradt másolatot visszatörli.
Így nem fordulhat elő, hogy egy sikertelen áthelyezésből kettő lesz
ugyanabból a képből. Ugyanez a védelem működik a Kukába helyezésnél, a
visszaállításnál és a megőrzött eredetik költöztetésénél is.

## Másolás, kivágás, beillesztés

**Szerkesztés ▸ Másolás** (Ctrl+C) és **Kivágás** (Ctrl+X) a
fájlkezelőbe adja át a fájlokat, így máshova beillesztheted őket.

A **Szerkesztés ▸ Beillesztés** (Ctrl+V) a másik irány: a vágólapra tett
fájlokat az **éppen kiválasztott mappába** másolja. Mindegy, honnan
kerültek oda — a fájlkezelőből vagy a PicasaPy fenti két parancsából.
Kivágás után áthelyezés lesz belőle, másolás után másolás.

Ha a célmappában már van azonos nevű fájl, a beillesztett kép **új nevet
kap**: semmi nem íródik felül.

Üres vágólapnál a menüpont szürke. Ha közben ürült ki a vágólap, a
program megmondja, miért nem történt semmi („Nincs beilleszthető fájl a
vágólapon.").

Szövegmezőben — például átnevezés közben — a Ctrl+V a mezőé marad, tehát
a szövegbe illeszt be, nem fájlt.

## Törlés

**Fájl ▸ Törlés lemezről** (Delete), vagy a kép helyi menüjéből; a
nézőben **Ctrl+Delete** (albumból megnyitott képen ez is csak az
albumból veszi ki, lásd lent).

Ez a menüpont **attól függ, hol állsz**: album nézetében **Eltávolítás az
albumból**, egy Emberek albumban **Eltávolítás az Emberek albumból** a
felirata, és akkor csak az összeállításból veszi ki a képet — a fájlhoz
nem nyúl. Mappában áll a **Törlés lemezről** felirat, és ott tényleg
törli a fájlt.

A program megerősítést kér. A kérdés ablaka **Elemek törlése**, és a
szövege attól függ, **hova** kerül a fájl:

- ha a rendszer **Kukája** használható, a program oda küldi a fájlt, és
  ezt kérdezi: „Biztosan a Kukába szeretné küldeni a kijelölt fájlt? (Így
  az összes olyan albumból is el fog tűnni, amelyben eddig látható
  volt.)" A jóváhagyó gomb **Kép törlése**, több képnél **Elemek
  törlése**;
- ha a Kuka **nem használható** — például hálózati megosztáson vagy
  pendrive-on lévő fájlnál —, a törlés **véglegesen** történik, és a
  kérdés ezt ki is mondja: „Biztosan végleg törli a kijelölt fájlt? (A
  művelet nem vonható vissza.)" A gomb ekkor **Fájl törlése**, illetve
  **Fájlok törlése**.

Az ablakban két gomb van, a jóváhagyó gomb és a **Mégse**.
Megnyitáskor a **Mégse** gomb kapja a fókuszt, így egy véletlen **Enter**
nem töröl semmit. Az ablak alján a **Ne kérdezzen újból, mindig
távolítsa el** jelölővel kapcsolhatod ki, hogy a program legközelebb is
rákérdezzen. Ugyanezt a **Beállítások ▸ Általános** lapon is
megteheted („Törlés a lemezről megerősítés nélkül"), és ott vissza is
kapcsolhatod.

## Keresés a lemezen

**Fájl ▸ Keresés a lemezen** (Ctrl+Enter) megnyitja a fájlkezelőben azt
a mappát, ahol a kép van. Ha **nincs kijelölt kép**, a Ctrl+Enter a
megnyitott mappát mutatja meg a fájlkezelőben (albumban és személyalbumban
ilyenkor nem csinál semmit).

A kép helyi menüjében ugyanez a **Keresés a lemezen** (Ctrl+Enter). Ha
**egyetlen** képet jelöltél ki, és annak a program megőrizte a szerkesztés
előtti eredetijét, a tétel helyén **Keresés** almenü nyílik, két sorral:

- **Fájl a lemezen** (Ctrl+Enter) — a kép mappája a fájlkezelőben,
- **Eredeti a lemezen** — a szerkesztés előtti, megőrzött eredeti fájl.

Több kijelölt képnél, illetve ha nincs megőrzött eredeti, az almenü nem
nyílik ki: a lapos **Keresés a lemezen** marad. Ez az eredeti Picasa
viselkedése.

Album- és Emberek-nézetben áll alatta a **Keresés a Picasában** is: ez a
kép **saját mappájára** ugrik vissza. Mappanézetben nem jelenik meg, mert
ott a kép már a saját mappájában látszik.

A helyi menüben ezen kívül:

- **Fájl megnyitása** — a rendszer alapértelmezett programjával,
- **Társítás** - te választod ki, melyik programmal nyíljon meg a kép.
  Windowson ez egyetlen menütétel, és a rendszer saját „Megnyitás
  ezzel" ablakát hozza elő. Linuxon almenü nyílik: felül a képtípushoz
  társított programok állnak, egy kattintás abban nyitja meg a képet;
  alul a **Társítás...** tétel egy ablakot nyit, ahol ugyanezek közül
  választhatsz, és a **Megnyitás** gombbal indítod. Ha egyetlen program
  sincs a típushoz társítva, az almenüben csak a **Társítás...** áll, az
  ablak pedig ezt írja: „Ehhez a fájltípushoz nincs társított
  alkalmazás." (A néző helyi menüjének **Társítás** tétele még nem
  működik.)
- **Teljes elérési út másolása** — a vágólapra teszi az útvonalat.

## Mappák

- **Mappa ▸ Áthelyezés…** — az egész mappa átköltöztetése. Ha ez menet
  közben elakad (például egy olvashatatlan almappánál), a mappa a régi
  helyén marad, és a célban **nem marad félkész másolat**. Egyetlen olyan
  pillanat van, ami már nem fordítható vissza — ott a hibaüzenet megmondja,
  hol találod a tartalmat.
- **Mappa ▸ Törlés…** — a mappa törlése a lemezről. A program külön
  rákérdez, mert az almappákat is elviszi.
- **Mappa ▸ Eltávolítás a Picasából…** — a mappa csak a nézetből kerül
  ki, a fájlok maradnak. A program **Jóváhagyás** címmel rákérdez, és a
  kérdésben a mappa **teljes útvonala** áll. A két gomb a **Mappa
  eltávolítása** és a **Mégse**; a fókusz a **Mappa eltávolítása**
  gombon áll, tehát az Enter eltávolítja a mappát.
