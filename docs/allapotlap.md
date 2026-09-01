# A tulajdonos lapja

**Egyetlen** olvasható oldal a tulajdonosnak, nem fejlesztőknek — három
szakasszal. A `docs/specs/` 70 lapja és 49 ezer sora nem alkalmas erre.

| szakasz | mit mutat |
|---|---|
| **Állapot** | hol tart a projekt: jegyek, menü-lefedettség, rothadás |
| **Bináris térkép** | mennyit fejtettünk vissza a Picasából, és hol |
| **Módszertan** | hogyan dolgozunk, és fognak-e a szabályaink |

Cím (ez nem változik):
<https://claude.ai/code/artifact/4deaf3dd-41c3-4da2-85ec-5fd14a98601e>

## Frissítés — egy paranccsal

```bash
cd ~/picasapy-agent && python3 eszkozok/egy_lap.py
```

Ez lefuttatja **mindhárom** forrás-generátort — az itteni
`scripts/allapotlap.py`-t és `scripts/binaris_terkep.py`-t, valamint a privát
repó `eszkozok/modszertan_lap.py`-ját —, és egyetlen oldallá rakja őket.
A két itteni szkript külön is futtatható (`python3 scripts/artifactok.py`),
de a **publikálás** mindig az összevont lapból történik.

Publikálni a **fenti címre** kell (`Artifact` hívás, `url` mező) — enélkül új
lap jön létre, és a felhasználó régi linkje elavul.

## Miért egy lap

Korábban három külön cím volt. A tulajdonos 2026-09-01-én jelezte, hogy a
frissítésük „senki földje": hét publikált lapból **egynek** volt ütemezett
frissítője, és az egyik **öt napja** állt. Három lap három hely volt, ahol el
lehetett felejteni a frissítést.

A részletes szabály — mikor kell frissíteni, mikor nem, és mit csinál a napi
háromszori háló — a privát repó `docs/lapok.md`-jében van, mert a munkavégzés
módjáról szól, nem a termékről.
