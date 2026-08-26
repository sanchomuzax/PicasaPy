"""Az arcfelismerő modell LETÖLTÉSE — épség-ellenőrzéssel (#1496).

## A lelet, ami a jegyet szülte

A `download_model()` a termékkódból SEHONNAN nem hívódott (két külön alakú
kereséssel igazolva: `grep -rn "download_model(" src/` és
`ast-grep -p 'download_model($$$)' -l py src/` — mindkettő csak a két
definíciót adta), a `~/.local/share/picasapy/models/` mappa pedig nem is
létezett. A felhasználónak kézzel kellett volna ONNX-fájlt másolnia.

## Miért ez a fájl a legfontosabb őre a jegynek

A régi letöltő **semmit nem ellenőrzött**: amit a szerver adott, azt
kiírta. Ez itt nem elméleti kockázat. Az OpenCV Zoo a modelleket **Git
LFS**-ben tárolja, és a `raw.githubusercontent.com` az LFS-fájlokra nem a
modellt, hanem egy **131 bájtos szövegmutatót** ad vissza (2026-08-26-i
mérés: `content-length: 131`, míg a `media.githubusercontent.com`-on
232 589). Egy elgépelt vagy elavult URL tehát némán egy szövegfájlt tett
volna a modell helyére — vagy egy megszakadt letöltés egy fél modellt,
amivel a felismerés **rosszul**, de látszólag működne.

Ezért minden alább következő állítás közül a `TestCsonkaEsHamisFajl` a
lényeg: ha az bukik, az „ellenőrizzük az épséget" mondat üres.

## Hálózat SEHOL

A tesztek egy `127.0.0.1`-en futó, eldobható HTTP-kiszolgálót címeznek
(loopback, nem hálózat) — a CI-nek hálózat nélkül is zöldnek kell lennie.
"""

from __future__ import annotations

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from picasapy.faces.model_download import (
    DEFAULT_MODEL_BASE_URL,
    DETECTOR_SPEC,
    EMBEDDER_SPEC,
    MODEL_BASE_URL_ENV_VAR,
    MODEL_SPECS,
    STATUS_CANCELLED,
    STATUS_CORRUPT,
    STATUS_NETWORK,
    STATUS_OK,
    download_missing,
    download_spec,
    missing_specs,
    model_base_url,
    model_url,
    total_missing_bytes,
)

#: Az LFS-mutató pontos alakja — ezt adja a `raw.githubusercontent.com` a
#: modellfájl HELYETT (2026-08-26, `gh api …/contents/…` base64-ből
#: dekódolva). Szó szerint ez a 131 bájt.
LFS_MUTATO = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4\n"
    b"size 232589\n"
)


class _Kiszolgalo:
    """Eldobható, loopback HTTP-kiszolgáló — útvonalanként nyers bájtokkal.

    A `lassito` esemény a válasz KÖZEPÉN várakoztat: így a megszakítás egy
    ténylegesen FUTÓ letöltést szakít meg, nem egy be sem indultat."""

    def __init__(self, tartalom: dict[str, bytes], lassito: threading.Event | None = None):
        self.tartalom = tartalom
        self.lassito = lassito
        self.keresesek: list[str] = []
        kiszolgalo = self

        class _Kezelo(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802 — a BaseHTTPRequestHandler neve
                kiszolgalo.keresesek.append(self.path)
                payload = kiszolgalo.tartalom.get(self.path)
                if payload is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                felezo = max(1, len(payload) // 2)
                self.wfile.write(payload[:felezo])
                self.wfile.flush()
                if kiszolgalo.lassito is not None:
                    kiszolgalo.lassito.wait(10.0)
                self.wfile.write(payload[felezo:])

            def log_message(self, *args):  # a teszt kimenetét ne szemetelje
                return

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Kezelo)
        self._httpd.daemon_threads = True
        self._szal = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self) -> _Kiszolgalo:
        self._szal.start()
        return self

    def __exit__(self, *_):
        self._httpd.shutdown()
        self._httpd.server_close()
        self._szal.join(5.0)

    @property
    def alap_url(self) -> str:
        cim, port = self._httpd.server_address[:2]
        return f"http://{cim}:{port}"


def _valodi_meretu_tartalom(spec) -> bytes:
    """A spec méretével EGYEZŐ, de tetszőleges tartalom — a sha256 nem stimmel."""
    return b"x" * spec.size_bytes


class TestSpecek:
    """A rögzített értékek — enélkül az ellenőrzés nem tud mihez mérni."""

    def test_mindket_modellnek_van_merete_es_ellenorzoosszege(self):
        assert len(MODEL_SPECS) == 2
        for spec in MODEL_SPECS:
            assert spec.size_bytes > 0, spec.filename
            assert len(spec.sha256) == 64, spec.filename
            assert set(spec.sha256) <= set("0123456789abcdef"), spec.filename
            assert spec.license_name, spec.filename

    def test_a_rogzitett_ertekek_az_upstream_LFS_mutatobol_valok(self):
        """A 2026-08-26-i mérés (`gh api repos/opencv/opencv_zoo/contents/…`)
        pontos értékei. Ha az upstream fájlt kicserélik, ez a teszt NEM
        fogja megmondani — de azt megakadályozza, hogy az értékek
        véletlenül, egy szerkesztés melléktermékeként elcsússzanak."""
        assert DETECTOR_SPEC.size_bytes == 232589
        assert DETECTOR_SPEC.sha256 == (
            "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
        )
        assert DETECTOR_SPEC.license_name == "MIT"
        assert EMBEDDER_SPEC.size_bytes == 38696353
        assert EMBEDDER_SPEC.sha256 == (
            "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
        )
        assert EMBEDDER_SPEC.license_name == "Apache-2.0"

    def test_a_forras_url_kornyezeti_valtozoval_felulirhato(self, monkeypatch):
        """A beállítható forrás — a tesztek is ezen az egy fogantyún át
        terelik a letöltést a helyi kiszolgálóra."""
        monkeypatch.delenv(MODEL_BASE_URL_ENV_VAR, raising=False)
        assert model_base_url() == DEFAULT_MODEL_BASE_URL
        assert model_url(DETECTOR_SPEC).startswith(DEFAULT_MODEL_BASE_URL)

        monkeypatch.setenv(MODEL_BASE_URL_ENV_VAR, "http://127.0.0.1:9/m")
        assert model_url(DETECTOR_SPEC) == (
            "http://127.0.0.1:9/m/" + DETECTOR_SPEC.relative_url
        )

    def test_a_zaro_perjel_nem_duplazodik(self, monkeypatch):
        monkeypatch.setenv(MODEL_BASE_URL_ENV_VAR, "http://127.0.0.1:9/m/")
        assert "//" not in model_url(DETECTOR_SPEC).removeprefix("http://")


class TestSikeresLetoltes:
    def test_a_fajl_a_helyere_kerul_es_a_haladas_vegigfut(self, tmp_path):
        payload = b"ONNX-nek-latszo-tartalom" * 40
        spec = DETECTOR_SPEC.masolat(
            size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
        )
        cel = tmp_path / spec.filename
        haladas: list[tuple[int, int]] = []

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            eredmeny = download_spec(
                spec,
                dest=cel,
                base_url=kiszolgalo.alap_url,
                progress=lambda kesz, ossz: haladas.append((kesz, ossz)),
                timeout=5.0,
            )

        assert eredmeny.status == STATUS_OK, eredmeny.detail
        assert eredmeny.ok is True
        assert cel.read_bytes() == payload
        assert haladas, "a letöltés nem jelzett haladást"
        assert haladas[-1] == (len(payload), len(payload))
        assert [k for k, _ in haladas] == sorted(k for k, _ in haladas)

    def test_reszlegesen_letoltott_part_fajl_nem_marad_hatra(self, tmp_path):
        payload = b"teljes tartalom"
        spec = DETECTOR_SPEC.masolat(
            size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
        )
        cel = tmp_path / spec.filename
        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            download_spec(spec, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0)
        assert list(tmp_path.iterdir()) == [cel], "ideiglenes fájl maradt a mappában"


class TestCsonkaEsHamisFajl:
    """⚠️ A jegy LEGFONTOSABB pontja: csonka modellel a felismerés némán
    ROSSZUL működne. Ha ezek az állítások eltűnnek, az „ellenőrizzük"
    üres ígéret."""

    def test_csonka_fajlra_BUKIK_es_nem_ir_semmit(self, tmp_path):
        """A szerver kevesebbet ad, mint amennyit a spec ígér."""
        payload = b"csak-a-fele"
        spec = DETECTOR_SPEC.masolat(
            size_bytes=len(payload) + 5_000,
            sha256=hashlib.sha256(payload).hexdigest(),
        )
        cel = tmp_path / spec.filename

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            eredmeny = download_spec(
                spec, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert eredmeny.status == STATUS_CORRUPT, eredmeny.detail
        assert eredmeny.ok is False
        assert not cel.exists(), "a csonka fájl a modell helyére került"
        assert list(tmp_path.iterdir()) == []

    def test_hosszabb_fajlra_BUKIK(self, tmp_path):
        payload = b"tul-hosszu-valasz" * 50
        spec = DETECTOR_SPEC.masolat(
            size_bytes=10, sha256=hashlib.sha256(payload).hexdigest()
        )
        cel = tmp_path / spec.filename

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            eredmeny = download_spec(
                spec, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert eredmeny.status == STATUS_CORRUPT, eredmeny.detail
        assert not cel.exists()

    def test_jo_meret_de_rossz_tartalom_BUKIK(self, tmp_path):
        """A méret önmagában kevés: az ellenőrzőösszegnek is fognia kell."""
        spec = DETECTOR_SPEC.masolat(size_bytes=64, sha256="0" * 64)
        payload = _valodi_meretu_tartalom(spec)
        cel = tmp_path / spec.filename

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            eredmeny = download_spec(
                spec, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert eredmeny.status == STATUS_CORRUPT, eredmeny.detail
        assert not cel.exists()

    def test_a_git_LFS_szovegmutato_NEM_kerul_a_modell_helyere(self, tmp_path):
        """A valódi, mért csapda: 131 bájt szöveg a 232 589 bájtos modell
        helyett (`raw.githubusercontent.com`)."""
        cel = tmp_path / DETECTOR_SPEC.filename

        with _Kiszolgalo({"/" + DETECTOR_SPEC.relative_url: LFS_MUTATO}) as kiszolgalo:
            eredmeny = download_spec(
                DETECTOR_SPEC, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert eredmeny.status == STATUS_CORRUPT, eredmeny.detail
        assert not cel.exists()

    def test_a_meglevo_jo_fajlt_a_bukott_letoltes_NEM_rontja_el(self, tmp_path):
        """Újratöltésnél a régi fájl a helyén marad, ha az új hibás."""
        cel = tmp_path / DETECTOR_SPEC.filename
        cel.write_bytes(b"a regi, mukodo modell")
        spec = DETECTOR_SPEC.masolat(size_bytes=999_999, sha256="1" * 64)

        with _Kiszolgalo({"/" + spec.relative_url: b"rossz"}) as kiszolgalo:
            eredmeny = download_spec(
                spec, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert eredmeny.ok is False
        assert cel.read_bytes() == b"a regi, mukodo modell"


class TestHalozatNelkul:
    """Néma bukás SEHOL — a hívó érthető okot kap."""

    def test_elerhetetlen_kiszolgalo_eseten_nem_dob_kivetelt(self, tmp_path):
        cel = tmp_path / DETECTOR_SPEC.filename
        eredmeny = download_spec(
            DETECTOR_SPEC,
            dest=cel,
            base_url="http://127.0.0.1:1/nincs-ilyen-szolgaltatas",
            timeout=1.0,
        )
        assert eredmeny.status == STATUS_NETWORK
        assert eredmeny.detail, "a hálózati hiba oka nincs megnevezve"
        assert not cel.exists()

    def test_404_eseten_is_halozati_hiba(self, tmp_path):
        cel = tmp_path / DETECTOR_SPEC.filename
        with _Kiszolgalo({}) as kiszolgalo:
            eredmeny = download_spec(
                DETECTOR_SPEC, dest=cel, base_url=kiszolgalo.alap_url, timeout=5.0
            )
        assert eredmeny.status == STATUS_NETWORK
        assert not cel.exists()


class TestMegszakitas:
    def test_a_futo_letoltes_megszakithato(self, tmp_path):
        payload = b"hosszu-tartalom" * 500
        spec = DETECTOR_SPEC.masolat(
            size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
        )
        cel = tmp_path / spec.filename
        lassito = threading.Event()
        megszakito = threading.Event()

        def _elso_haladasra_megszakit(kesz, _ossz):
            if kesz > 0:
                megszakito.set()
                lassito.set()

        with _Kiszolgalo({"/" + spec.relative_url: payload}, lassito) as kiszolgalo:
            eredmeny = download_spec(
                spec,
                dest=cel,
                base_url=kiszolgalo.alap_url,
                cancel=megszakito,
                progress=_elso_haladasra_megszakit,
                # Apró darabok: így az első beolvasás után VAN még mit
                # olvasni, tehát a megszakítás valódi, FUTÓ letöltést
                # szakít meg (nagy darabbal a `read()` a teljes választ
                # bevárná, és a megszakítás sosem érne oda).
                chunk_size=64,
                timeout=5.0,
            )

        assert eredmeny.status == STATUS_CANCELLED
        assert not cel.exists()
        assert list(tmp_path.iterdir()) == []

    def test_eleve_beallitott_megszakitas_eseten_el_sem_indul(self, tmp_path):
        megszakito = threading.Event()
        megszakito.set()
        with _Kiszolgalo({"/" + DETECTOR_SPEC.relative_url: b"barmi"}) as kiszolgalo:
            eredmeny = download_spec(
                DETECTOR_SPEC,
                dest=tmp_path / DETECTOR_SPEC.filename,
                base_url=kiszolgalo.alap_url,
                cancel=megszakito,
                timeout=5.0,
            )
            assert kiszolgalo.keresesek == [], "megszakítás után is volt hálózati kérés"
        assert eredmeny.status == STATUS_CANCELLED


class TestHianyzoModellek:
    """`missing_specs()` — a felület ebből tudja, van-e mit letölteni."""

    def test_ures_mappaban_mindket_modell_hianyzik(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        assert {spec.key for spec in missing_specs()} == {"detector", "embedder"}
        assert total_missing_bytes() == (
            DETECTOR_SPEC.size_bytes + EMBEDDER_SPEC.size_bytes
        )

    def test_a_meglevo_modell_kimarad(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        mappa = tmp_path / "picasapy" / "models"
        mappa.mkdir(parents=True)
        (mappa / DETECTOR_SPEC.filename).write_bytes(b"mar-megvan")
        assert {spec.key for spec in missing_specs()} == {"embedder"}
        assert total_missing_bytes() == EMBEDDER_SPEC.size_bytes


class TestEgyuttesLetoltes:
    """`download_missing()` — a felület EGY gombja mindkét modellt hozza."""

    def test_mindket_modell_letoltodik_es_a_haladas_osszesitett(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)

        tartalom: dict[str, bytes] = {}
        specek = []
        for eredeti in MODEL_SPECS:
            payload = (eredeti.key.encode() + b"-tartalom") * 7
            spec = eredeti.masolat(
                size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
            )
            specek.append(spec)
            tartalom["/" + spec.relative_url] = payload
        monkeypatch.setattr(
            "picasapy.faces.model_download.MODEL_SPECS", tuple(specek)
        )
        osszes = sum(spec.size_bytes for spec in specek)
        haladas: list[tuple[int, int]] = []

        with _Kiszolgalo(tartalom) as kiszolgalo:
            eredmenyek = download_missing(
                base_url=kiszolgalo.alap_url,
                progress=lambda kesz, ossz: haladas.append((kesz, ossz)),
                timeout=5.0,
            )

        assert [e.status for e in eredmenyek] == [STATUS_OK, STATUS_OK]
        mappa = tmp_path / "picasapy" / "models"
        for spec in specek:
            assert (mappa / spec.filename).is_file()
        assert haladas[-1] == (osszes, osszes)
        assert [k for k, _ in haladas] == sorted(k for k, _ in haladas), (
            "az összesített haladás visszaugrott a második modellnél"
        )

    def test_az_elso_modell_bukasa_utan_a_masodik_meg_sem_probalkozik(
        self, tmp_path, monkeypatch
    ):
        """Hálózat nélkül ne várjunk kétszer időtúllépést a felhasználóra."""
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        eredmenyek = download_missing(
            base_url="http://127.0.0.1:1/nincs", timeout=1.0
        )
        assert len(eredmenyek) == 1
        assert eredmenyek[0].status == STATUS_NETWORK


@pytest.mark.parametrize("spec", MODEL_SPECS, ids=lambda s: s.key)
def test_minden_spec_ugyanabba_a_mappaba_tolt(spec, tmp_path, monkeypatch):
    """A két modell UGYANOTT lakik — a felületi üzenet egy mappát nevez meg."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert spec.default_path().parent == tmp_path / "picasapy" / "models"
