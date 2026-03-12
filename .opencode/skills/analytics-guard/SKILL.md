---
name: analytics-guard
description: Implement PII scrubbing, consent checks, and GDPR compliance for the analytics domain
---

# analytics-guard - Analytics Domain Guard

Implements PII scrubbing, consent checks, and GDPR compliance. Fifth in the analytics domain chain (5/6).

## Usage
```
/analytics-guard
```

## Parameters
- None. This skill consumes analytics-schema and analytics-provider outputs and produces guard artifacts.

## What It Does
1. Implements **PiiScrubber** — strips PII from event payloads (email, phone, name)
2. Implements **ConsentGuard** — blocks event dispatch when consent not granted
3. Implements **GdprGuard** — right-to-deletion, data retention, anonymization
4. Integrates with Riverpod analytics state for guard decisions
5. Handles **sensitive field detection** — regex, keyword lists

## Output
- `pii_scrubber.dart` — PiiScrubber for event sanitization
- `consent_guard.dart` — ConsentGuard for consent checks
- `gdpr_guard.dart` — GdprGuard for GDPR compliance

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (analytics-schema responsibility)
- Write provider/repository code (analytics-provider responsibility)
- Write flow/state orchestration (analytics-flow responsibility)
- Write UI components or screens
- Write tests (analytics-test responsibility)

## Tech Stack
- **State:** Riverpod (reads analytics state for guard decisions)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** analytics (TaskSpec domain)
