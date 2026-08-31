"""#416: a még be nem kötött (helyfoglaló) menüpontok halványabb feliratot
és egy kicsi, világosszürke pontot kapnak a sor jobb szélén — a működő
menüpontoknál semmi nem változik.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


class TestPlaceholderMenuItemek:
    """A `PicasaMenuItem`-mel jelölt helyfoglaló tételek."""

    def test_placeholder_pont_lathato(self, qml_app):
        window, _controller, _engine = qml_app
        # ⚠️ #1616: a `menuFileNewAlbum` KIKERÜLT ebből a listából — az
        # „Új album…" azóta ÉLŐ menüpont (`Ctrl+N`-nel együtt). Ez a teszt
        # a JELÖLÉST méri, nem konkrét tételeket; ha egy példa bekötést kap,
        # itt kell másikat választani, nem a jelölést visszatenni rá.
        # ⚠️ #1526: a `menuEditCut` KIKERÜLT — a Kivágás azóta ÉLŐ
        # (a képek fájljait teszi a vágólapra, Ctrl+X-szel együtt).
        # Ugyanaz a menet, mint a #1616-nál: példát cserélünk, nem
        # jelölést teszünk vissza egy működő tételre.
        for name in (
            "menuViewDisplayMode16Bit",
            "menuViewThumbnailsOnly",
        ):
            item = window.findChild(QObject, name)
            assert item is not None, name
            assert item.property("placeholder") is True
            assert item.property("enabled") is False
            # #331-tanulság (MEMORY.md): a `visible` ZÁRT menünél az
            # ÖRÖKÖLT láthatóságot tükrözi (mindig False) — a menüt nem
            # nyitjuk fel, ezért csak a pont LÉTÉT és a rákötött feltételt
            # ellenőrizzük, nem az aktuális képernyő-láthatóságát.
            dot = item.findChild(QObject, "placeholderDot")
            assert dot is not None, name

    def test_placeholder_felirat_halvanyabb(self, qml_app):
        window, _controller, _engine = qml_app
        # #1616: a korábbi példa (`menuFileNewAlbum`) élővé vált, ezért
        # egy MA IS helyfoglaló tételen mérünk.
        # #1526: a következő példa (`menuEditCut`) is élővé vált — ez a
        # teszt a JELÖLÉST méri, nem konkrét tételeket.
        item = window.findChild(QObject, "menuViewDisplayMode16Bit")
        content = item.property("contentItem")
        assert content is not None
        # a felirat színe a Theme.textGray tokent használja (alap/világos
        # témában "#7a776f"), NEM a rendes (Theme.ink, "#1c1b19") szövegtinta
        assert content.property("color").name() == "#7a776f"


class TestMukodoMenuItemekValtozatlanok:
    """A már bekötött menüpontoknál TILOS pontnak/placeholder-jelzőnek
    megjelennie."""

    def test_mukodo_tetelnek_nincs_placeholder_jelzese(self, qml_app):
        window, _controller, _engine = qml_app
        for name in (
            "menuFileRename",
            "menuFileExport",
            "menuFileLocate",
            "menuEditCopyEffects",
            "menuViewDarkTheme",
        ):
            item = window.findChild(QObject, name)
            assert item is not None, name
            # sima QtQuick.Controls MenuItem: nincs ilyen tulajdonsága
            assert not item.property("placeholder")
            dot = item.findChild(QObject, "placeholderDot")
            assert dot is None, name
