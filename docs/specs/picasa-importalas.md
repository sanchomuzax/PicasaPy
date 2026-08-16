# Az importálás panelje (Acquire)

Az importálás felületét az **`acquirepanel.tre`** írja le, a szövegeit az
**`acquirepanel_text.tre`** (145 sor). Az üzenetek — 51 `CAcquireUI::*`
bejegyzés — **hivatalos magyar fordítással** léteznek.

## A panel felépítése

| terület | elem | felirat |
|---|---|---|
| forrás | `import_from_label` | **Import from:** |
| cél | `import_to_label` | **Import to:** |
| — | `import_delimiter_label` | `/` |
| mappanév | `subfolder_label` | **Folder title:** |
| másodpéldányok | `excludedupesbutton` | súgó: *Exclude photos that are already imported into Picasa* |
| — | `excludedupes_label` | **Exclude Duplicates** |
| előnézet | `previewlabel` | **Preview** |
| tálca | `importtraylabel` | **Import Tray** |
| üres állapot | `nothing` | **No photos available** |
| forgatás | `rotate1button` / `rotate2button` | *Rotate the Photo clockwise / counter-clockwise* |
| lapozás | `previousbutton` / `nextbutton` | *View the previous / next Photo* |
| csillag | `startoggle` | *Add/Remove Star* |
| kizárás | `excludetoggle` | *Exclude/Include* |
| **másolás után** | `delete_label` | **After Copying:** |
| megosztás | `share_with_label` · `selected_groups_label` (**Nobody**) · `add_groups_button` · `upload_label` | *Add people to share albums with* |
| online | `sync_options_button` | felirat **Options**, súgó *Online options* |
| gombok | `anowbutton` (**Import All**) · `import_selected` (**Import Selected**) · `acancelbutton` (**Cancel**) | |

## A tipp-sor NÉGY állapota

Az `importtiptext` **állapotfüggő** — a Picasa végigvezeti a felhasználót:

| # | szöveg |
|---:|---|
| 1 | Enter new folder title or choose existing folder to continue |
| 2 | Click Import All or Import Selected |
| 3 | Import into separate folders for each date taken |
| 4 | Import into folder with today's date |

A 3. és 4. a **mappa-elnevezési stratégiát** írja le: dátumonként külön
mappa, vagy egyetlen mappa a mai dátummal.

## A „kártya törlése" figyelmeztetés — DARABOKBÓL

Ez a Picasa legkomolyabb adatvesztési pontja, és a szöveg **kilenc
darabból** áll össze:

| erőforrás | HU |
|---|---|
| `WipeCardIntro` | **FIGYELMEZTETÉS**⏎⏎Azt választotta, hogy az **ÖSSZES FÁJLT** törli a forrás adathordozóról.⏎⏎ |
| `WipeCardDupesNotDone` | Importálás után a program %d fájlt töröl.⏎ |
| `WipeCardScanNotDone` | A program ismeretlen számú fájlt fog törölni az importálás után.⏎ |
| `WipeCardScanNotDoneSelected` | A program ismeretlen számú fájlt fog törölni a forrás adathordozóról, ha csak ennyi fájlt importál: |
| `WipeCardNotImported` | nem lesz importálva. |
| `WipeCardSingleDupe` | nem lesz importálva, mert már másodpéldány a Picasában.⏎ |
| `WipeCardMultiDupes` | nem lesz importálva, mert már másodpéldányok a Picasában.⏎ |
| `WipeCardSingleExlcuded` *(elgépelve!)* | Ezek egyike már másodpéldány a Picasában.⏎ |
| `WipeCardMultiExcluded` | %d már másodpéldány a Picasában.⏎ |
| `WipeCard1OtherFile` | ⏎A Picasa 1 fájlt nem ismer fel a törlendő fájlok közül.⏎ |
| `WipeCardOtherFiles` | ⏎A Picasa %d fájlt nem ismer fel a törlendő fájlok közül.⏎ |
| `WipeCardFinalWarning` | ⏎Biztosan eltávolítja az **ÖSSZES FÁJLT**?⏎⏎**A MŰVELET NEM VONHATÓ VISSZA.**⏎ |

> ⚠️ A `WipeCardSingleExlcuded` kulcsnév **elgépelt** az eredetiben
> („Exlcuded"). Aki az erőforrásokból dolgozik, ezt a formát keresse.

> A **fel nem ismert fájlokra** külön mondat figyelmeztet — a Picasa
> tudja, hogy a kártyán lehet olyasmi is, amit nem ő kezel.

## Az enyhébb változat: csak az importáltak törlése

| erőforrás | HU |
|---|---|
| `confirmRemove::title` | **Eltávolítás jóváhagyása** |
| `confirmRemoveCopied::message` | Biztosan eltávolítja az importált fájlokat a kártyáról? **A művelet nem vonható vissza.** |
| `confirmRemoveCopied::yesButton` | **Importált fájlok eltávolítása** |
| `confirmRemoveAll::yesButton` | **Az összes fájl eltávolítása** |
| `dontwarn` | A jövőben ne jelenjen meg ez a figyelmeztetés. |

## Folyamat és hibák

| erőforrás | HU |
|---|---|
| `loading1` | %d fájl betöltése |
| `copying` | **%2$d / %1$d fájl másolása** *(figyeld a felcserélt sorrendet!)* |
| `finishing` | Befejezés |
| `cleanup` | Karbantartás |
| `AcquiredFiles` | %d fájl beolvasva |
| `donenotifer` *(elgépelve)* | **Az importálás elkészült** |
| `errornotifer` *(elgépelve)* | Hiba történt az importálás során |
| `eNoConnection` | Nem sikerült az eszközhöz csatlakozni. Ellenőrizze a kapcsolatot. |
| `eAuthenticationErr` | A kijelölt eszköz foglalt. Próbálkozzon újra |
| `eFileErr` | Hiba történt az importálási kísérlet során. Nem érhető el a forrás, illetve megtelt vagy írásvédett a cél. |
| `eAllErr` | Ismeretlen hiba történt az importálási kísérlet során. |

> A magyar `copying` sztringben a **paraméterek sorrendje meg van
> fordítva** (`%2$d / %1$d`) — magyarul „100 / 3 fájl másolása" a
> természetes. Ezt a pozicionális jelölés teszi lehetővé; a fordítást
> **szó szerint** kell átvenni.

## Forrásfajták

`Removeable` → **Cserélhető meghajtó (%s)** · `folderondisk` → **Mappa a
lemezen** · `WiaDev` → `Wia-` (Windows Image Acquisition eszközök) ·
`devnone` → **Egyik sem**

*Bizonyítottsági fok: megerősített* (az `acquirepanel_text.tre` teljes
tartalma és az 51 `CAcquireUI::*` bejegyzés).
