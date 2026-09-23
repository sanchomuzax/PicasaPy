# A Main.qml betöltése: fordítás vagy példányosítás? (#3383, 2026-09-23)

*Gép: Raspberry Pi 5 (aarch64, 4 mag), Qt 6.8.2 / PySide6 6.8.2,
`QT_QPA_PLATFORM=offscreen`, üres könyvtár. Mérő:
`scripts/qml_betoltes_bontas.py --ismetles 5`.*

## A kérdés

A #3253 kimutatta, hogy a QML-szakasz (~1,2–1,6 s) egyetlen, osztatlan
létrehozási menet. A következő gyorsítás két kar közül választhat: a
**fordítást** csökkenteni (`qmlcachegen`) vagy a **példányosítást**
(kevesebb elem, halasztott részfák). A jegy azt kérte: melyik a nagyobb tétel?

## Melyik út járható ezen a gépen

| út | elérhető? |
|---|---|
| Qt QML-profiler (`qmldbg_profiler`) | **nem** — a Qt-bővítmények között nincs `qmltooling`, és `qmlprofiler` sincs telepítve |
| a két lépés szétválasztása a Qt nyilvános API-jával | **igen** — ezt mérjük |

A mérő a valódi `application.run()`-t futtatja (minden vezérlő, kontextus és
képszolgáltató a helyén), csak az `engine.load` helyére tesz két külön
időzített lépést:

* **fordítás**: `QQmlComponent(engine, url, PreferSynchronous)`, amíg `Ready`;
* **példányosítás**: `component.create(rootContext)`, a
  `Component.onCompleted` kezelőkkel együtt.

## Az eredmény (medián, 5 ismétlés)

| | fordítás | példányosítás |
|---|---:|---:|
| **hideg** — üres Qt-gyorsítótár (az első indítás egy frissítés után) | **737 ms** | 803 ms |
| **meleg** — a Qt lemez-gyorsítótára megvan (minden további indítás) | **114 ms** | **786 ms** |
| kontroll: lemez-gyorsítótár kikapcsolva (`QML_DISABLE_DISK_CACHE=1`, 3 mérés) | 706–741 ms | 825–835 ms |
| összevetésnek: az eredeti `engine.load` egyben, melegen | 1168 ms | |

Az egyedi értékek a szkript kimenetében, a szórás a példányosításnál nagyobb
(749–1073 ms), a fordításnál kicsi (a meleg öt mérés 111–118 ms).

## ⭐ A verdikt

1. **Meleg indulásnál a PÉLDÁNYOSÍTÁS a nagy tétel**: ~790 ms a ~114 ms
   fordítással szemben. A Qt a lefordított QML-t magától is gyorsítótárazza
   (a meleg gyorsítótárban 170 `.qmlc` fájl, 4,8 MB). Így a `qmlcachegen`
   bájtkód-része a második indítástól **nem hoz érdemi nyereséget** — azt a
   munkát a lemez-gyorsítótár már elvégezte.
2. **Hideg indulásnál a fordítás ~740 ms** — és hideg indulás minden
   **frissítés utáni első indítás**, mert az új verzió minden QML-fájlja
   újrafordul. Mivel naponta több kiadás megy ki, ez gyakori eset. Itt a
   `qmlcachegen` (előre, a csomagba fordított QML) a ~740 ms-ot
   megspórolná.
3. ⇒ A két kar nem verseng, hanem **más-más indítást gyorsít**: a
   `qmlcachegen` a frissítés utáni első indítást (−~0,7 s), a kevesebb/halasztott
   elem minden indítást.

## Amit ez a lap NEM mér

* **Elemenkénti bontást** — ahhoz a profiler-bővítmény kell, ami itt nincs.
  A jegy „legalább részfánként" kérését így csak a két lépés szintjén
  teljesíti; részfánkénti példányosítási időhöz `QQmlIncubator`-alapú mérő
  kellene (a betöltés átrendezésével, csak mérő üzemmódban).
* **A `engine.load` és a két lépés összege közti ~280 ms-ot**: melegen az
  `engine.load` 1168 ms, a fordítás + példányosítás ~900 ms. Ez **nem** a
  `QQmlApplicationEngine` fix költsége (egy 200 elemes kontroll-ablakon a
  két út azonos, ~20–40 ms), nincs rá kötött Python-kezelő
  (`objectCreated` sehol), és a lemez-gyorsítótár naplója a két úton
  azonos (nincs újrafordítás). Az ok ezzel a módszerrel nem bontható.
  A verdiktet nem fordítja meg: ha mind a 280 ms fordítás volna, a
  példányosítás akkor is a nagyobb tétel.
* **A `qmlcachegen` C++-ra fordított kötéseit** (a Qt 6 típusos
  kötés-fordítója) — ez a példányosítás alatti kötés-kiértékelést
  gyorsíthatná, de ezt csak a bevezetése után lehet megmérni.
* **Windowst** — ott a #1653 szerint más a nagyságrend; a szkript ott is
  futtatható (a memóriaplafon csak Linuxon kerül elé).

## Mellékmegfigyelés

A #3253 lapja a QML-szakaszra 1592,9 ms-ot mért (a 2. indításon); a mai
indulásmérő (`scripts/indulas_meres.py --futasok 2`) ugyanezen a kódon
**2054,8 ms**-ot (1., hideg) és **1446,2 ms**-ot (2., meleg) ad. A két
indítás közti ~600 ms éppen a fordítás hideg–meleg különbsége (737 → 114 ms).
