"""A CI-n LEGYEN core-fájl, amiből natív veremkép olvasható (#3265/#3178).

## A kiváltó eset

2026-09-16, main CI ubuntu 2/4: a `test_projekt_mappa_figyeles_1123.py`
szegmentált. A #3178 gépezete lefutott, de a natív veremkép ELMARADT:

```
--- NATÍV VEREMKÉP a coredumpctl-ből (…) ---
a coredumpctl 1-tel lépett ki: No coredumps found.
```

A GitHub-futtatón a `core_pattern` a `systemd-coredump`-nak adja át a
core-t, az viszont nem tárol semmit — tehát **sem fájl, sem coredumpctl-
bejegyzés** nincs, és a SIGSEGV-ről csak a Python-szálak képe marad. A
#430-osztályú hibáknál épp a C++ keret a lényeg.

## Amit ez a lépés csinál

A futtató a részfutások ELŐTT **fájlos mintára állítja** a
`core_pattern`-t (a munkakönyvtárba), majd a végén visszaállítja. Csak
ott, ahol ez legitim:

- **CI-n** (a fejlesztő gépének rendszerbeállításához nem nyúlunk),
- ha a minta tényleg KEZELŐNEK adja a core-t (`|`-es alak),
- és van **jelszó nélküli `sudo`** (a GitHub-futtatón van).

Bármelyik hiányzik ⇒ nem nyúlunk hozzá, és a hiány OKA a naplóba kerül —
a #3178 szabálya szerint hallgatni itt sem szabad.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_tests_3265", _GYOKER / "scripts" / "run_tests.py")
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)

KEZELOS = "|/usr/lib/systemd/systemd-coredump %P %u %g %s %t 9223372036854775808 %h"
FAJLOS = "core"


class TestMikorNyulunkHozza:
    def test_ci_kezelos_minta_sudoval_igen(self):
        assert rt._core_minta_atallithato(KEZELOS, ci=True, sudo="/usr/bin/sudo")

    def test_ci_nelkul_soha(self):
        """A fejlesztő gépének rendszerbeállítása nem a mi dolgunk."""
        assert not rt._core_minta_atallithato(KEZELOS, ci=False, sudo="/usr/bin/sudo")

    def test_sudo_nelkul_nem(self):
        assert not rt._core_minta_atallithato(KEZELOS, ci=True, sudo=None)

    def test_mar_fajlos_mintat_nem_bantunk(self):
        """Ha a kernel amúgy is fájlba írja, nincs mit átállítani."""
        assert not rt._core_minta_atallithato(FAJLOS, ci=True, sudo="/usr/bin/sudo")


class TestAParancs:
    def test_a_cel_a_munkakonyvtarba_mutat(self):
        cel = rt._core_cel_minta()
        assert str(cel).startswith(str(rt._ROOT))
        #: a `%p` a PID — így két egyidejű összeomlás nem írja felül egymást,
        #: és a `_core_fajlok()` `core.*` mintája megtalálja
        assert str(cel).endswith("core.%p")

    def test_a_parancs_jelszo_nelkuli_sudoval_ir(self):
        #: ⚠️ Az összevetés a `Path` PLATFORMHELYES alakjával megy: Windowson
        #: ugyanez az útvonal `\tmp\core.%p`, és a beégetett POSIX-alak
        #: miatt a próba ott bukott (mérve, main CI windows 1/4). A vizsgált
        #: logika platformfüggetlen, csak a VÁRT szöveg nem volt az.
        cel = Path("/tmp/core.%p")
        parancs = rt._core_minta_parancs("/usr/bin/sudo", cel)
        assert parancs[:3] == ["/usr/bin/sudo", "-n", "sh"]
        egyben = " ".join(parancs)
        assert "/proc/sys/kernel/core_pattern" in egyben
        assert str(cel) in egyben


class TestVisszaallitas:
    def test_a_visszaallitas_az_EREDETI_mintat_irja_vissza(self):
        parancs = rt._core_minta_parancs("/usr/bin/sudo", KEZELOS)
        assert KEZELOS in " ".join(parancs)

    def test_ures_regi_mintara_nem_ir_vissza(self, capsys):
        """Ha nem állítottunk át semmit, a visszaállítás NO-OP."""
        assert rt._allitsd_vissza_a_core_mintat(None) is False


class TestAGdbTelepitese:
    """A core magában semmit nem mond — `gdb` nélkül nincs natív keret.

    Mérve a PR #3266 első futásán: „van core (core.4952), de nincs `gdb`".
    A GitHub-futtatón a `gdb` nincs telepítve, de telepíthető."""

    def test_ci_sudoval_es_apttal_igen(self):
        assert rt._telepitheto_a_gdb(True, "/usr/bin/sudo", "/usr/bin/apt-get")

    def test_ci_nelkul_soha(self):
        """A fejlesztő gépére tesztfuttatóból nem telepítünk."""
        assert not rt._telepitheto_a_gdb(False, "/usr/bin/sudo", "/usr/bin/apt-get")

    def test_apt_nelkul_nem(self):
        assert not rt._telepitheto_a_gdb(True, "/usr/bin/sudo", None)

    def test_sudo_nelkul_nem(self):
        assert not rt._telepitheto_a_gdb(True, None, "/usr/bin/apt-get")
