"""#1029: a bal hasáb **Projektek** gyűjteménye — controller-szelet.

A `PeopleMixin` (#26) mintáját követő mixin: az `AppController` örökli, az
állapotát a `_reload()` frissíti (#1601 óta az Emberek gyűjteménnyel
KÖZÖS ini-söprésből, ld. `side_pane_controller.py`), így a háttér-
szinkron után is friss marad — a frissen mentett kollázs mappája a
következő szinkronnal magától megjelenik a hasábon.

A gyűjtemény tartalmának forrása a `.picasa.ini` `[Picasa]` `P2category`
kulcsa (`picasapy.index.project_folders`); a kattintás NEM kap saját utat:
a projekt-mappa MAPPA, tehát a hasáb meglévő `folderChosen` jelzésén át a
`selectFolder` nyitja meg — ahogy az „Exportált képek" sorai is.
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal

from picasapy.index.project_folders import project_folders


class ProjectFoldersMixin:
    """A Projektek gyűjtemény mappái a bal hasábnak."""

    projectFoldersChanged = Signal()

    def _init_project_folders(self) -> None:
        """A konstruktorból hívandó kezdeti állapot (`_init_people` mintája)."""
        self._project_folders: tuple = ()

    def _load_project_folders(self, conn) -> None:
        """CSAK a Projektek-lista frissítése, saját ini-söpréssel.

        ⚠️ #1601: a `_reload()` már NEM ezt hívja, hanem a
        `SidePaneMixin._load_side_pane`-t — az az Emberek gyűjteménnyel
        KÖZÖS, egyetlen `.picasa.ini`-söprésből állítja elő mindkettőt."""
        self._project_folders = project_folders(conn)
        self.projectFoldersChanged.emit()

    @Property(list, notify=projectFoldersChanged)
    def projectFolders(self):  # noqa: N802 — QML-property-stílus
        """A hasábnak: `[{path, name, count}, ...]` — LISTA, nem tuple
        (#232, a QML-ben a tuple nem tömb), az `albums` property mintájára.

        Az „Exportált képek" (#457) sorai ettől FÜGGETLENEK: azok a
        beállításokban élnek, ez itt a könyvtárban talált projekt-mappa."""
        return [
            {
                "path": folder.path,
                "name": folder.name,
                "count": folder.photo_count,
            }
            for folder in getattr(self, "_project_folders", ())
        ]
