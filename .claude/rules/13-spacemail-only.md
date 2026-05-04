# Email Routing: Spacemail Insight MCP Only

## Policy

All outbound email originating from any process, agent, script, service, worker, cron job, webhook handler, or test harness under this repository must route through the Spacemail Insight MCP tool surface, specifically the family of tools exposed as `mcp__claude_ai_Spacemail_Insight__*`. No other transport path for outbound email is permitted. Direct SMTP submission, provider HTTP APIs, third party SDKs, and raw transport libraries are prohibited. This includes but is not limited to SMTP, SendGrid, Mailgun, Postmark, Amazon SES, Resend, Nodemailer, and Python `smtplib`.

The policy applies whether the recipient is internal (employees, contractors) or external (customers, leads, partners, vendors), whether the volume is one message or one million, and whether the environment is local development, continuous integration, staging, or production. There is no exception for "quick scripts," "one off notifications," "transactional bypass," or "development smoke tests." Every code path that results in an email being delivered to a mailbox must go through the Spacemail Insight MCP surface.

The `pre_tool_use.py` hook and `review-agent` enforce this policy by scanning code for banned imports and banned HTTP endpoints. Writes that introduce any banned library, SDK, or endpoint are rejected before the file lands on disk.

## Rationale

Routing all outbound email through a single MCP surface produces five concrete operational benefits that direct provider integration cannot match:

1. **Unified audit trail.** Every send, every bounce, every open, and every unsubscribe is logged through a single pipeline. Compliance officers, incident responders, and support engineers do not need to correlate logs across SendGrid dashboards, Mailgun webhook tables, Postmark activity feeds, and raw SMTP server logs. One tool, one log.

2. **Sender identity consolidation.** DKIM keys, SPF records, DMARC policies, and return path addresses are configured once at the Spacemail Insight layer. When domains rotate, keys roll, or policies tighten, the change lands in one place. Sender reputation is managed as a single shared asset rather than a fragmented set of per-provider scores.

3. **Deliverability optimization.** Spacemail Insight applies warmup schedules, throttling, IP pool selection, and domain routing policies consistently. When a provider degrades or a specific IP pool is throttled by a major mailbox provider, the routing layer reroutes traffic without application code changes.

4. **CAN-SPAM, GDPR, and CASL compliance.** Footer injection (postal address, unsubscribe link), suppression list enforcement (global unsubscribes, complaint suppression, bounce suppression), and consent ledger lookups happen at the routing layer. Application code cannot accidentally bypass compliance controls by calling a provider SDK directly.

5. **Cost observability.** Per message cost, per domain cost, and per campaign cost are attributed automatically. There is no need to reconcile invoices from five providers.

A secondary benefit is that this policy eliminates an entire class of credential leakage incidents. There are no SMTP passwords, provider API keys, or IAM access keys embedded in application configuration because the application never authenticates to a provider directly. Rule 12 (Keychain) governs the small set of credentials held by the Spacemail Insight layer itself.

## Blocked Library and Service List

The following imports, SDKs, HTTP clients, and endpoints are blocked. The `pre_tool_use.py` hook scans file writes for these strings and rejects any write that introduces them. Existing callers must be migrated to the Spacemail Insight MCP tool surface.

### Python

1. `smtplib` from the standard library.
2. `aiosmtplib` for async SMTP.
3. `sendgrid` and `sendgrid.helpers.*` packages from the SendGrid Python SDK.
4. `mailgun` and any module under `mailgun.*`.
5. `postmark` and any module under `postmarker.*`.
6. `boto3.client('ses')` and `boto3.client('sesv2')` when used for outbound mail.
7. `resend` Python package.
8. Any library that wraps the above (for example `django.core.mail` configured with an SMTP or provider backend, `flask-mail`, `pyramid_mailer`).

### JavaScript and Node.js

1. `nodemailer` and `nodemailer-smtp-transport`.
2. `@sendgrid/mail` and `@sendgrid/client`.
3. `mailgun.js` and `mailgun-js`.
4. `postmark` (the Postmark Node SDK).
5. `@aws-sdk/client-ses` and `@aws-sdk/client-sesv2` when used for outbound mail.
6. `resend` npm package.
7. Any wrapper (for example `next-email`, `nuxt-mail`, `nestjs-mailer`) configured with SMTP or a banned provider backend.

### Raw HTTP and CLI

Any HTTP client call (using `curl`, `httpx`, `requests`, `fetch`, `axios`, `got`, `node-fetch`, or equivalent) whose destination host matches any of the following patterns is blocked:

1. `smtp.*` (any SMTP submission endpoint, including `smtp.gmail.com`, `smtp.office365.com`, `smtp.sendgrid.net`, `smtp.mailgun.org`, `smtp.postmarkapp.com`, `email-smtp.*.amazonaws.com`).
2. `api.sendgrid.com` (SendGrid v3 API).
3. `api.mailgun.net` (Mailgun API).
4. `api.postmarkapp.com` (Postmark API).
5. `email.*.amazonaws.com` and `sesv2.*.amazonaws.com` (SES API endpoints).
6. `api.resend.com`.
7. Any direct call to port 25, 465, 587, or 2525 from application code.

### Shell Commands

The `mail`, `sendmail`, `mailx`, `mutt`, `msmtp`, and `ssmtp` command line tools are blocked when invoked from scripts or build steps under this repository. Interactive developer usage outside the repository is not governed by this rule.

## Correct Usage

All outbound email must be sent by invoking a Spacemail Insight MCP tool. The tool name pattern is `mcp__claude_ai_Spacemail_Insight__{verb}` where `{verb}` is the specific action. The primary send tool is `mcp__claude_ai_Spacemail_Insight__send_email`.

Pseudo-code for a transactional send:

```text
response = mcp__claude_ai_Spacemail_Insight__send_email(
  from_address = "billing@example.com",
  from_name    = "Example Billing",
  to           = [{"email": "customer@example.net", "name": "Jane Customer"}],
  subject      = "Your invoice for April 2026",
  html_body    = render_template("invoice.html", {...}),
  text_body    = render_template("invoice.txt",  {...}),
  headers = {
    "X-Entity-Ref-ID": invoice.id,
    "List-Unsubscribe": "<mailto:unsubscribe@example.com?subject=unsub-" + customer.id + ">, <https://example.com/u/" + customer.token + ">",
    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
  },
  category       = "transactional.billing",
  consent_ledger = "billing_recipients",
  postal_address = "Example Inc., 123 Main St, Toronto ON M5V 1A1, Canada",
  suppress_if_complaint = true,
  suppress_if_bounce    = true
)
```

Pseudo-code for a bulk marketing send (note the extra consent and unsubscribe requirements):

```text
response = mcp__claude_ai_Spacemail_Insight__send_campaign(
  campaign_id      = "apr-2026-newsletter",
  from_address     = "news@example.com",
  from_name        = "Example News",
  segment_id       = "consented_global_newsletter",
  template_id      = "newsletter-apr-2026",
  unsubscribe_url  = "https://example.com/u/{{token}}",
  postal_address   = "Example Inc., 123 Main St, Toronto ON M5V 1A1, Canada",
  require_double_opt_in = true,
  consent_jurisdictions = ["EU", "UK", "CA"],
  throttle_rpm     = 2000
)
```

Other verbs in the `mcp__claude_ai_Spacemail_Insight__*` family include `validate_recipient`, `fetch_bounces`, `fetch_complaints`, `suppress_address`, `lookup_consent`, and `fetch_delivery_status`. The full list is discoverable via the MCP introspection surface at session start.

## Local Queue Pattern

For components that need a fire and forget semantic (HTTP request handlers that must return quickly, background workers that batch events, stream processors that emit notifications), the correct pattern is an asynchronous local queue drained by a dedicated worker that invokes Spacemail Insight MCP. Direct provider fallback is not permitted even under load.

Layered pattern:

1. **Producer side.** The request handler or background job writes an `OutboundEmail` record to a durable local queue. The queue is a database table (for example `outbound_email_queue` with columns `id`, `payload_jsonb`, `status`, `attempts`, `next_attempt_at`, `created_at`, `sent_at`, `error`) or a message broker topic (Redis Streams, Kafka). The handler returns after the enqueue succeeds. No provider call happens in the request path.

2. **Worker side.** A dedicated worker process polls the queue, claims a batch of pending records (for example with `FOR UPDATE SKIP LOCKED` in Postgres), invokes `mcp__claude_ai_Spacemail_Insight__send_email` for each record, and updates the record status based on the tool response. Retries use exponential backoff with jitter. Permanent failures land in a dead letter table for human review.

3. **Backpressure.** The worker respects the `throttle_rpm` hint returned by Spacemail Insight. If the MCP surface reports temporary unavailability, the worker pauses the queue and does not fall back to any provider.

Do not implement a "provider fallback" mode. If Spacemail Insight is unavailable, the queue backs up. The queue depth and age are monitored. When Spacemail Insight recovers, the queue drains. Skipping the MCP surface to "keep mail flowing" is a policy violation and the review agent will block any such code.

## Compliance Requirements

Every send must satisfy the compliance obligations of every jurisdiction whose recipients are included in the `to`, `cc`, or `bcc` lists. Because recipient addresses rarely reveal jurisdiction, the safe default is to satisfy the union of CAN-SPAM, GDPR, and CASL.

### CAN-SPAM (United States)

1. **Accurate headers.** The `From`, `Reply-To`, and `Return-Path` headers must identify the sending organization truthfully. Pseudonymous senders must still resolve to a real legal entity.
2. **Accurate subject line.** Deceptive or misleading subject lines are prohibited.
3. **Identification as advertisement.** Commercial messages must be clearly identified as such. Transactional messages are exempt from this specific requirement but still must satisfy the other CAN-SPAM rules.
4. **Postal address in footer.** Every commercial message must include a valid physical postal address of the sender. Spacemail Insight injects this from the `postal_address` field on the send call.
5. **Unsubscribe mechanism.** A conspicuous unsubscribe link must be included. The unsubscribe request must be honored within 10 business days. Spacemail Insight writes unsubscribe requests to the suppression list in real time.
6. **No harvesting.** Recipient lists must not be harvested from the web or purchased from address dealers.

### GDPR (European Union and European Economic Area)

1. **Lawful basis.** Marketing to EU recipients requires a lawful basis, typically consent. Consent must be freely given, specific, informed, and unambiguous.
2. **Double opt in.** For EU marketing recipients, double opt in is required. The recipient confirms by clicking a link sent to the supplied address before being added to the list. Spacemail Insight rejects bulk sends to EU segments that are not flagged as double opt in confirmed.
3. **Consent log.** The timestamp, IP address, form URL, and exact consent text shown at the time of opt in must be stored for the life of the relationship plus a statutory retention period. The `consent_ledger` parameter on the send call references the log.
4. **Easy withdrawal.** Withdrawal of consent must be as easy as giving it. A one click unsubscribe link satisfies this requirement. List-Unsubscribe and List-Unsubscribe-Post headers must be present.
5. **Data subject requests.** Data subjects may request access, rectification, erasure, and portability. The queue schema must preserve the fields needed to answer these requests.

### CASL (Canada)

1. **Express or implied consent.** Canadian Anti Spam Legislation requires either express consent or a narrowly defined implied consent based on an existing business relationship.
2. **Consent log.** As with GDPR, the time, method, and form of consent must be stored.
3. **Identification.** The sender must be identified by legal name and provide a postal address and a contact method (email or phone).
4. **Unsubscribe.** A functioning unsubscribe mechanism must process requests within 10 business days.
5. **Penalties.** Violations attract administrative monetary penalties up to one million Canadian dollars per violation for an individual and ten million for an organization. This is the strictest regime of the three and should be the default standard when jurisdiction is unclear.

## Enforcement

Policy enforcement is layered. Each layer catches violations that previous layers missed.

1. **Pre write scan.** The `pre_tool_use.py` hook runs before every `Write` and `Edit` tool call. It scans the proposed file contents for banned imports (`smtplib`, `nodemailer`, `@sendgrid/mail`, and the full blocked list above) and banned HTTP endpoints (`api.sendgrid.com`, `api.mailgun.net`, `smtp.*`, and the rest). A match rejects the write with a structured error that names the offending token and points to this rule file.

2. **Post write lint.** The `post_tool_use.py` hook runs after each write. It re scans the file to catch cases where the banned token was introduced via a rewrite that the pre scan did not flag (for example, a large multi file refactor). Matches generate a review request that blocks the pipeline until resolved.

3. **Review agent.** The review agent at pipeline stage 15 runs a repository wide grep for banned tokens on every changed file in the current batch and on the full list of files modified in the pipeline run. Any match blocks `decide-agent` from outputting `COMPLETE`.

4. **CI smoke test.** A shell test under `tests/` runs `rg --type py --type js --type ts` for the banned tokens on the whole repository. The job fails the build if any match exists outside the ignore list (which only ever contains this rule file itself and documentation files that enumerate the bans).

5. **Production observability.** The Spacemail Insight layer logs every send with the source binary and process name. Any send originating from a process that is not registered as a Spacemail caller triggers a paging alert. This catches runtime violations that slipped past static analysis.

## Fallback Blocker Protocol

When the Spacemail Insight MCP surface is unavailable for any reason (dependency outage, credential rotation in progress, planned maintenance, regional failure), the correct response is **not** to fall back to a provider SDK or direct SMTP. Falling back to a provider is a policy violation that voids the audit trail, the suppression list enforcement, and the compliance posture. Instead:

1. The worker that drains the outbound queue pauses the queue. It records the outage reason and the timestamp in the queue control table.
2. The producer side continues to enqueue messages. The durable queue absorbs the outage. Latency rises but no message is lost and no compliance control is skipped.
3. The on call engineer files a blocker entry in `docs/open-items.md` using the standard blocker schema (id, date, severity, owner, description, mitigation, resolution target). The entry is cross referenced from the nearest decision record in `docs/decisions/`.
4. If the outage exceeds the agreed recovery time objective, the on call engineer escalates to the Spacemail Insight vendor contact. No code change is made to route around the MCP layer.
5. When the MCP surface recovers, the worker resumes the queue. The blocker entry is updated with the resolution timestamp and moved to the resolved section.

The only acceptable alternative to the Spacemail Insight MCP surface is to not send the email. This is by design. If a specific transactional flow cannot tolerate the queue depth that grows during an outage, the correct response is to reduce the dependency on email for that flow (for example, by showing an in app notification and deferring the email), not to bypass the policy.

## Related Rules

1. **Rule 12 (Secrets: Keychain and age Encrypted Backup).** Any SMTP, provider API, or transport credentials required by the Spacemail Insight layer itself are stored in the macOS Keychain. Application code does not hold these credentials because application code does not authenticate to providers directly.
2. **Rule 07 (Decision Records).** Any exception to this policy, including temporary allowances during provider migrations or emergency incident response, must be documented as a decision record in `docs/decisions/` with the scope, duration, compensating controls, and the approving authority. Verbal exceptions are not valid.
3. **Rule 08 (Em Dash Ban).** All code comments, commit messages, and documentation under this repository follow the ASCII hyphen policy. This file is written with ASCII hyphens only.
4. **Rule 10 (Row Level Security).** The `outbound_email_queue`, `suppression_list`, and `consent_ledger` tables referenced in this rule are subject to RLS policies defined in rule 10.
5. **Rule 11 (Security Invoker).** Views over the email tables that expose data to dashboards and reporting tools are created with `security_invoker=on` so that the dashboard user's RLS policies apply, not the view owner's.

## Summary

1. Every outbound email routes through `mcp__claude_ai_Spacemail_Insight__*`.
2. Every other transport path (SMTP, SendGrid, Mailgun, Postmark, SES, Resend, Nodemailer, smtplib, raw HTTP to provider endpoints, `mail`/`sendmail`/`mailx`/`mutt`) is banned.
3. Every send satisfies the union of CAN-SPAM, GDPR, and CASL compliance controls.
4. Every component that needs fire and forget semantics uses a local durable queue drained by a worker that calls the MCP surface.
5. Every outage is absorbed by the queue. No provider fallback. No exceptions.
