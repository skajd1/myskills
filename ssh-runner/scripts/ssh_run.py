#!/usr/bin/env python3
"""Run a bounded private-key SSH command through Windows OpenSSH."""

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
        raise SystemExit("Windows OpenSSH client was not found on PATH.")

    command = [ssh]
    command.extend(
        [
            "-F",
            str(args.config),
            "-i",
            str(args.identity),
            "-o",
            f"ConnectTimeout={args.connect_timeout}",
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
        ]
    )

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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a single remote command through Windows OpenSSH with a private key.",
        epilog=(
            "Example: ssh_run.py --target 85 -- 'uname -a'"
        ),
    )
    skill_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--identity",
        type=Path,
        default=Path.home() / ".ssh" / "uface_id_rsa",
        help="Local private-key path. Defaults to ~/.ssh/uface_id_rsa.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=skill_root / "config" / "hosts.conf",
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
    if not args.config.is_file():
        print(f"SSH config does not exist: {args.config}", file=sys.stderr)
        return 2
    if not args.identity.is_file():
        print(f"Identity file does not exist: {args.identity}", file=sys.stderr)
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
