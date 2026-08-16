# A specifikációk tartalomjegyzéke

**Ez a lap a belépési pont a `docs/specs/`-be.** Egy sor laponként: mi van
benne, és **mennyi nyitott kérdés maradt** rajta. Egy kutatói kör innen
válasszon témát — ne a teljes mappa végiggrepeléséből.

A „nyitott" oszlop a lapon található `Nyitva` / `NYITOTT` / `dekódolatlan` /
`uncalibrated` jelölések száma. **A 0 nem azt jelenti, hogy a téma kész** —
azt, hogy nincs rajta *megjelölt* nyitott kérdés.

*Utolsó frissítés: 2026-08-16.*

## Hol van nyitott kérdés (itt érdemes kutatni)

| lap | nyitott | miről szól |
|---|---:|---|
| [filters-decoded.md](filters-decoded.md) | **17** | Szűrő-visszafejtés — a golden-mérések eredményei |
| [ui-audit-editor.md](ui-audit-editor.md) | **6** | A szerkesztőpanel és dialógusai |
| [filterdesc-registry.md](filterdesc-registry.md) | **6** | A `filterdesc.xml` hivatalos szűrő-regisztere |
| [ui-audit-mainwindow.md](ui-audit-mainwindow.md) | **3** | Főablak: mappafa, eszköztár, tálca, arányok |
| [picasa-ini-format.md](picasa-ini-format.md) | **2** | A `.picasa.ini` formátuma |
| [picasa-native-filter-registry.md](picasa-native-filter-registry.md) | **1** | A natív szűrő-nyilvántartás (49 bejegyzés) |
| [ui-audit-context-menus.md](ui-audit-context-menus.md) | **1** | Jobbklikkes helyi menük |

## Formátum-specifikációk (adatfájlok, erőforrások)

| lap | miről szól |
|---|---|
| [picasa-ini-format.md](picasa-ini-format.md) | A `.picasa.ini` — az igazságforrás, round-trip szabályokkal |
| [pmp-database.md](pmp-database.md) | A központi adatbázis (`db3` / PMP) |
| [picasa-imagedata-rekord.md](picasa-imagedata-rekord.md) | Az `imagedata` rekord — belső kép-nyilvántartás |
| [picasa-respack-format.md](picasa-respack-format.md) | `respack.yt` — a bináris erőforráscsomag (megfejtve) |
| [picasa-program-resources.md](picasa-program-resources.md) | Erőforrás- és formátum-leltár (gombok, web-export, plugin-ök) |
| [picasa-fen-dialogs.md](picasa-fen-dialogs.md) | A `.fen` dialógus-definíciók |
| [picasa-web-template-nyelv.md](picasa-web-template-nyelv.md) | A web-export sablonnyelve |
| [picasa-exe-strings.md](picasa-exe-strings.md) | Bináris string-bányászat |
| [picasa-beepitett-konyvtarak.md](picasa-beepitett-konyvtarak.md) | A Picasa beépített nyílt forráskódú könyvtárai |

## Képfeldolgozás (szűrők, render)

| lap | miről szól |
|---|---|
| [filters-decoded.md](filters-decoded.md) | A szűrők visszafejtett modelljei + golden-verdiktek |
| [filterdesc-registry.md](filterdesc-registry.md) | A `filterdesc.xml` — csúszkanevek, tartományok, alapértékek |
| [picasa-native-filter-registry.md](picasa-native-filter-registry.md) | A natív szűrő-tábla: 49 név → kezelő + képen belüli vezérlők |
| [picasa-native-filter-workers.md](picasa-native-filter-workers.md) | A natív szűrők munkafüggvényei — hívási térkép |
| [histogram-reference.md](histogram-reference.md) | Hisztogram-referencia és összevetés |

## Felület — KÖTELEZŐ méretspecifikációk

Ezek **normatívak**: a felületnek pontosan ezeket kell követnie.

| lap | miről szól |
|---|---|
| [szerkeszto-panel-meretek.md](szerkeszto-panel-meretek.md) | A szerkesztő bal panelje (201 elem) |
| [konyvtar-ablak-meretek.md](konyvtar-ablak-meretek.md) | A könyvtár-ablak (156 elem) |
| [jobb-fiok-meretek.md](jobb-fiok-meretek.md) | A jobb oldali fiók („Metaadatok", 80 elem) |
| [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) | A fő ablak elrendezése — a forrásból |

## Felület — auditok és lefedettség

| lap | miről szól |
|---|---|
| [ui-audit-editor.md](ui-audit-editor.md) | A szerkesztőpanel: fülek, effekt-csempék, dialógusok |
| [ui-audit-mainwindow.md](ui-audit-mainwindow.md) | Főablak: mappafa, eszköztár, tálca, görgetősáv |
| [ui-audit-menus.md](ui-audit-menus.md) | A teljes menürendszer |
| [ui-audit-context-menus.md](ui-audit-context-menus.md) | Jobbklikkes helyi menük |
| [ui-lefedettseg.md](ui-lefedettseg.md) | Az eredeti panelek ↔ a mi QML-fánk megfeleltetése |
| [picasa-beviteli-mezok.md](picasa-beviteli-mezok.md) | Beviteli mezők és párbeszédpanelek |

## Viselkedés és funkciók

| lap | miről szól |
|---|---|
| [picasa-create-features.md](picasa-create-features.md) | A „Létrehozás" menü funkciói |
| [picasa-bezaras-es-kilepes.md](picasa-bezaras-es-kilepes.md) | Mit zár be az „X" — bezárás és kilépés |
| [vorosszem-eszkoz-terve.md](vorosszem-eszkoz-terve.md) | A vörösszem-eszköz terve |

## Nyelv és megjelenés

| lap | miről szól |
|---|---|
| [picasa-hu-terminology.md](picasa-hu-terminology.md) | Hivatalos Picasa-magyar terminológia |
| [picasa-effekt-nevek.md](picasa-effekt-nevek.md) | Az effektek nevei és buboréksúgói |
| [picasa-effekt-feliratok.md](picasa-effekt-feliratok.md) | Az effekt-vezérlők feliratai |
| [design-guide.md](design-guide.md) | Dizájn-kézikönyv — hűség-referencia |
| [ux-principles.md](ux-principles.md) | UX-alapelvek — „a Picasa lelke" |

## Módszertan és tervezés

| lap | miről szól |
|---|---|
| [binaris-regeszet-modszertan.md](binaris-regeszet-modszertan.md) | **A szerszámosláda**: mit hoz ki egy eszköz, és mit NEM lát |
| [feature-map.md](feature-map.md) | Funkciótérkép és fázisterv |

## Mikor kell ezt a lapot frissíteni

| mikor | mit |
|---|---|
| **Új spec-lap születik** | egy sor a témakör táblájába — **ugyanabban a PR-ban** |
| **Egy lap nyitott kérdést zár le** | a „Hol van nyitott kérdés" táblában a szám csökken; ha 0-ra, a sor kikerül |
| **Új nyitott kérdést jelölsz meg** | a szám nő; ha eddig nem szerepelt, a sor bekerül |
| **Egy lap átnevezése/összevonása** | a hivatkozás javítása |
| **Kutatói kör INDULÁSAKOR** | csak olvasod — innen választasz témát |

**A frissítés nem külön kör.** Aki hozzányúl egy spec-laphoz, ugyanabban a
PR-ban hozza rendbe ezt a sort is — így az index nem tud elavulni. A
számokat ellenőrizni lehet:

```bash
for f in docs/specs/*.md; do
  printf "%-45s %s\n" "$(basename "$f")" \
    "$(grep -c 'Nyitva\|NYITOTT\|dekódolatlan\|uncalibrated' "$f")"
done
```
