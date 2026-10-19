# ADR-0022: Screenshot Pipeline Uses Real UI Captures Inside Claude-Generated Frames

## Status
accepted

## Context
Store screenshots must reflect the real app, but surrounding frames benefit from polished image generation.

## Decision
Capture real UI from the running app and composite it into Claude-generated device frames and marketing backgrounds.

## Consequences

### Positive
- Screenshots never misrepresent actual app behavior.
- Marketing frames look consistent and polished.
- Per-locale screenshots scale via templated frames.

### Negative
- Two-step pipeline is slower than pure capture.
- Frame updates require regenerating assets.

### Neutral
- Claude image generation is used only outside the device screen area.

## Alternatives Considered
- Fully generated screenshots (rejected: misrepresents the app).
- Plain captures only (rejected: weaker on store conversion).

## Related
- screenshots
- CLAUDE.md
