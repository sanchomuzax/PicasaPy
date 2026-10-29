# Feltöltés a Google Fotókba

A képtálca zöld **Feltöltés a Google Fotókba** gombja a tálcán lévő
képeket feltölti a saját Google Fotók-fiókodba.

Ez az egyetlen működő feltöltési út. A menükben lévő, hasonló nevű
tételek (például **Eszközök ▸ Feltöltés**) továbbra sem működnek, lásd
[Ami még nem érhető el](meg-nem-erheto-el.md).

## Mielőtt először feltöltesz: saját Google-kliens

Az eredeti Picasa a Google saját kapcsolatán át töltött fel; ez a
kapcsolat megszűnt. A PicasaPy ezért **a te saját Google-kliensedet**
használja. Ehhez a Google fejlesztői felületén egyszer létre kell hoznod
egy **asztali alkalmazás** típusú OAuth-klienst, és engedélyezned kell
hozzá a Google Fotók feltöltését. A Google ezután ad egy
**kliensazonosítót** és egy **klienstitkot**. Ezt a lépést a PicasaPy nem
tudja elvégezni helyetted.

Utána a PicasaPy-ban:

1. Nyisd meg az **Eszközök ▸ Beállítások…** ablakot, és válaszd a
   **Google Fotók** fület. Ha nem látszik, a fülsor jobb szélén lévő
   **›** nyíllal görgess oda.
2. Írd be az **OAuth-kliensazonosító** és az **OAuth-kliens titka**
   mezőbe a Google-tól kapott két értéket.
3. Kattints a **Mentés** gombra.
4. Kattints a **Bejelentkezés Google Fiókkal** gombra. Megnyílik a
   böngésződ; ott jelentkezz be, és engedélyezd a hozzáférést.
5. Ha sikerült, a fülön ez áll: **Bejelentkezve a Google Fotókba**.

A fül **Mentés** és **Bejelentkezés** gombja azonnal hat, nem kell hozzá
a Beállítások ablak **OK** gombja.

A klienstitkot és a bejelentkezést a program a rendszer kulcstartójában
tárolja, ha van ilyen, különben a felhasználói beállítások között. Ha
később csak a kliensazonosítót módosítod, a titok mezőjét üresen
hagyhatod: a mentett titok megmarad. Új kliensazonosítónál viszont újra
meg kell adnod a titkot, és újra be kell jelentkezned.

A **Kijelentkezés** gomb törli a mentett bejelentkezést. Ezután a
feltöltéshez újra be kell jelentkezned.

### Ha a bejelentkezés nem sikerül

A fül ilyenkor kiírja az okát:

- **Adja meg az érvényes OAuth-kliensazonosítót és -titkot.** - valamelyik
  mező üres vagy hibás.
- **Nem sikerült megnyitni az alapértelmezett böngészőt.** - állíts be
  alapértelmezett böngészőt a rendszeredben.
- **A bejelentkezés megszakadt.** vagy **A bejelentkezés időtúllépés
  miatt leállt. Próbálja újra.** - a böngészőben nem fejeződött be a
  bejelentkezés; kezdd újra.
- **A Google-bejelentkezés nem sikerült. Ellenőrizze az OAuth-kliens
  beállításait.** - a Google nem fogadta el a klienst; nézd meg, hogy
  asztali alkalmazás típusú-e, és engedélyezve van-e rajta a Google Fotók.

## Feltöltés

1. Tedd a feltöltendő képeket a képtálcára (lásd
   [A könyvtár](konyvtar.md)).
2. Kattints a tálca zöld **Feltöltés a Google Fotókba** gombjára.

A gomb szürke, ha nem vagy bejelentkezve, ha üres a tálca, vagy ha már
fut egy feltöltés.

A program **a tálca összes képét** feltölti, nem csak a tálcán
kijelölteket. Egy kis ablak mutatja, hol tart (például **Fotó
előkészítése: 2/5**, **A(z) kep.jpg feltöltése**), alatta egy
folyamatjelzővel. A **Mégse** gomb leállítja a feltöltést; ha végzett,
**A feltöltés befejeződött** felirat jelenik meg, és a gomb **Bezárás**
lesz.

### Mit tölt fel pontosan

- A képek a Google Fotók könyvtáradba kerülnek, **nem albumba**, és
  felirat nélkül, a fájl nevével.
- Ha egy kép hosszabbik oldala **1600 képpontnál** nagyobb, a program
  feltöltés előtt erre kicsinyíti. A kisebb képek változatlanul mennek
  fel.
- A program a **lemezen lévő fájlt** tölti fel. Ha egy képen olyan
  szerkesztés van, amit még nem mentettél el, azt előbb mentsd el
  (**Fájl ▸ Mentés**), ha a szerkesztett változatot szeretnéd feltölteni.

### Ha a feltöltés nem sikerül

Az ablak kiírja az okát, és ha egy adott kép akadt el, annak nevét is
(**Nem sikerült a(z) … feltöltése**). A gyakori üzenetek:

- **Hálózati hiba. Ellenőrizze a kapcsolatot, és próbálja újra.**
- **A Google Fotókba való bejelentkezés lejárt. Jelentkezzen be újra.**
  - a Beállítások **Google Fotók** fülén jelentkezz be ismét.
- **Túllépte a maximális feltöltési sebességet** - a Google egy időre
  korlátozta a feltöltést; várj, és próbáld később.
- **A Google Fotók átmenetileg nem érhető el** - próbáld később.
- **Egy fotót nem sikerült előkészíteni a feltöltéshez.** - a fájl sérült,
  vagy nem kép.
- **Ez a fotó túl nagy a feltöltéshez.**
- **Nincs fotó a Fotótálcán.**

## Kapcsolódó

- [A könyvtár és a képtálca](konyvtar.md)
- [Beállítások](beallitasok.md)
- [Ami még nem érhető el](meg-nem-erheto-el.md)
