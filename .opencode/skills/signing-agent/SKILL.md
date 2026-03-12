---
name: signing-agent
description: Android keystore, iOS provisioning, Play/App Store config
---

# signing-agent - App Signing & Store Config

Configures Android keystore, iOS provisioning profiles, and Play/App Store configuration. Produces signing config — no real keys or certificates.

## Usage
```
/signing-agent
```

## Parameters
- None. This skill produces signing config artifacts.

## What It Does
1. Configures **Android keystore** setup (key.properties, build.gradle)
2. Configures **iOS provisioning** (profiles, entitlements)
3. Configures **Play Store** upload config
4. Configures **App Store** upload config
5. Outputs **keystore config** — Android signing configuration
6. Outputs **provisioning config** — iOS signing configuration
7. Outputs **signing config** — unified signing documentation

## Output
- Keystore config — Android keystore configuration
- Provisioning config — iOS provisioning profiles
- Signing config — Play/App Store upload configuration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Include real keystores, keys, or certificates (config/templates only)

## Tech Stack
- **Android:** keystore, key.properties
- **iOS:** provisioning profiles, entitlements
- **Stores:** Google Play, App Store
