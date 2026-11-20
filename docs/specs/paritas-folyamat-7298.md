# Az Új készlet űrlap alapneve és névütközése az eredeti Picasával összevetve

Jegy: **#7298** (kutatás). Kör: 2026-11-20. Tárgy: a biztonsági mentés **Új
készlet...** űrlapja (`publish/newbackupset`, `NewBkDialog`), foglalt
alapnévnél. Bináris: `Picasa3.exe` 3.9.141.259, SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, csak
statikus vizsgálat (index + capstone, `picasa_dis.py`, futtatás nélkül).

Előzmények: [`biztonsagi-mentes.md`](biztonsagi-mentes.md) (9.1, 15.8, 4.),
[`ajandek-cd-kimenet.md`](ajandek-cd-kimenet.md) 11.5 (az alapnév), a #7290
lapja (`paritas-folyamat-7290.md`, a `research/7290-claude` ágon, 4.3 és J3), a
#7294 (az első megnyitáskor létrejövő alapkészlet, `fix/7294-claude` ág).

## 0. Következtetés

**A kérdés előfeltevése téves: az eredeti Új készlet űrlapja soha nem ad
alapnevet.** A név mező **üresen** nyílik, nincs számozás, nincs
előtöltött "My Backup Set". A "My Backup Set" (`il_BurnPanel::bksetname`) az
egész binárisban **egyetlen** helyen szerepel, a `0x006706d0` panel-feltöltőben,
és ott is csak akkor kerül használatra, ha a készletlista **üres**: ez az
automatikus alapkészlet (a #7294), nem az űrlap alapértéke.

1. **Milyen alapnevet ad foglalt "My Backup Set" mellett?** Egyet sem: üres
   mezőt. A felhasználónak kell nevet írnia.
2. **Mit csinál foglalt névnél?** Nem hibát, nem felülírást, nem
   átnevezést: a **Létrehozás gomb (`ok`) tiltott**, amíg a név üres, vagy
   **ASCII-kisbetűsítve megegyezik** egy létező készlet nevével
   (`0x00679570`). **Szöveg nincs**: a szövegtárban nincs "a készlet már
   létezik" jellegű azonosító. Szerkesztéskor ugyanez, a szerkesztett
   készlet saját, bájtra azonos nevét kivéve.

**Nálunk** két dolog tér el az eredetitől (1. és 5. szakasz): az űrlap a "My Backup
Set" nevet **előtölti** (`BackupHost.qml:217`, a #3189 megjegyzése szerint "az
eredeti NEM üres mezővel indít", ez **megdőlt**), és a gomb mindig élő, a
foglalt nevet csak mentéskor utasítjuk el hibaszöveggel
(`backup_controller_sets.py:87`). A #7294 óta az első megnyitás létrehozza
ugyanazt a nevet, ezért a változtatás nélküli **Új készlet + OK** mindig a
"A backup set with this name already exists." hibát adja. Ugyanezen az
űrlapon négy további, mért eltérés és egy kisebb van (5.1 szakasz). Javasolt fejlesztői
jegytörzs: **J1**; egy kis kutatási jegytörzs az induló állapot élő
megerősítésére: **J2** (7. szakasz).

## 1. Eredeti / nálunk / teendő

Jelölés: **EGYEZIK** · **ELTÉR** · **TÖBBLET** (nálunk van, az eredetiben
nincs). A "nálunk" oszlop **mérés** (kód olvasva, a main `b7bb9e5fb` kiadás;
a #7294 a `fix/7294-claude` ágon). Az "eredeti" oszlop utasításcímek.

| # | tárgy | eredeti (bináris cím) | nálunk (fájl:sor) | állapot | teendő |
|---|---|---|---|---|---|
| 1 | a név mező induló értéke új készletnél | **üres**: a `NewBkDialog` konstruktora nullázza a név mezőt (`0x00678c09`..`0x00678c3e`, `[this+0xc8]`), a felépítő ebből tölti a `name` vezérlőt (`0x006791d0`..`0x00679200`); a `newbackupset.fen` `<edit name="name">` elemének nincs alapértéke | `BackupHost.qml:214-217`: `urlapNev = qsTr("My Backup Set")` | **ELTÉR** | J1/1 |
| 2 | a "My Backup Set" szerepe | csak az **automatikus alapkészlet** neve üres listánál: `0x00670ae6` (`0x006706d0`); a 4 bájtos pásztázás az egész fájlon pontosan 1 hivatkozást ad rá (`0x00670aec`) és 1-et az azonosítóra (`0x00670ae7`) | #7294: `backup_controller_sets.py` (`fix/7294-claude`, `megnyitasiKeszlet`, 139. sor) a `BackupHost.qml` hívásából kapja a nevet | EGYEZIK (a #7294 helyes) | nincs |
| 3 | foglalt név új készletnél | a **Létrehozás gomb tiltott**: `0x00679570`, a készletlista bejárása `0x00679708`..`0x006798d7`, találatnál `0x00679833`, a gomb állítása `0x0067983b`..`0x0067986d` | a gomb mindig élő (`BackupHost.qml:609-616`); a vezérlő mentéskor utasít el: `backup_controller_sets.py:78-90`, a `UNIQUE` kulcs hibájából (`index/backup_sets.py:49`) | **ELTÉR** | J1/2 |
| 4 | hibaszöveg foglalt névre | **nincs**: a szövegtárban (azonosítók minden nyelven azonosak) egyetlen készlet-névütközési szöveg sincs; az egyetlen készlet-hibaszöveg az `il_NewBkDlgRenameError` (átnevezés, 6. szakasz) | "A backup set with this name already exists." (`backup_controller_sets.py:87`) | TÖBBLET | az űrlapról nem érhető el; védelmi ágként maradhat |
| 5 | számozás, felülírás, automatikus átnevezés | **nincs**: a beszúrás rendezett lista-beszúrás egyezés-vizsgálat és visszautasítás nélkül (`0x0067d800`, `0x0067da10`), az űrlap-út függvényeiben nincs számozó formátum | nincs | EGYEZIK | nincs |
| 6 | a név összehasonlítása | **ASCII A-Z kisbetűsítés** bájtonként (`0x00679766`..`0x0067977c`), **nincs levágás** | bináris `UNIQUE` (`backup_sets.py:49`), mentéskor `strip` (`backup_sets.py:113-125`) | **ELTÉR** | J1/2 |
| 7 | üres név | a gomb tiltott (`0x006795ca`..`0x006795ec`) | a vezérlő elutasítja: "Give the backup set a name." (`backup_controller_sets.py:57-61`) | ELTÉR (csak a mód) | J1/2 |
| 8 | szerkesztés, saját név | a szerkesztett készlet **bájtra azonos** nevét átengedi (`0x006797b3`..`0x006798b4`, az eredeti név a `[dlg+0xfc]`-ben, a másolat `0x00678fa5`..`0x00678fef`); más készlet nevére a gomb tiltott | nincs előzetes vizsgálat: `backup_controller_sets.py:95-117`, ütközésnél általános "The backup set could not be changed." | **ELTÉR** | J1/2 |

## 2. Az alapnév egyetlen helye

A négybájtos pásztázás a teljes `Picasa3.exe`-n (little-endian virtuális cím,
nem az index, tehát a vtábla-hívásra vak index kiesése nem számít):

| literál | cím | találat | hely |
|---|---|---:|---|
| `My Backup Set` | `0x00ca4670` | **1** | `0x00670aec` (a `0x00670aeb` `mov eax, imm` operandusa, `0x006706d0`) |
| `il_BurnPanel::bksetname` | `0x00ca4680` | **1** | `0x00670ae7` (`push imm`, `0x006706d0`) |
| `BKTag ` | `0x00ca4698` | **1** | `0x00670b04` (`0x006706d0`) |
| `BKTag %s` | `0x00ca614c` | **1** | `0x0067ad63` (a készlet-parancs kezelője, `0x00679ca0`) |
| `il_NewBkDlgRenameError` | `0x00ca6174` | **1** | `0x0067ae7a` (`0x00679ca0`) |
| `newbackupset` (az űrlap neve) | `0x00ca5e20` | **1** | `0x00678bea` (a konstruktor, `0x00678be0`) |
| `il_BurnPanel::DefBkFolder` | `0x00ca5e40` | **1** | `0x00678d69` (a konstruktor) |

⇒ a `NewBkDialog` konstruktora (`0x00678be0`, 507 b), a felépítője
(`0x00678e80`, 1167 b), a két adatcserélője (`0x00679310`, `0x00679570`) és a
parancskezelő (`0x00679ca0`) **egyike sem hivatkozik a `bksetname`-re**. A
konstruktor egyetlen `il_...` szövegtár-hivatkozása a `DefBkFolder` (az alapértelmezett
célmappa, `\Picasa Backup\`, magyarul `\Picasa biztonsági másolat\`).

**Az automatikus alapkészlet** (a #7290 4.3-ja és a #7294): `0x00670ab6`
(`test [ebp+0x2b4], 0xfffffffe`) a készletek számát nézi, **üres** listánál
`0x00670ae6`-tól létrehozza a "My Backup Set" nevű rekordot, kiírja a
`backups.xml`-t (`0x00670ca8`), különben a `LastBkSet`-re ugrik (`0x00670cb3`).
**A törlés** az utolsó készletre tiltott: `0x0067a683`..`0x0067a697`
(`2 * darab <= 2` esetén kilép a törlés-ágból), ezért az eredetiben a lista az
első megnyitás után soha többé nem üres (a nálunk is így van:
`PublishPanel.qml:377`, `visible: mentesKeszletek.length > 1`).

## 3. Az űrlap induló állapota (új készlet)

A parancskezelő (`0x00679ca0`) a `publish/newbackupset` azonosítót
`0x0067ab88`-nál hasonlítja, a `publish/editbackupset`-et `0x0067abe6`-nál; a
szerkesztés jelzője (`bl`) `0x0067ac84`..`0x0067ac96`: "szerkesztés ÉS van
készlet". Majd:

```
0x0067acaf  call 0x678be0      ; a NewBkDialog felépítése: [dlg+0xf4] = &készletek, [dlg+0xf8] = bl
0x0067ad00  call 0x8d26a0      ; modális futtatás
0x0067ad07  jne  0x67af27      ; nem nulla: Mégse, nincs változás
```

Új módban (`bl == 0`) a kezelő **semmit nem tölt** a párbeszédbe a futtatás
előtt (a másolás, `0x0067acf3`, csak szerkesztéskor fut), a konstruktor
pedig a név, a cél és a tartalom-mód mezőit nullázza (`[dlg+0xc8]`, `+0xd0`,
`+0xd4`: `0x00678c09`..`0x00678c3e`). ⇒ **üres név, CD/DVD típus, "Minden
fájltípus"**. A felépítő (`0x00678e80`) ezekből tölti a vezérlőket: a `type`
rádió 0 (a cél üres, `0x00678ec6`..`0x00678f3d`), a `files` rádió a
`[dlg+0xd4]` bitjeiből, a `name` a `[dlg+0xc8]`-ból (`0x006791d0`..`0x00679200`).

A `newbackupset.fen` ezt megerősíti: `<edit name="name" width="fill"/>`,
alapérték és `focus` nélkül; a gomb `<button title="Create" type="accept"
name="ok"/>`. A hivatalos magyar feliratok a
`referencia/panel-feliratok-hu.tsv` 621-631. sorában vannak (a többi nyelven a
`referencia/i18n/<nyelv>/newbackupset.xml`).

**Szerkesztéskor** (`[dlg+0xf8] != 0`, `0x0067920e`) a felépítő még három
dolgot tesz: a **`typegroup` (Mentés típusa) csoportot letiltja**
(`0x0067921b`..`0x00679241`), a címet `il_NewBkDialog::EditTitle`-re
("Edit Backup Set", `0x00679276`..`0x006792bb`), a gomb feliratát
`il_NewBkDialog::EditOKButton`-ra ("Change", `0x006792bf`..`0x006792d7`)
cseréli. Új készletnél a `.fen` feliratai maradnak: "New Backup Set" és "Create".
**A név eredeti értékét** (`[dlg+0xc8]`) a felépítő mindig átmásolja a
`[dlg+0xfc]`-be (`0x00678fa5`..`0x00678fef`): ez a szerkesztett készlet
"saját neve" a névellenőrzésben.

## 4. A névellenőrzés: `FUN_00679570` (985 b)

A függvény a párbeszéd **figyelője**, minden vezérlő-eseményre lefut. A
bizonyítás lépései:

| lépés | bizonyíték |
|---|---|
| a figyelő a `NewBkDialog` objektumon belüli al-objektum (`[dlg+0xbc]`), vtáblája `0x00ca6a30`, **1. slotja** a `0x00679570` | konstruktor: `0x00678c2c` (`mov [ebx], 0xca6a30`), vtábla-olvasás: `0x00ca6a34` = `0x00679570` |
| a konstruktor **kulcs nélkül** (minden eseményre) regisztrálja a figyelőt | `0x00678db0`..`0x00678dbb`: `call 0x8d59a0` üres kulccsal; a `0x008d59a0` üres kulcsnál az objektum `[+0x14]` listájába fűz (`0x008d59c9`..`0x008d5a6b`) |
| a kiváltó a figyelők listáját járja és a **1. slotot** hívja | `0x008d60b0`: `0x008d60d0`..`0x008d6124`, a hívás `0x008d6100` (`mov edx,[[esi]+4]`, `call edx`) |

**A függvény menete** (a `ret 8`: két veremargumentum, az esemény):

```
0x0067957f  a "name" vezérlő szövege              ; név = [esp+0x14]
0x006795ca  üres-e? (nincs mutató / hossz 0 / első bájt 0)   ; nemÜres = !üres
0x006795f6  ha nemÜres: a "type" rádió értéke; 1 = lemez-lemez
0x0067967e  ha lemez-lemez: a "disk" szöveg üres-e? -> nemÜres = a mappa nem üres
0x00679708  ha még nemÜres: a készletek bejárása, rekordonként 0x28 bájt (0x006798c6):
              a rekord neve (rekord+0) és a mezőszöveg ASCII-kisbetűsített
              bájtonkénti összehasonlítása (0x00679760..0x0067977c: 'A'..'Z' -> +0x20)
              egyezésnél (0x006797b3):
                [dlg+0xf8] == 0 (új készlet)  -> nemÜres = 0, kilép (0x00679833)
                szerkesztés: a mezőszöveg és a SZERKESZTETT készlet eredeti neve
                  (rekord: [dlg+0xfc]) BÁJTRA azonos? igen -> tovább a bejárással,
                  nem -> nemÜres = 0 (0x006798b4, 0x00679833)
0x0067983b  az "ok" vezérlő engedélyezése = (nemÜres != 0)   ; slot +0x114
```

A `0x0067983c` operandusa a `0x00c9ad6c` literál (négy bájtos pásztázás: 30
találat, köztük a felépítő `0x00679249`-es helye, ahol a szerkesztés a **gomb
feliratát** állítja: ugyanaz a vezérlő). Az engedélyező függvény a dialógus
vtáblájának `+0x114`-es slotja (`0x00ca69c8` = `0x008d2640`): név szerint
megkeresi a vezérlőt (`+0xa0`), letiltáskor áthelyezi a fókuszt, majd a vezérlő
`+0xc8`-as metódusát hívja a logikai értékkel; ugyanez a slot tiltja le a
`typegroup`-ot szerkesztéskor.

⇒ **A Létrehozás gomb engedett, ha a név nem üres, és (új készletnél) egyetlen
meglévő név sem egyezik vele ASCII-kisbetűsítve; lemez-lemez típusnál a cél
mappa is kell.** Nem ASCII betű (pl. `Á`/`á`) kis- és nagybetűs alakja
**különböző** névnek számít, és a szóközök is számítanak (nincs levágás).
A rendezett beszúrás is ezt a kisbetűsítést használja (`0x00676090`, 219 b).

## 5. Nálunk (mért)

```
src/picasapy/app/qml/PicasaPy/BackupHost.qml
  214-223  ujKeszletUrlap(): urlapNev = qsTr("My Backup Set"); urlapHiba = ""
  237-251  mentsdAzUrlapot(): ujKeszlet(...) / modositsdAKeszletet(...)
  489-491  cím: szerkesztettId >= 0 ? "Edit Backup Set" : "Backup Set"
  501      a név felirata: "Backup Set"
  506-511  a név mező (backupSetName), onTextEdited: urlapNev = text
  526-543  a típus-rádiók: szerkesztéskor is engedettek
  592-600  backupFormError: a hibaszöveg az űrlapon
  609-616  a gomb (backupFormSave): szerkesztésnél "Change", új készletnél "OK"; mindig engedett
src/picasapy/app/backup_controller_sets.py
  51-90    ujKeszlet(): üres név -> "Give the backup set a name."; a mentés kivétele -> "A backup set with this name already exists."
  95-117   modositsdAKeszletet(): ütközés -> "The backup set could not be changed."
src/picasapy/index/backup_sets.py
  49       name TEXT NOT NULL UNIQUE (bináris összehasonlítás)
  104-125  keszlet_letrehozasa: nev.strip(), INSERT
  134      keszletek(): ORDER BY name (bináris rendezés)
fix/7294-claude (még nem main):
  backup_controller_sets.py:139  megnyitasiKeszlet(alapnev): üres listánál ujKeszlet(alapnev, "", SZURO_MINDEN, TIPUS_CD_DVD)
  BackupHost.qml:155             a hívás: megnyitasiKeszlet(qsTr("My Backup Set"))
```

**A hiba oka két, külön helyes-hibás döntés találkozása:** a #3189 előtölti a
nevet (téves: az űrlap alapértéke üres), a #7294 pedig jól létrehozza az
alapkészletet ugyanazzal a névvel (helyes). A főmásolat mai állapotán a
`UNIQUE` kulcs mentéskor elutasítja a kettőt, és a felhasználó az
elutasítást látja.

### 5.1 Mellékleletek ugyanazon az űrlapon (a kérdésen kívül, de mérve)

| tárgy | eredeti | nálunk | állapot |
|---|---|---|---|
| új készlet ablakának címe | `newbackupset/window1.title`: "New Backup Set", magyarul **"Új mentési készlet"** (`panel-feliratok-hu.tsv:621`); az `il_NewBkDialogTitle` ("Backup Set") a **törlés-megerősítés** címe (`0x0067a76f`), nem az űrlapé | `BackupHost.qml:489-490`: "Backup Set" | **ELTÉR** |
| a név felirata | `newbackupset/labelgroup2.title`: "Name:", magyarul **"Név:"** (`tsv:622`) | `BackupHost.qml:501`: "Backup Set" (a panel `publish/label_backupname` felirata, más elem) | **ELTÉR** |
| a gomb új készletnél | `newbackupset/ok.title`: "Create", magyarul **"Létrehozás"** (`tsv:631`) | `BackupHost.qml:612`: "OK" (a QML-megjegyzés "ÚJ készletnél OK" téves) | **ELTÉR** |
| a típus-csoport szerkesztéskor | **tiltott** (`0x0067921b`..`0x00679241`) | engedett, a vezérlő át is veszi a típust (`BackupHost.qml:526-543`, `backup_controller_sets.py:95-107`) | **ELTÉR** |
| a lista sorrendje | rendezett, ASCII-kisbetűsítéssel (`0x0067d800`, `0x00676090`) | `ORDER BY name`, bináris (`backup_sets.py:134`) | ELTÉR (kicsi; a megjelenítést nem mértem) |

A hivatalos fordítások minden nyelven megvannak a
`referencia/i18n/<nyelv>/newbackupset.xml` fájlokban (`window1.title`,
`labelgroup2.title`, `ok.title`), a fejlesztő onnan vegye, ne fordítsa újra.

## 6. Az "Unable to rename Backup Set" NEM a névütközés hibája

Az egyetlen készlet-hibaszöveg (`il_NewBkDlgRenameError`, `0x0067ae79`) a
**szerkesztés** ágán van, és csak akkor jelenik meg, ha a név **megváltozott**:

```
0x0067adb5..0x0067ae17  az új és a régi belső név ("BKTag <név>") összehasonlítása;
                        azonos -> a rekord átmásolása, mentés (0x0067ae17)
0x0067ae70  call 0x473f80   ; a kép-adatbázis "<régi>-backuphash" mezőjének átnevezése
0x0067ae75  test eax,eax ; je 0x67ae17   ; 0 = rendben
0x0067ae79  il_NewBkDlgRenameError, MessageBox (0x00980700), kilép; a rekord nem változik
```

A `0x00473f80` a `<név>-backuphash` mezőnevet építi mindkét névből
(`0x00473fd5`, `0x0047402f`: `-backuphash` literál, `0x00c81450`), és a
`0x006a81c0`-n át az adatbázis mezőlistájában (`[db+0x58]`) kikeresett elemre
egy útvonal-ellenőrzés (`0x00992ed0`) után egy `0x00994400` hívást ad
(`0x006a8350`..`0x006a8358`, a sorrend fájl-átnevezésre vall); az eredmény
nem nulla értéke az `0x0067ae75`-nél hibaként kezelődik. A `0x00994400` belsejét
nem bontottam. A névütközést ez a lánc **nem vizsgálja**: azt a gomb tiltása
(4. szakasz) már előtte kizárja. ⇒ az üzenet az adatbázis-oldali átnevezés
hibája, **nem "foglalt név"** (a pontos kiváltó oka NINCS MEG, ld. a 9.
szakasz utolsó sorát).

## 7. Javasolt fejlesztői jegytörzsek

### J1 (P1, hiba) "Mentés: az Új készlet űrlap üres névvel indul, és a Létrehozás gomb tiltott üres vagy foglalt névnél"

**MIT AD MA:** az űrlap a "My Backup Set" nevet előtölti (`BackupHost.qml:217`),
a gomb mindig élő; a #7294 óta az első megnyitáskor létrejön ugyanez a név, ezért
a változtatás nélküli Új készlet + OK "A backup set with this name already
exists." hibát ad.
**Eredeti:** `0x00679570` (a név ellenőrzése és az `ok` gomb állítása,
`0x00679708`..`0x0067986d`), `0x00678e80` / `0x00678be0` (üres induló név,
`0x006791d0`, `0x00678c09`), `0x0067a683` (az utolsó készlet nem törölhető).
Lásd a 3-4. szakaszt; az űrlap `newbackupset.fen`.
**Teendő:**
1. `ujKeszletUrlap()` (`BackupHost.qml:214`): `urlapNev = ""`. Nincs számozás és
   nincs "My Backup Set"-előtöltés (az alapkészlet a #7294 dolga marad).
2. Új vezérlő-slot a foglaltság kérdezésére (pl. `keszletNevFoglalt(nev,
   szerkesztettId)`): igaz, ha **a szerkesztett készleten kívül** bármelyik
   készlet neve **ASCII A-Z kisbetűsítve** egyezik a szöveggel; a nem ASCII
   betűk kis/nagybetűs alakja különböző név, **levágás nincs** (a `strip`-et a
   felület ne az ellenőrzés előtt végezze). A séma (`UNIQUE`) változatlan marad.
3. A gomb (`backupFormSave`) `enabled`: a név nem üres ÉS nem foglalt ÉS (lemez-lemez
   típusnál) a mappa nem üres; a feltétel a mező szövegére és a típusra kötött
   (mint az eredeti: minden eseményre újraértékelődik). **Hibaszöveg az űrlapon
   nem jelenik meg névütközésre** (az eredetiben nincs). A `ujKeszlet` jelenlegi
   elutasító ága védelmi ágként maradhat.
4. Szerkesztésnél a saját név változatlanul hagyása engedett. **Tudatos eltérés:**
   az eredeti a saját név kis/nagybetűs átírását is tiltja (a saját rekordja
   ütközik a bájtra azonos ellenőrzésen); ezt **nem** követjük, mert hibának
   tűnik (a felhasználó ugyanazt a készletet nevezi át). Ezt a jegy mondja ki.
5. Ugyanebben a jegyben (ugyanaz az űrlap és fájl): a 5.1 melléklelet-tábla négy
   felirat- és viselkedéseltérése: új készletnél a cím "New Backup Set", a név
   felirata "Name:", a gomb "Create" (hivatalos fordítással, a
   `newbackupset.xml` alapján), szerkesztéskor a **típus-csoport tiltott**.
**Mihez ne nyúlj:** az `index/backup_sets.py` sémájához (a séma csak az
`index/`-é, és a `UNIQUE` marad), a #7294 alapkészlet-létrehozásához, a
`PublishPanel.qml` készlet-választójához.
**Kész, ha:** kattintásos QML-teszt a `BackupHost`-on: (a) üres készletlistán az
első megnyitás után pontosan 1 készlet van; az Új készlet űrlap neve **üres**, a
gomb **tiltott**; (b) a meglévő név bájtra azonos beírása tiltott; ugyanaz kis
`s`-sel az elején (`saját mentési készlet`) tiltott; a `SAJÁT mentési készlet`
(nem ASCII `Á`/`á` eltérés) **engedett**; egy új név engedett, és a kattintás
létrehozza; (c) szerkesztéskor a saját név engedett, másik készlet neve tiltott,
a típus-csoport tiltott; (d) a szomszédos elemek (készlet-legördülő, Törlés,
Mentés indítása) viselkedése változatlan; (e) a felületi szövegek nem tartalmaznak
új hibaszöveget névütközésre.

### J2 (P3, kutatás, Colab-felvétel) "Az Új készlet űrlap induló állapota az eredetiben"

**Eredeti:** `0x00679570`, `0x008d60b0` (a figyelő-kiváltó), `0x00678e80`.
A 3-4. szakasz a gomb tiltását **utasításokból** vezeti le, de az **induló**
kiértékelést (azonnal tiltott-e a gomb az üres névvel, még az első esemény
előtt) nem követtem végig a dialógus-motorban; a `bind attr="enabled"` elem
(a "Choose..." induló állapota) ilyen induló kiváltást feltételez. A J1
helyessége ettől **nem függ** (üres névvel a gomb nálunk tiltott, és ha az
eredeti engedné, üres nevű készletet kapna, amit mi sem engedünk).
**Teendő:** Colab-felvétel az eredeti Picasa 3.9-en, négy képpel: az űrlap
üresen nyitva; létező név beírva; új név beírva; szerkesztés megnyitva. A kép a
Létrehozás gomb állapotát és a típus-csoport állapotát mutassa.
**Kész, ha:** a négy kép a lap 3-4. szakaszához csatolva, és az induló állapot
sora "megerősített" fokra állítva.

## 8. Bizonyítottsági fok

| állítás | fok |
|---|---|
| a "My Backup Set" egyetlen hivatkozása a `0x006706d0` (az űrlap soha nem tölti elő) | **megerősített** (4 bájtos pásztázás az egész fájlon, 1-1 találat, és az index egyezik) |
| az űrlap név mezője üresen nyílik | **megerősített** (a konstruktor nullázza, a felépítő abból tölt, a `.fen`-ben nincs alapérték, a kezelő új módban nem tölt) |
| a Létrehozás gomb tiltott üres vagy foglalt névnél | **megerősített** (az utasítások olvasva, az `ok` vezérlő és az engedélyező slot azonosítva) |
| a kisbetűsítés csak ASCII A-Z, nincs levágás | **megerősített** (a bájtonkénti ciklus olvasva) |
| a figyelő minden vezérlő-eseményre lefut | **erős** (regisztráció üres kulccsal és a kiváltó ciklus olvasva; a kiváltó összes hívóját nem térképeztem fel) |
| az **induló** kiértékelés (azonnal tiltott gomb) | **erős következtetés, nincs követve** (J2) |
| nincs számozás, felülírás, hibaszöveg | **megerősített** az űrlap útjára: a hat függvény (`0x00679ca0` új/szerkeszt ága, `0x00678be0`, `0x00678e80`, `0x00679310`, `0x00679570`, `0x0067d800`) olvasva; a `0x006759c0` (`backups.xml` író) és a `0x006769f0` (`LastBkSet` író) nincs újraolvasva, a `biztonsagi-mentes.md` 1-2. és 9.1 szakasza rögzíti őket |
| az "Unable to rename Backup Set" az adatbázis-oldali átnevezés hibája, nem névütközés | **erős** (a hívási lánc olvasva, a `0x00994400` belsejét nem bontottam) |
| a szerkesztésnél a típus-csoport tiltott | **megerősített** (a `0x0067921b`..`0x00679241` a `+0x114` slotot a `typegroup`-ra hívja `0` értékkel) |

**Nem volt élő felvétel** az Új készlet űrlapról (a `kepek-leltar.md`-ben nincs
rá találat): az egész lap statikus, a J2 ezt pótolja.

## 9. Nyitott kérdések mérlege

`1 nyílt (nevesített, felvehető jegytörzsben: J2) · 5 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 "csak nyitva"`

| kérdés | állapot |
|---|---|
| milyen alapnevet ad az űrlap, ha a "My Backup Set" már létezik | **LEZÁRVA**: üres mezőt, soha nem ad nevet (0., 2., 3. szakasz) |
| mit csinál foglalt névnél | **LEZÁRVA**: a Létrehozás gomb tiltott, hibaszöveg nincs (4. szakasz) |
| milyen az összehasonlítás | **LEZÁRVA**: ASCII A-Z kisbetűsítés, nincs levágás (4. szakasz) |
| mi történik szerkesztésnél | **LEZÁRVA**: a saját, bájtra azonos név engedett, másik készlet neve tiltott (3-4. szakasz) |
| mi az "Unable to rename Backup Set" | **LEZÁRVA** a kérdés szempontjából: nem névütközés (6. szakasz) |
| a gomb **induló** állapota az üres névvel, az első esemény előtt | **NYÍLT, J2** |
| a `0x00994400` pontos hibakódjai | **HATÓKÖRÖN KÍVÜL**: a névütközés kérdését nem érinti, mert a gomb tiltása a lánc előtt kizár minden ütközést |

## 10. Amit KIZÁRTAM

- **"Az űrlap a 'My Backup Set' nevet tölti elő (az eredeti NEM üres mezővel
  indít)"** (a `BackupHost.qml:216` #3189-es megjegyzése): **MEGDŐLT**. A
  literálra egyetlen hivatkozás van (`0x00670aec`, a `0x006706d0`-ben), az űrlap
  útja nem érinti.
- **"Az eredeti számoz ('My Backup Set 2')"**: nincs számozó formátum az űrlap
  útján, és a rendezett beszúrás nem vizsgál egyezést.
- **"Az eredeti felülír, vagy magától átnevez"**: a gomb tiltása miatt ez az ág
  el sem érhető, és a beszúrás nem keres azonos nevet.
- **"Az eredeti 'már létezik' szöveget mutat"**: az enUS szövegtár (az
  azonosítók minden nyelven azonosak) névütközés-szövegei a mappákra, a
  felhasználónévre, a gyűjteményre és a személyre vonatkoznak, készletre egy
  sem (`grep -n -i 'exist\|already\|same name\|duplicate'
  referencia/i18n/enUS/stringres.xml`).
- **"Az `il_NewBkDialogTitle` ('Backup Set') az űrlap címe"**: a törlés-megerősítés
  címe (`0x0067a76f`).

## Mérés módja

1. A pásztázás: `python3 -I`, a `Picasa3.exe` bájtjain a literálcím
   `struct.pack("<I", va)` mintájának összes előfordulása (2. szakasz táblázata).
2. A függvényolvasás: `~/picasapy-agent/eszkozok/binaris/picasa_dis.py <cím>`
   (a bináris SHA-ja egyezik az indexével), a `0x00679570`, `0x00679310`,
   `0x00678e80`, `0x00678be0`, `0x00679ca0`, `0x0067d800`, `0x00676090`,
   `0x008d2640`, `0x008d59a0`, `0x008d60b0`, `0x00473f80`, `0x006a81c0` címekre.
3. A cím-atlasz (`atlasz_keres.py`) a készlet-párbeszéd függvényeire a
   `biztonsagi-mentes.md` 4., 9.1 és 15.8 szakaszát adta; a validátor
   (`0x00679570`) és a figyelő-lánc ÚJ.
4. A nálunk-oldal: a worktree `src/` fájljai (5. szakasz), a #7294 a
   `git show fix/7294-claude:<fájl>` kimenete.
