from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from fabric_cli.admission import generate_admission_report
from fabric_cli.evidence import source_issue_reference
from fabric_cli.frontier import FileIssueSource, GithubIssueSource, build_frontier
from fabric_cli.io import load_mapping
from fabric_cli.issues import FixtureIssueVerifier, GithubIssueVerifier, IssueVerifier
from fabric_cli.overlay import validate_overlay
from fabric_cli.pilot import RecordOnlyDeploymentAdapter, run_pilot
from fabric_cli.probes import (
    FixtureProbeAdapter,
    LinuxLocalProbeAdapter,
    ProbeAdapter,
    collect_observations,
)
from fabric_cli.routing import route_task
from fabric_cli.validation import validate_public_registry


def _current_worktree_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError("admission report must run from an issue worktree")
    return Path(result.stdout.strip()).resolve()


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
    admission_report.add_argument("--node-id", required=True)
    admission_report.add_argument(
        "--role-profile", choices=("compute", "workstation"), required=True
    )
    admission_report.add_argument(
        "--os-profile", choices=("ubuntu24", "ubuntu26", "pop24"), required=True
    )
    admission_report.add_argument("--observations", type=Path, required=True)
    admission_report.add_argument("--replay-ledger", type=Path, required=True)
    admission_report.add_argument("--view", choices=("public", "private"), default="public")
    admission_report.add_argument("--format", choices=("human", "json"), default="human")
    admission_collect = admission_subparsers.add_parser(
        "collect", help="collect read-only Linux admission observations"
    )
    admission_collect.add_argument("--node-id", required=True)
    admission_collect.add_argument(
        "--role-profile", choices=("compute", "workstation"), required=True
    )
    admission_collect.add_argument(
        "--os-profile", choices=("ubuntu24", "ubuntu26", "pop24"), required=True
    )
    admission_collect.add_argument(
        "--adapter", choices=("linux-local", "fixture"), default="linux-local"
    )
    admission_collect.add_argument("--probe-results", type=Path)
    admission_collect.add_argument("--issue-evidence", type=Path)
    admission_collect.add_argument("--probe-config", type=Path)
    admission_collect.add_argument("--probe-cwd", type=Path, default=Path.cwd())
    admission_collect.add_argument("--source-ref", required=True)
    admission_collect.add_argument("--output", type=Path, required=True)
    admission_collect.add_argument("--format", choices=("human", "json"), default="human")

    frontier = subparsers.add_parser("frontier", help="report the actionable issue frontier")
    frontier.add_argument("--root", type=Path, default=Path.cwd())
    frontier_source = frontier.add_mutually_exclusive_group(required=True)
    frontier_source.add_argument("--issues-file", type=Path)
    frontier_source.add_argument("--repository")
    frontier.add_argument("--format", choices=("human", "json"), default="human")

    pilot = subparsers.add_parser("pilot", help="run a deterministic bounded pilot")
    pilot.add_argument("--root", type=Path, default=Path.cwd())
    pilot.add_argument("--request", type=Path, required=True)
    pilot_issue_source = pilot.add_mutually_exclusive_group(required=True)
    pilot_issue_source.add_argument("--issue-repository")
    pilot_issue_source.add_argument("--issue-evidence", type=Path)
    pilot.add_argument("--worktree", type=Path, required=True)
    pilot.add_argument("--artifact", type=Path, required=True)
    pilot.add_argument("--review-evidence", type=Path, required=True)
    pilot.add_argument("--test-evidence", type=Path, required=True)
    pilot.add_argument("--health-evidence", type=Path, required=True)
    pilot.add_argument("--rollback-evidence", type=Path, required=True)
    pilot.add_argument("--receipt", type=Path, required=True)
    pilot.add_argument("--deployment-authorized", action="store_true")
    pilot.add_argument("--format", choices=("human", "json"), default="human")
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


def _render_frontier_human(payload: dict[str, Any]) -> str:
    lines = ["Actionable frontier"]
    for issue in payload["frontier"]:
        nodes = ", ".join(issue["suitable_nodes"]) or "no node label"
        lines.append(f"- #{issue['number']} [{issue['next_actor']}] {issue['title']} ({nodes})")
        lines.extend(
            f"  - {conflict['node_id']}: {conflict['admission_state']}"
            for conflict in issue["node_conflicts"]
        )
    return "\n".join(lines)


def _render_pilot_human(payload: dict[str, Any]) -> str:
    return (
        f"Pilot recorded: {payload['worker']} -> "
        f"sha256:{payload['artifact']['sha256']} -> record-only deployment"
    )


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
            replay_ledger = args.replay_ledger.resolve()
            if replay_ledger.is_relative_to(_current_worktree_root()):
                raise ValueError("private replay ledger must be outside the current worktree")
            admission_report = generate_admission_report(
                args.node_id,
                args.role_profile,
                args.os_profile,
                args.observations.resolve(),
                replay_ledger,
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
    if args.command == "admission" and args.admission_command == "collect":
        try:
            probe_cwd = args.probe_cwd.resolve()
            output_path = args.output.resolve()
            if output_path.is_relative_to(probe_cwd):
                raise ValueError("private observations must be written outside the probed worktree")
            adapter: ProbeAdapter
            source_issue = source_issue_reference(args.source_ref)
            if source_issue is None:
                raise ValueError("--source-ref must identify a public GitHub issue")
            if args.adapter == "fixture":
                if args.probe_results is None:
                    raise ValueError("--probe-results is required for the fixture adapter")
                if args.issue_evidence is None:
                    raise ValueError("--issue-evidence is required for the fixture adapter")
                adapter = FixtureProbeAdapter.from_path(args.probe_results.resolve())
                admission_issue_verifier: IssueVerifier = FixtureIssueVerifier.from_path(
                    args.issue_evidence.resolve()
                )
            else:
                if args.probe_results is not None:
                    raise ValueError("--probe-results is valid only with the fixture adapter")
                if args.issue_evidence is not None:
                    raise ValueError("--issue-evidence is valid only with the fixture adapter")
                if args.probe_config is None:
                    raise ValueError("--probe-config is required for the linux-local adapter")
                probe_config_path = args.probe_config.resolve()
                if probe_config_path.is_relative_to(probe_cwd):
                    raise ValueError(
                        "private probe configuration must be outside the probed worktree"
                    )
                probe_config = load_mapping(probe_config_path, "private probe configuration")
                private_network_target = probe_config.get("private_network_target")
                ssh_destination = probe_config.get("ssh_destination")
                disk_encryption_required = probe_config.get("disk_encryption_required")
                minimum_free_gib = probe_config.get("minimum_free_gib")
                if not isinstance(private_network_target, str) or not private_network_target:
                    raise ValueError("private probe configuration requires private_network_target")
                if not isinstance(ssh_destination, str) or not ssh_destination:
                    raise ValueError("private probe configuration requires ssh_destination")
                if not isinstance(disk_encryption_required, bool):
                    raise ValueError(
                        "private probe configuration requires disk_encryption_required"
                    )
                if (
                    not isinstance(minimum_free_gib, int)
                    or isinstance(minimum_free_gib, bool)
                    or minimum_free_gib <= 0
                ):
                    raise ValueError("private probe configuration requires minimum_free_gib")
                adapter = LinuxLocalProbeAdapter(
                    probe_cwd,
                    private_network_target,
                    ssh_destination,
                    disk_encryption_required,
                    minimum_free_gib * 1024**3,
                )
                admission_issue_verifier = GithubIssueVerifier(source_issue[0])
            payload = collect_observations(
                args.node_id,
                args.role_profile,
                args.os_profile,
                adapter,
                output_path,
                args.source_ref,
                admission_issue_verifier,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload = {"error": str(exc), "ok": False}
            print(json.dumps(payload, sort_keys=True) if args.format == "json" else str(exc))
            return 1
        print(
            json.dumps(payload, sort_keys=True)
            if args.format == "json"
            else f"Collected {payload['check_count']} checks for {payload['node_id']}"
        )
        return 0
    if args.command == "frontier":
        try:
            source = (
                FileIssueSource(args.issues_file.resolve())
                if args.issues_file is not None
                else GithubIssueSource(args.repository)
            )
            frontier_report = build_frontier(args.root.resolve(), source)
        except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
            payload = {"error": str(exc), "frontier": [], "ok": False}
            print(json.dumps(payload, sort_keys=True) if args.format == "json" else str(exc))
            return 1
        payload = frontier_report.as_dict()
        print(
            json.dumps(payload, sort_keys=True)
            if args.format == "json"
            else _render_frontier_human(payload)
        )
        return 0
    if args.command == "pilot":
        try:
            issue_verifier: IssueVerifier = (
                FixtureIssueVerifier.from_path(args.issue_evidence.resolve())
                if args.issue_evidence is not None
                else GithubIssueVerifier(args.issue_repository)
            )
            payload = run_pilot(
                args.root.resolve(),
                args.request.resolve(),
                args.worktree.resolve(),
                args.artifact.resolve(),
                args.review_evidence.resolve(),
                args.test_evidence.resolve(),
                args.health_evidence.resolve(),
                args.rollback_evidence.resolve(),
                args.deployment_authorized,
                issue_verifier,
                RecordOnlyDeploymentAdapter(args.receipt.resolve()),
            )
        except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
            payload = {"error": str(exc), "ok": False}
            print(json.dumps(payload, sort_keys=True) if args.format == "json" else str(exc))
            return 1
        print(
            json.dumps(payload, sort_keys=True)
            if args.format == "json"
            else _render_pilot_human(payload)
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
