"""#6752: a korábbi frissítősegéd-másolatok induláskor és új másolás előtt tűnjenek el."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from picasapy.app import update_cleanup, update_manager
from tests.app.test_update_manager_6340 import _InlinePool, _MemorySettings, _ReleaseClient


def test_regi_segedek_takaritasa_csak_a_szamozott_masolatokat_torli(tmp_path):
    nevek = (
        "PicasaPyUpdateHelper-123.exe",
        "PicasaPyUpdateHelper-4567.exe",
        "valami.exe",
        "PicasaPyUpdateHelper.exe",
        "PicasaPyUpdateHelper-a.exe",
        "PicasaPyUpdateHelper-12.txt",
    )
    for nev in nevek:
        (tmp_path / nev).write_bytes(b"fajl")

    update_manager.regi_segedek_takaritasa(tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(
        (
            "valami.exe",
            "PicasaPyUpdateHelper.exe",
            "PicasaPyUpdateHelper-a.exe",
            "PicasaPyUpdateHelper-12.txt",
        )
    )


def test_regi_segedek_takaritasa_oserror_utan_a_tobbi_masolatot_torli(
    tmp_path, monkeypatch
):
    nevek = (
        "PicasaPyUpdateHelper-11.exe",
        "PicasaPyUpdateHelper-22.exe",
        "PicasaPyUpdateHelper-33.exe",
    )
    for nev in nevek:
        (tmp_path / nev).write_bytes(b"fajl")

    unlink = update_manager._unlink

    def torles(self, *args, **kwargs):
        if self.name == "PicasaPyUpdateHelper-22.exe":
            raise PermissionError("a seged eppen fut")
        unlink(self, *args, **kwargs)

    monkeypatch.setattr(update_manager, "_unlink", torles)

    update_manager.regi_segedek_takaritasa(tmp_path)

    assert [path.name for path in tmp_path.iterdir()] == ["PicasaPyUpdateHelper-22.exe"]


def test_indulaskori_takaritas_a_segedmasolatokat_minden_inditasi_helyrol_torli(
    tmp_path, monkeypatch
):
    install_dir = tmp_path / "Programs" / "PicasaPy"
    install_dir.mkdir(parents=True)
    update_dir = install_dir.parent / "PicasaPy-update"
    temp_dir = tmp_path / "Temp"
    update_dir.mkdir()
    temp_dir.mkdir()
    (install_dir / "PicasaPyUpdateHelper.exe").write_bytes(b"eredeti")
    for mappa in (update_dir, temp_dir):
        (mappa / "PicasaPyUpdateHelper-123.exe").write_bytes(b"regi")

    monkeypatch.setattr(update_cleanup, "_platform", lambda: "win32")
    monkeypatch.setattr(update_cleanup, "_frozen", lambda: True)
    monkeypatch.setattr(update_cleanup, "_executable_path", lambda: install_dir / "PicasaPy.exe")
    monkeypatch.setattr(update_manager, "_tempdir", lambda: str(temp_dir))
    szalak = []

    class _HatterSzala:
        def __init__(self, *, target, name, daemon):
            szalak.append((target, name, daemon))

        def start(self):
            pass

    monkeypatch.setattr(update_cleanup, "_thread", _HatterSzala)

    update_cleanup.start_startup_cleanup()

    assert len(szalak) == 1
    szalak[0][0]()
    assert all(not (mappa / "PicasaPyUpdateHelper-123.exe").exists() for mappa in (update_dir, temp_dir))
    assert (install_dir / "PicasaPyUpdateHelper.exe").read_bytes() == b"eredeti"


def test_start_helper_takarit_masolas_elott_es_megtartja_az_uj_celt(
    tmp_path, monkeypatch
):
    install_dir = tmp_path / "Programs" / "PicasaPy"
    install_dir.mkdir(parents=True)
    helper = install_dir / "PicasaPyUpdateHelper.exe"
    helper.write_bytes(b"eredeti")
    update_dir = install_dir.parent / "PicasaPy-update"
    temp_dir = tmp_path / "Temp"
    update_dir.mkdir()
    temp_dir.mkdir()
    (update_dir / "PicasaPyUpdateHelper-123.exe").write_bytes(b"regi")
    (temp_dir / "PicasaPyUpdateHelper-456.exe").write_bytes(b"regi")
    monkeypatch.setattr(
        update_manager, "_futtato", SimpleNamespace(executable=str(install_dir / "PicasaPy.exe"))
    )
    monkeypatch.setattr(update_manager, "mappa_irhato", lambda _mappa: True)
    monkeypatch.setattr(update_manager, "_tempdir", lambda: str(temp_dir))
    vezerlo = update_manager.UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=_ReleaseClient(),
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )
    vezerlo._download_path = tmp_path / "frissites.zip"
    inditasok = []
    monkeypatch.setattr(
        update_manager,
        "_inditsd_a_segedet",
        lambda args, *, emelt: inditasok.append(Path(args[0])) or True,
    )

    assert vezerlo.installWhenExiting(False) is True

    cel = inditasok[0]
    assert cel.parent == update_dir
    assert cel.is_file()
    assert not (update_dir / "PicasaPyUpdateHelper-123.exe").exists()
    assert not (temp_dir / "PicasaPyUpdateHelper-456.exe").exists()
