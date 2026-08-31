# A PicasaPy saját funkcióinak jelölése a menüben

**Státusz:** ELFOGADVA · **Döntő:** a tulajdonos · **Dátum:** 2026-08-28

## A döntés

A PicasaPy **saját**, az eredeti Picasa 3-ban nem létező menüparancsai a
menüben **látható jelölést** kapnak. A jelölés formája **kék**, a konkrét
megvalósítás a megvalósító körre van bízva — a tulajdonos szavaival:
*„Lehet felőlem a menü színe is más, ami egyszerűbb."*

Két megengedett alak:

| alak | mikor válaszd |
|---|---|
| **a tétel szövege kék** | ha egyszerűbb — és a mérés szerint az |
| kis kék korong a jobb szélen | csak ha a színezés valamiért nem járható |

⚠️ **A jobb szél már foglalt.** A menüfeliratok gyorsbillentyűt is
hordoznak (`"Új album…" + "\tCtrl+N"` — a `PicasaMenuBar.qml`-ben több
tucat ilyen tétel van), és azt a Qt a **jobb szélre** igazítja. Egy ott
elhelyezett pötty ezzel versenyezne. Ezért az alapértelmezés a
**színezés**.

## Miért kellett dönteni

Áll egy korábbi, végleges döntés: *„a felület PONTOSAN úgy nézzen ki, mint
az eredeti Picasa"* (`szerkeszto-bal-panel.md`). A kék pötty ettől
**szándékos eltérés**, ezért nem lehet csendes megvalósítói döntés.

A tulajdonos kérte (2026-08-28), közvetlenül azután, hogy a
duplikátum-áthelyezésről (#1697) kiderült: **nem az eredeti viselkedése**,
hanem a mi bővítésünk. A kérdése ez volt: *„A nem eredeti funkciók
kaphatnának egy kis kék pötty jelölést a menüben a jobb szélen?"*

## Mit old meg

Ma **semmi nem különbözteti meg** a felületen az eredeti Picasa parancsait a
mi kiegészítéseinktől. Ez két konkrét kárt okoz:

1. **A felhasználó** nem tudja, mire számíthat: ha egy funkció nálunk
   máshogy működik, nem derül ki, hogy azért, mert a miénk.
2. **A fejlesztés** újra és újra a binárisban keresi olyasminek a
   viselkedését, ami ott nincs is. A #1697-nél ez ma megtörtént — előbb
   ellenőrizni kellett, létezik-e egyáltalán az eredetiben.

## A jelölés szabályai

- **Hol:** a menütétel jobb szélén, a gyorsbillentyű helyén/után.
- **Mi:** kis, tömör kék korong. Szöveg nem tartozik hozzá.
- **Súgó:** a tétel buboréksúgója mondja ki emberi nyelven, hogy ez a
  PicasaPy kiegészítése, nem az eredeti Picasa funkciója.
- **Mire NEM jár:** olyan parancsra, amely az eredetiben létezik, csak
  nálunk másképp/hiányosan működik — az **hiba**, nem saját funkció, és
  jegybe való, nem pöttybe.
- **Elérhetőség:** a pötty önmagában nem hordozhat információt színvakok
  számára — a buboréksúgó ezért kötelező, nem díszítés.

## Kötés

- **Státusz:** ELFOGADVA
- **Megvalósítja:** #1701 (v0.8.148) — `src/picasapy/app/qml/PicasaPy/PicasaMenuItem.qml`
  (`sajat` tulajdonság → kék felirat + kötelező buboréksúgó)
- **Őrzi:** `tests/app/qml_functional/test_sajat_funkcio_jeloles_1701.py`

## A megvalósítás választása — a színezés nyert

A döntéslap két alakot engedett meg, és a színezést tette
alapértelmezéssé. A megvalósító kör ezt választotta, a lap saját
indoklásával: a jobb szél foglalt a gyorsbillentyűkkel. A `PicasaMenuItem`
így három, egymástól FÜGGETLEN jelölést ismer — `placeholder` (még nem
működik), `retired` (volt, de kivezettük), `sajat` (soha nem is létezett).

**A ma megjelölt parancsok:** Súgó ▸ *Tesztüzem*, Súgó ▸ *Napló
elküldése…*. A teljes leltár összeállítása külön munka (a #1701 hatókörén
kívülre tette); az őr viszont MINDEN megjelölt tételre érvényes, és külön
állítja, hogy eredeti Picasa-parancs nem kaphat jelölést.
