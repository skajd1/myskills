---
name: ssh-runner
description: Run bounded SSH commands with an OpenSSH client and local-only host aliases. Use when a user asks Codex to connect to a configured server alias, inspect remote logs, processes, services, files, or deployments, or perform a specific remote maintenance command.
---

# SSH Runner

Use this skill for bounded private-key SSH command execution on servers the user is authorized to access.

## Essentials

1. Select a target alias from the local-only `config/hosts.conf` and get the remote command.
   - Never commit this file or disclose its contents.
   - If it is missing, run the runner once to create a commented local starter file, then add the authorized host aliases locally.
2. Let OpenSSH use the identity configured for the alias, or pass a local private-key path with `--identity`. Never read, print, copy, or commit key contents.
3. Keep normal host-key verification. Use `--accept-new-host-key` only after the user confirms the server identity.
4. Confirm before privileged, state-changing, destructive, reboot, service-stop, firewall, credential, database, or production deploy commands.
5. Summarize exit code and relevant output. Redact secrets from logs or command output.

## Runner

Use `scripts/ssh_run.py` from this skill directory with an available Python 3 interpreter. It invokes the OpenSSH client on `PATH` with this skill's local host config and `BatchMode=yes`. When `--identity` is supplied, it also applies `IdentitiesOnly=yes`. It does not support password authentication or manage key files.

```text
python scripts/ssh_run.py --target example-host -- "uname -a"
python scripts/ssh_run.py --target example-host -- "df -h"
python scripts/ssh_run.py --identity PATH_TO_PRIVATE_KEY --target example-host -- "tail -n 100 /var/log/app.log"
```

The `--` separator is required before the remote command. Prefer one bounded command over opening an interactive shell. Update the ignored, local-only `config/hosts.conf` only when aliases, hosts, users, or ports change. If the file is absent, the runner creates a commented starter file locally and exits so it can be configured before use.
