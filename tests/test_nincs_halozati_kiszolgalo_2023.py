"""A termékben NINCS hallgatózó hálózati kiszolgáló (#2023, ADR-011).

Az eredeti Picasa 3 saját HTTP/WebDAV-kiszolgálót futtat (14 végpont, köztük
egy **adatbázis-böngésző** lap), a helyi hálózaton hirdeti a gépnevet és a
felhasználónevet, és regisztrál egy `picasa://` URL-sémát, aminek egyik ága
**külső URL-ről tölt be bővítményt**. A PicasaPy ezt **szándékosan nem építi
meg** — az indoklás: `docs/decisions/nincs-halozati-kiszolgalo.md`.

## Miért teszt, és nem csak döntés

Egy „nem építjük meg" döntést semmi nem tart be, ha nincs mérője: egy későbbi
kör jóhiszeműen „fehér foltként" találna rá, és elkezdené megvalósítani. A
döntés ezért **kapuval** jár (a projekt szabálya: minden új szabály mellé
kapu vagy mérő).

## ⚠️ Amit ez NEM tilt

- a **kimenő** hálózati műveleteket (e-mail átadása, HTTP-kérés indítása):
  a döntés a BEÉRKEZŐ oldalról szól;
- a `tools/`, `scripts/`, `tests/` alatti ideiglenes kiszolgálókat: a kapu a
  **terméket** (`src/`) köti;
- a `socket` modul minden használatát: egy kimenő kapcsolat (`connect`) nem
  hallgatózás. A minta ezért `bind(`/`listen(`-re szűkít, nem az importra.
"""

from __future__ import annotations

import re
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]

#: A hallgatózás bevett alakjai. Mindegyik a BEÉRKEZŐ oldalt jelenti.
_MINTAK: tuple[tuple[str, str], ...] = (
    (r"\.bind\s*\(", "socket.bind() — hallgatózó kapcsolódási pont"),
    (r"\.listen\s*\(", "socket.listen() — hallgatózás"),
    (r"\bHTTPServer\b", "http.server.HTTPServer"),
    (r"\bThreadingHTTPServer\b", "http.server.ThreadingHTTPServer"),
    (r"\bBaseHTTPRequestHandler\b", "HTTP-kéréskezelő"),
    (r"\bsocketserver\b", "socketserver"),
    (r"\bimport\s+aiohttp\b|\bfrom\s+aiohttp\b", "aiohttp (kiszolgáló-keretrendszer)"),
    (r"\bimport\s+flask\b|\bfrom\s+flask\b", "flask"),
    (r"\bimport\s+uvicorn\b|\bfrom\s+uvicorn\b", "uvicorn"),
    (r"\bQTcpServer\b|\bQLocalServer\b|\bQHttpServer\b", "Qt-kiszolgáló osztály"),
    # URL-séma-regisztráció: a `picasa://` párja nálunk `picasapy://` lenne
    (r"x-scheme-handler/", "URL-séma-regisztráció (.desktop MIME-kezelő)"),
    (r"picasapy://", "saját URL-séma"),
)

#: Indokolt kivételek: `(fájl, minta-leírás)`. A lista SZÁNDÉKOSAN zárt — aki
#: felvesz ide valamit, a döntést módosítja (ADR-011), nem a tesztet igazítja.
_KIVETELEK: set[tuple[str, str]] = set()


def leletek(gyoker: Path | None = None) -> list[str]:
    """A `src/` alatti hallgatózás-jelek — a kapu és a próbái is ezt hívják."""
    gyoker = gyoker or GYOKER
    talalatok: list[str] = []
    for ut in sorted((gyoker / "src").rglob("*.py")):
        sorok = ut.read_text(encoding="utf-8", errors="replace").splitlines()
        for szam, sor in enumerate(sorok, start=1):
            # a kommentek és a docstring-sorok NEM leletek: a döntést épp
            # magyarázni kell tudni a kódban is (a `#2023` hivatkozásokat is
            # ide értve)
            csupasz = sor.strip()
            if csupasz.startswith("#"):
                continue
            for minta, leiras in _MINTAK:
                if not re.search(minta, sor):
                    continue
                relativ = ut.relative_to(gyoker).as_posix()
                if (relativ, leiras) in _KIVETELEK:
                    continue
                talalatok.append(f"{relativ}:{szam} — {leiras}: {csupasz[:70]}")
    return talalatok


class TestNincsKiszolgalo:
    def test_a_src_alatt_nincs_hallgatozo_socket(self) -> None:
        assert not leletek(), (
            "#2023: hallgatózó hálózati felület került a termékbe. Ez az "
            "ADR-011 (docs/decisions/nincs-halozati-kiszolgalo.md) szándékos "
            "eltérése az eredetitől — ha a döntés megváltozott, ELŐBB az ADR-t "
            "kell módosítani, nem a tesztet:\n  " + "\n  ".join(leletek())
        )


class TestAKapuMagaIsMukodik:
    """Ismert pozitív és ismert negatív: a nulla lelet csak akkor jelent
    valamit, ha a kapu egy VALÓDI szabálysértést fel is ismer."""

    def test_megfogja_a_hallgatozo_kiszolgalot(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "picasapy").mkdir(parents=True)
        (tmp_path / "src" / "picasapy" / "web.py").write_text(
            "from http.server import HTTPServer\n"
            "\n"
            "def indit():\n"
            "    kiszolgalo = HTTPServer((\"\", 8080), None)\n"
            "    kiszolgalo.serve_forever()\n",
            encoding="utf-8",
        )
        talalatok = leletek(tmp_path)
        assert talalatok, "a kapu nem ismerte fel a HTTPServert"
        assert any("HTTPServer" in t for t in talalatok)

    def test_megfogja_a_bind_hivast(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "picasapy").mkdir(parents=True)
        (tmp_path / "src" / "picasapy" / "lan.py").write_text(
            "import socket\n"
            "\n"
            "def hirdet():\n"
            "    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
            "    s.bind((\"0.0.0.0\", 6666))\n",
            encoding="utf-8",
        )
        assert any("bind()" in t for t in leletek(tmp_path))

    def test_a_KIMENO_kapcsolat_NEM_lelet(self, tmp_path: Path) -> None:
        """A `connect` és a `socket` import nem hallgatózás — a döntés a
        beérkező oldalról szól, és egy túl tág kapu a jogos kimenő
        műveleteket is megfogná."""
        (tmp_path / "src" / "picasapy").mkdir(parents=True)
        (tmp_path / "src" / "picasapy" / "kimeno.py").write_text(
            "import socket\n"
            "\n"
            "def kuld(adat):\n"
            "    s = socket.create_connection((\"pelda.hu\", 443))\n"
            "    s.sendall(adat)\n",
            encoding="utf-8",
        )
        assert leletek(tmp_path) == []

    def test_a_kommentben_emlitett_minta_NEM_lelet(self, tmp_path: Path) -> None:
        """A döntést magyarázni kell tudni a kódban is."""
        (tmp_path / "src" / "picasapy").mkdir(parents=True)
        (tmp_path / "src" / "picasapy" / "magyarazat.py").write_text(
            "# Az eredeti HTTPServer-t futtat, mi NEM (ADR-011, #2023).\n"
            "def semmi():\n"
            "    return None\n",
            encoding="utf-8",
        )
        assert leletek(tmp_path) == []


class TestADontesLapMEGVAN:
    """A kapu és a döntés együtt érnek valamit: ha a lap eltűnik, a teszt
    hibaüzenete egy nem létező fájlra hivatkozna."""

    def test_az_ADR_a_helyen_van(self) -> None:
        lap = GYOKER / "docs" / "decisions" / "nincs-halozati-kiszolgalo.md"
        assert lap.is_file(), "az ADR-011 lap hiányzik"
        szoveg = lap.read_text(encoding="utf-8")
        assert "#2023" in szoveg
        assert "picasa://" in szoveg, "a mért felület nevesítve legyen"

    def test_a_feature_map_NEM_CELKENT_jeloli(self) -> None:
        terkep = (GYOKER / "docs" / "specs" / "feature-map.md").read_text(
            encoding="utf-8"
        )
        nem_cel = terkep.split("## Nem cél")[-1]
        assert "#2023" in nem_cel, (
            "a beérkező hálózati felület nincs a „Nem cél” szakaszban — a "
            "lefedettségi rangsorban újra fehér foltként kerülne elő"
        )
