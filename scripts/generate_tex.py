#!/usr/bin/env python3
"""Regenerate expected .tex files for the svg2tikz test suite.

Reads tests/testcases.toml and converts each SVG to the expected .tex path,
overwriting whatever was there before.  Use this after changing the converter
so the golden files reflect the new output, then visually verify the results
before committing.

Usage
─────
  # Regenerate all expected files
  python scripts/generate_tex.py

  # Regenerate only specific tests (by id)
  python scripts/generate_tex.py circle ellipse transform

  # Dry run: show what would be written without actually writing
  python scripts/generate_tex.py --dry-run

  # Filter by category (directory name under testfiles/)
  python scripts/generate_tex.py --category shapes
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# pylint: disable=wrong-import-position
from svg2tikz import convert_file

CONFIG_TOML = os.path.join(os.path.dirname(__file__), "..", "tests", "testcases.toml")


def load_cases() -> List[Dict]:
    """Load test cases from ``tests/testcases.toml``.

    Returns
    -------
    List[Dict]
        List of test case dicts, each with keys ``id``, ``svg``,
        ``expected``, ``options``, ``depends_on``, and
        ``on_dependency_fail``.

    Raises
    ------
    SystemExit
        If neither ``tomllib`` (Python 3.11+) nor ``tomli`` is installed.
    """
    try:
        try:
            # pylint: disable=import-outside-toplevel
            import tomllib as _toml
        except ImportError:
            # pylint: disable=import-outside-toplevel
            import tomli as _toml
    except ImportError:
        print(
            "ERROR: Install tomli (pip install tomli) to parse testcases.toml",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(CONFIG_TOML, "rb") as f:
        data = _toml.load(f)
    return data.get("tests") or data.get("cases") or []


def category_of(case: Dict) -> str:
    """Return the category of a test case.

    The category is the immediate parent directory of the expected ``.tex``
    file (e.g. ``shapes`` for
    ``tests/testfiles/shapes/rectangle.tex``).

    Parameters
    ----------
    case : Dict
        A test case dict as returned by :func:`load_cases`.

    Returns
    -------
    str
        The subdirectory name, or an empty string if the path has fewer
        than two components.
    """
    path = case.get("expected", "")
    parts = path.replace("\\", "/").split("/")
    # expected path is like tests/testfiles/<category>/<name>.tex
    if len(parts) >= 2:
        return parts[-2]
    return ""


def generate(cases: List[Dict], dry_run: bool = False) -> None:
    """Convert each SVG in *cases* and write the result to its expected path.

    Parameters
    ----------
    cases : List[Dict]
        Test case dicts as returned by :func:`load_cases`, already filtered
        to the desired subset.
    dry_run : bool, optional
        When ``True``, print what would be written without actually writing
        any files. Defaults to ``False``.
    """
    ok = failed = 0
    for case in cases:
        cid = case.get("id", "?")
        svg = case["svg"]
        expected = case["expected"]
        options = case.get("options") or {}

        if not os.path.exists(svg):
            print(f"  SKIP  {cid}  (SVG not found: {svg})")
            continue

        os.makedirs(os.path.dirname(expected), exist_ok=True)

        if dry_run:
            print(f"  DRY   {cid}  →  {expected}  options={options}")
            continue

        try:
            # inkex's arg_parser reads sys.argv; isolate it from our own args.
            saved_argv = sys.argv
            sys.argv = sys.argv[:1]
            try:
                convert_file(svg, output=expected, **options)
            finally:
                sys.argv = saved_argv
            print(f"  OK    {cid}  →  {expected}")
            ok += 1
        # pylint: disable=broad-except
        except Exception as exc:
            print(f"  FAIL  {cid}  {exc}", file=sys.stderr)
            failed += 1

    if not dry_run:
        print(f"\n{ok} generated, {failed} failed.")


def main() -> None:
    """Entry point for the command-line interface.

    Parses arguments, filters test cases from :func:`load_cases`, and
    delegates to :func:`generate`.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ids", nargs="*", help="Test IDs to regenerate (default: all)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without writing",
    )
    parser.add_argument(
        "--category", help="Only regenerate tests in this category (subdirectory)"
    )
    args = parser.parse_args()

    cases = load_cases()

    if args.ids:
        id_set = set(args.ids)
        cases = [c for c in cases if c.get("id") in id_set]
        missing = id_set - {c["id"] for c in cases}
        if missing:
            print(f"WARNING: unknown test IDs: {sorted(missing)}", file=sys.stderr)

    if args.category:
        cases = [c for c in cases if category_of(c) == args.category]
        if not cases:
            print(
                f"WARNING: no tests found for category '{args.category}'",
                file=sys.stderr,
            )

    if not cases:
        print("No test cases matched.", file=sys.stderr)
        sys.exit(1)

    generate(cases, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
