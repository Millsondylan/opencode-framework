---
name: content-guard
description: Implement access control and content reporting for the content domain
---

# content-guard - Content Domain Guard

Implements access control and content reporting. Fifth in the content domain chain (5/6).

## Usage
```
/content-guard
```

## Parameters
- None. This skill consumes content-schema and content-provider outputs and produces guard artifacts.

## What It Does
1. Implements **AccessControlGuard** — content visibility by role, subscription, region
2. Implements **ContentReportGuard** — report inappropriate content, abuse flow
3. Integrates with Riverpod content state for guard decisions
4. Handles **gated content** — paywall, premium, age-restricted
5. Handles **report flow** — submit, feedback, moderation

## Output
- `access_control_guard.dart` — AccessControlGuard
- `content_report_guard.dart` — ContentReportGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (content-schema responsibility)
- Write provider/repository code (content-provider responsibility)
- Write flow/state orchestration (content-flow responsibility)
- Write UI components or screens
- Write tests (content-test responsibility)

## Tech Stack
- **State:** Riverpod (reads content state for guard decisions)
- **Backend:** Supabase (report API)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** content (TaskSpec domain)
