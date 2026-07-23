---
name: ssh-runner
description: Run bounded SSH commands with Windows OpenSSH, a local private key, and tracked host aliases. Use when a user asks Codex to connect to a configured server alias, inspect remote logs, processes, services, files, or deployments, or perform a specific remote maintenance command.
---

# SSH Runner

Use this skill for bounded private-key SSH command execution on servers the user is authorized to access.

## Essentials

1. Select a target alias from `config/hosts.conf` and get the remote command.
2. Use `%USERPROFILE%\.ssh\uface_id_rsa` by default or pass another local key with `--identity`. Never read, print, copy, or commit key contents.
3. Keep normal host-key verification. Use `--accept-new-host-key` only after the user confirms the server identity.
4. Confirm before privileged, state-changing, destructive, reboot, service-stop, firewall, credential, database, or production deploy commands.
5. Summarize exit code and relevant output. Redact secrets from logs or command output.

## Runner

Use `scripts/ssh_run.py` from this skill directory with the user-level Python below. It invokes Windows OpenSSH with this skill's host config, `BatchMode=yes`, and `IdentitiesOnly=yes`. It does not support password authentication or manage key files.

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --target 85 -- "uname -a"
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --target 103d -- "df -h"
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' scripts/ssh_run.py --identity C:\Users\wooch\.ssh\another_key --target ktnf -- "tail -n 100 /var/log/app.log"
```

The `--` separator is required before the remote command. Prefer one bounded command over opening an interactive shell. Update `config/hosts.conf` only when aliases, hosts, users, or ports change.
