# Finomhangolás — a hat csúszkaállás a Picasa exportján (2026-09-26, #3526)

**Mérőkészlet:** `\\DS215j\lemez\My Pictures\3449-pipetta-merokeszlet`. A mérőképek a javított generátorral készültek (#3449, PR #3525), az exportot a tulajdonos 2026-09-24-én készítette a windowsos Picasa 3.9-cel.
**Mérő:** `tools/golden/analyze_validation_kit.py <készlet>`, a `main` `46a04656` állapotán; a ΔE átlagos CIE76.

| lánc | eset | Picasa ↔ eredeti | **mi ↔ Picasa** | mi ↔ eredeti | SSIM | verdikt |
|---|---|---:|---:|---:|---:|---|
| `finetune=1,0.5,0.24,0.24,…,0` | alap | 18,903 | **0,194** | 18,934 | 0,9954 | JÓ |
| `finetune=1,1,0.48,0.48,…,0.5` | max | 47,015 | **0,176** | 47,041 | 0,9896 | JÓ |
| `finetune=1,0,0,0,…,−0.5` | min | 26,348 | **0,504** | 26,441 | 0,9989 | JÓ |
| `finetune2=1,0.5,0.24,0.24,…,0` | alap | 18,903 | **0,194** | 18,934 | 0,9954 | JÓ |
| `finetune2=1,1,0.48,0.48,…,1` | max | 50,990 | **0,175** | 51,012 | 0,9907 | JÓ |
| `finetune2=1,0,0,0,…,−1` | min | 35,031 | **0,574** | 35,133 | 0,9987 | JÓ |

A mezők sorrendje: Derítőfény, Csúcsfények, Árnyékok, (szín), Színhőmérséklet.

**Következtetés:** a Finomhangolás mindkét lánca mind a hat, felületről elérhető állásban a JPEG-újratömörítés zajszintjén adja vissza a Picasa kimenetét. A Picasa közben 19–51 ΔE-vel változtatott a képen. Fejlesztői teendő nincs. A legnagyobb maradék a két `min` eseté (0,50 és 0,57): itt a színhőmérséklet a tartomány alsó végén áll, a Derítőfény pedig 0.
