# A Fókuszált pixelesítés eltérése az eredetitől: ok és mérés (#6691)

Dátum: 2026-11-08. A kiinduló mérés: `2026-11-08-6585-ujrabesorolas.md`,
"PicnikFocalPixelate" szakasz (9 eset, 8 eltérő). A leírás helye:
`docs/specs/filters-decoded.md`, "A `PicnikFocalPixelate` önálló eltérésének oka".

## Módszer

- Eredeti exportok: a `picasa-colab-jobs` 403, 408-414 és 429 kiadása
  (`export__kNN.jpg`, 1280 px széles, Picasa 3.9, 4:2:0, azonos kvantálótáblák).
- Források: a `kellekek` kiadás `minta-kombinalt.tar.gz` (SHA256
  `eaebec870e698433cb62a56c54e0c256c6752692de87101614ca403d071d5557`, egyezik a
  `SHA256SUMS`-szal).
- Összevetés: `tools/golden/compare_render.py` módszere (SSIM, ΔE CIE76), a renderelt
  képet az export JPEG-beállításával újrakódolva (#4940, #6585).

## 1. Blokkrács: a kicsinyített méret kerekítése

Teljes kép, nyers render (nincs JPEG-újrakódolás), ΔE átlag. A "csonkolt" a régi
`int(W/Impact)`, a "legjobb" a (szélesség, magasság) jelöltek ±2..+3 tartományából a
legkisebb ΔE-jű.

| Lánc | Kép | `W/I` | `H/I` | csonkolt rács | ΔE | legjobb rács | ΔE | `trunc(v + 0,5)` |
|---|---|---:|---:|---|---:|---|---:|---|
| lanc-0142 | k02 | 29,958 | 16,851 | (29, 16) | 2,398 | (30, 17) | 1,325 | (30, 17) |
| lanc-0048 | k08 | 244,928 | 163,221 | (244, 163) | 2,700 | (245, 163) | 2,184 | (245, 163) |
| lanc-0124 | k04 | 35,328 | 23,543 | (35, 23) | 3,105 | (35, 24) | 1,158 | (35, 24) |
| lanc-0067 | k07 | 250,468 | 166,913 | (250, 166) | 1,466 | (250, 167) | 1,120 | (250, 167) |
| lanc-0022 | k02 | 33,453 | 18,817 | (33, 18) | 2,540 | (33, 19) | 1,321 | (33, 19) |
| lanc-0088 | k08 | 69,673 | 46,430 | (69, 46) | 2,856 | (70, 46) | 1,999 | (70, 46) |
| lanc-0115 | k05 | 35,990 | 22,691 | (35, 22) | 3,252 | (36, 23) | 1,136 | (36, 23) |
| lanc-0175 | k05 | 18,552 | 11,696 | (18, 11) | 3,548 | (19, 12) | 1,684 | (19, 12) |
| lanc-0190 | k10 | 207,221 | 138,094 | (207, 138) | 1,444 | (207, 138) | 1,444 | (207, 138) |

Mind a 9 esetben egyetlen rács adja a legkisebb ΔE-t, és az a kerekített méret. A
lanc-0190 rácsa a két szabály szerint azonos, ott a hiba a keverésben volt. A
blokkhatár-profil is ezt mutatja: lanc-0067-nél a Picasa sorhatárai 593, 598, 603,
...; a csonkolt rácsé 591, 596, 601, ...

## 2. Keverés: Fade és maszk

A kerekített rácson a keverési változatok, teljes kép, JPEG-újrakódolással, ΔE átlag:

| Lánc | Fade | float lerp (régi) | maszk, utána Fade (egész) | **Fade, utána maszk (egész)** | float maszk, natív Fade |
|---|---:|---:|---:|---:|---:|
| lanc-0142 | 63,2 | 0,689 | 0,038 | **0,020** | 0,039 |
| lanc-0048 | 45,9 | 0,952 | 0,214 | **0,096** | 0,212 |
| lanc-0124 | 4,7 | 0,617 | 0,302 | **0,081** | 0,286 |
| lanc-0067 | 22,6 | 0,570 | 0,093 | **0,008** | 0,076 |
| lanc-0022 | 38,2 | 0,682 | 0,306 | **0,123** | 0,301 |
| lanc-0088 | 36,2 | 0,708 | 0,047 | **0,041** | 0,049 |
| lanc-0115 | 11,8 | 0,551 | 0,167 | **0,073** | 0,155 |
| lanc-0175 | 40,7 | 0,682 | 0,086 | **0,027** | 0,087 |
| lanc-0190 | 23,1 | 0,683 | 0,020 | **0,019** | 0,020 |

A régi keverés a pixelezett részen mindegyik csatornán átlagosan +0,9..+1,1 szinttel
világosabb (a kerekített rácson is). A natív `alpha_blend` (`(b·(255-w) + t·w) >> 8`,
`w = trunc(256α) - 1`) súlyainak összege 255, a `>> 8` csonkít: ez adja az egy szintet.

## 3. A tárolt ablakok (a tesztben)

A teszt 160 x 128-as ablakokat vet össze (ld. `tests/render/test_focal_pixelate_golden_6691.py`).
ΔE átlag / p99 az ablakban, JPEG-újrakódolással:

| Lánc | csonkolás + float (régi) | kerekítés + float | csonkolás + natív | **kerekítés + natív (új)** |
|---|---:|---:|---:|---:|
| lanc-0142 | 2,128 / 7,44 | 0,782 / 3,00 | 1,954 / 7,81 | **0,257 / 2,21** |
| lanc-0048 | 1,588 / 6,29 | 1,077 / 4,33 | 1,512 / 6,49 | **0,726 / 3,93** |
| lanc-0124 | 10,446 / 30,41 | 1,134 / 3,76 | 10,429 / 30,29 | **0,711 / 3,56** |
| lanc-0067 | 2,354 / 12,13 | 0,707 / 2,19 | 2,288 / 12,19 | **0,061 / 1,23** |
| lanc-0022 | 2,739 / 8,54 | 1,201 / 5,14 | 2,617 / 8,82 | **0,716 / 3,46** |
| lanc-0088 | 1,583 / 7,27 | 0,705 / 2,41 | 1,547 / 7,30 | **0,000 / 0,00** |
| lanc-0115 | 6,147 / 23,76 | 0,842 / 2,99 | 6,126 / 24,05 | **0,314 / 2,24** |
| lanc-0175 | 3,733 / 11,50 | 0,732 / 2,61 | 3,755 / 11,18 | **0,190 / 2,29** |
| lanc-0190 | 0,965 / 3,02 | 0,965 / 3,02 | 0,014 / 0,88 | **0,014 / 0,88** |

A teljesen pixelezett részen (maszk >= 0,99) az új render ΔE-je 0,000-0,037 hat
ablakban (>= 5000 képpont), a lanc-0088 ablakában bitre egyező.

## 4. Eredmény a teljes képen (előtte és utána)

| Lánc | Feladat/kép | SSIM előtte | ΔE előtte | SSIM utána | ΔE utána | Ítélet utána |
|---|---|---:|---:|---:|---:|---|
| lanc-0142 | job-408/k02 | 0,97293 | 2,150 | 0,99995 | 0,020 | közelítés |
| lanc-0048 | job-408/k08 | 0,94671 | 2,150 | 0,99953 | 0,096 | közelítés |
| lanc-0124 | job-409/k04 | 0,94045 | 2,993 | 0,99893 | 0,081 | közelítés |
| lanc-0067 | job-410/k07 | 0,93147 | 1,238 | 0,99986 | 0,008 | közelítés |
| lanc-0022 | job-411/k02 | 0,95955 | 2,272 | 0,99849 | 0,123 | közelítés |
| lanc-0088 | job-413/k08 | 0,95864 | 2,259 | 0,99976 | 0,041 | közelítés |
| lanc-0115 | job-414/k05 | 0,90572 | 3,135 | 0,99897 | 0,073 | közelítés |
| lanc-0175 | job-429/k05 | 0,96717 | 3,172 | 0,99975 | 0,027 | közelítés |
| lanc-0190 | job-403/k10 | 0,99282 | 0,683 | 0,99949 | 0,019 | közelítés |

## 5. Nyitott: az átmeneti gyűrű bájtszintű képlete

Az átmeneti gyűrűben (maszk 0 és 1 között) az ablakokban ΔE 0,09-0,73 marad; ahol a
maszk 0 vagy 1, ott nincs. A maszk négy bájtszintű változatát próbáltam (a spec kétmegállós
színátmenet-képletével: a belső megálló `csonk(255 · inner / R)`; csonkoló vagy
kerekítő bájt; középponttal és a pixel sarkával), ΔE átlag a 9 ablakon:

| változat | átlag |
|---|---:|
| jelenlegi (`rint(255 · lineáris)`) | 0,332 |
| csonkoló bájt, pixelközép | 0,313 |
| kerekítő bájt, pixelközép | 0,375 |
| csonkoló bájt, pixelsarok | 0,223 |
| kerekítő bájt, pixelsarok | 0,298 |

Egyik sem bitre egyező, és egyik sem javít mindegyik ablakon, ezért nem került a kódba.
Az egész maszk-keverés (`masked_blend`) a gyűrűben így is jobb a régi float lerpnél
(0,09-0,73 a 0,37-1,19 helyett).
