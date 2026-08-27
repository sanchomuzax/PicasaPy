# Élő artifactok

Két olvasható oldal a tulajdonosnak, nem fejlesztőknek. A `docs/specs/`
69 lapja és 43 ezer sora nem alkalmas erre.

| lap | mit mutat | cím (ez nem változik) |
|---|---|---|
| **Állapotlap** | hol tart a projekt: jegyek, menü-lefedettség, rothadás | <https://claude.ai/code/artifact/4deaf3dd-41c3-4da2-85ec-5fd14a98601e> |
| **Bináris térkép** | mennyit fejtettünk vissza a Picasából, és hol | <https://claude.ai/code/artifact/3e4aac90-5195-45c3-ba94-661d26824f94> |

## Frissítés — EGY paranccsal, mindkettő

```bash
python3 scripts/artifactok.py
```

Kiírja mindkét lap fájlját ÉS a hozzá tartozó címet. Utána publikálni kell
őket a **kiírt címekre** (`Artifact` hívás, `url` mező) — enélkül új lap jön
létre, és a felhasználó régi linkje elavul.

⚠️ A bináris térképhez kell a **privát** agent-repó bináris indexe. Ha nincs
meg, a szkript `3`-mal lép ki és megmondja — féllábú lapot nem ír.

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


## Kommentek: automatikus értesítés NINCS

Ha valaki megosztott lapon hozzászól, arról **nem érkezik értesítés**, és
nincs figyelő folyamat sem. A kommentet **külön le kell kérni**:

```
Artifact(action="comments", url="<a lap címe>")
```

**Ezért a lekérés a kör végi frissítéshez van kötve:** a
`scripts/artifactok.py` kiírja a két kész `comments` hívást, hogy ne
emlékezetből múljon. Ez az egyetlen pillanat, amikor ez rendszeresen
megtörténik.

Két dolgot érdemes tudni a válaszokról:

* **„comments are not available on this artifact right now"** — a lap nincs
  megosztva senkivel, tehát nincs is hol kommentelni. Ez nem hiba.
* **Válaszolni csak olyan szálba lehet, ahol valaki `@claude`-ot említett.**
  Olvasni minden szálat lehet, de a válasz emberi engedélyhez kötött.
