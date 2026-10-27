"""A #5958 őre: a programindítás maradjon rövid, megnevezett lépéssor."""

import ast
from pathlib import Path


def test_run_delegates_to_named_startup_steps():
    repo = Path(__file__).resolve().parents[2]
    source = (repo / "src/picasapy/app/application.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    run = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "run"
    )

    direct_calls = []
    for statement in run.body:
        pending = list(ast.iter_child_nodes(statement))
        while pending:
            node = pending.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id.startswith("_startup_step_")
            ):
                direct_calls.append(node.func.id)
            pending.extend(ast.iter_child_nodes(node))

    assert run.end_lineno - run.lineno <= 220
    assert len(direct_calls) >= 6
