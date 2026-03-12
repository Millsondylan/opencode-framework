---
name: e-commerce-provider
description: Implement catalog, cart, and checkout for the e-commerce domain
---

# e-commerce-provider - E-Commerce Domain Provider

Implements catalog, cart, and checkout. Second in the e-commerce domain chain (2/6).

## Usage
```
/e-commerce-provider
```

## Parameters
- None. This skill consumes e-commerce-schema outputs and produces provider artifacts.

## What It Does
1. Implements **CatalogRepository** — product list, detail, search
2. Implements **CartRepository** — add, remove, update quantity
3. Implements **OrderRepository** — create order, fetch orders, tracking
4. Implements **EcommerceRemoteDataSource** — Supabase/Stripe client
5. Implements **EcommerceLocalDataSource** — Hive cart persistence
6. Handles **checkout** — payment intent, order creation

## Output
- `catalog_repository.dart` — CatalogRepository implementation
- `cart_repository.dart` — CartRepository implementation
- `order_repository.dart` — OrderRepository implementation
- `ecommerce_remote_data_source.dart` — Supabase/Stripe client
- `ecommerce_local_data_source.dart` — Hive cart persistence

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (e-commerce-schema responsibility)
- Write flow/state orchestration (e-commerce-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase, Stripe
- **Storage:** Hive (cart persistence)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** e-commerce (TaskSpec domain)
