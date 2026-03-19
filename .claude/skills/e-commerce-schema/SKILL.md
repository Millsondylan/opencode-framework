---
name: e-commerce-schema
description: Define product, cart, order, and type IDs 150–159 for the e-commerce domain
---

# e-commerce-schema - E-Commerce Domain Schema

Defines product, cart, order, and e-commerce state types for the e-commerce domain. First in the e-commerce domain chain (1/6).

## Usage
```
/e-commerce-schema
```

## Parameters
- None. This skill produces schema artifacts for the e-commerce domain.

## What It Does
1. Defines **Product** entity with Hive persistence (`@HiveType` typeId: 150)
2. Defines **CartItem** model with Hive persistence (typeId: 151)
3. Defines **Order** model with Hive persistence (typeId: 152)
4. Creates **ProductDTO**, **CartItemDTO**, **OrderDTO** for API/transport layer
5. Creates **ProductValidator**, **OrderValidator** for input validation
6. Defines order status (pending, paid, shipped, delivered, cancelled)

## Output
- `product.dart` — Product model with `@HiveType(typeId: 150)`
- `cart_item.dart` — CartItem model with `@HiveType(typeId: 151)`
- `order.dart` — Order model with `@HiveType(typeId: 152)`
- `product_dto.dart` — Product DTO for API/transport
- `order_dto.dart` — Order DTO for API/transport
- `product_validator.dart` — Product input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** e-commerce (TaskSpec domain)
