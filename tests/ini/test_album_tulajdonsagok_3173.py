"""#3173 — az album tulajdonságainak írása a `.picasa.ini`-be.

## A mezőkészlet MÉRVE, nem találgatva

A párbeszéd elrendezése a szállított `album.fen`-ben áll
(`research/copy_Picasa_3_7/Picasa3/runtime/album.fen`), a hivatalos magyar
feliratok a `referencia/i18n-hu/album.xml`-ben:

| mező | `album.fen` | magyar felirat |
|---|---|---|
| név | `<edit name="name" filter="filename"/>` | **Név:** |
| dátum | `<date name="date"/>` + „Automatic date" | **Dátum:** |
| zene | `<check … name="usemusic">` + `<browse name="music">` | **Zene:** |
| hely | `<edit name="location"/>` | **Felvétel készítésének helye (opcionális):** |
| leírás | `<edit height="3li" name="caption"/>` | **Leírás (opcionális):** |

⚠️ A **zene** ehhez a körhöz nem tartozik: diavetítés-/mozgófilm-zene nálunk
egyáltalán nincs, tehát a mező nem is menthető sehova. Az `album.fen` négy
másik mezője viszont pontosan az, amit az `ini/albums.py` `Album` rekordja már
modellez (`name`, `date`, `location`, `description`) — ez a lap ezt a négyet
méri.

⛔ A `caption` az `album.fen`-ben a mező NEVE; a `.picasa.ini`-ben a kulcs
`description` (az `albums_of` ezt olvassa) — a kettő nem keverhető össze.
"""

from __future__ import annotations

from picasapy.ini.albums import albums_of, ensure_album, with_album_fields
from picasapy.ini.document import parse_document


def _dok(szoveg: str = ""):
    return parse_document(szoveg)


class TestAzIras:
    def test_a_negy_mezo_kiirasa(self) -> None:
        dok = ensure_album(_dok(), "abc123", "Régi név")
        dok = with_album_fields(
            dok,
            "abc123",
            name="Nyaralás 2026",
            date="2026-07-14",
            location="Balaton",
            description="A nagy nyári kör",
        )
        album = albums_of(dok)[0]
        assert album.name == "Nyaralás 2026"
        assert album.date == "2026-07-14"
        assert album.location == "Balaton"
        assert album.description == "A nagy nyári kör"

    def test_a_nem_letezo_albumot_nem_hozza_letre(self) -> None:
        """⛔ Az írás NEM definiál új albumot: a tulajdonság-szerkesztés
        meglévő albumra szól, és egy elírt token nem hozhat létre szellem-
        albumot minden mappában."""
        dok = with_album_fields(_dok(), "nincs-ilyen", name="X")
        assert albums_of(dok) == ()

    def test_az_ures_ertek_TORLI_a_kulcsot(self) -> None:
        """Az opcionális mezők kiürítése törölje a kulcsot — üres kulcsot a
        Picasa sem hagy maga után (ld. `without_album`)."""
        dok = ensure_album(_dok(), "abc123", "Név")
        dok = with_album_fields(dok, "abc123", location="Balaton")
        assert albums_of(dok)[0].location == "Balaton"
        dok = with_album_fields(dok, "abc123", location="")
        assert albums_of(dok)[0].location is None
        assert "location=" not in dok.serialize()

    def test_a_None_MEGHAGYJA_a_meglevo_erteket(self) -> None:
        """A `None` azt jelenti: „ezt a mezőt nem szerkesztettük"."""
        dok = ensure_album(_dok(), "abc123", "Név")
        dok = with_album_fields(dok, "abc123", location="Balaton")
        dok = with_album_fields(dok, "abc123", name="Új név")
        album = albums_of(dok)[0]
        assert album.name == "Új név"
        assert album.location == "Balaton"

    def test_az_ures_NEV_nem_torolheto(self) -> None:
        """⛔ A név nem opcionális: névtelen album a listában azonosíthatatlan
        volna. Üres névre a meglévő név MARAD."""
        dok = ensure_album(_dok(), "abc123", "Név")
        dok = with_album_fields(dok, "abc123", name="   ")
        assert albums_of(dok)[0].name == "Név"

    def test_a_tagsagokat_nem_bantja(self) -> None:
        dok = parse_document(
            "[.album:abc123]\ntoken=abc123\nname=Név\n\n[kep.jpg]\nalbums=abc123\n"
        )
        dok = with_album_fields(dok, "abc123", name="Másik")
        szoveg = dok.serialize()
        assert "albums=abc123" in szoveg
        assert "name=Másik" in szoveg

    def test_a_round_trip_megmarad(self) -> None:
        """A jegy őr-pontja: átnevezés után a név round-trippel az ini-n át."""
        dok = ensure_album(_dok(), "abc123", "Régi")
        dok = with_album_fields(dok, "abc123", name="Átnevezett")
        ujra = parse_document(dok.serialize())
        assert albums_of(ujra)[0].name == "Átnevezett"
