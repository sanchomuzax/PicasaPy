"""A „Keresés a lemezen" IDÉZŐJELEZI az útvonalat Windowson (#1152).

## A tulajdonos jelentése (v0.8.27 után, Windows)

> „A »Keresés a lemezen« kinyitja a Dokumentumok mappát, de nem ez a
> feladat. A feladat az, hogy a képet tartalmazó mappába kerüljön a
> fájlkezelő, és legyen kijelölve a kérdéses fájl."

## Az eredeti — bizonyíték a binárisból

A `Picasa3.exe` **nem** használ `SHOpenFolderAndSelectItems`-et (nincs az
importok között) — `ShellExecuteA`-val indít `explorer`-t, és a
formátum-string a `string_xrefs.csv:16542-16543` szerint:

| cím | string |
|---|---|
| `0x00cd85f4` | `explorer` |
| `0x00cd8604` | `/select,"%s"` |

Mindkettőt ugyanaz a függvény hivatkozza (`0x00981280`).

⚠️ **Az útvonal IDÉZŐJELBEN van.** A mi kódunk idézőjel nélkül adta át
(`/select,{path}`), és a tulajdonos útvonalában SZÓKÖZ van
(`OneDrive - centralmediacsoport`) — az Intéző így nem tudta értelmezni,
és az alapértelmezett mappát nyitotta meg.
"""

from __future__ import annotations

from pathlib import Path


from picasapy.fileops import reveal


def _parancs_windowson(monkeypatch, ut: Path, *, kijelol: bool = True):
    monkeypatch.setattr(reveal, "_windows", lambda: True)
    monkeypatch.setattr(reveal, "_macos", lambda: False)
    return reveal._parancs(ut, kijelol=kijelol)


def test_a_kijelolo_parancs_IDEZOJELEZI_az_utvonalat(monkeypatch):
    """⚠️ A jegy magja: idézőjel nélkül a szóközös útvonal elhasal."""
    ut = Path(r"C:\Users\attila.virag\OneDrive - centralmediacsoport\Képek\AI19.jpg")

    parancs = _parancs_windowson(monkeypatch, ut)

    szoveg = parancs if isinstance(parancs, str) else " ".join(parancs)
    assert '/select,"' in szoveg, (
        "az útvonal nincs idézőjelben — az eredeti formátuma /select,\"%s\" "
        "(0x00cd8604), és szóközös útvonalnál e nélkül az Intéző mást nyit"
    )
    assert str(ut) in szoveg


def test_a_szokozos_utvonal_EGYBEN_marad(monkeypatch):
    """A `/select,"..."` EGY argumentum; a szóköz nem törheti szét.

    ⚠️ Ha listaként adjuk át, a Windows a szóközös argumentumot a SAJÁT
    szabályai szerint idézi (`"/select,C:\\..."`), ami NEM az a forma,
    amit az Intéző vár."""
    ut = Path(r"C:\Users\a b\Képek\AI19.jpg")

    parancs = _parancs_windowson(monkeypatch, ut)

    if isinstance(parancs, str):
        assert parancs.count('"') >= 2
    else:
        valasztok = [t for t in parancs if t.startswith("/select,")]
        assert len(valasztok) == 1, "a /select nem EGY argumentum"
        assert valasztok[0].endswith('"')


def test_kijeloles_nelkul_a_MAPPAT_nyitja(monkeypatch):
    """A mappa-megnyitó ág nem kap `/select`-et."""
    ut = Path(r"C:\Users\a b\Képek")

    parancs = _parancs_windowson(monkeypatch, ut, kijelol=False)

    szoveg = parancs if isinstance(parancs, str) else " ".join(parancs)
    assert "/select" not in szoveg
    assert str(ut) in szoveg
