# PicasaPy paritás-ellenőrzés - #4317

**Vizsgálati dátum:** 2026-10-13. **Hatókör:** a 2-4. réteg korábbi statikus QML-ellenőrzése, a 6. réteg tiszta profilos kattintáspróbája és a 7. réteg effektkimenet-mérése. A rétegállapotok a jegy korábbi köreihez és az alábbi bizonyítékokhoz kötődnek.

> **Első szétválasztás (#7116, 2026-11-16):** a lezárt réteg- és folyamatszintű összevetések változatlan szakaszai az [archívum 1](paritas-ellenorzes-archiv-1.md) lapra kerültek. Az első bontáskor még nyitott #7012 és #7022 szakasz a fő lapon maradt.
>
> **Második bontás (#7244 folytatás):** a lezárt #7031, #7032, #7059, #7069, #7083 és #7084 szakasz változatlanul a [második archívumba](paritas-ellenorzes-archiv-2.md) került. A #7012, #7022 és #7028 szakaszok, valamint az aktuálisan nyitott vizsgálatok a fő lapon maradtak.
>
> Az első archív lapon: #4317, #4339, #5245, #5260, #5265, #5271, #5272, #5277, #5295, #5396, #5398, #6845, #6862, #6963, #6964, #6967, #6970, #6975, #6984, #6988, #6989, #6996, #7000, #7001, #7006, #7008, #7009, #7024.
>
> A második archív lapon: #7031, #7032, #7059, #7069, #7083, #7084.

## #7022 A címkék hozzáadása és törlése teljes folyamata

### Vizsgálati határ és bizonyítottság

A vizsgálat tárgya a Picasa 3.9.141.259 bináris, SHA-256: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. Az eredeti UI-belépési pontok, az Add Tag bemenetének tokenizálása, a Quick Tags beállításai és a jelenlegi PicasaPy kódút statikusan összevethető. Az eredeti címkeírás tényleges fájl-/adatbázis-hatása, az írási hibák, a vegyes címkeállapotú törlés és a viewer út végpontja nyitott, mert a lokális diszasszembly a címke-panel modelljének frissítésénél egy fel nem oldott visszahívásba ér.

Az összesített bizonyítottsági fok **nyitott**. Az alábbi táblázatban a forrás szerint külön jelzem, hogy a részállítás megerősített, feltételes vagy `NINCS MEG`; egyetlen diszasszembly-útból nem emelek állítást megerősítetté.

### Belépési pontok, feltételek és panelhatás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Nézet > Tags:** a `0x00559150` menüépítő a `&Tags` feliratot a `0xd6e018` rekordba, annak `0x9d2c` parancskódját a `0xd6e022` mezőbe teszi. A `0x0065ab50` a `0x9d2c` kódot `thumbui/tags_toggle`-ra irányítja. A szomszéd `0x9d71` rekord a Properties parancs. A Tags-panel ki-/bekapcsolását a `0x005d9760` végzi. **A rekordazonosítás megerősített; a menü engedélyezési feltétele nyitott.** | `PicasaViewMenu.qml:94-109`, `MainMenuBar.qml:376-377`, `MainWindowLibraryActions.qml:17-23`: a menü mindig a Tags lap megnyitását kéri. Ha már a Tags az aktív lap, nyitva hagyja. | Eltérés: az eredeti aktív Tags fiók ismételt toggle-ja bezárja a fiókot; a jelenlegi menü ugyanarra az aktív lapra állít, és nyitva hagyja. A Tags menüút aktív állapotát a bináris toggle-hoz kell igazítani. |
| **Ctrl+T és Ctrl+K:** a `0x005e60d0` billentyűkezelő `0x4b` és `0x54` esetben ugyanazt, a `0x0065ab00` Tags-toggle-t hívja. A közös billentyűkezelő előtt állapotőrök vannak; ezek pontos néző-/szerkesztő- és fókuszfeltétele nyitott. | `MainKeyboardShortcuts.qml:101-108,320-334`; a közös engedélyezés `MainWindowCommands.qml:229-233`. Ctrl+T az aktív Tags fiókot bezárja, Ctrl+K mindig megnyitást kér. A billentyűk nem aktívak, ha a néző nyitva van vagy szövegmező kapott fókuszt. | Eltérés: Ctrl+K viselkedjen a Ctrl+T-vel azonos toggle-ként, ne csak nyissa a lapot. Az eredeti viewer alatti billentyűviselkedést külön kell eldönteni a nyitott bináris kapu után. |
| **Tálca / felső panelgomb:** a `0x005d9cc0` eseményút a Tags gombra a `0x0065ab00`-n át jut. A `0x005d9760` az aktív metadata lap nevét a bejövő eseménnyel hasonlítja össze (`0x005d9781-0x005d9998`); egyezéskor `thumbui/toggle_right_drawer`-t hív (`0x005d99a0`), más laptól Tags-re váltáskor bekapcsolja a Tags gombot és a `rightdrawerpanel/tagpanel` lapot (`0x005d9ad8-0x005d9b49`). **Ez az út egy diszasszemblyből feltételes.** | `TrayTopRow.qml:244-256,298-312`: az aktív panelgomb bezárja a fiókot, másik lapra kattintva vált. | A látható toggle-viselkedés egyezik. Az eredeti kijelölési, videó- és read-only kapuk nem láthatók ebben a routerben, ezért a teljes engedélyezést külön kell vizsgálni. |
| **Tulajdonságok > Edit Tags / néző:** a `0x00638990` felépít egy `PropertiesPanel::edit_keywords` eseményt. A lokális kód nem dönti el, hogy az esemény panelt vagy ablakot nyit, illetve mikor engedélyezett. A `0x005e60d0` billentyűút felső őre a néző alatti billentyűzést is nyitva hagyja. | `PropertiesPanel.qml:105-145`: a Keywords gomb a `KeywordsDialog` párbeszédablakot nyitja; a jobbklikkes Edit Tags esemény lapváltást kér. `PhotoViewerRightPanels.qml:17-42,61-105`, `PhotoViewerState.qml:155-171`: a néző Tags-panelje az aktuális, egyetlen képre hat; a gyors nézőben nem jelenik meg. A nézőbeli TagsPanel nem kap `readOnlySelection` értéket, ezért annak alapértéke `false`; ez eltér a `KeywordsDialog` saját ellenőrzésétől. | Ne tekintsük a nézőbeli ablaknyitást teljes paritásnak. Ghidra-kör kell a Properties-panel callback céljához és a viewer engedélyezéshez; addig nincs fejlesztői következtetés. |
| **Add Tag mező:** a `0x0063bb30` vessző (`0x2c`) mentén bontja a beírt szöveget, és a nem üres tokeneket külön adja hozzá a `0x0063bed0` útján. Üres értéknél `TagPanel::notify_notext`, részhibánál `Some of the text you entered could not be added as a tag.` üzenet jelenik meg (`0x0063bb9d-0x0063bbd9`, `0x0063bd90-0x0063bdb4`). **A tokenizálás egy diszasszembly-útból feltételes.** Kijelölés-, videó- és read-only engedélyezési feltétel: `NINCS MEG`. | `TagsPanel.qml:49-57,75-100`; `keywords_controller.py:65-68,176-190`. A vessző szóközzé alakul, tehát a `tag1, tag2` egyetlen címkévé válik. A bevitel csak kijelöléskor és írhatónak jelzett kiválasztásnál aktív (`TagsPanel.qml:14-25,79-90`). | Bizonyított bemeneti eltérés: vesszőnél az eredeti több címkét dolgoz fel, a jelenlegi egyet. A beírás elfogadási és részhiba-szabályát a bináris writer út feloldásával kell pontosítani. |
| **Quick Tags gomb:** a `quicktag_%d` esemény a `0x0063a5e0` eseménykezelőtől a `0x0063bed0` add útig jut. A bináris panelen tíz szerkeszthető hely van (`0x0083efa2`, határ `0xa`); két felső hely a `Preferences\quicktags::recent0/1` értékeknek foglalható le. Hiányzó `quicktags::enable_recents` alapértéke `1`. A recent frissítés az első két értékhez pontos, kis/nagybetűt megkülönböztető UTF-16 egyezést használ (`0x0063b960`); egyező recentnél nem rendez át, új címkénél az új kerül a 0. helyre, korábbi 0. az 1. helyre csúszik. **Ezeket a helyeket két bináris út egyezése támasztja alá.** | `TagsPanel.qml:210-218,260-353`; `keywords_controller.py:21-40,280-316,334-397`. Tíz kézi hely és két recent hely van. A jelenlegi recent-egyezés Unicode `casefold`-ot használ (`:297-316`), ezért eltérhet a bináris pontos egyezésétől. | Az UTF-16 pontos egyezést kell megtartani, ha a recent címke kis/nagybetűben tér el. A tízes kiosztás és a recent alapérték megegyezik. |
| **Quick Tags konfiguráció / Autofill:** a `0x0083ea00` konfigurációs ablak tíz mezőt, recent kapcsolót, `quicktagconfig/autofill`, OK és Cancel vezérlőt kezel. A `0x0083f580` Autofill esemény egyszeri műveletként üres mezőket tölt, a recent helyek foglaltságához igazítva indul. A jelöltlista forrása és a kitöltési szabály a lenti kiegészítésben feloldva; a jelöltek bejárási sorrendjének alapja (a könyvtár rekordjainak sorrendje) `NINCS MEG`. | `QuickTagsConfigDialog.qml:5-7,41-75,127-158`; `keywords_controller.py:334-397`. A jelenlegi autoFill beállítás tartós QSettings-kapcsoló; a gombok olvasásakor dinamikusan tölti az üres helyeket az index gyakorisági sorrendjéből. | Eltérés: az eredeti egyszeri mezőkitöltés helyett a jelenlegi tartós, megjelenítéskori feltöltést ad. A jelöltforrás/sorrend feloldása előtt a funkció pontos fejlesztési specifikációja nyitott. |
| **Címkesor helyi menü:** a `0x00735480` menüépítő sorrendje: Add this tag to entire selection, Search for items with this tag, Remove this tag. A `0x0063b430` kezeli a címkesor jobbklikkjét. A bináris `0x0065b160` 30 fölötti kijelölésnél nagy műveleti megerősítést mutat, de a hívás nem lett hozzárendelve minden címke-belépési ponthoz. | `TagContextMenu.qml:27-40`; `MainRightDrawer.qml:89-95`; a fő panel hozzáadását `MainLibrarySelectionState.qml:148-158` 30 fölötti elemszámnál megerősíti. | Eltérés: a három helyi menütétel jelenlegi sorrendje Remove, Search, Add; állítsuk az eredeti sorrendre. A 30 fölötti eredeti megerősítés és a konkrét művelet kapcsolata nyitott, ezért annak általánosításáról ne döntsünk. |
| **Címke törlése:** a Tags eseménykezelő `removetag` ága a megjelenített címkét a `0x0063d670` útján oldja fel, majd a `0x0063c5a0` listamódosítóhoz jut. Azt, hogy vegyes többképes állapotban mely fájlok íródnak, egyenkénti hiba hogyan terjed, és az eredmény visszavonható-e, a lokális út nem dönti el. `NINCS MEG`. | A sor melletti X és a helyi menü Remove tétele is a kijelölt sorokon hív eltávolítást (`TagsPanel.qml:180-204`, `MainRightDrawer.qml:85-87`; viewerben `PhotoViewerRightPanels.qml:86-90`). `keywords_controller.py:193-202` minden kiválasztott sor kulcsszólistájából eltávolítja a megegyező címkét. | A jelenlegi vegyes kijelölési eredmény statikusan egyértelmű; az eredetit a `0x0063c5a0` callback utáni íróút vagy eredeti Picasa-mérés nélkül nem lehet hozzá minősíteni. |

**Kiegészítés (2026-11-15): a Quick Tags Autofill jelöltforrása, sorrendje és kihagyási szabálya.** Statikus olvasás: utasításszintű diszasszembly a `0x0083f210`, `0x0083f3d0`, `0x0083f3f0`, `0x0083f580`, `0x0083f8f0`, `0x0083f2f0`, `0x0063d260`, `0x0063d550`, `0x00639c00`, `0x00437380`, `0x004936c0`, `0x004939e0`, `0x009881d0` és `0x009869a0` függvényen. A `0x0083f580` és `0x0063d260` esetében a `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt` dekompilálása külön úton ugyanezt adja. Futásidejű Picasa-mérés nincs. Fokok: **megerősített** = két független út, **erős** = egy út, egyértelmű utasításokkal, **feltételes** = következtetés.

1. **Hatás: egyszeri szerkesztési művelet, a mentés a bezárásig vár (megerősített).** A `quicktagconfig/autofill` vezérlő eseménye a `0x0083f210` ablakkezelőből (vtábla `0x00cc008c`) a `0x0083f580`-ra jut. Az csak a tíz szerkesztőmezőt állítja (`vtbl+0x34`), preferenciát nem ír. A `quicktags::tag%d` értékeket kizárólag a `0x0083f3f0` menti (a `0x0083f3d0` hívja a `0x10` eseményre; az üres mező `]empty` jelölőt kap), és kihagyja, ha a `[ablak+0xd5c]` Mégse-jelző be van állítva (`0x0083f24e`). Az Autofill tehát nem tartós beállítás: a mezők a bezárásig szerkeszthetők, a Mégse elveti őket. A recent-jelölőnégyzet értéke ezzel szemben azonnal íródik (`0x0083f2f0`, majd a preferencia-író `0x00401900`), és a `0x0083f210` Mégse ága csak a jelzőt állítja és bezár, a kapcsolót nem állítja vissza (erős: a végigkövetett utakban nincs visszaállító kód, mérés nincs).
2. **Jelöltforrás: a teljes könyvtár címkekészlete, nem a kijelölés (erős).** A `0x0083f580` jelöltjeit a `0x0063d260([ablak+0x268], lista, 100)` adja. A `[ablak+0x268]` a Tags-panel: a `0x0063d840` adja át a `0x0083e800` konstruktornak. A forrástömb a panel `+0x2c0` listája (darabszám `+0x2c4`), amelyet egyedül a panel `0x00639c00` betöltő virtuális metódusa tölt (`TagPanel` vtábla `0x00ca0aa4`, 32. hely) a `0x00437380([0xd67668]+0x1034, &panel+0x2c0)` hívással. A `0x00437380` a könyvtár kulcsszó-tárolójának (`db+0x17d8`, zárral védett) sztringkészletét kérdezi le (`0x00411910`, `0x00411210`, `0x004939e0`), minden elemet vesszőnél (`0x2c`) tokenekre bont (`0x009881d0`: tokenenként legfeljebb `0x80` bájt, szóközlevágás nincs), a tokeneket új sztringkészletbe teszi (`0x00493660`, `0x004936c0`), majd a készlet tömbjét sorrendben adja ki (`0x004939e0`). Hogy a tároló kulcsszó-tároló, azt a használat erősíti: a Tags-panel `0x0063ae00` függvényéből hívott `0x00437550` ugyanezt az objektumot elemenként vesszővel bontja.
3. **Jelöltsorrend: első előfordulás, nincs rendezés és nincs gyakoriság (erős; a negatív állítás csak a végigkövetett láncra érvényes).** A `0x004936c0` készlet kivonattal és bájtonkénti egyenlőségvizsgálattal egyedít, számlálója nincs, az új elemet a tömb végére fűzi. A `0x004939e0` és a `0x0063d260` indexsorrendben másol, a `0x0063d550` szűrő csak kihagy. A láncban sehol nincs összehasonlító vagy rendező hívás. Az egyedítés kis- és nagybetűre érzékeny (bájtra pontos). Ez **helyesbíti** a korábbi „valószínűleg a gyakori címkék" feltevést. A készlet tömbjébe az internáló `0x006a2a60` fűz (`[tábla+0xec][i]` sztring a `tábla+0x5c` készletbe); ezt a tábla olvasó metódusai hívják (például `0x006a5060`, amely a `0x006a41e0` keresés mellett internál), ezért az „első előfordulás" a rekordok olvasási sorrendje. Azt, hogy ez az adatbázis betöltési sorrendje vagy a felület első olvasásainak sorrendje, statikusan nem döntöttem el (feltételes).
4. **Mezősorrend és kihagyás (megerősített: az utasításszintű olvasás és a Ghidra-dekompilálás egyezik).** A kezdőmező S = 2, ha a `quicktags::enable_recents` (alapérték 1) be van kapcsolva, különben 0; a preferenciát a kattintás pillanatában olvassa, és a recent-jelölőnégyzet (`0x0083f2f0`) azonnal írja. Az i = S..9 mezőkön növekvő sorrendben megy végig (mező: `ablak+0x26c+i*0x118`). A mező szövegét előbb a `0x009869a0` UTF-8-tudatos szóközlevágáson engedi át; nem üres mezőt kihagy, és nem fogyaszt jelöltet. Az üres mezőbe a lista következő olyan jelöltjét írja, amelyre a `0x0083f8f0` nem igaz: (a) nem szerepel az S..9 mezők nyers szövegében (bájtra pontos egyezés; a két recent mezőt nem nézi), és (b) nem szerepel az ablak „már betöltött" listájában (`ablak+0xd60`, a konstruktor üresre állítja, tehát ablakonként új; legfeljebb 100 elem). A kizárt jelöltet az adott lefutásban végleg átlépi. Beírás után a jelölt a (b) listába kerül. Ha a lista elfogy, a többi üres mező üres marad. Következmény: ha a felhasználó ugyanabban az ablakban kiüríti az Autofill által töltött mezőt, az újabb kattintás már a következő jelöltet teszi be.
5. **A jelöltből kiesnek a recent értékek (erős).** A `0x0063d550` kihagyja azt a jelöltet, amely bájtra egyezik a két recent értékkel (`panel+0x2c8`), ha a panel `+0x350` jelzője (a `quicktags::enable_recents` másolata, a `0x00639c62` és `0x0063c80a` állítja) be van kapcsolva. Mellékhatás: a szűrő a panel másolatát olvassa, a kezdőmező a friss preferenciát, tehát a jelölőnégyzet átváltása és az OK között a kettő eltérhet (feltételes: a másolat frissítése csak a `0x0063c7d0`-ban látszik).
6. **A gomb állapota (erős).** A `0x0083ea00` felépítéskor (`0x0083efc5`) ugyanazt a `0x0063d260`-at 10-es korláttal hívja; ha a lista üres, a `quicktagconfig/autofill` vezérlő `+0x20e` bájtját 1-re állítja (`0x0083f008-0x0083f030`). Ugyanez a bájt a `base_0` és `base_1` vezérlőn a recent-jelölőnégyzetet követi (`0x0083f2f0`), így tiltást vagy elrejtést jelent; melyiket, az mérés nélkül nem dönthető el. A gomb tehát nem használható, ha nincs jelölt.

**Eltérések a jelenlegi PicasaPy-tól** (`keywords_controller.py:320-336,378-398`, `QuickTagsConfigDialog.qml:57,71-76,144-158`):

- Tartós, olvasáskor számolt `autoFillFrequent` kapcsoló az eredeti egyszeri gombja helyett (ismert, 5. jegytörzs).
- Sorrend: a PicasaPy gyakoriság szerint csökkenő, holtversenynél ábécé (`:332`); az eredeti nem rendez, a készletbe kerülés (első előfordulás) sorrendjét adja.
- Egyezés: a PicasaPy `casefold`-dal egyedít és szűr (`:329,390,394`); az eredeti bájtra pontos.
- Foglalt helyek: a PicasaPy `quickTagButtons` a felső két helyre a recent értéket írja, és ha kevesebb mint két recent van, ott `""` marad (`:386-388`); a következő `"" in labels` ág ezeket is feltölti a gyakori címkékkel (`:389-397`). Az eredeti bekapcsolt recent mellett a 0. és 1. mezőt soha nem tölti.
- A „már betöltött" lista és a 100 jelöltes plafon nincs meg; az Autofill gomb nem tiltódik le jelölt hiányában.
- Mégse: a PicasaPy `onRejected` ága a recent-kapcsolót is visszaállítja (`QuickTagsConfigDialog.qml:71-76`); az eredeti Mégse a mezőket elveti, de a már kiírt `quicktags::enable_recents` értéket statikusan nem állítja vissza (erős).

**Nyitott, pontos következő lépéssel:**

- Ghidra-kör kell: 0x006a5060 - a kulcsszó-tábla (a `db+0x17d8` objektum `+0x54` belső táblája) olvasó metódusa; a `0x006a2a60` internálást hívó többi olvasó közvetlen szomszédai: `0x006a5590`, `0x006a5a60`, `0x006a5c60`, `0x006a61f0`, `0x006a63f0`. Kérdés: a kulcsszó-tábla rekordjait az adatbázis megnyitásakor járja-e végig valaki (akkor az adatbázis rekordsorrendje a jelöltsorrend), vagy lustán, az első olvasáskor internál (akkor a felület olvasási sorrendje); és kikerül-e a címke a készletből, ha az utolsó képről is törlik [blokkoló a pontos jelöltsorrendhez, nem blokkoló a kihagyási szabályokhoz].
- Ghidra-kör kell: 0x006393b0 - a Tags-panel gyára (a `0x00639440` konstruktor egyetlen hívója): a panel példánya mikor jön létre és semmisül meg, és kik hívják a 32. vtábla-helyet (`0x00ca0aa4` = `0x00639c00`, `call [reg+0x80]`). Kérdés: a `+0x2c0` lista csak a panel létrehozásakor töltődik, vagy megjelenítéskor és címkeváltozás után is; ettől függ, hogy az Autofill friss vagy pillanatképes listát kap [nem blokkoló].
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4023`): a kimenet részben dönt. A `0x006393b0` (`:4023-4046`) a `TagPanel::ResCreate` osztály (`0x00ca0ae8`, 5 bejegyzés) 5. bejegyzése (`0x00ca0af8`, ez az egyetlen hivatkozója, nincs közvetlen hívó): `0x470` bájtot foglal (`0x0097c5d0`) és a `0x00639440` konstruktort hívja; a konstruktor a `TagPanel::vftable` (`0x00ca0a24`) címét írja a példányba (`0x0063945a`). A `ResCreate` statikus példányát (`0x00d35d34`) a `0x0040bf70` indulási regisztráló függvény adja át a `0x009ccc50`-nek (`0x0040c29e`), tehát a **gyár induláskor regisztrált**, a panelpéldány tényleges létrehozását (és megsemmisítését) az erőforrás-betöltő végzi, ennek ideje a kimenetből nem látszik. A 32. vtábla-hely (`0x00ca0aa4` = `0x00639c00`) hívóit a kimenet nem tartalmazza (`call [reg+0x80]`, az index nem látja). Az index szerint a `0x00639c00` (785 bájt) a `Preferences`, `editpanel/preview`, `i18n\tagpanel_text.xml`, `quicktags::enable_recents`, `icons/label`, `%s/taglist`, `%s/removetag` sztringeket használja, és hívja a `0x00437380`-at (a jelöltek forrása), vagyis a panel felépítő/betöltő metódusa; **hogy a `+0x2c0` lista csak a létrehozáskor, vagy megjelenítéskor és címkeváltozás után is töltődik, a kimenet nem dönti el**, mert a `0x00639c00` törzse nincs benne.
- Ghidra-kör kell: 0x00639c00 - a Tags-panel felépítő metódusa (a 32. vtábla-hely): mikor és hányszor fut (csak létrehozáskor, vagy minden megjelenítéskor), a `+0x2c0` lista itt töltődik-e a `0x00437380`-ból, és mi hívja a `[reg+0x80]` vtábla-hívással (az erőforrás-betöltő `0x009ccc50` környezete) [nem blokkoló]
- `NINCS MEG`: futásidejű eldöntő mérés a sorrendre. Megszerzés: Colab-feladat az eredeti Picasa 3.9-cel; három mappa, rövid, ismert nevű képekkel és ismert beolvasási sorrenddel, olyan címkékkel, ahol a gyakoriság és az első előfordulás sorrendje eltér (például a `b` címke 5 képen, az `a` címke 1 képen, a `b` az első mappában); Quick Tags konfiguráció, Autofill, a tíz mező szövege rögzítendő recent be- és kikapcsolva, majd a mezők kiürítése után újabb Autofill.

### Hatás és hibaágak a jelenlegi forrásban

- A PicasaPy a kijelölt képek címkeunióját listázza; egyelemű és többes kijelölésre ugyanazt az útvonalat használja (`keywords_controller.py:108-136`). A címke hozzáadása deduplikál; a törlés a kijelölt sorokon azonos címkét távolít el (`:176-202`). A fő Tags-panel/Quick Tags út több mint 30 kijelölt képnél megerősítést mutat (`MainLibrarySelectionState.qml:148-158`, `MainDialogs.qml:54-84`); a nézőbeli Tags-panel az aktuális egy képet célozza (`PhotoViewerState.qml:170-171`).
- JPEG-nél a `write_iptc_keywords` az IPTC Keywords mezőt írja; hamis eredmény vagy íráskivétel után a címke `.picasa.ini` `keywords=` CSV-be kerül. Más kiterjesztésnél közvetlenül az ini-út fut (`keywords_controller.py:204-243`). A módosított képszakaszokhoz `with_backuphash` kerül, a mentés `update_document(..., backup=True)` hívással történik (`:244-258,267-268`).
- A fő panel írásvédettségi előellenőrzése mappaszintű írás/törlés próbát használ, és a kijelölésben bármely sikertelen mappa esetén letiltja a bevitelét (`keywords_controller.py:138-174`, `MainRightDrawer.qml:68-75`). Ez nem fájlattribútum-ellenőrzés. A néző TagsPanel nem adja át ezt az ellenőrzést (`PhotoViewerRightPanels.qml:71-90`, `TagsPanel.qml:14-25`), ezért ott a bevitel a `hasSelection` alapján marad aktív. A JPEG IPTC hiba ini-tartalékot és látható hibaüzenetet eredményez; ini-írási hiba üzenetet ad, leállítja a további mappákat, és a jelenlegi mappa index-szinkronja kimarad (`keywords_controller.py:229-276`). Az IPTC-írás az ini-frissítés előtt történik, ezért részleges lemezállapot lehet.
- Sikeres ini-frissítés után a mappafa SQLite-indexe `sync_tree` hívással frissül (`keywords_controller.py:274-275`), utána az aktuális keresési/mappa nézet újratöltődik (`:276`, `controller_sync_mixin.py:65-130`). A címke helyi menü keresési tétele a keresőmezőbe írja a címkét és elindítja a keresést (`MainRightDrawer.qml:93-95`, `MainToolbar.qml:129-133`). A végső rács- és kijelölési állapot futásidejű ellenőrzés nélkül `NINCS MEG`.
- A binárisban a `keywords=%s\n` sztring előfordulása és a `0x0068b320` függvény önmagában nem bizonyítja, hogy a Tags add/remove út oda ír. A `0x0063bed0` lokális útja az `IKeywordUpdate` felület `+0x284` részén keresztül frissít UI/modell állapotot, a `0x0065b4b0` a `0x005c76b0` kijelölés/listaépítőhöz továbbít. A meglévő `0x005c76b0` dekompilálás az indirekt `0x005c7710` visszahívás tényleges célját és a fájlírót nem oldja fel.
- Az eredeti `.picasa.ini`/IPTC írás, index és keresés frissítése, rács/kijelölés végállapota, visszavonhatóság, fájlattribútum-írásvédelem, írási hiba és részleges végrehajtás: `NINCS MEG`. A címke-panel `keywords/readonly_file` és `keywords/readonly_label` erőforrásai igazolják, hogy read-only állapothoz tartozik vezérlő és tájékoztató szöveg; a pontos detektor és hibaág nem.

### Bizonyíték-nyilvántartás

| Érték / állítás | Forrás |
|---|---|
| Bináris változat és SHA-256 | `bináris (Picasa3.exe 3.9.141.259; 644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96)` |
| `View > Tags` rekordkód `0x9d2c`; `0x9d71` Properties | `bináris (0x00559150; 0x0065ab50)` |
| Ctrl+K és Ctrl+T közös Tags-toggle | `bináris (0x005e60d0; case 0x4b, 0x54; 0x0065ab00)` |
| Aktív Tags ismételt toggle és más lapra váltás | `bináris (0x005d9760; 0x005d99a0; 0x005d9ad8-0x005d9b49)` |
| Vesszőnkénti Add Tag tokenizálás és részhibaüzenet | `bináris (0x0063bbdc-0x0063bbf5; 0x0063bd90-0x0063bdb4)` |
| Tag sor helyi menü címkéi és sorrendje | `bináris (0x00735480; 0x0063b430)` |
| Tíz Quick Tags mező és két recent hely | `bináris (0x0083efa2; 0x0063c120; 0x0063c7d0)` |
| Quick Tags recent alapérték és írási szabály | `bináris (0x0063c7d0; 0x0063b960; 0x0063c120)` |
| Quick Tags Autofill egyszeri művelet | `bináris (0x0083ea00; 0x0083f580)` |
| Add/remove író callback és eredeti lemezvégállapot | `NINCS MEG` |
| PicasaPy `.jpg/.jpeg` IPTC, ini-tartalék, ini és index út | `keywords_controller.py:204-276` |
| 7022 címkézési mérőfutás az archívumban | `NINCS MEG` |

### A két független út

- **A út, utasításszintű bináris olvasás:** `0x00559150` rekordmezőiből a feliratot és parancskódot a `0x0065ab50` dispatcherig követtem; az Add Tag útban a `0x0063bb30` vessző-split és a `0x0063bed0` hívás látszik; a `0x005d9760` összehasonlítás elválasztja az azonos aktív lapra érkező toggle-t a lapváltástól.
- **B út, külön UI-adat/xref út:** a bináris string/xref adatok a Tags panel objektumaihoz és a `thumbui/tags_toggle` eseményhez vezettek; a meglévő `0x0063a5e0` Ghidra-kimenet külön azonosítja az `addtag`, `removetag`, `quicktag_%d` és `quick_config` eseményeket. A panel helyi menüjének rekordjai a `0x00735480`-ban külön sorban, külön kódmezőkkel állnak. Ez az út a belépési és menüpont-azonosítást alátámasztja, de nem igazolja a lemezírót.
- **Egyezés:** a View > Tags rekord `0x9d2c` és a `thumbui/tags_toggle` parancs egyezik a két út szerint. A Quick Tags tíz mező/két recent kiosztás egyező bináris konfigurációs és frissítő útból jön. A fájl-/metaadat-hatásra nincs második, független út.

### Cáfoló kísérlet

- **Menürekord:** megpróbáltam a közeli `0x9d71` kódot a `&Tags` szöveghez párosítani. A rekordbáziscím `0xd6e018`-hoz tartozó kódmező `0xd6e022 = 0x9d2c`; a dispatcher `0x9d71` ága `thumbui/properties_toggle`, míg `0x9d2c` ága `thumbui/tags_toggle`. A felcserélt párosítás cáfolódott.
- **Toggle:** ellenőriztem azt az alternatívát, hogy az aktív Tags-re ismételt parancs panelváltásként újranyitja a lapot. A router az aktív metadata lap karaktereit hasonlítja az érkező eseményhez; egyezéskor a `thumbui/toggle_right_drawer` hívásra jut, az explicit Tags-lap-bekapcsoló ág csak eltérő állapot esetén fut. Az alternatíva a statikus útvonal alapján cáfolódik; futásidejű Picasa-mérés továbbra sincs.
- **Autofill:** ellenőriztem, lehet-e a `quicktagconfig/autofill` tartós kapcsoló. A `0x0083f580` az üres szerkesztőmezők setterét hívja; a vezérlő útján nem találtam tartós Autofill-beállítás kulcsát. A kontrollt a `0x0083ea00` konfiguráció-építő és az `autofill` erőforrás is alátámasztja. A jelöltlista pontos forrása/sorrendje ettől még nyitott.

### A jegy „Kész, ha” pontjai

1. ⛔ **Minden belépési pont, engedélyezés, egy/több kép, videó és vegyes címkeállapot:** a View Tags, Ctrl+T, Ctrl+K, tálcagomb, Add Tag, Quick Tags és címkesor-menü ismert útja fel van térképezve; az eredeti kiválasztási, videó/read-only kapu, a viewer callback és a vegyes törlés hatása nyitott.
2. ⛔ **Panel, alapérték, javaslatlista és megjegyzett beállítás:** a bináris 10 kézi mező, két recent hely és one-shot Autofill ismert; az Autofill jelöltforrás/sorrend, a viewer ablak/panel célja és az eredeti mezők végső mentési/Cancel viselkedése nincs teljesen lezárva.
3. ⛔ **Fájlrendszer, IPTC/XMP, `.picasa.ini`, index, keresés, rács, kijelölés, vegyes törlés és undo:** a jelenlegi PicasaPy-forrás végig követhető; az eredeti bináris metadata-/fájlíró és végállapot hiányzik.
4. ⛔ **Read-only, íráshiba és részleges végrehajtás:** a jelenlegi PicasaPy-út le van írva; az eredeti Picasa hibaágai és részleges eredményei bináris callback-feloldás vagy mérés nélkül nem dönthetők el.

### Javasolt fejlesztői jegytörzsek

#### 1. A Nézet > Tags és Ctrl+K ismételt aktiváláskor zárja be az aktív fiókot

**Eredeti:** a `0x005d9760` az aktív `Preferences\active_metadata_tab` és a bejövő Tags-toggle egyezésekor a `thumbui/toggle_right_drawer` hívja; Ctrl+K és Ctrl+T közös `0x0065ab00` út.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A Tags-toggle aktív Tags lap esetén bezárja a fiókot (`0x005d9760`, `0x005d99a0`); Ctrl+K és Ctrl+T azonos út (`0x005e60d0`, `0x0065ab00`). | A Nézet menü és Ctrl+K csak megnyit (`PicasaViewMenu.qml:94-109`, `MainKeyboardShortcuts.qml:101-108`, `MainWindowLibraryActions.qml:17-23`). Ctrl+T és felső tálcagomb már vált (`MainKeyboardShortcuts.qml:320-334`, `TrayTopRow.qml:298-312`). | A Nézet > Tags és Ctrl+K út ugyanúgy váltson, mint az eredeti: másik lapról Tags-re, aktív Tags-ről fiókbezárásra. |

**Kész, ha:** könyvtár-nézetben nyitott Tags panelnél a Nézet > Tags és Ctrl+K bezárja a fiókot; zárt fióknál vagy másik aktív lapnál Tags-re vált. Ctrl+T és a felső panelgomb azonos eredményt ad. Viewer alatti paritást csak az eredeti kapu feloldása után kell megadni.

#### 2. Az Add Tag vesszővel elválasztva több címkét adjon hozzá

**Eredeti:** a `0x0063bb30` a vesszőn (`0x2c`) külön tokenekre bontja a szöveget, tokenenként ad hozzá; hibás elem esetén a többi érvényes elem feldolgozása után figyelmeztet.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Vesszőnként tokenizál, külön hozzáadási kísérlet és részhibaüzenet (`0x0063bbdc-0x0063bdb4`). | `TagsPanel.qml:49-57`, `keywords_controller.py:65-68,176-190`: a vessző szóközzé alakul, egy címke készül. | A bevitelt vesszőnként bontsa, üres részeket hagyja ki, a tokeneket külön dolgozza fel; részhiba esetén a sikeres címkék maradjanak meg, és legyen látható figyelmeztetés. |

**Kész, ha:** `tag1, tag2` két külön címkét hoz létre; üres vesszőrészek nem hoznak létre címkét; egy hibás token nem akadályozza az érvényes tokenek feldolgozását, és az eredmény látható.

#### 3. A címkesor helyi menüje az eredeti sorrendet mutassa

**Eredeti:** a `0x00735480` menüépítő sorrendben az Add this tag to entire selection, Search for items with this tag, Remove this tag elemeket állítja elő.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Add, Search, Remove (`0x00735480`, `0xd6f840` rekordtömb). | Remove, Search, Add (`TagContextMenu.qml:27-40`). | Rendezze a három menüpontot Add, Search, Remove sorrendbe; a műveletek célját ne változtassa. |

**Kész, ha:** a Tags-panel címkesorának jobbklikk-menüjében ez a sorrend látszik, mindhárom tétel a jelenlegi megfelelő műveletet indítja.

#### 4. A recent címke összevetése kövesse az eredeti pontos egyezést

**Eredeti:** a `0x0063b960` a két recent értéket pontos UTF-16 karakter-összevetéssel hasonlítja; csak pontos egyezéskor nem rendez át.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A már azonos karakterláncként szereplő recent nem rendeződik át (`0x0063b960`, `0x0063c120`). | A `keywords_controller.py:297-316` Python `casefold`-ot használ a recent egyezéshez. | Az ismételt recent keresése az eredeti pontos, kis/nagybetű-érzékeny karakterlánc-egyezését használja. |

**Kész, ha:** azonos címke ismétlése nem rendez át; csak kis/nagybetűben különböző címke új értékként kerül előre és a korábbi 0. helyet a 1. helyre tolja.

#### 5. A Quick Tags Autofill egyszeri művelet legyen

**Eredeti:** a `quicktagconfig/autofill` a `0x0083f580` útján egyszer tölt üres kézi mezőket; nem kapcsol be tartós feltöltést. A recent helyek fenntartása dönti el, hogy az első vagy a harmadik mezőtől kezdődik a feltöltés. A jelöltek forrása és a kihagyási szabály feloldva (ld. az 5/b. jegytörzset); csak a rekordok bejárási sorrendje nyitott.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Egyszeri Autofill az üres Quick Tags mezőkre; a recent helyeket kihagyja, ha a fenntartás be van kapcsolva (`0x0083ea00`, `0x0083f580`). | Tartós `autoFillFrequent` beállítás, amely a megjelenített gombokat olvasáskor tölti (`QuickTagsConfigDialog.qml:144-158`, `keywords_controller.py:364-397`). | A tartós megjelenítési kapcsolót cserélje egyszeri mezőkitöltés műveletre; a jelöltek forrását, sorrendjét és kihagyását az 5/b. jegytörzs adja. |

**Kész, ha:** a művelet csak az üres, konfigurált mezőket írja; fenntartott recent hely esetén azokat nem tölti fel; a már beírt kézi címkéket érintetlenül hagyja; a gombok a mentett mezőértékeket mutatják, nem olvasáskor számítják újra a gyakori címkéket. A jelöltforrás, a kihagyás és a sorrend részletes feltételeit az 5/b. jegytörzs adja.

#### 5/b. A Quick Tags Autofill jelöltforrása, kitöltési sorrendje és kihagyási szabálya (kiegészítés, 2026-11-15)

**Eredeti:** a `0x0083f580` a `0x0063d260`-tól kapott jelöltekből tölti az üres szerkesztőmezőket. A jelöltek a könyvtár vesszővel bontott, bájtra pontosan egyedített címkéi a készletbe kerülés (első előfordulás) sorrendjében, legfeljebb 100, a két recent érték nélkül. Recent mellett a 2. mezőtől, nélküle a 0.-tól tölt, növekvő sorrendben; a nem üres mezőt kihagyja, és a mezőkben vagy az ablak már betöltött listájában szereplő jelöltet átugorja.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Egyszeri gomb; a kezdőmező 2 (recent be) vagy 0; az üres mezőket tölti növekvő sorrendben, a nem üreset jelölt fogyasztása nélkül kihagyja (`0x0083f580`, `0x009869a0`). | A helyeket a `quickTagButtons` számolja olvasáskor; ha kevesebb mint két recent érték van, a felső két hely is betelhet (`keywords_controller.py:386-397`). | Az Autofill gomb csak a konfigurációs ablak mezőit írja; bekapcsolt recent mellett a 0. és 1. mezőhöz soha nem nyúl. |
| Jelöltek: a könyvtár címkéi vesszővel bontva, bájtra pontos egyedítéssel, a készletbe kerülés sorrendjében, legfeljebb 100, a két recent nélkül (`0x0063d260`, `0x0063d550`, `0x00437380`, `0x004936c0`). | `_frequent_keywords`: gyakoriság szerint csökkenő, holtversenynél ábécé, `casefold`-dal egyedítve (`keywords_controller.py:320-336`). | A jelöltsorrend az első előfordulás legyen, ne a gyakoriság, és az egyedítés kis- és nagybetűre érzékeny. A pontos bejárási sorrend nyitott (a `+0x2c0` lista írója; a `0x006a5060` nem az, lásd a Ghidra-kiegészítés 3-at); addig a PicasaPy index sorrendje (`all_photos`) a közelítés, és a jegy ezt ki is mondja. |
| Kihagyás: az S..9 mezők nyers szövegében vagy az ablak betöltött listájában (legfeljebb 100) szereplő jelölt (`0x0083f8f0`, `ablak+0xd60`). | Csak a megjelenített helyek `casefold`-os halmaza (`:390-396`). | A kihagyás nézze a mezők szövegét és az ablakban már betöltött jelölteket, bájtra pontosan; egy kiürített, korábban betöltött mezőbe az ismételt kattintás a következő jelöltet tegye. |
| A gomb letiltott vagy rejtett, ha nincs jelölt (`0x0083efc5-0x0083f030`). | Nincs Autofill gomb, csak jelölőnégyzet (`QuickTagsConfigDialog.qml:144-158`). | A gomb legyen letiltva, ha nincs jelölt. |

**Kész, ha:** az Autofill gombra kattintva egyszer töltődnek az üres mezők, utána szabadon szerkeszthetők; az OK ment, a Mégse visszaállít. Bekapcsolt recent mellett a 0. és 1. mező érintetlen akkor is, ha kevesebb mint két recent érték van; kikapcsolva a 0. mezőtől tölt. Az a mező, amelynek szövege szóközlevágás után nem üres, érintetlen, és nem fogyaszt jelöltet. Jelölt nem ismétlődik a mezőkben (a `Nap` és a `nap` két külön jelölt), a recent értékek nem jelöltek, és kiürített mezőbe az újabb kattintás a következő jelöltet teszi. Jelölt nélkül a gomb le van tiltva. A teszt valódi gombkattintással fut, a tíz mező szövegét ellenőrzi, mindkét recent-állásban, üres, részben töltött és elfogyó jelöltlistával.

#### 6. A Tulajdonságok panel kulcsszó-sorának szerkesztése a Tags panelt kapcsolja

**Eredeti:** a `0x00638990` a kulcsszavas sorhoz `edit_keywords` (`0x9d2c`) tételt ad, ami a `0x0065ab50` -> `thumbui/tags_toggle` útra fut (Ghidra-kör, 2026-11-15).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A jobb oldali Tags panel kapcsolása (`0x0065ab50`). | `PropertiesPanel.qml:105-145`: a Keywords gomb a `KeywordsDialog` modális ablakot nyitja. | A Tulajdonságok kulcsszó-sorának szerkesztése a Tags panelt nyissa vagy zárja, ugyanazon az úton, mint a Ctrl+T. |

**Kész, ha:** a Tulajdonságok panel kulcsszó-sorából indított szerkesztés a jobb oldali Tags panelt kapcsolja; valódi kattintásos teszt.

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 425 tartozik.

- **`0x0063d260` és `0x0063d550`, a jelöltlista szűrése (425).** Megválaszolva. A
  `0x0063d260(panel, kimeneti lista, korlát)` a panel `+0x2c0` listájának
  (darabszám: `+0x2c4 >> 1`) elemein halad, a **forrás sorrendjében**, 0-tól a
  korlát (itt 100) alatti indexig. Minden elemre a `0x0063d550` dönt: ha igazat
  ad, az elem kimarad, különben a kimeneti lista végére kerül. A
  ciklusszámláló a **forrás elemeit** számolja, nem a megtartottakat: ha a
  forrás első 100 eleme között mindkét recent érték szerepel, 98 jelölt marad.
  Az 5/b. jegytörzs "legfeljebb 100, a két recent nélkül" szövegét ez
  pontosítja: a korlát a forrás elejére vonatkozik. A `0x0063d550(elem)`: ha a
  panel `+0x350` jelzője be van kapcsolva (olvasat: a recent-kapcsoló), a
  `+0x2c8` tömb első két elemével (a két recent érték) veti össze az elemet,
  **bájtonként, kis- és nagybetűre érzékenyen** (kisbetűsítés nincs), és
  egyezésnél `1`-et ad, az elem kimarad. Ha a jelző ki van kapcsolva, nem
  hasonlít, és minden jelölt megmarad. Ha a recent hely üres, és a jelölt is
  null vagy üres, az is egyezésnek számít (az üres jelölt kimarad). A
  `0x0063d260` hívói: `0x0083ea00` (`0x0083efc5`, a konfigurációs ablak) és
  `0x0083f580` (`0x0083f5d4`, az Autofill). A `0x0063d550` másik hívója a
  `0x0063c120` (`0x0063c27a`, a recent-kezelés); a hívás célja a kimenetből nem
  látszik, de a bájtpontos, kis- és nagybetűre érzékeny összevetés a 4.
  jegytörzs "pontos egyezés" állítását nem cáfolja. **PicasaPy:**
  `_frequent_keywords` gyakoriság szerint rendez, és `casefold`-dal egyedít
  (`keywords_controller.py:320-336`); ezt az 5/b. jegytörzs már rögzíti.
- **`0x006a5060` (425).** Megválaszolva, de **nem a feltett kérdésre**: nem
  bejárás és nem készletépítő, hanem kulcs szerinti rekordba író függvény. A
  `0x006a5060(tábla, kulcs, érték)` az indexet az `EAX` regiszterben kapja;
  `-1` indexre `-1`-et ad. A tábla zárja alatt (szálazonosítóval újrabelépő
  zár) a `FUN_006a41e0(tábla, kulcs, 0x13320001, &rekord, 1)` megkeresi a
  kulcshoz tartozó rekordot, a `FUN_006a70e0(tábla, rekord)` ellenőrzi (mindkettő
  nem nulla hibakódot visszaad), majd a rekord saját zárja alatt a
  `rekord+0x1dc` tömb `index`. elemét **felülírja** az `érték`-kel, ha az eltér,
  és jelez a táblának (`FUN_006a2a60(&tábla[0x13])`). Közvetlen hívói a kimenet
  szerint: `0x00425f60`, `0x00444ee0`, `0x004451a0`, `0x00456610`, `0x00467ca0`,
  `0x004a9e20`, `0x005a0f60` és `0x007b2cc0`; a `0x00437380` (az 5/b.
  jegytörzs jelöltforrása) közöttük **nincs** (közvetett hívás lehetséges, de
  ebből a kimenetből nem látszik). Következmény: a jelöltsorrendet nem ez a
  függvény dönti el; a sorrend a panel `+0x2c0` listáját töltő kódon múlik, ez
  nincs a kimenetben. **PicasaPy:** a közelítés változatlan (az index
  `all_photos` sorrendje, 5/b.).

**A jegy lezárhatósága: NEM zárható.** A 425 a "Kész, ha" 2. pontját (panel,
javaslatlista) viszi közelebb: a szűrés és a korlát pontos, de a jelöltek
**sorrendje** továbbra is blokkolt (a `+0x2c0` lista írója nincs meg). Az 1., a
3. és a 4. pont (belépési pontok, fájl- és metaadat-hatás, íráshiba) a 425-től
nem érintett: Windows-mérés, illetve a viewer-kapu Ghidra-köre kell.
**Fejlesztői teendő:** új jegy nincs; az 5/b. jegytörzs "Kész, ha" pontjához
javasolt kiegészítés: a jelöltkorlát (100) a forrás első elemeire vonatkozik, a
két recent kihagyása után tehát legfeljebb 98 jelölt marad; az üres jelölt
bekapcsolt recentnél kimarad.

### Nyitott kérdések

- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x005c76b0` kijelölésgyűjtő, nem metaadat-író; a `+0xeac` a `CAlbumSelectionNode` típusúvá alakított csomópont, a `vtbl+0xdc` közönséges albumnál `0x00401570` (azonnal 0), arcalbumnál `0x0078a6c0`. A címkeíró út nyitott.
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x0063c5a0` egyelemű listát ad át a fő ablak `+0x284` objektumának, felületi frissítő lépés; fájlírót és többképes törlést nem tartalmaz. A vegyes címkeállapotú törlés nyitott.
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x00638990` a Tulajdonságok panel listaelemének helyi menüje; a kulcsszavas sorhoz (`0xca`) az `edit_keywords` tétel `0x9d2c` paranccsal jár, ami a diszpécserben a `0x0065ab50`-re, a `thumbui/tags_toggle`-ra fut: **a jobb oldali Tags panelt kapcsolja, nem modális ablakot nyit.** Nálunk a Keywords gomb a `KeywordsDialog` párbeszédablakot nyitja, ez igazolt eltérés (6. jegyjavaslat).
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a Ctrl+K (`0x4b`) és a Ctrl+T (`0x54`) közös ága a `0x0065ab00` (`tags_toggle`); a billentyűt nem kezeli, ha az ablak módkódja (`+0x30d4`) 2, 4 vagy 6 (vágás, vörösszem, retusálás, szöveg, Picnik), vagy ha a `0x0056c420`, `0x0056c110`, `0x0057c430(4)`, `0x0057c3b0` ellenőrzők egyike igaz. A teljes képernyős nézőbeli elérhetőség ezeken múlik.
- Ghidra-kör kell: 0x0056c420 - a négy ellenőrző (`0x0056c420`, `0x0056c110`, `0x0057c430`, `0x0057c3b0`) melyik nézetállapotot jelöli; a Ctrl+K teljes képernyős nézőben működik-e [nem blokkoló]
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:1711`): a `0x0056c420` (`:1711-1733`) igaz (1), ha a `DAT_00d67914` nem nulla, a `0x009c2fc0` megtalálja a **`panelroot/acquirepanel`** nevű felületi csomópontot (a hívóhely disassemblye: `mov edx, 0xc8e6d8`) és annak `+0x20c` bájtja 0; különben 0. Vagyis ez az **Import (acquire) panel** állapota, nem a szerkesztőé vagy a nézőé. A másik három ellenőrző a disassemblyből: a `0x0056c110` ugyanígy a `thumbui/printpanel` csomópontot (`0x00c8f0f0`) vizsgálja; a `0x0057c430(maszk)` bitenként dolgozik (`-1` esetén mindet VAGY-olja, egyébként csak a megadott bitet): `1` = a `[ablak+0x344c]` csomópont `+0x20c` bájtja 0, `2` = a `0x00562d00()` igaz vagy az ablak módkódja (`+0x30d4`) 2, 4 vagy 6, `4` = a `[ablak+0x30f4]` és a `[ablak+0x34a4]` is nem nulla, `8` = a `0x0056c110()` igaz; a `0x0057c3b0` az ablak `+0x16c` listájában az első olyan `ytBasePanel`-leszármazottat keresi, amelynek `+0x20c` bájtja 0 és `+0x9c` virtuális metódusa igazat ad. **A Ctrl+K teljes képernyős nézőben:** a `0x0057c430(4)` pontosan akkor igaz, ha a `+0x30f4` és a `+0x34a4` is nem nulla; ha a `+0x34a4` a nézőt jelöli (ez a #6530 szerint nem igazolt), akkor a főablak ága a nézőben nem kezeli a Ctrl+K-t, a nézőbeli saját billentyűkezelőt viszont a kimenet nem tartalmazza, ezért ez nem dönthető el.
- Ghidra-kör kell: 0x0057c3b0 - a `+0x9c` virtuális metódus (mely `ytBasePanel`-leszármazottakon ad igazat), és a `[ablak+0x34a4]` mező írói (a néző nyitva-e); ugyanitt a teljes képernyős néző (OneUp) saját billentyűkezelője: kezeli-e a Ctrl+K-t [nem blokkoló]
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a jelöltlistát a `0x0063d260(obj[+0x268], lista, 100)` építi, legfeljebb 100 elemmel a forrástömb (`+0x2c0`, darabszám `+0x2c4`) sorrendjében, a `0x0063d550` szűrővel; a 10 mezőt a 2.-tól tölti, ha a `quicktags::enable_recents` be van kapcsolva, egyébként a 0.-tól, csak az üreseket; a `0x0083f8f0` kihagyja a mezőkben már szereplő jelöltet. Az 5. jegyjavaslat ezzel megvalósítható, a forrástömb jelentését a kiegészítés oldja fel: nem gyakoriság, hanem a könyvtár kulcsszó-tárolójának első előfordulási sorrendje.
- Megválaszolva (Ghidra 425): a `0x006a5060` nem bejáró és nem készletépítő, hanem kulcs szerinti rekordba író (a `rekord+0x1dc` tömb egy elemét írja); közvetlen hívói között a `0x00437380` nincs. A jelöltlista szűrése teljes (`0x0063d260`, `0x0063d550`): a forrás sorrendjében, a forrás első 100 eleméből, a két recent nélkül (bájtpontos, kis- és nagybetűre érzékeny egyezés, ha a `+0x350` jelző be van kapcsolva).
- Ghidra-kör kell: a panel `+0x2c0` listájának írója - a `0x00437380` és a `0x004936c0` törzse (a jelöltek forrása, 5/b.) és a lenti `0x006393b0` tétel; ebből dől el, hogy az adatbázis rekordsorrendje, a lusta internálás sorrendje vagy más a jelöltsorrend (a kulcsszó-tábla rekordjait az adatbázis megnyitásakor járja-e végig valaki, vagy lustán, az első olvasáskor internál); kikerül-e a címke a készletből, ha az utolsó képről is törlik [blokkoló a pontos jelöltsorrendhez]
- Ghidra-kör kell: 0x006393b0 - a Tags-panel gyára (a `0x00639440` konstruktor egyetlen hívója) és a 32. vtábla-hely (`0x00ca0aa4` = `0x00639c00`) hívói: a `+0x2c0` lista csak a panel létrehozásakor töltődik, vagy megjelenítéskor és címkeváltozás után is; ettől függ, hogy az Autofill friss vagy pillanatképes listát kap [nem blokkoló]
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4023`): lásd a fenti `0x006393b0` választ: a `0x006393b0` a `TagPanel::ResCreate` gyárbejegyzése (`0x470` bájt és a `0x00639440` konstruktor), induláskor regisztrált; a panel létrehozásának és a `+0x2c0` lista töltésének ideje a kimenetből nem dönthető el, a következő cél a `0x00639c00` (32. vtábla-hely).
- `NINCS MEG`: futásidejű eldöntő mérés az Autofill jelöltsorrendjére. Megszerzés: Colab-feladat az eredeti Picasa 3.9-cel, három mappa ismert beolvasási sorrenddel, olyan címkékkel, ahol a gyakoriság és az első előfordulás sorrendje eltér; recent be- és kikapcsolva a tíz mező szövege, majd a mezők kiürítése után újabb Autofill.
- `NINCS MEG`: az eredeti Picasa-mérés a fájlok SHA-256-jával és a `.picasa.ini` előtte/utána tartalmával, egy- és többképes JPEG, videó, vegyes címkeállapot, írásvédett fájl/mappa és írási hiba mellett. A hálózat nélküli kutatói körben ilyen mérőadat nem állt rendelkezésre; az új gyűjtéshez a felhős mérőkörnek izolált profilban rögzítenie kell az eredeti Picasa végállapotot.

### Zárókör: a jelenlegi forrás és a megmaradt bizonyítékok (2026-11-16)

Ez a zárókör a fenti korábbi „Nálunk” állításokat és fejlesztői javaslatokat
felülírja ott, ahol a munkafa mostani forrása mást mutat. A Ghidra-kiegészítés 3
megmarad; az alábbi kiegészítés a korábban nyitott tételeket újraminősíti.

#### Belépési pontok és a mostani forrás

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Nézet > Tags:** az eredeti lapváltó az aktív Tags lap ismételt kérésére bezárja a jobb oldali fiókot; másik lapról Tags-re vált (`0x005d9760`, `0x005d99a0`, `0x005d9ad8`). | A menü a `MainMenuBar.qml:384-385` útján a `MainWindowLibraryActions.qml:15-23` kapcsolóhoz jut. | A könyvtárnézetben egyezik. A korábbi, csak megnyitást állító fejlesztői javaslat elavult, nem kell hozzá külön jegy. |
| **Ctrl+T és Ctrl+K:** közös bináris Tags-panel kapcsoló (`0x005e60d0`, `0x0065ab00`); a magasabb szintű néző- és szerkesztőállapot-őrök teljes eredménye nyitott. | Mindkét gyorsbillentyű a `valtsFiokLapot("tags")` függvényt hívja (`MainKeyboardShortcuts.qml:110-113,328-334`); az engedélyezés könyvtárnézetre és nem szövegmező-fókuszra korlátozott (`MainWindowCommands.qml:229-233`). | A könyvtárnézetben egyezik. Az eredeti teljes képernyős nézőbeli és szerkesztőbeli engedélyezést a lent megadott mérés dönti el; a régi, Ctrl+K-ra külön megnyitást javasló sor nem aktuális. |
| **Add Tag:** vesszőnként bont, az üres részeket kihagyja (`0x0063bb30`); a bináris figyelmeztető szöveg egyes elutasított elemek esetére létezik (`0x0063bb9d`, `0x0063bd90`). | `TagsPanel.qml:50-63` vesszőnként külön kérést küld és az üres tokeneket kihagyja; a fő panel hibát jelez (`MainRightDrawer.qml:83-92`). | A tokenizálás egyezik. Az eredeti részhiba és a fájlírás hibájának pontos kapcsolata nem következik a feliratból, a mérés része. A régi „vessző helyett szóköz” fejlesztői javaslat már nem indokolt. |
| **Címkesor helyi menü:** Add, Search, Remove (`0x00735480`). | A jelenlegi sorrend Add, Search, Remove (`TagContextMenu.qml:27-41`). | Egyezik; a korábbi sorrendjavító javaslat elavult. |
| **Tulajdonságok > Edit Tags:** `0x00638990` eseménye a Tags-panel kapcsolójáig jut (`0x0065ab50`). | A gomb és a helyi menü `editTagsRequested` jelet ad (`PropertiesPanel.qml:129-162`); a könyvtár és a néző befogadója a Tags lapot kapcsolja (`MainRightDrawer.qml:149`, `PhotoViewerRightPanels.qml:38-42`). | A régi modális ablakra vonatkozó eltérés nem áll fenn. A `KeywordsDialog` példány jelenléte önmagában nem bizonyít megnyitást; a kattintási jel útját ellenőriztem. |
| **Quick Tags alapérték:** tíz kézi hely; a felső kettő a két recent értéknek foglalható; hiányzó `quicktags::enable_recents` alapértéke be van kapcsolva (`0x0083efa2`, `0x0063c7d0`). | Tíz szerkesztőmező (`QuickTagsConfigDialog.qml:122-131`); a két felső hely alapértelmezetten fenntartott (`keywords_controller.py:393-402`). | A darabszám és az alapérték egyezik. |
| **Quick Tags előzmény:** ismételt, már tárolt érték nem rendeződik át; a bináris összevetés pontos és kis-/nagybetű-érzékeny (`0x0063b960`, `0x0063c120`). | `keywords_controller.py:341-359` a pontos Python-karakterláncot keresi; egyezésnél visszatér átrendezés nélkül. | Egyezik; a korábbi `casefold`-javító javaslat a jelenlegi forrásra nézve elavult. |
| **Quick Tags Autofill:** egyszeri mezőkitöltő; a jelöltlista szűrője a panel forráslistájának első 100 elemére fut (`0x0083f580`, `0x0063d260`, `0x0063d550`). | A beállítóban egyszeri gomb van, a jelöltek az ablak megnyitásakor gyorsítótárba kerülnek (`QuickTagsConfigDialog.qml:50-58,68-75,151-169`; `keywords_controller.py:420-459`). A jelenlegi kód előbb kiszűri a legutóbbi címkéket, majd 100 jelölt után áll meg (`keywords_controller.py:428-442`). | Az egyszeri művelet egyezik. A korlát eltér: az eredeti előbb a forrás első 100 elemét veszi, aztán szűri a legutóbbi értékeket; nálunk a 100-as határ a szűrés után van. Az eredeti forráslista sorrendjét még mérni kell. |
| **Mégse és recent kapcsoló:** a meglévő diszasszembly szerint a kapcsoló eseménye azonnal írja a preferenciát (`0x0083f2f0`); a Mégse ágban nem azonosítottam visszaállító írást. | A jelenlegi párbeszéd megnyitáskor menti a két kezdőértéket, Mégse esetén pedig visszaírja őket (`QuickTagsConfigDialog.qml:68-83`). | Lehetséges eltérés, de a Picasa látható, kilépés utáni értéke csak egy statikus úton következtethető. A mérésben ellenőrizendő, ezért külön implementációs jegyet még nem nyitok. |
| **Címke törlése és vegyes kijelölés:** a `0x0063c5a0` út a kijelölési frissítés előtt az `IKeywordUpdate` interfész `+8` helyét hívja; a megvalósítás teljes fájlhatása nyitott. | A `keywords_controller.py:193-202` minden kiválasztott sorból eltávolítja a kis-/nagybetűtől függetlenül egyező címkét. | A Picasa vegyes címkéjű kijelölésének végeredménye a lemezen és a felületen mérendő; a régi „csak felületi frissítő” leírás túl erős volt, lásd a cáfoló kísérletet. |

#### A jelenlegi PicasaPy-hatás és hibák

- Egy címke hozzáadása a sor címkelistáját kis-/nagybetűtől függetlenül egyedíti; törléskor minden egyező alakot eltávolít a kijelölt sorokból (`keywords_controller.py:176-202`). Több kijelölt kép hozzáadásakor a fő panel 30 fölött megerősítést kér (`MainRightDrawer.qml:83-92`). A néző Tags panelje a nézett képet célozza (`PhotoViewerRightPanels.qml:76-103`).
- `.jpg` és `.jpeg` esetén a PicasaPy a teljes IPTC Keywords `2:25` mezőt írja, kulcsszavanként egy adatmezővel (`metadata/iptc_writer.py:48-58`). Ezen az úton XMP-író hívás nincs. Sikertelen IPTC-írás után, illetve más kiterjesztésnél a `.picasa.ini` `keywords=` vesszővel összefűzött értéke a tartalék (`keywords_controller.py:229-244`). A módosítás után a kód `backuphash`-t ír és az ini-t menti (`:245-269`).
- A fő panel előre mappaszintű írási próbát végez, egyetlen írásvédett mappa is tiltja a bevitelt (`keywords_controller.py:138-174`, `MainRightDrawer.qml:69-76`). A néző Tags paneljének nincs ilyen bekötése (`PhotoViewerRightPanels.qml:76-95`), ezért ott a komponens alapértéke érvényesül. Ez a PicasaPy forrás viselkedése; az eredeti engedélyezési paritás mérésre vár.
- IPTC-hibánál a kód ini-tartalékot próbál és a hibát jelenti, ha az ini-frissítés sikerült. Ini-írási kivételnél hibát jelent, a további mappákat leállítja; a hibás mappához a `break` miatt indexszinkron nem fut, de az aktív nézet újratöltése a ciklus után megtörténik (`keywords_controller.py:230-279`). Mivel az IPTC-írás az ini-frissítés előtt, képenként történik, a későbbi ini-hiba korábban módosított JPEG-et részleges állapotban hagyhat.
- Sikeres mappaírás után a kód frissíti a mappafát az SQLite-indexben és újratölti az aktív keresési vagy mappanézetet (`keywords_controller.py:276-279`, `controller_sync_mixin.py:65-130`). A `set_photos` lecseréli a modell sorait (`controller_photo_list_mixin.py:155-157`); ez a Python út nem üríti kifejezetten a `selectedIndexes` vagy `selectedIndex` értékeit (`MainLibrarySelectionState.qml:29-32`). A végső kijelölés és az eredeti rácsállapot egyezése nem következik ezekből a hívásokból.

#### A megmaradt „NINCS MEG” és Ghidra-kérdések újraminősítése

- **Eredeti lemezvégállapot, index és visszavonás: `NINCS MEG`.** A `0x0063bed0` és `0x0063c5a0` címek hívási lánca a `CThumbUI::IKeywordUpdate` felületig követhető, de a kiválasztott képeken végrehajtott virtuális műveletek, az IPTC/XMP/ini kiírás, a hiba utáni állapot és a visszavonás nem bizonyított. A régi `0x005c76b0` dekompilálás a kijelölésgyűjtőt írja le, nem zárja le ezt a távolabbi ágat.
- **Részleges eredeti mérés (job-242): `mérés (docs/specs/paritas-ellenorzes.md:831; docs/specs/picasa-beviteli-mezok.md:364-372)`.** Egy JPEG-hez címke került a Tags panelen; a képernyőn a `proba` az `AI image` fölött szerepelt és az első Quick Tag `proba` volt. Az ini kivonat `backuphash=33706` értéket tartalmazott `keywords=` sor nélkül. Az eredeti JPEG és a nyers mérőfájl a megadott mérési tárban nincs, így ez nem azonosítja a kép IPTC/XMP mezőjét vagy bájtszintű változását, és nem bizonyít többképes, videós, vegyes címkéjű törlési vagy hibás esetet.
- **Quick Tags listaéletciklus és sorrend: részben megválaszolva.** A Ghidra 425 kimenet igazolja a forrás első 100 elemét követő recent-szűrést, de nem a panel `+0x2c0` listájának létrehozási sorrendjét és frissülését. A jelenlegi kód `all_photos` indexsorrendet használ, az ablak megnyitásakor pillanatfelvételt készít. Az eredeti kimenetet kontrollált címkekészlettel kell rögzíteni.
- **Ctrl+T/K néző- és szerkesztőkapu: nyitott, de nem igényel külön Ghidra-kört.** A `0x005e60d0` állapotőrei diszasszemblyből részben ismertek, a teljes képernyős nézőbeli felhasználói eredményt egy billentyűpróba dönti el. A jelenlegi kód mindkét billentyűt letiltja a nézőben.
- **A korábbi `Ghidra-kör kell` sorok döntése:** a `0x005c76b0` és `0x0063c5a0` régi kérései a fájlírás statikus útját és vegyes kijelölés belső végpontját keresték. A kijelölt elemek virtuális hívásai most követve vannak, de azok fájlhatása nyitott; a mért végállapot dönti el a felhasználói viselkedést, ezért a belső függvénynév nem blokkoló. A `0x00638990` kérdést a meglévő Ghidra-kimenet megválaszolja: a Tulajdonságok útja a Tags lap kapcsolója. A `0x005e60d0` és a `0x0056c420` nézőállapot-őreinek belső jelentése helyett a billentyűpróba dönti el az elérhetőséget; a belső függvénynév nem blokkoló. A `0x0083f580` / `0x0063d260` / `0x0063d550` kérdésből a 425-ös kör feloldotta a korlátot és a recent-szűrőt; a `0x00437380`, `0x004936c0` és `0x006393b0` dekompilálásával keresett `+0x2c0` lista sorrendjét és frissülését ugyanennek a mérésnek a jelöltsorrend- és újranyitási próbája válaszolja meg. A belső listaépítő azonosítása nem külön blokkoló. Ezekre most nem kérek új Ghidra-kört.
- A `meroadat.tar` nem tartalmazott a címkézési műveletekhez név szerint illő mérési tagot. A korábbi `job-242` sor dokumentált, de annak képe és nyers JPEG-je most nem áll rendelkezésre. A PicasaPy forrás és ez az egy eredeti képernyőállapot két külön bizonyíték, de a tárolási végpont állítására nem adnak egyező leletet, ezért az összesített fok **nyitott**.

#### A két független út

- **A út, eredeti bináris:** a `0x0063a5e0` hívó EAX-ben a Tags panelt adja át a `0x0063c5a0` függvénynek; a `0x005643e0` konstruktor az `IKeywordUpdate` táblát a fő objektum `+0x284` mezőjére állítja. A tábla adatcíme `0x00c906d8`; a `+8` hely `0x0065b3b0`-ra mutat. Az utasításokban ez a metódus kijelölt elemeket jár be, elemenként két további virtuális helyet hív, majd `0x0065ac80` frissítést indít. Ez bizonyítja, hogy a remove út nem merül ki a panel rajzolásában, de nem nevezi meg az elemenkénti metódusok lemezíró hatását.
- **B út, PicasaPy forrás és megmaradt mérési sor:** a jelenlegi Python/QML út fájlonként megnevezi az IPTC és ini írást, az indexfrissítést, a hibaágat és a panel frissítését; a job-242 korábbi képernyőleírása egy eredeti, egyképes hozzáadás látható végállapotát rögzíti.
- **Egyezés:** az Add Tag felületi hozzáadása és a Quick Tag recent megjelenése egyezik az egyetlen dokumentált job-242 állapottal. A lemezírásra, vegyes törlésre, hibára vagy visszavonásra a két út nem ad egyező, teljes bizonyítékot. Az összesített minősítés ezért nem „megerősített”.

#### Cáfoló kísérlet

Ellenőriztem azt az alternatívát, hogy a `0x0063c5a0` kizárólag panel- vagy listafrissítés. A hívó `0x0063a5e0` utasításszinten igazolja, hogy EAX-ben a panel kerül a függvénybe; a konstruktorból és a `0x00c906d8` vtable-adatból feloldott `+8` hely a `0x0065b3b0` metódusra jut, amely kijelölt elemenként `+0x60` és `+0x64` virtuális hívást tesz. Ez cáfolja a „csak rajzolás” értelmezést. A cáfoló eredményt külön út ellenőrizte: a virtuális tábla közvetlen bájtjai és a célfüggvény diszasszemblyje. A fájlíró célját ettől nem következtetem ki.

#### A jegy „Kész, ha” pontjai

1. ⛔ **Belépési pontok, engedélyezés, egy/több kép, videó, vegyes állapot:** az eredeti menü- és billentyűparancsok statikusan azonosítottak; a nézőkapu, kiválasztott képszám, videó és vegyes állapotú törlés tényleges eredménye hiányzik. Bizonyíték: `0x005d9760`, `0x005e60d0`, `0x0063a5e0`, `0x0063c5a0`; PicasaPy-forrás `MainWindowCommands.qml:232-233`, `MainRightDrawer.qml:83-95`, `PhotoViewerRightPanels.qml:76-103`.
2. ⛔ **Panel, alapérték, javaslatlista és megjegyzett beállítás:** a tíz mező, két recent hely és az alapértelmezett bekapcsolás ismert; az eredeti forráslista sorrendje, frissülése és a Mégse utáni recent érték futásidejű ellenőrzése hiányzik. Bizonyíték: `0x0083ea00`, `0x0083f580`, `0x0063d260`, Ghidra 425; PicasaPy-forrás `QuickTagsConfigDialog.qml:50-83,122-169`, `keywords_controller.py:393-402,420-507`.
3. ⛔ **Fájl, metaadat, `.picasa.ini`, index, keresés, rács, kijelölés, vegyes törlés és visszavonás:** PicasaPy forrásút megvan, az eredeti végállapot nem. A job-242 csak egy JPEG látható állapotát és ini-kivonatot rögzít; IPTC/XMP és JPEG nincs megmérve. Bizonyíték: `mérés (job-242, docs/specs/paritas-ellenorzes.md:831)`, `keywords_controller.py:204-279`, `metadata/iptc_writer.py:48-58`.
4. ⛔ **Írásvédelem, íráshiba és részleges végrehajtás:** a PicasaPy ág forrásból levezetett, az eredeti Picasa hibás és részleges végállapota hiányzik. Bizonyíték: `keywords_controller.py:138-174,230-279`; eredeti: `NINCS MEG`.

#### Javasolt fejlesztői jegytörzs

A korábbi hat fejlesztői javaslatból az aktív lap kapcsolása, a vesszőnkénti
tokenizálás, a helyi menü sorrendje, a recent pontos egyezése, az egyszeri
Autofill gomb és a Tulajdonságok útja a mostani forrásban már megvan. Ezekből
ne készüljön új, duplikált implementációs jegy. A bizonyított maradékhoz egy
szűk fejlesztői jegytörzs készíthető:

**Cím:** A Quick Tags Autofill a forrás első 100 eleméből szűrjön.

**Eredeti:** a `0x0063d260` a panel `+0x2c0` listájának első 100 elemét veszi,
majd a `0x0063d550` legutóbb használt címkéket kizáró szűrőjével jelölteket
hagy ki. Ha az első 100 között mindkét ilyen címke szerepel, legfeljebb 98
jelölt marad.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A korlát a forrás első 100 elemére esik, utána következik a legutóbb használt címkéket kizáró szűrés (`0x0063d260`, `0x0063d550`). | A legutóbbi értékek kizárása megelőzi a 100 jelöltes korlátot (`keywords_controller.py:428-442`); a rekordbejárás `all_photos` sorrendje (`:431-440`). | A forrás első 100 eleméből állítsa elő a jelölteket, majd szűrje ki a legutóbbi értékeket. Az eredeti forrás sorrendjét az alább megadott mérésből kell átvenni, nem szabad becsülni. |

**Kész, ha:** a rögzített Picasa-mintán az Autofill jelöltjei sorrendben
megegyeznek; a korlát a recent-szűrés előtt fut; ha a forrás első 100 eleméből
kettő recent címke kiesik, legfeljebb 98 érték marad; az ismételt gombnyomás és
a mezők kiürítése a mérésben rögzített eredményt adja. A törlési, fájlírási és
visszavonási paritásról csak az alábbi mérés után lehet végrehajtható fejlesztői
jegyet írni.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7009 alszakasz, és három helyesbítő megjegyzés a #7000 alszakaszban.

### Zárási döntés

**A #7022 jelenleg nem zárható. Az egyetlen blokkoló egy kontrollált Picasa
3.9.141.259 Windows-mérési kör**, amelynek egy elszigetelt könyvtárban kell
rögzítenie: a Nézet > Tags és Ctrl+T/Ctrl+K engedélyezését könyvtárban,
nézőben és szerkesztőben; egy és több kép, videó, valamint vegyes címkeállapot
hozzáadási és törlési végeredményét; a JPEG IPTC és XMP állapotát, a `.picasa.ini`-t és a
fájl hashét előtte/utána; index, keresés, rács és kijelölés frissülését; visszavonást,
írásvédelem, egyszeri és szándékosan hibás írás részleges eredményét; továbbá
100-nál több Quick Tags forráselem sorrendjét, recent szűrését, ismételt
Autofillt, párbeszédnyitást és Mégsét. A korábbi job-242 egyképes képernyő- és
ini-kivonatát újra fel kell használni részleges kontrollként, az elveszett
JPEG-végállapotot azonban nem szabad meglevőnek tekinteni.

Ez az egy mérési kör dönti el a felsorolt felhasználói viselkedéseket és a
Quick Tags fejlesztői jegy pontos forráslistás sorrendjét. A korlát és a
recent-szűrés sorrendjének eltérése már bizonyított, ezért az Autofill-jegytörzs
marad. A per-elemes virtuális cél statikus értelmezése a méréshez nem külön
blokkoló; ezért most nem kérek új Ghidra-kört.

### Zárókör 2 (2026-11-17): a megmaradt NINCS MEG és Ghidra-kör kell tételek eldöntése

Ez a kör az előző zárókör (2026-11-16) maradék tételeit döntötte el. A korábbi szakaszok érintetlenek, a helyesbítések itt vannak. Forrás: utasításszintű olvasás a `Picasa3.exe`-ből (SHA-256 fent), a bináris-index hívó- és sztringadatai, a teljes binárison futtatott eltoláskeresés (`eszkozok/binaris/tagkereso.py`), a PE importtábla bejárása a `call [0x00c4....]` címek feloldásához, és a `referencia/ghidra/2026-10-21-autocomplete.txt` korábbi dekompilálása. Futásidejű Picasa-mérés nincs. A „Nálunk” állítások a munkafa mostani forrásán ellenőrzöttek. Fokok: **megerősített** = két független út, **erős** = egy út, egyértelmű utasításokkal, **feltételes** = következtetés.

#### A. Eldöntve a meglévő bizonyítékból

**A1. Az Autofill jelöltlistáját csak a Tags-panel inicializálója tölti, a címkézés nem frissíti (megerősített); az inicializáló egyszeri futása erős.** Ez lezárja a `0x00639c00`, a `0x006393b0` („mikor töltődik”) és a „a panel `+0x2c0` listájának írója” sort.

- A `0x00639c00` a panel inicializálója (gyerekelemeket is létrehoz, ezért az ismételt futása kettőzött elemeket adna, vagyis valószínűleg egyszeri; a hívója vtábla-hívás, az index nem látja): betölti az `i18n\tagpanel_text.xml` fájlt (`0x00639c25`), a `quicktags::enable_recents` értéket a panel `+0x350` jelzőjébe olvassa (`0x00639c36-0x00639c62`), a könyvtár címkekészletét a `0x00437380(könyvtár, &panel+0x2c0)` hívással tölti (`0x00639c7b-0x00639c83`), rögzített színeket és méreteket állít (`0x00639cc5-0x00639d4b`), létrehozza a `%s/taglist` és `%s/removetag` gyerekelemeket (`0x00639d8b`, `0x00639e22`), végül a `0x0063ae00`, `0x0063b5a0`, `0x0063c7d0` függvényt hívja (`0x00639df7`, `0x00639dfd`, `0x00639eb4`).
- Első út: a teljes binárison futtatott eltoláskeresés a `[reg+0x2c0]` és `[reg+0x2c4]` hivatkozásokra a Tags-panel tartományában csak a konstruktort (`0x00639440`, nullázás `0x006394a5`, `0x006394ab`), a destruktort (`0x00639510`), az inicializálót (`0x00639c7b`) és az olvasó `0x0063d260`-at (`0x0063d2aa`, `0x0063d2c0`) találta. Második út: az index szerint a `0x00437380` egyetlen hívója a `0x00639c00` (`0x00639c83`), és a `0x00639c00`-nak nincs közvetlen hívója (a `TagPanel::vftable` tagja).
- A hozzáadás és a törlés utáni frissítő (`0x0065ac80`, `CThumbUI::UpdateKeywordStatus`) a `rightdrawerpanel/tagpanel` csomópontnak csak `selection_changed` eseményt küld (`0x0065acb1-0x0065acfb`). A `0x0063a5e0` erre csak a kijelölés címkelistáját építő `0x0063ae00`-at hívja (`2026-10-21-autocomplete.txt:131-440`), a `+0x2c0` listát nem.
- Következmény: egy munkamenetben újonnan felvett címke nem jelölt az Autofill számára, amíg az inicializáló újra nem fut (valószínűleg a panel újralétrehozásáig). **Nálunk:** `keywords_controller.py:453-460` (`beginQuickTagAutofill`) minden ablaknyitáskor friss jelöltlistát épít az indexből (`:420-442`). Az eltérés csak a munkamenet közben felvett új címkénél látszik; a panel létrehozásának idejét a B1 mérés dönti el, ezért erre jegytörzs egyelőre nincs.

**A2. A `+0x34a4` nem a néző állapota, hanem felugró menü számláló (megerősített; helyesbíti a 2026-11-16-i „ha a `+0x34a4` a nézőt jelöli” feltevést).**

- A `0x005e2000` a `0x005e2637`-en eggyel növeli a főablak `+0x34a4` mezőjét, a `0x005e264e`-en a `[0x00c407c4]` importot hívja (a PE importtábla bejárása szerint ez a USER32 `TrackPopupMenu`), a `0x005e2659`-en eggyel csökkenti. Ugyanez a minta a `0x005e26a0`-ban (`0x005e2e69`, `0x005e2e83`, `0x005e2e90`). A konstruktor (`0x005643e0`) nullázza (`0x00564c6e`).
- A `0x0057c430(4)` őr tehát csak felugró menü futása közben lehet igaz, amikor billentyű úgysem érkezik. A Ctrl+K és Ctrl+T nézőbeli elérhetőségét **nem** ez az őr dönti el. A `0x0056c420` és a `0x0056c110` őr az Import- és a Nyomtatás-panel állapota (korábban megválaszolt), a `+0x30d4` 2, 4, 6 módkódja szerkesztőeszköz-állapot (a `0x005f8d80` jóváhagyó kapu kérdező ágai, `ui-audit-editor.md:2450`). A maradék kérdés („szerkesztő nézetben, eszköz nélkül működik-e a Ctrl+K”) a B3 mérésé. Nem blokkoló.

**A3. A hozzáadás és a törlés lánca (erős; a követett láncra érvényes).**

- **Törlés** (`0x0063c5a0` → `IKeywordUpdate +8` = `0x0065b3b0`): minden kijelölt elemre és a törlendő címkére meghívja az elem tárolójának `+0x60` tagját (elem, címke), majd elemenként a `+0x64` tagot (elem, 1) (`0x0065b405-0x0065b46d`), a visszatérési értékeket eldobja, végül frissít (`0x0065b48d`). Nincs megerősítés, nincs küszöb, nincs hibaüzenet. Vegyes kijelölésnél tehát minden kijelölt képre lefut; a címke nélküli képen a `+0x60` belseje dönt, de felületi hatása nincs. **Nálunk:** `removeKeywordFromRows` a kijelölt sorokon megerősítés nélkül dolgozik (`keywords_controller.py:193-202`, `MainRightDrawer.qml:93-95`): egyezik.
- **Hozzáadás** (egy token, `0x0063bed0`): előbb `IKeywordUpdate +4` = `0x0065b160` (a 30 fölötti megerősítés, `0x0063c036`); ha a felhasználó nemet mond, a függvény a Legutóbbiak frissítése ELŐTT visszatér. Utána, ha a panel `+0x350` jelzője be van kapcsolva, a `0x0063c120` frissíti a Legutóbbiakat (`0x0063c085`), végül `IKeywordUpdate +0x14` = `0x0065b4b0` (`0x0063c0d9`) hajtja végre a hozzáadást: kijelölés-gyűjtő (`0x005c76b0`), majd `+0x10` = `0x0065b590`, amely üres listánál hatás nélkül 0-t ad (`0x0065b59c-0x0065b5a8`), különben a `0x004d9aa0` a címkét egy név szerinti, `__stricmp`-pel (kis- és nagybetűre érzéketlenül, `0x004d9b65`) kereső táblába szúrja az elemekkel, értesíti a figyelőket (`0x004d9eba` → `0x004db8f0`: verziószámláló, piszkos jelző, figyelők hívása), majd frissít (`0x0065b644`). **Nálunk:** a megerősítés a hozzáadás útján van (`MainRightDrawer.qml:83-92`, `MainLibrarySelectionState.qml:184-191`), a Legutóbbiak a megerősítés UTÁN frissülnek (`keywords_controller.py:177-190`): egyezik. A névegyeztetés nálunk Unicode `casefold` (`:185-188`, `:199-200`), a panel listája pedig csak az ASCII betűket hajtja kisbetűre (`:60-62`); nem ASCII betűk (`Ä` és `ä`) kis- és nagybetű-változatánál az eredeti `__stricmp` viselkedése mérés nélkül nem ismert (B2).
- **A „részleges hiba” üzenet kiváltója.** A `0x0063bb30` a `0x0063bed0` nem nulla és nem `0xf4242` (Mégse) értékét hibaként számolja (`0x0063bc9e-0x0063bca9`), és ha van hiba, kiírja a `Some of the text you entered could not be added as a tag.` szöveget (`0x0063bd90-0x0063bdb4`). A láncban a `0x004d9aa0` csak akkor ad nem nulla értéket, ha a tábla vagy a bejegyzés nem hozható létre (`or eax, -1`: `0x004d9d2e`, `0x004d9d4e`, `0x004d9d65`), vagy ha az elemtömb tömörítése memóriahiba miatt elbukik (`0x004d9be7` → `0x0074cf40`, `0x0074cf7d`: 4). Tartalmi elutasítás (tiltott karakter, létező címke) nincs. A túl hosszú token nem hibás, hanem levágott (A4). Az üzenet tehát hétköznapi bevitelnél gyakorlatilag nem jelenik meg. **Nálunk:** a figyelmeztetés a lemezírási hibát jelzi (`MainRightDrawer.qml:90-91`, `keywords_controller.py:268-273`); ez tudatos eltérés, nem blokkoló.

**A4. A bevitel tokenizálása (megerősített).** A bontó (`0x009881d0`) az üres tokent kihagyja: a határoló ismétlődéseit átugorja (`0x00988230-0x00988237`), az üres szakaszra újraindul (`0x00988272-0x00988274`), tehát `a,,b` és a záró vessző nem hoz létre üres címkét. Minden token legfeljebb `0x80` (128) bájt (`0x0063bbdc-0x0063bbe1`: a harmadik argumentum; `0x0098828c-0x00988290`: a hossz a korlátra vágva). Utána minden token elejéről és végéről levágja a szóközöket (`0x009869a0`), a belső szóközsorokat egyre szűkíti (második bontás szóközön, `0x0063bc5f-0x0063bc60`, összefűzés `0x0063bc71`). **Nálunk:** `TagsPanel.qml:52-63` vessző mentén bont és kihagyja az üreseket; `_clean_keyword` (`keywords_controller.py:65-68`) a szóközöket egyre szűkíti. Az egyetlen eltérés a 128 bájtos levágás, amelyet **nem** másolunk: egy többbájtos UTF-8 karaktert félbevághatna, és csak 128 bájtnál hosszabb címkénél látszana. Tudatos eltérés (zárókör döntése, 2026-11-17), nem blokkoló.

**A5. Írásvédettség, videó, visszavonás, lemezíró (erős a követett láncra; a lemezen látható végállapot a B2 mérésé).**

- **Íráskapu a panelben nincs a láncban.** A `keywords/readonly_file` és `keywords/readonly_label` sztringnek az index szerint egyetlen használója a `0x00840b80` (a `Keywords (%d pictures)` ablak állapotfrissítője). Ezt a `0x0065ac80` csak akkor hívja, ha a főablak `+0xed0` mezője nem nulla (`0x0065ad02`, `0x0065b07c`, `0x0065b0ad`); ezt a mezőt a teljes binárison egyetlen utasítás írja, a konstruktor nullázása (`0x00564d8c`; `add` vagy `lea` alakú hivatkozás nincs). A `Keywords (%d pictures)` ablak és az írásvédett felirata így a vizsgált binárisban elérhetetlen kód. Az „írásvédett” állapotot kiszámító `IKeywordUpdate +0xc` (`0x0065b310` → `0x0047d1b0`) útvonal-alapú, nem fájlattribútum-vizsgálat (nem hív Win32 függvényt). A panel `0x0063bb30`, `0x0063bed0`, `0x0063a5e0`, `0x0063c5a0` függvényében írásvédettségi kapu nincs. **Nálunk:** a panel előre szól és tiltja a bevitelt, ha a kijelölésben van írásvédett elem (`keywords_controller.py:138-170`, `TagsPanel.qml` `readOnlySelection`, #2998), mappaszintű próbaírással. Az eredeti panel tehát a követett lánc szerint nem tilt; hogy az írásvédett fájlon mi történik (némán elmarad, vagy a háttéríró jelez), a B2 mérés kérdése. A mai viselkedést addig nem bontjuk vissza.
- **A lemezíró aszinkron.** A `0x00415790` konstruktorú objektum (amelyhez az adatbázis-mentő `0x0041ba40` tartozik) `+0x2aa0` tagja a `FileTagger`, a `ytAsyncQueue<KeywordJob>` leszármazottja (vtábla `0x00c82938`; `0x00415d00-0x00415d0d` hívja a `0x00496c40` alapkonstruktort). A címkék fájlba írása tehát feladatsoron át, háttérben történik. A mentéskor a `0x0041ba40` a sort kiüríti (`0x0041bb3e`), a `0x00455e30` időkorláttal figyeli (`0x00455e4c`: `add edi, 0x2aa0`). A felületi frissítés (a táblába szúrás és a figyelők értesítése) azonnali, a fájl később íródik. A feladat konkrét végrehajtója (IPTC, XMP, `.picasa.ini`, formátumonként) statikusan nem azonosított, és a bájtszintű végállapot mérés nélkül sem eldönthető: B2.
- **Videó:** a hozzáadási láncban (`0x0065b590`, `0x004d9aa0`) típusszűrő nincs; a tárolás helye formátumonként a B2 mérésé.
- **Visszavonás:** a követett láncban (`0x0063bb30`, `0x0063bed0`, `0x0065b3b0`, `0x0065b4b0`, `0x0065b590`) visszavonási bejegyzés nincs; a `[0x00d6793c]` számláló a kurzorállapotot kezeli (`SetCursor`, `0x0065b518-0x0065b525`). Nálunk sincs címkézési visszavonás. Nem blokkoló.

**A6. Új, bizonyított eltérések a felületen.**

- **Üres gyorscímke-hely (megerősített).** A `0x0063a5e0` `quicktag_%d` ága a megjelenített értéket a `]empty` sztringgel veti össze (`0x0063a959-0x0063a967`, `0x0063a998`); egyezésnél a `0x0063a99a` a `0x0063a9da`-ra ugrik, amely a `0x0063d840`-et hívja, nem egyezésnél a `0x0063bed0`-et. A `0x0063d840` a `quicktagconfig` erőforrásból a „Configure Quick Tags” ablakot építi (`0x0063d8c2`, `0x0063d8db`). Második út: a `2026-10-21-autocomplete.txt` dekompilálása ugyanezt adja (`FUN_0063d840()` a `]empty` összevetés után). Az üres hely buboréksúgója `TagPanel::emptytip` („Click to configure quick tags”, `picasa-beviteli-mezok.md:227`). Az üres gyorscímkére kattintás tehát a konfigurációs ablakot nyitja, nem a „nincs beírt szöveg” súgót. Ez **helyesbíti** a #4271 olvasatát. **Nálunk:** `TagsPanel.qml:323-325` az üres helyre `tagNoTextDialog.open()`-t hív; a tesztek ezt rögzítik: `tests/app/qml_functional/test_cimke_panel_4271.py:250-256`, `tests/app/test_qml_quicktags.py:63-80`.
- **Üres szöveg Entere (erős; maga az üzenet korábbról megerősített).** Az Enter (`editselected`) a `0x0063acd0`-n át a `0x0063bb30(panel, 0)`-t hívja (`0x0063ad76`); üres vagy szóközös szövegnél `TagPanel::notify_notext` modális üzenet jelenik meg (`0x0063bb85-0x0063bbd9`), és semmi nem íródik. **Nálunk:** `TagsPanel.qml:52-56` (`submit`) üres szövegnél csendben visszatér, a `+` gomb üres szövegnél tiltott (`:100`), a súgóablak (`tagNoTextDialog`, `:382-399`) csak az üres gyorscímkéről nyílik. A `+` gomb eredeti tiltott vagy engedélyezett állapota üres szövegnél nem eldöntött (B3).
- **Helyi menü elválasztója (erős).** A `0x00735480` négy rekordot ad át a `0x00a6aee0` tételépítőnek (`push 4`, `0x0073559a`): Add (`0xa0b8`), Search (`0xa0b7`), egy csupa nulla rekord (`0x00d6f868`), Remove (`0xa0b9`). A `0x00a6aee0` a nulla feliratmutatót tartalmazó rekordot `0xffff` azonosítóval elválasztóként építi (`0x00a6af04-0x00a6af20`), ugyanígy, ahogy a Szerkesztés menü csupa nulla rekordjai elválasztók (`picasa-menusor-csoportok.md:75`). A Remove tétel előtt tehát elválasztó áll. **Nálunk:** `TagContextMenu.qml:27-41` három tétel, elválasztó nélkül. A menü vizuális egyezését eredeti képernyőkép híján nem mértük.
- **Mégse és a Legutóbbiak jelölőnégyzet (erős, mérésre vár).** A párbeszéd kattintáskezelője (`0x0083f210`) a Mégse ágon csak a `[ablak+0xd5c]` jelzőt állítja és bezár (`0x0083f24e-0x0083f266`); a jelölőnégyzet ága azonnal kiírja a `Preferences\quicktags::enable_recents` értéket (`0x0083f289-0x0083f2ae` → `0x0083f2f0`, `0x0083f375-0x0083f3a6`). Visszaállító írás nincs. **Nálunk:** `QuickTagsConfigDialog.qml:79-83` a Mégse a kapcsolót is visszaállítja. A viselkedés megfordítása működő funkciót érint, ezért a jegytörzs a B4 mérés után készül (a 2026-11-16-i „lehetséges eltérés” így erősre emelkedik).
- **Letiltott Autofill gomb (erős).** A `+0x20e` a vezérlők általános „tiltott” jelzője: a `0x009cd7e0` állítja és újrafestést kér (`or [node+8], 2`), a görgetősáv találatvizsgálata kihagyja, ha be van állítva (`0x009cf56d`). A `0x0083ea00` ezt állítja be az Autofill gombon, ha nincs jelölt, tehát a gomb letiltott, nem rejtett. **Nálunk:** `QuickTagsConfigDialog.qml:167` ugyanígy tiltja: egyezik.

**A7. A 30 fölötti megerősítés hatóköre (megerősített).** Az `IKeywordUpdate +4` (`0x0065b160`) egyetlen hívója a hozzáadás útja (`0x0063c036`); ez a gépelt hozzáadásnál tokenenként, a gyorscímkénél és a helyi menü „Add this tag to entire selection” tételénél egyaránt lefut. A törlésnél (A3) nincs. A gépelt bevitelnél a `0x0063bb30` ciklusa minden tokenre külön hívja a `0x0063bed0`-et (`0x0063bc99`), tehát tokenenként külön megerősítés jön; a Mégse (`0xf4242`) az adott tokent hagyja ki, a többit nem érinti (`0x0063bca2-0x0063bcae`). **Nálunk:** a kérdés helye és a törlés egyezik (`MainRightDrawer.qml:86-88`, `MainLibrarySelectionState.qml:184-191`; a törlés nem kér megerősítést), a tokenenkénti sorrend viszont **hibás**: a `submit()` ciklusa (`TagsPanel.qml:57-62`) egymás után hívja az `addRequested`-et, a 30 fölötti ág pedig a függő megerősítés `askFor`-ját hívja újra (`MainRightDrawer.qml:87`, `MainDialogs.qml:70-80`), amely felülírja a sorokat és a címkét. `tag1, tag2` bevitelnél 31 vagy több kijelölt képen így egyetlen kérdés jön, és csak az utolsó token (`tag2`) kerül fel; az első néma módon elvész. Új hiba, lásd az 5. jegytörzset.

#### Az eddig nyitott tételek eldöntése (14 tétel)

| Régi tétel | Döntés | Hol |
|---|---|---|
| `Ghidra-kör kell: 0x006a5060` és szomszédai (jelöltsorrend) | (b) mérés | B1. A Ghidra 425 válasza nem erre szólt; a sorrend a kulcsszó-tároló feltöltési sorrendje, ami a futó könyvtárhoz kötött |
| `Ghidra-kör kell: 0x006393b0` (két előfordulás) | (a) lezárva | A1; a létrehozás időpontja B1 |
| `Ghidra-kör kell: 0x00639c00` | (a) lezárva | A1 |
| `Ghidra-kör kell: 0x0056c420` | (a) lezárva | 2026-11-16 és A2 |
| `Ghidra-kör kell: 0x0057c3b0` (`+0x9c`, `+0x34a4`) | (a) részben lezárva, a maradék (b) mérés, nem blokkoló | A2, B3 |
| `Ghidra-kör kell:` a panel `+0x2c0` írója (`0x00437380`, `0x004936c0`) | (a) lezárva: az író a `0x00639c00`; a készlet sorrendje (b) mérés | A1, B1 |
| `NINCS MEG`: futásidejű sorrendmérés (két helyen) | (b) mérés | B1 |
| `NINCS MEG`: eredeti mérés fájlkivonattal és ini-vel | (b) mérés | B2 |
| `NINCS MEG`: kijelölés-, videó-, írásvédettségi feltétel | (a) lezárva a láncra, a látható eredmény (b) mérés | A5, B2 |
| `NINCS MEG`: címke törlése, vegyes kijelölés | (a) lezárva | A3 |
| `NINCS MEG`: író visszahívás és lemezvégállapot | (a) lezárva az aszinkron sorra, a bájtok (b) mérés, egy Ghidra-sor | A5, B2, lent |
| `NINCS MEG`: címkézési mérőfutás az archívumban | (b) mérés | B1-B4 |
| Index, keresés, rács, kijelölés végállapota | (a) az index és a keresés frissítése lezárva (azonnali tábla és `selection_changed`), a rács és a kijelölés (b) mérés | A1, A3, B2 |
| Visszavonás, hibaág, részleges végrehajtás | (a) lezárva: nincs visszavonás, törlésnél nincs hibaág, hozzáadásnál csak belső hiba; a háttéríró hibája (b) mérés | A3, A5, B2 |

#### B. Mérés dönti el (egy közös mérési jegy)

A következő tételeket sem újabb Ghidra-kör, sem statikus olvasás nem dönti el: a felhasználó által látott eredmény futó adatbázis-állapottól vagy fájlbájtoktól függ. Egy mérési jegy adja őket (Colab, az angol 3.9.141 Wine alatt, a `colab_felmero.py futtat --lepesek ...` útján, izolált mintakönyvtárral). A mérés saját eszközzel elvégezhető, ezért a jegye `ready`, nem `blocked`.

- **B1. Autofill sorrend és pillanatkép.** Három mappa, rövid ismert nevű képekkel és ismert beolvasási sorrenddel; olyan címkékkel, ahol a gyakoriság és az első előfordulás sorrendje eltér (`b` 5 képen az első mappában, `a` 1 képen). Tiszta indítás után Quick Tags konfiguráció, Autofill (Legutóbbiak be és ki), a tíz mező szövege rögzítendő; majd a mezők kiürítése és újabb Autofill; ezután ÚJ címke felvétele a munkamenetben, a konfiguráció újranyitása és Autofill (megjelenik-e az új címke); végül Picasa-újraindítás után megjelenik-e. Dönti: a jelöltsorrendet (`0x006a5060` és szomszédai, `0x00437380`, `0x004936c0`) és a pillanatkép idejét (`0x006393b0`).
- **B2. Címkézés végállapota.** JPEG, PNG és videó; egy kép és több kép; hozzáadás, törlés és vegyes törlés (két kép a címkével, egy nélküle); fájl SHA-256 előtte és utána, a `.picasa.ini` előtte és utána, a JPEG IPTC és XMP blokkjai, a késleltetés (a `FileTagger` aszinkron); a rács és a kijelölés a művelet után; írásvédett fájlon (`attrib +R`) hozzáadás: a panel felirata, a bevitel tilthatósága, a fájl és az ini állapota; egy `Árvíz` és `árvíz` címkepár hozzáadása és törlése. Dönti: a lemezvégállapotot, a vegyes törlés fájlhatását, az írásvédett és a videós viselkedést, a hibaágat, a nem ASCII kis- és nagybetűs egyeztetést.
- **B3. Ctrl+K, Ctrl+T és a Nézet > Tags engedélyezése.** Könyvtárban, szerkesztő nézetben eszköz nélkül és vágóeszközzel, teljes képernyős nézetben; a `+` gomb állapota üres szövegnél. Dönti: a nézőbeli és a szerkesztőbeli elérhetőséget (`0x0057c3b0`, `0x005e60d0`).
- **B4. Mégse és a Legutóbbiak kapcsoló.** A kapcsoló átváltása, Mégse, újranyitás; a panel két felső gombja közben. Dönti: az A6 Mégse pontját.

Egyetlen Ghidra-sor marad, nem blokkoló (a B2 bájtszintű eredményét magyarázza, nem helyettesíti):

- `Ghidra-kör kell: 0x00496d80 - a FileTagger (vtábla 0x00c82938) futtató ciklusa: a 0x00496f08 call edx a KeywordJob melyik virtuális tagját hívja, és az mit ír (IPTC, XMP, .picasa.ini); kik töltik a feladatsort (a 0x0041ba40 és a 0x00455e30 csak kiüríti, illetve várja)`

#### Helyesbítések a korábbi állításokhoz

- A `+0x34a4` mező nem a néző állapota, hanem felugró menü számláló (A2).
- Az üres gyorscímkére kattintás a konfigurációs ablakot nyitja, nem a „nincs beírt szöveg” súgót (A6); a #4271 olvasata és két tesztje ennek megfelelően javítandó.
- A `keywords/readonly_label` szöveg nem a Címkék panel kapuja: az eredetiben egy elérhetetlen ablakhoz tartozik (A5); a #2998 panel-kapuja nem az eredeti másolata. Visszabontása mérés (B2) előtt nem indokolt.
- A Mégse és a Legutóbbiak jelölőnégyzet „lehetséges eltérése” erős eltérés (A6), a jegytörzs a B4 után.

### Zárási döntés (a 2026-11-17-i zárókör után)

**A #7022 kutatási jegy lezárható.** Ez felülírja a 2026-11-16-i döntést, amely szerint az egyetlen blokkoló egy mérési kör. Indok: minden tétel, amelyből fejlesztői jegytörzs készíthető, a bináris utasításaiból eldőlt (A1-A7). A megmaradt tételek (B1-B4) peremesetek (sorrend nagy könyvtárnál, nézőbeli billentyű, a lemezre írt bájtok, Mégse), amelyektől az alábbi jegytörzsek egyike sem függ; ezek egy közös, felvehető mérési jegybe kerülnek. Bizonyítottsági fok: **megerősített** az Autofill-lista címkézéssel nem frissülésére, az üres gyorscímke eltérésre, a `+0x34a4` helyesbítésre és a tokenizálásra; **erős** az üres szöveg Entere eltérésre, a hozzáadás és a törlés láncára, a helyi menü elválasztójára, a letiltott Autofill gombra, az írásvédettségi kapu hiányára és a Mégse viselkedésre; **feltételes** a lemezvégállapotra (nincs mérve).

Nyitott kérdések mérlege (az „Az eddig nyitott tételek eldöntése” tábla 14 sora): 0 nyílt · 5 lezárva (a 2. és a 6. sor maradéka a B1 mérés kérdése, nem külön tétel) · 9 mérési jegyre kijelölve (B1-B4, felvehető, nem blokkoló) · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”.

**Készre ítélt jegytörzsek (jegy nem kell), a mai forráson ellenőrizve:**

- **1. Nézet > Tags, Ctrl+K, Ctrl+T, panelgomb:** kész, `MainWindowLibraryActions.qml:15-23` (`valtsFiokLapot`), `MainKeyboardShortcuts.qml:107-114,326-336`, `MainMenuBar.qml:378` (#7025).
- **2. Vesszős Add Tag:** kész, `TagsPanel.qml:52-63`.
- **3. Helyi menü sorrendje (Add, Search, Remove):** kész, `TagContextMenu.qml:27-41`; az elválasztó lent, a 3. jegytörzsben.
- **4. Pontos Legutóbbiak-egyezés:** kész, `keywords_controller.py:341-359`.
- **5. Egyszeri Autofill és jelöltforrás (5/b):** kész, `QuickTagsConfigDialog.qml:50-58,152-168`, `keywords_controller.py:420-508` (#7053); a sorrend közelítés az index sorrendjével, a pontos sorrend B1.
- **6. Tulajdonságok > Edit Tags a Tags panelt kapcsolja:** kész, `PropertiesPanel.qml:133,162`.

**Megmaradó fejlesztői jegytörzsek (öt):**

#### 1. (új) Az üres gyorscímke-hely a Quick Tags konfigurációs ablakot nyissa

**Eredeti:** a `quicktag_%d` esemény a megjelenített értéket a `]empty` sztringgel veti össze (`0x0063a959-0x0063a967`); egyezésnél a `0x0063d840` a „Configure Quick Tags” ablakot nyitja (`0x0063a99a` → `0x0063a9da`, `0x0063d8c2`, `0x0063d8db`), különben a hozzáadás fut. Az üres hely buboréksúgója `TagPanel::emptytip` („Click to configure quick tags”).

**Nálunk:** `TagsPanel.qml:323-325`: az üres (`?`) hely a „nincs beírt szöveg” súgóablakot nyitja (`tagNoTextDialog`); a buboréksúgó (`:328`) viszont a konfigurációt ígéri. A #4271 tesztjei ezt rögzítik: `tests/app/qml_functional/test_cimke_panel_4271.py:250-256`, `tests/app/test_qml_quicktags.py:63-80`.

**Teendő:** az üres hely kattintása a `quickTagsConfigDialog`-ot nyissa (a fogaskerék gombbal azonos úton, `TagsPanel.qml:269`); a nem üres hely továbbra is hozzáad. A két #4271 teszt ennek megfelelően módosul.

**Kész, ha:** valódi kattintás az üres (`?`) gyorscímkére megnyitja a Quick Tags konfigurációs ablakot, nem a „nincs beírt szöveg” ablakot, és nem ír címkét; nem üres hely kattintása hozzáad; a buboréksúgó változatlan; a módosított tesztek valódi kattintással futnak.

#### 2. (új) Az üres szöveg Entere a „nincs beírt szöveg” súgóablakot mutassa

**Eredeti:** az Enter (`editselected`) a `0x0063acd0`-n át a `0x0063bb30`-ra jut (`0x0063ad76`); üres vagy csak szóközt tartalmazó szövegnél `TagPanel::notify_notext` modális üzenet jelenik meg (`0x0063bb85-0x0063bbd9`), semmi nem íródik.

**Nálunk:** `TagsPanel.qml:52-56` (`submit`) csendben visszatér, a `+` gomb üres szövegnél tiltott (`:100`); a súgóablak (`:382-399`) csak az üres gyorscímkéről nyílik (ezt az 1. jegytörzs megszünteti).

**Teendő:** Enterre üres vagy csak szóközt tartalmazó szövegnél a `tagNoTextDialog` jelenjen meg; semmi ne íródjon. A `+` gomb tiltott állapota nem változik (az eredeti állapota B3). Kijelölés nélkül a mai tiltás marad (nem mért).

**Kész, ha:** kijelölt írható képnél az üres és a szóközös mező Entere megjeleníti az eredeti szövegű ablakot (`tagNoTextMessage`), és nem ír címkét; nem üres szövegnél a mai hozzáadás fut; valódi billentyűteszt (`Return`).

#### 3. (új) Elválasztó a címkesor helyi menüjében a Search és a Remove között

**Eredeti:** a `0x00735480` négy rekordot ad a `0x00a6aee0`-nak: Add (`0xa0b8`), Search (`0xa0b7`), csupa nulla rekord (`0x00d6f868`), Remove (`0xa0b9`); a nulla rekord elválasztó (`0x00a6af04-0x00a6af20`).

**Nálunk:** `TagContextMenu.qml:27-41`: három `MenuItem`, elválasztó nélkül.

**Teendő:** a „Search for items with this tag” és a „Remove this tag” közé `MenuSeparator` kerül; a három művelet célja nem változik.

**Kész, ha:** a címkesor jobbklikk-menüjében a sorrend Add, Search, elválasztó, Remove; mindhárom tétel a mai műveletét indítja. A vizuális egyezést eredeti képernyőkép híján a jegy nem méri, ezt kimondja.

#### 4. (megmaradt a 2026-11-16-i zárókörből) A Quick Tags Autofill a forrás első 100 eleméből szűrjön

**Eredeti:** a `0x0063d260` a panel `+0x2c0` listájának első 100 elemét veszi, majd a `0x0063d550` a két legutóbbi címkét kizárja; ha az első 100 között mindkettő szerepel, legfeljebb 98 jelölt marad.

**Nálunk:** `keywords_controller.py:420-442`: a két legutóbbi címke kizárása megelőzi a 100 jelöltes korlátot, így 100 jelölt marad.

**Teendő:** a korlát a forráslista első 100 egyedi elemére vonatkozzon, a szűrés utána fusson. A hatás csak 100-nál több egyedi címkénél és a 99. jelölt után látszik (egy Autofill legfeljebb tíz mezőt tölt), ezért olcsó és nem sürgős.

**Kész, ha:** 100-nál több egyedi címkénél, mindkét recent címkével az első 100 között, a jelöltlista 98 elemű; az üres jelölt kimarad; a recent címkék nem jelöltek.

#### 5. (új, hiba) Több tokenes bevitel 30 fölötti kijelölésnél minden tokent külön megerősítéssel adjon hozzá

**Eredeti:** a gépelt bevitel minden tokenjére külön lefut a hozzáadás (`0x0063bb30` → `0x0063bc99` → `0x0063bed0`), és mindegyik a saját 30 fölötti megerősítését kérdezi (`0x0063c036`, „Are you sure you want to apply this tag to all %d items?”). A Mégse az adott tokent hagyja ki, a következő tokenre ez nincs hatással (`0x0063bca2-0x0063bcae`).

**Nálunk:** `TagsPanel.qml:57-62` egymás után hívja az `addRequested`-et; `MainRightDrawer.qml:86-88` 30 fölötti kijelölésnél a `askFor`-t hívja, amely a függő ablak sorait és címkéjét felülírja (`MainDialogs.qml:70-80`). A felhasználó egyetlen kérdést lát, és csak az utolsó token kerül fel; az előzők némán elvesznek. A hibát a mai tesztek nem fedik (egy tokenes eseteket vizsgálnak).

**Teendő:** a tokenek megerősítése sorban történjen: a következő token kérdése az előző lezárása (Igen vagy Nem) után jön. Egy token vagy legfeljebb 30 kijelölt kép esetén a mai folyamat nem változik.

**Kész, ha:** 31 kijelölt képnél a `tag1, tag2` bevitel két egymás utáni megerősítést ad; mindkettőre igent mondva mindkét címke felkerül mind a 31 képre; az elsőre nemet mondva csak a `tag2` kerül fel; 30 vagy kevesebb képnél nincs kérdés és mindkét címke azonnal felkerül. A teszt valódi gépeléssel és Enterrel fut, a megerősítő ablak gombjait is megnyomja.

**Nem nyílik jegy (a zárókör döntése):** a 128 bájtos tokenlevágás másolása (A4, tudatos eltérés); a hibaüzenet kiváltója (A3, a PicasaPy a lemezírási hibát jelzi); az írásvédettségi kapu visszabontása (A5), a Mégse viselkedés (A6) és a pillanatkép-viselkedés (A1) a B mérés előtt; a `PropertiesPanel.qml:146-150` `KeywordsDialog` példánya, amelyet semmi nem nyit (az eredetiben a megfelelő ablak is elérhetetlen, A5), nem része ennek a jegynek.

**Következő irány (felvehető):** a B1-B4 mérési jegy, a fent megadott tartalommal és az egy Ghidra-sorral. Ez nem blokkolja a #7022 lezárását és a fenti öt jegytörzset.


### #7235-kiegészítés (2026-11-18): Tags-panel, OneUp-kapu és FileTagger

#### #478 - Tags-panel építő 0x00639c00

A 0x00639c00 dekompiláció (2026-11-18-koteg-466-495.txt:2724-2875) a Preferences/quicktags::enable_recents értéket olvassa, meghívja a 0x00437380 listafeltöltőt param_1+0xb0 argumentummal (a panel objektumán +0x2c0), majd a `taglist` erőforrásból panelkomponenseket hoz létre. A TagPanel::vftable 32. bejegyzése (byte-eltolás +0x80) erre a függvényre mutat. Ez a hívási szerződés két külön adatutat igazol: a builder-kódot és a vtable-adatot. Azt nem dönti el, hogy az építő csak panel-létrehozáskor vagy minden megjelenítéskor fut-e. A 0x009ccc50 xrefjei (0x0040bf70, 0x009c3860) és az erőforrás-betöltő regisztrációs hurok nem azonosítják a megjelenítési életciklust. Nyitott következő cím: 0x009ccc50 hívóinak és a Tags-panel láthatósági/callback útjának célzott feltárása. PicasaPy TagsPanel.qml és keywords_controller.py:283-506 külön kezeli a panelt és a quick-tag adatokat; a futási gyakoriság összevetése még nyitott.

#### #479 - 0x0057c3b0, +0x9c, +0x34a4, OneUp Ctrl+K

A 0x0057c3b0 (2026-11-18-koteg-466-495.txt:2876-2912) a window+0x16c panel-listán megy végig, kihagyja a panel+0x20c != 0 elemeket, ytBasePanel-típusra castol, majd a +0x9c virtuális metódust kérdezi. Független RTTI/vtable-adat és nyers utasítás alapján a ytBasePanel alapcél 0x004bdeb0 hamis (xor al,al; ret); a CollagePanel és MakeMoviePanel célja 0x007a5240 igaz (mov al,1; ret).

A +0x34a4 eltolású hivatkozások teljes .text-pásztázása a paszta.py memóriakapuján keresztül 67 találatot adott; releváns író a 0x00564c6e (mov [ebp+0x34a4], ebx), az olvasók a menüágakban szerepelnek. OneUp saját PreviewHandler-e (0x005c24c0) a WM_CHAR-útban Ctrl nélküli karaktereket kezel, ezért a saját karakterkezelője nem bizonyít Ctrl+K parancsot. A főablak 0x005e60d0 kezelőjében külön Ctrl+K ág van, amely a 0x0065ab00-ra vezet; a teljes képernyős saját kezelő és a globális út egymásra hatása továbbra is külön kérdés. Következő vizsgálat: a meglévő 0x005e60d0 kimenet globális útjának összevetése a OneUp 0x005c24c0 visszatérési/üzenet-útjával, és a 0x00564c6e pontos menüállapotának megnevezése.

#### #480 - FileTagger/KeywordJob 0x00496d80

A 0x00496d80 (2026-11-18-koteg-466-495.txt:2913-3115) a ytAsyncQueue<KeywordJob> worker-ciklusa; a 0x00c82960 vtable harmadik célja ez a függvény. A 0x00496f08 indirekt hívása a sorból kivett job-objektum vtable +0x64 slotját hívja. A konkrét implementáció és az általa írt IPTC/XMP/.picasa.ini mezők ebből a ciklusból nem látszanak. A 0x0041ba40 ürítő és 0x00455e30 várakozó címek nem queue-producerek. A worker xrefjei a sor feltöltését sem azonosítják. Nyitott következő célok: a nested KeywordJob vtable +0x64 konkrét célja, a sorba állító hívások és a job példányosítási pontjai. A PicasaPy keywords_controller.py:183-206 címkefolyamatot ír le, de az eredeti háttérmunka írói még nincsenek hozzárendelve.

## #7012: A Hozzáadás albumhoz teljes folyamata az eredeti Picasával összevetve

**Állapot: nyitott.** A menüpontok címkéjét és néhány kontextusfüggő parancsazonosítót a bináris rekordjaiból azonosítottam, a PicasaPy jelenlegi útja a forrásból követhető. Az eredeti albumválasztás utáni írási kezelő és a végállapot nincs igazolva, ezért a két termék teljes műveleti paritása nem állítható.

### Belépési pontok és engedélyezés

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fájl menü, `New Album...`, `Ctrl+N`: a főmenü `0x00559150` rekordja és a `referencia/i18n/enUS/shortcuts.xml:115-117` bejegyzése. Ez album-létrehozás, nem meglévő albumhoz adás. A főmenü rekordbázisa `0xd6e498`; a `0x0055b777` `eax` forrása `0x00c8d8b8` (`&View and Edit`), parancsmezője `0xd6e4a2 = 0x9ca0`. A következő rekord címkéje `&Batch Edit`, `0xd6e4ac` bázison. | `PicasaFileMenu.qml:23-27`; `MainMenuBar.qml:300-304`; `PicasaMenuBar.qml:750-754` | Ne számítsuk a `New Album` parancsot meglévő albumhoz adásnak. Eredeti közvetlen Add-to főmenü- vagy billentyűparancs: `NINCS MEG`. Az angol gyorsbillentyű-erőforrásban a `New Album` `Ctrl+N`; Add-to bejegyzést nem találtam. |
| Mappa bélyegképének helyi menüje: `&Add to Album` rekord `0x00730790`, parancsmező `0x9ca0`. | `PhotoContextMenu.qml:167-192`; `MainPhotoContextMenu.qml:124-138`; több kijelölés vagy az utolsó aktív kép: `MainLibrarySelectionState.qml:25-30` | Egy és több képnél ugyanaz a sorlista kerül az `addRowsToAlbum`-nak. Eredeti engedélyezés egy képre, több képre, videóra és már albumtag képre: `NINCS MEG`. PicasaPy útjában nincs képtípus-szűrés (`photo_ops_write_text_mixin.py:202-204`). |
| Album bélyegképének helyi menüje: `&Add to Album` rekord `0x00731050`, parancsmező `0x9ca0`. | Ugyanaz a kép-helyi menü és callback, `PhotoContextMenu.qml:167-192`; `MainPhotoContextMenu.qml:124-138` | A PicasaPy a kijelölt sorokat a megnevezett tokenhez adja; a már tagságban levő token ismétlése nem dupláz (`ini/albums.py:65-80`). Az eredeti ismételt hozzáadás eredménye: `NINCS MEG`. |
| Néző helyi menüje: `&Add to Album` rekord `0x007327a0`, parancsmező `0x9cc6`; a főablak diszpécsere ezt `0x00566270`-re küldi (`0x005cb990`). Ez a híváslánc még nem bizonyítja a kiválasztott albumba írást. | `ViewerContextMenu.qml:129-145`; `PhotoViewerContextActions.qml:118-121` | PicasaPyban az almenü csak legalább egy saját album esetén aktív, és a parancs az aktív nézősort adja át, tehát egy képet. Eredeti album nélküli, videós, már tagságban levő és többképes nézőállapot: `NINCS MEG`. A nézőben PicasaPy `New Album...` sort nem találtam. |
| Emberek-album képmenüje: `&Add to Album` rekord `0x007355c0`, parancsmező `0x9e39`; a főablak diszpécsere `0x00603660`-ra irányítja. | `PhotoContextMenu.qml:167-192`; `MainPhotoContextMenu.qml:129-131` | A PicasaPy általános album-hozzáadó útja a kijelölt sorokat használja. Az eredeti `0x00603660`-as ág albumtagságra gyakorolt hatása, engedélyezése és hibái `NINCS MEG`. |
| Képtálca: a `thumbui/addtobuttcon` a `thumbui/scratchback` gyereke, felirata `Add to`, súgója `Add selected items to an Album`. A gomb eseményútja `0x005fe130`, amely a tálca kijelöléséből építi/frissíti a `Labels` listát (`0x00664130`). A jobbklikkes `Hold Selection` másik rekord, bár ugyanazt a `0x9ca0` azonosítót használja. | `TrayScratchPanel.qml:497-539,542-577`; `tray_album_controller.py:237-257` | PicasaPy gombja csak nem üres tálcánál aktív, a meglévő albumot választva a tartott sorokat írja. Az eredeti gomb engedélyezési feltétele és az egyes tartott elemtípusok eredménye: `NINCS MEG`. |
| Húzás meglévő album sorára: az eredeti `lb_drop` esemény a `0x005e39a0`-hoz jut, de a meglévő Ghidra-kimenet a kérdéses fotólista és albumtagság kapcsolatát nem dönti el. A mappa-sor húzási kutatása nem bizonyít fotó-húzási viselkedést. | `AlbumsSection.qml:260-272`; `FolderPaneContent.qml:54-58`; `MainFolderPane.qml:137-140` | PicasaPy csak saját `payload == "photos"` húzást fogad, és az ejtett sorokat a célalbum tokenjéhez adja (`AlbumsSection.qml:42-45`). Az eredeti fotó-húzás, egy vagy több kép, videó, ismételt tagság és lemezhatás: `NINCS MEG`; lásd a Ghidra-kérést lent. |
| Húzás az albumlista üres területére: a binárisban szerepel a `You can drag and drop pictures here to make a new album.` szöveg (`0x00765d30` út); ez az üres lista promptja, nem bizonyíték az ejtés utáni dialógusra vagy írásra. | `AlbumsSection.qml:62-108`; `MainFolderPane.qml:130-135`; `FileOpsDialogs.qml:90-95` | PicasaPy a kijelölt képekkel `Untitled` albumot készít párbeszéd nélkül. Eredeti prompt utáni végrehajtás és mérési felvétel: `NINCS MEG` ebben a körben. |

Az eredeti `0x0056e1c0` menüállapot-kezelő módosítja az `0x9ca0`-hoz tartozó engedélyezést, de a vizsgált dekompilálás állapotbitjei nem felelnek meg bizonyítottan az egy kép, több kép, videó vagy már tag kategóriáknak. A menüpont megjelenése vagy a lista felépítése önmagában nem bizonyít műveleti engedélyezést.

### Ablak, almenü, alapérték és megjegyzett állapot

- Az eredeti helyi menükben az `Add to Album` rekord mellett a dinamikus albumlista és az `ID_LABELSNEW` / `New Album...` elem felépítése látható (`0x0056c5a0`, meglévő Ghidra-kimenet: `2026-10-21-idorend-32.txt`). A `0x00664130` `Labels` listát állít össze, és a `il_NewAlbumName` szöveget használja. A listaelem kiválasztásakor futó tartós írás nincs benne bizonyítva. A tálca erőforrásában az `Add to` gombhoz ugyancsak albumválasztó tartozik.
- Az eredeti Fájl menü `New Album...` útjáról egy korábbi, külön mérés Album Properties ablakot rögzített (`paritas-ellenorzes.md:971`, `mérés (ki00/kepernyo__11.png)`). Ez nem azonosítja bizonyítottan az Add to Album almenü New Album elemének pontos kezelőjét. A mezők az albumablak leírásában szerepelnek (`picasa-fen-dialogs.md:255-273`), de az Add-to út alapértékei és megjegyzett értékei: `NINCS MEG`.
- PicasaPy kép-helyi menüjében a meglévő albumok dinamikus listája után `New Album...` szerepel (`PhotoContextMenu.qml:167-192`); ez a tulajdonság-párbeszédet nyitja a kijelölt sorokkal (`MainPhotoContextMenu.qml:129-138`, `FileOpsDialogs.qml:82-111`). Nyitáskor a név fordított `Untitled`, a dátum, hely, leírás és zeneútvonal üres, a zene kikapcsolt; a függvény minden nyitáskor ezeket állítja vissza (`FileOpsDialogs.qml:100-111,114-116`).
- A PicasaPy tálcamenü meglévő albumokat, `Screensaver`, `Starred Photos` és `New Album...` tételeket kínál (`TrayScratchPanel.qml:542-577`). A New Album a tulajdonság-párbeszédet nyitja a tálca tartalmával (`MainTrayBar.qml:82-85`). A néző menü csak meglévő albumokat tartalmaz (`ViewerContextMenu.qml:131-145`).
- PicasaPy üres albumlista-területre ejtéskor párbeszéd nélkül `Untitled` albumot készít (`FileOpsDialogs.qml:90-95,114-116`). Ez más belépési út, mint a menü `New Album...` parancsa.

### Tárolás és felületi hatás

| Hatás | Eredeti Picasa 3.9 | Jelenlegi PicasaPy |
|---|---|---|
| Kép- és fájlrendszer | A kiválasztott albumra futó íróág nincs feloldva. Képfájl mozgatása/másolása: `NINCS MEG`. | A meglévő albumhoz adó út mappánként `.picasa.ini`-t ír; ebben a hívási ágban nem találtam képfájl-mozgatást (`photo_ops_write_text_mixin.py:206-227`). Az ini-írás backupolt (`:225`). |
| `.picasa.ini` tagság | Az album művelet `albums=` kulcsra gyakorolt eredeti hatása: `NINCS MEG`. | A token az érintett fotó `albums=` CSV-jéhez kerül; meglévő token ismétlése változatlan dokumentumot ad (`ini/albums.py:65-80`; `photo_ops_album_membership_mixin.py:28-62`). |
| Albumdefiníció, contacts/album adatbázis és SQLite index | Az Add-to művelet bármelyik adatbázisában történt írás vagy szinkron: `NINCS MEG`. Az album adatbázis inicializáló nyomai nem bizonyítják, hogy ezt a parancsot szolgálják ki. | A batch minden érintett mappánál `_sync_tree(conn, folder)`-t hív, majd siker után újratölti az albumlistát (`photo_ops_write_text_mixin.py:206-227`; `photo_ops_album_membership_mixin.py:255-268`; `controller_photo_list_mixin.py:183-197`). |
| Bal oldali albumfa | Művelet utáni fa és darabszám: `NINCS MEG`. | Siker esetén az albumlista újratöltése `albumsChanged` jelet küld, az albummodell az indexből számolja a tagságot (`controller_photo_list_mixin.py:183-197`). Köztes írási hiba esetén ez a siker utáni ág nem fut le. |
| Rács és kijelölés | Rács, sorok, kijelölés és fókusz végállapota: `NINCS MEG`. | Sikeres batch után `_refresh_view()` újraolvassa az aktuális nézetet. A `_show()` a fotórács modelljére állítja az új rekordokat; eltérő rekordsor esetén a modell-reset megtörténik (`controller_sync_mixin.py:65-101,111-157`; `photo_grid_state.py:192-211`). A kijelölés QML/Qt végállapotát ebből nem következtetem ki. |
| Ismételt hozzáadás | A már albumtag kép eredeti kezelése: `NINCS MEG`. | `with_album` nem ír be második példányt és nem változtatja a sorrendet (`ini/albums.py:65-80`). |
| Visszavonás | Az eredeti Undo/Undo All Edits vagy más visszavonás tagságra gyakorolt hatása: `NINCS MEG`. | A vizsgált `addRowsToAlbum` és `_write_album_batch` útban undo-hívást nem találtam. Felhasználói visszavonási lehetőség: `NINCS MEG`. |

### Hibák és részleges végrehajtás

- Eredeti: a `.picasa.ini` vagy album-adatbázis írási hibájának üzenete, megszakítási viselkedése, az előzőleg feldolgozott képek állapota és az esetleges visszagörgetés: `NINCS MEG`. Részben megválaszolva (Ghidra 2026-11-16, statikus): az `AlbumSync` (`0x00556ff0`) csak a `9` kódot kezeli, a többi hibakód elvész, megszakítás és visszagörgetés nincs, a már megírt mappák megmaradnak; az üzenet és a futásidejű végállapot nyitott.
- PicasaPy: a kijelölt sorok mappánként csoportosulnak, mappánként külön atomikus `update_document` fut, majd az indexfa újraszinkronizálása (`photo_ops_write_text_mixin.py:206-227`). Több mappás batch ezért nem egyetlen `.picasa.ini`-írás. Ha egy későbbi mappa írása hibát dob, a korábbi sikeres fájlírások már megtörténtek; a teljes index-tranzakció pontos részleges állapotát nem állítom.
- PicasaPy az ismert írási kivételeket `albumWriteFailed` jelzéssé alakítja, hamissal visszatér, a hibasáv az üzenetet mutatja (`photo_ops_album_membership_mixin.py:255-268`; `MainErrorBanner.qml:89-92`). A `_refresh_view()` és az albumlista siker utáni újratöltése ilyenkor nem fut le.
- **Helyesbítés:** az `open_index` `finally`-ban `conn.close()`-t hívja; a `_GuardedConnection.__exit__` visszagörgető ága ettől nem fut (`index/database.py:340-373`). A megelőző jegyzet visszagörgetésről szóló állítása nem bizonyított, visszavonva.

### Bizonyítottság, független utak és cáfoló kísérlet

- **A út, bináris rekord és utasításszintű vizsgálat:** a `&Add to Album` string-xref címekhez a helyi menük rekordbázisát és parancsmezőjét követtem. A `0x00559150` menürekordnál a `0x0055b777` `eax`-forrása `0x00c8d8b8`; ez a `0xd6e498` címkéjét állítja `&View and Edit` értékre, a hozzá tartozó parancsmező `0xd6e4a2 = 0x9ca0`. A következő, `0xd6e4ac` bázisú rekord címkéje `&Batch Edit` (`0x0055b79f`), tehát nem az előző parancs címkéje.
- **B út, független erőforrás:** a `thumbui.tre` és `thumbui_text.tre` az `Add to` tálcagomb helyét és `Add selected items to an Album` súgóját rögzíti; ezt a bináris `0x005fe130` -> `0x00664130` listafelépítő útja is megerősíti. Ez a két út a tálca Add-to felület létezésében egyezik. A többi helyi menü parancsazonosítója egy bináris útból feltételes, az albumtagság írási végállapotát egyik út sem igazolja.
- **Cáfoló kísérlet:** cáfoltam azt a jelöltet, hogy a `0x9ca0` minden helyen Add to Album. A főmenü rekordja `&View and Edit`; a tálca jobbklikk-menüjének `0xd6edca` mezője ugyanezt az azonosítót a `&Hold Selection` felirathoz használja (`0x00732f35` `Tray::ID_PICTURE_HOLDINPICTURETRAY`, `0x00732f3a` `eax = 0x00cae63c`, `0x00732f4c` `0x9ca0`). Mindkettőt a rekord bázisa, szövegforrása és parancsmezője alapján ellenőriztem. A parancsszám ezért önmagában nem jelentést hordozó, globális azonosító.
- **Bizonyítottsági fok:** a tálcagomb mint Add-to felület megerősített két független úttal. A helyi menük egyedi felirat/parancs párosítása egy bináris útra támaszkodik, ezért feltételes. A jegy teljes folyamata nyitott, mert az eredeti tagságíró, adatbázis-hatás, részleges hiba, visszavonás és végső UI-állapot nem dőlt el.

### A jegy „Kész, ha” pontjai

1. ⛔ **Minden belépő és feltétel, egy és több kép, videó, már albumban lévő kép:** a táblázat külön kezeli a fájlmenüt, két bélyegkép-nézetet, nézőt, Emberek-albumot, tálcát, meglévő albumra és üres területre ejtést. Az eredeti engedélyezési feltételek és a video/ismételt tagság viselkedése nyitott.
2. ⛔ **Ablak/almenü, alapérték és megjegyzett állapot:** a címkék/listaépítés és a jelenlegi dialógusértékek dokumentálva vannak. Az eredeti Add-to New Album elem dialógusa, értékei és megjegyzése nyitott.
3. ⛔ **Tárolás, index, fa, rács, kijelölés, ismétlés és undo:** PicasaPy útja forrásból le van írva. Az eredeti `.picasa.ini`, adatbázis, index, UI-végállapot, ismétlés és visszavonás nyitott.
4. ⛔ **Írási hiba és részleges végrehajtás:** PicasaPy hibajelzése dokumentált, az eredeti íróút és a pontos PicasaPy-index részleges hibaállapot további vizsgálatot igényel.

### Javasolt fejlesztői jegytörzs

E körben nincs bizonyított Add-to végállapotbeli eltérés, amelyhez biztonságosan fejlesztési jegy írható. Előbb a nyitott eredeti műveletet kell célzottan feloldani; a leírt PicasaPy viselkedés jelenlegi forrásállapot, nem önmagában paritásdöntés.

### Új kutatási jegyjavaslatok

- **Az eredeti Add to Album tagságíró és hibautja.** Kérdés: a dinamikus albumtétel kattintása mely kezelőn keresztül írja a képek tagságát, az `albums` mezőt, az album/contacts adatbázist és az indexet; mi történik egy/multiple, videó, már tag és írási hiba esetén; visszavonható-e? Hol keresd: `0x00664130` Labels-lista kiválasztási callback, `0x005cb990` command-diszpécser. A meglévő `2026-10-29-koteg-33.txt` a lista felépítését, `2026-10-21-idorend-30.txt` a dispatchert mutatja, de nem a kijelölt albumtagság-írást.
- **Fotók húzása meglévő albumra az eredeti Picasában.** Kérdés: az `0x005e39a0` `lb_drop` út fotó-kijelölést fogad-e, és mely albumtagság- vagy fájlrendszer-műveletet futtatja? A meglévő `2026-11-13-6845-6532-colab-decomp.txt` mappa/album-lista húzásról szóló dekompilálása ezt a fotó-húzási esetet nem dönti el.

### Nyitott

- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): a `0x00664130` csak a `Labels` listát építi (`"%s (%s)"`, `il_NewAlbumName`), a `0x005fe130` a tálca Add to gombja, csak nem üres tálcánál; a kiválasztáskor futó író egyikben sincs. Erős jelölt a `0x0045ef50` (lásd lent).
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x0045ef50` **nem** az album-tagságíró: minden más albumból eltávolítja az átadott elemeket (`0x006cb200`), kihagyva a célalbumot és amire a `0x004461a0` igaz; a hívója a `]facealbum:%d`-s `0x0055d120`, tehát arcalbumra vonatkozik (egy arc egy emberhez). A húzás albumra ennek megfelelően arcalbumnál kizárólagos tagságot ad; a közönséges album tagságírója ebben a körben nem került elő.
- Ghidra-kör kell: 0x005fe130 - a tálca Add to gombjának és a helyi menü Labels listájának elemválasztó visszahívása melyik kezelőt hívja, és az milyen `albums=`/adatbázis-írást végez [megválaszolva a statikus kutatási kiegészítésben lent: helyi menü `0x00536a90`, tálca `0x00577c30`; a fájlba írás kapcsa még nyitott]
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7028-colab-decomp.txt`): a `0x005fe130` a `thumbui/addtobuttcon` kezelője (a `0x005d9cc0` hívja), nem üres tálcánál a `0x00664130` listapanelt építi. A helyi menü `Add to Album` almenüjét (`0x9cb9`) a `0x005eab70` építi (hívója a `0x0056c5a0`): albumonként a `0x00452d10` album-azonosítójával, az Emberek- és a webes albumok nélkül, a végén `IDS_NEW_COLLECTION` (New Album) elemmel. Ez egyezik a PicasaPy almenüjével, amely saját albumokat és `New Album...` sort kínál. Az elemválasztás utáni tagságíró ebben a kötegben sincs, ezért a fenti blokkoló kérdés nyitott marad.
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): albumcsomópontra (`CAlbumSelectionNode`) ejtésnél a célalbum azonosítója `+0x3c0`; ha azonos a forrás albummal, nem történik semmi, különben a `0x0045ef50(db, lista, album)` írja a tagságot (ugyanez fut új album létrehozásakor a `0x0055d120`-ban). Emberek-albumnál külön ág (`]expeople:%d`, `0x0044bdf0`); a 4-es húzástípus a `0x005ea770` mappatulajdonságok útra megy. Fájltípus-feltétel nem látszik.
- NINCS MEG: eredeti Add-to/New Album párbeszéd alapértékei és megjegyzett állapota. Részben megválaszolva (Ghidra 2026-11-16, statikus): az Add-to `New Album...` útján (`1`-es mód) az alapértelmezett név üres, a dátum a lista első elemének ideje; a többi mező és a megjegyzett érték nyitott. Megszerzés: célzott Picasa 3.9 mérés a meglévő-album almenü New Album útján, képernyőkép és minden mező rögzítésével, majd külön ismétlés újranyitással.
- NINCS MEG: az eredeti Add-to siker/hiba utáni fa, rács, kijelölés, kép- és adatbázis-végállapot, valamint visszavonás. Megszerzés: a blokkoló Ghidra-kör után előtte/utána mérés kis, egy- és többmappás tesztkészleten; fájlok, `.picasa.ini`, album/contacts adatbázis és UI-állapot összevetése. A meglévő mérőadat-archívum taglistájában ehhez releváns Add-to/album-dialog felvételt nem találtam.

### Kiegészítés (2026-11-15, statikus kutatás): a kiválasztott albumhoz adás írója

Módszer: utasításszintű diszasszembly (`capstone`) a `0x0056c5a0`, `0x005e4ac0`, `0x005cb990`, `0x00536a90`, `0x00577c30`, `0x006ca130`, `0x006cae50`, `0x006ca5a0`, `0x004abc70`, `0x004b94a0`, `0x00402a90`, `0x00556ff0` és `0x0052c350` függvényen, valamint a `binary-index` (`xrefs`, `string_xrefs`, `rtti`) és a meglévő Ghidra-kimenetek olvasása. Futásidejű Picasa-mérés nincs. Fokok: **megerősített** = két független út, **erős** = egy út, egyértelmű utasításokkal, **feltételes** = következtetés.

**A blokkoló kérdés válasza (erős): a helyi menü `Add to Album` almenüjében egy album kiválasztását a `CThumbUI` osztály (`CThumbUI::vftable`, `0x00c9052c`) `0x00536a90(this, 0)` függvénye írja.** A kijelölt képek azonosítóit az album gyűjtemény-objektumának képlistájához fűzi. Az útja:

| Lépés | Cím | Mit tesz | Fok |
|---|---|---|---|
| 1. Almenü felépítése | `0x0056c5a0`, a `0x0056d24d`-től | `CreatePopupMenu`, majd `SetMenuItemInfo(menü, 0x9d8f)`: a popup a `0x9d8f` azonosítójú menüelem almenüje. Tartalma sorrendben: (a) a `0x004b94a0(nézet, &lista, 1)` albumai, vagyis azok a gyűjtemények, amelyek belső neve `]album:` előtaggal kezdődik, a `0x004baaa0` összefésülő rendezésével; (b) elválasztó, ha van album; (c) a `]star`, majd a `]screensaver` gyűjtemény, ha név szerint megtalálható a katalógusban; (d) elválasztó, ha volt (c); (e) `New Album...` (`ID_LABELSNEW`, parancs `0xa09c`). Az albumtételek parancsazonosítója `0xbb80 + sorszám`, az elemadat (`dwItemData`) a gyűjtemény azonosítója (`0x00a6b120` hozzáfűző burkoló). | erős |
| 2. Kiemelés | `0x005e4ac0` ablakkezelő, `WM_MENUSELECT` (`0x11f`) ág, a `0x005e4c35`-től | Minden kiemelésnél a `CThumbUI+0xe30`, `+0xe34`, `+0xe40` mező `-1`-re áll; a `0xbb80..0xc34f` tartományú parancsnál a `0x005c6670` (`GetMenuItemInfoA`, `MIIM_DATA`) elemadata kerül a `+0xe40` mezőbe. | erős |
| 3. Parancs | `WM_COMMAND` -> `0x00a527b0` -> `CThumbUI` vtábla `+0x5c` = `0x005cb990`, a `0x005cd981`-től | `0xbb80 <= parancs < 0xbf68`: `0x00536a90(this, 0)`; `0xbf68 <= parancs < 0xc350`: `0x00536a90(this, 1)` (ezt az Emberek-album menüjének `&Move to People Album` almenüje, `0xa0cd`, adja, a `]expeople:%d` ág, `0x0044bdf0`; nem közönséges albumtagság). | erős |
| 4. Író | `0x00536a90` | Lásd lent. | erős |

**A `0x00536a90(this, 0)` viselkedése, közönséges album esetén (erős).**

- Kilép, ha a `+0xe40` mező `-1`, vagy nincs aktuális csomópont vagy kijelölés (`+0xeac`, `+0xea8`), ilyenkor 0-val tér vissza, és semmit nem ír. A `+0xe40` mezőt a képlista összeállítása után, a gyűjtemény-objektum lekérése előtt (`0x00536c00`) állítja `-1`-re.
- Képlista: ha a szerkesztő vagy néző aktív (`0x00579330`, `editpanel/preview +0x20c == 0`) és `+0xe64 != -1`, akkor **egyetlen kép** (az aktuális, `+0xe64`); különben a **teljes kijelölés** (`0x007166c0`), kijelölési sorrendben.
- `0x004b0190(nézet, albumazonosító)` előállítja a gyűjtemény-objektum hozzáférőit; ha a `+0x5c` vagy a `+0x64` mező nulla, `-1`-gyel tér vissza, és semmi nem íródik, üzenet nélkül.
- **Már tag kép:** a `0x006cae50` (tagság-vizsgálat a `[objektum+0x64]` képlistában) igaz értékénél a képet **kihagyja**: nincs duplikálás, nincs átrendezés, nincs üzenet. Ez egyezik a PicasaPy `with_album` viselkedésével (`ini/albums.py:65-80`).
- **Új tag:** a `0x006ca130` hozzáfűzi a képazonosítót a képlista **végére** (`push_back`, zár alatt). Nem nulla visszatérésnél (a `4` memóriahiba) a függvény azonnal visszatér, a már hozzáadott képek bent maradnak, visszagörgetés nincs.
- **Videó és egyéb típus:** a függvényben nincs típusszűrés. A hívásai (`0x00401000`, `0x00407610`, `0x004133e0`, `0x00413490`, `0x00448a10`, `0x00448c90`, `0x0044bdf0`, `0x0045ecf0`, `0x0047bf40`, `0x0048ef20`, `0x004abc70`, `0x004af790`, `0x004b0190`, `0x004da1d0`, `0x00506400`, `0x00512c90`, `0x00579330`, `0x005d27d0`, `0x00602df0`, `0x0065b840`, `0x006ca130`, `0x006cae50`, `0x007166c0`, `0x00717140`, `0x0097c810`, `0x0097caf0`, `0x0097e4c0`, `0x009d2c80`) között nincs fájlnyitás, fájlírás, üzenetablak és visszavonás-regisztráció. Az Emberek-ág (`0x0044bdf0`, `0x004da1d0`) csak a `flag != 0` és Emberek-album esetén fut.
- Hozzáadás után: `0x004abc70(nézet, album)` a gyűjteményt "piszkosnak" jelöli (`[nézet+0x138]` állapottábla, 0x24 lépésköz, `+0xc` állapot), `[nézet+0x166] = 1`, `0x004af790` megkeresi az album sorát a bal oldali listában, és ha megvan, `0x009d2c80(0)` újrarajzolja azt, majd `0x0065b840(this, 0, 0, 1)` frissíti a fő nézetet. **Navigáció az albumra nincs** (a `New Album` ággal ellentétben). A kijelölés végállapota nyitott (`0x0065b840` belseje).
- Ha az album belső neve `]star` (`0x00536efe`, 6 bájtos összehasonlítás), a `0x005d27d0` a `thumbui/startoggle` csillag-kapcsolót frissíti. A `]star` választása tehát **hozzáadás** (a már csillagos kép marad), nem megfordítás.

**Tároló.** A tagság közvetlen helye a gyűjtemény-objektum `+0x64` képlistája (képazonosítók vektora), ez **memória** (erős). A `.picasa.ini` felé a katalógus megfigyelői visznek: a `0x00402a90` a `Preferences\AlbumIniSync` kapcsoló (alapérték 1) alapján létrehozza a `PicasaIniManager` (`0x00c89768`, 5 bejegyzés: `0x0052a7e0`, `0x0052a810`, `0x0052ab10`, `0x0052b220`, `0x0052c350`) és az őt használó `AlbumSync` megfigyelőt (`0x00c7f580`, a `+0x54` mezőben a kezelővel), amelyet a `0x00402370` a katalógus egyik táblájához köt. Az `AlbumSync` `0x00556ff0` és `0x00557760` bejegyzése mappánként hívja a `PicasaIniManager` `+0x10` bejegyzését, a `0x0052c350`-et (paraméterei: a mappa gyűjtemény-azonosítója, az album `]album:` előtagú belső neve, a képek listája). A `0x0052c350` a katalógus `+0x14` bejegyzésével lekéri a mappa útvonalát, hozzáfűzi a `.picasa.ini` nevet, a belső névből tokent képez, és az `albums` (és `token`) kulcsot írja (szövegei: `]album:`, `.album:`, `token`, `albums`, `.picasa.ini`). Ha `9`-et ad, az `AlbumSync` előbb az 1. bejegyzést (0x0052a810: a #7235-kiegészítés szerint name, token, description, location, date, majd a dinamikus kulcspárok írója `[.album:token]` meghatározásának létrehozása) hívja, majd újra próbálja a 4. bejegyzést (a `9` jelentése feltételes). A `0x0052b220` ugyanezeket a kulcsokat és a `description`, `location` kulcsot használja (az album meghatározásának olvasása vagy frissítése). Fok: a `0x0052c350` mint az `albums=` író **erős** (szövegek, hívási forma, az `AlbumSync` hívásai); az, hogy a `0x00536a90` után pontosan ez hívódik, és mikor, **feltételes**, mert a `0x004abc70` csak jelzőt állít. Az `AlbumIniSync = 0` esetén a `0x00402a90` kihagyja a két objektum létrehozását, tehát az ini-írás elmarad (feltételes).

**Tálca (erős).** A tálca `Add to` gombja (`0x005fe130`) csak a `Labels` listapanelt (`0x00664130`) építi és kapcsolja. Az írás a `thumbui/makealbum` csomópont kezelőjében van: `0x00577c30` (a `0x005d9cc0` hívja). A tálca képlistáját (`+0xea4`, `0x007164b0`) és a panel kijelölt sorának albumazonosítóját (`0x00562640`, sor `+4`) használja: `0x004b0190` + **`0x006ca5a0`** (kötegelt hozzáadás, a már tagokat kihagyja), majd `0x0065b840`, `0x004abc70` és `0x00665180` (a panel frissítése). A sor `+8` bájtjának 0. bitje (feltételes) az új album sort jelöli, az `0x00577ea0` ágra visz. A lista (`0x004b94a0(nézet, &lista, 0)`) minden listázható gyűjteményt tartalmaz az arcalbumok (`]facealbum:`) kivételével, tehát a `]star` és a `]screensaver` is bekerülhet; ez összefér a mért tálcamenü-sorrenddel (`TrayScratchPanel.qml:545`, job-259), de azt nem bizonyítja.

**Helyesbítés (erős).** A korábbi bejegyzések két azonosítása hibás:

1. A `0x005eab70` és a `0x9cb9` **nem az `Add to Album`**, hanem a Mappa helyi menü (`0x007319f0`) **`Move to Collection`** (`Folder::ID_ALBUM_MOVETOCOLLECTION`) almenüje. Az `IDS_NEW_COLLECTION` szövege `New Collection...`, a kérdése `Enter Collection Name:` (`referencia/i18n/enUK/stringres.xml:282,264`), tehát nem `New Album`. Az `0xafc8 + n` parancsok elemadatát ugyanaz a `WM_MENUSELECT` ág a `+0xe30` mezőbe teszi, a menü bezárásakor (`WM_EXITMENULOOP`, `0x212`) fut a `0x005eb160`, amely a `0x00445b80(db, mappa-csomópont, gyűjtemény, 1)` hívással a mappa gyűjteményét állítja; a `New Collection...` (`0xa04d`) a `0x005cd7b2` -> `0x005eb230` úton ugyanide fut. Ez a mappa gyűjteménybe sorolása, nem képek albumtagsága. A PicasaPy ezt már tudja (`src/picasapy/help/en/features/konyvtar.md:173`: a mappa jelenlegi gyűjteménye pipált és szürke).
2. A menürekord-építőkben a `mov word ptr [..], <parancs>` mező **az eggyel megelőző rekordhoz** tartozik, nem ahhoz a blokkhoz, amelyben áll. Bizonyíték három úton: (a) a `0x007319f0`-ban a `Collapse All` blokkban álló `0x9dc0` valójában az `Expand All` parancsa, a rákövetkező `0x9e3b` a `Collapse All`-é; a diszpécser mindkettőt a `0x00600ec0(this, 1)`, illetve `(this, 0)` hívásra küldi (kibontás, összecsukás); (b) a `0x00730790` első blokkjában, az `&Add to Album` mellett álló `0x9ca0` a megelőző `View and Edit` rekordé, és a diszpécser `thumbui/fullview`-ra küldi (`0x005cbd26`); (c) a néző menü `0x007327a0` építőjében az `&Add to Album` mellett álló `0x9cc6` a `0x00566270`-re megy, amely az `editpanel/preview` és a `thumbui/albumview` csomópontot kezeli, vagyis a visszatérés a könyvtárba; (d) az Emberek-menü `0x007355c0` építőjében a `Move to New Person...` `0xa0cc` parancsa a `0x005cd90d` -> `0x005e9890(this, 1)` útra megy (új személy), az `&Move to People Album` `0xa0cd` azonosítóját a `0x0056c5a0` Emberek-ága köti a személylista almenüre, a `Set as People Album Thumbnail` `0x9e39` parancsa a `0x00603660`-ra megy (borítókép), és az `&Add to Album` ebben a menüben is a `0x9d8f`. Következmény: az `&Add to Album` rekordok tényleges parancsa a `0x9d8f` (a rákövetkező blokk mezőjéből, a `0x00730790`, `0x00731050` és `0x007327a0` építőben), és a `0x0056c5a0` is ezt az azonosítót köti az almenüre; a `0x9d8f` a diszpécserben nincs kezelve (almenü-fej). A fenti táblázat `0x9ca0`, `0x9cc6` és `0x9e39` Add-to párosításai érvényüket vesztik; a `0x9ca0` a `View and Edit` azonosítója (a főmenü `&View and Edit` rekordjában is), a `0x9e39` az Emberek-album borítóképe. A tálcamenü `Hold Selection` rekordjának `0x9ca0` párosítását és az abból levont cáfoló kísérletet ez a kör nem ellenőrizte újra; ugyanez az eltolás érintheti.

**Összevetés a PicasaPyval.**

| Szempont | Eredeti | PicasaPy | Eltérés |
|---|---|---|---|
| Több kép | a kijelölés minden képe, sorrendben | `_rows_to_photos`, mappánként egy ini-írás (`photo_ops_album_membership_mixin.py:28-62`) | nincs |
| Már tag | kihagyja, nem duplikál, nem rendez át | `with_album` idempotens (`ini/albums.py:65-80`) | nincs |
| Hozzáadás helye | a képlista végére | az `albums=` lista végére (`ini/albums.py:65-80`) | nincs (a két tároló szerkezete más, a sorrend-egyezés feltételes) |
| Videó | nincs típusszűrés | nincs típusszűrés (`photo_ops_write_text_mixin.py:202-204`) | nincs |
| Néző | az aktuális egy kép (`+0xe64`) | az aktív nézősor (`PhotoViewerContextActions.qml:118-121`) | nincs |
| Hozzáadás után | az album sora és a nézet frissül, nincs navigáció, nincs kérdés | `_refresh_view()`, `albumsChanged` (`controller_photo_list_mixin.py:183-197`) | nincs |
| Almenü tartalma | albumok, elválasztó, `Starred Photos`, `Screensaver`, elválasztó, `New Album...` | albumok, elválasztó, `New Album...` (`PhotoContextMenu.qml:167-192`) | **van**: a `Starred Photos` és a `Screensaver` hiányzik a fotómenüből |
| `Starred Photos` választása | hozzáadás a `]star` gyűjteményhez (idempotens), csillag-kapcsoló frissítése | a tálcában `toggleStarMany` (megfordít, `photo_ops_transform_mixin.py:90`) | feltételes: a megfordítás és a hozzáadás kimenete eltér a már csillagos képnél |
| Albumok sorrendje | `0x004baaa0` rendezés | `controller.albums` sorrendje | nyitott |
| Visszavonás | nincs látható | nincs | nincs (feltételes) |
| Hiba | a `0x00536a90`-ban nincs üzenet; az ini-írás hibája az `AlbumSync`-ben ágazik: a `0x00556ff0` csak a `9` kódot kezeli (létrehozás, majd újrapróba), minden más hibakódot (a `-1`-et is) figyelmen kívül hagy, nincs üzenet, megszakítás vagy visszagörgetés (Ghidra 2026-11-16) | `albumWriteFailed` hibasáv (`photo_ops_album_membership_mixin.py:255-268`) | nyitott |

#### Javasolt fejlesztői jegytörzs (a statikus kutatás után)

**Fotómenü `Add to Album` almenüje: `Starred Photos` és `Screensaver` tétel.**

- Eredeti: a `0x0056c5a0` a fotók helyi menüjében az albumok után, elválasztóval lezárva, a `]star` és a `]screensaver` gyűjteményt is felkínálja, ha az adott gyűjtemény név szerint létezik a katalógusban; utána újabb elválasztó és a `New Album...` következik. A választás ugyanaz a `0x00536a90` ág: hozzáadás, a már tag kimarad, `]star` után a csillag-kapcsoló frissül. Fok: erős. A tételek megjelenése feltételes (létezik-e a gyűjtemény).
- Nálunk: `PhotoContextMenu.qml:167-192` csak az albumokat és a `New Album...` sort adja; a két különleges tétel csak a tálcamenüben van (`TrayScratchPanel.qml:542-577`).
- Elfogadási feltétel: a menü renderelt képe és az eredeti almenüről készült Picasa-képernyőkép összevetése (a szövegeket és az elválasztók helyét a bináris nem adja, csak a sorrendet). Képernyőkép nélkül a jegy nem zárható.
- Nem szabad: a tálcamenü mért sorrendje (`Screensaver`, `Starred Photos`, albumok, `New Album...`, elválasztó nélkül) nem változhat; a meglévő albumtételek és a `New Album...` viselkedése nem változhat.
- Nyitott döntés a jegyben: a `Starred Photos` tétel a már csillagos képen az eredetiben hozzáad (nem fordít), a PicasaPy `toggleStarMany` fordít; a jegynek ezt a binárisból kell eldöntenie (`0x005e81e0`, `0x005d27d0`).

#### Új kutatási jegyjavaslatok (a statikus kutatás után)

- A `0x00536a90` utáni ini-írás kapcsa: hogyan jut el a `0x004abc70` piszkos jelzője az `AlbumSync` és a `PicasaIniManager` hívásáig, és mikor (azonnal, időzítve, kilépéskor).
- A fotómenü almenüje a nézőben és az Emberek-albumban: melyik menütípus (`0x0056c5a0` második paramétere) melyik építőhöz tartozik.

#### Nyitott (statikus kutatás után)

- Ghidra-kör kell: 0x00556ff0 - az `AlbumSync` (`AlbumSync::vftable` `0x00c7f580`) 2. bejegyzése: ki és mikor hívja (vtábla-hívás, az index nem látja), és a `0x004abc70` piszkos jelzője (`[nézet+0x138]`, 0x24 lépésköz, `+0xc` állapot; ugrótábla `0x004abd3c`) hogyan vezet ide. Ezzel dől el az ini-írás időzítése és sorrendje.
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:1537`): a kimenet részben dönt. A `0x00556ff0` (`:1537-1710`) az `AlbumSync` 2. bejegyzése (`0x00c7f588`; a kimenet egyetlen hivatkozója ez az adatsor, vagyis vtábla-hívás), és **mappánként** dolgozik: a `+0x4c` objektum `+0x2c` metódusa adja a kép adatait, a `0x005578e0` a mappalistát, bejegyzésenként a `0x00557a50` a fájlnévlistát, majd a `+0x54` objektum `+0x10` metódusa fut `(bejegyzés, param_3, fájlnévlista)` argumentumokkal. A `+0x54` a `PicasaIniManager` (az `AlbumSync` konstruktora, `0x00402470`, a `+0x54`-be a második argumentumát teszi; a `0x00402a90` ezt a `0x00402b41` hívással épített `PicasaIniManager`-példányból adja, `[db+0x1054]`), a `+0x10` tehát a `0x0052c350`. **Hibakezelés:** csak a `9` visszatérést kezeli (`0x005572a7 cmp eax, 9`): létrehozó szerkezetet épít (`0x00557cf0`, ha az nem nulla, a létrehozás kimarad), a `+4` metódust hívja (`0x0052a810`), majd ugyanazzal a listával újra a `+0x10`-et; minden más visszatérési érték, a `-1` is, figyelmen kívül marad, nincs megszakítás és nincs visszagörgetés, a ciklus a következő mappára lép (`0x00557343`). **Az időzítés nyitva marad:** ki hívja a vtábla 2. helyét, a kimenet nem mondja meg. Az index szerint az `AlbumSync` az `AlbumNotification` leszármazottja (`0x00c7f680`), a `0x004039f0` a `[db+0x1050]` példányt és egy `CAlbumCreator` (`0x00c7f70c`) feladatot a `0x00556920`-nak adja át (`0x00403e16`), a sor kezelője az `AlbumNotificationManager` (`0x00c7f540`, `0x00402370` konstruktor, eseményobjektummal). A `0x004abc70` piszkos jelzője a kimenetben nincs.
- Ghidra-kör kell: 0x004d3080 - az `AlbumNotificationManager` (`0x00c7f540`) 2. bejegyzése, és a `0x004d3010`, `0x004d31c0`, `0x004d3150`, `0x004d3260`: a sorba tett `AlbumNotification` (`AlbumSync`) 2. bejegyzését (`0x00556ff0`) mikor és melyik szálon hívják (azonnal, időzítve, kilépéskor); 0x00556920 - a sorba tétel (hívói `0x004039f0`, `0x00576a20`); 0x004abc70 - a piszkos jelző (`[nézet+0x138]`, `0x24` lépésköz, `+0xc` állapot, ugrótábla `0x004abd3c`) hogyan jut ide [blokkoló az ini-írás időzítéséhez]
- Ghidra-kör kell: 0x0052c350 - a `PicasaIniManager` 4. bejegyzése: mely mappák `.picasa.ini` fájljába, milyen sorrendben és hibakezeléssel írja az `albums` és `token` kulcsot (`9`-es hibakód), és a `0x0052b220` ki hozza létre az `[.album:token]` szakaszt.
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:1191`): egy `0x0052c350` hívás **egyetlen mappa** `.picasa.ini` fájlját írja (`<mappa>/.picasa.ini`, sztring `0x00c80a6c`); a mappát a `param_2`-ből a `+4` objektum `+0x14` metódusa oldja fel (hiba: `-1`, ekkor semmi nem íródik). Hogy mely mappák következnek és milyen sorrendben, azt a hívó (`0x00556ff0`, `0x005578e0` mappalista) adja, ez a kimenetből nem látszik. A `param_3` albumazonosítóról a `]album:` előtagot (`0x00c7e8c0`, 7 karakter; `0x00987030`, `0x00986120`) levágja. **Sorrend és hibakezelés:** (1) ha a fájllista nem üres és az albumrekord nincs az ini szakaszai között (`0x0052cd90` hamis), `9`-cel tér vissza (`0x0052c475`), és ekkor még semmit nem írt (az első `0x005ab210` hívás ez után van); (2) az ini meglévő szakaszain sorban (`0x3c` lépésköz): ha a fájlnév nincs a listában (`0x0052d340` `-1`), a `0x0052cc80`, ha benne van, a `0x0052ca50` alakítja az `albums` értékét (a szerepük a hívási feltételből következik: kivétel, illetve hozzáadás), és csak ha a segéd igazat ad, íródik `0x005ab210(szakasz, "albums", érték)` (`0x00c7e900`); (3) a lista azon fájljaira, amelyeknek nem volt szakaszuk, a lista sorrendjében `0x005ab100` (szakasz felvétele) és `albums=<token>` következik; (4) üres lista esetén `0x005aafd0` és `token=<token>` (`0x00c7e8d0`) a `0x0052c990` által az azonosítóból képzett szakaszba. A függvény a részhívások eredményét nem gyűjti, nincs visszagörgetés, a részleges írás a hívó szintjén marad. **A `[.album:token]` szakaszt ez a függvény nem hozza létre:** a `9` utáni létrehozás a hívó `+4` metódusa, a `0x0052a810` (az index szerint `]album:`, `token`, `description`, `location`, `.picasa.ini`, `%I64u` sztringekkel, hívja a `0x005ab210`-et); a `0x0052b220` (4245 bájt, `.album:` és `albums` sztringekkel) hívója a kimenetben nincs, tehát a kérdésre erre nem ad választ.
- A 2026-11-18-as Ghidra-kiegészítés megválaszolta a 0x0052a810 kulcskészletét és sorrendjét: name, token, description, location, date, majd dinamikus kulcspárok. Nyitott: 0x0052b220 (+0xc slot) hívója és szerepe; 0x005578e0 mappalista-forrása és sorrendje; a 0x0052cc80/0x0052ca50 token-hozzáadás/kivétel pontos sorrendje és ismétlésviselkedése [nem blokkoló]. A 0x0052c350 korábbi dekompilációja a hívási feltételeket megmutatja, de a két segéd közvetlen szemantikáját nem.
- Ghidra-kör kell: 0x004a7890 - az albumlista rendezési kulcsa és iránya (a `0x004baaa0` összefésülő rendezés összehasonlítója): a menü sorrendje megegyezik-e a bal oldali listáéval.
- Ghidra-kör kell: 0x0056e1c0 - a `0x0056c5a0` második paramétere (`0x8a`, `0x8b`, `0xa6`, `0x127`, `0x13d`, `0x77`) melyik helyi menühöz tartozik; a néző menüje ugyanezt az almenüt (és a `New Album...` sort) kapja-e.
- Ghidra-kör kell: 0x005d9cc0 - a tálca `Labels` panel sorára kattintás azonnal ír-e, vagy a `thumbui/makealbum` gomb kell hozzá, és a `0x00665180` mit frissít.
- Ghidra-kör kell: 0x005e9bb0 - a `New Album...` (`0xa09c` -> `0x005e9890` -> `0x005e9bb0(this, 1)` -> `0x005eaab0` -> `0x005ea770`) párbeszédének alapértékei és a létrehozás utáni kijelölés. A `thumbui/albumbutton` gomb is ugyanide fut, tehát ez az eredeti `New Album` közös útja.
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:3643`): a kimenet részben dönt. A `0x005e9bb0(this, mód)` (`:3643-3789`) két módban fut. **Az `1`-es mód (a `New Album...` `0x005e9890`-ből, és a tálca `thumbui/albumbutton` eseményéből, `0x005da2f6`, `push 1`):** a `+0xea4` nézetet átmásolja a `+0xea8`-ba, és a `0x007166c0(nézet, 1)` listáját veszi; **alapértelmezett név nincs** (a `0x005eaab0` második paramétere 0). **A `0`-s mód** (a `0x9cb6` menüparancsból, `0x005cbce2`, és a tálca `thumbui/newfolder` eseményéből, `0x005da365`; az ugrótábla és a hívóhely-disassembly szerint): a `+0xeac` nézet `+0x3c0` mezőjéből a `+700` objektum `+0x48` al-objektumának `+0x14` metódusával kap egy sztringet (`0x004089e0`, `0x009a3b50` feldolgozza), ez lesz az alapértelmezett név. **Alapértelmezett dátum mindkét módban:** a `0x00c7ccf8` nyolcbájtos állandó (`double` 949998.0) a kiindulás, a `0x005c6460(a lista első eleme, &dátum)` ezt felülírja. **Üres lista:** a függvény `4`-gyel tér vissza, a párbeszéd nem nyílik meg; a `0x005e9890` ekkor (`0x005e98f1 cmp esi, 4`) az `IDS_MUSTHAVESELECTION` szöveget (`0x009ae710(0xfc, ...)`, `At least one image must be selected in order to perform this action.`) jeleníti meg, a tálca ágai a visszatérést eldobják, üzenet nincs. **A párbeszéd és a létrehozás** a `0x005eaab0(&név, alapnév, dátum)` (181 bájt, hívottai a `0x005ea770`, `0x007166c0`, `0x00506400`; a `0x005ea770` sztringjei `Labels`, `CThumbUI::albumname`), nem ez a függvény; nem nulla visszatérése (mégse) változtatás nélkül kilép. **A létrehozás utáni kijelölés:** `0` visszatérésnél `0x0065b840(this, 0, 0, 1)`, majd a `+0x2a4` objektum `+0x44` metódusa az új album nevével és `(1, 1, 0)` argumentumokkal; hogy ez pontosan kijelöl, megnyit vagy kinyit, a kimenet nem dönti el, mert ennek a metódusnak a törzse nincs benne; a `0x00600ac0` a Vissza/Előre előzmény visszaállításakor ugyanezt a metódust hívja a rekord mappa- vagy albumkulcsával és `(1, 1, 0)` argumentumokkal, tehát a hívás egy mappára vagy albumra lépés a bal oldali nézetben (a pontos jelentés nem dönthető el).
- Ghidra-kör kell: 0x005eaab0 és 0x005ea770 - a párbeszéd mezői és alapértékei (a név és a dátum alapértéke mellett a leírás, hely), a megjegyzett értékek újranyitáskor, és az album tényleges létrehozása; a `this+0x2a4` objektum `+0x44` metódusa - mit jelent a `(1, 1, 0)`: kijelöli-e az új albumot a bal oldali fában és a rácsot [nem blokkoló]
- NINCS MEG (futásidejű): a hozzáadás utáni rács, kijelölés és bal oldali fa végállapota. Megszerzés: előtte/utána mérés kis tesztkészleten a `0x0065b840(this, 0, 0, 1)` hatásának igazolására.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7012 alszakasz.

### Kiegészítés (2026-11-16, zárókör): a megmaradt tételek döntése

Módszer: a `Picasa3.exe` (3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`) utasításszintű visszafejtése (`capstone`), a hívóhelyek regiszter- és veremhasználatának ellenőrzésével; a meglévő Ghidra-kimenetek újraolvasása; a `docs/specs` többi lapja (menüleltár, helyi menük, tálca, ini, könyvtár-eszköztár). A dekompilációban `unaff_*` és `local_*` néven látszó értékeket mindenhol a hívóhely utasításaival vetettem össze. Futásidejű mérés nincs. Döntés: (a) a meglévő bizonyítékból eldőlt, (b) egy célzott Ghidra-kör vagy mérés dönt, (c) nem érinti a felhasználó által látható viselkedést. Fokok: megerősített (két független út), erős (egy út, egyértelmű utasítások), feltételes (következtetés).

**Három pontosítás a korábbi bejegyzésekhez (a régi szöveg érintetlen):**

1. **Húzás albumsorra: a `+0x3c0` a FORRÁS album, a cél a sor rekordjából jön (erős).** A `0x005e39a0` a ledobott elemek hordozójából (`ytDragNode`, a fotólista a `+0x280` mezőn) a `+0x278` mezőn át a `CAlbumSelectionNode`-ot kéri el, és annak `+0x3c0` mezőjét (`0x005e3b81 mov esi,[eax+0x3c0]`) a célazonosítóhoz hasonlítja (`0x005e3b87 cmp edi,esi`; egyezésnél semmi nem történik, a függvény 0-val tér vissza, `0x005e3bb2`). A célazonosító az `edi`: a `0x004ae4e0` által az ejtési sorhoz kitöltött rekord `+0x14` mezője (`0x005e3b27 mov edi,[esp+0x4c]`), és ezt kapja a `0x004b0190` (`0x005e3e83`) meg a köteges hozzáadó `0x006ca5a0` (`0x005e3ee8`). A korábbi „a célalbum azonosítója `+0x3c0`” megfogalmazás a két szerepet felcserélte; a viselkedés (azonos album: semmi; különben hozzáadás) ettől nem változik.
2. **A `0x0045ef50` nem a közönséges album tagságírója, hanem az arcalbumok kizárólagossági lépése (erős).** A `0x005e39a0` csak akkor hívja (`0x005e3efe`), ha a cél `0x004461a0`-ra hamis (`0x005e3eed test bl,bl; jne 0x5e3f47` átugorja). A `0x004461a0` (`0x004461de`-`0x004461e6`) igaz, ha a gyűjteményobjektum hiányzik, vagy a fejszava felső 24 bitje 1; ugyanezt a feltételt használja a menü- és tálcalistát építő `0x004b94a0` (`0x004b9597`), tehát ez a közönséges, felhasználói gyűjtemény (album, `]star`, `]screensaver`). Közönséges albumra ejtésnél ezért nincs más albumból törlés és nincs kizárólagos tagság: csak a `0x006ca5a0` köteges hozzáadása fut (a már tag képeket kihagyja).
3. **Az Add to Album almenü nem minden helyi menüben épül fel (erős).** A `0x0056c5a0` második paramétere a menü saját kontextusazonosítója (`ui-audit-context-menus.md:723-734`). Az almenü (`0x0056d24d`) a `0x70` (mappanézet képe), `0xa4` (albumnézet képe), `0x8a` (néző) és `0x13d` (Emberek-album képe) kontextusra épül fel (`0x0056d234`-`0x0056d247`, `0x0056d017`); az Emberek-ágon a `Move to People Album` almenü után mindig (`0x0056d227`, `0x0056d232`). Nem kapja a `0x8b` (tálca jobbklikk), `0x77` (album), `0xa6` (mappa), `0x127` és a `-1` (főmenü Picture) kontextus (`0x0056d247 jne 0x56d668`).

**A döntések:**

| Tétel | Döntés | Válasz | Bizonyíték | Fok |
|---|---|---|---|---|
| Közvetlen főmenü- vagy billentyűbelépés az Add to Album-hoz | (a) | **Nincs.** A főmenük leltárában (File, Edit, View, Folder, Picture, Create, Tools, Help: `picasa-menu-parancsok.csv`) és a gyorsbillentyű-erőforrásban (`shortcuts.xml:112-124`) nincs ilyen tétel. A Picture menüt a `0x0056e1c0` a `0x0056c5a0(this,-1,...)`-lel tölti (`0x0056f418`), de a `-1` kontextusnál az almenü nem épül fel. Az egyetlen főmenü- és billentyűbelépő a `New Album...` (Ctrl+N), és az nem meglévő albumhoz ad. | menüleltár, `shortcuts.xml`, `0x0056f418`, `0x0056d247` | erős |
| Engedélyezés: egy kép, több kép, videó, már albumtag kép (fotó- és albumnézet, Emberek-album) | (a) | **Mindig elérhető.** A `0x0056c5a0` elején a `-1`-től eltérő kontextusnál minden tételt pozíció szerint engedélyez (`0x0056c5cd`-`0x0056c5f4`, `0x400` jelzővel), a `0x9d8f` azonosítót csak a `SetMenuItemInfo` használja (`0x0056d272`), pozíció szerinti tiltás nincs a függvényben. A hozzáadó `0x00536a90` nem szűr típusra (videó is bekerül) és a már tag képet csendben kihagyja. Ez egyezik a PicasaPyval. | `0x0056c5b6`, `0x0056d272`, előző kör `0x00536a90` | erős |
| Néző helyi menü | (a), eltérés | A `0x8a` kontextus ugyanazt az almenüt kapja, mint a fotómenü: albumok, elválasztó, `Starred Photos`, `Screensaver`, elválasztó, `New Album...`. Albumok nélkül is legalább ez a három sor áll ott, tehát az almenü nem lehet üres. A PicasaPy nézőmenüje csak albumsorokat ad, és `menu.albums.length > 0` híján szürke (`ViewerContextMenu.qml:134-150`); a QML-komment szerint „album nélkül a Picasa is szürkén hagyja”, de ennek forrása a specben nincs, a bináris pedig ellentmond neki. Teendő: J1. | `0x0056d234`, `ui-audit-context-menus.md:727` | erős |
| Albumok sorrendje a menüben | (a), (c) | A menü és a bal oldali lista ugyanazt a rendezőt használja: `0x004b94a0` (`0x004b974a`) és a listaépítő `0x004b8ee0` (`0x004b916b`) is a `0x004baaa0` összefésülő rendezést hívja, amelynek összehasonlítója a `0x004a7890`: csoportbájt, névsor (kisbetűsítve, ASCII), majd a nézet rendezési módja (`+0xd8`, irány `+0x165`), végül névsor. PicasaPyban a menü és a hasáb ugyanazt a `controller.albums` listát kapja, tehát a kapcsolat azonos. Magának a bal hasáb sorrendjének paritása nem a #7012 hatóköre. **Nem blokkoló.** | `0x004a7890`, `0x004baaa0`, `0x004b94a0` | erős |
| Tálca: egy `Labels` sor aktiválása azonnal ír-e | (c) | A `thumbui/makealbum` kezelője, a `0x00577c30` a tálca képlistáját és a panel kijelölt sorát olvassa, majd megerősítés és további gomb nélkül ír meglévő albumnál (`0x004b0190`, `0x006ca5a0`, `0x0065b840`, `0x004abc70`, `0x00665180`); az új album sor a `0x00577ea0` párbeszédes ágra visz, más ablaknyitás nincs a törzsében. Az Add to gomb kezelője (`0x005fe130`) a `makealbum` parancsot csak akkor küldi közvetlenül, ha a panelmodell üres és album sincs (`0x005fe16f`-`0x005fe179` feltétel, `0x005fe24b` küldés); egyébként a listapanelt építi (`0x005fe2bc` `0x00664130`). Hogy melyik kód küldi a `makealbum` parancsot egy panelsor kiválasztásakor, nem dőlt el (a küldő hely a `0x005fe24b` kivételével nincs). Ez a felhasználónak nem látszik: a mért menü (job-259) sorlista, a sor hatása a mért job-257 szerint az OK után azonnali, külön megerősítő lépést egyik bináris út sem mutat, PicasaPy pedig a sor kiválasztásakor azonnal ír. **Nem blokkoló.** | `0x00577c30`, `0x005fe130`, job-257, job-259 | erős (az írás), feltételes (a sor és a parancs közti láncszem) |
| Tálca `Add to` gomb engedélyezési feltétele | (c) | A gomb nevére az egyetlen név szerinti `+0x20e` írás nullát ír (`0x00568948`, `0x009cd7e0`), tehát kijelölésfüggő tiltást nem találtam; a `+0x20e` a `0x00577c30`-ban a tálcacsomópontnál zárolásjelzőként szerepel (`0x00577c5e`). Üres tálcalistánál a `0x00577c30` 0-val kilép (`0x00577c9c`), hatás nincs. PicasaPy gombja üres tálcánál szürke (`TrayScratchPanel.qml`, `heldCount > 0`); legfeljebb ez a szürke állapot különbözhet, a művelet eredménye (nincs hatás) azonos. **Nem blokkoló.** | `0x00568948`, `0x00577c5e`, `0x00577c9c` | feltételes |
| Add to `New Album...`: párbeszéd, alapértékek, megjegyzett állapot | (a) | A `0xa09c` a `0x005cd90d`-nél `0x005e9890(this,0)`-ra megy (a `0xa0cc` ugyanott 1-et kap: új személy), majd `0x005e9bb0(this,1)` → `0x005eaab0` → `0x005ea770` → `0x006dc030`: **Album Properties párbeszéd**. Név: `IDS_DEFAULT_ALBUM_NAME` (Untitled), a `0x0055ce70` tölti. Dátum: a kijelölés ELSŐ képének dátuma (`0x005e9cd2 call 0x5c6460`), mínusz egy másodperc (`0x005ea792 fsub [0xcf50c8]`, az érték 1/86400 nap); ha a dátum nem olvasható, az őrérték 949998,0 (`0x00c7ccf8`) marad. Hely és leírás üres. Megjegyzett állapot nincs: a leíró minden hívásnál friss, a `0x0055ce70` és a `0x005ea770` nem olvas beállítást. OK után az új album frissül és megnyílik (`0x005e9e39 call 0x65b840`, `0x005e9e57` a fa `+0x44` hívása az új azonosítóval). PicasaPy: név egyezik, a dátum üres (`FileOpsDialogs.qml:100-104`), az új album megnyitása egyezik (#7076). Teendő: J1. | `0x005cd90d`, `0x005e9cb4`-`0x005e9cd2`, `0x005ea770`, `0x0055ce70` | erős |
| Húzás meglévő album sorára | (a) | Azonos forrás és cél: semmi. Közönséges albumra: `0x004b0190` majd `0x006ca5a0`, a már tagokat kihagyja, nincs kérdés, nincs kizárólagosság, nincs törlés a forrásból, a Ctrl nem számít (`0x005e3e04` a közönséges célnál mindig a hozzáadásra lép). Ha a gyűjtemény `+0x5c` vagy `+0x64` mezője nulla, -1-gyel tér vissza üzenet nélkül. Utána `0x004abc70` (módosított jelző) és `0x0065b840`. Típusszűrés nincs. PicasaPy ugyanezt adja (`AlbumsSection.qml:42-45`). **Nincs eltérés.** | `0x005e3b87`, `0x005e3e04`-`0x005e3ee8` | erős |
| Húzás a `newalbumprompt` helyőrző sorra (a 4-es típusú rekord, ez az üres lista sora) | (a), eltérés | A `0x005e39a0` a rekord `+0x30` mezőjét 4-gyel hasonlítja (`0x005e3a88`-`0x005e3a8f`), és `0x005e3aaf`-nál `0x005ea770(this, ledobott lista, 0, mai idő)`-t hív: **Album Properties párbeszéd** (album mód, mert a második argumentum 0: `0x005ea7d0 sete dl`), név Untitled, dátum a mai idő mínusz egy másodperc (`0x0098b6e0`, `0x005ea792`). OK után az album létrejön és a ledobott képek bekerülnek (`0x005ea420`), `0x005e3ac1` frissít, `0x005e3ade` az új albumot nyitja; Mégse: nincs változás. A `0x00765d30` ugyanezt a sort csak kattintáskor magyarázza egy üzenettel (`CAlbumList::newalbumprompt`). PicasaPy: párbeszéd nélkül, azonnal `Untitled` albumot készít (`FileOpsDialogs.qml:109-112`, a komment szerint „mérve”, de a `picasa-konyvtar-eszkoztar-viselkedes.md:97-100` helyesbítése ugyanezt az olvasatot a `0x005eb810` útra már visszavonta, és az ejtés útját a specben nem mérték). Teendő: J3. | `0x005e3a88`, `0x005e3aaf`, `0x005ea7d0`, `0x0098b6e0` | erős |
| Tagságíró és `.picasa.ini`: mely mappák, milyen sorrend, hibakód 9 (a korábbi két „Ghidra-kör kell”) | (a) | Az `AlbumSync` `0x00556ff0` bejegyzése a kép-azonosítókat mappánként csoportosítja, és mappánként a `PicasaIniManager` `+0x10` bejegyzését (`0x0052c350`, `0x005572a5`) hívja: a mappa útvonala + `.picasa.ini`, a belső névből (`]album:` után) a token, majd az `albums` kulcs írása a képek szakaszába. Ha a lista nem üres és a mappa ini-jében **nincs `[.album:token]` szakasz nem üres `name` kulccsal** (`0x0052cd90`), `0x0052c350` 9-et ad (`0x0052c475`). Erre az `AlbumSync` `0x00557cf0`-val leírót képez az album adataiból, a `+4` bejegyzéssel (`0x0052a810`) beírja a **szakaszt a mappa ini-jébe** (`name`, `token`, `description`, `location`, `date`), és újrahívja a `+0x10` bejegyzést (`0x005572df`-`0x00557310`). Minden más visszatérési értéket eldob, hibaüzenet nincs. **Következmény: meglévő albumhoz adásnál a célmappa ini-jébe az albumdefiníció is bekerül, ha ott hiányzik.** PicasaPy ezt csak új albumnál teszi (`createAlbum`, `test_album_write_controller.py:205-217`), meglévő albumhoz adásnál nem (`photo_ops_album_membership_mixin.py:35-50`, `addHeldToAlbum`: `tray_album_controller.py:253-257`). Teendő: J2. | `0x00556ff0`, `0x0052c350`, `0x0052cd90`, `0x0052a810` | erős (két egymásra utaló függvény és a kulcsnevek) |
| Mikor írja ki az eredeti az ini-t (az `AlbumSync` kiváltója, időzítés) | (c) | A tartós írás nem a `0x00536a90`-ban fut (az a memóriabeli listát módosítja és `0x004abc70`-nel jelez), hanem megfigyelőn át; a katalógus egy időzített sorkiürítője (`0x004a82d0`) legfeljebb 10 másodpercenként (`0x00cf3b28` = 10,0) dolgoz fel sorba állított módosításokat, és a speciális gyűjteményeknél ilyenkor írja a `#db3\saverlist.txt` és `starlist.txt` fájlt (`0x004a840f`, `0x004a843b`). Hogy az `AlbumSync` is ebből a sorból hívódik-e, feltételes. Felhasználó által látható hatás csak összeomlásnál vagy külső eszköz azonnali olvasásánál lenne; a végállapot (tartalom) fent eldőlt. PicasaPy azonnal ír, ami a biztonságosabb. **Nem blokkoló.** | `0x004a82d0`, `0x00cf3b28` | feltételes |
| `Starred Photos` sor választása már csillagos képen | (a) | **Hozzáad, nem fordít.** A `0x00536a90` végén a `]star` név (`0x00536efe`) csak a `thumbui/startoggle` kapcsoló frissítését (`0x005d27d0`) váltja ki, megfordító ág nincs benne; a már tag képet az általános ág kihagyja. A PicasaPy tálcamenüjének `toggleStarMany`-ja ettől eltér (megfordít). | `0x00536efe`, `0x00536f30` | erős |
| `Screensaver` sor hatása a fotómenüből (`]screensaver`) | (b) | A fotómenü útja a `0x00536a90`, a tálcáé a `0x00531a20` (`0x004d9aa0` + `#db3\saverlist.txt` írás + telepítő `0x00531ac0`). Hogy a fotómenüs út ugyanazt a fájlírást és telepítést kiváltja-e a fenti időzített sorkiürítőn át, nem dőlt el. Lásd a Zárási döntés egyetlen Ghidra-sorát. | `0x00531a20`, `0x004a82d0` | nyitott |
| Hozzáadás utáni bal fa, rács, kijelölés, fókusz | (c) | Az album sorát a `0x004af790` keresi meg és a `0x009d2c80(0)` újrarajzolja (darabszám), a főnézetet a `0x0065b840(this,0,0,1)` frissíti; navigáció az albumra nincs. A `0x00536a90` kijelölést csak olvas (`0x007166c0`, `0x00717140`: számolás és bejárás, módosítás nincs). Az újrarendezés pontos grafikai végállapota csak futásidejű méréssel olvasható le; eltérésre nincs bizonyíték, PicasaPy a kijelölést megtartja, ha a rekordsor nem változik. A jegyek „Nem szabad” listája: a kijelölés-megtartás nem változhat. **Nem blokkoló.** | `0x00536a90`, `0x0065b840` | erős (a kijelölés érintetlensége), feltételes (grafikai végállapot) |
| Visszavonás | (a) | **Nincs.** A `0x00536a90` hívásai között nincs visszavonás-regisztráció, és az eredeti Edit menü leltárában nincs albumműveleti visszavonás tétel (`picasa-menu-parancsok.csv`, `eMenuEdit`). PicasaPyban sincs. | `0x00536a90`, menüleltár | erős |
| Hiba és részleges végrehajtás | (a), (c) | A `0x00536a90` hibánál üzenet nélkül tér vissza; memóriahiba (`4`) esetén a már hozzáadott képek bent maradnak, visszagörgetés nincs. Az ini-írás hibáját az `AlbumSync` nem jelzi (a 9-esen kívül minden értéket eldob, `0x005572a7`). PicasaPy `albumWriteFailed` hibasávja többlet, adatot védő jelzés. **Nem blokkoló, nem törlendő.** | `0x00536a90`, `0x005572a7` | erős |
| Album adatbázis, contacts, SQLite index | (c) | A tartalom (`albums`, `[.album:]` szakasz) a fenti sorban eldőlt; a katalógus saját adatbázisfájljának szerkezete nem látszik a felhasználónak, az index PicasaPyban az ini-ből épül (a két termék között nincs közös fájl). **Nem blokkoló.** | `ini/` szerződés | erős |

### Zárási döntés

**A #7012 kutatási jegy lezárható.** Minden belépő, engedélyezési feltétel, tárolási lépés, hibaág és felületi hatás eldőlt (a), vagy kimondottan nem blokkoló (c). Egy kérdés maradt (b), de az nem a jegy lezárását gátolja, hanem a J1 fejlesztői jegy `Screensaver` sorának kiadását, és a J1 viszi tovább. **Blokkoló nincs.**

Ghidra-kör kell: 0x004a82d0 - az időzített sorkiürítő (legfeljebb 10 másodpercenként) mely sorba állított módosításból hívja a `0x004753b0`-at és írja a `#db3\saverlist.txt` fájlt, és a `0x00536a90` utáni `0x004abc70` jelző ide vezet-e; ebből dől el, hogy a fotómenü `Screensaver` sora (`]screensaver`) a tálcás ágtól (`0x00531a20`, `0x00531ac0`) eltérő hatású-e.

Ghidra-válasz (2026-11-17, második zárókör, utasításszintű vizsgálattal, lásd lent): a `0x004a82d0` a `ytList<TokenBackup>` sort üríti, a `0x004abc70` jelzője nem ehhez a sorhoz tartozik, és a kérdés nem érinti a felhasználó által látható PicasaPy-viselkedést. Döntés: (c), **nem blokkoló**.

A megmaradó fejlesztői jegytörzsek (mindegyik binárisból igazolt működésre épül, a „Nem szabad” sorok a már működő viselkedést védik):

**J1. Az Add to Album almenü tartalma és az új album párbeszéde.**

- Eredeti: a `0x0056c5a0` a fotómenü (`0x70`, `0xa4`, `0x13d`) és a néző (`0x8a`) almenüjét azonos sorrenddel építi: albumok, elválasztó (ha van album), `Starred Photos`, `Screensaver` (a két gyűjteményt a katalógus induláskor mindig regisztrálja, `0x004abe70`, ezért a gyakorlatban mindig megjelennek), elválasztó, `New Album...`. Az almenü mindig elérhető, albumok nélkül is. A `Starred Photos` hozzáad, nem fordít. A `New Album...` Album Properties párbeszédet nyit: név `Untitled` (magyarul `Névtelen`), dátum a kijelölés első képének dátuma mínusz egy másodperc, hely és leírás üres, megjegyzett állapot nincs; OK után az új album frissül és megnyílik. Fok: erős.
- Nálunk: a fotómenü almenüje csak albumokat és `New Album...` sort ad (`PhotoContextMenu.qml:167-192`); a néző almenüje csak albumsorokat ad, és album nélkül szürke (`ViewerContextMenu.qml:134-150`); az új album párbeszéd dátuma üres (`FileOpsDialogs.qml:100-104`); a tálcamenü `Starred Photos` sora megfordít (`toggleStarMany`).
- Teendő: (1) a néző almenüje megkapja a fotómenü teljes sorlistáját (`New Album...` is), és mindig elérhető; (2) a fotómenü és a néző almenüje megkapja a `Starred Photos` és `Screensaver` sort a fent leírt helyen; a `Starred Photos` a már csillagos képen nem fordít; (3) az Add to `New Album...` párbeszéd dátuma a kijelölés első képének dátuma mínusz egy másodperc (nincs dátum: üres). A `Screensaver` sor hatását a fenti egyetlen Ghidra-sor dönti el; addig a jegy nem adható ki (félkész nem megy ki).
- Kész, ha: a renderelt fotó- és néző-almenü az eredeti almenü képernyőképével összevetve egyezik (üres albumlistával és albumokkal is; a szürkítés kérdését a képernyőkép dönti el, a jegy nem törölheti azt magától); a `Starred Photos` kétszeri választása is csillagos képet ad; az új album párbeszéd dátuma teszttel ellenőrzött. Képernyőkép nélkül a jegy nem zárható.
- Nem szabad: a tálcamenü mért sorrendje (`Screensaver`, `Starred Photos`, albumok, `New Album...`, elválasztó nélkül) nem változhat; a meglévő albumsorok viselkedése és az új album megnyitása (#7076) nem változhat.

**J2. A célmappa `.picasa.ini`-jébe az albumdefiníció is kerüljön meglévő albumhoz adásnál.**

- Eredeti: a `0x00556ff0` mappánként hívja a `0x0052c350`-et; ha a mappa ini-jében nincs `[.album:token]` szakasz nem üres névvel, 9-et kap, `0x0052a810`-nel beírja a szakaszt (`name`, `token`, `description`, `location`, `date`), majd megismétli az `albums` írását. Fok: erős.
- Nálunk: `addRowsToAlbum` (`photo_ops_album_membership_mixin.py:35-50`) és `addHeldToAlbum` (`tray_album_controller.py:253-257`) meglévő albumnál csak az `albums=` sort írja; új albumnál a definíció minden érintett mappába kikerül (`createAlbum`).
- Teendő: mindkét út a mappánként módosított dokumentumban pótolja a hiányzó (vagy névtelen) `[.album:token]` szakaszt az album ismert adataival (név, dátum, hely, leírás), mielőtt a tagságot beírja; a meglévő, névvel ellátott szakaszt nem írja felül. A dátum alakja a mért `[.album:]` szakaszokat kövesse (`picasa-ini-format.md`).
- Kész, ha: teszt, amelyben az album csak az A mappa ini-jében van definiálva, és a B mappából adott kép hozzáadása után a B ini-jében is van `[.album:token]` ugyanazzal a névvel és dátummal, a képnél `albums=` tartalmazza a tokent; ismételt hozzáadás után a fájl bájtra változatlan; a már definiált mappa szakasza nem módosul; a tálcás és a menüs út egyaránt lefedett.
- Nem szabad: az `albums=` sorrendje (hozzáfűzés a végére), az idempotencia és a mappánkénti egyetlen ini-írás nem változhat.

**J3. Képek ejtése az üres albumlista helyőrző sorára: Album Properties párbeszéd.**

- Eredeti: az ejtés a 4-es típusú rekord sorára az Album Properties párbeszédet nyitja (név `Untitled`, dátum a mai idő mínusz egy másodperc, hely és leírás üres); OK után az album létrejön, a ledobott képek bekerülnek, és az új album nyílik meg; Mégse: nincs változás. Fok: erős (utasításszintű; húzásmérés nincs, a Colab-végrehajtó húzást nem tud: job-656, job-657).
- Nálunk: a `FileOpsDialogs.createAlbumFromDrop` párbeszéd nélkül, azonnal `Untitled` albumot készít (`FileOpsDialogs.qml:109-112`).
- Teendő: a helyőrző sorra ejtés a New Album... párbeszédet nyissa a ledobott sorokkal, mai dátum mínusz egy másodperc alapdátummal; OK után hozza létre az albumot és nyissa meg.
- Kész, ha: a QML-teszt a dialógust renderelve ellenőrzi (név, dátum), OK után az album, a tagság és az aktív album, Mégse után semmi változás.
- Nem szabad: a meglévő album sorára ejtés (hozzáadás), a #5121 célterület-elhelyezése és a menüs `New Album...` út nem változhat.

Nem blokkoló, külön nem jegyzett tételek: az albumsorrend a bal hasábbal egyező (a hasáb sorrendje külön paritási kérdés), a tálcagomb szürke állapota üres tálcánál, a hozzáadás utáni grafikai végállapot (futásidejű mérés, eltérésre nincs bizonyíték), az ini-írás időzítése, a PicasaPy hibasávja, a katalógus belső adatbázisa.

### Kiegészítés (2026-11-17, második zárókör): a "Nálunk" oszlop újraellenőrzése, két új felvétel és a megmaradt tételek

Módszer: a `Picasa3.exe` (3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`) utasításszintű visszafejtése (`capstone`, 32 bites x86), a bináris-index (`functions`, `xrefs`, `string_xrefs`, `rtti`) lekérdezése, a `referencia/kepernyo/` felvételeinek megnézése és a PicasaPy jelenlegi főágának olvasása (`grep`, a lent idézett sorszámokkal). Dekompilált veremváltozót (`unaff_*`, `local_*`) nem használtam: minden itt idézett állítás a függvény vagy a hívóhely utasításaiból, illetve a hívásgráfból jön, ezért korábbi következtetést sem kellett visszavonni. Futásidejű mérést ebben a körben nem végeztem. A korábbi bejegyzések szövege érintetlen; ahol ez a kiegészítés felülír valamit, kimondom. Fokok: megerősített (két független út), erős (egy út, egyértelmű utasítások), feltételes (következtetés).

**Új eredeti felvételek (korábban sehol nem hivatkozottak).**

- `referencia/kepernyo/2026-11-12-helyi-menu-add-to-album-job643.png`: eredeti Picasa 3.9, angol, két kijelölt kép, a könyvtárban csak a virtuális `Recently Updated` album. A kép helyi menüjének kinyitott `Add to Album` almenüje fentről lefelé: `Starred Photos`, `Screensaver`, vízszintes elválasztó, `New Album...`. Nincs vezető elválasztó, egy sor sem szürke, és a virtuális `Recently Updated` nem szerepel az albumok között.
- `referencia/kepernyo/2026-11-12-helyi-menu-new-album-job644.png`: a `New Album...` sor után megnyíló Album Properties ablak: a `Name` mező `Untitled` értékű és kijelölt, a `Date` `11/12/2026`, a zenei jelölőnégyzet kikapcsolt és a `Browse...` szürke, a `Place taken (optional)` és a `Description (optional)` üres, van `OK` és `Cancel` gomb. A felvétel neve szerint a mérés 2026-11-12-én készült, és a mappa és a képek dátuma is 2026. nov. 12. (a felvétel fejlécében és állapotsorában), ezért a felvétel a "mai nap" és az "első kép ideje mínusz egy másodperc" olvasatot nem választja szét, de a `0x005e9cd2` és `0x005ea792` alapú olvasatnak nem is mond ellent.

Fokozat: a nulla saját albumos almenüsorrend **megerősített** (felvétel és a `0x0056c5a0` építési sorrendje, két független út); az albumos sorok sorrendje és a néző menüje **erős** (csak bináris, felvétel nincs).

**Felülírt vagy pontosított korábbi állítások (a régi szöveg érintetlen).**

1. A J1 és a J2 kész, és a fő ágban van: a #7100 (almenü sorrend és új album dátum, fotómenü és néző) és a #7101 (albumdefiníció a célmappa ini-jébe) az 1.0.135 kiadás része. A fenti sorok és jegytörzsek erre vonatkozó "Nálunk" állításai (a fotómenü almenüje csak albumokat és `New Album...` sort ad, a néző almenüje album nélkül szürke, az új album dátuma üres, meglévő albumhoz adásnál nincs definíció) elavultak, az új állapot a lenti táblázatban áll.
2. A J3 (#7102) a zárókör idején még nem volt a fő ágban (a `fix/7102-codex` ágon várt); a PR #7106 2026-11-17-én beolvadt.
3. A tálca `New Album...` sorára a korábbi szöveg azt írja, hogy a párbeszédet "a tálca tartalmával" nyitja (`MainTrayBar.qml:82-85`). A kód a kijelölt sorokat adja át (`photoActionRows()`, `MainLibrarySelectionState.qml:72-80`), nem a tartott elemeket; a meglévő albumsorok viszont a tálca tartalmát írják (`addHeldToAlbum`, `tray_album_controller.py:240-266`). Hogy az eredeti tálcás sorai melyik képekre hatnak, a lenti (b) tétel dönti el.
4. A `0x004a82d0` kérdésére (lásd a régi egyetlen Ghidra-sort) a választ a lenti hetedik sor adja.

**A döntések (a jelenlegi forráson ellenőrizve):**

| Tétel | Döntés | Válasz | Bizonyíték | Fok |
|---|---|---|---|---|
| Fotómenü `Add to Album` almenüje, jelenlegi állapot | (a) | Sorrend: albumok (`Instantiator`), elválasztó csak ha van album, `Starred Photos`, `Screensaver`, elválasztó, `New Album...` (`PhotoContextMenu.qml:177-229`). Egyezik a job-643 felvétellel (nulla album) és a `0x0056c5a0` építési sorrendjével. A sorrendet és az elválasztót a #7100 QML-tesztje is ellenőrzi (`tests/app/qml_functional/test_hozzaadas_albumhoz_almenu_7100.py:158-222`). **Nincs eltérés.** | job-643, `0x0056c5a0` | megerősített (nulla album), erős (albumokkal) |
| Néző almenüje | (a) | Ugyanaz a sorlista (`ViewerContextMenu.qml:140-185`), `enabled` megkötés nincs, tehát album nélkül is elérhető, ahogy az eredeti `0x8a` kontextus. A három különleges sor a nézett képre hat (`PhotoViewerContextActions.qml:133-148`). **Nincs eltérés.** | `0x0056d234`, `ui-audit-context-menus.md:727` | erős |
| `Starred Photos` a fotó- és a néző menüben | (a) | Az `addStarMany` (`photo_ops_transform_mixin.py:109`) csak a még csillagtalan képekre ír, csillagot soha nem von le, ez egyezik az eredeti hozzáadó ággal (`0x00536a90`). A tálcamenü sora külön tétel (lásd a (b) sort). **Nincs eltérés.** | `0x00536efe`, `0x00536f30` | erős |
| Új album dátuma a fotó- és a néző menüben | (a) | Az `openAddToNewAlbum` az első kijelölt kép idejét adja mínusz egy másodperccel (`FileOpsDialogs.qml:94-102`, `ujmappa_datum.js:68-70`), idő nélküli képnél üres. A job-644 felvétel nem mond ellent. Idő nélküli képnél az eredeti őrértéke `949998,0` (`0x00c7ccf8`), a PicasaPy üres mezőt ad: ritka szélső eset, **nem blokkoló**. Egyébként **nincs eltérés.** | `0x005e9cd2`, `0x005ea792`, job-644 | erős |
| Albumdefiníció meglévő albumhoz adásnál (J2) | (a) | A fotómenü, a néző és a tálca albumsorai ugyanazt az `_album_membership_mutator`-t használják (`photo_ops_album_membership_mixin.py:30-91`, `tray_album_controller.py:240-266`): ha a célmappa ini-jében nincs `[.album:token]` szakasz, vagy a `name` üres, a szakasz a más mappákból ismert névvel, dátummal, hellyel és leírással kerül be; a névvel ellátott szakasz érintetlen marad, az `albums=` a végére fűz, és ismétlésnél nem változik (`ini/albums.py:65-80`). Tesztek: `tests/app/test_album_write_controller.py`, `tests/app/test_qml_tray_add_to_album_455.py`. **Nincs eltérés.** | `0x00556ff0`, `0x0052c350`, `0x0052a810` | erős |
| Húzás az üres albumlista helyőrző sorára (J3) | (a), eltérés marad | Az eredeti: a 4-es típusú rekordnál (`0x005e3a88`) a `0x005e3a95` `call 0x0098b6e0` az aktuális helyi időt állítja elő (időlekérdezés, majd a naptári mezők `+1900` és `+1` korrekcióval), a `0x005e3aaf` `0x005ea770`-et hív, ott `0x005ea792` `fsub` egy másodpercet von le, és `0x005ea7e0` a `0x006dc030` Album Properties párbeszédet nyitja. A zárókör idején a fő ágban a `FileOpsDialogs.qml:104-107` `createAlbumFromDrop` azonnal `Untitled` albumot hoz létre (`MainFolderPane.qml:130-133`). Teendő: J3 (#7102, nyitott). | `0x005e3a88`, `0x005e3aaf`, `0x005ea792`, `0x005ea7e0` | erős |
| `Screensaver` sor hatása a fotómenüből (a korábbi egyetlen Ghidra-sor, `0x004a82d0`) | (c) | A `0x004a82d0` nem tagságíró: a `CAlbumState` `+0x17c` mezőjén ülő `ytList<TokenBackup>` (RTTI `0x00c836f8`, konstruktor `0x004a1560`, `0x004a1613`) sorát üríti. A sorba fűző `0x004ba770` (0x18 bájtos csomópont, fej `+0x4c`, farok `+0x50`, darabszám `+0x48`) egyetlen hívója a `0x004a51f0`, a `CAlbumState` másodlagos vtáblájának (`0x00c836b4`) egyetlen bejegyzése: a `]screensaver` tokenhez 1-es (`0x004a52f1` `mov ebx, 1`, `0x004a5311`), a `]star` tokenhez 0-s fajtát rendel (`0x004a5345` `xor ebx, ebx`), és a `+0x134` mezőn át fűz (a másodlagos alap `+0x48` eltolásával ez a `+0x17c`). A `0x004a82d0` pontosan e két fajtára ír: az 1-esre `saverlist.txt`-t (`0x004a83f9`-`0x004a840f`), a 0-ra `starlist.txt`-t (`0x004a8425`-`0x004a843b`), fajtánként legfeljebb egyszer ürítésenként. Csak akkor fut, ha az utolsó ürítés óta legalább 10 másodperc telt el (`0x004a82ef` `fcomp [0xcf3b28]`, `0x004a82f7`-`0x004a82fa`: a küszöb alatt kilép), és a `0x004a8480` hívja elsőként (a `CAlbumState` főtáblájának utolsó bejegyzése, `0x00c8368c`). A `0x004abc70` jelzője nem ehhez a sorhoz tartozik: a `+0xf0` zár alatt a `+0x138` állapottábla elemét állítja (ugrótábla `0x004abd3c`: `0` és `3` és `4` a `3`-ra, `1` és `2` az `1`-re). A hiányzó láncszem: ki hívja a `0x004a51f0`-et egy gyűjtemény módosítása után (vtábla-hívás, az index nem látja; a `0x00536a90` és a `0x006ca5a0` hívásai között nincs). Felhasználónak látható hatása a PicasaPyban nincs: a képernyővédő forrásai a saját beállításban élnek, a program `saverlist.txt`-t nem ír (a `starlist.txt`-t csak az importáló olvassa, `pmpimport/importer.py:422`), az eredeti fájl átvétele külön, már rögzített kérdés (`picasa-menu-parancsok-viselkedes.md:1957-1961`). A fotómenü `Screensaver` sora ugyanazt a PicasaPy-műveletet kapja, mint a tálcás. **Nem blokkoló.** Ha a fájlírás pontos kiváltója valaha kell (például a `saverlist.txt` átvételéhez), a célpont a `0x004a51f0` vtábla-hívóhelye. | `0x004ba770`, `0x004a51f0`, `0x004a82d0`, `0x004a8480`, `0x004a1560`, `0x004abc70` | erős (a sor és az ürítő), feltételes (a kiváltó hívás) |
| `Screensaver` sor megerősítő ablaka a fotó- és a néző menüben | (a), eltérés | Az eredeti: a sor `0xbb80 + n` parancsa a `0x005cb990` diszpécserből a `0x00536a90(this, 0)`-ra fut, ugyanarra, mint bármely album. Ebben és a két szintnyi hívottjában nincs megerősítő vagy üzenetablak (a `0x009bac20` és a `MessageBoxA/W`, `DialogBox*` importok hívása hiányzik), az `addtosaver::warning` sztring egyetlen hivatkozója a `0x00531900` (a Létrehozás menü `Add to Screensaver...` kezelője), a `0x009bac20` egyetlen hívója a `0x0053xxxx` tartományban ugyanez. Nálunk: a `requestAddToScreensaver` (`MainLibrarySelectionState.qml:173-180`) albumnézetben megerősítést kér (`MainWindowCommands.qml:670-688`, "Are you sure you want to add all of the selected album's images?"), és ezt hívja a fotómenü (`MainPhotoContextMenu.qml:161`) és a néző (`PhotoViewerContextActions.qml:138-142`) `Screensaver` sora is; a kérdés az egész albumról szól, miközben csak a kijelölt képek kerülnek be. Teendő: J4. | `0x00536a90`, `0x00531900`, `0x009bac20` | erős |
| Tálca `New Album...` sor alapdátuma | (a), eltérés | Az eredeti kezelő, a `0x00577ea0` az Album Properties alapdátumául az aktuális helyi időt adja (`0x00577ee5` `call 0x0098b6e0`, `0x00577f07` `call 0x0055ce70`), az első kép idejét kérő hívás (`0x005c6460`) és az egy másodperces levonás nélkül; a párbeszédet a `0x00577f1d` `0x006dc030` nyitja. Nálunk: a sor üres dátummal nyit (`MainTrayBar.qml:82-85`, `FileOpsDialogs.qml:112-123`: `isoDate \|\| ""`), tehát a mentett `date=` is üres. A `[.album:]` szakasz `date` kulcsát a job-257 mérés rögzíti (`picasa-keptalca.md:1494`). Teendő: J4. | `0x00577ea0`, `0x0098b6e0` | erős |
| Tálca `Add to` menü: `Starred Photos` és `Screensaver` sor hatása, és a három különleges sor célpontja | (b) | Két olvasat van, a meglévő bizonyíték nem választ köztük. (A) A sorok a `Labels` lista közönséges gyűjteménysorai, és a kattintás a `thumbui/makealbum` kezelőre, a `0x00577c30`-ra fut: ennek közvetlen hívásai között nincs `]star`-ág, csillagkapcsoló vagy telepítő hívás, és két szintig megerősítő ablak sincs; a hozzáadás a `0x004b0190` és a `0x006ca5a0` útján megy (a tagot kihagyja). Ekkor a `Starred Photos` hozzáad, a `Screensaver` kérdés nélkül ad, és mindhárom különleges sor a tálca listájára hat. (B) A `picasa-keptalca.md:1492` a két sort a külön `action/screensaver` (`0x00531900`, megerősítéssel és telepítővel) és `thumbui/startoggle` (`0x005e81e0`) csomópontra köti; ekkor a `Starred Photos` megfordíthat, a `Screensaver` albumnézetben kérdez. A mért sorrend (`Screensaver`, `Starred Photos`, `Untitled`, `New Album...`) mindkét olvasattal összefér, mert ábécé szerint is így áll. A job-256 mérés csak a csillagtalan képet fedi le. A PicasaPy ma a (B) olvasat szerint viselkedik (`toggleStarMany`: `MainTrayBar.qml:78-81`, megerősítés albumnézetben, kijelölt sorok). **A döntő mérés egyetlen Colab-feladat** az eredeti Picasán: a tálcában két kép van tartva (az egyik már csillagozott), a rácson egy harmadik kép van kijelölve, a könyvtárban van egy `Aaa` nevű saját album is; `Add to` > `Starred Photos`, majd `Add to` > `Screensaver` albumnézetben. Mindegyik után képernyőkép, a bal sáv darabszámai és az érintett képek `.picasa.ini`-szakasza. Ebből dől el: hozzáad vagy megfordít a csillag, kér-e megerősítést a `Screensaver`, a tálca vagy a kijelölés a célpont, és hogy az `Aaa` album a `Screensaver` fölé kerül-e a menüben ((A) olvasat). A PicasaPy ma működő viselkedését a mérés előtt nem szabad változtatni. | `0x00577c30`, `picasa-keptalca.md:1492`, job-256 | feltételes |
| Értesítősáv a `Screensaver` hozzáadás után | (c) | A PicasaPy "Added %1 pictures to Screensaver." sávot mutat (`MainLibrarySelectionState.qml:167-171`), az eredeti menüs útja (`0x00536a90`) nem jelez vissza. Adatot nem érint, nem rontja a műveletet, a Létrehozás menü útján is ez a visszajelzés áll. **Nem blokkoló**, a J4 nem törli. | `0x00536a90` | erős |
| Húzás a bal lista `Starred Photos` sorára | (c) | A PicasaPy-ban a csillagozott soron nincs `DropArea` (az `AlbumsSection.qml` ejtési területe az albumdelegáltban van), az eredeti viselkedését nem vizsgáltam: a `0x005e39a0` a `0x004461a0`-ra igaz célt közönséges gyűjteménynek veszi, de hogy a lista csillagozott sora ejtési cél-e, nem dőlt el. Felvétel nem készíthető (a Colab-végrehajtó húzásra nem képes, job-656 és job-657). Nem az Add to alapfolyamat, **nem blokkoló**; ha egyszer kell, a `0x005e39a0` rekordtípus-ágaiból olvasható ki. | `0x005e39a0` | feltételes |

### Zárási döntés (második zárókör, 2026-11-17)

**A #7012 kutatási jegy lezárható.** Blokkoló nincs. Minden korábbi "NINCS MEG" és "Ghidra-kör kell:" tétel eldőlt (a), nem blokkoló (c), vagy egyetlen megnevezett mérésre fut (b). A `0x004a82d0` kérdés (c) lett, a két új felvétel (job-643, job-644) a nulla albumos almenüt megerősíti.

Az egyetlen nyitott tétel a (b) mérés (tálca `Add to` menü, `Starred Photos` és `Screensaver` sor, célpont). Ezt a hívó önálló mérési jegybe tegye (a Colab-végrehajtó futtatja, leírása a fenti táblázatban); az eredménye legfeljebb egy új fejlesztői jegyet (J5) hoz, a J3 és a J4 kiadását nem akadályozza, mert azok a tálca `Starred Photos` és `Screensaver` sorához nem nyúlnak. A jegy tehát nem vár semmire, ami rajtunk kívül áll.

A megmaradó fejlesztői jegytörzsek (mindegyik binárisból igazolt működésre épül):

- **J1 (#7100): kész, a fő ágban (1.0.135).** Nincs teendő. Utómunka a jegyen: a renderelt fotó- és néző-almenü képi összevetése a job-643 felvétellel (nulla album); az albumos sorrend csak a binárisra támaszkodik. Ebben a körben felületi renderelést nem futtattam, ezért az összevetés nincs elvégezve.
- **J2 (#7101): kész, a fő ágban (1.0.135).** Nincs teendő.
- **J3 (#7102): kész, a fő ágban (a PR #7106 2026-11-17-én beolvadt).** A lenti szöveg a beolvadás előtti állapotot írja le. Eredeti: a helyőrző sorra ejtés az Album Properties párbeszédet nyitja (név `Untitled`, dátum az aktuális idő mínusz egy másodperc, hely és leírás üres), OK után az album létrejön, a ledobott képek bekerülnek, és az új album nyílik meg; Mégse: nincs változás (`0x005e3a88`, `0x005e3aaf`, `0x005ea792`, `0x005ea7e0`; erős). Nálunk: `FileOpsDialogs.qml:104-107` párbeszéd nélkül, azonnal `Untitled` albumot készít; a `fix/7102-codex` ág ezt módosítja, de a fő ágban még nincs. Teendő: a helyőrző sorra ejtés a párbeszédet nyissa a ledobott sorokkal. Kész, ha: a QML-teszt a párbeszédet renderelve ellenőrzi (név, dátum), OK után az album, a tagság és az aktív album megvan, Mégse után semmi nem változik. Nem szabad: a meglévő album sorára ejtés (hozzáadás), a #5121 célterület-elhelyezése és a menüs `New Album...` út nem változhat.
- **J4 (#7131): a fotó- és a néző-almenü `Screensaver` sora megerősítés nélkül ad, és a tálca `New Album...` sora a mai dátumot ajánlja.** Eredeti: (1) az almenü `Screensaver` sora a `0x00536a90(this, 0)`-ra fut, ebben és két szintnyi hívottjában nincs megerősítő vagy üzenetablak, az `addtosaver::warning` egyetlen hivatkozója a `0x00531900`; (2) a tálca `New Album...` sorának kezelője (`0x00577ea0`) az Album Properties dátumát az aktuális helyi időre állítja, az első kép ideje és a másodperc levonása nélkül. Fok: erős. Nálunk: (1) a `requestAddToScreensaver` albumnézetben megerősítést kér (`MainLibrarySelectionState.qml:173-180`, `MainWindowCommands.qml:670-688`), és ezt hívja a fotómenü (`MainPhotoContextMenu.qml:161`) és a néző (`PhotoViewerContextActions.qml:138-142`) sora; (2) a tálca `New Album...` sora üres dátummal nyit (`MainTrayBar.qml:82-85`, `FileOpsDialogs.qml:112-123`). Teendő: (1) a fotómenü és a néző `Screensaver` sora a kijelölt (nézett) képeket kérdés nélkül adja a képernyővédőhöz; a Létrehozás menü `Add to Screensaver...` útja (`MainMenuBar.qml:184`) megtartja a megerősítést; a tálca sorát ez a jegy nem érinti, azt a (b) mérés dönti el. (2) A tálca `New Album...` sora az Album Properties dátumát az aktuális helyi dátumra állítja; a fotómenüs út (első kép ideje mínusz egy másodperc) nem változik. Kész, ha: QML-teszt albumnézetben, hogy a fotómenü és a néző `Screensaver` sora után nincs megerősítő ablak, és a képek bekerülnek a képernyővédő forrásai közé; a Létrehozás menü útja albumnézetben megerősítést kér; a tálcából nyitott `New Album...` párbeszéd dátuma a mai nap, és OK után az ini `date=` kulcsa ugyanez; a fotómenüs `New Album...` dátuma változatlan. Nem szabad: a tálcamenü mért sorrendje, a meglévő albumsorok viselkedése, a #7100 almenü-sorrendje, a Létrehozás menü megerősítése és a hozzáadás utáni értesítősáv nem változhat.

Nem blokkoló, külön nem jegyzett tételek (ebben a körben eldöntve): a `Screensaver` fájlírásának pontos kiváltója (a PicasaPy nem ír `saverlist.txt`-t), az értesítősáv a `Screensaver` hozzáadás után, az idő nélküli kép őrértéke az Add to új album párbeszédben, a bal lista `Starred Photos` sorára ejtés, valamint a korábban már nem blokkolónak jelölt tételek (albumsorrend, tálcagomb szürke állapota, hozzáadás utáni grafikai végállapot, az ini-írás időzítése, hibasáv, belső adatbázis).


### #7235-kiegészítés (2026-11-18): AlbumNotification, albumíró és képernyővédő-sor

#### #481 - AlbumNotificationManager / AlbumSync

A 0x00c7f540 AlbumNotificationManager::vftable második bejegyzése 0x004d3080; a 0x004d3080 dekompiláció (2026-11-18-koteg-466-495.txt:3116-3170) zárolás alatt másolja az értesítési adatokat, majd 0x004d3660-at hív. A 0x00c7f580 AlbumSync::vftable második bejegyzése 0x00556ff0 (+0x8). A korábbi 0x00556ff0 kimenet (2026-11-16-koteg-438-465.txt:1537-1694) album-metaadat-listát jár be és callbackeket futtat, de nem bizonyítja a hívás szálát vagy időzítését. A 0x00556920 xrefjei (0x004039f0, 0x00576a20) a sorba tétel környezetét adják, nem a végrehajtási időpontot. Nyitott következő címek: 0x004d3010, 0x004d31c0, 0x004d3150, 0x004d3260, 0x00556920 hívói, valamint a 0x00556ff0 hívásának timer-/kilépési útja. A jegyszöveg e pont után csonka (0x00…), ezért a hiányzó további hívólistát nem pótolom.

#### #482 - album-INI író 0x0052a810

A 0x0052a810 dekompiláció (2026-11-18-koteg-466-495.txt:3171-3367) új [.album:token] szakaszban ebben a sorrendben ír: name, token, description, location, date, majd a dinamikus mezőpárokat. A kulcsnevek PE-adatainak olvasása (0x00c7e8d0, 0x00c7e8d8, 0x00c7e8f8 és a literálok) a hívási sorrendtől külön ellenőrzi a megnevezést. A 0x0052b220 a PicasaIniManager::vftable +0xc slotja, és 4245 bájtos fájlrészt kezel, de e köteg nem tartalmazza a törzsét vagy hívóját. A 0x005578e0 a 0x00556a60 és 0x00556ff0 útból is hívódik; a mappalista forrása és sorrendje nem következik a hívásból. A 0x0052cc80/0x0052ca50 tokenútjának hívója (0x0052c350) szintén külön feloldandó. A meglévő 0x0052c350 dekompiláció már megadja a két segéd hívási feltételeit; nyitva marad a 0x0052b220 (+0xc slot) hívója/szerepe, a 0x005578e0 mappalista-forrása/sorrendje és a két tokensegéd közvetlen transzformációja. A feladat csonka vége a token kivételének/hozzáadásának pontos műveletét nem tartalmazza.

**Eredeti / PicasaPy / teendő - új album-INI kulcssorrend.**

| Eredeti (bináris 0x0052a810) | PicasaPy (fájl:sor) | Teendő |
|---|---|---|
| Új [.album:token] szakasz alapkészlete és sorrendje: name, token, description, location, date; ezután a dinamikus kulcspárok (0x0052a810, 2026-11-18-koteg-466-495.txt:3171-3367). | A `createAlbumWithProperties` először az `ensure_album`-ot hívja, amely token, majd name sorrendben fűz (ini/albums.py:218-238); utána a `with_album_fields` name, date, location, description sorrendben dolgozik (ini/albums.py:166-214; `photo_ops_album_membership_mixin.py:260-275`). Az új szakasz várható sorrendje ezért token, name, date, location, description. | Új album létrehozásakor a szakasz kulcsait az eredeti sorrendben írjuk: name, token, description, location, date. A meglévő szakaszok és más kulcsok round-trip sorrendjét nem változtatjuk. |

**Kész, ha:** egy új, kitöltött album után a .picasa.ini [.album:token] szakaszának első öt mezője pontosan name, token, description, location, date sorrendben jelenik meg, az értékek változatlanok; az üres mezők/zenekulcsok viselkedését ez a sor nem módosítja; meglévő album tulajdonságainak mentése és más szakaszok sorrendje változatlan.

#### #483 - időzített screensaver-sor 0x004a82d0

A 0x004a82d0 (2026-11-18-koteg-466-495.txt:3368-3477) az eltelt időt a DAT_00cf3b28 értékével veti össze. A PE-adat 0x00cf3b28 négy bájtja 00 00 20 41, azaz little-endian IEEE-754 10.0; ez a 10 másodperces küszöböt a dekompilációtól külön igazolja. Sorkiürítéskor a rekord 5. mezőjének 1 értéke a 0x004753b0-hoz és a #db3\\saverlist.txt ]screensaver bejegyzéséhez vezet; a 0 érték a DAT_00c811d4 karakterláncot írja. A korábbi #7012-kiegészítés szerint a queue a CAlbumState +0x17c mezőjű ytList<TokenBackup>; a 0x004a51f0 fűz bele, 1-es típussal a ]screensaverhez, 0-s típussal a ]starhoz, és a 0x004a82d0 üríti.

A 0x00536a90 utáni 0x004abc70 a +0x138 állapottáblát állítja, nem a TokenBackup-sort; ezért a kérdésben felvetett jelző nem vezet a 0x004a82d0 sorához. A 0x004a82d0 közvetlen hívója 0x004a8480. A még nyitott láncszem a 0x004a51f0 vtable-hívója és az, hogy a photo-menu hozzáadása mikor vált ki ilyen értesítést. A fotómenü ]screensaver sora a 0x0056c5a0 album-/fotómenü útján jelenik meg; a tálca 0x00531a20 ága külön írási út (lásd a picasa-menu-parancsok-viselkedes.md:35.3 szakaszát). A fotómenüben hiányzó Screensaver sort a #7012 meglévő fejlesztői jegytörzse kezeli. A saverlist.txt írási út ehhez nem ad külön, felhasználó által látható eltérést, ezért nem nyitok új fejlesztési tételt. Következő cél: a 0x004a51f0 vtable-hívóhelye; a 0x004abc70 már nem kérendő újra.

## #7028: A képek másolásának és beillesztésének teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
A PicasaPy állításait a jelenlegi forrásból ellenőriztem. A meglevő Ghidra-
kimeneteket célzott diszasszemblálással, a Copy/Cut/Paste útját egy friss,
kontextus nélküli, független újralevezetéssel ellenőriztem.

### Következtetés

A Picasa könyvtárnézeti Copy/Cut belső kijelöléslistát, forrásazonosítót és műveleti módot tárol; OneUp nézetben a Copy a renderelt képet teszi a rendszer-vágólapra `CF_BITMAP` formában. A Paste útból elérhető a Copy/Move megerősítő párbeszéd, amikor a kijelölt cél egy közönséges mappa, és eltér a forrásmappától; a `0x00579220` viszont csak a cél nélküli hibaág része. A PicasaPy OneUp képmásolása már megvan, de a fájllistás Paste, a célalbum kezelése, a kivágás jelzése és a köteg-hiba folytatása eltér; az eredeti dinamikus engedélyezését és a fájl/adatbázis/rács végállapotát egyetlen kontrollált mérési körnek kell eldöntenie.

### Bizonyítottsági fok

**Feltételes.** A fő belépési és hívási utat két külön bizonyítékút támasztja alá: a hívók utasításszintű olvasata, valamint a függvényhivatkozások, a Ghidra-kimenet és a párbeszéd erőforrás-sztringjeinek útja. A friss, kontextus nélküli újralevezetés megismételhetőségi ellenőrzés, nem külön bináris bizonyíték. A `.picasa.ini` és mentett eredetik másolási útja a meglévő Ghidra-anyagban látszik. Az egyes menüpontok dinamikus tiltása, az azonos mappás ág látható végállapota, a célalbum adatbázis-hatása és a hiba utáni teljes UI/DB3 állapot futásidejű próbája hiányzik.

### Bizonyítékjegyzék

| Állítás | Forrás | Minősítés |
|---|---|---|
| Copy/Cut: `0x005fe9f0` megjegyzi a `[esi+0x318c]` forrásazonosítót, a `0x00577ba0` az elemazonosító-listát állítja össze, a `[esi+0x31a4]` a módot tárolja; a Paste külön fogyasztója ugyanezt a módmezőt olvassa. | `bináris (0x005fe9f0, 0x00577ba0, 0x005feab0, 0x007166c0)` | megerősített: Copy/Cut íróút és Paste külön olvasóút |
| OneUp Copy: `0x0069b000` → `0x00a706f0`; `0x00a70776` `CF_BITMAP` formátummal hívja a `SetClipboardData` függvényt. | `bináris (0x0069b000, 0x00a706f0, 0x00a70776)` | feltételes: a bináris közvetlen olvasata igazolja; a második bizonyítékút nincs dokumentálva |
| Paste mód: `0x005feab0` a `[esi+0x31a4]` jelző ellentettjét adja a `0x005791d0`-nak. A Paste a `0x00784100`-ba a forrásazonosítót és a kijelöléslistát is átadja. | `bináris (0x005feab0, 0x005791d0, 0x00784100)` | megerősített: a hívó közvetlen disassemblyje és Ghidra |
| Copy/Move kérdés: a Paste hívója a `0x005791d0`; a `0x00784100` csak eltérő forrás/cél és közönséges mappacél esetén hívja a `0x00535020`-at. A wrapper `param_5=0` értékkel hívja a `0x005350b0`-at. | `bináris (0x005791d0, 0x00784100, 0x00535020, 0x005350b0)` | megerősített: hívói disassembly és külön függvényhivatkozás/szövegadat út egyezik |
| Ütközési párbeszéd: `Confirm Copy` / `Confirm Move`, majd névütközésnél `Rename Duplicates`, `Skip Duplicates`, `Cancel`. | `bináris (0x005350b0)`; független adatutat ad a `string_xrefs.csv`: a négy szöveg `0x00c89ea4`, `0x00c89ed4`, `0x00c89efc`, `0x00c89f2c` címen ehhez a függvényhez mutat | megerősített a párbeszéd és választék; az előálló névséma nem |
| Nincs cél: a `0x005791d0` az `IDS_NEED_SELECTED_ALBUM` üzenetet hívja, majd `0xf4242` értékkel tér vissza; a `0x00579220` e függvény kódja, nem önálló függvény. | `bináris (0x005791fb, 0x00579217, 0x00579220)` | feltételes: közvetlen disassemblyből |
| `+0x5d`: egybájtos kijelölési állapot, nem kivágásjelző és nem átlátszósági adat. A `0x00716f40` állítja, a `0x007166c0` és más kódutak a kijelölés összegyűjtésére olvassák. | `bináris (0x00716f40, 0x007166c0)`; másik leírás: `picasa-eger-es-kijeloles.md:11.3` | megerősített |
| Ctrl+X mérési nyom: a Selection Tray jelvény 96 képpontnyi eltérést mutatott; Ctrl+C-nél 0 képpont. A rács-bélyegképek halványítása nem szerepel ebben a megfigyelésben. | `mérés (picasa-gyorsbillentyuk.md:2720-2721; picasa-colab-jobs #456, kb-2)` | feltételes: a napló a tálcajelvényt nevezi meg, a nyers kép nem került elő |
| A Picasa binárisában megvan az `imagedata` oszlopregisztere; a mért db3-készletben PMP-oszlopfájlok és külön indexfájlok vannak. Ez nem bizonyítja a Paste utáni tartós rekordfrissítést. | `bináris (0x004127c0)`; `mérés (valódi Picasa 3.9 db3-készlet, pmp-database.md:197-205)` | katalógusszerkezet igazolt; a Paste utáni rekord és frissítési idő nincs meg |
| PicasaPy OneUp Copy a `rendered_image` képet adja a vágólapra; Paste fájllistát és `copy`/`cut` műveletjelzőt olvas. | `src/picasapy/app/qml/PicasaPy/MainLibrarySelectionState.qml:120-142`; `src/picasapy/app/edit_controller_clipboard_mixin.py:32-58`; `src/picasapy/app/fileops_controller_clipboard_mixin.py:16-72,98-121` | a forráskód megerősíti |
| PicasaPy másolás után a célmappát célzottan újraszinkronizálja; a háttérfigyelő önmagában nem bizonyíték a frissítésre. | `src/picasapy/app/fileops_controller_move_mixin.py:267-281`; `src/picasapy/app/application_services.py:24-61,110-113` | a forráskód megerősíti |

| Belépési pont | Eredeti Picasa (bináris cím) | Engedélyezési feltétel (Eredeti) | PicasaPy (fájl:sor) | Paritás |
|---|---|---|---|---|
| Szerkesztés menü Copy (`&Copy`) | `0x005cb990` -> `0x005fe9f0(0)`, parancskód `0x9d3b` (40251) | Könyvtárban legalább 1 kijelölt elem (`[esi + 0xeac] > 0`). Üres kijelölésnél inaktív / no-op (`ret 4`). Szerkesztőben az aktuális kép. | `PicasaEditMenu.qml:53-58` | Egyezik (`bar.hasSelection`) |
| Gyorsbillentyű Ctrl+C | Accelerator tábla (`0x007823f0`), parancskód `0x9d3b` | Megegyezik a Szerkesztés menü Copy feltételével. | `MainKeyboardShortcuts.qml:244-255` | Egyezik (`shortcutCopyFiles`) |
| Szerkesztés menü Cut (`Cu&t`) | `0x005cb990` -> `0x005fe9f0(1)`, parancskód `0x9d39` (40249) | Könyvtárban legalább 1 kijelölt elem. A `0x00716f40`-et `0` jelzővel hívja a `[this+0xea4]` nézetre (kijelölés törlése); a rácson halványított jelölés a kimenetben nincs (Ghidra 2026-11-16: a `+0x5d` a kijelölés jelzője). Szerkesztőben inaktív. | `PicasaEditMenu.qml:46-51` | Halványítási eltérés nem igazolt: az eredetiben halványított jelölés nem látszik. |
| Gyorsbillentyű Ctrl+X | Accelerator tábla (`0x007823f0`), parancskód `0x9d39` | Megegyezik a Szerkesztés menü Cut feltételével. | `MainKeyboardShortcuts.qml:256-267` | Egyezik a hívásban, hiányzik a vizuális jelölés. |
| Bélyegkép helyi menü | `0x00730790` | Nincs sima Copy / Cut tétel a helyi menüben (csak `Copy Path`, `Copy Effects`, `Move to New Folder...`). | `PhotoContextMenu.qml` | Egyezik (nincs közvetlen Copy/Cut a helyi menüben). |
| Szerkesztés menü Paste (`&Paste`) | `0x005cb990` -> `0x005feab0()`, parancskód `0x9d3c` (40252) | Belső vágólap nem üres VAGY külső vágólapon képadat/fájllista van. Szerkesztőben inaktív. Cél hiányában dialógus (`IDS_NEED_SELECTED_ALBUM`). | `PicasaEditMenu.qml:60-67` | Eltérés: cél hiányában a PicasaPy hibasávot mutat, vagy csendben nem tesz semmit. |
| Gyorsbillentyű Ctrl+V | Accelerator tábla (`0x007823f0`), parancskód `0x9d3c` | Megegyezik a Szerkesztés menü Paste feltételével. | `MainKeyboardShortcuts.qml:268-279` | Egyezik |
| Copy To Folder | Nincs ilyen önálló parancs | Az eredetiben külön Export (`0x9d3e`), Move Folder (`0x9df4`) és Move to New Folder (`0x9d68`) létezik. | Nincs önálló parancs | Egyezik |
| Média típusok | Kép és videó támogatott | Legalább 1 érvényes médiaelem kijelölve. | Kép és videó támogatott | Egyezik |

### Belépési pontok, feltételek

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Szerkesztés menü Copy (`0x9d3b`) és Ctrl+C: `0x005cb990` / `0x005e63f5` → `0x005fe9f0`. Könyvtárban a lista belső azonosítókat gyűjt; OneUp ágon a renderelt kép másolása hívódik. Üres lista után nincs beilleszthető tétel. A menü dinamikus tiltási feltétele nincs teljesen feloldva. | `PicasaEditMenu.qml:53-58`; `MainKeyboardShortcuts.qml:250-255`; OneUp út `MainLibrarySelectionState.qml:120-142` | Az egyes/többes, videó és nézőbeli menüengedélyezést a mérési kör rögzítse. A OneUp képadat-másolása már megvalósult, nincs fejlesztési teendő. |
| Szerkesztés menü Cut (`0x9d39`) és Ctrl+X: ugyanaz a `0x005fe9f0`, a hívó 0/1 módot ad át. A `+0x5d` kijelölési bájt átállhat; a bizonyíték nem jelent képhalványítást. | `PicasaEditMenu.qml:46-51`; `MainKeyboardShortcuts.qml:256-267`; `fileops_controller_clipboard_mixin.py:75-82` | Eltérés: PicasaPy a `cut` módot a külső vágólap-adatba írja, de nem tart fenn látható kivágási állapotot. Az eredeti látható Selection Tray jelvényét mérés rögzíti, rácshalványítást nem. Lásd a 4. fejlesztési jegyjavaslatot. |
| Kép-rács helyi menüje: a fénykép-helyi menü teljes listáján nincs szabványos Copy/Cut/Paste. Az `Address` szövegmező helyi menüje külön névtér, szabványos `WM_CUT/COPY/PASTE` üzenetekkel (`0x007331e0`, `0x00851a8f-0x00851ad2`). | `PhotoContextMenu.qml:478-482` (Copy Full Path); szövegmező menüje nem képparancs | Egyezik a képek helyi menüjénél. Ne keverjük az `Address` mező szövegműveleteivel. |
| Paste (`0x9d3c`): `0x005feab0` → `0x005791d0`. Ha nincs célmappa/album, az `IDS_NEED_SELECTED_ALBUM` üzenet hívódik. Szerkesztő-előnézetben a könyvtári Paste ág nem fut. A dinamikus menüengedélyezés teljes állapottáblája nyitott. | `PicasaEditMenu.qml:60-67`; `MainKeyboardShortcuts.qml:268-279`; `MainWindowCommands.qml:370-376` | Eltérés: cél nélkül nálunk a „There are no files on the clipboard to paste.” felirat jelenik meg, ha a vágólap amúgy nem üres. Lásd a 2. jegyjavaslatot. |
| Copy To Folder: a helyi parancs neve nem igazolt. A felhasználó által látható, mappába másoló művelet a File menü `Export Picture to Folder` (`0x9c81`) és a tálca `Export` gombja; ez nem Paste. | `PicasaFileMenu.qml:141-145`; `TrayActionArea.qml:407-420`; `ExportDialogs.qml:99-105,121-131`; részletes összevetés a #6970 szakaszban | Külön exportút, nincs új #7028 teendő. |
| Képek/videók, egy/több kijelölés, album vagy mappanézet: a kijelölési lista és a fájlműveleti út ismert, de az eredeti gombok minden dinamikus tiltási feltétele nem vezethető le ebből a hívásláncból. | `photoActionPaths()` `MainLibrarySelectionState.qml:197-208`; Paste célja `fileops_controller_clipboard_mixin.py:98-121` | NINCS MEG: a támogatott típusok és minden belépő állapotmátrixa. A lent megadott egyetlen mérési kör döntse el. |
| Albumcél: a `0x00784100` az albumfeltételnél külön `0x00506400` ágat hív; a fizikai fájlcél ága ettől különbözik. | `pasteFilesFromClipboard(dest_folder)` csak célmappa-szöveget fogad: `fileops_controller_clipboard_mixin.py:98-121`; QML hívó `MainWindowCommands.qml:370-376` | Eltérés: nincs albumtagságot kezelő Paste-ág a PicasaPy útban. Lásd a 3. jegyjavaslatot. |

### A vágólap és a megjegyzett állapot

**Könyvtárnézet.** A `0x005fe9f0` a kijelölt sorokat a `0x00577ba0` / `0x007166c0` útján belső azonosítólistába gyűjti, a forrásazonosítót a `[esi+0x318c]` mezőbe és a Copy/Cut módot a `[esi+0x31a4]` mezőbe teszi. A célzott handlerben nem látszik `OpenClipboard` vagy `SetClipboardData` hívás. A shell-féle formátumok globális regisztrációja (`0x005378e0`) a húzás-ejtés útját azonosítja; nem bizonyítja, hogy a könyvtári Copy ezt a fájllistát az operációs rendszer vágólapjára írja. A `picasa-menu-parancsok-viselkedes.md:655-669` e különválasztást rögzíti.

**OneUp.** Az `editpanel/preview` ágból a `0x0069b000` / `0x00a706f0` a szerkesztésekkel renderelt képet teszi a rendszer-vágólapra `CF_BITMAP` formában. Másoláskor nincs megerősítő ablak. A Cut OneUp-beli engedélyezése a kimenetekből nem dőlt el.

**PicasaPy.** A `MainLibrarySelectionState.qml:127-142` OneUpban a `copyRenderedImageToClipboard()`-et próbálja, máskülönben fájl-URL-re esik vissza. Könyvtári Copy/Cut a `QMimeData` fájl-URL-jeit és a GNOME `copy`/`cut` fejlécet teszi fel (`fileops_controller_clipboard_mixin.py:16-82`). Ezzel a OneUp Copy-ról szóló korábbi eltérésjegy elavult. A belső eredeti lista ürítési és Cut-mód-visszaállítási útja a `0x005feab0` utáni takarítási ágban látszik (`0x005feaeb-0x005feb22`).

### Beillesztés, fájlok, ini, katalógus és felületi állapot

1. **Nincs cél.** A `0x005791d0` az `IDS_NEED_SELECTED_ALBUM` üzenetet hívja (`0x005791fb-0x00579220`), `0xf4242` visszatéréssel. A `0x00579220` utasítás a függvényen belüli takarítás, nem megerősítő rutincím. PicasaPy `currentFolder` hiányánál a fájlműveleti vezérlő `False`-t ad, amit a QML tévesen üres vágólapnak ír ki.
2. **Közönséges mappacél.** A Paste `0x00784100`-ba viszi a forrásazonosítót. Ha a cél mappa és forrásazonosítója eltér, a `0x00535020` Copy vagy Move megerősítést indít, majd a `0x005350b0` fájl- és névütközési ágára kerül. A kérdés nem azonos mappánál jelenik meg. Az azonos forrás/cél út `0x00784100`-ban kihagyja a `0x00535020`-at; a fájlmásolás pontos hiánya ebben az ágban statikusan látszik, de a nullás visszatérés utáni látható állapotot mérés kell rögzítse.
3. **Albumcél.** A `0x00784100` a cél típusát és forrásazonosítót külön vizsgálja, és albumfeltételnél `0x00506400` ágra tér. Ez nem ugyanaz a fizikai fájlmásolási út. A teljes tagsági adatbázis-írás és a felületi végállapot nincs meg a meglevő dekompilációban.
4. **Fájl és metaadat.** A `0x005350b0` → `0x00479870` → `0x00478780` út a képfájl-másolás, a `.picasaoriginals` és a `ytPicasaINIFile` kezelés útja. A forrás `.picasa.ini` szekciójának attribútumait, így a csillag- és arcadatot, az eredeti másolóág olvassa. A cél fejléc névváltozás esetén módosul. A `CopyFileW` importot a `0x009af0c0` segédút hívja, de a jelenlegi Ghidra-anyag nem köti feloldottan a harmadik argumentumot a #7028 hívójához. A korábbi `0x00473bd6` és `bFailIfExists=1` állítást elhagytam.
5. **Ütközés.** A `0x005350b0` Copy/Move megerősítő kérdése után azonos célfájlnál `Rename Duplicates`, `Skip Duplicates` vagy `Cancel` választást ad. A generált név pontos utótagja a meglevő dekompilációból nem dőlt el. A PicasaPy `pasteFilesFromClipboard()` közvetlenül `policy="rename"` köteget indít, választóablak nélkül.
6. **Katalógus, mappafa és rács.** A Picasa PMP-oszlopregisztere a `0x004127c0` címen van; a mért db3-készletben a PMP-oszlopfájlok mellett külön indexfájlok is vannak (`pmp-database.md:61-103,197-205`). A `0x00784100` modellt kezelő függvényeket hív és a nézet állapotát jelöli; a meglevő bizonyíték nem adja meg a tartós db3-írás időpontját és a bal panel/rács képkocka utóállapotát. A `CFolderWatcher` és az „azonnali SQLite” állítás nem bizonyított, ezért eltávolítva. A PicasaPy másolás csak a célra jelez (`photoCopied`), az `application_services.py:24-61,110-113` célzott `resyncFolder()`-t indít; ez a rácsot és indexet frissíti, nem a forrást.
7. **Visszavonás.** A vizsgált eredeti Paste-hívásláncban Ctrl+Z visszavonó ág nem szerepel. A PicasaPy fájlművelete is külön másolási vagy mozgatási köteg; a kódforrás nem mutat Paste-hez kötött undo-parancsot.

### Hibák, névütközés és részleges végrehajtás

A `0x005350b0` fájlonként hívja a `0x00479870` segédet; a különleges `0xf4242` visszatérési értéknél a további elemeket tartalmazó ciklusból kilép. A korábban sikerült fájlok visszaállítására a meglevő hívási gráfban nincs ág. A konkrét `CopyFileW` hibakódot megjelenítő ablak, az adott fájl `.picasa.ini` írásának hibája és a kísérő eredeti hibája közti pontos sorrend nincs teljesen feloldva.

PicasaPy `fileops/batch.py:222-271` fájlonként rögzíti a hibát, majd a következő bemenettel folytatja. A `copy_photo()` (`fileops/copy.py:30-96`) a képfájlt visszavonja, ha a megőrzött eredeti másolása hibázik; a `.picasa.ini` írása a kép és eredeti másolása után történik, ezért annak hibája után a fájlok megmaradhatnak. Ez eltér a Picasa további elemeket leállító ágától, és a per-fájl rollback sem teljesen azonos.

| Funkció / Lépés | Eredeti Picasa (bináris cím) | PicasaPy (fájl:sor) | Teendő |
|---|---|---|---|
| Szerkesztés menü Copy | `0x005cb990` -> `0x005fe9f0(0)` | `src/picasapy/app/qml/PicasaPy/PicasaEditMenu.qml:53-58` | Nincs, paritásban van. |
| Gyorsbillentyű Ctrl+C | Accelerator `0x9d3b` (`0x007823f0`) | `src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:244-255` | Nincs, paritásban van. |
| Szerkesztés menü Cut | `0x005cb990` -> `0x005fe9f0(1)` | `src/picasapy/app/qml/PicasaPy/PicasaEditMenu.qml:46-51` | Nincs, paritásban van. |
| Rácselemek halványítása Cut esetén | **Nem igazolt** (Ghidra 2026-11-16): a `0x00716f40` a kijelölés jelzőjét (`[item + 0x5d]`) állítja, a Cut ezt `0`-val törli | Nincs vizuális jelölés a rácson | Nincs teendő, amíg a rajzoló oldal nem igazol halványítást (lásd a 3. jegyjavaslat elvetését). |
| Szerkesztő nézet (OneUp) másolás | `0x0069b000` -> `0x00a706f0` (`SetClipboardData(CF_BITMAP)`) | `fileops_controller_clipboard_mixin.py:16-56` (fájl-URL) | Paritási eltérés javítása: Szerkesztő nézetben a renderelt szerkesztett képet képadatként (`QImage`) kell a vágólapra helyezni. |
| Szerkesztés menü Paste | `0x005cb990` -> `0x005feab0()` | `src/picasapy/app/qml/PicasaPy/PicasaEditMenu.qml:60-67` | Nincs, paritásban van. |
| Gyorsbillentyű Ctrl+V | Accelerator `0x9d3c` (`0x007823f0`) | `src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:268-279` | Nincs, paritásban van. |
| Célválasztás figyelmeztetés | `0x005791fb` (`IDS_NEED_SELECTED_ALBUM`) | `MainWindowCommands.qml:5-7` (hibasáv) | Paritási eltérés javítása: ha nincs aktív mappa vagy album, figyelmeztető párbeszédablakot kell megjeleníteni. |
| Azonos mappa másolási megerősítés | `0x00579220`, `0x00c89d1c` (`CThumbUI::MoveFilesConfirmCopy`) | `fileops_controller_clipboard_mixin.py:84` (azonnali másolás) | Paritási eltérés javítása: azonos mappába másoláskor kérdezzen rá a felhasználónál a másolásra. |
| Fájlok másolása | `0x00473bd6` (`CopyFileW`) | `src/picasapy/fileops/copy.py:53` (`shutil.copy2`) | Nincs, paritásban van. |
| Mentett eredetik (`.picasaoriginals`) | `0x00478780` sor 509 | `src/picasapy/fileops/copy.py:78` (`copy_preserved_originals`) | Nincs, paritásban van. |
| `.picasa.ini` szekció másolása | `0x00478780` (`ytPicasaINIFile`) | `src/picasapy/fileops/copy.py:65` (`_copy_ini_section`) | Nincs, paritásban van. |
| Névütközés átnevezése | `0x005350b0` (`CThumbUI::MoveFilesRename`) | `src/picasapy/fileops/batch.py:159` (`_free_name`) | Nincs, paritásban van. |
| Részleges hiba lekezelése | Ciklus break, sikeresek megmaradnak | Ciklus break, sikeresek megmaradnak | Nincs, paritásban van. |

### Paritási összehasonlító táblázat

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Könyvtári Copy/Cut azonosítólista; OneUp Copy `CF_BITMAP` (`0x0069b000` → `0x00a706f0`). | Könyvtári fájllista, OneUp renderelt kép (`MainLibrarySelectionState.qml:120-142`; `edit_controller_clipboard_mixin.py:32-58`; `fileops_controller_clipboard_mixin.py:16-82`). | OneUp egyezik. A könyvtári vágólap formátumai és belső állapot-élettartama mérésre marad. |
| Eltérő forrás/célmappánál `Confirm Copy` / `Confirm Move`, majd ütközésnél Rename / Skip / Cancel (`0x00784100`, `0x00535020`, `0x005350b0`). | Párbeszéd nélkül, automatikus névátrendező `copyPhotos()`/`movePhotos()` (`fileops_controller_clipboard_mixin.py:98-121`; `fileops_controller_move_mixin.py:64-78`). | **Eltérés:** megerősítő és ütközésválasztó hiányzik. Lásd az 1. jegyjavaslatot. |
| Forrás/cél azonos mappánál a megerősítő/fizikai fájlút őre nem teljesül a `0x00784100`-ban; a látható végállapot nyitott. | `policy="rename"` mellett a `fileops/copy.py:30-96` ugyanoda is fizikai másolatot készíthet. | NINCS MEG: az eredeti művelet utáni állapotot a mérési kör rögzítse, mielőtt erre fejlesztési jegy készül. |
| Cél nélküli Paste figyelmeztetése `IDS_NEED_SELECTED_ALBUM` (`0x005791fb`). | „There are no files on the clipboard to paste.” (`MainWindowCommands.qml:370-376`). | **Eltérés:** a hiba oka és szövege nem egyezik. Lásd a 2. jegyjavaslatot. |
| Albumcél esetén külön tagsági ág (`0x00784100` → `0x00506400`). | Csak célmappa-útvonalat fogad; fájl másolása vagy mozgatása indul (`fileops_controller_clipboard_mixin.py:98-121`). | **Eltérés:** albumtagsági beillesztés hiányzik. Lásd a 3. jegyjavaslatot. |
| Kivágás után a Selection Tray jelvénye változott (`picasa-gyorsbillentyuk.md:2721`, 96 px diff); `+0x5d` kiválasztási bájt, nem rács-halványítás. | A `cut` csak a vágólap fejlécében tárolt; QML rácsban nincs kivágási jelzés (`fileops_controller_clipboard_mixin.py:75-82`; `ThumbDelegate.qml:120`). | **Eltérés:** a tálcajelzés hiányzik. Lásd a 4. jegyjavaslatot; ne készítsünk találgatott 0.5 átlátszóságot. |
| A CopyFile-művelet hibája után az eredeti ciklus `0xf4242`-nél megáll; korábbi kész fájlok megmaradnak (`0x005350b0`). | A `_run()` a hibás képet feljegyzi, de folytatja a köteget (`fileops/batch.py:222-271`). | **Eltérés:** az eredeti leállási szabály hiányzik. Lásd az 5. jegyjavaslatot. |
| Célmappa katalógus- és rácsfrissítése az eredeti Picasában | Célzott PicasaPy-resync (`application_services.py:24-61,110-113`; `library_controller_sync.py:110-116`). | Az eredeti db3 és rács végállapotát mérni kell; watcher/SQLite paritást nem állítok. |
| Kép, mentett eredeti és ini-szekció | `copy.py:30-130` (kép, megőrzött eredeti, szekció). | Fő fájl/ini tartalom útja egyezik; hibás írás részleges hatásához lásd a Nyitott mérést. |
| Copy To Folder / Export | `0x005cb990` `0x9c81`, `0x005312b0`; #6970 teljes összevetés. | Külön művelet, nem clipboard Paste; új #7028 teendő nincs. |

### A két független út

- **A út, hívói utasítások:** a `0x005feab0` és `0x005791d0` disassemblyje követi a Ctrl+V módját, forrásazonosítóját és kijelöléslistáját a `0x00784100` hívásáig; a `0x00784100` hívóhelyének push-sorrendje feloldja a `0x00535020` paramétereit.
- **B út, hivatkozások és párbeszédadatok:** a függvényhivatkozási lista a Paste `0x005791d0` címet a `0x00784100` hívójaként azonosítja; a `string_xrefs.csv` a `Confirm Copy` és `Confirm Move`, valamint a `Rename Duplicates` és `Skip Duplicates` szövegeket a `0x005350b0` függvényhez rendeli. A Ghidra-út innen visszaköti a párbeszédet a `0x00535020` wrapperhez. A forrás- és hívóoldali eredmény egyezik.
- **Megismételhetőségi ellenőrzés:** a `ujralevezetes.py brief` kizárólag a kérdést és címlistát adott át egy új, kontextus nélküli ügynöknek, amely a Paste Copy/Move útját és a `+0x5d` kijelölési jelentését önállóan újra levezette; ez nem helyettesíti a független xref/adat-utat.
- **Másik réteg:** a PicasaPy jelenlegi QML/Python hívási útja és a PMP/db3 formátum-specifikáció megerősíti a helyi oldali állításokat, nem használja az eredeti leletet bizonyítékként.

### Cáfoló kísérlet

Azt próbáltam cáfolni, hogy a Copy/Move megerősítő kizárólag a húzás-ejtés parancsából nyílik. A `0x00784100` közvetlen hívólistájában szerepel a Paste `0x005791d0`, és a Paste disassemblyje ezt a `0x00784100`-at hívja a belső vágólap forrásazonosítójával. A hipotézis cáfolódott: a megerősítő elérhető Ctrl+V-ből is, ha az eltérő forrás/célmappás feltétel teljesül. Külön cáfoló körként a `+0x5d` Cut-jelző értelmezését ellenőriztem: a `0x00716f40` setter és a `0x007166c0` kiválasztás-összegyűjtő út ugyanazt a bájtot kijelölési állapotként kezeli, a mérési napló pedig tálcajelvényt, nem bélyegkép-halványítást jegyez fel.

### A jegy „Kész, ha” pontjai

1. ⛔ **Belépési pontok:** Copy, Cut, Paste, Ctrl+C/X/V, fénykép-helyi menü és Export / Copy To Folder különválasztva. Az eredeti dinamikus engedélyezési mátrix és a képek/videók feltételei nyitottak; a mérési út szerepel.
2. ⛔ **Vágólap és megerősítések:** a belső könyvtári állapot, OneUp `CF_BITMAP`, Paste Copy/Move kérdés és ütközési választék dokumentálva. A dinamikus menüengedélyezés és a OneUp Cut feltétele futásidejű mérést igényel.
3. ⛔ **Fájlok, ini, index, mappafa és rács:** a fájl/ini út megvan; az eredeti PMP/db3 rekord, a bal panel és a rács művelet utáni állapota és az időzítés nincs mérve.
4. ⛔ **Ütközés és részleges köteg:** a Rename/Skip/Cancel választék és az első fájlhibánál történő leállás bizonyított; a PicasaPy folytatási eltérése kódból ellenőrzött. A pontos CopyFileW-paraméter és a konkrét írásihiba-ablak nincs meg.
5. ✅ **Összehasonlító táblázat és fejlesztői jegytörzsek:** lent szerepelnek, mindegyik `Eredeti:` sorral és mérhető „Kész, ha” feltétellel.

#### 3. jegyjavaslat (ELVETVE, a Nyitott kérdések 2. pontja eldőlt: Ghidra 2026-11-16): Kivágott képek halványított jelölése a rácson
- **Cím:** Rács: a vágólapra kivágott (Cut) fotók jelenjenek meg halványítottan a beillesztésig
- **Törzs:**
  ⛔ **Helyesbítve (Ghidra 2026-11-16):** a `+0x5d` a rácselem kijelölt jelzője, a Cut a `0x00716f40`-et `0` jelzővel hívja (kijelölés törlése); a halványítás nem igazolt, ez a javaslat elvetve. Az eredeti, megcáfolt állítás: `0x00716f40` (`[item + 0x5d] = 1`). Az eredeti Picasa kivágáskor a rácson a kijelölt elemeket áttetszőként / halványítottként jeleníti meg, jelezve a leendő áthelyezést.
  Nálunk: a PicasaPy nem tárol vizuális kivágási állapotot a bélyegképekhez.
  Teendő: A vezérlőben vezetni kell a kivágott fájlok listáját (`cutFiles`), és a `ThumbDelegate.qml`-ben az érintett elemek áttetszőségét (pl. `opacity: isCut ? 0.5 : 1.0`) módosítani.
  Kész, ha: a Ctrl+X megnyomásakor a kijelölt képek halványítottan jelennek meg a rácson, majd beillesztéskor vagy újabb másoláskor a halványítás megszűnik.

### Javasolt fejlesztői jegytörzsek

#### 1. Paste-nél eredeti megerősítő és névütközési választó

**Eredeti:** `0x00784100` eltérő forrás- és célmappánál `0x00535020`-on át `Confirm Copy` vagy `Confirm Move` kérdést nyit. A `0x005350b0` ütközésnél `Rename Duplicates`, `Skip Duplicates` és `Cancel` választ ad.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Eltérő mappánál megerősít; célütközésnél a felhasználó választ más név, kihagyás vagy mégse között. | `fileops_controller_clipboard_mixin.py:98-121` azonnal `copyPhotos`/`movePhotos` köteget indít `rename` házirenddel; nincs Paste-dialógus. | A forrás és cél azonosítóját ellenőrző Paste-réteg kérdezzen rá az eltérő mappás másolásra/mozgatásra, és az ütközésnél kínálja fel az eredeti három választ. |

**Kész, ha:** eltérő forrás/célmappánál Elvetés után nincs fájlrendszer-változás; Jóváhagyás után konfliktusmentes képek átkerülnek; ütközésnél Átnevezés, Kihagyás és Mégse mérhetően az eredeti szerint működik. Az azonos mappás viselkedést csak a lent kért mérés után implementáljuk.

1. A `CThumbUI::MoveFilesConfirmCopy` szöveget (`0x00c89f0c`) a bináris-index szerint a `0x005350b0` használja, nem a `0x00579220`; a `0x00579220` a szerkesztőpanel elemeit kezeli. Hogy a kérdés pontosan mikor jön (azonos mappa, mindig, vagy csak húzásnál), nincs igazolva.
   - Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7028-colab-decomp.txt`): a `0x005350b0` a fájlok albummappába mozgatásának vagy másolásának közös rutinja; a `param_4` választja a szöveget (1: `MoveFilesConfirmCopy`, 0: `MoveFilesConfirmMove`), a `param_5 == 0` esetén mindig kérdez, 1 esetén csak a `0x00992ed0` fájlonkénti jelzésére. Hívói: `0x00535020` és `0x005e39a0` (ejtés albumra vagy mappára, mozgatás, mindig kérdez), `0x00541fc0` (másolás, csak jelzésnél). **A kérdés a mozgatásé és a húzásé, nem a Ctrl+V beillesztésé**, ezért a 2. jegyjavaslat a mostani formájában elvetve; a húzásos mozgatás kérdése külön összevetés tárgya.
   - **Feloldás (#7112, 2026-11-16):** a fenti „nem a Ctrl+V beillesztésé” mondat a saját hívólistájának ellentmond. A bináris-index hívóélei szerint a Paste `0x005791d0` hívja a `0x00784100`-at, az egyetlen hívóként a `0x00784100` hívja a `0x00535020`-at, az pedig a `0x005350b0`-at (`param_5=0`, mindig kérdez). A Ctrl+V tehát eléri a megerősítést, amikor a `0x00784100` feltétele (eltérő forrás- és célmappa, közönséges mappacél) teljesül; azonos mappánál és albumcélnál nem. Az 1. jegyjavaslat (#7112) ezért érvényes, a mondat a húzásos utakra (`0x005e39a0`) vonatkozó megjegyzésként olvasandó.
2. A `0x00716f40` egy elem `+0x5d` bájtját állítja; hogy ez a rácson halványított megjelenítést jelent-e, az értelmezés, nem bizonyíték.
   - Ghidra-kör kell: 0x00716f40 - Mit jelöl a rácselem `+0x5d` bájtja, és a kivágás után hogyan rajzolja a rács az így jelölt elemet [nem blokkoló]
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4536`): **a `+0x5d` a rácselem kijelölt jelzője, nem a kivágásé** (`picasa-eger-es-kijeloles.md:310`), és a kimenet nem igazolja a kivágott elemek halványított rajzolását. A `0x00716f40(jelző)` (`:4536-4594`) a nézet (`+0x32c` tömb, `+0x330` darabszám) minden elemén, amelynek `+0x5a` bájtja 0, a `+0x5d`-t a `jelző` értékére állítja (a `+0x5a != 0` elemen nullázza), a változást `+0x59 = 1`-gyel (újrarajzolás) jelzi, `jelző != 0` esetén a nézet `+0x390` mezőjét az első ilyen elem `+0xb4` kulcsára állítja, végül a `+0x31c` tömb minden elemének `+4` metódusát hívja: összes elem kijelölése (1) vagy a kijelölés törlése (0). A Cut/Copy kezelő `0x005fe9f0` (a `0x9d39` Cut a `0x005cbb29 push 1`, a `0x9d3b` Copy `edi` = 0 értékkel, a billentyűről az `X` = `0x58` a `0x005e63f5-0x005e63fe` szerint) ezt **`0` jelzővel** hívja a `[this+0xea4]` nézetre (`0x005fea7c push 0`, `0x005fea7e`), tehát a kijelölést törli, nem jelöl kivágottra; az `1` jelzős hívók a `0x00577ba0` (`0x00577bc3`, `[this+0xeac]`, ha a `0x00716920` nullát ad), a `0x005e5070` (`0x005e5084`) és a `0x0082a670` (`0x0082bfe0`). A kivágás jelzője a `[this+0x31a4]` bájt (a `0x005fe9f0` írja, `0x005fea8d`), amelyet a beillesztő ág olvas (`0x005fead6`, `0x005feb0f`) és nulláz (`0x005feb1b`), a `0x00564db6` is nulláz; a `.text` pásztázása szerint rácsrajzoló nem olvassa. **A rácson halványított megjelenítés tehát nem igazolt; a 3. jegyjavaslat alapja (`0x00716f40`, `[item+0x5d] = 1` mint kivágási jelölés) téves értelmezés volt, a javaslat elvetve.** A rajzoló oldal (a `+0x5d` és `+0x59` olvasói) nincs a kimenetben.
- Ghidra-kör kell: 0x005feab0 - a beillesztő ág (a `[this+0x31a4]` kivágás-jelző olvasója, `0x005fead6`, `0x005feb0f`): a vágólap fájllistáját (`+0x319c`) mikor üríti, és van-e a kivágott elemekre rácsszintű jelölés (a rajzoló a `+0x319c` listát vagy a `+0x31a4` bájtot olvassa-e) [nem blokkoló]
  - **Megválaszolva a zárókörben (2026-11-17), lásd A2:** a lista a sikeres beillesztés után mindig kiürül (`0x005feaeb-0x005feb05`), a `+0x31a4` bájtot csak három függvény éri el (a konstruktor `0x005643e0`, a Másolás/Kivágás kezelő `0x005fe9f0`, a Beillesztés kezelő `0x005feab0`), rajzoló egyik sem; a kivágás tehát a rácson nem jelenik meg.

#### 2. Paste cél nélkül a megfelelő figyelmeztetést adja

**Eredeti:** `0x005791d0` a cél hiányakor az `IDS_NEED_SELECTED_ALBUM` üzenetet hívja (`0x005791fb-0x00579220`).

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A kijelölt mappa vagy album hiányát jelzi. | `MainWindowCommands.qml:370-376` az üres vágólap szövegét mutatja, ha a Paste nem indul el; a célmappa üressége miatt ez is megtörténik. | Különböztesd meg az üres vágólapot a hiányzó Paste-céltól, és az utóbbihoz adj megfelelő, lefordított figyelmeztetést. |

**Kész, ha:** nem üres vágólappal, cél nélküli Paste esetén célhiányt nevez meg a figyelmeztetés; üres vágólapnál megmarad az üres vágólap üzenete; egyik eset sem hoz létre fájlt.

#### 3. Paste külön kezelje a virtuális albumcélt

**Eredeti:** `0x00784100` albumfeltételnél a `0x00506400` ágra tér, külön a közönséges mappacél fájlműveleti útjától. Az albumtagság és a tartós adatbázis-hatás pontos formája még nincs megmérve.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Albumcél esetén külön bináris ág fut; a pontos tagsági és fájlhatás nyitott. | `fileops_controller_clipboard_mixin.py:98-121` csak `dest_folder` útvonalat kap és fájlműveletet indít. | A Paste kezelő különböztesse meg az albumcélt a mappától, majd a mért eredeti hatást a helyi index/API-n át valósítsa meg. |

**Kész, ha:** virtuális album Paste-je a mért eredeti szerint változtatja a tagságot, a fájlokat és a rács/albumlistát; közönséges mappa Paste-je továbbra is a mappacél fájlműveleti útját követi.

#### 4. Kivágás állapota legyen látható a képtálcán

**Eredeti:** a `picasa-gyorsbillentyuk.md:2721` eredeti mérési napló a Ctrl+X utáni Selection Tray állapotjelző jelvény 96 képpontos változását jegyzi. A `0x00716f40` által állított `+0x5d` kijelölési állapot, nem átlátszóság.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Kivágás után látható tálcajelzés változik. | `fileops_controller_clipboard_mixin.py:75-82` a `cut` fejlécet írja ki; nincs tálcaállapot-jelzés. A `ThumbDelegate.qml:120` csak a rejtett képeket halványítja. | A PicasaPy jelezze a tálcán a kivágás/mozgatás állapotát, a felmért eredeti képi jelzést követve; ne a `+0x5d` mezőt utánozza áttetszőségként. |

**Kész, ha:** Ctrl+X után a tálcajelzés a mérési mintával megegyezően megváltozik; Ctrl+C ezt nem teszi; Paste vagy új Copy/Cut után az állapot a felmért eredeti szerint áll vissza.

#### 5. Paste-köteg álljon meg az első fájlhibánál

**Eredeti:** a `0x005350b0` hívási út a `0xf4242` fájlműveleti eredménynél kilép a további elemek ciklusából; a korábbi sikeres másolatokat nem görgeti vissza.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Első fájlhiba után a későbbi képeket nem kezdi el; korábbi sikeres elemek megmaradnak. | `fileops/batch.py:222-271` a hibát rögzíti és folytatja a köteget. | A clipboard Paste köteg jelezze az első végleges fájlhibát és ne indítsa el a következő elemeket; tartsa meg a korábbi sikeres másolatokat. |

**Kész, ha:** három képből a második írási hibájánál az első másolat megmarad, a második hibás állapotú, a harmadik nem keletkezik; egy összegző jelzés nevezi meg a hibát.

### Új kutatási jegyjavaslatok

Most nem javaslok külön kutatási jegyet; az egyetlen nyitott mérési kör ugyanezen #7028 Paste-folyamatot zárja.

### Nyitott

- `NINCS MEG: az eredeti Copy/Cut/Paste menü és gyorsbillentyű dinamikus engedélyezése üres/egy/több elem, videó, könyvtár, OneUp és szövegfókusz esetén; azonos mappás Paste tényleges fájl- és UI-utóállapota; albumcél tagsági hatása; a Paste után írt PMP/db3 rekord és a bal panel/rács/kijelölés végállapota; CopyFileW ütközési/írási hibánál a konkrét fájl- és ini-részállapot. Megszerzés: egy kontrollált Picasa 3.9 Windows-mérési sorozat a fent felsorolt esetekkel. Minden lépés előtt/után rögzíteni kell a rendszer-vágólap formátumait, kijelölést, bal panelt és rácsot; le kell menteni a forrás/cél fájlokat, `.picasa.ini`-ket és db3 mappát, valamint a párbeszédeket és hibaszöveget. [blokkoló]`
  - **Helyesbítve a zárókörben (2026-11-17): a tétel már NEM blokkoló.** A dinamikus engedélyezést, az azonos mappás és az albumcélú beillesztést és a rács végállapotát a bináris utasításai eldöntötték (A1, A3, A4); a maradék peremtételek egy közös, felvehető mérési jegybe kerülnek (B).
- `Ghidra-kör kell: 0x00478780 - a CopyFileW indirekt hívásának harmadik argumentuma a 0x00479870 Paste-hívási útból. A meglévő dekompiláció a .picasa.ini és a mentett eredetik útját feltárja, de az import harmadik paraméterét nem köti a Paste-híváshoz; a pontos összekötést célzottan kell megmutatni. [nem blokkoló]`
  - **Lezárva a zárókörben (2026-11-17), lásd A8:** nem érinti a látható viselkedést, mert a névütközést a beillesztés a másolás ELŐTT feloldja (Átnevezés, Kihagyás, Mégse). A `CopyFileW` burkolója a `0x009af0c0` (UTF-8 átalakító), de a hívói közvetettek, ezért új Ghidra-kör nem kell.

### Zárási döntés

**A #7028 még nem zárható le.** Egyetlen blokkoló marad: a fenti kontrollált Picasa 3.9 mérési sorozat, amely a dinamikus engedélyezést, azonos mappás és albumcélú Paste-et, a db3/rács végállapotot és a részleges írási hibát együtt rögzíti. Az 1., 2. és 5. fejlesztési jegyjavaslat statikus eltérésre épül; a 3. és 4. javaslat pontos viselkedését a mérésnek kell véglegesítenie. A pontos CopyFileW-argumentum külön, nem blokkoló Ghidra-kérdés. Az azonos mappás és albumcélú teendőket a mérés előtt nem szabad végleges specifikációként implementálni.

### Zárókör (2026-11-17): a megmaradt NINCS MEG és Ghidra-kör kell tételek eldöntése

Ez a kör az előző szöveg maradék tételeit döntötte el. A korábbi szakaszok érintetlenek, a helyesbítések itt vannak. Forrás: utasításszintű olvasás a `Picasa3.exe`-ből (SHA-256 fent), a bináris-index sztring- és hívóadatai, a `.text` bájtmintás pásztázása (a `+0x318c`, `+0x319c`, `+0x31a0`, `+0x31a4` mezők hozzáférői, a `0x9d39`, `0x9d3b`, `0x9d3c` parancsazonosítók, a `CopyFileW` hívói), a PE importtábla bejárása a közvetett hívások feloldásához, a `referencia/ghidra/2026-11-15-7012-7028-colab-decomp.txt` korábbi dekompilálása, az `album-sorrend.md` 2.3 szakasza és az eredeti Picasa üres könyvtáras Szerkesztés menüjének képernyőképe (`referencia/kepek-leltar.md` 55. sor, `Colab EN 02 - Edit menu.png`, colab #7). Futásidejű Picasa-mérés nincs. A „Nálunk” állítások a munkafa mostani forrásán ellenőrzöttek (a #7112, #7113, #7114 és #7121 már beolvadt). Fokok: **megerősített** = két független út, **erős** = egy út, egyértelmű utasításokkal, **feltételes** = következtetés.

#### A. Eldöntve a meglévő bizonyítékból

**A0. A `0x00784100` paraméterei a hívóhely disassemblyjéből (megerősített; ez a korábbi dekompiláció `unaff_EDI` és `param_*` értelmezését ellenőrzi).** A `0x005791d0` a `0x005792b3` és `0x005792c3` között a `[főablak+0xeac]` értéket (a bal oldalon megnyitott mappa vagy album kijelölés-csomópontja) az `edi` regiszterbe teszi, ez a `0x00784100` `this` értéke. A négy veremargumentum: (1) a lista, amelyet a `0x007164b0` a `[főablak+0xea4]` csomópont összes nem rejtett eleméből épít (`0x0057923c-0x0057924f`), (2) a sor, a `[főablak+0xeac]` kijelölt soraiból a `0x007172e0` listájának első eleme, kijelölés nélkül -1 (`0x0057927f-0x005792a6`), (3) a FORRÁS azonosítója a `[főablak+0x318c]` mezőből (`0x005792ad`), amelyet a Másolás/Kivágás kezelő ír (`0x005fea40-0x005fea46`: `[[főablak+0xeac]+0x3c0]`), (4) a másolás jelző, amelyet a `0x005feab0` ad (`0x005fead6-0x005feae0`: a `[+0x31a4]` mód nulla-e). A `0x00784100` belsejében a CÉL a `this+0x3c0` (`0x0078428e`, `0x00784336`), a forrás az `ebp` (`0x00784108`), a másolás jelző a `[esp+0xf4]` (`0x007842e1`, `0x00784353`). A `0x004461a0` igaz értéke a közönséges gyűjteményt jelöli (album; a `0x004461de-0x004461e6` fejszó-vizsgálat, a #7012 szakasz szerint), a `0x004ac8f0` az iPhoto- vagy Photos-könyvtár `Masters` mappáját (#7059 szakasz). Következmény: a Beillesztés listája a `+0xea4` csomópontból (a tálca csomópontja, `ui-audit-context-menus.md:1062`) jön, NEM a Másolás által töltött `+0x319c` listából; a `+0x319c` és `+0x31a0` mezőt a `0x005791d0` és a `0x00784100` egyáltalán nem olvassa (a teljes `.text` pásztázása: a `+0x319c` olvasói a `0x005643e0`, `0x00565300`, `0x00577ba0`, `0x00577fd0`, `0x005feab0`, a `0x00784100` és `0x005791d0` nincs köztük). A lista és a tálca tartalmának viszonya a B2 mérésé; a PicasaPy az operációs rendszer vágólapját használja (#1526), ez tudatos bővítés, nem teendő.

**A1. A Kivágás, a Másolás és a Beillesztés engedélyezése a főmenüben (megerősített a kijelölésre és az üres állapotra, erős a Beillesztés szabályára).**

- A Szerkesztés menü a `0x0056e1c0` 1-es menüfajtájának ága (ugrótábla `0x0056f8f8`, 1. elem: `0x0056e742`). A kapu a könyvtári főágban (`0x0056ec28-0x0056ecbd`): a Kivágás (`0x9d39`) és a Másolás (`0x9d3b`) akkor él, ha a `[esp+0x12]` jelző igaz ÉS nincs futó felugró menü (`[főablak+0x34a4] == 0`). A jelzőt a `0x0056e2fd-0x0056e306` az állapotmaszk `0x2` vagy `0x4` bitjéből veszi. A maszkot a `0x005cb1a0` építi: a `0x2` bitet a nem üres kijelölés állítja (`0x005cb2a4`), a többes kijelölés a `0x200` bitet (`0x005cb2ae`), a videó a `0x20` bitet (`0x005cb3ab`) a `0x2` megtartásával; a `0x4` bitet a függvény egyetlen utasítása sem állítja. Tehát kijelölés nélkül mindkettő szürke, egy vagy több képnél és videónál él, a média típusa nem szűr. Második út: az eredeti Picasa üres könyvtáras Szerkesztés menüjén a Kivágás, a Másolás és a Beillesztés szürke (`Colab EN 02 - Edit menu.png`).
- A Beillesztés (`0x9d3c`, `0x0056ec75-0x0056ecbb`) akkor él, ha egyszerre igaz: a belső vágólap listája nem üres (`[főablak+0x31a0] >> 1 != 0`), az aktuális mappa vagy album azonosítója (`[[főablak+0xeac]+0x3c0]`, -1, ha nincs csomópont) ELTÉR a Másoláskor megjegyzett forrásétól (`[főablak+0x318c]`), és nincs futó felugró menü. **Külső vágólap (más program fájljai) a kapuban nem szerepel.**
- A OneUp (néző és szerkesztő) ága: a `0x0056e752` a `[esp+0x13]` jelzőt vizsgálja, amelyet a `0x0056e265` az `editpanel/preview` objektum `+0x20c` bájtjából állít. Ebben az ágban a Kivágás és a Beillesztés feltétel nélkül tiltott (`0x0056e95f-0x0056e967`, `0x0056e985-0x0056e98d`), a Másolás él, ha nincs futó felugró menü (`0x0056e969-0x0056e983`). A kezelők ezt tükrözik: a Másolás kezelő OneUpban a renderelt képet teszi a vágólapra (`0x005fea16-0x005fea26` → `0x0069b000`), a Beillesztés kezelő semmit nem tesz (`0x005fead4` → `0x005feb27`).
- Ha az állapotmaszk `0x4000` bitje be van állítva, a három tétel blokkja kimarad (`0x0056ec28-0x0056ec2d`). Egy másik könyvtári ág (`0x0056eb9a-0x0056ebdb`) mindhármat feltétel nélkül tiltja; a hozzá vezető feltételt nem azonosítottam (feltételes, nem blokkoló: a PicasaPy a főágat követi).
- **Gyorsbillentyű.** A kezelők maguk csak a fenti OneUp-őrt tartalmazzák; hogy a Ctrl+C, Ctrl+X és Ctrl+V a menü tiltott tételére is elküldi-e a parancsot, a kódból nem dönthető el (feltételes), a B3 mérés dönti el. Szövegfókusz: az `Address` mező saját helyi menüje külön névtér (`0x007331e0`, `WM_CUT`, `WM_COPY`, `WM_PASTE`); a főmenü kapuja a szövegfókuszt nem vizsgálja.
- **Nálunk.** Könyvtárban a Kivágás és a Másolás egyezik: PicasaEditMenu.qml:46-58, enabled: bar.photoActionsEnabled, ami MainMenuBar.qml:75 szerint photoActionRows().length > 0; a billentyűk MainKeyboardShortcuts.qml:250-272 ugyanezt adják szövegfókusz-kapuval (ez a PicasaPy-ban szükséges védelem, nem eltérés). A Beillesztés: PicasaEditMenu.qml:68, enabled: bar.clipboardHasFiles (az operációs rendszer vágólapján van-e fájl, fileops_controller.py:206), a billentyű MainKeyboardShortcuts.qml:275-284, _konyvtariGyorsbillentyuEngedelyezve (MainWindowCommands.qml:232: nincs nézőnyitás és nincs szövegfókusz). Eltérések: (1) a Szerkesztés menü Kivágása és Beillesztése nézőben és szerkesztőben él, és a Ctrl+X nézőben is kivág; (2) azonos mappában a Beillesztés engedélyezése eltér. A sikeres beillesztés utáni saját vágólapürítés egyezik az eredetivel (A2), külső fájl-vágólaphoz nem nyúlunk.

**A2. A sikeres beillesztés kiüríti a belső vágólapot; a kivágás jelzőjét semmi nem rajzolja (erős; megválaszolja a `0x005feab0` Ghidra-sort).**

- A `0x005feab0` a `0x005791d0` nulla visszatérése után (`0x005fead6-0x005feae9`) MINDIG felszabadítja és kinullázza a `[+0x319c]` listát (`0x005feaeb-0x005feb0f`), Másolás után is. A nem nulla visszatérésnél (`0xf4242`: Mégse vagy hatástalan eset) a lista megmarad. A kivágás jelzője (`[+0x31a4]`) csak sikeres beillesztés után nullázódik (`0x005feb16-0x005feb1b`). Mivel a Beillesztés menütétel a lista darabszámától függ (A1), **egy Másolás után egyszer illeszthető be a lista**; újabb Másolás vagy Kivágás kell hozzá.
- A `+0x31a4` mezőt a teljes `.text` pásztázása szerint három függvény éri el: a konstruktor (`0x005643e0`, `0x00564db8`), a Másolás/Kivágás kezelő (`0x005fe9f0`, `0x005fea8f`) és a Beillesztés kezelő (`0x005feab0`). **Rajzoló nincs köztük**, tehát a kivágás állapota sem a rácson, sem máshol nem jelenik meg ezen a mezőn át. Ez a 4. jegytörzs „tálcajel” alapját gyengíti (lásd lent).
- Kivágás utáni beillesztés végén a `0x005feb18-0x005feb22` a `0x00577fd0(főablak, 0)` függvényt hívja. A `0x00577fd0` a `Clear Tray` parancs kezelője (sztringek: `IDS_CLEARTRAY`, `This will clear your entire tray.  Are you sure you want to do this?`); hívói még a főparancs-kezelő (`0x005cc03e`) és a tálcagomb kezelője (`0x005da51e`). A nulla második argumentumnál a megerősítő kérdés kimarad (`0x00578025-0x0057802a`, feltételes: a törzs nincs végig olvasva). Tehát a **Kivágás utáni Beillesztés a tálcát kiüríti** (erős a hívásra, feltételes a hatásra); a B2 mérés rögzíti.
- **Nálunk:** a fileops_controller_clipboard_mixin.py:185-217,294-300 sikeres köteg után kiüríti a PicasaPy saját vágólapját; Mégse/hiba után megtartja, és idegen program vágólapját nem törli. A sikeres beillesztés utáni belső listaürítés egyezik. A tálca érintetlen; annak összevetése a B2 után marad.

**A3. Azonos mappa (megerősített: a menü kapuja és a kezelő ága külön kód).**

- A menü tiltja (A1). Ha a parancs mégis eljut a `0x00784100`-ig, a `0x00784336-0x0078434d` szerint a cél és a forrás azonossága kihagyja a `0x00535020` ágat: **nincs megerősítő kérdés, nincs fájlművelet, nincs új fájl.** A `0x00784392-0x007844f3` ciklus ekkor a beillesztett elemeket a cél rendezett képlistájában a megadott helyre mozgatja (a már bent levőt előbb kiveszi: `0x006cb200`, majd beszúrja: `0x006c9e80`; az `album-sorrend.md` 2.3 szakasza szerint ez a kézi sorrend átírása), a záró ciklus kijelöli őket (`+0x5d = 1`, `+0x9c = 0x100`, ld. a dekompilálás `5782-5787` sorát), és 0-t ad vissza. A beszúrás helye kijelölés nélkül a lista vége (`0x0078411d-0x007841da`, a `[this+0x460]` lista darabszáma), egyébként a `0x007172e0` listájának első eleme (hogy ez sorszám vagy azonosító, feltételes).
- **A korábbi „NINCS MEG: az azonos mappás Paste tényleges fájl- és felületi végállapota” ezzel eldőlt:** a látható eredmény nem másolat, hanem a kézi sorrend változása és a kijelölés, és a menüből el sem érhető.
- **Nálunk:** `fileops_controller_clipboard_mixin.py:181-186`: azonos mappánál közvetlen `rename` házirendű fizikai másolat (`név-1.jpg`), a menü nem tiltja. A kézi sorrend a PicasaPy-ban saját kiterjesztés (`priority=`, #1721), ezért a sorrendbeszúrást nem utánozzuk; a teendő a tiltás (6. jegytörzs).

**A4. Albumcél (erős), és a `0x00506400` helyesbítése (megerősített).**

- Ha a cél közönséges gyűjtemény (`0x004461a0(cél)` igaz, eredménye a `0x00784211`-nél a `[esp+0x13]`-ban), a `0x00535020` ág kimarad (`0x0078434f`: a `cmp [esp+0x13], cl` után `jne 0x0078438b`). Nincs megerősítő kérdés, nincs fájlművelet, a forrásfájl nem változik. A beillesztett elemek a cél képlistájába kerülnek ugyanazon a tárolón (`this+0x3fc`, a lista a `+0x64` mezőben), amelyre a helyi menü `Add to Album` almenüje is ír (`0x00536a90` → `0x006ca130`, lásd a #7012 szakasz „a kiválasztott albumhoz adás írója” részét). Két különbség az `Add to Album` tételhez képest: a már tag elem NEM marad ki, hanem a megadott helyre kerül (előbb kiveszi, majd beszúrja), és a beszúrás helye a cél rács első kijelölt eleme (kijelölés nélkül a vége), nem a lista vége. Kivágásnál sem törlődik semmi a forrásból (a `0x0045ef50` ág csak nem közönséges cél esetén fut, `0x00784392` utáni feltétel). A végén az elemek kijelöltek, a lista kiürül (A2).
- **A `0x00506400` NEM albumtagság-író és NEM albumcél-ág; ez helyesbíti az 1. táblázat „Albumcél” sorát és a 3. jegyjavaslat alapját.** Az utasítások szerint a `0x00506400` a katalógus zárja alatt végigmegy az átadott azonosítólistán, és minden elemet, amelynek katalógus-bejegyzése `0x3e9` típusú (`[bejegyzés+0x18]`), a bejegyzés `+0x20` mezőjére cserél (`0x00506453-0x00506496`): az arcbejegyzés azonosítóját a forrásfénykép azonosítójára. A `0x00784100`-ban a hívás (`0x007842dc`) csak akkor érhető el, ha a forrás és a cél személyalbum-jelzője (`0x00448c90`) eltér, a forrás személyalbum, és a cél közönséges gyűjtemény (`0x007842a0-0x007842c3`); ekkor a másolás jelzőt is bekapcsolja (`0x007842e1`). A fordított irány (közönséges kép személyalbumba) némán megáll (`0x007843b8`). A `0x005cb1a0` ugyanezt hívja a személyalbum kijelölésének leképezésére (`0x005cb29f`). Második, független jel: a nyomtatási út `0x005c7830` függvénye a `Preferences\PeopleAlbumUseFaceSrc` kulcsot olvassa, majd a `0x00506400`-at hívja (a #6988 szakasz, `referencia/ghidra/2026-11-15-6988-colab-decomp.txt:1043-1055`), vagyis az arcforrás-választás a függvény dolga, nem az albumtagságé. A `0x00448c90` személyalbum-jelzői szerepe a `picasa-arcfelismeres-kutatasi-naplo.md` szerint a hívóhelyből következtetett (feltételes); a PicasaPy-ban személyalbumba beillesztés nincs, ezért nem teendő.
- **Nálunk (hiba):** a `showAlbum` megtartja a korábbi mappa-kontextust (`controller_filter_mixin.py:137-149`, `_current_folder` nem változik), a Beillesztés pedig `pasteFilesFromClipboard(hostController.currentFolder, mappaNezet)` hívással megy (`MainWindowCommands.qml:380-381`), ahol albumnézetben `mappaNezet == false`. **Albumnézetben a Ctrl+V tehát a korábban megnyitott mappába másol fájlokat, megerősítés nélkül, és az albumhoz nem ad hozzá semmit.** A felhasználó az albumban nézi az eredményt, és semmit nem lát. Lásd a 3. jegytörzset.

**A5. A rács és a kijelölés végállapota a beillesztés után (erős).** Másolás eltérő fizikai mappába: a `0x00784100` a fájlművelet után azonnal 0-t ad vissza (`0x0078437e-0x00784385`), a kijelölést és a sorrendet nem érinti; az új fájlok a célmappa nézetében a fájlművelet és a beolvasás útján jelennek meg (az időzítés B2). Áthelyezés (Kivágás, fizikai forrás és cél): a fájlművelet után a kezelő a 3. és 4. pont szerint beszúr, és a beillesztett elemeket kijelöli. Forrás album vagy `Masters` mappa: a Kivágás kényszerített Másolás (`0x0078434f-0x00784353`, `0x0078432e`), mert onnan nem lehet fizikailag áthelyezni; cél `Masters` mappa: néma megállás (`0x00784302-0x00784309`). A db3 és a PMP-oszlopfájlok írási PILLANATA nem látható viselkedés (a felhasználó a rácson és a mappafán látja az eredményt), ezért nem blokkoló; a bal panel, a rács és a tálca végállapota a B2 mérésé.

**A6. A cél nélküli Beillesztés üzenete (megerősített).** A `0x005791d0` a hibaszöveget akkor adja, ha a `[főablak+0xeac]` csomópont nulla (`0x005791f3-0x005791f9`), vagyis nincs megnyitott mappa vagy album; a szöveget a `0x009ae710`, a megjelenítést a `0x009807f0` végzi (`0x005791fb-0x0057921b`), ugyanaz a függvény, amelyet a #7121 a modális Információ-ablakhoz azonosított. **Üres lista (`0x007164b0` üres, `0x00579259-0x0057925d`) esetén a kezelő üzenet nélkül 0xf4242-vel tér vissza.** **Nálunk:** a #7113 a szöveget és a feltételt megvalósította (`MainWindowCommands.qml:375-380`, `A Folder or Album must be selected to do this.`), de hibasávban (`errorBanner`), nem modális ablakban; a #7121 `showOperationInfo` ablaka (`MainWindowDialogStack.qml`) erre kész. Az üres vágólap hibasávja (`MainWindowCommands.qml:384`) kis, nem blokkoló eltérés: az eredetiben a menü ilyenkor szürke, a billentyű néma.

**A7. Típusszűrés (megerősített).** Sem a menükapuban (A1), sem a `0x00784100`, `0x00535020` és `0x005350b0` láncban nincs kép- és videótípus-szűrés; a kijelölés-gyűjtők (`0x005cb1a0`, `0x007164b0`) csak a rejtett jelzőt (`+0x5a`) vizsgálják. A PicasaPy kép és videó támogatása egyezik.

**A8. Hiba, részleges állapot, `CopyFileW` (lezárva, nem blokkoló).** A látható rész bizonyított és megvalósított: a `0x005350b0` ciklusa a `0xf4242` eredménynél kilép, a korábbi másolatok megmaradnak (#7114). A fájl- és ini-részállapot lemezszintű sorrendje (a `.picasa.ini` írása a fájl után) nem látható viselkedés. A `CopyFileW` importját (IAT `0x00c404c0`) egyetlen függvény hívja, a `0x009af0c0` (`0x009af192`), amely UTF-8 szöveget alakít át a Win32 hívás előtt; a burkoló hívói közvetettek (a címe a `0x00c32cf0` függvénymutató-táblában áll, közvetlen `call` és abszolút hivatkozás nincs a kódban), ezért a harmadik argumentum statikusan nem követhető olcsón. Nem is kell: a beillesztés a névütközést a másolás ELŐTT feloldja (`This folder already contains files with the same name`, Átnevezés, Kihagyás, Mégse), tehát a felülírási jelző csak versenyhelyzetben látszana. Új Ghidra-kör nem kell.

#### B. Mérés dönti el (egy közös mérési jegy, nem blokkoló)

A következő tételeket sem újabb Ghidra-kör, sem statikus olvasás nem dönti el olcsón. Egy mérési jegy adja őket (Colab, az angol 3.9.141 Wine alatt, a `colab_felmero.py futtat --lepesek ...` útján, izolált mintakönyvtárral: három mappa A, B, C, mindegyikben ismert nevű képek, egy album, a C mappában egy azonos nevű kép). A mérés saját eszközzel elvégezhető, ezért a jegye `ready`, nem `blocked`, és semmi nem épül rá a 3. és a 6. jegytörzsből.

- **B1. Kivágás és tálcajel.** Ctrl+X és Ctrl+C ugyanazon három kijelölt képen, teljes ablak előtte és utána, pixelkülönbség-térkép. Dönti: a „96 képpontos” tálcajel (`picasa-gyorsbillentyuk.md:2720-2721`, `picasa-colab-jobs #456`, a nyers kép nem került elő) tényleges helyét és okát, vagyis a 4. jegytörzs sorsát. A statikus kép ellene szól (A2: a kivágás jelzőjét semmi nem rajzolja).
- **B2. Mit illeszt be, mi marad.** Másolás az A mappában, lépés a B mappába, Beillesztés menüből: a tálca tartalma a mappaváltás előtt és után, a beillesztett képek forrása (a Másolás kijelölése vagy a tálca), mikor jelennek meg a fájlok a rácson és a mappafán, a kijelölés; Kivágás és Beillesztés után a tálca tartalma (a `0x00577fd0` hívás); Beillesztés albumba (sorrend, kijelölés). Dönti: A0 és A2 maradékát.
- **B3. Gyorsbillentyű és tiltott menütétel.** Ctrl+V azonos mappában (a menü szürke), sikeres beillesztés után második Ctrl+V, Ctrl+X nézőben. Dönti: a billentyű megkerüli-e a menükaput.
- **B4. Névütközés.** Azonos nevű fájl a célban, Átnevezés választása: a keletkező fájlnév utótag-sémája (a #7112 jelenlegi `név-1` sémája a #6845 szakaszban bizonyíték nélkül „egyezik”). Írásvédett célmappa (`attrib +R`): hibaüzenet és részleges állapot.

#### Helyesbítések a korábbi állításokhoz

- **A Szerkesztés menü „Belső vágólap nem üres VAGY külső vágólapon képadat/fájllista van” kapuja (a belépési pontok táblája, Beillesztés sor) téves.** A kapu a belső lista nem üres, az aktuális mappa eltér a forrástól, és nincs futó felugró menü (A1); külső vágólap nem szerepel benne.
- **„Könyvtárban legalább 1 kijelölt elem (`[esi + 0xeac] > 0`)” a Másolás és Kivágás sorokban:** a `0x005fe9f0` kezdő vizsgálata (`cmp [esi+0xeac], 0`) a bal paneli csomópont létét ellenőrzi, nem a kijelölés darabszámát; a kijelölés nem üres voltát a menükapu (`0x2` maszkbit, A1) és a `0x00577ba0` gyűjtő adja. A `0x00577ba0` ráadásul kijelölés nélkül az összes elemet kijelöli (`0x00577bb2-0x00577bc3`, `0x00716920` nullát ad), ha a menü a tételt engedte.
- **„Azonos mappa másolási megerősítés | `0x00579220`, `0x00c89d1c` | Paritási eltérés javítása: azonos mappába másoláskor kérdezzen” (a hibák táblázat 877. sora) téves.** A `0x00579220` a cél nélküli ág egyik utasítása, a megerősítő szöveg a `0x005350b0` függvényé, és azonos mappánál NINCS kérdés (A3). A sor javítási teendője törlendő.
- **„Fájlok másolása | `0x00473bd6` (`CopyFileW`)” (878. sor)** a szöveg 4. pontja szerint már visszavont állítás; a táblázat sora maradt. Nem bizonyított cím (A8).
- **„Részleges hiba lekezelése: Ciklus break … Nincs, paritásban van” (882. sor) ellentmond a 894. sornak;** a helyes: az eredeti kilép az első hibánál, a PicasaPy a #7114 óta ugyanígy tesz (Kész).
- **A „Szerkesztő nézet (OneUp) másolás … Paritási eltérés javítása” (873. sor)** elavult: a #7030 óta megvalósított (`MainLibrarySelectionState.qml:127-142`); a hozzá tartozó korábbi jegyjavaslat nem indítandó.
- **A Kivágás és a Beillesztés „Szerkesztőben inaktív … Egyezik” sorai (821-826. sor)** a PicasaPy oldalán nem igazak: a menü és a Ctrl+X nézőben él (A1, 6. jegytörzs).
- **A `0x00506400` „albumcél” szerepe** (A4) megdőlt; ez a 3. jegyjavaslat („Paste külön kezelje a virtuális albumcélt”) „Eredeti” sorát is érinti, lásd a 3. jegytörzs újraírását lent.

#### Az eddig nyitott tételek eldöntése (14 tétel)

| Régi tétel | Döntés | Hol |
|---|---|---|
| `NINCS MEG`: dinamikus engedélyezés (üres, egy, több elem, videó, könyvtár, OneUp, szövegfókusz) | (a) lezárva; a billentyű útja (b) mérés | A1, A7, B3 |
| `NINCS MEG`: azonos mappás beillesztés fájl- és felületi végállapota | (a) lezárva | A3 |
| `NINCS MEG`: albumcél tagsági hatása | (a) lezárva; a `0x00506400` helyesbítve | A4 |
| `NINCS MEG`: a db3 és PMP rekord, a bal panel, a rács és a kijelölés végállapota | (a) a kijelölés és a sorrend lezárva; az írás pillanata (c) nem látható; a rács időzítése (b) | A5, B2 |
| `NINCS MEG`: `CopyFileW` ütközési és írási hibánál a fájl- és ini-részállapot | (c) nem látható viselkedés; a hibaüzenet (b) | A8, B4 |
| `Ghidra-kör kell: 0x00478780` (`CopyFileW` harmadik argumentuma) | (c) lezárva | A8 |
| `Ghidra-kör kell: 0x005feab0` (a kivágás-jelző olvasója, a lista ürítése) | (a) lezárva | A2 |
| A kivágás tálcajele (96 képpont) | (b) mérés | B1 |
| A Kivágás OneUp-beli engedélyezése | (a) lezárva: a menü tiltja, a kezelő másolja a képet | A1 |
| A Beillesztés szerkesztőben inaktív voltának feltétele | (a) lezárva | A1 |
| A Beillesztés külső vágólap-kapuja | (a) helyesbítve: nincs ilyen kapu | A1 |
| A `Rename Duplicates` utótagja | (b) mérés | B4 |
| Új: a Beillesztés listájának forrása (tálca vagy Másolás-lista) | (b) mérés, nem blokkoló; a PicasaPy-ra nincs hatása | A0, B2 |
| Új: a Kivágás utáni tálcaürítés (`0x00577fd0`) | (b) mérés, nem blokkoló | A2, B2 |

#### Fejlesztői jegytörzsek a mai forráson ellenőrizve

- **1. Paste megerősítő és ütközésválasztó: KÉSZ** (#7112, `fileops_controller_clipboard_mixin.py:145-186`, `MainWindowDialogStack.qml:103`). Nincs további teendő.
- **2. Cél nélküli Paste: KÉSZ szöveg és feltétel szerint** (#7113). A modális ablak maradéka a 6. jegytörzs 4. pontja.
- **5. Megállás az első fájlhibánál: KÉSZ** (#7114, `batch.py`, `fileops_controller_clipboard_mixin.py:132-143`).
- **Régi 3. jegyjavaslat (halványított rács): ELVETVE** (Ghidra 2026-11-16, A2).
- **4. Kivágás tálcajele: NEM INDÍTHATÓ.** Az „Eredeti” (a 96 képpontos jel) nyers kép nélkül nem mérhető elfogadási feltétel, és a statikus kép ellene szól (A2). A B1 mérés után kell újra megítélni; addig nem része a #7028 lezárásának.

#### 3. jegytörzs (újraírva): A Beillesztés albumnézetben az albumhoz adjon, ne másoljon fájlt

**Eredeti:** a `0x00784100` (cél: `[főablak+0xeac]`, `+0x3c0`; forrás: `[főablak+0x318c]`) közönséges gyűjtemény (album) cél esetén kihagyja a fájlműveleti ágat (`0x0078434f`, `0x0078438b`): nincs megerősítő kérdés, nincs fájlmásolás. Az elemek a cél rendezett képlistájába kerülnek (`0x006c9e80`), a már tag elem előbb kikerül és a megadott helyre kerül (`0x006cb200`), a hely a cél rács első kijelölt eleme, kijelölés nélkül a lista vége. A végén az elemek kijelöltek, és a belső vágólap kiürül. A Kivágás albumcélnál nem töröl a forrásból. A `0x00506400` ebben nem szerepel (A4).

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Album cél: tagság a cél képlistájába szúrással, fájl nem keletkezik, kérdés nincs. | `controller_filter_mixin.py:137-149` megtartja a korábbi mappát; `MainWindowCommands.qml:380-381` a korábbi mappába másol, megerősítés nélkül. | `viewModeName == "album"` esetén a Beillesztés a vágólap fájljait útvonal szerint képekre oldja fel, és az album tagjává teszi a meglévő tagság-úton (`photo_ops_album_membership_mixin.py:31` `addRowsToAlbum`, `ini/albums.py:65` `with_album`); fájlt nem másol, a korábbi mappához nem nyúl. A már tag kép nem duplikálódik. A Kivágás sem töröl. |

**Kész, ha:** (1) albumnézetben a menü és a Ctrl+V a vágólap képeit az album tagjává teszi, és sehol nem keletkezik új fájl (a korábban megnyitott mappa tartalma változatlan); (2) a már tag kép nem kerül kétszer az albumba; (3) Kivágás után az album ugyanígy működik, a forrásfájl a helyén marad; (4) mappanézetben a viselkedés változatlan. A pozícióbeszúrás (a cél rács első kijelölt eleme) nem része a jegynek, mert a PicasaPy kézi album-sorrendje saját kiterjesztés (#1721).

#### 6. jegytörzs (új): A Kivágás és a Beillesztés engedélyezése az eredeti szerint

**Eredeti:** a `0x0056e1c0` Szerkesztés-ága (A1): nézőben és szerkesztőben a Kivágás és a Beillesztés tiltott (`0x0056e95f-0x0056e98d`), a Beillesztés kezelő hatástalan (`0x005fead4`); könyvtárban a Beillesztés akkor él, ha a belső lista nem üres, a mappa eltér a forrástól (`0x0056ec92`), és a sikeres beillesztés a listát kiüríti (`0x005feaeb-0x005feb05`). Azonos mappában nincs fájlművelet (A3). A cél nélküli üzenet modális Információ-ablak (A6).

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Nézőben és szerkesztőben a Kivágás és a Beillesztés szürke, a Másolás él. | `PicasaEditMenu.qml:46-68` kapu nélkül; `MainKeyboardShortcuts.qml:264-272` Ctrl+X nézőben is kivág. | Néző nyitva (`viewerOpen`): a Kivágás és a Beillesztés tétele tiltott, a Ctrl+X nem kivág. |
| Azonos mappában a Beillesztés szürke. | `PicasaEditMenu.qml:68` csak `clipboardHasFiles`; `fileops_controller_clipboard_mixin.py:181-186` azonos mappánál `név-1` másolatot készít. | A Beillesztés tiltott, ha a vágólap minden fájlja az aktuális mappában van; a billentyű és a menü ugyanazt a kaput használja. Fizikai másolat azonos mappába nem készül. |
| Sikeres beillesztés után a belső lista üres, a tétel szürke; Mégse esetén megmarad. | A saját vágólap sikeres köteg után ürül, hiba/Mégse esetén megmarad (fileops_controller_clipboard_mixin.py:185-217,294-300); külső vágólap megmarad. | Egyezik a belső lista ürítése; a külső vágólap megőrzése PicasaPy-saját védelem. Nincs teendő. |
| A cél nélküli üzenet modális Információ-ablak (`0x005791fb-0x0057921b`). | `MainWindowCommands.qml:375-380` hibasáv. | A #7121 `showOperationInfo` ablakának (`MainWindowDialogStack.qml:42-45`) hívása a hibasáv helyett. |

**Kész, ha:** (1) nézőben a Szerkesztés menü Kivágása és Beillesztése szürke, a Ctrl+X és a Ctrl+V hatástalan, a Másolás él; (2) azonos mappában a Beillesztés szürke és a Ctrl+V nem készít fájlt; (3) saját Másolás és sikeres beillesztés után a Beillesztés szürke, új Másolás után él; (4) a cél nélküli üzenet modális ablakban jelenik meg, a hibasáv nem; (5) a külső fájl-vágólap beillesztése eltérő mappába változatlanul működik. A tálca ürítése a Kivágás után (A2) a B2 mérés előtt nem része a jegynek.

### Zárási döntés (a 2026-11-17-i zárókör után)

**A #7028 kutatási jegy lezárható.** Ez felülírja az előző döntést, amely szerint az egyetlen blokkoló egy mérési sorozat. Indok: minden tétel, amelyből fejlesztői jegytörzs készíthető, a bináris utasításaiból eldőlt (A0-A8): a dinamikus engedélyezés, az azonos mappás és az albumcélú beillesztés, a rács és a kijelölés végállapota, a kivágás jelzőjének olvasói és a `CopyFileW` kérdése. A megmaradt tételek (B1-B4) peremesetek vagy kozmetikai részletek (a billentyű és a menükapu viszonya, a névütközés utótagja, a tálca tartalma), amelyektől a 3. és a 6. jegytörzs nem függ; egy közös, felvehető mérési jegybe kerülnek. Bizonyítottsági fok: **megerősített** a `0x00784100` paramétereire (A0), a Kivágás és Másolás kijelöléskapujára, az azonos mappás ágra és a `0x00506400` helyesbítésére; **erős** a Beillesztés menükapujára, az albumcélú ágra, a lista kiürülésére és a kivágás-jelző olvasóira; **feltételes** a gyorsbillentyű kapujára, a tálcaürítés hatására és az `0x0056eb9a` ág feltételére.

Nyitott kérdések mérlege (az „Az eddig nyitott tételek eldöntése” tábla 14 sora): 0 nyílt · 8 lezárva (az 1., 4. és 5. sor maradéka a B mérés kérdése, nem külön tétel) · 4 mérési jegyre kijelölve (B1-B4, felvehető, nem blokkoló) · 0 blokkolt · 2 nem látható viselkedés (nem blokkoló) · 0 „csak nyitva”.

**Fejlesztői jegytörzsek, amelyek maradnak (mindegyik Eredeti / Nálunk / Teendő / Kész, ha, a mai forráson ellenőrizve):**

- **3. A Beillesztés albumnézetben az albumhoz adjon:** jegy kell, hibajavítás (a Ctrl+V albumnézetben a korábbi mappába másol). Lásd fent.
- **6. A Kivágás és a Beillesztés engedélyezése az eredeti szerint:** jegy kell (nézőkapu, azonos mappa, ürítés, modális üzenet). Lásd fent.

**Készre ítélt vagy nem indítandó jegytörzsek (jegy nem kell):** az 1. (#7112), a 2. (#7113, a maradék a 6. 4. pontja), az 5. (#7114), a régi 3. jegyjavaslat (halványítás, elvetve) és a 4. (tálcajel, nem indítható, a B1 mérés után ítélendő).

**Egyetlen felvehető mérési jegy:** B1-B4 (angol 3.9.141 Wine, Colab); `ready` címke, nem blokkoló. Új Ghidra-kör nem kell.


### #7235-kiegészítés (2026-11-18): kivágott elemek jelzője és sikeres beillesztés

#### #484 - 0x005feab0

A 0x005feab0 dekompiláció (2026-11-18-koteg-466-495.txt:3478-3515) a sikeres 0x005791d0 után felszabadítja és nullázza a [this+0x319c] belső fájllistát; ha a [this+0x31a4] kivágásjelző igaz, azt is törli és meghívja a 0x00577fd0-at. A visszatérési/no-op ágon a függvény korábban kilép, a lista és jelző megmarad. A korábbi teljes .text-pásztázás a +0x31a4 olvasóit a kivágás/beillesztés útjaira, nem a rácsrajzolóra kötötte; az A2 szakasz a +0x319c listaolvasóit is felsorolja, köztük nincs bélyegkép-rajzoló. Ez a két külön adatút együtt támasztja alá, hogy nincs rácsszintű kivágásjelzés. Így a belső kivágott elemeknek a sikeres beillesztés után nincs rácsszintű halványító jelzése. PicasaPy fileops_controller_clipboard_mixin.py:208-217,235-300 a saját vágólapját a sikeres beillesztés után üríti; ez a régi Picasa belső állapotának megfelelő irány. Az A2 meglévő jegytörzs-bővítése a részletes PicasaPy-egyezést/eltérést és a „Kész, ha” feltételt tartalmazza.

## #7033: A dátum és idő beállításának teljes folyamata

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldalt a binárisból és az erőforrásokból, a PicasaPy oldalt a
jelenlegi forrásból olvastam. Ez a rész a 7033 kérdéseit fedi le; nem
tekinti bizonyítéknak a korábbi, részleges dátummódosító-leírást.

### Következtetés

Az eredeti Eszközök menü és a Tulajdonságok panel `DateTimeOriginal` sorának
helyi menüje ugyanahhoz a `0x9e0e` parancshoz vezet; külön gyorsbillentyűt vagy
a rács helyi menüjében parancsot nem találtam. Egy kép közvetlen dátumot kap, több kép
alapértelmezés szerint eltolást; a 22 képes Picasa 3.9-es képernyőkép az
eltolás rádió kijelölését méri, a Ghidra-kimenet pedig nem talál megjegyzett
beállítást. A párbeszéd kezdeti dátummezője a feloldott kijelölési lista első
elemének katalógusából lekért `FILETIME`-mal indul; a lista a rács indexsorrendjét
követi. A JPEG-ág a
`DateTimeOriginal` mezőt írja, a nem-EXIF ág a fájlrendszer idejét és
`thumbindex.db` rekordját kezeli, `.picasa.ini` kulcsot nem ír. A még
megmaradt, felhasználó által látható pontokat egyetlen kontrollált
Windows-mérési sorozat dönti el, ezért a jegy még nem zárható.

### Bizonyítottsági fok

**Feltételes.** A kezdő dátum forrását a hívóhely utasításai, a konstruktor
adatátvétele és a kijelölési lista külön feltárt sorrendje együtt igazolja; a
PicasaPy jelenlegi QML-je ugyanezt a sorindex szerinti első elemet választja.
A relatív alapmódot külön meglévő képernyőmérés igazolja, a megjegyzés hiányát
a Ghidra-kimenet. A néző/tálca menüengedélyezése, a natív ablak viselkedése,
a siker utáni látható végállapot és az írásvédettség tényleges kimenete továbbra
is Windows-mérést igényel.

### 1. Belépési pontok, kijelölés és gyorsbillentyű

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Eszközök menü.** A `0x00559150` menürekord-építő a `0x00c8e048` azonosítót és `0x00c8e070` feliratot társítja a `0x00d6e904` rekordhoz; ennek parancsmezője `0x9e0e` (`0x0055c7cd`). A parancs-diszpécser `0x005cb990` `case 0x9e0e` ága `0x0057d7f0`-re lép. Egy kép a közvetlen dátumot, legalább két kép az eltolási adatot adja át (`0x0057d7f0`, `0x0077cf70`). | A menütétel `PicasaToolsMenu.qml:79-83`; a könyvtári művelet a `MainMenuBar.qml:354-355` címen adja át a `photoActionRows()` értékét. A `MainMenuBar.qml:112-114` legalább egy kijelölést és zárt nézőt követel. | A kezelő viselkedése igazolt; az eredeti menüpont üres kijelölés, néző és tálca melletti engedélyezése mérendő. A `0x005c76b0` kijelölés nélkül is összegyűjtheti a látható elemeket, ezért a kezelő tartalékágából önmagában nem következik a menü állapota. |
| **Tulajdonság helyi menüje.** A `0x00638990` a kiválasztott `PropertiesListItem` `+8` típusát vizsgálja; `0x37` esetén hozzáadja a `0x9e0e` parancsot és a `0x00c8e048` feliratot. A hívó `0x00637fa0`. A `0x37` az EXIF `0x9003` `DateTimeOriginal` mező (`picasa-metaadat-tulajdonsagok.md:53`). | A `PropertiesPanel.qml:165-169` dátumtípusú sorhoz jeleníti meg a „Adjust &Date and Time...” műveletet; a jobb kattintás sorfelismerése `:194-205`. A könyvtári panel `MainRightDrawer.qml:150-154`, a néző panelje `PhotoViewerRightPanels.qml:43-47` az adott sorral nyitja meg a párbeszédet. | **Egyezik a belépési pont.** A régi „csak Edit Tags” leírás elavult; erre fejlesztői jegy nem indokolt. |
| **Rács helyi menüje.** A teljes `.text` pásztázás a `0x9e0e` közvetlen kódtalálatait csak a menürekord-építőben (`0x0055c7cd`) és a tulajdonságmenüben (`0x00638a0a`) találta. Külön rács-helyi dátumparancsot nem azonosítottam. | A `PhotoContextMenu.qml:163-520` nem tartalmaz dátummódosítót. | Az eredeti közvetlen kódbeli dátumbejárat hiánya ellenőrzött. A Tools menü ettől még meghívható lehet rácskijelölésre. |
| **Néző.** A `0x005c76b0` előbb a látható nézetet gyűjti; üres nézetlista esetén a `this+0xe64` aktuális képre hivatkozik, ha az nem `-1`. A főablak-eseménykezelő és a parancs menüengedélyezése ettől még nincs végigkövetve. | A `MainMenuBar.qml:112-114` az Eszközök dátumműveletét letiltja nyitott nézőnél; a `ViewerContextMenu.qml:122-294` nem tartalmaz dátumműveletet. | A bináris kezelője képes az aktuális egyképes nézet elemét bemenetként felvenni, de az eredeti menü tényleges engedélyezése mérendő. A PicasaPy tiltása ismert eltérésjelölt. |
| **Képtálca.** Az eredeti `0x005c76b0` bemenete a látható nézet, a csoportosított arcnézet csomópontja (`+0x3c9`, virtuális `+0xdc`), illetve az aktuális kép (`+0xe68`); külön tálcalista nem szerepel az útban. | A `TrayContextMenu.qml:40-95` nem tartalmaz dátummódosítót. Az Eszközök menü `MainMenuBar.qml:112-114` a főrács `selectedIndexes` értékéhez kötődik, nem a tálca tartalmához. | A vizsgált kezelő útja nem a tálca-listát adja át. Az Eszközök menü tálca melletti elérhetőségét egy Windows-mérés zárja le. |
| **Gyorsbillentyű.** A `Picasa3i18n.dll` `SHORTCUTS.XML` erőforrása 48 rekeszt tartalmaz dátum-idő műveletre mutató rekord nélkül; a `0x00559150` menüsor 32 gyorsbillentyűs rekordja közt sincs `0x9e0e`. A `0x00c8e070` felirat `Adjust &Date and Time...`; ez menübillentyűt jelez, külön Ctrl/Alt+billentyű-kötést nem. | A QML felirata szintén `Adjust &Date and Time...` (`PicasaToolsMenu.qml:80`); a teljes `MainKeyboardShortcuts.qml:1-551` fájlban nincs dátumművelet. | Külön gyorsbillentyű-parancsot egyik oldalon sem találtam. A menü feliratának `D` menübillentyűje nem külön műveletbillentyű. |

Az eredeti kezelő a `0x0057d7f0` útján hívja a `0x005c76b0` kiválasztási
segédet. Egy elemnél a cím `Adjust Photo Date`; két vagy több elemnél a
`0x0077c7c0` a `OffsetPhotoDate:Title` erőforrásból darabszámos címet épít.
A kezdő `FILETIME` adatútját a hívóhely disassemblyje tisztázza: a
`0x0057d894` a `CThumbUI+0x50` objektum `+0x6c` értékét betölti EDI-be, de ez
nem a dátum. A `0x0057d8f3` a feloldott lista első azonosítójával meghívja a
katalógus `+0xc4` virtuális metódusát, amely a veremrekordba írja a dátumot.
A `0x0057d91a` a korábban betöltött `+0x6c` értéket külön argumentumként
veremre teszi, majd a `0x0057d91b` az EDI-t a `+0xc4` által kitöltött
veremrekordra állítja a `0x0077c670` konstruktor `0x0057d923` hívása előtt.
A konstruktor az `unaff_EDI[0]` és `[1]` értékét másolja a kezdeti
dátum/idő mezőkbe (`referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt`,
#402-403). Így a kezdő érték a feloldott lista első elemének katalógusadata,
nem a `CThumbUI+0x50` objektum `+0x6c` mezője.

A sorrend külön bizonyítékból ismert: a `0x00506500` megtartja a bemeneti
sorrendet, a `0x007166c0` pedig a látható, kijelölt elemeket rácsindex szerint
gyűjti (`referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt`, #418;
`2026-11-16-7022-7031-7033-colab-decomp.txt`, #424). A párbeszéd tehát a
rácssorrend szerinti első kijelölt kép idejéből indul. Kijelölés nélkül a
segéd látható elemeket is gyűjthet, de ebből nem következik a Tools menü
engedélyezése.

### 2. Ablak, mezők és alapértékek

Az eredeti `runtime/offsettime.fen` leíró (`0x00cb40a0` azonosító,
`0x00cb4090` előnézeti elem) `Current photo date` dátum/idő mezőt,
`New photo date` dátum/idő mezőt, `relative` és `absolute` rádiót, valamint
OK/Cancel gombot sorol fel. A `0x0077c7c0` a `currentdate` vezérlőt tölti,
majd a kapott FILETIME alapján állítja elő az új dátum és idő kezdeti
értékét. A `0x0057d7f0` a lista első azonosítójával kéri le a katalógus
`+0xc4` metódusát (`0x0057d8ec`-`0x0057d8f3`); az általa kitöltött
veremrekord címe kerül EDI-be a `0x0077c670` konstruktor hívásakor
(`0x0057d91b`-`0x0057d923`). A konstruktor ezt a rekordot másolja a jelenlegi
és új dátum/idő mezőkbe (#402-403). A külön betöltött
`CThumbUI+0x50` objektum `+0x6c` értéke egy másik argumentum, nem a kezdeti
`FILETIME`. A `0x00506500` megőrzi a listát, a `0x007166c0` rácsindex szerint
gyűjti; a kezdő dátum ezért a rácssorrend első kijelölt elemének ideje.
A többes elemszám
csak akkor kerül a címbe, ha a darabszám nagyobb egynél (`0x0077c7c0`). Az
eredeti `.fen` szélesség-megjelölése `fit`.

Az `adjust_type` rádiólekérdezését a `0x0077cee0` végzi; az elfogadáskor a
`0x0077cd50` dolgozza fel a `newdate`, `newtime` és `adjust_type` mezőket.
A konstruktor a belső módjelzőt 1-re állítja; a lekérdezés szerint ez a 0.
rádiógomb értéke (`referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt`,
#402). Az eredeti `runtime/offsettime.fen:19-21` a `relative` rádiót teszi
elsőnek, az `absolute` rádiót másodiknak; a meglévő 22 képes Picasa 3.9-es
képernyőképen az első, `Adjust all photo dates by the amount` rádió van
kijelölve (`referencia/kepek-leltar.md:104`, `Colab EN 28 - Adjust Photo Date.png`).
Az eredeti tehát eltolás móddal indul több képnél, de a háttérfeldolgozó egy képnél
közvetlen célidőt ír. A konstruktor és a két párbeszédkezelő nem olvas és nem
ír megjegyzett beállítást; a módot nem menti el.

Az eredeti módok végrehajtási jelentése: az `0x0057d7f0` több kijelölt
elem és relatív jelző esetén az új és régi idő különbségét számolja
(`0x0077cf70`), majd a `+0x80/+0x84` munkaszál-mezőket adja át;
abszolút módban cél-FILETIME-t állít a `+0x78/+0x7c` mezőkbe. A
`0x0077cfd0` az előbbi alakot a `0x00490580`, a cél-FILETIME alakot a
`0x00490c10` háttérfeldolgozóhoz köti. Egyetlen kijelölt elemnél a `0x0057d7f0`
mindig közvetlen cél-FILETIME-t ad át (`0x0057d9d4-0x0057da08`), tehát az
egy-képes eredmény abszolút.

PicasaPy oldalon az `AdjustTimestampDialog.qml:62-82` előbb a kapott sorokat
számszerű sorindex szerint rendezi (`:65-67`), majd az első rendezett sorból
tölti a jelenlegi és új időt (`:68-69`); minden nyitáskor relatív módot
választ (`:80-81`), és a címet csak több sornál bővíti (`:22-24`). Az eredeti
és a PicasaPy kezdő dátumforrása egyaránt a rácssorrend szerinti első kép, a
relatív mód és a beállítás meg nem jegyzése is egyezik. Az egyképes cím
egyezik; az egyképes eredeti végrehajtás közvetlen cél-FILETIME-t ad át, a
PicasaPy relatív képlete pedig az azonos kezdő időből ugyanarra a célidőre jut.

A PicasaPy ablak modális és 540 széles (`AdjustTimestampDialog.qml:25-29`);
az eredeti leíró `width="fit"` értéket ad, modális jelzőt nem tartalmaz.
Ez a leírók közti eltérés önmagában nem bizonyítja a tényleges natív
ablakszélesség vagy modalitás különbségét.

### 3. Fájlrendszer, `.picasa.ini`, index és nézet

| Hatás | Eredeti Picasa 3.9 | Jelenlegi PicasaPy |
|---|---|---|
| **JPEG EXIF** | A rekord `0x37` tulajdonságát (`0x004906f7`, `0x00490d3c`) állítja, ami EXIF `0x9003` `DateTimeOriginal`. A `0x009ed330` íróút a `0x009eb290` tempfájlos ága; a csere `0x00994400`. | A `timestamp_controller.py:74-123` a forrás JPEG EXIF `0x9003` mezőjét ideiglenes fájlon át cseréli. A `timestamp_controller.py:248-305` siker esetén újraszkenneli a mappát. |
| **Fájlidők** | A `0x009eb290` a `0x00ab35e0`-t a 0x009f05c0 és 0x0098bc10 sikeres (0) visszatérése után hívja, még a temp-kimenet (`0x009ec530`) és csere (`0x00994400`) előtt. Ebből nem igazolt, hogy a helper a `DateTime` (`0x0132`) értéket írja a fájlidőkre, vagy hogy a #7154 hibás mintáin ezen az ágon továbbjutott. A `0x00ab34d0`/`SetFileTime` szerepének ezt a helyet érintő kapcsolata is nyitott. Hibás EXIF-írás után a `0x00992780` létrehozásiidő-ág külön út. | Sikeres JPEG-írás után a `timestamp_controller.py:197-208` visszaállítja a korábban mentett hozzáférési és módosítási időt, Windowson a létrehozási időt is. Sikertelen írásnál `:179-194` Windowson a létrehozási időt próbálja állítani; más platformon nincs létrehozásiidő-írás. |
| **Videó és nem JPEG** | A háttérfeldolgozó a `0x0049070a` és `0x00490d4f` címen a `thumbindex` típusmezőjét vizsgálja. Csak a 2-es típus megy EXIF-ágra; a videók mért típusai 8, 10 és 11, ezért a nem-EXIF ágra mennek. A `0x00992780` a fájl létrehozási idejét, a `0x004ef3c0` vagy `0x004ef5a0` a `thumbindex.db` rekord első FILETIME-ját írja és piszkosnak jelöli (`pmp-database.md:4167-4218`). | A videó/nem JPEG EXIF-írása hibára fut, majd a `timestamp_controller.py:290-305` az effektív dátumot a SQLite `photos.taken_at_override` mezőjébe írja. A fájlrendszer létrehozási idejét csak Windowson próbálja állítani (`:131-176`). |
| **`.picasa.ini`** | A vizsgált `0x0057d7f0` → `0x0077cfd0` → háttérfeldolgozó/író lánc a forrásfájl EXIF-ét vagy a `thumbindex` rekordot kezeli; a pásztázás nem talált `.picasa.ini` író hívást ebben a láncban. Ez csak erre a műveletre szól. | A `timestamp_controller.py:248-308` EXIF-et, indexfelülírást és mappaszinkront használ; nem hív ini-író API-t. |
| **Index, mappadátum, rács** | A nem-EXIF ág `thumbindex` dátummezője igazolt. A sikeres JPEG után az eredeti adatbázis- és rácsfrissítés pontos végállapota, a mappafa és a kijelölés nem dőlt el. **NINCS MEG.** | A `sync_photos.py:202-242` a `taken_at_override` értéket felhasználva újraszámolja az indexelt mappadátumot. A `timestamp_controller.py:308-320` a végén `_refresh_view()`-t hív. A kiválasztott rácssor megőrzése nem következik ebből. |
| **Időrend** | A dátummódosító utáni időrendi végállapotot az átvizsgált bináris út nem dönti el. **NINCS MEG.** | A dátumművelet nem hív `syncFinished` jelet (`timestamp_controller.py:308-320`). Az időrend-vezérlő erre a jelre van kötve (`application_startup_controllers.py:270-274`), és saját `reload()`-ja újraolvassa az indexet (`timeline_controller.py:213-229`). Dátummódosítás közben nyitott időrend frissítése nincs igazolva. |
| **Visszavonás** | A dátumkezelő és a két dátumíró worker nem vesz fel visszavonási adatot (`0x0057d7f0`, `0x00490580`, `0x00490c10`). Az eredeti Szerkesztés menüben nincs általános Visszavonás parancs; a Kép menü „Undo All Edits” kezelője szerkesztési kulcsokat töröl, nem állítja vissza a `DateTimeOriginal` vagy a `thumbindex` dátumát (`picasa-menusor-csoportok.md:191-218`, #7009: `0x005ef3e0`, `0x005ef6b0`). A vizsgált eredeti felhasználói út tehát nem visszavonható. | A `timestamp_controller.py:248-320` nem hív dátumművelethez tartozó visszavonót. A `undoBatchEdit` a szerkesztési láncot állítja vissza (`batch_effect_controller.py:470-532`), nem a dátumot. | Egyezik abban, hogy a dátummódosító saját visszavonást nem biztosít. |

Az eredeti `.picasa.ini`-re vonatkozó negatív állítás a dátumművelet
hívásláncára korlátozott, nem a Picasa egészére. A PicasaPy EXIF-siker
esetén az index újraolvasása veszi át az új `DateTimeOriginal` értéket;
írási hiba, videó vagy nem JPEG esetén a külön indexfelülírás marad
érvényben (`timestamp_controller.py:283-305`).

### 4. Írási hibák, írásvédelem és részleges végrehajtás

Az eredeti `0x00490580` és `0x00490c10` háttérfeldolgozója képenként járja be a kijelölést.
Ha az EXIF-író (`0x009ed330`) nem ad sikeres eredményt, a háttérfeldolgozó a
`0x00992780` fájlidő-ágra lép; a nem-EXIF tartalék az adott támogatott
típusnál a `0x004ef3c0` vagy `0x004ef5a0` rekordmódosítót is meghívja.
A következő kijelölt elem feldolgozása folytatódik. Visszagörgető hívást
nem találtam, ezért a bináris útban részleges siker lehetséges. A
`0x00992780` és a `0x004ef3c0`/`0x004ef5a0` visszatérési értékét a két worker
nem ellenőrzi; a vezérlés a következő kijelölt elemre lép. Ezekben a munkaszál-ágakban
explicit hibaüzenet-küldés nem látható, de a Windows-felületen megjelenő
pontos jelzést és a tényleges fájl/katalógus állapotot futásmérés nélkül nem
állítom.

Az eredeti kódágban külön írásvédettség-előellenőrzést nem azonosítottam.
Az, hogy egy Windows `readonly` attribútum vagy mappaszintű engedély mellett
az EXIF-csere, a `SetFileTime`-tartalék és a katalógusírás közül melyik
sikerül, csak a tényleges Picasa 3.9 futás és előtte/utána fájl- és
az adatbázis vizsgálatával dönthető el. **NINCS MEG.**

A PicasaPy-ban az EXIF-kivétel kezelt tartalékág: `taken_at_override`-t ír
(`timestamp_controller.py:179-194, 283-305`). A háttérköteg soros; egy
nem kezelt fájl- vagy adatbázishiba megállítja a hátralévő munkákat, a
korábbi fájlírásokat nem vonja vissza, hibát jelez, majd a folyamatablakot
lezárja (`photo_ops_write_core_mixin.py:99-140`,
`timestamp_controller.py:308-320`). Így részleges végrehajtás itt is
lehetséges. Fájlattribútummal írásvédett fájlnál az ideiglenes fájl vagy csere hibájának
tényleges oka a fájl- és mappaengedélytől függ; a kód nem vizsgál külön
attribútumot előre.

### 5. A két független út

- **A út, a hívóhely és konstruktor utasításszintű olvasása:** a
  `0x0057d894`-ben betöltött `+0x6c` értéket a hívó a veremre teszi, majd a
  `0x0057d91b` a `0x0077c670` hívás előtt az EDI-t a katalógus `+0xc4`
  kimeneti rekordjára állítja. A konstruktor ezen a mutatón keresztül tölti
  be a kezdő dátummezőt. Ez az út a dátumértéket azonosítja, a lista sorrendjét
  nem feltételezi.
- **B út, külön feltárt kijelölési lánc:** a `0x007166c0` a kijelölt,
  látható elemeket rácsindex szerint adja, a `0x00506500` pedig megőrzi a
  bemeneti sorrendet és a feloldott első elem kerül a lista elejére
  (`referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt`, #418;
  `2026-11-16-7022-7031-7033-colab-decomp.txt`, #424). Ez az út a sorrendet
  azonosítja, nem használja a kezdő dátumra vonatkozó A út következtetését.
  A PicasaPy forrás külön ellenőrzése (`AdjustTimestampDialog.qml:65-69`)
  ugyancsak a számszerű sorindex szerinti első sort használja.
- **Külön felületi mérés:** a `Colab EN 28` képernyőn a relatív mód van
  kiválasztva, a `runtime/offsettime.fen` ezt teszi első rádiónak. A
  `0x00638990` Tulajdonságok-lista menüépítő a `0x37` tulajdonsághoz adja a
  `0x9e0e` parancsot; a `pmp-database.md` 15.1-15.2 szakasza a videós ág
  `thumbindex` első FILETIME-ját azonosítja.
- **Egyezés:** az A bináris hívóhely/konstruktor út és a B kiválasztási
  sorrend út egyezik: a párbeszéd dátummezőjét a rácsindex szerinti első
  kijelölt kép katalógusadata tölti, ahogy a PicasaPy rendezett
  `photoRows[0]` értéke is. A PicasaPy jelenlegi forrása ezt közvetlenül is
  alátámasztja. A külön Tulajdonságok-menü és katalógusrekord-út egyezik a
  `0x9e0e` művelet, a `0x37` EXIF-tulajdonság és a nem-EXIF katalógusmező
  tekintetében. Az eredeti Tools menü engedélyezése, a natív ablak és a siker
  utáni látható állapot futásmérést igényel.

### 6. Cáfoló kísérlet

Megpróbáltam cáfolni azt, hogy külön dátum gyorsbillentyű vagy további
közvetlen helyi menüparancs tartozik a `0x9e0e` kódhoz. A `paszta.py`
`memoria_kapu()`-ja után a lineáris `.text` pásztázás 2 884 879 utasítást
vizsgált: a közvetlen `0x9e0e`/felirat operandusai csak a `0x00559150`
menürekord-építőben és a `0x00638990` tulajdonságmenüben jelentek meg.
Az ellenpróbát külön erőforrás- és rekordlistával ellenőriztem: a
`SHORTCUTS.XML` 48 elemében nincs dátum/adjust/timestamp rekord, a
`0x00559150` 32 menü gyorsbillentyű-rekordjában pedig nincs `0x9e0e`.
Ezek a kontrollok a közvetlen kötést cáfoló alternatív keresést azonos
mércével, a bináris közvetlen címekre és az erőforrás teljes rekeszszámára
ellenőrizték. Az ellenpróba az erőforrás teljes rekeszszámát és a közvetlen
bináris hivatkozásokat vizsgálta, ezért nem az index negatív találatára épül.
A `&Date` felirat menü-mnemonikája ettől külön marad.

A korábbi dátumforrás-olvasatot is cáfoltam: ha a `CThumbUI+0x50` objektum
`+0x6c` értéke volna a kezdő dátum, a konstruktor ezt az értéket használná.
A hívóhelyen viszont a `0x0057d91a` ezt külön argumentumként veremre teszi,
majd a `0x0057d91b` az EDI-t átállítja a katalógus `+0xc4` rekordjára; a
`0x0077c670` az `unaff_EDI[0..1]` rekordpárt olvassa. Ezt a cáfolatot a
Ghidra konstruktorleírás és a hívóhely Capstone-utasításai egymástól
függetlenül támasztják alá. A lista sorrendjére irányuló külön ellenőrzés
(`0x007166c0`, `0x00506500`) és a jelenlegi QML számszerű rendezése szintén
megcáfolja a régi kattintási sorrend állítást. A 15.2/b szerinti ellenpróba
tehát ugyanazon bizonyítékmércével ellenőrizte a régi állítás cáfolatát.

### 7. A kérdés „Kész, ha” pontjai

A megadott jegyszöveg négy kérdést sorol fel, külön „Kész, ha” felsorolást
nem ad. Ezek alapján:

1. ⛔ **Belépési pontok és feltételek:** Eszközök menü és Tulajdonságok-lista
   helyi menü címmel bizonyított (`0x00559150`, `0x005cb990`,
   `0x00638990`); a jelenlegi PicasaPy Tulajdonságok-menü is megvan
   (`PropertiesPanel.qml:165-169, 194-205`). Külön dátum gyorsbillentyű nincs
   az erőforrásban; az eredeti Tools menü néző/tálca/üres kijelölés melletti
   állapota és az írásvédettségi kimenet nyitott.
2. ⛔ **Ablak, alapértékek és megjegyzés:** a mezők, módok, OK/Mégse,
   elemszámos cím, a kezdő relatív mód és a megjegyzés hiánya ismert
   (`0x0077c7c0`, `0x0077c670`, `0x0077cd50`, `0x0077cee0`; mérés:
   `Colab EN 28`). A kezdeti dátum a rácssorrend első kijelölt eleméből jön
   (`0x0057d8f3`, `0x0057d91b`, `0x0057d923`, #402-403, #418, #424), a
   PicasaPy is a rendezett első sort használja. A natív ablak mérete és
   modális viselkedése mérendő.
3. ⛔ **Hatás és visszavonás:** a JPEG `DateTimeOriginal`, a nem-EXIF
   `thumbindex` és fájlidő ág, az `.ini`-kulcs hiánya és a visszavonás hiánya
   igazolt. A JPEG index, a rácssorrend, a mappafa és az idővonal siker utáni
   tényleges állapotát még mérni kell.
4. ⛔ **Írásvédelem és részleges hiba:** a hibás EXIF-írás a tartalékágra
   lép, a soros háttérfeldolgozó továbblép és visszagörgetés nem látszik
   (`0x00490580`, `0x00490c10`). A fájlattribútum, a mappa jogosultsága,
   a pontos hibaüzenet és a részleges Windows-futás eredménye nincs megmérve.

### 8. Javasolt fejlesztői jegytörzs

#### A Tulajdonságok panel dátumsorának helyi menüje (már megvalósítva)

**Eredeti:** a `0x00638990` a `PropertiesListItem` `0x37` típusú
`DateTimeOriginal` sorához (`0x9003`) hozzáadja a `0x9e0e` Dátum és idő
beállítása parancsot. A `0x00637fa0` hívja ezt a helyi menüépítőt.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00638990`: `0x37` tulajdonságsorhoz a `0x9e0e` műveletet adja. | `PropertiesPanel.qml:165-169, 194-205`, `MainRightDrawer.qml:150-154`, `PhotoViewerRightPanels.qml:43-47`: a dátumsor jobb kattintására az adott kép dátumállítója nyílik. | **Nincs teendő.** A helyi menü a jelenlegi forrásban megvan, és az adott sorral nyitja a párbeszédet. |

**Állapot:** teljesült a forrásban; más tulajdonságsorhoz nem kapcsolódik a
dátummódosító menütétel.

#### Fájlidő-jegyjelölt: visszavonva (#7154, pontosítva #7266)

**A korábbi állítás nincs meg:** a meglévő bizonyíték nem igazolja, hogy a `0x00ab35e0` az EXIF `DateTime` (`0x0132`) értékét írja a fájl hozzáférési és módosítási idejére. A `0x009eb290` a `0x1c` kulcsot keresi a dátum-munkaszál táblájában; a `0x009f05c0` hiányzó kulcsnál 9-et ad, a munkaszál táblájában pedig csak a `0x37` kulcs kerül be. Emiatt a `0x0098bc10` és a `0x00ab35e0` ezen az úton nem fut. Ez a feltétel nem állítja meg a későbbi temp-kimeneti és csereágat, ezért a #7154 változatlan JPEG-jeinek tényleges hibapontja továbbra is nyitott. **A korábbi, `DateTime`-ra állító fejlesztői jegyjelöltet nem indítom; új Eredeti/Nálunk eltérés és kész recept nincs bizonyítva.** Következő vizsgálati címek: `0x009ed330` hívóágai, `0x009eb820` előkészítője és `0x009ec530` temp-kimeneti ága.

> **Mérés, 2026-11-18 (#7154, Colab, Wine, angol 3.9.141).** Egy EXIF nélküli JPEG dátummódosítása után a fájl 727 bájttal nő: EXIF (`Software`=`Picasa`, `ExifVersion`=`0220`, `DateTimeOriginal`), XMP (`exif:DateTimeOriginal`) és IPTC (`DateCreated`, `TimeCreated`, `0x0425` MD5) szegmens keletkezik. `DateTime` (`0x0132`) és `DateTimeDigitized` nem íródik. A második módosítás az így EXIF-essé vált fájlon is lefut (előre és visszafelé), mindhárom helyet frissíti, a méret nem változik. A módosítási idő mindkét módosítás után a régi marad; a hozzáférési idő egy módosítás után a régi, a második után az írás ideje (= ctime); az állapotváltozási idő a módosítás ideje. A fájlidő tehát nem az új dátumra és nem a `DateTime`-ra áll. Az `idorend` minta `DateTime`-os, szintetikus EXIF-es JPEG-jein a módosítás nem érvényesül (fájl, EXIF, ctime, megjelenítés változatlan; négy kép, összesen tíz próba), az oka ismeretlen, ezért a `DateTime`-ra állító (`0x00ab35e0`) ág nem megfigyelt. Írásvédett (Linux 0444) EXIF nélküli JPEG módosítása hibaüzenet nélkül lefut, a fájl végül nem írásvédett (Wine; Windowsra nem általánosítható). Időzóna: UTC.

**Következtetés (#7154).** A megfigyelhető esetben a fájlidő nem követi az új dátumot: a módosítási idő megmarad, ahogy a #4927 állította, és ahogy a PicasaPy `timestamp_controller.py:197-208` visszaállítása csinálja. A fenti „kövesse a `DateTime`-ot” jelölt ezért **nem nyit jegyet**. A `DateTime`-os ág oka hívássorrendjét a #7266 tisztázta; a helper-visszatérések további vizsgálata szükséges. Mért eltérés: az eredeti az EXIF mellett XMP és IPTC dátumot is ír, a PicasaPy csak az EXIF `DateTimeOriginal`-t; erre nyílt a #7237.

### 9. Új kutatási jegyjavaslatok

Nincs külön kutatási jegyjavaslat; a lent felsorolt nyitott pontok a 7033
folyamatához tartoznak.

### Ghidra-kiegészítés (2026-11-15, várólista 402-403)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt` (privát
kutatási tár).

- **`0x0077c670`, kezdő mód.** A dátumeltolás ablakának konstruktora és két
  kezelője (`0x0077cee0`, `0x0077cd50`) nem olvas és nem ír megjegyzett
  beállítást. A konstruktor a belső módjelzőt 1-re állítja; a `0x0077cee0`
  ebből `jelző = (érték == 0)` alakban számol vissza, tehát a kezdő állapot az
  `adjust_type` 0. rádiója. A `runtime/offsettime.fen:19-21` sorrendje
  `relative`, majd `absolute`; a meglévő `Colab EN 28` képernyőképen az első,
  relatív rádió van kijelölve. **PicasaPy:** az `AdjustTimestampDialog.qml`
  minden nyitáskor az eltolás rádióját jelöli be (`checked: true`), és nem
  jegyez meg semmit. A kezdő mód és a megjegyzés hiánya egyezik.
- **`0x0057d7f0`, a kezdő dátum adatútja.** A párbeszédnek átadott FILETIME
  a `CThumbUI` vtable `+0x24` helyén meghívott `0x00a6ccf0` getterrel kapott
  objektum `+0x6c` mezőjéből jön (`0x0057d894`-`0x0057d923`). A `0x0057d7f0`
  ettől külön meghívja a katalógus `+0xc4` virtuális helyét a feloldott lista
  első azonosítójával. A #403 ezt a külön katalóguslekérést és a lista első
  elemének kérését rögzíti, de nem bizonyítja, hogy ez az elem adja a
  párbeszéd kezdeti FILETIME-ját. A `0x00506500` nem rendez; a `0x007166c0`
  a kijelölt látható elemeket rácssorrendben adja. Több képnél eltolás,
  egy képnél abszolút célidő kerül a háttérfeldolgozónak. A kezdő dátum
  képforrása nyitott, ezért a PicasaPy `photoRows[0]` értékével való eltérés
  nem állítható.

### Ghidra-kiegészítés 2 (2026-11-15, várólista 413-418)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt` (privát
kutatási tár). Ide a 418 tartozik. A `0x005c76b0` törzsét a már meglévő
`2026-11-15-7012-7022-colab-decomp.txt` kimenetből olvastam, nem a 413-418
kötegből.

- **`0x00506500`, rendezi-e a listát (418).** Megválaszolva: **nem rendez.** A
  `param_1` a katalógus (rekordtömb `param_1[0xfc]`, darabszám
  `param_1[0xfd] >> 1`), a `param_2` a bemeneti lista (mutató és darabszám).
  Zárolja a katalógust (`EnterCriticalSection`), majd a lista elemein a
  bemeneti sorrendben halad: a tartományon kívüli azonosítót elhagyja; a rekord
  `+0x18` mezőjét nézi, és ha az `0x3e9`, az azonosítót a rekord `+0x20`
  mezőjével (`piVar2[8]`) cseréli; a már felvett azonosítót nem veszi fel újra
  (az első előfordulás marad). Az eredmény a bemeneti sorrendet követi, és
  helyben felülírja a bemeneti listát. Null listára `4`, egyébként `0` a
  visszatérés. A `0x3e9` jelentése ("hivatkozó" rekord) a fejléc olvasata; a
  kimenet csak a mezőértéket mutatja. Hívói: `0x0057d879` (a `0x0057d7f0`, a
  dátumállító) és `0x007dc704` (`0x007dc4f0`). Következmény: a dátumablak a
  bemeneti lista első, feloldott, tartományban lévő elemének adatát külön
  lekéri; az ablak kezdeti dátummezőjének forrását ez nem azonosítja.
- **A bemeneti lista sorrendje (`0x005c76b0`).** A `0x0057d7f0` a
  `FUN_005c76b0(0,1,1,1)`-et hívja (`0x0057d813`). Mivel `param_1 == 0`: ha a
  `this+0xeac` csoportosított arcnézetet jelző objektumának `+0x3c9` bájtja nem
  nulla, az eredményt annak `0xdc` virtuális metódusa adja; különben a
  `this+0xea8` objektumra hívott `FUN_007166c0(objektum, jelző)` tölti a
  listát (a jelző 1); ha ez üresen hagyja, és a `this+0xe64` nem `-1`,
  egyetlen elem kerül be (`this+0xe68`). A 424 később feloldotta a
  `FUN_007166c0` rácssorrendű bejárását és a `+0x3c9` jelentését; a
  csoportosított arcnézet `+0xdc` céljait a zárókör RTTI- és helyi
  disassembly-ellenőrzése azonosította. **PicasaPy:** a `photoActionRows()` a
  `selectedRows()` útján a `selectedIndexes` tömböt adja
  (`MainLibrarySelectionState.qml:70-78`, `selection.js:32-36`), úgy, ahogy a
  kattintások építették: a Ctrl+kattintás a végére fűz (`selection.js:7-12`), a
  Shift+kattintás növekvő tartományt ad (`selection.js:15-21`). Az
  `AdjustTimestampDialog.qml:66` a `photoRows[0]` elemet használja, tehát a
  **kattintási sorrend** első elemét, nem a rács szerinti elsőt (a "Locate on
  Disk" ezzel szemben szándékosan rácssorrendet használ, `selection.js:38-46`).
  A 2026-11-16-i 424 kimenet a lista rácssorrendjét lezárta. A lista első
  eleme és a párbeszéd kezdő FILETIME-ja közötti kapcsolat nem dőlt el; a
  kattintási sorrendből eredő #7054 eltérés ezért mérés nélkül nem állítható.

**Korábbi állapot a 418 után:** a jegy ekkor még nem volt zárható. Ez a tábla
köztes állapotot rögzít; a friss státuszt a `### 10. Nyitott` és a
`### Zárási döntés` adja.

| Pont | Állapot a 413-418 után | Miért |
|---|---|---|
| 1. Belépési pontok és feltételek | ⛔ | A 418 nem érinti: a néző- és tálcakapu, az írásvédettségi kapu nyitott. |
| 2. Ablak, alapértékek és megjegyzés | ⛔ (közelebb) | A lista első eleme és a "nem rendez" megvan; a lista sorrendje (`FUN_007166c0`) és a rádió sorrendje (`offsettime.fen`) nyitott. |
| 3. Hatás és visszavonás | ⛔ | A 418 nem érinti: index, rács, mappafa, időrend, Undo nyitott. |
| 4. Írásvédelem és részleges hiba | ⛔ | A 418 nem érinti: Windows-mérés kell. |

Új fejlesztői jegyet a 418 nem indokol; a meglévő jegytörzs (a Tulajdonságok
panel dátumsorának helyi menüje) változatlan. Ha a `FUN_007166c0` rácssorrendet
ad, a `photoRows[0]` használata új eltérés-jelölt lesz.

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 424 tartozik. A `0x005c76b0` törzse ebben a kimenetben is
szerepel; a 418 még a `2026-11-15-7012-7022-colab-decomp.txt` kimenetből
olvasta.

- **`0x007166c0`, a lista töltője (424).** Megválaszolva: **a lista
  rácssorrendű, nem kattintási sorrendű.** A `FUN_007166c0(nézet, jelző)` a
  kimeneti listát előbb üríti, előkészítést hív (`FUN_0071c8c0`; ha a nézet
  `param_1[0xb3]` mezőjének (`+0x2cc`) bájtja nem nulla, a `+0xc4` virtuális
  metódust is), majd az elemeket
  **index szerint, 0-tól a darabszámig** járja be (a nézet `+0xb4` metódusa a
  darabszám, a `+0xb8` az `i`. elem). Az első bejárás azokat az elemeket
  gyűjti, amelyeknek a `+0x5d` bájtja nem nulla és a `+0x5a` bájtja nulla, és az
  elem `+0xb4` mezőjét (azonosító) fűzi a listához, a bejárás sorrendjében. Ha a
  jelző be van kapcsolva, és az első bejárás után a lista üres, a második
  bejárás az összes olyan elemet gyűjti, amelynek a `+0x5a` bájtja nulla (a
  `+0x5d` ekkor nem számít). Visszatérés: `0`, memóriahibánál `4`. A `+0x5d`
  (kijelölt) és a `+0x5a` (rejtett) jelentés a fejléc olvasata, a kimenet csak
  a bájt vizsgálatát mutatja. A kimenetben a kattintások sorrendjét tároló lista,
  időbélyeg vagy sorszám sehol nem szerepel: **a kattintási sorrend ebből az
  útból nem származtatható.**

  A hívó `FUN_005c76b0`: a `this+0xea8` nézetre hívja, a jelző `1`, ha ez a
  nézet azonos a `this+0xea4` nézettel, vagy a `param_2` nem nulla (a
  dátumállító útján `FUN_005c76b0(0,1,1,1)`, a 418 szerint, tehát `1`). Ha a
  `this+0xeac` objektum `+0x3c9` bájtja nem nulla, a lista nem a nézetből, hanem
  az objektum `+0xdc` metódusából jön. A `picasa-arcfelismeres.md:839-845`
  ezt a jelzőt csoportosított arcnézetként azonosítja. A bináris-index
  `rtti.csv` szerint a `CFoundFaceSelectionNode` `+0xdc` célja `0x0078a6c0`,
  amely a kijelölt csoportok gyermek-képvektorait fűzi a kimenethez;
  a `CAlbumSelectionNode` megfelelő célja `0x00401570`, üres eredménnyel.
  Ha a nézet nem ad elemet, és a `this+0xe64` nem `-1`, egyetlen elem kerül be
  (`this+0xe68`). A csoportosított arcnézethez tartozó út tehát nem marad
  ismeretlen virtuális hívás.

  **Következmény:** a kijelölési lista a nézet **index szerinti első
  kijelölt képével** kezdődik, a Ctrl+kattintások sorrendjétől függetlenül.
  Ebből nem következik, hogy a párbeszéd kezdő dátummezője ugyanezt az időt
  használja: annak FILETIME-ja a `CThumbUI+0x50` objektum `+0x6c` mezőjéből
  érkezik. Kijelölés nélkül
  (jelző `1`) a lista nem üres: az első nem rejtett elem kerülne elő; hogy a
  parancs kijelölés nélkül elérhető-e, a belépési kapun múlik, ami nyitott.
  **PicasaPy:** az `AdjustTimestampDialog.qml:65-66` a `photoRows[0]` elemet
  használja, ez a kattintási sorrend első eleme: a Ctrl+kattintás a végére fűz
  (`selection.js:7-12`), a Shift+kattintás növekvő tartományt ad
  (`selection.js:15-21`), és a `photoActionRows()` ezt a tömböt adja
  (`MainLibrarySelectionState.qml:29-32`, `:72-80`). Példa: az 5. kép, majd
  Ctrl+kattintással a 2. kép kijelölése után a PicasaPy a kattintási sorrend
  szerinti első, vagyis az 5. kép idejéből indul. Az eredeti kezdő mezőjének
  képforrása nem bizonyított; a rácssorrendből nem következik, hogy a 2. kép
  idejét mutatja. A #7054 fejlesztési javaslat ezért a futásmérésig visszavonva.
  A rács szerinti rendezésre kész minta van: a "Locate on Disk" a #6995 óta rácssorrendet
  használ (`selection.js:43`, `pathsInGridOrder`). A PicasaPy `openForRows`
  üres kijelölésre nem nyit (`AdjustTimestampDialog.qml:62-64`).

**Korábbi állapot a 424 után:** a jegy ekkor még nem volt zárható. Ez a tábla
köztes állapotot rögzít; a friss státuszt a `### 10. Nyitott` és a
`### Zárási döntés` adja.

**Helyesbítés a zárókörben:** a korábbi köztes következtetés, amely az első
rácssorrendű képet nevezte meg a dátumablak kezdeti idejeként, túlterjeszkedett
a bizonyítékon. A 424 csak a kijelölési lista sorrendjét igazolja; a párbeszéd
FILETIME-ja a `CThumbUI+0x50` objektum `+0x6c` mezőjéből jön. A kezdő mező
képforrása nyitott marad, amíg a kontrollált mérés nem azonosítja.

| Pont | Állapot a 419-425 után | Miért |
|---|---|---|
| 1. Belépési pontok és feltételek | ⛔ | A Tools és Properties út, valamint a gyorsbillentyű hiánya megvan. Az eredeti néző/tálca/üres kijelölés menüállapota és az írásvédettségi kimenet még mérendő. |
| 2. Ablak, alapértékek és megjegyzés | ✅ (téves köztes állapot, később helyesbítve) | A 424 a kijelölési lista rácssorrendjét igazolta, nem a párbeszéd kezdő dátumának képforrását. A kezdő `FILETIME` külön adatútja a `CThumbUI+0x50` objektum `+0x6c` mezője; lásd a közvetlenül alatta álló helyesbítést és a friss `### 10. Nyitott` táblát. |
| 3. Hatás és visszavonás | ⛔ | A közvetlen adattárolás és az undo hiánya megvan; a JPEG index, rács, mappafa és idővonal siker utáni állapota még mérendő. |
| 4. Írásvédelem és részleges hiba | ⛔ | A hibás EXIF-írás tartalékága és a visszagörgetés hiánya megvan; a tényleges Windows üzenet és részleges eredmény még mérendő. |

Az első kép kezdő dátumként való használata most bizonyított; a #7054
eltérésjavaslat nem indokolt. A Tulajdonságok-panel dátumsorának helyi menüje
a jelenlegi forrásban már megvan, ezért az sem nyitott fejlesztői eltérés.

### 10. Nyitott

- **NINCS MEG, egyetlen blokkoló mérési sorozat:** az alábbi nyitott,
  felhasználó által látható pontokat egy elkülönített Picasa 3.9.141.259
  Windows-futás előtte és utána rögzített eredménye dönti el.

| Nyitott tétel | Mit dönt el a meglévő bizonyíték | Státusz és megszerzés |
|---|---|---|
| A kezdeti dátummező melyik kép idejét mutatja. | A `0x0057d8f3` katalógus `+0xc4` lekérése tölti a `0x0077c670` konstruktor által olvasott rekordot; a `0x007166c0` és `0x00506500` alapján ez a rácssorrend szerinti első kijelölt elem. | **Lezárva, statikusan igazolt.** A `0x0057d894`-ben betöltött `+0x6c` külön argumentum, nem a kezdeti `FILETIME`; a hívóhely disassemblyje ellenőrzi az EDI felülírását. |
| Eszközök menü engedélyezése üres kijelölésnél, nézőben és képtálcával. | A kezelő a nézet elemeit és tartalékágban az aktuális képet összegyűjtheti, de ez nem bizonyítja, hogy a menü engedélyezett-e. A dátum Tulajdonságok-helyi menüje igazolt, külön dátum gyorsbillentyű nincs. | **Blokkoló, látható.** Picasa 3.9 felületmérés az Eszközök menü állapotáról üres kijelölés, egy és több kép, néző és csak képtálca állapotban. |
| Az ablak tényleges mérete és modális viselkedése. | A `runtime/offsettime.fen` leíró `width="fit"` értéke nem adja meg a tényleges ablakméretet, és modális jelzőt sem tartalmaz. | **Blokkoló, látható.** A natív Picasa 3.9 párbeszédablak méretét és a főablakra gyakorolt modalitását kell rögzíteni. |
| Siker után a rács, kijelölés, mappafa és nyitott idővonal állapota. | A bináris közvetlen íróutat megmutatja, de nem a főablak frissítésének végállapotát. | **Blokkoló, látható.** Előtte és utána rögzített Picasa 3.9 felületmérés több képpel, nyitva hagyott idővonallal. |
| Fájlattribútummal írásvédett fájl, mappajogosultsági hiba, hibaüzenet és részleges köteg eredménye. | A kódág tartalék írást és továbblépést mutat, visszagörgetést nem; a Windows hibaüzenetét és a tényleges eredményt nem. | **Blokkoló, látható.** Külön írásvédett fájllal és írásra tiltott mappával végzett többképes Picasa 3.9 mérés. |
| A JPEG utáni `thumbindex.db` belső rekord pontos változása. | A közvetlen EXIF írás ismert; a JPEG utáni katalógus-frissítés pontos rekordállapota nem. | **Nem blokkoló.** A belső adatbázissor önmagában nem látható a felhasználónak; a belőle eredő rács-, mappa- és idővonal-változás a fenti mérés része. |

Egyetlen kontrollált mérési sorozat fedje le a fenti blokkoló pontokat.
Rögzítendő az Eszközök menü állapota üres kijelölésnél, egy és több kép,
néző és csak képtálca mellett; az ablak mérete és modális viselkedése; a
módosítás előtti és utáni EXIF, fájlidők, rácssorrend, kijelölés, mappafa,
nyitott idővonal, pontos hibaüzenetek és a részleges végállapot. A sikeres
egyképes és többképes utat, az írásvédett JPEG-et, az írásra tiltott mappát
és a videó bemenetet is vizsgálja a sorozat. A párbeszéd kezdő dátumának
forrását nem kell ezzel a méréssel eldönteni; statikusan igazolt. A méréshez
Windowsos Picasa 3.9 környezet kell; a
jelenlegi helyi gépen az eredeti PE32 bináris olvasható, de sem `wine`, sem
`wine64` futtató nincs elérhető. Új Ghidra-kör nem szükséges.
- **NINCS MEG, nem blokkoló:** a megadott mérőadat-archívumban nincs
  dátummódosítási munkamenet (`adjust`, `timestamp`, `offsettime` névvel
  jelölt tag nincs). Ez a felhasználói viselkedésen nem változtat; a fenti
  kontrollált Windows-mérés a szükséges forrás.

### Zárási döntés

**A #7033 jelenleg nem zárható.** Egyetlen blokkoló maradt: a fenti,
elkülönített Picasa 3.9 Windows-mérési sorozat. Ghidra-kör nem kell; a
kezdő dátum képforrása statikusan igazolt. Fejlesztői eltérésjelölt az
eredeti JPEG fájlidő-kezelése; a Properties dátumsorának helyi menüje a
jelenlegi forrásban már egyezik.

### Hívói helyesbítés a zárókörhöz (2026-11-16): a kezdő dátum forrása igazolt, a #7054 áll

A zárókör a kezdő `FILETIME`-ot a `CThumbUI+0x50` objektum `+0x6c` mezőjének
tulajdonította. Ez téves: az a 4 bájtos érték a `0x0077c670` első paramétere
(`param_1`, a `FUN_009a5620` kapja), nem időpont. A hívóhely disassemblyje:

- `0x0057d8f3`: a katalógus `+0xc4` virtuális metódusa a lista **első** elemére
  (`*local_12c`) tölti ki a veremrekordot;
- `0x0057d8f5`-`0x0057d910`: a rekord 8 bájtja az `[esp+0x18]`/`[esp+0x1c]`
  helyre kerül;
- `0x0057d91b`: a négy argumentum után a `lea edi, [esp+0x28]` épp erre a
  8 bájtra mutat;
- `0x0077c670`: az `unaff_EDI[0]`/`[1]` kerül az `in_EAX[0x32..0x35]` mezőkbe,
  ez a párbeszéd kezdő ideje.

A kezdő dátum tehát a kijelölési lista első elemének (a 424 szerint a rács
szerinti első kijelölt képnek) az ideje. A #7054 (a dátumablak a rács szerinti
első kép dátumával nyílik) helyes, **nem vonjuk vissza**; a fenti mérési
sorozat erre a kérdésre nem kell. A zárási döntés blokkolója ezzel megszűnt;
a megmaradt mérési pontok (írásvédett fájl üzenete, siker utáni idővonal) a
felhasználó számára látható viselkedést érintik, de egyik sem a kezdő mezőé.

### Zárókör (2026-11-17): a megmaradt tételek döntése

Az alábbi audit a korábbi Ghidra-kiegészítések történeti állításait nem vonja
össze és nem törli. Ahol a régi bekezdés a `CThumbUI+0x50` `+0x6c` mezőt nevezi
kezdő dátumnak, vagy nyitva hagyja a képforrást, ott a jelen zárókör a közvetlen
hívóhely disassemblyjével ellenőrzött `unaff_EDI` adatátvétel az irányadó.

| Korábbi `NINCS MEG` vagy nyitott állítás | Újraellenőrzés eredménye és forrás | Státusz |
|---|---|---|
| A dátumablak kezdő dátumának képforrása. | `0x0057d8f3` a feloldott lista első elemétől kéri a katalógus `+0xc4` adatot; `0x0057d91b` az EDI-t az ezzel kitöltött rekordra állítja a `0x0077c670` hívása előtt. A konstruktor `unaff_EDI[0..1]` értékét teszi a dátummezőbe. A `0x00506500` megőrzi a sorrendet, a `0x007166c0` rácsindex szerint adja a kijelölést. | **Lezárva.** A rácssorrend szerinti első kijelölt kép ideje. A `+0x6c` nem a dátummező forrása. A PicasaPy `AdjustTimestampDialog.qml:65-69` a sorindex szerint rendezett első képből indul. |
| Tulajdonságok dátumsorának helyi menüje. | Eredeti `0x00638990`; jelenleg `PropertiesPanel.qml:165-169, 194-205`, `MainRightDrawer.qml:150-154`, `PhotoViewerRightPanels.qml:43-47`. | **Lezárva, egyezik.** Régi eltérésjavaslat nem marad. |
| Eszközök menü üres kijelölésnél, nézőben és képtálcával. | A kezelő bemenetgyűjtése nem bizonyítja a menü engedélyezését. PicasaPy forrása `MainMenuBar.qml:112-114`; eredeti tényleges menüállapotot nem rögzít meglévő mérés. | **NINCS MEG, blokkoló és látható.** Picasa 3.9 Windows felületi mérés kell az egyes állapotokban. |
| Párbeszéd tényleges mérete és modalitása. | Az eredeti `offsettime.fen` `width="fit"` leírása nem adja meg a natív méretet vagy modalitást. PicasaPy forrásban a `modal: true`, `width: 540` (`AdjustTimestampDialog.qml:25-29`), ami nem bizonyítja az eredeti futási értéket. | **NINCS MEG, blokkoló és látható.** Natív Windows párbeszédablak mérése kell. |
| Siker utáni rács, kijelölés, mappafa és idővonal. | PicasaPy újraszkenneli a mappát és frissíti a nézetet (`timestamp_controller.py:308-320`, `sync_photos.py:202-242`); az időrend újratöltése `syncFinished` jelhez kötött (`application_startup_controllers.py:270-274`), amelyet a dátumkezelő nem bocsát ki. Az eredeti látható végállapot nincs a bináris íróútból eldöntve. | **NINCS MEG, blokkoló és látható.** Előtte-utána Windows felületi mérés kell, nyitva hagyott időrenddel. |
| Írásvédett fájl, mappajogosultság, hibaüzenet és részleges köteg. | A két eredeti worker hibás EXIF után fallbacket hív, a fallback és katalógusmódosítás visszatérését nem ellenőrzi, majd továbblép; visszagörgetés nem látható (`0x00490580`, `0x00490c10`, `0x00992780`, `0x004ef3c0`, `0x004ef5a0`). A tényleges Windows fájl- és indexállapot, illetve a látható hiba nem állapítható meg futtatás nélkül. | **NINCS MEG, blokkoló és látható.** Írásvédett JPEG, írásra tiltott mappa és többképes próba kell; rögzítse a pontos üzenetet és a részleges eredményt. |
| A JPEG utáni `thumbindex.db` belső rekord pontos állapota. | A felhasználói hatásait külön sorok kezelik; a belső rekordérték önmagában nem látható. | **NINCS MEG, nem blokkoló.** |
| Dátummódosítási mérőadat-archívum. | A megadott archívum tagnevei között nincs a dátummódosításhoz tartozó munkamenet. | **NINCS MEG, nem blokkoló.** A szükséges hiányzó forrás a Windows-futás. |

Egyetlen célzott mérés dönt el minden nyitott, felhasználó által látható
állítást: Picasa 3.9.141.259 Windows alatt rögzíteni kell az Eszközök menü
állapotát üres, egyképes és többképes kijelölésnél, nézőben és képtálcával; a
párbeszéd méretét és modalitását; egy sikeres dátummódosítás előtt és után az
EXIF-et, fájlidőket, rácssorrendet, kijelölést, mappafát és megnyitott
idővonalat; végül az írásvédett JPEG, az írásra tiltott mappa és a részleges
többképes végrehajtás pontos eredményét. A kezdő dátum képforrását ez a mérés
már nem dönti el. A Ghidra-kimenetek megvannak és a hívóhely megerősíti a
rekordforrást; a #7033 alatt nincs további `Ghidra-kör kell:` tétel.

### Zárási döntés

**A #7033 nem zárható le a jelen bizonyítékkal.** Az egyetlen blokkoló a fenti
egyetlen, összefüggő Picasa 3.9 Windows-mérési sorozat. A kezdő dátum forrása
megerősített két független bináris úttal; a PicasaPy sorindex szerinti
rendezése a forrásban ellenőrzött. A részletes tulajdonságmenü-eltérés és a
#7054 képforrás-eltérés nem marad nyitva.

A korábbi fájlidő-fejlesztői jegytörzs jelöltet a #7154 mérés nem indította el, és a #7266 sem támasztotta alá az `Eredeti` állítását. A `0x009eb290` helper-kapui és hívási sorrendje megvan, de a helper eredménye a sikertelen `DateTime`-os mintákon **NINCS MEG**. A fájlidő-receptet ezért visszavontam; a `0x009f05c0`, `0x0098bc10` és `0x009ec530` hibautak a nyitott következő vizsgálatok.

**Eldöntve (#7154, 2026-11-18):** a mérés a #4927 állítását igazolta (a módosítási idő megmarad), ez a jelölt nem nyit jegyet; részletek a „fájlideje kövesse az eredeti Picasát” szakasz alatti mérésnél.

### #7266-kiegészítés (#496, 2026-11-19): a JPEG dátumíró hívássorrendje

Az `0x009eb290` nem hasonlítja közvetlenül az EXIF `0x0132` mezőt. A `0x009f05c0` a belső metaadat-táblában keresi az `0x1c` kulcsot, és hiányzó kulcsnál 9-et ad. A dátum-munkaszál táblájának felépítése csak az `0x37` (`DateTimeOriginal`, `0x9003`) kulcsot teszi be, ezért a keresés 9-cel tér vissza; az `0x0098bc10` nem fut le, így a `0x00ab35e0` fájlidő-segéd sem. Ha a második segédet meghívják, az `0x0098cfe0` hibájára vagy `local_24 == -1` esetén 3-at ad; a feldolgozott dátum sentinel értékével való egyezéskor -1-et, eltéréskor 0-t ad. Csak a két segéd 0 visszatérése után futna a `0x00ab35e0`. A kihagyott segéd nem korai kilépés: a függvény a temp-kimeneti és csereág felé folytatja. A #7154 tíz sikertelen próbája nem naplózta, hogy az `0x009eb290` belépett-e, illetve hol hibázott az előkészítés, temp-írás vagy csere során. A korábbi, `0x00ab35e0`-t a `DateTime` értékére állítóként leíró mondatot visszavontam. Következő: `0x009ed330` hívóágai, `0x009eb820` előkészítése és `0x009ec530` temp-kimeneti ága.

## #7060: A diavetítés teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldalt a binárisból (statikus olvasás `capstone`-nal, a programot
nem futtattam), a `.tre` erőforrásokból és a hivatalos magyar feliratokból, a
PicasaPy oldalt a jelenlegi forrásból olvastam. A korábbi lapok igazolt
részeire hivatkozom (`picasa-diavetito-sav.md`, `picasa-diavetito-sav-5550.md`,
`picasa-gyorsbillentyuk.md` 12. szakasz, `picasa-idorend-bemutato-kutatas.md`,
`picasa-idorend-viselkedes.md`), nem kutatom újra; ahol ellentmondok nekik,
külön jelzem.

### Következtetés

- **Belépés.** A Nézet ▸ Diavetítés (`0x9c9f`), a felső Mappa/Album menü ▸
  Diavetítés megtekintése (`0x9c6d`), a `Ctrl+4`, a mappa- és albumfejléc `play` gombja és
  a szerkesztő `Play` gombja (a `thumbui/sbutton` álneve) mind ugyanabba a
  függvénybe fut: `0x005e8a70(this, 0)`. Az Időrend (`0x9ccc`, `Ctrl+5`,
  `thumbui/timelinebutton`) ugyanide fut, `1` móddal. A PicasaPy-ban is egyetlen
  indító van (`MainSlideshow.qml:60`). A `0x9c6d` a felső `eMenuLabelFolder`
  menü parancsa, nem a mappa vagy album jobbklikk-menüjéé; az eredeti Folder és
  Album helyi menük teljes leltára, valamint a PicasaPy helyi menüi sem adnak
  diavetítés-parancsot.
- **Fő lelet: két vetítő van, és a normál nem az, amelyikre a korábbi
  összevetések épültek.** A `0x005e8a70` `0` módban, `Shift` nélkül
  (`0x005e8b00`, `0x005e8b0a`) nem a `qshow`/`OneUpUI` vetítőt indítja
  (`0x008037e0`, `oneup.tre`), hanem a főablakba ágyazott szerkesztő-egyképes
  vetítést (`0x0075de50`, `editoneup.tre`). A `qshow` csak az Időrendnél
  (`1` mód) vagy lenyomott `Shift` mellett indul. Ebből következik, hogy a
  `picasa-diavetito-sav.md` és a `picasa-diavetito-sav-5550.md` `oneup.tre`
  szerinti sáv-összevetése, a Timeline gomb láthatósága (#5653) és a
  `picasa-gyorsbillentyuk.md` 12.5-12.9 szakasza a **normál** vetítésre nem
  érvényes. Ugyanez megadja a `+0x332f` bájt által jelölt billentyűmód nevét,
  amely a `paritas-ellenorzes.md:420` szerint eddig `NINCS MEG` volt: a
  normál diavetítés. A #6930 helyesbítése (a szünetbeli sáv a `OneUpUI`
  hostcseréje) ezért csak a `qshow` útra igaz; a normál vetítés
  szünetbeli sávjának forrása nyitott (G3).
- **Mit vetít.** Az aktuális nézet (`[this+0xea8]`: mappa, album, keresés
  eredménye) minden olyan elemét, amelynek `+0x5a` jelzője nulla, az aktuális
  képtől indulva; a kijelölés nem szűri a listát, és kijelölés nélkül az
  első elem lesz kijelölve (`0x00717bb0`). Üres nézetnél hang és üzenet nélkül
  nem történik semmi. A PicasaPy ugyanezt teszi (a teljes `controller.photos`
  listát vetíti), a **videó** kivételével: az eredeti a videót is
  lejátssza, a vágási pontok (`moviestart`, `movieend`) átadásával, és a dia
  ideje a film hossza; a PicasaPy kihagyja őket.
- **Vezérlők és alapértékek.** A dia ideje `SlideshowEffectTime` (alapérték
  `3`, `+`/`-` után `1` és `20` közé szorul), az ismétlés `LoopSlideshow`
  (alapérték ki), a zene `PlayMP3Tracks` (alapérték be), az átmenet
  `ThumbUISlideShow::transition` (hét elem, alapérték Dissolve). Ezek és a
  megőrzésük a PicasaPy-val egyeznek. Eltérések: (1) az eredeti normál
  vetítésben nincs Timeline gomb, a PicasaPy-ban van; (2) a `Fel`/`Le`, az
  `1`-`9`, valamint a `Pause`/`Play` már a jelenlegi PicasaPy-forrásban is
  megvan; az eredeti normál vetítésben a `Enter` és `Ctrl+R` nincs bekötve,
  nálunk viszont továbblépést, illetve forgatást végez (G6); (3) a kézi
  léptetés a lista
  szélén: az eredetiben előre az utolsó képről az elsőre fordul (a
  `LoopSlideshow`-tól függetlenül), hátra az első képen nem lép
  (`0x00717eb0`, utasításszint), nálunk hurok nélkül előre kilép, hurokkal
  hátra az elsőről az utolsóra fordul; (4) az `auto2` kattintási terület a
  `.tre` szerint a kép szinte egésze, nálunk 14 képpontos sáv (feltételes).
- **Kilépés.** `Esc` vagy a `Kilépés` gomb: a kurzor visszatér, a zene leáll,
  és a program oda tér vissza, ahonnan indult (szerkesztő, ha ott volt, különben
  a könyvtár). Mivel az aktuális elem és a nézet kijelölése együtt mozog (`0x005704d0` →
  `0x00717c50`; a kézi léptetésnél `0x00717eb0`), az utoljára látott kép marad
  kijelölt és aktuális (az automatikus léptetés útja feltételes, G1). Tárolt adatot a kilépés nem ír.
  A PicasaPy ezzel egyezik (`MainSlideshow.qml:92-114`).
- **Rejtett, sérült, elérhetetlen kép.** A `+0x5a` jelzőjű elemet a lista
  kihagyja; hogy ez a jelző a rejtett képet jelenti-e, és mi történik betölthetetlen
  vagy hálózati úton elérhetetlen fájllal, a binárisból még nem dőlt el
  (9. szakasz).

### Bizonyítottsági fok

**Feltételes.** A belépési hívások, az elágazás és a két vetítő szétválasztása
két független útból igazolt (a 7. szakasz), de futásmérés nincs: a #375 Colab-
felvétel a `Ctrl+4`-et és a `Space`-t mérte, a vezérlősáv alakját nem
különítette el. Megerősített: a belépési táblázat és a `Shift`-elágazás
utasításai. Feltételes: a `0x0075de50` ág "normál vetítés" azonosítása, a
videó lejátszása, a nézet-bejárás szabályai. `NINCS MEG`: a 9. szakasz tételei.

### 1. Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Nézet ▸ Diavetítés.** A `0x00559150` rekordja `0x9c9f` (`picasa-menu-parancsok.csv:181`). **Felső Mappa/Album ▸ Diavetítés megtekintése.** A `0x00559150` `eMenuLabelFolder` rekordja `0x9c6d` (`:74`); az `eMenuLabelFolder` a menüsáv Mappa menüosztálya (`picasa-menu-parancsok-viselkedes.md` 30. adag), Album-nézetben a cím Albumra vált. A `0x005cb990` mindkét azonosítót a `0x005cbbd1` közös ágára küldi, amely `0x005e8a70(this, 0)`-t hív (`0x005cbbd3`). | `PicasaViewMenu.qml:174-178`, `PicasaFolderMenu.qml:9,30-34`, `PicasaMenuBar.qml:739-743`, `MainMenuBar.qml:366`, `MainWindowCommands.qml:451-452`, `MainSlideshow.qml:60-71` | Egyezik: mindkét felső menütétel ugyanazt a műveletet indítja. A `0x9c6d` nem helyi menüparancs. |
| **Mappa/Album helyi menüje (jobb klikk).** A teljes Folder-építő (`0x007319f0`, a `picasa-menu-parancsok-viselkedes.md` 32.1-ben felsorolt 18 tétel) és az Album-építő (`0x00732160`, 1081 B; célzott disassembly) nem tartalmazza az `ID_ALBUM_SLIDESHOW` / `0x9c6d` parancsot. A `0x9c6d` a felső menüé; az a korábbi állítás, hogy helyi menüpont, a 30. adagban helyesbített téves besorolás. | `FolderContextMenu.qml`, `AlbumContextMenu.qml` (a két QML helyi menüben nincs slideshow tétel); a felső menü külön `PicasaFolderMenu.qml:30-34` | Egyezik: a mappa és album jobbklikk-menüje egyik rendszerben sem indít diavetítést; nincs fejlesztői teendő. |
| **`Ctrl+4`.** A `0x005e60d0` `0x005e625e`-`0x005e626f` ága: `call 0x005696c0` (kapu), `push 0`, `push ebp`, `call 0x005e8a70`. A `Ctrl+5` ugyanitt `push 1` (`0x005e6287`). | `MainKeyboardShortcuts.qml:323-329` | Egyezik. A `0x005696c0` kapu jelentése nyitott (G6). |
| **Mappa/album fejléc `play` gombja.** A `0x005e0f70` a `play` nevet (`0xc96f44`) hasonlítja (`0x005e143c`-`0x005e1461`), majd `push 0`, `call 0x005e8a70` (`0x005e146c`-`0x005e146f`). Súgó: `Diavetítés teljes képernyőn` (`headerpaneltext.tre:38-39`, hivatalos magyar: `panel-feliratok-hu.tsv:474`). | `LightboxHeaderButtons.qml:30-47`, `LightboxFeedGroup.qml:69-71`, `MainLibraryCanvas.qml:267-269` | A belépés és a súgószöveg egyezik. Hogy a nem aktuális mappa fejlécéről melyik nézet és melyik kép kerül sorra, nyitott (G5). |
| **Szerkesztő `Play` gombja.** `editpanel/sbutton` (felirat `Lejátszás`, `panel-feliratok-hu.tsv:4913`), `Property alias thumbui/sbutton` (`editpanel.tre:1124-1127`); a `thumbui/sbutton` ág (`0x005d9cc0`: `cmp ecx, 0xc900e0` `0x005da733`, `push 0` `0x005da740`) szintén `0x005e8a70(this, 0)`. A könyvtár alsó `Slideshow` gombja (`thumbui/sbutton`) alapból `m_hidden` (`konyvtar-ablak-meretek.md:419-422`). | `PhotoViewerTopBar.qml:196-203`, `PhotoViewerQuickToolbar.qml:104-114`, `MainSlideshow.qml:62-65` (a néző aktuális képétől indul) | A belépés egyezik. Kis eltérés a súgószövegben: az eredeti hivatalos magyar szöveg `Állítson össze és nézzen diavetítést ezekből a fotókból` (`panel-feliratok-hu.tsv:4914`), a PicasaPy `Diavetítés lejátszása`. |
| **Időrend.** `0x9ccc` → `0x005cbbdd` (`push 1`), `Ctrl+5` `0x005e6287`, `thumbui/timelinebutton` `0x005da7ab` (`push 1`): `0x005e8a70(this, 1)`, a `qshow` útja. | `PicasaViewMenu.qml:180-185`, `TimelinePanel.qml:539` | Nem tárgya ennek a szakasznak (`picasa-idorend-viselkedes.md` 38.2.8). |
| **`Shift` lenyomva.** `0x005e8ae5`-`0x005e8b00`: ha az alkalmazás aktív (`[0xd67849]`), `GetAsyncKeyState(0x10)` felső bitje `jne 0x005e8d5d`, vagyis a `qshow` ágra ugrik, `0` módban is. A `[0xd67849]` írói: `0x00576419` (`1`) és a `WM_ACTIVATEAPP` (`0x1c`) ág `0x00a52e55`-`0x00a52e66`. | nincs | Rejtett, dokumentálatlan változat (a `oneup.tre` sávval). Nem teendő; a PicasaPy-ban nem kell megvalósítani, amíg látható célja nincs igazolva. |
| **Nem ide tartozik.** A `Include Slideshow` az Ajándék CD-n (`CDSlideshow`, `0x0066f470`) és a képernyővédő előnézete (`startScreensaverPreview`) más funkció. | `PublishPanel.qml:180-186`, `MainSlideshow.qml:74-90` | Nem vizsgálva. |

### 2. A két vetítő: az elágazás

A `0x005e8a70` elején két kapu van, mindkettő `-1`-et ad vissza: (a) látható
`editpanel/preview` elem, és `[this+0x3094]` vagy `[this+0x30a0]` nagyobb
nullánál, és `[this+0x332e]` nem nulla (`0x005e8a89`-`0x005e8ac8`); (b) a
`0x005696c0` igaz és az `editpanel/only_1up_toggle` visszatérése `0xf4242`
(`0x005e8aca`-`0x005e8ae3`). A mezők jelentése nyitott (G6, G8). Utána:

| hívás | ágkezdet | vetítő | erőforrás | kezelők |
|---|---|---|---|---|
| `0` mód, nincs `Shift` | `0x005e8b10`-`0x005e8d5a`, belép: `0x0075de50` | a főablakba ágyazott szerkesztő-egyképes (`[this+0x332f]` = 1) | `editoneup.tre` (a `panelroot.tre:2-3` építi be) | gombok `0x00760240`, billentyűk `0x00760970`, óraütés `0x0075f430`, szünet `0x00760070` |
| `0` mód, `Shift` lenyomva | `0x005e8d5d`-`0x005e9787` → `0x008037e0` | `qshow`/`OneUpUI` | `oneup.tre` | gombok `0x008032e0`, billentyűk `0x00801270`, szünet `0x00801130` |
| `1` mód (Időrend) | ugyanaz | `qshow` | `oneup.tre` | ugyanaz |

Az `0x005e8d5d` szakaszba a függvényen belül csak két ugrás vezet, mindkettő a
`0x005e8b00` és a `0x005e8b0a` címen (szkript a függvény összes ugrására, a
munkafa `.bt/` mappájában, a kör végén törölve). A `0x0075de50` közvetlen hívottjai
között nincs `0x008037e0`, `0x007fa7f0`, `0x007fda00` vagy `0x00802c60`; vtáblán
át történő hívást ez nem zár ki.

A `0x0075de50` normál vetítésként azonosítása (feltételes) ezen áll: belépéskor
beolvassa a `LoopSlideshow` és a `PlayMP3Tracks` beállítást a `[this+0x335c]`
és `[this+0x335d]` mezőbe (`0x0075e5d9`, `0x0075e620`), a dia idejét a
`SlideshowEffectTime` kulcsból (`[this+0x3340]`, alapérték `3`:
`0x00564a41`), hivatkozik az `editoneup/sszoomsliderclip` és `editpanel/sscaption`
elemekre, a `OneUpUI::second`/`seconds`/`Format` szövegeket a `0x0075f960`
használja, és az átmenet-választó (`editoneup/transtype`, `0x0075d810`) a
`ThumbUISlideShow::transition` kulcsot írja (`0x00760b00`).

A két erőforrás különbsége (`diff oneup.tre editoneup.tre`, csak az érdemi):

| elem | `oneup.tre` (`Shift`/Időrend) | `editoneup.tre` (normál) |
|---|---|---|
| `exit` | `stripback` közvetlen gyermeke, bal sarok (`:40`) | a `centergroup` bal széle (`:40`) |
| `timeline` | látható (`:59`) | `m_hidden` és `m_disabled` (`:62-66`); az `editoneup/timeline` névre a kódban egyetlen hivatkozás sincs (string-xref), tehát soha nem lesz látható |
| `stripback` | `YConstraint 1, 1, -20` (`:165`) | `YConstraint 1, 1, -5` (`:172`) |
| `sszoomsliderclip` | nincs | van (`:68-70`) |
| hivatalos magyar `bcklabel` | `Kilépés a diavetítőből` (`panel-feliratok-hu.tsv:641`) | `Kilépés` (`:4911`) |

A PicasaPy felirata `Kilépés` (`picasapy_hu.ts`, `Exit`), tehát a `editoneup`
felirattal egyezik; a sávja viszont a `oneup.tre` szerinti (Timeline gomb a
`SlideshowControls.qml:183-188` és `SlideshowView.qml:55-57` szerint).

### 3. Mit vetít, honnan indul

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Lista.** A `[this+0xea8]` az aktuális nézet objektuma (írója `0x0056bc10`: `0x0056bc73`; `vt+0xb4` darabszám, `vt+0xb8(i)` elem). A léptető (`0x00717d10`, hívja `0x0075fac0`) a `0x00717560` listáját járja: a nézet minden eleme, amelynek `+0x5a` bájtja nulla (`0x007175c6`), a nézet sorrendjében. A kijelölt elemek (`+0x5d` nem nulla) csak a kiinduló helyzethez (`0x00717420` a `0x00717d10`-ben) és a „van-e kijelölés" kapuhoz kellenek (`0x005c6710` → `0x007166c0`). Hivatalos súgó: `Diavetítés megtekintése a kijelölt mappa vagy album fotóiból` (`panel-feliratok-hu.tsv:5154`). | `MainSlideshow.qml:131-134` (`controller.photos`, a teljes nézet), `SlideshowView.qml:190-209` | Egyezik. Több kép kijelölésénél az eredeti is a teljes nézetet járja (feltételes; futásmérés javasolt, 9. szakasz). |
| **Kezdőkép.** `[this+0xe64]`, az aktuális elem (`0x005e8bc3`-`0x005e8c33`, `0x0075e77e`: `[this+0x3370] = [this+0xe64]`). Ha a nézetben nincs kijelölt elem (`0x005c6710` visszatérése 0, `0x005e8bcf`-`0x005e8bd6`), a `0x00717bb0` az első `+0x5a == 0` elemet jelöli ki és teszi aktuálissá. Szerkesztőből indítva (`[this+0x3331]`, `0x00579330`) a szerkesztett kép az aktuális. Könyvtárból indítva a `0x005e8c42`-`0x005e8c51` ág előbb a `searchcontainer/search` elemet kezeli (`0x009cd730`) és a `thumbui/fullview` módra kapcsol (`0x009cd8a0`), csak azután lép be a vetítésbe (`0x005e8d36`). | `MainSlideshow.qml:60-65`: nézőből a néző aktuális képe, különben `max(0, selectedIndex)` | Egyezik. |
| **Üres nézet.** `0x005e8b4b`-`0x005e8b55`: `vt+0xb4` darabszám nulla → `0x0052e8a0`, `or eax, -1` (`0x005e8b3d`), kilép. Üzenet nincs (az Időrend `IDS_MUST_SELECT` üzenete a másik ág, `0x005e983e`). | `MainSlideshow.qml:66-70`: nincs vetíthető fotó → `exitSlideshow()`, üzenet nincs | Hatásában egyezik (néma). Mellékhatás: nálunk az ablak előbb teljes képernyőre vált, aztán visszaáll (`:66-70`); az eredetiben ilyen nincs. Nincs mérve, hogy látszik-e (kis ellenőrzés a 9. szakaszban). |
| **Videó.** A rekordtípus `8`, `9`, `0xa`, `0xb`, `0xc`, `0x17` vagy `0x1d` (`0x005e8b93`-`0x005e8bb4`, `0x0075ee2c`-`0x0075ee4d`) → film ág (`0x0075eda0`): a tétel `moviestart` és `movieend` nevű tulajdonságát olvassa (`0x0075f006`, `0x0075f0bb`), a `[film+0xc8]` és `[film+0xd0]` mezőbe írja, a lejátszó készenlétét legfeljebb húsz próbálkozással kivárja (`0x0075ee73`-`0x0075ee9d`, a várakozó import neve nincs feloldva), a dia idejét a film hosszára állítja: `(hossz - kezdőeltolás) / 10 000 000` másodperc (`0x0075f1bb`-`0x0075f2e2`, `[this+0x3334]`; hogy a hossz a vágott hossz-e, nincs eldöntve), és `[this+0x3332] = 1` (`0x0075f32f`). A mért videótípusok: `8`, `10`, `11` (`paritas-ellenorzes.md` 7033, 3. szakasz). | `SlideshowView.qml:194-209` (`isVideoAt` → kihagyja), `:211-218` | **Igazolt eltérés (statikus):** az eredeti a videót is vetíti, a vágási pontok szerint; mi kihagyjuk. Jegytörzs lent (D3). |
| **Rejtett kép.** A `+0x5a` jelzőjű elemet a lista és a kijelölés-választás is kihagyja (`0x007175c6`, `0x00717485`, `0x00717c01`, és a kijelölés-gyűjtő `0x007166c0` is: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt:2070-2196`, ahol az elemeket index szerint, vagyis rácssorrendben járja). A jelző jelentése (rejtett kép, fejlécsor, hiányzó fájl) a kimenetből nem olvasható ki, csak a bájt vizsgálata; a #7033 fejléc-olvasata „rejtett"-nek veszi, mérés nincs. | a PicasaPy modellből kerül a vetítésbe | Nyitott (G2). |
| **Sérült vagy hálózati úton elérhetetlen kép.** A fotóág (`0x0075eda0`, `0x0075f33f`) és az időzített léptetés (`0x0075f430`) eléri a megjelenítési útvonalat (`0x00569260` → `0x0040fa40`); a `0x006d00c0` nem fájlbetöltési-hiba-kezelő, hanem képkocka-/erőforrás-frissítő. A tényleges hibaállapot továbbadása nincs azonosítva. | `SlideshowView.qml:354-389`, `SlideshowCurrentImage.qml:76-84` | **NINCS MEG** (G4); a PicasaPy oldali képfeldolgozásnál sincs ezen a helyen külön `Image.Error` ág. |

### 4. Vezérlők, alapértékek, megjegyzett állapot

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Gombok.** `editoneup.tre`: `exit`, `prev`, `auto`, `next`, `plusone`/`minusone` és a `tps`/`tpslabel` időblokk (`centergroup`), `transtype`, `rotateleft`, `rotateright`, `star`, `captionbutton`; a `timeline` rejtett. `auto2` (`:20-23`): `m_scaleX`, `YConstraint 0, 0, 0` és `YConstraint 1, 1, -97`, vagyis a felső széltől a sáv fölötti `97` képpontig nyúlik (`macros.tre:21-27` szerint két `YConstraint` nyújt), az `auto` művelete. Parancsnév-lánc: `0x00760240` (`exit` → `0x0075de50`; `plusone`/`minusone` → `0x0075f960`; `auto`/`auto2` → léptetés-indítás). | `SlideshowControls.qml:55-70` (`auto2` sáv, 14 képpont), `:170-345` | A felsorolás egyezik, a `Timeline` gomb kivételével (D1). **Az `auto2` területe eltér** (feltételes, erőforrás-szemantika): nálunk 14 képpontos felső sáv (#5649, a `respack.yt` `800 x 14` adatából), a `.tre` szerint a kép szinte egésze. Ez megválaszolja a `picasa-diavetito-sav-5550.md` N3 kérdését. D4. |
| **Dia ideje.** `SlideshowEffectTime`, alapérték `3` (`0x00564a41`, `0x007facd3`). `+`/`-`: `0x0075f960` a kulcs értékéhez adja a `±1`-et, `1,0` és `[0x00cf4974]` = `20,0` közé szorítja, kiírja (`0x00401900`) és a `N másodperc` szöveget (`OneUpUI::Format` `%d %s`, `second`/`seconds`) a `editoneup/tps` elemre teszi. Minden dia elején újra beolvassa (`0x0075edb2`-`0x0075edbd`). | `controller_slideshow_mixin.py:106-135` (`1`-`20`, alapérték `3`, hibás érték `3`), `SlideshowControls.qml:284-345` | Egyezik. |
| **Számjegyek `0`-`9`.** `0x00760970`: a számjegy értékét kiírja a `SlideshowEffectTime` kulcsba, és ha az olvasás nullát ad, `1`-et ír (`0x00760a19`-`0x00760a49`); szünetben a címkét is frissíti (`0x00760a4e`-`0x00760a5e`). | `SlideshowView.qml:713-731` | Egyezik. |
| **Léptetés billentyűvel.** `0x00760970`: `Bal` (`0x25`) és `Fel` (`0x26`) hátra, `Jobb` (`0x27`) és `Le` (`0x28`) előre (`0x00760a6c`-`0x00760a78`), `Esc` (`0x1b`) kilép (`0x00760990`), `Space` (`0x20`) kapcsolja az `editoneup/auto` elemet (`0x007609d0`), `Pause` (`0x13`) csak lejátszás közben, `Play` (`0xfa`) csak szünetben. `Enter` (`0x0d`) és `Ctrl+R` nincs ebben a kezelőben; a normál vetítési módot jelző `[this+0x332f]` mellett a közös billentyűút korán visszatér (`0x005e6710`, `0x005e60d0`). | `SlideshowView.qml:663-720`: `Fel`/`Le`, `Enter`, `Ctrl+R`, számjegyek és `Pause`/`Play` | **Részben eltér.** A `Fel`/`Le`, számjegyek, `Pause`/`Play` egyeznek. A PicasaPy az `Enter`-t továbblépésre, a `Ctrl+R`-t forgatásra használja; az eredeti normál vetítési ágban a külön kezelő ezeket nem dolgozza fel, a közös kezelő a `+0x332f` kapun visszatér. D2 maradjon erre a két billentyűre szűkítve. |
| **Kézi léptetés a lista szélén.** `0x0075fb20`: ha az első kijelölt elem a nézet utolsó indexén áll és előre lép, `0x00717bb0` az első elemet jelöli ki, a `LoopSlideshow` értékétől függetlenül (`0x0075fba2`-`0x0075fbd5`); egyébként `0x00717260` / `0x007172a0` (a rács nyíl-léptetője, `0x00717eb0`), amely a lista szélén nem fordul körbe és nem lép (`0x00718031`-`0x0071804a`: a `pos + delta` kívül esik, a visszatérés `0xf4240` kijelölésváltás nélkül), tehát hátra az első képen az eredeti áll. Az automatikus léptetés (`0x00717d10`, `loop` = `[this+0x335c]`) a lista végén hurok nélkül `[nézet+0x2e0] = -1`-et ad (`0x00717e76`). | `SlideshowView.qml:278-282`: hurok nélkül az utolsó képről előre lépve `stop()`, vagyis kilép | **Eltérés (a léptető függvények utasításszinten igazoltak, a teljes hatás futásmérésre vár):** az eredetiben a kézi előre lépés az utolsó képről visszafordul az elsőre, hátra az első képről nem lép; nálunk hurok nélkül az előre lépés kilép, hurokkal a hátra lépés az elsőről az utolsóra fordul. Az automatikus lista-vég viselkedése nyitott: a `0x0075f430` óraütés és a `0x00569260` útján nincs közvetlen hívás a kilépésre (`0x0075de50`), tehát az eredeti nem biztos, hogy kilép (G1). |
| **Ismétlés.** `LoopSlideshow`, alapérték `0` (`0x007fad0a`), belépéskor `[this+0x335c]`-be másolva, kilépéskor nullázva (`0x0075e5d9`, `0x0075debb`). | `controller_slideshow_mixin.py:137-149` (alapérték ki) | Egyezik. A másolás miatt a vetítés közbeni beállításváltás az eredetiben nem hat; nálunk a kötés élő, de a Beállítások ablak közben nem érhető el. |
| **Zene.** `PlayMP3Tracks`, alapérték `1` (`0x007fadbb`), belépéskor `[this+0x335d]`; a zeneforrás `MP3SlideshowPath` (`0x0075cdc0`, zenei szál: `0x0075ca20`, a példány `[this+0x33a4]`); szünetben `0x00760070` hívja a `0x0075d570`-et. | `controller_slideshow_mixin.py:151-212`, `SlideshowMusic.qml:1-50` | Az alapérték egyezik; a sávsorrend, a szünetben viselkedés és a hangerő nincs vizsgálva (G7). |
| **Átmenet.** `ThumbUISlideShow::transition` DWORD `0`-`6`, alapérték `2` (Dissolve), a választó írja (`0x00760ca5`, `picasa-diavetito-sav-5550.md` 1.3.3); hét elem (`0xd342e8`). | `controller_slideshow_mixin.py:14-57`, `SlideshowControls.qml:226-245` | Egyezik (a tárolási forma eltérése dokumentált, nem teendő). |
| **Felirat.** `captionmode`, alapérték `0` (`0x00564b51`-`0x00564b90`, `[this+0xdd8]`), írója `0x005749e0`; az `editoneup/captionbutton` két állapotú (`showtarget`/`hidetarget`). | `controller_slideshow_mixin.py:213-222` (három mód) | A három állapot eltérése már ismert (`picasa-diavetito-sav.md` 6. jegyjavaslat); az `editoneup` sem ad harmadik állapotot. Nincs új lelet. |
| **Mit jegyez meg.** Kizárólag `Preferences` kulcsot ír: `SlideshowEffectTime` (minden `+`/`-` és számjegy után), `ThumbUISlideShow::transition`, `captionmode`; `LoopSlideshow`, `PlayMP3Tracks`, `MP3SlideshowPath` a Beállítások ablakból jön. Utolsó pozíciót, nézetet nem jegyez. | `controller_slideshow_mixin.py` (`view/slideshow*`) | Egyezik. |

### 5. Kilépés és hatás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Kilépés indítása.** `Esc` → `0x00760990` → `0x0075de50`; `exit` gomb → `0x00760240` → `0x0075de50` (`picasa-idorend-viselkedes.md:2866`). A `0x0075de50` a `[this+0x332f]` szerint kapcsol: nulla → belép (`0x0075e4bd`), nem nulla → kilép. | `SlideshowView.qml:663-666`, `SlideshowControls.qml:174-179` | Egyezik. |
| **Kilépéskor.** A kurzor visszajön (`push 1`, `call 0x0097e510`, `0x0075dea3`-`0x0075deab`), `[this+0x335c]`, `[this+0x335d]` nulla (`0x0075debb`, `0x0075dec1`), a zenei objektum leáll (`0x0075ccb0`) és a program várakozik a szálára (`0x0097b420`, `0x3e8` időkorlát; a szál-értelmezés feltételes), `[this+0x332f]` és `[this+0x3330]` nulla (`0x0075e0a8`, `0x0075e0ae`), az `editpanel/fullscreenswitcher` elem a panel-váltón (`0x009cd8a0`) át visszakapcsol (`0x0075e0b4`; ugyanez a hívás a belépő ágon is áll, `0x0075e520`, tehát a teljes képernyőre váltás oda-vissza ezen megy, feltételes). | `MainSlideshow.qml:92-97` (ablakállapot vissza) | Egyezik. |
| **Hova tér vissza.** Ha a vetítés előtt a szerkesztő látszott (`[this+0x3331]`, `0x005e8c3a`), a `0x00566a70`, különben a könyvtár (`0x00566270`, a `searchcontainer/search` elem kezelése): `0x0075e205`-`0x0075e237`. | `MainSlideshow.qml:105-113`: nyitott néző esetén a néző az utolsó képre áll, különben a rács | Egyezik. |
| **Mi lesz kijelölve.** A léptetés a nézet kijelölését viszi magával: `0x00717260`/`0x007172a0` → `0x00717eb0`, amely az aktuális elem (`[nézet+0x390]`) helyzetéhez ±1-et ad a nem jelzett (`+0x5a == 0`) elemek listájában, `Shift` nélkül a többi elem kijelölését törli (`+0x5d = 0`), a célt kijelöli és aktuálissá teszi, és frissít (`0x00717ed0`-`0x00717f04`, `0x00717fe2`-`0x00718016`, `0x00718058`-`0x007180ef`). Az aktuális elem (`[this+0xe64]`) írói közül (`tagkereso.py`: közvetlen írás csak a betöltőben `0x00564cc7` és a `0x005e8a70`-ben `0x005e8c2d`, `lea` alakban a `0x005704d0`-ban, `0x005704eb`-`0x005704fe`) a `0x005704d0` az elemváltó, és ez a nézetben is kijelöli az elemet (`0x00717c50`, `0x0057066e`), tehát az aktuális elem és a kijelölés együtt mozog. Hogy az óraütés (automatikus léptetés) melyik úton jut a `0x005704d0`-ig, nincs végigkövetve (G1). Kilépéskor az első kijelölt elem `+0x5d` jelzője 1, `[nézet+0x390]` az azonosítója, és `0x0071b810` frissít (`0x0075e3c1`-`0x0075e487`). | `MainSlideshow.qml:109-112`: `selectedIndexes = [currentIndex]` | Egyezik. |
| **Tárolt adat.** A kilépés ága nem hív `.picasa.ini`- vagy indexírót. A vetítés alatti forgatás és csillagozás a közös útra megy (`0x00760240` → `0x005eef30`, `0x005e81e0`), ez nem a vetítés sajátja. | `MainSlideshow.qml:191-199` (`toggleStar`, `rotateLeft`/`rotateRight`) | Egyezik. A negatív állítás a kilépés hívási ágára korlátozott. |
| **Windows képernyőkímélő.** A normál kilépési ágban közvetlenül a kurzort visszaállító `0x0097e510` látszik (`0x0075dea3`-`0x0075deab`); nem találtam itt közvetlen képernyőkímélő-beállítás írást. Az indirekt hatás és a rendszer tétlenségi viselkedése **NINCS MEG**. | `MainSlideshow.qml:73-83, 92-103`: az alkalmazáson belüli képernyőkímélő-előnézet külön út, a normál kilépés ablakállapotot állít vissza. | Nyitott: Windows-futásmérés kell a Picasa normál `Ctrl+4` útján; rögzíteni kell a rendszer képernyőkímélő-beállításait előtte/utána, és azt is, hogy vetítés közben elindul-e. |

### 6. Üres kijelölés, üres nézet

Az eredeti normál vetítésben nincs `IDS_MUST_SELECT` üzenet (az az Időrend
`0x005e983e` ága); nulla elemnél csendben visszatér (`0x005e8b34`-`0x005e8b46`).
Kijelölés nélkül az első nem jelzett elemet kijelöli és onnan indul
(`0x005e8bcf`-`0x005e8bde`). A PicasaPy ugyanígy hallgat és az első képtől
indul (`MainSlideshow.qml:60-71`).

### 7. A két független út és a cáfoló kísérlet

- **A út, utasítások.** A `0x005cb990` ugrótábla (`0x005cbbd1`), a `0x005e60d0`, `0x005e0f70`, `0x005d9cc0` hívóhelyek `push 0`-val, a `0x005e8a70` elágazása (`0x005e8ae5`-`0x005e8b0a`) és a `0x0075de50` belépő/kilépő ága, `capstone`-nal, a `pe_dis.py` olvasóján át.
- **B út, független forrás.** A `FUN_005e8a70` Ghidra-dekompilátuma
  (`referencia/ghidra/2026-10-17-qshow-diavetites.txt:125-126` a feltétel, `:189` a `FUN_0075de50()` hívás, `:604` a `FUN_008037e0()` hívás) ugyanazt mutatja:
  `if ((DAT_00d67849 == '\0' || !(GetAsyncKeyState(0x10) & 0x8000)) && param_2 == '\0') { ... iVar6 = FUN_0075de50(); ... return iVar6; }`,
  a `qshow` ág (`FUN_008037e0`) csak utána jön. A `0x0075de50` sztring-hivatkozásai (`LoopSlideshow`, `PlayMP3Tracks`, `editoneup/sszoomsliderclip`, `editpanel/sscaption`, `editpanel/fullscreenswitcher`) a bináris-indexből, az `editoneup.tre` beépítése a `panelroot.tre:2-3`-ból.
- **Cáfoló kísérlet.** (1) Van-e más út a `qshow` szakaszba `0` módban `Shift` nélkül? A függvény összes ugrásának átnézése (a munkafa `.bt/` mappájában készült szkripttel, a kör végén törölve): az `0x005e8d5d`-`0x005e9a8e` tartományba csak a `0x005e8b00` és a `0x005e8b0a` ugrik. (2) A `[0xd67849]` valóban az aktív ablak jelzője-e, vagy állandó? Két írója van, az egyik a `WM_ACTIVATEAPP` ágon az üzenet `wParam` értékét írja (`0x00a52e55`-`0x00a52e66`), tehát a `Shift` vizsgálata valódi. (3) A `0x0075de50` csak a szerkesztő sima egyképes nézete lehet-e, nem vetítés? Nem: a `LoopSlideshow`/`PlayMP3Tracks` beolvasás, a `ss`-előtagú elemek és az átmenet-választó ezt cáfolják. **Határ:** az index és az ugrás-pásztázás a vtáblán át történő hívást nem látja; a `0x0075de50` közvetett hívója a `qshow` felé nem zárható ki, de a normál `0` módú útra nincs ilyen jel.
- **A G4 címének cáfoló ellenőrzése.** A korábbi `0x006d00c0 = képbetöltési-hiba-kezelő` feltevést célzottan támadtam. A függvény disassemblyje a `[this+0x20]` / `[this+0x24]` erőforrás-állapotot kezeli és virtuális metódust hív; a `0x00569260` hívó rajzolási objektumot és szélesség/magasság/alfa argumentumokat ad át. Független ellenőrzésként a Ghidra `0x005683a0` hívója kiszámított képkocka-méretet és alfát ad a `0x006d00c0`-nak (`2026-11-15-7006-7008-7009-7012-colab-decomp.txt:2754`). A két út egyezik: a `0x006d00c0`-hoz rendelt fájlbetöltési szerep nem igazolható, és a függvény közvetlen szerepe képkocka-/erőforrás-frissítés. Ez a cáfolat csak a hibás cím-hozzárendelést zárja ki; a tényleges fájlbetöltési hibaág továbbra is nyitott.

### 8. Javasolt fejlesztői jegytörzsek

#### D1. A normál diavetítés vezérlősávjában ne legyen Timeline gomb

**Eredeti:** a `0x005e8a70` `0` módban, `Shift` nélkül az `editoneup` vetítőt indítja (`0x0075de50`); ennek erőforrása az `editoneup.tre`, ahol a `timeline` `m_hidden` és `m_disabled` (`:62-66`), és a kódban az `editoneup/timeline` névre egyetlen hivatkozás sincs. Az átmenet-választó (`editoneup/transtype`) nem rejtett.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `editoneup.tre:62-66` | `SlideshowView.qml:55-57` (`timelineButtonVisible`), `SlideshowControls.qml:183-188, 227-231` | A normál diavetítésben a Timeline gomb ne látszódjon, az átmenet-választó mindig. Az Időrend-bemutató saját vetítése (`timelineSlideshow`) változatlan. |

**Kész, ha:** normál vetítésben (`Ctrl+4`, menü) a `slideshowTimelineButton` nem látszik, a `slideshowTransitionBox` mindig; a #5653 tesztjeit ennek megfelelően kell átírni. A sáv elrendezése (az `exit` a középső csoportban, `5` képpont) csak a csoporton belüli sorrend megmérése után módosítható (`NINCS MEG`, `picasa-diavetito-sav.md` 7. jegyjavaslat).

#### D2. A normál diavetítésben az `Enter` és a `Ctrl+R` ne kapjon műveletet

**Eredeti:** a `0x00760970` külön kezelő nem tartalmaz `Enter`- vagy `R`-ágat. A `0x005e6710` a nem kezelt gombot a közös `0x005e60d0` útra továbbítja, amely a normál vetítés `[this+0x332f]` állapotánál azonnal visszatér.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00760970`, `0x005e6710`, `0x005e60d0` | `SlideshowView.qml:677-680, 706-711` | A normál vetítésben ne léptessen az `Enter`, és ne forgasson a `Ctrl+R`/`Ctrl+Shift+R`; a már egyező `Fel`/`Le`, számjegy és `Pause`/`Play` kezelés maradjon. |

**Kész, ha:** normál vetítésben az `Enter` nem léptet, a `Ctrl+R` és `Ctrl+Shift+R` nem forgat; a `Fel`/`Le`, számjegy, `Pause` és `Play` továbbra is a Picasa-műveletet végzi.

#### D3. A videó a diavetítésben (vágási pontok szerint)

**Előfeltétel:** futásmérés (Colab): videót is tartalmazó mappa `Ctrl+4`-gyel; a videó játszik-e, mennyi ideig áll a dia. Ha az eredeti kihagyja, a jegytörzs elvetendő.

**Eredeti:** `0x0075eda0` a `8`, `9`, `0xa`, `0xb`, `0xc`, `0x17`, `0x1d` rekordtípusnál film ágra lép: a `moviestart` és `movieend` tulajdonságot a lejátszó `+0xc8` és `+0xd0` mezőjébe írja (`0x0075f006`-`0x0075f135`), a dia ideje a film hossza másodpercben, `(hossz - kezdőeltolás) / 10 000 000` (`0x0075f1bb`-`0x0075f2e2`).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x0075eda0`, `0x0075f15a`-`0x0075f2e2` | `SlideshowView.qml:194-218` (`isVideoAt` kihagyás) | A vetítés vegye be a videót, adja át a vágási pontokat a lejátszónak, és a következő diára a film hossza után lépjen. |

**Kész, ha:** egy videót is tartalmazó mappán a vetítés a videót játssza (a vágási pontokat átadva a lejátszónak), a dia ideje a film hossza, és utána lép; a többi dia ideje változatlan. Hogy a hossz a vágott hossz-e, a futásmérés dönti el.

#### D4. Az `auto2` kattintási terület: a kép szinte egésze, nem 14 képpontos sáv

**Előfeltétel:** futásmérés (Colab): a vetítés közepére kattintva (a sáv fölött) vált-e lejátszás és szünet között. Ha nem, a jegytörzs elvetendő, és az erőforrás-szemantika olvasatát helyesbíteni kell.

**Eredeti:** `editoneup.tre:20-23` és `oneup.tre:20-23`: `auto2: root`, `m_scaleX`, `YConstraint 0, 0, 0`, `YConstraint 1, 1, -97`. A `macros.tre:21-33` szerint két ugyanazon tengelyű megszorítás nyújt (`m_scaleY`, `m_scaleXY`, a `back` elem így tölti ki a szülőt), tehát a terület a felső széltől a szülő aljánál `97` képponttal feljebbi vonalig ér. A kezelő az `auto` kezelőjével azonos (`0x00803486` és `0x008034c5` ugyanazt a függvényt hívja; az `editoneup` oldalon a `0x00760240` `auto`/`auto2` ága).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `editoneup.tre:20-23`, `macros.tre:21-27` | `SlideshowControls.qml:56-70` (14 képpont magas `MouseArea`) | A `slideshowAuto2Area` magassága a szülő magassága mínusz `97` képpont legyen, a sáv és a felirat helye nélkül. |

**Kész, ha:** a vetítés közepére kattintva a lejátszás/szünet vált, és a sáv gombjai (a `97` képpontos alsó zóna) érintetlenül működnek; a `PressFeedbackOverlay` ne takarja a képet.

#### D5. A szerkesztő `Play` gombjának súgószövege

**Lezárva:** az eredeti `editpanel/sbutton` súgója (`editpaneltext.tre:8-9`)
magyarul `Állítson össze és nézzen diavetítést ezekből a fotókból`
(`panel-feliratok-hu.tsv:4914`). A jelenlegi `PhotoViewerTopBar.qml:200` és
`PhotoViewerQuickToolbar.qml:111` ugyanazt az eredeti kulcsot használja; a
`picasapy_hu.ts:10940-10943,11079-11082` fordítása a hivatalos magyar
szöveg. Fejlesztői jegy nem indokolt.

A kézi léptetés lista-szélének viselkedése (előre az utolsó képről az elsőre, hátra
az első képen nem lép) statikusan eltér a PicasaPy-tól, ezért a D7 jegytörzs
lent szerepel; a felhasználói végállapotot futásmérés erősítse meg. Az
automatikus lista-vég külön nyitott kérdés (G1, D6).

### 9. Nyitott

- Futásmérés kell (G1): hurok nélkül, kétképes mappában az utolsó dia után marad-e az utolsó kép, változik-e a lejátszás állapota vagy bezárul-e a vetítő. A `0x0075f430`-ból nincs közvetlen kilépő hívás; az automatikus lépés a `0x005c4ce0` → `0x0075fb20` úton a nézet kijelölését is frissíti.
- Futásmérés kell (G2): egy Picasában elrejtett kép szereplése `Ctrl+4` vetítéskor. A `+0x5b` szemantikai neve nem blokkoló, mert a vetítő listagyűjtője nem olvassa.
- Futásmérés kell (G3): normál `Ctrl+4` alatt a szünet, egérmozgás, sáv körüli egér és várakozás hatása a vezérlősávra. A #375 felvételei nem találhatók a helyi `referencia/` alatt.
- Futásmérés kell (G4, blokkoló): csonka, hiányzó és elérhetetlen hálózati képfájl kezelése; rögzíteni kell, hogy a vetítés átugorja, megállítja vagy jelzi-e a hibát.
- **NINCS MEG** a Windows képernyőkímélő beállításának változása és a vetítés alatti aktiválódása. Futásmérés: `Ctrl+4` előtt és után beállításrögzítés, majd megfigyelés a rendszer tétlenségi határán túl.
- Futásmérés kell (G5): nem aktuális mappafejléc `play` gombja után a vetített mappanév és első kép. A hívás sorindex nélkül az alkalmazás aktuális nézetét adja át, de a gombkattintás előtti nézetváltás nem bizonyított.
- G6 megválaszolva meglévő dekompilációból és a hívóhely disassemblyjéből: az `Enter` és `Ctrl+R` nem jut a főablak műveletágába normál vetítésben; a `0x005696c0` nyers feltétele a 9/a táblában.
- Futásmérés kell (G7): két különböző nevű zenefájllal a sorrend, ismétlés, szünet/folytatás és kilépés hallható hatása. A `0x0075cdc0` csak az `MP3SlideshowPath` beállítást tölti be.
- G8 megválaszolva a nyers feltétel szintjén: a `0x005e8a70` indítási kapuja a 9/a táblában szerepel; a mezők pontos neve nem blokkoló.

- Ghidra-kör kell: 0x0075f430 - mi történik az óraütés lista-vég ágán, ha a `[nézet+0x2e0]` `-1` és a `LoopSlideshow` ki: megáll az utolsó képen, szünetbe lép, vagy kilép (a `0x0075f430`-ból és a `0x00569260`-ból nincs közvetlen hívás a kilépő `0x0075de50`-re); és ugyanitt: az automatikus léptetés melyik úton hívja az aktuális elemet váltó `0x005704d0`-et, vagyis a nézet kijelölése valóban a látott képet követi-e. (G1)
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4871`): a kimenet részben dönt. A `0x0075f430` (`:4871-5092`) **sem a kilépőt (`0x0075de50`), sem a szünet-kapcsolót (`0x00760070`) nem hívja**; hívottjai: `0x00569260`, `0x00569400`, `0x006cfe10`, `0x006cffd0`, `0x0075eac0` (dia betöltés), `0x0075eda0` (fotó ág), `0x0075fac0`, `0x00760190`, `0x00a54b70`, `0x0052e2f0`. A léptetés a `0x0075f58e`-nál a `0x0075fac0(1)`-en át megy, amely az `[ablak+0xea8]` nézetet, az argumentumot és a `LoopSlideshow` jelzőt (`[ablak+0x335c]`) a nézet `0x00717d10` léptetőjének adja, majd `0x00569260`-at hív (`0x0075fac0-0x0075fae4`, disassembly). **Az automatikus léptetés tehát a nézet saját léptetőjén megy, a `0x005704d0`-et (hívói `0x0053ce00`, `0x0056a160`, `0x0056b6f0`, `0x0056bfd0`, `0x005706b0`, `0x005fa020`) sem a `0x0075f430`, sem a `0x0075fac0`, sem a `0x00569260` nem hívja közvetlenül**; a nézet kijelölésének követése a léptető (`0x00717d10` -> `0x00717eb0`) viselkedése. A lista-végi ág (`[nézet+0x2e0] == -1`, `LoopSlideshow` ki) kimenetele a kimenetből nem dönthető el, mert a `0x00717d10` és a `0x006cfe10`/`0x006cffd0` (regiszterargumentumos hívások) törzse nincs benne, a megállás, szünet vagy kilépés tehát a léptetőben vagy a hívókban (`0x00571e50`, `0x005c4ce0`) dől el.
- Ghidra-kör kell: 0x00717d10 - a léptető: a lista végén `LoopSlideshow` ki esetén mit ad vissza és mit állít (`[nézet+0x2e0]`, `[nézet+0x390]`), és a hívói közül a `0x005c4ce0` és a `0x00571e50` mit tesz a visszatérési értékekkel (megáll az utolsó képen, szünet, kilépés a `0x0075de50`-re) (G1) [nem blokkoló]
- Ghidra-kör kell: 0x00717560 - az elem `+0x5a` és `+0x5b` bájtjának jelentése és írói (rejtett kép, fejlécsor, hiányzó fájl): a nézet-bejárások (`0x00717560`, `0x00717420`, `0x007166c0`, `0x00717eb0`) ezt a jelzőt hagyják ki. (G2)
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4595`): a kimenet részben dönt. A `0x00717560` (`:4595-4678`) csak **olvassa** a `+0x5a` bájtot: a nézet elemein (`+0xb4` darabszám, `+0xb8(i)` elem) sorban végigmegy, és csak azok indexét teszi a listába, amelyeknek a `+0x5a` bájtja 0; előtte a `0x0071c8c0`-at hívja, és ha a nézet `+0x2cc` bájtja nem nulla, a nézet `+0xc4` metódusát. A `+0x5a` tehát a bejárásokból **kizárt elem** jelzője; hogy ez rejtett kép, fejlécsor vagy hiányzó fájl, a kimenetből nem dönthető el. A disassembly szerint az elem alaphelyzetbe állítása (`0x00713eb0`) a `+0x5a`-t 0-ra, a `+0x59`-et és a `+0x5b`-t 1-re állítja (`0x00713f82`, `0x00713fb8`, `0x00713fbc`); a `+0x5b`-t 0-ra állítja a `0x0071c8c0` (`0x0071c8dd`, a bejárások eleji hívás) és a `0x00716d70` (`0x00716e25`); a `+0x5a`-t 1-re állítja a `0x00714010` (20 bájt, hívója `0x00781680`) és a `0x00716d70` (`0x00716e53`), további írója a `0x0071dd40` (`0x0071e038`, 0). A `+0x5b` jelentése nem dönthető el.
- Ghidra-kör kell: 0x00716d70 - a `+0x5a` és `+0x5b` írója (462 bájt, nézet-szűrő?): mikor kerül 1-be a `+0x5a` (rejtett kép, fejlécsor, hiányzó fájl), és mit jelent a `+0x5b`; 0x00714010 és a hívója 0x00781680 (G2) [nem blokkoló]
- Ghidra-kör kell: 0x005c4ce0 - az `editoneup` vezérlősáv megjelenése: mikor látszik a normál vetítés sávja (szünet, egérmozgás, sáv fölötti tartózkodás); a #6930 szerinti hostcsere (`0x00802c20` → `0x009833a0`) a `OneUpUI`-ra, tehát a `qshow` útra vonatkozik; a normál vetítésben a szünet-kapcsoló a `0x00760070` (`0x0075d570`, `0x0075eac0`), és hogy ez hogyan jeleníti meg a sávot, nincs vizsgálva. (G3)
- Ghidra-kör kell: 0x006d00c0 - a diaváltás (`0x0075eda0` fotó ág, `0x0075eac0`) betöltési hibája: sérült, hiányzó vagy hálózati úton elérhetetlen fájlnál kihagyja-e a diát, hibát mutat-e, megáll-e. (G4)
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4482`): **a `0x006d00c0` nem a betöltési hibát kezeli:** (`:4482-4535`) háromparaméteres beállító: a `[objektum+0x80]`, `+0x84`, `+0x88` mezőt írja az `(param_1, param_2, param_3)` értékeire, szálazonosítóval újrabelépő zár alatt, és `0`-t ad vissza; hibaágat, üzenetet vagy kihagyást nem tartalmaz. Hívói a `0x005683a0`, `0x00569260` (a léptetés utáni hívás), `0x0075de50` (a vetítésből kilépő), `0x00774d60`, `0x00775390`. A sérült, hiányzó vagy hálózati úton elérhetetlen fájl kezelése tehát nem itt van; az index szerint a fotó ág (`0x0075eda0`, 1505 bájt) a `moviestart`, `movieend`, `%x-transition` sztringeket használja, a `0x0075eac0` az `editoneup/prev`, `next`, `sscaption`, `captionbutton`, `rotateleft`, `rotateright`, `star` vezérlőket kezeli; a betöltési hibaág egyik függvényben sem látszik.
- Ghidra-kör kell: 0x0075eda0 - a fotó ág (1505 bájt; hívottai `0x00460180`, `0x00465b20`, `0x004963d0`, `0x0054ba80`, `0x00552120`, `0x00555720`, `0x00906cf0`): sérült, hiányzó vagy hálózati úton elérhetetlen fájl betöltési hibája: kihagyja-e a diát, hibát mutat-e, megáll-e (G4) [nem blokkoló]
- Ghidra-kör kell: 0x005e0f70 - a fejléc `play` gombja: a `0x005e146f` hívás előtt melyik nézet az aktuális (`0x0056bc10`), tehát nem az aktuális mappa fejlécéről melyik képsorozat indul. (G5)
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:2532`): a kimenet dönt: **a `play` ág nem vált nézetet.** A `0x005e0f70` (`:2532-3589`) az eseményszöveg `3` sorszámú tagját (`0x00988f30(…, 3, 0)`) hasonlítja össze sztringként a kezelt nevekkel, és a `play` egyezésnél (`0x005e1461`) a `0x005e8a70(ablak, 0)`-t hívja (`0x005e146f`); előtte semmi nem állít nézetet, a `0x0056bc10` hívása a teljes függvényben nincs meg. A `2` sorszámú tagból `_atol`-lal kiolvasott számot (`local_1468`) a `play` ág nem használja és nem is adja át. **Ebből következik, hogy a fejléc `play` gombja mindig az ablak éppen aktuális nézetéből indít vetítést, nem a gombot hordozó fejléc mappájából;** hogy ez az aktuális nézet melyik, azt a korábbi vizsgálat szerint a `0x0056bc10` állítja (`[ablak+0xea8]`).
- Ghidra-kör kell: 0x0056bc10 - a `[ablak+0xea8]` aktuális nézet írója: mikor áll át egy fejlécre kattintáskor (a mappalista fejlécén a kattintás a mappát is aktuálissá teszi-e a `play` előtt) (G5) [nem blokkoló]
- Ghidra-kör kell: 0x005e60d0 - az `Enter` (`0x0d`) ág, a `Ctrl+R`/`Ctrl+Shift+R` ág és a `Ctrl+4` ág `0x005696c0` kapuja: mit csinál az `Enter` és a forgatás-billentyű normál vetítés közben (a `0x00760970` egyiket sem kezeli), és mikor tiltja a `0x005696c0` a `0x005e8a70` hívását. (G6)
- Ghidra-kör kell: 0x0075cdc0 - a normál vetítés zenéje: a `MP3SlideshowPath` mappa sávjainak sorrendje (rendezett vagy véletlen), ismétlés, szünetben viselkedés (`0x0075d570`), és a kilépési várakozás (`0x0097b420`, `0x3e8`). (G7)
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4679`): a kimenet részben dönt. A `0x0075cdc0` (`:4679-4870`, egyetlen hívója a zenei szál `0x0075ca20`, `0x0075ca55`) **csak a zeneforrást állítja be, a sávok sorrendjét, az ismétlést, a szünetbeli viselkedést és a kilépési várakozást nem.** Ha a `[objektum+0x1a8]` útvonal nem üres, a `+0x94`-re másolja, `GetShortPathNameW`-vel rövid útvonalat képez (`0x412` karakteres puffer), azt UTF-8-ra alakítja (`WideCharToMultiByte`, `0xfde9`), és a `+200` mezőbe teszi (sikertelen rövidítésnél az eredeti útvonal marad). Ha a `[objektum+0x1ac]` bájt nem nulla, a `Preferences` `MP3SlideshowPath` értékét olvassa (`0x00407630`, `0x004078e0`), és a `+0x48` mezőbe teszi (`0x009a5f80`); ha az érték üres vagy nulla hosszú, alapértelmezett mappát kér a `0x00980ec0(0)`, `0x009a38a0`, `0x009a3db0` hívásokkal (melyik rendszermappa, a kimenetből nem dönthető el).
- Ghidra-kör kell: 0x0075ca20 - a zenei szál: a `+0x48` mappa sávjainak sorrendje (rendezett vagy véletlen), ismétlés, szünetben viselkedés (`0x0075d570`), kilépési várakozás (`0x0097b420`, `0x3e8`); és 0x009a3db0 - az alapértelmezett zenemappa (G7) [nem blokkoló]
- Ghidra-kör kell: 0x005e8a70 - az elején lévő kapuk (`0x005e8a89`-`0x005e8ac8`): a `[this+0x3094]`, `[this+0x30a0]`, `[this+0x332e]` jelentése (képtálca? szerkesztő-állapot?), vagyis mikor nem indul a vetítés. (G8)
- Futásmérés kell: a `picasa-colab-jobs #375` 17-18. képén (szünetben látható sáv) látszik-e Timeline gomb és hol áll az `Exit` (a D1 előfeltétele); ugyanitt: normál `Ctrl+4` tényleg az `editoneup` vetítő-e.
- Futásmérés kell: videót is tartalmazó mappán `Ctrl+4`: játszik-e a videó, és mennyi ideig áll a dia (D3 előfeltétele).
- Futásmérés kell: három nem szomszédos kép kijelölve, `Ctrl+4`, majd `Jobb` nyíl többször: csak a három, vagy a teljes nézet jön-e; az utolsó képen `Jobb` nyíl hurok nélkül: visszafordul-e az elsőre.
- Futásmérés kell: üres mappán `Ctrl+4`: látszik-e bármi (üzenet, ablakváltás), és a PicasaPy előbb-teljes-képernyőre-vált villanása látszik-e.
- Futásmérés kell: a vetítés közepére kattintva (a sáv fölött) vált-e lejátszás és szünet között (D4 előfeltétele).
- Futásmérés kell: videó, többes kijelölés, üres mappa és `auto2` esetén a táblázatban megadott felhasználói hatás rögzítése; az `Esc`, `Fel`/`Le`, számjegyek, `Pause`/`Play` kódútja statikusan igazolt.

### 9/a. Zárókör: a megmaradt kérdések feldolgozása

Az alábbi állapotok a fenti nyitott lista zárókörös kiegészítései. A korábbi
Ghidra-kimeneteket nem törlöm; ahol a korábbi Ghidra-kérésre már van válasz,
az itt megadott cím szerinti eredmény a mérvadó. A feloldatlan kérdéseknél
az alábbi mérés a következő döntő lépés, új dekompilációs kérés nem maradt.

| Tétel | Zárókörös válasz és fennmaradó bizonyíték |
|---|---|
| G1, időzített léptetés és lista vége | A `0x005c4ce0` hívó csak akkor léptet a `0x0075fb20`-szal, ha a `0x0075f430` nem nulla eredményt ad. A `0x0075fb20` a `0x00717420` listájából választ, majd a `0x00717260`/`0x007172a0` úton frissíti a rács kijelölését és az aktuális elemet; az utasításszintű híváslánc megerősíti, hogy az automatikus lépés ezt a közös léptetőt használja. A `0x00717d10` a `LoopSlideshow` kikapcsolt állapotában a következő index helyére `-1`-et ír. A végső képernyőállapot (marad-e az utolsó kép, változik-e a lejátszás jelzője) **NINCS MEG**; futásmérés kell egy kétképes mappán, a második kép utáni legalább két diaidő megfigyelésével. Fejlesztői jegy csak ennek eredménye után nyitható. |
| G2, `+0x5a` és `+0x5b` | A `0x00717560` Ghidra-kimenetének hívóhelyei disassembly alapján helyesek: a nézet az `EDI`-n érkezik, a kimeneti listatároló az `ESI`-n; a gyűjtő csak a `+0x5a == 0` elemeket teszi a sorozatba. A `+0x5b` értékét ez az algoritmus nem vizsgálja, így a `+0x5b` szemantikai neve nem befolyásolja a vetített halmazt (**nem blokkoló**). A `+0x5a` a kapcsolódó specifikációkban kizáró/elnyomó jelző, de hogy ez pontosan a rejtett képeket jelenti-e, **NINCS MEG**; döntő mérés: egy normál mappában egyetlen, Picasában elrejtett képpel `Ctrl+4`, majd annak láthatóságát rögzíteni. |
| G3, az `editoneup` vezérlősáv | A `0x005c4ce0` az időzített képkocka- és egér-eseményeket kezeli; ebből önmagában nem dől el a normál `editoneup` sáv láthatósági szabálya. A jelenlegi PicasaPy szünetkor megmutatja a sávot, lejátszáskor elrejti, majd egérmozgás után időzítve rejti el (`SlideshowView.qml:445-469`, `SlideshowControls.qml:11-53`). Eltérésre futásmérés kell: `Ctrl+4`, egérmozgás a kép közepén és a sáv körül, szünet, majd mozdulatlanság; minden állapotban képernyőképpel. |
| G4, sérült, hiányzó vagy hálózaton elérhetetlen kép | A `0x0075f430` képkészenléti órát és megjelenítési útvonalat kezel, a `0x006d00c0` pedig erőforrás-/képkocka-frissítő, nem hibaág. A korábbi címhozzárendelést a `0x00569260` és a `0x005683a0` hívóadatainak független összevetése cáfolja. A hiba végső felhasználói hatása **NINCS MEG**. Döntő egyetlen futásmérési menet három külön képpel: csonka képfájl, megszűnt helyi fájl és elérhetetlenné tett hálózati út; rögzítendő, hogy a vetítés átugorja, megállítja vagy jelzi-e a hibát. Ez blokkolja a teljes folyamat lezárását. |
| Windows képernyőkímélő | A kilépési függvényben nem látható közvetlen beállításírás, de az indirekt rendszerhatás és a tétlenség alatti aktiválás nem állapítható meg indexnegatívból. Döntő mérés: az eredeti `Ctrl+4` előtt és után a Windows képernyőkímélő beállításának rögzítése, majd a vetítést a beállított tétlenségi időn túl figyelni. Felhasználó által látható viselkedés, ezért nem jelölhető nem blokkolónak. |
| G5, fejléc `play` nem aktuális mappán | A `0x005de8e0` hívóhely a `play` ágban az alkalmazásobjektumot adja a `0x005e0f70`-nek, az ág pedig csak a `FUN_005e8a70(this, 0)` hívást végzi, sorindex nélkül. A vetítésindító az objektum aktuális `[this+0xea8]` nézetét olvassa. Ez megadja a közvetlen forrást a hívás pillanatában, de a nem aktuális mappafejléc kattintása előtte átállítja-e ezt a nézetet, **NINCS MEG**. Döntő mérés: egy másik mappafejléc `play` gombja, előtte és utána a mappa neve és az első vetített kép rögzítésével. |
| G6, Enter, `Ctrl+R`, `Ctrl+4` kapu | Megválaszolva meglévő dekompilációból és a hívóhely disassemblyjéből. A `0x005e6710` először a `0x00760970` normál vetítési billentyűkezelőt hívja; a `Ctrl+4` közös útját kezelő `0x005e60d0` a `[this+0x332f] != 0` állapotnál visszatér. Emiatt az eredeti normál vetítésben az `Enter` és a `Ctrl+R` nem jut a főablak műveletágába. A `0x005696c0` nyers kapuja: a `previewclip2` elem létezzen és `[elem+0x20c] == 0` legyen, továbbá a `this+0x668` és `this+0x99c` Windows-ablak téglalapjai egyezzenek; csak ekkor igaz. A `0x005e8a70` igaz kapunál az `only_1up_toggle` műveletet próbálja, és a `0xf4242` visszatérés megszakítja az indítást. A mezők beszédes neve **NINCS MEG**, de a tényleges nyers kapu ismert; külön Ghidra-kör nem szükséges. |
| G7, zene | A `0x0075cdc0` a `Preferences/MP3SlideshowPath` értéket tölti a hangobjektum `+0x48` mezőjébe. A `0x00760070` szünetkapcsoló meghívja a `0x0075d570`-et, amely a hangobjektum állapotmezőjét váltja; a sávlista sorrendje, az ismétlés és a hallható szünet/kilépés eredménye ezekből nem dől el. A jelenlegi PicasaPy a zenefájl-lista aktuális elemét játssza, a végén körbeér (`SlideshowMusic.qml:11-36,46-49`). Döntő mérés: két eltérő nevű sávval ellenőrizni a sorrendet, végigjátszást, szünet/folytatást és kilépést. |
| G8, vetítésindítási kapuk | A `0x005e8a70` ág disassemblyje rögzíti a feltételt: ha `DAT_00d67914 != 0`, a `preview` elem létezik, `[preview+0x20c] == 0`, továbbá `[this+0x3094] > 0` vagy `[this+0x30a0] > 0`, és `[this+0x332e] != 0`, az indítás `-1`-gyel visszatér. A mezők pontos funkcióneve nem azonosított; a viselkedési feltétel statikusan ismert, a címkézés **nem blokkoló** és új Ghidra-kört nem indokol. |
| Üres mappa, kijelölés, videó, kattintási terület | A jelenlegi forrás szerint az üres indulás előtt teljes képernyőre vált (`MainSlideshow.qml:60-70`), a sorozat nem függ a kijelöltek számától (`MainSlideshow.qml:60-68`, `SlideshowView.qml:194-218`), a videót kihagyja (`SlideshowView.qml:194-218`), a képközép kattintási sávja 14 képpont (`SlideshowControls.qml:56-70`). Az eredeti oldali üres ablakváltás, többes kijelölés, videólejátszás és `auto2` kattintási terület mért látható hatása külön képernyőképes megfigyelést kér; ezek a már megadott egyetlen Windows-mérési menet további állapotai. |
| D2 és D5 korábbi eltérés | D2 szűkítve marad az `Enter` és a `Ctrl+R`/`Ctrl+Shift+R` különbségére; a `Fel`/`Le`, számjegyek, `Pause`/`Play` jelenlegi forrásban megvan. D5 lezárva: a jelenlegi fordítás megegyezik a hivatalos magyar súgószöveggel. |

### A jegy „Kész, ha” pontjai

| Feltétel | Állapot |
|---|---|
| Belépési pontok: Nézet menü, eszköztár/fejléc, gyorsbillentyű, néző, mappa/album helyi menü | ✅ A két felső menüparancs, `Ctrl+4`, fejléc `play` és szerkesztő gomb útja megvan; a mappa és album helyi menü egyik rendszerben sem tartalmaz slideshow tételt. ⛔ Nem aktuális mappafejléc esetén a kattintás előtti nézetváltás futásban nem bizonyított. |
| Vetített elemek: kijelölt vagy teljes nézet, mappa/album, fotó és videó | ✅ Statikusan igazolt, hogy a kijelölés nem szűri a teljes aktuális nézetet, és üres nézetnél csendes a visszatérés. ⛔ A `+0x5a` pontos UI-jelentése, a többes kijelölés futási képe és a videó lejátszása mérendő. |
| Vezérlők, alapértékek és megőrzés | ✅ A diaidő, ismétlés, zene jelölő, átmenet és a mostani billentyűforrások összevetve. ⛔ A Timeline normál vetítésbeli eltérése, a sáv láthatóságának futási képe és a zene lista sorrendje még teendő. |
| Kilépési hatás, visszatérés, kijelölés, képernyőkímélő és tárolás | ✅ A visszatérési nézet, aktuális kép és vetítési kilépési ág statikusan összevetve. ⛔ A lista végi képernyőállapot és a Windows képernyőkímélő hatása mérendő. |
| Rejtett, sérült, elérhetetlen kép és üres kijelölés | ✅ Az üres kijelölés és üres nézet útja statikusan összevetve. ⛔ A rejtett kép jelzője és a hibás vagy elérhetetlen kép látható kezelése mérendő. |

### A két független út és a cáfoló kísérlet zárókörös kiegészítése

- **A út, utasításszint:** `annot_disasm.py` a `0x005de8e0` → `0x005e0f70` fejléc-hívásnál, a `0x005e6710` → `0x00760970` billentyűútnál, a `0x005e60d0` kapujánál és a `0x005c4ce0` → `0x0075f430` → `0x0075fb20` időzített léptetésnél. A `0x00717eb0` hívója a `0x00717560` paraméter- és kimeneti regisztereit is igazolja.
- **B út, külön kimenet és másik réteg:** a `referencia/ghidra/2026-11-16-koteg-438-465.txt` `FUN_0075f430`, `FUN_00717560`, `FUN_005e0f70` és `FUN_0075cdc0` dekompilációi, a korábbi `2026-10-17-qshow-2.txt` `FUN_005e60d0` kimenete, valamint a `tre` erőforrások és a jelenlegi forrás. Ahol ugyanarra a viselkedési útra vonatkozik, az utasításszintű olvasattal egyezik. A futásmérés hiányát ez nem pótolja, ezért a teljes következtetés feltételes.
- **Cáfoló kísérlet:** megpróbáltam a `+0x5b` bájtot a vetített sorozat kizáró feltételének tekinteni, és a `+0x5a` jelzőt automatikusan „rejtett képnek” nevezni. A `FUN_00717560` Ghidra-kimenete a `+0x5a` bájtot vizsgálja; a hívóhely disassemblyje az `EDI` nézetet és `ESI` kimeneti tömböt erősíti meg, és a `+0x5b` nem szerepel a listaképző ágban. Az eredmény cáfolja a `+0x5b` kizáró szerepét, de nem igazolja a `+0x5a` emberi jelentését. Ugyanazzal a bizonyítási mércével ellenőriztem a cáfolatot: a kapcsolódó specifikációk is csak kizáró/elnyomó jelzőnek nevezik; a rejtett képre vonatkozó megfeleltetést a Picasa-futásmérésnek kell eldöntenie.
- **Belépési pontot cáfoló kísérlet:** a korábbi besorolás szerint a `0x9c6d` a mappa/album helyi menüjéből indította volna a vetítést. Ezt a `0x00732160` teljes függvényének közvetlen disassemblyjével ellenőriztem; az Album menüépítő parancsai és feliratai között nincs `ID_ALBUM_SLIDESHOW`/`0x9c6d`. Független ellenőrzésként a teljes, szűretlen Folder-helyi menüleltárt (`0x007319f0`, 18 tétel; `picasa-menu-parancsok-viselkedes.md` 32.1) és az `eMenuLabelFolder` osztály besorolását vetettem össze; ez a felső Mappa főmenü osztálya, ahogy a menüviselkedés-lap 30. adagja helyesbíti. A jelenlegi `FolderContextMenu.qml`/`AlbumContextMenu.qml` ugyanígy nem kínál helyi slideshow parancsot, míg a `PicasaFolderMenu.qml` igen. A cáfolatot tehát két külön forrású úton ellenőriztem; a helyes következtetés az, hogy a két jobbklikk-menü nem belépési pont, és ebből nem következik fejlesztői eltérés.

#### D6. A nem ismétlődő vetítés lista végén maradjon nyitva

**Eredeti:** a `0x00717d10` hurok nélkül `-1` következő indexet állít be; a `0x0075f430` és időzítőhívója (`0x005c4ce0`) nem hívja a vetítést lezáró `0x0075de50` függvényt. A végső képernyőállapot futásmérésig nyitott.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00717d10`, `0x0075f430`, `0x005c4ce0` | `SlideshowView.qml:278-282` | Ha a mért eredeti a vetítőben marad az utolsó képen, a következő dia hiányánál ne hívjunk `stop()`-ot; tartsuk meg az utolsó képet és a vetítőt. |

**Kész, ha:** a futásmérés igazolja, hogy nem ismétlő beállításnál az eredeti az utolsó képen marad, a PicasaPy sem lép ki, és a bezárás továbbra is az eredeti `Esc`/kilépés műveletre történik.

#### D7. A kézi léptetés lista-végi viselkedése

**Eredeti:** a `0x0075fb20` előre léptetésnél az utolsó elemről a `0x00717bb0`-n át az elsőt választja, a `LoopSlideshow` értékétől függetlenül; a `0x00717eb0` az első elemről hátra nem lép.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x0075fb20`, `0x00717eb0` | `SlideshowView.qml:201-204, 278-286` | Kézi előre lépéskor az utolsó elemről mindig az elsőre lépjen; kézi hátra lépéskor az első elemen maradjon, a `LoopSlideshow` beállításától függetlenül. Az automatikus léptetést külön kezelje. |

**Kész, ha:** futásmérés után kézi előrelépés az utolsó képről az elsőre visz akkor is, ha az ismétlés ki van kapcsolva; kézi hátralépés az első képen nem változtat képet akkor sem, ha az ismétlés be van kapcsolva.

### Zárókör 2 (2026-11-18)

Az alábbi táblázat az eddig megmaradt állításokat a jelenlegi forrással
ellenőrzi. A korábbi Ghidra-kérésekre van kimenet; új dekompiláció nem dönti el
a nyitott kérdéseket, mert azok a futó program képernyőn vagy hangban látható
hatásai. A `+0x5b` és a kapumezők beszédes neve nem befolyásol felhasználói
műveletet, ezért ezek nem blokkolók.

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Időzített lista-vég: `0x0075f430`, `0x0075fac0`, `0x00717d10`; a végső ablakállapot közvetlenül nem következik a törzsekből. | `SlideshowView.qml:278-282` leállítja a vetítőt, ha nincs következő kép. | Kétképes mappán, ismétlés nélkül mérni, hogy az eredeti az utolsó képen megáll, szünetel vagy kilép; csak ezután dönthető el D6. |
| A `0x00717560` listaépítő a `+0x5a == 0` elemeket veszi fel; a bájt neve nem ismert. | `controller_photo_list_mixin.py:117-120`, `MainSlideshow.qml:131-134`: a rejtett képek alapból kiszűrődnek, de `showHidden` mellett bekerülhetnek. | Egy Picasában elrejtett képet tartalmazó mappával mérni, bekerül-e a normál vetítésbe. A `+0x5b` jelentése nem blokkoló, mert a listaépítő nem olvassa. |
| #375 futásmérés: `picasa-gyorsbillentyuk.md:2336-2354,2406-2424`; Space szüneteltet és folytat, Escape visszatér, szünetben a sáv látszik, folytatáskor eltűnik. A vezérlők pontos készlete, a mutató és kattintás hatása nincs mérve. | `SlideshowView.qml:445-469`, `SlideshowControls.qml:56-70,174-241`. | A mérést ugyanazon Windows-meneten ki kell egészíteni képernyőképpel és egérpróbákkal; a már mért Space/Escape eredményt nem kell újra eldönteni. |
| `editoneup.tre:62-66`: a normál vetítőben a Timeline rejtett. | `SlideshowView.qml:55-57`, `SlideshowControls.qml:183-188`: a gomb a beállítástól és képernyőmélységtől függően látszhat. | Azonos gépen, alapbeállítással rögzíteni, látszik-e a Timeline; eltérés esetén D1. |
| `0x00760970`, `0x005e6710`, `0x005e60d0`: a normál útban nincs `Enter` vagy `Ctrl+R` művelet. | `SlideshowView.qml:677-680,706-711`: Enter léptet, Ctrl+R forgat. | Statikus eltérés: D2, a normál vetítésben ez a két művelet ne fusson. |
| `0x0075eda0`, `0x0075f006-0x0075f2e2`: a videó külön lejátszási ágra kerül, a vágási pontok a lejátszóba jutnak, az időzítés a film hosszából készül. | `SlideshowView.qml:194-218`: a videó kimarad. | Egy ismert hosszú és vágott videóval rögzíteni a lejátszást, a kezdő- és záróvágást, a következő képre lépést; az eredmény pontosítja D3 diaidejét. |
| `editoneup.tre:20-23`, `macros.tre:21-33`, `0x00760240`: az `auto2` nagy felső kattintási területet használ, az `auto` műveletét hívja. | `SlideshowControls.qml:56-70`: 14 képpont magas kattintási terület. | A kép közepére és az alsó vezérlősáv fölötti részre külön kattintani; ha mindkettő kapcsolja a vetítést, D4 a középső terület kiterjesztése. |
| `0x0075fb20`, `0x00717eb0`: kézi előrelépés az utolsó elemről az elsőre fordul; hátra az első elemen marad. | `SlideshowView.qml:201-204,278-286`: a hurok beállítása a kézi léptetést is szabályozza. | Statikus eltérés: D7; a két határhelyzetet ismétlés ki- és bekapcsolásával mérni kell, majd a kézi műveletet az eredetihez igazítani. |
| `0x005de8e0`, `0x005e0f70`, `0x005e8a70`: a fejléc `play` ága az éppen aktuális ablakot adja át, de a fejléc kattintása előtti nézetváltás nyitott. | `MainSlideshow.qml:60-68,131-134`: az aktuális nézőképből vagy kijelölésből indul. | Másik mappa fejlécén levő `play` gombbal rögzíteni a vetített mappát és az első képet. |
| `0x0075cdc0`, `0x0075ca20`, `0x0075d570`: a zene forrása beállítható vagy alapértelmezett mappából jön; az alapértelmezett mappa, a sorrend és a hallható szünet/ismétlés nincs feloldva. | `controller_slideshow_mixin.py:188-211`, `SlideshowMusic.qml:11-49`: mappasorrend és lejátszás van megadva. | Két eltérő nevű hangfájllal rögzíteni a sorrendet, a végén történő viselkedést, szünetet, folytatást és kilépést; egy második próbában ürítse ki a Picasa zeneútvonal-beállítását, és rögzítse, honnan próbál zenét betölteni. |
| Kilépés és képernyőkímélő: a vetítési függvényben nincs közvetlen Windows-beállítás írása; a rendszer tétlenségi viselkedése és a teljes automatikus kijelölés-út nyitott. | `MainSlideshow.qml:92-112`: visszaállítja az ablakot és a vetítő indexét; a programképernyő-védő előnézete külön út (`:73-84`). | A Windows-beállításokat és a Picasa beállításait futtatás előtt/után összevetni; az eredeti vetítést a beállított tétlenségi határig figyelni, majd Escape után rögzíteni az aktuális képet és kijelölést. |
| Sérült, hiányzó és hálózaton elérhetetlen kép: `0x006d00c0` képkocka-/erőforrás-frissítő, a betöltési hiba felhasználói hatása nincs azonosítva. | `SlideshowCurrentImage.qml:1-6,76-84`: nincs külön `Image.Error` kezelőág. | Három külön próbában csonka fájlt, törölt helyi fájlt és elérhetetlen hálózati útvonalat megnyitni; rögzíteni az üzenetet, az átugrást, a megállást vagy az üres képet. Ez a fő blokkoló. |
| Üres mappa: `0x005e8b4b-0x005e8b55` csendben visszatér. | `MainSlideshow.qml:60-70`: előbb teljes képernyőre vált, aztán visszaáll. | Üres mappán mérni, látszik-e ablakváltás vagy más felületi villanás. |

**Cáfoló kísérlet, az automatikus kilépéskori kijelölésre:** megpróbáltam
megcáfolni a korábbi állítást, hogy az utoljára mutatott kép minden automatikus
lépés után biztosan a könyvtár aktuális kijelölése lesz. A `0x0075f430`,
`0x0075fac0` és `0x00569260` disassemblyjében nincs közvetlen hívás a
`0x005704d0` kijelölésváltóra; a Ghidra-kimenet a nézet indexének léptetését
mutatja, nem a teljes kilépéskori felületi állapotot. Az indirekt hívásokat ez
nem zárja ki, ezért az eredmény nem cáfolja véglegesen az állítást: a korábbi
biztos megfogalmazást visszavonom, a végső kijelölést mérésre hagyom. A
cáfoló kísérletet ugyanazzal a mércével ellenőriztem: a disassembly és a
Ghidra-kimenet ugyanazt a közvetlen léptetési utat mutatja, de egyik sem
helyettesíti a visszatérés utáni képernyőkép megfigyelését.

### A jegy „Kész, ha” pontjai, záróellenőrzés

| Feltétel | Állapot |
|---|---|
| Belépési pontok: Nézet, eszköztár és fejléc, gyorsbillentyű, néző, helyi menü | ✅ A felső menük, `Ctrl+4`, fejléc `play` és néző útja dokumentált; a mappa és album helyi menüben nincs indító. ⛔ Nem aktuális fejléc `play` esetén az eredeti kijelölés mérése hiányzik. |
| Vetített elemek: kijelölés, mappa vagy album, fotó, videó | ✅ A bináris a teljes aktuális listát járja, nem csak a kijelölteket. ⛔ A rejtett kép jelentése és a videó tényleges futása mérendő. |
| Vezérlők, alapértékek, megjegyzés | ✅ A diaidő, ismétlés és zenei beállítás bináris útja dokumentált; a #375 a Space/Escape hatását méri. ⛔ A Timeline feltételét, kattintási területet és zene hallható viselkedését ugyanazon beállításokkal kell rögzíteni. |
| Kilépés, visszatérés, kijelölés, képernyőkímélő és tárolás | ✅ Visszatérési nézet és PicasaPy visszaállítása forrásból ellenőrizve. ⛔ Az eredeti automatikus kijelölés, Windows-képernyőkímélő és tárolt beállítások változása mérendő. |
| Rejtett, sérült, elérhetetlen kép és üres lista | ✅ A csendes üres eredeti ág binárisan igazolt. ⛔ A rejtett és betölthetetlen képek látható kezelése, valamint az üres ablakváltás hatása mérendő. |

### Bizonyítottsági fok, független utak

**Feltételes.** A statikusan olvasható utaknál az A és B bizonyíték egyezik,
de a teljes kérdés felhasználói hatásai közül többhöz nincs eredeti Windows-
futásmérés. Ezért a teljes folyamatot nem nevezem megerősítettnek.

- **A út:** az eredeti Picasa célzott Capstone disassemblyje, a hívók
  regiszter- és paraméterátadása, továbbá az erőforrásfájlok. A konkrét
  címek és leletek a fenti táblázatban szerepelnek.
- **B út:** a már létező Ghidra-kimenetek (`2026-11-16-koteg-438-465.txt`,
  `2026-11-16-7022-7031-7033-colab-decomp.txt`), a `.tre` adatok, a #375
  eredeti mérésének dokumentált képei és a jelenlegi PicasaPy-forrás. Ezek
  ugyanazokat a már statikusan igazolt belépési, billentyű- és listaútvonalakat
  támasztják alá. A futásmérésre hagyott hatásokban nincs két egyező út.
- **Mérési bizonyíték:** `picasa-gyorsbillentyuk.md:2336-2354,2406-2424`,
  #375: 26 rögzített kép; a vetítés indítása, szüneteltetése, folytatása és
  bezárása, továbbá a sáv szünetbeli láthatósága dokumentált. A helyi
  munkafában maguk a képfájlok nincsenek meg; a specben rögzített mérési
  eredmény rendelkezésre áll.

### Egyetlen szükséges eredeti Windows-mérési menet

A hívó ezt a Colab-végrehajtónak adja fel. Minden állapotváltás után készüljön
képernyőkép és ablaklista; az egér- és hangpróbáknál a bemenetet és a hallható
eredményt is jegyezze fel. Használjon elkülönített Windows-profilt és külön
tesztmappákat, hogy a tárolt beállítások és a tesztadatok visszaállíthatók
legyenek.

1. Rögzítse a Picasa beállításait és a Windows képernyőkímélő-beállításait.
   Jegyezze fel a Picasában kijelölt képet, az aktuális mappát, a diaidőt, az
   ismétlést, a zene mappáját és a zene be/ki állapotát.
2. Egy legalább három fotós mappában jelöljön ki három nem szomszédos képet,
   majd külön indítsa a vetítést a Nézet menüből és `Ctrl+4`-gyel. Rögzítse
   az első képet, a további sorrendet, a vezérlősáv minden gombját, és a
   kilépés utáni képet és kijelölést. Ismételje meg kijelölés nélkül, majd
   egyetlen kijelölt képpel is. Nyisson meg egy képet a nézőben, onnan a
   `Play` gombbal indítson, majd a mappa vagy album fejlécének gombjával is;
   rögzítse, melyik kép és lista indul. A gombsor `Előző` és `Következő`
   műveletét is próbálja ki, majd az egyik menetet `Escape`-pel, a másikat a
   Kilépés gombbal zárja le. Külön Space-szel szüneteltesse és folytassa; a
   már ismert #375 eredmény megismétlése mellett vigye a mutatót a kép közepére
   és a gombok fölé, majd kattintson a kép közepére és az alsó sáv fölötti
   területre.
3. Egyetlen elrejtett képet tartalmazó mappában indítsa újra a normál
   vetítést, és rögzítse, bekerül-e. Egy külön üres mappával indítson; jegyezze
   fel az üzenetet, ablakváltást és esetleges villanást.
4. Egy külön mappában legyen egy támogatott, ismert időtartamú és vágott
   videó. Rögzítse, elindul-e, a lejátszás tényleges hosszát, a megadott
   vágási pontok hatását és a következő képre váltást. Egy másik menetben
   csonka kép, törölt helyi kép és elérhetetlenné tett hálózati útvonal
   szerepeljen külön-külön; mindegyiknél rögzítse az üzenetet, üres képet,
   átugrást vagy megállást.
5. Két különböző nevű zenefájllal rögzítse az első és a következő számot, a
   lejátszás végén történő viselkedést, a Space szünetét és a kilépés utáni
   hangot. Először a Picasa zenemappa legyen az ismert tesztmappa, majd egy
   másik próbában ürítse ki az `MP3SlideshowPath` beállítást, és rögzítse az
   eredeti alapértelmezett forrását.
6. Ismétlés kikapcsolva és bekapcsolva is léptessen kézzel az utolsó képről
   előre és az elsőről hátra. Egy kétképes mappán várja meg az utolsó
   automatikus dia után a következő időzített váltást; rögzítse, hogy a kép,
   vetítő és lejátszás állapota mi lesz.
7. Tegyen egy másik mappát aktuálissá, majd kattintson egy nem aktuális mappa
   fejlécének `play` gombjára; jegyezze fel a mappa nevét és az első képet.
8. `Ctrl+4` előtt és Escape után újra rögzítse a Picasa és Windows beállításait.
   Ezután egy külön menetben várja meg a Windowsban beállított tétlenségi
   határt, és jegyezze fel, aktiválódik-e a képernyőkímélő. Ne állítson be
   helyette becsült időt. A külön Windows-profilban módosítsa a diavetítés
   beállításai közül a felületen elérhetőket, majd indítsa újra a Picasát és
   ellenőrizze, mely értékek maradtak meg. A `Preferences` értékeket és a
   `.picasa.ini` fájlokat a próba előtt és után hasonlítsa össze; a normál
   indítás és Escape közötti eltérést különítse el a szándékosan módosított
   beállításoktól.

Ez az egy mérési menet az egyetlen blokkoló. Új Ghidra-kör nem kell: a nyitott
tételek felhasználói hatása mérendő, nem egy függvénynév vagy mezőnév.

### Javasolt fejlesztői jegytörzsek

Az alábbi szövegek a statikusan igazolt eltérések fejlesztési kiindulópontjai;
a mérés után a feltételes tételeket csak akkor kell felvenni, ha az eredeti
Windows-eredmény alátámasztja őket.

#### D1. A normál diavetítés Timeline gombja

Eredeti: a normál `editoneup` vetítőben a `timeline` rejtett (`editoneup.tre:62-66`).

Nálunk: a Timeline gomb feltételesen látható (`SlideshowView.qml:55-57`, `SlideshowControls.qml:183-188`); alapértelmezett `BigSlideshow2` mellett 16 vagy 32 bites képernyőn megjelenhet.

Teendő: a normál diavetítésben rejtse el a Timeline gombot; az Időrend saját vetítése maradjon külön.

Kész, ha: normál `Ctrl+4` vetítésben nem látszik a Timeline, az átmenetválasztó látható marad, és az Időrend bemutatója nem változik.

#### D2. Enter és Ctrl+R normál vetítésben

Eredeti: a normál vetítés billentyűútja az `Enter` és `Ctrl+R` parancsra nem végez műveletet (`0x00760970`, `0x005e6710`, `0x005e60d0`).

Nálunk: az `Enter` léptet, a `Ctrl+R` és `Ctrl+Shift+R` forgat (`SlideshowView.qml:677-680,706-711`).

Teendő: normál vetítésben ne kezelje ezeket a billentyűket; a `Fel`/`Le`, számjegy, `Pause` és `Play` maradjon működő.

Kész, ha: `Enter`, `Ctrl+R` és `Ctrl+Shift+R` nem módosít képet vagy lejátszást, a többi felsorolt billentyű továbbra is az eredeti műveletét végzi.

#### D3. Videó a diavetítésben

Eredeti: a videó saját lejátszási ágba jut, a vágási pontokat átadja a lejátszónak, a diaidőt a film hosszából számítja (`0x0075eda0`, `0x0075f006-0x0075f2e2`).

Nálunk: a videókat a vetítési sor átugorja (`SlideshowView.qml:194-218`).

Teendő: a mérésben látott eredeti videólejátszás, vágás és váltási idő alapján vegye be a videót a diavetítésbe.

Kész, ha: ismert tesztvideó indul, az eredeti Picasában mért kezdő- és záróvágást követi, majd a mért idő után a következő képre lép.

#### D4. Az automatikus léptetést kapcsoló kattintási terület

Eredeti: az `auto2` terület az `auto` műveletét hívja, és az erőforrás megszorításai a felső részen nagy kattintási területet írnak le (`editoneup.tre:20-23`, `macros.tre:21-33`, `0x00760240`).

Nálunk: kattintási területe 14 képpont magas (`SlideshowControls.qml:56-70`).

Teendő: ha a középső kattintást a Windows-mérés igazolja, terjessze ki a kattintási területet a mért határig úgy, hogy a vezérlősáv gombjai működjenek.

Kész, ha: a kép közepén végzett kattintás a mért módon kapcsolja a szünetet és folytatást; a vezérlősáv minden gombja továbbra is elérhető.

#### D7. Kézi léptetés a lista két szélén

Eredeti: előre az utolsó képről az elsőre fordul, hátra az első képen marad (`0x0075fb20`, `0x00717eb0`).

Nálunk: a kézi léptetés a hurokbeállítást követi (`SlideshowView.qml:201-204,278-286`).

Teendő: a méréssel egyezően különítse el a kézi és az automatikus léptetést; kézzel előre az utolsó képről forduljon az elsőre, hátra az első képen maradjon.

Kész, ha: mindkét határeset a mért eredeti szerint működik ismétlés be- és kikapcsolt állapotában.

#### D6. Automatikus lista-vég, csak ha a mérés eltérést igazol

Eredeti: a lista végén látható állapot nincs eldöntve; a `0x00717d10`, `0x0075f430` és `0x005c4ce0` út önmagában nem bizonyítja, hogy a vetítő megáll vagy kilép.

Nálunk: a következő kép hiányakor a vetítés leáll (`SlideshowView.qml:278-282`).

Teendő: csak akkor változtassa meg a leállást, ha a kétképes, ismétlés nélküli mérés szerint az eredeti az utolsó képen marad.

Kész, ha: a mért eredeti végállapot megegyezik a PicasaPy-ban, és a vetítés továbbra is az eredeti Escape vagy Kilépés művelettel zárható be.

### Zárási döntés

**A #7060 kutatási jegy még nem zárható le. Egyetlen blokkoló** a fenti,
képernyőképes Windows-mérési menet; elsőbbségi része a csonka, hiányzó és
elérhetetlen hálózati képekre vonatkozó hibaút. A menet a többi megmaradt
felhasználói hatást is ugyanabban a külön Windows-profilban dönti el. A
a forrás és a bináris vizsgálata lezárult, új Ghidra-kérés nincs.

**Megerősített statikus eltérések:** D2, D7; D1, D3 és D4 a megadott Windows-
beállításokkal és kattintási próbákkal még ellenőrizendő. D6 csak akkor
fejlesztési tétel, ha a lista-végi mérés eltérést mutat. A rejtett kép,
zenesorrend, fejlécindítás, üres lista, automatikus kilépési kijelölés,
képernyőkímélő és képhiba eredménye a méréstől függ. Ezek külön kutatási
jegyet nem igényelnek, mert ugyanannak a #7060 folyamatnak a nyitott pontjai.

### #7234 statikus kiegészítés a G1/G2/G4/G7 kérdésekhez (2026-11-18)

**G1 - léptető és visszatérés.** A `0x00717d10` előbb a `0x0071c8c0`-t,
majd a `0x00717560`-at hívja; ha az nulla, a `0x00717420`-at próbálja. Ha
mindkettő nulla, a `view+0x2e0` mezőbe `-1`-et ír és 0-val tér vissza;
egyébként a helper értékét adja vissza (`2026-11-18-koteg-466-495.txt:3617-3671`).
A függvény nem olvassa a `LoopSlideshow` mezőt, és maga nem írja a `+0x390`
mezőt. A `0x00717c50` közvetlen hívó a hívás után a célértéket a `+0x390`-be
írja (bináris `0x00717c50:0x00717cec-0x00717cf5`). A jegyben megnevezett
`0x005c4ce0` és `0x00571e50` a `0x0075f430` hívói, nem a léptető közvetlen
hívói; a `0x0075f430` → `0x0075fac0` úton a léptető visszatérési értékét
nem használják (`2026-11-16-koteg-438-465.txt:4871-4891`, bináris
`0x0075fac0`). Az utolsó kép, ismétlés nélküli eredeti UI-végállapota továbbra
is nyitott; PicasaPy a vetítőt nyitva hagyja az utolsó képen
(`SlideshowView.qml:288-299`, mért #7209).

**#486 hívói pontosítása.** A `0x005c4ce0` `0x13` eseményágban a
`0x0075f430` visszatérését igaz/hamis jelzésként használja: nem nulla értéknél
meghívja a `0x0075fb20(param_1+8, 1)`-et, majd `0xf4241`-gyel tér vissza
(`2026-11-05-2026-11-05-sav-elrejtes-6531.txt:273-296`). A `0x0075f430`
útján a léptető saját visszatérése nem jut vissza ehhez a feltételhez. A
`0x00571e50` törzse nincs a helyi Ghidra-kimenetekben; a meglévő találatok csak
hívóhely-xrefek, ezért annak szünet-, lista-végi vagy kilépési ágát nem
állítom. PicasaPy oldalon a lejátszási végállapot forrása
`SlideshowView.qml:288-299`; a LoopSlideshow-paritás mindaddig nyitott,
amíg az eredeti hívási ág nem tisztázott.

**G2 - `+0x5a`/`+0x5b`.** A `0x00716d70` a bejárt elemek `+0x5b` mezőjét
nullázza; `param_3 == 0` esetén `+0x5a=1`, nem nulla `param_3` esetén
`+0x5a=0` (`…466-495.txt:3674-3794`). A `0x00714010` csak `+0x5a`-t
állítja 1-re, és akkor `+0x59` dirty jelzőt is ír, ha az előző `+0x5a` nulla
(bináris `0x00714010`). A `0x00781680` ezt a segédet a `0x0078299a` helyen,
egy előző feltételes ág után hívja; az ág nem bizonyítja önmagában, hogy a
mező rejtett képet, fejlécsort vagy hiányzó fájlt jelent. A `0x00717560`
bejáró csak a `+0x5a == 0` elemeket teszi a lista kimenetébe, ezért a nem nulla
érték szemantikája: kizárás a diavetítési listából (`2026-11-16-koteg-438-465.txt:4595-4678`).
Azt, hogy a kérdezett három állapot közül melyik íróág állítja 1-re, és a
`+0x5b` jelentését ez nem dönti el.

**G4 - fájlbetöltési hiba.** A `0x0075eda0` nem általános fotóbetöltő:
`moviestart`/`movieend` metaadatot keres, videóidőt számol, és 0-val tér vissza
(`…466-495.txt:3795-4106`). A közvetlen hívók közt `0x0075de50`, `0x0075f430`,
`0x0075fb20`, `0x00760240` van. Sérült/hiányzó/hálózati képfájlra adott
eredeti viselkedés ebből nem következik. PicasaPy slideshow-képútjának eredeti
hiba-paritása ezért nyitott.

**G7 - zeneszál.** A `0x0075ca20` meghívja a `0x0075cdc0` forrásépítőt, majd
az `+0x48` listához jutott forrásból dolgozik (`…466-495.txt:4110-4267`). A
`0x0075cdc0` a `Preferences\MP3SlideshowPath` értékéből egyetlen listatételt
épít; üres beállításnál a `0x00cb224c` (`mp3\\`) útvonalrészt a
`0x009a38a0` helperen átoldja, majd a `0x009a3db0` enumerátort hívja (bináris
`0x0075cdc0`). A forráslista rendezése nem látható itt, ezért rendezett vagy
véletlen sorrend nem állítható. A `0x0075d570` az audioobjektum `+0x18` vagy
`+0x1c` vtable metódusát váltja és a thread `+0x1a4` állapotát állítja;
ez a pause út. A `0x0075d620` kilépési útban `0x3e8` ms számlálóról indul,
`0xa` ms lépésekben vár, majd `close audio1`-t küld. A külön `0x0097b420`
várakozót a `0x0075c960` destruktor `0` argumentummal hívja, tehát a két
várakozási út nem ugyanaz (bináris `0x0075d620`, `0x0075c960`). PicasaPy
albumból, bekapcsolt mappából vagy beállított mappából olvas; az utóbbi
`.mp3` fájljait kis-/nagybetűtől független fájlnév szerint rendezi
(`controller_slideshow_mixin.py:173-196`). Az eredeti enumerátor sorrendje és
a repeat szabály még nem eldöntött.

#### Eredeti / nálunk / teendő - alapértelmezett zeneforrás

Eredeti: ha `MP3SlideshowPath` üres, a `0x0075cdc0` a `mp3\\` alapútvonalat
oldja fel a `0x009a38a0` segéden át, majd a `0x009a3db0` enumerátort hívja
(`0x0075cdc0`). A tényleges abszolút alapmappa a kimenetből **NINCS MEG**.

Nálunk: a `view/slideshowMusicFolder` alapértéke üres
(`controller_slideshow_mixin.py:146-148`), ezt a `Path("").expanduser()`
út a folyamat aktuális könyvtáraként kezeli, majd ott keresi a `.mp3` fájlokat
(`:183-196`).

Teendő: az üres globális zenemappa esetén a PicasaPy az eredeti `mp3\\`
alapútvonal feloldásának megfelelő mappából olvasson; a pontos gyökérút
feloldása után ezt ne a folyamat munkakönyvtára helyettesítse.

Kész, ha:

- üres felhasználói beállításkor a PicasaPy kizárólag az eredeti Picasa által
  használt alapmappából enumerál;
- a feloldott alapmappa útja forrással vagy pontos méréssel dokumentált;
- az egyedileg beállított album-, mappa- és globális források továbbra is a
  meglévő elsőbbségi sorrendben működnek.

**Nyitott - célzott következő címek:**

- Ghidra-kör kell: 0x00717c50 - a közvetlen léptetőhívó a visszatérés után milyen lista-végi és `LoopSlideshow` állapotot ad a nézetnek
- Ghidra-kör kell: 0x00717eb0 - a két léptetőhívási ág `+0x390`-írása és lista-végi visszatérése
- Ghidra-kör kell: 0x00571e50 - a `0x0075f430`-at hívó eseménykezelő hogyan kezeli annak visszatérését, a szünetet, a lista végét és a `0x0075de50`-re kilépést; meglévő Ghidra-anyagban csak xref szerepel [blokkoló]
- Ghidra-kör kell: 0x00781680 - a `0x00714010` hívása előtti feltétel és a `+0x5a`-t okozó nézetállapot
- Ghidra-kör kell: 0x0075de50 - a fő diavetítő út és a tényleges fotóbetöltő/hibaág címe
- Ghidra-kör kell: 0x009a3db0 - a `mp3\\` útvonal enumerálásának eleje-vége sorrendje és a rendező vagy véletlen sorrendet adó hívás
- Ghidra-kör kell: 0x0075d430 - a zeneszál track-választási, ismétlési és következő sávra lépési szabálya

### #7266-kiegészítés (#501-505, 2026-11-19): slideshow-léptetés és zene

Az `0x00571e50` a `CThumbUI` vtábla `+0x74` helyén van (`0x00c9052c` alaptábla, `0x00c905a0` függvénymutató). A `+0x375` jelző 0 értékénél 1000-et, nem nulla értékénél 10-et ad; egy korábbi `+0x24` felület-ellenőrzés 100-zal tér vissza. A függvény vizsgálja a látható elemszámot (`0x00716cb0`) és egy további kiválasztási állapotot (`0x00716d10`), de a vtable-helyet meghívó eseménykezelő és az utolsó képnél a visszatérő érték fogyasztása nincs azonosítva. Következő: a `CThumbUI` `+0x74` helyének virtuális hívója és az azt követő időzítő-/léptetőág. A `0x00781680` csak sikeres `0x00717420` után, érvényes indexű, nem nulla elem mellett hívja a `0x0071b810` állapotjárót, ha a `+0x5a` és `+0x5b` bájt is nulla; az új elemnél (`+0x5d != 1` és `+0x5a == 0`) előbb `+0x59 := 1`, majd `+0x5d := 1` íródik. A `0x00717420`, `0x00717560` és `0x00717d10` csak a memóriabeli diavetítő-elemeket és jelzőket járja; a sérült, hiányzó vagy elérhetetlen fájl osztályozását nem mutatja.

Az `0x009a3db0` nem MP3-bejáró: a dinamikus könyvtárlétrehozási hívás után a 3-as „nincs ilyen út” hibánál szülőútvonalat épít és rekurzívan próbál, a 0xb7 „már létezik” értéket sikernek tekinti. Az üres `MP3SlideshowPath` beállításnál a `0x0075cdc0` a `0x009a38a0` útvonal-összeállítót, majd a `0x009a5fa0` enumerátort hívja. A `0x009a5fa0` `*.*` mintával használja a Win32 első/következő fájl keresést, alkönyvtárakba rekurzívan halad, és a jelöltet csak akkor fűzi a listához, ha az objektum vtable `+0x20` visszahívása 0-val tér vissza. A függvényben nincs `.mp3` szövegteszt és nincs rendezés; a sorrendet a Win32 keresés adja, a szűrő a még azonosítatlan `+0x20` célban van. A `0x009a38a0` pontos alapértelmezett útvonal-összetevőit a címre korlátozott diszasszembly nem nevezi meg. Nálunk a `controller_slideshow_mixin.py:176-194` `.mp3` fájlokra szűr és fájlnév casefold szerinti rendezést alkalmaz; mivel az eredeti visszahívás szűrője nincs meg, eltérés nem állítható. A `0x0075d430` a zenelistán belüli pozíciót növeli, lista-végen 0-ra állítja, majd a `0x0075d1c0` lejátszási útját hívja; ez a zenei hurok a diavetítés képhurok-beállításától külön áll. A jelenlegi `SlideshowMusic.qml:30-36` modulo-léptetése ezzel egyezik.

## #7072: A keresés teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldalt a binárisból (statikus olvasás `capstone`-nal, a programot
nem futtattam), az index `string_xrefs`/`xrefs` tábláiból, a magyar szövegtárból
(`stringres-en-hu.tsv`, `panel-feliratok-hu.tsv`) és a projekt saját
mintaadatából (`research/testdata/Picasa2/db3/wordhash.dat`, csak olvasás)
olvastam; a PicasaPy oldalt a jelenlegi forrásból. A korábbi lapok igazolt
részeire hivatkozom (`picasa-kereses-modok.md` 2-3. és idő-csúszka szakasz,
`picasa-menu-parancsok-viselkedes.md` 20., 26., 59., 60. szakasz,
`picasa-gyorsbillentyuk.md` Ctrl+F/F3 sorai, `racs-ures-allapot.md`,
`album-sorrend.md` 2.1 és 2.6, `picasa-beviteli-mezok.md`,
`picasa-idorend-bemutato-kutatas.md` a `+0x162` keresési jelzőről), nem
kutatom újra; ahol ellentmondok nekik, külön jelzem. A mintafájlt csak olvastam; az eredeti EXE-t nem másoltam a munkafába.

**A menürekord-szabály (#7012) alkalmazása.** A menüépítő `0x00559150`
rekordjaiban a parancsmező az eggyel előző rekordhoz tartozik. A keresés
menütételeire ellenőriztem: a `Search &Options` (`ID_VIEW_SEARCHVIEW`,
kulcs `0x0055a9fa`) parancsa a következő, `Small &Pictures` kulcs utáni
blokkban álló `0x9d2b` (`0x0055aa7d`); a `Save &search results...`
(`ID_SAVESEARCH`) parancsa a következő, `ID_SEARCHTOKEN` kulcs utáni
blokkban álló `0x9d52` (`0x0055c3b8`); az `ID_SEARCHTOKEN` („Show &tag as
album...") parancsa a következő, `ID_PASSPORT` kulcs utáni blokkban álló
`0x9de3` (`0x0055c402`). A diszpécser (`0x005cb990`) a `0x9d52`-t a
`0x005cc7ab` ágra (`0x005d86a0`), a `0x9de3`-at a `0x005cc7b6` ágra
(`0x005d8330`) viszi (bájttábla `0x005cde04`, dword tábla `0x005cdc30`,
bázis `0x9d44`), tehát a párosítás a kezelővel is egyezik. A `Search for...`
almenü (`0x0055c307`, hét gyerek a `0x00d6e708` címen) saját parancsmezője
nulla (`0x0055c368`).

### Következtetés

- **Egyetlen kapu van: `0x0065b840`.** A keresőmező szövegét, a hat szűrőgombot
  (csillag, arc, film, online, geocímke, másodpéldány) és a kor-csúszkát
  `0x00660c80` EGYETLEN szűrőobjektumba gyűjti, `0x00662220` pedig egyszer hajtja
  végre. Ennek mindegyik belépő (gépelés, gombkattintás, menü, billentyű) a
  `0x0065b840` hívásával végződik. A PicasaPy-ban a szűrőgombok és a
  szöveges keresés **külön nézetmód**, és egymást váltják
  (`search_controller.py:23-60`, `controller_filter_mixin.py:20-67`), ezért a
  kombinált szűrés (szöveg + csillag + arc + kor együtt) nálunk nem létezik.
- **Belépési pontok.** A keresőmező; `Ctrl+F` és `F3` (a `searchbutton`
  kattintása); aktív keresésnél a második megnyomás kilép (PicasaPy-ban is);
  Nézet ▸ Keresési opciók (`0x9d2b`); Eszközök ▸ Keresés hat színe és a
  Fekete-fehér (`color:<szín>` token a mezőbe, `0x0065b7b0`);
  Címke megjelenítése albumként (`0x9de3`); Ctrl+F6 (`dupesearch`); a
  szűrőgombok és az idő-csúszka; az Emberek-felület (`]unknownface`,
  személy: `0x005439e0`, `0x0063d7b0` szintén a `0x0065b7b0`-en át írnak a
  mezőbe). **Új, eddig dokumentálatlan belépő: gépelés a mappalistán vagy a
  képrácson** (`0x005c3fe0` ← `0x005c40e0`, `0x005c42d0`): egy nyomtatható
  karakter a keresőmezőbe kerül és a fókusz oda ugrik. A PicasaPy-ban
  már kezeli ezt a rácson a módosító nélküli 0x21-0x7f karakterekre
  (SearchGridKeys.qml:72-90), a mappalistán viszont
  csak a fel/le navigáció van bekötve (FolderPaneContent.qml:304-307).
- **Gépelés közben.** Nincs időzítő és nincs késleltetés. A mező
  `EN_CHANGE` értesítése (`0x005e4e0d`) azonnal `0x0065b840(this, 0, 1, 1)`-et
  hív, **kivéve** ha a billentyűzet-sorban már vár egy `WM_KEYDOWN`
  (`0x0097fb90`: `GetQueueStatus(QS_KEY)` majd `PeekMessageA(0x100, 0x100)`),
  és ha a szöveg a legutóbbival bájtra azonos, akkor sem keres újra
  (`0x0065b906`-`0x0065b988`). Vagyis a gyors gépelés közbülső lenyomásait az
  eredeti átugorja, a végén biztosan lefut egy keresés. A PicasaPy minden
  `onTextEdited`-re szinkron kereső hívást indít (`MainWindowToolbar.qml:59-64`),
  és csak a javaslatlista vár késleltetéssel (150 ezredmásodperc,
  `MainWindowCommands.qml:730-733`).
- **A szöveg feldolgozása.** (1) A szöveg elejéről és végéről levágja a
  szóközt, vesszőt, pontot, per- és visszaper jelet (`StrTrimA` ` ,./\`,
  `0x00660e8e`); nálunk csak `text.strip()` (`search_controller.py:33`).
  (2) Ha a szöveg a lokalizált `tag:` előtaggal kezdődik (`tagsearch`, magyarul
  `címke:`), az előtagot levágja (`0x006622aa`-`0x0066230d`); nálunk nincs.
  (3) A szót kisbetűsíti (`0x009871f0`), és szavakra bontja (`0x006c0fc0`):
  szókarakter az ASCII betű és számjegy, a `:`, a Latin-1 betűk és minden
  nem-ASCII UTF-8 karakter; minden más (szóköz, `_`, `-`, `.`, `,`, `/`,
  idézőjel) elválasztó. A szavak közti elválasztó szakaszban álló `-` a
  KÖVETKEZŐ szót kizárt szóvá teszi. Nálunk a teljes szöveg EGY
  FTS5-frázis (`index/queries.py:501`), tehát a több szó egymás melletti,
  azonos sorrendű egyezést jelent, és a `-` jelnek nincs szerepe.
- **Mire keres (mért).** Az eredeti keresőindex (`db3\wordhash.dat`) szavakat
  tárol, nem mezőket. A 140 755 képes mintán (124 268 szó, mind kisbetűs) szó
  fájlnévnek, kiterjesztésnek, gyártónak/modellnek és EXIF-adatnak tűnő
  tokenalakokból (`img`, `dsc`, `dsc09117`, `jpg` 119 512 képen, `png`, `mp4`,
  `sony`, `canon`, `huawei`, `samsung`, `i9300`, `exif`, `iptc`, `iso:`, `fókusz:`,
  `vaku`, felbontások), a dátumból és időből (`2010:06:07`, `13:36:29`), a
  színekből (`color:orange` 59 632 képen, `color:blue`, `color:green`,
  `color:red`), a helyből (`geo:lat=...*`, helynevek), a feliratból és a
  kulcsszavakból (ékezetes magyar szavak, ékezettel tárolva), valamint
  `]`-jelű belső tokenekből (`]album:<azonosító>`, `]star`, `]geo`, `]face`,
  `]edited`, `]hidden`, `]unknownface`, `]web_<fiók>` és még nyolc) áll. A
  PicasaPy FTS-indexe csak a fájlnevet, a feliratot és a kulcsszót tartalmazza
  (`index/schema.py:122-125`), a mappanév-egyezés külön ág
  (`index/queries.py:502-514`).
- **Hatás.** A keresés a `]search` virtuális albumot és a
  `CAlbumState+0x162` keresési jelzőt állítja (`0x00662c53`). Az eredménysáv
  szövegeit a `0x005715d0` útvonal kezeli; a visszakeresett erőforráskulcsok
  `searchoptions/searchresult` és `searchoptions/label_search1`. Az eredeti
  pontos megjelenési állapotot nem mértem. A PicasaPy keresőmezője találatnál
  zöld, találat nélkül piros, üresen alapszínű
  (`MainToolbar.qml:508-510`, `Theme.qml:45-50,430-431`,
  `controller_state_mixin.py:148-153`); az eredményszöveg és a számformázás
  is jelen van (`formatting_search_bar.py:17-83`,
  `formatting_status.py:15-26`).
- **Kilépés.** Négy út van, mind a `0x005d47e0` törlő rutinra fut: (1) a
  `searchclr` (X) gomb `(1, 0)` argumentummal: töröl és újraépít, a korábbi
  pozíciót NEM állítja vissza; (2) a „Back to View All" gomb (`viewallbutton`)
  `(0, 0)`-val töröl, majd kikapcsolja a keresősáv gombját, aminek
  kapcsoló-eseménye `(1, 1)`-gyel újraépít ÉS visszaállítja a keresés kezdetén
  megjegyzett nézethelyzetet és fókuszt (az eseménylánc `0x005d8810` →
  `0x005d4a20` szakaszát nem követtem végig, feltételes); (3) a keresősáv gombjának kikapcsolása (`Ctrl+F`/`F3` második
  megnyomása, `0x005d4a20`) szintén `(1, 1)`; (4) **az `Esc` a képrácson**
  (`0x005c42d0`, `0x005c42f8`-`0x005c4342`) `(1, 0)`-val, ha a
  `0x0057c430(4)` feltétel hamis (igaz esetén a `publish/cancel` elemet
  kattintja; a feltétel jelentését a `publish/cancel` elemből
  következtetem). A PicasaPy rácsbeli `Esc`-je is törli a keresést és a
  szűrőt, majd bezárja a keresési beállításokat (`SearchGridKeys.qml:16-20,
  54-69`); ha a javaslatlista nyitva van, az első `Esc` csak azt zárja.
  Aktív keresésnél a második `Ctrl+F`/`F3` ugyancsak kilép
  (`MainKeyboardShortcuts.qml:39-60`, `SearchGridKeys.qml:22-34`).
  A keresés előtti kijelölés/helyzet visszaállítása nálunk nincs.
- **Rejtett képek.** Alapból kizárja őket: ha a `Preferences\ShowHidden`
  (`[this+0x3188]`) hamis, a szűrő a `]hidden` tokent a kizárt listába teszi
  (`0x00660ca2`). A PicasaPy rácsa ugyanezt adja (`_show` szűr,
  `controller_photo_list_mixin.py:117-120`), de a bal hasáb, a `searchResultCount`,
  a mező-visszajelzés és az eredménysáv a szűrés előtti listából készül
  (`search_controller.py:55-76`, `controller_photo_list_mixin.py:117-120`).
  Ez igazolt eltérés: rejtett találat beleszámít a bal hasábba és a sávba,
  miközben a rácson nem jelenik meg (6. szakasz).
- **Sok találat, hálózat.** A végrehajtó és a szűrő függvényei (`0x00662b20`,
  `0x00662220`, `0x00660c80`, `0x0043f9a0`, `0x0043c410`, `0x00422ce0`,
  `0x006c0fc0`) közvetlen API-importjai között nincs fájl- és hálózati
  művelet; a keresés index-hozzáférő virtuális hívásokat is végez, ezért az
  elérhetetlen hálózati mappa hatását ez önmagában nem dönti el.
  **NINCS MEG**: ezt csak eredeti Picasán, elérhetetlen, de korábban indexelt
  hálózati mappával végzett kontrollmérés dönti el. Rögzített találatszám-
  korlátot a végrehajtóban nem azonosítottam; a 1000 fölötti darabszámot
  ezres csoportokkal formázza (`0x0066324c`, `0x00663278`). A PicasaPy
  ugyancsak csoportosítja a számokat (`formatting_search_bar.py:17-35`); a
  nagyon nagy találathalmaz futásidejű memória- és sebességhatása NINCS MEG.
- **Mit jegyez meg.** A keresés első szövegváltozásakor megjegyzi a nézet
  helyzetét: a bal hasáb aktuális elemét (`[this+0xe94]`) és az aktuális vagy
  kijelölt kép sorszámát (`[this+0xe98]`) (`0x0065ba5c`-`0x0065bb0c`); ezt csak
  a sáv bezárása állítja vissza (`0x005fa430`; hogy a visszaállítás
  kijelölést, görgetést vagy mappát jelent, feltételes). Megjegyzi a
  fókuszban volt elem nevét is (`[this+0xf6c]`). A keresés a
  Vissza/Előre előzménybe is bekerül: a `thumbui/navback` és `thumbui/navfw`
  (`0x005d9cc0`, `0x005d9ec7`-`0x005d9ecd`, `0x005d9f3f`-`0x005d9f45`) a
  `0x00600ac0`-val visszaállítja a szöveget, az öt szűrőgombot és a
  keresősáv állapotát. Tartós (indítások közötti) tárolást nem találtam.
  A PicasaPy könyvtárnézetében nincs Vissza/Előre előzmény; gépeléskor
  törli a kijelölést (`src/picasapy/app/qml/PicasaPy/MainWindowToolbar.qml:59-64`),
  és nincs keresés előtti nézethelyzetet visszaállító állapota.

### Bizonyítottsági fok

**Feltételes** az összkép: a statikus bináris és a mai forrás több kérdésre
pontos választ ad, de a szűrési AND/OR-szemantika, a mappalista gépelése,
a Unicode/ékezet-viselkedés, a nagyon nagy találathalmaz és a hálózati
mappa futásidejű hatása nincs teljesen eldöntve. A PicasaPy oldali
megállapítások forrásszinten ellenőrzöttek; az eredeti Picasa felületi
hatásairól nem készült új futásmérés.

**Erős, függetlenül, újra levezetett rész:** a `0x006c0fc0` a pozitív és a
kizárt (`-`) tagokat külön vektorokba teszi, `0x0043f9a0` pedig külön
dolgozza fel ezeket. Az `AND`/`OR` összesített logika és a szűrőgombok
találatokhoz való pontos kapcsolata ettől még `NINCS MEG`.

### A két független út

- **A: a bináris célzott olvasása:** a meglévő Ghidra-kimenet
  (`referencia/ghidra/2026-11-16-koteg-426-437.txt`, `0x0043f9a0`,
  `0x006c0fc0`) és a helyi célzott diszasszemblálás a parser két kimeneti
  vektorát és a végrehajtó külön bejárásait mutatja.
- **B: vak, friss kontextusú újralevezetés:** a külön bíráló a
  `0x006c0fc0` `-`-ágát (`0x006c10a3`-`0x006c10fe`,
  `0x006c1201`-`0x006c13a7`) és a `0x0043f9a0` két bejárását
  (`0x0043fd04`-`0x0043fdbd`, `0x0043ff7f`-`0x00440058`) önállóan
  olvasta. Az út A-val egyezik a pozitív/kizárt listák elkülönítésében;
  a kompozíciót egyik út sem dönti el.

### Cáfoló kísérlet

- **Cáfolandó állítás:** a PicasaPy rácsból gépelt karakter nem indít
  keresést, és a találati háttérjelzés hiányzik. A cáfoló ellenőrzés a
  forráslánc volt: a `MainLibraryCanvas.qml` a rács billentyűeseményét
  továbbítja (`:288-314`), a `SearchGridKeys.qml` a bevitelt a mezőbe
  illeszti és keresést indít (`:72-90`); a mező háttérkötése
  `MainToolbar.qml:508-510`, a színek és visszajelzés `Theme.qml:45-50,
  430-431` és `controller_state_mixin.py:148-153` alatt van. Az állítás
  megdőlt; ugyanezen forráslánc azt is mutatja, hogy a mappalista csak
  fel/le nyilat kezel (`FolderPaneContent.qml:304-307`).
- **Rejtett találat cáfoló ellenőrzése:** a nyers találati rekord közvetlenül
  kerül a bal hasáb és a számláló építésébe (`search_controller.py:55-76`),
  majd csak `_show`-ban szűrődik a rács számára
  (`controller_photo_list_mixin.py:117-120`). Korábbi szűrésre utaló
  külön út nincs a hívási láncban, így a darabszám-eltérés megmarad.

### 1. Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Keresőmező.** A `searchcontainer/search` elem építője `0x0040e7b0` (stílus: `GetWindowLongA(-0x10) \| 0x80`, `0x0040e7fc`-`0x0040e80e`), mellette a `searchautomatikus kiegészítés` lista (`0x0040e81d`). A szöveg olvasása `0x0065b88e` (`0x00986200`). | `MainToolbar.qml:530-551` (`TextInput`, `onTextEdited`, nyíl- és Esc-kezelés a javaslatlistához) | Egyezik a mező megléte. A viselkedés eltérései a 3-5. szakaszban. |
| **`Ctrl+F`, `F3`.** `0x005e63bb`, `0x005e69a4` kapcsolóként nyitja/zárja a keresést (`0x005d4a20`). | `MainKeyboardShortcuts.qml:39-60`, `SearchGridKeys.qml:22-34` a második billentyűnyomást kilépésként kezeli. | A belépés és kilépés egyezik; csak a keresés előtti nézethelyzet visszaállítása marad E2. |
| **Nézet ▸ Keresési opciók.** `ID_VIEW_SEARCHVIEW`, parancs `0x9d2b` (`0x0055aa7d` a következő rekord blokkjában, #7012), kezelő `0x005cbb50` → `0x009cd8a0`. | `MainToolbar.qml:53-58` (`toggleSearchOptions`) | Egyezik (korábbi lap: #4641). |
| **Eszközök ▸ Keresés ▸ hat szín és Fekete-fehér.** `0x005ccc41`-`0x005ccca7`: `color:<szín>` token, `0x0065b7b0` hat lépése (szöveg a mezőbe, sáv megjelenítése, kurzor a végére, újraépítés). A tokeneket a `0x00424c20` adja a szín osztályából (`0x00c8134c`-`0x00c813ac`). | `MainMenuBar.qml:212`, `MainToolbar.qml:129-133` | Egyezik. |
| **Címke megjelenítése albumként.** `ID_SEARCHTOKEN`, `0x9de3`, kezelő `0x005d8330`. | `MainWindowCommands.qml:234-249`, `photo_ops_album_actions_mixin.py:57-` | Egyezik: a címkéből rendes albumot készít; ez nem közvetlen keresőmező-mód. |
| **Keresési eredmények mentése.** `ID_SAVESEARCH`, parancs `0x9d52` (`0x0055c3b8`), kezelő `0x005d86a0` (1000-es küszöb, `Create Album`). | nem vizsgált (korábbi lap: #1405) | Nem tárgya ennek a körnek. |
| **Szűrőgombok és idő-csúszka.** A `0x005d8810` kezelő minden gombot a `0x0065b840` hívásával zár (`0x005d95af`-`0x005d95b4`); a szűrőobjektum `0x00660c80` mind a hatot és a csúszkát (`timeslider/scaleslider`, `0x00660eab`) egyszerre olvassa. | `ToolbarFilterControls.qml:87-381`, `controller_filter_mixin.py:20-67` (külön nézetmódok) | **Eltér** (E1): a szűrők nem kombinálhatók a szöveggel és egymással. |
| **Gépelés a mappalistán és a képrácson.** A mappalista (`0x005c40e0`) és a rács (`0x005c42d0`) módosító nélküli karaktereseményt ad a `0x005c3fe0` kezelőnek. Az elemzett ág a `0x21`-`0x7f` és a `0x100` fölötti kódot engedi át, a `0x20` alatti és a `0x80`-`0xff` értékeket nem; a karakter alsó bájtját adja tovább. A mezőre fókuszál, beírja a karaktert, és elnyeli az eseményt. A magas kódág karaktereseményhez való viszonya külön nyitott. | Rács: `SearchGridKeys.qml:72-90`, csak `0x21`-`0x7f`; mappalista: `FolderPaneContent.qml:304-307`, csak fel/le nyilat kezel. | **Részben egyezik (E3):** a mappalistából hiányzik; a PicasaPy rácsának gépelési útja csak a binárisan egyértelmű ASCII tartományban van igazolva. |
| **Ismeretlen arcok és személy.** `0x005439e0` (`]unknownface`), `0x0063d7b0` a `0x0065b7b0`-en át a mezőbe írja a tokent. | nem vizsgált | Nem tárgya ennek a körnek. |
| **Másodpéldány-kereső.** `Ctrl+F6`, Eszközök ▸ Kísérleti: `searchoptions/dupesearch` (`picasa-kereses-modok.md`). | `MainToolbar.qml` `dupesearch` gomb | Egyezik (korábbi lap: #2169). |

### 2. Mire keres: a szóindex mért tartalma

A keresés nem mezőkben, hanem a `db3\wordhash.dat` szótárában keres
(`CIndexer`, `0x004dca40`; `album-sorrend.md` 2.1). A fájl formátuma `album-sorrend.md` 2.6 szerinti. A projekt saját
`Picasa2/db3/wordhash.dat` mintáján egy korábbi feldolgozás 140 755 képet és
124 268 különböző, kisbetűs keresőszót adott; a parse 0 bájt maradékot jelzett.
A mostani próba a fájl SHA-256-át és fejlécét ellenőrizte, a teljes
szótárszámlálást nem ismételte meg. Az alábbi számok a korábbi mintamérésből
valók. A csoportcímek a tokenek alakját írják le; önmagukban nem bizonyítják,
hogy az adott token melyik fotómezőből származik. A mező-hozzárendelés nyitott.

| Megfigyelt tokenalak | Példa és darabszám (képek, ahol a szó szerepel) | Megjegyzés |
|---|---|---|
| fájlnévnek tűnő tokenek | `img` 49 263, `dsc` 30 342, `dsc09117` 1 | a `_` és `.` elválasztó, a név darabjai külön szavak |
| kiterjesztésnek tűnő tokenek | `jpg` 119 512, `png` 7 702, `mp4` 1 770, `jpeg` 2 678 | a kiterjesztésnek látszó alak is token |
| gyártó-/modellnévnek tűnő tokenek | `sony` 35 263, `samsung` 19 171, `huawei` 23 086, `canon` 5 537, `i9300` 11 975 | a minta ilyen alakú szavai; a mezőeredet nincs bizonyítva |
| EXIF-adatnak tűnő tokenek | `exif` 107 561, `iptc` 107 368, `iso:` 95 883, `fókusz:` 96 990, `vaku` 56 943 | az `iso:` és a `fókusz:` a `:` miatt egy szó; a forrásmező nincs bizonyítva |
| felbontás, számok | `1280` 21 828, `960` 21 607, `2048` 21 305 | csupa számjegyű szó 47 472 van |
| dátum és idő | `2010:06:07`, `13:36:29` | a `:` szókarakter, a dátum `ÉÉÉÉ:HH:NN` alakban egy szó |
| szín | `color:orange` 59 632, `color:blue` 33 339, `color:green` 23 167, `color:red` 11 186 | a színkeresés is szóegyezés (a PicasaPy külön `photo_colors` táblát használ) |
| hely | `geo:lat=...*` és `geo:lon=...*` (234 szó), helynevek és `.. km to <hely> in <megye> <ország>*` | a `*` végű szó 307, ebből 56 szóközt tartalmaz |
| belső tokenek | `]album:<azonosító>`, `]star`, `]geo` 36 261, `]face`, `]edited` 30 496, `]hidden`, `]unknownface`, `]history`, `]revertable`, `]screensaver`, `]search`, `]snapshot`, `]suppress`, `]updated`, `]web`, `]web_<fiók>` | |
| feliratnak/címkének tűnő tokenek | ékezetes magyar szavak, kisbetűsen (`és` 49, `fák`, `térképen`) | a mintában az ékezet megmaradt; a lekérdezés oldali ékezetkezelés NINCS MEG |

További mért tények: a 124 268 szó közül **nulla** tartalmaz nagybetűt (az
indexelés kisbetűsít); kötőjeles szó nincs, aláhúzás csak a `]web_<fiók>`
tokenben van (a `-` és `_` elválasztó); a mappanév szavainak jelenlétét a
szótárból nem lehet kimutatni; a `]album:<azonosító>` token előfordulása önmagában nem bizonyít mappanév-keresést,
ezért a mappanévre keresés mechanizmusa NINCS MEG. A PicasaPy FTS-indexe
(`name`, `caption_ini`, `keywords_ini`, `caption_file`, `keywords_file`) a
gyártót, EXIF-szavakat, kiterjesztést, dátumot és helyet nem keresi.

### 3. Gépelés közben

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Eseményút.** A főablak üzenetkezelője (`0x005e4ac0`) a `WM_COMMAND` (`0x111`) ágon (`0x005e4dda`) a mező kezelőjének (`[this+0xf48]`, `0x005e4e05`) `EN_CHANGE` (`0x300`) kódjára hívja `0x97fb90`-et, és ha az hamis, `0x0065b840(this, 0, 1, 1)`-et (`0x005e4e1e`-`0x005e4e25`). Időzítő-API (`SetTimer`) sem ebben, sem a `0x0065b840`, `0x00662b20`, `0x005d47e0` függvényben nincs. | `MainToolbar.qml:538`, `MainWindowToolbar.qml:59-64` | **Eltér** (E5): nincs billentyűsor-őr és nincs azonos-szöveg kihagyás. |
| **Billentyűsor-őr.** `0x0097fb90`: `GetQueueStatus(1)` felső szavának 0. bitje (`0x0097fb95`-`0x0097fb9e`), majd `PeekMessageA(&msg, 0, 0x100, 0x100, 0)` (`0x0097fba2`-`0x0097fbb5`); igaz, ha vár `WM_KEYDOWN`. Igaz értéknél a keresés elmarad (`0x005e4e1c`). | nincs | A gyors gépelés közbülső keresései elmaradjanak (E5). A hatás nincs mérve. |
| **Azonos szöveg kihagyása.** A `0x0065b840` harmadik argumentuma nem nulla: a mező szövegét bájtonként összeveti a legutóbbival (`[this+0xde4]`, `0x0065b906`-`0x0065b988`), és egyezésnél nem keres újra (`0x0065bb20`). | `search_controller.py:23-60` (minden hívás újrakeres) | E5. |
| **Szövegtisztítás.** `0x00660e8e`: `StrTrimA(szöveg, " ,./\")` (szóköz, vessző, pont, per, visszaper az elejéről és a végéről). | `search_controller.py:33` (`text.strip()`) | **Eltér** (E6). |
| **Kis- és nagybetű.** `0x009871f0` a szöveget kisbetűsíti: ASCII `A`-`Z` (`0x009872e2`-`0x009872f0`), a többbájtos karaktert a `0x00989f80`-nal (a Unicode-átalakítás jellege NINCS MEG). | FTS5 alapértelmezett tokenizáló (kisbetű-érzéketlen, `index/schema.py:122`) és `casefold()` a mappanévre (`queries.py:502`) | Egyezik a hatás; a Unicode-hajtás egyezése nem mért. |
| **Ékezet.** Az index ékezettel tárol, a kisbetűsítés nem hajt ékezetet; ékezet-hajtás a keresési oldalon a tisztító és a bontó kódban nincs (a `0x0043c410` mélyét nem olvastam). | FTS5 `unicode61` alapbeállítás: a mellékjel eltávolítása a SQLite-verziótól függ (nem mért) | NINCS MEG (Nyitott: `0x0043C410`). |
| **Több szó.** `0x006c0fc0`: szavakra bont (szókarakter: ASCII betű és számjegy, `:`, Latin-1 betű, minden nem-ASCII UTF-8 karakter, bitmap `0x00d30bd0`). A szavak közti szakaszban álló `-` a következő szót kizárttá teszi (`0x006c10a3`-`0x006c10a8`; a jelző szavanként nullázódik, `0x006c1030`). A `0x0043f9a0` a szavakat külön kéri le (`0x0043fd20`-`0x0043fe98`), és számlálóval veti össze (`0x00413210`, `0x00413250`). | `queries.py:501` (egész szöveg egy frázis, `"` duplázva) | **Eltér** (E7): több szó nálunk csak egymás melletti sorrendben egyezik; a `-` kizárás és az idézőjel nálunk nem szerepel. A kizárás és az ÉS/VAGY pontos jelentése feltételes. |
| **Idézőjel.** A `"` (0x22) nincs a szókarakter-bitmapen, tehát elválasztó; idézőjel-frázis kezelés a bontóban nincs. | az idézőjel a frázisba kerül (`queries.py:501`) | Egyezést okozó eltérés: a PicasaPy `"` karaktert is frázisként keres (feltételes hatás). |
| **Előtagok.** `tag:` (lokalizált: `címke:`): a `0x006622aa` (`tagsearch`, `0x00987030` előtag-vizsgálat, `0x00986120` levágás) lehámozza, és `[szűrő+0xc]`-t állítja. A `color:` és a `]`-tokenek szóként kerülnek az indexbe. | `search_color.parse_color_terms` a `color:`/`szín:` előtagra (`queries.py:471`) | `tag:` hiányzik (E7). A `[szűrő+0xc]` hatása NINCS MEG. |
| **Javaslatlista.** `CSearchEditBox` (`0x00cb432c`): nyíl fel/le (`0x77d3a5`-`0x77d3b1`), PageUp/PageDown (`0x77d401`-`0x77d409`), Enter (`0x77d43d`), bal/jobb. A sorok kirajzolója `0x0077e2e0` a beírt szöveget kisbetű-érzéketlenül, szóhatáron kiemeli (`0x0077e360`-`0x0077e3e7`), a darabszám `(%d) ` vagy ` (%d)` alakú (`0x0077e9ef`, `0x0077eb7d`); az ikonok: `icons/label`, `icons/album`, `icons/folder`, `icons/imageresult` (`0x0077eee0`). | `SearchSuggestions.qml:1-60`, `search_controller.py:112-122`, `queries.py:551-` (csak mappa és album, részszó-egyezés bárhol a névben) | **Eltér** (E8): nálunk nincs címke- és képtalálat-sor, és a kiemelés nem szóhatáros. A forrás és a sorrend NINCS MEG. |

### 4. Hatás: sáv, rács, bal hasáb, kijelölés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Végrehajtás.** `0x00662b20` zárat vesz (`0x00662b36`, szálazonosító és kritikus szakasz), időt mér (`QueryPerformanceCounter`), szűrőt épít (`0x00662b94`), végrehajt (`0x00662bcd` → `0x00662220`), majd a keresési jelzőt írja: `[CAlbumState+0x162]` = a szűrő fajtája (`0x00662c53`; 0 nincs szűrő, 1 csak gombok, 2 szöveg, kor vagy másodpéldány: `0x0065aa80`). Üres szöveg és nincs gomb: minden látható kép (`0x00422ce0`). | `search_controller.py:23-60` (üres szöveg: a mappa-feed) | Egyezik a fő út (üres szöveg a normál nézet). A nézetpozíció megjegyzése hiányzik (E2). |
| **A bal hasáb.** Keresési módban a lista a találatos sorokra szűkül, a kategória-állapot nem számít (`+0x162`, `picasa-idorend-bemutato-kutatas.md`; a `]search` sor `0x004ad430`, `Search results`). | `search_controller.py:71-76` (`load_matches`), `FolderPane.qml:26-31` | **E9:** a bal hasáb címe eltér; a PicasaPy a kifejezést és darabszámot is kiírja. |
| **Eredménysáv szövege.** Az eredeti `searchmatchstr`, `nomatch`, `sresults` és `searchdisplay` szövegei, az ezres csoportosítással (`0x00662d7d`-`0x006634c1`, `0x0066324c`). | `formatting_search_bar.py:60-83` az eredeti `Search results for …`/`No matches` szöveget adja; `formatting_status.py:15-26` tagolja a darabszámot. | A keresősáv eredményszövegének és számformázásának eltérése a #7079 óta lezárt. A bal hasáb felirata külön E9; a rejtett találatok számlálása E10. |
| **A mező háttérszíne.** Találatnál `#E4F1E5`, találat nélkül `#FFCBCB`, üres keresésnél alapszín (`0x00662d06`-`0x00662d34`). | `MainToolbar.qml:508-510`, `Theme.qml:45-50,430-431`, `controller_state_mixin.py:148-153` | Egyezik (#7079); nincs új fejlesztési teendő. |
| **Találat nélkül.** A rács-háttérszöveg (`thumbui/lightbox_bgtext`, `0x00662c73`/`0x00662c93`) a találatlista méretétől függ; a „Keresés mindenhol" gomb halott. | `racs-ures-allapot.md`, `LightboxFeed.qml` `gridEmptyText` | Egyezik (korábbi lap: #1945). |
| **Rács és kijelölés.** Új keresésnél újrapozicionálja a rácsot; a bezáró út visszaállítja az elmentett helyzetet (`0x006636a6`-`0x006636b6`, `0x005d49f8`-`0x005fa430`). | `MainWindowToolbar.qml:59-64` gépelésenként törli a kijelölést; helyzetet nem ment. | **E2:** a keresés előtti nézethelyzet visszaállítása maradt; pontosan melyik UI-állapot tér vissza, eredeti futásméréssel kell eldönteni. |

### 5. Kilépés a keresésből

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **X gomb (`searchclr`).** `0x005d8810` → `0x005d47e0(this, 1, 0)` (`0x005d891c`-`0x005d8920`). Törli a szöveget (`0x005d4965`-`0x005d4974`), mind a hat gombot (`0x005d48aa`-`0x005d48f6`), az idő-csúszkát (`0x005d4906`-`0x005d491e`), a két belső listát (`0x005d4927`-`0x005d494e`), a hasonlósági mintát (`0x005d8280`), a fókuszt a mezőre teszi (`0x005d4989`), majd az előző fókuszelemre (`0x005d498f`-`0x005d49c9`), és `0x0065b840(this,0,0,1)`-gyel újraépít (`0x005d49eb`). | `MainToolbar.qml:583-606`, `MainWindowToolbar.qml:65-69` | Részben egyezik: a gombok és a kor-csúszka törlése hiányzik, mert nálunk külön nézetmódok (E1). |
| **Back to View All.** `viewallbutton` (`0x005d9564`): `0x005d47e0(this, 0, 0)` (nem épít újra), majd a keresősáv gombját kikapcsolja (`0x005d957c`-`0x005d959a`), ami `(1, 1)` útra visz: újraépítés és pozíció-visszaállítás. Súgója: `Exit Search Mode`. | `MainLibraryCanvas.qml:35-75`, `controller_filter_mixin.py:153-164` | Egyezik a gomb és a felirat; a pozíció-visszaállítás hiányzik (E2). |
| **`Ctrl+F`/`F3` még egyszer; a sáv gombja.** `0x005d4a20` → `0x005d47e0(this, 1, 1)`. | `MainKeyboardShortcuts.qml:39-60`, `SearchGridKeys.qml:22-34` | Egyezik a kilépés; E2-ben csak a keresés előtti nézethelyzet visszaállítása marad. |
| **`Esc` a rácson.** A `0x005c42d0` keresés nélkül is a törlő rutinra jut; a `publish/cancel` ág feltételes (`0x005c42f8`-`0x005c4342`). | `SearchGridKeys.qml:46-69`; ha a javaslatlista látszik, az első `Esc` azt zárja. | A keresés törlése egyezik; a javaslatlista első `Esc`-es bezárása PicasaPy-specifikus. |
| **`Esc` a keresőmezőben.** A `CSearchEditBox` kezelője (`0x0077d380`) nem tartalmaz `0x1b` összevetést (csak nyilak, PageUp/Down, Enter). A mező saját üzenet-feldolgozása NINCS MEG. | `MainToolbar.qml:540-551` | NINCS MEG (Nyitott: `0x0077D380`). |
| **Üresre törlés billentyűvel.** A szöveg üresre törlése után a `0x0065b840` `[this+0xe94] = -1`-et ír (`0x0065ba4d`), a szűrő fajtája 0 lesz, a keresési jelző kikapcsol, a nézet a normál nézethez tér vissza (`0x0065aa80`, `0x00662c53`); a megjegyzett pozíció elvész. | `search_controller.py:38-44` (üres szöveg: mappa-feed) | Egyezik a fő hatás. |

### 6. Rejtett képek, sok találat, elérhetetlen hálózat

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Rejtett képek.** A `ShowHidden` hamis állapotában a `]hidden` token a kizárt listába kerül (`0x00660c84`-`0x00660e25`). | `search_controller.py:55-76` a nyers találatokból számol; `controller_photo_list_mixin.py:117-120` csak a rács előtt szűri a rejtetteket. | **Biztos eltérés (E10):** a hasáb, a mezőjelzés és az eredménysáv beleszámolja a rácsról kizárt képeket. |
| **Nagyon sok találat.** Az átnézett végrehajtóban nincs rögzített találatszám-korlát; a darabszám 1000 fölött tagolt (`0x0066324c`, `0x00663278`). | `queries.py:446-523` minden találatot visszaad; `formatting_search_bar.py:17-35` tagolja a darabszámot. | A megjelenítési tagolás egyezik; a nagyon nagy készlet futásidejű memória-/sebességhatása `NINCS MEG`, eredeti kontrollmérés szükséges. |
| **Elérhetetlen hálózati mappa.** Az index-hozzáférés virtuális hívásainak hálózati hatása nem dőlt el; a közvetlen fájl-/hálózati API-import hiánya nem elég bizonyíték. | `queries.py:446-523` az SQLite-indexből keres. | **NINCS MEG:** eredeti Picasán, korábban indexelt de lekapcsolt hálózati mappával végzett mérés kell. |

### 7. Összevetés egy táblázatban (a jelenlegi HEAD szerint)

**A #7079 óta lezárt különbségek:** a mező találat szerinti háttérszíne, a keresősáv eredményszövege és az ezres tagolás a főágon már megvan (`MainToolbar.qml:508-510,629-640`, `formatting_search_bar.py:17-83`, `formatting_status.py:15-26`). Ezekre nem javaslok új fejlesztői jegyet.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00660c80` + `0x00662220` egy szűrőobjektumba gyűjti a szöveget, szűrőgombokat és kor-csúszkát; a találat-összevonás pontos AND/OR szabálya nyitott. | `src/picasapy/app/search_controller.py:23-60`, `controller_filter_mixin.py:20-67`: a szöveges keresés külön nézetmód, felülírja az aktív szűrőt. | **E1:** közös szűrőállapot; az eredményhalmaz pontos logikáját a `0x004dc690`/`0x004dcb90` vizsgálata után rögzíteni. |
| A `]search` bal oldali sor neve `Search results` (`0x004ad430`). | `FolderPane.qml:26-31` a `Search results for "%1" (%2)` alakot mutatja. | **E9:** a bal hasáb saját kereséssor-feliratát az eredeti `Search results` alakhoz kell igazítani; a számláló eredeti helyét méréssel rögzíteni. |
| A keresés elején a bal hasáb, a képindex és a fókusz mentése (`0x0065ba5c`-`0x0065bb0c`); a sávbezárás visszaállító útja (`0x005fa430`). | `MainWindowToolbar.qml:59-64` minden gépelésre törli a kijelölést; nincs keresés előtti állapotot visszaállító állapot. | **E2:** a pontosan megmért nézethelyzet/fókusz visszaállítása Back to View All és második `Ctrl+F`/`F3` esetén; X esetén ne álljon vissza. |
| Mappalistán és rácson gépelt karakter a keresőmezőbe kerül (`0x005c3fe0`, hívók `0x005c40e0`, `0x005c42d0`). | Rács: `SearchGridKeys.qml:72-90`; mappalista: `FolderPaneContent.qml:304-307` csak fel/le nyilat kezel. | **E3:** a mappalistán is induljon a keresés; a `0x80` fölötti karakterek eredeti kezelése maradjon méréshez kötött. |
| `EN_CHANGE` közvetlen keresés, várakozó `WM_KEYDOWN` kihagyása (`0x005e4e0d`, `0x0097fb90`), azonos szöveg ismételt lekérdezésének elhagyása (`0x0065b906`-`0x0065b988`). | `MainWindowToolbar.qml:59-64` minden `onTextEdited` eseménynél keres; a 150 ms-os timer csak a javaslatlistát frissíti (`MainWindowCommands.qml:730-733`). | **E5:** a fölös köztes keresések elhagyása és az azonos szövegű újrahívás kihagyása. |
| Trim-karakterek ` ,./\\` (`0x00660e8e`), lokalizált `tag:`/`címke:` előtag (`0x006622aa`), több pozitív és kizárt tag vektora (`0x006c0fc0`, `0x0043f9a0`). | `search_controller.py:33` `strip()`; `index/queries.py:490-523` a teljes bemenetet idézett FTS-kifejezésként kezeli; `color:`/`szín:` külön kerül feldolgozásra. | **E6/E7:** a tisztítás, előtag és tokenizálás az eredeti szabályára; a pontos AND/OR összefésülés előbb bináris-körrel zárandó. |
| A mintabeli `wordhash.dat` kereshető szavai közt van fájlnévnek, kiterjesztésnek, kamerának/EXIF-nek, dátumnak/időnek, színnek, helynek, feliratnak, kulcsszónak és belső tokennek tűnő alak (mérés a mintafájlon; a mezőépítő út nyitott). | `index/schema.py:122-125`, `index/queries.py:446-523`: név, felirat, kulcsszó, mappanév-ág és színindex. | **E8:** a bizonyított mezőcsoportokat fokozatosan indexelni; pontos mező-hozzárendelés nélkül ne állítsunk teljes paritást. A javaslatlista eredeti forrása/sorrendje külön nyitott kérdés. |
| A javaslatlistában címke-, album-, mappa- és képtalálat-típus jelenik meg, ikonnal és szóhatáros kiemeléssel (`0x0077E2E0`, `0x0077EEE0`). | `SearchSuggestions.qml:1-60`, `search_controller.py:112-122`, `queries.py:551-605`: jelenleg csak album- és mappajavaslat. | **E11:** egészítsük ki címke- és képtalálattal; a forrás sorrendje és számlálási szabálya eredeti mérést igényel. |
| Rejtett képek kizárása `Preferences\\ShowHidden` alapján (`0x00660c84`-`0x00660e25`). | `search_controller.py:55-76` a nyers találatokból készít bal hasábot és számlálót; `controller_photo_list_mixin.py:117-120` csak utána szűri a rácsot. | **E10:** a hasáb, számláló, mező-visszajelzés és sáv a látható találatok számát használja. |

### Javasolt fejlesztői jegytörzsek

**1. Keresés és szűrők egy közös állapotban (E1)**

Eredeti: a `0x0065b840` a szöveget, a csillag-/arc-/film-/online-/geocímke-/másodpéldány-szűrőket és a kor-csúszkát egy `0x00660c80` szűrőobjektumba gyűjti, majd a `0x00662220` futtatja. A pontos AND/OR összevonás `NINCS MEG`.

Nálunk: `search()` és a szűrőnézetek külön állapotok; szöveges keresés felülírja az aktív szűrőt.

Teendő: tegyük közös állapotba a keresőkifejezést, a szűrőkapcsolókat és a korértéket. Az eredmény-összevonás pontos logikáját csak a bináris segédfüggvények ellenőrzése után implementáljuk.

Kész, ha:

- a keresőszöveg és egy szűrő egyszerre maradhat aktív;
- egyetlen szűrő kikapcsolása nem törli a keresőkifejezést;
- az eredményhalmaz az igazolt eredeti szabályt követi, becsült AND/OR nincs.

**2. A keresés előtti nézethelyzet visszaállítása (E2)**

Eredeti: a keresés kezdetén elmenti a bal hasáb kiválasztását, a képindexet és a fókuszelemet (`0x0065ba5c`-`0x0065bb0c`); a sáv bezárásának egyik útja visszaállít (`0x005fa430`). Az X útja nem állít vissza.

Nálunk: gépeléskor a kijelölés törlődik (`MainWindowToolbar.qml:59-64`), az előző nézethelyzetet nem menti.

Teendő: a visszaállítás pontos hatását az eredeti mappalistán/rácson mérjük meg, majd Back to View All és a második `Ctrl+F`/`F3` útján állítsuk vissza; az X maradjon törlő út.

Kész, ha:

- a mérésben igazolt mappa, képkijelölés, görgetés és fókusz kerül vissza;
- az X nem állítja vissza a keresés előtti állapotot;
- keresés nélkül egyik kilépő út sem változtatja a kijelölést.

**3. Gépelés a mappalistán is indítsa a keresést (E3)**

Eredeti: a `0x005c40e0` albumlista- és a `0x005c42d0` rácsút a `0x005c3fe0` karakterkezelőbe vezet; az igazolt `0x21`-`0x7f` tartományban a mezőre fókuszál és továbbítja a karaktert. A magasabb kódág még nem tisztázott.

Nálunk: a rácsban működik (`SearchGridKeys.qml:72-90`); a mappalistában csak fel/le léptetés van (`FolderPaneContent.qml:304-307`).

Teendő: a mappalista billentyűútját kapcsoljuk a közös kereső-kezelőhöz. A `0x80`-`0xff` és `0x100` fölötti kódok pontos viselkedése csak mérés után kerüljön be.

Kész, ha:

- módosító nélküli, eredetivel igazolt karakterre a keresőmező kap fókuszt;
- a karakter egyetlen alkalommal kerül a mezőbe és elindítja a keresést;
- a vezérlőgombok és módosított billentyűk nem váltanak keresésre.

**4. Felesleges köztes keresések kihagyása (E5)**

Eredeti: az `EN_CHANGE` azonnal keres, de kihagyja a váró `WM_KEYDOWN` idején érkező köztes futást (`0x0097fb90`), és azonos szövegnél nem kérdez újra (`0x0065b906`-`0x0065b988`).

Nálunk: minden szövegváltozás szinkron lekérdezés; a késleltetés kizárólag a javaslatlistára vonatkozik.

Teendő: a gépelés közben összevonható futásokat és az azonos szövegű ismétlést hagyjuk ki úgy, hogy a végső szövegre biztosan lefusson egy keresés.

Kész, ha:

- a végső szöveg minden billentyűsorozat végén megjelenik;
- a köztes, már elavult keresés nem fut le;
- azonos kifejezés újabb hívása nem indít új indexlekérdezést.

**5. Keresőkifejezés-feldolgozás az eredeti szabályai szerint (E6/E7)**

Eredeti: a szélső ` ,./\\` karaktereket levágja (`0x00660e8e`), a `tag:`/`címke:` előtagot kezeli (`0x006622aa`), majd a pozitív és `-`-os tagokat külön adja át (`0x006c0fc0`, `0x0043f9a0`). A pozitív/kizárt listák pontos AND/OR összevonása még nyitott.

Nálunk: `strip()` és egyetlen idézett FTS-kifejezés; a `tag:` nincs külön kezelve.

Teendő: a szöveg tisztítását és tagokra bontását az eredetihez igazítani; a találati logikát a függvénysegédek elemzése előtt ne találgassuk.

Kész, ha:

- a szélső tisztítókarakterek, `_`, `.` és idézőjelek a bináris szerint viselkednek;
- a lokalizált `tag:` előtag ugyanazt az utat használja;
- pozitív és kizárt tagok a mért összevonási szabályt követik.

**6. A kereshető képmezők bővítése (E8)**

Eredeti: a helyi `wordhash.dat` mintában fájlnév- és kiterjesztés-szavak, kamera/EXIF-nek megfelelő szavak, dátum/idő-, hely-, szín-, felirat- és kulcsszavak is vannak; a mezőépítő pontos hozzárendelése még nyitott.

Nálunk: a FTS-oszlopok a fájlnevet, feliratot és kulcsszavakat fedik (`index/schema.py:122-125`); a szín és a mappanév külön lekérdezési ágon van (`index/queries.py:446-523`).

Teendő: a már igazoltan hiányzó mezőcsoportokra készüljön bővítés, de csak az eredeti builder-lánc mező-hozzárendelésének és kontrollmérésének lezárása után.

Kész, ha:

- a fájlnév, felirat, címke, szín és mappanév jelenlegi útjának paritását külön mérés igazolja;
- az eredetivel igazolt kamera/EXIF-, kiterjesztés-, dátum- és helymezők kereshetők;
- egyetlen mező forrását sem becsülték a minta puszta szavai alapján.

**7. A bal hasáb kereséssor-felirata (E9)**

Eredeti: a `]search` sor felirata `Search results` (`0x004ad430`).

Nálunk: a `FolderPane.qml:26-31` a `Search results for "%1" (%2)` szöveget írja ki; a kifejezést és a találatszámot is belefoglalja.

Teendő: a sor feliratát igazítsuk az eredetihez, a számláló helyét pedig az eredeti felületi mérés szerint döntsük el.

Kész, ha:

- a bal hasáb sora az eredeti feliratot használja;
- a számláló csak akkor jelenik meg ott, ha az eredeti mérés ezt igazolja;
- a keresősáv eredményszövege külön marad, mert annak paritását a #7079 óta igazoltuk.

**8. Rejtett találatok ne torzítsák a darabszámot (E10)**

Eredeti: a rejtett képek alapból kiesnek a találati halmazból (`0x00660c84`-`0x00660e25`).

Nálunk: a bal hasáb, a keresési darabszám és a sáv a rejtett szűrés előtt készül, míg a rács utána szűr.

Teendő: a megjelenő rács-listából számoljuk a találatszámot, a keresőmező visszajelzését és a bal hasáb elemeit.

Kész, ha:

- `ShowHidden` ki mellett rejtett találat nem növeli a látható darabszámot;
- `ShowHidden` be mellett a találat bekerül a rácsba és a számlálóba;
- a hasáb, az eredménysáv és a rács ugyanazt a látható találathalmazt jelzi.

**9. Az automatikus kiegészítési javaslatok típusainak kiegészítése (E11)**

Eredeti: a kirajzoló négy ikontípushoz ad sztringet (`0x0077E2E0`, `0x0077EEE0`): címke, album, mappa és képtalálat; a beírt szó kiemelése szóhatárhoz igazodik.

Nálunk: a javaslatok csak album- és mappanevek (`SearchSuggestions.qml:1-60`, `queries.py:551-605`); nincs címke- és képtalálat-sor.

Teendő: vegyük fel a címke- és képtalálat-javaslatokat, valamint az eredetivel egyező kiemelést. A kategóriák sorrendjét és a darabszám jelentését az eredeti automatikus kiegészítés adatútja feltárása után rögzítsük.

Kész, ha:

- a négy igazolt javaslattípus megjelenik;
- a kiemelés a szóhatárokat és kisbetű-érzéketlenséget követi;
- a találatok darabszáma és a kategóriák sorrendje mért eredeti szabályt követ.

### Nyitott

- **NINCS MEG:** a teljes szó, előtag vagy részszó egyezés. A meglévő `2026-11-16-koteg-426-437.txt` `0x0043C410` dekompiláció a `0x0043D7B3` címen indirekt vtable-hívást mutat, nem a célmetódust. Út: az adott vtable-slot célját előbb oldd fel az index/data xref és a meglévő diszasszemblálás alapján; utána a célmetódus összehasonlító ciklusát kövesd, és csak azonosított címhez kérj célzott Ghidra-kört.
- `Ghidra-kör kell: 0x0098C780: a `0x0043C410` hívása a query kulcs karaktereit milyen kódolásban alakítja át; végez-e ékezet- vagy kisbetű-hajtást? A meglévő `0x0043C410` kimenet csak a hívást tartalmazza, a célfüggvényt nem. [blokkoló az ékezet-paritásra]
- `Ghidra-kör kell: 0x004DC690: a `0x0043F9A0` pozitív keresőszavainál milyen halmazműveletet végez a bemeneti találati bitmapen, és hogyan működik több pozitív szóval? A meglévő dekompiláció csak a hívásait mutatja, a helper törzsét nem. [blokkoló az E1/E7 eredménylogikájára]
- `Ghidra-kör kell: 0x004DCB90: a `0x0043F9A0` kizárt szavainál mely találatokat törli a bitmapből, és hogyan viselkedik több kizárt szóval? A meglévő dekompiláció csak a hívást mutatja. [blokkoló az E7 kizárási logikájára]
- `Ghidra-kör kell: 0x005C3FE0: a mappalistáról és rácsról érkező esemény `+0x10` mezőjének kódtípusa mi; mit jelent a `0x100` feletti ág és miért az alsó bájt kerül a szövegbe? A meglévő Ghidra-fájlok a hívókat tartalmazzák, a célfüggvény törzse nincs meg. [blokkoló az E3 nem-ASCII tartományára]
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:2488`): a `0x005c3fe0` (`:2488-2531`, hívói `0x005c40e0` és `0x005c42d0`) a mappalistáról és rácsról érkező billentyű "gépelés a keresőmezőbe" útja. **Feltételei** (disassembly `0x005c3fe4-0x005c401b`): nem igaz, hogy a `[ablak+0x30f4]` és a `[ablak+0x34a4]` is nem nulla; az esemény `+0x64` jelzőbájtjának `0xc` bitjei nullák (nincs Ctrl és Alt); és a `+0x10` mező értéke előjeles összehasonlítással `0x20 < kód < 0x80` VAGY `kód > 0xff`. **A `0x80-0xff` tartomány (Latin-1: `á`, `é`, `í`, `ó`, `ö`, `ú`, `ü` és társaik) és a szóköz nincs elfogadva**, a `0x100` feletti ág igen. Ha a feltétel igaz: megkeresi a `searchcontainer/search` csomópontot (`0x00c80484`, `ytWinTrackNode`-ra átalakítva), fókuszt ad neki (az ablak `+0x7c` metódusa), **a `+0x10` mező alsó bájtjából** (`movzx ecx, byte ptr [edi+0x10]`, `0x005c4059`) egykarakteres sztringet képez (`0x00985c00`) és a `0x0065b7b0`-nak adja (az index szerint `searchcontainer/searchbutton` sztringet használ), és `1000000`-t (`0xf4240`, kezelt) ad vissza; különben `1000001`-et (`0xf4241`, nem kezelt). **Következmény:** ha a `+0x10` UTF-16 kódegység, a `0x100` feletti betűk (`ő` `0x151`, `ű` `0x171`) alsó bájtja (`0x51`, `0x71`, azaz `Q`, `q`) kerül a szövegbe. A mező kódtípusát (karakterkód vagy gombkód) a kimenet nem nevezi meg; a `0x0067eca0` (`CTextEditNode`) ugyanezt a mezőt a `0x56` (`V`) értékkel hasonlítja Ctrl jelzővel, ami gombkódra utal, a `0x20 < kód < 0x80` tartomány viszont karakterkódra.
- Ghidra-kör kell: 0x005c40e0 - a mappalista billentyűkezelője (457 bájt, `b_down`, `lb_right` sztringek): melyik eseménytípus (karakter vagy gomblenyomás) kerül a `0x005c3fe0`-ba, és ki írja az esemény `+0x10` mezőjét (UTF-16 kódegység vagy Latin-1/ANSI kód); gépelhető-e `ő`, `ű`, `á` a rácson indított keresésbe (E3) [blokkoló az E3 nem-ASCII tartományára]
  - Válasz (2026-11-18, második zárókör): eldöntve (a), a program ablakai ANSI-ak, az ékezetes betű (`0x80`-`0xff`) nem ugrik a keresőmezőbe; lásd „Második zárókör”, 4. pont.
- `Ghidra-kör kell: 0x0077D380: a keresőmező saját kezelője vagy bázisosztálya kezeli-e az `Esc`/`Delete` billentyűt, ha nincs nyitva a javaslatlista? A helyi kimenetekben ezt a címet nem találtam. [nem blokkoló]
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:5093`): a `0x0077d380` (`:5093-5147`, a `CSearchEditBox::vftable` `0x00cb43d4` 1. bejegyzése, `0x00cb43d4` 2. helye `0x0077e210`) **nem kezeli az `Esc` (`0x1b`) és a `Delete` (`0x2e`) billentyűt.** Ha a javaslatlista objektum (`[this+0x104]`) nincs, `-1`-gyel tér vissza. `WM_KEYDOWN` (`+4 == 0x100`) esetén: Fel (`0x26`, a lista `+0x20` metódusa) és Le (`0x28`, `+0x24`) mindig, `1000000` (kezelt) visszatéréssel; ha a mező szövege üres (`GetWindowTextLengthA` 0): Bal (`0x25`, `+0x28(0)`) és Jobb (`0x27`, `+0x2c(0)`); a PageUp (`0x21`, `+8(0)`), PageDown (`0x22`, `+0xc(0)`) és Enter (`0x0d`, `+0x48()`) szövegtől függetlenül; ezek és minden más billentyű `1000001`-et (nem kezelt) adnak, tehát **az `Esc` és a `Delete` a mező saját és bázisosztályi üzenetkezelőjéhez jut, nincs elnyelve.** A bázisosztály kezelője nincs a kimenetben; az index szerint a fő vtábla (`0x00cb432c`) számos bejegyzése közös a `TagPanel::AutoComplete` vtáblájával (`0x0060f1b0`, `0x00610040`, `0x0060eeb0`), tehát a bázis az automatikus kiegészítő szerkesztőmező.
- Ghidra-kör kell: 0x0060f1b0 és 0x00610040 - a `CSearchEditBox` és a `TagPanel::AutoComplete` közös bázisosztályának üzenetkezelője (a `0x00cb432c` vtábla 8. és 9. bejegyzése): mit tesz az `Esc` és a `Delete`, ha a javaslatlista nincs nyitva (mezőtörlés, fókusz elvétele, semmi) [nem blokkoló]
  - Válasz (2026-11-18, második zárókör): nem kell Ghidra-kör; az `Esc` és a `Delete` mezőhatását M2 méri, nem blokkoló.
- **NINCS MEG:** az eredeti szóindex pontos mező-hozzárendelése. A `0x004DA990` dekompiláció már megvan, de a benne hívott helper/getter-láncból nem dőlt el, mely szavak jönnek a fájlnévből, EXIF-ből, feliratból, címkéből, dátumból, helyből vagy kameraadatból. Út: a meglévő `2026-11-16-koteg-426-437.txt` `0x004DA990` és `0x004403C0` kimenetének továbbkövetése, majd kontrollált mintával mezőnkénti mérés; új kört ugyanarra a címre csak a hiányzó helpercímek azonosítása után kérj.
- **NINCS MEG:** az automatikus kiegészítési javaslatok forrásainak sorrendje és a darabszám jelentése. A `0x0077E2E0` meglévő kimenet kirajzolója, kiemelése és ikonkulcsai rendelkezésre állnak, de a kategóriák forrását nem állapítottam meg. Út: a keresőmező/automatikus kiegészítés létrehozó útjának folytatása a meglévő kimenet alapján, majd eredeti felületi mérés.
- **NINCS MEG:** a keresés előtti teljes állapot visszaállítása és a navigációs rekord létrehozási pontja. A meglévő `0x00600AC0` kimenet a keresőszöveg és szűrőgombok visszaállítását mutatja, de a képindex, fókusz, kor-csúszka és rekord létrehozása nem dőlt el. Út: a meglévő dekompilációból a mentő/hívó ág követése, kontrollált eredeti mérés a Back to View All, Ctrl+F/F3 és X utakra.
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:3955`): a kimenet részben dönt. A `0x00600ac0` (`:3955-4022`, hívói a `0x005d9cc0` `thumbui/navback` és `thumbui/navfw` ága, `0x005d9ecd`, `0x005d9f45`) egy navigációs rekordból állítja vissza az állapotot. **A rekord mezői a kimenet szerint:** `[0]` (a mappa vagy album kulcsa), `[1]` (a keresőszöveg) és az öt egybájtos jelző (`+0x9`, `+0xd`, `+0xf`, `+0x11`, `+0x13`: az öt szűrőgomb, `0x009cd8f0` állítja). **A visszaállítás sorrendje:** az öt szűrőgomb, `0x009862c0([ablak+0xf48])`, a `0x005c65e0` eredménye még egy `0x009cd8f0` hívással, a keresőszöveg (`0x00575130(szöveg, 1)`), majd **`[ablak+0x2a4]` `+0x44` metódusa a rekord kulcsával és `(1, 1, 0)` argumentumokkal** (ugyanaz a hívás, amelyet a `0x005e9bb0` az új album létrehozása után használ, tehát a mappára vagy albumra lépés a bal oldali nézetben), `0x0065b840(ablak, 0, 0, 1)` frissítés, `0x004bd9e0`, a `[[ablak+0x2c0]+0x2e0]` sztring másolása, `0x00660c80(ablak, ...)` (5524 bájt, `searchoptions/dupesearch`, `searchcontainer/searchbutton`, `webview`, `starsearch`, `facesearch` sztringek), `0x0057ec70(ablak+0x32b0)` és `0x004bda50`. **Képindexet vagy fókuszált elemet a rekord nem hordoz** (a mezői között nincs ilyen), a kor-csúszka (`0x0057ec70` célja) és a rekord létrehozási pontja a kimenetből nem dönthető el.
- Ghidra-kör kell: 0x00660c80 - a keresősáv állapotának visszaállítása (5524 bájt): mely mezők (kijelölés, fókusz, görgetés) állnak vissza; 0x0057ec70 - a `+0x32b0` objektum (kor-csúszka?) és a navigációs rekord létrehozója (a `thumbui/navback` lista felvétele keresés indításakor, hívói `0x0057f1d0`, `0x00604260`, `0x006042b0`) [nem blokkoló]
  - Válasz (2026-11-18, második zárókör): nem blokkoló (c); a Vissza/Előre előzmény a PicasaPy-ban nem létezik, a keresés előtti állapot mentése a `[főablak+0xe94..0xe9c]` mezőkben igazolt (lásd „Második zárókör”, 3. pont), a látható eredményt M1 méri.
- **NINCS MEG:** a nagyon nagy eredménylista memória- és sebességhatása. Út: eredeti Picasa pontosan rögzített, változó méretű katalógusokon végzett idő- és memória-mérése; határértéket mérés nélkül nem adok meg.
- Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:1734`, az eredménysáv szövegeihez, a Hatás bekezdés `0x005715d0` hivatkozásához): a `0x005715d0` (`:1734-1787`) az eredménysáv két szövegét állítja, egyetlen hívója a keresést végző `0x00662b20` (`0x00663617`). A `0x009cd080` két csomópontot keres a disassembly szerint: `searchoptions/searchresult` (`0x00c8f5dc`) és `searchoptions/label_search1` (`0x00c8f5f8`); az elsőre a hívótól kapott szöveget teszi (`+0x14` metódus), ha bármelyik csomópont hiányzik, `4`-et ad vissza. **A második címke szövege:** ha a keresőszöveg nem üres, az `il_SetSearchStatus::1` erőforrás (`0x00c8f624`), amely a szövegtárban `Date Range: ` (hu: `Dátumtartomány: `), utána a keresőszöveg (`0x00985af0`); a függvény ellenőrzi, hogy az erőforrásszöveg első karaktere szóköz-e, és ha nem, egy szóközt tesz (`0x00985c00`, `0x20`) a sztringbe, mielőtt a keresőszöveget hozzáfűzi; üres keresőszövegnél a címke üres. **Következtetés:** a `label_search1` az eredetiben "Date Range: <keresőszöveg>" alakú (a név szerint dátumtartomány-kereséshez tartozik), nem a találatszám; a találatszám-szöveg (`searchresult`) összeállítása a hívóban, a `0x00662b20`-ban van.
- Ghidra-kör kell: 0x00662b20 - az eredménysáv szövegeinek összeállítása a `0x005715d0` hívása előtt (`0x00663601`, `0x00663606`: a formátumsztringek `0x00c89a98`, `0x00c9ca04`, `0x00c954c0`, `0x00ca2c88`): milyen szöveg kerül a `searchresult` címkére (találatszám, dátumtartomány, "nincs találat"), és mikor lesz a `label_search1` szövege a `Date Range: ` alakú [nem blokkoló]
  - Válasz (2026-11-18, második zárókör): lezárt, nem kell új kör; a szöveget a #7079 óta a `formatting_search_bar.py` adja, a `label_search1` szerepe tisztázott (lásd a döntési táblázatot).
- **NINCS MEG:** korábban indexelt, majd elérhetetlenné tett hálózati mappa keresési hatása. Út: eredeti Picasa kontrollmérése azonos katalógussal online/offline állapotban; az index virtuális hívásai miatt az importtábla önmagában nem dönt.
- `Colab-feladat kell: keresés találattal és találat nélkül (mezőszín/sáv), Esc a keresőmezőben és a rácson, gépelés a mappalistán és rácson, majd kilépés X-szel, Back to View All-lal és második Ctrl+F/F3-mal; képernyőkép és előtte/utána mappa-, kijelölés-, görgetés- és fókuszállapot. [a futásidejű felületi hatások lezárására]

Nyitott kérdések: 7 célzott Ghidra-kérdés (3 régi és 4 új a 2026-11-16-i kör után), 6 `NINCS MEG` tétel, 1 eredeti felületi mérés.

Lezárva (a bizonyítékkal): a belépési pontok (1. szakasz); az eseményút és a billentyűsor-őr, időzítő nincs (3.); a szövegtisztítás (3.); a szóbontás szabályai (3.); a szóindex mért tartalma (2.); a kilépő utak és az `Esc` a rácson (5.); a mezőszín (4.); a rejtett képek kizárása az eredetiben (6.); a végrehajtó és a szűrő nem használ fájl- és hálózati API-t (6.); a megjegyzett nézethelyzet, a fókusz és az előzménybe mentés (Következtetés).

### Cáfoló kísérletek és kizárt út

- **„A gépelés késleltetve indul."** Cáfolva: `SetTimer` nincs a `0x005e4ac0`, `0x0065b840`, `0x00662b20`, `0x005d47e0` függvények importjai között (a híváslistát a PE import-táblából feloldva néztem), és az `EN_CHANGE` ág közvetlenül hívja a keresést. A kivétel a `0x0097fb90` billentyűsor-őr.
- **„A keresés fájlokat nyit meg."** Cáfolva a hívott függvényekre (`CreateFile`, `FindFirstFile` és hálózati API egyik sincs az importjaikban); az adatbázisréteg vtábla-hívásait nem követtem.
- **„A `Searchfor` almenü maga is keresést indít."** Kizárva: saját parancsa nulla (`0x0055c368`), a hét gyerek a `color:` tokent írja (`picasa-menu-parancsok-viselkedes.md` 20.).
- **A `CThumbUI::searchmatch` (` (%d matches)`) és a `CThumUI::searchsizekey` (`size<`, magyarul `méret<`) kulcsok** a szövegtárban vannak, de az EXE-ben hivatkozó literál nincs (nyers bájtkeresés a teljes PE-n, a prefixszel egyező találatok a `searchmatchstr` és `searchmatchnum` voltak): az eredeti ezeket nem használja. Egy `méret<` típusú keresés tehát nem bizonyított.
- **Elvetett értelmezés:** a `searchoptions/moviesearch` (`0x005d4a90`, `Preferences\SupportMovies`) és a `searchcontainer/moviesearch` két külön elem; a kapcsolat köztük nincs bizonyítva, ezért a filmszűrő láthatóságát ez a lap nem állítja a `SupportMovies`-hoz.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7072 szakasz a keresés belépő- és kilépőútjaival, a szóindex mért tartalmával, a gépelés és az eredménysáv viselkedésével, tíz eltéréssel (E1-E10, ebből az E10 feltételes), hat javasolt jegyleírással, nyolc nevesített Ghidra-körrel és egy Colab-feladattal.

### Zárókörös kiegészítés (2026-11-17)

A zárókör az alábbi státuszokat rendeli a korábbi `Nyitott` felsorolás tételeihez. A régi Ghidra-válaszokat nem vontam össze és nem töröltem. A „Nálunk” oszlopot a jelenlegi forrásból ellenőriztem.

#### A korábbi nyitott tételek döntése

| Tétel | Zárókörös válasz és státusz |
|---|---|
| Teljes szó, előtag vagy részszó egyezés | Az eredeti `0x004dc690` az indexelt szavakat a keresőszó hosszával hasonlítja össze, tehát előtagot keres; részszó-egyezést ez az út nem bizonyít. A `0x004dcb90` a pontos indexelt szó adatát keresi vissza. **Lezárva:** helyi diszasszemblálás (`0x004dc690`, `0x004dcb90`). |
| Kisbetű és ékezet | A `0x0098c780` téves cél: dátumformázó. A `0x009871f0` az ASCII nagybetűket kisbetűsíti, a több-bájtos UTF-8 bemenetet UTF-16-re alakítva `LCMAP_LOWERCASE`-t hív. Ékezetet eltávolító lépést nem találtam. A kereső és az indexelő is hívja ezt a segédet (`0x006c0fc0`, `0x004403c0`). **Lezárva statikusan;** tényleges helyi beállítás szerinti találati paritásra felületi mérés kell. |
| Pozitív és kizárt keresőszavak | A `0x006c0fc0` külön pozitív és kizárt szólistát állít elő. A `0x0043f9a0` pozitív ágának bitmapjeit a `0x00413290` metszi; a kizáró ág a negatív bitmapben megjelölt képeket törli az addigi eredményből. A `0x004dc690` előtagot enged, mindkét szólistában. A `0x004dcb90` nem a kizárás kezelője, hanem a szóindex pontos adatát adja vissza. **Lezárva statikusan;** a szöveg és az eszköztárszűrők egymás közötti kapcsolata továbbra is nyitott. |
| `0x005c3fe0` és `0x005c40e0`, gépelés a mappalistán vagy a rácson | A meglévő Ghidra-válasz szerint a `0x005c3fe0` a `+0x10` mező alsó bájtját fűzi a kereséshez. A `0x005c40e0` a `+0x64` jelző 0. bitjénél erre az ágra lép, egyébként a mezőt billentyűkódokkal hasonlítja össze. A karakterkódot előállító eseményforrás és a mező kódolása egyik kimenetben sincs meg. **NINCS MEG:** mérés eredeti Picasában, `a`, `á`, `ő`, `ű` begépelésével külön a rácsban és a mappalistán; a beírt keresőszöveget és találatokat kell rögzíteni. |
| `0x0077d380`, keresőmezőbeli Esc és Delete | A meglévő Ghidra-válasz megerősíti, hogy a keresőmező saját kezelője nem nyeli el e két billentyűt, hanem továbbadja az alapkezelésnek. A `0x0060f1b0` és `0x00610040` helyi diszasszemblálása megmutatja a közös eseményutat, a tényleges mezőhatást nem. **NINCS MEG:** mérés eredeti Picasában, javaslatlista nyitva és zárva, a szöveg kurzorának elején és közepén; rögzítendő a szöveg, a fókusz és a keresési állapot. Ghidra-kör nem szükséges ehhez a látható kimenethez. |
| Visszahívás és megjegyzett nézethelyzet | A `0x00600ac0` meglévő kimenete szerint a navigációs rekord mappa- vagy albumkulcsot, keresőszöveget és öt szűrőjelzőt hordoz. A `0x005fa430` helyi utasításai a visszaállításkor listaválasztási és mappára vagy albumra navigáló ágat mutatnak. A rekord mezői nem bizonyítják a képkijelölés vagy fókusz visszaállítását; a kor-csúszka külön `0x0057ec70` hívást kap. **NINCS MEG:** mérés Back to View All, második Ctrl+F/F3 és X után, előre beállított mappa-, képkijelölés-, görgetés-, fókusz- és kor-szűrőállapottal. A korábbi „képindex és fókusz mentése” állítást a meglévő rekordkimenet nem támasztja alá. |
| `0x00660c80`, `0x0057ec70` visszaállító szerepe | A `0x00600ac0` kimenete már megmutatja, hogy a visszahívás visszaállítja az öt szűrőkapcsolót és a keresőszöveget, majd a mappa- vagy albumkulcsot. A kor-csúszka objektum pontos látható hatása ebből nem dőlt el. **NINCS MEG:** ugyanaz a fenti, előre beállított kor-szűrős felületi mérés. A régi Ghidra-kérés nem indok a meglevő `0x00660c80` kimenet újbóli kérésére. |
| `0x00662b20`, eredménysáv | A meglévő Ghidra-válasz feloldja a két eredménysáv-elem szerepét: a `searchresult` szövegét a keresési darabszámhoz állítja, a `label_search1` a nem üres kifejezéshez `Date Range: ` előtagot használ. A jelenlegi keresősáv magyar szövege a `formatting_search_bar.py:60-83` alatt kezeli a találatot és a találat nélkül állapotot. **Lezárva:** meglévő Ghidra-kimenet és jelenlegi forrás. |
| Pontos mező-hozzárendelés | A meglévő `0x004da990` kimenet az index belső listakezelését mutatja, de nem nevezi meg a fájlnév, felirat, kulcsszó, kamera, dátum, hely és szín forrását. A meglévő `wordhash.dat` vizsgálat 28 indexelt mezőt igazol, a mezők neveit nem. **NINCS MEG:** célzott Ghidra-kör a `0x00682c00` hívóra, amely az egyetlen közvetlen hívója a `0x004403c0` szóindexelőnek, majd mezőnkénti, egyedi értékű eredeti próba. |
| Javaslatlista forrása, sorrendje és darabszáma | A meglevő rajzolóadat négy ikontípust bizonyít, de nem az adatforrást és a sorrendet. A PicasaPy javaslatlistája csak mappát és albumot ad (`search_controller.py:117-128`). Ez külön, látható javaslatlista-kérdés; önmagában nem dönti el a keresési találatok tagságát, ezért a #7072 négy kérdésének lezárását nem blokkolja. Következő kutatási kérdésként maradjon külön nyilvántartva. |
| Nagy találatszám | Az átnézett eredeti végrehajtóban nem találtam rögzített találatszám-korlátot; a keresés találati bitmapet használ és a darabszámot tagolja. Az eredeti futásidejű idő- és memóriahatás **NINCS MEG**: változó találatszámú katalógussal kell mérni, a tényleges darabszám, futási idő és memória rögzítésével. A PicasaPy 140 755 képes mérőadaton 27 179 találat mellett 597 ms mediánt dokumentál (`index/queries.py:512-514`); ez nem az eredeti Picasa mérése. |
| Elérhetetlen hálózati mappa | A keresési út közvetlen fájl- és hálózati API-hívás nélkül, indexrétegen át dolgozik; az index virtuális hívásainak offline hatása ebből nem dönthető el. **NINCS MEG:** ugyanazon, előzetesen indexelt hálózati katalógus online és elérhetetlen állapotú keresési próbája, a találatlista, hibajelzés és befejezés rögzítésével. |

#### Jelenlegi forrás szerinti eltérések

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A pozitív szavak bitmapjeinek metszete, a kizárt szavak eltávolítása; előtag-egyezés (`0x0043f9a0`, `0x00413290`, `0x004dc690`). | `src/picasapy/index/queries.py:540-570`: egyetlen idézett FTS-kifejezés; a `tag:`/`címke:` előtag eltávolítása után sincs címkemezőre szűrés (`:18-51`). | E6/E7: a tokenek és kizárások eredeti szabályára állítani. |
| A keresés, a csillag-, arc-, film- és más szűrők, valamint a kor-szűrő egy közös objektumban vannak (`0x00660c80`, `0x00662220`). | `src/picasapy/app/search_controller.py:23-60`, `controller_filter_mixin.py:20-67`: a szöveges keresés külön nézetmódra vált és kikapcsolja az aktív szűrőt. | E1: közös állapot; a szűrők szöveges kereséssel való eredménykapcsolatát csak eredeti bizonyíték után rögzíteni. |
| A keresés eredménye a rejtett szűrő alkalmazása után készül (`0x00660c84`-`0x00660e25`). | `src/picasapy/app/search_controller.py:77-82` nyers találatokból készíti a bal hasábot és a számlálót; `controller_photo_list_mixin.py:117-120` csak a rács kirajzolása előtt szűri a rejtetteket; `controller_state_mixin.py:148-169` a nyers számlálót használja a visszajelzéshez. | E10: előbb képezze a látható találati halmazt, majd abból frissítse a hasábot, a visszajelzést és a rácsot. |
| A `]search` sor neve `Search results` (`0x004ad430`). | `src/picasapy/app/qml/PicasaPy/FolderPane.qml:26-31`: `Search results for "%1" (%2)`. | E9: a sor feliratát igazítani, a darabszám helyét az eredeti mérése szerint meghatározni. |
| A mappalistán és a rácson gépelt karakter a keresőmezőbe kerül (`0x005c3fe0`, `0x005c40e0`, `0x005c42d0`). | `src/picasapy/app/qml/PicasaPy/SearchGridKeys.qml:72-90` csak a `0x21`-`0x7f` karaktertartományt kezeli; `FolderPaneContent.qml:304-307` fel/le nyilat kezel. | E3: a mappalistát a közös karakterútba kötni, az eredeti ékezetes viselkedés méréséig nem kiterjeszteni. |
| A `tag:`/`címke:` keresőelőtag mezőszűrést állít; az idézőjel nem frázisjelölő; a pont és aláhúzás elválasztó; a pozitív/kizárt szavak különülnek el. | `src/picasapy/index/queries.py:21-51, 540-570`: a tag-előtag csak leválik, a megmaradó szöveg idézett frázis. | E6/E7: a feldolgozást és a mezőszűrést a bizonyított eredeti szabályhoz igazítani. |
| Az eredeti kereső az indexelt mezők között a mezőforrásokhoz kötött szavakat keresi; az attribútumok pontos felsorolása a `0x00682c00` vizsgálata után állítható össze. | `src/picasapy/index/schema.py:122-125`, `queries.py:496-537`: név, felirat, kulcsszó, mappanév és színtoken szerepel; kamera, dátum és hely nem önálló keresőoszlop. | E8: csak bizonyított eredeti mezőkre készítsen bővítést; mezőnkénti próbával igazolja a találatot. |
| Rejtett kép nem része a találati halmaznak, ha a rejtett képek mutatása ki van kapcsolva (`0x00660c84`-`0x00660e25`). | A fenti nyers számlálási út miatt a kereső visszajelzése találatot jelezhet akkor is, ha a rács üres. | E10: a keresési darabszám és a látható rács tagságának egyezése. |

#### Javasolt fejlesztői jegytörzsek

| Jegy | Eredeti | Nálunk | Teendő | Kész, ha |
|---|---|---|---|---|
| E1 | Eredeti: a keresés és a szűrőkapcsolók egy objektumban futnak (`0x00660c80`, `0x00662220`). | Nálunk: `search_controller.py:23-60`; a szöveges keresés kikapcsolja az aktív szűrőt. | Teendő: közös keresési és szűrőállapot, az eredménykapcsolat csak igazolt szabály szerint. | Kész, ha: a szöveges keresés és bármelyik szűrő együtt aktív, és az eredményhalmaz a mért eredeti szabályt követi. |
| E2 | Eredeti: a navigációs rekord mappa/album kulcsot, keresőszöveget és öt szűrőjelzőt tartalmaz (`0x00600ac0`); a teljes nézet-visszaállítás felületi hatása még mérendő. | Nálunk: `MainWindowToolbar.qml:82-84`; gépeléskor a kijelölés törlődik, keresés előtti nézethelyzetet a forrás nem ment. | Teendő: a méréssel igazolt mappa-, kijelölés-, görgetés-, fókusz- és kor-állapotot visszaállítani az eredeti kilépőutakon. | Kész, ha: Back to View All, második Ctrl+F/F3 és X az eredetileg mért állapotot adják. |
| E3 | Eredeti: a mappalistán és rácson gépelés a keresőmezőbe vezet (`0x005c3fe0`, `0x005c40e0`, `0x005c42d0`); a nem ASCII kódolás nyitott. | Nálunk: rácson `SearchGridKeys.qml:72-90`; a mappalistán `FolderPaneContent.qml:304-307` csak fel/le. | Teendő: a mappalistát a közös keresési karakterútba kötni; a kódtartományokat mérés szerint kezelni. | Kész, ha: minden mért karakter egyszer kerül a mezőbe, és a Ctrl/Alt-os billentyűk nem indítanak keresést. |
| E6/E7 | Eredeti: a szóelőtagok és kizárások külön listába kerülnek, a pozitív szavak metsződnek (`0x006c0fc0`, `0x0043f9a0`, `0x00413290`); a `tag:` mezőszűrő. | Nálunk: `queries.py:18-51, 540-570`; a keresés egy idézett frázis, a `tag:` csak leválik. | Teendő: a tisztítást, előtagot, pozitív és kizárt szavakat az eredetihez igazítani. | Kész, ha: pont, aláhúzás, idézőjel, `tag:`/`címke:`, előtag és mínuszos szó a bizonyított eredeti találatokat adja. |
| E8 | Eredeti: a mezőforrások között név, felirat, címke, kamera/EXIF, dátum, hely és szín lehetséges; a pontos hozzárendelés még nincs meg. | Nálunk: `schema.py:122-125`, `queries.py:496-537`; név, felirat, kulcsszó, mappanév és színút. | Teendő: a `0x00682c00` és a mezőnkénti próba után csak a bizonyított hiányzó mezőket felvenni. | Kész, ha: minden mező egyedi próbaértékkel külön igazolt, találgatott mező nincs. |
| E9 | Eredeti: a bal hasáb keresési sora `Search results` (`0x004ad430`). | Nálunk: `FolderPane.qml:26-31` a kifejezést és darabszámot írja ki. | Teendő: az eredeti sorfelirat és a méréssel igazolt számlálóhely használata. | Kész, ha: a sorfelirat és a számláló helye az eredeti felületi mérés szerint egyezik. |
| E10 | Eredeti: a rejtett képek a keresés előtt kiesnek (`0x00660c84`-`0x00660e25`). | Nálunk: `search_controller.py:77-82`, majd `controller_photo_list_mixin.py:117-120`; a bal hasáb és számláló nyers eredményt használ. | Teendő: a látható halmazból építeni a hasábot, számlálót és rácsot. | Kész, ha: a rejtett képek ki/be állapota mellett a bal hasáb, mezőjelzés, eredménysáv és rács ugyanazt a látható tagságot mutatja. |

E5 időzítési jegy: a jelenlegi `MainWindowToolbar.qml:48-69, 82-87` nem használ időzítőt, az eseményhurok következő körében futtatja a keresést, és azonos aktív kifejezésnél kihagyja az ismétlést; ezt az eredeti `EN_CHANGE` út és az azonos szövegű újrahívás elhagyása alátámasztja (`0x005e4e0d`, `0x0097fb90`, `0x0065b906`-`0x0065b988`). Új E5 fejlesztői jegyet nem javaslok.

#### Bizonyítottság és cáfoló próba

**Fok: nyitott.** A szóillesztés részletei binárisból megvannak, de a pontos kereshető mezők, az ékezetes billentyűút és több kilépési állapot, a nagyon sok találat futásidejű hatása, valamint a hálózat nélkül maradt mappa viselkedése még nem dőlt el eredeti Picasa-méréssel.

**Két út a szóillesztéshez:**

- **A:** a meglévő Ghidra-kimenet a `0x006c0fc0` pozitív/kizárt listáját és a `0x0043f9a0` feldolgozó ágait mutatja.
- **B:** a helyi utasításszintű olvasás a `0x004dc690` előtag-összehasonlítását és a `0x00413290` találati bitképeinek metszetét mutatja; a `0x0043fda4` hívóhely veremargumentumai igazolják, melyik bitmap a forrás és melyik a cél. A két út egyezik a pozitív szavak metszésében és a kizárt szavak törlésében.

**Cáfoló kísérlet:** megpróbáltam cáfolni, hogy az eredeti csak idézett, teljes frázist keres, és hogy a `0x004dcb90` végzi a kizárást. A `0x004dc690` hívólistáján és utasításain a keresőszó hosszával végzett előtag-összehasonlítás látszik; a `0x0043f9a0` kizáró ciklusa a negatív bitmapben megjelölt elemeket törli, míg `0x004dcb90` az index pontos szóadatát keresi vissza. A cáfoló eredményét a tényleges hívóhelyekkel ellenőriztem; az eredeti nem azonos az egyetlen idézett FTS-frázissal.

#### A jegy „Kész, ha” pontjai

- ⛔ **Belépési pontok és kereshető adatok:** a fő kereső, billentyűút, menü és szűrőkapcsolók feltártak; az eredeti mező-hozzárendelés még nincs meg (`0x00682c00`).
- ⛔ **Gépelés közbeni viselkedés:** az eredeti időzítő nélküli keresés, kisbetűsítés, előtag-egyezés és pozitív/kizárt szavak feltártak; az eseménykód ékezetes karaktereinek eredménye mérendő.
- ⛔ **Bal hasáb, rács, kijelölés, találat nélkül és kilépés:** a fő statikus utak és az eredménysáv megvannak; a keresőmező Esc/Delete alapkezelése és a visszaálló nézetállapot felületi eredménye mérendő.
- ⛔ **Rejtett, sok találat, elérhetetlen hálózat:** a rejtett képek eredeti kizárása bizonyított, de a jelenlegi számlálás eltér; az eredeti teljesítmény és offline viselkedés nincs megmérve.

#### Nyitott

- `Ghidra-kör kell: 0x00682c00 - mely fájlmezők és metaadat-értékek kerülnek a 0x004403c0 szóindexelőbe, különösen név, felirat, kulcsszó, kamera/EXIF, dátum, hely és szín esetén? A meglévő 0x004da990 kimenet az index belső listakezelését fedi le, a 0x004403c0 közvetlen hívója nincs dekompilálva. [blokkoló a kereshető mezők lezárására]`
  - Válasz (2026-11-18, második zárókör): téves cél, a `0x00682c00` feltöltéskezelő; az új egyetlen kérés a `0x00456610` (lásd „Második zárókör”, 6. pont és a döntési táblázat alatti sor).
- **NINCS MEG - eseménykód:** eredeti Picasában a rácson és mappalistán külön gépeld be az `a`, `á`, `ő`, `ű` karaktereket; rögzítsd a keresőmező tényleges karaktereit és találatait. A `0x005c3fe0` az alsó bájtot használja, de a bemeneti kódolást a bináris bizonyíték nem nevezi meg.
- **NINCS MEG - Esc, Delete és visszaállítás:** a keresőmezőben nyitott és zárt javaslatlistával, továbbá a rácson próbáld az Esc-et; a Delete-t a mező elején és közepén. Indulás előtt rögzítsd a kiválasztott mappát, képet, görgetést, fókuszt és kor-szűrőt; lépj ki X-szel, Back to View All-lal és második Ctrl+F/F3-mal, majd rögzítsd az állapotot.
- **NINCS MEG - látható mezőeredmény:** külön, egyedi kifejezéssel keress fájlnevet, mappanevet, feliratot, címkét, helyet, dátumot, kamerát és színt. Rögzítsd a keresőkifejezést és a képek listáját; a mezőcímkéket a `0x00682c00` eredményével vesd össze.
- **NINCS MEG - rejtett találat:** ugyanazzal az indexelt katalógussal keress rejtett képre `ShowHidden` ki és be állapotban; rögzítsd külön a bal hasábot, rácsot, visszajelzést és darabszámot.
- **NINCS MEG - sok találat és hálózati leválás:** változó tényleges találatszámú katalógusokon rögzítsd az eredeti keresési időt és memóriahasználatot; ugyanazt az előre indexelt hálózati katalógust próbáld online és elérhetetlen állapotban, rögzítve a találatokat, hibajelzést és befejezést.
- **Külön kutatási kérdés:** az automatikus kiegészítés javaslatainak forrása, sorrendje és darabszáma. Ez a javaslatlista, nem a keresési találathalmaz viselkedését vizsgálja.

### Zárási döntés

**A #7072 jelenleg nem zárható le.** Egyetlen blokkoló a meg nem szerzett eredeti Picasa-bizonyítékcsomag: a mezőforrások célzott `0x00682c00` Ghidra-köre, valamint a fenti konkrét felületi mérések. A statikus szóillesztési kérdések lezártak; az E1, E2, E3, E6/E7, E8, E9 és E10 fejlesztői jegytörzsei maradnak, az eredeti viselkedés pontosítása után véglegesíthetők. Az E11 javaslatlista külön követő kérdés.

(A fenti döntést a következő, „Második zárókör” szakasz felülírja; a korábbi szöveg megmarad.)

### Második zárókör (2026-11-18)

A második zárókör a megmaradt `NINCS MEG` és `Ghidra-kör kell:` tételeket
egyenként döntötte el: (a) a meglévő bizonyítékból, (b) egyetlen célzott körrel
vagy futtatott méréssel, (c) nem blokkolónak minősítve. Új bizonyíték: helyi
utasításszintű olvasás (`capstone`, a `Picasa3.exe` 3.9.141.259, SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, csak
olvasva; a veremértelmezést és a mezőeltolásokat a hívóhelyek utasításain
ellenőriztem, nem a dekompilációból vettem át), a bináris-index, és az eredeti
Picasa 3 magyar referencia-képernyőképe
(`2741-keresesre-megjeleno-bal-also-mezo-tartalma.jpg`, a tulajdonos
átadómappájában, leltár: `referencia/kepek-leltar.md`). A „Nálunk” oszlopokat a
mai főág (`b0c51a68e`) forrásán `grep`-pel ellenőriztem. A korábbi szakaszokat és
Ghidra-válaszokat nem töröltem és nem vontam össze; ahol ez a szakasz felülír
egy korábbi állítást, kimondom.

#### Felülírt vagy pontosított korábbi állítások

1. **E9 visszavonva: a bal hasáb sorfelirata egyezik.** Az eredeti Picasa 3
   referenciaképén az `Albumok (3)` csoport első sora `Találatok a(z) "ai"
   kifejezésre (365)`: a kifejezés és a darabszám is benne van, ugyanúgy, mint a
   `Csillagozott képek (6)` és a `Legutóbb frissítve (34)` soroknál. A szövegtár
   `CThumbUI::searchmatchstr` kulcsa `Search results for "%s"` / `Találatok a(z)
   "%s" kifejezésre` (`referencia/stringres-en-hu.tsv:794`). A `0x004ad430` csak a
   sor alapértelmezett `CAlbumState::SearchResults` nevét (`Search results`,
   magyarul `Találatok`) adja a létrehozáskor (`0x004ad45e`-`0x004ad482`, a két
   záró argumentum nulla); a korábbi „A `]search` sor neve `Search results`”
   állítás ezt a létrehozási nevet olvasta megjelenő szövegnek. A PicasaPy az
   eredeti alakot adja: `FolderPane.qml:29-31`, magyar fordítás
   `picasapy_hu.ts:7899-7901` (`Találatok a(z) "%1" kifejezésre (%2)`). **A „7. A
   bal hasáb kereséssor-felirata (E9)” jegytörzs, a 7. szakasz E9 sora és a
   zárókörös E9 sor visszavonva, fejlesztői teendő nincs.** Egy mellékkérdés
   marad: a képernyőképen (a javaslatlista nyitva, a rács még a régi mappát
   mutatja) a bal hasáb minden mappát felsorol, tehát a #49-es „szűkül a
   találatos mappákra” viselkedés beállt állapotát a kép nem igazolja; ezt M1
   méri.

2. **E1: a szöveg és a gombok kapcsolata ÉS, igazolt a csillag, az arc és a
   geocímke gombra.** A `0x00662220` a `0x0043f9a0`-nak átadja a keresőszöveget
   (`[szűrő+0x2c]`) és a szűrő pozitív szólistáját (`[szűrő+0x30]`, mérete
   `[szűrő+0x34]`; `0x00662352`-`0x00662365`). A `0x0043f9a0` a szöveget a
   `0x006c0fc0`-val bontja, a kimeneti listákat a teljes függvényben nem nullázza,
   csak hozzáfűz (a méret növelése `0x006c1394`, `0x006c1516`; a hívás
   `0x0043fa3b`-`0x0043fa4b`: az első kimenet ugyanaz a pozitív lista, a második a
   kizárt lista). A gombok belső szójelét (`]star` `0x006615db`, `]face`
   `0x006617f3`, `]geo` `0x00661a0c`; a feltétel a `[szűrő+1]`, `[szűrő+9]`,
   `[szűrő+0xb]` jelző) a `0x00660c80` ugyanennek a pozitív listának a végére írja
   (a `0x006611af` előbb nullázza). A végrehajtó a pozitív lista minden szavára
   külön bitképet kér és metszi (`0x0043fda4` -> `0x00413290`). Következtetés: a
   szöveg szavai és a három gomb szójelei egy listában vannak, az eredményhalmaz
   a metszetük, tehát **ÉS**. A mért szótárban a `]star`, `]geo`, `]face` valóban
   szóként szerepel (2. szakasz, a belső szójelek sora). A rejtett kép kizárása
   (`]hidden`, `0x00660ca2`) a `[szűrő+0x48]` kizárt listába kerül, nem a
   pozitívba. A film, az online és a másodpéldány gomb, valamint a kor-csúszka
   kapcsolata a szöveggel **nincs igazolva** (külön jelzők, `0x00661093`-`0x00661115`;
   a `0x00662220` ágait nem olvastam végig): M6 méri.

3. **E2: a keresés előtti állapot mentése igazolt, a korábbi két megállapítás nem
   mond ellent egymásnak.** A `0x0065ba5c`-`0x0065bb0c` szakasz az első nem üres
   szövegváltozáskor, ha a mentett hely még üres (`[főablak+0xe94] == -1`,
   `0x0065ba5c`), három mezőt ír a főablak-objektumba: `[főablak+0xe98]` a
   kijelölt kép sorszáma (`[főablak+0xe68]`), ennek híján az aktuális kép
   sorszáma (`[főablak+0xe64]`) (`0x0065ba69`-`0x0065ba7a`); `[főablak+0xe9c]`
   egy jelzőbájt (`0x0065ba88`-`0x0065baa9`); `[főablak+0xe94]` a bal hasáb
   kijelölt sorának indexe (`0x0065bac0`-`0x0065bb0c`). Ez más tároló, mint a
   Vissza/Előre navigációs rekord (`0x00600ac0`), amelynek tényleg nincs
   képindexe: az „a rekordkimenet nem támasztja alá” sor a rekordra igaz, az
   ablakmezőkre nem. A kilépő rutin (`0x005d47e0(újraépít, visszaállít)`) csak
   akkor olvassa ki a mentett `[főablak+0xe94]`-et és a rácson épp kijelölt
   képet, ha mindkét argumentum nem nulla (`0x005d47f0`-`0x005d4845`); ezután
   újraépít (`0x0065b840`, `0x005d49eb`), majd a `0x005fa430`-at hívja
   (`0x005d4a01`, csak ha a második argumentum nem nulla). A `0x005fa430` az
   átadott képet a mentett `[főablak+0xe98]`/`[főablak+0xe9c]` értékkel veti
   össze (`0x005fa451`-`0x005fa47c`), és ennek alapján választja ki a
   visszaállítandó listasort. Az X gomb `(1, 0)`-val hívja, tehát NEM állít
   vissza; a „Back to View All” és a második `Ctrl+F`/`F3` `(1, 1)`-gyel igen. A
   `0x005fa430` további ágát nem követtem végig, ezért a tényleges görgetési
   helyzet és a fókusz M1-re marad.

4. **E3: a nem-ASCII ág statikusan lezárva (ANSI ablak).** A `WM_CHAR` üzenetet a
   billentyűszűrő (`0x00a53b00`, a `0x00a53b2f`-nél a `0x102` ág) a `0x00a582f0`-nak
   adja, ez az üzenet `wParam` alsó 16 bitjét (előjelesen bővítve,
   `0x00a5836c`-`0x00a58370`) a `0x009dd770`-nel az esemény `+0x10` mezőjébe
   írja. A program minden saját ablakát az ANSI-változatú függvénnyel hozza létre:
   a `CreateWindowExA` négy hívóhelyen szerepel (`0x0054b761` filmgyerekablak,
   `0x00924b79` és `0x0092631f` az ATL osztályai, `0x00aa58fd` a javaslatlista), a
   Unicode-változatnak egyetlen hívóhelye van (`0x009aec0a`), és ennek a függvénynek
   (`0x009aeb10`) nincs hívója az indexben; az osztályokat `RegisterClassA` és
   `RegisterClassExA` jegyzi be (`0x0054c8a5`, `0x00920907`, `0x009246cd`), a
   `RegisterClassW` (`0x009b0191`) szintén egy hívó nélküli függvényben áll
   (`0x009b0080`); az üzenetciklus `GetMessageA`/`PeekMessageA`/`DispatchMessageA`.
   ANSI ablakban a `WM_CHAR` egy bájt a rendszer kódlapján (magyar rendszeren
   Windows-1250: `á` `0xE1`, `ő` `0xF5`, `ű` `0xFB`), vagyis a `0x80`-`0xff`
   tartományba esik, amelyet a `0x005c3fe0` elvet; a `0x100` fölötti ág magyar
   rendszeren nem érhető el. Következtetés: az eredetiben a rácson és a mappalistán
   az ékezetes betű NEM ugrik a keresőmezőbe. A korábbi `ő` -> `Q` feltevés
   (`+0x10` alsó bájtja) ANSI ablakban nem fordulhat elő. A vtábla-hívásokat az
   index nem látja, ezért a következtetés erős, de nem teljes; M5 megerősíti, nem
   blokkoló. A PicasaPy rácsa már ezt adja (`SearchGridKeys.qml:77`:
   `code < 0x21 || code > 0x7f`), a mappalista nem.

5. **E5 kész, E6 kész, E7 csak részben.** E5 (#7081): `MainWindowToolbar.qml:54-88`
   (`Qt.callLater`, azonos szövegnél nincs újrakeresés). E6 (#7081):
   `index/queries.py:21-50` az eredeti szerint vágja a szélső ` ,./\` karaktereket,
   leválasztja a `tag:`/`címke:` előtagot, és szóhatárokra bont. E7-ből hiányzik:
   a szavak egyetlen idézett frázisba kerülnek (`queries.py:555`), tehát csak
   egymás mellett, ebben a sorrendben egyeznek; a `-` jel elválasztóvá válik
   (kizárás nincs); előtag-egyezés nincs (teljes szó). Az E6/E7 jegytörzs ennek
   megfelelően szűkül (lent).

6. **A `0x00682c00` Ghidra-kérés téves célra mutatott.** A függvény sztringjei
   feltöltéskezelőhöz tartoznak (`Deleting suppressed photos`,
   `CUploadManager::DeleteSuppressed`, `UploadManager::DeleteCancelMessage`,
   `Logged in for sync`), a `0x004403c0` pedig csak a `]web_` és `]suppress`
   szójelre hivatkozik: ez a feltöltési állapot szójeleit frissíti, nem a fájlnév-,
   felirat- vagy EXIF-szavakat. A szóbeszúró (`0x004d9aa0`, kisbetűsít a
   `0x009871f0`-nel) 23 hívója közül a `0x00456610` (17 276 bájt) az, amelyik a
   `.picasa.ini` mezőire hivatkozik (`caption`, `keywords`, `rating`, `hidden`,
   `geotag`, `faces`, `filters`, `albumlist`). Az E8 Ghidra-kérés ezért erre a
   címre módosul (lent).

7. **E11: új adat a referenciaképről.** `ai` begépelésekor a legördülő tíz sora
   azonos ikonú, darabszámos szósor: `ai (332)`, `ai2 (2)`, `ai1 (2)`, `ai3 (2)`,
   `ai11 (1)`, `ai10 (1)`, `ai13 (1)`, `ai12 (1)`, `ai15 (1)`, `ai14 (1)`.
   A darabszám szerint csökkenő a sorrend, azonos darabszámnál nem névsori
   (`ai2`, `ai1`, `ai3`; `ai11`, `ai10`, `ai13`, `ai12`...); a keresett szóval
   kezdődő szavak (előtag-egyezés) jelennek meg; mappa- vagy albumsor a tíz
   sorban nincs. A PicasaPy javaslatlistája csak mappát és albumot ad
   (`index/queries.py:605-`, `search_controller.py:118-`,
   `SearchSuggestions.qml:16,90,96`). A felső korlát (a tíz sor korlát-e vagy a
   találatok száma), az azonos darabszám sorrendje és a mappa/album/képtalálat
   sorok megjelenése M4-re marad.

#### A megmaradt nyitott tételek döntése

| Tétel | Döntés | Jelölés |
|---|---|---|
| Mező-hozzárendelés (E8): a korábbi `0x00682c00` kérés | (b) a cél javítva, lent egyetlen Ghidra-kör; a mezőnkénti megfigyelés M3 | blokkoló az E8 fejlesztői jegyre, **nem blokkoló** a #7072 lezárására, ha a K2 követő jegy elkészül |
| `0x005c3fe0`/`0x005c40e0`: eseménykód, ékezetes betűk (E3) | (a) ANSI ablak, a `0x80`-`0xff` elvetve (4. pont) | lezárva statikusan; M5 csak megerősít; **nem blokkoló** |
| `0x0077d380`, `0x0060f1b0`, `0x00610040`: `Esc` és `Delete` a keresőmezőben | (b) futtatott mérés (M2); Ghidra-kör nem szükséges, mert a kezelő egyiket sem nyeli el, a mezőhatás a szerkesztőmezőé (a `Delete` valószínűleg a kurzor utáni karaktert törli, ez nincs bizonyítva) | **nem blokkoló** |
| Visszaállítás és megjegyzett nézethelyzet (E2) | (a) a mentett mezők és a kilépő utak (3. pont); (b) a látható eredmény M1 | E2 jegytörzs M1 után vehető fel |
| `0x00660c80`, `0x0057ec70`: kor-csúszka állapota, a navigációs rekord létrehozója | (c) a Vissza/Előre előzmény (`thumbui/navback`, `navfw`) a PicasaPy könyvtárnézetében nem létezik (`grep -rn navback src/picasapy` találat nélkül), a rekord létrehozása ennek a hiányzó funkciónak a része, nem a keresésé; a kor-csúszka kilépés utáni állását M1 e) lépése méri | **nem blokkoló** |
| `0x00662b20`, az eredménysáv szövege | lezárt (#7079), a `Date Range: ` címke szerepe tisztázott | lezárva |
| Javaslatlista forrása, sorrendje, darabszáma (E11) | (b) a képernyőkép részben dönt (7. pont); a többit M4 mérje | **nem blokkoló** a találathalmazra; E11 jegytörzs M4 után |
| Nagy találatszám | (c) a végrehajtóban nincs találatszám-korlát, a PicasaPy is mindet visszaadja; csak a sebességet érinti, nem a találatok tagságát | **nem blokkoló** |
| Elérhetetlen hálózati mappa | (c) a keresés a helyi `db3` szóindexből dolgozik (`album-sorrend.md` 2.1), a PicasaPy keresése sem nyúl a fájlrendszerhez; a lekapcsolt mappa miniatűrjeinek és megnyitásának viselkedése a mappakezelő és a megjelenítés jegyeinek tárgya | **nem blokkoló** |
| Rejtett találat | (a) az eredetiben a rejtett kép kizárva a találati halmazból (`0x00660ca2`), a számláló, a hasáb és a sáv ugyanabból a halmazból épül (egyetlen végrehajtó); a PicasaPy nyers listából számol (E10) | lezárva statikusan; E10 felvehető mérés nélkül |
| A `tag:`/`címke:` előtag hatása (`[szűrő+0xc]`) | (b) M3 két keresése (`címke:zqkw1` és `zqkw1`) eldönti, van-e mezőszűrés | **nem blokkoló**; addig az előtag csak leválik (mai viselkedés) |
| Szöveg és film/online/másodpéldány gomb/kor-csúszka kapcsolata (E1) | (b) M6 | **nem blokkoló** a szöveg és a csillag/arc/geocímke gomb ÉS-kapcsolatára |

#### K2 statikus eredmény (#7196)

A `0x00456610`-hoz már volt archivált Ghidra-kimenet; ezt a függvény méretre
korlátozott helyi disassemblyjével és a bináris-index xrefjeivel ellenőriztem.
Az alábbi eredmény a közvetlen hívásokat rögzíti. A `0x004d9aa0` kulcsot és
rekordazonosító-listát frissít; önmagában nem bont szöveget szavakra.

| `.picasa.ini` mező (string-xref) | Utasításút a `0x00456610`-ban | Közvetlen szóindex-hatás | Bizonyítottság |
|---|---|---|---|
| `caption` (`0x00c7fad0`) | A mezőág `0x00458946`/`0x00458984`; a teljes mezőértéket a `+0x50` virtuális helyre adja át (`0x00458991`). | Nem a `0x004d9aa0`-t hívja közvetlenül. Helyi szóköz-/szókarakter-darabolás nincs; a callback utáni szóhatár **NINCS MEG**. | megerősített: a közvetlen átadás; nyitott: a callback végső feldolgozása |
| `keywords` (`0x00c81848`) | A `0x004588d7` a `0x009881d0`-t hívja `0x2c` (vessző) elválasztóval; az eredmény elemei egyenként a `+0x5c` virtuális helyre jutnak (`0x00458904`). | Vesszőnkénti elembontás bizonyított; szóközön belüli vagy további szóhatár **NINCS MEG**, mert a callback célja nincs feloldva. Nincs közvetlen `0x004d9aa0` hívás. | megerősített: a vesszőtagolás; nyitott: a végső szóhatár |
| `rating` (`0x00c81448`) | Az `atol` a `0x00458a33` címen olvassa az értéket; nem nulla értéknél a `0x00458b1d` hívja a beszúrót. | A `]star` jelölő kerül be (`0x00c811d4`); a numerikus érték nem indexkulcs. | megerősített |
| `hidden` (`0x00c81860`) | A `yes` ág a `0x00458ee5` címen hívja a beszúrót; a másik ág `0x004da1d0`-t használ. | A `yes` értékhez `]hidden` jelölő tartozik (`0x00c811f4`). | megerősített |
| `geotag` (`0x00c81874`) | A `0x00459344` körüli ág `sscanf("%lf,%lf")`-fel két koordinátát olvas. | Ebben az ágban nincs közvetlen `0x004d9aa0` hívás; a koordinátaszöveg indexelése nem igazolt. | megerősített: a parse-út; nyitott: downstream hatás |
| `faces` (`0x00c81884`) | Külön rekordág indul `0x0045944a`-nél. | Ebben az ágban nincs közvetlen `0x004d9aa0` hívás; a rekord későbbi hatása nem igazolt. | megerősített: a külön ág; nyitott: downstream hatás |
| `filters` (`0x00c80b04`) | Külön szűrőfeldolgozó ág indul `0x00457704`-től. | Ebben az ágban nincs közvetlen `0x004d9aa0` hívás; az effektadatok későbbi hatása nem igazolt. | megerősített: a külön ág; nyitott: downstream hatás |
| `albumlist` (`0x00c8188c`) | Ha a `param_6` engedi, az értéket a `0x005c2100` kapja a `0x00459984` címen. | Nincs közvetlen `0x004d9aa0` hívás. | megerősített: a közvetlen hívási út |

A `0x00456610` négy közvetlen `0x004d9aa0` hívása: `0x00458b1d`
(`rating` → `]star`), `0x00458ce9` (`star` igen → `]star`), `0x00458ee5`
(`hidden` igen → `]hidden`) és `0x0045907a` (`screensaver` → `]screensaver`).
Ez a közvetlen híváslista a disassemblyvel, az archivált dekompilációval és az
index hívás-xrefjeivel egyezik.

A másik két jelölt sem dönti el a fájlmezők forrását. A `0x00439a80` a
`0x0043b4f4` körüli rekordgyűjtés után `0x0044bdf0`-t hív, majd a
`0x0043b51d` címen a `0x004d9aa0`-t; a kulcs dinamikus (`param_1 + 0x1a`),
jelentése **NINCS MEG**. A `0x00437550` teljes függvénytestében a vesszőtagolás
után `0x004d9570`-t hív (`0x004378f9`, `0x0043791a`), közvetlen
`0x004d9aa0` hívása nincs. Ebből nem következik, hogy fájlnév, kiterjesztés,
EXIF, dátum vagy helyszavak egyik ágban sincsenek: e források hozzárendelése
**NINCS MEG**.

**Cáfoló kör:** ellenőriztem azt a lehetőséget, hogy a `caption`/`keywords`
mezőt maga a `0x00456610` bontja általános szavakra. A teljes érintett
utasításlánc ezt cáfolja: a caption egyben callbacket kap, a keywords csak
vesszőnként tagolódik. Ez nem cáfolja, hogy a feloldatlan callback később
szavakra bont.

**M3 futásidejű kiegészítése (#7195):** az eredeti `.picasa.ini`-felirat
kereshető (`j706/13`), és az ini-kulcsszó szavanként is kereshető
(`AI image` → `image`, `j706/16`, `j704/40`). Ezzel a két viselkedéssel
kapcsolatos nyitott mérési pont eldőlt. A komment nem igazol külön IPTC-
feliratot/kulcsszót, többtagú ini-feliratot, EXIF make/modelt, dátumot vagy
geotaget; ezek adatforrás-hozzárendelése továbbra is nyitott.

**Bizonyítottság:** a közvetlen mezőágak és híváshelyek megerősítettek a
disassembly, a Ghidra-kimenet és az xrefek egyezése alapján. A végső
caption-/keyword-szóhatár, a callbackek szemantikája, valamint a fájlnév-,
EXIF-, dátum- és helyszavak forrása nyitott; ezekhez M3 szükséges.

#### A futtatott M1-M6 mérés eljárása (#7195)

- A hívó a Colab-végrehajtón futtatta a #7195 részfeladatait. Az alábbiak a reprodukciós tervet őrzik; a mért és nyitva maradt eredmények a szakasz végén, a „Mért eredmény (#7195) és jegytörzsek” alatt vannak. Minden lépéshez képernyőkép és a megnevezett állapotok szöveges rögzítése tartozik; az eredeti Picasa 3.9.141.259 magyar felülettel.

- **M1: a bal hasáb és a nézethelyzet a keresés után (E2, E9 mellékkérdés).**
  Előkészítés: három mappa (`AA` 6 kép, `BB` 6 kép, `CC` 3 kép); az `AA` és a `CC`
  képeinek feliratában szerepel az egyedi `zqsearch` szó, a `BB`-ben nem; a kor-csúszka
  alaphelyzetben.
  1. Válaszd a `BB` mappát, jelöld ki a 4. képet, görgess úgy, hogy a 4. kép a rács
     alján látsszon. Képernyőkép (K0).
  2. Gépeld a keresőmezőbe: `zqsearch`; várd meg, míg a javaslatlista bezárul és az
     eredmény megjelenik. Képernyőkép (K1); rögzítsd: szűkül-e a bal hasáb, melyik
     sor a kijelölt, mit mutat a rács és a zöld sáv.
  3. Kilépés, mindig újrakezdve az 1-2. lépést: a) X gomb; b) „Back to View All”;
     c) kétszer `Ctrl+F`; d) előbb jelölj ki egy képet az eredményből (az `AA`
     2. képe), majd „Back to View All”; e) az 1. lépés előtt állítsd a kor-csúszkát
     egy közbülső értékre, majd „Back to View All”; f) a keresés közben válts
     másik mappára (`CC`), majd „Back to View All”. Mindegyik után képernyőkép és
     rögzítés: kijelölt mappa, kijelölt kép, görgetési helyzet (melyik kép látszik a
     rács tetején), fókuszban lévő elem, a keresőmező szövege, a kor-csúszka állása.
- **M2: `Esc` és `Delete` a keresőmezőben (nem blokkoló).**
  1. Gépeld: `abc`; `Home`; `Delete`; rögzítsd a mező szövegét és a találati
     állapotot.
  2. Gépelj egy olyan előtagot, amelyre van javaslat (a legördülő nyitva); `Esc`;
     rögzítsd: a legördülő, a szöveg, a fókusz, a keresés állapota.
  3. Aktív keresés, a legördülő zárva, a fókusz a mezőben: `Esc`; rögzítsd ugyanezeket.
- **M3: mezőforrások, előtag, kizárás, ÉS (E8, E7, a `tag:` előtag).**
  Előkészítés: hat JPEG, egyedi értékekkel: a) fájlnév `zqfn1.jpg`; b) felirat
  `zqcap1` (egyik képen a `.picasa.ini`-ben, másikon IPTC-ben); c) kulcsszó `zqkw1`
  (ugyanígy két forrásból); d) mappanév `zqfolder1`; e) EXIF gyártó `ZQMAKE`, modell
  `ZQMODEL`; f) dátum `2011:03:04`; egy kép felirata `zqcap1`, kulcsszava `zqkw1`
  egyszerre; egy kép ékezetes felirattal `őzqá`. Keresések, mindegyik után a
  találatlista rögzítve: `zqfn1`; `zqcap1`; `zqkw1`; `zqfolder1`; `zqmake`;
  `zqmodel`; `2011:03:04`; `jpg`; `zqcap` (előtag); `qcap1` (szó belseje);
  `zqcap1 zqkw1` (ÉS); `zqkw1 zqcap1` (sorrend); `zqcap1 -zqkw1` (kizárás);
  `-zqkw1`; `"zqcap1"`; `címke:zqkw1`; `címke:zqcap1`; `őzqá`; `ozqa` (ékezet
  nélkül); `zqcap1.zqkw1`.
- **M4: javaslatlista (E11).**
  Előkészítés: kulcsszavak `ai`, `ai1`...`ai15` különböző darabszámmal; egy `ai`
  előtagú mappa; egy `ai` előtagú album; `ai` előtagú fájlnevű képek; egy szó
  belsejében `ai`-t tartalmazó kulcsszó (`mainstream`). Gépeld: `ai`, `a`, `ai1`,
  `AI`, `ál`, `main`; mindegyiknél képernyőkép a legördülőről; rögzítsd a sorok
  számát, az ikont, a szöveget, a darabszámot és a sorrendet. 15-nél több egyező
  kulcsszónál számold meg a sorokat (van-e felső korlát). Kattints egy szósorra, egy
  mappasorra és egy albumsorra: rögzítsd, mi történik (keresés vagy ugrás).
- **M5: ékezetes betű a rácson és a mappalistán (E3, megerősítés).** Gépeld a rács
  fókuszával, majd a mappalista fókuszával: `a`, `á`, `ő`, `ű`; rögzítsd a keresőmező
  tartalmát és a fókuszt.
- **M6: szöveg és szűrőgombok (E1).** Katalógus csillagozott, filmes, online
  (feltöltött), másodpéldányos, arcos és geocímkés képekkel, mindegyik feliratában
  `zqsearch`. Minden gombra (és a kor-csúszkára) külön: a) a szűrő egyedül; b) a
  szöveg egyedül; c) a szöveg a szűrővel együtt (a találatok száma és listája);
  d) két gomb egyszerre; e) a gomb kikapcsolása a szöveg megtartásával; f) a szöveg
  törlése a gomb megtartásával.

### Zárási döntés

**A #7072 vizsgálati jegyhez szükséges K1 és K2 bizonyíték rendelkezésre áll.**
A K1 eredeti futásidejű mérése a #7195 Colab-feladataiból származik; a K2
statikus eredménye a fenti „K2 statikus eredmény (#7196)” szakasz. Az új
fejlesztői jegytörzsek és az egyező viselkedések a #7195-ös összefoglalóban
szerepelnek. Nyitott marad az E1 második üteme (M6 hiányzik), az E8 nem mért
mezőforrásai, valamint a lejjebb felsorolt M1/M4 részletkérdések; ezek külön
követő munkák, nem a két mérési kör függő eredményei.

**A #7195-ből négy fejlesztői jegytörzs készíthető elő:** (1) Esc a keresőmezőben;
(2) keresésből kilépés és bal hasáb; (3) javaslatlista; (4) `tag:` mezőszűkítés.
Az E6/E7 (`ÉS`, `-` kizárás, előtag-illesztés), a `.` szóhatár, a fájlnév,
felirat, kulcsszó és mappanév kereshetősége egyezik, ezért ezekhez nincs új jegy.
Az E1 második üteméhez és az instabil, pusztán kizáró kereséshez elvárást nem
vezetünk be.

**E1: a keresőszöveg és a csillag, az arc és a geocímke szűrő együtt**

Eredeti: a `0x0043f9a0` a keresőszöveg szavait és a gombok belső szójeleit (`]star`, `]face`, `]geo`) egyetlen pozitív szólistában kapja (`0x00662352`-`0x00662365`, `0x006615db`, `0x006617f3`, `0x00661a0c`), a találat a lista minden szavának metszete (`0x0043fda4`, `0x00413290`): a szöveg és a gombok ÉS kapcsolatban vannak. A rejtett kép kizárása külön kizárt listában van (`0x00660ca2`).

Nálunk: a szöveges keresés és a szűrők egymást kizáró nézetmódok. A `_view_mode` egyetlen érték (`controller_filter_mixin.py:37,60,85,128,146,163`), a `search()` kikapcsolja az aktív szűrőt (`search_controller.py:40-41`), a szűrőgombok (`ToolbarFilterControls.qml:117-118,176-177,222-223,276-277,353-354,428`) pedig a keresést.

Teendő: a keresőkifejezés és a csillag, az arc és a geocímke szűrőkapcsoló közös állapotba kerüljön, a találathalmaz a feltételek metszete. A film, az online és a másodpéldány gomb, valamint a kor-csúszka a mai viselkedésben marad, amíg az M6 nem döntött (külön jegy, E1b). A szűrőgomb kikapcsolása a keresőszöveget, a szöveg törlése a gombot megtartja.

Kész, ha:

- a szöveg és a csillag, az arc vagy a geocímke szűrő egyszerre aktív, és a találat csak az a kép, amely a szövegnek és a szűrőnek is megfelel;
- a három gomb közül egy kikapcsolása nem törli a keresőszöveget, a szöveg törlése nem kapcsolja ki a gombot;
- az eredményt a bal hasáb, a darabszám és a rács ugyanabból a közös halmazból mutatja;
- a film, az online, a másodpéldány gomb és a kor-csúszka viselkedése változatlan.

**E3: gépelés a mappalistán is indítsa a keresést**

Eredeti: a mappalista (`0x005c40e0`) és a rács (`0x005c42d0`) a `0x005c3fe0`-ba vezeti a módosító nélküli karaktert. A `0x20 < kód < 0x80` tartományban (`0x21`-`0x7f`) a keresőmezőre fókuszál, beírja a karaktert, és elnyeli az eseményt; a `0x80`-`0xff` tartományt (az ékezetes betűket) elveti, mert az ablak ANSI.

Nálunk: a rács már így működik (`SearchGridKeys.qml:72-90`, `:77`: `code < 0x21 || code > 0x7f`); a mappalista csak fel és le nyilat kezel (`FolderPaneContent.qml:306-307`).

Teendő: a mappalista karakterbevitele ugyanazt az útvonalat használja, mint a rács, ugyanazzal a `0x21`-`0x7f` tartománnyal.

Kész, ha:

- a mappalistán módosító nélkül begépelt `0x21`-`0x7f` karakter a keresőmezőbe kerül, a mező kap fókuszt, és elindul a keresés;
- a karakter egyszer kerül a mezőbe (nem duplán);
- az ékezetes betű (`á`, `ő`, `ű`) a rácson és a mappalistán sem ugrik a mezőbe;
- a `Ctrl`-os és az `Alt`-os billentyűk nem indítanak keresést.

**E6/E7: a korábbi fejlesztői tervezetet visszavonja a #7193 és a #7195.**
A szavankénti ÉS, a vegyes keresésben használt `-` kizárás, az előtag-egyezés
és a szóhatárbontás jelenlegi állapota egyezik az eredeti méréssel; lásd a
„Mért eredmény (#7195) és jegytörzsek” egyezési sorát. Új jegytörzs nem kell.

**E10: a rejtett találatok ne torzítsák a darabszámot**

Eredeti: a rejtett kép alapból nincs a találati halmazban (`]hidden` a kizárt listában, `0x00660ca2`, ha a `Preferences\ShowHidden` hamis); a bal hasáb, a darabszám és a zöld sáv ugyanabból a halmazból épül.

Nálunk: a bal hasáb és a darabszám a nyers találatokból készül (`search_controller.py:77-82`), a sáv szövege is (`controller_sync_mixin.py:50-63`); a rejtett képeket csak a rács előtt szűri a `controller_photo_list_mixin.py:119-120`.

Teendő: a rejtett szűrést a keresés minden ágán (`search`, `selectFolderKeepSearch`, `_refresh_view`: `controller_sync_mixin.py:65-`) a hasáb, a darabszám és a sáv előtt kell elvégezni, egyetlen közös segédben, hogy a rács szűrése ne duplikálódjon.

Kész, ha:

- `ShowHidden` ki mellett a rejtett találat nem növeli a bal hasáb, a mezőjelzés, a sáv és a rács darabszámát;
- `ShowHidden` be mellett a találat mind a négyben megjelenik;
- a kapcsoló átváltása után a számok frissülnek;
- a hasáb, a sáv és a rács ugyanazt a látható halmazt mutatja.

**E2: a keresés előtti nézethelyzet visszaállítása.**
A K1 előtti tervezetet a #7195 mérése felülírta: az X és a „Back to View All”
is visszaállítja a keresés előtti mappát és képet; a második `Ctrl+F` mért
viselkedése eltér. A friss jegytörzs a „Mért eredmény (#7195) és jegytörzsek”
2. pontjában van.

**E11: a javaslatlista.**
A K1 előtti tervezetet a #7195 M4 mérése pontosította; a friss, korlátozott
jegytörzs a „Mért eredmény (#7195) és jegytörzsek” 3. pontjában van. A nem
mért szó-/albumsor-kattintás és a nyitott sorrendi részlet nem kerül elvárásba.

**E8: a kereshető képmezők bővítése (K2 után vehető fel)**

Eredeti: a szóindex fájlnév-, kiterjesztés-, EXIF-, dátum-, hely-, szín-, felirat- és kulcsszó-szerű szavakat is tartalmaz (2. szakasz); a mező-hozzárendelés nincs meg.

Nálunk: az FTS-oszlopok a fájlnevet, a feliratot és a kulcsszót fedik (`index/schema.py:122-125`), a mappanév és a szín külön ág (`index/queries.py:496-566`).

Teendő: a K2 (a `0x00456610` Ghidra-kör és az M3) után csak a bizonyított hiányzó mezőket felvenni, mezőnként igazolva.

Kész, ha:

- minden felvett mező egyedi próbaértékkel, az eredetin mérve igazolt;
- találgatott mező nincs.

#### Mért eredmény (#7195) és jegytörzsek

Az eredeti Picasa 3.9.141.259 futásidejű mérését a Colab-végrehajtó végezte
(`picasa-colab-jobs` #702-#709). A feliratot és a kulcsszót `.picasa.ini`-ből
adták meg, majd újraindították a Picasát. Az alábbi mért megfigyelések és a
PicasaPy forráskódjának összevetése a két független bizonyítékút; a névvel
azonosított M1-M4 mérési lépések és naplósorok a táblában szerepelnek.

##### Mért állítások és jelenlegi kódbeli viselkedés

| Funkció | Eredeti Picasa (mérés; bináris cím) | PicasaPy a főágon | Eredmény |
|---|---|---|---|
| `Esc`, nyitott javaslatlista | Csak a lista zárul be; a mező és a keresés megmarad (M2, `j707/32`, `j708/19`; a szerkesztő útja a #7072-ben: `0x0077d380`, `0x0060f1b0`, `0x00610040`). | A `MainToolbar.qml:540-550` és `MainWindowToolbar.qml:72-81` csak a látható listát zárja. | **Egyezik.** |
| `Esc`, zárt lista, aktív keresés | Törli a keresőmezőt és kilép a keresésből; a fókusz a mezőben marad (M2, `j703/25`, `j703/27`; a fenti szerkesztő/bázisosztály címek). | A `MainToolbar.qml:540-550` nem ad zárt listás műveletet; a `SearchGridKeys.qml:54-69` Esc-kezelője a rács billentyűútja. | **Eltér:** nincs a keresőmezőre kötött megfelelő kilépő ág. |
| `Delete` a mezőben | Szokásos szerkesztés, a kurzor utáni karakter törlése (M2, `j703/11`). | A keresőmező nem írja felül a `Delete`-et; a szövegszerkesztés natív útján marad (`MainToolbar.qml:530-551`). | **Egyezik.** |
| Kilépés és előzményállapot | X és „Back to View All” után a keresés előtti mappa és kép kijelölt, a kép látható; a pontos előző görgetés nem áll vissza (M1, `j707/16`, `j707/24`). Másik mappára váltás után is az eredeti mappa és kép tér vissza (M1, `j709/38`). A mentés és visszaállítás útjai: `0x0065ba5c`-`0x0065bb0c`, `0x005d47e0`, `0x005fa430`. | Gépeléskor törlődik a kijelölés (`MainWindowToolbar.qml:82-87`); a `clearFilter()` az aktuális mappát tölti újra (`controller_filter_mixin.py:199-212`); keresés közbeni mappaválasztás felülírja az aktuális mappát (`search_controller.py:138-163`); a „Back to View All” is törli a kijelölést (`MainLibraryCanvas.qml:59-73`). | **Eltér:** nincs keresés előtti mappa/kép mentés és visszaállítás. A pontos görgetési pozíciót az eredeti sem állítja vissza. |
| Keresés alatti bal hasáb | A találatos mappákra szűkül; az `Albums` és `People` kategória csak találatnál jelenik meg, az `Other Stuff` nem évszám-csoportként (M1, `j707/14`, `j708/16`). A keresés fő útja `0x0065b840`; a `]search` felirat címe `0x004ad430`. A kategóriafeltétel futásidejű, **mérve, cím nélkül**. | A találatos mappákat `search_controller.py:124-129` és `folder_list_model.py:209-228` mutatja; az Album és People elemek külön UI-adatúton jelennek meg (`FolderPaneContent.qml:34-74`, `AlbumsSection.qml:72-115`). | **Részben egyezik:** a mappákra szűkítés és az évszám-elválasztó nélküli találati lista egyezik; a mért kategóriafeltételt külön kezelni kell. |
| A keresés előtti mappa nincs a találati listában | Nincs kijelölt mappasor, ha az előző mappa nem találatos (M1, `j707/14`). | A keresési modell csak a találatos mappák sorait tölti (`folder_list_model.py:209-228`). | **Egyezik** a mért M1-helyzetben. |
| `Ctrl+F` kétszer, nyitott listával | Nem történik művelet; a fókusz a mezőben, a lista nyitva marad (M1, `j709/18`). | Aktív keresésnél a második `Ctrl+F` kilép (`SearchGridKeys.qml:22-34`; gyorsbillentyű-út: `MainKeyboardShortcuts.qml:39-53`). | **Eltér.** |
| Javaslatlista: típusok, sorrend, felső korlát | 10 sor; a mappa elöl, utána szó-javaslatok; a sorokon azonos ikon (M4, `j708/16`). A szósorok belső sorrendje nem dőlt el. | Alapértelmezett korlát 8; az albumok előzik meg a mappákat; szójavaslat nincs (`index/queries.py:660-711`, `search_controller.py:165-176`). | **Eltér.** A 10 sor, mappa-előrehelyezés és mért szósorok indokoltak; további sorrendi szabály nem. |
| Javaslatlista: mappasor kattintása | A név és egy záró szóköz kerül a keresőmezőbe, és a mappa kijelölődik (M4, `j708/28`); az eseménykezelő címe az indexben nem azonosítható, **mérve, cím nélkül**. | A `MainWindowCommands.qml:756-760` törli a keresést és közvetlenül mappára lép. | **Eltér.** |
| Mezők és szavak | Az ini-felirat kereshető (`j706/13`); az ini-kulcsszó szavanként is (`AI image` → `image`, `j706/16`, `j704/40`); a fájlnév a kiterjesztéssel (`jpg`, 23 kép; `j702/34`, `j704/34`), a mappanév (`j708/40`), az előtag (`j706/19`, `j708/23`), a `.` szóhatár (`j706/37`), az ÉS és a sorrendfüggetlenség (`j706/25`, `/28`), valamint a vegyes `-` kizárás (`j706/31`) igazolt. A `tag:` leválik és kulcsszóra szűkít (`tag:zqcap1` = 0, `tag:zqkw1` = 2; `j708/31`, `j706/40`). | Az FTS mind a fájlnevet, ini- és fájlfeliratot/kulcsszót tartalmazza (`index/schema.py:121-125`); a normalizálás előtagot választ le és pontnál bont (`index/queries.py:21-70`); kereséskor a pozitív szavak külön prefix-ÉS lekérdezések, a `-` szavak kizártak (`index/queries.py:559-627`); a mappanevet külön ág keresi (`index/queries.py:575-605`). A `tag:` is csak leválik, mezőszűkítés nélkül (`index/queries.py:21-37`, `515-556`). | **Egyezik** az általános mező-/szóillesztés; **eltér** a mért `tag:` kulcsszó-szűkítés. |

PicasaPy-oldali fájl:sor hivatkozásokat a fenti sorok adják meg. A javaslatlista
mappasor-kattintásához és a bal hasáb külön `Albums`/`People` feltételéhez a
célzott `string_xrefs`-keresés nem adott külön kezelőcímet; ezeket a táblában
`mérve, cím nélkül` jelöltem, nem állítom, hogy a binárisban nincs ilyen kód.

##### Jegytörzsek

**1. Esc a keresőmezőben**

Eredeti: a keresőmező szerkesztőútja (`0x0077d380`, `0x0060f1b0`, `0x00610040`; #7072) M2-ben mérve: nyitott listánál az Esc csak a listát zárja (`j707/32`, `j708/19`); zárt listás, aktív keresésnél törli a szöveget, kilép a keresésből, a fókuszt a mezőben hagyja (`j703/25`, `j703/27`). A `Delete` szokásos szerkesztés (`j703/11`).

Nálunk: nyitott listánál az út egyezik (`MainToolbar.qml:540-550`, `MainWindowToolbar.qml:72-81`); zárt listás Esc-kezelés nincs a keresőmezőn (`MainToolbar.qml:540-550`), a rács kezelője külön út (`SearchGridKeys.qml:54-69`).

Teendő: a keresőmező Esc-kezelése kövesse a mért két állapotot: nyitott listánál zárja a listát és őrizze meg a keresést; zárt listás aktív keresésnél ürítse a mezőt, lépjen ki, és tartsa a fókuszt a mezőn.

Kész, ha:

- nyitott javaslatlistán az Esc csak bezárja a listát, a szöveg és a találati állapot változatlan;
- zárt lista és aktív keresés mellett az Esc törli a szöveget, kilép a keresésből, a fókusz a mezőben marad;
- a `Delete` továbbra is a kurzor utáni karaktert törli.

**2. Kilépés a keresésből és a bal hasáb találati állapota**

Eredeti: az első nem üres kereséskor a mappa-/képkijelölés mentési útja `0x0065ba5c`-`0x0065bb0c`; a kilépéshez `0x005d47e0` és `0x005fa430` tartozik (#7072). M1 szerint az X és a „Back to View All” a keresés előtti mappát és képet állítja vissza, a kép látható (`j707/16`, `j707/24`); mappaváltás után is a keresés előtti mappa és kép áll vissza (`j709/38`). A pontos görgetési pozíció nem áll vissza. A találatos mappákra szűkítés a `0x0065b840` keresési út mellett M1-ben mérve; az `Albums`/`People` találatfeltétel külön kezelőcíme nincs meg a statikus indexben.

Nálunk: a gépelés törli a kijelölést (`MainWindowToolbar.qml:82-87`); a kilépő `clearFilter()` az aktuális mappát tölti újra (`controller_filter_mixin.py:199-212`); a keresés közbeni mappaváltás felülírja az aktuális mappát (`search_controller.py:138-163`); a „Back to View All” törli a kijelölést (`MainLibraryCanvas.qml:59-73`). A találatos mappák listája már szűkül (`search_controller.py:124-129`, `folder_list_model.py:209-228`), de az Album/People kategória külön UI-útját a keresési találatok nem vezérlik (`FolderPaneContent.qml:34-74`, `AlbumsSection.qml:72-115`). A második `Ctrl+F` keresésből kilép (`SearchGridKeys.qml:22-34`), míg az eredetin M1-ben nyitott lista mellett nem történt semmi (`j709/18`).

Teendő: az első keresés kezdetekor őrizzük meg a kijelölt mappát és képet; az X és a „Back to View All” állítsa vissza ezeket akkor is, ha keresés közben másik mappára váltottunk. A bal hasáb a találatos mappákat mutassa, és az `Albums`/`People` találati sorokat csak akkor jelenítse meg, ha azokhoz van találat. A második `Ctrl+F`-et a mért, nyitott listás állapotban ne alakítsuk kereséskilépéssé. A görgetés pontos visszaállítása ne legyen követelmény.

Kész, ha:

- X és „Back to View All” után a keresés előtti mappa és kép kijelölt, a kép látható;
- a mappaváltás nem cseréli le a keresés előtti visszaállítási állapotot;
- a bal hasábban csak találatos mappák szerepelnek, az `Albums` és `People` találati sorai csak egyezésnél látszanak, és a találati mappák között nincs évszám-csoportosítás;
- a keresőmezőben nyitott javaslatlista mellett a második `Ctrl+F` nem léptet ki a keresésből;
- a pontos előző görgetési helyzetet a megvalósítás nem ígéri.

**3. Javaslatlista korlátja és mappasorának kiválasztása**

Eredeti: M4-ben legfeljebb 10 sort mértek, a mappasor a szó-javaslatok előtt állt (`j708/16`); mappasorra kattintáskor a mappanév és záró szóköz került a mezőbe, a mappa kijelölődött (`j708/28`). A rajzoló/ikon címek a #7072-ből: `0x0077e2e0`, `0x0077eee0`. A kattintási kezelőcímet az index-keresés nem azonosította: `mérve, cím nélkül`.

Nálunk: 8 a lekérdezés alapértelmezett korlátja, a sorrend album aztán mappa, és szó-javaslat nincs (`index/queries.py:660-711`, `search_controller.py:165-176`). A mappasorra kattintás törli a keresést és mappára lép (`MainWindowCommands.qml:756-760`).

Teendő: a listát legfeljebb 10 sorra korlátozzuk, az eredetivel mért mappa-előrehelyezéssel és szó-javaslatokkal; mappasor kiválasztásakor a mappanév kerüljön a mezőbe záró szóközzel, maradjon aktív a keresés, és a bal hasáb válassza ki a mappát.

Kész, ha:

- az M4-ben igazolt tíz soros felső korlát érvényesül és a mappajavaslat a szó-javaslatok előtt áll;
- a javaslatlista legalább a mért szó- és mappasorokat mutatja, 10 sornál nem többet;
- a mért mappa- és szójavaslat-sorok az eredetivel egyező ikont használják;
- mappasor választása a mezőbe írja a mappanevet és a záró szóközt, aktív keresésben tart, és kijelöli a mappát;
- nem rögzítünk nem mért holtverseny-szabály, kis-/nagybetűsorrend vagy darabszám-szabályt.

**4. A `tag:` előtag kulcsszóra szűkít**

Eredeti: a `0x006622aa` leválasztja a `tag:` előtagot (#7072); M3 igazolta, hogy utána a keresés kulcsszóra szűkül: `tag:zqcap1` nulla, `tag:zqkw1` két találat (`j708/31`, `j706/40`). A `címke:` mérését a beviteli hiba miatt nem vesszük elvárásnak (`j708/34`).

Nálunk: az `index/queries.py:21-37` a `tag:` és `címke:` előtagot egyaránt eltávolítja, majd a `search_photos()` az általános FTS-mezőkön keres (`index/queries.py:515-556`, `schema.py:121-125`).

Teendő: a mért `tag:` előtag csak a kulcsszómezőben keressen; a sima lekérdezés globális mezőkészlete maradjon változatlan. A `címke:` lokalizált előtagot ne tekintsük igazoltnak ebből a mérésből.

Kész, ha:

- `tag:zqkw1` csak az `zqkw1` kulcsszóval jelölt képeket adja;
- `tag:zqcap1` nem talál feliratban vagy fájlnévben szereplő `zqcap1` értékre;
- előtag nélkül a név, felirat, kulcsszó és mappanév keresése továbbra is működik;
- a `címke:` viselkedéshez nem kerül be nem mért elvárás.

##### Kiegészítő mérés (#7220)

A mérés a `picasa-colab-jobs` #740, #741 és #742 feladata (eredeti Picasa 3.9.141.259, `alapallapot` indulás; a #737-#739 elrontott, friss indulású futás volt, nem használható).

- **Felvételi dátum kereshető (mérve, #741).** Az `idorend`-mintán a `2019:03` 7, a `2014:11` 3, a `2009:05` 1, a `2021` 2 találatot ad. A szóindexben (`wordhash.dat`) szó a teljes dátum (`2019:03:08`), az év (`2019`) és az idő (`09:15:00`), gyártó-/modellszó és `exif` jelzőszó nincs. A Properties négy dátumot mutat (Camera Date, Digitized Date, Modified Date, File Date). PicasaPy: nincs dátumszó az FTS-ben (`index/schema.py:122-125`). **Eltér** (#7241).
- **Ékezetes bevitel (mérve):** a végrehajtó `gepel` lépése karaktereket ejt (`áéíóöőúüű` -> `éíü`, `tükörfúrógép` -> `tkörfúrógép`), az `ő`/`ű` `o`/`u` lesz (CP1252 ANSI mező). Az idézőjel nem gépelhető. A `címke:` és az idézőjeles frázis ezért nem mérhető (a végrehajtó szövegbevitele javul).
- **Ékezet nélküli keresés (mérve, kontroll nélkül):** az `arvizturo` 0 találatot ad a `árvíztűrő tükörfúrógép` feliratra; a pozitív kontroll hiányzik. Eltérés csak a kontroll után (a kontroll a #7220 folytatásában).
- **Javaslatlista (mérve, #708/16 és #741):** a szósorok `szó (N)` darabszámot mutatnak (`ai (37)`, `ai1 (3)`..., az `ai1..ai8` az ini-vel egyező), a szósorok közt dátumszavak is vannak (`2019:03:08 (28)`: 7 kép x 4 dátummező), és a mért listákon a darabszám szerint csökkenő sorrendben állnak a mappasor után. PicasaPy: darabszám rejtett (`SearchSuggestions.qml:140-141`), forrás csak teljes kulcsszó, sorrend előfordulási. **Eltér** (#7242). Ezzel a „`(37)` darabszám eredete" kérdés eldőlt.
- **Folytatás (második kör, `picasa-colab-jobs` #743-#746, `alapallapot` indulás).**
- **A `kombinalt` k01-k10 EXIF-je (mérve, #743).** Artist 8 képen, Copyright 6 képen; gyártó/modell, felvételi dátum, GPS és IPTC-hely nincs. Gépezeti akadály marad: nincs ilyen EXIF-mintakészlet.
- **EXIF Artist kereshető (mérve, #746).** `Delso` 1, `Konsek` 2, `Hons` 2, `Halicki` 1, `slusarczyk` (kisbetűvel a `SLUSARCZYK` értékre) 1, `Diego Delso` 1 találat; a javaslatlista a szót kisbetűvel adja (`delso (1)`, `konsek (2)`, `hons (4)`, `halicki (1)`). PicasaPy: az Artist nincs az FTS-ben (`index/schema.py:121-125`). **Eltér** (#7254). A Copyright szavai nem eldönthetők (`CC-BY-SA` 0 találat); az `exif` 0 találat, jelzőszó Make/Model nélkül nincs.
- **Szöveg + gombok (mérve, #744).** A csillag (1, önmagában 2), az arc (2, a `Unnamed (6)` szerint önmagában 6) és a geocímke (1, az ini szerint önmagában 2) a szöveggel metszetet ad, a szöveg a mezőben marad; a gomb kikapcsolása után a szöveges találat visszatér, a szöveg törlése gomb mellett a gomb nézetét adja. Egyezik a #7191-gyel. A film a szöveggel 1 találat, de a mintán egyetlen videó van, ezért a metszet nem különíthető el (nyitott).
- **Szöveg + kor-csúszka (mérve, #744).** A szöveg a mezőben marad, a találat a szöveges találat (a mintán minden kép mai, a szűkítő hatás nem látszott). A zöld sáv jobb szélén `Date Range:  Pictures up to 2 months old.` (csúszka kb. 0,53), jobb szélen `... 2 days old.`, bal szélen nincs felirat. PicasaPy: külön `age` nézet, a felirat a találati szöveg után, előtag nélkül (`MainLibraryCanvas.qml:80-90`). **Eltér** (#7255).
- **Javaslat szósor (mérve, #745).** Kisbetűs index-szó (`ZqKase` -> `zqkase (1)`), a nagy- és vegyes betűs gépelés ugyanazt adja; kattintásra a mező a szót és egy szóközt kapja, és a keresés lefut (`zqkase `: 1, `zqai `: 3 találat). Sorrend: csökkenő darabszám, egyenlőnél első előfordulás. PicasaPy: a szósorra kattintás nem csinál semmit (`MainWindowCommands.qml:755-769`). **Eltér** (#7253).
- **Üres album a javaslatlistán (mérve, #745).** A `zqalbum (0)` album a `zq` és a `zqalb` begépelésére nem jelent meg, és az album neve nem találat. Nem üres albumra és az albumsor kattintására nincs mérés.
- **Folytatás (harmadik kör, `picasa-colab-jobs` #747-#750, `alapallapot` indulás).**
- **Album a javaslatlistán és az albumsor kattintása (mérve, #747, #749).** A nem üres album (`zqalbum`, 1 kép) a `zqalb` begépelésére egy sor album ikonnal: `zqalbum (1)`; az üres album (`zqalbum (0)`) a listán nincs. Az albumnév keresőszó: `zqalb` az album képét találja (1 kép, `Displaying 1 picture in 2 albums`). Az albumsor kattintása: a mező `zqalbum ` (név + egy szóköz), a keresés fut, az album kijelölődik a bal hasábon, a zöld sáv marad. PicasaPy: az üres albumot is listázza (`index/albums.py:169-170`), az albumnevet nem keresi (`index/queries.py:566-640`), az albumsor kattintása törli a keresést (`MainWindowCommands.qml:762-766`). **Eltér** (#7263). Technikai: a `File > New Album...` kijelölt képpel is üres albumot hoz létre, a kép húzással kerül az album sorára.
- **Kor-csúszka + szöveg (mérve, #748).** A csúszka a szöveges találatot szűkíti (metszet): `2019` (7 kép) a 6 éves állásnál 0, `2021` (2 kép) a 6 évesnél 2, a 4 hónaposnál 0; a 0 állásnál a szöveges találat visszatér. A szöveg törlése után a csúszka marad, és önmagában dátumszűrő a teljes könyvtáron (4 hónap: 24 kép, 6 év: 26 kép, 2 nap: 24 kép). PicasaPy: külön `age` nézet, a keresés nem kapja meg a kort (`controller_filter_mixin.py:111-140`). **Eltér** (#7255).
- **Film (mérve, #749).** A film egyedül 2 videót ad (két videóval); a film + szöveg metszet (`zqvid`: 1; #744: 5 -> 1). PicasaPy: a film külön nézetmód, a szöveg kilép belőle (`search_controller.py:105-115`). **Eltér** (#7264).
- **EXIF Copyright (mérve, #750).** `cc` 3 és `sa` 3 kép (a `CC-BY-SA 4.0` értékű k03, k08, k10); a szótárban `cc`, `sa` szó. Az EXIF értékszavai (`Centered`, `Inches`) nem szavak (0 kép). PicasaPy: az FTS-ben nincs (`index/schema.py:121-125`). **Eltér** (#7254). A `halicki (1)` és `hons (4)` darabszám nyitott (a javaslatlista a mérésben nem jelent meg).
- **Szótár (a `wordhash.dat`-ból, #750).** A kép szélessége és magassága is szó (`1280`, `853`, `720`, `807`, `597`, `851`); keresésre nem mért.
- **Nem mért:** az album sor sorrendje a mappa- és szósorokhoz képest, az albumnév részszó (nem előtag) illesztése, a szélesség/magasság szó keresése, a `by` és `4.0` Copyright-tokenek, a darabszám eredete (`hons (4)`), az ékezetes bevitel, az idézőjel és a `címke:` (F2, nem volt feladat).

##### Egyező viselkedések és elvárás nélkül hagyott mérés

- **Egyezik (#7193 / M3):** külön szavak közötti ÉS, sorrendfüggetlenség, vegyes `-` kizárás, előtag-egyezés, `.` szóhatár, fájlnév a kiterjesztéssel, ini-felirat/-kulcsszó, mappanév és a szó belseji részlet elutasítása. Ezekhez nincs jegytörzs.
- **Nincs elvárás:** a pusztán kizáró keresés darabszáma instabil volt (`j702/28`, `j704/31`, `j706/34`); erre nem írunk specifikációt.
- **Nyitott:** EXIF make/model, dátum, IPTC-felirat/-kulcsszó, idézőjeles frázis, `címke:` és ékezetmentes keresés (`j708/34`, `j708/37` vagy hiányzó minta); M1 d) kijelölés utáni kilépés, kor-csúszka, M1 e) csúszkás változat, Esc utáni görgetés többmappás állapotban; M4 szósor-/albumsor-kattintás, kis-/nagybetű és a `(37)` darabszám eredete; az M6 szűrőgombok és kor-csúszka kombinációi.

##### A két független út és a cáfoló kísérlet

- **A - eredeti futásidejű mérés:** M1-M4, a fenti `j702`-`j709` naplósorokkal. Ez adja az eredeti Picasa tényleges fókusz-, kijelölés-, találat- és javaslatállapotát.
- **B - PicasaPy-forrás:** külön végigkövetve a keresőmező QML-billentyűútját, a keresővezérlő és indexlekérdezés útját, a javaslatlistát és a mappasor `onChosen` ágát (a fenti fájl:sor hivatkozások). Az ágakból következik a 8-as korlát, az album-előresorolás, a minden mezőre érvényes `tag:` és a mentett előzményállapot hiánya.
- **Egyezés:** a nyitott listás Esc, a `Delete`, a találatos mappákra szűkítés, az M3 által mért általános mező-/szóillesztések mindkét útja egyezik; a zárt listás Esc, a kilépés/visszaállítás, a javaslatlista és a `tag:` eltérései egymástól függetlenül látszanak a mérésben és a kódban.
- **Cáfoló kísérlet:** megvizsgáltam, hogy a keresőmező zárt listás Esc-je vagy a visszaállítás egy másik UI-ágon mégis megvalósul-e. A `MainToolbar.qml:540-550` zárt lista esetén nem kezeli az Esc-et; a rács saját `SearchGridKeys.qml:54-69` útja nem állít vissza előző mappát/képet. Az X/Back ágak a kijelölést törlik, a mappaválasztó pedig felülírja az aktuális mappát (`MainWindowToolbar.qml:89-102`, `MainLibraryCanvas.qml:59-73`, `search_controller.py:138-163`). A cáfoló ugyanazt a kódút-mércét teljesíti, mint az első olvasás: nem találtam alternatív mentési vagy mező-Esc-kezelőt; az eltérések fennmaradnak.

**Bizonyítottság:** a mért és a PicasaPy-oldali viselkedés-összevetés megerősített, mert a két külön út az egyező és eltérő állításokra ugyanazt adja. A kattintásra vonatkozó eredeti eseménykezelő címe nincs meg, ezért azt külön `mérve, cím nélkül` jelöltem; új Ghidra-kör nem szükséges a négy jegytörzs elkészítéséhez.

**Nyitott:** a fenti, „elvárás nélkül hagyott mérés” sorai; a megadott bizonyítékok alapján újabb bináris cím-kérés nem indokolt.

### #7234 zárókör a keresés-visszaállításról és a szóindex célcíméről (2026-11-18)

**#492 - a keresés állapotának visszaállítása.** A `0x00660c80` a
keresési/szűrőállapotot rekonstruáló rutin: átveszi a rejtett képek jelzőjét,
az aktuális mappakulcsot, a beviteli szöveget és a keresőgombok állapotát
(`2026-11-18-koteg-466-495.txt:4783-5907`). Ez nem igazolja a keresőmező
kijelölésének, fókuszának vagy görgetésének visszaállítását; ezekre a
függvényben közvetlen, szemantikailag feloldott mezőírás nincs. A `+0x32b0`
objektum jelentése nem igazolt, ezért nem nevezem kor-csúszkának.

A keresés előtti kép- és mappasor mentése külön út: az első nem üres
kereséskor a `0x0065ba5c-0x0065bb0c` a főablak `+0xe98`, `+0xe9c`, `+0xe94`
mezőibe menti a képindexet, jelzőt és balhasáb-indexet; a kilépés
`0x005d47e0`/`0x005fa430` útja ezekből állít vissza. A #7195 M1 mérés szerint
X és „Back to View All” után a korábbi mappa és kép visszaáll, de a pontos
görgetési hely nem. PicasaPy oldalon a keresés közbeni kijelölés törlődik
(`MainWindowToolbar.qml:82-87`), a mappaváltás felülírja az aktuális mappát
(`search_controller.py:150-163`), és a visszalépő gomb törli a kijelölést
(`MainLibraryCanvas.qml:59-73`): ez az E2 fejlesztői jegytörzsben már szereplő
eltérés.

A `0x0057f1d0` 0x70 bájtos navigációs rekordot foglal, a `+0x8` objektumot a
`0x0057ec70`-tel másolja, majd a rekordot a kapott listához fűzi. Közvetlen
hívói a `0x00604260` és `0x006042b0` Vissza/Előre kezelők; a `thumbui/navback`
xrefje a navigációs útban jelenik meg (`2026-11-15-7012-7022-colab-decomp.txt`,
`2026-11-15-7012-7028-colab-decomp.txt`). Ez nem bizonyítja, hogy a keresés indításakor
előzményrekord készül. A `0x0057ec70` részletes mezőhatása és a `+0x32b0`
objektum UI-jelentése nyitott.

- Ghidra-kör kell: 0x0057ec70 - a `+0x32b0` objektum tényleges UI-típusa, mezői, valamint a keresésindításkor történő kijelölés/fókusz/görgetés-visszaállítás esetleges kapcsolata [nem blokkoló]

**#493 - a `0x004403c0` nem a fotómezők indexelője.** A `0x00682c00`
dekompilációja ezt a függvényt a `CUploadManager::DeleteSuppressed` útban
hívja, a `]web_` és `]suppress` feltöltési szójelekkel
(`2026-11-18-koteg-466-495.txt:5908-6467`). A bináris-index a `0x004403c0`
közvetlen hívójaként ezt az utat mutatja. A valódi általános szó-beszúró a
`0x004d9aa0`; annak meglévő dekompilációja listát frissít, a forrásmezőket nem
nevezi meg (`2026-11-15-6963-colab-decomp.txt:7335-7415`).

A már létező `0x00456610` `.picasa.ini`-olvasó kimenet részleges mezőútja:
`caption` értéket egyben a `+0x50` virtuális callback kapja; a `keywords`
mezőt vesszőnként tagolja, és az elemek a `+0x5c` callbackre jutnak. A
`rating` → `]star`, `hidden=yes` → `]hidden` és `screensaver` → `]screensaver`
út közvetlenül a `0x004d9aa0`-t hívja (`2026-10-21-idorend-31.txt`,
`0x00456610`; a hívó-xrefek ellenőrzése: bináris-index `xrefs`). A callbackek
szóhatára, valamint a fájlnév, kiterjesztés, kamera/EXIF, dátum, hely és szín
forrása **NINCS MEG**. PicasaPy oldalon az FTS a nevet, feliratot és
kulcsszót fedi (`src/picasapy/index/schema.py:121-149`); a mappanév és a szín
külön út (`src/picasapy/index/queries.py:516-566`), kamera/EXIF, dátum és
hely nem önálló FTS-oszlop.

#### Eredeti / nálunk / teendő - mező-hozzárendelés

Eredeti: a `0x004403c0` a feltöltési `]web_`/`]suppress` állapothoz tartozik;
a `.picasa.ini` mezők részben a `0x00456610`-ból a `0x004d9aa0` vagy a
feloldatlan virtuális callback útjára jutnak. A mezők teljes térképe nincs
meg.

Nálunk: `index/schema.py:121-149` FTS-oszlopa a fájlnév/felirat/kulcsszó;
`index/queries.py:516-566` a mappanév- és színkeresést külön kezeli.

Teendő: előbb a valódi `0x004d9aa0` beszúró összes közvetlen hívóján keresd
meg a token eredetét; utána egyedi értékű mérés igazolja a kamera/EXIF,
dátum, hely és szín kereshetőségét. A régi `0x00682c00` kérés nem maradhat
fotómező-indexelő célként.

Kész, ha:

- a fájlnév, felirat, kulcsszó, kamera/EXIF, dátum, hely és szín mindegyikéhez
  megvan a bináris mezőút vagy a pontos eredeti mérés;
- az egyes mezők eredményét külön, egyedi próbaértékkel rögzítették;
- hiányzó bizonyítékot nyitott kérdésként hagytak, becsült mező nincs.

**Célzott következő kérés:** Ghidra-kör kell: `0x004d9aa0` - az általános
szó-beszúró már dekompilált törzse csak a token normalizálását és tárolását
mutatja; az új kérdés a közvetlen hívók mezőeredetének csoportos feltárása
(különösen `0x0041c340`, `0x00439a80`, `0x00449090`, `0x00456610`), és a
`0x00456610` `+0x50`/`+0x5c` callbackjeinek célja. Ez új kérdés, nem a
meglévő beszúró-dekompiláció megismétlése.

**Cáfoló kör.** Megpróbáltam cáfolni, hogy a `0x00682c00` általános
fotómetaadat-indexelő lenne. A függvény kontextusa a `CUploadManager` törlési
folyamata, a hívás bemeneti szavai `]web_`/`]suppress`; a független index-xref
ugyanazt az egyetlen direkt hívóágat adja. Ez cáfolja a cím szerepét a
felirat-/EXIF-indexelés bizonyítékaként, de nem cáfolja, hogy más hívóágak
fotómezőket indexelnek.

### #7266-kiegészítés (#506-507, 2026-11-19): navigációs rekord és szóindex

A `0x0057ec70` a navigációs rekord első dwordjét, refcountolt sztringjét és a `0x0057ed00` segéden keresztül az összetett részrekordot másolja. A `0x00600ac0` a `0x00660c80` által összeállított pillanatképet teszi a `+0x32b0` mezőbe egy albumtagság-módosításkor. A pillanatképben keresési szöveg, rejtett-elemek jelző, szűrőgombok és nézet-/kijelölési állapotok vannak; ezért a `+0x32b0` a keresési és nézetállapot mentett példánya. Az összetett részrekord teljes mezőtérképe a `0x0057ed00` pontos vizsgálatáig nyitott.

A `0x004d9aa0` általános szóindexelő a kapott tokeneket tárolja, nem nevezi meg a fájlmezőket. A `.picasa.ini`-olvasó `0x00456610` a `caption` értéket egyben a `+0x50` callbacknek, a `keywords` vesszőtagjait a `+0x5c` callbacknek adja át; a `rating`, `hidden=yes` és `screensaver` jelzéseknek külön tokenútjuk van. A közvetlen hívók `0x0041c340`, `0x00439a80` és `0x00449090` ismertek, de a tokenforrásul adott rekord mezői és az objektumok `+0x2c`/`+0x50`/`+0x5c` virtuális céljai nincsenek feloldva. Ezek a hívók már dekompilálva vannak, ezért nem kérem ugyanazokat újra; következő lépés a vtable-célok azonosítása a hívó objektumok építőágából.

## #7082: A Mappakezelő teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti bináris nem futott; a kódoldali leletek célzott x86-diszasszemblálásból,
az indexből és a már meglévő Ghidra-kimenetekből származnak. A helyi oldalt a
jelenlegi QML/Python-forrásból olvastam. A NAS-hoz nem nyúltam.

**Mérési kapu.** Lefuttattam a kért `grep -rn 'job-[0-9]' docs/specs/`
ellenőrzést. A Mappakezelő-spec (`picasa-mappakezelo.md`) nem hivatkozik
kapcsolódó `job-NNN` felvételre; a 9/b-ben lévő korábbi tulajdonosi
képernyő-összevetés csak UI-állapotot dokumentál. A paritáslap korábbi
`ki00`/`ki06` felvétele a dialógus megnyitását mutatja, nem a teljes hatást.
A `~/.local/share/picasapy-meroadat/meroadat.tar` tartalomjegyzékében nem
találtam Mappakezelő- vagy job-felvételt, ezért nem bontottam ki adatot.

### Következtetés

Az eredeti Picasa Mappakezelőjének két menübelépője és ezek állapotszerkesztési,
megerősítési, mentési láncának több része igazolható; a jelenlegi Fájl és
Eszközök menüpont ugyanarra a dialógusra vezet, és a szerkesztőnézet alatti
tiltást is tükrözi. A teljes paritás nem zárható le: a `scanlist.txt` tartós
írása, a `.picasa.ini` és a pontos nézet-/kijelölés-hatás, továbbá az eredeti
hibás, hálózati és írásvédett esetek futásidejű kimenete nem bizonyított.

**Bizonyítottsági fok: nyitott.** A két menüút, az OK-út közvetlen fájl- és
indexműveletei, a Cancel működése és a jelenlegi forrásfolyam feltártak. A
kérdés maga viszont minden belépést és minden következményt kér; a hiányzó
runtime-adatok miatt ezekből nem következik teljes viselkedési paritás.

### Bizonyíték

| Érték / állítás | Forrás |
|---|---|
| Fájl ▸ „Add Folder to Picasa…” és Eszközök ▸ „Folder Manager…” ugyanazt a `0x9caa` parancsot használja; a menürekord-párosításnál a #7012 szerinti előző rekord szabály érvényes. | bináris (`0x00559150`, rekordadat `0xd6d988`/`0xd6e850`, parancs `0x9caa`); `picasa-menu-parancsok.csv:59,132` |
| A `0x9caa` dispatcher-útja `0x005ce590` mód=0 ágára vezet, amely a Mappakezelőt nyitja; a mód=1 ág külön mappaeltávolító út. | bináris (`0x005cb990`, index 104, `0x005cbdd3`, `0x005ce590`, `0x005ce5b4`); a külön eltávolítás `0x9cce` |
| Mindkét eredeti menüpont szürke az `editpanel/preview` aktív állapotában. | bináris (`0x0056e1c0`, `0x9caa` állapotkapu); helyi menükapcsolat: `picasa-menu-parancsok-viselkedes.md:2130-2163` |
| Az eredeti dialógus kezdő mérete 550×450; alapból a „Scan Once” opció van benyomva, a mappa tényleges állapotát viszont a könyvtár listái adják. | bináris erőforrás (`respack.yt`, `tre:foldermgr`, `docbounds`); bináris (`0x007c60d0`, `0x007c5c40`) |
| A meglévő specifikáció a „Watched Folders” látható listáját a `Preferences\HotFolders` beállításhoz köti; a vele párhuzamos `watchedfolders.txt`-írás pontos kapcsolatát/idejét nem rögzíti. | bináris (`0x00418ad0`); `picasa-mappakezelo.md:1046-1075`; a fájlíró `0x004f5960` |
| OK-ra az eredeti sorrend közvetlenül: `watchedfolders.txt` teljes újraírása, `]album:removed` index-token, feltételes arckizárás (`frexcludefolders.txt` és `imagedata_facerect`), záró nézetfrissítés. | bináris (`0x005cef20`, `0x005cf49b`, `0x004f5960`, `0x005cf500`, `0x004b9200`, `0x005cf529`, `0x00491210`, `0x004f5d90`, `0x005cf535`, `0x0065b840`) |
| A Mappakezelő OK-ja meghívja a `0x004f6a20`-at; a `+0x484` callback-lista vtable `+8` célja nincs feloldva. A DBLoader-slot `0x0055ff50` lokális disassemblyje a `0x006d4710` memóriabeli lista-frissítőt hívja; annak értesítési fogadója szintén virtuális. | bináris (`0x005cf411`, `0x004f7db8`-`0x004f7dbc`, `0x0055ff50`-`0x0055ff68`); meglévő Ghidra-kimenet: `2026-11-11-6532-colab-12-olvasok-hivok.txt:4978-6039,20149-20263,22742-22767`; DBLoader slotadat: `picasa-idorend-bemutato-kutatas.md:2581` |
| Helyi ablakméret, állapotmezők, menükapcsolat, Cancel és háttérsor-forrás. | forráskód: `FolderManagerDialog.qml:19-80,100-145,327-336`; `FolderStatePanel.qml:24-34`; `PicasaFileMenu.qml:38-45`; `PicasaToolsMenu.qml:12-18`; `MainMenuBar.qml:121-126,196`; `library_controller_folders.py:397-469` |
| Eredeti `.picasa.ini`-diff, összes további belépési pont, lemezhiba/ütközés, megszakítás, hálózati/írásvédett futás és OK utáni visszavonás. | NINCS MEG: nincs releváns `job-NNN` felvétel; a hiányzó viselkedést tiszta profillal és kontrollált fájl-/index-diffel kell rögzíteni. |

### Eredeti / nálunk / teendő

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fájl ▸ „Add Folder to Picasa…” és Eszközök ▸ „Folder Manager…”: mindkettő `0x9caa`, mód=0 → `0x005ce590`; szerkesztő-előnézetben tiltva (`0x0056e1c0`). | `PicasaFileMenu.qml:38-45`; `PicasaToolsMenu.qml:12-18`; `MainMenuBar.qml:121-126,196` | Egyezik. A `picasa-mappakezelo.md:1112` régi állítása, miszerint a Fájl-tétel helyfoglaló, a jelenlegi forrás szerint elavult; ezen a lapon korrigálva. |
| További eredeti eszköztár-, helyimenü- vagy Mappakezelőt nyitó billentyűút hiánya nem bizonyított. A hasonló `0x9cce`/„Remove from Picasa…” parancs külön eltávolító művelet. | A jelenlegi forrásban a két menü nyitja közvetlenül a dialógust; a `FolderManagerDialog.qml:327-336` Escape-je bezárás/Mégse, nem belépő; a mappa-kontextusmenü külön eltávolítást kínál (`FolderContextMenu.qml:312-316`). A Picasa-adatok átvétele külön dialógus (`MainWindowCommands.qml:688-701`). | Ne állítsunk teljes belépő-paritást. Colab-felvételen járd végig az eredeti menüket, helyi menüket, eszköztárat és billentyűket; a `0x9cce` ne kerüljön Mappakezelő-belépőként a listába. |
| `foldermgr.tre` mezői: bal oldali mappafa; útmutató; aktuális mappára 3 állapot; ettől külön arcfelismerés-kapcsoló; a figyelt mappák listája; OK/Mégse/Súgó. Kezdő méret 550×450; kezdeti opció `scan_once`, a per-mappa állapot a könyvtári listákból frissül (`0x007c60d0`). | `FolderManagerDialog.qml:19-59,181-204,349-439`; `FolderStatePanel.qml:24-34`; ablakméret `FolderManagerDialog.qml:27-31` | Az alapelrendezés egyezik. Az eredeti ablak pozíciójának/méretének újranyitás utáni megőrzése és az aktuális rádióállapot teljes futásidejű paritása nincs mérve. |
| OK előtt a dialógus deltákat gyűjt; Mégse és Escape nem alkalmazza őket (`0x007c285f-0x007c2866`, `0x007c28c6`, `0x007c6430`). | `FolderManagerDialog.qml:49-80,100-145,327-336` | Egyezik a felhasználó által látott Cancel/OK határ. A helyi `setFolderManagerState` a scanlistet közvetlenül írja (`library_controller_folders.py:103-133`), ezért az OK belső írási sorrendje nem egyetlen közös fájlmentés. |
| Teljes meghajtó „Scan Always” kérdés: „No” a `watch` állapotot kikapcsolja és az `remove` rádiót benyomja (`0x007c294b-0x007c29d5`). | `FolderManagerDialog.qml:264-300,531-538` | Egyezik: a helyi „No” `none` állapotot léptet. |
| Figyelt mappa eltávolításának `IDS_HOTFOLDER_CONFIRM` szövege ebben a buildben nem töltődik be; az OK-kori arcadat-törlésről külön kérdés van (`0x007c54d6`, `CFolderMgrDialog::confirmfrexclude`). | `FolderManagerDialog.qml:131-145,289-298,540-555` | A helyi megerősítés a figyelt mappákra többlet az eredetihez képest; a már rögzített ADR-005 szándékos biztonsági eltérésként tartja meg. Nincs új fejlesztői jegy. Az arctörlési kérdés időzítése egyezik; az eredeti `.picasa.ini`-hatása nyitott. |
| Az eredeti Help böngészőben a régi Google support URL-t nyitja (`0x007c4d23`, `0x007c4d77`). | `FolderManagerDialog.qml:485-491,558-588` | A helyi rövid súgó szándékos helyettesítés, mert a régi súgócikk nem érhető el; új paritásjegy nem javasolt. |
| Eltávolításkor `0x004b9200` `]album:removed` tokent tesz az indexbe; képfájl-törlés nincs a leírt műveletben. Az arckizárás a `0x00491210` és `0x004f5d90` útján megy. A scanlist-persistálás ellentmondásos dokumentációjú. | `library_controller_folders.py:472-531,552-620`; `folder_manager_save_controller.py:75-119`; a scanlist írója `library_controller_folders.py:103-133` | Az index-token és a fájlírás közvetlen sorrendje dokumentált. `scanlist.txt` OK utáni írási időpontját/útját és az `.ini`-diffet ne tekintsük lezártnak; lásd Nyitott. |
| Eredeti záró művelet `0x0065b840`; bal hasáb, rács, kijelölés és státuszsor pontos végállapota nincs mérve. | Eltávolítás az aktuális gyökér alatt üríti az aktív mappanézetet és újratölt (`library_controller_folders.py:518-531`); a scanOnce indexbe dolgozik háttérsorban (`:430-469`). | Nincs igazolt paritás vagy fejlesztési eltérés. Mérj képernyő- és indexállapotot a művelet előtti/utáni képkockákon. |
| Írásvédett profil, elérhetetlen megosztás, párhuzamos módosítás, félbeszakítás és utólagos visszavonás: NINCS MEG futásidejű lelet. | A helyi mentő a `syncFailed` jelzést adja és bezárhat (`folder_manager_save_controller.py:75-90`; `MainErrorBanner.qml:79-84`); a korábban sikerült lépéseket nem görgeti vissza (`save_folder_manager.py:148-159`). A scanOnce sorba áll és nem szakítható meg (`library_controller_folders.py:430-469`). | Ne következtessünk paritásra. Eredeti Windows-felvétel kell külön írásvédett profil, hibás/leválasztott út, ütköző OK, Cancel/folyamatmegszakítás és művelet utáni visszavonás esettel. |

### A mentési út részlete

Az eredeti `0x005cef20` OK-alkalmazó közvetlen sorrendjében a figyelt mappák fájlja
írása (`0x005cf49b → 0x004f5960`) megelőzi a törlési sírkövet
(`0x005cf500 → 0x004b9200`). Ezután csak nem üres arckizárási deltánál hívja a
`0x00491210`-et, amely az `imagedata_facerect` értékeit is átállítja és a
`0x004f5d90`-nel újraírja a `frexcludefolders.txt`-et; a záró ág
`0x0065b840`. A `0x005cf411 → 0x004f6a20` hívás ugyanebben az OK-ágban van.

A `picasa-mappakezelo.md` 5.2/c és 17.2 szakasza egymásnak ellentmondóan
állítja, hogy ez a hívás a `scanlist.txt`-et írja, illetve nem írja. A meglévő
Ghidra-kimenet `FUN_004f6a20` dekompilációja fel nem oldott virtuális callbacket
mutat (`0x004f7dbc`): a `+0x484` listán lévő objektum vtable `+8` metódusát
hívja. A DBLoader vtable-jának második címe `0x0055ff50`, de nem bizonyított,
hogy a `+0x484` lista elemei mind DBLoader típusúak. A `0x0055ff50` lokális
disassemblyje egy rövid thunkot mutat, amely a `0x006d4710`-hez hív; ennek
meglévő Ghidra-dekompilációja egy memóriabeli vektor elemét frissíti, majd a
`0x006a2a60` értesítő útját hívja. Az utóbbi út egy további, konkrét példányhoz
nem kötött vtable `+8` fogadót hív. Így a vizsgált részben nincs közvetlen
scanlist-fájlíró, de az értesítési fogadó lehetséges tartós mellékhatása nincs
feloldva; a `scanlist.txt` OK-kori írása továbbra is nyitott. Helyi programban a
`setFolderManagerState` minden állapotnál közvetlenül meghívja a
`write_scan_list`-et, még a figyelt mappák és az arckizárás mentése előtt.

A meglévő bináris lelet a felületen látható „Watched Folders” lista tárolását
a `Preferences\HotFolders` beállításhoz is köti (`0x00418ad0`). A registry-érték
és a `watchedfolders.txt` OK-kori frissítése közötti sorrend/kapcsolat nincs
végigkövetve; az eredeti runtime-felvételnek a profil beállításait is rögzítenie
kell, nem csak a fájlokat.

Az eredeti Manager-útvonalon `.picasa.ini` író nem azonosítható a vizsgált
közvetlen hívássorban. A `0x00491210` meglévő Ghidra-anyaga az index- és
`frexcludefolders.txt` útját mutatja; ez önmagában nem zárja ki a későbbi vagy
közvetett `.ini`-módosítást. PicasaPyban a kapcsoló nem törli a
`.picasa.ini` `faces=`/`[Contacts2]` adatait (`library_controller_folders.py:573-578`).
Az eredeti előtte/utána fájldiff nélkül erre eltérést nem állítok.

### A két független út

- **A: utasításszintű út:** a `0x00559150` menüépítőnél a két felirathoz
  tartozó rekordot a #7012 szabály szerint párosítottam; mindkettő parancsa
  `0x9caa`. A `0x005cb990` dispatcher 104. táblabejegyzése a
  `0x005cbdd3 → 0x005ce590(mode=0)` út, amely a dialógust nyitja.
- **B: külön adat-/hívóút:** a menüparancs-katalógusban két külön
  `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` rekord van (`picasa-menu-parancsok.csv:59,132`),
  az eredeti `0x005ce590` hívói közül pedig a mód=0 a menüút, a mód=1 a
  külön `Remove from Picasa` funkció. A forráskódban két külön QML-menüelem
  ugyanarra a helyi `folderManagerRequested` jelre csatlakozik.
- A két út a két menübelépő azonosságában egyezik. A teljes kérdéshez nem
  elégségesek: nincs ettől független eredeti runtime-felvétel, amely a
  rejtett belépőket, mellékhatásokat, hibákat és az undo útját is igazolná.

### Cáfoló kísérlet

Megpróbáltam cáfolni, hogy a másik hasonló mappa-parancs is Mappakezelőt
nyit-e: a menürekord- és dispatcher-útban a `0x005cbd11` mód=1 hívást
ellenőriztem. Az nem a második `0x9caa` menürekordhoz tartozik, hanem külön
`0x9cce` parancs; a vele kapcsolatos megerősítő eltávolító dialógus másik
folyamat. A cáfoló leletet a menü CSV-vel és a dispatcher disassemblyjével
ellenőrizve az eredeti két menübelépő állítása megmarad, de toolbar/gyorsbillentyű
hiányára továbbra sem ad negatív bizonyítékot.

Megpróbáltam cáfolni azt, hogy a `0x004f6a20` közvetett úton perzisztálhat.
Az eredeti disassembly és a meglévő Ghidra-kimenet egyaránt megmutatja a
`0x004f7dbc` virtuális hívást: a `+0x484` listán lévő objektum vtable `+8`
slotja fut le. A DBLoader vtable táblája ennek a típusnak a slotját
`0x0055ff50`-ként azonosítja, de a lista minden elemének típusa nincs
igazolva. A lokális disassembly szerint a `0x0055ff50` thunk `0x006d4710`-hez
hív; a meglévő Ghidra-dekompiláció a vektor-módosítás és a `0x006a2a60`
értesítése után egy másik, virtuális megfigyelőhívást mutat. A `grep -il '0055ff50' ~/picasapy-agent/referencia/ghidra/*.txt` nem talált erre a thunkra
dekompilációt, de a `0x006d4710` és `0x006a2a60` címet tartalmazó meglévő
kimeneteket külön ellenőriztem. A közvetlen file-írás hipotézisét a
`0x006d4710` törzse nem támasztja alá; a megfigyelőhívás miatt a közvetett
perzisztálás nem cáfolható. A cáfoló kísérlet tehát szűkítette a lehetséges
írás helyét, de a scanlist-hatást nem döntötte el.

### A jegy „Kész, ha” pontjai

1. ⛔ **Belépési pontok és feltételek:** két eredeti menü és szerkesztőnézet-kapu,
   valamint a helyi párjaik igazoltak; eredeti toolbar, helyi menü és
   Mappakezelőt nyitó gyorsbillentyű teljes kizárása nincs meg.
2. ⛔ **Ablak, mezők, alapértékek, megjegyzett állapot és kérdések:** alapelrendezés,
   három állapot, arckizáró kapcsoló, teljes meghajtó és OK-kori arcmegerősítés
   ismert; ablakgeometria megőrzése, ütközések és minden esetleges további
   kérdés nincs runtime-mérve.
3. ⛔ **Hatás fájlokra, `.picasa.ini`-re, indexre, bal hasábra, rácsra,
   kijelölésre, háttérre és állapotsorra:** a közvetlen írók, sírkő és
   `imagedata_facerect` út bizonyított; scanlist-tartósítás, `.ini`-diff és a
   a felület teljes végállapota nincs bizonyítva.
4. ⛔ **Hiba, ütközés, megszakítás, hálózat/írásvédelem és visszavonás:** nincs
   eredeti futtatott felvétel; PicasaPy-oldalon a hibasáv, a sorba állítás és
   az egyszeri keresés megszakíthatatlansága forrásból olvasható, ez nem
   igazolja az eredeti viselkedést.

### Javasolt jegytörzs-bővítés

Jelen körben nincs kódfejlesztési jegy, amelyet a teljes paritás állítása
nélkül pontosan meg lehetne fogalmazni. A bizonyított UI-eltérések a helyi
megerősítés a figyelt mappákra (ADR-005 szerinti szándékos többlet) és a régi online
Help helyetti rövid helyi súgó; ezekhez új feladatot nem javaslok.

Ha az eredeti runtime-felvétel később eltérést igazol, a jegytörzsben minden
javasolt kódváltozás ilyen alakban szerepeljen:

> Eredeti: `<bináris cím vagy mérés eredménye>`.
> Nálunk: `<fájl:sor>`.
> Teendő: `<szűk, pontos implementáció>`.
> Kész, ha: `<eredeti kimenetet rögzítő kontrollált eset>`.

### Új kutatási jegyjavaslatok

Új kérdés-jegy helyett a #7082 nyitott runtime-pontjait egy eredeti Windowsos
Colab-felvételben kell lezárni. A mérési terv: tiszta profil; mindkét menüből
nyitás és szerkesztő-előnézet; valamennyi helyi menü/eszköztár/billentyű
bejárása; egyenként rögzített Scan Once/Remove/Scan Always/arckizárás OK és
Cancel; előtte/utána `watchedfolders.txt`, `frexcludefolders.txt`, `scanlist.txt`,
db3, érintett `.picasa.ini` fájlok és képfájlok diffje; bal panel/rács/kijelölés/
állapotsor képkockái; külön read-only profil, ismétlődő gyökér, megszakítás,
leválasztott hálózati út és OK utáni undo-próba.

### Nyitott

- `Ghidra-kör kell: 0x006a2a60 - oldd fel, hogy a 0x0055ff50 → 0x006d4710 értesítési útján a 0x006a2a60 által az (objektum+0x32c) címen tárolt pointeren át elért objektum vtable +8 fogadója konkrétan milyen példány a Mappakezelő OK-útján, és elindít-e scanlist.txt vagy más tartós adatírást. A meglévő 2026-11-11 Ghidra-kimenet már dekompilálja a 0x004f6a20, 0x006d4710 és 0x006a2a60 függvényt; a hiányzó kérdés a callback-lista, az értesítő fogadó és a Mappakezelő-példány közötti konkrét típus-/xref-kapcsolat, nem a függvénytörzsek újradekompilálása. [blokkoló a scanlist-hatás lezárására]`
  - Zárókör (2026-11-17): LEZÁRVA a meglévő bizonyítékból és a hívóhely utasításaival, nincs szükség új Ghidra-körre: a visszahívás rekesze `+8`, vagyis `0x0055ff70` → `0x00419240` (nem a `0x0055ff50` → `0x006d4710`), fájlt nem ír; a `scanlist.txt`-et az OK nem írja (Zárókör 1. és 2. pont).
- `NINCS MEG: PicasaPy Mappakezelő teljes balhasáb/rács/kijelölés/állapotsor utóállapota az eredetivel azonos adatállapotban. Megszerzés: a fenti kontrollált Colab-felvétel előtte/utána képkockái és index-diffje.`
  - Zárókör (2026-11-17): a bináris eldönti, hogy az OK a keresés végrehajtóját kényszerítve újrafuttatja (`0x0065b840` → `0x00662b20`); a látható részletekre (bal hasáb, rács, kijelölés, állapotsor) egyetlen Colab-feladat marad, ez a jegy egyetlen blokkolója (Zárókör 6. pont).
- `NINCS MEG: az eredeti OK/Cancel, ismétlődő mappa, írásvédett profil, leválasztott hálózati út, megszakítás és OK utáni undo látható kimenete. Megszerzés: a fenti esetek külön futtatott, tiszta profilú Colab-felvétele.`
  - Zárókör (2026-11-17): LEZÁRVA a binárisból: ismétlődő mappa, írási hiba (az eredeti néma), megszakítás, visszavonás (nincs) és ablakméret-megőrzés (nincs) eldőlt (Zárókör 3. és 4. pont); a hálózati meghajtó megjelenése örökölt, nem blokkoló, már nyilvántartott (`picasa-mappakezelo.md` 13.4/a, 13.9).
- `NINCS MEG: a face-detection kizárás eredeti .picasa.ini-hatása. Megszerzés: kizárás előtt/után az érintett mappák .picasa.ini fájljainak és az adatbázisnak a tartalmi diffje.`
  - Zárókör (2026-11-17): LEZÁRVA, erős: az OK-út közvetlen zárlatában nincs `.picasa.ini`-hoz vagy `faces`, `Contacts2` sztringhez kötött függvény; nálunk is egyezik (Zárókör 3. pont).
- Eredeti menürekordokból a két menüút igazolt; **NINCS MEG** a további belépőutak teljes negatív bizonyítéka. Megszerzés: menü-, helyimenü-, eszköztár- és billentyűbejárás képernyőfelvétellel és parancsazonosító-naplóval.
  - Zárókör (2026-11-17): LEZÁRVA, erős: a `0x9caa` azonosítót csak a két menürekord és a szürkítési kapu hivatkozza, a diszpécser táblájában csak ez viszi a Mappakezelő ágára, az exe-ben nincs gyorsítótábla vagy menüerőforrás (Zárókör 5. pont).

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7082 szakasz; bizonyított eredeti OK-lánc, a helyi menük és mentés, eltérés-/nyitott táblázat, falszifikáció és célzott runtime-mérési terv.

### Zárókör (2026-11-17): a megmaradt tételek döntése

Módszer: minden megmaradt „NINCS MEG” és „Ghidra-kör kell” tételt a meglévő bizonyítékból és új, helyi, utasításszintű olvasásból döntöttem el (a bináris a fent megadott `Picasa3.exe`, csak olvasva; Ghidra nem futott). A „Nálunk” oszlopot a mai forráson ellenőriztem (grep, a sorszámok a 2026-11-17-i állapotra vonatkoznak). A dekompiláció veremértelmezését ott, ahol állítás múlt rajta (a visszahívás rekesze, a záró lépés paraméterei), a hívóhely utasításaival vetettem össze; ennek eredménye az 1. pont helyesbítése.

**Hívási zárlat.** Egy kiindulási függvény zárlata a belőle közvetlen hívásokkal elérhető függvények halmaza (a bináris indexének hívási táblájából, `xrefs`). Ebből kiszűrtem azokat, amelyek fájl- vagy beállításíró importot hivatkoznak (`imports`, függvényenkénti hivatkozás: `CreateFileA/W`, `WriteFile`, `SetEndOfFile`, `RegSetValueEx*`, `RegCreateKeyEx*` és társaik), vagy a megnevezett fájlok sztringjét. **Kontroll:** a `watchedfolders.txt` írójának (`0x004f5960`) és a `scanlist.txt` írójának (`0x004f61c0`) zárlata eléri a `CreateFileA`, `CreateFileW`, `SetEndOfFile` és `WriteFile` importot hivatkozó függvényeket, tehát a mérő lát fájlírást. **A mérő határa:** a virtuális hívásokat az index nem látja, ezért a „nincs író a zárlatban” állítás a közvetlen hívásokra és a külön feloldott visszahívásra érvényes, nem a feloldatlan virtuális hívásokra.

#### 1. Helyesbítés: az OK-út megfigyelő-értesítője a `0x0055ff70`, nem a `0x0055ff50`

A fenti szakasz („A mentési út részlete”, „Cáfoló kísérlet”, „Nyitott”) a `0x004f6a20` végén lévő virtuális hívást (`0x004f7db8`-`0x004f7dbc`) a `DBLoader` vtábla második címével (`0x0055ff50`) azonosította, és erre építette a `0x006d4710` → `0x006a2a60` láncot, valamint a blokkoló „Ghidra-kör kell” sort. **A rekesz eltolása téves volt.**

- **Hívóhely:** `0x004f7da4 mov ecx,[ebx+0x484]` (a beolvasó megfigyelő-listája), `0x004f7db2 mov eax,[eax]` (az objektum), `0x004f7db4 mov edx,[eax]` (a vtábla), **`0x004f7db8 mov eax,[edx+8]`**, `0x004f7dbb push ebx`, `0x004f7dbc call eax`. Tehát a vtábla `+8` eltolású, vagyis **harmadik** bejegyzése hívódik, egyetlen veremparaméterrel.
- **A `DBLoader` vtábla** (`0x00c7f5c0`, RTTI: `DBLoader::vftable`, a típusleíró `.?AVDBLoader@@`): `+0` `0x0055ece0`, `+4` `0x0055ff50`, **`+8` `0x0055ff70`**, `+0xc` `0x00401570`. A `0x0055ff50` a `+4` rekesz (`ret 8`, két paraméter, `0x0055ff68`), a `0x0055ff70` a `+8` rekesz (`ret 4`, egy paraméter, `0x0055ff7b`). A hívóhely egy paramétert tesz a verembe: a `ret 4` egyezik vele, a `ret 8` nem.
- **Egyetlen megfigyelő van feliratkozva.** A `+0x484` lista (a beolvasó, vagyis az alkalmazásobjektum `+0xf8` mezőjében lévő `ytDirScanner` objektum mezője) írói a `0x401000`-`0x580000` tartományban: a konstruktor (`0x004e41f0`, `0x004e43e1`/`0x004e43e7`, nullázás), a takarító (`0x004e4960`, `0x004e4aa5`/`0x004e4aab`) és a hozzáfűző `0x004e4ea0` (`0x004e4f2a`, `0x004e4f77`). A teljes binárisra futtatott korábbi keresés (`2026-11-11-6532-colab-11-484-irok.txt`) további `+0x484` íróit nem a beolvasó objektumra írják: a `0x00514180` más osztály konstruktora (vtábla `0x00c891e4`), a `0x0067e980` a mezőt számként használja (`sub`, `fild`), a `0x008b0ce0`, `0x008bb4d0`, `0x008cd360` szóméretű mezőt ír. A hozzáfűző egyetlen hívója a `0x004183c0` (`0x004188cf`), annak egyetlen hívója az alkalmazás-előkészítő `0x00402f90` (`0x0040361c`). Ott a feliratkozó objektumot a `0x004035d0`-`0x00403605` hozza létre: `0x8c` bájt, `[obj] = 0xc7f5c0` (`0x004035f5`), `[obj+4]` az alkalmazásobjektum (`[ebx+0x1034]`, `0x004035fb`).
- **A `0x0055ff70` egyetlen dolga:** `mov eax,[ecx+4]`, `push eax`, `call 0x00419240`, `xor eax,eax`, `ret 4`.
- **A `0x00419240` (950 bájt) memóriabeli frissítés.** Zárolja a beolvasó kritikus szakaszát (`app+0xf8`), az `app+0x4e8` lista elemeiből jelzőbájt-vektort képez (az elem `+0x1d` bájtjából, `0x00419346`-`0x00419371`), ezt a `0x004db940`-nek adja át az `app+0x68` mezővel (`0x004193ba`-`0x004193be`), majd az `app+0x988` és `app+0xbb0` mezők kritikus szakaszát is zárolva az `app+0xbb0` mező `+0x58` listájának elemeire a beolvasó `0x004ef8f0` vizsgálatát hívja (`0x004194fe`), és 9-es eredménynél virtuálisan hívja az `app+0x48` beágyazott objektum `+0xec` rekeszét az elem sorszámával (`0x00419503`-`0x00419518`). Sztringet nem hivatkozik. Zárlata 144 függvény; fájl- vagy beállításíró importot hivatkozó függvény nincs benne, kivéve a `0x00bef7d3`-at, ami a C futásidejű könyvtár végzetes hibaüzenet-kiírója (`Runtime Error!`, `R6009`), és csak a memóriafoglalás (`0x00bf426f`) hibaágán át érhető el.
- A tévesen azonosított `0x0055ff50` → `0x006d4710` útnak (két paraméteres, másik értesítés) a zárlata szintén nem tartalmaz adatfájl-írót.

**Következmény:** a „Ghidra-kör kell: 0x006a2a60” sor megszűnik, mert a `0x006a2a60` nem az OK-út értesítésének útján van. A `0x0055ff70` célja feloldott, és nem ír fájlt. Az `app+0x48` objektum `+0xec` rekeszének célja nincs feloldva; ez nem a beolvasó objektum (az az `app+0xf8`), ezért a `scanlist.txt`-hez nincs köze (lásd 2. pont), és látható hatása legfeljebb egy lista elem frissítése lehet: **nem blokkoló**.

#### 2. A `scanlist.txt` írója a beolvasó leállítási mentése, nem az OK-út

- **Az író egyetlen hívója virtuális.** A `0x004f61c0` egyetlen hívója a `0x004f54b0` (`xrefs`). A `0x004f54b0`-nak az indexben nincs közvetlen hívója (a `0x004f61c0`-t elérő fordított hívási zárlat csak e két függvény). A címe két vtáblában áll, mindkettőben a `+4` rekeszen: a `0x00c86c28` (`ytDirScanner`, a típusleíró `0x00cfbd9c`, ahol az objektumon belüli eltolás 88, vagyis `+0x58`) és a `0x00ca8240` (`ytDirScannerWindows`, `0x00d07988`). A két vtábla első hat rekesze azonos (`0x00509c20`, `0x004f54b0`, `0x00959340`, `0x00a4a070`, `0x00a4a080`, `0x00a4a090`). A vtábla címét a konstruktorok írják az objektumba (`0x004e424f`, `0x004e4982`, `0x0041585d`).
- **Mit csinál a `0x004f54b0`** (1188 bájt, `ret 8`): `ebx = esi - 0x58` (`0x004f54c2`, az al-objektumból a teljes objektumra számol), kritikus szakasz, majd virtuális hívás az al-objektum saját vtábláján `+0x10`-en (`0x004f5505`-`0x004f550a`): ez a `0x00a4a080`, ami az al-objektum `+8` bájtját adja vissza (`mov al,[ecx+8]`). Hamis eredménynél kilép (`0x004f550e`). Igaz eredménynél megnyitja a `thumbindex.db` fájlt (`0x004f555a push 0xc863a0`, mód: `wbS`, `0x004f5563`, megnyitó: `0x009917f0`), a rekordokat egyenként írja, a ciklus után a **`0x004f579c mov ecx,3`**, `0x004f57a1 call 0x004f25f0` (a diagnosztikai CSV írója), majd **`0x004f57aa call 0x004f61c0`**: a `scanlist.txt` írása; végül az al-objektum `+8` bájtját nullázza (`0x004f57bb mov byte ptr [eax+8],0`). A `+8` bájt tehát a mentés módosítás-jelzője: a mentés csak beállított jelzőnél fut, és lefutása után törli (a jelző beállítója az al-objektum `+0x14` rekesze, `0x00a4a090`, `mov [ecx+8],al`; a két rekeszt az indexben közvetlenül senki nem hívja).
- **A `0x004f25f0` módválasztása:** `1` → `dirscanner-start.csv` (`0x004f26a9`, `0x00c86490`), `2` → `dirscanner-up.csv` (`0x004f26d5`, `0x00c864a8`), **`3` → `dirscanner-shutdown.csv`** (`0x004f26e4`, `0x00c864bc`). A `0x004f54b0` a 3-as móddal hív. A CSV-t a `WriteDirscannerCSV` beállítás vezérli (`pmp-database.md`, a „HÁROM pillanat” szakasz).
- **Az OK-út közvetlen zárlata.** A `0x005cef20` hívottjai közül a nézetfrissítés (`0x0065b840`) nélküli rész (`0x004f5960`, `0x004b9200`, `0x00491210`, `0x004f6a20`, `0x00419c30`, `0x00492e40`, `0x0052e1f0`) együtt 381 függvény. Ebben nincs a `0x004f61c0` és a `0x004f54b0`; az érdekes sztringeket hivatkozó függvények csak a `watchedfolders.txt` (`0x004f5960`), a `frexcludefolders.txt` (`0x004f5d90`) és a `]album:removed` (`0x004b9200`) függvényei (meg egy beállításjegyzék-útvonal olvasó segédfüggvény: `0x009961c0`, `Shell Folders`). A fájlírást hivatkozó importok csak az általános fájlkezelő rétegben vannak (`0x00c1b805`, `0x00c1a940`, `0x00c1677c`, `0x00c0ec24`, és a fent említett hibaüzenet-kiíró `0x00bef7d3`); beállításíró import nincs.

**Következtetés:** az OK nem írja a `scanlist.txt`-et. Az eredetiben a `scanlist.txt` a beolvasó leállításakor frissül, a `thumbindex.db`-vel együtt. Ez egybevág a `picasa-mappakezelo.md` 17.2 negatív eredményével, és pontosítja annak indoklását: a `0x004183c0` az **olvasót** (`0x004f6380`) hívja (indításkor), az **írót** csak a `0x004f54b0`.

Bizonyítottsági fok: **megerősített** az OK-útra (közvetlen zárlat és az egyetlen, feloldott megfigyelő); **erős** a leállítási időzítésre (a CSV 3-as módja a függvény saját jelölése); **NINCS MEG** a `0x004f54b0` és a jelző beállítójának virtuális hívója (az index nem látja). Ez csak a mentés időpontját dönti el (leállításkor, vagy a jelző miatt korábban is), az OK-út közvetlen zárlatát nem érinti, és látható viselkedést nem: **nem blokkoló**.

**Nálunk (ellenőrizve):** `library_controller_folders.py:104-133`, a `setFolderManagerState` az OK mentési zárójelén belül (`FolderManagerDialog.qml:107-129`) azonnal újraírja a `scanlist.txt`-et. Az eredeti leállításkor ír. A felhasználó semmit nem lát ebből egy normál munkamenetben; eltérés csak szabálytalan leállásnál lehet (az eredeti a kilépés előtti egyszeri keresés jelölőit elveszíthetné, a mi korábbi írásunk nem). **Döntés: szándékos, előnyös eltérés (`picasa-mappakezelo.md` 17.5), nem blokkoló, fejlesztői jegy nincs.**

#### 3. Az OK-út teljes mellékhatás-halmaza

A 2. pont 381 függvényes zárlata (a nézetfrissítés nélkül) alapján az OK közvetlen hívásokkal ezt végzi: `watchedfolders.txt` újraírása (`0x004f5960`), `]album:removed` jelzés (`0x004b9200`), a feltételes arckizárás (`0x00491210`: az `imagedata_facerect` átállítása és a `frexcludefolders.txt` írása `0x004f5d90`-nel), a beolvasó memóriabeli listáinak frissítése (`0x004f6a20`) és a nézetfrissítés (`0x0065b840`). A nézetfrissítés zárlata 3350 függvény, olvasó és író útvonalakkal vegyesen (köztük `.picasa.ini`-t megnevező függvényekkel), ezért arra a pontra írásmentességet nem állítok, a hatását a 6. pont mérése dönti el. Az alábbi állítások a nézetfrissítés nélküli részre és a külön megnevezett zárlatokra vonatkoznak. Ami **nincs** benne:

- **`.picasa.ini` írása és névcímke-törlés.** A zárlatban egyetlen függvény sem hivatkozza a `.picasa.ini` / `Picasa.ini` sztringet, sem a `faces`, `Contacts2`, `facetags` sztringet; az arckizárás külön zárlata (`0x00491210`, 317 függvény) is csak a `frexcludefolders.txt` íróját és egy útvonal-segédet tartalmaz. A „remove all faces and name tags” kérdés tehát az eredetiben az `imagedata_facerect` jelölést és a kizáró fájlt érinti, a `.picasa.ini` `faces=` és `[Contacts2]` soraihoz közvetlenül nem nyúl. Bizonyítottsági fok: **erős** (nem megerősített: a virtuális hívásokat a mérő nem látja, és egy útvonalat paraméterként kapó ini-író nem hivatkozna sztringet). **Nálunk (ellenőrizve):** `library_controller_folders.py:573-578`: a kapcsoló nem törli a `.picasa.ini` `faces=` és `[Contacts2]` sorait; a `_jeloljuk_kizartnak` (`:605-619`) a saját `face` tábla találatait törli és a fotókat jelöli. **Egyezik.**
- **Ablakméret és helyzet megőrzése.** A `GetWindowPlacement` és a `SetWindowPlacement` egyetlen hivatkozója a főablak `0x005760e0` függvénye; a Mappakezelő osztály 52 függvényének (`0x007bf000`-`0x007cb000`) zárlata nem éri el. Beállításíró az OK-úton nincs, és az indexben nincs ablakhelyzetre utaló beállításkulcs-sztring. Az eredeti dialógus tehát minden megnyitáskor a `respack.yt` mérete (550×450) szerint nyílik, nem őrzi az utolsó méretet vagy helyzetet. **Nálunk (ellenőrizve):** `FolderManagerDialog.qml:27-28` fix 550×450, `Settings` vagy mentett geometria nincs. **Egyezik.**
- **Visszavonás.** Az egyetlen visszavonási verem osztály az `EditStack` (`0x00ca82f4`, `0x00ca8334`); a vtábláját csak a `0x006a92a0` és a `0x006a94b0` hivatkozza, egyik sincs az OK-út zárlatában. Mappaszintű visszavonás tehát az eredetiben nincs. **Nálunk (ellenőrizve):** `FolderManagerDialog.qml`, `folder_manager_save_controller.py`, `library_controller_folders.py` nem kínál visszavonást (`grep -i undo|visszavon`: csak magyarázó megjegyzések). **Egyezik.**
- **Megszakítás.** A dialógus mezői (`foldermgr.tre`, 1.1 szakasz) a mappafa, a három állapot, az arckapcsoló, a lista, OK, Mégse és Súgó: megszakító vezérlő nincs. Az OK a hívó szálon, közvetlen hívásokkal írja a fájlokat és a jelölést; a „Keresés egyszer” hatására indított beolvasás a beolvasó szálon fut, annak leállítására a Mappakezelőben nincs felület. **Nálunk:** a `scanFolderOnce` sorba áll és nem szakítható meg (`library_controller_folders.py:397-469`). **Egyezik.**
- **Ismétlődő mappa.** A `0x005cef20` első ciklusa (`0x005cef8d call 0x00492e40`, `0x005cef92 cmp eax,-1`, `0x005cef95 jne 0x005cf12b`) a könyvtár figyelt-listájában (`+0x364`) tagsági vizsgálatot végez, és a már szereplő mappát átugorja, tehát nem kerül kétszer a listába. **Nálunk (ellenőrizve):** `addWatchedFolder` (`library_controller_folders.py:319-343`, a `_find_root` ellenőrzés `:334-336`) nem vesz fel másodszor mappát, és `mar-figyelt` jelzést ad; a dialógus amúgy is csak az új mappákat adja át (`FolderManagerDialog.qml:107-129`). **Egyezik** (a jelzés nálunk többlet, az eredeti csendben átugorja).

#### 4. Az írási hiba az eredetiben néma

- **Eredeti:** a `watchedfolders.txt` írója megnyitási hibánál átugorja a mappaciklust (`0x004f5991 test edi,edi`, `0x004f5993 je 0x004f59ec`), és mindig 0-val tér vissza (`0x004f5a1b xor eax,eax`). A `frexcludefolders.txt` írója ugyanígy (`0x004f5dc1 test edi,edi`, `0x004f5dc3 je 0x004f5e1c`). A hívó az eredményt nem vizsgálja (`0x005cf49b call 0x004f5960`, majd `0x005cf4a0 mov eax,[esp+0x44]` felülírja az `eax`-et). Írásvédett profilnál, elérhetetlen megosztásnál vagy foglalt fájlnál az eredeti OK ezért **nem jelez**: az ablak bezárul, a fájl változatlan marad.
- **Nálunk (ellenőrizve):** `folder_manager_save.py:130-160` nem nyeli el az író kivételét, és a záró lépés akkor is lefut; `folder_manager_save_controller.py:75-90` naplóz és `syncFailed` jelzést ad (látható hibasáv: `MainErrorBanner.qml:7`), a korábban sikerült lépéseket nem görgeti vissza.
- **Döntés:** szándékos eltérés (az #1207 tanulsága a kódban: a beállítás nem tűnhet el némán). A nálunk látható jelzés többlet az eredetihez képest, ritka lemezhibánál jelentkezik, **nem blokkoló, fejlesztői jegy nincs**.

#### 5. További belépőutak: nincsenek

- **A `0x9caa` azonosító előfordulásai.** A 16 bites alakban a `.text`-ben nyolc bájtegyezés van; ebből három valódi azonosító: a két menürekord írása a menüépítőben (`0x00559241` a Fájl, `0x0055c592` az Eszközök menü rekordjába) és a szürkítési kapu (`0x0056f567`, `push 0x9caa`, `0x0056e1c0`). A másik öt egyezés (`0x0095d0c2`, `0x00a3652d`, `0x00a36594`, `0x00a365a1`, `0x00a365d7`) `call` utasítások relatív címének bájtja (`e8 .. aa 9c 03 00` és `.. aa 9c ff`). A `.rdata` és `.data` szakaszban nincs előfordulás (a menürekordok futásidőben épülnek). A 32 bites alak egyetlen helye a `0x0056f567`.
- **A diszpécser táblái.** A `0x005cb990` három bájtindex- és ugrótáblát használ (`0x005cdb34` és `0x005cd9fc`, az azonosítóból `0x9c42` levonva; `0x005cde04` és `0x005cdc30`, `0x9d44` levonva; `0x005cdfe0` és `0x005cdefc`, `0xa02e` levonva). A `0x005cbdd1` ág (a Mappakezelő nyitása, mód 0) csak az elsőben szerepel, egyetlen bejegyzéssel (35. rekesz), amelyhez egyedül a `0x9caa` tartozik; a másik két táblában nincs ilyen cél, a tábla előtti összehasonlító ágak más kódra vezetnek.
- **A nyitó és a konstruktor.** A `0x005ce590`-nek két közvetlen hívóhelye van, mindkettő a diszpécserben (`0x005cbd11` mód 1, `0x005cbdd3` mód 0); címére adatban nincs mutató (`.rdata` keresés). A dialógus konstruktorának (`0x007c0130`) egyetlen hívója a nyitó (`0x005ce75d`).
- **Erőforrások.** A `Picasa3.exe` erőforrásai között nincs gyorsítótábla, menü és RCDATA (a típusok: kurzor, ikon, párbeszéd, sztring, csoport-ikon és -kurzor, verzió, jegyzék, egy 11-es típusú tétel). A `respack.yt` (2909 bejegyzés, 140 `.tre` forrás) nem tartalmaz `INCLUDEEXCLUDEFOLDERS` sztringet; az exe-ben a sztring csak a menüépítőben van (`0x00c8c75c`, `0x00c8e1e4`).
- **Következtetés (erős; nem megerősített: dinamikusan képzett azonosítót az index nem lát): az eredeti Mappakezelőnek pontosan két belépője van, a Fájl és az Eszközök menü; eszköztár-, helyimenü- vagy billentyűútja nincs.** A két menüpont szürke az `editpanel/preview` aktív állapotában (`0x0056e1c0`).
- **Nálunk (ellenőrizve, 2026-11-17):** `PicasaFileMenu.qml:38-45` (`menuFileAddFolder`) és `PicasaToolsMenu.qml:12-18` (`menuToolsFolderManager`), mindkettő `enabled: !bar.editorActive` és `bar.folderManagerRequested()`; a kötés `MainMenuBar.qml:189` (`hostFolderManager.open()`), a kapu `MainMenuBar.qml:117` (`editorActive: hostWindow.viewerOpen`), a betöltés `MainWindowCommands.qml:600`, a `Main.qml:645` köti be. Más belépő nincs (`grep folderManagerRequested|hostFolderManager`). A mappa-kontextusmenü külön eltávolítást kínál (`FolderContextMenu.qml:324`), a Picasa-adatok átvétele külön dialógus (`MainWindowCommands.qml:699`). **Egyezik.**
- **Elavult hivatkozások a fenti táblázatban** (csak a sorszámok csúsztak, a tartalom egyezik): `MainMenuBar.qml:121-126,196` → `:117,189`; `FolderContextMenu.qml:312-316` → `:324`; `MainWindowCommands.qml:688-701` → `:699`; `FolderManagerDialog.qml:19-80,100-145,327-336` → méret `:27-28`, Mégse `:78`, OK-alkalmazás `:107-129`, Escape `:332-336`; `save_folder_manager.py:148-159` → a modul neve `folder_manager_save.py` (`:130-160`).

#### 6. A záró lépés (`0x0065b840`) és a főablak állapota utána

- **Mit hív az OK a végén.** `0x005cf52e push 1`, `0x005cf530 push 0`, `0x005cf532 push 0`, `0x005cf534 push ebp`, `0x005cf535 call 0x0065b840`; a függvény `ret 0x10`-nel tér vissza, vagyis négy paramétere van (a főablak objektuma, 0, 0, 1). A veremeltolásokat a függvényen belül ellenőriztem: a második paraméter az `0x0065b84b` vizsgálata (0 → kimarad a `[eax+0x166] := 1`), a harmadik a `0x0065b8f9` vizsgálata (0 → ugrás a `0x0065b98e`-re, vagyis kimarad a „változatlan keresőszöveg” korai kilépés), a negyedik a `0x0065bb12`-nél a `0x00662b20` második paramétere.
- **Mit csinál.** A `0x0065b840` a keresősáv kezelője (sztringjei: `searchcontainer/searchbutton`, `searchcontainer/searchclr`): a szövegtörlő gombot a keresőszöveg meglététől függően mutatja vagy rejti (`0x0065b8f7`, virtuális hívás `+0x68`/`+0x6c`), a szöveget a `[ebp+0xde4]` mezőbe teszi, üres szövegnél `[ebp+0xe94] := -1` (`0x0065ba4d`), és **minden úton** meghívja a keresés végrehajtóját, a `0x00662b20`-at (`0x0065bb1b`), kényszerített (negyedik paraméter 1) módban.
- **A `0x00662b20` (3202 bájt)** a keresés végrehajtása: sztringjei `Search results for "%s"`, `No matches`, `Displaying %s %s in %s %s (%0.3f seconds)`, `CThumbUI::searchdisplay`, `CThumbUI::sresults` és társaik; több mint harminc közvetlen hívottja van; egyetlen hívója a `0x0065b840`. **Az eredeti OK után tehát a főablak újrafuttatja a jelenlegi keresést vagy nézetet** (az eredményfejléc szövegeivel együtt), nem csupán „frissít”.
- **Nálunk (ellenőrizve):** `folder_manager_save_controller.py:116-119`, a `_finish_folder_manager_save` a `_reload()`-ot hívja és jelez (`statusChanged`); a mentés `finally` ágában mindig lefut (`folder_manager_save.py:157-159`). A kényszerített újrafuttatás és az újratöltés fajtája azonos.
- **Ami a binárisból nem olvasható ki:** a látható részletek (a bal hasáb kinyitott ágai, a rács görgetési helye, a kijelölés megmaradása, az eredményfejléc és az állapotsor szövege az OK utáni másodpercekben). Ezek a `0x00662b20` és több mint harminc hívottja futásidejű viselkedésén múlnak, utasításszintű olvasással nem dönthetők el megbízhatóan.
- **Mérés, ami eldönti (az egyetlen megmaradó):** `Colab-feladat kell: a főablak teljes képe a Mappakezelő OK előtt és után az eredeti Picasa 3.9-en (Wine), tiszta profillal a mintakönyvtáron. Lépések: (1) a bal hasábban egy többképes mappa kijelölése és a rácsban három kép kijelölése, képkocka; (2) Eszközök ▸ Mappakezelő, egy másik mappán „Scan Always”, OK, képkockák 1, 5 és 30 másodperc múlva (bal hasáb, rács, kijelölés, görgetés, fejléc, állapotsor); (3) ugyanez „Scan Once” esettel; (4) ugyanez „Remove from Picasa” esettel; (5) kontrollként Mégse. Minden esetben a `watchedfolders.txt`, `scanlist.txt`, `frexcludefolders.txt` módosítási ideje és tartalmi kivonata az OK után azonnal, majd a Picasa leállítása után (ez a 2. pont leállítási időzítését is igazolja). Egy feladat 1-3 perc, modell nélkül fut (`colab_felmero.py futtat`). [a jegy egyetlen blokkolója]`
- **A mérés mellékterméke:** a megnyitáskor látható rádióállapot ellenőrzése egy figyelt, egy egyszer beolvasott és egy kizárt mappán (a leképezés binárisból megvan: `picasa-mappakezelo.md` 5.2/b, 5.4, `0x007c60d0`, `0x007c5ef0`; a futásidejű összevetés nem blokkoló).

#### 7. A megmaradt tételek egyenként

| Tétel (a „Nyitott” listából és a táblázatból) | Döntés |
|---|---|
| `Ghidra-kör kell: 0x006a2a60` | LEZÁRVA: a rekesz-eltolás tévedés volt, a megfigyelő célja `0x0055ff70` → `0x00419240`, fájlt nem ír (1. pont) |
| `scanlist.txt` OK-kori írása | LEZÁRVA: az OK nem írja, a beolvasó leállításakor frissül (2. pont); a mi korai írásunk szándékos eltérés |
| `.picasa.ini`-hatás (arckizárás) | LEZÁRVA, erős: közvetlenül nem ír `.picasa.ini`-t (3. pont) |
| további belépőutak | LEZÁRVA, erős: pontosan két menübelépő (5. pont) |
| ablakméret és helyzet megőrzése | LEZÁRVA: nem őrzi, nálunk sem (3. pont) |
| ismétlődő mappa | LEZÁRVA: az OK átugorja a már figyelt mappát (3. pont) |
| írásvédett profil, elérhetetlen megosztás | LEZÁRVA: az eredeti néma, nálunk hibasáv (4. pont, szándékos eltérés) |
| OK utáni visszavonás | LEZÁRVA: az eredetiben nincs (3. pont) |
| megszakítás | LEZÁRVA: nincs megszakító vezérlő (3. pont) |
| OK és Mégse határa | LEZÁRVA (7.1 szakasz és a fenti táblázat) |
| rádióállapot megnyitáskor | LEZÁRVA a binárisból (5.2/b, 5.4); a futásidejű összevetés a 6. pont mérésének mellékterméke, nem blokkoló |
| bal hasáb, rács, kijelölés, állapotsor az OK után | **NYÍLT**: a 6. pont egyetlen mérése (Colab-feladat) |
| leválasztott hálózati meghajtó megjelenése és kinyitása | KIVITT a #6391 jegyhez, ahol saját jegytörzse és külön futásidejű mérése van (`picasa-mappakezelo.md` 13.4/a és 13.9); nem az OK-út kérdése, a #7082-t nem blokkolja |
| a `0x004f54b0` virtuális hívója, az `app+0x48` `+0xec` rekesz célja | NEM BLOKKOLÓ, látható viselkedést nem érint: az első csak a mentés időpontját, a második legfeljebb egy lista elem frissítését dönthetné el (1. és 2. pont) |

Nyitott kérdések: 1 nyílt (megnevezett, felvehető Colab-feladat, a jegy egyetlen blokkolója) · 11 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva; a #6391-be kivitt, már nyilvántartott: 1 (a hálózati meghajtó megjelenése); a látható viselkedést nem érintő, nem blokkoló, e körben talált: 2 (a `0x004f54b0` hívója, az `app+0x48` rekesz célja).

### Zárási döntés

**A #7082 kutatási jegy egyetlen mérés nélkül nem zárható; blokkoló ez az egy:** a főablak látható állapota a Mappakezelő OK után (Zárókör 6. pont), amelyet egyetlen Colab-felvétel dönt el (a feladat leírása a 6. pontban van, a hívó adja fel). Minden más tétel lezárult (11 lezárva, 0 blokkolt, 0 csak-nyitva); a hálózati meghajtó kérdése a #6391 jegyen él (saját jegytörzzsel), a két e körben talált, látható hatás nélküli tétel nem blokkoló.

Ha a felvétel a bal hasábban, a rácson, a kijelölésben és az állapotsorban az `_reload()` útjával azonos képet mutat, a jegy ugyanazzal a mozdulattal zárható, fejlesztői teendő nincs. Ha eltérést mutat, a fejlesztői jegytörzs a „Javasolt jegytörzs-bővítés” sablonja szerint készül (Eredeti: a mért képkocka és a `0x0065b840` → `0x00662b20` út; Nálunk: `folder_manager_save_controller.py:116-119`; Teendő: a mért különbséget szűken kijavítani; Kész, ha: az előtte/utána képkocka-pár egyezik).

**Fejlesztői jegytörzs jelenleg nem marad,** mert a szakasz egyetlen bizonyított eltérése sem kér kódmódosítást:

- az OK-kori `scanlist.txt`-írás (a mi korai írásunk szándékos és előnyös, `picasa-mappakezelo.md` 17.5);
- az írási hiba jelzése (az eredeti néma, nálunk hibasáv, az #1207 tanulságából szándékosan);
- a figyelt mappákra adott megerősítés (ADR-005) és a rövid helyi súgó, amelyeket a fenti táblázat már szándékos eltérésként rögzít.

**Helyesbítések a korábbi szövegre (a régi szöveg érintetlen, a helyesbítések itt vannak):** a „Nyitott” első sora és a „Cáfoló kísérlet” utolsó bekezdése a `0x0055ff50` rekeszre épített láncot állította, ez téves (Zárókör 1. pont); a „Nálunk” oszlop több hivatkozásának sorszáma elavult (Zárókör 5. pont, utolsó pont); a „Nyitott” harmadik sorában említett hálózati út a #6391 hatóköre; a `picasa-mappakezelo.md` 17.2 szakaszának „kizárólag a 0x004f54b0 és a 0x004183c0 felől hívódik” mondata pontosítandó: az olvasót a `0x004183c0`, az írót csak a `0x004f54b0` hívja, és az utóbbi a beolvasó leállítási mentése (a hívó vezesse át).

### Mért eredmény (#7163, 2026-11-18)

#### Következtetés

Az eredeti Picasa 3.9-ben a Scan Always és Scan Once OK-ja nem változtatja meg a főablakot, ha a megadott mappa nem tartalmaz új képet; egy másik, megjelenített mappa eltávolítása viszont azonnal kiveszi a sort és a szakaszt, miközben a kijelölt mappa, a három kép kijelölése, az állapotsor és a rács képpontbeli görgetési helye megmarad (a rövidülő tartalom a végén természetesen korlátozhatja az eltolást). Ha a képek visszakerülnek az indexbe, a szakasz ugrás nélkül tér vissza. PicasaPy ugyanezeket a kijelöléseket és a lista tartalmi frissítését megtartja, de a Mappakezelő OK-ja a rácsot a kijelölt mappa szakaszának elejére görgeti; ez az egy igazolt, fejlesztői teendőt indokló eltérés.

#### Bizonyítottsági fok

**Megerősített** a görgetési eltérésre, a kijelölés megmaradására és a Remove lista-hatására: az eredeti oldalt a #712-#717 mérési esetek, a PicasaPy oldalt a teljes OK→újratöltés→QML-görgetés kódút igazolja. A mérőadat-archívumban nincs benne a hivatkozott képkocka vagy videó, ezért a feladatban megadott mérési leírásra és fájlazonosítókra támaszkodom; a nyers képeket nem ellenőriztem újra. Az eredeti bináris lánca külön, utasításszintű bizonyíték.

#### Bizonyíték

| Állítás | Eredeti Picasa 3.9 | PicasaPy (forráskód) |
|---|---|---|
| Scan Always OK után, kép nélküli mappán a főablak 45 másodpercig képpontra azonos. | mérés (#712, `kepernyo__10` ↔ `kepernyo__23-29`, `video__21.mp4`) | A mentési callback `_reload()`-ot hív; a folder-módú újratöltés alapértelmezetten újraaktiválja a mappát, ezért a QML `folderActivated` jelet kap (`folder_manager_save_controller.py:116-119`, `controller_sync_mixin.py:169-207`). |
| Scan Once OK után a rács, a kijelölés, a bal hasáb és az állapotsor változatlan marad. | mérés (#713, `kepernyo__11` ↔ `kepernyo__24-30`) | A kijelölt képsorok azonosító alapján állnak vissza (`MainWindowCommands.qml:81-96`); a bal hasáb kijelölt útvonala a `currentFolder` (`MainFolderPane.qml:41`, `FolderPaneTreeRow.qml:49-51`). A három kijelölt képnél az alsó sáv kijelölés-összesítést mutat (`TrayInfoBar.qml:121-130`). |
| Másik megjelenített mappa Remove-ja bezárás előtt kiveszi a sort és szakaszt, csökkenti a mappaszámot; a kijelölés, a kijelölt mappa, az állapotsor és a görgetési eltolás megmarad. | mérés (#714-#715, `kepernyo__24-30`, `j714/v/f_011.png`) | A Remove törli a gyökeret az indexből és újratölt (`library_controller_folders.py:472-495`, figyelt gyökérnél `:498-531`); a mentési út is újratölt a dialógus bezárása előtt (`FolderManagerDialog.qml:107-129`). A mappalista új soraiból eltűnik a célmappa (`controller_sync_mixin.py:186-194`). A görgetés viszont a kijelölt szakasz elejére ugrik (lásd alább). |
| A Scan Always visszavétele után a szakasz és a sor visszatér ugrás nélkül, a kijelölés megmarad; rövid „Picasa Notifier” értesítés látható, folyamatjelző nincs. | mérés (#717, `kepernyo__37-41`, `video__35.mp4`); az értesítés csak megfigyelés, nem elvárás | A scan befejezésének görgetésmegőrző útja létezik (`controller_sync_mixin.py:146-155`), de a Mappakezelő OK gombjának saját újratöltése előtte a mappa elejére görget. A PicasaPy kék háttérmunka-hulláma meglévő, szándékos saját UX-kiegészítés (#70; `TrayInfoBar.qml:13-16`, `docs/decisions/vedett-sajat-funkciok.md:134-138`), nem új paritási jegy. |
| Mégse után a főablak változatlan. | mérés (#716, `kepernyo__11` ↔ `kepernyo__24-30`) | A Mégse visszaállítja a piszkozatot és bezárja a dialógust, mentést nem indít (`FolderManagerDialog.qml:78-80, 336, 481`). |
| `watchedfolders.txt` módosítási ideje minden OK-kor az OK másodpercére változik, tartalomváltozás nélkül is. | mérés (#712, #715) | PicasaPy minden mentésnél kiírja (`folder_manager_save_controller.py:93-99`, `folder_manager_save.py:148-159`). |
| A Scan Once-nál megfigyelt `frexcludefolders.txt` tartalma `C:\Users\felhasznalo\Pictures\Picasa\`; a `scanlist.txt` `+C:\` sora a teljes adatbázis-kiírással együtt jelent meg. | mérés (#713, #714, #716, #717) | A `+` befoglaló gyökeret jelöl (`picasa-mappakezelo.md:1292-1328`); a mérés időbeli együttállása önmagában nem írót bizonyít. A már feltárt bináris út szerint a Mappakezelő közvetlen OK-lánca nem írja a `scanlist.txt`-t; a leállítási író és az OK-út különbségét a `picasa-mappakezelo.md:2930-2935` és e szakasz korábbi záróköre rögzíti. Nálunk az állapotváltó `setFolderManagerState` írja a fájlt (`library_controller_folders.py:104-133`); a különbség a korábbi specifikációban tudatos eltérésként szerepel (`picasa-mappakezelo.md:2963-2979`). |

#### A két független út

- **A - eredeti mérés:** a #712-#717 Colab-felvételek a Picasa 3.9 futásidejű képernyőjét és a fájlok időbélyegeit rögzítik. Ezek szerint a Remove megőrzi a képpontbeli görgetést.
- **B - PicasaPy kódút:** a `FolderManagerDialog.qml:107-125` a Remove-ot a mentési zárójelen belül hajtja végre; a `folder_manager_save_controller.py:116-119` végül argumentum nélküli `_reload()`-ot hív. A `_reload` alapértéke `preserve_scroll=False` (`controller_sync_mixin.py:169-170`), és folder-módban `selectFolder(self._current_folder)`-re jut (`:195-207`). A `selectFolder` `folderActivated`-et bocsát ki (`controller.py:328-336`); a `LightboxFeed.qml:549-558` ezt `positionViewAtIndex(i, ListView.Beginning)` hívással, vagyis a csoport elejére görgetéssel kezeli (`:560-569`).
- **Egyezés:** a két út a görgetésre eltér, tehát egy fejlesztői jegyet indokol; a kiválasztott képek és mappa megtartására, illetve a Remove utáni sor-/szakaszfrissítésre egyezik.

#### Cáfoló kísérlet

Megpróbáltam cáfolni, hogy az OK minden esetben a szakasz elejére görget: megkerestem az összes `_reload()`-hívót és a `preserve_scroll` alternatívát. Háttér-szinkron és újraszinkronizálás valóban hív `preserve_scroll=True`-t (`controller_sync_mixin.py:143,151,167`, `library_controller_activity.py:100`, `library_controller_resync.py:135`), de a Mappakezelő záró callbackje egyiket sem használja; a Remove közben előforduló `removeFolder` és `removeWatchedFolder` újratöltései szintén alapértelmezettek (`library_controller_folders.py:495,531`). A cáfolatot ugyanezekkel a fájl- és sorszintű hivatkozásokkal ellenőriztem; a görgetési eltérés fennmarad.

#### A jegy „Kész, ha” pontjai

- ✅ Scan Always, kép nélküli mappán: az eredeti főablak változatlan marad 45 másodpercig (#712).
- ✅ Scan Once, kép nélküli mappán: az eredeti rács, kijelölés, bal hasáb és állapotsor változatlan (#713).
- ✅ Másik megjelenített mappa Remove-ja: az eredeti sor/szakasz azonnal eltűnik és a mappaszám csökken; kijelölés, állapotsor és görgetési eltolás megmarad (#714-#715).
- ✅ Scan Always után újra megjelenő képek: az eredeti sor/szakasz ugrás nélkül tér vissza; Cancel-kontroll nem változtat a főablakon (#716-#717).
- ✅ Az eredmény bekerült ebbe a #7082 szakaszba; a görgetési eltéréshez egy külön, teljes fejlesztői jegytörzs következik. A fájltartalom és a rendes leállítás utáni állapot nem teljesült, ezeket nyitva hagyom.

#### Javasolt fejlesztői jegytörzs

##### A Mappakezelő OK-ja tartsa meg a rács görgetési helyét

**Eredeti:** A #7163 mérése (#712-#717) szerint a Picasa 3.9-ben a Scan Always/Scan Once OK nem mozdítja el a főablakot kép nélküli mappa esetén; másik megjelenített mappa Remove-ja után a rács képpontbeli eltolása megmarad (a rövidebb lista a végén korlátozhatja), és Scan Always újraindexelésekor az új szakasz ugrás nélkül jelenik meg. Az eredeti OK-lánc: `0x005cf535` → `0x0065b840` → `0x00662b20`; az első hívás a `0x005cf52e-0x005cf535` utasításokban a kényszerítő `1` argumentummal látszik, a végrehajtó hívása `0x0065bb12-0x0065bb1b`. Bizonyíték: #712-#717 képkockák és videók; a lánc utasításszinten a helyi `annot_disasm.py` kimenetével ellenőrizve.

**Nálunk:** `folder_manager_save_controller.py:116-119` a mentés végén `_reload()`-ot hív; a `controller_sync_mixin.py:169-207` alapértelmezett folder-ágán ez `selectFolder(currentFolder)`, majd `folderActivated`. A `LightboxFeed.qml:549-558, 560-569` a csoport elejére görget. A Remove-ot végző `removeFolder`/`removeWatchedFolder` közben is lefuthat ilyen alapértelmezett újratöltés (`library_controller_folders.py:472-495, 498-531`), még a záró callback előtt. A kijelölt képeket és mappát a jelenlegi kód megtartja; ezt a jegy nem változtathatja meg.

**Teendő:** a Mappakezelő OK-zárójelen belül a Remove ne végezzen köztes, görgetést visszaállító nézetfrissítést; a végső frissítés őrizze meg a rács aktuális görgetési helyét, és ne bocsásson ki olyan mappaaktiválást, amely a kijelölt csoport elejére ugrik. A közvetlen, Mappakezelőn kívüli Remove út viselkedése maradjon külön kezelve.

**Kész, ha:**

- Mappakezelő OK után, másik kép nélküli mappán Scan Always és Scan Once esetén a kiválasztott mappa, a három kijelölt kép és a rács görgetési helye változatlan marad az 1/5/30 másodperces ellenőrzéskor.
- Másik megjelenített mappa Remove-ja után a sor/szakasz eltűnik és a darabszám csökken, miközben a kiválasztott mappa, képek, állapotsor és a görgetési eltolás megmarad; csak a rövidebb tartalom által kikényszerített végpozíció-korlát alkalmazható.
- Ha a Scan Always új képeket indexel, az új mappaszakasz megjelenik úgy, hogy a meglévő nézetpozíció és kijelölés megmarad.
- A Mappakezelő Cancel továbbra sem írja át a nézetet.

#### Új kutatási jegyjavaslatok

- **A Mappakezelő fájljainak tartalma és rendes kilépés utáni állapota** - pontosan mi van a `watchedfolders.txt` és `frexcludefolders.txt` fájlban Scan Once, Remove, Cancel és visszakeresés után, illetve milyen a Scan Always/Once fájlállapota rendes kilépés után? Keresd a #712-#717 Colab-kimenetekben; ha a fájl eltűnése miatt nem gyűjthető ki, javítsd célzottan a végrehajtó kimenetgyűjtését vagy indíts külön mintamérést.
- **A kijelölt mappa eltávolítása** - mit mutat az eredeti Picasa, ha a Remove az aktuálisan kijelölt mappát vagy a kijelölt képeket tartalmazó mappát éri? Keresd egy külön Colab-mérésben, mert a #714-#715 másik, nem kijelölt mappát távolított el.
- **Első beolvasás még nem indexelt képekkel** - mikor jelenik meg az új mappaszakasz Scan Always és Scan Once esetén? Keresd olyan Colab-mintakönyvtárban, amelynek képei a beolvasás előtt még nincsenek az indexben.

#### Nyitott

- `watchedfolders.txt` és `frexcludefolders.txt` pontos tartalma Scan Once, Remove, Cancel és visszakeresés után: **NINCS MEG**; a #712-#717 nyers kimenet hiányzik a helyi archívumból, a felsorolt Colab-eredmények vagy új célzott mérés szükséges.
- Scan Always és Scan Once rendes Picasa-kilépés utáni fájlállapota: **NINCS MEG**; a mérési csomagban rendes kilépés csak a Cancel-kontrollnál történt.
- Még nem indexelt képeket tartalmazó mappa első Scan Always/Once beolvasásának látható eredménye: **NINCS MEG**; a megadott mintában ilyen eset nem volt.
- Az aktuálisan kijelölt mappa, illetve a kijelölt képeket tartalmazó mappa Remove-ja: **NINCS MEG**; külön eredeti-Picasa mérés szükséges.
- A képkockák videó szerinti pontos időrendje és a „Picasa Notifier” pontos megjelenési hossza: **NINCS MEG** helyben; a videók hiányoznak az archívumból. Az értesítés rövid megjelenése csak megfigyelés, nem elvárás.
- A `scanlist.txt` `+` előtagjának jelentése és a Mappakezelő közvetlen OK-útjának írása nem marad nyitva: a `+` befoglaló gyökeret jelöl (`picasa-mappakezelo.md:1292-1328`), az OK közvetlen lánca nem hívja a fájlírót (`:2930-2935`; e lap korábbi záróköre).

## #7266: A 2026-11-19-i dekompilálás nyitott kérdései

Forrás: a privát kutatási tár 2026-11-19-koteg-496-517.txt állományának címzett blokkjai; az érintett, korábban nyitott útvonalakhoz az itt hivatkozott spec-szakaszok és a helyi, címre korlátozott Capstone-diszasszembly. A dekompiláció önmagában nem old fel minden mezőnevet és eseménycélpontot.

| # | Bizonyított válasz vagy nyitott kérdés; következő cím |
|---|---|
| 496 · 0x009eb290 | A 0x009eb290-ben nincs közvetlen 0x0132-vizsgálat. A 0x009f05c0 az 0x1c kulcs hiányakor 9-et ad; a dátum-munkaszál hash-táblájába csak a 0x37 kulcs kerül. Emiatt a 0x0098bc10 és a 0x00ab35e0 nem fut, de a függvény a temp-kimeneti ág felé folytatja. Ez megmagyarázza a fájlidő-segéd kihagyását, nem a #7154 változatlan EXIF-fájlját. Következő: 0x009ed330, 0x009eb820, 0x009ec530. |
| 497 · 0x004b0190 | A 0x00744ee0 kevesebb mint két kijelölt kép esetén a 0x004133e0 vektort inicializálja, a 0x004b0190 album- és mappatároló-iterátorokat köt, majd a 0x006cab20-at hívja. Utóbbi a kapott vektort bemeneti sorrendben járja. Nem bizonyított, hogy az bejáróforrás a teljes album minden képét beveszi, vagy mi adja a forrás sorrendjét. Következő: a 0x004b0190 által meghívott, objektum vtable +0x2c célja és a vektor előállítója. |
| 498 · 0x005cb180 | Ha a külső objektum +0xeac mutatója nem nulla, a függvény a belső objektum +0x3c0 dwordjét adja vissza, máskülönben -1-et. A hívók az értéket azonosítóként használják, de a mappa-/albumazonosító-fajta és a mező írója nincs meg. Következő: a +0x3c0 mező írójának megkeresése mezőhivatkozás-vizsgálattal; a 0x005cb990 már dekompilált és nem kérendő újra. |
| 499 · 0x00d67904 | Ez adatcím. A 0x00745770 innen, a +0x20 indítóhelyen indítja a CPrintJobThread példányt. A CPrintJobThread saját vtáblájában a +0x20 cél 0x00709430, amely azonnal nullával tér vissza; a munkát végző +0x2c cél 0x007434d0 a +0x60 listát járja. Ez a 0x00777470-et hívja; annak további 0x007774b0 és 0x00861bb0 hívásainál nincs meg a videó-/hiányzófájl-szűrő. Következő: 0x007774b0, 0x00861bb0. |
| 500 · 0x005d78d0 | A közvetlen törzs tab- és effektpanel-állapotot frissít; közvetlen nyomtatópanel- vagy kijelölésírás nincs. A közvetett út a 0x005d7680 effektfrissítő dinamikus hívásain múlhat. Következő: 0x005d7680 és az ott használt cél-vtábla. |
| 501 · 0x00571e50 | A függvény a CThumbUI vtábla +0x74 helye, mutatótáblacím 0x00c905a0. A +0x375 jelző 0 esetén 1000-et, máskülönben 10-et ad; korábbi felület-ellenőrzésnél 100-at adhat. A léptető eseménykezelő és az utolsó képnél a visszatérés fogyasztása nyitott. Következő: a CThumbUI +0x74 virtuális hívójának feloldása a 0x00c905a0 slot használati útján. |
| 502 · 0x00781680 | Lezárva. A 0x0071b810 csak sikeres 0x00717420 után, érvényes indexű és nem nulla elem mellett fut, ha a +0x5a és +0x5b is nulla. Új elemnél, ha +0x5d nem 1 és +0x5a nulla, előbb +0x59 := 1, majd +0x5d := 1 történik. A jelzők szemantikai neve nem szükséges a kért hívási feltételhez. |
| 503 · 0x0075de50 | A 0x00717420, 0x00717560 és 0x00717d10 memóriabeli diavetítő-elemeket gyűjt és állapotjelzőket vizsgál; fájlt nem nyit és sérült/hiányzó/elérhetetlen képet nem osztályoz. A hiba felismerő út a diavetítő-objektum vtable +0xb8 elemlekérő/betöltő célja mögött van. Következő: az adott vtable +0xb8 céljának azonosítása. |
| 504 · 0x009a3db0 | A 0x009a3db0 könyvtárat hoz létre, nem enumerál. A 0x009a5fa0 *.* mintával hívja a Win32 első/következő fájl keresést, az alkönyvtárakba rekurzívan halad, és csak a vtable +0x20 visszahívás 0 eredményénél fűz elemet a listához. Ebben nincs .mp3 teszt vagy rendezés; a felsorolás a Win32 találati sorrendjét tartja, de a végső lejátszási sorrendhez a lista további útja is kell. A visszahívás szűrője és a default út összetevői nyitottak; nálunk controller_slideshow_mixin.py:176-194 .mp3-ra szűr és fájlnév szerint rendez. Következő: 0x009a38a0, valamint az objektum vtable +0x20 céljának feloldása. |
| 505 · 0x0075d430 | Lezárva. A zenelista aktuális pozícióját növeli, lista-végen 0-ra fordítja, majd az aktuális útvonalat adja lejátszásra a 0x0075d1c0 útján. Ez külön áll a képlistát ismétlő jelzőtől. A PicasaPy SlideshowMusic.qml:30-36 modulo-léptetése egyezik. |
| 506 · 0x0057ec70 | Lezárva a kért szerep szintjén. A rutin az első dwordöt, a refcountolt sztringet és a 0x0057ed00-val a részrekordot másolja. A 0x00600ac0 a 0x00660c80 által összeállított keresési, szűrő-, nézet- és kijelölési pillanatképet teszi a +0x32b0 mezőbe albumtagság-változtatáskor. A részrekord összes mezőjéhez a 0x0057ed00 külön vizsgálata kell. |
| 507 · 0x004d9aa0 | A 0x0041c340, 0x00439a80 és 0x00449090 hívók ismert paramétereket adnak át, de a tokenekhez használt összes fájlmező nincs azonosítva. A 0x00456610 a captiont egészben a +0x50 callbackre, a keywords vesszőtagjait a +0x5c callbackre adja; a rating, hidden és screensaver külön tokenút. Következő: e hívók objektumainak +0x2c, +0x50 és +0x5c vtable-céljai. |
| 508 · 0x00476ec0 | A 0x00476ec0 látható ágai 0-val térnek vissza. A 0x00462ba0 dekompilált aláírása void, a 0x00477210 mégis 0/1 állapotot képez a hívás után, ezért a másolási kód jelentése nem állapítható meg ebből. A 0x004082f0 öt sztringmezőt ürít üres bemenetnél, de az Undo-Save argumentumok szerepe nyitott. Következő: 0x00477210, 0x004082f0 és a kimeneti mezők írói. |
| 509 · 0x005ef3e0 | A pozitív sztringhivatkozás a 0x119 / IDS_CONFIRM_REDEYE_REVERT fogyasztóját a 0x00752ae0 címre vezeti. Az Undo All többképes út az IDS_CONFIRMREVERT_MULTIPLE szöveget használja, majd elemenként a 0x005ef6b0-et hívja. A hibaút 0x005f3e10 és 0x0046d7d0 felé megy, de a hibajelzés helye nyitott. Következő: 0x00752ae0 törzse; a hibaút dinamikus célja a 0x0046d7d0 környezetében. |
| 510 · 0x00467ca0 | A +0x18 mező 1/2/5 értékeinek tényleges írói és jelentése nincsenek meg. A korábban vizsgált 0x004e3ab0, 0x004e5070 és 0x004e40c0 más mezőműveleteket végez, nem azonosítja ezeket a kódokat. Következő: mezőírók felkutatása a +0x18 tageltolás írásainak indexfüggetlen vizsgálatával; a cím csak ezután kérhető dekompilálásra. |
| 511 · 0x0067f580 | A négy wrapper a 0x0076b110 szerkesztőmód-beállító útjához tartozik. A 0x0067f5a0, 0x0076b0c0 és 0x0076b0e0 függvénymutatói rendre 0x00ca6ce0, 0x00ca6ba4 és 0x00ca6b88 alatt találhatók. A kattintás, Enter, gépelés és kilépés események megfeleltetése a vezérlő callback-adata nélkül nyitott. Következő: a fenti adatcímekhez rendelt vezérlőesemény-rekordok és a 0x0076b110 hívói. |
| 512 · 0x009869a0 | A rutin a több-bájtos UTF-8 jelölés alapján halad, a vezető ASCII whitespace bájthosszát adja át a 0x00986120 részsztring-segédnek. A függvényben nincs maximumhossz-állandó; a záró whitespace vizsgálat nem bizonyít záróvágást, és a felsőbb korlát nincs meg. Következő: a feliratút 0x0067f2a0 hívójának bemeneti korlátja. |
| 513 · 0x0067eca0 | A Ctrl+V/C/X út explicit; a 0x0076ace0 nem mutat WM_UNDO ágat, az ismeretlen eseményt a 0x00a68c00 általános kezelőnek adja. A natív visszavonás célja ezután sem ismert. Következő: 0x00a68c00 és a natív szerkesztőmező eljárása. |
| 514 · 0x004a51f0 | Lezárva. A ]album: kulcs feloldása, a tagságlista tényleges megváltozása és a +0x3f8 listener jelenléte együtt váltja ki a listener vtable +0x8 slot hívását albumazonosítóval és tagsági adattal. A PicasaPy-paritás nem volt a kérdés része, és nem állapítható meg ebből a törzsből. |
| 515 · 0x009bef50 | A 0x009bd640 üres értékmutatónál törli a meglévő kulcssort, hiányzó kulcsnál nem szúr be sort. Típus-1 parancsnál a közvetlen cél a rekord +0x4 mezője; a tulajdonosi objektum jelentése nyitott. Következő: 0x009bd390 és a típus-1 rekord létrehozója. |
| 516 · 0x0065b840 | A mozgatás után a 0x0053f4a0 a [puVar10+0xa9] objektum +0x44 virtuális helyét hívja a mozgatott mappával, (1,1,0) paraméterekkel. A kijelölt mappa és a rács tartalma a címzett vftáblacél nélkül nyitott. Következő: a 0x0053f4a0 hívásban részt vevő objektum vftáblája és a +0x44 cél. |
| 517 · 0x006db4e0 | A Cancel út a 0x00849d00 takarítás után 0-val tér vissza, és nem hívja a 0x006db730 mentőutat. A 0x008496c0 a dialógus +0xc8, +0xcc, +0xcd és +0xd0 kezdeti mezőit állítja; az újranyitáskor visszatöltött mezőforrás nyitott. Következő: a 0x006dc030 +0x40 virtuális címzettje és a mezőket újranyitáskor betöltő modellút. |

### Bizonyítottság, cáfoló kör és fejlesztési döntés

**Bizonyítottsági fok: feltételes.** A közvetlen ágak, visszatérési értékek és vtable-slotok több kérdésnél rögzítettek. A 22 kérdés közül #502, #505, #506 és #514 a kért szinten lezárult; a többi nyitott mezőjelentésre, virtuális célra vagy futásidejű eredményre vár. Nincs bizonyított új PicasaPy-eltérés, amelyhez fejlesztési jegytörzs írható.

**A út:** a megadott Ghidra-kimenetek utasításágai és mezőműveletei, különösen a 0x009eb290, 0x009f05c0, 0x0098bc10, 0x009a5fa0, 0x00717420 és 0x009bd640. **B út:** független, címre szűkített diszasszembly, a dátum-munkaszál 0x37 kulcsbeírásának korábbi követése, pozitív xrefek, RTTI-slotok és a PicasaPy-forrás ellenőrzése. A #496 hiányzó kulcs miatti 9 visszatérését az A és B út egymástól függetlenül támasztja alá; a #499 slotcímeknél a RTTI és a célfüggvény diszasszemblye egyezik. A nyitott mezőnevekhez és dinamikus célokhoz nincs második, független feloldás.

**Cáfoló kísérlet (#496):** azt próbáltam cáfolni, hogy az EXIF `0x0132` jelenléte közvetlenül ágat vált vagy leállítja a fájlírót. A 0x009eb290 utasításmenetében nincs `0x0132` összehasonlítás. A hash-tábla beírásainak korábbi ellenőrzése csak a 0x37 kulcsot találta; a 0x009f05c0 mostani dekompilációja hiányzó kulcsra 9-et ad. Így a 0x0098bc10 és 0x00ab35e0 kimarad, miközben a függvény a későbbi temp-ágra lép. A cáfolat azt támasztja alá, hogy a 0x0132 nem állítja le közvetlenül az EXIF-írást; a #7154 minták későbbi hibapontját nem cáfolja, mert a tíz mérés nem rögzítette a munkaszál belépését, az előkészítő eredményét vagy a csere ágát.

**Fejlesztési jegytörzs:** jelenleg nem indokolt. A PicasaPy mp3-szűrője és névrendezése ismert, de az eredeti 0x009a5fa0 visszahívás szűrője és a lista későbbi feldolgozása nyitott. A nyomtatási szűrők, nyomtatási vektor teljessége és az albumtulajdonságok újranyitási értékei sem bizonyítottak. Nincs még megalapozott `Eredeti / Nálunk / Teendő` fejlesztési táblázat.

**Nyitott, új Ghidra-címek:**

- `Ghidra-kör kell: 0x009ed330 - a dátum-munkaszál hívóága belép-e a 0x009eb290 íróba a #7154 mintákon, és milyen eredményből következik a korai kilépés? [blokkoló]`
- `Ghidra-kör kell: 0x009eb820 - mely előkészítési hibaág akadályozhatja meg a temp-kimenetet? [blokkoló]`
- `Ghidra-kör kell: 0x009ec530 - milyen hibakódok és visszatérések akadályozzák a temp-kimenet és a fájlcsere befejezését? [blokkoló]`
- `Ghidra-kör kell: 0x007774b0 - hol és milyen feltételekkel szűri a nyomtatási út a videót vagy a hiányzó fájlt? [blokkoló]`
- `Ghidra-kör kell: 0x00861bb0 - milyen nyomtatási fájl- és képellenőrzéseket végez a rekordszintű feldolgozásban? [blokkoló]`
- `Ghidra-kör kell: 0x005d7680 - a panel-visszaállítás effektfrissítő útja okoz-e közvetett kijelölés- vagy nyomtatópanel-változást? [blokkoló]`
- `Ghidra-kör kell: 0x009a38a0 - mely abszolút mappaútvonal-összetevőket és sorrendet állítja elő az alapértelmezett MP3 útvonalhoz? [blokkoló]`
- `Ghidra-kör kell: 0x00477210 - milyen másolási eredményeket olvas és hogyan képez belőlük 0/1 állapotot? [blokkoló]`
- `Ghidra-kör kell: 0x004082f0 - milyen argumentumokkal hívja az Undo-Save az öt sztringmező ürítését, és mely mezők jelentenek másolási státuszt? [blokkoló]`
- `Ghidra-kör kell: 0x00752ae0 - hogyan fogyasztja a IDS_CONFIRM_REDEYE_REVERT sztringet, és melyik vörösszem-visszavonási eseményhez tartozik? [blokkoló]`
- `Ghidra-kör kell: 0x0067f2a0 - hol szab felső hosszkorlátot a felirat szerkesztési útja a 0x009869a0 meghívása előtt? [blokkoló]`
- `Ghidra-kör kell: 0x00a68c00 - hová továbbítja a szerkesztőmező a WM_UNDO eseményt? [blokkoló]`
- `Ghidra-kör kell: 0x009bd390 - milyen célobjektumot rendel a típus-1 INI parancs +0x4 mezőjéhez? [blokkoló]`

**Még nem kérhető Ghidra-cím:** #497, #498, #501, #503, #507, #510, #511, #516 és #517 esetén a következő vtable-cél vagy mezőíró címe nincs feloldva. A meglévő függvénytörzsek ismételt dekompilálása nem segítene; előbb a tároló visszahívása, a diavetítő-vtábla, a mezőírás vagy a vezérlőadat célját kell statikusan azonosítani. A már dekompilált címeket, köztük 0x00744ee0, 0x005cb990, 0x00717420, 0x00717d10, 0x00717560, 0x00462ba0, 0x005ef520, 0x005ef6b0, 0x004e3ab0, 0x004e5070, 0x004e40c0, 0x0076ace0, 0x009bd640, 0x006dc030 és 0x008496c0, nem kérem újra.

### Módosított fájlok

- docs/specs/paritas-ellenorzes.md: a 22 kérdés válasz-/következő-cím táblája; #496 fájlidő-jelölt és #517 régi Z4 állítás helyesbítése; slideshow, keresés, mappaáthelyezés és Album Properties kiegészítése.
- docs/specs/picasa-nyomtatas.md: #497-500 részleges válaszai és nyitott célcímek.
- docs/specs/picasa-beviteli-mezok.md: #508-513 revert, Undo, képaláírás és natív Undo útja.
- docs/specs/picasa-ini-format.md: #515 sorosítókérdés és nyitva maradó címek.
- docs/specs/picasa-keptalca.md: #514 albumtagság-értesítő feltétele és vtable-slotja.

## #7266 folytató kiegészítés: a 549-561-es köteg (2026-11-19)

Az alábbi táblázat a #7266 nyitva maradt 13 kérdésére ad választ. A „feltételes” jelölés azt jelenti, hogy a bináris ág vagy adatút olvasható, de a kérdés egy további futásidejű bemenetet, dinamikus címzettet vagy mezőjelentést kíván.

| Cím / kérdés | Válasz és bizonyítottság | Forrás / következő lépés |
|---|---|---|
| 0x009ed330 - belép-e az íróba a #7154 mintákon, milyen eredmény vált ki korai kilépést? | Feltételes: a munkaszál csak a local_54 == 2 ágon hívja a 0x009eb290-et. A nulla visszatérés a hívó sikerágára visz, a nem nulla eredmény a bejegyzés eltávolításához vezet. A #7154 minták local_54 értéke és az író tényleges meghívása nincs meg. | 2026-11-19-koteg-549-561.txt:1-63; 2026-11-11-6532-colab-9-hivok.txt:18801-18809. A 0x009ed39a körüli célzott diszasszembly megerősíti az EAX visszaadását. Következő: a #7154 eredeti munkaszálának bemeneti státuszát kell rögzíteni. |
| 0x009eb820 - mely előkészítési hiba gátolja a temp-kimenetet? | Feltételes: az előkészítő nem nulla eredménye azonnal visszatér a 0x009eb290-ből, még a ideiglenes kimeneti ág előtt. A függvény 2-t ad olvasási/seek/hibás szegmens esetén, 3-at a két bájtnál rövidebb szegmensre, 4-et érvénytelen bemenet/allokációs hiba esetén. | 2026-11-19-koteg-549-561.txt:66-437; 2026-11-19-koteg-496-517.txt:74-76. |
| 0x009ec530 - mely hibakódok gátolják az ideiglenes kimenet és a csere végét? | Feltételes: a 0x009ec530 nem nulla eredménye a 0x009eb290 hibakimenetére visz, a 0x00994400 cserehívás előtt. A látható közvetlen kódok 2 és 4; egyes ágak belső rutin eredményét adják tovább. | 2026-11-19-koteg-549-561.txt:440-821; 2026-11-19-koteg-496-517.txt:195-205, 232-240. |
| 0x007774b0 - hol szűri a videót vagy hiányzó fájlt? | Feltételes: a 0x007774b0 rekordot és nyomtatási elrendezést kezel, speciális +0x1c == 0x10 és +0xfc == 0 feltételekkel hív nyomtatósegédeket. E törzsben nincs fájllétezés- vagy videófeltétel. | 2026-11-19-koteg-549-561.txt:824-914. Következő: 0x008623c0 képrajzoló út, illetve a 0x00777470 hívás utáni dinamikus rajzolóhely. |
| 0x00861bb0 - milyen fájl- és képellenőrzést végez a rekordszintű feldolgozás? | Feltételes: StartDocA után végigjárja a feladatcsoportokat, rekordokat ad a 0x00861f50-nek, majd oldalakat a 0x00862000-nek. Rajzolási hiba esetén AbortDoc; sikeres oldalak után EndDoc. Közvetlen fájlút- vagy képfájl-létezés-ellenőrzés nincs ebben a törzsben. | 2026-11-19-koteg-549-561.txt:917-1110. Következő: 0x008623c0. |
| 0x005d7680 - okoz-e az effektfrissítő közvetett kijelölés- vagy nyomtatópanel-változást? | Válasz: a vizsgált hívási láncban nem. A rutin a ytButtonNode +0x213/+0x244 mezőit írja; a 0x00409f50 geometriarekordot hasonlít, a 0x0040a050 ugyanilyen rekordot másol. E láncban nincs kijelölés- vagy nyomtatópanel-írás. | 2026-11-19-koteg-549-561.txt:1113-1174; bináris 0x00409f50 és 0x0040a050. |
| 0x009a38a0 - hogyan áll elő az alapértelmezett MP3 útvonal és enumeráció? | Feltételes: üres Preferences\MP3SlideshowPath esetén a hívó sorrendje 0x00980ec0(0) → 0x009a38a0 → 0x009a3db0, végül a kapott lista a +0x48 mezőbe kerül. A mappanevek és abszolút útvonal-összetevők nem dőltek el. | 2026-11-19-koteg-549-561.txt:1177-1247; 2026-11-16-koteg-438-465.txt:4806-4854; 2026-11-19-koteg-496-517.txt:2995-3066. Következő: 0x00980ec0 és 0x009a3930 dekompilációja. |
| 0x00477210 - milyen másolási eredményt képez 0/1 állapottá? | Feltételes: a 0x00462ba0 visszatérési értékéből a 0x00477210 a (eredmény == 0) kifejezést adja át a 0x00476ec0-nek, tehát 0 → 1, bármely nem nulla → 0. A 0x00462ba0 gépi kódja közvetlenül 2, 3 és 9 értékkel is tér vissza, illetve egy belső nem nulla eredményt adhat tovább; ezek üzleti jelentése nincs azonosítva. | 2026-11-19-koteg-549-561.txt:1250-1301; bináris 0x00462ba0: 0x00462bda, 0x00462ca9, 0x004631b2, 0x00462c32. Következő: 0x004edf60 visszatérési jelentése. |
| 0x004082f0 - Undo-Save paraméterei és másolási állapotmezők? | Feltételes: üres EAX bemenetnél az EDI-ben kapott rekordbázis 0, 0x208, 0x410, 0x618 és 0x820 sztringmezőit üríti; nem üres bemenetnél a 0x009a34a0 segédhez fordul. Ezek nem bizonyított másolási státuszmezők. A külön visszavonhatósági állapotot a 0x00476ec0 a +0x18f4 alapértékben és a +0x18f0 mögötti indexelt bájtokban tárolja. | 2026-11-19-koteg-549-561.txt:1420-1531; 2026-11-19-koteg-496-517.txt:3617-3650; bináris 0x0046d7d0 hívása 0x004082f0-nek. |
| 0x00752ae0 - fogyasztja-e az IDS_CONFIRM_REDEYE_REVERT-et? | Feltételes: a redeye műveletág nem a 0x119 azonosítót kéri, hanem 0x11b / IDS_CONFIRM_UNDO_REDEYE-et; ez az egy vörösszem-visszavonás megerősítése. A 0x119 tényleges fogyasztója nincs meg. | 2026-11-19-koteg-549-561.txt:1534-1908, különösen 1748-1779. Memóriakapus paszta.py-pásztázás: 150 közvetlen 0x009ae710 hívás előtt az előző legfeljebb 12 utasítás között nincs 0x119 operandus; ez a minta nem zárja ki a távolabbról/regiszteren át feladást. Következő: 0x009ae710 híváshelyein az argumentumok adatútjának vizsgálata. |
| 0x0067f2a0 - hol szab felső hosszkorlátot a feliratút? | Feltételes: a 0x0067f2a0 a bemeneti sztringet közvetlenül a 0x009869a0-nek adja, és ebben a törzsben nincs felső hosszkorlát. A 0x0067eca0 már ismert hívójában a másolás/beillesztés ág sem mutat ilyen felső korlátot; a másik két közvetlen hívó korláta nyitott. | 2026-11-19-koteg-549-561.txt:1911-1953; 2026-11-19-koteg-496-517.txt:8546-8750. Következő: 0x00565cf0 és 0x00568010 bemeneti előkészítése. |
| 0x00a68c00 - hová jut a WM_UNDO? | Feltételes: a 0x00a68c00 a 0x15 típusú belső eseményt külön kezeli; más eseményt a 0x009e3c70-nek továbbít. A típus nincs Win32 WM_UNDO-hoz kötve, így a natív üzenet címzettje nem állapítható meg ebből. | 2026-11-19-koteg-549-561.txt:1956-1985; 2026-11-19-koteg-496-517.txt:8633-8641. Következő: 0x009e3c70 esemény/üzenet-kezelő útja. |
| 0x009bd390 - mi a típus-1 rekord +0x4 célja? | Feltételes: a 0x009bf000 a +0x4 szövegobjektumot a 0x009bd640 második argumentumaként adja tovább; ez a módosítandó INI-szekció neve. A dokumentumot/sorosítóobjektumot az első argumentum külön adja. A parancsrekordot létrehozó magasabb szintű forrás nyitott. | 2026-11-19-koteg-549-561.txt:1988-2059; 2026-11-19-koteg-521-548.txt:10180-10225; bináris 0x009bf000. Következő: 0x0099b710 rekord-előállító. |

**Eltérésdöntés:** nincs bizonyított új Eredeti/Nálunk viselkedéspár. A nyitott print-szűrő, a feloldatlan abszolút MP3-alapút és a 0x119 erőforrás-fogyasztó nem alapoz meg fejlesztési jegytörzset.
