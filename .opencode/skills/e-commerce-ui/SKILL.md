---
name: e-commerce-ui
description: Implement ProductGridScreen, CartScreen, and checkout for the e-commerce domain
---

# e-commerce-ui - E-Commerce Domain UI

Implements ProductGridScreen, CartScreen, and checkout. Fourth in the e-commerce domain chain (4/6).

## Usage
```
/e-commerce-ui
```

## Parameters
- None. This skill consumes e-commerce-flow outputs and produces UI artifacts.

## What It Does
1. Implements **ProductGridScreen** — product grid, search, filter, category
2. Implements **ProductDetailScreen** — product info, add to cart, reviews
3. Implements **CartScreen** — cart items, quantity, remove, total
4. Implements **CheckoutScreen** — payment form, order summary, confirm
5. Implements **OrderTrackingScreen** — order status, timeline
6. Uses **Material 3** — components, theming, typography

## Output
- `product_grid_screen.dart` — ProductGridScreen widget
- `product_detail_screen.dart` — ProductDetailScreen widget
- `cart_screen.dart` — CartScreen widget
- `checkout_screen.dart` — CheckoutScreen widget
- `order_tracking_screen.dart` — OrderTrackingScreen widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (e-commerce-schema responsibility)
- Write repository or data source code (e-commerce-provider responsibility)
- Write flow/state orchestration (e-commerce-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read ecommerceProvider, cartProvider, call EcommerceNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** e-commerce (TaskSpec domain)
