"""A mentés képfájl- és pillanatkép-segédműveletei (#6168)."""

from __future__ import annotations

import contextlib
import logging
import os
import stat
from collections.abc import Iterator
from pathlib import Path
import numpy as np
import picasapy.edit.save as api

_log = logging.getLogger(__name__)

#: A `.jpg.jpg` név átnevezésének fogantyúja (#1375): a teszt EZT cserélje.
_atnevez = os.rename

#: A célok, amelyeknél a kész kép `.jpg` utótaggal megmarad (#7462).
_JPEG_KITERJESZTESEK = frozenset({".jpg", ".jpeg"})


def _kep_irasa(image_path: Path, payload: bytes) -> None:
    api.write_atomic(
        image_path,
        payload,
        lock_retries=api._ZAR_UJRA,
        lock_retry_delay=api._ZAR_KESLELTETES,
    )


def _mentett_kep_irasa(
    image_path: Path,
    payload: bytes,
    *,
    bytes_elotte: bytes,
    uj_fajlok: tuple[Path, ...],
    uj_mappak: tuple[Path, ...],
) -> None:
    """A Mentés képírása (#7462): a `_kep_irasa`, csere-hiba esetére bővítve.

    Ha a kész képet nem sikerül a helyére tenni (pl. írásvédett a cél), az
    eredeti Picasa szerint (`job-957`) a kész kép `<név>.<kit>.jpg` néven a
    cél mellett marad, és `.picasaoriginals` mentés nincs: a mentés által
    létrehozott `uj_fajlok` és `uj_mappak` eltűnnek. A hiba megy tovább.

    #7476: ha a hiba ellenére a kép bájtjai szerint a csere megtörtént, a
    `bytes_elotte` íródik vissza, és a hiba megy tovább. Ha a visszaírás nem
    sikerül, a függvény hiba nélkül tér vissza: a szerkesztett kép a helyén
    van, tehát a hívónak be kell fejeznie a mentést.

    Csak a `save_edited` hívja: a Visszavonás, a Visszaállítás és a
    visszagörgetés a `_kep_irasa` úton marad.
    """

    def csere_hibaja(temp_nev: str) -> None:
        # #7476: ha a csere a hiba ellenére megtörténhetett, a megőrzött
        # eredetihez nem nyúlunk, a lenti ág dönt a kép bájtjai alapján.
        if not os.path.lexists(temp_nev) or _a_csere_megtortent(
            image_path, bytes_elotte, payload
        ):
            return
        # A `.jpg.jpg` a JPEG-író kiterjesztés-cseréje (#7428); nem JPEG
        # célra az eredeti viselkedése nincs mérve, ott a temp törlődik.
        if image_path.suffix.lower() in _JPEG_KITERJESZTESEK:
            _kesz_kep_megtartasa(
                Path(temp_nev), image_path.with_name(f"{image_path.name}.jpg")
            )
        _mentes_nyomanak_torlese(uj_fajlok, uj_mappak)

    try:
        api.write_atomic(
            image_path,
            payload,
            lock_retries=api._ZAR_UJRA,
            lock_retry_delay=api._ZAR_KESLELTETES,
            refuse_write_protected=True,
            on_replace_failure=csere_hibaja,
        )
    except OSError as hiba:
        if not _a_csere_megtortent(image_path, bytes_elotte, payload):
            raise
        # A visszaírás is jelezhet hibát a csere után, ezért megint a bájtok
        # döntenek.
        with contextlib.suppress(OSError):
            _kep_irasa(image_path, bytes_elotte)
        if not _a_csere_megtortent(image_path, bytes_elotte, payload):
            raise
        _log.warning(
            "A képcsere után hiba jött (%s), és a régi kép nem írható vissza: "
            "a mentés befejeződik (%s)",
            hiba,
            image_path,
        )


def _a_csere_megtortent(image_path: Path, bytes_elotte: bytes, payload: bytes) -> bool:
    """A lemezen bizonyíthatóan az új kép áll-e (#7476). Nem dob.

    Olvashatatlan képnél, és ha az új tartalom azonos a régivel, `False`.
    """
    if payload == bytes_elotte:
        return False
    try:
        return image_path.read_bytes() == payload
    except OSError:
        return False


@contextlib.contextmanager
def _nyom_torlese_irasi_hibanal(
    image_path: Path,
    bytes_elotte: bytes,
    *,
    uj_fajlok: tuple[Path, ...],
    uj_mappak: tuple[Path, ...],
) -> Iterator[None]:
    """A Mentés csere előtti hibájánál eltünteti a mentés nyomát (#7466).

    A törlés feltételét a `_nyom_torlese_valtozatlan_kepnel` mondja ki. A
    hiba változatlanul megy tovább.

    A csere hibájánál a `_mentett_kep_irasa` akkor is takarít, ha a kép épp
    zárolt és nem olvasható, de a kész kép még az ideiglenes fájlban van (a
    csere tehát nem történt meg).
    """
    try:
        yield
    except BaseException:
        _nyom_torlese_valtozatlan_kepnel(
            image_path, bytes_elotte, uj_fajlok=uj_fajlok, uj_mappak=uj_mappak
        )
        raise


def _nyom_torlese_valtozatlan_kepnel(
    image_path: Path,
    bytes_elotte: bytes,
    *,
    uj_fajlok: tuple[Path, ...],
    uj_mappak: tuple[Path, ...],
) -> None:
    """A meghiúsult mentés nyomának törlése, ha a kép bájtra a régi.

    Az ott maradt pillanatképre az „Utolsó mentés visszavonása” ráfutna, és
    törölné az ini `filters=` sorát, pedig mentés nem történt (#7466, #7469).

    Ha a kép eltér a mentés előttitől, vagy nem olvasható, a másolat lehet az
    eredeti egyetlen példánya, ezért marad. Best-effort: nem dob, hogy a
    hívóhoz a mentés eredeti hibája jusson el.
    """
    with contextlib.suppress(OSError):
        if image_path.read_bytes() == bytes_elotte:
            _mentes_nyomanak_torlese(uj_fajlok, uj_mappak)


def _kesz_kep_megtartasa(temp: Path, cel: Path) -> None:
    """A kész, de a helyére nem tett kép `cel` néven marad.

    Meglévő fájlt nem írunk felül: az a felhasználó saját képe is lehet.
    Best-effort: a hívóhoz a csere eredeti hibája jusson el.
    """
    with contextlib.suppress(OSError):
        # Az ideiglenes fájl a cél jogait örökölte; az írásvédettséget ne
        # vigye tovább (Windowson törölni sem lehetne).
        temp.chmod(stat.S_IMODE(temp.stat().st_mode) | stat.S_IWRITE)
        if not os.path.lexists(cel):
            _atnevez(temp, cel)


def _mentes_nyomanak_torlese(
    fajlok: tuple[Path, ...], mappak: tuple[Path, ...]
) -> None:
    """A meghiúsult mentés által létrehozott fájlok és mappák törlése.

    A `mappak` belülről kifelé halad; az `rmdir` csak üres mappát töröl.
    """
    for fajl in fajlok:
        with contextlib.suppress(OSError):
            fajl.unlink()
    for mappa in mappak:
        with contextlib.suppress(OSError):
            mappa.rmdir()


def find_original_backup(image_path: str | api.Path) -> api.Path | None:
    """A képhez megőrzött eredeti — MINDKÉT mappanevet megnézve (#1425).

    Az `ORIGINALS_DIR_NAMES` sorrendjében keres (régi `Originals` előbb, ld.
    a modul „Két mappanév" szakaszát), és az első meglévő fájl útját adja
    vissza. Ha egyik mappában sincs példány, `None`.

    Csak a KÉT ismert nevet nézi meg, kis-nagybetű pontosan, és nem listázza
    ki a mappát: képenként így legfeljebb két `stat()` — a #1146 tanulsága
    szerint a tulajdonos gyűjteménye hálózati megosztáson él, ahol minden
    fölösleges könyvtárlistázás egy hálózati kör.
    """
    image_path = api.Path(image_path)
    for dir_name in api.ORIGINALS_DIR_NAMES:
        candidate = image_path.parent / dir_name / image_path.name
        if candidate.is_file():
            return candidate
    return None

def _missing_original_message(image_path: Path) -> str:
    """A „nincs megőrzött eredeti" ÉRTHETŐ üzenete (#1425).

    A néma elutasítás a projekt visszatérő hibaosztálya (#1003, #1207,
    #1213): a felhasználónak — aki nem programozó — meg kell tudnia, MIT
    kerestünk, HOL, és mikor működik egyáltalán a Visszaállítás. Belső
    függvénynevek nem szivároghatnak ki ide.
    """
    mappak = " és ".join(f"„{name}”" for name in api.ORIGINALS_DIR_NAMES)
    return (
        f"Ehhez a képhez nincs megőrzött eredeti: {image_path.name}. "
        f"A kép melletti {mappak} nevű almappák egyikében sem találtuk meg "
        f"a mentés előtti változatát. A Visszaállítás csak olyan képnél "
        f"működik, amelyről készült ilyen másolat — a PicasaPy és a Picasa "
        f"is az első mentéskor készíti el. "
        f"(Keresett hely: {image_path.parent})"
    )

def _backup_path_for(image_path: Path) -> Path:
    """Ahová egy ÚJ eredeti-mentés kerül: mindig a `.picasaoriginals`.

    A régi, `Originals` mappát csak OLVASSUK (ld. `find_original_backup`) —
    a Picasa-korabeli, látható mappába nem írunk.
    """
    return image_path.parent / api.ORIGINALS_DIR_NAME / image_path.name

def _original_ini_path(image_path: Path, backup_path: Path | None = None) -> Path:
    """A kiválasztott megőrzött eredeti-mappa `.picasa.ini`-je.

    Mentésnél a tényleges eredeti fájl mappáját kapjuk meg. Visszavonásnál
    előbb ugyanazt a fájlt keressük; ha hiányzik, a meglévő eredeti-mappa
    ini-jét választjuk, végül az új `.picasaoriginals` mappa az alapérték.
    """
    if backup_path is None:
        backup_path = api.find_original_backup(image_path)
    if backup_path is not None:
        return backup_path.parent / api._INI_FILENAME

    for directory_name in api.ORIGINALS_DIR_NAMES:
        directory = image_path.parent / directory_name
        if api.ini_source_path(directory / api._INI_FILENAME) is not None:
            return directory / api._INI_FILENAME
    return image_path.parent / api.ORIGINALS_DIR_NAME / api._INI_FILENAME

def _snapshot_path(image_path: Path, number: int) -> Path:
    """Ahová egy ÚJ pillanatkép kerül: a `.picasapy-snapshots` alkönyvtárba.

    #444: a Picasa binárisában a `.picasaoriginals` névmintája `%s.%d.jpg`
    (`.mov`, `.wmv`) — vagyis a „szent" eredeti MELLETT mentésenként külön,
    SORSZÁMOZOTT másolat is készül. Ez teszi lehetővé az „Utolsó mentés
    visszavonása" parancsot (`undo_save`): az utolsó mentés visszavonható
    úgy, hogy a SZERKESZTÉSEK MEGMARADNAK.

    #2512: a NÉVMINTÁT megtartjuk, a HELYET nem. A Picasáéval közös
    mappában ez a név egy önálló kép „szent" eredetijétől
    megkülönböztethetetlen volt (ld. a modul „A pillanatképek KÜLÖN
    NÉVTERE" szakaszát), és a `find_original_backup` emiatt idegen
    bájtokat adott vissza.
    """
    directory = image_path.parent / api.ORIGINALS_DIR_NAME / api.SNAPSHOT_DIR_NAME
    return directory / f"{image_path.stem}.{number}{image_path.suffix}"

def _legacy_snapshot_path(image_path: Path, number: int) -> Path:
    """A pillanatkép RÉGI, a `.picasaoriginals`-szal közös helye (#444).

    Ide már nem írunk (#2512), de a sorszám-kiosztásnál számít: ha a régi
    helyen áll ezen a néven fájl, a sorszámot átlépjük. Nem a felülírás
    ellen — az új hely miatt az kizárt —, hanem hogy ugyanaz a sorszám ne
    létezzen KÉTSZER, két különböző helyen: az `undo_save` a legnagyobb
    sorszámú példányt veszi, és egyenlőségnél nem tudná eldönteni, melyik
    a frissebb.
    """
    directory = image_path.parent / api.ORIGINALS_DIR_NAME
    return directory / f"{image_path.stem}.{number}{image_path.suffix}"

def _existing_snapshots(image_path: Path) -> list[tuple[int, Path]]:
    """A meglévő sorszámozott pillanatképek `(N, útvonal)` párjai, növekvő
    sorrendben.

    A keresés a `fileops.originals.snapshot_numbers` KÖZÖS szabálya (#1449) —
    itt korábban `glob()` állt, két néma hibával:

    * a fájlnévben lévő `[`, `*` vagy `?` a mintában jokerként viselkedett
      (egy `IMG[1].jpg` képnél rossz vagy nulla találat),
    * és nem nézte, hogy a `<név>.<N><kiterjesztés>` alak egy ÖNÁLLÓ kép
      megőrzött eredetije is lehet — az `undo_save` pedig a felhasznált
      pillanatképet TÖRLI, tehát egy másik kép visszaútját semmisítette
      volna meg.

    **Az óvatosságnak ára van** (#1449 átnézés, 3. lelet): ha a képmappában
    van azonos nevű önálló kép, a példány kimarad, és az `undo_save`
    elveszíti a visszavonást egy LÉTEZŐ pillanatképhez. Adat nem vész el, de
    a sorszám-átlépés (`save_edited`) miatt minden további mentés újabb
    teljes méretű JPEG-et halmoz, amit semmi nem takarít. Tisztább megoldás
    nincs: a két eset a lemezen bitre azonosan néz ki, a tévedés iránya
    pedig itt egy MÁSIK kép visszaútjának a megsemmisítése lenne. Amit
    megtehetünk, az a kimondás — ld. `_nincs_visszavonhato_mentes`.

    **Két hely, egy lista** (#2512): az ÚJ pillanatképeink a
    `.picasapy-snapshots` alkönyvtárban vannak, a korábbi verzióink (és a
    Picasa) példányai a `.picasaoriginals`-ban közvetlenül. A
    `snapshot_numbers` mindkettőt végignézi; a fenti óvatossági szabály
    csak a RÉGI helyre vonatkozik, mert az ÚJ alkönyvtárba rajtunk kívül
    senki nem ír.

    A késleltetett import szándékos: a `fileops` csomag maga is (lustán) ide
    nyúl a mappanevekért, a modulszintű import körbeérne."""
    from picasapy.fileops.originals import snapshot_numbers

    directory = image_path.parent / api.ORIGINALS_DIR_NAME
    return sorted(
        (szam, path) for szam, _, path in snapshot_numbers(directory, image_path)
    )

def _nincs_visszavonhato_mentes(image_path: Path) -> str:
    """A „nincs mit visszavonni" üzenet — a KÉT eset másképp szól.

    Az `_existing_snapshots` üres eredménye nem mindig azt jelenti, hogy a
    mappa üres: kimarad belőle az a példány is, aminek a KÉPMAPPÁBAN van
    azonos nevű gazdája (`a.jpg` mentése `a.1.jpg` pillanatképet ír, de
    `a.1.jpg` lehet egy önálló kép is). Az óvatosság indokolt — az
    `undo_save` a felhasznált pillanatképet TÖRLI —, de az „üres vagy
    hiányzik" ilyenkor egyszerűen nem igaz, és a felhasználó nem tudja meg,
    mit tehetne (#1449 átnézés, 3. lelet)."""
    from picasapy.fileops.originals import ambiguous_snapshot_names

    directory = image_path.parent / api.ORIGINALS_DIR_NAME
    ketertelmuek = ambiguous_snapshot_names(directory, image_path)
    if not ketertelmuek:
        return (
            f"Nincs visszavonható mentés: {image_path.name} "
            f"({api.ORIGINALS_DIR_NAME} üres vagy hiányzik)"
        )
    nevek = ", ".join(ketertelmuek)
    return (
        f"A legutóbbi mentést nem tudjuk visszavonni ennél a képnél: "
        f"{image_path.name}. A(z) „{api.ORIGINALS_DIR_NAME}” mappában van hozzá "
        f"illő fájl ({nevek}), de a képmappában UGYANEZEN a néven önálló kép "
        f"is áll — így nem dönthető el, hogy az a kép mentés előtti "
        f"állapota-e, vagy a másik kép megőrzött eredetije. Biztonságból "
        f"békén hagyjuk: a visszavonás azt a fájlt törölné, és ha a másik "
        f"képhez tartozik, annak a visszaútja veszne el. Ha vissza szeretné "
        f"kapni a visszavonás lehetőségét, adjon a(z) {nevek} nevű képnek "
        f"másik nevet."
    )

def _encode_image(suffix: str, image: np.ndarray, jpeg_quality: int) -> bytes:
    """A renderelt képmátrix kódolása a cél kiterjesztésének megfelelő
    formátumba — `cv2.imencode`-dal (memóriapuffer, nem fájlútvonal),
    accent-path-biztosan (MEMORY.md #190)."""
    ext = suffix.lower() or ".jpg"
    params: list[int] = []
    if ext in (".jpg", ".jpeg"):
        params = [api.cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
    # #1527: az OpenCV NEM mindig `ok=False`-szal jelez. Ismeretlen
    # kiterjesztésnél `cv2.error`-t DOB („could not find encoder for the
    # specified extension"), ami eddig NYERSEN szökött ki a mentésből — a
    # `save_controller._SAVE_ERRORS` sem fogta, mert a `cv2.error` nem
    # `OSError`/`ValueError`. Ez a hivatalos „fájlformázási hiba" ága
    # (`CFileSaveThread:filesaveerr3`), tehát ide `SaveError` való.
    try:
        ok, encoded = api.cv2.imencode(ext, image, params)
    except api.cv2.error as hiba:
        raise api.SaveError(f"A renderelt kép nem kódolható ide: {ext!r}") from hiba
    if not ok:
        raise api.SaveError(f"A renderelt kép nem kódolható ide: {ext!r}")
    return encoded.tobytes()
