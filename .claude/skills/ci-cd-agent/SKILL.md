---
name: ci-cd-agent
description: GitHub Actions, Fastlane, Codemagic
---

# ci-cd-agent - CI/CD Pipeline

Configures GitHub Actions, Fastlane, and Codemagic for build automation, testing, and deployment.

## Usage
```
/ci-cd-agent
```

## Parameters
- None. This skill produces CI/CD artifacts.

## What It Does
1. Configures **GitHub Actions** workflows
2. Sets up **Fastlane** lanes (build, test, deploy)
3. Configures **Codemagic** (if used)
4. Outputs **.github/workflows/ci.yaml** — CI pipeline
5. Outputs **fastlane/** — Fastfile, lanes, config
6. Outputs **build scripts** — build and deploy automation

## Output
- `.github/workflows/ci.yaml` — GitHub Actions CI workflow
- `fastlane/` — Fastlane configuration (Fastfile, lanes)
- Build scripts — automation scripts

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Include real secrets (use env vars, GitHub Secrets)

## Tech Stack
- **CI:** GitHub Actions
- **Build:** Fastlane, Codemagic
- **Platform:** Flutter/Dart (mobile)
