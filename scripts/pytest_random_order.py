"""Failed test predecessor reporter for the #6590 nightly run.

Load only when ``pytest-randomly`` is enabled. The direct predecessor is a
diagnostic candidate for an order-dependent failure, not proof of causation.
"""

from __future__ import annotations

import json
import os

_ORDER: list[str] = []
_PREFIX = "PICASAPY_RANDOM_ORDER\t"


def _failure_predecessors(
    order: list[str], failed: list[str]
) -> list[tuple[str, str]]:
    """Return each failed nodeid with the item immediately before it."""
    pairs = []
    for nodeid in failed:
        try:
            index = order.index(nodeid)
        except ValueError:
            continue
        predecessor = order[index - 1] if index else ""
        pairs.append((nodeid, predecessor))
    return pairs


def _write_order_pairs(pairs: list[tuple[str, str]]) -> None:
    """Put machine-readable rows on separate lines after pytest's progress output."""
    if not pairs:
        return
    print()
    for nodeid, predecessor in pairs:
        print(f"{_PREFIX}{nodeid}\t{predecessor}", flush=True)


def pytest_collection_finish(session) -> None:
    """Save the final collection order after order-changing hooks ran."""
    _ORDER[:] = [item.nodeid for item in session.items]


def pytest_sessionfinish(session, exitstatus: int) -> None:
    """Report failed tests and requested targets with their direct predecessor."""
    failed: list[str] = []
    if exitstatus != 0:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            failed = list(dict.fromkeys(
                report.nodeid for report in reporter.stats.get("failed", [])
            ))
    try:
        targets = json.loads(os.environ.get("PICASAPY_RANDOM_ORDER_TARGETS", "[]"))
    except (TypeError, ValueError):
        targets = []
    nodeids = list(dict.fromkeys([*failed, *(t for t in targets if isinstance(t, str))]))
    _write_order_pairs(_failure_predecessors(_ORDER, nodeids))
