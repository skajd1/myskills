---
name: ssh-runner
description: Connect to user-specified SSH servers and run remote shell commands. Use when a user asks Codex to SSH into a server by host, port, account, password, identity file, jump host, or SSH config alias; inspect remote logs, processes, services, files, or deployments; or run bounded maintenance commands with safety checks.
---

# SSH Runner

Use this skill for bounded SSH command execution on servers the user is authorized to access.

## Essentials

1. Get the target, port, account/auth method, and remote command. Infer from `~/.ssh/config` only when clear.
2. If the user provides a password, use password mode with `--password-env`; never pass the password as a command-line argument.
3. Keep normal host-key verification. Use `--accept-new-host-key` only after the user confirms the server identity.
4. Confirm before privileged, state-changing, destructive, reboot, service-stop, firewall, credential, database, or production deploy commands.
5. Summarize exit code and relevant output. Redact secrets from logs or command output.

## Runner

Use `scripts/ssh_run.py` from this skill directory with the user-level Python below by default. Do not create a separate Paramiko/parakimo implementation or use a project virtualenv unless the user asks.

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --target user@example.com --port 22 -- "uname -a"
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --target my-ssh-alias -- "df -h"
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --target app@example.com --jump bastion@example.com -- "tail -n 100 /var/log/app.log"
$env:SSH_RUN_PASSWORD = '<password>'; & 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --target user@example.com --password-env SSH_RUN_PASSWORD -- "whoami"
```

Password mode requires Paramiko in `C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe`. The `--` separator is required before the remote command. Prefer one bounded command over opening an interactive shell.
