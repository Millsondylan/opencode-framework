# Security Invoker (Views and Functions)

## Policy

Every Postgres view created or modified during pipeline execution must be defined with the `security_invoker = on` option. Every Postgres function must default to `SECURITY INVOKER`. The `SECURITY DEFINER` attribute is permitted only for functions that carry a documented justification in an inline comment block and a paired entry in `docs/decisions/`.

Scope:

1. Every `CREATE VIEW` in any migration file under `supabase/migrations/`, `db/migrations/`, or equivalent.
2. Every `CREATE OR REPLACE VIEW` statement.
3. Every `ALTER VIEW` that retrofits view options on an existing view.
4. Every `CREATE FUNCTION` and `CREATE OR REPLACE FUNCTION` statement, regardless of language (SQL, PL/pgSQL, PL/Python, PL/v8).
5. Every Supabase Studio view or function created through the dashboard.
6. Every ORM generated view or function (Prisma raw migrations, Drizzle custom SQL, etc.).

A migration that introduces a view without `WITH (security_invoker = on)` must not merge into the main branch. A migration that introduces a `SECURITY DEFINER` function without an accompanying justification block must also not merge.

## Rationale

1. Row-Level Security policies on the underlying tables apply only when the view runs as the invoker. By default, Postgres views run with the permissions and RLS context of the view owner (typically `postgres` in Supabase). This means a view owner with superuser or service-role privileges bypasses every RLS policy on the underlying tables, turning the view into an authorization bypass.
2. Definer views silently expose data across tenant boundaries. A view owner who holds BYPASSRLS (the default for `postgres`) returns rows that any authenticated caller would not otherwise be allowed to see. The caller's JWT, role, and RLS predicates are not consulted.
3. Definer functions are a common privilege-escalation vector. A `SECURITY DEFINER` function executes with the owner's privileges, so any SQL injection vulnerability inside the function body, or any unvalidated input path, translates directly into owner-level write access.
4. Invoker semantics are auditable. When every view and function runs as the invoker, reviewers can reason about authorization by reading the RLS policies alone. Definer views and functions require reading the function body plus the owner's grants to understand the effective access path.
5. Invoker views cooperate with PostgREST. Supabase exposes views over a REST API. When the view is defined as invoker, the REST caller's JWT flows through to the underlying tables, and RLS policies on those tables gate the response.

## View Syntax

Postgres 15 introduced the `security_invoker` view option. Earlier versions do not support the option and must be upgraded before this rule can be enforced.

Create a new view with the option:

```sql
CREATE VIEW public.active_accounts
  WITH (security_invoker = on) AS
SELECT
  id,
  user_id,
  balance,
  created_at
FROM public.accounts
WHERE balance > 0;
```

Create or replace an existing view while preserving the option:

```sql
CREATE OR REPLACE VIEW public.active_accounts
  WITH (security_invoker = on) AS
SELECT
  id,
  user_id,
  balance,
  created_at
FROM public.accounts
WHERE balance > 0 AND created_at > now() - interval '90 days';
```

Retrofit the option on an existing view without rewriting the definition:

```sql
ALTER VIEW public.active_accounts SET (security_invoker = on);
```

Required Postgres version: 15 or later. Supabase Cloud and recent Supabase Local images meet this requirement. For self-hosted Postgres below 15, upgrade before landing any migration that depends on this rule.

## Function Syntax

Declare `SECURITY INVOKER` explicitly on every function, even though it is the default. Explicit annotation documents intent for reviewers and prevents accidental changes when the function is edited later.

Invoker function (required default):

```sql
CREATE OR REPLACE FUNCTION public.get_my_balance()
RETURNS numeric
LANGUAGE sql
SECURITY INVOKER
STABLE
AS $$
  SELECT balance FROM public.accounts WHERE user_id = auth.uid();
$$;
```

Definer function (permitted only with justification, see Exception Process below):

```sql
CREATE OR REPLACE FUNCTION public.admin_recompute_balances()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  /*
   * SECURITY DEFINER justification:
   * This function recomputes ledger balances from the transactions table
   * during a nightly batch. It must iterate across every tenant, which
   * requires BYPASSRLS. It is called only from pg_cron under the
   * postgres role. See docs/decisions/0042-definer-admin-recompute-balances.md
   * for the full rationale and rollback plan.
   */
  PERFORM public.recompute_all_tenants();
END;
$$;
```

Contrast:

1. `SECURITY INVOKER` runs the function body with the caller's role and RLS context. If the caller is `authenticated`, RLS predicates on every referenced table apply.
2. `SECURITY DEFINER` runs the function body with the owner's role and permissions. RLS is bypassed if the owner holds BYPASSRLS (typically `postgres`). The caller's JWT and role are not consulted inside the function body.
3. Always set `search_path` explicitly on `SECURITY DEFINER` functions. Without it, a malicious caller can shadow a function name in their own schema and have the definer function call the attacker's code with elevated privileges.

## Materialized Views Exception

Materialized views do not support the `security_invoker` option in Postgres 15 or 16. The option is parsed but has no effect at query time because the cached data was produced when the matview was last refreshed, under the refresher's role.

Required mitigations when a materialized view is necessary:

1. Enable RLS on every base table the matview reads from, exactly as rule 10 requires.
2. Grant `SELECT` on the matview only to a dedicated role that represents the intended audience (for example `authenticated` for a per-user aggregate, `anon` only for truly public data).
3. Revoke `SELECT` from `PUBLIC` explicitly.
4. If the matview contains tenant data, partition it by tenant and create a per-tenant view over the matview that filters by `auth.uid()` or the tenant claim. Do not expose the raw matview to clients.
5. Refresh the matview under a least-privileged role. If the refresher must be `postgres` or a service role, document that fact in the decision record for the matview.

Example GRANT pattern for a matview:

```sql
CREATE MATERIALIZED VIEW public.daily_order_totals AS
SELECT
  order_date,
  tenant_id,
  sum(amount) AS total
FROM public.orders
GROUP BY order_date, tenant_id;

REVOKE ALL ON public.daily_order_totals FROM PUBLIC;
GRANT SELECT ON public.daily_order_totals TO authenticated;
```

Wrap the matview in an invoker view that filters by tenant:

```sql
CREATE VIEW public.my_daily_totals
  WITH (security_invoker = on) AS
SELECT
  order_date,
  total
FROM public.daily_order_totals
WHERE tenant_id = (auth.jwt() ->> 'tenant_id')::uuid;
```

## Forbidden

1. `CREATE VIEW <name> AS SELECT ...` without the `WITH (security_invoker = on)` clause. Reviewers must reject the migration.
2. `CREATE OR REPLACE VIEW <name> AS SELECT ...` without the option, even if the prior definition had the option. `CREATE OR REPLACE VIEW` fully redefines the view, including options.
3. `CREATE FUNCTION ... SECURITY DEFINER` without a comment block inside the function body stating the justification, the caller, and the reference to the decision record.
4. `ALTER FUNCTION ... SECURITY DEFINER` on an existing invoker function without the same justification.
5. `SECURITY DEFINER` functions that omit `SET search_path = ...`. Always pin the search path to trusted schemas.
6. Views that select from tables in other schemas owned by superusers (for example `auth.users`) without confirming that the invoker has `SELECT` on those tables. If the view owner has access but the invoker does not, an invoker view will raise a permission error at query time, which is the correct behavior but must be anticipated by the caller.

## Verification

`pre-flight-checker` runs the following query against the target database before allowing any build-agent to proceed with a migration that touches views or functions:

```sql
SELECT
  n.nspname AS schema,
  c.relname AS view,
  c.reloptions
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'v'
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY n.nspname, c.relname;
```

The check fails pre-flight if any view in an application-owned schema has `reloptions` that does not contain `security_invoker=on`. A `NULL` value for `reloptions` means no options are set, which is a failure. The failure message lists the offending views so the orchestrator can route to a build agent for remediation.

Supplementary check via `information_schema.views` for cross-database portability:

```sql
SELECT
  table_schema,
  table_name,
  view_definition
FROM information_schema.views
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;
```

`information_schema.views` does not expose the `security_invoker` option directly, so pre-flight also runs the `pg_class.reloptions` query above and cross-references. The combined result set must show every application view with `security_invoker=on` present in `reloptions`.

Function check:

```sql
SELECT
  n.nspname AS schema,
  p.proname AS function,
  p.prosecdef AS is_definer
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY n.nspname, p.proname;
```

Any row with `is_definer = true` must have a paired decision record at `docs/decisions/NNNN-definer-<function>.md`. `pre-flight-checker` fails if it finds a definer function without a corresponding decision record in the repository.

Additional verification steps:

1. Grep every migration in the current pull request for the literal string `CREATE VIEW` and confirm each occurrence is followed by `WITH (security_invoker = on)`.
2. Grep for `SECURITY DEFINER` and confirm each match has an adjacent comment block and a decision record filename.
3. For every modified view, run a representative query as a synthetic `authenticated` JWT and confirm the row set matches the RLS predicate on the underlying table.
4. For every modified definer function, run the function under a non-owner role and confirm the expected privilege boundary.

## Exception Process

`SECURITY DEFINER` is permitted only when all of the following conditions are met:

1. A comment block inside the function body states the reason the definer attribute is necessary, the identity of the expected caller, and the name of the decision record. The comment block appears on the first line of the function body, before any executable statement.
2. A decision record at `docs/decisions/NNNN-definer-<function>.md` exists in the repository. The record states: the function name, the reason invoker was insufficient, the expected caller (cron job, service role, webhook), the blast radius of a compromised caller, the rollback plan, and the operator's identity.
3. A reviewer with the `database` or `security` role has approved the pull request that introduces the definer function. The approval must cite the decision record by filename in the review comment.
4. The function sets `search_path` explicitly with `SET search_path = ...` to a list of trusted schemas (typically `public, pg_temp`).
5. The function validates every input argument against injection. String concatenation into dynamic SQL is prohibited inside definer functions. Use `format('%I', ident)` for identifiers and `format('%L', literal)` for literals, or parameterized `EXECUTE ... USING ...`.

A pull request that introduces a definer function without all five conditions must be rejected in review. `review-agent` scans for `SECURITY DEFINER` and fails the review if the paired comment block or decision record is missing.

Forbidden shortcuts:

1. Adding `SECURITY DEFINER` to an existing invoker function via `ALTER FUNCTION` without a paired decision record.
2. Shipping a definer function as `SECURITY INVOKER` in the migration and flipping it to definer post-deploy via the Supabase dashboard. The change is not captured by migrations and cannot be audited.
3. Reusing an existing decision record for a new definer function. Each function requires its own record.

## Related Rules

1. Rule 10, `10-rls.md`, Row-Level Security, is the foundation that invoker views and invoker functions rely on. Without RLS on the base tables, invoker semantics provide no additional protection.
2. Rule 12, `12-keychain.md`, covers secure storage of the Supabase service-role key, which is the role that typically owns definer functions. Leaking the service-role key invalidates the isolation that invoker semantics provide.
3. Rule 05, `05-operational-policies.md`, Anti-Destruction Rules, for the broader migration safety framework that wraps security-invoker enforcement.
4. Rule 08, `08-em-dash-ban.md`, for character sanitation on view names, function bodies, comment blocks, and decision records.
