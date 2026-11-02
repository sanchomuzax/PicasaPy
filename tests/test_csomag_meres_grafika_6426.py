"""#6426 — a mérő bemelegíti és naplózza a grafikai indulási útvonalat."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib
import importlib.util
from pathlib import Path


_GYOKER = Path(__file__).resolve().parents[1]
_MERES_UT = _GYOKER / "packaging/windows/csomag_meres.py"
_SPEC = importlib.util.spec_from_file_location("csomag_meres_grafika_6426", _MERES_UT)
csomag_meres = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(csomag_meres)
ido_modul = importlib.import_module("csomag_meres_ido")


# Rontás-kontroll: az elemzők kategória- és URL-feldolgozását módosítva ez piros.
def test_a_qt_naplosorokbol_a_forraskodolasa_es_a_grafikus_hatter_ismerheto_fel():
    kimenet = "\n".join(
        (
            'qt.qml.diskcache: Error loading "file:///C:/Program%20Files/PicasaPy/_internal/picasapy/app/qml/PicasaPy/Main.qml" from disk cache: "No such file or directory"',
            'qt.qml.diskcache: Error loading "file:///C:/Program%20Files/PicasaPy/_internal/picasapy/app/qml/PicasaPy/PeoplePane.qml" from disk cache: "No such file or directory"',
            'qt.qml.diskcache: Error loading "file:///C:/Qt/qml/QtQuick/Controls/Button.qml" from disk cache: "No such file or directory"',
            'qt.qml.diskcache: Error loading "file:///C:/Qt/qml/QtQuick/Controls/Thing.js" from disk cache: "No such file or directory"',
            "qt.rhi.general: Created D3D11 device 00000123",
        )
    )

    assert ido_modul.qml_ujraforditott_fajlok(kimenet) == [
        "PicasaPy/Main.qml",
        "PicasaPy/PeoplePane.qml",
        "QtQuick/Controls/Button.qml",
    ]
    assert ido_modul.grafikus_hatter_nev(kimenet) == "Direct3D 11"


def test_a_sikertelen_backend_proba_helyett_a_sikeresen_letrehozottat_irja_ki():
    kimenet = "\n".join(
        (
            "qt.rhi.general: Failed to create D3D11 device; trying Vulkan",
            "qt.rhi.general: Created Vulkan device 00000456",
        )
    )

    assert ido_modul.grafikus_hatter_nev(kimenet) == "Vulkan"


def test_az_elemzo_husz_fajlnal_tobbet_nem_ir_ki():
    sorok = [
        f'qt.qml.diskcache: Error loading "file:///C:/qml/Q{i}.qml" from disk cache: "No such file or directory"'
        for i in range(25)
    ]

    assert len(ido_modul.qml_ujraforditott_fajlok("\n".join(sorok))) == 20


def test_a_valodi_ablakos_meres_engedelyezi_a_qml_es_rhi_diagnosztikat(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        ido_modul,
        "_profil",
        lambda *_args, **_kwargs: (
            {"QT_LOGGING_RULES": "*.debug=false"},
            tmp_path / "library",
        ),
    )
    monkeypatch.setattr(ido_modul, "_naplo_sorai", lambda _root: [])
    inditasok = []

    def popen(_command, *, env, **_kwargs):
        inditasok.append(env)
        return object()

    monkeypatch.setattr(ido_modul, "_popen", popen)
    ido_modul._egy_inditas(
        ["PicasaPy.exe"],
        tmp_path,
        ablakkal=False,
        indulo_hatar_ms=1000,
    )

    szabalyok = inditasok[0]["QT_LOGGING_RULES"]
    assert szabalyok.startswith("*.debug=false;")
    assert "qt.qml.diskcache.debug=true" in szabalyok
    assert "qt.scenegraph.general.debug=true" in szabalyok
    assert "qt.rhi.general.debug=true" in szabalyok


def test_a_meres_a_qml_es_a_grafikai_melegites_utan_indul_eloszor(
    monkeypatch, tmp_path, capsys
):
    qml_cache_warmup = importlib.import_module("qml_cache_warmup")
    esemenyek = []
    env = {"LOCALAPPDATA": str(tmp_path / "local")}
    monkeypatch.setattr(
        ido_modul,
        "_profil",
        lambda root, kepek=0: (
            esemenyek.append(("profil", root, kepek)) or env,
            root / "library",
        ),
    )
    monkeypatch.setattr(
        qml_cache_warmup,
        "melegitsd_qml_cache",
        lambda *_args, **_kwargs: esemenyek.append(("qml",)),
    )
    monkeypatch.setattr(
        qml_cache_warmup,
        "melegitsd_qml_grafikat",
        lambda *_args, **_kwargs: esemenyek.append(("grafika",)),
        raising=False,
    )
    monkeypatch.setattr(ido_modul, "_bevar", lambda result: result)
    naplo = "\n".join(
        (
            'qt.qml.diskcache: Error loading "file:///C:/qml/Main.qml" from disk cache: "No such file or directory"',
            "qt.rhi.general: Created D3D11 device 00000123",
        )
    )

    def inditas(*_args, **_kwargs):
        esemenyek.append(("meres",))
        return {
            "kod": 0,
            "fal_mp": 0.1,
            "sorok": [],
            "indult": datetime.now(timezone.utc),
            "kimenet": naplo,
            "valodi_ablak": True,
            "indulo_hatar_ms": 1000,
            "indulo_kep_kotelezo": False,
        }

    monkeypatch.setattr(ido_modul, "_egy_inditas", inditas)
    monkeypatch.setattr(ido_modul, "hatar_hiba", lambda *_args: None)
    monkeypatch.setattr(ido_modul, "indulo_kozepertek_hiba", lambda *_args: None)

    assert (
        ido_modul._ido_futtato(
            "indulo", ["PicasaPy.exe"], 2, tmp_path, None, 0, 5.0, 1000
        )
        == 0
    )

    output = capsys.readouterr().out
    assert [event[0] for event in esemenyek] == [
        "profil",
        "qml",
        "grafika",
        "meres",
        "meres",
    ]
    assert output.count("futás közben forrásból fordított QML") == 1
    assert "Main.qml" in output
    assert "grafikus háttér: Direct3D 11" in output


def test_a_telepito_a_grafikai_melegitest_a_felhasznaloi_inditas_elott_futtatja():
    setup = (_GYOKER / "packaging/windows/picasapy.iss").read_text(encoding="utf-8")
    qml = setup.index('Parameters: "--qml-elofordit"')
    grafika = setup.index('Parameters: "--qml-grafika-melegites"')
    inditas = setup.index('Description: "{cm:LaunchProgram')

    assert qml < grafika < inditas
    assert "runhidden waituntilterminated runasoriginaluser" in setup[grafika:inditas]


def test_az_induloablak_lepesen_is_ot_masodperces_fokapu_van():
    workflow = (_GYOKER / ".github/workflows/package.yml").read_text(encoding="utf-8")
    indulo = workflow.split("- name: Mérés — az indulóablak megjelenése", 1)[1]
    assert "--indulo-hatar-ms 1000" in indulo
    assert "--hatar-mp 5" in indulo
