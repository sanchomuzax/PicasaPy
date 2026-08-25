# A Nézet ▸ Mappanézet menü — a bal hasáb GYÖKERE és HIERARCHIÁJA

*Picasa 3.9.141.259, mérve 2026-08-25. Minden állítás mellett cím
(image base `0x400000`) vagy fájl+sor.*

> **Ez a lap egy funkcionális félreértést javít.** A `Nézet ▸ Mappanézet`
> **nem rendezés**. Nem azonos sem az indexképek helyi menüjének „Mappa
> rendezésének alapja", sem a `Mappa ▸ Rendezés` almenüjével. Azt szabja
> meg, hogy a bal hasáb **melyik gyökérből** és **milyen szerkezetben**
> mutatja a mappákat.

---

## 1. MIT AD MA a PicasaPy

| | |
|---|---|
| `PicasaMenuBar.qml:408` | a mi „Folder View" almenünk **öt rendezési tétel**: *Sort by creation date · recent changes · size · name · Reverse sort* |
| `PicasaMenuBar.qml:456` | a `Mappa ▸ Sort By` almenü **MEGEGYEZŐ bekötéssel** — ugyanaz az öt tétel, ugyanaz a `folderSort` |
| `folder_photo_sort_controller.py:13` | a kód is így dokumentálja: *„`folderSort` (#321) — a MAPPÁK sorrendjét — Nézet ▸ Mappanézet"* |
| `FolderHierarchyView.qml:8` | van lapos↔fa kapcsolónk (**kettő** mód) |
| `folder_hierarchy_controller.py:69` | van `simplified` property… |
| **mérve** | **…de a `simplified` sehol nincs bekötve QML-ben** (`grep -rn "simplified" src/picasapy/app/qml/` → **0 találat**) |
| `FolderListContextMenu.qml:101` | „&Simplified Tree View" — `placeholder: true`, azaz **halott** |
| gyökérválasztás | **nincs** ilyen fogalmunk |

**Egy mondatban: a mi „Mappanézet" menünk a `Mappa ▸ Rendezés` másolata,
az eredeti Mappanézet funkciójából pedig egyetlen elem sem érhető el
menüből.**

---

## 2. Az eredeti szerkezete — HÁROM menütétel és HAT parancs

### 2.1 A menüsáv `Nézet ▸ Mappanézet` almenüje (3 tétel)

| parancs | angol | magyar | típus |
|---|---|---|---|
| `ID_VIEW_FOLDERS` | &Flat Folder View | Egyszerű mappanézet | rádió |
| `ID_VIEW_ALL` | &Tree View | Fanézet | rádió |
| `ID_VIEW_WATCHED` | &Simplified Tree View | Egyszerűsített fanézet | **külön pipa** |

### 2.2 A mappa-hasáb helyi menüje — `thumbui/folderviewpopup` (`0x00733480`)

Ugyanez a funkció **másik belépési ponton**, négy további tétellel.
⚠️ Ezek közül **csak a Sajátgép valódi gyökér** — a másik három a teljes
fára vált, majd odaugrik; ld. **4.5/b**.

| parancs | felirat | magyar |
|---|---|---|
| `eMenuViewWin::ID_VIEW_MYCOMPUTER` | My &Computer | Sajátgép |
| `eMenuViewWin::ID_VIEW_MYPICTURES` | My &Pictures | Képek |
| `eMenuViewWin::ID_VIEW_MYDOCS` | My Do&cuments | Dokumentumok |
| `eMenuView::ID_VIEW_DESKTOP` | &Desktop | Asztal |
| `AlbumList::ID_VIEW_WATCHED` | &Simplified Tree View | Egyszerűsített fanézet |
| `AlbumList::ID_VIEW_THUMBNAILS` | Show &Thumbnails in Library | *(külön funkció)* |

---

## 3. ⛔ A LEGFONTOSABB LELET: ez NEM háromállású rádiógomb

A pipa-frissítő `0x00574b70` bizonyítja, hogy **kettő + egy** van, nem három:

```
0x00574c3d  mov al, [edx+0x9d]   ; neg/sbb/and 0xfffffff8/add 8
0x00574c4e  push 0x9db6          ; PIPÁS, ha [+0x9d] == 0
0x00574c5c  mov dl, [ecx+0x9d]   ; neg/sbb/and 8
0x00574c6a  push 0x9db9          ; PIPÁS, ha [+0x9d] != 0
0x00574c72  push "SimplifiedHierarchy" → 0x407a20
0x00574ca5  push 0x9db8          ; PIPÁS, ha SimplifiedHierarchy igaz
```

- **`0x9db6` = Egyszerű mappanézet**, **`0x9db9` = Fanézet** — egyetlen
  bájt (`[+0x9d]`) két állapota, azaz **kizáró pár**.
- **`0x9db8` = Egyszerűsített fanézet** — a pipája **`[+0x9d]`-től
  FÜGGETLEN**: önálló, tartós ki-be kapcsoló.

*(A `[+0x9d]` jelentése mérve: `0x575130` a `"flat"` ágban
`[esp+0x14]=0`-t tesz (`0x005752e4`), minden más ágban 1 az alapérték
(`0x0057529f`), és a végén `[eax+0x9d] = [esp+0x14]` (`0x00575593`).
Tehát **`[+0x9d]` = „hierarchikus"**.)*

> **Ez a három parancsazonosító az EGYETLEN, amit kiadok.** Nem a
> menüépítő rekordsorrendjéből vezettem le — az a leképezés kétszer
> megbukott (`picasa-menu-parancsok-viselkedes.md`) —, hanem a pipa-kód
> **jelentéstani horgonyából**. A négy gyökér numerikus azonosítóját
> szándékosan **nem** adom meg: nekünk nincs Win32 parancsazonosítónk.

---

## 4. A mechanizmus — `0x00575130` (1332 b), a nézetalkalmazó

Egyetlen függvény kapja meg a **gyökér-tokent** és mindent elvégez.
A hat token: **`flat` · `all` · `watched` · `mypics` · `mydocs` ·
`desktop`** *(a `0x004aea10` feloldója további kettőt ismer — `myvids`,
`mymusic` —, ezek a menüből nem érhetők el)*.

### 4.1 Az „Egyszerűsített fanézet" MEGFEJTÉSE

```
0x0057517c  cmp ebp, "all"                 ; csak az „all" gyökérnél
0x00575194  push "SimplifiedHierarchy"
0x0057519b  push "Preferences"
0x005751af  call 0x407a20                  ; beállítás-olvasó
0x005751e5  cmp byte [esp+0x1f], 0
0x005751ec  mov ebp, "watched"             ; ⇐ A GYÖKÉR KICSERÉLŐDIK
```

**`SimplifiedHierarchy = 1` esetén az `all` gyökér `watched`-re
cserélődik.** Vagyis az „egyszerűsített" fa nem a teljes gépet mutatja,
hanem **csak a figyelt mappák ágait**. Ez nem a fa tömörítése — ez a fa
**hatókörének** szűkítése.

⚠️ **Nálunk `folder_hierarchy.py:119` `_simplify()` mást csinál:** az
egygyermekes köztes csomópontokat vonja össze (útvonal-tömörítés). A
látvány hasonló lehet, a **mechanizmus más**, és a hatóköre is: a mi
verziónk sosem rejt el mappát, az eredeti igen.

### 4.2 A hasáb fejlécének felirata

| gyökér | token | felirat (EN / HU) |
|---|---|---|
| `flat` | `ViewRoot::AllFolders` | Default View / **Alapértelmezett nézet** |
| `all`, `watched` | `ViewRoot::All` | My Computer / **Sajátgép** |

*(`0x005752e9`, `0x0057535e`; a feliratok: `stringres-en-hu.tsv` 2429–2430.)*

### 4.3 Mit ír, mikor

| | |
|---|---|
| **azonnal, kapcsoláskor** | `Preferences\SimplifiedHierarchy` (`0x005cc63f`: olvas → `neg/sbb/add 1` = logikai tagadás → visszaír) |
| **kilépéskor** | `Preferences\LastViewRoot` és `\LastViewRoot2` — a `0x00576660` (457 b) írja a `LastAlbumSelected`-del együtt, a `0x00407630` beállítás-íróval; hívó: `0x0057c4e0` |
| **indulásnál** | ugyanez a három kulcs olvasódik vissza: `0x0040d3c0` (513–531. sor) |
| **lemez / adatbázis** | **semmi** — nincs újraindexelés, nincs `.picasa.ini`-írás |

*(Két gyökér-rekesz van (`[+0x2e0]`, `[+0x2f0]`); melyik mit takar, az
Win32 registry-részlet, a mi tárolásunkra nézve közömbös — ld. 8. pont.)*

### 4.4 Mi fut le a váltás után (`0x005755a0`–`0x005755e3`)

1. `[+0x166] = 1`, `[+0x174] = 1` — piszkos jelzők
2. `0x006dc190` → **újratördelés**
3. `0x0065b840(obj, 0, 0, 1)` — **a lista újraépítése**
4. a görgetés megőrzése: `[+0x30c] = [+0x320] + [+0x2f8]`
5. `0x00574b70` — a menüpipák frissítése

**A váltás azonnali és olcsó** — nincs folyamatjelző, nincs háttérszál.

### 4.5 A három érintett felületi vezérlő

| vezérlő | hívás | mikor aktív |
|---|---|---|
| `thumbui/folderview` | `0x9cd8f0` | mindig (a gyökérválasztó legördülő) |
| `thumbui/flatview` | `0x9cd8f0`, paraméter = `[esp+0x14]==0` | **csak lapos módban** |
| `thumbui/soloview` | `0x9cd9a0` | az eredménye a `[+0x9c]` mezőbe megy |
| `thumbui/folderviewpopup` | `0x9cd080` | a helyi menü |

### 4.5/b ⚠️ HELYESBÍTÉS: a három rendszermappa NEM önálló gyökér

*(Utólagos mérés, 2026-08-25 — a 2.2 szakasz „négy gyökér" megfogalmazása
ezt félrevezetően sugallta.)*

A `mypics` / `mydocs` / `desktop` ág mindegyike **azonos alakú**:

```
push 2 · push "all" · call 0x575130   ; ⇐ ELŐBB átvált a TELJES fára
push <kimenet> · call <rendszermappa-feloldó>
```

*(`0x005753b2`–`0x005753d4`, `0x0057540b`–`0x0057542d`,
`0x00575461`–`0x0057547e`.)*

⇒ **Csak KÉT valódi gyökér van: `flat` és `all`** *(plusz az `all`
`watched`-re cserélt változata)*. A három rendszermappa-tétel a **teljes
fára vált, majd felfedi és kijelöli** azt a mappát. A `[+0x2e0]`/`[+0x2f0]`
rekesz viszont a `mypics`/`mydocs`/`desktop` tokent tárolja — ezért kapnak
a helyi menüben mégis rádiógomb-pipát.

**A feloldók és a CSIDL-jük** — az érték a `0x00996140` hívása előtt:

| token | függvény | CSIDL | Linux-megfelelő |
|---|---|---|---|
| `mypics` | `0x009966a0` | **`0x27`** `CSIDL_MYPICTURES` | `XDG_PICTURES_DIR` |
| `mydocs` | `0x00996230` | **`0x05`** `CSIDL_PERSONAL` | `XDG_DOCUMENTS_DIR` |
| `desktop` | `0x00996b90` | **`0x00`** `CSIDL_DESKTOP` | `XDG_DESKTOP_DIR` |

A `mypics` feloldó **maga is visszaesik** a Dokumentumokra, ha a Képek
mappa nem oldható fel (`0x00996747  call 0x996230`).

### 4.5/c A fejlécfelirat — csak KETTŐ rögzített van

Mindkét ág ugyanabba a felirat-beállítóba (`0x005c2100`) fut, de mást ad neki:

| eset | mi kerül a fejlécbe |
|---|---|
| `flat` | **rögzített** erőforrás-szöveg: „Alapértelmezett nézet" |
| `all`, `watched` | **rögzített** erőforrás-szöveg: „Sajátgép" |
| `mypics`, `mydocs`, `desktop` | **a feloldott mappa saját útvonala/neve** (`0x00575483  mov esi, eax`) — nincs hozzá erőforrás-szöveg |

Ezért van a `stringres`-ben pontosan **két** `ViewRoot::` kulcs, és nem öt.

### 4.6 Hibaeset

A `0x00575130` a `mypics` / `mydocs` / `desktop` gyökereket a Windows
mappa-feloldóin át kéri le (`0x009966a0`, `0x00996230`, `0x00996b90`), és
**önmagát hívja újra `"all"` gyökérrel**, ha a feloldás nem ad útvonalat
(`0x005753bd`, `0x00575416`, `0x0057546c`). Vagyis a **hibakezelés
visszaesés a Sajátgép-gyökérre**, nem hibaüzenet.

---

## 5. Eredeti / nálunk / teendő

| # | eredeti | nálunk MA | teendő |
|---:|---|---|---|
| 1 | `Nézet ▸ Mappanézet` = 3 szerkezeti tétel | **5 rendezési tétel** (a `Mappa ▸ Rendezés` másolata) | a rendezést ki a Mappanézetből |
| 2 | Egyszerű ↔ Fa: kizáró pár | megvan (`FolderHierarchyView`) | menübe kötni |
| 3 | Egyszerűsített fanézet: **külön, tartós kapcsoló** | `simplified` property **nincs bekötve** | bekötni + tartóssá tenni |
| 4 | „egyszerűsített" = a gyökér `all`→`watched` | `_simplify()` = útvonal-tömörítés | a szemantikát a mérthez igazítani |
| 5 | 4 gyökér a helyi menüben | **nincs** gyökér-fogalom | megépíteni |
| 6 | fejléc: „Alapértelmezett nézet" / „Sajátgép" | nincs | megjeleníteni |
| 7 | `SimplifiedHierarchy` azonnal tárolódik | nincs tárolva | beállításba |
| 8 | a gyökér kilépéskor tárolódik | nincs tárolva | beállításba |
| 9 | a helyi menü tétele élő | `placeholder: true` | élővé tenni |

---

## 6. Kész, ha

- [ ] A `Nézet ▸ Mappanézet` almenü **három** tételt tartalmaz: Egyszerű
      mappanézet · Fanézet · Egyszerűsített fanézet — és **egyetlen
      rendezési tételt sem**.
- [ ] Az első kettő **kizáró pár**, a harmadik **független pipa**.
- [ ] A rendezés kizárólag a `Mappa ▸ Rendezés` és az indexkép-helyimenü
      alatt marad.
- [ ] Az Egyszerűsített fanézet **elrejti a nem figyelt ágakat**.
- [ ] A mappa-hasáb helyi menüje kínálja a négy gyökeret, és élő.
- [ ] A hasáb fejléce „Alapértelmezett nézet", illetve „Sajátgép".
- [ ] Mindhárom állapot **túléli az újraindítást**.
- [ ] A váltás **nem** indít újraindexelést, és megőrzi a görgetést.

---

## 7. Bizonyítottsági fok

**Megerősített**: a menütételek és feliratok; a kettő+egy szerkezet
(`0x00574b70`); a `SimplifiedHierarchy` gyökércseréje (`0x0057517c`–
`0x005751ec`); a hat gyökér-token és a hozzájuk tartozó kezelők
(`0x005cc62c`–`0x005cc6e4`); a fejlécfeliratok; a `LastViewRoot`/
`LastViewRoot2` mentés és visszatöltés; az azonnali, indexelés nélküli
frissítés.

**Erős, nem mért**: hogy a `watched` gyökér pontosan mely ágakat rajzolja
(a rajzolás a `0x004b6190` `CAlbumState::Folders`-ében van, 7518 b —
nem bontottam ki).

**Elvetve**: hogy a Mappanézet rendezés lenne; hogy három egyenrangú mód
lenne (a #1407 eredeti címe így szólt); hogy az „egyszerűsített" a fa
tömörítése lenne.

---

## 8. Nyitott kérdések mérlege

| kérdés | állapot |
|---|---|
| Mit csinál a Mappanézet három tétele? | **LEZÁRVA** — 2–4. szakasz |
| Hány gyökér van, és honnan érhetők el? | **LEZÁRVA** — 2.2, 4. |
| Mit ír, mikor, hova? | **LEZÁRVA** — 4.3 |
| Mi fut le utána? | **LEZÁRVA** — 4.4 |
| Hibaeset? | **LEZÁRVA** — 4.6 |
| Induláskori állapot? | **LEZÁRVA** — 4.3 |
| `LastViewRoot` vs `LastViewRoot2` szerepe | **HATÓKÖRÖN KÍVÜL** — Win32 registry-részlet; nálunk egyetlen saját beállítás tárolja a gyökeret, a kettéosztás nem reprodukálandó |
| A `watched` gyökér pontos ágválogatása | **LEZÁRVA mint erős állítás**, a rajzoló kibontása külön jegy tárgya (#1407) |

```
Nyitott kérdések: 0 nyílt · 7 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

## 9. Amit KIZÁRTAM

- **A menüépítő rekordsorrendjéből NEM vezettem le parancsazonosítót.**
  Az a leképezés kétszer megbukott; a három kiadott azonosító a pipa-kód
  jelentéstani horgonyából jön.
- **`thumbui/soloview`**: a Mappanézet frissíti, de a szerepe nem
  következik a mért kódból — nem állítok róla semmit.
