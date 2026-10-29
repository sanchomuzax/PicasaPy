"""A mappaleírások és a rejtett mappa jelölőinek mentése."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Slot
from picasapy.scanner import PICASA_INI_NAME
from .photo_ops_controller import _WRITE_ERRORS


class AppControllerFolderDescriptionMixin:
    def _set_folder_hidden_in_ini(self, path: str, hidden: bool) -> None:
        """A rejtési írás cserélhető pontja a korábbi controller API-hoz."""
        from . import controller as controller_module

        controller_module.set_folder_hidden_in_ini(path, hidden)

    def setFolderDescription(self, text: str) -> None:
        """A KIVÁLASZTOTT mappa leírásának mentése (kompatibilitási út —
        a feed-fejlécek a setFolderDescriptionOf-ot hívják)."""
        if not self._current_folder:
            return
        self.setFolderDescriptionOf(self._current_folder, text)

    @Slot(str, str)
    def setFolderDescriptionOf(self, folder_path: str, text: str) -> None:
        """Mappa-leírás mentése — Picasa-kompatibilis: `[Picasa]/description`
        kulcs a mappa `.picasa.ini`-jében (nem indexelt, resync nem kell)."""
        if not folder_path:
            return
        text = text.strip()
        ini_path = Path(folder_path) / PICASA_INI_NAME

        # #137: útvonalanként soros írás — az előzetes ujjlenyomat-
        # ellenőrzésig észlelt Picasa-módosítás újrajátszódik. A check/save
        # közti külső írás teljes kizárását a fájlrendszer nem garantálja.
        def mutate(document):
            if text:
                return document.with_value("Picasa", "description", text)
            return document.with_removed("Picasa", "description")

        # #2506: az írás bukása NEM lehet néma. Írásvédett mappán vagy tele
        # lemezen a kivétel eddig a QML-slotból szökött ki, a feed-fejléc
        # pedig már az ÚJ leírást mutatta — a felhasználó azt hitte,
        # mentett. A projekt meglévő hibacsatornája ez (#459: a
        # `photoOpFailed` a `syncFailed`-en át a `Main.qml` `errorBanner`-be
        # fut be); a gyorstárat és a jelzéseket csak SIKERES írás után
        # frissítjük, hogy a felület se hazudjon (#2497 tanulsága).
        # A controller.update_document patch-pontját a bontás előtt is a
        # controller modul adta; a modulon át hívás megtartja ezt a seamet.
        from . import controller as controller_module

        try:
            controller_module.update_document(ini_path, mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.jelentsdAzIrasiHibat(error)
            return
        self._descriptions[folder_path] = text
        if folder_path == self._current_folder:
            self._folder_description = text
        self._description_revision += 1
        self.descriptionsChanged.emit()
        self.statusChanged.emit()
