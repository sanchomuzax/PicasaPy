"""A `.tpl` parancsnyelv (#351): parszolás + `<%var%>`/`<%if%>` motor.

docs/specs/picasa-program-resources.md 2.3–2.4. alfejezet a teljes spec."""

import pytest

from picasapy.webexport.tpl_lang import (
    CopyCommand,
    DefineCommand,
    IncludeCommand,
    LoopCommand,
    TargetLoopCommand,
    TplSyntaxError,
    eval_conditionals,
    parse_header,
    parse_tpl,
    render,
    substitute_vars,
)


class TestParseHeader:
    def test_extracts_version_name_description(self):
        text = '#templatefile -v "1.0" -n "Fehér" -d "Egy leírás"\ndefine x y\n'
        header = parse_header(text)
        assert header.version == "1.0"
        assert header.name == "Fehér"
        assert header.description == "Egy leírás"

    def test_missing_header_gives_empty_defaults(self):
        header = parse_header("define x y\n")
        assert header == parse_header("")


class TestParseTplCommands:
    def test_define(self):
        commands = parse_tpl("define exportFileName index.html\n")
        assert commands == (DefineCommand("exportFileName", "index.html"),)

    def test_define_with_multiword_value_joined(self):
        commands = parse_tpl("define greeting Hello World\n")
        assert commands == (DefineCommand("greeting", "Hello World"),)

    def test_include(self):
        commands = parse_tpl("include header.html\n")
        assert commands == (IncludeCommand("header.html"),)

    def test_loop_without_extra_args(self):
        commands = parse_tpl("loop imagelistelement.html\n")
        assert commands == (LoopCommand("imagelistelement.html", ()),)

    def test_loop_with_notimplemented_extra_args_preserved(self):
        commands = parse_tpl("loop imagelistelement.html 3 1 2\n")
        assert commands == (
            LoopCommand("imagelistelement.html", ("3", "1", "2")),
        )

    def test_targetloop(self):
        commands = parse_tpl("targetloop imagetarget.tpl includedtarget.html\n")
        assert commands == (
            TargetLoopCommand("imagetarget.tpl", "includedtarget.html"),
        )

    def test_copy_without_destination(self):
        commands = parse_tpl("copy assets\\\n")
        assert commands == (CopyCommand("assets\\", None),)

    def test_copy_with_destination(self):
        commands = parse_tpl("copy assets\\ static\\\n")
        assert commands == (CopyCommand("assets\\", "static\\"),)

    def test_comment_and_header_lines_skipped(self):
        text = (
            '#templatefile -v "1.0" -n "X" -d "Y"\n'
            "# ez egy megjegyzés\n"
            "\n"
            "define a b\n"
        )
        commands = parse_tpl(text)
        assert commands == (DefineCommand("a", "b"),)

    def test_unknown_command_raises(self):
        with pytest.raises(TplSyntaxError):
            parse_tpl("frobnicate x y\n")

    def test_define_needs_two_args(self):
        with pytest.raises(TplSyntaxError):
            parse_tpl("define onlyname\n")

    def test_trailing_backslash_does_not_break_tokenizer(self):
        # a shlex-szel ELLENTÉTBEN a sor végi backslash sima literál karakter
        # (Windows-könyvtárjelölés, ld. `copy assets\`), nem escape-kezdet
        commands = parse_tpl("copy assets\\ static\\\n")
        assert commands == (CopyCommand("assets\\", "static\\"),)


class TestSubstituteVars:
    def test_replaces_known_variable(self):
        assert substitute_vars("Hello <%name%>!", {"name": "Világ"}) == "Hello Világ!"

    def test_unknown_variable_becomes_empty(self):
        assert substitute_vars("<%missing%>", {}) == ""

    def test_multiple_occurrences(self):
        assert substitute_vars("<%a%>-<%a%>", {"a": "x"}) == "x-x"

    def test_does_not_touch_if_endif_markers(self):
        text = "<%if flag%>x<%endif%>"
        # a `substitute_vars` önmagában nem nyúl az if/endif jelölőkhöz,
        # mert a mintázat kizárólag \w+ tartalmat enged <% %> között
        assert substitute_vars(text, {}) == text


class TestEvalConditionals:
    def test_true_condition_keeps_content(self):
        assert eval_conditionals("<%if flag%>igen<%endif%>", {"flag": "true"}) == "igen"

    def test_false_condition_removes_content(self):
        assert eval_conditionals("<%if flag%>igen<%endif%>", {"flag": ""}) == ""

    def test_missing_variable_is_falsy(self):
        assert eval_conditionals("<%if flag%>igen<%endif%>", {}) == ""

    def test_negation_flips_truthy(self):
        assert eval_conditionals("<%if !flag%>igen<%endif%>", {"flag": ""}) == "igen"
        assert eval_conditionals("<%if !flag%>igen<%endif%>", {"flag": "true"}) == ""

    def test_zero_and_false_strings_are_falsy(self):
        assert eval_conditionals("<%if flag%>x<%endif%>", {"flag": "0"}) == ""
        assert eval_conditionals("<%if flag%>x<%endif%>", {"flag": "false"}) == ""

    def test_surrounding_text_preserved(self):
        result = eval_conditionals(
            "előtte<%if flag%>közép<%endif%>utána", {"flag": "true"}
        )
        assert result == "előtteközéputána"

    def test_nested_conditionals(self):
        text = "<%if outer%>A<%if inner%>B<%endif%>C<%endif%>"
        assert eval_conditionals(text, {"outer": "true", "inner": "true"}) == "ABC"
        assert eval_conditionals(text, {"outer": "true", "inner": ""}) == "AC"
        assert eval_conditionals(text, {"outer": "", "inner": "true"}) == ""

    def test_unterminated_if_left_as_is(self):
        text = "x<%if flag%>y"
        assert eval_conditionals(text, {"flag": "true"}) == text


class TestRender:
    def test_combines_conditionals_and_substitution(self):
        text = "<%if show%>Szia, <%name%>!<%endif%>"
        assert render(text, {"show": "true", "name": "Éva"}) == "Szia, Éva!"
        assert render(text, {"show": "", "name": "Éva"}) == ""
