"""#7383: a Hangolás-látogatás ÚJ `finetune2` réteget fűz a lánc végére.

Az eredeti Picasában a betöltött `finetune2` mellé új réteg kerül (két réteg a
láncban, J6c). A munkamenet `append_finetune`-je ezért sosem cserél és sosem
dob el meglévő finetune-réteget (a `set_finetune` ellenben a helyén cserél).
"""

from __future__ import annotations

import pytest

from picasapy.edit import EditSession


def _finetune_sorok(session: EditSession) -> list[tuple[str, ...]]:
    return [op.params for op in session.ops if op.name.casefold() == "finetune2"]


class TestAppendFinetune:
    def test_ures_lancra_a_vegere_kerul(self):
        session = EditSession().append_finetune(
            fill=0.1, highlights=0.2, shadows=0.3, temperature=-0.4
        )
        assert session.to_value() == (
            "finetune2=1,0.100000,0.200000,0.300000,00000000,-0.400000;"
        )

    def test_a_betoltott_finetune2_melle_uj_reteg_kerul(self):
        """J6c: `finetune2=1,0,0,0,ffccc6b2,0` mellett a húzás után két sor áll,
        a másodiknak a p4-je `00000000`."""
        session = EditSession.from_value("finetune2=1,0,0,0,ffccc6b2,0;")
        uj = session.append_finetune(
            fill=0.0, highlights=0.2, shadows=0.0, temperature=0.0
        )
        sorok = _finetune_sorok(uj)
        assert len(sorok) == 2
        assert sorok[0][4] == "ffccc6b2"
        assert sorok[1][4] == "00000000"

    def test_az_ismeretlen_es_kovetkezo_retegek_erintetlenek(self):
        session = EditSession.from_value("grain2=1,0.5;finetune2=1,0.5,0,0,00000000,0;sat=1,0.5;")
        uj = session.append_finetune(
            fill=0.0, highlights=0.1, shadows=0.0, temperature=0.0
        )
        assert [op.name for op in uj.ops] == ["grain2", "finetune2", "sat", "finetune2"]
        assert uj.ops[:3] == session.ops

    def test_a_pipetta_szine_megadhato(self):
        session = EditSession().append_finetune(
            fill=0.0, highlights=0.0, shadows=0.0, temperature=0.0, neutral="ff102030"
        )
        assert _finetune_sorok(session)[0][4] == "ff102030"

    def test_az_eredeti_munkamenet_valtozatlan(self):
        session = EditSession.from_value("enhance=1;")
        session.append_finetune(fill=0.1, highlights=0.0, shadows=0.0, temperature=0.0)
        assert session.to_value() == "enhance=1;"

    @pytest.mark.parametrize("nev", ("finetune2", "finetune"))
    def test_a_v1_finetune_melle_is_uj_finetune2_jon(self, nev):
        session = EditSession.from_value(f"{nev}=1,0.3,0,0,00000000,0;")
        uj = session.append_finetune(
            fill=0.0, highlights=0.1, shadows=0.0, temperature=0.0
        )
        assert [op.name for op in uj.ops] == [nev, "finetune2"]
