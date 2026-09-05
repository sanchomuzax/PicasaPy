"""#2491 — a PicasaPy által írt `.picasa.ini` BÁJTRA olyan legyen, amilyet a
Picasa is ír.

A tulajdonos jelentése szerint az együttélés egyirányúvá vált: amit a Picasa
ír, azt látjuk, amit MI írunk, azt a Picasa nem veszi észre. A Picasa itt nem
futtatható (Windows-program), ezért a bizonyíték csak az lehet, hogy a
kimenetünket **valódi, Picasa által ÍRT** referenciákhoz mérjük.

Két, méréssel alátámasztott állítást rögzítenek az itteni őrök:

1. **Sorvégjel.** A `research/` alatti, kizárólag a Picasa által írt
   `.picasa.ini` fájlok mind **CRLF** sorvégűek (75 fájl, egyetlen kivétel
   nélkül); a LF-es és a vegyes sorvégű minták kivétel nélkül olyanok,
   amelyeknek a MI kimenetünk volt az alapja. Egy meglévő fájl sorvégjelét
   a dokumentum-réteg eddig is örökölte — a rés az ÚJ fájlnál volt: az
   üres dokumentum `\\n`-t adott, tehát a Picasa által még nem érintett
   mappában (pontosan a #2491 helyzete) LF-es fájlt hoztunk létre.

2. **A `filters=` alakja.** Az egygombos „Jó napom van" a láncban
   `enhance=1;` — engedélyező flaggel, kanonikus (kisbetűs) néven,
   pontosvesszővel lezárva. Ez a kulcs a kép szakaszába kerül, a szakasz
   fejléce a fájlnév.

⚠️ Amit ez a lap NEM állít: hogy a LF-es sorvég volt a jelentett hiba oka.
A `research/testdata/golden-kit-result/` bizonyítja, hogy a Picasa a mi
LF-es fájljainkat is BEOLVASTA (a saját CRLF-es `backuphash=` sorait fűzte
melléjük). A CRLF tehát az eredetivel való egyezés, nem mért gyógyír.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.edit.session import EditSession
from picasapy.ini import parse_document, update_document

#: Egy valódi, a Picasa 3 által ÍRT `.picasa.ini` bájtra (a tulajdonos gépe,
#: `research/#2007-rotate-ini/.picasa.ini`, 2026-09-02). Azért literál és nem
#: fájlhivatkozás, mert a `research/` mappa nincs a repóban — fájlból olvasva
#: az őr a CI-n MINDIG kimaradna, tehát nem lenne foga.
_PICASA_REFERENCIA = (
    b"[Picasa]\r\n"
    b"P2category=Exported Pictures\r\n"
    b"date=46267.802095\r\n"
    b"[_03c62d34-6e84-4b2c-aa2b-e25c54f24d08.jpg]\r\n"
    b"rotate=rotate(0)\r\n"
    b"backuphash=6547\r\n"
)

_KEP = "235707.jpg"


def _effekt_kiirasa(mappa: Path) -> bytes:
    """A „Jó napom van" a mag API-ján át — pontosan úgy, ahogy a szerkesztő."""
    (mappa / _KEP).write_bytes(b"\xff\xd8\xff\xd9")
    ini = mappa / ".picasa.ini"
    lanc = EditSession.from_value("").apply("enhance").to_value()
    update_document(ini, lambda doc: doc.with_value(_KEP, "filters", lanc), backup=True)
    return ini.read_bytes()


def test_a_referencia_valoban_crlf_soregu() -> None:
    """Kontroll: a mérce tényleg CRLF-es, Picasa-írta tartalom (#2491/2)."""
    assert _PICASA_REFERENCIA.count(b"\r\n") == _PICASA_REFERENCIA.count(b"\n") > 0


def test_uj_ini_a_picasa_soregjelevel_keletkezik(tmp_path: Path) -> None:
    """ÚJ mappában is CRLF — a Picasa sosem ír LF-es `.picasa.ini`-t (#2491)."""
    nyers = _effekt_kiirasa(tmp_path)
    assert b"\n" in nyers
    assert nyers.count(b"\r\n") == nyers.count(b"\n"), (
        f"LF-es sor maradt a kimenetben: {nyers!r}"
    )


def test_uj_ini_teljes_bajtkepe(tmp_path: Path) -> None:
    """A „Jó napom van" kimenete BÁJTRA — a hibaosztály horgonya (#2491)."""
    assert _effekt_kiirasa(tmp_path) == b"[235707.jpg]\r\nfilters=enhance=1;\r\n"


def test_meglevo_picasa_fajl_soregjele_valtozatlan(tmp_path: Path) -> None:
    """Meglévő fájlnál a MEGLÉVŐ sorvég marad — a round-trip elv (#2491)."""
    eredeti = _PICASA_REFERENCIA
    (tmp_path / ".picasa.ini").write_bytes(eredeti)
    nyers = _effekt_kiirasa(tmp_path)
    assert nyers.startswith(eredeti), "a meglévő tartalom bájtra megmaradt"
    assert nyers.count(b"\r\n") == nyers.count(b"\n")
    assert nyers.endswith(b"[235707.jpg]\r\nfilters=enhance=1;\r\n")


def test_lf_es_fajl_lf_marad(tmp_path: Path) -> None:
    """LF-es (nem Picasa-írta) fájlt NEM írunk át CRLF-re (#2491).

    A round-trip elv erősebb, mint az alapértelmezés: amit nem mi hoztunk
    létre, ahhoz nem nyúlunk hozzá stílus-okból."""
    (tmp_path / ".picasa.ini").write_bytes(b"[Picasa]\nname=proba\n")
    nyers = _effekt_kiirasa(tmp_path)
    assert b"\r\n" not in nyers, f"CRLF-re írtuk át az LF-es fájlt: {nyers!r}"


def test_ures_dokumentum_alapertelmezett_sorvegjele() -> None:
    """Az egység szintjén: az üres dokumentum sorvégjele CRLF (#2491)."""
    assert parse_document("").newline == "\r\n"
