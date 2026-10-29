"""#6163: a kollázs-renderelő forrásfájljai 800 sor alatt maradnak."""

from pathlib import Path


_GYOKER = Path(__file__).resolve().parents[2]
_RENDER = _GYOKER / "src" / "picasapy" / "collage"
_FAJLOK = ("picasa_render.py", "picasa_render_layouts.py")
_MAX_SOR = 799


def test_minden_render_modul_800_sor_alatt_marad() -> None:
    hianyzo = [nev for nev in _FAJLOK if not (_RENDER / nev).is_file()]
    sorok = {
        nev: len((_RENDER / nev).read_text(encoding="utf-8").splitlines())
        for nev in _FAJLOK
        if (_RENDER / nev).is_file()
    }
    tul_hosszu = {nev: db for nev, db in sorok.items() if db > _MAX_SOR}

    assert not tul_hosszu, f"A renderelő fájlok 800 soros plafonja sérült: {tul_hosszu}"
    assert not hianyzo, f"Hiányzó renderelő modulok: {hianyzo}"


# rontás-kontroll: picasa_render.py 1085 sor → 1 failed (átalakítás előtti állapot)
