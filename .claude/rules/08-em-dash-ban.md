# Dash Ban

## Overview

This project prohibits all non-ASCII horizontal dash characters in every artifact produced by every agent and by the orchestrator. Only the ASCII hyphen-minus (U+002D) is permitted.

Rationale:

1. Clipboard corruption. Non-ASCII dashes frequently fail to round-trip through terminals, SSH sessions, and code editors configured with single-byte locales. Pasting a payload containing U+2014 into a shell often triggers "command not found" or silent character substitution.
2. Diff noise. When an IDE or a word processor auto-converts a typed hyphen into U+2013 or U+2014, the resulting diff hunks mix real content changes with invisible punctuation changes. Reviewers waste cycles distinguishing semantic edits from encoding artifacts.
3. Visual ambiguity. U+2014 (em-dash), U+2013 (en-dash), U+2012 (figure dash), and U+2015 (horizontal bar) render at nearly identical widths in most monospace fonts. Code depending on exact string equality breaks in ways that are invisible to the human reviewer.
4. Grep reliability. ASCII-only dashes let `grep`, `ripgrep`, and `sed` operate without locale flags or Unicode-aware regex engines.
5. Cross-platform stability. Windows CP1252, macOS UTF-8, and Linux terminal emulators each handle the U+2012 to U+2015 range differently. ASCII hyphen is universal.

## Forbidden Characters

| Codepoint | Name           | UTF-8 Hex   |
|-----------|----------------|-------------|
| U+2014    | Em Dash        | `E2 80 94`  |
| U+2013    | En Dash        | `E2 80 93`  |
| U+2012    | Figure Dash    | `E2 80 92`  |
| U+2015    | Horizontal Bar | `E2 80 95`  |

Any occurrence of any of these four codepoints in any agent output, tool input, file write, file edit, commit message, or comment constitutes a rule violation.

## Allowed Characters

| Codepoint | Name              | ASCII |
|-----------|-------------------|-------|
| U+002D    | Hyphen-Minus      | `-`   |
| U+003A    | Colon             | `:`   |
| U+002E    | Full Stop         | `.`   |
| U+002C    | Comma             | `,`   |

Use the ASCII hyphen-minus for all compound words, negative numbers, command-line flags, and range separators. Use colon, comma, or period to replace em-dash or en-dash clause separators.

## Scope

The ban applies to every output surface:

1. Orchestrator responses to the user.
2. Agent outputs returned from subagent invocations.
3. Tool inputs passed to Write, Edit, Bash, and any other tool.
4. File writes created by build-agent or any implementation agent.
5. File edits applied by debugger or any modification agent.
6. Git commit messages authored via `git commit -m`.
7. Code comments in every language (`//`, `#`, `/* */`, `<!-- -->`, `"""..."""`, etc.).
8. String literals in source code.
9. Docstrings, JSDoc blocks, rustdoc blocks, and any other in-code documentation.
10. Log statements emitted at any level.
11. Markdown headings, body text, tables, and fenced code blocks.
12. JSON, YAML, and TOML values.
13. SQL identifiers and string literals.
14. Environment variable values set in `.env` templates.

There is no carve-out for quoted user input reproduced back to the user. If the user pastes text containing banned characters, the agent must strip or substitute them before echoing the content back.

## Detection Patterns

### Python

```python
import re

BANNED_DASH_PATTERN = re.compile('[\u2012\u2013\u2014\u2015]')

def contains_banned_dash(text: str) -> bool:
    return bool(BANNED_DASH_PATTERN.search(text))

def strip_banned_dash(text: str) -> str:
    return BANNED_DASH_PATTERN.sub('-', text)
```

### ripgrep or grep with PCRE

```bash
grep -P '[\x{2012}-\x{2015}]' FILE
rg '[\u2012-\u2015]' FILE
```

### Ruby

```ruby
BANNED_DASH = /[\u2012\u2013\u2014\u2015]/

def contains_banned_dash?(text)
  text.match?(BANNED_DASH)
end
```

### Node.js

```javascript
const BANNED_DASH = /[\u2012\u2013\u2014\u2015]/u;

function containsBannedDash(text) {
  return BANNED_DASH.test(text);
}
```

### Shell one-liner (scan all tracked files)

```bash
git ls-files | xargs grep -lP '[\x{2012}-\x{2015}]' 2>/dev/null
```

## Enforcement

1. `pre_tool_use.py` hook (PreToolUse) scans every Write, Edit, and Bash tool input for the banned codepoints and blocks the tool invocation on match. The hook exits with a non-zero status and emits a diagnostic naming the offending codepoint and its position in the input.
2. `review-agent` performs a final scan of every file modified during the current pipeline run and flags any residual banned dash as an imperfection, forcing a debugger pass before decide-agent can output COMPLETE.
3. CI jobs should run the shell one-liner above and fail the build if any match is returned.
4. Pre-commit hooks (when configured by the project) run the same scan against staged changes.
5. Agents that detect a banned dash in their own draft output must silently substitute it before emitting the final response. No meta-commentary about the substitution is required.

## Substitution Guide

| Original usage                 | Replace with                  | Example before          | Example after            |
|--------------------------------|-------------------------------|-------------------------|--------------------------|
| Compound word                  | ASCII hyphen                  | `well`+U+2014+`known`   | `well-known`             |
| Parenthetical clause           | Comma pair, or parentheses    | `foo`+U+2014+`bar`+U+2014+`baz` | `foo, bar, baz`  |
| Clause separator, strong break | Colon, or period + new sentence | `Result`+U+2014+`pass`| `Result: pass`           |
| Range, numeric                 | ASCII hyphen                  | `10`+U+2013+`20`        | `10-20`                  |
| Range, date                    | ASCII hyphen                  | `Jan`+U+2013+`Mar`      | `Jan-Mar`                |
| Bullet lead-in                 | Colon or period               | `Note`+U+2014+`do`+space+`X`| `Note: do X`         |
| Attribution after quote        | Two ASCII hyphens             | U+2014+`Author`         | `-- Author`              |

Choose the substitution that preserves the semantic relationship between the two sides of the original dash. When in doubt, prefer the colon for definitional relationships and the comma for parenthetical asides.

## Known Source Patterns

The banned characters most commonly enter a codebase through these channels:

1. macOS keyboard shortcut `Option` + `-` produces U+2013 by default, and `Option` + `Shift` + `-` produces U+2014. Agents running on macOS must never emit a literal keystroke that would trigger these bindings into a final output buffer.
2. Google Docs, Microsoft Word, and Apple Pages enable "smart punctuation" by default, which silently rewrites a typed hyphen-space-hyphen sequence into a U+2014. Any text drafted in these editors and pasted into a repo must pass through a sanitizer first.
3. Slack, Discord, and Notion also apply smart-punctuation substitutions. Content copied from chat transcripts must be scanned.
4. Some Markdown renderers (notably older versions of pandoc and redcarpet) auto-convert `--` into U+2013 and `---` into U+2014 during render. This does not affect source files but can mislead authors reviewing rendered documentation into believing their source already contains the fancy dash.
5. LLM tokenizers frequently emit U+2014 natively when a training corpus was heavy on professionally edited prose. Agents must scrub their own output before returning it.
6. OCR output from scanned PDFs often maps hand-drawn horizontal strokes to U+2015 (horizontal bar) rather than ASCII hyphen.
7. `clipboard.read()` in browser automation (Puppeteer, Playwright, Selenium) may receive smart-quoted content. Always sanitize clipboard payloads before writing them to files.

## Related Rules

1. `.claude/rules/05-operational-policies.md`, Anti-Destruction Rules, for the broader file safety framework.
2. `.claude/rules/01-pipeline-orchestration.md`, review-agent responsibilities, for the post-build enforcement step.
3. `.claude/rules/09-confidence-scoring.md`, Format Compliance dimension, which includes dash-ban compliance as a format criterion.
