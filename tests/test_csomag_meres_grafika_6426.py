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


def _egy_inditas_kornyezete(monkeypatch, tmp_path, env):
    monkeypatch.setattr(
        ido_modul,
        "_profil",
        lambda *_args, **_kwargs: (env, tmp_path / "library"),
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
    return inditasok[0]


def test_alapertelmezetten_kikapcsolt_a_nehez_qt_naplozas(monkeypatch, tmp_path):
    monkeypatch.delenv("PICASAPY_MERES_QT_NAPLO", raising=False)
    env = _egy_inditas_kornyezete(
        monkeypatch,
        tmp_path,
        {
            "QT_LOGGING_RULES": (
                "*.debug=false;qt.qml.diskcache.debug=true;"
                "qt.scenegraph.general.debug=true;qt.rhi.general.debug=true"
            ),
            "QT_FORCE_STDERR_LOGGING": "1",
            "QSG_INFO": "1",
        },
    )

    assert env["QT_LOGGING_RULES"] == "*.debug=false"
    assert "QT_FORCE_STDERR_LOGGING" not in env
    assert "QSG_INFO" not in env

    monkeypatch.setenv("PICASAPY_MERES_QT_NAPLO", "1")
    env = _egy_inditas_kornyezete(
        monkeypatch, tmp_path, {"QT_LOGGING_RULES": "*.debug=false"}
    )
    szabalyok = env["QT_LOGGING_RULES"]
    assert szabalyok.startswith("*.debug=false;")
    assert "qt.qml.diskcache.debug=true" in szabalyok
    assert "qt.scenegraph.general.debug=true" in szabalyok
    assert "qt.rhi.general.debug=true" in szabalyok
    assert env["QT_FORCE_STDERR_LOGGING"] == "1"
    assert env["QSG_INFO"] == "1"

    workflow = (_GYOKER / ".github/workflows/package.yml").read_text(
        encoding="utf-8"
    )
    assert "PICASAPY_MERES_QT_NAPLO" not in workflow
    meres = (_GYOKER / "packaging/windows/csomag_meres_ido.py").read_text(
        encoding="utf-8"
    )
    assert "PICASAPY_MERES_QT_NAPLO" in meres


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


class _KeszFolyamat:
    returncode = 0
    pid = 1

    def communicate(self, timeout=None):
        return (b"qt.rhi.general: Created D3D11 device\n", b"")


def test_a_valodi_ablak_jelzo_es_a_kimenet_eljut_a_jelentesig(tmp_path, monkeypatch):
    """A Package-mérésen a jelentés üres maradt: a `_bevar` nem adta tovább a
    `valodi_ablak` jelzőt, ezért a diagnosztika egyetlen sort sem írt."""
    monkeypatch.setattr(ido_modul, "_naplo_sorai", lambda _g: [])
    futas = {"folyamat": _KeszFolyamat(), "indult": datetime.now(timezone.utc), "kezdet": 0.0,
             "korabbi": 0, "gyoker": tmp_path, "indulo_hatar_ms": None,
             "indulo_kep_kotelezo": False, "valodi_ablak": True}
    eredmeny = ido_modul._bevar(futas)
    assert eredmeny["valodi_ablak"] is True
    sorok = ido_modul._indulasi_grafikai_jelentes(1, eredmeny)
    assert any("grafikus háttér" in s for s in sorok)


def test_valodi_ablaknal_a_qt_naplo_a_kimenetre_kerul(tmp_path, monkeypatch):
    """Windowson az ablakos program a Qt naplóját OutputDebugString-re írja;
    a `QT_FORCE_STDERR_LOGGING=1` nélkül a mérés semmit nem lát belőle."""
    elkapott = {}

    def _popen(parancs, *, env, **_kw):
        elkapott.update(env)
        return _KeszFolyamat()

    monkeypatch.setattr(ido_modul, "_popen", _popen)
    monkeypatch.setattr(ido_modul, "_naplo_sorai", lambda _g: [])
    monkeypatch.setenv("PICASAPY_MERES_QT_NAPLO", "1")
    ido_modul._egy_inditas(["x.exe"], tmp_path, ablakkal=True)
    assert elkapott["QT_FORCE_STDERR_LOGGING"] == "1"
    assert elkapott["QSG_INFO"] == "1"


def test_a_qt_naplo_nyers_relevans_sorai_kiirodnak():
    kimenet = "valami\nqt.rhi.general: Created D3D11 device\nQSG: threaded render loop\nmás\n"
    assert ido_modul.qt_naplo_sorok(kimenet) == [
        "qt.rhi.general: Created D3D11 device", "QSG: threaded render loop"]


class _LassanKilepoFolyamat:
    """`communicate` az első néhány hívásra még fut (időtúllépés)."""

    pid = 4242
    returncode = 0

    def __init__(self, futo_korok: int):
        self.maradek = futo_korok

    def communicate(self, timeout=None):
        import subprocess

        if self.maradek > 0:
            self.maradek -= 1
            raise subprocess.TimeoutExpired("PicasaPy.exe", timeout)
        return (b"", b"")


def _splash_futas(tmp_path, folyamat):
    return {"folyamat": folyamat, "indult": datetime.now(timezone.utc), "kezdet": 0.0,
            "korabbi": 0, "gyoker": tmp_path, "indulo_hatar_ms": 1000,
            "indulo_kep_kotelezo": True, "valodi_ablak": True}


def test_a_splash_kepet_addig_probalja_amig_ki_nem_rajzolodik(tmp_path, monkeypatch):
    """A splash első felsorolásakor az ablak még nincs kirajzolva; egyetlen
    próbával a gyors indulásoknál a mérés hamisan piros lett (#6426)."""
    monkeypatch.setattr(ido_modul, "_naplo_sorai", lambda _g: [])
    monkeypatch.setattr(ido_modul, "_ablakikonok",
                        lambda _pid: {7: {"cim": "PicasaPy Startup"}}, raising=False)
    probak = []

    def kep(hwnd):
        probak.append(hwnd)
        if len(probak) < 3:
            return b"rossz", None, "a renderelt indulóképen nincs fehér kártya logóval"
        return b"png", (668, 263, 45), None

    monkeypatch.setattr(ido_modul, "_induloablak_kepe", kep, raising=False)
    eredmeny = ido_modul._bevar(_splash_futas(tmp_path, _LassanKilepoFolyamat(10)))
    assert len(probak) == 3
    assert eredmeny["indulo_kep"] == b"png"
    assert eredmeny["indulo_kep_hiba"] is None


def test_a_splash_eltunese_utan_nem_probalkozik_tovabb(tmp_path, monkeypatch):
    monkeypatch.setattr(ido_modul, "_naplo_sorai", lambda _g: [])
    ablakok = [{7: {"cim": "PicasaPy Startup"}}, {7: {"cim": "PicasaPy Startup"}}]
    monkeypatch.setattr(ido_modul, "_ablakikonok",
                        lambda _pid: ablakok.pop(0) if ablakok else {8: {"cim": "PicasaPy"}},
                        raising=False)
    probak = []

    def kep(hwnd):
        probak.append(hwnd)
        return b"rossz", None, "a renderelt indulóképen nincs fehér kártya logóval"

    monkeypatch.setattr(ido_modul, "_induloablak_kepe", kep, raising=False)
    eredmeny = ido_modul._bevar(_splash_futas(tmp_path, _LassanKilepoFolyamat(10)))
    assert len(probak) == 2
    # a hibás kép is megmarad, hogy a jelentés megmutathassa, mi látszott
    assert eredmeny["indulo_kep"] == b"rossz"
    assert eredmeny["indulo_kep_info"] is None
    assert eredmeny["indulo_kep_hiba"] == "a renderelt indulóképen nincs fehér kártya logóval"


def test_a_splash_kepe_a_reteges_ablakot_is_rogziti():
    """Az áttetsző splash réteges (layered) ablak; a Pillow alapértelmezésben
    kihagyja, így a mérő a mögötte levő főablakot fényképezte (CI-kép, #6426)."""
    import ast
    import inspect

    windows_modul = importlib.import_module("csomag_meres_windows")
    fa = ast.parse(inspect.getsource(windows_modul._induloablak_kepe))
    hivasok = [
        csomopont
        for csomopont in ast.walk(fa)
        if isinstance(csomopont, ast.Call)
        and isinstance(csomopont.func, ast.Attribute)
        and csomopont.func.attr == "grab"
    ]
    assert hivasok, "a splash képe nem ImageGrab.grab-bal készül"
    for hivas in hivasok:
        kapcsolok = {k.arg: k.value for k in hivas.keywords}
        assert "include_layered_windows" in kapcsolok
        assert getattr(kapcsolok["include_layered_windows"], "value", None) is True
