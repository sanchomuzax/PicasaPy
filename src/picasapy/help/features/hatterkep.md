# Asztali háttérkép

Egy képet vagy egy kész kollázst egyetlen paranccsal az asztalod
háttérképévé tehetsz.

## Egy kijelölt képből

Jelölj ki egy képet, majd **Létrehozás ▸ Beállítás háttérképként…**.
Kijelölés nélkül a menüpont szürke. Ha több képet jelöltél ki, az első
lesz a háttér.

## Egy kollázsból

A kollázs-panel **Asztali háttérkép** gombja egy lépésben elkészíti a
kollázst, és rögtön be is állítja háttérképnek. Lásd
[Kollázs](kollazs.md).

## Mi történik közben

A program **másolatot** készít a képről a **Hátterek** mappába, és azt
állítja be háttérképnek. Így a háttérkép akkor is megmarad, ha az
eredeti képet később átnevezed, áthelyezed vagy törlöd.

A másolat a kép **szerkesztett, helyesen álló** változata: ami a
PicasaPy-ban a képen látszik (forgatás, tükrözés, vágás, effektek), az a háttéren
is ott van, és az oldalt fényképezett kép sem kerül oldalára. Az eredeti
fájl változatlan marad.

A Hátterek mappa a kollázsok célmappája mellett van — alapállapotban a
képmappádon belül, a Picasa projektmappái közt. Ha a kollázsok
célmappáját áthelyezted, a háttérkép is oda kerül.

A kép **középre** kerül, nyújtás és mozaik nélkül, ahogy az eredeti
Picasa is tette.

## Ha nem sikerül beállítani

Windowson a program magával a rendszerrel állíttatja be a hátteret, ezért
ott rendszerint sikerül. Linuxon a legelterjedtebb asztali környezetekkel
próbálkozik — köztük a GNOME-mal, a **KDE Plasmával**, a Raspberry Pi
asztalával és a **labwc**, Sway és hasonló (wlroots-alapú) asztalokkal.
KDE Plasmán a rendszer saját háttérkép-eszköze, a wlroots-alapú asztalokon
a `swaybg` program kell hozzá; ha ez hiányzik, a beállítás nem sikerül. Ha egyikkel sem jár sikerrel,
nem hallgat el: **megmondja, hova tette a képet**, hogy a rendszer saját
beállításaiban kézzel kiválaszthasd.

Siker esetén rövid üzenet jelzi, hogy a háttérkép beállt.
