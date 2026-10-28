"""A diavetítés fennmaradó felelősségei önálló QML-részekben élnek (#6102)."""

from pathlib import Path


_QML = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy"
_RESZEK = {
    "SlideshowMusic": "SlideshowMusic.qml",
    "SlideshowModelSync": "SlideshowModelSync.qml",
}


def test_a_zene_es_modellkovetes_kulon_belso_komponens():
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    hianyzo = [
        f"internal {tipus} {fajl}"
        for tipus, fajl in _RESZEK.items()
        if f"internal {tipus} {fajl}" not in qmldir
        or not (_QML / fajl).is_file()
    ]

    assert not hianyzo, f"hiányzó diavetítési komponens(ek): {hianyzo}"


def test_az_uj_diavetitesi_reszek_800_sor_alatt_maradnak():
    hosszak = {
        fajl: len((_QML / fajl).read_text(encoding="utf-8").splitlines())
        for fajl in _RESZEK.values()
        if (_QML / fajl).is_file()
    }

    assert set(hosszak) == set(_RESZEK.values()) and all(
        sorok <= 800 for sorok in hosszak.values()
    ), f"hiányzó vagy túl nagy diavetítési rész: {hosszak}"


def test_a_belso_reszek_neve_nem_parbeszedablakot_jelol():
    assert all("Dialog" not in nev for nev in _RESZEK)
