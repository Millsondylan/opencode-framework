---
skill: test-writer
category: quality
description: "Test prompt for test-writer skill — produces minimal test artifacts"
---

# Test: test-writer (Quality Skill)

Exercises the **test-writer** skill. Use with test-writer agent (or build-agent if simulating) with `skill: test-writer` assigned.

## Prompt

```
Write tests per test-writer skill guidance.

skill: test-writer

Given a simple function under test (e.g., a validator or utility), produce:
1. A test plan mapping tests to acceptance criteria
2. At least one real test with actual assertions (no mocks, no assert True, no placeholders)

Output: A minimal test file or test plan document. If no source exists, output a test plan template showing how tests would map to TaskSpec acceptance criteria.
```

## Expected Verifiable Output

- **Test file mode:** `*_test.dart` or `*.test.ts` with real assertions
- **Plan mode:** Markdown test plan with acceptance-criteria-to-test mapping

## Verification

1. Agent reads `.opencode/skills/test-writer/SKILL.md` (evidence: output maps tests to acceptance criteria, avoids mocks/placeholders)
2. Output follows skill guidance (no mocks, no assert True, no pass stubs per skill "What It Must NOT Do")
