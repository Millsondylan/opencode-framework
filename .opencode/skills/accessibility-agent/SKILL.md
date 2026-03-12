---
name: accessibility-agent
description: Semantic order, Semantics widget, screen reader labels, contrast, touch targets
---

# accessibility-agent - Accessibility (a11y)

Configures semantic order, Semantics widget, screen reader labels, contrast, and touch targets. Produces accessibility infrastructure.

## Usage
```
/accessibility-agent
```

## Parameters
- None. This skill produces accessibility artifacts.

## What It Does
1. Configures **semantic order** (Semantics, semantics order)
2. Adds **Semantics widget** wrappers where needed
3. Defines **screen reader labels** (semanticLabel, hint)
4. Ensures **contrast** compliance (WCAG)
5. Ensures **touch targets** ≥ 48×48dp
6. Outputs **Semantics wrappers** — reusable a11y components
7. Outputs **accessibility checklist** — verification guide
8. Outputs **screen reader labels** — label definitions

## Output
- Semantics wrappers — reusable a11y components
- Accessibility checklist — verification guide
- Screen reader labels — semantic label definitions

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)

## Tech Stack
- **a11y:** Semantics, TalkBack, VoiceOver
- **Standards:** WCAG
- **Touch:** 48×48dp minimum
- **Platform:** Flutter/Dart (mobile)
