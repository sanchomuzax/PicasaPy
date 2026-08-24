"""#1187 — a `SAJÁT FUNKCIÓ` jelölés őrének tesztjei.

Az őr két irányban ellenőrzi a jegyzék (`docs/decisions/
vedett-sajat-funkciok.md`) és a kód szinkronját, és mindkettőnek **van
foga**: egy mesterségesen becsempészett szétcsúszást (árva tétel, jelöletlen
fájl, jelöletlen jegyzék-tétel) meg kell fognia — a puszta „lefut hiba
nélkül" nem elég.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import check_protected_features as guard  # noqa: E402

_ENTRY = "- `{path}` (#1) — leírás.\n"


def _jegyzek(tmp_path: Path, *sorok: str) -> Path:
    jegyzek = tmp_path / "vedett-sajat-funkciok.md"
    jegyzek.write_text(
        "# Jegyzék\n\n## Ismert esetek\n\n" + "".join(sorok), encoding="utf-8"
    )
    return jegyzek


def _futtat(jegyzek: Path, tmp_path: Path) -> int:
    """`main()` a tmp_path-ot használva gyökérnek ÉS alapnak."""
    return guard.main(
        ["--registry", str(jegyzek), "--roots", str(tmp_path), "--base", str(tmp_path)]
    )


# -- 1. van foga: mindhárom hibafajta ---------------------------------------


def test_az_arva_tetelt_megtalalja(tmp_path: Path) -> None:
    """A jegyzék egy nem létező fájlra mutat."""
    jegyzek = _jegyzek(tmp_path, _ENTRY.format(path="nincs/ilyen.py"))
    kod = _futtat(jegyzek, tmp_path)
    assert kod == 1


def test_a_jelolo_nelkuli_celfajlt_megtalalja(tmp_path: Path) -> None:
    """A hivatkozott fájl létezik, de nincs benne a jelölő szöveg."""
    cel = tmp_path / "kod.py"
    cel.write_text("# semmi különös\n", encoding="utf-8")
    jegyzek = _jegyzek(tmp_path, _ENTRY.format(path="kod.py"))
    kod = _futtat(jegyzek, tmp_path)
    assert kod == 1


def test_a_jeloletlen_jegyzeku_fajlt_megtalalja(tmp_path: Path) -> None:
    """Van `SAJÁT FUNKCIÓ` jelölés a kódban, de nincs hozzá jegyzék-tétel.

    A jegyzéknek van egy MÁSIK, rendben lévő tétele — hogy a hiba biztosan
    a 2. irányú (kód → jegyzék) ellenőrzésből jöjjön, ne az üres jegyzék
    2-es kilépési kódjából.
    """
    (tmp_path / "rendben.py").write_text(
        "# SAJÁT FUNKCIÓ (#1): ez fel van véve\n", encoding="utf-8"
    )
    (tmp_path / "elfelejtett.py").write_text(
        "# SAJÁT FUNKCIÓ (#9): senki nem vette fel a jegyzékbe\n",
        encoding="utf-8",
    )
    jegyzek = _jegyzek(tmp_path, _ENTRY.format(path="rendben.py"))
    kod = _futtat(jegyzek, tmp_path)
    assert kod == 1


# -- 2. nem kiabál hiába: a rendben lévő eset -------------------------------


def test_a_rendben_levo_parost_elfogadja(tmp_path: Path) -> None:
    cel = tmp_path / "kod.py"
    cel.write_text("# SAJÁT FUNKCIÓ (#1): mind rendben\n", encoding="utf-8")
    jegyzek = _jegyzek(tmp_path, _ENTRY.format(path="kod.py"))
    kod = _futtat(jegyzek, tmp_path)
    assert kod == 0


def test_a_sor_utani_sor_hivatkozas_a_puszta_fajlutvonalat_hasznalja(
    tmp_path: Path,
) -> None:
    """`fájl.py:42` alakú hivatkozásnál a `:sor` rész nem számít bele."""
    cel = tmp_path / "kod.py"
    cel.write_text("# SAJÁT FUNKCIÓ (#1): itt\n", encoding="utf-8")
    jegyzek = _jegyzek(tmp_path, _ENTRY.format(path="kod.py:42"))
    kod = _futtat(jegyzek, tmp_path)
    assert kod == 0


def test_a_kizart_fajlokat_a_2_iranyu_ellenorzes_kihagyja(tmp_path: Path) -> None:
    """A jegyzék és a módszertan saját maga is tartalmazza a `MARKER`-t
    (a konvenció bemutatásához) — ez nem hamis riasztás forrása."""
    kizart_relative = next(iter(guard.EXCLUDED_FROM_REVERSE_CHECK))
    kizart = _REPO_ROOT / kizart_relative
    assert guard.MARKER in guard._read_text(kizart)


# -- 3. a parancssor hibaútjai -----------------------------------------------


def test_a_hianyzo_jegyzek_kettes_kilepesi_kodot_ad(tmp_path: Path) -> None:
    kod = guard.main(["--registry", str(tmp_path / "nincs.md")])
    assert kod == 2


def test_az_ures_jegyzek_kettes_kilepesi_kodot_ad(tmp_path: Path) -> None:
    jegyzek = _jegyzek(tmp_path)  # nincs egyetlen "- `...`" sor sem
    kod = _futtat(jegyzek, tmp_path)
    assert kod == 2


# -- 4. az ÉLES fa: a jegyzék ne rohadjon el --------------------------------


def test_az_eles_jegyzek_egyezik_a_kodfaval() -> None:
    """Ugyanaz, amit egy kézi futtatás a repó gyökeréről lefuttatna."""
    assert guard.main([]) == 0
