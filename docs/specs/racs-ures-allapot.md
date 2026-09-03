# A rács ÜRES ÁLLAPOTA (`thumbui/lightbox_bgtext`)

**Mi ez:** amikor a könyvtár rácsában nincs mit mutatni, a Picasa a rács
közepére **egyetlen sor szöveget** ír. Nem egy szöveg: **hét változat** van,
és a kód választ közülük — sőt az egyik változatnak **két megfogalmazása**
van, egy futásidejű kapcsolóval.

**A lap a MŰKÖDÉST írja le**, a geometria a végén áll. Kiváltó: a `thumbui`
UI-lefedettségi sor `lightbox_esolo_button`/`_text` tétele.

Testvérlapok: [`picasa-kereses-modok.md`](picasa-kereses-modok.md),
[`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md).

## 1. ⛔ A LEGFONTOSABB: a „Keresés mindenhol" gomb HALOTT

*Forrás: `thumbui.tre:208` (`thumbui/lightbox_esolo_button`) · `thumbui.tre:200` (`thumbui/lightbox_esolo_text`).*

A lefedettségi mérés két elemet jelölt hiányzónak:

| elem | felirat |
|---|---|
| `thumbui/lightbox_esolo_text` | *„No results found in this album"* — **„Nincs találat ebben az albumban"** |
| `thumbui/lightbox_esolo_button` | *„Search All"* — **„Keresés mindenhol"** |

A `thumbui.tre` a szándékot is leírja (195–198. sor):

```
#-----------------------------------------------------------
# Exit Solo - Shown when search in started from solo and
# no results are found
#-----------------------------------------------------------
```

**Ez a felület azonban SOHA NEM JELENIK MEG a 3.9-ben.** Mindkét elem
`m_hidden`, és semmi nem veszi le róluk:

| ellenőrzés | eredmény |
|---|---|
| nyers bájtkeresés a teljes `Picasa3.exe`-ben a `lightbox_esolo_text` mintára | **0 találat** |
| ugyanaz a `lightbox_esolo_button` mintára | **0 találat** |
| ugyanaz az `exit_solo` mintára (a réteg típusneve) | **0 találat** |
| `string_xrefs` a bináris indexben `%esolo%`-ra | **0 sor** |
| a `.tre`-korpusz egésze: `showtarget`/`hidetarget` a két elemre | **nincs** — csak a saját deklarációjuk és a feliratuk |

**Kontroll ugyanazzal a módszerrel:** a testvér `lightbox_bgtext` neve
**megtalálható** a binárisban (fájloffset `0x8a2a78`, VA `0x00ca2a70`), és
**három** függvény kéri le. Vagyis a mechanizmus **névalapú**, és épp ezért
a két `esolo` elem hiánya bizonyíték, nem mérési hézag.

⇒ **Nem szabad megépíteni „mert az eredetiben így van".** Az eredetiben
nincs így: megtervezték, felirattal együtt, és **bekötetlenül hagyták**.

## 2. Ami VAN: `lightbox_bgtext` — egy elem, HÉT szöveg

A `thumbui_text.tre` 4–23. sora (a `Text1`…`Text7` kulcsok a szövegtömb
elemei, **0-alapú** indexszel):

| index | kulcs | szöveg |
|---:|---|---|
| 0 | `Text1` | *No photos found* |
| 1 | `Text2` | *All Files are backed up in this set* |
| 2 | `Text3` | *No photos found for cd* |
| 3 | `Text4` | *All photos have been uploaded* |
| 4 | `Text5` | *All photos currently online have these settings* |
| 5 | `Text6` | *No photos can be removed from Picasa Web Albums* |
| 6 | `Text7` | *No photos can be removed from Google Photos* |

⚠️ **Nem hibaüzenetek.** A hétből **négy megnyugtató visszajelzés**
(„minden mentve", „minden feltöltve", „mindegyikre ez a beállítás áll") —
az üres rács itt **eredmény**, nem hiány.

### 2.1 A választó: `0x00676b10` (131 bájt) — utasításszinten

```
0x00676b11  mov ebx, [esp+8]              ; az ARGUMENTUM = a szöveg indexe
0x00676b17  mov edx, 0xca2a70             ; "thumbui/lightbox_bgtext"
0x00676b1c  call 0x9cd080                 ; elem-feloldás
0x00676b27  cmp ebx, 5                    ; ha az index 5 …
0x00676b2e  call 0x431290                 ;   … egy kapcsoló lekérdezése
0x00676b37  mov edi, 6                    ;   … igaz esetén 6 LESZ belőle
0x00676b3c  mov eax, [esi+0x300]          ; a szövegtömb hossza (>>1)
0x00676b44  cmp edi, eax / jae            ; TARTOMÁNY-ellenőrzés
0x00676b53  lea ecx, [eax + edi*4]        ; a tömb edi-edik eleme
0x00676b59  call vt[0x14]                 ; a felirat beállítása
--- és UGYANEBBEN a hívásban ---
0x00676b5b  mov edx, 0xca5c14             ; "publish/uploadallinfotext"
0x00676b6f  lea ecx, [ebx-3]              ; ANNAK az indexe = arg − 3
0x00676b89  call vt[0x14]
```

**Két szabály ebből:**

1. **Az 5-ös index KÉTFÉLE szöveget adhat.** A kapcsoló a `0x00431290`
   (205 bájt), ami a `Preferences\LastUserESState` kulcsot olvassa:
   igaz esetén az index **6**-ra vált ⇒ *„Picasa Web Albums"* helyett
   *„Google Photos"*. Ugyanaz az állapot, más megnevezéssel — a Google
   márkaváltása.
2. **Ugyanaz a hívás a feltöltés-panel infósorát is állítja**
   (`publish/uploadallinfotext`), **hárommal kisebb** indexszel. A két
   szövegtömb tehát *szinkronban* van tartva: a rács 3. szövege a panel
   0. szövegével egy párt alkot.

### 2.2 A hívók — a mért kontextusok

| hívó | méret | melyik index | mi ez |
|---|---:|---|---|
| `0x006706d0` | 2759 b | **3** (`push 3`, `0x006708a0`) | *„All photos have been uploaded"* — a feltöltés-ág |
| `0x00679ca0` | 6960 b | **számított** (`push edx`, `0x0067b285`) | a közzététel-panel; az index futásidőben áll elő |

A `lightbox_bgtext` elemnevet közvetlenül (a választó megkerülésével)
további két függvény kéri le: **`0x00662b20`** (a keresési fejléc-építő —
ugyanitt van a *„Search results for \"%s\""*, a `%d results:` és a
`CThumbUI::sresults`/`sfaces`/`sstarred`/`sonline`/`smovies` kulcs) és
**`0x0067be30`** (a CD-írás panel: `Picasa CD`, `publish/backupcdheader`,
`il_BurnPanel::*`). Ezek a `vt[0x68]`/`vt[0x6c]` rekeszt hívják — vagyis
**megjelenítés/elrejtés**, nem szövegváltás.

⇒ A felelősség szétválik: **a szöveget a `0x00676b10` állítja, a
láthatóságot a két kontextus-függvény kapcsolja.**

## 3. Geometria és stílus

| | |
|---|---|
| elem | `layer:thumbui/static(nothing): lightbox_bgtext` |
| tervezővászon | `430, 231 – 578, 251` = **148 × 20** |
| szülő | `thumbui/albumsback` (a rács háttere) |
| kötés (`thumbui.tre:190–193`) | `m_displayfont18_Reg`, **`m_centerXY`**, `m_hidden` |

⇒ **a rács területének pontos KÖZEPÉN**, 18 pontos „Regular" kijelző-betűvel.

*(A halott `esolo` pár ugyanennek a szülőnek a gyereke: a gomb
`m_centerXY` szintén középen, a szöveg `m_centerX` + `YConstraint .5, .5, 20`,
tehát 20 képponttal a középvonal alatt; a tervezővásznon a gomb
`430, 237 – 578, 259` = 148 × 22, a szöveg `430, 261 – 578, 281` = 148 × 20.
Ezt **nem építjük meg** — az 1. szakasz szerint halott.)*

## 4. Eredeti / nálunk / teendő

A „nálunk" oszlop **mérés**. ⚠️ A tábla a **#1945 megvalósítása után**
frissült — a korábbi állapot (`683883b1`, „nincs üzenet") már nem érvényes.

| | eredeti (mért) | nálunk (mért) | teendő |
|---|---|---|---|
| üres rács üzenete | **van**, a rács közepén, 18 pt | **van** — `gridEmptyText` a `LightboxFeed.qml`-ben, `anchors.centerIn`, `font.pointSize: 18` | ✅ kész (#1945) |
| hány szöveg | **hét** kontextus-változat | **egy**: a 0. index („No photos found" / „A program nem talált fotókat") | a maradék hat a webalbum-/CD-/mentés-ághoz tartozik, ami nálunk nincs |
| a márkaváltás | az 5. index **`LastUserESState`** szerint „Picasa Web Albums" vagy „Google Photos" | — | hatókörön kívül (webalbum-ág) |
| „Keresés mindenhol" gomb | **halott** az eredetiben | nincs | **NE épüljön meg** |

**Egy ponton TÖBBET adunk az eredetinél, szándékosan.** Az üzenet nálunk
akkor sem jelenik meg, ha a rács azért üres, mert **még fut a betöltés**
(`controller.isWorking`). Az eredetiben erre nincs mért kapu; nálunk a
mondat enélkül a betöltés alatt azt állítaná, hogy nincs kép — az a
**hazudó állapot** hibaosztálya (#1798).

**Mérés módja nálunk — a #1945 ELŐTT** (a lelet levezetése, történeti):
két lekérdezés-alak — `grep -rn 'No photos found\|Nincs találat\|emptyText'`
a QML/Python fán (**0 találat a rácsra**), és
`grep -rniE 'no (photos|results)|nincs (találat|kép)'` (3 találat, mind
**párbeszéd-hibaüzenet**: `create_controller.py:279`, `:344`,
`print_controller.py:340`) — **egyik sem a rács üres állapota**.

**A #1945 UTÁN** ugyanez a keresés a `LightboxFeed.qml` `gridEmptyText`
elemét is megtalálja; az őr-teszt:
`tests/app/qml_functional/test_ures_racs_uzenet_1945.py`.

## 5. Nyitott kérdések mérlege

`0 nyílt · 5 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| mit csinál a „Keresés mindenhol" gomb | **LEZÁRVA, NEGATÍV** — semmit: bekötetlen (1.) |
| mi jelenik meg helyette | **LEZÁRVA** — `lightbox_bgtext`, hét szöveggel (2.) |
| ki állítja a szöveget | **LEZÁRVA** — `0x00676b10`, indexszel (2.1) |
| miért két „nem távolítható el" szöveg | **LEZÁRVA** — `LastUserESState` (`0x00431290`) váltja a márkanevet (2.1) |
| hol és milyen betűvel jelenik meg | **LEZÁRVA** — a rács közepén, `m_displayfont18_Reg` (3.) |
| **melyik kontextus melyik indexet adja** | **BLOKKOLT** — a két közvetlen hívóból egy immediate (`push 3`), a másik **számított** (`0x0067b285`, `push edx`). Az olcsó lánc kimerült: a `.tre` nem mondja meg, a szövegtár sem, a sztring-xref a négy függvényt adja, és mind a négyet elolvastam. **Megszerzés:** a `0x00679ca0` (6960 b) közzététel-panel célzott dekompilációja. **A megvalósítást nem blokkolja:** a „nincs találat" ág az index **0**, az immediate-tel igazolt ág az index 3. |

## 6. Amit KIZÁRTAM

- **„a »Keresés mindenhol« gomb kis jegy értékű funkció"** — a
  `picasa-menu-parancsok-viselkedes.md` 51.4 így vette fel. **Megdőlt:**
  a gomb az eredetiben soha nem jelenik meg.
- **„a `lightbox_bgtext` egyetlen szöveg"** — hét van, és a hétből négy
  **megnyugtató**, nem hibaüzenet.
- **„a szöveget a megjelenítő kontextus írja"** — nem: külön választó
  függvény (`0x00676b10`) állítja, a kontextus csak mutat/rejt.

*Bizonyítottsági fok: **megerősített** a halott `esolo` párra (négy
lekérdezés-alak, plusz pozitív kontroll a testvér elemen), a hét szövegre,
a választó működésére és a `LastUserESState` kapcsolóra (utasításszinten
olvasva); **erős** arra, hogy nálunk nincs üres-állapot üzenet (két
lekérdezés-alak).*

---

Jegy: **#1945**.
