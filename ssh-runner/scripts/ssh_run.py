#!/usr/bin/env python3
"""Run a bounded SSH command through an OpenSSH client."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(password\s*=\s*)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key\s*=\s*)[^\s]+"),
    re.compile(r"(?i)(token\s*=\s*)[^\s]+"),
    re.compile(r"(?i)(secret\s*=\s*)[^\s]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]

LOCAL_CONFIG_STARTER = """# Local-only OpenSSH host aliases.
# This file is intentionally ignored by Git.
#
# Example:
# Host example
#     HostName 192.0.2.10
#     User your-user
#     Port 22
"""

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDENTITY = SKILL_ROOT / "config" / "identities" / "default"


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout: str
    stderr: str


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        if pattern.flags & re.DOTALL:
            redacted = pattern.sub("[REDACTED PRIVATE KEY]", redacted)
        else:
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
    return redacted


def build_ssh_command(args: argparse.Namespace) -> list[str]:
    ssh = shutil.which("ssh")
    if ssh is None:
        raise SystemExit("OpenSSH client was not found on PATH.")

    command = [ssh]
    command.extend(
        [
            "-F",
            str(args.config),
            "-o",
            f"ConnectTimeout={args.connect_timeout}",
            "-o",
            "BatchMode=yes",
        ]
    )

    if args.identity is not None:
        command.extend(["-i", str(args.identity), "-o", "IdentitiesOnly=yes"])

    if args.accept_new_host_key:
        command.extend(["-o", "StrictHostKeyChecking=accept-new"])

    command.append(args.target)
    remote_command = args.remote_command
    if isinstance(remote_command, list):
        remote_command = normalize_remote_command(remote_command)
    command.append(remote_command)
    return command


def run(args: argparse.Namespace) -> RunResult:
    command = build_ssh_command(args)
    completed = subprocess.run(
        command,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=args.timeout,
        check=False,
    )
    return RunResult(
        exit_code=completed.returncode,
        stdout=redact(completed.stdout),
        stderr=redact(completed.stderr),
    )


def normalize_remote_command(parts: list[str]) -> str:
    if parts and parts[0] == "--":
        parts = parts[1:]
    return " ".join(parts).strip()


def ensure_local_config(config_path: Path) -> bool:
    if config_path.exists():
        return False
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(LOCAL_CONFIG_STARTER, encoding="utf-8", newline="\n")
    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a single remote command through an OpenSSH client.",
        epilog=(
            "Example: ssh_run.py --target example-host -- 'uname -a'"
        ),
    )
    parser.add_argument(
        "--identity",
        type=Path,
        default=DEFAULT_IDENTITY,
        help=(
            "Private-key path. Defaults to the Git-ignored skill-local "
            "config/identities/default file."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=SKILL_ROOT / "config" / "hosts.conf",
        help="OpenSSH host config. Defaults to this skill's config/hosts.conf.",
    )
    parser.add_argument("--target", required=True, help="Host alias from config/hosts.conf.")
    parser.add_argument("--timeout", type=int, default=120, help="Overall command timeout in seconds.")
    parser.add_argument("--connect-timeout", type=int, default=15, help="SSH connection timeout in seconds.")
    parser.add_argument(
        "--accept-new-host-key",
        action="store_true",
        help="Use StrictHostKeyChecking=accept-new after user confirmation.",
    )
    parser.add_argument("remote_command", nargs=argparse.REMAINDER, help="Remote shell command after --.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    args.remote_command = normalize_remote_command(args.remote_command)
    if not args.remote_command:
        print("Remote command is required after --.", file=sys.stderr)
        return 2
    if ensure_local_config(args.config):
        print(
            f"Created local SSH config starter: {args.config}\n"
            "Add authorized host aliases locally, then run the command again.",
            file=sys.stderr,
        )
        return 2
    if not args.config.is_file():
        print(f"SSH config does not exist: {args.config}", file=sys.stderr)
        return 2
    if not args.identity.is_file():
        print(
            "Skill-local SSH identity is missing. Ask the user for the exact path of an "
            "authorized private key, then copy it without reading its contents to: "
            f"{DEFAULT_IDENTITY}",
            file=sys.stderr,
        )
        return 2
    try:
        result = run(args)
    except subprocess.TimeoutExpired:
        print(f"SSH command timed out after {args.timeout} seconds.", file=sys.stderr)
        return 124

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
