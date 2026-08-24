# A Képtálca (Picture Tray / „Selection") — MŰKÖDÉS-spec

*Kutatói kör: 2026-08-24. Jegy: **#455** (a Klipek fül, **#1153**, erre épül).*

A Picasa alsó sávjának bal oldalán ülő **gyűjtő-munkaterület**. Belső neve
**`scratch`**, a felületen megjelenő felirata **„Selection"**. Ez a lap a
**működést** írja le; a látvány a `design-guide.md`-ben van.

---

## 1. ⭐ A LEGFONTOSABB LELET: a tálca NEM MARAD MEG újraindítás után

Három független ellenőrzés, mind negatív:

| amit kerestem | hol | eredmény |
|---|---|---|
| `]scratch` (vagy bármi tálca-szerű) token | a felhasználó **valódi** `albumdata_token.pmp`-ja, **2371 sor** | **nincs.** Pontosan **hét** nem-`]album:` token létezik: `]star`, `]screensaver`, `]updated`, `]history:email`, `]history:upload`, `]unknownface`, `]search` |
| tálca-fájl | a valódi `Picasa2` profilmappa | **nincs** — csak `cache`, `db3`, `ioqueue`, `runtime`, `tmp` és két naplófájl |
| `Preferences\…` kulcs | a bináris teljes sztringtára | **nincs** tálca/hold/scratch témájú kulcs |

> ⛔ **A tálca tartalma memóriában él, és a program bezárásával elvész.**
> Ha a PicasaPy megőrizné, az **eltérés** lenne, nem javítás.

*Bizonyítottsági fok: **erős**. A hét token felsorolása és a profilmappa
tartalma megerősített (mért), a „nincs máshol" negatívum a sztringtár
teljességén áll.*

---

## 2. A vezérlők — és amiben a #455 leírása PONTATLAN

A `.tre` szerint a tálca **négy** vezérlőt hordoz. **A gombokon NINCS
felirat**: a `.tre`-ben a `#Label` sorok **ki vannak kommentezve**, tehát
ikon + súgóbuborék az egész.

| elem | `.tre` azonosító | felirat | súgó (EN) | súgó (HU) |
|---|---|---|---|---|
| a sáv címkéje | `thumbui/scratchlabel` | **„Selection"** (`Text`, 14-es font, középre) | — | — |
| megtartás | `thumbui/scratchhold` | **nincs** (kikommentezve) | *Hold selected items* | — |
| ürítés | `thumbui/scratchclear` | **nincs** (kikommentezve) | *Clear items from the selection* | — |
| albumhoz adás | `thumbui/addtobuttcon` | **nincs** (kikommentezve) | *Add selected items to an Album* | — |

⚠️ A **#455 „Kijelölés megtartása" / „Kijelölés eltávolítása" gombfeliratot**
említ. Ezek **nem gombfeliratok**, hanem a `Tray` **helyi menü** két
parancsának feliratai (ld. 3.).

### 2.1 Geometria — kényszerekből, nem respackből

A tálca dobozát a `.tre` kényszerei adják (a respackben csak az **ikonok**
vannak: `scratchhold_icon` 468 b, `scratchclear_icon` 593 b,
`addto_arrow` 53 b, `#holdadorner` 438 b):

```
thumbui/scratchback : thumbui/basecontrolset   m_offsetB
    XConstraint 0, 0,    5        ; balról 5 px
    XConstraint 1, .365, -15      ; az alsó sáv szélességének 36,5%-áig, −15 px
thumbui/scratch     : thumbui/scratchback      ; a bélyegkép-sáv
    XConstraint 0,0,5 · XConstraint 1,1,-50    ; jobbról 50 px HELY A KÉT GOMBNAK
    YConstraint 0,0,5 · YConstraint 1,1,-5
thumbui/scratchhold , thumbui/scratchclear : thumbui/scratchback
    m_buttontypecolor · m_offsetRT             ; jobb-felső horgony
thumbui/scratchpadbase : thumbui/scratchback   m_offsetLRB
thumbui/scratchlabel   : thumbui/scratchpadbase  m_displayfont14 · m_centerXY
```

⇒ **A tálca az alsó sáv bal 36,5%-át foglalja el**, és a jobb szélén 50 px
van fenntartva a két ikongombnak.

---

## 3. A `Tray` helyi menü — PONTOSAN két parancs

| parancs | EN | HU |
|---|---|---|
| `Tray::ID_PICTURE_HOLDINPICTURETRAY` | *&Hold Selection* | **Kijelölés &megtartása** |
| `Tray::ID_REMOVE_SELECTION` | *&Remove Selection* | **Kijelölés &eltávolítása** |

A `Tray::` névtérben **több parancs nincs** a szövegtárban.

---

## 4. A KÉT — egymástól különböző — ürítés-megerősítés

A #455 egyet említ; **kettő van**, más szöveggel és más gombokkal:

### 4.1 Teljes ürítés

| kulcs | EN | HU |
|---|---|---|
| `IDS_CLEARTRAY` | *This will clear your entire tray. Are you sure you want to do this?* | **Ezzel a művelettel a teljes tálcát kiüríti. Biztosan ezt szeretné tenni?** |
| `IDS_CLEARTRAY_YES_BUTTON` | *Clear Tray* | **Törlés a tálcáról** |

### 4.2 A RÉGÓTA tartott elemek ürítése

| kulcs | EN | HU |
|---|---|---|
| `il_ClearFromTray` | *Would you like to clear your old held items from the tray?* | **El szeretné távolítani a tálcán régóta tárolt elemeket?** |
| `il_ClearFromTrayYesButton` | *Clear Tray* | **Törlés a tálcáról** |
| `il_ClearFromTrayNoButton` | *Don't Clear* | **Törlés mellőzése** |

⇒ A 4.2 **nem** a Törlés gomb megerősítése, hanem egy külön, **felkínált**
takarítás („régóta tartott" elemekre). A kettőt nem szabad összevonni.

## 5. Az őrfeltétel üzenete

| kulcs | EN | HU |
|---|---|---|
| `IDS_MUST_SELECT` | *You must have images in the Picture Tray to do this.* | **A művelet elvégzéséhez a képtálcán elemeknek kell lenniük.** |

*(Ne keverjük össze a hasonló `IDS_MUSTHAVESELECTION` /
`IDS_NEEDS_SELECTION` üzenetekkel — azok a **kijelölésre** vonatkoznak, nem
a tálcára.)*

## 6. A jelvény a rácsban

`thumbui/#holdadorner` — a respackben **438 bájtos** réteg. A `#` előtag a
Picasa erőforrás-nyelvében a **kompozit/overlay** elemeket jelöli.

---

## 7. ✅ IGAZOLVA: a tálca alatti gombsor sorrendje

A #455 sorrendje **helyes** — a respack deklarációs sorrendje megerősíti:

```
print → email → export → shop(order) → hello(sharewith) → blog → collage → movie → morebutton
```

> ⚠️ **NEGATÍV EREDMÉNY, hogy a következő kör ne járja be újra:** a
> `buttons/core-lh2.pbz` (ZIP-archívum, benne kilenc `.pbf` XML) `<placement>`
> számai **MÁS** sorrendet adnak (webupload 1.0, ebutton 2.0, pbutton 3.0,
> folderbutton 4.0, orderbutton 5.0, blogger 6.0, collage 7.0, sharewith 9.0).
> **Ez nem az alap-elrendezés**, hanem a bővíthető gombok beszúrási rendje —
> pontosan ahogy a #455 „Pontosítás" bekezdése mondja. A `.pbz` alapján
> **ne** írjuk át a sorrendet.

A `.pbf` formátum egyébként dokumentálásra érdemes: `<button id=… type="static|dynamic">`,
`<placement>`, `<label>`, `<icon name=… src="runtime"/>`, `<tooltip>` +
**19 nyelvi változat** (`tooltip_hu` nincs köztük).

## 8. `trayexec` — a műveletsor ADATVEZÉRELT

A `0x005dc890` függvény sztringkörnyezete egy **deklaratív akció-rendszert**
rajzol ki: `action`, `foreach`, `trayexec`, `export`, `export_message`,
`uploader`, `provider`, `hybrid`, `hybridalbum`, `geolocate`, `country`,
`internal`, valamint a `Preparing images…` és az
`ExecuteAction::defaultmsg` üzenet.

⇒ A tálca alatti gombok **nem külön-külön drótozott** kezelők: nevesített
akciókat futtatnak, és a **`trayexec`** a hatókör, ami azt jelenti, hogy az
akció **a tálca tartalmán** dolgozik. Ez egybevág a #455 3. teendőjével.

*Bizonyítottsági fok: **erős** (sztringkörnyezet); a dispécser utasításszintű
végigkövetése nem történt meg.*

## 9. ⛔ NEGATÍV: a `Tray contains:` NEM felhasználói felület

A `<p>Tray contains:</p>` sztring a `0x004c8350`-ben ül, együtt ezekkel:
`text/html`, `<body border=40px>`, `<style>button {…}</style>`, `/uidebug`,
`/focusalbum`, `%s/thumb/%s.jpg?size=-%d`, `<p>Album list:<p/>`.

⇒ Ez a Picasa **beépített HTTP-s hibakereső lapja** (`/uidebug`), ami a
tálca tartalmát bélyegképekként listázza. **Fejlesztői eszköz — nem kell
megépíteni.**

---

## 10. Ami NYITVA marad (örökölt, a #455-ből)

1. **A „Hold Selection" és az „Add to Picture Tray" pontos viszonya.** A
   `Tray::` névtérben csak a `HOLDINPICTURETRAY` és a `REMOVE_SELECTION`
   van; „Add to Picture Tray" nevű parancs a szövegtárban **nem szerepel** —
   tehát vagy más néven fut, vagy nem létezik. **Ez a kör nem döntötte el.**
2. **A tálca mint fogd-és-vidd FORRÁS az Intéző felé** — a #455 említi, a
   viselkedés nincs visszakövetve.
3. **Mi számít „régóta tartott" elemnek** (a 4.2 küszöbe) — a szöveg
   létezik, a feltétel nincs kimérve.
