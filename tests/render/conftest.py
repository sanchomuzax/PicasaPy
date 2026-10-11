"""A render-tesztek közös fixture-jei.

A betűcsalád-próbák ugyanazt a Qt-alkalmazást és második próbabetűt kérik,
mint az app-tesztek (#4546, #4831) — a definíció egy helyen marad.
"""

from app.conftest import legalabb_ket_betucsalad, qt_app  # noqa: F401
