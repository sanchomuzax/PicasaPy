"""A mentés .picasa.ini round-trip segédműveletei (#6168)."""

from __future__ import annotations

from pathlib import Path
import picasapy.edit.save as api
from picasapy.edit.save import _PhotoIniSnapshot
from picasapy.ini import IniDocument


def _ini_ertek(document: IniDocument, section_name: str, key: str) -> str | None:
    """Egy képszakasz kulcsának értéke, hiányzó szakasznál `None`."""
    section = document.section(section_name)
    return section.get(key) if section is not None else None


#: Egy írási kísérlet: (kiírandó dokumentum, forrásfájl, előtte-dokumentum).
_Kiserlet = tuple[IniDocument, Path | None, IniDocument]


def _iras_rogzitese(
    snapshot: _PhotoIniSnapshot,
    ini_path: Path,
    section_name: str,
    kiserlet: _Kiserlet,
) -> None:
    """A lemezre került írás előállapota a kompenzációhoz."""
    candidate, source, before = kiserlet
    snapshot.values = {
        key: _ini_ertek(before, section_name, key) for key in snapshot.values
    }
    snapshot.document = before
    snapshot.target_existed = source == ini_path
    snapshot.written_document = candidate


def _irasunk_a_lemezen_van(
    ini_path: Path,
    section_name: str,
    keys: tuple[str, ...],
    kiserlet: _Kiserlet,
) -> bool:
    """A hibát dobó írás ettől még lecserélte-e a fájlt (#7473).

    Igen, ha valamelyik kulcs, amelyet változtatni akartunk, a kiírandó
    értéken áll (akkor is, ha közben külső változás is jött), vagy az előtte
    hiányzó cél tartalma a mi dokumentumunk. Nem dob: olvashatatlan célnál az
    eredeti írási hiba megy tovább.
    """
    candidate, source, before = kiserlet
    try:
        if not ini_path.is_file():
            return False
        current = api.load_or_empty(ini_path)
    except OSError:
        return False
    if source != ini_path and current.serialize() == candidate.serialize():
        return True
    return any(
        _ini_ertek(current, section_name, key)
        == _ini_ertek(candidate, section_name, key)
        != _ini_ertek(before, section_name, key)
        for key in keys
    )


def _section_name(image_path: Path) -> str:
    """A `.picasa.ini`-beli szekciónév: a fájl neve, a spec `[<fájlnév.ext>]`
    szabálya szerint (ld. `picasa-ini-format.md`)."""
    return image_path.name

def _update_ini_document(
    image_path: Path,
    mutate,
    *,
    rollback_snapshot: _PhotoIniSnapshot | None = None,
    section_name: str | None = None,
) -> IniDocument:
    """Ütközésbiztos, atomikus, backup-olt ini-frissítés (#137-minta).

    Kizárólag a round-trip réteget (`update_document`) hívja — soha nem ír
    közvetlenül fájlba —, hogy az ismeretlen kulcsok/szekciók bitre pontosan
    megmaradjanak (spec 2. írási szabálya)."""
    return api._update_ini_path(
        image_path.parent / api._INI_FILENAME,
        mutate,
        rollback_snapshot=rollback_snapshot,
        section_name=section_name,
    )

def _update_ini_path(
    ini_path: Path,
    mutate,
    *,
    rollback_snapshot: _PhotoIniSnapshot | None = None,
    section_name: str | None = None,
) -> IniDocument:
    """Ütközésbiztos, atomikus ini-frissítés az `ini` round-trip API-n át.

    A `rollback_snapshot.written_document` akkor (és csak akkor) töltődik ki,
    ha az írás a lemezre került: sikeres visszatérésnél, és akkor is, ha a
    hiba már a fájlcsere UTÁN jött (#7473).
    """
    if rollback_snapshot is None:
        return api.update_document(ini_path, mutate, backup=True)
    if section_name is None:
        raise ValueError("A visszagörgetéshez ini-szekciónév szükséges")

    # Az update_document minden ütközésnél újra meghívja a tiszta mutátort,
    # és a nyertes próbálkozás `mutated` objektumát adja vissza. Az azonos
    # objektumhoz rögzítjük a tényleges előtti dokumentumot és forrást, hogy
    # a kompenzáció ne az előzetes (esetleg elavult) olvasást írja vissza.
    attempts: list[_Kiserlet] = []

    def capture_attempt(document: IniDocument) -> IniDocument:
        updated = mutate(document)
        attempts.append((updated, api.ini_source_path(ini_path), document))
        return updated

    try:
        written = api.update_document(ini_path, capture_attempt, backup=True)
    except OSError:
        # Csak az `OSError` jöhet csere után (pl. a könyvtár fsync-je); az
        # ütközés- és kódolási hibák írás nélkül dobnak.
        if attempts and _irasunk_a_lemezen_van(
            ini_path, section_name, tuple(rollback_snapshot.values), attempts[-1]
        ):
            _iras_rogzitese(rollback_snapshot, ini_path, section_name, attempts[-1])
        raise
    for kiserlet in reversed(attempts):
        if kiserlet[0] is written:
            _iras_rogzitese(rollback_snapshot, ini_path, section_name, kiserlet)
            return written
    raise RuntimeError("Az ini-frissítés nyertes előállapota nem található")

def _photo_ini_values(
    ini_path: Path, section_name: str, keys: tuple[str, ...]
) -> api._PhotoIniSnapshot:
    """Egy képszakasz érintett kulcsainak mentés előtti értékei."""
    target_existed = ini_path.is_file()
    document = api.load_or_empty(ini_path)
    section = document.section(section_name)
    return api._PhotoIniSnapshot(
        values={
            key: section.get(key) if section is not None else None
            for key in keys
        },
        document=document,
        target_existed=target_existed,
    )

def _restore_photo_ini_values(
    ini_path: Path, section_name: str, snapshot: _PhotoIniSnapshot
) -> None:
    """API-n át visszaállítja a kompenzáló írással felülírt kulcsértékeket.

    Ha a mi írásunk nem került a lemezre (`written_document` hiányzik), nincs
    teendő: egy fölös visszaírás (pl. tele lemeznél) maga is hibázna.

    Ha a meglévő ini a mi írásunk óta nem változott, a művelet előtti
    dokumentum megy vissza egészben, így a kulcsok sorrendje (a bájtok) is a
    régi (#7469). Egyébként csak azt a kulcsot állítja vissza, amely a
    kompenzáló írás óta is a mi kiírt értékünkön áll: a közben érkezett külső
    változást megőrzi.
    """

    written = snapshot.written_document
    if written is None:
        return

    def mutate(document):
        current_section = document.section(section_name)
        for key, value in snapshot.values.items():
            current_value = (
                current_section.get(key) if current_section is not None else None
            )
            if current_value != _ini_ertek(written, section_name, key):
                continue
            if value is None:
                document = document.with_removed(section_name, key)
            else:
                document = document.with_value(
                    section_name,
                    key,
                    value,
                    carried=key in (api._FILTERS_KEY, api._REDO_KEY),
                )
        return document

    def egeszben_vagy_kulcsonkent(document):
        if document.serialize() == written.serialize():
            return snapshot.document
        return mutate(document)

    if snapshot.target_existed:
        api.update_document(
            ini_path, egeszben_vagy_kulcsonkent, backup=False, touch=snapshot.touch
        )
        return

    # A mentés hozhatta létre a cél `.picasa.ini`-t (esetleg egy régi
    # `Picasa.ini` forrásból kiindulva). Ha a sikeres írás óta bájtra pontosan
    # változatlan maradt, törölhető a művelet előtti hiányállapot visszaállításához.
    if api.remove_ini_target_if_content_matches(ini_path, written):
        return
    if not ini_path.is_file():
        return

    # Közben módosított célfájlnál nem törlünk: az érintett kulcsokat API-n
    # át visszaállítjuk, az esetleges idegen sorokat pedig megőrizzük.
    api.update_document(ini_path, mutate, backup=False, touch=snapshot.touch)
