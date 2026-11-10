"""Az alsó állapotsáv munkanevei (#6440).

A háttérmunka technikai szálneve (`_start_background(name=...)`) itt kap
emberi nyelvű nevet. A tábla a SZÁLNÉVVEL indexel: a meglévő, egyedi névadó
hívások így változatlanok maradnak. Ami nincs a táblában, az általános
szöveget kap; az őr (`tests/app/test_allapotsav_munkanev_6440.py`)
megnevezi, ha egy új név kimaradt.

A nevek `QT_TRANSLATE_NOOP`-pal állnak a táblában, így a `lupdate` kiszedi
őket; a fordítást a futásidejű fordító adja a `munka_neve`-ben.
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication

KONTEXTUS = "BusyActivity"

ALAP_MUNKANEV = QT_TRANSLATE_NOOP(KONTEXTUS, "Working in the background")
TOBB_MUNKA = QT_TRANSLATE_NOOP(KONTEXTUS, "%1 (+%2 more)")

#: Szálnév (vagy a közvetlen hívóhelyek kulcsa) -> emberi munkanév.
MUNKANEVEK: dict[str, str] = {
    "picasapy-sync-rescan": QT_TRANSLATE_NOOP(KONTEXTUS, "Scanning folders"),
    "picasapy-sync-dirty": QT_TRANSLATE_NOOP(KONTEXTUS, "Syncing changed folders"),
    "picasapy-indulasi-koltozes": QT_TRANSLATE_NOOP(KONTEXTUS, "Moving the library"),
    "picasapy-index-iro": QT_TRANSLATE_NOOP(KONTEXTUS, "Saving the index"),
    "picasapy-thumbnails": QT_TRANSLATE_NOOP(KONTEXTUS, "Generating thumbnails"),
    "picasapy-print": QT_TRANSLATE_NOOP(KONTEXTUS, "Printing"),
    "backup-plan": QT_TRANSLATE_NOOP(KONTEXTUS, "Planning backup"),
    "backup-run": QT_TRANSLATE_NOOP(KONTEXTUS, "Running backup"),
    "backup-iso": QT_TRANSLATE_NOOP(KONTEXTUS, "Creating backup image"),
    "backup-restore": QT_TRANSLATE_NOOP(KONTEXTUS, "Restoring backup"),
    "picasapy-rename": QT_TRANSLATE_NOOP(KONTEXTUS, "Renaming photos"),
    "picasapy-movie": QT_TRANSLATE_NOOP(KONTEXTUS, "Creating movie"),
    "picasapy-dedup": QT_TRANSLATE_NOOP(KONTEXTUS, "Searching for duplicates"),
    "picasapy-face-embed": QT_TRANSLATE_NOOP(KONTEXTUS, "Scanning faces"),
    "picasapy-face-model-download": QT_TRANSLATE_NOOP(KONTEXTUS, "Downloading face model"),
    "picasapy-discovery-startup": QT_TRANSLATE_NOOP(KONTEXTUS, "Searching for a Picasa library"),
    "picasapy-discovery": QT_TRANSLATE_NOOP(KONTEXTUS, "Searching for a Picasa library"),
    "picasapy-export": QT_TRANSLATE_NOOP(KONTEXTUS, "Exporting photos"),
    "picasapy-earth-export": QT_TRANSLATE_NOOP(KONTEXTUS, "Exporting to Google Earth"),
    "picasapy-importsource-scan": QT_TRANSLATE_NOOP(KONTEXTUS, "Scanning import source"),
    "picasapy-importsource-scanfiles": QT_TRANSLATE_NOOP(KONTEXTUS, "Scanning import source"),
    "picasapy-importsource-run": QT_TRANSLATE_NOOP(KONTEXTUS, "Importing photos"),
    "picasapy-editpreview": QT_TRANSLATE_NOOP(KONTEXTUS, "Rendering edit preview"),
    "picasapy-similarity": QT_TRANSLATE_NOOP(KONTEXTUS, "Finding similar photos"),
    "picasapy-passport": QT_TRANSLATE_NOOP(KONTEXTUS, "Preparing passport photo"),
    "picasapy-batcheffect": QT_TRANSLATE_NOOP(KONTEXTUS, "Applying effects to photos"),
    "picasapy-compact": QT_TRANSLATE_NOOP(KONTEXTUS, "Compacting database"),
    "picasapy-export-movie-clip": QT_TRANSLATE_NOOP(KONTEXTUS, "Exporting movie clip"),
    "picasapy-webexport": QT_TRANSLATE_NOOP(KONTEXTUS, "Creating web album"),
    "picasapy-ftp-publish": QT_TRANSLATE_NOOP(KONTEXTUS, "Publishing web album"),
    "picasapy-collage-panel": QT_TRANSLATE_NOOP(KONTEXTUS, "Rendering collage"),
    "picasapy-save-copy": QT_TRANSLATE_NOOP(KONTEXTUS, "Saving copy"),
    "backup-folders": QT_TRANSLATE_NOOP(KONTEXTUS, "Listing backup folders"),
    "picasapy-collage-preview": QT_TRANSLATE_NOOP(KONTEXTUS, "Rendering collage preview"),
    "picasapy-collage": QT_TRANSLATE_NOOP(KONTEXTUS, "Creating collage"),
    "picasapy-dupes": QT_TRANSLATE_NOOP(KONTEXTUS, "Searching for duplicates"),
    "picasapy-face-scan": QT_TRANSLATE_NOOP(KONTEXTUS, "Scanning faces"),
    "picasapy-foldertree-roots": QT_TRANSLATE_NOOP(KONTEXTUS, "Loading folders"),
    # #6697: induláskor a meglévő index képlistája, a bejárás előtt
    "picasapy-initial-library-feed": QT_TRANSLATE_NOOP(KONTEXTUS, "Loading folders"),
    "picasapy-side-pane-cache": QT_TRANSLATE_NOOP(KONTEXTUS, "Loading folders"),
    "picasapy-sync-exported-folder": QT_TRANSLATE_NOOP(KONTEXTUS, "Syncing changed folders"),
    "picasapy-foldertree": QT_TRANSLATE_NOOP(KONTEXTUS, "Loading subfolders"),
    "picasapy-capture-frame": QT_TRANSLATE_NOOP(KONTEXTUS, "Capturing movie frame"),
    "picasapy-frissesseg-sweep": QT_TRANSLATE_NOOP(KONTEXTUS, "Checking folders for changes"),
    "picasapy-photowrite": QT_TRANSLATE_NOOP(KONTEXTUS, "Saving photo details"),
    "picasapy-photowrite-koteg": QT_TRANSLATE_NOOP(KONTEXTUS, "Saving photo details"),
    "picasapy-xmp-arcok": QT_TRANSLATE_NOOP(KONTEXTUS, "Writing face names to photos"),
    "picasapy-db3-import": QT_TRANSLATE_NOOP(KONTEXTUS, "Importing from the Picasa database"),
    "picasapy-poster": QT_TRANSLATE_NOOP(KONTEXTUS, "Creating poster"),
    "picasapy-save-restore": QT_TRANSLATE_NOOP(KONTEXTUS, "Restoring photos"),
    "picasapy-save": QT_TRANSLATE_NOOP(KONTEXTUS, "Saving changes to photos"),
    "picasapy-startup-maintenance": QT_TRANSLATE_NOOP(KONTEXTUS, "Startup maintenance"),
    "picasapy-tesztuzem-megosztas": QT_TRANSLATE_NOOP(KONTEXTUS, "Preparing the startup log"),
    "picasapy-google-photos-oauth": QT_TRANSLATE_NOOP(KONTEXTUS, "Connecting to Google Photos"),
    "picasapy-google-photos-revoke": QT_TRANSLATE_NOOP(KONTEXTUS, "Disconnecting from Google Photos"),
    "picasapy-google-photos-upload": QT_TRANSLATE_NOOP(KONTEXTUS, "Uploading to Google Photos"),
}


def munka_neve(szalnev: str | None) -> str:
    """A szálnévhez tartozó, a fordítóval kiírt munkanév; ismeretlennél az
    általános szöveg."""
    forras = MUNKANEVEK.get(szalnev or "", ALAP_MUNKANEV)
    return QCoreApplication.translate(KONTEXTUS, forras)


def aktivitas_szoveg(munkak: Sequence[str]) -> str:
    """Az állapotsáv szövege: a LEGFRISSEBB munka neve, és ha több fut, a
    többi darabszáma (`... (+2 more)`). Üres listánál üres szöveg."""
    if not munkak:
        return ""
    legfrissebb = munkak[-1] or QCoreApplication.translate(KONTEXTUS, ALAP_MUNKANEV)
    tovabbi = len(munkak) - 1
    if tovabbi == 0:
        return legfrissebb
    sablon = QCoreApplication.translate(KONTEXTUS, TOBB_MUNKA)
    # A darabszám kerül előbb, a név utoljára: így egy „%2”-t tartalmazó
    # munkanév nem torzítja el a sablont.
    return sablon.replace("%2", str(tovabbi)).replace("%1", legfrissebb)
