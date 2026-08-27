from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fabric_cli.validation import validate_public_registry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fabric")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the Public Registry")
    validate.add_argument("--root", type=Path, default=Path.cwd())
    validate.add_argument("--prohibited-patterns", type=Path)
    validate.add_argument("--format", choices=("human", "json"), default="human")
    return parser


def _render_human(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["ok"] else "FAIL"
    lines = [f"Public Registry: {status}"]
    for check in payload["checks"]:
        check_status = "PASS" if check["ok"] else "FAIL"
        lines.append(f"- {check['name']}: {check_status}")
        lines.extend(f"  - {error}" for error in check["errors"])
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        report = validate_public_registry(args.root.resolve(), args.prohibited_patterns)
        payload = report.as_dict()
        if args.format == "json":
            print(json.dumps(payload, sort_keys=True))
        else:
            print(_render_human(payload))
        return 0 if report.ok else 1
    raise AssertionError(f"unhandled command: {args.command}")
