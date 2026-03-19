---
name: e-commerce-flow
description: Implement cart state, checkout, and order tracking for the e-commerce domain
---

# e-commerce-flow - E-Commerce Domain Flow

Implements cart state, checkout, and order tracking. Third in the e-commerce domain chain (3/6).

## Usage
```
/e-commerce-flow
```

## Parameters
- None. This skill consumes e-commerce-schema and e-commerce-provider outputs and produces flow artifacts.

## What It Does
1. Implements **EcommerceNotifier** — Riverpod StateNotifier for e-commerce state
2. Defines **EcommerceState** — cart, cart total, orders, loading, error
3. Registers **ecommerceProvider**, **cartProvider**, **orderProvider**
4. Orchestrates **cart state** — add, remove, update, sync
5. Orchestrates **checkout** — validate cart, payment, order creation
6. Orchestrates **order tracking** — fetch status, refresh
7. Handles **cart persistence** — sync to server, merge conflicts

## Output
- `ecommerce_notifier.dart` — EcommerceNotifier (StateNotifier<EcommerceState>)
- `ecommerce_state.dart` — EcommerceState sealed class / union type
- `ecommerce_provider.dart` — ecommerceProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (e-commerce-schema responsibility)
- Write repository or data source code (e-commerce-provider responsibility)
- Write UI components or screens (e-commerce-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (cart via provider)
- **Backend:** Supabase/Stripe (via e-commerce-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** e-commerce (TaskSpec domain)
