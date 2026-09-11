# Fájlműveletek: átnevezés, áthelyezés, törlés

Ezek a parancsok a **lemezen lévő fájlokra** hatnak, nem csak a
nézetre. A PicasaPy minden ilyen műveletnél rákérdez.

## Átnevezés

**Fájl ▸ Átnevezés…** (F2), vagy a kép helyi menüjéből.

Írd be az új nevet. Több kép egyszerre is átnevezhető — ilyenkor a
program sorszámozza őket. A párbeszédben bekapcsolhatod, hogy a névbe
kerüljön bele a **Dátum** és a **Képfelbontás** is; alul példát mutat,
hogyan fog kinézni a kész név.

## Áthelyezés

- **Fájl ▸ Áthelyezés új mappába…** — a kijelölt képek új mappába
  kerülnek.
- A képeket **húzással** is átteheted egy másik mappára a bal hasábon.

A program megerősítést kér, és kiírja, hova viszi őket. Haladásjelző
mutatja, hányadik fájlnál tart.

Ha a célmappában már van azonos nevű fájl, választhatsz: **Másodpéldányok
átnevezése** (a bevitt fájlok új nevet kapnak) vagy **Másodpéldányok
kihagyása**.

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
nézőben **Ctrl+Delete**.

Ez a menüpont **attól függ, hol állsz**: album nézetében **Eltávolítás az
albumból**, egy Emberek albumban **Eltávolítás az Emberek albumból** a
felirata, és akkor csak az összeállításból veszi ki a képet — a fájlhoz
nem nyúl. Mappában áll a **Törlés lemezről** felirat, és ott tényleg
törli a fájlt.

A program megerősítést kér. A megerősítést a **Beállítások ▸ Általános**
lapon ki lehet kapcsolni („Törlés a lemezről megerősítés nélkül").

## Keresés a lemezen

**Fájl ▸ Keresés a lemezen** (Ctrl+Enter) megnyitja a fájlkezelőben azt
a mappát, ahol a kép van.

A kép helyi menüjében ezen kívül:

- **Fájl megnyitása** — a rendszer alapértelmezett programjával,
- **Teljes elérési út másolása** — a vágólapra teszi az útvonalat,
- **Eredeti a lemezen** — a szerkesztés előtti eredeti fájlhoz visz,
- **Keresés a Picasában** — a keresésből visszaugrik a kép saját
  mappájába.

## Mappák

- **Mappa ▸ Áthelyezés…** — az egész mappa átköltöztetése. Ha ez menet
  közben elakad (például egy olvashatatlan almappánál), a mappa a régi
  helyén marad, és a célban **nem marad félkész másolat**. Egyetlen olyan
  pillanat van, ami már nem fordítható vissza — ott a hibaüzenet megmondja,
  hol találod a tartalmat.
- **Mappa ▸ Törlés…** — a mappa törlése a lemezről. A program külön
  rákérdez, mert az almappákat is elviszi.
- **Mappa ▸ Eltávolítás a Picasából…** — a mappa csak a nézetből kerül
  ki, a fájlok maradnak.
