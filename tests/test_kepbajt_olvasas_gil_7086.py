"""A képfájl bájtjainak olvasása nem foghatja a GIL-t (#7086).

A tulajdonos hálózati mappán görgetett, és a program lefagyott, amint be nem
töltött bélyegképek kerültek a látótérbe. Lassított fájlrendszeren mérve: a
négy bélyegkép-szál a `np.fromfile`-ban olvasta a hálózati fájlt, és a
`np.fromfile` olvasás közben fogja a GIL-t, ezért a fő szál (a felület) addig
nem futhatott. Egyetlen lassú fájlon a fő szál 130 ms-ig esett ki, sima
`open().read()`-del 16 ms-ig.
"""

from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path

import pytest

from picasapy.cvimage import read_image_bytes

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.mark.skipif(os.name != "posix", reason="elnevezett cső (FIFO) csak POSIX-on van")
def test_lassu_forras_olvasasa_kozben_a_fo_szal_fut(tmp_path):
    cso = tmp_path / "lassu.jpg"
    os.mkfifo(cso)
    adat = b"\xff\xd8" + b"x" * 4096

    def iro():
        with open(cso, "wb") as f:
            time.sleep(1.0)  # a hálózati fájl ennyi ideig késlekedik
            f.write(adat)

    eredmeny = {}

    def olvaso():
        eredmeny["payload"] = read_image_bytes(cso)

    threading.Thread(target=iro, daemon=True).start()
    t = threading.Thread(target=olvaso, daemon=True)
    t.start()

    utemek = 0
    hatarido = time.monotonic() + 10.0
    while t.is_alive() and time.monotonic() < hatarido:
        time.sleep(0.01)
        utemek += 1
    t.join(10.0)

    assert not t.is_alive(), "az olvasás nem fejeződött be"
    assert eredmeny["payload"] is not None
    assert bytes(eredmeny["payload"]) == adat
    # 1 s várakozás alatt 10 ms-os ütemmel legalább ~50 ütem kell, ha a fő
    # szál közben futhat; GIL-t fogó olvasásnál alig néhány
    assert utemek >= 50, f"a fő szál az olvasás alatt csak {utemek}-szor futott"


def test_ures_es_hianyzo_fajl_none(tmp_path):
    ures = tmp_path / "ures.jpg"
    ures.write_bytes(b"")
    assert read_image_bytes(ures) is None
    assert read_image_bytes(tmp_path / "nincs.jpg") is None


def test_a_forraskodban_nincs_np_fromfile():
    """Őr: képbájtot csak GIL-t elengedő olvasással szabad betölteni."""
    talalat = []
    for ut in SRC.rglob("*.py"):
        for n, sor in enumerate(ut.read_text(encoding="utf-8").splitlines(), 1):
            kod = sor.split("#", 1)[0]
            if re.search(r"\b(np|numpy)\.fromfile\s*\(", kod):
                talalat.append(f"{ut.relative_to(SRC)}:{n}")
    assert not talalat, (
        "np.fromfile olvasás közben fogja a GIL-t, hálózati fájlon a felület "
        f"megáll (#7086); használd a cvimage.read_image_bytes-t: {talalat}"
    )
