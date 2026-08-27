
## Az export VÍZJELE — pontos paraméterek (2026-08-27)

A vízjelet a **`0x0045c4b0`** (955 b) rajzolja; hívója a
`CPreparedDBImage` (`0x007948c0`) a `0x0045c430`-on át. A beállítások:
`Preferences\ExportWatermark` és `\ExportWatermarkText` (az export-motor
`0x0073f320` olvassa), a webalbum-ágon `PWAWatermark`.

| paraméter | érték | bizonyíték |
|---|---|---|
| **betűméret** | **max(12, max(szélesség, magasság) / 50)** képpont | `0x0045c509` (min=12), `0x0045c514` (a nagyobbik oldal), `0x0045c516`–`0x0045c51d` (magic `0x51EB851F` + `shr 4` = /50) |
| **betűcsalád** | **Arial** | `0x0045c535` |
| **vastagság** | **600** | `0x0045c530` (`mov eax, 0x258`) |
| **méretezés** | **1,0** | `0x0045c52a` (`fld1`) |
| **margó** | **= a betűméret**, mind a négy oldalon | `0x0045c563`/`0x0045c565` és `0x0045c58b`–`0x0045c593` |
| **alsó korlát** | **32 képpontnál** kisebb oldal ⇒ nincs vízjel (4-es hibakód) | `0x0045c4be`–`0x0045c4c4` |
| szín | átlátszatlan fehér *(**erős**, nem megerősített)* | `0x0045c627` (`0xFFFFFFFF`) |

**Számított méretek:** 4000×3000 → 80 px · 3000×2000 → 60 · 1600×1200 → 32
· 1024×768 → 20 · 640×480 → 12.

⚠️ **Nálunk 1,5–1,75-ször nagyobb** (`exporter.py:490`), mert a
**kisebbik** oldalból számol, 500-zal oszt, és vonalas betűt rajzol.
Jegy: **#1603**.

## Az export VÍZJELE — pontos paraméterek (2026-08-27)

A vízjelet a **`0x0045c4b0`** (955 b) rajzolja; hívója a
`CPreparedDBImage` (`0x007948c0`) a `0x0045c430`-on át. A beállítások:
`Preferences\ExportWatermark` és `\ExportWatermarkText` (az export-motor
`0x0073f320` olvassa), a webalbum-ágon `PWAWatermark`.

| paraméter | érték | bizonyíték |
|---|---|---|
| **betűméret** | **max(12, max(szélesség, magasság) / 50)** képpont | `0x0045c509` (min=12), `0x0045c514` (a **nagyobbik** oldal), `0x0045c516`–`0x0045c51d` (magic `0x51EB851F` + `shr 4` = osztás 50-nel) |
| **betűcsalád** | **Arial** | `0x0045c535` |
| **vastagság** | **600** | `0x0045c530` (`mov eax, 0x258`) |
| **méretezés** | **1,0** | `0x0045c52a` (`fld1`) |
| **margó** | **= a betűméret**, mind a négy oldalon | `0x0045c563`/`0x0045c565`, `0x0045c58b`–`0x0045c593` |
| **alsó korlát** | **32 képpontnál** kisebb oldal ⇒ nincs vízjel (4-es hibakód) | `0x0045c4be`–`0x0045c4c4` |
| szín | átlátszatlan fehér — **erős**, nem megerősített | `0x0045c627` (`0xFFFFFFFF`) |

**Számított méretek:** 4000×3000 → **80** px · 3000×2000 → **60** ·
1600×1200 → **32** · 1024×768 → **20** · 640×480 → **12**.

⚠️ **Nálunk 1,5–1,75-ször nagyobb** (`export/exporter.py:490`), mert a
**kisebbik** oldalból számol, 500-zal oszt, és vonalas (Hershey) betűt
rajzol. A függvény docstringje azt állította, hogy a paraméterek „nem
rekonstruálhatók" — **ez megdőlt**. Jegy: **#1603**.
