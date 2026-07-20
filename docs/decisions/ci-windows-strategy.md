# ADR-002: Windows CI-láb — pytest-timeout + ritkítás

Dátum: 2026-07-20 · Státusz: ELFOGADVA

## Helyzet

A `ci.yml` a kezdetektől (2026-07-18) minden push/PR-en lefuttatta a teljes
tesztkészletet `ubuntu-latest` ÉS `windows-latest` runneren is. A 138 eddigi
`CI / Test (windows-latest)` futásból:

- 86 sikeres (62%)
- 13 hibás (9%)
- 38 megszakítva/beragadt (28%) — a #53-as GIL-deadlock osztályba tartozó
  hang, amit a 2026-07-19-i `timeout-minutes: 20` csak *tünetileg* kezelt
  (nem fagyasztja le órákra az Actions-sort, de a futás maga továbbra is
  elakad és megszakad).

Ez az arány önmagában is magas, és összecseng a szélesebb közösségi
tapasztalattal: a GitHub-hosted Windows runner lassabb, drágább és
flakyebb, mint a Linux/macOS társai, a Qt/pytest-qt projektek pedig
visszatérően dokumentálnak Windows-specifikus "post-test hang" jelenséget
(pytest-qt #223, pytest #8700) — ez nem PicasaPy-specifikus hiba, hanem
ismert kockázat.

## Döntés

1. **`pytest-timeout` bevezetése mindkét lábon** (`--timeout=60
   --timeout-method=thread`): egy beragadó egyedi teszt 60 mp után
   megszakad, ahelyett hogy a teljes job 20 percig lógna, majd
   cancel-elődne. Ez konkrét, azonosítható hibát ad (melyik teszt akadt
   be), nem csak egy megszakított jobot.
2. **A `windows-latest` láb különálló job**, és **csak `push` eseményen fut**
   (`if: github.event_name == 'push'`, ami a repó `on:` szabálya miatt
   gyakorlatilag a `main`-re kerülést jelenti) — PR-eken/session-branch-eken
   NEM fut. A `ubuntu-latest` láb változatlanul minden push-on és PR-en fut.

## Indoklás

- **A projekt Linux-first** (rögzített döntés, CLAUDE.md) — a napi
  fejlesztői visszajelzést a gyors, megbízható Linux-teszt adja; ezt nem
  szabad, hogy egy flaky Windows-futás blokkolja vagy lassítsa minden
  PR-en.
- **A keresztplatform-cél mégis valós** (a felhasználó ma is Windows-os
  Picasát használ, az import ismételhetőségét ez indokolja) — ezért a
  Windows-ellenőrzést nem törüljük ki, csak ritkítjuk: elég, ha a ténylegesen
  mergelt kódon fut le, nem minden egyes push-nál egy még nyitott PR-en.
- **A pytest-timeout nem oldja meg a mögöttes Qt/GIL-hangot**, de sokkal
  olcsóbbá teszi a diagnózist: a jövőben egy konkrét teszt neve és 60 mp-es
  határ jelzi a bajt, nem egy 20 perces, megszakított, névtelen job.

## Következmények

- Kevesebb Windows-futás → kevesebb elszabadult/megszakított futás,
  kevesebb runner-idő elfecsérelve.
- Ha egy PR mégis Windows-specifikus regressziót vezetne be, azt csak a
  main-be kerülés UTÁN vesszük észre (nem a PR-en) — ez tudatosan vállalt
  kockázat, cserébe a napi munka gyorsabb/megbízhatóbb.
- Ha a beragadás továbbra is gyakori marad a `pytest-timeout` bevezetése
  után is, a következő lépés a konkrét beragadó teszt (valószínűleg
  `tests/app/test_qml_functional.py`, #53) Windows alóli kizárása vagy
  külön debug-jegy nyitása — ezt a jegyzőkönyvet akkor frissíteni kell.
