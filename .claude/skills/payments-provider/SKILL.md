---
name: payments-provider
description: Implement RevenueCat, Stripe, or Google Play Billing integration with repository and datasources for the payments domain
---

# payments-provider - Payments Domain Provider

Implements RevenueCat, Stripe, or Google Play Billing integration, repository layer, remote/local data sources, and billing client wrappers. Second in the payments domain chain (2/6).

## Usage
```
/payments-provider
```

## Parameters
- None. This skill consumes payments-schema outputs and produces provider artifacts.

## What It Does
1. Integrates **RevenueCat** and/or **Stripe** and/or **Google Play Billing** (purchases, subscriptions, entitlements)
2. Implements **PaymentsRepository** — domain-facing repository interface
3. Implements **PaymentsRemoteDataSource** — RevenueCat/Stripe/Play Billing client wrapper
4. Implements **PaymentsLocalDataSource** — Hive or local cache for offline entitlements
5. Handles purchase flow, subscription status, and entitlement checks
6. Supports receipt validation and webhook handling (Stripe/Supabase Edge Functions)

## Output
- `payments_repository.dart` — PaymentsRepository implementation
- `payments_remote_data_source.dart` — PaymentsRemoteDataSource (RevenueCat/Stripe/Play Billing)
- `payments_local_data_source.dart` — PaymentsLocalDataSource (Hive/local cache)
- Billing integration adapters for chosen provider(s)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (payments-schema responsibility)
- Write flow/state orchestration (payments-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** RevenueCat, Stripe, Google Play Billing (one or more)
- **State:** Riverpod (provider registration only, not flow logic)
- **Storage:** Hive for local entitlement cache
- **Architecture:** Clean Architecture (data layer)
- **Domain:** payments (TaskSpec domain)
