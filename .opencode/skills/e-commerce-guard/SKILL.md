---
name: e-commerce-guard
description: Implement inventory validation and coupon validation for the e-commerce domain
---

# e-commerce-guard - E-Commerce Domain Guard

Implements inventory validation and coupon validation. Fifth in the e-commerce domain chain (5/6).

## Usage
```
/e-commerce-guard
```

## Parameters
- None. This skill consumes e-commerce-schema and e-commerce-provider outputs and produces guard artifacts.

## What It Does
1. Implements **InventoryGuard** — validate stock before add-to-cart, checkout
2. Implements **CouponGuard** — validate coupon code, apply discount
3. Integrates with Riverpod e-commerce state for guard decisions
4. Handles **out-of-stock** — user feedback, disable add-to-cart
5. Handles **coupon errors** — invalid, expired, usage limit

## Output
- `inventory_guard.dart` — InventoryGuard
- `coupon_guard.dart` — CouponGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (e-commerce-schema responsibility)
- Write provider/repository code (e-commerce-provider responsibility)
- Write flow/state orchestration (e-commerce-flow responsibility)
- Write UI components or screens
- Write tests (e-commerce-test responsibility)

## Tech Stack
- **State:** Riverpod (reads e-commerce state for guard decisions)
- **Backend:** Supabase (inventory, coupon API)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** e-commerce (TaskSpec domain)
