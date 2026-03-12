---
name: theme-agent
description: Material 3 design system — color tokens, typography, spacing, dark/light, component theme
---

# theme-agent - Design System & Theme

Creates Material 3 design system — color tokens, typography, spacing, dark/light themes, component theme. Mobile-first: 320–480px, safe areas, 48×48dp touch targets.

## Usage
```
/theme-agent
```

## Parameters
- None. This skill produces theme artifacts.

## What It Does
1. Defines **color tokens** (primary, secondary, surface, error, etc.)
2. Defines **typography** scale (headline, body, label)
3. Defines **spacing** scale (4dp base, 8dp grid)
4. Configures **dark/light** themes
5. Defines **component theme** (buttons, cards, inputs)
6. Applies **mobile-first** constraints: 320–480px viewport
7. Configures **safe areas** (notch, home indicator)
8. Ensures **48×48dp touch targets** minimum
9. Outputs **app_theme.dart** — ThemeData
10. Outputs **app_colors.dart** — color tokens
11. Outputs **app_typography.dart** — text styles
12. Outputs **app_spacing.dart** — spacing constants
13. Outputs **app_breakpoints.dart** — responsive breakpoints
14. Outputs **app_safe_area.dart** — safe area utilities

## Output
- `app_theme.dart` — ThemeData configuration
- `app_colors.dart` — Color tokens
- `app_typography.dart` — Typography scale
- `app_spacing.dart` — Spacing constants
- `app_breakpoints.dart` — Responsive breakpoints
- `app_safe_area.dart` — Safe area utilities

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)

## Tech Stack
- **Design:** Material 3
- **Platform:** Flutter/Dart (mobile)
- **Constraints:** 320–480px, 48×48dp touch targets
