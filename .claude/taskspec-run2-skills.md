# TaskSpec — Run 2: 17 Skills (Architecture, Infrastructure, Theme, Cross-cutting, Data Layer)

## Request Summary

Create 17 skills for architecture, infrastructure, theme, cross-cutting concerns, and data layer. Each skill is a SKILL.md file that guides build agents when implementing these concerns in a Flutter/Dart mobile app. Output path: `.claude/skills/{skill-name}/SKILL.md`. Format: YAML frontmatter (name, description), sections: Usage, Parameters, What It Does, Output, What It Must NOT Do. Shared constraints: anti-orchestration, tech stack (Riverpod, Hive, Supabase, Material 3, Clean Architecture).

---

## Features

### Architecture (4 skills)

#### F1: architecture-agent
**Description:** Skill for implementing Clean Architecture structure, layer boundaries, and project organization.
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/architecture-agent/SKILL.md`
- [ ] YAML frontmatter: `name: architecture-agent`, `description` (concise)
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: folder structure (domain/data/presentation), layer boundaries, dependency rules, Clean Architecture conventions
- [ ] Output: directory structure, barrel files, layer separation
- [ ] What It Must NOT Do: Call other agents or use Task tool; implement domain logic; write tests
- [ ] Tech Stack section: Riverpod, Hive, Supabase, Material 3, Clean Architecture
- [ ] Anti-orchestration rule included

#### F2: di-agent
**Description:** Skill for implementing dependency injection (Riverpod providers, scopes, overrides).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/di-agent/SKILL.md`
- [ ] YAML frontmatter: `name: di-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: Riverpod provider setup, ProviderScope, overrides for testing, repository/provider registration
- [ ] Output: provider definitions, main.dart ProviderScope setup, override patterns
- [ ] What It Must NOT Do: Call other agents; implement business logic; write tests
- [ ] Tech Stack: Riverpod, Clean Architecture
- [ ] Anti-orchestration rule included

#### F3: router-agent
**Description:** Skill for implementing navigation and routing (GoRouter, declarative routes, deep links).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/router-agent/SKILL.md`
- [ ] YAML frontmatter: `name: router-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: GoRouter setup, route definitions, shell routes, redirects, deep link handling
- [ ] Output: router configuration, route constants, navigation helpers
- [ ] What It Must NOT Do: Call other agents; implement screen UI; write route guards (guard skills)
- [ ] Tech Stack: GoRouter (or equivalent), Material 3
- [ ] Anti-orchestration rule included

#### F4: convention-enforcement-agent
**Description:** Skill for enforcing code conventions (lint rules, formatting, naming).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/convention-enforcement-agent/SKILL.md`
- [ ] YAML frontmatter: `name: convention-enforcement-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: analysis_options.yaml, custom lint rules, dart format, naming conventions
- [ ] Output: lint config, custom rule definitions, CI integration for lint
- [ ] What It Must NOT Do: Call other agents; change business logic; write tests
- [ ] Tech Stack: Dart analyzer, flutter_lints
- [ ] Anti-orchestration rule included

---

### Infrastructure (4 skills)

#### F5: env-config-agent
**Description:** Skill for environment configuration (dev/staging/prod, env vars, secrets).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/env-config-agent/SKILL.md`
- [ ] YAML frontmatter: `name: env-config-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: env config per flavor, --dart-define, .env handling (no secrets in code), Supabase URL/anon key injection
- [ ] Output: env config classes, flavor setup, build config
- [ ] What It Must NOT Do: Call other agents; hardcode secrets; write tests
- [ ] Tech Stack: Flutter flavors, Supabase
- [ ] Anti-orchestration rule included

#### F6: dependency-agent
**Description:** Skill for managing dependencies (pubspec.yaml, version constraints, transitive deps).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/dependency-agent/SKILL.md`
- [ ] YAML frontmatter: `name: dependency-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: pubspec.yaml structure, dependency_overrides, version resolution, dep upgrade guidance
- [ ] Output: pubspec updates, dependency graph awareness
- [ ] What It Must NOT Do: Call other agents; add unnecessary deps; write tests
- [ ] Tech Stack: Dart pub, Flutter
- [ ] Anti-orchestration rule included

#### F7: ci-cd-agent
**Description:** Skill for CI/CD pipelines (build, test, deploy).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/ci-cd-agent/SKILL.md`
- [ ] YAML frontmatter: `name: ci-cd-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: GitHub Actions / Codemagic / similar, build matrix, test job, deploy to stores
- [ ] Output: workflow files, build scripts
- [ ] What It Must NOT Do: Call other agents; modify app code; write tests
- [ ] Tech Stack: CI platform (GitHub Actions, etc.)
- [ ] Anti-orchestration rule included

#### F8: signing-agent
**Description:** Skill for app signing (Android keystore, iOS provisioning, release builds).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/signing-agent/SKILL.md`
- [ ] YAML frontmatter: `name: signing-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: Android signing config, iOS provisioning, key.properties, release build setup
- [ ] Output: signing config files, build.gradle updates, Xcode project config
- [ ] What It Must NOT Do: Call other agents; commit keys or secrets; write tests
- [ ] Tech Stack: Flutter, Android, iOS
- [ ] Anti-orchestration rule included

---

### Theme (1 skill)

#### F9: theme-agent
**Description:** Skill for theming (Material 3, light/dark, color schemes, typography).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/theme-agent/SKILL.md`
- [ ] YAML frontmatter: `name: theme-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: ThemeData, ColorScheme, Material 3, light/dark mode, typography, component themes
- [ ] Output: theme.dart, app theme provider, MaterialApp theme config
- [ ] What It Must NOT Do: Call other agents; implement screen layouts; write tests
- [ ] Tech Stack: Material 3, Flutter
- [ ] Anti-orchestration rule included

---

### Cross-cutting (4 skills)

#### F10: logging-agent
**Description:** Skill for structured logging (levels, tags, crash reporting).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/logging-agent/SKILL.md`
- [ ] YAML frontmatter: `name: logging-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: Logger setup, log levels, tags, PII scrubbing, crash reporting integration
- [ ] Output: logger utility, log interceptor, crash handler
- [ ] What It Must NOT Do: Call other agents; log secrets; write tests
- [ ] Tech Stack: Dart logging, Firebase Crashlytics (optional)
- [ ] Anti-orchestration rule included

#### F11: localization-agent
**Description:** Skill for i18n/l10n (arb files, l10n generation, locale switching).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/localization-agent/SKILL.md`
- [ ] YAML frontmatter: `name: localization-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: flutter_localizations, arb files, l10n.yaml, AppLocalizations, locale provider
- [ ] Output: arb files, generated l10n, locale switching logic
- [ ] What It Must NOT Do: Call other agents; hardcode strings in UI; write tests
- [ ] Tech Stack: Flutter intl, flutter_localizations
- [ ] Anti-orchestration rule included

#### F12: performance-agent
**Description:** Skill for performance optimization (profiling, lazy loading, image optimization).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/performance-agent/SKILL.md`
- [ ] YAML frontmatter: `name: performance-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: DevTools profiling, ListView.builder, image caching, const constructors, avoid rebuilds
- [ ] Output: performance patterns, optimization guidelines
- [ ] What It Must NOT Do: Call other agents; over-optimize prematurely; write tests
- [ ] Tech Stack: Flutter, Riverpod (select/selectAsync)
- [ ] Anti-orchestration rule included

#### F13: accessibility-agent
**Description:** Skill for accessibility (Semantics, screen readers, contrast).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/accessibility-agent/SKILL.md`
- [ ] YAML frontmatter: `name: accessibility-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: Semantics, semanticsLabel, semanticsHint, focus order, contrast ratios, touch targets
- [ ] Output: semantic annotations, a11y wrapper patterns
- [ ] What It Must NOT Do: Call other agents; implement business logic; write tests
- [ ] Tech Stack: Flutter Semantics, Material 3
- [ ] Anti-orchestration rule included

---

### Data Layer (4 skills)

#### F14: api-client-agent
**Description:** Skill for API client setup (HTTP, Supabase client, interceptors).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/api-client-agent/SKILL.md`
- [ ] YAML frontmatter: `name: api-client-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: Supabase client init, Dio/HTTP interceptors, auth header injection, error mapping
- [ ] Output: api_client.dart, Supabase singleton, interceptor chain
- [ ] What It Must NOT Do: Call other agents; implement repository logic; write tests
- [ ] Tech Stack: Supabase, Dio (optional)
- [ ] Anti-orchestration rule included

#### F15: local-storage-agent
**Description:** Skill for local persistence (Hive, SharedPreferences, secure storage).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/local-storage-agent/SKILL.md`
- [ ] YAML frontmatter: `name: local-storage-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: Hive init, TypeAdapters, box management, flutter_secure_storage for secrets
- [ ] Output: storage service, Hive setup, adapter registration
- [ ] What It Must NOT Do: Call other agents; implement sync logic; write tests
- [ ] Tech Stack: Hive, flutter_secure_storage
- [ ] Anti-orchestration rule included

#### F16: sync-agent
**Description:** Skill for offline-first sync (conflict resolution, Supabase realtime).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/sync-agent/SKILL.md`
- [ ] YAML frontmatter: `name: sync-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: offline queue, conflict resolution (last-write-wins or custom), Supabase realtime subscriptions
- [ ] Output: sync service, conflict resolver, realtime channel setup
- [ ] What It Must NOT Do: Call other agents; implement domain-specific sync (use domain sync skills); write tests
- [ ] Tech Stack: Hive, Supabase Realtime
- [ ] Anti-orchestration rule included

#### F17: cache-agent
**Description:** Skill for caching (in-memory, disk, TTL, invalidation).
**Acceptance Criteria:**
- [ ] SKILL.md exists at `.claude/skills/cache-agent/SKILL.md`
- [ ] YAML frontmatter: `name: cache-agent`, `description`
- [ ] Sections: Usage, Parameters, What It Does, Output, What It Must NOT Do
- [ ] What It Does: cache layer, TTL, invalidation strategies, Riverpod cache (keepAlive, autoDispose)
- [ ] Output: cache service, cache provider patterns
- [ ] What It Must NOT Do: Call other agents; implement repository logic; write tests
- [ ] Tech Stack: Riverpod, Hive (optional for disk cache)
- [ ] Anti-orchestration rule included

---

## Risks

- **Reference dependency:** Mobile Agents — Complete Build Agent Reference is user-provided; if build-agents lack access, content may be generic. Mitigation: Include sufficient inline guidance in TaskSpec.
- **Overlap with domain skills:** sync-agent may overlap with domain sync skills (e.g., offline-sync-*). Mitigation: sync-agent focuses on generic sync infrastructure; domain sync skills handle domain-specific models and flows.
- **Tech stack drift:** If project uses different stack (e.g., GetIt instead of Riverpod), skills may need adjustment. Mitigation: Document assumptions in each skill; plan-agent can flag if codebase differs.

---

## Assumptions

- Flutter/Dart mobile app (iOS/Android).
- Tech stack: Riverpod (state), Hive (local storage), Supabase (backend/auth/realtime), Material 3 (UI), Clean Architecture (layers).
- All skills follow anti-orchestration: agents must NOT call other agents or use Task tool; emit `REQUEST:` if delegation needed.
- Skill format matches existing domain skills (analytics-flow, auth-provider): YAML frontmatter + Usage, Parameters, What It Does, Output, What It Must NOT Do.
- Build agents create SKILL.md files only; no Dart/Flutter implementation in this run.
- Output path: `.claude/skills/{skill-name}/SKILL.md` where skill-name is the agent name (e.g., `architecture-agent`).

---

## Blockers

- None. Proceed to code-discovery and plan-agent.

---

## Next Stage Recommendation

Proceed to **code-discovery** to verify `.claude/skills/` structure and existing skill format. Then **plan-agent** to create batched implementation plan (e.g., 9 batches of 1–2 skills per build-agent, aligned with feature groupings above).
