"""A Megjelenítési mód menü ne kínáljon jelöletlen halott tételt — #1658.

A tulajdonos kétszer jelentette (#1598, majd RPi5-ön a 0.8.127-tel), hogy a
módok nem hatnak. A mérés szerint igaza volt, de nem úgy: a 11 tételből
akkor 4 működött, 7 nem — és **egyik sem volt jelölve**.

A jelölés RÉGÓTA létezik (`PicasaMenuItem.qml`, #416/#422):

* `placeholder: true` — „a hely megvan, funkció még nincs mögötte";
* `retired: true` — „a szolgáltatás megszűnt, sosem lesz bekötve".

A #1575 mind a 11 tételt sima `MenuItem`-ként vezette be, jelölés nélkül.
Nem az eszköz hiányzott — nem használtuk. Ez az őr azért van, hogy a
hibaosztály (#1443, #1515, #1528, #1550, #1615, #1633) ne jöhessen vissza
hetedszer: **ha a menübe bekerül egy mód megvalósítás nélkül és jelölés
nélkül, ez a teszt bukik.**
"""

from __future__ import annotations

from picasapy.render.display_modes import PIXEL_AFFECTING_MODES

#: A menütétel `objectName`-je → a mögötte álló módazonosító.
#: KIÍRT lista: ha új tétel kerül a menübe, ide is fel kell venni, különben
#: a lefedettségi teszt bukik — ez szándékos.
TETELEK: dict[str, str] = {
    "menuViewDisplayModeAuto": "auto",
    "menuViewDisplayModeNormal": "normal",
    "menuViewDisplayMode16Bit": "dither16",
    "menuViewDisplayModeRemoteDesktop": "rdesk",
    "menuViewDisplayModeLcd": "lcd",
    "menuViewDisplayModeProjector": "projector",
    "menuViewDisplayModeOverflow": "overflow",
    "menuViewDisplayModeMacGamma": "mac",
    "menuViewDisplayModeLinearGamma": "linear",
    "menuViewDisplayModeSepia": "sepia",
    "menuViewDisplayModeBlackWhite": "bw",
}

#: SZÁNDÉKOS üresjárat: a 24 bites a rádió alapértelmezettje (nincs
#: átalakítás), az Automatikus Linuxon no-op (16 bites képernyőn szemcsézne).
#: Ezek MŰKÖDNEK — nem halott tételek, tehát nem kapnak jelölést.
SZANDEKOS_NOOP = frozenset({"auto", "normal"})

#: Amit sosem kötünk be — a `docs/specs/picasa-megjelenitesi-modok.md`
#: 7. táblázata mindkettőt „hatókörön kívül"-nek mondja.
# #1730: a `mac` KIKERÜLT — a #1658 „nincs referencia-mérés" indoka
# megszűnt (a #1580 képpont-mérése megvan), és a mód azóta él.
NYUGDIJAZOTT = frozenset({"rdesk"})

#: Megvalósítható, de ma értelmetlen (16 bites képernyő nincs).
HELYFOGLALO = frozenset({"dither16"})


def _tetel(window, nev):
    elem = window.findChild(object, nev)
    assert elem is not None, f"nincs ilyen menütétel: {nev}"
    return elem


class TestABesorolasTeljes:
    def test_minden_mod_pontosan_egy_csoportba_tartozik(self):
        """A négy csoport lefedi a 11 módot, és nem fedik át egymást."""
        besorolt = PIXEL_AFFECTING_MODES | SZANDEKOS_NOOP | NYUGDIJAZOTT | HELYFOGLALO
        assert set(TETELEK.values()) == besorolt
        parok = [
            (PIXEL_AFFECTING_MODES, SZANDEKOS_NOOP),
            (PIXEL_AFFECTING_MODES, NYUGDIJAZOTT),
            (PIXEL_AFFECTING_MODES, HELYFOGLALO),
            (SZANDEKOS_NOOP, NYUGDIJAZOTT),
            (SZANDEKOS_NOOP, HELYFOGLALO),
            (NYUGDIJAZOTT, HELYFOGLALO),
        ]
        for a, b in parok:
            assert not (a & b), f"átfedő csoportok: {a & b}"


class TestAMenuJelolesei:
    """Ez a jegy magja: a felületen látszódjon, mi működik és mi nem."""

    def test_a_mukodo_modok_kattinthatok(self, qml_app_module):
        window, _ctl, _e = qml_app_module
        for nev, mod in TETELEK.items():
            if mod not in PIXEL_AFFECTING_MODES and mod not in SZANDEKOS_NOOP:
                continue
            elem = _tetel(window, nev)
            assert elem.property("enabled") is True, (
                f"{nev} ({mod}) működik, mégis le van tiltva"
            )

    def test_a_nyugdijazott_modok_jelolve_es_kattinthatatlanok(self, qml_app_module):
        window, _ctl, _e = qml_app_module
        for nev, mod in TETELEK.items():
            if mod not in NYUGDIJAZOTT:
                continue
            elem = _tetel(window, nev)
            assert elem.property("retired") is True, f"{nev} nincs nyugdíjazva"
            assert elem.property("enabled") is False, f"{nev} kattintható maradt"

    def test_a_helyfoglalo_modok_jelolve_es_kattinthatatlanok(self, qml_app_module):
        window, _ctl, _e = qml_app_module
        for nev, mod in TETELEK.items():
            if mod not in HELYFOGLALO:
                continue
            elem = _tetel(window, nev)
            assert elem.property("placeholder") is True, f"{nev} nincs helyfoglalónak jelölve"
            assert elem.property("enabled") is False, f"{nev} kattintható maradt"

    def test_egyetlen_meg_nem_valositott_mod_sem_kattinthato(self, qml_app_module):
        """Az őr FOGA: ha bárki bevezet egy módot megvalósítás nélkül és
        jelölés nélkül, itt bukik — nem a felhasználó gépén."""
        window, _ctl, _e = qml_app_module
        vetkesek = []
        for nev, mod in TETELEK.items():
            if mod in PIXEL_AFFECTING_MODES or mod in SZANDEKOS_NOOP:
                continue
            elem = _tetel(window, nev)
            if elem.property("enabled") is not False:
                vetkesek.append(f"{nev} ({mod})")
        assert not vetkesek, (
            "megvalósítás nélküli, mégis kattintható megjelenítési mód: "
            + ", ".join(vetkesek)
        )
