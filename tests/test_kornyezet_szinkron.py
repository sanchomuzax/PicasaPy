"""A futtatókörnyezet EGY igazságforrásból épül — őr.

2026-08-17-ig a környezet csomaglistája **négy végrehajtható helyen** élt
párhuzamosan (a CI `ci.yml`-je, a Claude- és a Codex-session hookja, plusz a
`pyproject.toml`), és a szinkronjukat mindössze egy komment kérte
(„a lista a .github/workflows/ci.yml-lel szinkronban tartandó"). A komment
nem bizonyíték (PROTOKOLL): a lista már el is csúszott, két ponton.

- A `libpulse0` (Qt Multimedia, #14) a CI-ben szerepelt, a hookokban nem —
  a felhős session tehát MÁS környezetben futtatta ugyanazt a
  tesztkészletet, mint amiben a CI zöldre váltott.
- A `ruff` egyik telepítőben sem szerepelt, hiába kéri a CONTRIBUTING és a
  PROTOKOLL kötelező lépésként; ahol a sessionben mégis elérhető volt, ott
  egy véletlen, nem deklarált adottság adta.

A javítás szándékosan NEM egy összehasonlító őr lett: az továbbra is négy
lista maradna, csak riasztana. A többi lista **megszűnt**. A Python-csomagok
igazságforrása a `pyproject.toml` (`dependencies` + a `dev` extra), a
rendszercsomagoké a `packaging/qt-runtime-deps.txt`, és minden telepítő ezeken
át, a `scripts/print_dependencies.py`-vel kérdezi le őket. Ugyanaz a minta,
amivel a #646 a tételes package-data listát váltotta ki egy `graft`-tal.

Ez a teszt azt őrzi, hogy MÁSODIK lista ne szülessen újra.

Hatókör: a CI-munkafolyamatok és a session-indító hookok — az a halmaz,
aminek a szétcsúszása fájt. A `packaging/` kiadás-szkriptjei szándékosan
kimaradnak: azok nem a futtatókörnyezetet építik, hanem egy eldobható,
egyszer használatos build-venv-et.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_PYPROJECT = _GYOKER / "pyproject.toml"
_APT_LISTA = _GYOKER / "packaging" / "qt-runtime-deps.txt"
_SZKRIPT = _GYOKER / "scripts" / "print_dependencies.py"
_BOOTSTRAP = _GYOKER / "scripts" / "bootstrap_env.sh"
_HOOKOK = (
    _GYOKER / ".claude" / "hooks" / "session-start.sh",
    _GYOKER / ".codex" / "hooks" / "session-start.sh",
)

#: A fejlesztői eszközök, amiket a `dev` extrának hoznia KELL. A `ruff` és a
#: `pytest` azért kötelező elem, mert a PROTOKOLL push előtti lépésként kéri
#: mindkettőt — ha a session-környezet nem telepíti, a lépés kimarad.
_KOTELEZO_DEV = ("pytest", "pytest-cov", "ruff", "build")

#: A rendszercsomagok, amik nélkül a Qt/QML-tesztek nem futnak le. A
#: `libpulse0` a Qt Multimedia (videó, #14) betöltéséhez kell — pont ez volt
#: az a csomag, ami a CI és a session között elcsúszott.
_KOTELEZO_APT = ("libegl1", "libgl1", "libxkbcommon0", "libpulse0")


def _telepito_sorok(szoveg: str) -> list[str]:
    """A fájl `pip install` / `apt-get install` sorai, kommentek nélkül.

    A komment-levágás a `#`-nál történik: shellben és YAML-ben egyaránt ez a
    komment jele, a workflow `run: |` blokkjaiban lévő shell-kommenteket is
    beleértve. Így egy magyarázó komment szabadon leírhat csomagnevet (a
    fenti modul-docstring maga is tele van velük) — a tiltás csak azt üti,
    ami ténylegesen TELEPÍT.
    """
    sorok = []
    for nyers in szoveg.splitlines():
        sor = nyers.split("#", 1)[0]
        if "pip install" in sor or "apt-get install" in sor:
            sorok.append(sor)
    return sorok


def _vizsgalt_fajlok() -> list[Path]:
    """A CI-munkafolyamatok és a session-hookok — a szabály hatóköre."""
    fajlok = sorted((_GYOKER / ".github" / "workflows").glob("*.yml"))
    fajlok.extend(h for h in _HOOKOK if h.exists())
    if _BOOTSTRAP.exists():
        fajlok.append(_BOOTSTRAP)
    return fajlok


def _deklaralt_python_csomagok() -> list[str]:
    adat = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    projekt = adat["project"]
    csomagok = list(projekt.get("dependencies", []))
    csomagok.extend(projekt.get("optional-dependencies", {}).get("dev", []))
    # A verzió-megkötéseket (`pytest>=8`) levágjuk: a puszta nevekre keresünk.
    return [re.split(r"[<>=!~\[ ]", cs, maxsplit=1)[0].strip() for cs in csomagok]


def _deklaralt_apt_csomagok() -> list[str]:
    sorok = _APT_LISTA.read_text(encoding="utf-8").splitlines()
    return [s.strip() for s in sorok if s.strip() and not s.strip().startswith("#")]


def _futtat(*argumentumok: str) -> list[str]:
    kimenet = subprocess.run(
        [sys.executable, str(_SZKRIPT), *argumentumok],
        capture_output=True,
        text=True,
        check=True,
        cwd=_GYOKER,
    )
    return kimenet.stdout.split()


def test_a_dev_extra_hozza_a_fejlesztoi_eszkozoket() -> None:
    """A `dev` extra nélkül a session-környezetből hiányzik a teszt/lint."""
    deklaralt = _deklaralt_python_csomagok()
    hianyzik = [cs for cs in _KOTELEZO_DEV if cs not in deklaralt]
    assert not hianyzik, (
        f"a pyproject.toml `dev` extrájából hiányzik: {hianyzik}. "
        "Enélkül a session-hook nem telepíti őket, és a PROTOKOLL push előtti "
        "lépése (teljes teszt + ruff) csendben kimarad."
    )


def test_a_rendszercsomagok_listaja_teljes() -> None:
    """A Qt-hez kellő rendszercsomagok egyetlen, közös fájlban élnek."""
    assert _APT_LISTA.exists(), f"hiányzik a rendszercsomag-lista: {_APT_LISTA}"
    csomagok = _deklaralt_apt_csomagok()
    hianyzik = [cs for cs in _KOTELEZO_APT if cs not in csomagok]
    assert not hianyzik, f"a rendszercsomag-listából hiányzik: {hianyzik}"


def test_a_szkript_a_deklaraciot_adja_vissza() -> None:
    """A lekérdező szkript nem saját listát tart, hanem a deklarációt olvassa."""
    adat = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    projekt = adat["project"]

    futasideju = _futtat()
    assert futasideju == list(projekt["dependencies"])

    dev = _futtat("--dev")
    assert dev == list(projekt["optional-dependencies"]["dev"])

    assert _futtat("--all") == futasideju + dev
    assert _futtat("--apt") == _deklaralt_apt_csomagok()


def test_nincs_masodik_csomaglista() -> None:
    """Egyetlen telepítő sor sem sorolhat fel csomagot tételesen.

    Ez a teszt lelke. Nem azt méri, hogy a listák EGYEZNEK (két lista
    egyezése holnap már nem áll), hanem hogy második lista nem is létezik:
    a CI és a hookok kizárólag a `print_dependencies.py`-n át telepítenek.
    """
    tiltott = _deklaralt_python_csomagok() + _deklaralt_apt_csomagok()
    talalatok: list[str] = []

    for fajl in _vizsgalt_fajlok():
        for sor in _telepito_sorok(fajl.read_text(encoding="utf-8")):
            for csomag in tiltott:
                if re.search(rf"(?<![\w-]){re.escape(csomag)}(?![\w-])", sor):
                    utvonal = fajl.relative_to(_GYOKER)
                    talalatok.append(f"{utvonal}: {csomag} — {sor.strip()}")

    assert not talalatok, (
        "tételes csomaglista került vissza a telepítőkbe:\n  "
        + "\n  ".join(talalatok)
        + "\nHasználd helyette: pip install $(python scripts/print_dependencies.py --all)"
    )


def test_a_hookok_a_kozos_bootstrapot_hivjak() -> None:
    """A két session-hook ugyanazt a szkriptet futtatja, nem másolatokat."""
    assert _BOOTSTRAP.exists(), f"hiányzik a közös bootstrap: {_BOOTSTRAP}"
    for hook in _HOOKOK:
        szoveg = hook.read_text(encoding="utf-8")
        assert "bootstrap_env.sh" in szoveg, (
            f"a(z) {hook.relative_to(_GYOKER)} nem a közös bootstrapot hívja — "
            "a két hook logikája újra szétmásolódott"
        )


def test_a_ci_valoban_lefuttatja_a_hookot() -> None:
    """Van olyan CI-job, ami magát a bootstrapot futtatja (nem csak leírja).

    A PROTOKOLL szabálya: a KIMENETET kell ellenőrizni, ne a szándékot. Az
    egyetlen érvényes bizonyíték arra, hogy a session-környezet működik, az,
    ha egy tiszta gépen tényleg felépül és futnak benne a Qt-tesztek —
    ugyanaz az elv, mint a `check_declared_setuptools_minimum.py`-nál, ami a
    deklarált setuptools-minimumot a valósághoz méri, nem önmagához.
    """
    futtatja = [
        f.name
        for f in (_GYOKER / ".github" / "workflows").glob("*.yml")
        if "bootstrap_env.sh" in f.read_text(encoding="utf-8")
    ]
    assert futtatja, (
        "egyetlen CI-munkafolyamat sem futtatja a session-bootstrapot — "
        "a session-környezet így megint csak deklaráció, nem bizonyíték"
    )
