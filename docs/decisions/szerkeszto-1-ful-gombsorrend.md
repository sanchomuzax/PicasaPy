# A szerkesztő 1. füljének („Gyakori javítások") gombsorrendje — VÉGLEGES

**Állapot:** eldöntve, lezárva. **Dátum:** 2026-08-16. **Döntő:** a tulajdonos,
az eredeti Picasa 3.9 (Windows) képernyőképe alapján. **Jegy:** #464.

## A sorrend — ez az érvényes, ehhez kell igazodni

Három sor, soronként három csempe, **alattuk** a Derítőfény-csúszka:

```
Vágás            Kiegyenesítés          Vörösszem
Jó napom van     Automatikus kontraszt  Automatikus szín
Retusálás        Szöveg
─────────────────────────────────────────────────────────
[kis kép]  ──────●────────  Derítőfény
─────────────────────────────────────────────────────────
Visszavonás: <lépés>            Újra
```

Kódban (`EditorTabCommonFixes.qml`, ebben a forrás-sorrendben):

| # | `objectName` | felirat |
|---:|---|---|
| 1 | `editToolCrop` | Vágás |
| 2 | `editToolTilt` | Kiegyenesítés |
| 3 | `editToolRedeye` | Vörösszem |
| 4 | `editToolEnhance` | Jó napom van |
| 5 | `editToolAutolight` | Automatikus kontraszt |
| 6 | `editToolAutocolor` | Automatikus szín |
| 7 | `editToolRetouch` | Retusálás |
| 8 | `editToolText` | Szöveg |
| 9 | `fixesFillSlider` | Derítőfény (csúszka, a rács ALATT) |

**Kreatív készlet (`picnik`) nincs** — halott online funkció, tudatosan
kihagyva (ld. `ui-audit-editor.md`).

## ⚠️ Amit ez a lap egyszer s mindenkorra eldönt

Az `editpanel.tre` **erőforrás-sorrendje NEM a kirajzolási sorrend.** A
binárisból kiolvasott lista (crop → redeye → enhance → picnik → autocolor →
autolighting → filllight → horizonadjust → edittext → retouch) **négy ponton**
eltér attól, amit a program ténylegesen mutat: a Kiegyenesítés helye, az
Automatikus szín/kontraszt párosa, a Szöveg/Retusálás párosa, és a
Derítőfény-csúszka helye.

**A képernyőkép nyer.** A tulajdonos 2026-08-16-i, kifejezett rendelkezése
(#464 hozzászólás): *„Ez a valódi és végleges effekt sorrend az első fülön!
TILOS megkérdőjelezned újra! A kódban valami nem látszik vagy nem került
feltárásra, azért mond ellent!"*

Vagyis a kérdés **nincs nyitva**. Az erőforrás-sorrend és a képernyő közti
eltérés magyarázata még FELTÁRATLAN — nagy valószínűséggel egy futásidejű
átrendezés vagy egy külön elrendezés-leíró, amit a kutatás eddig nem talált
meg. **Ez kutatási nyitott pont, NEM ok a sorrend megváltoztatására.** Aki
egyszer megtalálja, ide írja be — a sorrendhez akkor sem nyúl.

## Miért kellett ezt külön lapra írni

A sorrend **kétszer** került napirendre újra:

1. Egyszer a jegy szövege alapján (feljegyzésből készült, téves sorrend) — a
   tulajdonos képernyőképe felülírta;
2. másodszor egy 2026-08-16-i bináris-kutatás alapján, ami az erőforrás-
   sorrendet hozta, és ismét ellentmondott a kódnak.

A tulajdonos ekkor jelezte, hogy ezt már **húsznál többször** megadta. Ez a lap
a végleges hivatkozási pont; a `PROTOKOLL.md` szerint elvetett irányt csendben
visszahozni tilos, és **ez itt egy elvetett irány**.

## Az őr

`tests/app/qml_functional/test_editor_464.py` → `TestTab1ButtonOrder` állítja a
forrás-sorrendet, és külön teszt őrzi, hogy a Kreatív készlet csempéje nincs
jelen. **Ha egy jövőbeli kör „javítani" akarja a sorrendet, ez a teszt fog
elbukni — és akkor ezt a lapot kell elolvasni, nem a tesztet átírni.**
