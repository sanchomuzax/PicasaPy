# A keresősáv `webview` szűrője KIMARAD

Állapot: eldöntve · Dátum: 2026-09-15 · jegy: #839

## A döntés

Az eredeti keresősáv **öt** szűrő-ikont visel; a negyedik a **`webview`**
(„Show uploads to web albums only" — csak a webalbumba feltöltött képek).
**Ezt nem valósítjuk meg.**

## Miért

A szűrő a Picasa Web Albums / Google+ feltöltéseket szűrte. **A szolgáltatás
megszűnt**, a feltöltési út nincs és nem is lesz a PicasaPy-ban (ugyanaz a
hatókör-döntés, ami a Feltöltéskezelőt és a Bloggert is kihagyja). Egy olyan
szűrő, amely **soha nem talál semmit**, rosszabb, mint a hiánya: a
felhasználó azt hiszi, a képei nincsenek feltöltve, holott a fogalom maga
nem létezik nálunk.

## Ami a helyén van

A mi keresősávunkban ugyanezen a helyen a **másodpéldány-szűrő**
(`dupeFilter`) áll. ⚠️ Ez **SAJÁT FUNKCIÓ**: az eredetiben a
másodpéldány-keresés nem szűrő-ikon, hanem a keresési beállítások felugró
paneljében él (`searchoptions/dupesearch`, a `searchbutton` nyitja), és a
menüben „Fájlok másodpéldányainak megjelenítése" néven. A #839 mérése ezt
külön kimondja.

⇒ a sorrendünk így **★ · arc · videó · másodpéldány · geo**, az eredeti
**★ · arc · videó · web · geo** helyett: a negyedik hely tartalma más, a
többi egyezik.

## Mi cáfolná

Ha előkerülne egy olyan feltöltési cél, amit a PicasaPy támogat (pl. saját
szerver, FTP — ld. #428), akkor a „csak a feltöltöttek" szűrőnek **lenne**
jelentése, és a döntést újra kell nyitni. A kihagyás tehát a
szolgáltatás hiányához kötött, nem a szűrő gondolatához.

## Forrás

`docs/specs/ui-audit-mainwindow.md` → „A keresősáv teljes eleme-listája a
forrásból" (a `searchcontainer.tre` 125 sora; a felületkód `0x00660c80` és
`0x005d47e0` ugyanezt a hét azonosítót hivatkozza).

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/MainToolbar.qml`
- **Őrzi:** `tests/app/qml_functional/test_szuro_sugok_839.py`
