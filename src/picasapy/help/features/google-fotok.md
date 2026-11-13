# Feltöltés a Google Fotókba

A képeidet a saját Google Fotók-fiókodba töltheted fel. Négy helyről
indíthatod:

- a képtálca zöld **Feltöltés a Google Fotókba** gombjával (a tálca
  képei),
- a bal hasábon egy **mappa** helyi menüjének **Feltöltés a Google
  Fotókba...** tételével (a mappa összes képe),
- a bal hasábon egy saját **album** helyi menüjének **Feltöltés a Google
  Fotókba...** tételével (az album összes képe),
- a rácsban a mappa fejlécének **Feltöltés** gombjával (a mappa összes
  képe, lásd [A könyvtár](konyvtar.md)).

A menükben lévő többi, hasonló nevű tétel (például **Eszközök ▸
Feltöltés**, vagy a **Legutóbb frissítve** album helyi menüjének
feltöltési tétele) nem működik, lásd
[Ami még nem érhető el](meg-nem-erheto-el.md).

## Bejelentkezés

A bejelentkezéshez kattints a menüsor jobb szélén a **Bejelentkezés
Google Fiókkal** feliratra. Megnyílik a böngésző; jelentkezz be, és
hagyd jóvá a hozzáférést. A bejelentkezés után a felirat helyén három
elem áll, függőleges vonallal elválasztva:

- a Google-fiókod e-mail-címe (erre nem lehet kattintani; ha a
  bejelentkezés még egy korábbi verzióból maradt, helyette **Bejelentkezve
  a Google Fotókba** áll),
- **Google Fotók**: a böngészőben megnyitja a Google Fotók oldalát,
- **Kijelentkezés**: törli a mentett bejelentkezést.

Ha a PicasaPy csomag nem tartalmaz beépített Google-klienst, a feliratra
kattintva egy rövid üzenet jelzi: **A Google-bejelentkezés ebben a
változatban még nem érhető el.** Az **OK** bezárja. A **Beállítások ▸
Google Fotók** fül bejelentkezési gombja ugyanazt a beépített klienst
használja.

A fülön az **Adatvédelmi tájékoztató** és a **Felhasználási feltételek**
hivatkozás is ott áll; a böngészőben nyílnak meg.

## Speciális: saját Google-kliens

A legtöbb felhasználónak nem kell saját Google-klienst beállítania. Ha
haladó felhasználóként mégis sajátot használnál, nyisd meg a **Beállítások
▸ Google Fotók** fület, és bontsd ki a **Speciális: saját Google-kliens
(nem kötelező)** részt. Add meg az OAuth-kliensazonosítót és a kliens
titkos kulcsát, majd kattints a **Mentés** gombra. Ezután a fül vagy a
menüsor bejelentkezési gombjával indíthatod a bejelentkezést.

A saját klienshez a Google fejlesztői felületén **asztali alkalmazás**
típusú OAuth-klienst kell létrehoznod, és engedélyezned kell rajta a
Google Fotók feltöltését. A két értéket a Google adja. A beépített
PicasaPy-kliens csomagolt változatban nem igényel saját beállítást.
Forrásból indított futtatáskor a beépített kliens a
`PICASAPY_GOOGLE_CLIENT_ID` és `PICASAPY_GOOGLE_CLIENT_SECRET`
környezeti változókkal érhető el.

A kliens titkos kulcsát és a bejelentkezést a program a rendszer
kulcstartójában tárolja, ha van ilyen, különben a felhasználói
beállítások között. Ha később csak a kliensazonosítót módosítod, a
titok mezőjét üresen hagyhatod: a mentett titok megmarad. Új
kliensazonosítónál viszont újra meg kell adnod a titkot, és újra be kell
jelentkezned.

A **Kijelentkezés** művelet törli a mentett bejelentkezést. Ezután a
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

A gomb szürke, ha üres a tálca, vagy ha már fut egy feltöltés vagy
bejelentkezés. Ha még nem vagy bejelentkezve, a gomb először a
bejelentkezést indítja el a böngészőben (lásd fent), és a sikeres
bejelentkezés után magától folytatja a feltöltést. Ugyanígy működik a
mappa- és albummenü, valamint a mappa fejlécének **Feltöltés** gombja
is.

Mappából vagy albumból indítva a program a mappa, illetve az album
**összes** képét feltölti, a kijelöléstől függetlenül.

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
