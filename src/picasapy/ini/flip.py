"""Tükrözés bitmaszk konstansok a .picasa.ini formátumhoz (#2976, #6688).

A jelzőértékek az ini BITMASZKJÁT követik:
1 = vízszintes, 2 = függőleges, 3 = mindkettő.
A maszk és a toggled_flip tisztán bitművelet, független a render lánctól.
"""

from __future__ import annotations

#: Vízszintes tükrözés (bal-jobb) - az ini-maszk 0. bitje (#2976).
FLIP_HORIZONTAL: int = 1

#: Függőleges tükrözés (fel-le) - az ini-maszk 1. bitje (#2976).
FLIP_VERTICAL: int = 2

#: A két bit együtt. Ennél nagyobb értéket nem értelmezünk.
FLIP_MASK: int = FLIP_VERTICAL | FLIP_HORIZONTAL


def toggled_flip(flags: int, direction: int) -> int:
    """A jelző ki/be kapcsolása egy irányra - a csillag mintája.

    Ugyanarra az irányra másodszor nyomva visszaáll az eredeti állapot, mert
    a tükrözés önmaga inverze. Az értelmezhetetlen bitek leesnek.
    """
    return (int(flags or 0) ^ int(direction or 0)) & FLIP_MASK
