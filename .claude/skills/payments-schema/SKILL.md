---
name: payments-schema
description: Define subscription models, transaction records, and entitlement definitions for the payments domain
---

# payments-schema - Payments Domain Schema

Defines subscription models, transaction records, entitlement definitions, and payment state types for the payments domain. First in the payments domain chain (1/6).

## Usage
```
/payments-schema
```

## Parameters
- None. This skill produces schema artifacts for the payments domain.

## What It Does
1. Defines **Subscription** entity with Hive persistence (`@HiveType` typeId: 20)
2. Defines **Transaction** model with Hive persistence (typeId: 21)
3. Defines **Entitlement** model with Hive persistence (typeId: 22)
4. Defines **Product** / **Plan** enums or models for offerings (typeIds: 23–24)
5. Creates **SubscriptionDTO**, **TransactionDTO**, **EntitlementDTO** for API/transport layer
6. Creates validators for subscription and transaction input validation
7. Defines payment state types (active, expired, pending, error)

## Output
- `subscription_entity.dart` — Subscription model with `@HiveType(typeId: 20)`
- `transaction_entity.dart` — Transaction model with `@HiveType(typeId: 21)`
- `entitlement_entity.dart` — Entitlement model with `@HiveType(typeId: 22)`
- `product.dart` or `plan.dart` — Product/Plan enum or model (typeIds: 23–24)
- `subscription_dto.dart` — Subscription DTO for API/transport
- `transaction_dto.dart` — Transaction DTO for API/transport
- `entitlement_dto.dart` — Entitlement DTO for API/transport
- `subscription_validator.dart` — Subscription input validation
- `transaction_validator.dart` — Transaction input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** payments (TaskSpec domain)
