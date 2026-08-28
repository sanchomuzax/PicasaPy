"""„Exportált képek" — az exportált mappák nyilvántartása (#457).

Az eredeti Picasa az exportált mappákat egy külön **„Exported Pictures"**
csomópont alá gyűjtötte a navigációban: az export nem tűnt el a
fájlrendszerben, hanem **nyomon követhető** maradt. Ez a modul ennek az
adatoldala — a lista a beállításokban él (nem az indexben), mert nem a
fotókról szól, hanem arról, hogy a felhasználó hova exportált.

A lista **legutóbbi elöl** rendezett, korlátos hosszú, és a már nem
létező mappákat kiszűri: az exportált mappát a felhasználó bármikor
törölheti vagy átnevezheti a fájlkezelőben, és attól még nem lehet
zavaros a navigáció.
"""

from __future__ import annotations

from pathlib import Path

#: A nyilvántartás beállítás-kulcsa.
EXPORTED_FOLDERS_SETTINGS_KEY = "export/exportedfolders"

#: Ennyi mappát tartunk. Az eredeti korlátja nem derül ki a binárisból —
#: ez a MI döntésünk: elég ahhoz, hogy a szokásos munkamenet
#: visszakereshető legyen, kevés ahhoz, hogy a hasáb tele legyen vele.
MAX_EXPORTED_FOLDERS = 20


def _clean(values) -> list[str]:
    """QSettings-ből visszaolvasott érték listává — a Qt egyetlen elemnél
    stringet ad vissza, nem listát (a `recentSources` mintája)."""
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    return [str(value) for value in values if str(value).strip()]


def remember_exported_folder(existing, folder: str | Path) -> list[str]:
    """Az újonnan használt célmappa a lista ELEJÉRE; duplikátum nélkül.

    Tiszta függvény (nem nyúl beállításhoz), hogy tesztelhető legyen — a
    tárolást a vezérlő intézi.
    """
    path = str(Path(folder))
    if not path.strip():
        return _clean(existing)
    remaining = [item for item in _clean(existing) if item != path]
    return [path, *remaining][:MAX_EXPORTED_FOLDERS]


def registered_exported_folders(values) -> tuple[str, ...]:
    """A nyilvántartott exportcélok — **létezés-ellenőrzés NÉLKÜL** (#1667).

    Az `existing_exported_folders` párja. A különbség szándékos, és két
    okból nem hagyható el:

    * **Nem nyúl a lemezhez.** Ez a lista az induláskori takarítás
      (`prune_foreign_folders`, #58) védett gyökereit adja, ami az indulás
      kritikus útján fut. Húsz `is_dir()` egy hálózati exportcélon
      másodpercekbe kerülhet — a védelemhez pedig nem kell tudni, hogy a
      mappa MOST ott van-e.
    * **A hiány nem bizonyíték** (#1560). Egy lecsatolt NAS vagy egy
      leválasztott külső lemez exportcélja „nem létezőnek" látszik, de a
      képek megvannak. Ha a hiánya miatt kitakarítanánk az indexből, a
      visszatéréskor a teljes újraolvasás következne — pontosan az a kár,
      amit a #1560 leír.

    A navigációs csomópont ettől függetlenül a létezőket mutatja: ott az
    `existing_exported_folders` a helyes választás."""
    return tuple(_clean(values))


def existing_exported_folders(values) -> list[str]:
    """A listából csak azok, amelyek MA IS léteznek.

    Az exportált mappa a fájlkezelőben bármikor eltűnhet — a navigációban
    nem akarunk halott csomópontokat mutatni."""
    return [path for path in _clean(values) if Path(path).is_dir()]


__all__ = [
    "EXPORTED_FOLDERS_SETTINGS_KEY",
    "MAX_EXPORTED_FOLDERS",
    "existing_exported_folders",
    "registered_exported_folders",
    "remember_exported_folder",
]
