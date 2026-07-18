# Automatizált integrátor-kör

2026-07-18-tól az integrátor-kört egy ütemezett Claude-Routine futtatja
(**„PicasaPy integrátor-kör"**, óránként, friss remote sessionben, a
claude.ai Routines felületén kezelhető — szüneteltetés/törlés ott).

## Mit csinál minden órában

1. Végignézi a nyitott PR-eket; a mérce az ubuntu CI-láb (a Windows-láb
   kísérleti, nem blokkol).
2. Merge előtt lokálisan összefésüli a PR-t a friss mainnel, lefuttatja a
   teljes tesztkészletet és — ha kell — az i18n-regent; konfliktust és
   forró-fájl-bekötést ő old meg (ld. CONTRIBUTING.md).
3. Zöld teszt után mergel, zárja az issue-t, törli a PR branchét.
4. Érdemi merge után verzió-bump + tag + GitHub Release.
5. Takarítás: 3+ napja álló `in-progress` issue-k visszaállítása
   `ready`-re, árva `claude/*` branchök PR-körbe terelése.
6. Piros CI-nál: kis, egyértelmű javítást pushol a PR branchre; egyébként
   diagnózis-kommentet ír és nyitva hagyja a PR-t.

A futás végén push-értesítés megy a tulajdonosnak, rövid magyar
összefoglalóval.

## Mit jelent ez a feature-sessionöknek

Semmi új teendő: a CONTRIBUTING.md szerinti PR-protokoll változatlan.
Zöld CI-jú PR-t nem kell „bejelenteni" — legkésőbb a következő óránkénti
körben magától beolvad. Ha egy PR-nek kézi integrációs igénye van
(forró fájl bekötése), azt továbbra is az issue-ban kell leírni.
