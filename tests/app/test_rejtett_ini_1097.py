"""A rejtett `.picasa.ini` felülírása nem buktathatja el a mentést (#1097).

## A tulajdonos jelentése (v0.8.23, Windows)

```
A kollázs nem készült el.
[Errno 13] Permission denied: '…\\Képek\\Picasa\\Kollázsok\\.picasa.ini'
```

## A két hiba

1. **A megnyitás módja.** A `write_text()` windowson `CREATE_ALWAYS`-szel
   nyit, ami egy létező, **REJTETT** fájlon `ERROR_ACCESS_DENIED`-del bukik.
   A #1088 óta a VALÓDI Picasa-mappába írunk, ahol a `.picasa.ini`-t a
   Picasa hozta létre — rejtettként. Létező fájlt `r+`-szal kell nyitni
   (`OPEN_EXISTING`), akkor a rejtett jelző nem számít.

   ⚠️ Ideiglenes fájl + átnevezés itt NEM jó: az új fájl nem rejtett, tehát
   a `.picasa.ini` a felhasználó Intézőjében láthatóvá válna.

2. **A hiba SÚLYA.** Az ini a mappa MEGJELÖLÉSE, és a JPEG meg a `.cxf`
   ekkor MÁR a lemezen van. Ha csak a megjelölés bukik, az figyelmeztetés —
   „a kollázs nem készült el" hazugság, és a felhasználó azt hiszi,
   elveszett a munkája.
"""

from __future__ import annotations

import builtins


from picasapy.app import collage_output


def test_letezo_ini_t_NEM_csonkolva_nyitunk(tmp_path, monkeypatch):
    """Létező ini → `r+`, nem `w`. Ez a windowsos bukás gyökere.

    Linuxon a rejtett jelző nem létezik, tehát a valódi hibát itt nem
    lehet előidézni — a megnyitás MÓDJÁT viszont igen, és a hiba pontosan
    az volt."""
    mappa = tmp_path / "Kollázsok"
    mappa.mkdir()
    (mappa / ".picasa.ini").write_text("[Picasa]\n", encoding="utf-8")

    modok: list[str] = []
    eredeti = builtins.open

    def figyelo(fajl, mod="r", *args, **kwargs):
        if str(fajl).endswith(".picasa.ini"):
            modok.append(mod)
        return eredeti(fajl, mod, *args, **kwargs)

    # #1375: a modul SAJÁT fogantyúját cseréljük, nem a `builtins.open`-t —
    # az utóbbi a folyamat összes fájlmegnyitását ide terelné, amíg a teszt
    # fut. A csere így csak azt látja, amit EZ a modul nyit; ha valaki
    # visszaesne a `write_text()`-re (a #1097 gyökere), a `_open` meg sem
    # hívódna, és az alábbi „meg sem nyitottuk" állítás bukna el.
    monkeypatch.setattr(collage_output, "_open", figyelo)
    collage_output.write_album_ini(mappa, "Kollázsok")

    assert modok, (
        "a modul meg sem nyitotta az ini-t — visszaesés a csonkoló "
        "`write_text()`-re (#1097)?"
    )
    assert all("w" not in mod for mod in modok), (
        f"csonkoló megnyitás egy LÉTEZŐ ini-n: {modok} — "
        "windowson ez rejtett fájlon Permission denied"
    )


def test_a_megjeloles_bukasa_NEM_viszi_el_a_kollazst(tmp_path, monkeypatch):
    """Ha az ini nem írható, a kollázs akkor is elkészült.

    A tulajdonos ezt olvasta: „A kollázs nem készült el" — miközben a JPEG
    és a `.cxf` már a lemezen volt."""
    from picasapy.collage.nodes import CollageNode
    from picasapy.collage.themes import NOBORDER
    from support.jpeg_factory import make_jpeg

    kep = tmp_path / "a.jpg"
    make_jpeg(kep, size=(160, 120))
    beallitas = collage_output.render_settings(
        theme="picturegrid",
        border=NOBORDER,
        spacing=0.0,
        shadows=False,
        page_ratio=0.75,
        background_rgb=(255, 255, 255),
        frame_center=-1,
        seed=1,
        width=400,
    )
    node = CollageNode(
        path=str(kep),
        center_x=200.0,
        center_y=150.0,
        width=200.0,
        height=150.0,
        border=NOBORDER,
    )

    def robban(*_a, **_k):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(collage_output, "write_album_ini", robban)
    cel = tmp_path / "ki" / "k.jpg"

    eredmeny = collage_output.render_collage((node,), beallitas, cel)

    assert eredmeny.path is not None, "a mentés kudarcnak látszik"
    assert cel.exists() and cel.with_suffix(".cxf").exists()
