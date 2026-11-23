"""#7369: a Gyakori javítások Derítőfénye a `fill` réteget szerkeszti.

Az eredeti Picasa az 1. fülön a `fill`, a 2. fülön (Hangolás) a `finetune2`
szűrőt aktiválja (`0x005d7780`). A két réteg egymástól független, ezért a
munkamenetnek külön olvasója és írója kell a `fill`-hez: a `finetune2`
műveletei a `fill` sort nem érinthetik, és fordítva.
"""

from __future__ import annotations

import pytest

from picasapy.edit import EditSession
from picasapy.ini.filters import FilterOp


def _fill_sorok(session: EditSession) -> list[str]:
    return [op.name for op in session.ops if op.name.casefold() == "fill"]


class TestFillRetegIrasa:
    def test_ures_lancra_a_fill_ket_mezovel_kerul_be(self):
        session = EditSession().set_fill(0.5)
        assert session.to_value() == "fill=1,0.500000;"

    def test_a_beirt_ertek_visszaolvashato(self):
        assert EditSession().set_fill(0.3).fill_value() == pytest.approx(0.3)

    def test_fill_nelkuli_lancon_az_ertek_none(self):
        assert EditSession().fill_value() is None

    def test_a_meglevo_fill_a_helyen_cserelodik(self):
        session = (
            EditSession()
            .set_fill(0.2)
            .append_effect("sat", ("1", "0.5"))
            .set_fill(0.8)
        )
        assert session.to_value() == "fill=1,0.800000;sat=1,0.5;"

    def test_az_idegen_fill_sor_is_felolvashato(self):
        """Az eredeti Picasa írta `fill=1,0.5` sor értéke 0.5 (1089 ilyen
        önálló sor van a korpuszban)."""
        session = EditSession(ops=(FilterOp(name="fill", params=("1", "0.5")),))
        assert session.fill_value() == pytest.approx(0.5)

    def test_hibas_fill_parameter_nem_dob(self):
        session = EditSession(ops=(FilterOp(name="fill", params=("1", "x")),))
        assert session.fill_value() == pytest.approx(0.0)

    def test_a_clear_fill_csak_a_fill_reteget_veszi_le(self):
        session = (
            EditSession()
            .set_fill(0.4)
            .set_finetune(fill=0.1, highlights=0.2, shadows=0.0, temperature=0.0)
            .clear_fill()
        )
        assert session.fill_value() is None
        assert session.has_finetune() is True


class TestAKetRetegFuggetlen:
    def test_a_set_finetune_nem_nyul_a_fill_reteghez(self):
        session = EditSession().set_fill(0.5).set_finetune(
            fill=0.9, highlights=0.0, shadows=0.0, temperature=0.0
        )
        assert session.fill_value() == pytest.approx(0.5)
        assert session.finetune_values().fill == pytest.approx(0.9)
        assert _fill_sorok(session) == ["fill"]

    def test_a_set_fill_nem_nyul_a_finetune2_reteghez(self):
        session = EditSession().set_finetune(
            fill=0.9, highlights=0.1, shadows=0.2, temperature=0.3
        ).set_fill(0.5)
        values = session.finetune_values()
        assert values is not None
        assert values.fill == pytest.approx(0.9)
        assert values.highlights == pytest.approx(0.1)
        assert session.fill_value() == pytest.approx(0.5)

    def test_a_finetune_olvaso_nem_latja_a_fill_sort(self):
        """A `fill` rétegből sosem lesz Hangolás-érték."""
        session = EditSession().set_fill(0.5)
        assert session.finetune_values() is None
        assert session.has_finetune() is False

    def test_a_clear_finetune_a_fill_reteget_megtartja(self):
        session = EditSession().set_fill(0.5).set_finetune(
            fill=0.9, highlights=0.0, shadows=0.0, temperature=0.0
        ).clear_finetune()
        assert session.fill_value() == pytest.approx(0.5)
