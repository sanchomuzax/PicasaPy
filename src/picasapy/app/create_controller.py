"""Létrehozás menü: kollázs és mozgófilm (#29) — az AppController szelete.

Mindkét művelet háttérszálon fut (nagy képeknél, NAS-on percekig tarthat),
és ugyanazt a jelzés-mintát követi, mint az export (#16/#136):

- `...Finished(útvonal, felhasznált, kihagyott)` — sikeres futás,
- `...Failed(üzenet)` — emberi nyelvű hibaüzenet (a hívó dialógusa mutatja),
- a mozgófilm közben `movieProgress(kész, összes)` képenként.

A dialógusok a célfájlt `file://` URL-ként adják át (a QML FileDialog
alakja) — a `to_local_path` fordítja vissza helyi útvonallá.

## A kollázs-piszkozat (#960)

A Picasa szerkesztés közben külön szálon írta az **`autosave.cxf`**
piszkozatot, és a következő indításkor felajánlotta a visszaállítást (spec
1.5). Nálunk a piszkozat ott keletkezik, ahol a vászon geometriája
egyáltalán létezik: az élő előnézet és a mentés `CollageReport.nodes`-
csomópontjaiból (#942). Két szabály tartja értelmesnek:

1. **Sosem találunk ki geometriát.** Ha a rajzoló nem ad csomópontot,
   piszkozat sem születik — a formátum épp azt ígéri, hogy pontosan
   visszaáll.

   ⚠️ A Többszörös exponálás **nem** ilyen eset (#1248). Geometriát tényleg
   nem helyez el, de a `.cxf`-nek tudnia kell, MELYIK képekből készült; az
   eredeti is képenként egy, teljes lapos csomópontot ír (mérve:
   `referencia/kollazs-golden/AI7.cxf`). Amíg nálunk üres maradt, az
   újraszerkesztés fekete lapot adott, a mentés pedig azt jelentette, hogy
   „az összes képet eltávolították".
2. **A piszkozat hibája sosem viheti el a kollázst.** Írása és eldobása
   naplózott, de nyelt hiba: a felhasználó munkája fontosabb, mint a
   biztonsági másolata.

Sikeres mentés után a piszkozat betöltötte a szerepét, ezért eldobjuk.
"""

from __future__ import annotations

import logging
import math  # noqa: F401 - régi importút
import sqlite3  # noqa: F401 - régi importút
from pathlib import Path
from xml.etree import ElementTree  # noqa: F401 - régi importút

from PySide6.QtCore import Property, QUrl, Signal, Slot  # noqa: F401 - régi importút
from PySide6.QtGui import QImageReader  # noqa: F401 - régi importút

from picasapy.collage import write_collage  # noqa: F401 - régi importút
from picasapy.collage.autosave import (
    discard_autosave,  # noqa: F401 - régi importút
    has_recoverable_draft,  # noqa: F401 - régi importút
    recover_orphan_draft,  # noqa: F401 - régi importút
    write_autosave,  # noqa: F401 - régi importút
)
from picasapy.collage.draft import project_from_nodes  # noqa: F401 - régi importút
from picasapy.collage.picasa_render import PicasaCollageSettings, make_picasa_collage  # noqa: F401 - régi importút
from picasapy.app.collage_preview import CollagePreviewProvider  # noqa: F401 - régi importút
from picasapy.app.movie_preview import MovieTransitionPreviewProvider  # noqa: F401 - régi importút
from picasapy.collage.themes import BORDER_THEMES, COLLAGE_THEMES, NOBORDER  # noqa: F401 - régi importút
from picasapy.index import album_photos, open_index
from picasapy.ini import load_or_empty, read_folder_music
from picasapy.movie import MovieSettings, export_movie  # noqa: F401 - régi importút
from picasapy.movie.mxf import (
    MxfAtmenet,  # noqa: F401 - régi importút
    MxfForras,  # noqa: F401 - régi importút
    MxfSzovegParam,  # noqa: F401 - régi importút
    MxfProjekt,  # noqa: F401 - régi importút
    projekt_utvonal,  # noqa: F401 - régi importút
    read_mxf,  # noqa: F401 - régi importút
    write_mxf,
)
from picasapy.scanner import PICASA_INI_NAME

from . import collage_output, collage_prefs  # noqa: F401 - régi importút
from .appearance_controller import coerce_ui_preference_flag  # noqa: F401 - régi importút
from .formatting import to_local_path
from .poster_controller import PosterMixin
from .create_movie_mixin import _CreateMovieMixin
from .create_collage_mixin import _CreateCollageMixin

logger = logging.getLogger(__name__)

# A kollázs alapértelmezett vászonmérete — nyomtatható, de nem irreális.
_COLLAGE_SIZE = (1600, 1200)
# Egy kollázsba/filmbe ennél több képet nincs értelme tenni: a cellák
# olvashatatlanul kicsik lennének, a videó pedig órákig tartana.
_MAX_ITEMS = 200
# A képek közti áttűnés felső korlátja (mp) — ennél hosszabb áttűnés
# elmossa a diavetítés ritmusát.
_MAX_TRANSITION_S = 0.5
_MOVIE_SIZES = (
    (320, 240), (640, 480), (800, 600), (1024, 768), (1600, 1200),
    (1280, 720), (1920, 1080),
)
_MOVIE_TRANSITIONS = (
    "cut", "dissolve", "dissolveblack", "dissolvewhite", "wipeleft",
    "wiperight", "wipeup", "wipedown", "diagwipeul", "diagwipeur",
    "diagwipedl", "diagwipedr", "pushleft", "pushright", "pushtop",
    "pushdown", "circlein", "circleout", "kenburns", "kenburnsaoi",
    "timelapse", "rect",
)
_MOVIE_SLIDE_DURATION_KEY = "slideduration"
_MOVIE_TRANSITION_KEY = "makemovietransition"
_MOVIE_SLIDE_DURATION_DEFAULT = 4.0
_MOVIE_SLIDE_DURATION_MIN = 1.0
_MOVIE_SLIDE_DURATION_MAX = 300.0
_MOVIE_PREFERENCES = {
    "captions": ("CMakeMoviePanel::showcaptions", False),
    "cropfit": ("CMakeMoviePanel::cropfit", False),
    "removeLowResFaces": ("makemoviepanel/remove_low_res_faces", False),
    # #5288: a valódi méret (1:1) kapcsoló, a spec szerint alapból bekapcsolva.
    "actualSize": ("makemovie1to1", True),
}
# #920: az élő előnézet mérete. Kicsi, mert a Képkupac pakolója
# időkorlátos keresést futtat — teljes felbontáson a felület beragadna.
_PREVIEW_SIZE = (640, 480)


def film_zene_mappabol(forrasok) -> Path | None:
    """A közös forrásmappa engedélyezett zenéje filmkészítéshez.

    Csak egyetlen fizikai mappából származó képkészlethez rendelünk mappazenét;
    több mappánál a film panel kézi hangsáv-választása marad érvényes.
    """
    mappak = []
    for forras in forrasok or ():
        helyi = to_local_path(str(forras))
        if not helyi:
            return None
        mappak.append(Path(helyi).expanduser().parent)
    if not mappak:
        return None

    try:
        kozos_mappa = mappak[0].resolve()
        if any(mappa.resolve() != kozos_mappa for mappa in mappak[1:]):
            return None
        enabled, music_file = read_folder_music(
            load_or_empty(kozos_mappa / PICASA_INI_NAME)
        )
        if not enabled or not music_file:
            return None
        zene = Path(music_file).expanduser()
        if not zene.is_absolute():
            zene = kozos_mappa / zene
        zene = zene.resolve()
        return zene if zene.is_file() else None
    except OSError:
        return None


def _movie_call(name: str, *args):
    """A filmrész betöltése csak az első meghíváskor."""
    from .create_movie_controller import MovieCreationOperations

    return getattr(MovieCreationOperations, name)(*args)


def _collage_call(name: str, *args):
    """A kollázsrész betöltése csak az első meghíváskor."""
    from .create_collage_operations import CollageCreationOperations

    return getattr(CollageCreationOperations, name)(*args)


def _write_movie_project(video_path: str | Path, project) -> None:
    """A filmprojekt régi modulbeli írókapuja és monkeypatch-célpontja."""
    write_mxf(Path(video_path).with_suffix(".mxf"), project)


class CreateMixin(_CreateMovieMixin, _CreateCollageMixin, PosterMixin):
    """Poszter-, kollázs- és mozgófilm-készítés a kijelölésből."""

    @Slot(list, result=str)
    def filmMusicForSources(self, sources) -> str:  # noqa: N802
        """Az album vagy az egy mappából vett képek alapértelmezett zenéje."""
        mode, token = getattr(self, "_view_mode", ("", ""))
        if mode == "album" and token and self._sources_belong_to_album(
            sources, token
        ):
            album_music = self.albumMusicFile(token)
            if album_music:
                return album_music
        zene = film_zene_mappabol(sources)
        return str(zene) if zene is not None else ""

    def _sources_belong_to_album(self, sources, token: str) -> bool:
        """Csak a megnyitott album képeire adjon albumzene-alapértéket."""
        helyi_forrasok = []
        for source in sources or ():
            local_path = to_local_path(str(source))
            if not local_path:
                return False
            try:
                helyi_forrasok.append(Path(local_path).expanduser().resolve())
            except (OSError, RuntimeError, ValueError):
                return False
        if not helyi_forrasok:
            return False
        try:
            with open_index(self._db_path) as connection:
                album_utak = {
                    (Path(photo.folder_path) / photo.name).resolve()
                    for photo in album_photos(connection, token)
                }
        except (OSError, sqlite3.Error, RuntimeError, ValueError):
            return False
        return bool(album_utak) and all(path in album_utak for path in helyi_forrasok)

    _elozo_film_cel: Path | None = None
