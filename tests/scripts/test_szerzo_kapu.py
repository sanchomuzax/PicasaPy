"""A szerző-kapu FOGA — a kapu SAJÁT biztonsági tulajdonságait állítja.

Egy ilyen kapunál nem az a kockázat, hogy rosszul dönt, hanem hogy **maga
válik támadási felületté**. Két klasszikus rés van, és mindkettőt itt zárjuk:

1. ``pull_request_target`` — forkból érkező PR-nél is titkokat és írásra
   jogosult tokent ad. Ez az ellátásilánc-támadások bevett belépője.
2. ``actions/checkout`` — ha a kapu kicsekkolja a PR kódját, akkor a
   *vizsgált* kód fut a *vizsgáló* jogaival.

A kapu ezért csak az esemény adatait olvassa. Ha valaki egyszer beleírná
bármelyiket, ez a teszt elbukik.
"""
from __future__ import annotations

import pathlib
import unittest

GYOKER = pathlib.Path(__file__).resolve().parents[2]
KAPU = GYOKER / ".github" / "workflows" / "szerzo-kapu.yml"


class SzerzoKapuTeszt(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(KAPU.is_file(), f"hiányzik a szerző-kapu: {KAPU}")
        self.szoveg = KAPU.read_text(encoding="utf-8")
        # A KOMMENTEK NÉLKÜLI szöveg. A fájl magyarázata SZÁNDÉKOSAN kimondja,
        # mit nem használunk (`pull_request_target`) és miért — ha a nyers
        # szövegben keresnénk, a saját magyarázatunk buktatná a tesztet, és a
        # javítás a magyarázat törlése lenne. A tényleges beállítás számít.
        self.hatasos = "\n".join(
            s for s in self.szoveg.splitlines() if not s.lstrip().startswith("#")
        )

    def test_nem_hasznal_pull_request_targetet(self) -> None:
        self.assertNotIn(
            "pull_request_target", self.hatasos,
            "a `pull_request_target` forkból is titkokat adna — a kapu maga "
            "válna az ellátásilánc-támadás belépőjévé",
        )

    def test_nem_csekkolja_ki_a_pr_kodjat(self) -> None:
        self.assertNotIn(
            "actions/checkout", self.hatasos,
            "ha a kapu kicsekkolja a PR kódját, a VIZSGÁLT kód fut a VIZSGÁLÓ "
            "jogaival — a kapu csak az esemény adatait olvashatja",
        )

    def test_a_komment_szures_nem_vakitja_meg_az_ort(self) -> None:
        """A foga: magvetett hiba a TÉNYLEGES beállításban buktassa a tesztet."""
        magvetett = self.szoveg.replace(
            "on:\n  pull_request:", "on:\n  pull_request_target:"
        )
        hatasos = "\n".join(
            s for s in magvetett.splitlines() if not s.lstrip().startswith("#")
        )
        self.assertIn("pull_request_target", hatasos,
                      "a komment-szűrés a valódi beállítást is elnyelte volna")

    def test_csak_olvaso_jogot_ker(self) -> None:
        self.assertIn("contents: read", self.hatasos)
        for jog in ("contents: write", "pull-requests: write", "issues: write"):
            with self.subTest(jog=jog):
                self.assertNotIn(jog, self.hatasos)

    def test_a_lista_tartalmazza_a_mai_ket_szerzot(self) -> None:
        for szerzo in ("sanchomuzax", "picasapy-claude-agent[bot]"):
            with self.subTest(szerzo=szerzo):
                self.assertIn(szerzo, self.szoveg)

    def test_ismeretlen_szerzonel_bukik(self) -> None:
        """A kapu foga: a nem-egyező ág `exit 1`-gyel zárul."""
        self.assertIn("exit 1", self.szoveg)
        self.assertIn("grep -qxF", self.szoveg,
                      "pontos, teljes soros egyezés kell — a részleges "
                      "illeszkedés (pl. `grep -q`) idegen nevet is átengedne")


if __name__ == "__main__":
    unittest.main()
