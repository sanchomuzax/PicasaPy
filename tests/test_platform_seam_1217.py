"""Minden platformfüggő ág legyen HELYETTESÍTHETŐ (#1217).

## A minta, ami egyetlen napon NÉGYSZER bukott

| jegy | a teszt feltevése | a windows-lábon |
|---|---|---|
| #1076 | `XDG_CONFIG_HOME` adja a konfig-mappát | a natív `%APPDATA%`-n bukott |
| #1182 | `$XDG_DATA_HOME/Trash` a lomtár | a natív Lomtáron bukott |
| #1206 | a `/` a negyedik gyökér | a valódi meghajtókon bukott |
| #1167 | a „teljes gép" a home-könyvtár | a valódi meghajtókon bukott |

**Mind a négyben a TERMÉK volt helyes, és a TESZT bukott** — ráadásul úgy,
hogy a bukás a natív (helyes) viselkedést mutatta hibának.

## A szabály

> Ha egy teszt állítása egy platformra igaz, a teszt MONDJA KI, melyikre.

Ehhez a terméknek adnia kell egy fogantyút: a platform-lekérdezés legyen
**modulszintű, helyettesíthető** — vagy `_platform()` függvény, vagy
nevesített `platform=` paraméter. Aki közvetlenül a `sys.platform`-ot
olvassa egy elágazásban, azt a teszt csak a saját gépén tudja állítani.

⚠️ **A `skipif` nem megoldás:** a kihagyott teszt a másik platformon NEM
mér semmit. A rögzítéssel mindkét lábon fut, és azt méri, amit állít.

## A szabálynak KÉT oldala van

A fenti csak a TERMÉK oldala: legyen fogantyú. Az őr eredeti változata
(#1268) csak ezt nézte, és emiatt két rés maradt rajta:

1. **A fogantyú megkerülhető más néven.** A `sys.platform` tiltása nem
   fogta meg az `os.name`-et és a `platform.system()`-et — három ág így is
   közvetlenül a valódi oprendszert kérdezte (`ioutil`, `platform_storage`,
   `perf_controller`).
2. **A teszt a fogantyú MELLETT is rögzíthet — rosszul.** Négy teszt a
   `monkeypatch.setattr("…modul.sys.platform", "linux")` alakot használta.
   Ez nem a modul fogantyúját cseréli: a `modul.sys` MAGA a globális `sys`
   modul, tehát a rögzítés **minden** modulra hat, az egész teszt idejére.
   A szivárgás már meg is történt — a `test_fileops_controller.py` saját
   kommentje őrzi: „a `sys.platform` linuxra állítása miatt egy másik
   teszt" elbukott. Egy platform-rögzítés ne legyen mellékhatásos.

Ezért az alábbi őrök együtt érvényesek: fogantyú legyen, EGY néven legyen,
és a teszt a fogantyút rögzítse, ne a globális `sys`-t.

## Mérés (2026-08-24, a #1217 zárásakor)

Ezt a fájlt nem számolva **19** platformfüggő tesztfájl van. A jegy
nyitásakor ebből **6** mondta ki a platformját szabályosan; a kör után
**12**. A maradék 7 szándékosan `skipif` (ld. a következő szakaszt).

A javított rögzítések: **12 hely, 6 fájlban** — `test_application.py` (4),
`test_qml_perf_panel.py` (4), `test_reveal.py`, `test_reveal_platform_1104.py`,
`test_fileops_controller.py`, `test_run_tests_maradek_eletjel_1358.py`.
⚠️ A bevezető commit üzenete tévesen „kilenc helyet" ír: az a foga-próba
sértési ALAKJAINAK száma (9), nem a javított helyeké (12). A mérvadó szám
ez itt — a jegy épp arról szól, hogy az ellenőrizetlen szám félrevisz.

## Ahol a rögzítés NEM lehetséges — és ezért marad `skipif`

A szabály a *helyettesíthető függvénytől* függő viselkedésre szól. Ahol a
teszt a VALÓDI oprendszer egy képességét használja, ott nincs mit
rögzíteni: a `skipif` a helyes eszköz, és a `reason` mondja meg, melyik
képesség hiányzik. Az alábbiakat szándékosan NEM írtuk át (#1217):

| teszt | mitől függ valóban |
|---|---|
| `test_paths.py::test_symlink_resolved` | szimbolikus link LÉTREHOZÁSA |
| `test_paths.py::TestPathKey` | `os.path.normcase` kis/nagybetű-szemantikája |
| `test_ioutil.py::TestModePreservation` | `chmod` — Windowson csak a read-only bit |
| `metadata/test_iptc_writer.py::test_file_mode_preserved` | ugyanaz a `chmod` |
| `fileops/test_writable.py` | valódi írásjogosultság |
| `fileops/test_move_folder.py::test_a_posix_system_path_is_refused` | `Path("/etc").resolve()` |
| `app/test_folder_dedup_repro.py` | szimbolikus link LÉTREHOZÁSA |
| `app/test_edit_controller.py` | `os.geteuid()` (root alatt más a jogosultság) |
| `app/test_fileops_controller.py::TestTrashAvailableFor` | `os.getuid` megléte |

Ezekben a `skipif` NEM hallgatólagos feltevés: kimondja, mit nem tud a
másik platform. A tiltott alak az, amikor egy **helyettesíthető** ág marad
mérés nélkül.
"""

from __future__ import annotations

import ast
import pathlib

GYOKER = pathlib.Path(__file__).resolve().parents[1]
FORRAS = GYOKER / "src" / "picasapy"
TESZTEK = GYOKER / "tests"

#: Ahol a `sys.platform` olvasása RENDBEN van: maga a fogantyú, illetve a
#: nevesített paraméter alapértéke.
_ENGEDETT_FUGGVENYEK = {"_platform"}


def _platform_olvasasok(fa: ast.AST) -> list[ast.Attribute]:
    """A `sys.platform` attribútum-olvasások a fában."""
    return [
        csomopont
        for csomopont in ast.walk(fa)
        if isinstance(csomopont, ast.Attribute)
        and csomopont.attr == "platform"
        and isinstance(csomopont.value, ast.Name)
        and csomopont.value.id == "sys"
    ]


def _egyeb_platform_lekerdezesek(fa: ast.AST) -> list[ast.AST]:
    """A `sys.platform`-on KÍVÜLI platform-azonosító lekérdezések.

    Ugyanaz a döntés, más néven: `os.name` (`"posix"`/`"nt"`) és
    `platform.system()` (`"Linux"`/`"Windows"`/`"Darwin"`). A #1268-as őr
    csak a `sys.platform`-ot tiltotta, ezért három ág némán megkerülte —
    és azokat a tesztek a mai napig nem tudják kimondani."""
    talalatok: list[ast.AST] = []
    for cs in ast.walk(fa):
        if (
            isinstance(cs, ast.Attribute)
            and cs.attr == "name"
            and isinstance(cs.value, ast.Name)
            and cs.value.id == "os"
        ):
            talalatok.append(cs)
        elif (
            isinstance(cs, ast.Call)
            and isinstance(cs.func, ast.Attribute)
            and cs.func.attr == "system"
            and isinstance(cs.func.value, ast.Name)
            and cs.func.value.id == "platform"
        ):
            talalatok.append(cs)
    return talalatok


def _van_platform_parameter(fuggveny) -> bool:
    """Van-e `platform` nevű paramétere — az is szabályos fogantyú.

    Az `application.py` ezt használja: `platform: str | None = None`, majd
    `sys.platform if platform is None else platform`. A teszt így ki tudja
    mondani, melyik platformot méri — a hívásban."""
    argok = fuggveny.args
    nevek = {
        a.arg
        for a in [*argok.posonlyargs, *argok.args, *argok.kwonlyargs]
    }
    return "platform" in nevek


def _fuggveny_torzsek(fa: ast.AST) -> dict[int, tuple[str, bool]]:
    """Sorszám → (az őt tartalmazó függvény neve, van-e platform-paramétere).

    A legbelső nyer."""
    hova: dict[int, tuple[str, bool]] = {}
    for csomopont in ast.walk(fa):
        if isinstance(csomopont, ast.FunctionDef | ast.AsyncFunctionDef):
            adat = (csomopont.name, _van_platform_parameter(csomopont))
            for sor in range(csomopont.lineno, (csomopont.end_lineno or 0) + 1):
                hova[sor] = adat
    return hova


def test_a_sys_platform_csak_a_fogantyuban_es_alapertekben_all():
    """Elágazásban közvetlen `sys.platform` nem lehet."""
    vetok: list[str] = []
    for ut in sorted(FORRAS.rglob("*.py")):
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        hova = _fuggveny_torzsek(fa)
        # a nevesített paraméterek alapértékei (pl. `platform=sys.platform`)
        alapertekek = {
            id(ertek)
            for csomopont in ast.walk(fa)
            if isinstance(csomopont, ast.FunctionDef | ast.AsyncFunctionDef)
            for ertek in [*csomopont.args.defaults, *csomopont.args.kw_defaults]
            if ertek is not None
        }
        for olvasas in _platform_olvasasok(fa):
            if id(olvasas) in alapertekek:
                continue
            nev, van_parameter = hova.get(olvasas.lineno, ("<modul>", False))
            if nev in _ENGEDETT_FUGGVENYEK or van_parameter:
                continue
            vetok.append(
                f"{ut.relative_to(FORRAS.parents[1])}:{olvasas.lineno} ({nev})"
            )

    assert not vetok, (
        "közvetlen `sys.platform` olvasás elágazásban — a teszt így nem "
        "tudja kimondani, melyik platformot méri (#1217):\n  "
        + "\n  ".join(vetok)
    )


def test_a_fogantyu_neve_egyseges():
    """Ahol van fogantyú, ott `_platform` a neve — ne legyen három név."""
    nevek: set[str] = set()
    for ut in sorted(FORRAS.rglob("*.py")):
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        for csomopont in ast.walk(fa):
            if not isinstance(csomopont, ast.FunctionDef):
                continue
            if _platform_olvasasok(csomopont) and not _van_platform_parameter(
                csomopont
            ):
                nevek.add(csomopont.name)

    assert nevek <= _ENGEDETT_FUGGVENYEK, (
        f"a platform-fogantyú több néven él: {sorted(nevek)}"
    )


def test_minden_platform_lekerdezes_a_fogantyun_at_megy():
    """`os.name` és `platform.system()` sem kerülheti meg a fogantyút.

    Ugyanazt a kérdést teszik fel, mint a `sys.platform` — csak más
    szótárral. Ha egy ág ezeken dönt, a tesztje megint csak a fejlesztői
    gépet tudja mérni."""
    vetok: list[str] = []
    for ut in sorted(FORRAS.rglob("*.py")):
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        hova = _fuggveny_torzsek(fa)
        for csomopont in _egyeb_platform_lekerdezesek(fa):
            nev, van_parameter = hova.get(csomopont.lineno, ("<modul>", False))
            if nev in _ENGEDETT_FUGGVENYEK or van_parameter:
                continue
            vetok.append(
                f"{ut.relative_to(FORRAS.parents[1])}:{csomopont.lineno} ({nev})"
            )

    assert not vetok, (
        "`os.name` / `platform.system()` a fogantyún kívül — ez ugyanaz a "
        "platform-döntés más néven, és a teszt nem tudja kimondani (#1217):"
        "\n  " + "\n  ".join(vetok)
    )


def test_a_platform_nev_nem_jelent_mast_sehol():
    """A `_platform` NÉV egyetlen dolgot jelentsen: a fogantyút.

    A `logwriter.py` egy ideig `import platform as _platform` alakban a
    STANDARD MODULT nevezte így (diagnosztikai fejléchez). Egy név, két
    jelentés — pont az a zavar, amit a jegy meg akar szüntetni, csak
    fordítva."""
    vetok: list[str] = []
    for ut in sorted(FORRAS.rglob("*.py")):
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        for cs in ast.walk(fa):
            if not isinstance(cs, ast.Import | ast.ImportFrom):
                continue
            for alias in cs.names:
                if alias.asname == "_platform":
                    vetok.append(f"{ut.relative_to(FORRAS.parents[1])}:{cs.lineno}")

    assert not vetok, (
        "a `_platform` név modul-aliasként is él — a fogantyú nevét ne "
        f"jelentse mást (#1217): {vetok}"
    )


# ---------------------------------------------------------------------
# A szabály MÁSIK oldala: hogyan rögzítsen a TESZT.
# ---------------------------------------------------------------------


def _setattr_hivasok(fa: ast.AST) -> list[ast.Call]:
    """A `monkeypatch.setattr(...)` hívások."""
    return [
        cs
        for cs in ast.walk(fa)
        if isinstance(cs, ast.Call)
        and isinstance(cs.func, ast.Attribute)
        and cs.func.attr == "setattr"
        and isinstance(cs.func.value, ast.Name)
        and cs.func.value.id == "monkeypatch"
    ]


def _globalis_platformot_ir(hivas: ast.Call) -> str | None:
    """A hívás a GLOBÁLIS `sys.platform`-ot / `os.name`-et írja-e át.

    Két alak vezet ugyanoda, és egyik sem a modul fogantyúját cseréli:

    * sztringes: `monkeypatch.setattr("picasapy.x.y.sys.platform", "linux")`
      — a `monkeypatch` a pont előtti részt oldja fel objektumként, és a
      `modul.sys` MAGA a globális `sys` modul;
    * objektumos: `monkeypatch.setattr(modul.sys, "platform", "win32")`
      vagy `monkeypatch.setattr(sys, "platform", "win32")` — ugyanaz.

    Mindkettő a teszt teljes idejére ÁTÍRJA a platform-választ MINDEN
    modul számára. Mindhárom szótár tiltott (`sys.platform`, `os.name`,
    `platform.system`): a `perf_controller` tesztjei épp a harmadikat
    használták, ugyanezzel a mellékhatással."""
    #: (modul, attribútum) párok, amik a GLOBÁLIS platform-választ adják
    tiltott = {("sys", "platform"), ("os", "name"), ("platform", "system")}

    if not hivas.args:
        return None
    elso = hivas.args[0]

    if isinstance(elso, ast.Constant) and isinstance(elso.value, str):
        darabok = elso.value.split(".")
        if len(darabok) >= 2 and tuple(darabok[-2:]) in tiltott:
            return elso.value
        return None

    if len(hivas.args) < 2:
        return None
    masodik = hivas.args[1]
    if not isinstance(masodik, ast.Constant) or not isinstance(masodik.value, str):
        return None
    # `sys` vagy `<bármi>.sys` az első argumentum?
    modulnev = None
    if isinstance(elso, ast.Name):
        modulnev = elso.id
    elif isinstance(elso, ast.Attribute):
        modulnev = elso.attr
    if (modulnev, masodik.value) in tiltott:
        return f"{modulnev}.{masodik.value}"
    return None


def test_a_teszt_a_fogantyut_rogzitse_ne_a_globalis_sys_t():
    """Platform-rögzítés csak a modul `_platform` fogantyúján át.

    A globális `sys.platform` átírása MELLÉKHATÁSOS: átszivárog minden más
    modulra, ami ugyanabban a tesztben fut. Nem elmélet — a
    `test_fileops_controller.py` kommentje egy valódi, ilyen okból elbukott
    tesztet őriz.

    A helyes alak::

        monkeypatch.setattr(reveal, "_platform", lambda: "win32")
    """
    vetok: list[str] = []
    for ut in sorted(TESZTEK.rglob("test_*.py")):
        if ut.name == pathlib.Path(__file__).name:
            continue  # ez a fájl a MINTÁKAT írja le, nem használja őket
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        for hivas in _setattr_hivasok(fa):
            cel = _globalis_platformot_ir(hivas)
            if cel is not None:
                vetok.append(f"{ut.relative_to(GYOKER)}:{hivas.lineno} → {cel}")

    assert not vetok, (
        "a teszt a GLOBÁLIS platformot írja át a modul fogantyúja helyett "
        "— ez minden más modulra átszivárog (#1217). Helyette: "
        '`monkeypatch.setattr(modul, "_platform", lambda: "win32")`:\n  '
        + "\n  ".join(vetok)
    )
