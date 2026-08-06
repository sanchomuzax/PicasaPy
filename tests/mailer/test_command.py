"""`picasapy.mailer.command` — determinisztikus parancs-összeállítás
(#32, RÉSZLEGES kör)."""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.mailer.command import (
    EMAIL_SIZE_PRESETS,
    build_mailto_url,
    build_xdg_email_argv,
    resolve_email_max_dimension,
)


class TestResolveEmailMaxDimension:
    def test_smallest_preset_is_640(self):
        assert resolve_email_max_dimension(0) == 640

    def test_last_preset_is_original_size(self):
        assert resolve_email_max_dimension(len(EMAIL_SIZE_PRESETS) - 1) is None

    def test_presets_are_ascending_before_the_original_entry(self):
        sized = [value for value in EMAIL_SIZE_PRESETS if value is not None]
        assert sized == sorted(sized)

    @pytest.mark.parametrize("index", [-1, 5, 100])
    def test_rejects_out_of_range_index(self, index):
        with pytest.raises(ValueError):
            resolve_email_max_dimension(index)


class TestBuildXdgEmailArgv:
    def test_includes_subject_and_body(self):
        argv = build_xdg_email_argv("Cím", "Szöveg")
        assert argv[0] == "xdg-email"
        assert "--subject" in argv
        assert argv[argv.index("--subject") + 1] == "Cím"
        assert "--body" in argv
        assert argv[argv.index("--body") + 1] == "Szöveg"

    def test_omits_empty_subject_and_body(self):
        argv = build_xdg_email_argv("", "")
        assert "--subject" not in argv
        assert "--body" not in argv

    def test_adds_one_attach_flag_per_file(self):
        attachments = [Path("/tmp/a.jpg"), Path("/tmp/b.jpg")]
        argv = build_xdg_email_argv("s", "b", attachments)
        assert argv.count("--attach") == 2
        # Windowson a Path backslash-formát ad — az elvárás is azzal számol
        assert str(Path("/tmp/a.jpg")) in argv
        assert str(Path("/tmp/b.jpg")) in argv

    def test_no_attach_flags_without_attachments(self):
        argv = build_xdg_email_argv("s", "b")
        assert "--attach" not in argv

    def test_result_is_a_flat_argv_list_no_shell_string(self):
        # a subprocess.Popen(argv) shell=False hívásnak felel meg — a
        # tárgy/szöveg szóközei/idézőjelei nem törhetik szét a parancsot
        argv = build_xdg_email_argv('Idézőjeles "cím"', "sor egy\nsor kettő")
        assert isinstance(argv, list)
        assert all(isinstance(part, str) for part in argv)
        assert 'Idézőjeles "cím"' in argv


class TestBuildMailtoUrl:
    def test_starts_with_mailto_scheme(self):
        assert build_mailto_url("s", "b").startswith("mailto:")

    def test_encodes_subject_and_body(self):
        url = build_mailto_url("Cím ékezettel", "sor egy\nsor kettő")
        assert "subject=" in url
        assert "body=" in url
        assert " " not in url  # a szóköz kódolva van
        assert "\n" not in url

    def test_empty_subject_and_body_yields_bare_mailto(self):
        assert build_mailto_url("", "") == "mailto:"
