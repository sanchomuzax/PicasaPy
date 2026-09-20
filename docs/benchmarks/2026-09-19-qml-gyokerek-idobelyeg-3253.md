# A QML-gyökerek időbélyege NEM ad gyökerenkénti bontást (#3253, 2026-09-19)

*Gép: Raspberry Pi 5 (aarch64, 4 mag), `QT_QPA_PLATFORM=offscreen`, üres
könyvtár, `scripts/indulas_meres.py --futasok 2` (a melegen futó 2. indítás).*

## A kérdés

A #3253 azt kérte, hogy a maradék ~1200 ms QML-időt a **valódi `Main.qml`
fában** bontsuk fel: időbélyeg a fa gyökereinél, a
`Component.onCompleted`-ben, a betöltési sorrend megváltoztatása nélkül.

## A mérés

A `Main.qml` **106 közvetlen gyermeke** közül **105** kapott jelölőt (a
`Component{}` nem kaphat: a QML szabálya szerint *„Component elements may
not contain properties other than id"* — a betöltés különben elszáll). A
jelölő a projekt `startupStatus`-mintája szerint `typeof`-őrrel hivatkozik a
hídra, mert a QML-funkcionális tesztek a fát a híd nélkül töltik be.

| mérés | érték |
|---|---:|
| a QML-szakasz teljes ideje | **1592,9 ms** |
| az **első** jelölő (`Binding`, a fájl első gyökere) | **1514,6 ms** |
| a maradék **103** jelölő ÖSSZEGE | **73,1 ms** |
| a legnagyobb egyedi jelölő a maradékból (`SplashScreen`) | 67,8 ms |
| ugyanez műszerezés nélkül (3 mérés) | 1513,4 · 1579,9 · (3393,3 kiugró) |

## ⛔ A verdikt: a `Component.onCompleted` NEM alkalmas erre

A QML a teljes objektumfát **először létrehozza**, és a
`Component.onCompleted` kezelők csak utána, egy külön **befejező menetben**
futnak le. Ezért az ELSŐ jelölő tartalmazza a fordítást és a teljes
példányosítást (1514,6 ms), a többi 103 pedig csak a kezelők közti
mikro-réseket (összesen 73,1 ms) — köztük a `PhotoViewer`, a `SplitView` és
a panelek is 0,1–0,2 ms-mal, ami nyilvánvalóan nem a saját költségük.

⇒ **A jegy törzsében javasolt módszer nem működik**, és ezt nem a szám
nagysága, hanem a Qt életciklusa okozza. A műszerezést ezért **nem tartottuk
meg** — dead code lett volna, ami semmit nem mér.

## Amit a mérés MÉGIS eldöntött

A jegy utolsó kérdése: *„van-e még olyan tétel, ami nem látszik az
induláskor és mégis drága?"*

**Nincs — legalábbis a gyökerek szintjén nem így keresendő.** A teljes
QML-idő egyetlen, osztatlan blokkban (létrehozási menet) telik el, tehát
egy-egy gyökér halasztása innentől nem a jó kar: a #1612 nyeresége is azért
volt nagy, mert a `CollagePanel` a `Component{}`-be kerülve a
**fordításból** is kiesett, nem csak a példányosításból.

⇒ A további gyorsítás eszköze a **fordítás/példányosítás egésze**
(`qmlcachegen`, kevesebb elem, több halasztott részfa), nem újabb egyedi
halasztás. A gyökerenkénti bontáshoz Qt-szintű eszköz kell (QML-profiler
vagy `QQmlIncubator`-alapú, saját létrehozási menet), nem QML-oldali jelölő.

## Amit ez a lap NEM mond

* Nem mér GPU-t és nem mér felhasználói élményt — csak az indulási idővonal
  QML-szakaszát.
* A 3393,3 ms-os kiugró mérés benne van a táblában: a gép terhelése a mérés
  alatt ~2,0 volt, tehát a ±70 ms-os szórás mellett ritkán kétszeres kiugrás
  is előfordul. Az 1514,6 ms-os lelet ennél nagyságrenddel nagyobb, ezért a
  következtetést a zaj nem érinti.
