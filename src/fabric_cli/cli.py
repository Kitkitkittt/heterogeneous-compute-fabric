from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from fabric_cli.admission import generate_admission_report
from fabric_cli.overlay import validate_overlay
from fabric_cli.routing import route_task
from fabric_cli.validation import validate_public_registry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fabric")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the Public Registry")
    validate.add_argument("--root", type=Path, default=Path.cwd())
    validate.add_argument("--prohibited-patterns", type=Path)
    validate.add_argument("--format", choices=("human", "json"), default="human")

    route = subparsers.add_parser("route", help="route work to eligible Node Slots")
    route.add_argument("--root", type=Path, default=Path.cwd())
    route.add_argument("--repository", required=True)
    route.add_argument("--architecture", required=True)
    route.add_argument("--role", action="append", default=[])
    route.add_argument("--format", choices=("human", "json"), default="human")

    overlay = subparsers.add_parser("overlay", help="work with a Private Operations Overlay")
    overlay_subparsers = overlay.add_subparsers(dest="overlay_command", required=True)
    overlay_validate = overlay_subparsers.add_parser("validate", help="validate a private overlay")
    overlay_validate.add_argument("--root", type=Path, default=Path.cwd())
    overlay_validate.add_argument("--overlay", type=Path, required=True)
    overlay_validate.add_argument("--format", choices=("human", "json"), default="human")

    admission = subparsers.add_parser("admission", help="evaluate Node Slot admission evidence")
    admission_subparsers = admission.add_subparsers(dest="admission_command", required=True)
    admission_report = admission_subparsers.add_parser(
        "report", help="generate an admission report"
    )
    admission_report.add_argument("--profile", required=True)
    admission_report.add_argument("--observations", type=Path, required=True)
    admission_report.add_argument("--view", choices=("public", "private"), default="public")
    admission_report.add_argument("--format", choices=("human", "json"), default="human")
    return parser


def _render_human(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["ok"] else "FAIL"
    lines = [f"Public Registry: {status}"]
    for check in payload["checks"]:
        check_status = "PASS" if check["ok"] else "FAIL"
        lines.append(f"- {check['name']}: {check_status}")
        lines.extend(f"  - {error}" for error in check["errors"])
    return "\n".join(lines)


def _render_route_human(payload: dict[str, Any]) -> str:
    if payload["ok"]:
        return "Eligible Node Slots: " + ", ".join(payload["eligible_nodes"])
    lines = ["No eligible Node Slots"]
    for decision in payload["decisions"]:
        lines.append(f"- {decision['node_id']}: {', '.join(decision['reasons'])}")
    return "\n".join(lines)


def _render_overlay_human(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["ok"] else "FAIL"
    lines = [f"Private Operations Overlay: {status}"]
    lines.extend(f"- {node['node_id']}: joined" for node in payload["nodes"])
    lines.extend(f"- {error}" for error in payload["errors"])
    return "\n".join(lines)


def _render_admission_human(payload: dict[str, Any]) -> str:
    lines = [f"{payload['node_id']} admission: {payload['node_admission']}"]
    lines.extend(f"- {role}: {state}" for role, state in payload["role_admission"].items())
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
    if args.command == "route":
        try:
            route_result = route_task(
                args.root.resolve(),
                args.repository,
                args.architecture,
                tuple(args.role),
            )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            payload = {"decisions": [], "eligible_nodes": [], "error": str(exc), "ok": False}
            print(json.dumps(payload, sort_keys=True) if args.format == "json" else str(exc))
            return 1
        payload = route_result.as_dict()
        print(
            json.dumps(payload, sort_keys=True)
            if args.format == "json"
            else _render_route_human(payload)
        )
        return 0 if route_result.ok else 1
    if args.command == "overlay" and args.overlay_command == "validate":
        try:
            overlay_result = validate_overlay(args.root.resolve(), args.overlay.resolve())
        except (OSError, ValueError, yaml.YAMLError) as exc:
            payload = {"errors": [str(exc)], "nodes": [], "ok": False}
            print(json.dumps(payload, sort_keys=True) if args.format == "json" else str(exc))
            return 1
        payload = overlay_result.as_dict()
        print(
            json.dumps(payload, sort_keys=True)
            if args.format == "json"
            else _render_overlay_human(payload)
        )
        return 0 if overlay_result.ok else 1
    if args.command == "admission" and args.admission_command == "report":
        try:
            admission_report = generate_admission_report(
                args.profile,
                args.observations.resolve(),
                args.view,
            )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            payload = {"error": str(exc), "ok": False}
            print(json.dumps(payload, sort_keys=True) if args.format == "json" else str(exc))
            return 1
        payload = admission_report.as_dict()
        print(
            json.dumps(payload, sort_keys=True)
            if args.format == "json"
            else _render_admission_human(payload)
        )
        return 0 if admission_report.ok else 1
    raise AssertionError(f"unhandled command: {args.command}")
