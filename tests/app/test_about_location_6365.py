"""A Névjegyben látható programhely meghatározása (#6365)."""

from pathlib import Path
from types import SimpleNamespace

from picasapy.app import application_location


def test_csomagolt_futasnal_az_exe_mappaja(monkeypatch, tmp_path):
    exe = tmp_path / "telepitett" / "PicasaPy.exe"
    exe.parent.mkdir()
    monkeypatch.setattr(
        application_location,
        "sys",
        SimpleNamespace(frozen=True, executable=str(exe)),
    )

    assert Path(application_location.program_location()) == exe.parent.resolve()


def test_forrasbol_futasnal_a_picasapy_csomagmappa(monkeypatch, tmp_path):
    modul = tmp_path / "src" / "picasapy" / "app" / "application_location.py"
    modul.parent.mkdir(parents=True)
    monkeypatch.setattr(application_location, "__file__", str(modul))
    monkeypatch.setattr(
        application_location,
        "sys",
        SimpleNamespace(frozen=False, executable=""),
    )

    assert Path(application_location.program_location()) == modul.parents[1].resolve()


def test_a_futas_helye_bekerul_a_qml_kornyezetbe():
    gyoker = Path(__file__).resolve().parents[2]
    indito = (gyoker / "src/picasapy/app/application_startup_qml.py").read_text(
        encoding="utf-8"
    )

    assert 'setContextProperty("appLocation", program_location())' in indito
