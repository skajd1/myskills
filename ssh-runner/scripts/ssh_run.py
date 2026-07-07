#!/usr/bin/env python3
"""Run a bounded SSH command with OpenSSH or optional password auth."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass


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
        raise SystemExit("OpenSSH client was not found on PATH.")

    command = [ssh, "-p", str(args.port), "-o", f"ConnectTimeout={args.connect_timeout}"]

    if args.batch_mode:
        command.extend(["-o", "BatchMode=yes"])
    if args.accept_new_host_key:
        command.extend(["-o", "StrictHostKeyChecking=accept-new"])
    if args.identity:
        command.extend(["-i", args.identity])
    if args.jump:
        command.extend(["-J", args.jump])

    command.append(args.target)
    command.append(args.remote_command)
    return command


def split_target(args: argparse.Namespace) -> tuple[str, str]:
    if args.username:
        return args.username, args.target
    if "@" in args.target:
        username, host = args.target.rsplit("@", 1)
        if username and host:
            return username, host
    raise SystemExit("Password mode requires --username or a user@host target.")


def run_paramiko(args: argparse.Namespace, password: str) -> RunResult:
    try:
        import paramiko
    except ImportError as exc:
        raise SystemExit(
            "Password mode requires Paramiko. Install it with: python -m pip install paramiko"
        ) from exc

    if args.identity:
        raise SystemExit("Password mode does not use --identity. Use key auth without --password-env.")
    if args.jump:
        raise SystemExit("Password mode does not support --jump. Use SSH config/key auth for jump hosts.")

    username, host = split_target(args)
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if args.accept_new_host_key:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

    try:
        client.connect(
            hostname=host,
            port=args.port,
            username=username,
            password=password,
            timeout=args.connect_timeout,
            banner_timeout=args.connect_timeout,
            auth_timeout=args.connect_timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        stdin, stdout, stderr = client.exec_command(args.remote_command, timeout=args.timeout)
        stdin.close()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        return RunResult(
            exit_code=stdout.channel.recv_exit_status(),
            stdout=redact(out),
            stderr=redact(err),
        )
    finally:
        client.close()


def run(args: argparse.Namespace) -> RunResult:
    if args.password_env:
        password = os.environ.get(args.password_env)
        if not password:
            raise SystemExit(f"Environment variable is not set: {args.password_env}")
        return run_paramiko(args, password)

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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a single remote command through OpenSSH.",
        epilog="Example: ssh_run.py --target user@example.com --port 22 -- 'uname -a'",
    )
    parser.add_argument("--target", required=True, help="SSH target, such as host alias or user@host.")
    parser.add_argument("--port", type=int, default=22, help="SSH port. Defaults to 22.")
    parser.add_argument("--identity", help="Path to a private key file. Do not pass key contents.")
    parser.add_argument("--username", help="Username for password mode when --target is a bare host.")
    parser.add_argument(
        "--password-env",
        help="Read SSH password from this environment variable and use Paramiko password auth.",
    )
    parser.add_argument("--jump", help="Optional ProxyJump target, such as bastion@example.com.")
    parser.add_argument("--timeout", type=int, default=120, help="Overall command timeout in seconds.")
    parser.add_argument("--connect-timeout", type=int, default=15, help="SSH connection timeout in seconds.")
    parser.add_argument(
        "--accept-new-host-key",
        action="store_true",
        help="Use StrictHostKeyChecking=accept-new after user confirmation.",
    )
    parser.add_argument(
        "--no-batch-mode",
        dest="batch_mode",
        action="store_false",
        help="Allow interactive auth prompts. Use only when the user requested it.",
    )
    parser.add_argument("remote_command", nargs=argparse.REMAINDER, help="Remote shell command after --.")
    parser.set_defaults(batch_mode=True)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    args.remote_command = " ".join(args.remote_command).strip()
    if args.port < 1 or args.port > 65535:
        print("Port must be between 1 and 65535.", file=sys.stderr)
        return 2
    if not args.remote_command:
        print("Remote command is required after --.", file=sys.stderr)
        return 2
    if args.identity and not os.path.exists(args.identity):
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
