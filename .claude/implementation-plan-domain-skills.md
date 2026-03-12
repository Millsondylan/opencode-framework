# Implementation Plan: 96 Domain Chain Skills

## Batch Summary
- **Total Features:** 16 (F1–F16, one domain each)
- **Total Skills:** 96 (6 per domain: schema, provider, flow, ui, guard, test)
- **Total Batches:** 48
- **Estimated Build Agents:** 48 (chain 1→55→1)

## Skill Format Reference (from `.opencode/skills/finish/` and `prompt/`)
- **YAML frontmatter:** `name`, `description`
- **Markdown sections:** Usage, Parameters, What It Does, Output
- **Output path:** `.opencode/skills/{domain}-{pattern}/SKILL.md`

## Domain Chain Order (per domain)
1. schema → 2. provider → 3. flow → 4. ui → 5. guard → 6. test

## 16 Domains (F1–F16)
| F# | Domain |
|----|--------|
| F1 | auth |
| F2 | profile |
| F3 | billing |
| F4 | notification |
| F5 | chat |
| F6 | media |
| F7 | location |
| F8 | subscription |
| F9 | inventory |
| F10 | order |
| F11 | search |
| F12 | analytics |
| F13 | settings |
| F14 | onboarding |
| F15 | content |
| F16 | sync |

---

## Batch 1: auth-schema, auth-provider
**Assigned to:** build-agent-1  
**Features:** F1 (auth domain, skills 1–2)

### auth-schema
**Complexity:** Simple  
**Files to Create:**
- `.opencode/skills/auth-schema/SKILL.md` — Schema skill for auth domain

**Content Guidance (Mobile Agents Reference):**
- User model (id, email, displayName, photoURL, etc.)
- Token models (access token, refresh token, session)
- Auth state types (signed-in, signed-out, loading, error)

**Implementation Notes:**
- YAML: `name: auth-schema`, `description: Define auth data models and types`
- Sections: Usage, Parameters, What It Does, Output
- Reference existing `.opencode/skills/finish/SKILL.md` structure

### auth-provider
**Complexity:** Simple  
**Files to Create:**
- `.opencode/skills/auth-provider/SKILL.md` — Provider skill for auth

**Content Guidance (Mobile Agents Reference):**
- Supabase Auth integration (signUp, signIn, signOut, session)
- Token refresh, session persistence
- OAuth providers (Google, Apple, etc.)

**Implementation Notes:**
- YAML: `name: auth-provider`, `description: Implement auth provider (e.g. Supabase Auth)`
- Include provider-specific patterns from reference

---

## Batch 2: auth-flow, auth-ui
**Assigned to:** build-agent-2  
**Features:** F1 (auth domain, skills 3–4)

### auth-flow
**Complexity:** Medium-Low  
**Files to Create:**
- `.opencode/skills/auth-flow/SKILL.md` — Flow skill for auth

**Content Guidance:** Login/signup/logout flows, session restoration, error handling

### auth-ui
**Complexity:** Medium-Low  
**Files to Create:**
- `.opencode/skills/auth-ui/SKILL.md` — UI skill for auth

**Content Guidance:** Login screen, signup form, password reset, loading states

---

## Batch 3: auth-guard, auth-test
**Assigned to:** build-agent-3  
**Features:** F1 (auth domain, skills 5–6)

### auth-guard
**Complexity:** Simple  
**Files to Create:**
- `.opencode/skills/auth-guard/SKILL.md` — Guard skill for auth

**Content Guidance:** Route protection, auth middleware, redirect logic

### auth-test
**Complexity:** Simple  
**Files to Create:**
- `.opencode/skills/auth-test/SKILL.md` — Test skill for auth

**Content Guidance:** Unit tests for auth logic, integration tests for flows

---

## Batch 4: profile-schema, profile-provider
**Assigned to:** build-agent-4  
**Features:** F2 (profile domain)

### profile-schema
**Files to Create:** `.opencode/skills/profile-schema/SKILL.md`  
**Content Guidance:** User profile model, preferences, avatar, metadata

### profile-provider
**Files to Create:** `.opencode/skills/profile-provider/SKILL.md`  
**Content Guidance:** Profile CRUD, Supabase/API integration, avatar upload

---

## Batch 5: profile-flow, profile-ui
**Assigned to:** build-agent-5  
**Features:** F2

### profile-flow
**Files to Create:** `.opencode/skills/profile-flow/SKILL.md`  
**Content Guidance:** Edit profile flow, avatar change flow, validation

### profile-ui
**Files to Create:** `.opencode/skills/profile-ui/SKILL.md`  
**Content Guidance:** Profile screen, edit form, avatar picker

---

## Batch 6: profile-guard, profile-test
**Assigned to:** build-agent-6  
**Features:** F2

### profile-guard
**Files to Create:** `.opencode/skills/profile-guard/SKILL.md`  
**Content Guidance:** Require auth for profile access, ownership checks

### profile-test
**Files to Create:** `.opencode/skills/profile-test/SKILL.md`  
**Content Guidance:** Profile CRUD tests, validation tests

---

## Batch 7: billing-schema, billing-provider
**Assigned to:** build-agent-7  
**Features:** F3 (billing domain)

### billing-schema
**Files to Create:** `.opencode/skills/billing-schema/SKILL.md`  
**Content Guidance:** Plan model, invoice model, subscription status

### billing-provider
**Files to Create:** `.opencode/skills/billing-provider/SKILL.md`  
**Content Guidance:** Stripe/RevenueCat integration, subscription APIs

---

## Batch 8: billing-flow, billing-ui
**Assigned to:** build-agent-8  
**Features:** F3

### billing-flow
**Files to Create:** `.opencode/skills/billing-flow/SKILL.md`  
**Content Guidance:** Purchase flow, restore flow, upgrade/downgrade

### billing-ui
**Files to Create:** `.opencode/skills/billing-ui/SKILL.md`  
**Content Guidance:** Paywall, plan selector, subscription management UI

---

## Batch 9: billing-guard, billing-test
**Assigned to:** build-agent-9  
**Features:** F3

### billing-guard
**Files to Create:** `.opencode/skills/billing-guard/SKILL.md`  
**Content Guidance:** Premium feature gating, subscription status checks

### billing-test
**Files to Create:** `.opencode/skills/billing-test/SKILL.md`  
**Content Guidance:** Purchase flow tests, restore tests, mock providers

---

## Batch 10: notification-schema, notification-provider
**Assigned to:** build-agent-10  
**Features:** F4 (notification domain)

### notification-schema
**Files to Create:** `.opencode/skills/notification-schema/SKILL.md`  
**Content Guidance:** Notification model, push token, preferences

### notification-provider
**Files to Create:** `.opencode/skills/notification-provider/SKILL.md`  
**Content Guidance:** FCM/APNs, token registration, local notifications

---

## Batch 11: notification-flow, notification-ui
**Assigned to:** build-agent-11  
**Features:** F4

### notification-flow
**Files to Create:** `.opencode/skills/notification-flow/SKILL.md`  
**Content Guidance:** Permission request flow, deep link handling

### notification-ui
**Files to Create:** `.opencode/skills/notification-ui/SKILL.md`  
**Content Guidance:** In-app notification list, settings toggle

---

## Batch 12: notification-guard, notification-test
**Assigned to:** build-agent-12  
**Features:** F4

### notification-guard
**Files to Create:** `.opencode/skills/notification-guard/SKILL.md`  
**Content Guidance:** Permission checks, feature gating by notification status

### notification-test
**Files to Create:** `.opencode/skills/notification-test/SKILL.md`  
**Content Guidance:** Mock push tests, permission flow tests

---

## Batch 13: chat-schema, chat-provider
**Assigned to:** build-agent-13  
**Features:** F5 (chat domain)

### chat-schema
**Files to Create:** `.opencode/skills/chat-schema/SKILL.md`  
**Content Guidance:** Message model, conversation model, participant

### chat-provider
**Files to Create:** `.opencode/skills/chat-provider/SKILL.md`  
**Content Guidance:** Realtime subscriptions, message CRUD, presence

---

## Batch 14: chat-flow, chat-ui
**Assigned to:** build-agent-14  
**Features:** F5

### chat-flow
**Files to Create:** `.opencode/skills/chat-flow/SKILL.md`  
**Content Guidance:** Send message flow, load more, typing indicators

### chat-ui
**Files to Create:** `.opencode/skills/chat-ui/SKILL.md`  
**Content Guidance:** Chat list, message bubble, input bar

---

## Batch 15: chat-guard, chat-test
**Assigned to:** build-agent-15  
**Features:** F5

### chat-guard
**Files to Create:** `.opencode/skills/chat-guard/SKILL.md`  
**Content Guidance:** Conversation access checks, participant validation

### chat-test
**Files to Create:** `.opencode/skills/chat-test/SKILL.md`  
**Content Guidance:** Message send/receive tests, realtime mock tests

---

## Batch 16: media-schema, media-provider
**Assigned to:** build-agent-16  
**Features:** F6 (media domain)

### media-schema
**Files to Create:** `.opencode/skills/media-schema/SKILL.md`  
**Content Guidance:** Media model, upload metadata, thumbnail

### media-provider
**Files to Create:** `.opencode/skills/media-provider/SKILL.md`  
**Content Guidance:** Supabase Storage, upload/download, presigned URLs

---

## Batch 17: media-flow, media-ui
**Assigned to:** build-agent-17  
**Features:** F6

### media-flow
**Files to Create:** `.opencode/skills/media-flow/SKILL.md`  
**Content Guidance:** Upload flow, picker flow, progress handling

### media-ui
**Files to Create:** `.opencode/skills/media-ui/SKILL.md`  
**Content Guidance:** Image picker, gallery, upload progress

---

## Batch 18: media-guard, media-test
**Assigned to:** build-agent-18  
**Features:** F6

### media-guard
**Files to Create:** `.opencode/skills/media-guard/SKILL.md`  
**Content Guidance:** File size limits, type validation, quota checks

### media-test
**Files to Create:** `.opencode/skills/media-test/SKILL.md`  
**Content Guidance:** Upload/download tests, mock storage

---

## Batch 19: location-schema, location-provider
**Assigned to:** build-agent-19  
**Features:** F7 (location domain)

### location-schema
**Files to Create:** `.opencode/skills/location-schema/SKILL.md`  
**Content Guidance:** Lat/lng model, geofence, address

### location-provider
**Files to Create:** `.opencode/skills/location-provider/SKILL.md`  
**Content Guidance:** Geolocator, permission handling, background location

---

## Batch 20: location-flow, location-ui
**Assigned to:** build-agent-20  
**Features:** F7

### location-flow
**Files to Create:** `.opencode/skills/location-flow/SKILL.md`  
**Content Guidance:** Permission flow, get current location, watch position

### location-ui
**Files to Create:** `.opencode/skills/location-ui/SKILL.md`  
**Content Guidance:** Map widget, location picker, address display

---

## Batch 21: location-guard, location-test
**Assigned to:** build-agent-21  
**Features:** F7

### location-guard
**Files to Create:** `.opencode/skills/location-guard/SKILL.md`  
**Content Guidance:** Permission checks, service availability

### location-test
**Files to Create:** `.opencode/skills/location-test/SKILL.md`  
**Content Guidance:** Mock location tests, permission flow tests

---

## Batch 22: subscription-schema, subscription-provider
**Assigned to:** build-agent-22  
**Features:** F8 (subscription domain)

### subscription-schema
**Files to Create:** `.opencode/skills/subscription-schema/SKILL.md`  
**Content Guidance:** Subscription model, entitlement, trial status

### subscription-provider
**Files to Create:** `.opencode/skills/subscription-provider/SKILL.md`  
**Content Guidance:** RevenueCat/Stripe subscriptions, entitlement checks

---

## Batch 23: subscription-flow, subscription-ui
**Assigned to:** build-agent-23  
**Features:** F8

### subscription-flow
**Files to Create:** `.opencode/skills/subscription-flow/SKILL.md`  
**Content Guidance:** Subscribe flow, cancel flow, trial handling

### subscription-ui
**Files to Create:** `.opencode/skills/subscription-ui/SKILL.md`  
**Content Guidance:** Plan cards, manage subscription screen

---

## Batch 24: subscription-guard, subscription-test
**Assigned to:** build-agent-24  
**Features:** F8

### subscription-guard
**Files to Create:** `.opencode/skills/subscription-guard/SKILL.md`  
**Content Guidance:** Entitlement checks, feature gating

### subscription-test
**Files to Create:** `.opencode/skills/subscription-test/SKILL.md`  
**Content Guidance:** Mock subscription tests, entitlement tests

---

## Batch 25: inventory-schema, inventory-provider
**Assigned to:** build-agent-25  
**Features:** F9 (inventory domain)

### inventory-schema
**Files to Create:** `.opencode/skills/inventory-schema/SKILL.md`  
**Content Guidance:** Item model, stock level, variant

### inventory-provider
**Files to Create:** `.opencode/skills/inventory-provider/SKILL.md`  
**Content Guidance:** Inventory CRUD, stock updates, sync

---

## Batch 26: inventory-flow, inventory-ui
**Assigned to:** build-agent-26  
**Features:** F9

### inventory-flow
**Files to Create:** `.opencode/skills/inventory-flow/SKILL.md`  
**Content Guidance:** Stock check flow, reserve flow, restock flow

### inventory-ui
**Files to Create:** `.opencode/skills/inventory-ui/SKILL.md`  
**Content Guidance:** Stock display, low-stock warning, inventory list

---

## Batch 27: inventory-guard, inventory-test
**Assigned to:** build-agent-27  
**Features:** F9

### inventory-guard
**Files to Create:** `.opencode/skills/inventory-guard/SKILL.md`  
**Content Guidance:** Stock availability checks, concurrency guards

### inventory-test
**Files to Create:** `.opencode/skills/inventory-test/SKILL.md`  
**Content Guidance:** Stock update tests, race condition tests

---

## Batch 28: order-schema, order-provider
**Assigned to:** build-agent-28  
**Features:** F10 (order domain)

### order-schema
**Files to Create:** `.opencode/skills/order-schema/SKILL.md`  
**Content Guidance:** Order model, order item, status enum

### order-provider
**Files to Create:** `.opencode/skills/order-provider/SKILL.md`  
**Content Guidance:** Order CRUD, status updates, history

---

## Batch 29: order-flow, order-ui
**Assigned to:** build-agent-29  
**Features:** F10

### order-flow
**Files to Create:** `.opencode/skills/order-flow/SKILL.md`  
**Content Guidance:** Checkout flow, order confirmation, cancel flow

### order-ui
**Files to Create:** `.opencode/skills/order-ui/SKILL.md`  
**Content Guidance:** Order list, order detail, status badge

---

## Batch 30: order-guard, order-test
**Assigned to:** build-agent-30  
**Features:** F10

### order-guard
**Files to Create:** `.opencode/skills/order-guard/SKILL.md`  
**Content Guidance:** Ownership checks, status transition validation

### order-test
**Files to Create:** `.opencode/skills/order-test/SKILL.md`  
**Content Guidance:** Order lifecycle tests, checkout tests

---

## Batch 31: search-schema, search-provider
**Assigned to:** build-agent-31  
**Features:** F11 (search domain)

### search-schema
**Files to Create:** `.opencode/skills/search-schema/SKILL.md`  
**Content Guidance:** Search result model, filter model, sort options

### search-provider
**Files to Create:** `.opencode/skills/search-provider/SKILL.md`  
**Content Guidance:** Full-text search, filters, pagination

---

## Batch 32: search-flow, search-ui
**Assigned to:** build-agent-32  
**Features:** F11

### search-flow
**Files to Create:** `.opencode/skills/search-flow/SKILL.md`  
**Content Guidance:** Search flow, debounce, filter application

### search-ui
**Files to Create:** `.opencode/skills/search-ui/SKILL.md`  
**Content Guidance:** Search bar, results list, filter chips

---

## Batch 33: search-guard, search-test
**Assigned to:** build-agent-33  
**Features:** F11

### search-guard
**Files to Create:** `.opencode/skills/search-guard/SKILL.md`  
**Content Guidance:** Rate limiting, query validation, auth for results

### search-test
**Files to Create:** `.opencode/skills/search-test/SKILL.md`  
**Content Guidance:** Search result tests, filter tests

---

## Batch 34: analytics-schema, analytics-provider
**Assigned to:** build-agent-34  
**Features:** F12 (analytics domain)

### analytics-schema
**Files to Create:** `.opencode/skills/analytics-schema/SKILL.md`  
**Content Guidance:** Event model, property model, user property

### analytics-provider
**Files to Create:** `.opencode/skills/analytics-provider/SKILL.md`  
**Content Guidance:** Firebase Analytics, Mixpanel, event logging

---

## Batch 35: analytics-flow, analytics-ui
**Assigned to:** build-agent-35  
**Features:** F12

### analytics-flow
**Files to Create:** `.opencode/skills/analytics-flow/SKILL.md`  
**Content Guidance:** Event tracking flow, screen tracking, user properties

### analytics-ui
**Files to Create:** `.opencode/skills/analytics-ui/SKILL.md`  
**Content Guidance:** Dashboard placeholders, debug overlay (dev only)

---

## Batch 36: analytics-guard, analytics-test
**Assigned to:** build-agent-36  
**Features:** F12

### analytics-guard
**Files to Create:** `.opencode/skills/analytics-guard/SKILL.md`  
**Content Guidance:** PII scrubbing, consent checks, dev vs prod

### analytics-test
**Files to Create:** `.opencode/skills/analytics-test/SKILL.md`  
**Content Guidance:** Event capture tests, mock provider tests

---

## Batch 37: settings-schema, settings-provider
**Assigned to:** build-agent-37  
**Features:** F13 (settings domain)

### settings-schema
**Files to Create:** `.opencode/skills/settings-schema/SKILL.md`  
**Content Guidance:** Settings model, preference keys, defaults

### settings-provider
**Files to Create:** `.opencode/skills/settings-provider/SKILL.md`  
**Content Guidance:** SharedPreferences/UserDefaults, sync to backend

---

## Batch 38: settings-flow, settings-ui
**Assigned to:** build-agent-38  
**Features:** F13

### settings-flow
**Files to Create:** `.opencode/skills/settings-flow/SKILL.md`  
**Content Guidance:** Save flow, reset flow, migration flow

### settings-ui
**Files to Create:** `.opencode/skills/settings-ui/SKILL.md`  
**Content Guidance:** Settings list, toggle, picker, section headers

---

## Batch 39: settings-guard, settings-test
**Assigned to:** build-agent-39  
**Features:** F13

### settings-guard
**Files to Create:** `.opencode/skills/settings-guard/SKILL.md`  
**Content Guidance:** Validation, feature-flag gating for settings

### settings-test
**Files to Create:** `.opencode/skills/settings-test/SKILL.md`  
**Content Guidance:** Persistence tests, default value tests

---

## Batch 40: onboarding-schema, onboarding-provider
**Assigned to:** build-agent-40  
**Features:** F14 (onboarding domain)

### onboarding-schema
**Files to Create:** `.opencode/skills/onboarding-schema/SKILL.md`  
**Content Guidance:** Onboarding step model, completion state

### onboarding-provider
**Files to Create:** `.opencode/skills/onboarding-provider/SKILL.md`  
**Content Guidance:** Step completion tracking, persistence

---

## Batch 41: onboarding-flow, onboarding-ui
**Assigned to:** build-agent-41  
**Features:** F14

### onboarding-flow
**Files to Create:** `.opencode/skills/onboarding-flow/SKILL.md`  
**Content Guidance:** Step navigation, skip flow, completion flow

### onboarding-ui
**Files to Create:** `.opencode/skills/onboarding-ui/SKILL.md`  
**Content Guidance:** PageView, step indicators, CTA buttons

---

## Batch 42: onboarding-guard, onboarding-test
**Assigned to:** build-agent-42  
**Features:** F14

### onboarding-guard
**Files to Create:** `.opencode/skills/onboarding-guard/SKILL.md`  
**Content Guidance:** First-launch check, skip-once logic

### onboarding-test
**Files to Create:** `.opencode/skills/onboarding-test/SKILL.md`  
**Content Guidance:** Step navigation tests, completion tests

---

## Batch 43: content-schema, content-provider
**Assigned to:** build-agent-43  
**Features:** F15 (content domain)

### content-schema
**Files to Create:** `.opencode/skills/content-schema/SKILL.md`  
**Content Guidance:** Content model, block type, metadata

### content-provider
**Files to Create:** `.opencode/skills/content-provider/SKILL.md`  
**Content Guidance:** Content fetch, pagination, caching

---

## Batch 44: content-flow, content-ui
**Assigned to:** build-agent-44  
**Features:** F15

### content-flow
**Files to Create:** `.opencode/skills/content-flow/SKILL.md`  
**Content Guidance:** Load flow, refresh flow, infinite scroll

### content-ui
**Files to Create:** `.opencode/skills/content-ui/SKILL.md`  
**Content Guidance:** Content card, list, detail view, skeleton

---

## Batch 45: content-guard, content-test
**Assigned to:** build-agent-45  
**Features:** F15

### content-guard
**Files to Create:** `.opencode/skills/content-guard/SKILL.md`  
**Content Guidance:** Access control, age gate, content filter

### content-test
**Files to Create:** `.opencode/skills/content-test/SKILL.md`  
**Content Guidance:** Fetch tests, cache tests, pagination tests

---

## Batch 46: sync-schema, sync-provider
**Assigned to:** build-agent-46  
**Features:** F16 (sync domain)

### sync-schema
**Files to Create:** `.opencode/skills/sync-schema/SKILL.md`  
**Content Guidance:** Sync state model, conflict model, last-modified

### sync-provider
**Files to Create:** `.opencode/skills/sync-provider/SKILL.md`  
**Content Guidance:** Offline-first, conflict resolution, Supabase realtime

---

## Batch 47: sync-flow, sync-ui
**Assigned to:** build-agent-47  
**Features:** F16

### sync-flow
**Files to Create:** `.opencode/skills/sync-flow/SKILL.md`  
**Content Guidance:** Sync trigger flow, conflict resolution flow, retry

### sync-ui
**Files to Create:** `.opencode/skills/sync-ui/SKILL.md`  
**Content Guidance:** Sync indicator, offline banner, conflict dialog

---

## Batch 48: sync-guard, sync-test
**Assigned to:** build-agent-48  
**Features:** F16

### sync-guard
**Files to Create:** `.opencode/skills/sync-guard/SKILL.md`  
**Content Guidance:** Connectivity checks, conflict prevention

### sync-test
**Files to Create:** `.opencode/skills/sync-test/SKILL.md`  
**Content Guidance:** Sync cycle tests, conflict resolution tests, offline tests

---

## Test Criteria

**Pre-implementation:**
- [ ] Baseline: existing skills (finish, prompt) unchanged
- [ ] `.opencode/skills/` directory exists

**Post-implementation:**
- [ ] All 96 SKILL.md files exist at `.opencode/skills/{domain}-{pattern}/SKILL.md`
- [ ] Each file has valid YAML frontmatter (name, description)
- [ ] Each file has Usage, Parameters, What It Does, Output sections
- [ ] Format matches finish/prompt conventions
- [ ] No hardcoded secrets or credentials

**Per-batch verification:**
- [ ] Files created per batch specification
- [ ] Content aligns with Mobile Agents reference for domain

## Risks
- **Domain list may differ:** If TaskSpec specified different 16 domains, batches 4–48 need domain name substitution.
- **Reference dependency:** Build-agents need access to Mobile Agents — Complete Build Agent Reference for domain-specific content; if unavailable, use generic patterns.

## Dependencies
- Mobile Agents — Complete Build Agent Reference (user-provided, from earlier conversation)
- Existing skill format: `.opencode/skills/finish/SKILL.md`, `.opencode/skills/prompt/SKILL.md`
