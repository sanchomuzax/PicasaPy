"""Az önfrissítés a cserélt program QML-cache-ét melegíti (#6374)."""

from __future__ import annotations

from pathlib import Path

from picasapy.app import update_swap_helper as helper


def _csere_futtatasa(monkeypatch, tmp_path: Path, *, elevated: bool, admin: bool, qml_ok: bool):
    esemenyek = []
    stage_root = tmp_path / "stage"
    stage_root.mkdir()
    monkeypatch.setattr(helper, "wait_for_process", lambda _pid: esemenyek.append("wait"))
    monkeypatch.setattr(helper, "_mkdtemp", lambda **_kw: str(stage_root))
    monkeypatch.setattr(helper, "extract_update_archive", lambda _archive, stage: stage)

    def csere(_staged, _install, *, launch):
        esemenyek.append("ellenorzes")
        assert launch()
        return True

    monkeypatch.setattr(helper, "swap_update_directory", csere)
    monkeypatch.setattr(helper, "_onellenorzes", lambda _exe: True)
    monkeypatch.setattr(helper, "_rendszergazda", lambda: admin)
    monkeypatch.setattr(
        helper,
        "_qml_elofordit",
        lambda _exe, **_kw: esemenyek.append("qml") or qml_ok,
    )
    monkeypatch.setattr(
        helper,
        "_qml_grafika_melegites",
        lambda _exe, **_kw: esemenyek.append("grafika") or True,
        raising=False,
    )
    monkeypatch.setattr(
        helper,
        "inditsd_a_felhasznalonak",
        lambda _exe, **_kw: esemenyek.append("inditas"),
    )
    monkeypatch.setattr(helper, "_log_update", lambda *_args, **_kw: None)

    siker = helper.install_after_exit(
        123,
        tmp_path / "update.zip",
        tmp_path / "install",
        "PicasaPy.exe",
        uac_emelt=elevated,
    )
    return siker, esemenyek


def test_a_nem_emelt_frissites_az_uj_program_inditasa_elott_fordit(monkeypatch, tmp_path):
    siker, esemenyek = _csere_futtatasa(
        monkeypatch, tmp_path, elevated=False, admin=False, qml_ok=True
    )

    assert siker is True
    assert esemenyek.index("ellenorzes") < esemenyek.index("qml") < esemenyek.index("inditas")
    assert esemenyek.index("qml") < esemenyek.index("grafika") < esemenyek.index("inditas")


def test_az_emelt_rendszergazdai_frissites_atadja_a_melegitest_az_elso_indulasnak(
    monkeypatch, tmp_path
):
    siker, esemenyek = _csere_futtatasa(
        monkeypatch, tmp_path, elevated=True, admin=True, qml_ok=True
    )

    assert siker is True
    assert "qml" not in esemenyek
    assert esemenyek.index("ellenorzes") < esemenyek.index("inditas")


def test_a_qml_elomelegites_hibaja_nem_buktatja_a_sikeres_cseret(monkeypatch, tmp_path):
    siker, esemenyek = _csere_futtatasa(
        monkeypatch, tmp_path, elevated=False, admin=False, qml_ok=False
    )

    assert siker is True
    assert esemenyek.index("qml") < esemenyek.index("inditas")
