# -*- coding: utf-8 -*-
"""Dynamically generated tests for svg -> tikz conversion.

Test cases are loaded from tests/testcases.toml.  Each entry converts an SVG
with given options and compares the output against an expected .tex file.

If testcases.toml is absent the module falls back to auto-discovering all
*.svg files under tests/testfiles/ (recursively) and pairing them with same-
named .tex files — useful for a quick sanity check with no config.

Dependencies
────────────
A test can declare depends_on = ["other_id"] so that if "other_id" failed the
dependent test is skipped (or failed) automatically, keeping the output clean.

Diff output
───────────
When actual output differs from expected, a unified diff is printed in the
assertion message so you can immediately see what changed without opening files.

To regenerate expected .tex files run:
    python scripts/generate_tex.py
"""

from __future__ import annotations

import difflib
import io
import os
import sys
import unittest
from typing import Dict, List

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz import convert_file

CONFIG_TOML = os.path.join(os.path.dirname(__file__), "testcases.toml")


def load_config() -> List[Dict]:
    """Load test cases from ``tests/testcases.toml`` if it exists.

    Returns
    -------
    List[Dict]
        Normalised list of test case dicts, each with keys ``id``, ``svg``,
        ``expected``, ``options``, ``depends_on``, and
        ``on_dependency_fail``.  Returns an empty list when the config file
        is absent or no TOML parser is available.

    Raises
    ------
    ValueError
        If a config entry has neither an ``id`` nor an ``svg`` field.
    """
    cfg = None
    if os.path.exists(CONFIG_TOML):
        # Prefer TOML if available
        try:
            try:
                # pylint: disable=import-outside-toplevel
                import tomllib as _toml  # Python 3.11
            except ImportError:
                # pylint: disable=import-outside-toplevel
                import tomli as _toml
        except ImportError:
            _toml = None
        if _toml is not None:
            with open(CONFIG_TOML, "rb") as f:
                data = _toml.load(f)
            cfg = data.get("tests") or data.get("cases")

    if not cfg:
        return []

    # Normalize entries
    normalized = []
    for entry in cfg:
        eid = entry.get("id")
        if not eid:
            # try derive from svg
            svg = entry.get("svg")
            if svg:
                eid = os.path.splitext(os.path.basename(svg))[0]
            else:
                raise ValueError("Test entry missing 'id' and 'svg'")
        svg = entry.get("svg") or f"tests/testfiles/{eid}.svg"
        expected = entry.get("expected") or f"tests/testfiles/{eid}.tex"
        options = entry.get("options") or {}
        depends_on = entry.get("depends_on") or []
        on_dep_fail = entry.get("on_dependency_fail") or "skip"
        normalized.append(
            {
                "id": eid,
                "svg": svg,
                "expected": expected,
                "options": options,
                "depends_on": depends_on,
                "on_dependency_fail": on_dep_fail,
            }
        )
    return normalized


def topological_sort(cases: List[Dict]) -> List[Dict]:
    """Sort test cases so every dependency runs before its dependents.

    Uses Kahn's algorithm.  Unknown dependency IDs are warned about and
    silently dropped rather than causing an error.

    Parameters
    ----------
    cases : List[Dict]
        Unsorted list of test case dicts as returned by :func:`load_config`
        or :func:`autodiscover_cases`.

    Returns
    -------
    List[Dict]
        The same dicts reordered so that for every ``depends_on``
        relationship, the dependency appears earlier in the list.

    Raises
    ------
    RuntimeError
        If a dependency cycle is detected among the test cases.
    """
    id_to_case = {c["id"]: c for c in cases}
    deps = {c["id"]: set(c.get("depends_on") or []) for c in cases}

    # Remove unknown dependencies with warning
    for k, s in deps.items():
        unknown = {d for d in s if d not in id_to_case}
        if unknown:
            print(
                f"Warning: test '{k}' depends on unknown tests: {sorted(unknown)}",
                file=sys.stderr,
            )
            s.difference_update(unknown)

    # Kahn

    # Get items without dependence
    no_deps = [k for k, s in deps.items() if not s]
    ordered = []
    while no_deps:
        n = no_deps.pop(0)

        # Add to ordered list
        ordered.append(id_to_case[n])

        # remove n from others
        for m, s in deps.items():
            if n in s:
                s.remove(n)
                if not s:
                    # If no deps left, add to no_deps
                    no_deps.append(m)
        deps.pop(n)
    if deps:
        # cycle detected
        raise RuntimeError(f"Cycle detected in test dependencies: {deps}")
    return ordered


# Build test cases
testcases = load_config()

try:
    testcases = topological_sort(testcases)
except RuntimeError as exc:  # pragma: no cover - misconfiguration
    print("Failed to order tests:, ", exc, file=sys.stderr)


# Keep results so dependents can be skipped or failed when a dependency fails.
results: Dict[str, bool] = {}


class TestGeneratedCases(unittest.TestCase):
    """Generated tests run in dependency-respecting order."""


def make_test(case):
    """Create a ``unittest.TestCase`` method for a single test case.

    The returned function converts *case*'s SVG, writes the result to
    ``tests/testdest/<id>.tex``, and compares it line-by-line with the
    expected ``.tex`` file.  A unified diff is included in the assertion
    message when the files differ.

    If any dependency listed in ``depends_on`` previously failed, the test
    is skipped or failed depending on ``on_dependency_fail``.

    Parameters
    ----------
    case : Dict
        A test case dict as returned by :func:`load_config`.

    Returns
    -------
    Callable
        A bound-style method suitable for attaching to a
        ``unittest.TestCase`` subclass via ``setattr``.
    """

    def test(self):
        cid = case["id"]
        # Check dependencies
        failed_deps = [d for d in case["depends_on"] if results.get(d) is False]
        if failed_deps:
            msg = f"Dependency test(s) failed: {failed_deps}"
            if case.get("on_dependency_fail", "skip") == "fail":
                self.fail(msg)
            else:
                self.skipTest(msg)

        svg = case["svg"]
        expected = case["expected"]
        options = case.get("options", {}) or {}

        # Where to write the actual file: tests/testdest/<id>.tex
        actual_path = os.path.join(os.path.dirname(__file__), "testdest", f"{cid}.tex")

        # Ensure testdest exists
        os.makedirs(os.path.dirname(actual_path), exist_ok=True)

        convert_file(svg, output=actual_path, **options)

        try:
            with io.open(expected, encoding="utf-8") as fexp:
                exp_text = fexp.read().splitlines(keepends=True)
        except FileNotFoundError:
            # helpful error
            results[cid] = False
            self.fail(
                f"Expected file not found: {expected} (run scripts/generate_tex.py to create) "
            )

        with io.open(actual_path, encoding="utf-8") as fact:
            act_text = fact.read().splitlines(keepends=True)

        if exp_text != act_text:
            # produce a unified diff in the assertion message
            diff = difflib.unified_diff(
                exp_text,
                act_text,
                fromfile=f"expected: {expected}",
                tofile=f"actual:   {actual_path}",
                lineterm="",
            )
            diff_text = "\n" + "\n".join(diff)
            results[cid] = False
            self.fail(f"Output mismatch for '{cid}':{diff_text}")

        # Passed
        results[cid] = True
        # cleanup actual file
        try:
            os.remove(actual_path)
        except OSError:
            pass

    return test


# Dynamically attach test methods with a stable order prefix so unittest runs
# them in dependency-respecting order.
for _idx, _case in enumerate(testcases, start=1):
    setattr(TestGeneratedCases, f"test_{_idx:03d}_{_case['id']}", make_test(_case))
    del _idx, _case


if __name__ == "__main__":
    unittest.main()
