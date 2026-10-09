"""#416: a még be nem kötött (helyfoglaló) menüpontok halványabb feliratot
és egy kicsi, világosszürke pontot kapnak a sor jobb szélén — a működő
menüpontoknál semmi nem változik.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _placeholder_items(window):
    return [
        item
        for item in window.findChildren(QObject)
        if bool(item.property("placeholder"))
    ]


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
        placeholders = _placeholder_items(window)
        assert placeholders, "eltűntek a helyfoglalónak jelölt menütételek"
        for item in placeholders:
            assert item.property("placeholder") is True
            assert item.property("enabled") is False
            # #331-tanulság (MEMORY.md): a `visible` ZÁRT menünél az
            # ÖRÖKÖLT láthatóságot tükrözi (mindig False) — a menüt nem
            # nyitjuk fel, ezért csak a pont LÉTÉT és a rákötött feltételt
            # ellenőrizzük, nem az aktuális képernyő-láthatóságát.
            dot = item.findChild(QObject, "placeholderDot")
            assert dot is not None, item.objectName() or item.property("text")

    def test_placeholder_felirat_halvanyabb(self, qml_app):
        window, _controller, _engine = qml_app
        placeholders = _placeholder_items(window)
        assert placeholders, "eltűntek a helyfoglalónak jelölt menütételek"
        item = placeholders[0]
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
        ):
            item = window.findChild(QObject, name)
            assert item is not None, name
            # sima QtQuick.Controls MenuItem: nincs ilyen tulajdonsága
            assert not item.property("placeholder")
            dot = item.findChild(QObject, "placeholderDot")
            assert dot is None, name

    def test_sajat_mukodo_tetelen_nincs_lathato_pont(self, qml_app):
        """#4638: a Sötét téma SAJÁT tétel (`PicasaMenuItem`, `sajat`), így
        a sablonja a pontot is tartalmazza — de a működő tételen az nem
        látszik. Ez a látható állapotot őrzi, nem a belső fa alakját."""
        window, _controller, _engine = qml_app
        item = window.findChild(QObject, "menuViewDarkTheme")
        assert item is not None
        assert item.property("placeholder") is False
        dot = item.findChild(QObject, "placeholderDot")
        assert dot is None or dot.property("visible") is False
