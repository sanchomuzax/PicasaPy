# ADR-013: A helyi menük RAJZOLTAK maradnak — tudatos eltérés a mechanizmustól a látvány hűségéért

Dátum: 2026-09-15 · Státusz: ELFOGADVA · jegy: #886

## A helyzet

Az eredeti Picasa menüsora és **minden** jobbklikkes helyi menüje **natív
Windows-menü**: a program nem rajzolja őket, hanem a rendszerre bízza.
Nálunk mindegyik QML-ben van megfestve (`AlbumContextMenu.qml`,
`FolderContextMenu.qml`, `CollectionContextMenu.qml`,
`FolderListContextMenu.qml`).

Ez nem apró stíluskülönbség, hanem **mechanizmus-eltérés**, ezért döntés
kellett hozzá.

### A mérés (a binárisból)

| állítás | bizonyíték |
|---|---|
| a menük futásidőben épülnek, nem erőforrás-sablonból | **`LoadMenuW` nincs** az importtáblában |
| 36 hívóhely hoz létre felugró menüt | `CreatePopupMenu` |
| a megjelenítés a rendszeré | `TrackPopupMenu` (4 hely) + `TrackPopupMenuEx` (1) |
| a tételek pipálhatók / tilthatók | `CheckMenuItem` 13 hely, `EnableMenuItem` 17 hely |
| van **félkövér alapértelmezett** tétel | `SetMenuDefaultItem` |
| **nincs saját rajzolás** | a menüépítő (`0x0056c5a0`, 6816 b) `MF_OWNERDRAW` (`0x100`) jelző NÉLKÜL fűz be |
| a program a menühöz tartozó **kontextus-azonosítót** olvassa | `GetMenuInfo` egyetlen hívása (`0x005e7c20`): `cbSize = 0x1c`, `fMask = 8` — ⛔ **`MIM_MENUDATA`**, nem `MIM_STYLE` (helyesbítés, 2026-09-18: `ui-audit-context-menus.md` **C.2**) |

**Amit a Picasa MAGA rajzol:** csak a panelen belüli legördülőket
(`CPopupList`, `ytPopupListNode`, `ytTextPopupListItem`,
`ytSimpleSeparatorPopupListItem`, `CMixedPopupList`, `ButtconPopupCreator`).

## A döntés

**Marad a QML-ben rajzolt menü**, és az eredeti Windows XP-menü kinézetére
hangoljuk.

### Miért nem a rendszer menüje

A „rendszer" út (`QMenu`) ugyanazt a *mechanizmust* adná, mint az eredeti.
Linuxon viszont nem XP-menüt ad, hanem az itteni asztali környezet menüjét —
tehát a mechanizmus hűségéért cserébe épp a **látványt** veszítenénk el.

A projekt vezérelve — *„a felület pontosan úgy nézzen ki, mint az eredeti
Picasa"* — a **látványra** mutat. Ahol a kettő szembekerül, a látvány nyer.

Másodlagos, de egyirányba mutató érv: a panelen belüli legördülőket **az
eredeti is maga rajzolta**, tehát a rajzolt úttal a menü és a legördülő
egymás mellett konzisztens marad; a vegyes megoldás (natív menü + rajzolt
legördülő) két különböző kinézetet tenne egymás mellé ugyanabban az ablakban.

## A következmények

A döntés **hangolást** ír elő, nem átírást. A `#886` nyitva maradó pontjai:

1. a négy helyi menü QML-je a mért XP-méretekre, sorközre, keretre és
   színekre áll — az elfogadás **LÁTÁS**: renderelt menü vs. referencia,
   mért eltéréssel, nem számolt geometria;
2. ✅ **félkövér alapértelmezett tétel** — MEGVAN (2026-09-18): pontosan
   kettő van, `MF_BYCOMMAND` szerint (`0x9ca0` a kép- és a tálca-menüben,
   `0x9cc6` a nézőben), máshol nincs. Mérés és őr:
   `docs/specs/ui-audit-context-menus.md` **C**;
3. **gyorsbillentyű-oszlop** a felirat mellett, a 24 kimért tételen. A
   módosító-előtag a `0x00a6b250` bitmaszkjából áll össze (`Ctrl+` /
   `Shift+` / `Alt+`), **nem a feliratból**;
4. **ikon egyik tételre sem kerül** — a korábbi „öt ikonos tétel" lelet
   helyesbítve lett: az a mező a módosító-maszk;
5. a menütételek **pipálhatók és tilthatók** maradnak (`CheckMenuItem` /
   `EnableMenuItem` párja);
6. ⭐ **a szerkezet is eltér, nem csak a mechanizmus.** Az eredetiben NINCS
   négy külön helyi menü: 14 hívóhely megy EGY belépési ponton
   (`0x005e7c20`) EGY táblavezérelt építőbe (`0x0056c5a0`), és a kontextus
   **kivonással** adódik — az öt ág ugyanabból a menüből TÖRÖL tételeket
   (`MF_BYPOSITION`). Részletek: `docs/specs/ui-audit-context-menus.md`
   **B** szakasz. Nálunk négy helyen kell karbantartani ugyanazt a
   tételkészletet; ez a döntést nem változtatja meg, de a hangolás elé
   odatesz egy összevonási kérdést.

A panelen belüli legördülők változatlanul saját rajzolásúak maradnak — ezt a
döntés nem érinti.

## ⛔ Amit ez az ADR NEM ad meg

**Az XP-menü méreteit.** Azok nem a Picasa binárisában vannak: a natív menüt
a Windows saját témamotorja rajzolta, tehát a bináris visszafejtése ezekre a
számokra **elvileg sem** tud válaszolni — ott csak az van, hogy a program
átadta a menüt a rendszernek.

⇒ A hangolás (1. pont) forrása **nem** lehet a binárisból mért szám.

⚠️ És **képernyőkép sem oldja meg** — pontosan azért, amiért a döntés a
rajzolt utat választotta. A natív menüt az AKTUÁLIS rendszer témamotorja
rajzolja, tehát a ma futó Windowson készült kép a MAI Windows menüjét
mutatná, nem az XP-ét. Aki a jegyet viszi, ne kérjen ilyen képernyőképet: a
kérdésre nem válaszol.

Ami marad: a **Windows XP (Luna) dokumentált menü-metrikái** mint
**másodlagos** forrás — és a jegyben, valamint a kódban ki kell mondani,
hogy ez nem a saját példányunkról mért érték. Ez a projekt szokásos
„mérve" fokozatánál gyengébb bizonyíték, és annak is kell látszania; a
hiányt „józan ész" szerinti értékkel pótolni viszont tilos.

## Kapcsolódó

`docs/specs/ui-audit-context-menus.md` (a tételsorok és a B szakasz
kivonás-lelete) · #886 (a jegy) · a `gui-toolkit.md` ADR (miért QML az egész
felület).

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml`
- **Őrzi:** `tests/app/test_folder_context_menu_320.py`
