---
name: e-commerce-test
description: Write cart logic and checkout tests for the e-commerce domain
---

# e-commerce-test - E-Commerce Domain Test

Writes cart logic and checkout tests. Sixth in the e-commerce domain chain (6/6).

## Usage
```
/e-commerce-test
```

## Parameters
- None. This skill consumes all prior e-commerce domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for e-commerce logic (cart, order, guards)
2. Writes **cart logic tests** — add, remove, quantity, total
3. Writes **checkout tests** — validation, payment, order creation
4. Provides **mock e-commerce repository** for isolated testing
5. Achieves **>80% coverage** for e-commerce domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `cart_repository_test.dart` — Unit tests for CartRepository
- `order_repository_test.dart` — Unit tests for OrderRepository
- `ecommerce_notifier_test.dart` — Unit tests for EcommerceNotifier
- `cart_logic_test.dart` — Cart logic tests
- `checkout_test.dart` — Checkout tests
- `mock_ecommerce_repository.dart` — Mock e-commerce repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production e-commerce logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase/Stripe client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** e-commerce (TaskSpec domain)
