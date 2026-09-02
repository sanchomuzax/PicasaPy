---
name: picasapy-dev
description: PicasaPy fejlesztés indítása felügyelt munkamenetben — vegyél le egy `ready` jegyet és vidd végig (foglalás → ág → TDD → PR → kézzel indított CI → merge → verzió/CHANGELOG → jegyzárás). Akkor hívd, ha a felhasználó fejlesztést kér („dolgozz”, „vegyél le egy jegyet”, „fejlessz”), vagy ha ezt a skillt nevesíti. Éjszakai, felügyelet nélküli munkára a `sancho-night-work` való.
---

# PicasaPy fejlesztés (picasapy-dev)

Egy hívás, ami elindítja a rendes fejlesztői kört. **Ez a fájl NEM tartalmazza
a szabályokat** — azok a `PROTOKOLL.md`-ben élnek, egy helyen. Itt csak a
sorrend van, hogy semmi ne maradjon ki.

Ha ez a kettő szétcsúszik, a `PROTOKOLL.md` az igazság.

## 0. Ellenőrizd, hogy nem vakon dolgozol

A privát agent-kontextusnak (`picasapy-agent`) megvan kell lennie — a
session-start hook klónozza. Ha a hook figyelmeztetett, hogy hiányzik:
`add_repo` + klón + `register_repo_root`, és csak utána kezdj.

Olvasd el, ebben a sorrendben:

1. `PROTOKOLL.md` — **a szabálykönyv**: foglalás, hatókör, forró fájlok,
   git-buktatók, teszt, i18n, integráció, CI-indítás, a feladat-ciklus vége.
2. `memory/00-index.md` és a feladathoz tartozó memória-lapok.
3. `memory/tanulsagok.md` — amibe korábbi körök belefutottak.

## 1. Jegyválasztás

`list_issues` a `ready` címkére, frissen. Sorrend: **P0 → P1 → P2…**; azon
belül az effektek a legfontosabbak, a nyomtatás és az e-mail a legkevésbé.

**A `ready` címke önmagában nem elég.** A foglalás-ellenőrzés három lépése a
`PROTOKOLL.md` „Foglalás" pontjában van — végezd el mind a hármat, mielőtt
egy sor kódot írsz. Ha a jegy foglalt, vegyél másikat.

## 2. A kör

```
foglalás → ág (push -u azonnal) → bukó teszt → kód → teljes teszt + lint
  → PR → CI KÉZI INDÍTÁSA → zöld CI → merge → verzió + CHANGELOG
  → jegy-komment → jegy zárása (in-progress címke le)
```

Két lépés, amit a legkönnyebb elfelejteni, mindkettő a `PROTOKOLL.md`-ben
részletezve:

- **a CI nem indul el magától** az integrációs tokennel érkező PR-re — kézzel
  kell indítani, különben örökké vársz egy zöldre, ami sosem jön;
- **a feladat nem ér véget a PR-rel**: a merge, a verzióemelés és a jegy
  lezárása is a vállalóé.

## 3. Munka közben

- **Hatókör**: ha más hibát látsz, nyiss rá jegyet — ne javítsd. (Egy
  javítás, amit senki nem kért, nem ajándék, hanem ütközés.)
- **Kérdezés**: a felhasználó nem programozó. Fejlesztői eldöntendő kérdést
  ne tegyél fel — hozz józan alapértelmezést, és foglald össze egy mondatban.
  **Kivétel: UI-döntést (elrendezés, szöveg, viselkedés) MINDIG kérdezz meg.**
- **Nyelv**: minden chat-válasz magyarul.
- **Bizonytalanság**: ha a `docs/specs/`, a jegyek és a privát repó nem ad
  egyértelmű választ, **kutasd a bináris indexet**, ne találgass —
  `referencia/binary-index/`, `referencia/dekompilalt*/`. Bináris hivatkozás
  csak visszakereshető címmel érvényes.
- **Az őrnek legyen foga**: minden új tesztet futtass le a javítás NÉLKÜL is,
  és győződj meg róla, hogy tényleg elbukik — tiszta fán.

## 4. Lezárás

A `PROTOKOLL.md` „A feladat-ciklus VÉGE" szakasza szerint. A jegy addig a
tiéd, amíg le nem zárult — a PR megnyitása nem befejezés.

**Ha a kör átnézést is tartalmazott** (code review, önátnézés, mérőszett-
kiértékelés), a záró összefoglaló tartalmazza a mérleg-sort — a négy állapot
és a kötelező mellékletek a `PROTOKOLL.md` „Lelet-elszámolás" szakaszában:

```
Leletek: L lelet · J javítandó · E elvetve · H elhalasztva · D duplikátum · 0 besorolatlan
```

Besorolatlan lelettel a kör nem zárható. Az `ELVETVE` **ellenbizonyítékot**
kíván (fájl+sor, mérés vagy jegy) — „nem tűnik fontosnak” nem elég.

**Ha a kör agentet indított**, a záró összefoglaló ezt a sort is tartalmazza:

```
Brief-ellenőrzőlista: 2/2
```

A két őrizetlen tétel (forró fájl, explicit modell) másolható alakban a
`PROTOKOLL.md` „Az agent-brief ellenőrzőlistája" szakaszában áll. A másik
kettőt — tesztfuttató és kiadás-tilalom — **hook** őrzi, azokat nem kell
beírni.
