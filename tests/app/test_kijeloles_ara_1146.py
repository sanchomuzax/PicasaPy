"""A kijelölés-változás ára MAPPÁNKÉNT, ne soronként (#1146).

## A lelet

Két QML-kötés a kijelölés TELJES sorlistájával hív Python-slotot, és
mindkettő **soronként** nyúlt a lemezhez:

| slot | soronkénti munkája |
|---|---|
| `hasSavedBackup` | `Path.is_dir()` + `Path.glob()` a `.picasaoriginals`-on |
| `peopleOfRows` | `load_document()` — egy `.picasa.ini` beolvasása |

2 002 soros kijelölésnél ez 10 010 `stat()` + 6 006 ini-beolvasás **egyetlen
billentyűleütésre**.

⚠️ A tulajdonos gyűjteménye **hálózati megosztáson** van, ahol minden
`stat()` és minden ini-olvasás hálózati kör — ott ez nem lassulás, hanem
fagyás.

A kép ugyanabban a mappában van; a mappa `.picasaoriginals`-át és
`.picasa.ini`-jét **egyszer** kell megnézni, nem képenként.
"""

from __future__ import annotations

from pathlib import Path



def test_hasSavedBackup_mappankent_nez_a_lemezre(tmp_path, monkeypatch):
    """100 kép EGY mappában → EGY könyvtár-vizsgálat, nem száz."""
    from picasapy.app import save_controller

    hivasok: list[str] = []
    eredeti_glob = Path.glob

    def figyelo(self, minta):
        hivasok.append(str(self))
        return eredeti_glob(self, minta)

    monkeypatch.setattr(Path, "glob", figyelo)

    mappa = tmp_path / "kepek"
    (mappa / ".picasaoriginals").mkdir(parents=True)

    class _Rec:
        def __init__(self, nev):
            self.folder_path = str(mappa)
            self.name = nev

    class _Host(save_controller.SaveMixin):
        def _selected_records(self, rows):
            return [_Rec(f"k{i}.jpg") for i in rows]

    _Host().hasSavedBackup(list(range(100)))

    assert len(hivasok) <= 1, (
        f"{len(hivasok)} könyvtár-listázás 100 képre EGY mappában — "
        "hálózati megosztáson ez fagyás"
    )


def test_peopleOfRows_mappankent_olvas_init(tmp_path, monkeypatch):
    """100 kép EGY mappában → EGY ini-beolvasás, nem száz."""
    from picasapy.app import people_controller

    olvasasok: list[str] = []
    eredeti = people_controller.load_document

    def figyelo(ut, *a, **k):
        olvasasok.append(str(ut))
        return eredeti(ut, *a, **k)

    monkeypatch.setattr(people_controller, "load_document", figyelo)

    mappa = tmp_path / "kepek"
    mappa.mkdir()
    (mappa / ".picasa.ini").write_text("[Contacts2]\n", encoding="utf-8")

    class _Photo:
        def __init__(self, nev):
            self.folder_path = str(mappa)
            self.name = nev

    class _Host(people_controller.PeopleMixin):
        def _rows_to_photos(self, rows):
            return [_Photo(f"k{i}.jpg") for i in rows]

    _Host().peopleOfRows(list(range(100)))

    assert len(olvasasok) <= 1, (
        f"{len(olvasasok)} ini-beolvasás 100 képre EGY mappában"
    )
