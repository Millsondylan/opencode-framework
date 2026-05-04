---
description: "Provision a new project atomically: repo, Supabase, Cloudflare, GitHub, Keychain"
---

# /bootstrap

Spin up a new project with every provider wired consistently. `/bootstrap` calls the `bootstrap/bootstrap` script that provisions a git repo, a Supabase project with RLS on, a Cloudflare Pages and Workers deployment, a GitHub remote, and Keychain secret entries, all atomically with rollback on partial failure. Per ADR-0030, manual per-provider setup is prohibited.

## Arguments

- `<stack>`: one of `flutter`, `nextjs`, `expo`, `cli`, `api`. Selects the starter template and the provider wiring profile.
- `<name>`: project slug in kebab-case, used as the repo name, the Supabase project name, the Cloudflare project name, and the Keychain service prefix.
- `--org <org>`: GitHub org for the remote. Defaults to the authenticated user.
- `--region <region>`: Supabase region. Defaults to `us-east-1`.
- `--private`: create the GitHub repo as private. Defaults to private.
- `--skip <provider>`: skip a specific provider (`supabase`, `cloudflare`, `github`, `keychain`). Repeatable.

## Pipeline

Runs the bootstrap sequence under a single atomic transaction with rollback on failure:

1. local repo init (git init, starter template from `bootstrap/templates/<stack>/`, first commit)
2. Supabase project create (RLS enabled default per ADR-0006, `security_invoker` default per ADR-0007)
3. Cloudflare Pages project create plus Workers binding (Next.js stacks only, per ADR-0026)
4. GitHub repo create plus remote push (respects `--private` and `--org`)
5. Keychain secret entries for all credentials (Supabase anon, service role, Cloudflare API token, GitHub PAT) per ADR-0008
6. `.env.example` generation with placeholder values only (never real secrets)
7. rollback handler: on any failure, delete partially-created resources and the repo, restoring the pre-bootstrap state

## Example

```
/bootstrap flutter finance-tracker
/bootstrap nextjs marketing-site --org mycompany --region eu-west-1
/bootstrap cli dev-tools --skip cloudflare --skip supabase
```

## Related

- ADR-0030 (bootstrap provisions all providers atomically)
- ADR-0006 (RLS on every table), ADR-0007 (security_invoker on every view)
- ADR-0008 (Keychain plus age-encrypted backup for secrets)
- ADR-0026 (Cloudflare Pages + Workers for Next.js)
- `bootstrap/bootstrap` script for the implementation
- `/ship` for the first pipeline run after bootstrap completes
