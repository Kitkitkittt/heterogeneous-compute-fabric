from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from fabric_cli.admission import required_checks, validate_profile_assignment
from fabric_cli.evidence import (
    ADMISSION_SCHEMA,
    new_admission_provenance,
    source_issue_number,
    source_issue_reference,
)
from fabric_cli.issues import IssueVerifier


@dataclass(frozen=True)
class ProbeResult:
    returncode: int | None
    outputs: tuple[str, ...]
    stderr: str


class ProbeAdapter(Protocol):
    @property
    def collector_id(self) -> str: ...

    def probe(self, check_name: str) -> ProbeResult: ...


@dataclass(frozen=True)
class FixtureProbeAdapter:
    results: dict[str, Any]

    @property
    def collector_id(self) -> str:
        return "fabric-cli/fixture-v1"

    @classmethod
    def from_path(cls, path: Path) -> FixtureProbeAdapter:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("probe results must contain an object")
        return cls(value)

    def probe(self, check_name: str) -> ProbeResult:
        value = self.results.get(check_name)
        if not isinstance(value, dict):
            return ProbeResult(None, (), "fixture has no result")
        returncode = value.get("returncode")
        outputs = value.get("outputs", [])
        stderr = value.get("stderr", "")
        if (
            not isinstance(returncode, int)
            or not isinstance(outputs, list)
            or not all(isinstance(output, str) for output in outputs)
            or not isinstance(stderr, str)
        ):
            raise ValueError(f"{check_name}: invalid fixture probe result")
        return ProbeResult(returncode, tuple(outputs), stderr)


ProbeCommands = tuple[tuple[str, ...], ...]
DISK_HEALTH_SCRIPT = """
import json
import subprocess
devices = subprocess.run(
    ["lsblk", "-dnpo", "NAME,TYPE"], check=True, capture_output=True, text=True
).stdout.splitlines()
disks = [line.split()[0] for line in devices if line.split()[-1] == "disk"]
results = [
    subprocess.run(["smartctl", "-H", disk], capture_output=True, text=True)
    for disk in disks
]
healthy = bool(results) and all(
    result.returncode in (0, 4) and "PASSED" in result.stdout.upper() for result in results
)
print(json.dumps({"all_healthy": healthy, "disk_count": len(disks)}))
raise SystemExit(0 if healthy else 1)
""".strip()
PROBE_COMMANDS: dict[str, ProbeCommands] = {
    "hardware": (("lscpu",), ("free", "--bytes")),
    "os_profile": (("cat", "/etc/os-release"),),
    "disk": (
        ("lsblk", "--json", "--output", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS"),
        ("python3", "-c", DISK_HEALTH_SCRIPT),
    ),
    "git_worktree": (
        ("git", "rev-parse", "--is-inside-work-tree"),
        ("git", "rev-parse", "--git-dir"),
        ("git", "rev-parse", "--git-common-dir"),
        ("git", "symbolic-ref", "--short", "HEAD"),
        ("git", "status", "--porcelain"),
    ),
    "time_sync": (("timedatectl", "show", "--property=NTPSynchronized", "--value"),),
    "software_updates": (("apt-get", "--simulate", "upgrade"),),
    "firewall": (("ufw", "status"),),
    "container_execution": (
        (
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "busybox:1.36",
            "echo",
            "container-smoke-ok",
        ),
    ),
    "load_thermals": (
        ("python3", "-c", "print('bounded-load-ok' if sum(i*i for i in range(100000)) else '')"),
        ("sensors", "-j"),
    ),
    "cpu_execution": (("python3", "-c", "print(sum(i*i for i in range(100000)))"),),
    "memory_execution": (("python3", "-c", "x=bytearray(16777216); x[0]=1; print(len(x))"),),
    "nvidia_identity": (("nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"),),
    "nvidia_driver": (("nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"),),
    "host_gpu_smoke": (
        (
            "python3",
            "-c",
            "import torch; assert torch.cuda.is_available(); "
            "x=torch.ones((64,64),device='cuda'); assert float((x@x).sum())>0; "
            "print('cuda-smoke-ok')",
        ),
    ),
    "container_toolkit": (("nvidia-ctk", "--version"),),
    "gpu_container_smoke": (
        (
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--gpus",
            "all",
            "nvidia/cuda:12.6.0-base-ubuntu24.04",
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
        ),
    ),
    "displays": (("xrandr", "--query"),),
    "browser_acceleration": (("chromium", "--headless=new", "--dump-dom", "chrome://gpu"),),
    "suspend_resume": (("journalctl", "-b", "-1", "--no-pager", "-n", "200"),),
    "shutdown_reboot": (("last", "-x", "-n", "20"),),
    "ethernet": (("networkctl", "status"),),
    "wifi": (("iw", "dev"),),
    "bluetooth": (("bluetoothctl", "show"),),
    "audio": (("pactl", "info"),),
    "usb": (("lsusb",),),
    "editor_toolchain": (("git", "--version"),),
    "containers": (("docker", "info"),),
    "graphics_smoke": (("glxinfo", "-B"),),
    "secure_boot_policy": (("mokutil", "--sb-state"),),
}


@dataclass(frozen=True)
class LinuxLocalProbeAdapter:
    cwd: Path
    private_network_target: str
    ssh_destination: str
    disk_encryption_required: bool
    minimum_free_bytes: int
    timeout_seconds: int = 30

    @property
    def collector_id(self) -> str:
        return "fabric-cli/linux-local-v1"

    def probe(self, check_name: str) -> ProbeResult:
        commands = (
            (
                ("tailscale", "ping", "--c", "1", self.private_network_target),
                (
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "PasswordAuthentication=no",
                    "-o",
                    "KbdInteractiveAuthentication=no",
                    "-o",
                    "ConnectTimeout=10",
                    self.ssh_destination,
                    "true",
                ),
                ("sshd", "-T"),
            )
            if check_name == "network_ssh"
            else (
                (
                    (
                        "python3",
                        "-c",
                        _disk_policy_script(
                            self.disk_encryption_required,
                            self.minimum_free_bytes,
                        ),
                    ),
                )
                if check_name == "disk_encryption_headroom"
                else PROBE_COMMANDS.get(check_name)
            )
        )
        if commands is None:
            return ProbeResult(None, (), "no safe automated probe is defined")
        outputs: list[str] = []
        errors: list[str] = []
        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    cwd=self.cwd,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    check=False,
                    timeout=self.timeout_seconds,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                return ProbeResult(None, tuple(outputs), type(exc).__name__)
            outputs.append(result.stdout.strip())
            if result.stderr.strip():
                errors.append(result.stderr.strip())
            if result.returncode != 0:
                return ProbeResult(result.returncode, tuple(outputs), "\n".join(errors))
        return ProbeResult(0, tuple(outputs), "\n".join(errors))


def _json_object(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _thermal_reading(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_thermal_reading(child) for child in value.values())
    if isinstance(value, list):
        return any(_thermal_reading(child) for child in value)
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value < 110


def _disk_policy_script(encryption_required: bool, minimum_free_bytes: int) -> str:
    return "\n".join(
        (
            "import json, shutil, subprocess",
            "source = subprocess.run(['findmnt', '-n', '-o', 'SOURCE', '/'], "
            "check=True, capture_output=True, text=True).stdout.strip().split('[', 1)[0]",
            "types = subprocess.run(['lsblk', '-s', '-n', '-o', 'TYPE', source], "
            "check=True, capture_output=True, text=True).stdout.strip().splitlines()",
            "encrypted = 'crypt' in types",
            f"required = {encryption_required!r}",
            f"minimum = {minimum_free_bytes}",
            "free = shutil.disk_usage('/').free",
            "value = {'encrypted': encrypted, 'encryption_required': required, "
            "'free_bytes': free, 'minimum_free_bytes': minimum, "
            "'policy_match': encrypted == required and free >= minimum}",
            "print(json.dumps(value, sort_keys=True))",
            "raise SystemExit(0 if value['policy_match'] else 1)",
        )
    )


def _issue_branch_matches_source(branch: str, source_ref: str) -> bool:
    branch_match = re.fullmatch(r"codex/(\d+)-[a-z0-9][a-z0-9-]*", branch)
    issue_number = source_issue_number(source_ref)
    return bool(branch_match and issue_number and int(branch_match.group(1)) == issue_number)


def _semantic_pass(
    check_name: str,
    outputs: tuple[str, ...],
    os_profile: str,
    source_ref: str,
) -> bool:
    joined = "\n".join(outputs)
    lowered = joined.casefold()
    predicates: dict[str, Callable[[], bool]] = {
        "hardware": lambda: len(outputs) == 2 and "architecture:" in lowered and "mem:" in lowered,
        "disk": lambda: (
            len(outputs) == 2
            and bool((_json_object(outputs[0]) or {}).get("blockdevices"))
            and bool((_json_object(outputs[1]) or {}).get("all_healthy"))
            and int((_json_object(outputs[1]) or {}).get("disk_count", 0)) > 0
        ),
        "disk_encryption_headroom": lambda: bool(
            len(outputs) == 1
            and (_json_object(outputs[0]) or {}).get("policy_match") is True
            and int((_json_object(outputs[0]) or {}).get("free_bytes", 0))
            >= int((_json_object(outputs[0]) or {}).get("minimum_free_bytes", 1))
        ),
        "time_sync": lambda: outputs == ("yes",),
        "software_updates": lambda: bool(outputs and re.search(r"\b0 upgraded\b", lowered)),
        "firewall": lambda: "status: active" in lowered,
        "network_ssh": lambda: (
            len(outputs) == 3
            and "pong from" in outputs[0].casefold()
            and outputs[1] == ""
            and "pubkeyauthentication yes" in lowered
            and "passwordauthentication no" in lowered
        ),
        "git_worktree": lambda: (
            len(outputs) == 5
            and outputs[0] == "true"
            and "/worktrees/" in outputs[1].replace("\\", "/")
            and "/worktrees/" not in outputs[2].replace("\\", "/")
            and _issue_branch_matches_source(outputs[3], source_ref)
            and outputs[4] == ""
        ),
        "container_execution": lambda: outputs == ("container-smoke-ok",),
        "load_thermals": lambda: (
            len(outputs) == 2
            and outputs[0] == "bounded-load-ok"
            and _thermal_reading(_json_object(outputs[1]))
        ),
        "cpu_execution": lambda: outputs == ("333328333350000",),
        "memory_execution": lambda: outputs == ("16777216",),
        "nvidia_identity": lambda: bool(outputs and outputs[0] and "n/a" not in lowered),
        "nvidia_driver": lambda: bool(outputs and re.fullmatch(r"\d+(?:\.\d+)+", outputs[0])),
        "host_gpu_smoke": lambda: outputs == ("cuda-smoke-ok",),
        "container_toolkit": lambda: bool(
            outputs and "nvidia" in lowered and re.search(r"\d+\.\d+", joined)
        ),
        "gpu_container_smoke": lambda: bool(
            outputs
            and outputs[0]
            and "n/a" not in lowered
            and any(marker in lowered for marker in ("nvidia", "rtx", "a100", "h100"))
        ),
        "displays": lambda: " connected" in lowered,
        "browser_acceleration": lambda: (
            "graphics feature status" in lowered and "hardware accelerated" in lowered
        ),
        "suspend_resume": lambda: "suspend" in lowered and "resume" in lowered,
        "shutdown_reboot": lambda: "reboot" in lowered and "shutdown" in lowered,
        "ethernet": lambda: "routable" in lowered or "configured" in lowered,
        "wifi": lambda: "interface" in lowered,
        "bluetooth": lambda: "powered: yes" in lowered,
        "audio": lambda: "server name" in lowered,
        "usb": lambda: " id " in lowered,
        "editor_toolchain": lambda: lowered.startswith("git version "),
        "containers": lambda: "server version" in lowered,
        "graphics_smoke": lambda: "direct rendering: yes" in lowered,
        "secure_boot_policy": lambda: (
            "secureboot enabled" in lowered or "secureboot disabled" in lowered
        ),
    }
    if check_name == "os_profile":
        expected_id = "pop" if os_profile == "pop24" else "ubuntu"
        expected_version = "26.04" if os_profile == "ubuntu26" else "24.04"
        return f"id={expected_id}" in lowered and f'version_id="{expected_version}"' in lowered
    predicate = predicates.get(check_name)
    return predicate() if predicate is not None else False


def collect_observations(
    node_id: str,
    role_profile: str,
    os_profile: str,
    adapter: ProbeAdapter,
    output_path: Path,
    source_ref: str,
    issue_verifier: IssueVerifier,
) -> dict[str, Any]:
    validate_profile_assignment(node_id, role_profile, os_profile)
    provenance = new_admission_provenance(adapter.collector_id, source_ref)
    issue_reference = source_issue_reference(source_ref)
    if issue_reference is None:
        raise ValueError("admission provenance requires a public-safe GitHub issue source")
    source_repository, source_issue = issue_reference
    checks: dict[str, Any] = {}
    for check_name in required_checks(role_profile, os_profile):
        result = adapter.probe(check_name)
        if result.returncode is None:
            status = "unknown"
        elif result.returncode != 0 or not _semantic_pass(
            check_name,
            result.outputs,
            os_profile,
            source_ref,
        ):
            status = "fail"
        elif check_name == "git_worktree":
            try:
                authority = issue_verifier.verify(source_issue, result.outputs[3])
            except ValueError:
                status = "fail"
            else:
                status = "pass" if authority.get("repository") == source_repository else "fail"
        else:
            status = "pass"
        private_evidence = "\n".join((*result.outputs, result.stderr)).strip()
        public_status = "passed" if status == "pass" else status
        checks[check_name] = {
            "private_evidence": private_evidence or None,
            "public_evidence": f"{check_name} probe {public_status}",
            "status": status,
        }
    document = {
        "checks": checks,
        "node_id": node_id,
        "os_profile": os_profile,
        "role_profile": role_profile,
        "schema": ADMISSION_SCHEMA,
        **provenance.as_dict(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return {
        "check_count": len(checks),
        "node_id": node_id,
        "ok": True,
        "output_written": True,
        "role_profile": role_profile,
    }
