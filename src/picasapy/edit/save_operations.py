"""Mentési műveletek: mentés, visszavonás és visszaállítás (#6168)."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import picasapy.edit.save as api
from picasapy.edit.save import _PhotoIniSnapshot
from picasapy.edit.session import EditSession
from picasapy.ini import IniDocument


def save_edited(
    image_path: str | api.Path,
    rendered_image: np.ndarray,
    filters: EditSession,
    *,
    jpeg_quality: int = api._DEFAULT_JPEG_QUALITY,
) -> api.SaveResult:
    """A nem-destruktív "Mentés": a renderelt kép az eredeti helyére kerül.

    Args:
        image_path: A kép jelenlegi, fizikai elérési útja a mappában (a
            `.picasa.ini` mellette, a szülőkönyvtárban van).
        rendered_image: A szerkesztési lánc beleégetésével kapott
            képmátrix, OpenCV BGR-konvencióban (ahogy a render/export
            modulok is használják) — a RENDERELÉS a hívó feladata, ez a
            függvény csak a perzisztenciát és az ini-könyvelést végzi.
        filters: A MOST mentett szerkesztési lánc (`EditSession`); ennek
            szerializált értéke kerül az eredeti-mappa ini-jének `filters=`
            kulcsába.
        jpeg_quality: JPEG-minőség (csak `.jpg`/`.jpeg` célútnál számít).

    Returns:
        `SaveResult` a végrehajtott lépések adataival.

    Raises:
        SaveError: ha a renderelt kép nem kódolható a cél kiterjesztésbe,
            vagy ha az ini-hiba utáni képfájl-visszaállítás sem sikerült
            (#297 — ekkor a kép és az ini nyilvántartása eltér).
        OSError | IniSaveError | IniConflictError: ha az ini-könyvelés nem
            sikerült. A képfájl ilyenkor VISSZAÁLL a mentés előtti
            állapotra, hogy ne maradjon dupla-szerkesztés (#297).
    """
    image_path = api.Path(image_path)
    # #1425: a „szent" eredeti bármelyik ismert mappanév alatt ott lehet —
    # ha van, azt tekintjük megőrzöttnek, és nem teszünk mellé másodikat.
    existing_backup = api.find_original_backup(image_path)
    backup_path = existing_backup or api._backup_path_for(image_path)
    filters_value = filters.to_value()
    section = api._section_name(image_path)
    current_ini_path = image_path.parent / api._INI_FILENAME
    original_ini_path = backup_path.parent / api._INI_FILENAME
    # Minden ini-olvasás és visszaállítási állapotfelvétel a kép cseréje
    # ELŐTT történjen: olvasási hiba esetén ne maradjon beégetett, de el nem
    # könyvelt kép.
    current_before = api._photo_ini_values(
        current_ini_path,
        section,
        (api._FILTERS_KEY, api._REDO_KEY, "backuphash", api._MODDATE_KEY),
    )
    original_before = api._photo_ini_values(
        original_ini_path, section, (api._FILTERS_KEY, api._MODDATE_KEY)
    )

    # A (b) lépés ELŐTTI bájtok — ezekre kell visszaállni, ha a (c) elbukik
    # (#297). Első mentésnél ez maga az eredeti (ugyanaz, ami a
    # `.picasaoriginals`-ba kerül), ismételt mentésnél a KORÁBBI mentés
    # renderelt tartalma.
    source_stat = image_path.stat()
    original_mtime_ns = source_stat.st_mtime_ns
    moddate_value = api.moddate_from_timestamp_ns(original_mtime_ns)
    bytes_before_write = image_path.read_bytes()

    # (a) Az eredeti megőrzése — KIZÁRÓLAG ha még nincs korábbi mentésből
    # (sem a mai, sem a 2009 előtti nevű mappában).
    backup_created_now = existing_backup is None
    backup_mtime_ns = (
        original_mtime_ns if backup_created_now else backup_path.stat().st_mtime_ns
    )
    if backup_created_now:
        api.write_atomic(backup_path, bytes_before_write, make_parents=True)

    # (a2) #444: MENTÉSENKÉNTI, sorszámozott pillanatkép a mentés ELŐTTI
    # bájtokról — ez teszi visszavonhatóvá az utolsó mentést a szerkesztések
    # elvesztése nélkül (`undo_save`). A „szent" eredeti (fent) ettől
    # függetlenül megmarad a Visszaállításhoz.
    snapshots = api._existing_snapshots(image_path)
    next_number = (snapshots[-1][0] + 1) if snapshots else 1
    # A foglalt sorszámokat átlépjük — MINDKÉT helyen nézve.
    #
    # #1449 (a régi hely): a `<név>.<N>` alak kétértelmű, ott állhat egy
    # MÁSIK, önálló kép megőrzött eredetije (`a.jpg` pillanatképe és
    # `a.1.jpg` eredetije azonos nevű). #2512 óta ODA MÁR NEM ÍRUNK, tehát
    # felülírni nem tudnánk; a régi hely mégis számít, mert ugyanaz a
    # sorszám nem létezhet kétszer, két különböző helyen — az `undo_save` a
    # legnagyobb sorszámot veszi, és egyenlőségnél nem tudná eldönteni,
    # melyik a frissebb (`_legacy_snapshot_path`).
    #
    # Az ÚJ helyen a vizsgálat egy korábbi mentés árváját fogja meg (pl. ha
    # a kép azóta más nevet kapott és vissza).
    while (
        api._snapshot_path(image_path, next_number).exists()
        or api._legacy_snapshot_path(image_path, next_number).exists()
    ):
        next_number += 1
    api.write_atomic(
        api._snapshot_path(image_path, next_number), bytes_before_write, make_parents=True
    )

    # (b) A renderelt kép az eredeti HELYÉRE.
    payload = api._encode_image(image_path.suffix, rendered_image, jpeg_quality)
    api._kep_irasa(image_path, payload)

    # (c) A lánc és a mentés előtti fájlidő az eredeti-mappa ini-jébe kerül,
    # a #5810 szerinti backuphash pedig az aktuális mappa ini-jébe. Két ini
    # frissítése nem atomikus, ezért a már sikeres írásokat visszagörgetjük,
    # ha a következő lépés hibázik.
    completed_ini_writes: list[tuple[api.Path, _PhotoIniSnapshot]] = []
    try:
        current_before.written_document = api._update_ini_document(
            image_path,
            lambda document: api.with_backuphash(
                document.with_removed(api._section_name(image_path), api._FILTERS_KEY)
                .with_removed(api._section_name(image_path), api._REDO_KEY),
                api._section_name(image_path),
            ),
            rollback_snapshot=current_before,
            section_name=section,
        )
        completed_ini_writes.append((current_ini_path, current_before))
        original_before.written_document = api._update_ini_path(
            original_ini_path,
            lambda document: (
                document.with_value(
                    api._section_name(image_path), api._FILTERS_KEY,
                    filters_value, carried=True,
                )
                if filters_value
                else document.with_removed(api._section_name(image_path), api._FILTERS_KEY)
            ).with_value(
                api._section_name(image_path), api._MODDATE_KEY, moddate_value, carried=True
            ),
            rollback_snapshot=original_before,
            section_name=section,
        )
        completed_ini_writes.append((original_ini_path, original_before))
        # Az eredeti-mappa ini-frissítése a #643 szerint megérinti a
        # képfájlokat; a megőrzött eredeti másolatán ezt vissza kell állítani
        # az előzőleg rögzített mtime-ra. Első mentésnél ez a forrásé, későbbi
        # mentéseknél a változatlanul megőrzött eredetié.
        api.os.utime(
            backup_path,
            ns=(backup_path.stat().st_atime_ns, backup_mtime_ns),
        )
    except api._INI_WRITE_ERRORS as error:
        rollback_errors = []
        for ini_path, previous_state in reversed(completed_ini_writes):
            try:
                api._restore_photo_ini_values(
                    ini_path, section, previous_state
                )
            except api._INI_WRITE_ERRORS as rollback_error:
                rollback_errors.append(rollback_error)
        image_restore_error = None
        try:
            api._restore_image_or_raise(image_path, bytes_before_write, backup_path, error)
        except api.SaveError as restore_error:
            image_restore_error = restore_error
        if rollback_errors or image_restore_error:
            details = [str(item) for item in rollback_errors]
            if image_restore_error is not None:
                details.append(str(image_restore_error))
            raise api.SaveError(
                "A mentés meghiúsult, és a korábbi fájlállapot teljes "
                f"visszaállítása sem sikerült: {'; '.join(details)}"
            ) from error
        raise

    return api.SaveResult(
        image_path=image_path,
        original_backup_path=backup_path,
        backup_created_now=backup_created_now,
        filters_value=filters_value,
    )

def undo_save(image_path: str | api.Path) -> api.UndoSaveResult:
    """„Utolsó mentés visszavonása" — a SZERKESZTÉSEK MEGMARADNAK (#444).

    Ez a Picasa négy mentés-műveletéből a köztes fokozat, és élesen KÜLÖNBÖZIK
    a `revert`-től:

    * `revert` — a kép visszaáll a „szent" eredetire, és a szerkesztési
      könyvelés is törlődik: *„This cannot be undone and all changes will be
      lost."*
    * `undo_save` — csak az UTOLSÓ lemezre írást vonja vissza: a kép a mentés
      előtti bájtjait kapja vissza, az eredeti-mappa ini-jében tárolt lánc
      pedig visszakerül az aktuális `filters=`-be. Régi PicasaPy-mentésnél a
      láncot a korábbi `redo=` értékből veszi át. Az eredeti szavakkal: *„To undo the last
      save and keep edits click 'Undo Save'."*

    A mentés előtti bájtok a mentésenként készülő, sorszámozott
    pillanatképből jönnek (`_snapshot_path`); a felhasznált pillanatkép a
    művelet végén törlődik, így többszöri hívás lépésenként halad visszafelé.

    Raises:
        SaveError: ha nincs visszavonható mentés (nincs pillanatkép).
    """
    image_path = api.Path(image_path)
    snapshots = api._existing_snapshots(image_path)
    if not snapshots:
        raise api.SaveError(api._nincs_visszavonhato_mentes(image_path))
    number, snapshot = snapshots[-1]
    del number

    section = api._section_name(image_path)
    current_ini_path = image_path.parent / api._INI_FILENAME
    original_backup = api.find_original_backup(image_path)
    original_ini_path = api._original_ini_path(image_path, original_backup)
    current_before = api._photo_ini_values(
        current_ini_path, section, (api._FILTERS_KEY, api._REDO_KEY, "backuphash", api._MODDATE_KEY)
    )
    original_before = api._photo_ini_values(
        original_ini_path, section, (api._FILTERS_KEY, api._MODDATE_KEY)
    )
    current_section = current_before.document.section(section)
    original_section = original_before.document.section(section)
    original_filters = (
        original_section.get(api._FILTERS_KEY) if original_section is not None else None
    )
    original_moddate = (
        original_section.get(api._MODDATE_KEY) if original_section is not None else None
    )
    legacy_redo = (
        current_section.get(api._REDO_KEY) if current_section is not None else None
    )
    restored_filters = (original_filters or legacy_redo or "")

    bytes_before = image_path.read_bytes()
    api._kep_irasa(image_path, snapshot.read_bytes())
    completed_ini_writes: list[tuple[api.Path, _PhotoIniSnapshot]] = []
    try:
        def restore_current_metadata(document: IniDocument) -> IniDocument:
            # #643: a `redo=`-ból VISSZAforgatott lánc, átvitt tartalom.
            updated = (
                document.with_value(section, api._FILTERS_KEY, restored_filters, carried=True)
                if restored_filters
                else document.with_removed(section, api._FILTERS_KEY)
            ).with_removed(section, api._REDO_KEY)
            # A régi mentések eredeti ini-jében nincs feltétlenül moddate.
            # Ilyenkor megőrizzük az aktuális ini esetleges értékét, és nem
            # találunk ki újat. #2675: az `originhash`-t nem töröljük.
            if original_moddate is not None:
                updated = updated.with_value(
                    section, api._MODDATE_KEY, original_moddate, carried=True
                )
            return api.with_backuphash(updated, section)

        current_before.written_document = api._update_ini_document(
            image_path,
            restore_current_metadata,
            rollback_snapshot=current_before,
            section_name=section,
        )
        completed_ini_writes.append((current_ini_path, current_before))
        if original_filters is not None:
            original_before.written_document = api._update_ini_path(
                original_ini_path,
                lambda doc: doc.with_removed(section, api._FILTERS_KEY),
                rollback_snapshot=original_before,
                section_name=section,
            )
            completed_ini_writes.append((original_ini_path, original_before))
    except api._INI_WRITE_ERRORS as error:
        rollback_errors = []
        for ini_path, previous_state in reversed(completed_ini_writes):
            try:
                api._restore_photo_ini_values(ini_path, section, previous_state)
            except api._INI_WRITE_ERRORS as rollback_error:
                rollback_errors.append(rollback_error)
        image_restore_error = None
        try:
            api._restore_image_or_raise(image_path, bytes_before, snapshot, error)
        except api.SaveError as restore_error:
            image_restore_error = restore_error
        if rollback_errors or image_restore_error:
            details = [str(item) for item in rollback_errors]
            if image_restore_error is not None:
                details.append(str(image_restore_error))
            raise api.SaveError(
                "A visszavonás meghiúsult, és a korábbi fájlállapot teljes "
                f"visszaállítása sem sikerült: {'; '.join(details)}"
            ) from error
        raise

    snapshot.unlink(missing_ok=True)
    return api.UndoSaveResult(
        image_path=image_path,
        restored_from=snapshot,
        restored_filters=restored_filters,
    )

def revert(image_path: str | api.Path) -> api.RevertResult:
    """A "Visszaállítás": a megőrzött eredeti visszamásolása.

    Az eredetit MINDKÉT ismert mappanév alatt keresi (`.picasaoriginals` és
    a 2009 előtti `Originals` — ld. a modul „Két mappanév" szakaszát), és a
    `RevertResult.restored_from` megmondja, melyikből dolgozott (#1425).

    A korábbi szerkesztés-könyvelést (`filters=`, `redo=`) az
    ini-ből törli — a fájl a szerkesztés ELŐTTI állapotba kerül vissza,
    a nem-technikai felhasználó elvárása szerint: "vissza az eredetihez".
    Minden más ini-kulcs (csillag, felirat, arcok, albumok, `backuphash`,
    `originhash` — #2675: az a letöltés provenienciája, nem a szerkesztés
    könyvelése —, ismeretlen mezők) érintetlen marad.

    Args:
        image_path: A kép jelenlegi, fizikai elérési útja a mappában.

    Returns:
        `RevertResult` a visszaállítás adataival.

    Raises:
        SaveError: ha egyik ismert mappában sincs megőrzött eredeti — az
            üzenet a felhasználónak szól, és megnevezi mindkét mappát
            (`_missing_original_message`).
    """
    image_path = api.Path(image_path)
    backup_path = api.find_original_backup(image_path)
    if backup_path is None:
        raise api.SaveError(api._missing_original_message(image_path))

    section = api._section_name(image_path)
    current_ini_path = image_path.parent / api._INI_FILENAME
    original_ini_path = backup_path.parent / api._INI_FILENAME
    # Az ini előzetes olvasása a képfájl cseréje előtt történik. Így ha az
    # ini olvashatatlan, a Visszaállítás még nem változtatta meg a képet.
    current_before = api._photo_ini_values(
        current_ini_path, section, api._EDIT_BOOKKEEPING_KEYS
    )
    original_before = api._photo_ini_values(
        original_ini_path, section, (api._FILTERS_KEY,)
    )
    original_section = original_before.document.section(section)
    original_filters = (
        original_section.get(api._FILTERS_KEY)
        if original_section is not None
        else None
    )

    # A visszaállítás ELŐTTI (szerkesztett) bájtok — ezekre kell visszaállni,
    # ha az ini-kulcsok törlése elbukik (#297, fordított irányú rés). Ha a
    # képfájl közben eltűnt, nincs mire visszaállni: ilyenkor a `revert`
    # pótolja a fájlt, és hiba esetén ott is hagyja.
    edited_bytes = image_path.read_bytes() if image_path.exists() else None

    original_bytes = backup_path.read_bytes()
    api._kep_irasa(image_path, original_bytes)

    completed_ini_writes: list[tuple[api.Path, _PhotoIniSnapshot]] = []

    try:
        current_before.written_document = api._update_ini_document(
            image_path,
            lambda document: (
                document.with_removed(section, api._FILTERS_KEY).with_removed(
                    section, api._REDO_KEY
                )
            ),
            rollback_snapshot=current_before,
            section_name=section,
        )
        completed_ini_writes.append((current_ini_path, current_before))
        if original_filters is not None:
            original_before.written_document = api._update_ini_path(
                original_ini_path,
                lambda document: document.with_removed(section, api._FILTERS_KEY),
                rollback_snapshot=original_before,
                section_name=section,
            )
            completed_ini_writes.append((original_ini_path, original_before))
    except api._INI_WRITE_ERRORS as error:
        rollback_errors = []
        for ini_path, previous_state in reversed(completed_ini_writes):
            try:
                api._restore_photo_ini_values(ini_path, section, previous_state)
            except api._INI_WRITE_ERRORS as rollback_error:
                rollback_errors.append(rollback_error)
        image_restore_error = None
        if edited_bytes is not None:
            try:
                api._restore_image_or_raise(image_path, edited_bytes, backup_path, error)
            except api.SaveError as restore_error:
                image_restore_error = restore_error
        if rollback_errors or image_restore_error:
            details = [str(item) for item in rollback_errors]
            if image_restore_error is not None:
                details.append(str(image_restore_error))
            raise api.SaveError(
                "A visszaállítás meghiúsult, és a korábbi fájlállapot teljes "
                f"visszaállítása sem sikerült: {'; '.join(details)}"
            ) from error
        raise

    return api.RevertResult(
        image_path=image_path,
        restored_from=backup_path,
        removed_keys=api._EDIT_BOOKKEEPING_KEYS,
    )

def _restore_image_or_raise(
    image_path: Path, payload: bytes, backup_path: Path, error: Exception
) -> None:
    """A képfájl visszaállítása a művelet előtti bájtokra (#297).

    Ha maga a visszaállítás is elbukik, `SaveError`-t emel: a felhasználónak
    magyarul, cselekvésre fordíthatóan meg kell tudnia, hogy a kép fizikailag
    elmentődött, a `.picasa.ini` nyilvántartása viszont nem követte — így
    tudja, hogy a kép a következő megnyitáskor kétszer szerkesztettnek
    látszhat, és hol keresse az eredetit."""
    try:
        api._kep_irasa(image_path, payload)
    except OSError as restore_error:
        raise api.SaveError(
            f"A kép elmentődött ({image_path}), de a .picasa.ini "
            f"nyilvántartása nem frissült ({error}), és a kép mentés előtti "
            f"állapotát sem sikerült visszaállítani ({restore_error}). A kép "
            f"a következő megnyitáskor kétszer szerkesztettnek látszhat; az "
            f"érintetlen eredeti itt található: {backup_path} "
            f"(a(z) {api.ORIGINALS_DIR_NAME} mappában)."
        ) from error
