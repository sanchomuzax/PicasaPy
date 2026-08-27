# Élő állapotlap

Egy olvasható oldal arról, **hol tart a projekt most** — a tulajdonosnak, nem
fejlesztőknek. A `docs/specs/` 68 lapja és 43 ezer sora nem alkalmas erre.

**A lap címe (ez nem változik):**

<https://claude.ai/code/artifact/4deaf3dd-41c3-4da2-85ec-5fd14a98601e>

## Mit mutat

| szakasz | forrása |
|---|---|
| menü-lefedettség | `scripts/menu_lefedettseg.py` — a Picasa parancslistája vs. a mi dokumentációnk |
| „Ez vár rád" | `felhasználóra-vár` és `blocked` címkés jegyek |
| a következő öt kutatnivaló | a lefedettségi mérés determinisztikus sorrendje |
| rothadás-mutató | hány jegyhez nem nyúlt senki a nyitása óta |
| spec-lapok nyitott kérdéssel | a `docs/specs/00-index.md` kézi listája |

## Hogyan kell frissíteni

**Egyetlen mondat a lényeg: a lapot nem írjuk, hanem újraszámoljuk.**

```bash
python3 scripts/allapotlap.py
```

Ez `docs/allapotlap.html`-t állít elő (git-ignorált, mert minden futásnál
változik). Ezután **ugyanarra a címre** kell publikálni:

- `Artifact` hívás, `file_path` = a generált HTML,
- **`url` = a fenti cím** — enélkül új, különálló lap jön létre, és a
  felhasználó régi linkje elavul;
- `favicon` = `📐` (ne változtasd — a felhasználó ezen az ikonon találja meg
  a böngészőfülét).

A címet a szkript is kiírja futás után, és a `--url` kapcsolóval magában is
lekérdezhető:

```bash
python3 scripts/allapotlap.py --url
```

## Mikor frissítsd

Bármelyik munkamenet frissítheti, és érdemes is a kör végén, ha a kör
jegyeket nyitott vagy zárt. Nincs kára a gyakori frissítésnek: a szkript csak
olvas (fájlok + `gh issue list`).

## Miért így, és nem kézzel írt összefoglalóként

Mert a kézzel írt összefoglaló elrothad. A projektben ez már megtörtént a
listás jegyekkel: a 2026-08-26-i mérés szerint a nyitott jegyek fele a
nyitása óta érintetlen — a tulajdonos maga vette észre, hogy *„elfelejtik a
fejlesztők kezelni, és így elvesznek, nem frissülnek."*

Egy mért lap nem tud elavulni. Legfeljebb régi lehet — és a dátumát a
fejlécében kiírja, tehát az is látszik.
