# A négy csatornánkénti LUT-os szűrő a küszöb alatt (RPi5) — #22

**Mérve:** 2026-09-24 · **gép:** Raspberry Pi 5 Model B, aarch64, 4 mag ·
**szkript:** `scripts/gpu_cpu_kesleltetes_meres.py` (ugyanaz, mint a
2026-09-18-i mérésé, hogy a két szám összevethető legyen)

## A kérdés

A 2026-09-18-i mérés (`2026-09-18-cpu-eloonezet-kesleltetes-22.md`) szerint
az `autocontrast`, `colortemp`, `enhance` és `warm` az előnézeti felbontáson
100 ms fölött fut. A jegy ezt GPU-úttal akarta megoldani.

## Amit a mérés közben kiderült

Mind a négy szűrő **csatornánkénti 256-os táblázat**, és a kódunk már ma is
táblázattal számolt. A költség tehát nem a számításé volt, hanem a táblázat
alkalmazásáé: a numpy-indexelés 2560 × 1707 képponton ~100 ms, az OpenCV
`LUT`-ja ugyanerre néhány ms. A `colortemp` ráadásul a táblázatot
képpontonként, int64-ben számolta újra.

⇒ A küszöb GPU nélkül, **bitre azonos** kimenettel elérhető, és a
tesztkörnyezetben ellenőrizhető is — a GPU-út ott el sem indul (#3070).

## A változás

| hely | előtte | utána |
|---|---|---|
| `curves.apply_channel_luts` | numpy-indexelés csatornánként + `np.stack` | `cv2.LUT` egy `(256, 3)` bájttáblával |
| `native_colortemp` | a képlet képpontonként, int64-ben | a képlet a 256 szintre egyszer, utána `cv2.LUT` |
| `ops._channel_black_white_points` és társa | három `np.bincount` | `cv2.calcHist`, 2^24 képpontos sávokban int64-be összegezve |

A float32-es `calcHist` 2^24 fölött már nem pontos egész, ezért sávokban
számol.

## Eredmény (medián, ms)

| szűrő | 2026-09-24 main | ez az ág | verdikt |
|---|---:|---:|---|
| `autocontrast` | 140,3 | **42,2** | azonnali |
| `colortemp` | 679,5 | **13,5** | azonnali |
| `enhance` | 135,2 | **20,1** | azonnali |
| `warm` | 97,1 | **5,3** | azonnali |
| `invert` | 4,1 | 4,0 | azonnali (nem érintett) |
| `crossprocess` | 2399 | 3737 | akadozik — **nem érintett**, külön jegy: #3570 |

A `crossprocess` szórása a két futás között nagy (min 2678, max 7368 ms); a
változás nem nyúl hozzá.

## Bizonyíték a bitre azonosságra

`tests/render/test_lut_gyorsitas_22.py`: a régi megvalósítás szó szerint,
mérceként él a próbában, és az új út véletlen képen, tartományon kívüli és
pontosan ,5-re eső LUT-értékeken, nem folytonos nézeten, a `colortemp`
48 paraméterpárján és a hisztogram több sávos útján is bitre ugyanazt adja.
