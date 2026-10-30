"""Az arcdetektálás futásnyomainak és mappakizárásának műveletei."""


from __future__ import annotations


import sqlite3


#: A `face_scan.ok` értékei — a jelölés OKA (#2519).
#:
#: `detektalva`: lefutott a detektálás (találattal vagy anélkül). A fájl
#: megváltozása feloldja: az új tartalmat újra meg kell nézni.
#:
#: `kizarva`: a Mappakezelő arcfelismerés-kizárása tette ki. **ERŐSEBB** — a
#: fájl változása sem oldja fel, csak a szándékos visszaengedés
#: (`forget_face_scan`). Ez az eredeti Picasa `facerect = 1` jelzőjének
#: megfelelője (`docs/specs/picasa-imagedata-rekord.md`, #2515): a téglalap
#: írója csak nulla értékre ír, tehát az 1 megvédi a képet.
OK_DETEKTALVA = "detektalva"
OK_KIZARVA = "kizarva"

#: A mappa ÉS az alfái — a kizárás az egész fára vonatkozik (`#449`: „a
#: mappára és az alfáira"). A `LIKE`-minta ESCAPE-elve megy, mert egy valódi
#: mappanévben is állhat `%` vagy `_` (mindkettő joker a `LIKE`-ban).
#:
#: ⚠️ #2765: MINDKÉT elválasztóra illeszkedünk, nem csak a platforméra. A
#: #2761 a fixen `/`-t fűző mintát a platformére (`os.sep`) cserélte — és
#: ezzel átcsapott a másik oldalra: a POSIX-alakban tárolt utak (átvett
#: adatbázis, másik gépről hozott `.picasa.ini`-korpusz, régebbi indexünk)
#: Windowson estek ki. A `folders.path` tehát nem feltétlenül natív alakú —
#: ezt a `rstrip("/\\")` már eddig is kimondta, csak a minta nem követte.
_MAPPAFA_FELTETEL = (
    "(f.path = ? OR f.path LIKE ? ESCAPE '\\' OR f.path LIKE ? ESCAPE '\\')"
)


def _like_vedett(szoveg: str) -> str:
    """A `LIKE`-minta escape-elése (`ESCAPE '\'`): a backslash ÖNMAGÁT is
    escape-eli, a `%` és a `_` pedig joker."""
    return szoveg.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _mappafa_parameterek(folder_path: str) -> tuple[str, str, str]:
    """A `_MAPPAFA_FELTETEL` három paramétere: a pontos út, majd az alfa-minta
    MINDKÉT elválasztóval (perjel és fordított perjel).

    Nincs platform-elágazás: a tárolt út alakja nem a futó gépé, hanem azé,
    ahol az index készült. Két mintát adunk, és a `LIKE` dönt."""
    # a záró elválasztót MINDKÉT alakban levágjuk (a `C:\kepek\` és a
    # `/kepek/` ugyanazt a fát jelenti, mint a lezáró jel nélküli alak)
    torzs = _like_vedett(folder_path.rstrip("/\\"))
    return (folder_path, torzs + "/%", torzs + "\\\\%")


def mark_face_scan(
    conn: sqlite3.Connection,
    photo_id: int,
    *,
    mtime_ns: int,
    size: int,
    ok: str = OK_DETEKTALVA,
) -> None:
    """Nyom hagyása arról, hogy a fotón LEFUTOTT az arc-detektálás.

    A `face` tábla csak a megtalált arcokat tárolja, ezért nyom nélkül egy
    arc nélküli fotó megkülönböztethetetlen a még sosem vizsgálttól — a
    detektálás minden szkennelésnél újrafutna rajta (#2519).

    Fotónként EGY sor (a `photo_id` az elsődleges kulcs), tehát az ismételt
    jelölés felülír, nem duplikál. A hívó felelős a commitért."""
    conn.execute(
        "INSERT INTO face_scan(photo_id, mtime_ns, size, ok) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(photo_id) DO UPDATE SET"
        " mtime_ns = excluded.mtime_ns, size = excluded.size, ok = excluded.ok",
        (photo_id, int(mtime_ns), int(size), ok),
    )


def face_scan_done(
    conn: sqlite3.Connection, photo_id: int, *, mtime_ns: int, size: int
) -> bool:
    """Lefutott-e már a detektálás EZEN a fájlállapoton?

    `True`, ha van jelölés, ÉS vagy a fájl azonossága (`mtime_ns`, `size`)
    egyezik, vagy a jelölés oka `kizarva` — az utóbbit a fájl változása sem
    oldja fel (ld. `OK_KIZARVA`)."""
    sor = conn.execute(
        "SELECT mtime_ns, size, ok FROM face_scan WHERE photo_id = ?", (photo_id,)
    ).fetchone()
    if sor is None:
        return False
    if sor[2] == OK_KIZARVA:
        return True
    return int(sor[0]) == int(mtime_ns) and int(sor[1]) == int(size)


def mark_folder_excluded(conn: sqlite3.Connection, folder_path: str) -> int:
    """A mappa MINDEN fotójának megjelölése `kizarva` okkal; a megjelöltek
    száma.

    Az eredeti Picasa a Mappakezelő arcfelismerés-kizárásakor teszi ki a
    saját jelzőjét a képekre (`CFolderMgrDialog` → `FUN_005cef20` →
    `FUN_00491210` → `FUN_00446960`, `0x00491627`) — enélkül a mappa
    visszaengedése azonnal, kérdés nélkül újraindítaná a detektálást.

    A hívó felelős a commitért."""
    kurzor = conn.execute(
        "INSERT INTO face_scan(photo_id, mtime_ns, size, ok)"
        " SELECT p.id, p.mtime_ns, p.size, ?"
        " FROM photos p JOIN folders f ON f.id = p.folder_id"
        f" WHERE {_MAPPAFA_FELTETEL}"
        " ON CONFLICT(photo_id) DO UPDATE SET"
        " mtime_ns = excluded.mtime_ns, size = excluded.size, ok = excluded.ok",
        (OK_KIZARVA, *_mappafa_parameterek(folder_path)),
    )
    return int(kurzor.rowcount)


def forget_face_scan(
    conn: sqlite3.Connection, *, folder_path: str | None = None, photo_id: int | None = None
) -> int:
    """A jelölés törlése — ettől a következő szkennelés újra megnézi a
    fotókat. A törölt sorok száma.

    Egy mappa visszaengedésekor a hívó a felhasználó megerősítő válasza UTÁN
    hívja: a jelölés eldobása szándékos döntés, nem automatizmus."""
    if photo_id is not None:
        kurzor = conn.execute("DELETE FROM face_scan WHERE photo_id = ?", (photo_id,))
    elif folder_path is not None:
        kurzor = conn.execute(
            "DELETE FROM face_scan WHERE photo_id IN ("
            " SELECT p.id FROM photos p JOIN folders f ON f.id = p.folder_id"
            f" WHERE {_MAPPAFA_FELTETEL})",
            _mappafa_parameterek(folder_path),
        )
    else:
        raise ValueError("a `folder_path` és a `photo_id` közül az egyik kötelező")
    return int(kurzor.rowcount)


def delete_faces_in_folder(conn: sqlite3.Connection, folder_path: str) -> int:
    """A mappa (és alfái) fotóihoz tárolt SAJÁT arc-találatok törlése; a
    törölt sorok száma.

    A `.picasa.ini` `faces=` / `[Contacts2]` adatát ez NEM érinti — az a
    felhasználó saját, Picasában felvett adata. Itt csak a származtatott
    (bármikor újraszámolható) találataink tűnnek el, a kizárás megerősítő
    kérdése után (#2519). A hívó felelős a commitért."""
    kurzor = conn.execute(
        "DELETE FROM face WHERE photo_id IN ("
        " SELECT p.id FROM photos p JOIN folders f ON f.id = p.folder_id"
        f" WHERE {_MAPPAFA_FELTETEL})",
        _mappafa_parameterek(folder_path),
    )
    return int(kurzor.rowcount)
