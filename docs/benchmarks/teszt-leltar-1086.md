# Teszt-leltár: hol megy el a PR-kör ideje (#1086, 2026-08-23)

A tulajdonos kérése: *„nézzétek át, mely tesztekre nincsen minden PR előtt
szükség, mert kibaszottul felesleges azt a kódrészt újratesztelni, ami nem
változik semmit már, vagy egyszeri, de megoldott problémából fújtunk
kibaszott nagy teszt-lufit."*

Ez a lap **mérés**, nem vélemény. Forrás: `scripts/teszt_idok.json`
(fájlonkénti mért futásidő) + a fa statikus leltára.

---

## 1. A mérés

| | teszt | idő | idő-arány |
|---|---:|---:|---:|
| **összes** | **6 572** | **2 781 s** | 100% |
| ebből **QML-app** (a `qml_app` fixture-t használó) | 802 | **1 896 s** | **68%** |
| ebből **teszt-lufi** (egy jegyhez ≥12 teszt) | 1 324 | 522 s | 19% |
| ebből **dekódolt magok** (`render/`, `collage/`, `ini/`) | 1 751 | **~0 s** | **0%** |

*(A magok a mérésben 0,0 s-mal szerepelnek, mert a mérőszkript csak a
`tests/app` fájljait bontja külön; a mag-készlet egyben, a
`tests --ignore=tests/app` egységben fut: **145,9 s** mind az 1751 tesztre.)*

### A tíz legdrágább fájl

| idő | teszt | fájl |
|---:|---:|---|
| 113,7 s | 38 | `tests/app/qml_functional/test_editor.py` |
| 88,1 s | 26 | `tests/app/qml_functional/test_collage_panel_wiring_985.py` |
| 67,6 s | 16 | `tests/app/qml_functional/test_editor_crop_aspect_448.py` |
| 65,3 s | 25 | `tests/app/test_qml_fileops_export.py` |
| 63,4 s | 21 | `tests/app/test_batch_effect_controller.py` |
| 56,9 s | 23 | `tests/app/test_qml_import_source.py` |
| 55,3 s | 14 | `tests/app/qml_functional/test_library_frame_hidden_1026.py` |
| 46,9 s | 16 | `tests/app/test_qml_dedup.py` |
| 42,9 s | 13 | `tests/app/qml_functional/test_collage_draft_restore_1051.py` |
| 38,1 s | 11 | `tests/app/qml_functional/test_dark_theme_chrome.py` |

---

## 2. ⚠️ A mérés KÉT feltevést cáfolt

**(a) „A dekódolt képlet-magok több száz tesztje minden PR-en lefut, és ez
drága."** — A magok a teszt-darabszám **27%-át** adják, de a futásidő
**0%-át**: mind az 1 751 teszt együtt 145,9 s, egyetlen részfutásban. A
`test_editor.py` **egymaga** ennél lassabb (113,7 s / 38 teszt). A magok
tesztjei tehát **nem a pazarlás helye** — kivenni őket a PR-sávból
kockázat lenne haszon nélkül.

**(b) „A magok hónapok óta nem változnak."** — Mérve (`git log`):

| terület | utolsó változás |
|---|---|
| `src/picasapy/render/` | **2026-08-21** |
| `src/picasapy/ini/document.py` | 2026-08-16 |
| `src/picasapy/collage/rects.py` | 2026-08-16 |
| `src/picasapy/cvimage.py` | 2026-07-24 |

Egyedül a `cvimage` áll egy hónapja. A `render/` **tegnap** változott — és
a #1141 (szűrőnév-illesztés) épp ma nyúlt hozzá. A „változatlan mag"
premissza tehát nem áll.

**Ebből következik: a lassúság oka nem a magok, hanem a QML-tesztek** —
mindegyik felépíti a teljes alkalmazást (`qml_app` fixture), ami
fájlonként másodpercekbe kerül, és 802 teszt csinálja meg újra meg újra.

---

## 3. A megtartás mércéje (a jegy 2. pontja)

Egy teszt maradjon, ha **mindkettő igaz**:

1. **elbukik a javítás nélkül** (van foga) — ezt a projekt ma minden új
   tesztnél ellenőrzi (tiszta fán futtatás);
2. a **felhasználónak látszó** viselkedést vagy egy **dekódolt
   invariánst** állít.

Ami egyikre sem igaz, az törölhető. ⚠️ **De**: ami valaha valódi hibát
fogott meg, azt **javítani** kell, nem eldobni — ma többször is előfordult,
hogy egy zöld teszt a ROSSZ követelményt őrizte (#1027, #1045, #1059,
#1141), és a helyes lépés az átkötés volt.

---

## 4. Javaslat — a mérés szerint sorrendben

### 4.1 A legnagyobb nyereség: az app-építés megosztása

A 68%-os tétel oka szerkezeti: minden QML-tesztfájl **saját processzben**
építi fel a teljes alkalmazást (`test_qml_*`, `qml_functional/*`). A
darabolás (#1127) ezt platformonként négyfelé osztotta, de a felépítés
költsége megmaradt.

Két, egymástól független irány (mindkettő önálló jegy):

- **modul-szintű `qml_app`** ott, ahol a teszt nem ír állapotot (a
  `test_qml_navigation.py` már így csinálja: „a Main.qml-t EGYSZER
  töltjük be");
- **a csak-olvasó QML-tesztek összevonása** kevesebb fájlba (a fájlonkénti
  izoláció a #53 GIL-deadlock miatt kell — az összevonás ezt nem sérti,
  amíg a fájlok száma csökken, nem a processzeké nő).

### 4.2 A lufik: 68 fájl, 1 324 teszt

Nem tömeges törlés. A mérce a 3. szakasz; a leltár a legnagyobbakról:

| teszt | idő | fájl | javaslat |
|---:|---:|---|---|
| 66 | 14,5 s | `test_collage_controller_943.py` | átnézés: a paraméterezett variációk 3–4 esetre szűkíthetők |
| 42 | 12,5 s | `test_collage_settings_tab_946.py` | ua. |
| 38 | ~0 s | `test_chain_range_validation_382.py` | **marad** — dekódolt invariáns, gyors |
| 35 | ~0 s | `test_shadow_977.py` | **marad** — mért képlet |
| 28 | 32,1 s | `test_collage_output_ui_949.py` | átnézés (drága ÉS nagy) |
| 26 | 88,1 s | `test_collage_panel_wiring_985.py` | **elsődleges jelölt** — a legdrágább lufi |

⚠️ Mind a hat a **kollázs-sávé** (#1109) — a szűkítést a sáv gazdájával
kell egyeztetni, nem egyoldalúan elvégezni.

### 4.3 Két sáv — csak markerrel, sosem némán

Ahol egy teszt értékes, de nem kell minden PR-en (golden-készletek,
paritás-mérések), `@pytest.mark.lassu` jelölés + a PR-sávból kizárás. A
teljes sáv éjszakai futásban; **bukása ugyanúgy jegyet érdemel**.

Ez a lap ezt a mechanizmust **nem** vezeti be — a mérés szerint a
nyereség (19% idő) töredéke a 4.1-nek (68%), és a néma lefedettség-vesztés
kockázata valós. Előbb a 4.1.

---

## 5. Amit ez a kör NEM csinált

- **Nem törölt egyetlen tesztet sem.** A jegy leltárt és javaslatot kért.
- Nem vezetett be sávokat (ld. 4.3 indoklás).
- A kollázs-fájlok szűkítése a sáv gazdájával egyeztetendő.
