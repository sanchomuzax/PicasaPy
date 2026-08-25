"""A bal hasáb fa-mappanézetének bekötése a teszt-fixture-ökbe (#1454).

Az `application.py` a `FolderHierarchyController`-t nem csak regisztrálja,
hanem **fel is tölti** az index `folders` táblájából, és a `syncFinished`
jelzésre újratölti. Enélkül a vezérlő üres, a fa egyetlen sort mutat — és a
rá épülő tesztek némán semmit sem mérnének.

Azért KÖZÖS helyen él, mert két `qml_app` fixture van (a `tests/app/` és a
`tests/app/qml_functional/` alatt), és a #1454-ben a bekötés először csak az
egyikbe került be. Az ilyen féloldalas tükrözés a projektben már megfogott
minket: a szülő fixture-re épülő teszt zölden mért volna egy halott menüt,
mert nála a `folderHierarchyController` `undefined` maradt volna.
"""

from __future__ import annotations

import logging
import sqlite3


def wire_folder_hierarchy(engine, controller, db_path):
    """A vezérlő létrehozása, feltöltése és regisztrálása a QML-kontextusba.

    A visszatérési érték a vezérlő — a hívó fixture tartsa életben, amíg a
    motor él.
    """
    from picasapy.app.folder_hierarchy_controller import FolderHierarchyController
    from picasapy.app.models import sorted_folder_rows
    from picasapy.index import open_index

    folder_hierarchy_controller = FolderHierarchyController()

    def _reload() -> None:
        # az `application.py._reload_folder_hierarchy` tükre — a sérült
        # index ott sem dönti el a `syncFinished` kiszolgálását, csak
        # naplózik, és a fa a korábbi tartalmán marad
        try:
            with open_index(db_path) as conn:
                folder_hierarchy_controller.setFolders(
                    [
                        {"path": path, "count": count}
                        for _name, path, count, *_rest in sorted_folder_rows(conn)
                    ]
                )
        except sqlite3.DatabaseError:
            logging.getLogger(__name__).exception(
                "a fa-mappanézet frissítése hibára futott"
            )

    _reload()
    controller.syncFinished.connect(_reload)
    engine.rootContext().setContextProperty(
        "folderHierarchyController", folder_hierarchy_controller
    )
    return folder_hierarchy_controller
