---
name: layout-audit-agent
description: Overflow safety, scroll, keyboard avoidance, safe area
---

# layout-audit-agent - Layout Quality Audit

Audits layout quality: overflow safety, scroll behavior, keyboard avoidance, safe area handling. Produces structured report.

## Usage
```
/layout-audit-agent
```

## Parameters
- **Target screens** — Screens or layouts to audit
- **Viewport sizes** — Optional list (e.g., 320×568, 375×812)

## What It Does
1. Checks for overflow risks (unbounded height, fixed sizes)
2. Validates scroll behavior (ScrollView, ListView where needed)
3. Audits keyboard avoidance (insets, resize, focus)
4. Verifies safe area usage (notch, home indicator, status bar)
5. Flags layout constraints and flex issues

## Output
- `layout-audit-agent-report.json` — Findings, severity, screen, line refs

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Modify source code (read-only audit)
- Skip small-screen or large-text scenarios
- Ignore RTL or locale-specific layout needs when relevant
