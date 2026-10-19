"""#5347: a kiadási jegyzet tartalék-szövegében nincs gondolatjel, félkötőjel vagy unicode mínusz.

A nagykötőjel-kapu az ilyen leírású kiadás későbbi szerkesztését (képfeltöltés)
blokkolja; a v0.9.149 képe így maradt el.
"""

from __future__ import annotations

import pytest

from scripts.ensure_release import tartalek_jegyzet

TILTOTT = ("—", "–", "−")


@pytest.mark.parametrize("valtozasok", [None, (), ("a bal sáv sora (#5341)",)])
def test_tartalek_jegyzetben_nincs_tiltott_kotojel(valtozasok):
    szoveg = tartalek_jegyzet(valtozasok)
    assert not any(jel in szoveg for jel in TILTOTT), szoveg
