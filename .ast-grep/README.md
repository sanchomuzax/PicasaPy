# Szerkezeti kódszabályok (ast-grep)

Ezek a szabályok a **szintaxisfán** keresnek, nem szövegben — így olyan
hibaosztályokat találnak meg, amiket a `ruff` nem tud kifejezni, a `grep`
pedig elárasztana zajjal.

Futtatás a repó gyökeréből:

```bash
ast-grep scan
```

Egyetlen szabály, JSON-kimenettel:

```bash
ast-grep scan --rule .ast-grep/rules/unclamped-size-scaled-blur-radius.yml --json=compact
```

Telepítés: `cargo install ast-grep` (a projekt nem függ tőle — a CI nem
futtatja, ez fejlesztői segédeszköz).

## Miért pont ez a három?

Mindhárom egy **valóban megtörtént** hibából származik, nem elméletből:

| szabály | mit fog meg | honnan |
|---|---|---|
| `unclamped-size-scaled-blur-radius` | képmérettől függő elmosás-sugár 255-ös korlát nélkül | #504 — a Lomo/Holga befagyása és fekete kimenete |
| `sigma-derived-gaussian-kernel` | `cv2.GaussianBlur` szigmából származó kernellel | #504 — 168 másodperc egyetlen lépésre egy 12 MP-es képen |
| `literal-color-tuple` | beégetett szín-hármas a render-rétegben | #510 / #515 — két munkamenet vitatkozott a csatornasorrendről, és egyik sem találta el az igazi hibát |

A szabályok `note:` mezője leírja a hátteret és a javítás módját, hogy a
találat önmagában is érthető legyen.

## Szabályírás közben

- **Blokk-stílusú YAML kell**, ha a minta vesszőt tartalmaz. A folyam-stílusú
  `{ pattern: max(height, width), stopBy: end }` **némán elromlik** (a YAML a
  vesszőnél elvágja), és a szabály nulla találatot ad — nem hibát. Ez egy
  teljes hibakeresési kört elvitt.
- A `kind:` mellé **ne** tegyél `all:`/`any:`/`not:` testvért — a felső
  szinten használj `all:`-t, és tedd a `kind`-ot is alá sub-rule-ként.
- Relációs szabályoknál (`has`, `inside`) mindig `stopBy: end`.
- Előbb egy pici próbafájlon ellenőrizd, hogy a szabály a **javított** kódra
  már NEM üt — így regressziós őrré válik, nem csak keresővé.
