# Secrets: Keychain and age-Encrypted Backup

## Policy

Every runtime secret consumed by any process under this repository must live in the macOS Keychain at runtime. Local `.env` files may contain only placeholder values (for example `API_KEY=REPLACE_ME`) and must never contain real credentials. Any iCloud-synced backup of Keychain items must be encrypted with `age` before synchronization. Plaintext backups of Keychain exports are forbidden.

A commit that introduces a real secret into any file on disk must not merge into the main branch. The `pre_tool_use.py` hook blocks the write before it lands.

## Scope

The policy applies to every class of secret consumed by local development, CI, and deployment tooling associated with this repository:

1. API keys for third-party services (Anthropic, OpenAI, Stripe, SendGrid, Twilio, GitHub, GitLab, etc.).
2. Database connection strings that include a password or any bearer credential (Postgres URIs with passwords, MongoDB connection strings, Redis URLs with auth).
3. OAuth client secrets, refresh tokens, and access tokens for any provider.
4. Signing keys for code signing, package publishing, and JWT issuance.
5. User passwords, service account passwords, and privileged database role passwords.
6. TLS private keys and certificate bundle passphrases.
7. SSH private keys used by local scripts or CI runners.
8. Webhook signing secrets.
9. Encryption keys for at-rest data (AES keys, `age` private keys, KMS CMK references).

## Keychain Commands

Use the built-in `security` tool on macOS. Every secret follows a consistent `service` and `account` naming convention so that other scripts can locate the item without hardcoding.

Service naming convention:

1. `service` is the reverse-domain identifier of the project followed by the logical secret name. Example: `com.example.myapp.anthropic_api_key`.
2. `account` is the human identity that owns the secret, typically the developer's email or a service account name. Example: `developer@example.com` or `ci-runner@example.com`.

Add a generic password:

```bash
security add-generic-password \
  -s "com.example.myapp.anthropic_api_key" \
  -a "developer@example.com" \
  -w \
  -U
```

Flags:

1. `-s` sets the service identifier.
2. `-a` sets the account identifier.
3. `-w` prompts for the password on stdin so the value never appears in shell history.
4. `-U` updates the item if it already exists.

Retrieve a generic password to stdout:

```bash
security find-generic-password \
  -s "com.example.myapp.anthropic_api_key" \
  -a "developer@example.com" \
  -w
```

Delete a generic password:

```bash
security delete-generic-password \
  -s "com.example.myapp.anthropic_api_key" \
  -a "developer@example.com"
```

List items matching a service prefix:

```bash
security dump-keychain | grep "com.example.myapp"
```

Export an item reference for use in a wrapper script:

```bash
MYAPP_ANTHROPIC_KEY="$(security find-generic-password \
  -s 'com.example.myapp.anthropic_api_key' \
  -a 'developer@example.com' \
  -w)"
```

## age Encryption for Backup

Any backup of Keychain items that leaves the local machine (iCloud Drive, Time Machine to an off-site volume, cloud storage) must be encrypted with `age` before synchronization. The repository stores the public key only; the private key lives in offline cold storage (for example, a hardware security key or a printed and vaulted paper backup).

Install `age`:

```bash
brew install age
```

Generate a key pair (one-time setup, run on an air-gapped machine if possible):

```bash
age-keygen -o ~/keys/backup-key.txt
```

The output file contains both the public key (on the first non-comment line, prefixed `age1`) and the private key (prefixed `AGE-SECRET-KEY-1`). Copy the public key into the repository at `docs/keys/backup-recipients.txt`. Move the file with the private key to cold storage and erase it from the working machine.

Encrypt a Keychain export before backup:

```bash
security dump-keychain -d ~/Library/Keychains/login.keychain-db > /tmp/keychain.plain
age --recipient "$(cat docs/keys/backup-recipients.txt)" \
    --output /tmp/keychain.age \
    /tmp/keychain.plain
shred -u /tmp/keychain.plain
```

Decrypt on recovery:

```bash
age --decrypt \
    --identity ~/keys/backup-key.txt \
    --output /tmp/keychain.plain \
    /tmp/keychain.age
```

Rules:

1. The plaintext dump must never be written to an iCloud-synced directory. Use `/tmp` or a non-synced path.
2. The plaintext file must be shredded with `shred -u` (or `rm -P` on macOS) immediately after encryption.
3. Multiple recipients may be specified with repeated `--recipient` flags, which lets a team share a backup without sharing a single private key.

## Environment Variable Injection

Processes that require secrets as environment variables must receive them through a wrapper script that reads the Keychain at invocation time and execs the target command with the variables set. This keeps the secret out of persistent shell history, `.env` files, process listings in stable scripts, and shell profile files.

Wrapper script pattern at `scripts/with-secrets.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ACCOUNT="developer@example.com"

fetch() {
  security find-generic-password \
    -s "com.example.myapp.$1" \
    -a "$ACCOUNT" \
    -w
}

export ANTHROPIC_API_KEY="$(fetch anthropic_api_key)"
export OPENAI_API_KEY="$(fetch openai_api_key)"
export DATABASE_URL="$(fetch database_url)"

exec "$@"
```

Invoke a command with secrets loaded:

```bash
./scripts/with-secrets.sh npm run dev
./scripts/with-secrets.sh python -m app
./scripts/with-secrets.sh pytest tests/integration
```

Rules:

1. The wrapper uses `exec` so the target process replaces the wrapper shell, which ensures the secret does not linger in a parent process environment.
2. `set -euo pipefail` forces an early exit if any Keychain lookup fails, preventing the target command from running with an empty secret.
3. The wrapper must not write the secret values to any file, log, or stderr. The Keychain fetch is the only point of disclosure.

## Forbidden Storage

The following storage locations are forbidden for real secrets:

1. Committed `.env` files that contain real values. The repository may contain `.env.example` with placeholder text (for example `API_KEY=REPLACE_ME`) but never the real key.
2. Android `SharedPreferences` or iOS `UserDefaults`. Both are readable by any other code running as the same user and are backed up unencrypted in many configurations.
3. Plain files under `~/` or `/etc/` (for example `~/.secrets`, `~/.config/app/key.txt`, `/etc/myapp.conf`).
4. Hardcoded string literals in source code, including template literals, base64-encoded strings, and "obfuscated" constants. Any attacker who obtains the binary can recover the secret in seconds.
5. Browser `localStorage`, `sessionStorage`, IndexedDB, and cookies that are not marked `Secure` and `HttpOnly`. JavaScript-accessible storage must never contain a long-lived credential.
6. Git submodules, Git LFS blobs, or private repositories that are not audited for access.
7. Notion, Confluence, Google Docs, Dropbox Paper, or any other shared-document platform.
8. Slack or Discord messages, even in private channels.
9. Paste buffers that sync across devices (Universal Clipboard, Paste app, etc.) while the clipboard contents are plaintext.
10. Screenshots, screen recordings, or presentation slides.

## CI Fallback

CI runners do not have access to the developer's macOS Keychain. Use a provider-native secret store instead. Never copy the Keychain contents into a CI configuration file.

Preferred providers by platform:

1. GitHub Actions: repository Secrets, environment Secrets, and organization Secrets. Reference with `${{ secrets.ANTHROPIC_API_KEY }}` in the workflow YAML. Prefer environment Secrets for per-environment gating.
2. Vercel: project Environment Variables scoped to Production, Preview, and Development. Reference with `process.env.ANTHROPIC_API_KEY` at build or runtime.
3. Doppler: configure a project and environment, install the Doppler CLI on the runner, and invoke commands under `doppler run -- <command>`. Doppler injects variables at exec time without writing them to disk.
4. AWS Secrets Manager or AWS Systems Manager Parameter Store: for long-lived infrastructure secrets accessed by Lambda, ECS, or EC2. Use IAM roles attached to the compute principal instead of bundling credentials.
5. GCP Secret Manager: for workloads running on Cloud Run, GKE, or Cloud Functions. Use Workload Identity instead of service account keys.
6. HashiCorp Vault: for on-premises or multi-cloud workloads that need central secret management. Configure dynamic database credentials when possible to reduce blast radius.

Rules for CI:

1. The workflow YAML must reference secrets by name only. No secret value appears in the workflow file.
2. The secret must be scoped to the minimum set of branches, environments, and workflows that need it.
3. The secret must never be echoed to stdout, written to an artifact, or exported to a public log.
4. The secret must be rotated when any maintainer who had access to it leaves the project.

## Enforcement

`pre_tool_use.py` (PreToolUse hook) scans every Write and Edit payload for patterns that indicate a real secret. A match blocks the tool invocation with a non-zero exit code and a diagnostic message naming the offending pattern and the line number.

Detected patterns:

1. Anthropic API keys: literal `sk-ant-` followed by 10 or more characters.
2. Anthropic project API keys: literal `sk-proj-` followed by 10 or more characters.
3. Generic secret keys: `sk-` followed by 20 or more alphanumeric characters.
4. AWS Access Key IDs: `AKIA` followed by 16 uppercase alphanumeric characters.
5. AWS secret access keys: `AWS_SECRET_ACCESS_KEY` assigned to a value of 20 or more characters.
6. PEM-encoded private keys: any five-dash `BEGIN` header containing `PRIVATE KEY` (RSA, EC, DSA, OPENSSH variants).
7. GitHub personal access tokens: `ghp_` or `ghs_` followed by 36 or more characters.
8. GitLab personal access tokens: `glpat-` followed by 20 or more characters.
9. Hardcoded Bearer tokens: literal `Bearer ` followed by 20 or more characters drawn from the alphanumeric, dash, or dot set.
10. Hardcoded `API_KEY` or `API_SECRET` assignments: either identifier on the left of `=` or `:` bound to a quoted string literal of 8 or more characters.
11. Hardcoded password assignments: `password`, `PASSWORD`, or `passwd` (case-insensitive) bound to a quoted string literal of 4 or more characters.

When the hook blocks a write, the diagnostic message states:

1. The file path of the target.
2. The pattern name that matched.
3. The line number of the match.
4. A remediation hint that points to this rule and suggests either rotating the leaked value or moving it into the Keychain.

The hook must fail closed. If the scan cannot run (for example because the pattern file is missing), the hook blocks the write by default and instructs the operator to investigate.

`review-agent` performs a secondary scan at the end of each pipeline run and flags any residual match as an imperfection, forcing a debugger pass before `decide-agent` can output COMPLETE.

CI jobs should run the same scan against the diff of every pull request and reject the build on any match.

## Rotation Policy

Any secret that is known to have left the secure perimeter must be rotated within 24 hours of discovery. The perimeter is breached whenever any of the following occurs:

1. The secret appears in a commit on any branch, including deleted branches (Git history retains the blob).
2. The secret appears in a build log, CI artifact, or error report that is accessible to anyone outside the list of authorized operators.
3. The secret is pasted into a chat, ticket, email, or document that is not end-to-end encrypted between authorized operators.
4. A workstation that had the secret in Keychain is lost, stolen, or reassigned.
5. A maintainer who had access to the secret leaves the project.

Rotation procedure:

1. Generate a new secret at the provider. Record the new value directly into the Keychain on the operator's machine. Never paste the value into a chat or document.
2. Update every consumer (local dev, CI secrets, production deploy) to reference the new value.
3. Revoke the old secret at the provider. Verify revocation by attempting a request with the old value and confirming it fails.
4. Create a decision record at `docs/decisions/NNNN-leak-<secret-name>.md` stating: the secret that leaked, the discovery channel, the estimated exposure window, the rotation timestamp, the operator who performed the rotation, and any lessons learned.
5. If the leak involves customer data access (for example a service-role key that can read every tenant), escalate to the security lead and assess whether a disclosure is required under applicable regulations.
6. If Git history contains the leaked blob, rewrite history to remove the blob only when the secret has been fully rotated. Force-pushing over a leaked blob does not remove it from clones and forks; rotation is the only reliable remedy.

Forbidden rotation shortcuts:

1. "We will rotate it next sprint." Rotation must complete within 24 hours.
2. Reusing the leaked value elsewhere. A leaked secret is dead; it cannot be redeployed.
3. Rotating without a decision record. Every rotation leaves an auditable trail.

## Related Rules

1. Rule 10, `10-rls.md`, Row-Level Security, for the database-level enforcement that protects user data when a credential is compromised.
2. Rule 11, `11-security-invoker.md`, for the view and function attributes that complement RLS and limit blast radius when service-role credentials are held by privileged consumers.
3. Rule 13, `13-spacemail-only.md`, for the permitted outbound mail provider that must be configured via a Keychain-stored SMTP credential, not a hardcoded value.
4. Rule 05, `05-operational-policies.md`, Anti-Destruction Rules, for the broader file safety framework that wraps secret handling.
5. Rule 08, `08-em-dash-ban.md`, for character sanitation on secret names, decision records, and rotation logs.
