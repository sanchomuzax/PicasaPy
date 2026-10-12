# Poszter készítése

A poszter egyetlen képet **több lapra vág szét**, hogy a lapokat külön
kinyomtatva és egymás mellé téve nagy poszter legyen belőle.

## Indítás

Jelölj ki egy képet, majd **Létrehozás ▸ Poszter készítése…**. Ha több
képet jelöltél ki, a program az **elsőből** készít posztert.

A **Poszterbeállítások** ablak három beállítást kér:

- **Poszterméret:** — 200% és 1000% között, százasával. A szám megadja,
  hány sorra és oszlopra vágja a program a képet: 200%-nál 2 × 2, 300%-nál
  3 × 3 lapra, és így tovább 1000%-ig (10 × 10).
- **Papírméret:** — a nyomtatandó lap mérete. A területi beállításod
  szerint metrikus környezetben **10x15** és **20x25**, hüvelykesben
  **4x6** és **8.5x11** közül választasz; a program megjegyzi az utolsót.
  Ma a választás még nem változtatja meg, hogyan vágódik a kép.
- **Átfedő mozaikok** — bejelölve a szomszédos lapok a belső szélük felé
  kicsit (a lap méretének 10%-ával) átnyúlnak egymásba, így az
  összeillesztés könnyebb.

A tipp az ablakban: ha nem szeretnéd, hogy a program csonkolja a képet,
előbb vágd a papírral azonos arányúra.

Az **OK** elindítja a munkát, a **Mégse** elveti.

## Mi lesz belőle

A lapok a **forráskép mellé, ugyanabba a mappába** kerülnek, és a
fájlnevük elején a lap helye áll: **sor-oszlop-eredetifájlnév**, nullától
számolva. Egy `nyaralas.jpg`-ból 200%-nál például `0-0-nyaralas.jpg`,
`0-1-nyaralas.jpg`, `1-0-nyaralas.jpg` és `1-1-nyaralas.jpg` lesz. A
lapok ugyanabban a formátumban készülnek, mint az eredeti kép; az
eredetit a program nem változtatja meg.

A poszter a kép **szerkesztett** változatából készül (vágás, forgatás,
effektek), és a fényképezőgép által megjelölt tájolás szerint helyesen
áll — álló képből tehát álló poszter lesz.

A végén az ablak kiírja: „A poszterlapok elkészültek.", alatta a
fájlok listájával. Ha nem sikerült — például nem olvasható a kép, vagy
nem írható a mappa —, ezt látod: „A poszterlapokat nem sikerült
létrehozni.", és az ok. Nagy képnél a munka eltarthat egy ideig, de a
program közben használható; két percnél tovább nem várja meg.

A kinyomtatáshoz jelöld ki a lapokat a könyvtárban, majd használd a
[Nyomtatás](nyomtatas.md) parancsot.
