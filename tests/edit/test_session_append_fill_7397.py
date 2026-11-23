"""#7397: az `append_fill` új `fill` réteget fűz a lánc végére, nem cserél.

Az eredeti Picasában (E27, job-906) a Gyakori javítások Derítőfény-csúszkájának
húzása a betöltött `fill` mellé ÚJ réteget ad (`fill=1,0.500000;fill=1,0.523364;`).
A `set_fill` a helyén cserél, ezért az maradt a többi hívónak.
"""

from __future__ import annotations

import pytest

from picasapy.edit import EditSession
from picasapy.ini.filters import FilterOp


def _fill_ertekek(session: EditSession) -> list[str]:
    return [op.params[1] for op in session.ops if op.matches("fill")]


class TestAppendFill:
    def test_ures_lancra_a_fill_ket_mezovel_kerul_be(self):
        assert EditSession().append_fill(0.5).to_value() == "fill=1,0.500000;"

    def test_a_betoltott_fill_melle_uj_reteg_kerul(self):
        betoltott = EditSession(ops=(FilterOp(name="fill", params=("1", "0.5")),))

        session = betoltott.append_fill(0.523364)

        assert session.to_value() == "fill=1,0.5;fill=1,0.523364;"

    def test_a_betoltott_reteg_valtozatlan_marad(self):
        betoltott = EditSession(ops=(FilterOp(name="fill", params=("1", "0.5")),))

        session = betoltott.append_fill(0.9)

        assert session.ops[0] == betoltott.ops[0]
        assert _fill_ertekek(session) == ["0.5", "0.900000"]

    def test_a_sorrend_a_lanc_vege(self):
        session = (
            EditSession()
            .set_fill(0.2)
            .append_effect("sat", ("1", "0.5"))
            .append_fill(0.8)
        )

        assert [op.name for op in session.ops] == ["fill", "sat", "fill"]

    def test_a_finetune2_reteghez_nem_nyul(self):
        session = (
            EditSession()
            .set_finetune(fill=0.4, highlights=0.0, shadows=0.0, temperature=0.0)
            .append_fill(0.5)
        )

        assert session.finetune_values().fill == pytest.approx(0.4)
        assert session.fill_value() == pytest.approx(0.5)

    def test_a_set_fill_tovabbra_a_helyen_cserel(self):
        """A `set_fill` a többi hívónak marad: az első `fill` helyén cserél."""
        session = EditSession().set_fill(0.2).set_fill(0.8)

        assert session.to_value() == "fill=1,0.800000;"

    def test_az_eredeti_nem_valtozik(self):
        eredeti = EditSession().set_fill(0.3)

        eredeti.append_fill(0.6)

        assert eredeti.to_value() == "fill=1,0.300000;"
