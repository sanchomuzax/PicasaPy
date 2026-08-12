# A natív szűrők munkafüggvényei — a hívási térkép

A `picasa-native-filter-registry.md` a **belépési pontokat** adja meg (42
szűrő → callback). Ez a lap egy réteggel mélyebb: a callbackek **vékony
burkolók**, amik a csúszkaértékeket kiolvassák a paraméterblokkból, és egy
közös **munkafüggvényt** hívnak.

Forrás: a 35 callback Ghidra-dekompilálása (12.1.2, Java 21), a nyers C-kód a
privát agent-repóban: `referencia/dekompilalt/natív-szűrők.c`.

## A burkoló-minta

```c
void contrast(int param_1, undefined4 param_2) {
  FUN_0090c2c0(param_2, *(undefined4 *)(param_1 + 0x28), 0, 0x3f800000);
  return;
}
```

- `param_1 + 0x28`, `+0x2c`, `+0x30` — az **1., 2., 3. csúszka** értéke (float)
- `param_1 + 0x40` — egy **24 bites szín** (a pipetta / fehérpont)
- `0x3f800000` = `1.0f`

## A közös munkafüggvények — ezek a valódi algoritmusok

| cím | mit csinál (a hívók alapján) | hívók |
|---|---|---|
| **`0x0090ac20`** | **Derítőfény (Fill Light)** | `backlight`, `fill`, `autobacklight`, `triple`, `triple2`, `triple3`, `finetune`, `finetune2` — **8 szűrő** |
| **`0x0090c3b0`** | **szinthúzás (Kiemelések/Árnyékok)** | `triple2`, `triple3`, `autolight`, `finetune`, `finetune2` |
| **`0x0090eda0`** | **fehérpont / semleges szín** (a pipetta és a szín-varázspálca magja) | `whitept`, `colorfix`, `autocolor`, `finetune`, `finetune2` |
| **`0x0090ea10`** | **színhőmérséklet** | `colortemp`, `colorfix`, `finetune` |
| **`0x0090c2c0`** | **kontraszt** | `contrast`, `triple` |
| **`0x0090c430`** | a `finetune`-család negyedik lépése | `triple2`, `triple3`, `finetune`, `finetune2` |
| **`0x009db610`** | **hisztogram-elemzés / automatikus szintek** | `enhance`, `autocontrast`, `tint`, `rainbow` |
| `0x009aabf0` | semleges/„nincs hatás" beállítás (a `0xffffffff` argumentumú ágakban) | 16 szűrő |

### Egyszűrős munkafüggvények

| szűrő | munkafüggvény |
|---|---|
| `shadow` (Árnyék és kiemelés) | `0x0090d3e0` (három csúszka) |
| `blur` (Elhomályosítás) | `0x0090cf60` |
| `glow` / `glow2` | `0x0090d4b0` |
| `unsharp` / `unsharp2` | `0x0090c4a0` |
| `warm` | `0x0090c040` |
| `sat` | `0x0090e200` + `0x0090b930` |
| `grain` / `grain2` | `0x0090a2e0` |
| `dir_sat` | `0x0090dbb0` |
| `dir_brite` | `0x0090d8b0` |
| `linblur` | `0x0090de10` |
| `ansel` | `0x00a3f2f0` + `0x0090e680` |

`sepia` a burkolóban **nem hív semmit** a 0x9x tartományból — vagy beágyazott,
vagy egy fix mátrix az adatokban.

## Amit ez azonnal megmond

**1. Nyolc munkafüggvény lefedi a készlet nagy részét.** Nem 42 algoritmust
kell megírni: a `0x90ac20`, `0x90c3b0`, `0x90eda0`, `0x90ea10`, `0x90c2c0`,
`0x90c430`, `0x9db610` és `0x90d3e0` megvalósításával a `finetune`-család, a
`triple`-család, az `autolight`, `autocolor`, `autocontrast`, `enhance`,
`colorfix`, `whitept`, `colortemp`, `contrast`, `backlight`, `fill` és
`autobacklight` **mind kész**.

**2. A `fill` = `backlight` = `autobacklight` = a `finetune` Derítőfénye.**
Mind a `0x90ac20`-at hívja. Egy implementáció.

**3. Az `autolight` („Automatikus kontraszt") ugyanazt a szinthúzást hívja
(`0x90c3b0`), mint a `finetune`.** Ez egybevág a méréssel (#535, #539): az
automatikák nem külön algoritmusok, hanem **automatikusan megválasztott
paraméterek** ugyanahhoz a maghoz.

**4. A `0x90eda0` a szín-varázspálca és a pipetta közös magja.** A mérés
szerint a pálca a `finetune2` p4 mezőjébe ír színt (#551) — a hívási térkép
ezt megerősíti: `whitept`, `colorfix`, `autocolor`, `finetune`, `finetune2`
mind ide fut be.

**5. A dekompilált `finetune2` visszaigazolja a mért képletet:**

```c
fVar2 = 1.0 - *(float *)(param_1 + 0x2c);   // 1 − Kiemelések
if (fVar2 <= 0.001) fVar2 = 0.001;          // nullaosztás elleni védés
```

Ez pontosan az `1/(1−h)` nevezője, amit a mérőkészletből vezettünk le — **két
független úton ugyanaz**.

## Következő lépés

A **munkafüggvények** dekompilálása (a fenti nyolc + az egyszűrősök). Ott van
a tényleges pixel-matematika; a mostani réteg csak a paraméterátadást
mutatja.
