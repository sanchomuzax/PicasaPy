# Kép exportálása mappába — a Picasa export-ága

## Az export VÍZJELE — pontos paraméterek (2026-08-27, pontosítva 2026-09-01)

A vízjelet a **`0x0045c4b0`** (955 b) rajzolja; hívója a
`CPreparedDBImage` (`0x007948c0`) a `0x0045c430`-on át. A beállítások:
`Preferences\ExportWatermark` és `\ExportWatermarkText` (az export-motor
`0x0073f320` olvassa), a webalbum-ágon `PWAWatermark`.

| paraméter | érték | bizonyíték |
|---|---|---|
| **betűméret** | **max(12, max(szélesség, magasság) / 50)** képpont | `0x0045c509` (min=12), `0x0045c514` (a **nagyobbik** oldal), `0x0045c516`–`0x0045c51d` (magic `0x51EB851F` + `shr 4` = osztás 50-nel) |
| **betűcsalád** | **Arial** | `0x0045c535` |
| **vastagság** | **600** (félkövér) | `0x0045c530` (`mov eax, 0x258`) |
| **méretezés** | **1,0** | `0x0045c52a` (`fld1`) |
| **margó** | **= a betűméret**, mind a négy oldalon | `0x0045c563`/`0x0045c565`, `0x0045c58b`–`0x0045c593` |
| **alsó korlát** | **32 képpontnál alacsonyabb MAGASSÁGÚ** képre nincs vízjel (4-es hibakód) | `0x0045c4be`–`0x0045c4c4`: `cmp ecx, 0x20` az `[esi+0xc]` = **magasság** mezőn |
| szín | átlátszatlan fehér — **erős**, nem megerősített | `0x0045c627` (`0xFFFFFFFF`) |

⚠️ Az alsó korlát a **magasságra** vonatkozik, nem „a kisebbik oldalra":
egy 2000×20 képpontos panorámára nem kerül vízjel, egy 20×2000-esre igen.
Ez a lap korábbi változata tévesen „oldalt" írt.

**Számított méretek:** 4000×3000 → **80** px · 3000×2000 → **60** ·
1600×1200 → **32** · 1024×768 → **20** · 640×480 → **12**.

### Nálunk — a mai állapot

A **#1603 óta egyezik**: `export/exporter.py`
(`_watermark_font_size_px`, `_apply_watermark`) a **hosszabb** oldalból
számol, egész osztással 50-nel, `max(12, …)` alsó korláttal; a margó mind a
négy oldalon a betűméret; 32 képpontnál alacsonyabb magasságú képre nem
kerül vízjel.

Egyetlen ismert eltérés maradt, és az **környezetfüggő**: ha a gépen nincs
használható TrueType-betű (például csupasz CI-képen), a rajzolás
Hershey-visszaesésre vált — a méret és az elhelyezés ilyenkor is a fenti
szabályokat követi, csak a betű **alakja** közelítő, nem Arial.

> **A lap korábbi változata két hibát hordozott** (#1641): a szakasz szó
> szerint kétszer szerepelt, és a figyelmeztetése a #1603 ELŐTTI állapotot
> („nálunk 1,5–1,75-ször nagyobb") írta le aktuálisként. Aki ezt olvasta, a
> már javított viselkedést hitte volna hibának.
