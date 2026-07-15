# Kutatási terv — nyitott kérdések

Állapot: 2026-07-15. A formátum-specifikációk megvannak (`docs/specs/`);
az alábbiak igényelnek még kutatást/mérést a fejlesztés megkezdése előtt.

## 1. GUI toolkit benchmark (döntés előtt)

Jelöltek: **PySide6/Qt (QML + Widgets)** — fő esélyes; GTK4 (PyGObject);
Dear PyGui; web-frontend (Tauri/NiceGUI/Flet).

Mérési terv (RPi5-ön, Wayland alatt):
- Thumbnail-rács: 10k / 50k / 100k elem görgetési FPS, memória
- Képváltási latencia (following-kép előtöltéssel)
- GPU-integráció: OpenGL ES 3.1 / shader-pipeline elérhetősége a toolkitből
- Csomagolhatóság Linuxra (Flatpak/AppImage), későbbi Win/Mac port költsége

Kimenet: `docs/decisions/gui-toolkit.md` (ADR).

## 2. Pixelhű szűrő-reprodukció (a legnagyobb kockázat)

A kétirányú ini-kompatibilitás miatt a `filters=` láncnak ugyanazt a képet kell
adnia, mint az eredeti Picasa — de az `enhance`, `autolight`, `autocolor`,
`finetune2` pontos algoritmusa nem publikus.

Terv:
1. Eredeti Picasa 3.9 futtatása Wine alatt (vagy Windows VM-ben)
2. Referencia-készlet: ~50 változatos tesztkép × minden szűrő × paraméter-rács
3. A Picasa renderelt kimenetének mentése → golden képek
4. Saját implementáció illesztése; elfogadás SSIM / ΔE metrikával (küszöb TBD)
5. `finetune2` 5. (ismeretlen) paraméterének feltérképezése méréssel

## 3. Teljesítmény-alapmérések (RPi5)

- pyvips vs Pillow(-SIMD) vs OpenCV: thumbnail-generálás áteresztőképesség
- SQLite indexelési stratégia 100k+ képre; FTS a kereséshez
- Fájlrendszer-figyelés: inotify (watchdog lib) skálázhatóság sok mappára

## 4. Arcfelismerő stack (3. fázishoz)

- Jelöltek: OpenCV (YuNet), dlib, InsightFace/ArcFace ONNX runtime-mal
- Szempontok: RPi5 CPU/NPU-n futtathatóság, csoportosítási minőség, licenc
- Picasa-kompatibilis kimenet: rect64 + contact_id + contacts kezelés

## 5. PMP-import validálás

- `vosbergw/picasa3meta` kód auditja és felélesztése (Python 3.12+ kompat?)
- Teszt valódi Picasa-könyvtárral: van-e hozzáférhető régi db3 mappánk?
- Csak-db-ben-élő adatok (képsorrend, ignorált arcok) kinyerésének ellenőrzése

## 6. Referencia-repók klónozása és audit

`skisoo/PicasaDBReader`, `vosbergw/picasa3meta`, `vosbergw/metaSave`,
`Philipp91/picasa2digikam`, `bufemc/picasa2xmp` → a `research/` mappába
(gitignore-olt), licencek ellenőrzése (GPL-3.0 többnél — a *kód átvétele*
licenc-következménnyel jár, a *formátumtudás* nem).

## NotebookLM forrás

Notebook: „Picasa metaadatok és adatbázisok dekódolási útmutatója"
ID: `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e` (30 forrás)
https://notebooklm.google.com/notebook/f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e
