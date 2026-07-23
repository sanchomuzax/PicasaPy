# Feed-stresszmérés: 100k fotó a rácsban (#142)

A research-plan 1. pontjának lezárása: „50k–100k elemes rács-stresszteszt
és memóriamérés a valódi MVP-rácson". A mérések **ismételhetők** — a
számok újramérhetők bármely gépen (RPi5-ön is) az alábbi parancsokkal.

## Eszközök

| Réteg | Eszköz | Futtatás |
|---|---|---|
| Python (modell + provider) | `tools/benchmarks/bench_feed_100k.py` | `QT_QPA_PLATFORM=offscreen python3 tools/benchmarks/bench_feed_100k.py` |
| QML (valódi rács) | `tests/app/test_feed_stress_100k.py` | `PICASAPY_STRESS=1 QT_QPA_PLATFORM=offscreen timeout 300 python3 -m pytest tests/app/test_feed_stress_100k.py -q -s` |

A QML-stresszteszt alapból SKIP (env-kapcsolós), hogy a CI-t ne lassítsa;
a virtualizálás felső korlátját (cellaszám < 400) viszont assertként is
kikényszeríti, tehát lefuttatva regresszióvédelem is.

## Eredmények — felhő-konténer, x86-64, offscreen (2026-07-23, v0.4.41)

**Python-réteg (100 000 szintetikus rekord, minden 10. képen filters-lánc):**

| Mérés | Idő |
|---|---|
| `PhotoGridModel.set_photos` (első, teljes reset) | 0,001 s |
| `set_photos` változatlan tartalommal (#142 no-op gyorsút) | 0,000 s |
| `ThumbnailProvider.register_photos` (lusta filters-parse) | 0,401 s |
| tracemalloc-csúcs | 40,4 MB |
| RSS-delta (100k rekord + modell) | +88 MB |

**QML-réteg (valódi LightboxFeed, 100k képes egyetlen mappa — legrosszabb eset):**

| Mérés | Érték |
|---|---|
| `_show` (első betöltés + események lecsengése) | 0,21 s |
| Mély görgetés (50%-ra, majd az aljára) | 0,14 s |
| `_show` újra, változatlan feeddel (mappaváltás-gyorsút) | 0,16 s |
| Példányosított cellák fent / mélyre görgetve | **42 / 54** (korlát: <400) |
| RSS-delta a teszt alatt | +66 MB |

## Következtetések

- A #142-es virtualizálás után a cellaszám a mappamérettől FÜGGETLEN
  (~1 képernyőnyi + puffer); a virtualizálás előtti viselkedés 100k
  delegate-et példányosított volna (~gigabájtos textúra-igény).
- A `set_photos` no-op gyorsút és a lusta filters-parse hatása a
  Python-oldalon gyakorlatilag nullára viszi a háttér-szinkronok utáni
  újratöltés költségét, ha a tartalom nem változott.
- A memória-lábnyom 100k fotónál is ~90 MB nagyságrendű (rekordok +
  modell), ami RPi5-ön (4–8 GB) bőven belefér.
- **RPi5-újramérés:** a fenti számok x86-os konténerből származnak; a
  módszertan változatlan újrafuttatással RPi5-ön is mérhető — a
  cellaszám-korlát ott is azonos (hardverfüggetlen), az időket érdemes
  egyszer élesben is rögzíteni.
