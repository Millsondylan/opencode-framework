---
name: media-schema
description: Define media item, upload state, CDN, and type IDs 80–89 for the media domain
---

# media-schema - Media Domain Schema

Defines media item, upload state, CDN references, and media types for the media domain. First in the media domain chain (1/6).

## Usage
```
/media-schema
```

## Parameters
- None. This skill produces schema artifacts for the media domain.

## What It Does
1. Defines **MediaItem** entity with Hive persistence (`@HiveType` typeId: 80)
2. Defines **UploadState** model with Hive persistence (typeId: 81)
3. Defines **CdnUrl** model with Hive persistence (typeId: 82)
4. Creates **MediaItemDTO** and **UploadStateDTO** for API/transport layer
5. Creates **MediaItemValidator** for input validation
6. Defines media types (image, video, audio, document)

## Output
- `media_item.dart` — MediaItem model with `@HiveType(typeId: 80)`
- `upload_state.dart` — UploadState model with `@HiveType(typeId: 81)`
- `cdn_url.dart` — CdnUrl model with `@HiveType(typeId: 82)`
- `media_item_dto.dart` — MediaItem DTO for API/transport
- `upload_state_dto.dart` — UploadState DTO for API/transport
- `media_item_validator.dart` — MediaItem input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** media (TaskSpec domain)
