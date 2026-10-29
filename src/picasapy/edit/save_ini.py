"""A mentés .picasa.ini round-trip segédműveletei (#6168)."""

from __future__ import annotations

from pathlib import Path
import picasapy.edit.save as api
from picasapy.edit.save import _PhotoIniSnapshot
from picasapy.ini import IniDocument


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
    """Ütközésbiztos, atomikus ini-frissítés az `ini` round-trip API-n át."""
    if rollback_snapshot is None:
        return api.update_document(ini_path, mutate, backup=True)
    if section_name is None:
        raise ValueError("A visszagörgetéshez ini-szekciónév szükséges")

    # Az update_document minden ütközésnél újra meghívja a tiszta mutátort,
    # és a nyertes próbálkozás `mutated` objektumát adja vissza. Az azonos
    # objektumhoz rögzítjük a tényleges előtti dokumentumot és forrást, hogy
    # a kompenzáció ne az előzetes (esetleg elavult) olvasást írja vissza.
    attempts: list[tuple[IniDocument, Path | None, IniDocument]] = []

    def capture_attempt(document: IniDocument) -> IniDocument:
        updated = mutate(document)
        attempts.append((updated, api.ini_source_path(ini_path), document))
        return updated

    written = api.update_document(ini_path, capture_attempt, backup=True)
    for candidate, source, before in reversed(attempts):
        if candidate is written:
            section = before.section(section_name)
            rollback_snapshot.values = {
                key: section.get(key) if section is not None else None
                for key in rollback_snapshot.values
            }
            rollback_snapshot.document = before
            rollback_snapshot.target_existed = source == ini_path
            rollback_snapshot.written_document = written
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

    Csak azt a kulcsot állítja vissza, amely a kompenzáló írás óta is a mi
    kiírt értékünkön áll. A közben érkezett külső változást megőrzi.
    """

    written_section = (
        snapshot.written_document.section(section_name)
        if snapshot.written_document is not None
        else None
    )

    def mutate(document):
        current_section = document.section(section_name)
        for key, value in snapshot.values.items():
            written_value = (
                written_section.get(key) if written_section is not None else None
            )
            current_value = (
                current_section.get(key) if current_section is not None else None
            )
            if current_value != written_value:
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

    if snapshot.target_existed:
        api.update_document(ini_path, mutate, backup=False)
        return

    # A mentés hozhatta létre a cél `.picasa.ini`-t (esetleg egy régi
    # `Picasa.ini` forrásból kiindulva). Ha a sikeres írás óta bájtra pontosan
    # változatlan maradt, törölhető a művelet előtti hiányállapot visszaállításához.
    if snapshot.written_document is not None and api.remove_ini_target_if_content_matches(
        ini_path, snapshot.written_document
    ):
        return
    if not ini_path.is_file():
        return

    # Közben módosított célfájlnál nem törlünk: az érintett kulcsokat API-n
    # át visszaállítjuk, az esetleges idegen sorokat pedig megőrizzük.
    api.update_document(ini_path, mutate, backup=False)
