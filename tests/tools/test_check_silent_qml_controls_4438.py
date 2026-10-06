"""#4438 — a QML-oldali néma vezérlők gépi őrének tesztjei."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import check_silent_qml_controls as guard  # noqa: E402


def _repo(tmp_path: Path, *, qml: str, python: str = "") -> Path:
    source = tmp_path / "src" / "picasapy" / "app"
    qml_dir = source / "qml"
    qml_dir.mkdir(parents=True)
    (qml_dir / "Main.qml").write_text(qml, encoding="utf-8")
    if python:
        (source / "window.py").write_text(python, encoding="utf-8")
    return tmp_path


def _category_findings(root: Path, category: str):
    return [finding for finding in guard.scan(root) if finding.category == category]


def test_empty_and_console_only_click_handlers_are_candidates(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        qml='''\
import QtQuick.Controls
Item {
    Button { objectName: "emptyButton"; onClicked: { } }
    MenuItem { objectName: "logOnly"; onTriggered: console.log("clicked") }
    Button { objectName: "working"; onClicked: controller.open() }
}
''',
    )

    handlers = _category_findings(root, "silent-handler")

    assert {finding.key.split(":")[-1] for finding in handlers} == {
        "onClicked",
        "onTriggered",
    }
    assert all("working" not in finding.key for finding in handlers)


def test_empty_function_and_arrow_handlers_are_candidates(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        qml='''\
Item {
    Button { objectName: "emptyFunction"; onClicked: function() {} }
    MenuItem { objectName: "logArrow"; onTriggered: () => console.log("clicked") }
    Button { objectName: "emptyArrow"; onClicked: () => {} }
}
''',
    )

    handlers = _category_findings(root, "silent-handler")

    assert len(handlers) == 3
    assert all(finding.key.endswith(("onClicked", "onTriggered")) for finding in handlers)


def test_a_constant_disabled_control_is_a_candidate(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        qml='''\
import QtQuick.Controls
Item {
    Button {
        objectName: "disabledButton"
        enabled: false
    }
}
''',
    )

    findings = _category_findings(root, "constant-disabled")

    assert len(findings) == 1
    assert "Main.qml" in findings[0].key


def test_an_unhandled_qml_signal_is_a_candidate(tmp_path: Path) -> None:
    root = _repo(tmp_path, qml="Item { signal actionRequested() }\n")

    findings = _category_findings(root, "unbound-signal")

    assert [finding.key for finding in findings] == [
        "src/picasapy/app/qml/Main.qml::actionRequested"
    ]


def test_qml_handler_or_production_connect_counts_as_a_signal_binding(
    tmp_path: Path,
) -> None:
    root = _repo(
        tmp_path,
        qml='''\
Item {
    id: root
    signal qmlHandled()
    signal pythonHandled()
    Connections { target: root; function onQmlHandled() { root.visible = true } }
}
''',
        python="window.pythonHandled.connect(self.handle)\n",
    )

    assert _category_findings(root, "unbound-signal") == []


def test_a_signal_on_an_inline_component_is_bound_at_its_use_site(
    tmp_path: Path,
) -> None:
    root = _repo(
        tmp_path,
        qml='''\
Item {
    component Toggle: Item { signal toggled() }
    Toggle { onToggled: visible = !visible }
}
''',
    )

    assert _category_findings(root, "unbound-signal") == []


def test_a_signal_on_a_loader_component_is_bound_through_loader_item(
    tmp_path: Path,
) -> None:
    root = _repo(
        tmp_path,
        qml='''\
Item {
    Loader { id: playerLoader; source: "VideoPlayerView.qml" }
    Connections {
        target: playerLoader.item
        function onTrimRequested() { root.visible = true }
    }
}
''',
    )
    qml_dir = root / "src" / "picasapy" / "app" / "qml"
    (qml_dir / "VideoPlayerView.qml").write_text(
        "Item { signal trimRequested() }\n", encoding="utf-8"
    )

    assert _category_findings(root, "unbound-signal") == []


def test_an_unrelated_component_handler_does_not_bind_the_signal(
    tmp_path: Path,
) -> None:
    root = _repo(
        tmp_path,
        qml="import QtQuick\nItem { Widget {} }\n",
    )
    qml_dir = root / "src" / "picasapy" / "app" / "qml"
    (qml_dir / "Widget.qml").write_text(
        "Item { signal actionRequested() }\n", encoding="utf-8"
    )
    (qml_dir / "Other.qml").write_text(
        "Item { function onActionRequested() {} }\n", encoding="utf-8"
    )

    findings = _category_findings(root, "unbound-signal")
    assert [finding.key for finding in findings] == [
        "src/picasapy/app/qml/Widget.qml::actionRequested"
    ]

    (qml_dir / "Main.qml").write_text(
        "import QtQuick\nItem { Widget { onActionRequested: visible = true } }\n",
        encoding="utf-8",
    )
    assert _category_findings(root, "unbound-signal") == []


def test_comments_and_string_literals_do_not_create_findings(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        qml='''\
Item {
    // enabled: false; signal imaginary(); onClicked: {}
    property string note: "enabled: false onClicked: {} signal fake()"
    Button { onClicked: controller.run() }
}
''',
    )

    assert guard.scan(root) == []


def test_the_production_tree_matches_the_reviewed_baseline() -> None:
    findings = guard.scan(_REPO_ROOT)
    baseline = guard.load_baseline(guard._DEFAULT_BASELINE)

    new, stale = guard.compare(findings, baseline)

    assert new == []
    assert stale == []
    assert len(baseline) <= guard.MAX_BASELINE_ENTRIES
