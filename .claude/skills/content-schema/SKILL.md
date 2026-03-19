---
name: content-schema
description: Define content item, rich text, categories, and type IDs 120–129 for the content domain
---

# content-schema - Content Domain Schema

Defines content item, rich text, categories, and content state types for the content domain. First in the content domain chain (1/6).

## Usage
```
/content-schema
```

## Parameters
- None. This skill produces schema artifacts for the content domain.

## What It Does
1. Defines **ContentItem** entity with Hive persistence (`@HiveType` typeId: 120)
2. Defines **RichText** model with Hive persistence (typeId: 121)
3. Defines **Category** model with Hive persistence (typeId: 122)
4. Creates **ContentItemDTO**, **CategoryDTO** for API/transport layer
5. Creates **ContentItemValidator** for input validation
6. Defines content types (article, video, podcast, link)

## Output
- `content_item.dart` — ContentItem model with `@HiveType(typeId: 120)`
- `rich_text.dart` — RichText model with `@HiveType(typeId: 121)`
- `category.dart` — Category model with `@HiveType(typeId: 122)`
- `content_item_dto.dart` — ContentItem DTO for API/transport
- `category_dto.dart` — Category DTO for API/transport
- `content_item_validator.dart` — ContentItem input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** content (TaskSpec domain)
