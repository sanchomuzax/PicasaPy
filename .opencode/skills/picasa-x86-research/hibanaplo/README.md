# OSGi-hiba: egyedi Java GhidraScript betöltésének javítása (2026-08-12)

Ez a mappa az egyedi Java GhidraScript korábbi, reprodukálható hibáját és a
Ghidra 12.1.2 / Java 21 környezetben ellenőrzött javítást rögzíti.

## Környezet

- Codespace `standardLinux32gb`, a skill `create` + `setup` szerint
- Ghidra **12.1.2 PUBLIC**, Java **21.0.10-ms** (`java -version` a naplóban,
  a `java21-home` fájlból beállítva)
- A projekt előzőleg **sikeres** teljes autoanalízissel készült
  (`Analysis succeeded`, `Import succeeded`)

## A parancs

```bash
export JAVA_HOME=$(cat /tmp/picasa-research/java21-home)
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/picasa-research
GH=$(ls -d tools/ghidra_*/ | head -1)
"$GH"support/analyzeHeadless /tmp/picasa-research/project picasa \
    -process Picasa3.exe -noanalysis \
    -scriptPath /tmp/picasa-research -postScript FilterRegistry.java
```

## A hiba

```
ERROR REPORT SCRIPT ERROR: FilterRegistry.java : The class could not be found.
It must be the public class of the .java file:
Failed to get OSGi bundle containing script: /tmp/picasa-research/FilterRegistry.java
  ghidra.app.script.GhidraScriptLoadException
  ... Caused by: java.lang.ClassNotFoundException:
      Failed to get OSGi bundle containing script
      at ghidra.app.script.JavaScriptProvider.loadClass(JavaScriptProvider.java:163)
```

## Amit már kipróbáltam — és NEM oldotta meg

1. **A `SKILL.md` szerinti javítás:** a távoli
   `~/.config/ghidra/ghidra_12.1.2_PUBLIC/osgi/compiled-bundles` törlése,
   majd újrafuttatás Java 21-gyel. **Ugyanaz a hiba** (2. napló).
2. Java-verzió ellenőrizve: a napló első sora `openjdk version "21.0.10"` —
   tehát nem class-version ütközés.

## Gyökérok és javítás

A `-scriptPath /tmp/picasa-research` túl tág volt: ez alatt található a
`tools/ghidra_12.1.2_PUBLIC` telepítés és annak sok Java-forrása. A Ghidra a
teljes scriptPath könyvtárat egyetlen OSGi forrás-bundle-ként kezeli, ezért a
saját forrásait is megpróbálta bevenni a fordításba. A bundle felépítése
meghiúsult, de a headless felület csak a generikus class-not-found hibát
mutatta.

A javítás: szkriptenként külön
`/tmp/picasa-research/scripts/<szkriptnév>` levélkönyvtár, benne csak az adott
felhasználói szkripttel, és pontosan ezt kell átadni `-scriptPath`-ként.

Tiszta Ghidra 12.1.2 / Java 21 Codespace-ban ellenőrizve:

1. a minimális `HelloScript.java` a dedikált könyvtárból kiírta a
   `PICASAPY_GHIDRA_SCRIPT_OK` jelzőt;
2. az eredeti `FilterRegistry.java` ugyanonnan végigfutott `=== VEGE ===`-ig;
3. ugyanazt a fájlt visszatéve a gyökérbe és a régi, tág scriptPath-tal a
   korábbi OSGi-hiba pontosan reprodukálódott.

## Megkerülő megoldás, ami MŰKÖDÖTT

A feladat (a natív szűrő-nyilvántartás kinyerése) végül **Ghidra nélkül**,
helyben megoldódott: a PE-szekciótáblából számolt virtuális címek 4 bájtos,
little-endian keresésével. Eredmény:
`PicasaPy/docs/specs/picasa-native-filter-registry.md` — mind a 42 szűrő
callback-címe.

Ez azonban **nem helyettesíti a dekompilálást**: a callbackek belsejéhez
továbbra is kell működő Ghidra-szkriptelés.

## Fájlok

- `FilterRegistry.java` — az eredeti szkript, amely a javított útvonalról lefut
- `HelloScript.java` — minimális sikeres betöltési kontroll
- `1-elso-futas.log` — az első futás naplója
- `2-osgi-cache-torles-utan.log` — a dokumentált javítás után, ugyanaz a hiba
