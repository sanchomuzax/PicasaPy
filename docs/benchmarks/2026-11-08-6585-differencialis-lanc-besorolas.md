# #6585 - Differenciális szűrőláncok újramérése

**Mérés dátuma:** 2026-11-08  
**Main commit:** `94623605fe73affb3fe1a1833499117e43ab1762`

## Adat és módszer

A saját oldalt a jelenlegi kóddal az `r6585i/lancok.json` 200 rekordjából rendereltem. Ez a jegyzék 20 köteget tartalmaz, kötegenként 10 képpel; a job JSON-okban és INI-kben szereplő `filters=` értékeket gépileg összevetettem a jegyzékkel. Minden kötegben megvan a tíz megfelelő eredeti `export__kNN.jpg`, és a k01-k10 forráskép is elérhető. A 200 rekord, a bemeneti INI és az eredeti export párosítása ellenőrizve: PASS.

A küszöb a `tools/golden/compare_render.py` meglévő `Thresholds()` értéke: `pixel_tol=1`, `frac_tol=0.002`, `ssim_min=0.98`, `de_mean_max=2.0`. A saját PNG-ket az összevető az eredeti JPEG mintavételezésével és kvantálótábláival kódolja újra. Az `egyezik` a meglévő `pixelhű` vagy `közelítés` ítéletet jelenti.

```sh
mkdir -p .tmp/6585-r6585i-main-94623605
cp .bt/meres/r6585i/lancok.json .tmp/6585-r6585i-main-94623605/lancok.json
python3 scripts/differencialis_lanc.py sajat --be .tmp/6585-r6585i-main-94623605 --nevjegyzek .bt/meres/kombinalt/nevjegyzek.json --kepek .bt/meres/kombinalt/kepek
python3 scripts/differencialis_lanc.py osszevet --be .tmp/6585-r6585i-main-94623605 --eredeti .bt/meres/r6585i/eredeti
```

## Eredmény

**200 lánc:** 168 egyezik, 32 eltér; helyi hiba, hibás export és hiányzó export: 0.
Az elérhető korábbi `.bt/meres/r6585i/eredmeny.csv` fájlhoz képest a láncítéletek változása 0/200, a tárolt SSIM/ΔE mezőké 0/200. Az újramérés tehát 0 eltérést tüntetett el: a korábbi 32-ből mind a 32 megmaradt.

| Lánc | Kép | SSIM | ΔE átlag | Eredmény | a/b/c |
|---|---|---:|---:|---|:---:|
| lanc-0001 | k01.jpg | 0.99784 | 0.318 | egyezik | - |
| lanc-0002 | k02.jpg | 0.99559 | 0.778 | egyezik | - |
| lanc-0003 | k03.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0004 | k04.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0005 | k05.jpg | 0.76627 | 29.271 | eltér | c |
| lanc-0006 | k06.jpg | 0.99914 | 0.221 | egyezik | - |
| lanc-0007 | k07.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0008 | k08.jpg | 0.99955 | 0.288 | egyezik | - |
| lanc-0009 | k09.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0010 | k10.jpg | 0.84817 | 2.624 | eltér | c |
| lanc-0011 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0012 | k02.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0013 | k03.jpg | 0.99927 | 0.057 | egyezik | - |
| lanc-0014 | k04.jpg | 0.99548 | 0.140 | egyezik | - |
| lanc-0015 | k05.jpg | 0.99995 | 0.004 | egyezik | - |
| lanc-0016 | k06.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0017 | k07.jpg | 0.99933 | 0.042 | egyezik | - |
| lanc-0018 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0019 | k09.jpg | 0.98210 | 1.847 | egyezik | - |
| lanc-0020 | k10.jpg | 0.99769 | 0.099 | egyezik | - |
| lanc-0021 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0022 | k02.jpg | 0.93721 | 3.036 | eltér | c |
| lanc-0023 | k03.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0024 | k04.jpg | 0.99973 | 0.059 | egyezik | - |
| lanc-0025 | k05.jpg | 0.98793 | 0.822 | egyezik | - |
| lanc-0026 | k06.jpg | 0.99999 | 0.000 | egyezik | - |
| lanc-0027 | k07.jpg | 0.99952 | 0.044 | egyezik | - |
| lanc-0028 | k08.jpg | 0.99900 | 0.428 | egyezik | - |
| lanc-0029 | k09.jpg | 0.99036 | 1.250 | egyezik | - |
| lanc-0030 | k10.jpg | 0.98434 | 1.927 | egyezik | - |
| lanc-0031 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0032 | k02.jpg | 0.98941 | 0.525 | egyezik | - |
| lanc-0033 | k03.jpg | 0.99997 | 0.012 | egyezik | - |
| lanc-0034 | k04.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0035 | k05.jpg | 0.99225 | 1.044 | egyezik | - |
| lanc-0036 | k06.jpg | 0.99984 | 0.017 | egyezik | - |
| lanc-0037 | k07.jpg | 0.99939 | 0.047 | egyezik | - |
| lanc-0038 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0039 | k09.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0040 | k10.jpg | 0.98780 | 1.035 | egyezik | - |
| lanc-0041 | k01.jpg | 0.99104 | 0.707 | egyezik | - |
| lanc-0042 | k02.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0043 | k03.jpg | 0.76992 | 2.031 | eltér | c |
| lanc-0044 | k04.jpg | 0.99632 | 0.512 | egyezik | - |
| lanc-0045 | k05.jpg | 0.43336 | 93.951 | eltér | b |
| lanc-0046 | k06.jpg | 0.99924 | 0.262 | egyezik | - |
| lanc-0047 | k07.jpg | 0.98697 | 0.523 | egyezik | - |
| lanc-0048 | k08.jpg | 0.94329 | 2.260 | eltér | c |
| lanc-0049 | k09.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0050 | k10.jpg | 0.98972 | 0.495 | egyezik | - |
| lanc-0051 | k01.jpg | 0.99655 | 0.898 | egyezik | - |
| lanc-0052 | k02.jpg | 0.41064 | 139.805 | eltér | a |
| lanc-0053 | k03.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0054 | k04.jpg | 0.99146 | 0.539 | egyezik | - |
| lanc-0055 | k05.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0056 | k06.jpg | 0.99329 | 2.636 | eltér | c |
| lanc-0057 | k07.jpg | 0.99848 | 0.029 | egyezik | - |
| lanc-0058 | k08.jpg | 0.99981 | 0.032 | egyezik | - |
| lanc-0059 | k09.jpg | 0.99784 | 0.625 | egyezik | - |
| lanc-0060 | k10.jpg | 0.86391 | 2.067 | eltér | c |
| lanc-0061 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0062 | k02.jpg | 0.98657 | 0.782 | egyezik | - |
| lanc-0063 | k03.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0064 | k04.jpg | 0.98455 | 1.237 | egyezik | - |
| lanc-0065 | k05.jpg | 0.92529 | 2.177 | eltér | c |
| lanc-0066 | k06.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0067 | k07.jpg | 0.90360 | 3.180 | eltér | c |
| lanc-0068 | k08.jpg | 0.99912 | 0.169 | egyezik | - |
| lanc-0069 | k09.jpg | 0.99931 | 0.087 | egyezik | - |
| lanc-0070 | k10.jpg | 0.99293 | 0.712 | egyezik | - |
| lanc-0071 | k01.jpg | 0.99366 | 0.441 | egyezik | - |
| lanc-0072 | k02.jpg | 0.99627 | 0.162 | egyezik | - |
| lanc-0073 | k03.jpg | 0.99917 | 0.042 | egyezik | - |
| lanc-0074 | k04.jpg | 0.99649 | 0.690 | egyezik | - |
| lanc-0075 | k05.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0076 | k06.jpg | 0.99758 | 0.127 | egyezik | - |
| lanc-0077 | k07.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0078 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0079 | k09.jpg | 0.99503 | 0.669 | egyezik | - |
| lanc-0080 | k10.jpg | 0.80866 | 91.311 | eltér | c |
| lanc-0081 | k01.jpg | 0.99975 | 0.122 | egyezik | - |
| lanc-0082 | k02.jpg | 0.99059 | 1.121 | egyezik | - |
| lanc-0083 | k03.jpg | 0.99534 | 0.196 | egyezik | - |
| lanc-0084 | k04.jpg | 0.98678 | 0.731 | egyezik | - |
| lanc-0085 | k05.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0086 | k06.jpg | 0.99485 | 0.676 | egyezik | - |
| lanc-0087 | k07.jpg | 0.98434 | 1.650 | egyezik | - |
| lanc-0088 | k08.jpg | 0.93046 | 1.515 | eltér | c |
| lanc-0089 | k09.jpg | 0.98587 | 2.142 | eltér | c |
| lanc-0090 | k10.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0091 | k01.jpg | 0.99462 | 0.788 | egyezik | - |
| lanc-0092 | k02.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0093 | k03.jpg | 0.99264 | 0.374 | egyezik | - |
| lanc-0094 | k04.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0095 | k05.jpg | 0.65876 | 1.011 | eltér | c |
| lanc-0096 | k06.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0097 | k07.jpg | 0.99768 | 0.132 | egyezik | - |
| lanc-0098 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0099 | k09.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0100 | k10.jpg | 0.99136 | 0.438 | egyezik | - |
| lanc-0101 | k01.jpg | 0.97000 | 49.235 | eltér | c |
| lanc-0102 | k02.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0103 | k03.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0104 | k04.jpg | 0.98542 | 0.410 | egyezik | - |
| lanc-0105 | k05.jpg | 0.95417 | 3.585 | eltér | c |
| lanc-0106 | k06.jpg | 0.98955 | 0.957 | egyezik | - |
| lanc-0107 | k07.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0108 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0109 | k09.jpg | 0.99948 | 0.274 | egyezik | - |
| lanc-0110 | k10.jpg | 0.99996 | 0.030 | egyezik | - |
| lanc-0111 | k01.jpg | 0.99888 | 0.334 | egyezik | - |
| lanc-0112 | k02.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0113 | k03.jpg | 0.97662 | 0.824 | eltér | c |
| lanc-0114 | k04.jpg | 0.99728 | 0.198 | egyezik | - |
| lanc-0115 | k05.jpg | 0.88714 | 3.408 | eltér | c |
| lanc-0116 | k06.jpg | 0.76752 | 0.881 | eltér | c |
| lanc-0117 | k07.jpg | 0.95824 | 1.639 | eltér | c |
| lanc-0118 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0119 | k09.jpg | 0.95999 | 1.077 | eltér | c |
| lanc-0120 | k10.jpg | 0.99992 | 0.011 | egyezik | - |
| lanc-0121 | k01.jpg | 0.99272 | 1.539 | egyezik | - |
| lanc-0122 | k02.jpg | 0.99228 | 0.615 | egyezik | - |
| lanc-0123 | k03.jpg | 0.99444 | 0.367 | egyezik | - |
| lanc-0124 | k04.jpg | 0.89940 | 11.270 | eltér | c |
| lanc-0125 | k05.jpg | 0.98689 | 1.233 | egyezik | - |
| lanc-0126 | k06.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0127 | k07.jpg | 0.99437 | 0.787 | egyezik | - |
| lanc-0128 | k08.jpg | 0.99508 | 0.365 | egyezik | - |
| lanc-0129 | k09.jpg | 0.99986 | 0.172 | egyezik | - |
| lanc-0130 | k10.jpg | 0.99892 | 0.370 | egyezik | - |
| lanc-0131 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0132 | k02.jpg | 0.98634 | 1.044 | egyezik | - |
| lanc-0133 | k03.jpg | 0.99379 | 0.282 | egyezik | - |
| lanc-0134 | k04.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0135 | k05.jpg | 0.98576 | 0.945 | egyezik | - |
| lanc-0136 | k06.jpg | 0.99612 | 0.151 | egyezik | - |
| lanc-0137 | k07.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0138 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0139 | k09.jpg | 0.99561 | 1.159 | egyezik | - |
| lanc-0140 | k10.jpg | 0.90142 | 2.564 | eltér | c |
| lanc-0141 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0142 | k02.jpg | 0.94643 | 2.437 | eltér | c |
| lanc-0143 | k03.jpg | 0.99386 | 0.299 | egyezik | - |
| lanc-0144 | k04.jpg | 0.83592 | 62.688 | eltér | c |
| lanc-0145 | k05.jpg | 0.98208 | 1.005 | egyezik | - |
| lanc-0146 | k06.jpg | 0.99329 | 0.156 | egyezik | - |
| lanc-0147 | k07.jpg | 0.99720 | 0.983 | egyezik | - |
| lanc-0148 | k08.jpg | 0.99999 | 0.000 | egyezik | - |
| lanc-0149 | k09.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0150 | k10.jpg | 0.99926 | 0.114 | egyezik | - |
| lanc-0151 | k01.jpg | 0.99839 | 0.221 | egyezik | - |
| lanc-0152 | k02.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0153 | k03.jpg | 0.98965 | 0.464 | egyezik | - |
| lanc-0154 | k04.jpg | 0.99999 | 0.000 | egyezik | - |
| lanc-0155 | k05.jpg | 0.99995 | 0.010 | egyezik | - |
| lanc-0156 | k06.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0157 | k07.jpg | 0.99568 | 0.799 | egyezik | - |
| lanc-0158 | k08.jpg | 0.99944 | 0.384 | egyezik | - |
| lanc-0159 | k09.jpg | 0.99999 | 0.000 | egyezik | - |
| lanc-0160 | k10.jpg | 0.99999 | 0.007 | egyezik | - |
| lanc-0161 | k01.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0162 | k02.jpg | 0.99523 | 0.377 | egyezik | - |
| lanc-0163 | k03.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0164 | k04.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0165 | k05.jpg | 0.99721 | 0.467 | egyezik | - |
| lanc-0166 | k06.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0167 | k07.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0168 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0169 | k09.jpg | 0.91502 | 2.178 | eltér | c |
| lanc-0170 | k10.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0171 | k01.jpg | 0.99076 | 1.020 | egyezik | - |
| lanc-0172 | k02.jpg | 0.98594 | 1.085 | egyezik | - |
| lanc-0173 | k03.jpg | 0.99343 | 0.400 | egyezik | - |
| lanc-0174 | k04.jpg | 0.99893 | 0.011 | egyezik | - |
| lanc-0175 | k05.jpg | 0.97040 | 3.666 | eltér | c |
| lanc-0176 | k06.jpg | 0.98951 | 0.266 | egyezik | - |
| lanc-0177 | k07.jpg | 0.99579 | 0.183 | egyezik | - |
| lanc-0178 | k08.jpg | 0.99218 | 3.003 | eltér | c |
| lanc-0179 | k09.jpg | 0.99014 | 0.656 | egyezik | - |
| lanc-0180 | k10.jpg | 0.99992 | 0.127 | egyezik | - |
| lanc-0181 | k01.jpg | 0.99269 | 0.590 | egyezik | - |
| lanc-0182 | k02.jpg | 0.99618 | 0.793 | egyezik | - |
| lanc-0183 | k03.jpg | 0.99651 | 0.192 | egyezik | - |
| lanc-0184 | k04.jpg | 0.98724 | 1.042 | egyezik | - |
| lanc-0185 | k05.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0186 | k06.jpg | 0.97919 | 1.075 | eltér | c |
| lanc-0187 | k07.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0188 | k08.jpg | 0.99728 | 0.734 | egyezik | - |
| lanc-0189 | k09.jpg | 0.99839 | 0.303 | egyezik | - |
| lanc-0190 | k10.jpg | 0.98653 | 37.440 | eltér | c |
| lanc-0191 | k01.jpg | 0.99438 | 0.336 | egyezik | - |
| lanc-0192 | k02.jpg | 0.99605 | 0.441 | egyezik | - |
| lanc-0193 | k03.jpg | 0.99682 | 0.628 | egyezik | - |
| lanc-0194 | k04.jpg | 0.99998 | 0.021 | egyezik | - |
| lanc-0195 | k05.jpg | 0.98127 | 1.618 | egyezik | - |
| lanc-0196 | k06.jpg | 0.86683 | 0.473 | eltér | c |
| lanc-0197 | k07.jpg | 0.99996 | 0.004 | egyezik | - |
| lanc-0198 | k08.jpg | 1.00000 | 0.000 | egyezik | - |
| lanc-0199 | k09.jpg | 0.98875 | 0.555 | egyezik | - |
| lanc-0200 | k10.jpg | 0.99999 | 0.007 | egyezik | - |

## A 32 eltérő lánc besorolása

- **a - 1 lánc:** legalább egy szűrő azonos bemeneten és pontos paraméterrel önállóan is eltér.
- **b - 1 lánc:** minden szűrő külön-külön egyezik, de a lánc eltér; ez a mérés kölcsönhatást támaszt alá.
- **c - 30 lánc:** hiányzik az összes tagra azonos bemenetű egyszűrős mérés, vagy véletlen szemcse miatt nem lehet képpontosan besorolni. Ezeknél nem állítok kölcsönhatást.

| Lánc | Kép | SSIM | ΔE átlag | a/b/c | Egyszűrős bizonyíték | `filters=` |
|---|---|---:|---:|:---:|---|---|
| lanc-0005 | k05.jpg | 0.76627 | 29.271 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;colorfix=1,ffc0ea7e,-0.140316;colorfix=1,ff680664,-0.249688;LocalContrast=1,13.446470,1.197972;rainbow=1,229.438578;Holga=1,63.516887,91.816275,29.159809;` |
| lanc-0010 | k10.jpg | 0.84817 | 2.624 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `PencilSketch=1,3.844177,163.752261,80.619866;grain2=1;backlight=1,0.015514;` |
| lanc-0022 | k02.jpg | 0.93721 | 3.036 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `PicnikFocalPixelate=1,0.596101,0.315251,38.262959,67.621441,30.602824,38.221530,0;dir_sat=1,0.570065,0.531207;unsharp2=1,1.889519;enhance=1;` |
| lanc-0043 | k03.jpg | 0.76992 | 2.031 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 2 véletlen szemcse-effektet a pixelmérésből kizártam | `unsharp=1,0.429447;PicnikGrain=1,9.856920,1;grain2=1;TwoTone=1,-34.649025,42.816806,49.327950,00cc1cd3,00f3ee8e;` |
| lanc-0045 | k05.jpg | 0.43336 | 93.951 | b | Minden tag egyszűrős mérése egyezik: egy-005, egy-006, egy-007, egy-008 | `colortemp=1,-0.233761,0.848145;Pixelate=1,134.455942,6.872625,47.676487;dir_brite=1,-0.884987,-0.873954;DropShadow=1,5.692017,241.473639,41.331983,00c9dd31,005df725,98.258864;` |
| lanc-0048 | k08.jpg | 0.94329 | 2.260 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `autolight=1;PicnikFocalPixelate=1,0.754539,0.257084,5.226035,44.746379,30.137856,45.902113,0;` |
| lanc-0052 | k02.jpg | 0.41064 | 139.805 | a | egy-001 (SSIM 0.74630, ΔE 115.147); egy-004 (SSIM 0.85067, ΔE 1.201); régi hex-szín-elöl colorfix-sorrendet tartalmaz | `colorfix=1,ffca3cff,-0.164578;QuantizePalette=1,26.911384,95.029648,32.254115;Matte=1,17.132769,1.798025,76.264178,005b4ee5;triple2=1,0.246858,0.780767,0.172505;` |
| lanc-0056 | k06.jpg | 0.99329 | 2.636 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `gamma=1,0.480449;TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;linblur=1,0.466086,0.005391,9.064718;rainbow=1,244.890456;triple=1,-0.207838,-0.406449,0.214067;` |
| lanc-0060 | k10.jpg | 0.86391 | 2.067 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `Vignette=1,48.277238,1.527099,84.880421,00c7828a;grain2=1;DropShadow=1,20.235157,164.620360,83.506034,007d27c2,009d04a2,3.158258;` |
| lanc-0065 | k05.jpg | 0.92529 | 2.177 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `Boost=1,36.252043;shadow=1,0.764285,0.655234,0.163184;grain2=1;ansel=1,ff25d557;` |
| lanc-0067 | k07.jpg | 0.90360 | 3.180 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `PicnikFocalPixelate=1,0.379377,0.280311,5.110434,52.012805,56.186495,22.578563,0;Holga=1,27.444017,76.630990,12.639445;LocalContrast=1,18.977791,2.424472;` |
| lanc-0080 | k10.jpg | 0.80866 | 91.311 | c | 1 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `colorfix=1,ff773aed,0.352651;unsharp=1,0.385234;` |
| lanc-0088 | k08.jpg | 0.93046 | 1.515 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `PicnikFocalPixelate=1,0.257873,0.777093,18.371648,16.955073,83.975403,36.162119,0;unsharp=1,0.811594;PencilSketch=1,2.433558,9.770045,31.821444;radtint=1,0.113828,0.081816,0.197103,ffe11e1b;` |
| lanc-0089 | k09.jpg | 0.98587 | 2.142 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `IR=1,6.505770;radsat=1,0.935702,0.276913,-0.462013,0.789662;warm=1;triple2=1,0.127180,0.190318,0.055157;` |
| lanc-0095 | k05.jpg | 0.65876 | 1.011 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `sepia=1;ansel=1,ff06c7fb;triple2=1,0.613640,0.987095,0.051496;dir_sharp=1,-0.767675,0.017529;` |
| lanc-0101 | k01.jpg | 0.97000 | 49.235 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `IR=1,54.049313;colorfix=1,ff2739b2,-0.326245;Soften=1,95.657333,30.076586;unsharp=1,0.559595;dir_tint=1,0.176344,0.148523,0.298786,0.227118,ff2d5a0f;autocontrast=1;` |
| lanc-0105 | k05.jpg | 0.95417 | 3.585 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `IR=1,58.632346;contrast=1,0.357453;triple2=1,0.794439,0.822413,0.416504;Holga=1,49.395584,4.298524,95.564966;` |
| lanc-0113 | k03.jpg | 0.97662 | 0.824 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `radsat=1,0.495786,0.199929,0.644282,0.226320;glow2=1,0.938053,7.426568;HeatMap=1,-166.268420,33.668530;Sixties=1,24.277937,00831e27,0;HDR=1,25.214587,5.596100,24.480760;warm=1;` |
| lanc-0115 | k05.jpg | 0.88714 | 3.408 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `glow=1,0.240375,86.608439;grain=1;PicnikFocalPixelate=1,0.734580,0.362004,35.565019,64.583751,83.643288,11.843983,0;unsharp2=1,0.890722;` |
| lanc-0116 | k06.jpg | 0.76752 | 0.881 | c | 6 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `Soften=1,81.679116,95.722213;glow=1,0.220319,29.085845;triple2=1,0.500244,0.837205,0.579954;CrossProcess=1,22.173648;unsharp2=1,0.973675;sepia=1;` |
| lanc-0117 | k07.jpg | 0.95824 | 1.639 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `grain2=1;glow=1,0.943897,17.486931;HeatMap=1,-101.723152,46.384101;CrossProcess=1,1.191213;radblur=1,0.195302,0.408240,-0.055610,-0.967370;` |
| lanc-0119 | k09.jpg | 0.95999 | 1.077 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `whitept=1,ff12141f;grain=1;Comicize=1,97.076368,83.882062,99.079918;Pixelate=1,72.192947,3.126227,5.346142;` |
| lanc-0124 | k04.jpg | 0.89940 | 11.270 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `colorfix=1,ff50b5af,-0.481740;PicnikFocalPixelate=1,0.457857,0.092015,36.231898,86.737197,46.345083,4.704272,0;autocontrast=1;radsat=1,0.466994,0.173746,0.209913,0.696717;grain2=1;` |
| lanc-0140 | k10.jpg | 0.90142 | 2.564 | c | 4 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `HDR=1,65.299969,1.626753,76.860461;dir_sharp=1,-0.397475,0.968720;backlight=1,0.832331;warm=1;grain=1;` |
| lanc-0142 | k02.jpg | 0.94643 | 2.437 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `PicnikFocalPixelate=1,0.698914,0.945061,42.726991,31.797369,60.493888,63.244677,0;QuantizePalette=1,26.866748,28.222955,86.942047;triple3=1,0.554400,0.413470,0.290744;PicnikGrain=1,16.060125,1;` |
| lanc-0144 | k04.jpg | 0.83592 | 62.688 | c | 1 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `rainbow=1,157.860004;HDR=1,18.018149,2.319506,99.392683;sat=1,-0.245977;colorfix=1,ff3de652,0.486719;` |
| lanc-0169 | k09.jpg | 0.91502 | 2.178 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés; 1 véletlen szemcse-effektet a pixelmérésből kizártam | `autolight=1;autocolor=1;grain=1;` |
| lanc-0175 | k05.jpg | 0.97040 | 3.666 | c | 6 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `LocalContrast=1,2.946479,1.789300;whitept=1,ff58c424;CrossProcess=1,58.866455;Neon=1,9.673465,00d24fdc;Matte=1,20.730945,1.532521,86.826862,005f3295;PicnikFocalPixelate=1,0.423806,0.517357,68.995914,38.741837,79.479973,40.691224,0;` |
| lanc-0178 | k08.jpg | 0.99218 | 3.003 | c | 2 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `triple3=1,0.218352,0.361045,0.311731;triple2=1,0.218250,0.303895,0.317896;dir_sat=1,0.037718,-0.414407;colortemp=1,-0.389167,0.612947;` |
| lanc-0186 | k06.jpg | 0.97919 | 1.075 | c | 3 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `colorfix=1,ff789687,0.154606;ansel=1,ff3758f3;unsharp2=1,1.569590;` |
| lanc-0190 | k10.jpg | 0.98653 | 37.440 | c | 1 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `autocolor=1;radtint=1,0.886560,0.666967,0.816773,ffb6ba2a;colorfix=1,ffccfb8f,-0.256467;PicnikFocalPixelate=1,0.188181,0.532512,6.176970,4.362248,97.625661,23.072798,0;` |
| lanc-0196 | k06.jpg | 0.86683 | 0.473 | c | 6 taghoz nincs azonos bemeneten és paraméterrel egyszűrős mérés | `ansel=1,ff2580a0;blur=1,0.471994;QuantizePalette=1,8.678893,3.935281,52.351552;dir_sharp=1,-0.326623,0.790902;triple2=1,0.632434,0.867620,0.690895;CrossProcess=1,28.019592;` |

## A #6617/#6618 utáni egyszűrős eredmények

A `r6585f` 64 egyszűrős esetét is újrarendereltem és ugyanazzal az eredeti Picasa-exporttal hasonlítottam össze: 61 egyezik, 3 eltér (kihagyott/hiányzó: 0). Az archív CSV 46/18-at rögzített; most 15 korábbi eltérés egyezik és 0 új eltérés nincs. Az eltűnt egyszűrős eltérések azonosítói: `egy-002`, `egy-008`, `egy-010`, `egy-014`, `egy-019`, `egy-022`, `egy-025`, `egy-026`, `egy-028`, `egy-029`, `egy-032`, `egy-039`, `egy-045`, `egy-046`, `egy-048`.

| Eset | Archív mérés | Mostani mérés | Láncszintű eredmény |
|---|---|---|---|
| `DropShadow` (`egy-008`, a #6618 paramétereivel) | SSIM 0.52615, ΔE 8.079, eltér | SSIM 1.00000, ΔE 0.000, egyezik | `lanc-0045` továbbra is eltér (SSIM 0.43336, ΔE 93.951); a négy önállóan egyező tag alapján `b`. |
| `colorfix` (`egy-001`, a #6617 mérési sora) | SSIM 0.76280, ΔE 115.272, eltér | SSIM 0.74630, ΔE 115.147, eltér | `lanc-0052` továbbra is eltér (SSIM 0.41064, ΔE 139.805); a `triple2` önálló mérése is eltér, ezért `a`. |

A jelenlegi egyszűrős eltérések:

| Azonosító | Szűrő | SSIM | ΔE átlag |
|---|---|---:|---:|
| egy-001 | `colorfix=1,ffca3cff,-0.164578;` | 0.74630 | 115.147 |
| egy-004 | `triple2=1,0.246858,0.780767,0.172505;` | 0.85067 | 1.201 |
| egy-061 | `PencilSketch=1,4.337774,181.320163,60.058559;` | 0.97095 | 0.982 |

A 15 egyszűrős státuszváltozás közül csak a `DropShadow`-próba tartozik közvetlenül a #6618-hoz. A fennmaradó 14 változást nem tulajdonítom automatikusan a #6617/#6618 javításoknak: az újraértékelés a jelenlegi referencia-JPEG kódolást használja.

## Adatminőségi megjegyzés

Az `r6585i/lancok.json` 9 olyan `colorfix` műveletet tartalmaz 8 láncban, amelynek első paramétere hex szín (`colorfix=1,ff...,hőmérséklet`), vagyis a #6617 előtti sorrendet használja. A #6617-höz tartozó job-407 mérés és a jelenlegi kód tesztje szerint az eredeti Picasa ezt az alakot figyelmen kívül hagyja, míg a PicasaPy régi mentésként beolvassa és alkalmazza. Ezeket a fagyasztott adatbeli sorokat mértem le, de mai, érvényes `colorfix`-láncok eredményeként nem szabad értelmezni. A megadott munkafeladatot nem bővítettem a köteg újragenerálásával.

A korábbi egyszűrős mérés 18 eltéréséből 15 most egyezik. A teljes láncoknál viszont az archív és friss 200 soros táblázat státusza és metrikája változatlan: 168 egyezik, 32 eltér. A `lanc-0045` egyenként hibátlan szűrőinek együttállása bizonyított eltérés; a további 30 „c” sorhoz nincs elegendő azonos bemenetű egyszűrős adat vagy véletlen szemcsézés zavarja az összevetést.

## A régi sorrendű `colorfix` tagok kiszűrése (2026-11-10)

Az előző szakasz feltevését lemértem. A 32 eltérő láncból az a 8, amelyben hex első paraméterű `colorfix` tag áll, újra renderelődött úgy, hogy ezeket a tagokat kihagytam, a lánc többi tagja változatlan maradt. Az összevetés ugyanazzal az eredeti Picasa-exporttal és ugyanazokkal a golden küszöbökkel történt.

| Azonosító | Előtte: SSIM / ΔE | A tag nélkül: SSIM / ΔE | Ítélet |
|---|---|---|---|
| lanc-0005 | 0.76627 / 29.271 | 0.98611 / 0.608 | egyezik |
| lanc-0052 | 0.41064 / 139.805 | 0.85688 / 1.153 | eltér |
| lanc-0080 | 0.80866 / 91.311 | 1.00000 / 0.000 | egyezik |
| lanc-0101 | 0.97000 / 49.235 | 0.99637 / 0.554 | egyezik |
| lanc-0124 | 0.89940 / 11.270 | 0.99779 / 0.093 | egyezik |
| lanc-0144 | 0.83592 / 62.688 | 0.98889 / 0.933 | egyezik |
| lanc-0186 | 0.97919 / 1.075 | 1.00000 / 0.000 | egyezik |
| lanc-0190 | 0.98653 / 37.440 | 0.99188 / 0.889 | egyezik |

Az egyszűrős `egy-001` (`colorfix=1,ffca3cff,-0.164578;`) eredeti exportja a változatlan forrásképpel bitre egyezik (SSIM 1.00000, ΔE 0.000), tehát a Picasa ezt a tagot sem alkalmazta.

**Következtetés.** A „c” csoport mind a hat nagy eltérésű sora (ΔE 11 és 92 között) és a `lanc-0186` a köteg adathibája, nem a PicasaPy renderelőjének hibája. A köteg a #6617 előtt készült, amikor a generátor a szín, majd hőmérséklet sorrendet írta. Ezt az eredeti Picasa elveti, a PicasaPy pedig régi mentésként natív sorrendre alakítja és alkalmazza. A #6617 óta a generátor (`format_param_values`) natív sorrendben ír (`colorfix=1,<hőmérséklet>,<szín>`), így egy új köteg már a valódi `colorfix`-utat méri. A `lanc-0052` maradék eltérése a láncban maradt többi tagé (`QuantizePalette`, `Matte` és társai), ez az „a” besorolású sor.

A „c” csoport így 30-ról 23 sorra szűkül. Mind a 23 maradék eltérés kicsi (ΔE 0,47 és 3,67 között), és 21-ben véletlen szemcsézés (`grain`, `grain2`, `PicnikGrain`), `PicnikFocalPixelate` vagy `triple2` áll (kivétel: `lanc-0056` és `lanc-0113`). A következő lépés ezek leszűkítése egyszűrős Colab-mérésekkel a láncbeli bemeneten.

## Újramérés a mostani kóddal (2026-11-10 délután)

A 200 láncot a `68741414d` állapotú fő ággal helyben újrarendereltem, és ugyanazokkal az eredeti exportokkal vetettem össze (`differencialis_lanc.py sajat`, majd `osszevet`). Eredmény: **176 egyezik, 24 tér el** (korábban 168 és 32).

Nyolc lánc vált egyezővé: `lanc-0022`, `0048`, `0056`, `0067`, `0088`, `0115`, `0142`, `0175`. Ebből hétben `PicnikFocalPixelate` áll, ezt a #6691 igazította az eredetihez. A `lanc-0056`-ban `rainbow` van, ezt a #6743 javította. Egyezőből egy sem lett eltérő.

A 24 eltérés besorolása:

| Csoport | Láncok | Ok |
|---|---|---|
| régi sorrendű `colorfix` (8) | 0005, 0052, 0080, 0101, 0124, 0144, 0186, 0190 | a köteg adathibája (előző szakasz); a 0052-ben a többi tag is eltér |
| ismert együttállás (1) | 0045 | egyenként hibátlan szűrők együtt (`a` csoport) |
| véletlen szemcsézés (8) | 0010, 0043, 0060, 0065, 0117, 0119, 0140, 0169 | `grain`, `grain2` vagy `PicnikGrain` a láncban |
| `triple2` (6) | 0089, 0095, 0105, 0116, 0178, 0196 | a folyamatszintű dither-fázis (#3092) |
| erősített közelítés (1) | 0113 | lásd lent |

**`lanc-0113` leszűkítése.** Hat Colab-mérés (picasa-colab-jobs #486-#491), mindegyikben egy tag kihagyva. A `radsat` nélkül a lánc gyakorlatilag pixelhű (SSIM 0.99985, ΔE 0.064). Bármely más tag kihagyásakor egyezik vagy a határon marad (ΔE 0,22 és 0,85 között). Ugyanez a `radsat` ugyanezen a képen egymagában egyezik (`egy-043`: SSIM 0.99692, ΔE 0.351, `közelítés`). Következtetés: a `radsat` kis közelítési hibáját a mögötte álló `glow2`, `HeatMap`, `Sixties` és `HDR` felerősíti. Ez nem új hiba, hanem a `radsat` meglévő közelítésének láncbeli következménye. Ha a `radsat` pixelhűvé válik, ez a lánc is egyezni fog.

**`lanc-0056` leszűkítése.** Öt Colab-mérés (#481-#485): mind az öt, egy taggal rövidebb változat egyezett. Az ok a táblázat elavulása volt, a teljes lánc a mostani kóddal is egyezik (SSIM 0.99603, ΔE 0.587).

Ezzel a véletlen és a `triple2` nélküli láncok között nem maradt megmagyarázatlan eltérés. A szemcsés láncok összevetéséhez a szemcsét ki kell zárni a mérésből, vagy a #6712 óta a kötegelt exportra érvényes `rand()`-folyammal kell renderelni. A `triple2`-csoport a #3092-höz tartozik.
