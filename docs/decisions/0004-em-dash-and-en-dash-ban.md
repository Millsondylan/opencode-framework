# ADR-0004: Em-Dash and En-Dash Ban Across All Outputs

## Status
accepted

## Context
Fancy dashes corrupt clipboards, produce noisy diffs, and break grep-based enforcement.

## Decision
Ban the four fancy dash code points in every file, message, comment, and commit; scan on every write.

## Consequences

### Positive
- Universal terminal and editor compatibility.
- Clean diffs without invisible punctuation churn.
- Simple grep and sed rules that work without Unicode flags.

### Negative
- Contributors lose a typographic option they may prefer.
- macOS smart-punctuation must be disabled on authoring tools.

### Neutral
- ASCII hyphen-minus, colon, comma, and period cover all replacement cases.

## Alternatives Considered
- Allow fancy dashes in prose only (rejected: inconsistent across code and docs).
- Auto-rewrite in post-processing (rejected: still allows them upstream).

## Related
- .claude/rules/08-em-dash-ban.md
- .claude/hooks/pre_tool_use.py
