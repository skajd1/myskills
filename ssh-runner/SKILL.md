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
2. Store the authorized private key at the skill-local `config/identities/default` path, which is ignored by Git.
   - If that file exists, always use it for SSH commands; do not search the home directory or let OpenSSH choose another identity.
   - If it is missing, ask the user for the exact path of an existing authorized private key before attempting SSH. After the user identifies it, copy (do not move) it to `config/identities/default`, restrict access to the current user where supported, and never read or print its contents.
   - Never commit the private key or any file under `config/identities/`.
3. Keep normal host-key verification. Use `--accept-new-host-key` only after the user confirms the server identity.
4. Confirm before privileged, state-changing, destructive, reboot, service-stop, firewall, credential, database, or production deploy commands.
5. Summarize exit code and relevant output. Redact secrets from logs or command output.

## Runner

Use `scripts/ssh_run.py` from this skill directory with an available Python 3 interpreter. It invokes the OpenSSH client on `PATH` with this skill's local host config, `BatchMode=yes`, the skill-local `config/identities/default` private key, and `IdentitiesOnly=yes`. It does not support password authentication. The runner fails with a setup message when the skill-local key is missing; ask the user for the source key path and copy it into place before retrying.

```text
python scripts/ssh_run.py --target example-host -- "uname -a"
python scripts/ssh_run.py --target example-host -- "df -h"
```

The `--` separator is required before the remote command. Prefer one bounded command over opening an interactive shell. Update the ignored, local-only `config/hosts.conf` only when aliases, hosts, users, or ports change. If the file is absent, the runner creates a commented starter file locally and exits so it can be configured before use. Use `--identity` only as an explicitly authorized exceptional override; normal runs must use `config/identities/default`.
