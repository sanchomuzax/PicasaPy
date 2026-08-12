# ADR-002: Offline (jelenleg nem elérhető) mappa kezelése

Dátum: 2026-08-12 · Státusz: ELFOGADVA · jegy: #459 (5. pont)

## A helyzet

A felhasználó képei **NAS-on** vannak. Ott mindennapos, hogy egy megosztás
épp nincs csatolva, egy lemez ki van húzva, egy mount lehal.

Az **eredeti Picasáról nem derült ki**, mit tett ilyenkor: a
`Picasa3i18n.dll` sztring-erőforrásában **nincs egyetlen üzenet sem** a nem
elérhető mappára. A `runtime/missing.jpg` helyettesítő kép létezik, de a
felhasználási helye sem azonosítható. Ez tehát **nem másolható viselkedés**,
hanem a mi saját döntésünk — ezért kap külön ADR-t.

## A döntés

**Az offline mappa bennmarad az indexben.** A mappa sora és a fotó-sorai
sértetlenül megmaradnak (stabil rekord-id-kkel), a bélyegképek a
gyorsítótárból látszanak. A mappa `offline = 1` jelölést kap
(`folders.offline`, séma v11), a bal hasábon dőlt és halvány sorként jelenik
meg, súgószöveggel. A mappára lépéskor a program **kimondja**, mi a helyzet
(borostyán tájékoztató sáv a piros hibasáv helyett) — a jegy negatív
példájának (néma bukás) az ellentéte.

A jelölés **magától elmúlik**: az első sikeres scan `offline = 0`-ra állítja
a mappát. A NAS visszatérése után tehát nincs teendő, és nincs órákig tartó
teljes újraépítés sem.

## Hogyan ismerjük fel az offline mappát

Ez a döntés lényegi része, mert **nincs rá közvetlen jel**: a levált
NAS-mount üres könyvtárként van jelen, a `scandir` simán lefut rá.

A `picasapy.index.sync.folder_looks_offline` szűk, szándékosan konzervatív
szabálya — csak olyan mappára fut, amelyet a mostani scan nem látott, **és
amelyhez van fotó az indexben**:

| a mappa útvonala most | döntés |
|---|---|
| `scandir` hibára fut (ESTALE/EIO/EACCES/ENOTCONN) | **offline** |
| létezik, de **nulla bejegyzés** van benne | **offline** |
| létezik, és van benne bármi (csak média nincs) | takarítható |
| nem létezik | takarítható |

A második sor a lényeg: a levált mount pontosan így néz ki, míg a
felhasználó által **kiürített** fotómappában rendszerint ott marad legalább
a `.picasa.ini` vagy más fájl.

Ez a #132 gyökér-szintű védelmének a **mappa-szintű párja**. A #132 csak a
gyökeret óvta; egy mélyebben lévő, leváló mappa fotói eddig némán kiestek az
indexből (`_prune_folders`, illetve a watcher-ágon `_remove_folder`).

## A vállalt tévedés-irány

A szabály tévedhet: egy **teljesen üresre törölt** (még `.picasa.ini`-t sem
tartalmazó) mappa offline jelölést kap, ahelyett hogy eltűnne a listából.

Ezt vállaljuk, mert a másik irányú tévedés **adatvesztés**: egy levált NAS
teljes fotó-készlete (és vele a stabil id-kre épülő albumtagságok,
arccímkék, hasonlósági gyorsítótár) esne ki az indexből. A rossz irányban
tévedve a felhasználó egy fölösleges, üres sort lát, amit a Mappakezelő
→ „Eltávolítás a Picasából" pontjával bármikor eltüntethet — a jó irányban
tévedve órákig tartó újraépítés és elveszett metaadat lenne a következmény.

## Amit NEM csinálunk

- **Nem próbáljuk automatikusan újracsatolni** a megosztást. A mount a
  rendszer dolga; a program csak észleli és jelzi az állapotot.
- **Nem tiltjuk le** az offline mappa megnyitását: a bélyegképek a
  gyorsítótárból nézhetők. Csak az eredeti fájlt igénylő műveletek buknak —
  azok viszont üzenettel, nem némán.
- **Nem törlünk semmit automatikusan.** A végleges eltávolítás mindig
  explicit felhasználói művelet marad.
