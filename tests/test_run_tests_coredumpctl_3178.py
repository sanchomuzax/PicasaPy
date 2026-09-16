"""#3178 — ahol a core-t a systemd kapja meg, a `coredumpctl` az út.

Az eszköz első éles jelentése (PR #3239, ubuntu 2/4) ezt írta:

```
nincs core-fájl … (core_pattern: |/usr/lib/systemd/systemd-coredump %P %u …)
```

⇒ A GitHub-futtatón a kernel **kezelőnek adja át** a core-t, tehát a
munkakönyvtárban sosem lesz fájl. A natív veremkép ott a `coredumpctl`-en át
érhető el — ez a lap azt méri.

⚠️ A `ulimit`-es ág MEGMARAD: ahol a `core_pattern` fájlt ír (a fejlesztői
gép), ott az a rövidebb út. A két ág sorrendje: előbb a fájl, aztán a kezelő.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


class HamisEredmeny:
    def __init__(self, kimenet="", hiba="", kod=0):
        self.stdout = kimenet
        self.stderr = hiba
        self.returncode = kod


class TestAKezelosMinta:
    def test_a_csovezetett_minta_felismerese(self) -> None:
        assert run_tests._kezelo_kapja_a_core_t(
            "|/usr/lib/systemd/systemd-coredump %P %u %g %s %t 9223372036854775808 %h %d"
        )
        assert not run_tests._kezelo_kapja_a_core_t("core")
        assert not run_tests._kezelo_kapja_a_core_t("core.%p")
        assert not run_tests._kezelo_kapja_a_core_t("(nem olvasható: valami)")


class TestACoredumpctlAg:
    def test_kezelos_mintanal_a_coredumpctl_t_kerdezi(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)  # nincs core-fájl
        monkeypatch.setattr(
            run_tests,
            "_core_minta",
            lambda: "|/usr/lib/systemd/systemd-coredump %P %u",
        )
        monkeypatch.setattr(
            run_tests, "_which", lambda nev: f"/usr/bin/{nev}"
        )
        hivasok: list[list[str]] = []

        def hamis_run(parancs, **_kw):
            hivasok.append(parancs)
            if parancs[0].endswith("coredumpctl") and "info" in parancs:
                return HamisEredmeny(
                    kimenet="Signal: 11 (SEGV)\nExecutable: /usr/bin/python3\n"
                )
            return HamisEredmeny()

        monkeypatch.setattr(run_tests, "_run", hamis_run)

        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is True
        kimenet = capsys.readouterr().out
        assert "Signal: 11 (SEGV)" in kimenet
        assert any("coredumpctl" in p[0] for p in hivasok)

    def test_coredumpctl_NELKUL_kimondja(self, monkeypatch, tmp_path, capsys) -> None:
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(
            run_tests, "_core_minta", lambda: "|/usr/lib/systemd/systemd-coredump"
        )
        monkeypatch.setattr(run_tests, "_which", lambda nev: None)
        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is False
        kimenet = capsys.readouterr().out.lower()
        assert "coredumpctl" in kimenet

    def test_a_FAJLOS_ag_elsobbseget_kap(self, monkeypatch, tmp_path, capsys) -> None:
        """Ahol van core-fájl, ott a `gdb` közvetlenül azt nyitja — a
        `coredumpctl`-t meg sem kérdezzük."""
        (tmp_path / "core.42").write_bytes(b"x")
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(
            run_tests, "_core_minta", lambda: "|/usr/lib/systemd/systemd-coredump"
        )
        monkeypatch.setattr(run_tests, "_which", lambda nev: f"/usr/bin/{nev}")
        hivasok: list[list[str]] = []

        def hamis_run(parancs, **_kw):
            hivasok.append(parancs)
            return HamisEredmeny(kimenet="#0 QObject::~QObject()\n")

        monkeypatch.setattr(run_tests, "_run", hamis_run)
        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is True
        assert all("coredumpctl" not in p[0] for p in hivasok)
        assert "QObject" in capsys.readouterr().out

    def test_kezelo_nelkul_es_core_nelkul_marad_a_regi_uzenet(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(run_tests, "_core_minta", lambda: "core")
        monkeypatch.setattr(run_tests, "_which", lambda nev: f"/usr/bin/{nev}")
        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is False
        kimenet = capsys.readouterr().out
        assert "nincs core" in kimenet.lower()
        assert "core_pattern: core" in kimenet
